from PySide import QtGui, QtCore

from pyqtgraph.dockarea import Dock

from ccpn import Spectrum

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

  firstPpm, lastPpm = spectrum.getDimValueFromPoint(spectrumDim, region)

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
      spectrumView = self.getWrapperObject(spectrumDisplay._wrappedData.findFirstSpectrumView(dataSource=spectrum._wrappedData))
      for strip in spectrumView.strips:
        strip.displaySpectrum(spectrum)
      self.dockArea.guiWindow.removeBlankDisplay()

