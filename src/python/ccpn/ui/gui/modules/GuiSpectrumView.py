"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:39 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtCore, QtGui

import collections

from ccpn.util import Colour
from ccpn.ui.gui.Base import Base as GuiBase

import pyqtgraph as pg

#from ccpn.ui.gui.modules.spectrumPane.PeakListItem import PeakListItem
#from ccpn.ui.gui.modules.spectrumPane.IntegralListItem import IntegralListItem

SpectrumViewParams = collections.namedtuple('SpectrumViewParams', ('valuePerPoint',
                                                                   'totalPointCount',
                                                                   'minAliasedFrequency',
                                                                   'maxAliasedFrequency',
                                                                   'dataDim'))

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

    self._apiDataSource = self._wrappedData.spectrumView.dataSource
    self.spectrumGroupsToolBar = None

    action = self.strip.spectrumDisplay.spectrumActionDict.get(self._apiDataSource)
    if action and not action.isChecked():
      self.setVisible(False)
      # below does not work so looks like we have a Qt / data model visibility sync issue
      #self._wrappedData.spectrumView.displayPositiveContours = self._wrappedData.spectrumView.displayNegativeContours = False

    ##self.spectrum = self._parent # Is this necessary?
    
    ###self.setDimMapping(dimMapping)
    #self.peakListItems = {} # CCPN peakList -> Qt peakListItem

    # strip = self._parent
    # strip.setupAxes()
    
    """
    for peakList in spectrum.peakLists:
      self.peakListItems[peakList.pid] = PeakListItem(self, peakList)
"""      
    # guiSpectrumDisplay.spectrumItems.append(self)
    
    ##for strip in self.strips:
    ##  strip.addSpectrum(self)

  def paint(self, painter, option, widget=None):

    pass
    
  def boundingRect(self):  # seems necessary to have

    return QtCore.QRectF(-1000, -1000, 1000, 1000)  # TBD: remove hardwiring

  # override of Qt setVisible
  def setVisible(self, visible):
    QtGui.QGraphicsItem.setVisible(self, visible)
    for peakListView in self.peakListViews:
      peakListView.setVisible(visible)

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

  def _getSpectrumViewParams(self, axisDim:int) -> tuple:
    """Get position, width, totalPointCount, minAliasedFrequency, maxAliasedFrequency
    for axisDimth axis (zero-origin)"""

    # axis = self.strip.orderedAxes[axisDim]
    dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[axisDim]
    totalPointCount = (dataDim.numPointsOrig if hasattr(dataDim, "numPointsOrig")
                       else dataDim.numPoints)
    for ii,dd in enumerate(dataDim.dataSource.sortedDataDims()):
      # Must be done this way as dataDim.dim may not be in order 1,2,3 (e.g. for projections)
      if dd is dataDim:
        minAliasedFrequency, maxAliasedFrequency = (self.spectrum.aliasingLimits)[ii]
        break
    else:
      minAliasedFrequency = maxAliasedFrequency = dataDim = None

    if hasattr(dataDim, 'primaryDataDimRef'):
      # FreqDataDim - get ppm valuePerPoint
      ddr = dataDim.primaryDataDimRef
      valuePerPoint = ddr and ddr.valuePerPoint
    elif hasattr(dataDim, 'valuePerPoint'):
      # FidDataDim - get time valuePerPoint
      valuePerPoint = dataDim.valuePerPoint
    else:
      # Sampled DataDim - return None
      valuePerPoint = None

    # return axis.position, axis.width, totalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim
    return SpectrumViewParams(valuePerPoint, totalPointCount,
                              minAliasedFrequency, maxAliasedFrequency, dataDim)

  def _getColour(self, colourAttr, defaultColour=None):

    colour = getattr(self, colourAttr)
    # if not colour:
    #   colour = getattr(self.spectrum, colourAttr)
      
    if not colour:
      colour = defaultColour

    colour = Colour.colourNameToHexDict.get(colour, colour)  # works even if None
      
    return colour

  def _spectrumViewHasChanged(self):
    """Change action icon colour and other changes when spectrumView changes

    NB SpectrumView change notifiers are triggered when either DataSource or ApiSpectrumView change"""
    spectrumDisplay = self.strip.spectrumDisplay
    apiDataSource = self.spectrum._wrappedData

    # Update action icol colour
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if action:
      pix=QtGui.QPixmap(QtCore.QSize(60, 10))
      if spectrumDisplay.is1D:
        pix.fill(QtGui.QColor(self.sliceColour))
      else:
        pix.fill(QtGui.QColor(self.positiveContourColour))
      action.setIcon(QtGui.QIcon(pix))

    # Update strip
    self.strip.update()

  def _createdSpectrumView(self):
    """Set up SpectrumDisplay when new StripSpectrumView is created - for notifiers"""

    # NBNB TBD FIXME get rid of API objects

    spectrumDisplay = self.strip.spectrumDisplay
    spectrum = self.spectrum

    # Set Z widgets for nD strips
    if not spectrumDisplay.is1D:
      strip = self.strip
      if not strip.haveSetupZWidgets:
        strip._setZWidgets()

    # Handle action buttons
    apiDataSource = spectrum._wrappedData
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if not action:
      # add toolbar action (button)
      spectrumName = spectrum.name
      if len(spectrumName) > 12:
        spectrumName = spectrumName[:12]+'.....'
      action = spectrumDisplay.spectrumToolBar.addAction(spectrumName)
      action.setCheckable(True)
      action.setChecked(True)
      action.setToolTip(spectrum.name)
      widget = spectrumDisplay.spectrumToolBar.widgetForAction(action)
      widget.setIconSize(QtCore.QSize(120, 10))
      if spectrumDisplay.is1D:
        widget.setFixedSize(100, 30)
      else:
        widget.setFixedSize(75, 30)
      widget.spectrumView = self._wrappedData
      spectrumDisplay.spectrumActionDict[apiDataSource] = action
      # The following call sets the icon colours:
      self._spectrumViewHasChanged()

    if spectrumDisplay.is1D:
      action.toggled.connect(self.plot.setVisible)
    action.toggled.connect(self.setVisible)


  def _deletedSpectrumView(self):
    """Update interface when a spectrumView is deleted"""
    scene = self.strip.plotWidget.scene()
    scene.removeItem(self)
    if hasattr(self, 'plot'):  # 1d
      scene.removeItem(self.plot)

  def refreshData(self):

    raise Exception('Needs to be implemented in subclass')
