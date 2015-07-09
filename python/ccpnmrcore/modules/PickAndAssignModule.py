__author__ = 'simon1'


import pyqtgraph as pg

from pyqtgraph.dockarea import Dock

from PyQt4 import QtCore

import math

from ccpncore.gui.Button import Button
from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.popups.SelectDisplaysPopup import SelectDisplaysAndSpectraPopup

class PickAndAssignModule(CcpnDock, Base):

  def __init__(self, parent=None, project=None):

    CcpnDock.__init__(self, parent=None, name='Backbone Assignment')

    self.displayButton = Button(self, text='Select Modules', callback=self.showDisplayPopup)
    self.layout.addWidget(self.displayButton, 0, 0, 1, 1)
    self.restrictedPickButton = Button(self, text='Restricted Pick', callback=self.restrictedPick)
    self.layout.addWidget(self.restrictedPickButton, 0, 2, 1, 1)

    self.project = project
    self.current = project._appBase.current
    self.peakTable = PeakListSimple(self, peakLists=project.peakLists, callback=self.goToPositionInModules)
    self.layout.addWidget(self.peakTable, 2, 0, 1, 6)

    # print((parent.window()))
    parent.window().showAtomSelector()

  def restrictedPick(self):
    position = self.selectedPeak.position
    peak = self.selectedPeak
    axisCodes = self.selectedPeak.peakList.spectrum.axisCodes
    hdim = axisCodes.index('H')
    ndim = axisCodes.index('N')
    print(self.selectedPeak.position)
    for module in self.selectedDisplays:
      for spectrumView in module.strips[0].spectrumViews:
       if module.axisCodes[2] == 'N':
        selectedRegion = [[peak.position[hdim]-0.01, peak.position[ndim]-0.05],
                          [peak.position[hdim]+0.01, peak.position[ndim]+0.05]]
        peakList = spectrumView.spectrum.peakLists[0]
        if spectrumView.spectrum.dimensionCount > 1:
          print(spectrumView.strip.orderedAxes[1].region)
          selectedRegion[0].insert(1, spectrumView.strip.orderedAxes[1].region[0])
          selectedRegion[1].insert(1, spectrumView.strip.orderedAxes[1].region[1])
          print('selectedRegion',selectedRegion)
          apiSpectrumView = spectrumView._wrappedData
          newPeaks = peakList.findPeaksNd(selectedRegion, apiSpectrumView.spectrumView.orderedDataDims,
                                          doPos=apiSpectrumView.spectrumView.displayPositiveContours,
                                          doNeg=apiSpectrumView.spectrumView.displayNegativeContours)
          for peak in newPeaks:
            peak.isSelected = True
          for strip in module.strips:
            strip.showPeaks(peakList)
          # module.peaks = newPeaks


  def goToPositionInModules(self, peak=None, row=None, col=None):
    self.selectedPeak = peak
    axisCodes = peak.peakList.spectrum.axisCodes
    hdim = axisCodes.index('H')
    ndim = axisCodes.index('N')
    for module in self.selectedDisplays:
      print(module.axisCodes[2])
      if module.axisCodes[2] == 'N':
        module.orderedStrips[0].orderedAxes[2].position = peak.position[ndim]
        line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
        line.setPos(QtCore.QPointF(peak.position[hdim], 0))
        module.orderedStrips[0].plotWidget.addItem(line)
      elif module.axisCodes[2] == 'H':
        module.orderedStrips[0].orderedAxes[2].position = peak.position[hdim]
        line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
        line.setPos(QtCore.QPointF(peak.position[ndim], 0))
        module.orderedStrips[0].plotWidget.addItem(line)


      else:
        pass

      print(peak)

  def showDisplayPopup(self):
    popup = SelectDisplaysAndSpectraPopup(self, project=self.project, dim=3)
    popup.exec_()
