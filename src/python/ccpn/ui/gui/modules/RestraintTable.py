__author__ = 'simon1'

from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from PyQt4 import QtGui, QtCore


class RestraintTable(CcpnModule):
  def __init__(self, parent=None, restraintLists=None, name='Restraint Table', **kw):

    CcpnModule.__init__(self, name=name)

    project = kw.get('project')

    if not restraintLists:
      if project is None:
        restraintLists = []
      else:
        restraintLists = project.restraintLists

    self.restraintLists = restraintLists

    label = Label(self, "Restraint List:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.restraintListPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.restraintListPulldown, 0, 1)
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

    tipTexts = ['Restraimt Id',
                'Atoms involved in the restraint',
                'Target value for the restraint',
                'Upper limit for the restraint',
                'Lower limitf or the restraint',
                'Error on the restraint',
                'Number of peaks used to derive this restraint '
                ]

    self.restraintTable = GuiTableGenerator(self, restraintLists,
                                                actionCallback=self._callback, columns=columns,
                                                selector=self.restraintListPulldown,
                                                tipTexts=tipTexts)

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.restraintTable, 3, 0, 1, 4)

  def _getContributions(self, restraint):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    if restraint.restraintContributions[0].restraintItems:
      return ' - '.join(restraint.restraintContributions[0].restraintItems[0])


  def _getRestraintPeakCount(self, restraint):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    peaks = restraint.peaks
    if peaks:
      return len(peaks)
    else:
      return 0

  def _callback(self):
    pass
