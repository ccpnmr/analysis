__author__ = 'simon1'

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.Label import Label


class ExperimentFilterPopup(QtGui.QDialog, Base):
  def __init__(self, spectrum=None, parent=None, **kw):
    super(ExperimentFilterPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    detectionBox = GroupBox(self, grid=(0, 0), gridSpan=(1, 4))
    filterBox = GroupBox(self, grid=(1, 0), gridSpan=(2, 4))
    selectionBox = GroupBox(self, grid=(3, 0), gridSpan=(1, 4))

    # filter by detection nucleus
    self.cCheckBox = CheckBox(detectionBox, grid=(0, 0), hAlign='r')
    cLabel = Label(detectionBox, text='C-detected', grid=(0, 1), hAlign='l')
    self.hCheckBox = CheckBox(detectionBox, grid=(0, 2), hAlign='r')
    hLabel = Label(detectionBox, text='H-detected', grid=(0, 3), hAlign='l')
    self.nCheckBox = CheckBox(detectionBox, grid=(0, 4), hAlign='r')
    nLabel = Label(detectionBox, text='N-detected', grid=(0, 5), hAlign='l')

    # filter by transfer technique
    self.simpleCheckBox = CheckBox(filterBox, grid=(0, 0))
    simpleLabel = Label(filterBox, grid=(0, 1), hAlign='l', text='simple')
    self.aromaticCheckBox = CheckBox(filterBox, grid=(0, 2))
    aromaticLabel = Label(filterBox, grid=(0, 3), hAlign='l', text='aromatic')
    self.jTransferCheckBox = CheckBox(filterBox, grid=(0, 4))
    jTransferLabel = Label(filterBox, grid=(0, 5), hAlign='l', text='J-transfer')
    self.jMultibondCheckBox = CheckBox(filterBox, grid=(0, 6))
    jMultibondLabel = Label(filterBox, grid=(0, 7), hAlign='l', text='J-multibond')
    self.mqCheckBox = CheckBox(filterBox, grid=(1, 0))
    mqLabel = Label(filterBox, grid=(1, 1), hAlign='l', text='MQ')
    self.projectedCheckBox = CheckBox(filterBox, grid=(1, 2))
    projectedLabel = Label(filterBox, grid=(1, 3), hAlign='l', text='projected')
    self.relayedCheckBox = CheckBox(filterBox, grid=(1, 4))
    relayedLabel = Label(filterBox, grid=(1, 5), hAlign='l', text='relayed')
    self.throughSpaceCheckBox = CheckBox(filterBox, grid=(1, 6))
    throughSpaceLabel = Label(filterBox, grid=(1, 7), hAlign='l', text='through-space')


    experimentLabel = Label(selectionBox, text='experiment type', grid=(0, 0), hAlign='r')
    experimentPulldown = FilteringPulldownList(selectionBox, grid=(0, 1))

    self.experimentTypes = spectrum.project._experimentTypeMap
    axisCodes = []
    for isotopeCode in spectrum.isotopeCodes:
      axisCodes.append(''.join([char for char in isotopeCode if not char.isdigit()]))

    atomCodes = tuple(sorted(axisCodes))
    pulldownItems = list(self.experimentTypes[spectrum.dimensionCount].get(atomCodes).keys())

    experimentPulldown.setData(pulldownItems)

    self.buttonBox = ButtonList(self, grid=(4, 3), texts=['Close', 'Apply'],
                           callbacks=[self.reject, self._setExperimentType])


  def _setExperimentType(self, spectrum, atomCodes, item):
    expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(item)
    spectrum.experimentType = expType
