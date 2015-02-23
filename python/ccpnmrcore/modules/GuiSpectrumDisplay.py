__author__ = 'simon'

import importlib, os

from PySide import QtGui, QtCore

from ccpn.lib.wrapper import Spectrum as LibSpectrum

from ccpncore.gui.Label import Label
from ccpncore.gui.ToolBar import ToolBar
from ccpn.lib.wrapper import Spectrum as LibSpectrum

from ccpnmrcore.gui.Frame import Frame as GuiFrame
from ccpnmrcore.modules.GuiModule import GuiModule

def _findPpmRegion(spectrum, axisDim, spectrumDim):

  pointCount = spectrum.pointCounts[spectrumDim]
  if axisDim < 2: # want entire region
    region = (0, pointCount)
  else:
    n = pointCount // 2
    region = (n, n+1)

  firstPpm, lastPpm = LibSpectrum.getDimValueFromPoint(spectrum, spectrumDim, region)

  return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)


class GuiSpectrumDisplay(GuiModule):

  def __init__(self):
    GuiModule.__init__(self)

    self.guiStrips = []
    self.spectrumToolBar = ToolBar(self.dock, grid=(0, 0), gridSpan=(1, 2))
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    screenWidth  = QtGui.QApplication.desktop().screenGeometry().width()
    # self.spectrumToolBar.setMaximumWidth(screenWidth*0.6)
    self.hLines = []
    self.vLines = []
    self.spectrumUtilToolBar = ToolBar(self.dock, grid=(0, 2), gridSpan=(1, 1))
    # self.spectrumUtilToolBar.setMinimumWidth(screenWidth*0.15)
    toolBarColour = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumUtilToolBar.palette())
    palette2 = QtGui.QPalette(self.spectrumToolBar.palette())
    palette.setColor(QtGui.QPalette.Button,toolBarColour)
    palette2.setColor(QtGui.QPalette.Button,toolBarColour)

    self.positionBox = Label(self.dock, grid=(0, 3), gridSpan=(1, 1))
    self.positionBox.setFixedWidth(screenWidth*0.08)
    self.stripFrame = GuiFrame(self.dock, appBase=self._appBase, grid=(1, 0), gridSpan=(1, 3))

    self.stripFrame.guiSpectrumDisplay = self
    # self.dock.addWidget(self.stripFrame)
    #
    #
    # for n, apiStrip in enumerate(apiSpectrumDisplay.sortedStrips()):   ### probably need orderedStrips() here ?? ask Rasmus
    #   className = apiStrip.className
    #   classModule = importlib.import_module('ccpnmrcore.modules.Gui' + className)
    #   clazz = getattr(classModule, 'Gui'+className)
    #   guiStrip = clazz(self.stripFrame, apiStrip)

    # self.currentStrip = apiSpectrumDisplay.sortedStrips()[0].guiStrip

  def fillToolBar(self):

    self.spectrumUtilToolBar.addAction('+', self.addStrip)
    self.spectrumUtilToolBar.addAction('-', self.removeStrip)


  def addSpectrumToDisplay(self, spectrum):

    spectrumView = self.getWrapperObject(self._wrappedData.findFirstSpectrumView(dataSource=spectrum._wrappedData))

    dimensionCount = spectrum.dimensionCount
    dimensionOrdering = range(1, dimensionCount+1)
    apiSpectrumDisplay = self._wrappedData
    if apiSpectrumDisplay.axes:
      for m, axisCode in enumerate(apiSpectrumDisplay.axisCodes):
        position, width = _findPpmRegion(spectrum, m, dimensionOrdering[m]-1) # -1 because dimensionOrdering starts at 1
        for n, strip in enumerate(spectrumView.strips):
          if m == 1: # Y direction
            if n == 0:
              axis = apiSpectrumDisplay.findFirstAxis(code=axisCode)
              axis.position = position
              axis.width = width
          else: # other directions
            axis = apiSpectrumDisplay.findFirstAxis(code=axisCode)
            axis.position = position
            axis.width = width

          viewBox = strip.viewBox
          region = (position-0.5*width, position+0.5*width)
          if m == 0:
            viewBox.setXRange(*region)
          elif m == 1:
            viewBox.setYRange(*region)

    else: # need to create these since not done automatically (or are they now?)
      # TBD: assume all strips the same and the strip direction is the Y direction
      for m, axisCode in enumerate(apiSpectrumDisplay.axisCodes):
        position, width = _findPpmRegion(spectrum, m, dimensionOrdering[m]-1) # -1 because dimensionOrdering starts at 1
        for n, strip in enumerate(spectrumView.strips):
          if m == 1: # Y direction
            if n == 0:
              apiSpectrumDisplay.newFrequencyAxis(code=axisCode, position=position, width=width, stripSerial=1)
          else: # other directions
            apiSpectrumDisplay.newFrequencyAxis(code=axisCode, position=position, width=width, stripSerial=1) # TBD: non-frequency axis; TBD: should have stripSerial=0 but that not working

          viewBox = strip.viewBox
          region = (position-0.5*width, position+0.5*width)
          if m == 0:
            viewBox.setXRange(*region)
          elif m == 1:
            viewBox.setYRange(*region)

    for strip in spectrumView.strips:
      strip.displaySpectrum(spectrumView)

  def addStrip(self):
    pass  # TBD: should raise exception if not implemented in subclass


  def removeStrip(self):
    pass

  def zoomYAll(self):
    self.currentStrip.zoomYAll()

  def zoomXAll(self):
    self.currentStrip.zoomXAll()

  def restoreZoom(self):
    self.currentStrip.restoreZoom()

  def storeZoom(self):
    self.currentStrip.storeZoom()
    
    