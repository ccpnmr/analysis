__author__ = 'simon1'

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from application.core.modules.GuiTableGenerator import GuiTableGenerator
from PyQt4 import QtGui, QtCore


class ChemicalShiftTable(CcpnDock):

  def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Lists', **kw):

    if not chemicalShiftLists:
      chemicalShiftLists = []

    CcpnDock.__init__(self, name=name)

    self.chemicalShiftLists = chemicalShiftLists

    # label = Label(self, "Chemical Shift List:")
    # self.layout.addWidget(label, 0, 0)
    label = Label(self, "Chemical Shift List:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.chemicalShiftListPulldown, 0, 1)
    self.layout.addWidget(widget1, 0, 0)
    # if callback is None:
    #   callback=self.selectPeak

    columns = [('#', '_key'),
               ('Shift', lambda chemicalShift: '%8.3f' % chemicalShift.value),
               ('Std. Dev.', lambda chemicalShift: ('%6.3f' % chemicalShift.valueError
               if chemicalShift.valueError else '   0   ')),
               ('Peak count', lambda chemicalShift: '%3d ' % self.getShiftPeakCount(chemicalShift))
              ]

    tipTexts = ['Atom Pid',
                'Value of chemical shift',
                'Standard deviation of chemical shift',
                'Number of peaks associated with this ChemicalShiftList that are assigned to this NmrAtom']

    self.chemicalShiftTable = GuiTableGenerator(self, chemicalShiftLists,
                                                actionCallback=self.callback, columns=columns,
                                                selector=self.chemicalShiftListPulldown,
                                                tipTexts=tipTexts)

    newLabel = Label(self, '', grid=(2, 0))

    self.layout.addWidget(self.chemicalShiftTable, 3, 0, 1, 4)

  def getShiftPeakCount(self, chemicalShift):
    """return number of peaks assigned to NmrAtom in Experiments and PakLists
    using ChemicalShiftList"""
    chemicalShiftList = chemicalShift.chemicalShiftList
    peaks = chemicalShift.nmrAtom.assignedPeaks()
    return (len(set(x for x in peaks
                    if x.peakList.chemicalShiftList is chemicalShiftList)))


  def callback(self):
    pass

