__author__ = 'simon1'

from pyqtgraph.dockarea import Dock

from ccpncore.gui.DockLabel import DockLabel
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator


class ChemicalShiftTable(Dock):

  def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Lists', **kw):

    if not chemicalShiftLists:
      chemicalShiftLists = []

    Dock.__init__(self, name=name)

    self.label.hide()
    self.label = DockLabel(name, self)
    self.label.show()

    self.chemicalShiftLists = chemicalShiftLists

    label = Label(self, "Chemical Shift List")
    self.layout.addWidget(label, 0, 0)

    self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1))

    columns = [('#', '_key'), ('atom', 'nmrAtom'), ('atom type', lambda shift: shift.nmrAtom.name), ('shift', 'value')]

    self.chemicalShiftTable = GuiTableGenerator(self, chemicalShiftLists, callback=None, columns=columns, selector=self.chemicalShiftListPulldown)

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.chemicalShiftTable, 3, 0, 1, 4)