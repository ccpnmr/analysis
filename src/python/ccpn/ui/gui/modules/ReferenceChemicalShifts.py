__author__ = 'simon'

import pyqtgraph as pg

from ccpn.core.lib.Assignment import CCP_CODES
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.util.Colour import spectrumHexColours
from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import getCcpCodeData

class ReferenceChemicalShifts(CcpnModule): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, project, moduleArea):


    CcpnModule.__init__(self, name='Reference Chemical Shifts')

    self.plotWidget = pg.PlotWidget()
    moduleArea.addModule(self)
    self.project = project
    self.addWidget(self.plotWidget, 1, 0, 1, 4)
    self.plotWidget.plotItem.addLegend(offset=[1, 10])
    self.residueTypeLabel = Label(self, "Residue Type")
    self.addWidget(self.residueTypeLabel, 0, 0)
    self.residueTypePulldown = PulldownList(self, callback=self._updateModule)
    self.residueTypePulldown.setData(CCP_CODES)
    self.addWidget(self.residueTypePulldown, 0, 1)
    self.atomTypeLabel = Label(self, 'Atom Type')
    self.addWidget(self.atomTypeLabel, 0, 2)
    self.atomTypePulldown = PulldownList(self, callback=self._updateModule)
    self.atomTypePulldown.setData(['Hydrogen', 'Heavy'])
    self.addWidget(self.atomTypePulldown, 0, 3)
    self._updateModule()


  def _getDistributionForResidue(self, ccpCode:str, atomType:str):
    """
    Takes a ccpCode and an atom type (Hydrogen or Heavy) and returns a dictionary of lists
    containing the chemical shift distribution for each atom of the specified type in the residue
    """
    dataSets = {}
    ccpData = getCcpCodeData(self.project._apiNmrProject, ccpCode, molType='protein', atomType=atomType)

    atomNames = list(ccpData.keys())

    for atomName in atomNames:
      distribution = ccpData[atomName].distribution
      refPoint = ccpData[atomName].refPoint
      refValue = ccpData[atomName].refValue
      valuePerPoint = ccpData[atomName].valuePerPoint
      x = []
      y = []
      colour = spectrumHexColours[atomNames.index(atomName)]
      for i in range(len(distribution)):
        x.append(refValue+valuePerPoint*(i-refPoint))
        y.append(distribution[i])
      dataSets[atomName] = [x, y, colour]

    return dataSets

  def _updateModule(self, item=None):
    """
    Updates the information displayed in the module when either the residue type or the atom type
    selectors are changed.
    """
    self.plotWidget.clear()
    self.plotWidget.plotItem.legend.items = []
    self.plotWidget.showGrid(x=True, y=True)
    atomType = self.atomTypePulldown.currentText()
    ccpCode = self.residueTypePulldown.currentText()
    dataSets = self._getDistributionForResidue(ccpCode, atomType)
    for atomName, dataSet in dataSets.items():
      self.plotWidget.plot(dataSet[0], dataSet[1], pen=dataSet[2], name=atomName, kargs={'clear':True})
