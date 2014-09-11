"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
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
