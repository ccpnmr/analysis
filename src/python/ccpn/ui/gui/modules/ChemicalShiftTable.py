__author__ = 'simon1'

from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from PyQt4 import QtGui, QtCore


class ChemicalShiftTable(CcpnModule):
  def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Table', **kw):

    if not chemicalShiftLists:
      chemicalShiftLists = []

    CcpnModule.__init__(self, name=name)

    self.chemicalShiftLists = chemicalShiftLists

    label = Label(self, "Chemical Shift List:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.chemicalShiftListPulldown, 0, 1)
    self.layout.addWidget(widget1, 0, 0)

    columns = [('#', '_key'),
               ('Shift', lambda chemicalShift: '%8.3f' % chemicalShift.value),
               ('Std. Dev.', lambda chemicalShift: ('%6.3f' % chemicalShift.valueError
                                                    if chemicalShift.valueError else '   0   ')),
               ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
               ]

    tipTexts = ['Atom Pid',
                'Value of chemical shift',
                'Standard deviation of chemical shift',
                'Number of peaks associated with this ChemicalShiftList that are assigned to this '
                'NmrAtom']

    self.chemicalShiftTable = GuiTableGenerator(self, chemicalShiftLists,
                                                actionCallback=self._callback, columns=columns,
                                                selector=self.chemicalShiftListPulldown,
                                                tipTexts=tipTexts, objectType='chemicalShifts')

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.chemicalShiftTable, 3, 0, 1, 4)

  def _getShiftPeakCount(self, chemicalShift):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    chemicalShiftList = chemicalShift.chemicalShiftList
    peaks = chemicalShift.nmrAtom.assignedPeaks
    return (len(set(x for x in peaks
                    if x.peakList.chemicalShiftList is chemicalShiftList)))

  def _callback(self, obj, row, col):
    pass


class NmrAtomShiftTable(ChemicalShiftTable):
  """Alternative proposal to the ChemicalShiftTable"""

  def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Table', **kw):

    if not chemicalShiftLists:
      chemicalShiftLists = []

    CcpnModule.__init__(self, name=name)

    self.chemicalShiftLists = chemicalShiftLists

    label = Label(self, "Chemical Shift List:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.chemicalShiftListPulldown, 0, 1)
    self.layout.addWidget(widget1, 0, 0)

    # # Temporary - for testing
    # label1 = Label(self, 'Show from all ChemicalShiftLists? Yes/No')
    # self.layout.addWidget(label1, 0, 2, QtCore.Qt.AlignRight)

    columns = [('#', lambda chemicalShift: chemicalShift.nmrAtom.serial),
               ('NmrResidue', lambda chemicalShift: chemicalShift._key.rsplit('.', 1)[0]),
               ('Name', lambda chemicalShift: chemicalShift._key.rsplit('.', 1)[-1]),
               ('Shift', lambda chemicalShift: '%8.3f' % chemicalShift.value),
               ('Std. Dev.', lambda chemicalShift: ('%6.3f' % chemicalShift.valueError
                                                    if chemicalShift.valueError else '   0   ')),
               ('Shift list peaks',
                lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift)),
               ('All peaks',
                lambda chemicalShift: '%3d ' % len(set(x for x in
                                                       chemicalShift.nmrAtom.assignedPeaks))
                )
               ]

    tipTexts = ['NmrAtom serial number',
                'NmrResidue Id',
                'NmrAtom name',
                'Value of chemical shift, in selected ChemicalShiftList',
                'Standard deviation of chemical shift, in selected ChemicalShiftList',
                'Number of peaks assigned to this NmrAtom in PeakLists associated with this '
                'ChemicalShiftList',
                'Number of peaks assigned to this NmrAtom across all PeakLists']

    self.chemicalShiftTable = GuiTableGenerator(self, chemicalShiftLists,
                                                actionCallback=self._callback, columns=columns,
                                                selector=self.chemicalShiftListPulldown,
                                                tipTexts=tipTexts, objectType='chemicalShifts')
    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.chemicalShiftTable, 3, 0, 1, 4)

  def _callback(self, obj, row, col):

    if obj: # should presumably always be the case
      chemicalShift = obj
      chemicalShift.project._appBase.current.nmrAtom = chemicalShift.nmrAtom
      chemicalShift.project._appBase.current.nmrResidue = chemicalShift.nmrAtom.nmrResidue

