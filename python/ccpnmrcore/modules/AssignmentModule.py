from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator

class AssignmentModule(CcpnDock, Base):
  def __init__(self, parent=None, project=None, peaks=None, **kw):

    CcpnDock.__init__(self, name="Assignment Module")

    Base.__init__(self, **kw)

    dimensionCount = len(peaks[0].dimensionNmrAtoms)
    self.chemicalShiftList = peaks[0].peakList.spectrum.chemicalShiftList

    self.listWidgets = []
    self.objectTables = []
    for i in range(dimensionCount):
      shift = peaks[0].position[i]
      for residue in project.nmrResidues:
        for atom in residue.atoms:
          if shift-0.02 < self.chemicalShiftList.findChemicalShift(atom).value < shift+0.02:
            print(atom)
      listWidget = ListWidget(self)
      self.listWidgets.append((listWidget, [i, 0, 1, 1]))
      columns = [('#', 'serial'), ('name', lambda peak, i: self.getPeakName(peak, i)),
                  ('Delta', 'volume'),
       ('SD', 'figureOfMerit'), ('Distance', 'height')]
      tipTexts = ['','','','','']

      objectTable = GuiTableGenerator(self, self.project.peakLists, callback=None, columns=columns, tipTexts=tipTexts,
                                      selector=None, tipTexts=tipTexts)
      # objectTable = PeakListSimple(self, peakLists=project.peakLists, callback=None, grid=(i, 1))

      self.objectTables.append((objectTable, [i, 1, 1, 3]))

    for listWidget in self.listWidgets:
      self.layout.addWidget(listWidget[0], *listWidget[1])

    for objectTable in self.objectTables:
      self.layout.addWidget(objectTable[0], *objectTable[1])



  def getPeakName(self, peak, dim):
    if peak.dimensionNmrAtoms[dim].name is not None:
      return peak.dimensionNmrAtoms[dim].name
    else:
      return None

  # self.chemicalShiftList.fetchChemicalShift(peaks[0].dimensionNmrAtoms[i]).value-peaks[0].position[i]