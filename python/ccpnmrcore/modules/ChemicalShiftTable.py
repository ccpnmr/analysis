__author__ = 'simon1'

from pyqtgraph.dockarea import Dock

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator


class ChemicalShiftTable(CcpnDock):

  def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Lists', **kw):

    if not chemicalShiftLists:
      chemicalShiftLists = []

    CcpnDock.__init__(self, name=name)

    self.chemicalShiftLists = chemicalShiftLists

    label = Label(self, "Chemical Shift List")
    self.layout.addWidget(label, 0, 0)

    self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1))

    columns = [('#', '_key'), ('atom', 'nmrAtom'), ('atom type', lambda shift: shift.nmrAtom.name), ('shift', 'value')]

    tipTexts = ['atom key', 'name of NmrAtom', 'Atom Type', 'value of chemical shift']

    self.chemicalShiftTable = GuiTableGenerator(self, chemicalShiftLists, callback=None, columns=columns, selector=self.chemicalShiftListPulldown, tipTexts=tipTexts)

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.chemicalShiftTable, 3, 0, 1, 4)