__author__ = 'simon1'

from ccpncore.gui.Button import Button
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.FileDialog import FileDialog
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.TextEditor import TextEditor

from application.core.DropBase import DropBase

from PyQt4 import QtGui


class MacroEditor(DropBase, CcpnDock):

  def __init__(self, parent, mainWindow, name, showRecordButtons=False):
    CcpnDock.__init__(self, name=name)
    widget = QtGui.QWidget()
    self.parent = parent
    self.parent.addDock(self)
    self.preferences = mainWindow._appBase.preferences.general
    self.textBox = TextEditor()
    self.mainWindow = mainWindow
    widgetLayout = QtGui.QGridLayout()
    widget.setLayout(widgetLayout)
    self.label1 = Label(self, 'Macro Name')
    self.lineEdit1 = LineEdit(self)
    self.button = Button(self, '...', callback=self.openMacroFile)
    widget.layout().addWidget(self.label1, 0, 0, 1, 1)
    widget.layout().addWidget(self.lineEdit1, 0, 1, 1, 3)
    widget.layout().addWidget(self.button, 0, 4, 1, 1)
    widget.layout().addWidget(self.textBox, 2, 0, 1, 5)
    # if self.note.text is not None:
    self.buttonBox = ButtonList(self, texts=['Start', 'Stop', 'Close', 'Save Macro'],
            callbacks=[self.startMacroRecord, self.stopMacroRecord, self._reject, self.saveMacro])
    widget.layout().addWidget(self.buttonBox, 3, 3, 1, 2)
    self.layout.addWidget(widget)
    self.buttonBox.buttons[1].setDisabled(True)
    self.buttonBox.buttons[0].setEnabled(True)

    if showRecordButtons is False:
      self.buttonBox.buttons[0].hide()
      self.buttonBox.buttons[1].hide()


  def saveMacro(self):
    """
    Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
    appears for specification of the file path.
    """
    if self.lineEdit1.text() == '':
      self.saveMacroAs()
    else:
      with open(self.lineEdit1.text(), 'w') as f:
        f.write(self.textBox.toPlainText())
        f.close()

    # newText = self.textBox.toPlainText()
    # self.macroFile.write(newText)

  def saveMacroAs(self):
    """
    Opens a save file dialog and saves the text inside the textbox to a file specified in the dialog.
    """
    macroPath = self.preferences.macroPath
    colourScheme = self.preferences.colourScheme
    newText = self.textBox.toPlainText()
    filePath = FileDialog(self, text='Save Macro As...', acceptMode=1, fileMode=0, preferences=self.preferences,
                           directory=macroPath, selectedFilter='*.py')

    if not filePath:
      return

    with open(filePath, 'w') as f:
      f.write(newText)
      f.close()


  def openMacroFile(self):
    """
    Opens a file dialog box at the macro path specified in the application preferences and loads the
    contents of the macro file into the textbox.
    """
    macroPath = self.preferences.macroPath
    filePath = FileDialog(self, text='Open Macro', fileMode=1, acceptMode=0, directory=macroPath,
                          preferences=self.preferences)

    with open(filePath, 'r') as f:
      for line in f.readlines():
        self.textBox.insertPlainText(line)
      self.macroFile = f

    self.lineEdit1.setText(filePath)

  def startMacroRecord(self):
    """
    Starts recording of a macro from commands performed in the software and output to the console.
    """
    self.mainWindow.recordingMacro = True
    self.buttonBox.buttons[1].setEnabled(True)
    self.buttonBox.buttons[0].setDisabled(True)


  def stopMacroRecord(self):
    """
    Stops macro recording.
    """
    self.mainWindow.recordingMacro = False
    self.buttonBox.buttons[1].setDisabled(True)
    self.buttonBox.buttons[0].setEnabled(True)

  def _reject(self):
    self.close()

