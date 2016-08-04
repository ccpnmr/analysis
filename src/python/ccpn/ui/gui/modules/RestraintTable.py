__author__ = 'simon1'

from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from PyQt4 import QtGui, QtCore


class RestraintTable(CcpnModule):
  def __init__(self, parent=None, restraintLists=None, name='Distance Restraint Table', **kw):

    if not restraintLists:
      restraintLists = []

    CcpnModule.__init__(self, name=name)

    self.restraintLists = restraintLists

    # label = Label(self, "Chemical Shift List:")
    # self.layout.addWidget(label, 0, 0)
    label = Label(self, "Restraint List:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.chemicalShiftListPulldown, 0, 1)
    self.layout.addWidget(widget1, 0, 0)

    columns = [('#', '_key'),
               ('Atoms', lambda restraint: self._getContributions(restraint)),
               ('Target Value.', 'targetValue'),
               ('Upper Limit', 'upperLimit'),
               ('Lower Limit', 'lowerLimit'),
               ('Error', 'error'),
               ('Peaks', lambda restraint: '%3d ' % self._getRestraintPeakCount(restraint))
               # ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
               ]

    tipTexts = ['Atom Pid',
                'Value of chemical shift',
                'Standard deviation of chemical shift',
                'Standard deviation of chemical shift',
                'Standard deviation of chemical shift',
                'Standard deviation of chemical shift',
                # 'Number of peaks associated with this ChemicalShiftList that are assigned to this '
                'NmrAtom'
                ]

    self.chemicalShiftTable = GuiTableGenerator(self, restraintLists,
                                                actionCallback=self._callback, columns=columns,
                                                selector=self.chemicalShiftListPulldown,
                                                tipTexts=tipTexts)

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.chemicalShiftTable, 3, 0, 1, 4)

  def _getContributions(self, restraint):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    return ' - '.join(restraint.restraintContributions[0].restraintItems[0])


  def _getRestraintPeakCount(self, restraint):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    import random
    peaks = restraint.peaks
    return random.randint(0, 15)

  def _callback(self):
    pass
