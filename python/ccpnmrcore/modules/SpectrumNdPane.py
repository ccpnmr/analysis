import operator

from PySide import QtCore, QtGui, QtOpenGL

from ccpnmrcore.modules.SpectrumPane import SpectrumPane

from ccpnmrcore.modules.spectrumPane.SpectrumNdItem import SpectrumNdItem

class SpectrumNdPane(SpectrumPane):

  def __init__(self, *args, **kw):
    
    SpectrumPane.__init__(self, *args, **kw)

    self.plotItem.setAcceptDrops(True)
    
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)

    self.viewBox.invertX()
    self.viewBox.invertY()
      
    self.showGrid(x=True, y=True)
    self.region = None
          
  ##### functions used externally #####

  # overrides superclass function
  def clearSpectra(self):
    
    SpectrumPane.clearSpectra(self)    
    self.region = None
    
  # implements superclass function
  def addSpectrum(self, spectrumVar, dimMapping=None):
    
    spectrum = self.getObject(spectrumVar)
    if spectrum.dimensionCount < 1:
      # TBD: logger message
      return
      
    # TBD: check if dimensions make sense
      
    spectrumItem = SpectrumNdItem(self, spectrum, dimMapping, self.region)
    self.scene().addItem(spectrumItem)
