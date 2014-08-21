from PySide import QtCore, QtGui

from OpenGL import GL

from ccpncore.util.Color import Color
from ccpnmrcore.Base import Base

import pyqtgraph as pg

from ccpnmrcore.modules.spectrumPane.PeakListItem import PeakListItem
from ccpnmrcore.modules.spectrumPane.IntegralListItem import IntegralListItem

# this class mixes both OpenGL and Qt functionality
# it's a Qt QGraphicsItem because that means can re-order drawing of spectra peaks easily
# and it also allows turning on and off of a spectrum easily
# it also used OpenGL for drawing contours (ND) or lines (1D)

# abstract class: subclass needs to implement drawSpectrum()
class SpectrumItem(QtGui.QGraphicsItem, Base):  # abstract class

  def __init__(self, spectrumPane, spectrum, dimMapping=None):
    """ spectrumPane is the parent
        spectrum is the Spectrum object
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    
    QtGui.QGraphicsItem.__init__(self)
    Base.__init__(self, spectrumPane.project)
        
    self.spectrumPane = spectrumPane
    self.spectrum = spectrum
    self.setDimMapping(dimMapping)
    
    self.peakListItems = {} # CCPN peakList -> Qt peakListItem
    """
    for peakList in spectrum.peakLists:
      self.peakListItems[peakList.pid] = PeakListItem(self, peakList)
"""      
    spectrumPane.spectrumItems.append(self)

  def boundingRect(self):  # seems necessary to have

    return QtCore.QRectF(-1000, -1000, 1000, 1000)  # TBD: remove hardwiring
    
  def setDimMapping(self, dimMapping=None):
    
    spectrum = self.spectrum
    
    if dimMapping is None:
      dimMapping = {}
      for i in range(spectrum.dimensionCount):
        dimMapping[i] = i
            
    self.dimMapping = dimMapping
    dimensionCount = spectrum.dimensionCount

    xDim = yDim = None
    inverseDimMapping = {}
    for dim in dimMapping:
      inverseDim = dimMapping[dim]
      if inverseDim == 0:
        xDim = inverseDim
      elif inverseDim == 1:
        yDim = inverseDim
    
    if xDim is not None: 
      assert 0 <= xDim < dimensionCount, 'xDim = %d, dimensionCount = %d' % (xDim, dimensionCount)
      
    if yDim is not None:
      assert 0 <= yDim < dimensionCount, 'yDim = %d, dimensionCount = %d' % (yDim, dimensionCount)
      assert xDim != yDim, 'xDim = yDim = %d' % xDim
    
    self.xDim = xDim
    self.yDim = yDim

