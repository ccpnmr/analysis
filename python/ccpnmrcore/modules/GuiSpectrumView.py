"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from PyQt4 import QtCore, QtGui

from ccpncore.util.Colour import Colour
from ccpnmrcore.Base import Base as GuiBase

import pyqtgraph as pg

#from ccpnmrcore.modules.spectrumPane.PeakListItem import PeakListItem
#from ccpnmrcore.modules.spectrumPane.IntegralListItem import IntegralListItem

class GuiSpectrumView(GuiBase, QtGui.QGraphicsItem):

  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
  def __init__(self):
    """ spectrumPane is the parent
        spectrum is the Spectrum object
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    
    QtGui.QGraphicsItem.__init__(self, scene=self.strip.plotWidget.scene())
    GuiBase.__init__(self, self._project._appBase)
    
    self.apiDataSource = self._wrappedData.spectrumView.dataSource
    ##self.spectrum = self._parent # Is this necessary?
    
    ###self.setDimMapping(dimMapping)
    self.peakListItems = {} # CCPN peakList -> Qt peakListItem

    # strip = self._parent
    # strip.setupAxes()
    
    """
    for peakList in spectrum.peakLists:
      self.peakListItems[peakList.pid] = PeakListItem(self, peakList)
"""      
    # guiSpectrumDisplay.spectrumItems.append(self)
    
    ##for strip in self.strips:
    ##  strip.addSpectrum(self)

  ##def boundingRect(self):  # seems necessary to have

  ##  return QtCore.QRectF(-1000, -1000, 1000, 1000)  # TBD: remove hardwiring
    
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
