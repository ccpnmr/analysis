from PySide import QtCore, QtGui

from OpenGL import GL

from ccpncore.util.Color import Color

# this class mixes both OpenGL and Qt functionality
# it's a Qt QGraphicsItem because that means can re-order drawing of spectra peaks easily
# and it also allows turning on and off of a spectrum easily
# it also used OpenGL for drawing contours (ND) or lines (1D)

# abstract class: subclass needs to implement drawSpectrum()
class SpectrumItem(QtGui.QGraphicsItem):  # abstract class

  def __init__(self, spectrumPane, spectrumVar, region=None, dimMapping=None):
    """ spectrumPane is the parent
        spectrumVar is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    
    QtGui.QGraphicsItem.__init__(self)
    self.setFlag(QtGui.QGraphicsItem.ItemHasNoContents, True)
    
    ###spectrum = self.getById(spectrumVar)
    # below TEMP, waiting for wrapper model
    spectrum = spectrumVar
    
    #if region is None:
    #  region = spectrum.defaultRegion(dimMapping)
    
    self.spectrumPane = spectrumPane
    self.spectrum = spectrum
    self.region = region
    self.setDimMapping(dimMapping)
    
    self.peakListItems = {} # CCPN peakList -> Qt peakListItem
    
    for peakList in spectrum.peakLists:
      self.peakListItems[peakList] = PeakListItem(self, peakList)
    
    spectrumPane.spectrumItems.append(self)

  def setDimMapping(self, dimMapping):
    
    self.dimMapping = dimMapping
    xDim = yDim = None
    if dimMapping:
      inverseDimMapping = {}
      for dim in self.dimMapping:
        inverseDim = dimMapping[dim]
        if inverseDim == 0:
          xDim = inverseDim
        elif inversedim == 1:
          yDim = inverseDime
    
    dimCount = self.spectrum.dimCount
    if xDim is not None: 
      assert 0 <= xDim < dimCount, 'xDim = %d, dimCount = %d' % (xDim, dimCount)
      
    if yDim is not None:
      assert 0 <= yDim < dimCount, 'yDim = %d, dimCount = %d' % (yDim, dimCount)
      assert xDim != yDim, 'xDim = yDim = %d' % xDim
    
    self.xDim = xDim
    self.yDim = yDim

  def drawSpectrum(self, painter, rect):
    
    raise Exception('should be implemented in subclass')
    
  # any attribute not known about is checked first int the parent and then in the spectrum
  def __getattr__(self, attr):

    if hasattr(self.parent, attr):
      return getattr(self.parent, attr)
    elif hasattr(self, spectrum, attr)
      return getattr(self.spectrum, attr)
      
    raise AttributeError("%s instance has no attribute '%s'" % (self.__class__.__name__, attr))

