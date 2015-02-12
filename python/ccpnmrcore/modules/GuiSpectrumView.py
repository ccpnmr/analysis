"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from PySide import QtCore, QtGui

from OpenGL import GL

from ccpncore.util.Colour import Colour
from ccpnmrcore.Base import Base as GuiBase

import pyqtgraph as pg

#from ccpnmrcore.modules.spectrumPane.PeakListItem import PeakListItem
#from ccpnmrcore.modules.spectrumPane.IntegralListItem import IntegralListItem

# this class mixes both OpenGL and Qt functionality
# it's a Qt QGraphicsItem because that means can re-order drawing of spectra peaks easily
# and it also allows turning on and off of a spectrum easily
# it also used OpenGL for drawing contours (ND) or lines (1D)

# abstract class: subclass needs to implement drawSpectrum()
class GuiSpectrumView(QtGui.QGraphicsItem, GuiBase):  # abstract class

  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
  def __init__(self):
    """ spectrumPane is the parent
        spectrum is the Spectrum object
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    
    QtGui.QGraphicsItem.__init__(self)
    GuiBase.__init__(self, self._project._appBase)
    
    self.apiDataSource = self._wrappedData.dataSource
    self.spectrum = self._parent # Is this necessary?
    
    ###self.setDimMapping(dimMapping)
    self.peakListItems = {} # CCPN peakList -> Qt peakListItem

    
    """
    for peakList in spectrum.peakLists:
      self.peakListItems[peakList.pid] = PeakListItem(self, peakList)
"""      
    # guiSpectrumDisplay.spectrumItems.append(self)

  def boundingRect(self):  # seems necessary to have

    return QtCore.QRectF(-1000, -1000, 1000, 1000)  # TBD: remove hardwiring
    
  """
  def setDimMapping(self, dimMapping=None):
    
    dimensionCount = self.spectrum.dimensionCount
    if dimMapping is None:
      dimMapping = {}
      for i in range(dimensionCount):
        dimMapping[i] = i
    self.dimMapping = dimMapping

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
  """
