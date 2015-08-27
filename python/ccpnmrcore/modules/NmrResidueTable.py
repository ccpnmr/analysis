__author__ = 'simon1'

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator

from ccpn.lib.windowUtil import navigateToNmrResidue


class NmrResidueTable(CcpnDock):

  def __init__(self, parent=None, project=None, name='Chemical Shift Lists', **kw):

    # if not nmrChains:
    #   nmrChains = []

    CcpnDock.__init__(self, name=name)
    self.project = project
    self.selectedDisplays = None
    self.nmrChains = project.nmrChains

    label = Label(self, "Nmr Chain" )
    self.layout.addWidget(label, 0, 0)

    self.nmrChainPulldown = PulldownList(self, grid=(0, 1))

    columns = [('#', lambda nmrResidue: self.getSequenceCode(nmrResidue)), ('Nmr Residue', '_key'),
               ('NmrAtoms', lambda nmrResidue: self.getNmrAtoms(nmrResidue)),
               ('Number of Peaks', lambda nmrResidue: self.getNmrResiduePeaks(nmrResidue))]

    tipTexts = ['Nmr Residue key', 'Name of NmrResidue', 'Atoms in NmrResidue',
                'Peaks assigned to Nmr Residue']

    self.nmrResidueTable = GuiTableGenerator(self, self.nmrChains, callback=self.navigateTo, columns=columns,
                                             selector=self.nmrChainPulldown, tipTexts=tipTexts)

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.nmrResidueTable, 3, 0, 1, 4)

  def getNmrAtoms(self, nmrResidue):
    return ', '.join([atom.name for atom in nmrResidue.atoms])

  def getNmrResiduePeaks(self, nmrResidue):
    return sum([len(atom.assignedPeaks) for atom in nmrResidue.atoms])

  def navigateTo(self, nmrResidue=None, row=None, col=None):

    navigateToNmrResidue(self.project, nmrResidue, selectedDisplays=self.selectedDisplays)

  def getSequenceCode(self, nmrResidue):
    try:
      return int(nmrResidue.sequenceCode)
    except ValueError:
      return nmrResidue.sequenceCode

