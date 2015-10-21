__author__ = 'simon'

from ccpn.lib.Assignment import CCP_CODES

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.lib.assignment.ChemicalShift import getCcpCodeData
from ccpncore.util.Colour import spectrumHexColours
import pyqtgraph as pg

class ReferenceChemicalShifts(CcpnDock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, project, dockArea):


    CcpnDock.__init__(self, name='Reference Chemical Shifts')

    self.plotWidget = pg.PlotWidget()
    dockArea.addDock(self)
    self.project = project
    self.addWidget(self.plotWidget, 1, 0, 1, 4)
    self.plotWidget.plotItem.addLegend(offset=[-30, 30])

    dataSets = ('Ala')

    self.residueTypeLabel = Label(self, "Residue Type")
    self.addWidget(self.residueTypeLabel, 0, 0)
    self.residueTypePulldown = PulldownList(self, callback=self.updateModule)
    self.residueTypePulldown.setData(CCP_CODES)
    self.addWidget(self.residueTypePulldown, 0, 1)
    self.atomTypeLabel = Label(self, 'Atom Type')
    self.addWidget(self.atomTypeLabel, 0, 2)
    self.atomTypePulldown = PulldownList(self, callback=self.updateModule)
    self.atomTypePulldown.setData(['Hydrogen', 'Heavy'])
    self.addWidget(self.atomTypePulldown, 0, 3)
    self.updateModule()


  def getDistributionForResidue(self, ccpCode, atomType):

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

  def updateModule(self, item=None):
    self.plotWidget.clear()
    self.plotWidget.plotItem.legend.items = []
    self.plotWidget.grid.show()
    atomType = self.atomTypePulldown.currentText()
    ccpCode = self.residueTypePulldown.currentText()
    dataSets = self.getDistributionForResidue(ccpCode, atomType)
    for atomName, dataSet in dataSets.items():
      self.plotWidget.plot(dataSet[0], dataSet[1], pen=dataSet[2], name=atomName, kargs={'clear':True})
