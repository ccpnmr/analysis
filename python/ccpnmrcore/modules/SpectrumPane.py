import operator

from PySide import QtCore, QtGui, QtOpenGL

from ccpnmrcore.modules.Base import Base
from ccpnmrcore.modules.spectrumPane.SpectrumScene import SpectrumScene

# this allows combining of OpenGL and ordinary Qt drawing
# the pre-calculated OpenGL is done in the drawPre() function
# then the Qt scene is drawn (presumably it's in the "Item" layer)
# then the on-the-fly Qt is drone in the drawPost() function
# both drawPre() and drawPost() are called from the scene code
# most drawing happens automatically because of Qt
# only the OpenGL needs to be called explicitly

# abstract class: subclass needs to implement addSpectrum()
class SpectrumPane(QtGui.QGraphicsView, Base):
  
  def __init__(self, project, parent, spectraVar=None, region=None, dimMapping=None, **kw):
    
    QtGui.QGraphicsView.__init__(self, parent)
    Base.__init__(self, project, **kw)
    
    if spectraVar is None:
      spectraVar = []
      
    self.setViewport(QtOpenGL.QGLWidget()) # this allows combining of OpenGL and ordinary Qt drawing
    
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate) # recommended for OpenGL usage
    # When any visible part of the scene changes or is reexposed, QGraphicsView will update the entire viewport
    
    self.setScene(SpectrumScene(self)) # the scene initiates the drawing
      
    self.setSpectra(spectraVar, region, dimMapping)
    
  ##### functions used externally #####

  def clearSpectra(self):
    
    self.spectrumItems = []
    self.region = None
    self.dimMapping = None
        
  def addSpectrum(self, spectrumVar, region=None, dimMapping=None):
    
    raise Exception('should be implemented in subclass')
      
  def setSpectra(self, spectraVar, region=None, dimMapping=None):
    
    self.clearSpectra()
    for spectrumVar in spectraVar:
      self.addSpectrum(spectrumVar, region, dimMapping)

  ##### functions called from SpectrumScene #####
    
  # can be overridden (so implemented) in subclass
  # meant for OpenGL drawing
  def drawPre(self, painter, rect):

    pass

  # can be overridden (so implemented) in subclass
  # meant for on-the-fly (so not scene-related) Qt drawing
  def drawPost(self, painter, rect):

    pass



  
  