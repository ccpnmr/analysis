"""Module Documentation here
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

import os
import random

from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.framework.PathsAndUrls import ccpn2Url

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.TextEditor import TextEditor

from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpn.util import Logging
from ccpn.util import Register
from ccpn.util import Url

LOG_FILE_TEXT = 'Log file'
PROJECT_DIR_TEXT = 'Project directory'

SCRIPT_URL = ccpn2Url + '/cgi-bin/feedback/submitFeedback.py'

# code below has to be synchronised with code in SCRIPT_URL

class FeedbackPopup(QtGui.QDialog):

  # parent mandatory and that needs to have attributes _appBase and colourScheme
  def __init__(self, parent, title='Feedback Form'):
     
    QtGui.QDialog.__init__(self, parent=parent)
    self.setWindowTitle(title)

    self._registrationDict = Register.loadDict()

    frame = Frame(self)

    row = 0
    message = 'For bug reports please submit precise information, including any error message left on the console'
    label = Label(frame, message, grid=(row,0), gridSpan=(1,2))

    for key in ('name', 'organisation', 'email'):
      row += 1
      label = Label(frame, text='%s: ' % metaUtil.upperFirst(key), grid=(row,0))
      label = Label(frame, text=self._registrationDict.get(key), grid=(row,1))

    row += 1
    label = Label(frame, text='Include: ', grid=(row,0))
    includeFrame = Frame(frame, grid=(row,1))
    self.includeLogBox = CheckBox(includeFrame, text=LOG_FILE_TEXT, checked=True, grid=(0,0))
    self.includeProjectBox = CheckBox(includeFrame, text=PROJECT_DIR_TEXT, checked=False, grid=(0,1))

    row += 1
    label = Label(frame, text='Feedback: ', grid=(row,0))
    self.textEditor = TextEditor(frame, grid=(row,1))

    row += 1
    button = Button(frame, 'Submit', callback=self._submitFeedback, grid=(row, 1))

  def _submitFeedback(self):
    
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
      fileName = apiIo.packageProject(project._wrappedData.parent, filePrefix, includeBackups=True, includeLogs=includeLog)
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
      data[key] = self._registrationDict.get(key, 'None')
      
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

