__author__ = 'simon1'

from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.Menu import MenuBar
from ccpncore.gui.TextEditor import TextEditor

from application.core.DropBase import DropBase

from PyQt4 import QtGui


class NotesEditor(DropBase, CcpnDock):

  def __init__(self, parent, project, name='Notes Editor', note=None):
    CcpnDock.__init__(self, name=name)
    widget = QtGui.QWidget()
    self._appBase = project._appBase
    self.project = project
    self.parent = parent
    self.parent.addDock(self)
    self.textBox = TextEditor()
    self.note = note
    widgetLayout = QtGui.QGridLayout()
    widget.setLayout(widgetLayout)
    # self.menuBar = MenuBar(self)
    # self.menuBar.setNativeMenuBar(False)
    # self.fileMenu = self.menuBar.addMenu('File')
    # self.editMenu = self.menuBar.addMenu('Edit')
    self.label1 = Label(self, text='Note name')
    self.lineEdit1 = LineEdit(self)
    # widget.layout().addWidget(self.menuBar, 0, 0, 1, 5)
    widget.layout().addWidget(self.label1, 1, 0)
    widget.layout().addWidget(self.lineEdit1, 1, 1, 1, 4)
    # self.lineEdit1.editingFinished.connect(self._setNoteName)
    widget.layout().addWidget(self.textBox, 2, 0, 1, 5)
    # if self.note.text is not None:
    if note:
      self.textBox.setText(note.text)
      self.lineEdit1.setText(self.note.name)
    self.buttonBox = ButtonList(self, texts=['Close', 'Save Note'], callbacks=[self._reject, self._saveNote])
    widget.layout().addWidget(self.buttonBox, 3, 3, 1, 2)
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

  def processText(self, text, event):
    if not self.note:
      self.note = self.project.newNote()
    self.textBox.setText(text)
    self.overlay.hide()

