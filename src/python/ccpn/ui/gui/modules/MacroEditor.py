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


class MacroEditor(CcpnModule):

  includeSettingsWidget = False
  className = 'MacroEditor'

  def __init__(self, mainWindow=None, name='Macro Editor', filePath=None):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    if mainWindow:
      self.mainWindow = mainWindow
      self.application = mainWindow.application
      self.project = mainWindow.application.project
      self.current = mainWindow.application.current
      self.preferences = self.application.preferences

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
    self.buttonBox = ButtonList(self, texts=['Open', 'Save', 'Run'],
                                callbacks=[self._openMacroFile, self._saveMacro, None], grid = (hGrid,1))

   # if  a path is specified then open it
    self.filePath = filePath

    if self.filePath:

      self._openPath(filePath)
      self._setFileName(filePath)


  # def _changedName(self):
  #   print()




  def _saveMacro(self):
    """
    Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
    appears for specification of the file path.
    """
    if self.nameLineEdit.get() == self._getFileNameFromPath(self.filePath):
      with open(self.filePath, 'w') as f:
        f.write(self.textBox.toPlainText())
        f.close()
    else:
      self._saveMacroAs()



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

  def _setFileName(self, filePath):

    fileName = self._getFileNameFromPath(filePath)
    self.nameLineEdit.set(str(fileName))

  def _getFileNameFromPath(self, filePath):
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

  module = MacroEditor(mainWindow=None, filePath='/Users/luca/Desktop/tqqt.py')


  moduleArea.addModule(module)

  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % module.moduleName)
  win.show()


  app.start()
  win.close()

