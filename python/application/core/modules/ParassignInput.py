from PyQt4 import QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Spinbox import Spinbox


class ParassignInput(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(ParassignInput, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    label1a = Label(self, text="Structure", grid=(1, 0))
    pulldownlist1a = PulldownList(self, grid=(1, 1))
    label2a = Label(self, text="Experimental PCS", grid=(2, 0))
    listwidget2a = ListWidget(self, grid=(2, 1), gridSpan=(1, 3))
    for peakList in project.peakLists:
      listwidget2a.addItem(str(peakList.pid))
    label3a = Label(self, text="Mutant 1:", grid=(3, 0))
    lineedit3a = LineEdit(self, grid=(3, 1))
    label3b = Label(self, text="Mutant 1:", grid=(3, 2))
    lineedit3b = LineEdit(self, grid=(3, 3))
    label4a = Label(self, text="Xax 1", grid=(4, 0))
    lineedit4a = LineEdit(self, grid=(4, 1))
    label4b = Label(self, text="Xrh 1", grid=(4, 2))
    lineedit4b = LineEdit(self, grid=(4, 3))
    label5a = Label(self, text="Xax minimum 1", grid=(5, 0))
    lineedit5a = LineEdit(self, grid=(5, 1))
    label5b = Label(self, text="Xax maximum 1", grid=(5, 2))
    lineedit5b = LineEdit(self, grid=(5, 3))
    label6a = Label(self, text="Xrh minimum 1", grid=(6, 0))
    doublespinbox6a = DoubleSpinbox(self, grid=(6, 1))
    label6b = Label(self, text="Xrh maximum 1", grid=(6, 2))
    doublespinbox6b = DoubleSpinbox(self, grid=(6, 3))
    label7a = Label(self, text="threshold 1", grid=(7, 0))
    doublespinbox7a = DoubleSpinbox(self, grid=(7, 1))
    label7b = Label(self, text="threshold 1", grid=(7, 2))
    doublespinbox7b = DoubleSpinbox(self, grid=(7, 3))
    label8a = Label(self, text="steps", grid=(8, 0))
    spinbox8a = Spinbox(self, grid=(8, 1))
    label8b = Label(self, text="Iterations", grid=(8, 2))
    spinbox8b = Spinbox(self, grid=(8, 3))
    label9a = Label(self, text="Bound? ", grid=(9, 0))
    pulldownlist9a = PulldownList(self, grid=(9, 1))
    label9b = Label(self, text="Search", grid=(9, 2))
    pulldownlist9b = PulldownList(self, grid=(9, 3))
    label10a = Label(self, text="cutoff distance", grid=(10, 0))
    doublespinbox10a = DoubleSpinbox(self, grid=(10, 1))
    label10b = Label(self, text="B0", grid=(10, 2))
    doublespinbox10b = DoubleSpinbox(self, grid=(10, 3))
    label11a = Label(self, text="S", grid=(11, 0))
    doublespinbox11a = DoubleSpinbox(self, grid=(11, 1))
    label11b = Label(self, text="correlation time", grid=(11, 2))
    doublespinbox11b = DoubleSpinbox(self, grid=(11, 3))
    label12a = Label(self, text="Save JSON config", grid=(12, 0))
    button12a = Button(self, grid=(12, 1))
    label12b = Label(self, text="PARAssign", grid=(12, 2))
    button12b = Button(self, grid=(12, 3))
