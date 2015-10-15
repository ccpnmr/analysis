__author__ = 'simon1'

from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.Menu import MenuBar
from ccpncore.gui.TextEditor import TextEditor

from ccpnmrcore.DropBase import DropBase

from PyQt4 import QtGui


class NotesEditor(DropBase, CcpnDock):

  def __init__(self, parent, note, name, item=None):
    CcpnDock.__init__(self, name=name)
    widget = QtGui.QWidget()
    self._appBase = note.project._appBase
    self.parent = parent
    self.parent.addDock(self)
    self.textBox = TextEditor()
    self.note = note
    self.item = item
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
    self.lineEdit1.editingFinished.connect(self.setNoteName)
    widget.layout().addWidget(self.textBox, 2, 0, 1, 5)
    # if self.note.text is not None:
    self.textBox.setText(note.text)
    self.lineEdit1.setText(self.note.name)
    self.buttonBox = ButtonList(self, texts=['Close', 'Save Note'], callbacks=[self.reject, self.saveNote])
    widget.layout().addWidget(self.buttonBox, 3, 3, 1, 2)
    self.layout.addWidget(widget)

  def setNoteName(self):
    self.note.rename(self.lineEdit1.text())

  def saveNote(self):
    newText = self.textBox.toPlainText()
    self.note.text = newText
    self.item.setText(0, self.note.pid)


    self.close()

  def reject(self):
    self.close()
