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

import datetime
import os

class MacroEditor(CcpnModule):
  """
  This module will create a python file which can be run from a console.
  A file will be created in the temporary  macro directory .ccpn/macros
  and will be automatically saved every changes on the text editor.
  The user can decide to save as a new file location.



  If a file is specified when open the module, than only that file will be opened.

  Saving is automatically done every changes on the text editor.
  The macro name is the file name on the disk (without the .py extension).
  If the name is changed from the module, also the file name is automatically changed.

  When opening a restored module, the saved macro will be re-opened .

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
    self.macroPath = None #self.preferences.general.userMacroPath

    self.mainWidget.layout().setSpacing(5)
    self.mainWidget.layout().setContentsMargins(10,10,10,10)

    hGrid = 0
    self.namelabel = Label(self.mainWidget, 'Macro Name', grid=(hGrid,0))
    self.nameLineEdit = LineEdit(self.mainWidget,  grid=(0,1))
    # self.nameLineEdit.editingFinished().connect(self._changedName)

    hGrid +=1
    # macro editing area
    self.textBox = TextEditor(self.mainWidget, grid=(hGrid,0), gridSpan=(1,2))


    hGrid +=1
    self.buttonBox = ButtonList(self, texts=['Open', 'Save As', 'Run'],
                                callbacks=[self._openMacroFile, self._saveMacroAs, self._runMacro], grid = (hGrid,1))

    # ghost Widget to restore a macro when opening a saved project  which had the macroEditor opened
    self._pathLineEdit = LineEdit(self.mainWidget, grid=(hGrid, 0))
    self._pathLineEdit.hide()



    self.filePath = filePath
    if self.filePath: # if  a path is specified then opens it
      self._openPath(self.filePath)

    else: # otherwise it creates a temp file.
      self._createTemporaryFile()

    self._setFileName(self.filePath)


    self.textBox.editingFinished.connect(self._saveMacro)  # automatic saving
    self.nameLineEdit.editingFinished.connect(self._macroNameChanged)  # automatic renaming the fileName

  def restoreWidgetsState(self, **widgetsState):
    super(MacroEditor, self).restoreWidgetsState(**widgetsState)
    if self._pathLineEdit.get() is not '' or None:
      self._openPath(self._pathLineEdit.get())


  def _createTemporaryFile(self):
    dateTime = datetime.datetime.now().strftime("%y-%m-%d-%H:%M:%S")
    fileName = 'Macro'+dateTime
    filePath = self.application.tempMacrosPath + '/'+ fileName
    if filePath:
      if not filePath.endswith('.py'):
        filePath+='.py'
      with open(filePath, 'w') as f:
        f.write('')
        f.close()
    self.filePath = filePath
    self._pathLineEdit.setText(self.filePath)


  def _runMacro(self):
    if self._pythonConsole is not None:
      if self.filePath:
        self._pythonConsole._runMacro(self.filePath)
      else:
        MessageDialog.showWarning('', 'No file found. Save the macro first')

  def _saveMacro(self):
    """
    Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
    appears for specification of the file path.
    """

    if self._pathLineEdit.get():
      self.filePath = self._pathLineEdit.get()
      if  self.filePath:
        with open(self.filePath, 'w') as f:
          f.write(self.textBox.toPlainText())
          f.close()

  def _macroNameChanged(self):
    if self.filePath:
      if self.nameLineEdit.get() is not '':
        self.filePath = self.filePath.replace(self._getFileNameFromPath(self.filePath), self.nameLineEdit.get())
        self._pathLineEdit.setText(self.filePath )
        self._saveMacro()




  def _saveMacroAs(self):
    """
    Opens a save file dialog and saves the text inside the textbox to a file specified in the dialog.
    """

    # macroPath = self.preferences.general.userMacroPath or None
    # colourScheme = self.preferences.general.colourScheme
    newText = self.textBox.toPlainText()
    dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                        acceptMode=FileDialog.AcceptSave,selectFile=self.nameLineEdit.text(),
                        directory=None, filter='*.py')
    filePath = dialog.selectedFile()

    if filePath:
      if not filePath.endswith('.py'):
        filePath+='.py'
      with open(filePath, 'w') as f:
        f.write(newText)
        f.close()
    self.filePath = filePath
    self._pathLineEdit.setText(self.filePath)
    self.nameLineEdit.set(self._getFileNameFromPath(filePath))

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
      with open(filePath, 'r') as f:
        self.textBox.clear()
        for line in f.readlines():
          self.textBox.insertPlainText(line)
        self.macroFile = f
        self.filePath = filePath
        self._pathLineEdit.setText(self.filePath)

  def _setFileName(self, filePath):

    fileName = self._getFileNameFromPath(filePath)
    self.nameLineEdit.set(str(fileName))

  def _getFileNameFromPath(self, filePath):
    if isinstance(filePath,str):
      if filePath.endswith('.py'):
        path = filePath.split('/')
        fileName = path[-1].split('.')[0]
        return fileName






  # def _startMacroRecord(self):
  #   """
  #   Starts recording of a macro from commands performed in the software and output to the console.
  #   """
  #   self.mainWindow.recordingMacro = True
  #   self.buttonBox.buttons[1].setEnabled(True)
  #   self.buttonBox.buttons[0].setDisabled(True)
  #   self.mainWindow.editor = self
  #
  #
  # def _stopMacroRecord(self):
  #   """
  #   Stops macro recording.
  #   """
  #   self.mainWindow.recordingMacro = False
  #   self.buttonBox.buttons[1].setDisabled(True)
  #   self.buttonBox.buttons[0].setEnabled(True)
  #   del self.mainWindow.editor



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

