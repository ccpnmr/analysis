#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:40 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
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
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor


class NotesEditor(CcpnModule):
  """
  This class implements the module by wrapping a StructureTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True

  className = 'NotesEditorModule'

  def __init__(self, parent, project=None, mainWindow=None, name='Notes Editor', note=None):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    if not mainWindow:
      self.mainWindow = mainWindow
      self.application = mainWindow.application
      self.project = mainWindow.application.project
      self.current = mainWindow.application.current

    # widget = QtGui.QWidget()
    self._appBase = project._appBase
    self.project = project
    # self.parent = parent
    # self.parent.addModule(self)
    self.note = note
    # widgetLayout = QtGui.QGridLayout()
    # widget.setLayout(widgetLayout)

    self.label1 = Label(self.mainWidget, text='Note name', grid=(1,0), vAlign='centre', hAlign='right')
    self.lineEdit1 = LineEdit(self.mainWidget, grid=(1,1), gridSpan=(1,2), vAlign='top')
    self.mainWidget.layout().addItem(QtGui.QSpacerItem(5, 5, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed), 2, 0, 1, 1)
    # self.mainWidget.layout().addItem(QtGui.QSpacerItem(5, 5, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed), grid=(2,0), gridSpan=(1,1))
    self.textBox = TextEditor(self.mainWidget, grid=(3,0), gridSpan=(1,7))

    # self.addWidget(self.label1, 1, 0)
    # self.addWidget(self.lineEdit1, 1, 1, 1, 4)
    # self.addWidget(self.textBox, 2, 0, 1, 5)

    if note:
      self.textBox.setText(note.text)
      self.lineEdit1.setText(self.note.name)

    self.buttonBox = ButtonList(self.mainWidget, texts=['Save', 'Cancel']
                                , callbacks=[self._saveNote, self._reject]
                                , grid=(4,5), gridSpan=(1,2))

    self.mainWidget.setContentsMargins(5, 5, 5, 5)
    self.processText = self._processText
    # self.layout.addWidget(widget)

  def _setNoteName(self):
    """
    Sets the name of the note based on the text in the Note name text box.
    """
    if not self.note:
      self.note = self.project.newNote(name=self.lineEdit1.text())
    self.note.rename(self.lineEdit1.text())

  def _saveNote(self):
    """
    Saves the text in the textbox to the note object.
    """
    newText = self.textBox.toPlainText()
    self._setNoteName()
    self.note.text = newText
    self.close()

  def _reject(self):
    """
    Closes the note editor ignoring all changes.
    """
    self.close()

  def _processText(self, text, event):
    if not self.note:
      self.note = self.project.newNote()
    self.textBox.setText(text)
    self.overlay.hide()

