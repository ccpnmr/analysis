from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

import os
import random

from ccpncore.memops.metamodel import Util as metaUtil

from application.core.widgets.Button import Button
from application.core.widgets.CheckBox import CheckBox
from application.core.widgets.Frame import Frame
from application.core.widgets.Label import Label
from application.core.widgets import MessageDialog
from application.core.widgets.TextEditor import TextEditor

from ccpn.util import Io
from ccpn.util import Logging
from ccpn.util import Register
from ccpn.util import Url

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
      filePrefix = 'feedback%s' % random.randint(1, 10000000)
      project = appBase.project
      projectPath = project.path
      directory = os.path.dirname(projectPath)
      filePrefix = os.path.join(directory, filePrefix)
      fileName = Io.packageProject(project._wrappedData.parent, filePrefix, includeBackups=True, includeLogs=includeLog)
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

