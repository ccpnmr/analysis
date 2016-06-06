__author__ = 'simon1'

from PyQt4 import QtGui, QtCore

from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList



class NmrResidueTable(QtGui.QWidget, Base):

  def __init__(self, parent=None, project=None, callback=None, **kw):

    # if not nmrChains:
    #   nmrChains = []

    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.project = project
    self.nmrChains = project.nmrChains

    label = Label(self, "NmrChain:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.nmrChainPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.nmrChainPulldown, 0, 1)
    self.layout().addWidget(widget1, 0, 0)

    columns = [('#', lambda nmrResidue: nmrResidue.serial),
               ('NmrChain', lambda nmrResidue: nmrResidue._parent.id),
               ('Sequence','sequenceCode'),
               # ('Sequence',lambda nmrResidue: '%-8s' % nmrResidue.sequenceCode),
               ('Type', 'residueType'),
               ('NmrAtoms', lambda nmrResidue: self._getNmrAtoms(nmrResidue)),
               ('Peak count', lambda nmrResidue: '%3d ' % self._getNmrResiduePeaks(nmrResidue))]

    tipTexts = ['NmrResidue serial number', 'Nmr Residue key',
                'Sequence code of NmrResidue',  'Type of NmrResidue',
                'Atoms in NmrResidue', 'Number of peaks assigned to Nmr Residue']

    self.nmrResidueTable = GuiTableGenerator(self, self.project.nmrChains, actionCallback=callback, columns=columns,
                                             selector=self.nmrChainPulldown, tipTexts=tipTexts, objectType='nmrResidues',
                                             selectionCallback=self._setNmrResidue)

    self.layout().addWidget(self.nmrResidueTable, 1, 0, 1, 6)


  def _getNmrAtoms(self, nmrResidue):
    return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms]),
                            key=CcpnSorting.stringSortKey))

  def _getNmrResiduePeaks(self, nmrResidue):
    l1 = [peak for atom in nmrResidue.nmrAtoms for peak in atom.assignedPeaks]
    return len(set(l1))

  def _setNmrResidue(self, nmrResidue, row, col):
    self.project._appBase.current.nmrResidue = nmrResidue


