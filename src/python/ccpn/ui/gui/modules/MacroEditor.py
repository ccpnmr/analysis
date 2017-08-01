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
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

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

  def __init__(self, mainWindow=None, name='Macro Editor', showRecordButtons=False):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    self.preferences = self.application.preferences

    # macro selection
    self.label1 = Label(self, 'Macro Name')
    self.lineEdit1 = LineEdit(self)
    self.button = Button(self, text='Select...', callback=self._openMacroFile, vPolicy='fixed')

    # macro editing area
    self.textBox = TextEditor()

    # layouts
    #widget = QtGui.QWidget()
    widget = self.mainWidget
    widgetLayout = QtGui.QGridLayout()
    widget.setLayout(widgetLayout)
    widget.layout().setSpacing(5)
    widget.layout().setContentsMargins(10,10,10,10)
    widget.layout().addWidget(self.label1,    0, 0, 1, 1)
    widget.layout().addWidget(self.lineEdit1, 0, 1, 1, 3)
    widget.layout().addWidget(self.button,    0, 4, 1, 1)
    widget.layout().addWidget(self.textBox,   1, 0, 1, 5)

    self.buttonBox = ButtonList(self, texts=['Start', 'Stop', 'Close', 'Save Macro'],
                                callbacks=[self._startMacroRecord, self._stopMacroRecord, self._reject, self._saveMacro])
#    buttonLayout = QtGui.QGridLayout()
#    self.buttonBox.setLayout(buttonLayout)
#    self.buttonBox.layout().setSpacing(0)

    self.buttonBox.buttons[1].setDisabled(True)
    self.buttonBox.buttons[0].setEnabled(True)
    widget.layout().addWidget(self.buttonBox, 2, 3, 1, 2)

#    self.layout().setSpacing(1)
#    self.layout.addWidget(widget)

    if showRecordButtons is False:
      self.buttonBox.buttons[0].hide()
      self.buttonBox.buttons[1].hide()


  def _saveMacro(self):
    """
    Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
    appears for specification of the file path.
    """
    if self.lineEdit1.text() == '':
      self._saveMacroAs()
    else:
      with open(self.lineEdit1.text(), 'w') as f:
        f.write(self.textBox.toPlainText())
        f.close()

    # newText = self.textBox.toPlainText()
    # self.macroFile.write(newText)

  def _saveMacroAs(self):
    """
    Opens a save file dialog and saves the text inside the textbox to a file specified in the dialog.
    """
    macroPath = self.preferences.general.userMacroPath
    # colourScheme = self.preferences.general.colourScheme
    newText = self.textBox.toPlainText()
    dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                        acceptMode=FileDialog.AcceptSave, preferences=self.preferences.general,
                        directory=macroPath, filter='*.py')
    filePath = dialog.selectedFile()
    if filePath:
      with open(filePath, 'w') as f:
        f.write(newText)
        f.close()

  def _openMacroFile(self):
    """
    Opens a file dialog box at the macro path specified in the application preferences and loads the
    contents of the macro file into the textbox.
    """
    macroPath = self.preferences.general.userMacroPath
    dialog = FileDialog(self, text='Open Macro', fileMode=FileDialog.ExistingFile,
                        acceptMode=FileDialog.AcceptOpen, directory=macroPath,
                        preferences=self.preferences.general, filter='*.py')

    filePath = dialog.selectedFile()
    if filePath:
      with open(filePath, 'r') as f:
        self.textBox.clear()
        for line in f.readlines():
          self.textBox.insertPlainText(line)
        self.macroFile = f

      self.lineEdit1.setText(filePath)

  def _startMacroRecord(self):
    """
    Starts recording of a macro from commands performed in the software and output to the console.
    """
    self.mainWindow.recordingMacro = True
    self.buttonBox.buttons[1].setEnabled(True)
    self.buttonBox.buttons[0].setDisabled(True)


  def _stopMacroRecord(self):
    """
    Stops macro recording.
    """
    self.mainWindow.recordingMacro = False
    self.buttonBox.buttons[1].setDisabled(True)
    self.buttonBox.buttons[0].setEnabled(True)

  def _reject(self):
    self.close()

