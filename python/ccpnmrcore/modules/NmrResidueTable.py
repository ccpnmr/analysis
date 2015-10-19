__author__ = 'simon1'

from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator



class NmrResidueTable(QtGui.QWidget, Base):

  def __init__(self, parent=None, project=None, callback=None, **kw):

    # if not nmrChains:
    #   nmrChains = []

    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.project = project
    self.nmrChains = project.nmrChains

    label = Label(self, "Nmr Chain", grid=(0, 0))

    self.nmrChainPulldown = PulldownList(self, grid=(0, 1))

    columns = [('#', lambda nmrResidue: self.getSequenceCode(nmrResidue)), ('Nmr Residue', '_key'),
               ('NmrAtoms', lambda nmrResidue: self.getNmrAtoms(nmrResidue)),
               ('Number of Peaks', lambda nmrResidue: self.getNmrResiduePeaks(nmrResidue))]

    tipTexts = ['Nmr Residue key', 'Name of NmrResidue', 'Atoms in NmrResidue',
                'Peaks assigned to Nmr Residue']

    self.nmrResidueTable = GuiTableGenerator(self, self.nmrChains, callback=callback, columns=columns,
                                             selector=self.nmrChainPulldown, tipTexts=tipTexts,
                                             selectionCallback=self.setNmrResidue)

    self.layout().addWidget(self.nmrResidueTable, 3, 0, 1, 4)


  def getNmrAtoms(self, nmrResidue):
    return ', '.join([atom.name for atom in nmrResidue.nmrAtoms])

  def getNmrResiduePeaks(self, nmrResidue):
    return sum([len(atom.assignedPeaks()) for atom in nmrResidue.nmrAtoms])

  def getSequenceCode(self, nmrResidue):
    try:
      return int(nmrResidue.sequenceCode)
    except ValueError:
      return nmrResidue.sequenceCode

  def setNmrResidue(self, nmrResidue, row, col):
    self.project._appBase.current.nmrResidue = nmrResidue
