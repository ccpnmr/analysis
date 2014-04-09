from PySide import QtGui

# this allows combining of OpenGL and ordinary Qt drawing
# the pre-calculated OpenGL is done in the drawBackground() function
# then the Qt scene is drawn (presumably it's in the "Item" layer)
# then the on-the-fly Qt is drone in the drawForeground() function

class SpectrumScene(QtGui.QGraphicsScene):
  
  def __init__(self, spectrumPane):
    
    QtGui.QGraphicsScene.__init__(self)

    self.spectrumPane = spectrumPane
    
  # overrides QGraphicsScene implementation
  def drawBackground(self, painter, rect):
  
    self.spectrumPane.drawPre(painter, rect)
  
  # overrides QGraphicsScene implementation
  def drawForeground(self, painter, rect):

    self.spectrumPane.drawPost(painter, rect)
