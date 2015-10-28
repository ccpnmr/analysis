from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

import os
import random
import tarfile

from ccpncore.memops.metamodel import Util as metaUtil

from ccpncore.gui.Button import Button
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Frame import Frame
from ccpncore.gui.Label import Label
from ccpncore.gui import MessageDialog
from ccpncore.gui.TextEditor import TextEditor

from ccpncore.util import Logging
from ccpncore.util import Register
from ccpncore.util import Url

LOG_FILE_TEXT = 'Log file'
PROJECT_DIR_TEXT = 'Project directory'

SCRIPT_URL = 'http://www2.ccpn.ac.uk/cgi-bin/feedback/submitFeedback.py'

# code below has to be synchronised with code in SCRIPT_URL

class FeedbackPopup(QtGui.QDialog):

  # parent mandatory and that needs to have attributes _appBase and colourScheme
  def __init__(self, parent, title='Feedback Form'):
     
    QtGui.QDialog.__init__(self, parent=parent)
    self.setWindowTitle(title)

    self.registrationDict = Register.loadDict()

    frame = Frame(self)

    row = 0
    message = 'For bug reports please submit precise information, including any error message left on the console'
    label = Label(frame, message, grid=(row,0), gridSpan=(1,2))

    for key in ('name', 'organisation', 'email'):
      row += 1
      label = Label(frame, text='%s: ' % metaUtil.upperFirst(key), grid=(row,0))
      label = Label(frame, text=self.registrationDict.get(key), grid=(row,1))

    row += 1
    label = Label(frame, text='Include: ', grid=(row,0))
    includeFrame = Frame(frame, grid=(row,1))
    self.includeLogBox = CheckBox(includeFrame, text=LOG_FILE_TEXT, checked=True, grid=(0,0))
    self.includeProjectBox = CheckBox(includeFrame, text=PROJECT_DIR_TEXT, checked=False, grid=(0,1))

    row += 1
    label = Label(frame, text='Feedback: ', grid=(row,0))
    self.textEditor = TextEditor(frame, grid=(row,1))

    row += 1
    button = Button(frame, 'Submit', callback=self.submitFeedback, grid=(row,1)) 

  def submitFeedback(self):
    
    includeLog = self.includeLogBox.get()
    includeProject = self.includeProjectBox.get()
    feedback = self.textEditor.get().strip()
    
    if not feedback:
      return
      
    appBase = self.parent()._appBase
    
    if includeProject:
      # cannot use tempfile because that always hands back open object and tarfile needs actual path
      fileName = 'feedback%s.tgz' % random.randint(1, 10000000)
      try:
        projectPath = appBase.project.path
        directory = os.path.dirname(projectPath)
        pathToTar = os.path.basename(projectPath)
        cwd = os.getcwd()
        os.chdir(directory)
        tarFp = tarfile.open(fileName, 'w:gz')
        tarFp.add(pathToTar)
      finally:
        os.chdir(cwd)
        tarFp.close()
      fileName = os.path.join(directory, fileName)
    elif includeLog:
      logger = Logging.getLogger()
      if not hasattr(logger, 'logPath'):
        return
      fileName = logger.logPath
    else:
      fileName = None
      
    data = {}
    data['version'] = appBase.applicationVersion
    
    data['feedback'] = feedback
    
    for key in ('name', 'organisation', 'email'):
      data[key] = self.registrationDict.get(key, 'None')
      
    if fileName:
      try:
        response = Url.uploadFile(SCRIPT_URL, fileName, data)
      finally:
        if includeProject:
          os.remove(fileName)
    else:
      response = Url.fetchUrl(SCRIPT_URL, data)
      
    if 'Data successfully uploaded' in response:
      title = 'Success'
      msg = 'Feedback successfully submitted'
    else:
      title = 'Failure'
      msg = 'Problem submitting feedback'
      
    info = MessageDialog.showInfo(title,
          msg, colourScheme=self.parent().colourScheme)
      
    #print(response)
    self.hide()

