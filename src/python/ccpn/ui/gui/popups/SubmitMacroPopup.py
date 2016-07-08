"""Module Documentation here
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9315 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

import os
import urllib

from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Entry import Entry
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.TextEditor import TextEditor

from ccpn.util import Register
from ccpn.util import Url

SCRIPT_URL = 'http://www2.ccpn.ac.uk/cgi-bin/macros/submitMacro.py'

# code below has to be synchronised with code in SCRIPT_URL

class SubmitMacroPopup(QtGui.QDialog):

  # parent mandatory and that needs to have attributes _appBase and colourScheme
  def __init__(self, parent, title='Submit Macro Form'):
    QtGui.QDialog.__init__(self, parent=parent)
    self.setWindowTitle(title)

    self._registrationDict = Register.loadDict()

    frame = Frame(self)

    row = 0
    for key in ('name', 'organisation', 'email'):
      label = Label(frame, text='%s: ' % metaUtil.upperFirst(key), grid=(row,0))
      label = Label(frame, text=self._registrationDict.get(key), grid=(row,1))
      row += 1

    button = Button(frame, 'Macro path:', callback=self._selectMacro, grid=(row, 0))
    self.pathEntry = Entry(frame, maxLength=200, grid=(row,1))
    row += 1

    label = Label(frame, text='Keywords: ', grid=(row,0))
    self.keywordsEntry = Entry(frame, grid=(row,1))
    row += 1

    label = Label(frame, text='Description: ', grid=(row,0))
    self.textEditor = TextEditor(frame, grid=(row,1))
    row += 1

    button = Button(frame, 'Submit', callback=self._submitMacro, grid=(row, 1))

  def _selectMacro(self):
    
    dialog = FileDialog(parent=self.parent(), fileMode=FileDialog.ExistingFile, text='Select Macro',
                        preferences=self.parent().application.preferences.general)
    path = dialog.selectedFile()
    if path:
      self.pathEntry.set(path)

  def _submitMacro(self):

    application = self.parent.application
    logger = application.project._logger
    
    filePath = self.pathEntry.get()
    if not filePath or not os.path.exists(filePath) or not os.path.isfile(filePath):
      dialog = MessageDialog.showError('Error',
          'Path does not exist or is not file', colourScheme=self.parent().colourScheme)
      logger.error('Path specified for macro does not exist or is not file: %s' % filePath)
      return
      
    keywords = self.keywordsEntry.get()
    description = self.textEditor.get()
    
    if not keywords or not description:
      dialog = MessageDialog.showError('Error',
          'Both keywords and description required', colourScheme=self.parent().colourScheme)
      logger.error('Both keywords and description required for macro')
      return
      
    keywords = keywords.strip()
    description = description.strip()
    
    data = {}
    data['version'] = application.applicationVersion
    data['keywords'] = keywords
    data['description'] = description
    
    for key in ('name', 'organisation', 'email'):
      data[key] = self._registrationDict.get(key, 'None')
      
    try:
     response = Url.uploadFile(SCRIPT_URL, filePath, data)
    except urllib.error.HTTPError as e:
      response = str(e)
    if 'Macro successfully uploaded' in response:
      title = 'Success'
      msg = loggerMsg = 'Macro successfully submitted'
    else:
      title = 'Failure'
      msg = 'Problem submitting macro, see log for details'
      loggerMsg = 'Problem submitting macro: %s' % response
      
    logger.info(loggerMsg)
    info = MessageDialog.showInfo(title,
          msg, colourScheme=self.parent().colourScheme)
      
    self.hide()
