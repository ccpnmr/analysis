from PyQt4 import QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.TextEditor import TextEditor

import sys

class LoadSequence(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(LoadSequence, self).__init__(parent)
    Base.__init__(self, **kw)

    self.project = project

    label2a = Label(self, text="Molecule Name", grid=(2, 0))
    moleculeName = LineEdit(self, text="", grid=(2, 1), gridSpan=(1, 1))
    label2b = Label(self, text="Molecule Type", grid=(2, 2))
    self.molTypePulldown = PulldownList(self, grid=(2, 3))
    molTypes = ['protein','DNA', 'RNA']
    self.molTypePulldown.setData(molTypes)
    label3a = Label(self, text="sequence", grid=(3, 0))
    self.sequenceEditor = TextEditor(self, grid=(3, 1), gridSpan=(1, 3))
    label4a = Label(self, 'Sequence Start', grid=(4, 0))
    lineEdit1a = Spinbox(self, grid=(4, 1), value=1, min=-100, max=1000000)
    label5a = Label(self, 'Chain code', grid=(4, 2))
    lineEdit2a = LineEdit(self, grid=(4, 3), text='A')

    buttonBox = ButtonList(self, grid=(6, 3), texts=['Cancel', 'Load Sequence'],
                           callbacks=[self.reject, self.loadSequence])
    self.sequenceStart = 1
    self.chainCode = 'A'
    # self.sequence = sequenceEditor.toPlainText()
    self.moleculeName = 'Molecule 1'
    moleculeName.textChanged.connect(self.setMoleculeName)
    lineEdit1a.valueChanged.connect(self.setSequenceStart)
    lineEdit2a.textChanged.connect(self.setChainCode)
    self.sequenceEditor.textChanged.connect(self.setSequence)

  def loadSequence(self):
    self.project.makeSimpleChain(sequence=self.sequence, compoundName=self.moleculeName,
                                 startNumber=self.sequenceStart, shortName=self.chainCode,
                                 molType=self.molTypePulldown.currentText())
    self.accept()

  def setSequenceStart(self, value):
    self.sequenceStart = int(value)

  def setChainCode(self, value):
    self.chainCode = value

  def setSequence(self):
    sequence = self.sequenceEditor.toPlainText()
    if not ' ' in sequence:
      self.sequence = self.sequenceEditor.toPlainText()
    else:
      self.sequence = tuple(sequence.split())
    # self.accept()

  def setMoleculeName(self, value):
    self.moleculeName = value


