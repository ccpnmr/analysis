from PySide import QtGui, QtCore

from pyqtgraph.dockarea import Dock

from ccpn import Spectrum
from ccpn.lib.wrapper import Spectrum as LibSpectrum

from ccpncore.gui.Label import Label

from ccpnmrcore.gui.Frame import Frame as GuiFrame
from ccpnmrcore.DropBase import DropBase
# from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay


def _findPpmRegion(spectrum, axisDim, spectrumDim):

  pointCount = spectrum.pointCounts[spectrumDim]
  if axisDim < 2: # want entire region
    region = (0, pointCount)
  else:
    n = pointCount // 2
    region = (n, n+1)

  firstPpm, lastPpm = LibSpectrum.getDimValueFromPoint(spectrum, spectrumDim, region)

  return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)

class GuiBlankDisplay(DropBase, Dock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, dockArea):
    
    self.dockArea = dockArea
    
    Dock.__init__(self, name='BlankDisplay', size=(1100,1300))
    dockArea.addDock(self)
    
    DropBase.__init__(self, dockArea.guiWindow._appBase, self.dropCallback)
    
    self.label = Label(self, text='Drag Spectrum Here', grid=(0, 0))

  def dropCallback(self, dropObject):
    
    if isinstance(dropObject, Spectrum):
      spectrum = dropObject
      spectrumDisplay = self.dockArea.guiWindow.createSpectrumDisplay(spectrum)
      spectrumDisplay.addSpectrumToDisplay(spectrum)
      # spectrumView = self.getWrapperObject(spectrumDisplay._wrappedData.findFirstSpectrumView(dataSource=spectrum._wrappedData))
      #
      # dimensionCount = spectrum.dimensionCount
      # dimensionOrdering = range(1, dimensionCount+1)
      # apiSpectrumDisplay = spectrumDisplay._wrappedData
      # if apiSpectrumDisplay.axes:
      #   for m, axisCode in enumerate(apiSpectrumDisplay.axisCodes):
      #     position, width = _findPpmRegion(spectrum, m, dimensionOrdering[m]-1) # -1 because dimensionOrdering starts at 1
      #     for n, strip in enumerate(spectrumView.strips):
      #       if m == 1: # Y direction
      #         if n == 0:
      #           axis = apiSpectrumDisplay.findFirstAxis(code=axisCode)
      #           axis.position = position
      #           axis.width = width
      #       else: # other directions
      #         axis = apiSpectrumDisplay.findFirstAxis(code=axisCode)
      #         axis.position = position
      #         axis.width = width
      #
      #       viewBox = strip.viewBox
      #       region = (position-0.5*width, position+0.5*width)
      #       if m == 0:
      #         viewBox.setXRange(*region)
      #       elif m == 1:
      #         viewBox.setYRange(*region)
      #
      # else: # need to create these since not done automatically (or are they now?)
      #   # TBD: assume all strips the same and the strip direction is the Y direction
      #   for m, axisCode in enumerate(apiSpectrumDisplay.axisCodes):
      #     position, width = _findPpmRegion(spectrum, m, dimensionOrdering[m]-1) # -1 because dimensionOrdering starts at 1
      #     for n, strip in enumerate(spectrumView.strips):
      #       if m == 1: # Y direction
      #         if n == 0:
      #           apiSpectrumDisplay.newFrequencyAxis(code=axisCode, position=position, width=width, stripSerial=1)
      #       else: # other directions
      #         apiSpectrumDisplay.newFrequencyAxis(code=axisCode, position=position, width=width, stripSerial=1) # TBD: non-frequency axis; TBD: should have stripSerial=0 but that not working
      #
      #       viewBox = strip.viewBox
      #       region = (position-0.5*width, position+0.5*width)
      #       if m == 0:
      #         viewBox.setXRange(*region)
      #       elif m == 1:
      #         viewBox.setYRange(*region)
      #
      # for strip in spectrumView.strips:
      #   strip.displaySpectrum(spectrumView)
      self.dockArea.guiWindow.removeBlankDisplay()
      return spectrumDisplay

