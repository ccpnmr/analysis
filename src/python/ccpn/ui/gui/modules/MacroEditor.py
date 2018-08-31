#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.PythonEditor import QCodeEditor
import datetime
import os

class MacroEditor(CcpnModule):
  """
  This module will create a temp python file when you press the run button and will execute it from the console.
  A file will be created in the temporary  macro directory .ccpn/macros
  and will be automatically deleted after the macro is ran.
  The user can decide to save as a in a new file location.

  The macro name is the file name on the disk (without the .py extension).
  NB. If you open an existing file.py and modify it, the changes are not automatically re-written on the disk.
   All changes WILL BE LOST if not save them. Automatic saving of a .py file can be dangerous for the users.

  """
  includeSettingsWidget = False
  className = 'MacroEditor'


  def __init__(self, mainWindow=None, name='Macro Editor', filePath=None):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)


    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    self.preferences = self.application.preferences
    self._pythonConsole = self.mainWindow.pythonConsole
    if self._pythonConsole is None:
      self._pythonConsole = IpythonConsole(self.mainWindow )
    self.macroPath =self.preferences.general.userMacroPath
    self._isTempMacro = True
    self._originalOpenedFile = None

    self.mainWidget.layout().setSpacing(5)
    self.mainWidget.layout().setContentsMargins(10,10,10,10)

    hGrid = 0
    self.namelabel = Label(self.mainWidget, 'Macro Name', grid=(hGrid,0))
    self.nameLineEdit = LineEdit(self.mainWidget,  grid=(0,1))
    # self.nameLineEdit.editingFinished().connect(self._changedName)

    hGrid +=1
    # macro editing area
    self.textBox = QCodeEditor(self.mainWidget, grid=(hGrid,0), acceptDrops=True, gridSpan=(1,2))

    hGrid +=1
    self.buttonBox = ButtonList(self, texts=['Open', 'save','Save As', 'Run'],
                                callbacks=[self._openMacroFile,self._saveMacro, self._saveMacroAs, self._runMacro], grid = (hGrid,1))


    self.filePath = filePath
    if self.filePath: # if  a path is specified then opens it
      self._openPath(self.filePath)

    self._setFileName(self.filePath)


    # self.textBox.editingFinished.connect(self._saveMacro)  # automatic saving
    # self.nameLineEdit.editingFinished.connect(self._macroNameChanged)  # automatic renaming the fileName

    self.droppedNotifier = GuiNotifier(self.textBox,
                                     [GuiNotifier.DROPEVENT], [DropBase.URLS],
                                     self._processDroppedItems)

  def _processDroppedItems(self, data):
    """
    CallBack for Drop events
    """
    urls = data.get('urls', [])
    if len(urls) == 1:
      filePath = urls[0]
      if len(self.textBox.get())>0:
        ok= MessageDialog.showYesNoWarning('Open new macro', 'Replace the current macro?')
        if ok:
          self._openPath(filePath)
          self._setFileName(filePath)
        else:
          return
      else:
        self._openPath(filePath)
        self._setFileName(filePath)
    else:
      MessageDialog.showMessage('', 'Drop only a file at the time')


  def _createTemporaryFile(self, name=None):
    if name is None:
      dateTime = datetime.datetime.now().strftime("%y-%m-%d-%H:%M:%S")
      tempName = 'Macro'+dateTime
      name = tempName
    filePath = self.application.tempMacrosPath + '/'+ name
    if filePath:
      if not filePath.endswith('.py'):
        filePath+='.py'
      with open(filePath, 'w') as f:
        f.write('')
        f.close()
    self.filePath = filePath
    return filePath


  def _runMacro(self):
    if self._pythonConsole is not None:
      if self.filePath:
        # self._pythonConsole._runMacro(self.filePath)
        if not self.filePath in self.preferences.recentMacros and not self._isTempMacro:
          self.preferences.recentMacros.append(self.filePath)

      self.filePath = self._createTemporaryFile()
      self._saveTextToFile(self.filePath)
      self._pythonConsole._runMacro(self.filePath)
      self._deleteTempMacro(self.filePath)
    else:
      MessageDialog.showWarning('', 'No Console available')


  def _saveMacro(self):
    """
    Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
    appears for specification of the file path.
    """

    if not self.filePath:
      print('No Path, This was a temp macro ')
      self._saveMacroAs()

    if self._originalOpenedFile:
      if self._getFileNameFromPath(self._originalOpenedFile) != self.nameLineEdit.get():
        print('Same file but different name',self._originalOpenedFile, self.nameLineEdit.get())
        self._saveMacroAs()
      else:
        self._saveTextToFile(self._originalOpenedFile)

  def _macroNameChanged(self):
    if self.filePath:
      if self.nameLineEdit.get() is not '':
        self.filePath = self.filePath.replace(self._getFileNameFromPath(self.filePath), self.nameLineEdit.get())
        self._saveMacro()



  def _deleteTempMacro(self, filePath):
    if os.path.exists(filePath):
      os.remove(filePath)
      self.filePath = None
    else:
      getLogger().debug("Trying to remove a temporary Macro file which does not exist")

  def saveToPdf(self):
    self.textBox.saveToPDF()

  def _saveTextToFile(self, filePath):
    if filePath:
      with open(filePath, 'w') as f:
        f.write(self.textBox.toPlainText())
        f.close()

  def _saveMacroAs(self):
    """
    Opens a save file dialog and saves the text inside the textbox to a file specified in the dialog.
    """

    newText = self.textBox.toPlainText()
    dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                        acceptMode=FileDialog.AcceptSave,selectFile=self.nameLineEdit.text(),
                        directory=self.macroPath, filter='*.py')
    filePath = dialog.selectedFile()

    if filePath:
      if not filePath.endswith('.py'):
        filePath+='.py'
      with open(filePath, 'w') as f:
        f.write(newText)
        f.close()

    if filePath:
      self.nameLineEdit.set(self._getFileNameFromPath(filePath))
      self.filePath = filePath

  def _openMacroFile(self):
    """
    Opens a file dialog box at the macro path specified in the application preferences and loads the
    contents of the macro file into the textbox.
    """

    dialog = FileDialog(self, text='Open Macro', fileMode=FileDialog.ExistingFile,
                        acceptMode=FileDialog.AcceptOpen, directory=self.macroPath,
                        filter='*.py')

    filePath = dialog.selectedFile()
    self._openPath(filePath)
    self._setFileName(filePath)


  def _openPath(self, filePath):

    if filePath:
      if filePath.endswith('.py'):
        with open(filePath, 'r') as f:
          self.textBox.clear()
          for line in f.readlines():
            self.textBox.insertPlainText(line)
          self.macroFile = f
          self.filePath = filePath
          self._originalOpenedFile = filePath
          self._isTempMacro = False
      else:
        MessageDialog.showMessage('Format Not Recognised', 'On MacroEditor you can drop only a *.py file type')

  def _setFileName(self, filePath):

    fileName = self._getFileNameFromPath(filePath)
    self.nameLineEdit.set(str(fileName))

  def _getFileNameFromPath(self, filePath):
    if isinstance(filePath,str):
      if filePath.endswith('.py'):
        path = filePath.split('/')
        fileName = path[-1].split('.')[0]
        return fileName



if __name__ == '__main__':
  from PyQt5 import QtGui, QtWidgets
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
  from ccpn.ui.gui.widgets.CheckBox import EditableCheckBox, CheckBox




  app = TestApplication()
  win = QtWidgets.QMainWindow()

  moduleArea = CcpnModuleArea(mainWindow=None)

  module = MacroEditor(mainWindow=None)


  moduleArea.addModule(module)

  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % module.moduleName)
  win.show()


  app.start()
  win.close()

