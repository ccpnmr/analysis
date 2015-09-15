__author__ = 'simon1'

from ccpncore.gui.Button import Button
from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.popups.SelectDisplaysPopup import SelectDisplaysAndSpectraPopup

from ccpnmrcore.lib.Window import navigateToPeakPosition

class PickAndAssignModule(CcpnDock, Base):

  def __init__(self, parent=None, project=None):

    CcpnDock.__init__(self, parent=None, name='Pick And Assign')
    spacingLabel = Label(self)
    spacingLabel.setFixedHeight(15)
    self.layout.addWidget(spacingLabel, 0, 1, 1, 1)

    self.displayButton = Button(self, text='Select Modules', callback=self.showDisplayPopup)
    self.layout.addWidget(self.displayButton, 1, 0, 1, 1)
    self.restrictedPickButton = Button(self, text='Restricted Pick', callback=self.restrictedPick)
    self.layout.addWidget(self.restrictedPickButton, 1, 2, 1, 1)

    self.project = project
    self.current = project._appBase.current
    self.peakTable = PeakListSimple(self, project=project, callback=self.goToPositionInModules)
    self.layout.addWidget(spacingLabel, 2, 1, 1, 1)

    self.layout.addWidget(self.peakTable, 4, 0, 1, 4)

    # parent.window().showAtomSelector()

  def restrictedPick(self):
    position = self.selectedPeak.position
    peak = self.selectedPeak
    axisCodes = self.selectedPeak.peakList.spectrum.axisCodes

    for module in self.project.spectrumDisplays:
      if len(module.strips[0].orderedAxes) > 2:
        for spectrumView in module.strips[0].spectrumViews:
          selectedRegion = [['']*3, ['']*3]

          for moduleAxisCode in spectrumView.spectrum.axisCodes:

            if moduleAxisCode in axisCodes:
              index = axisCodes.index(moduleAxisCode)
              index2 = spectrumView.spectrum.axisCodes.index(moduleAxisCode)
              selectedRegion[0][index2] = position[index]-spectrumView.spectrum.assignmentTolerances[index]
              selectedRegion[1][index2] = position[index]+spectrumView.spectrum.assignmentTolerances[index]
            else:
              index3 = spectrumView.spectrum.axisCodes.index(moduleAxisCode)

              selectedRegion[0][index3] = spectrumView.strip.orderedAxes[index3].region[0]
              selectedRegion[1][index3] = spectrumView.strip.orderedAxes[index3].region[1]

          peakList = spectrumView.spectrum.peakLists[0]
          if spectrumView.spectrum.dimensionCount > 1:
            apiSpectrumView = spectrumView._wrappedData
            newPeaks = peakList.pickPeaksNd(selectedRegion, apiSpectrumView.spectrumView.orderedDataDims,
                                            doPos=True,
                                            doNeg=True)
            for peak in newPeaks:
              peak.isSelected = True
            for strip in module.strips:
              strip.showPeaks(peakList)


  def goToPositionInModules(self, peak=None, row=None, col=None):
    navigateToPeakPosition(self.project, peak,  markPositions=True)
    self.selectedPeak = peak


  def showDisplayPopup(self):
    popup = SelectDisplaysAndSpectraPopup(self, project=self.project, dim=2)
    popup.show()


