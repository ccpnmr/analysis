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
          
  ##### functions used externally #####

  # implements superclass function
  def addSpectrum(self, spectrumVar, region=None, dimMapping=None):
    
    spectrumItem = SpectrumNdItem(self, spectrumVar, region, dimMapping)
    self.scene().addItem(spectrumItem)
