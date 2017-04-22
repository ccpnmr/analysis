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

  def __init__(self, parent, project, name='Notes Editor', note=None):
    CcpnModule.__init__(self, name=name)
    widget = QtGui.QWidget()
    self._appBase = project._appBase
    self.project = project
    self.parent = parent
    self.parent.addModule(self)
    self.textBox = TextEditor()
    self.note = note
    widgetLayout = QtGui.QGridLayout()
    widget.setLayout(widgetLayout)
    self.label1 = Label(self, text='Note name')
    self.lineEdit1 = LineEdit(self)
    widget.layout().addWidget(self.label1, 1, 0)
    widget.layout().addWidget(self.lineEdit1, 1, 1, 1, 4)
    widget.layout().addWidget(self.textBox, 2, 0, 1, 5)
    if note:
      self.textBox.setText(note.text)
      self.lineEdit1.setText(self.note.name)
    self.buttonBox = ButtonList(self, texts=['Save', 'Cancel'],
                                callbacks=[self._saveNote, self._reject])
    widget.layout().addWidget(self.buttonBox, 3, 3, 1, 2)
    self.processText = self._processText
    self.layout.addWidget(widget)

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

