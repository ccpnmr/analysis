"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import collections
from ccpn.util import Colour
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier

#import pyqtgraph as pg

#from ccpn.ui.gui.modules.spectrumPane.PeakListItem import PeakListItem
#from ccpn.ui.gui.modules.spectrumPane.IntegralListItem import IntegralListItem

SpectrumViewParams = collections.namedtuple('SpectrumViewParams', ('valuePerPoint',
                                                                   'totalPointCount',
                                                                   'minAliasedFrequency',
                                                                   'maxAliasedFrequency',
                                                                   'dataDim'))

class GuiSpectrumView(QtWidgets.QGraphicsObject):

    #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
    def __init__(self):
        """ spectrumPane is the parent
            spectrum is the Spectrum object
            dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
            (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
        """

        QtWidgets.QGraphicsItem.__init__(self)  #, scene=self.strip.plotWidget.scene())
        # self.scene = self.strip.plotWidget.scene
        # self._currentBoundingRect = self.strip.plotWidget.sceneRect()

        self._apiDataSource = self._wrappedData.spectrumView.dataSource
        self.spectrumGroupsToolBar = None

        action = self.strip.spectrumDisplay.spectrumActionDict.get(self._apiDataSource)
        if action and not action.isChecked():
            self.setVisible(False)

        self._showContours = True

    # To write your own graphics item, you first create a subclass of QGraphicsItem, and
    # then start by implementing its two pure virtual public functions:
    # boundingRect(), which returns an estimate of the area painted by the item,
    # and paint(), which implements the actual painting. For example:

    # mandatory function to override for QGraphicsItem
    # Implemented in GuiSpectrumViewNd or GuiSpectrumView1d
    def paint(self, painter, option, widget=None):
        pass

    # def updateGeometryChange(self):  # ejb - can we call this?
    #     self._currentBoundingRect = self.strip.plotWidget.sceneRect()
    #     self.prepareGeometryChange()
    #     # print ('>>>prepareGeometryChange', self._currentBoundingRect)

    # mandatory function to override for QGraphicsItem
    # def boundingRect(self):  # seems necessary to have
    #     return self._currentBoundingRect

    # Earlier versions too large value (~1400,1000);
    # i.e larger then inital MainWIndow size; reduced to (900, 700); but (100, 150) appears
    # to give less flicker in Scrolled Strips.

    # override of Qt setVisible
    def setVisible(self, visible):
        QtWidgets.QGraphicsItem.setVisible(self, visible)
        try:
            if self:  # ejb - ?? crashes on table update otherwise
                action = self.strip.spectrumDisplay.spectrumActionDict.get(self._apiDataSource)
                action.setChecked(visible)
                # for peakListView in self.peakListViews:
                #   peakListView.setVisible(visible)
        except:
            getLogger().debug('No visible peaklists')  # gwv changed to debug to reduce output

        # repaint all displays - this is called for each spectrumView in the spectrumDisplay
        # all are attached to the same click
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

        # notify that the spectrumView has changed
        self._finaliseAction('change')

    # def setDimMapping(self, dimMapping=None):
    #
    #   dimensionCount = self.spectrum.dimensionCount
    #   if dimMapping is None:
    #     dimMapping = {}
    #     for i in range(dimensionCount):
    #       dimMapping[i] = i
    #   self.dimMapping = dimMapping
    #
    #   xDim = yDim = None
    #   inverseDimMapping = {}
    #   for dim in dimMapping:
    #     inverseDim = dimMapping[dim]
    #     if inverseDim == 0:
    #       xDim = inverseDim
    #     elif inverseDim == 1:
    #       yDim = inverseDim
    #
    #   if xDim is not None:
    #     assert 0 <= xDim < dimensionCount, 'xDim = %d, dimensionCount = %d' % (xDim, dimensionCount)
    #
    #   if yDim is not None:
    #     assert 0 <= yDim < dimensionCount, 'yDim = %d, dimensionCount = %d' % (yDim, dimensionCount)
    #     assert xDim != yDim, 'xDim = yDim = %d' % xDim
    #
    #   self.xDim = xDim
    #   self.yDim = yDim

    def _getSpectrumViewParams(self, axisDim: int) -> tuple:
        """Get position, width, totalPointCount, minAliasedFrequency, maxAliasedFrequency
        for axisDimth axis (zero-origin)"""

        # axis = self.strip.orderedAxes[axisDim]
        dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[axisDim]

        if not dataDim:
            return

        totalPointCount = (dataDim.numPointsOrig if hasattr(dataDim, "numPointsOrig")
                           else dataDim.numPoints)
        for ii, dd in enumerate(dataDim.dataSource.sortedDataDims()):
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

    def refreshData(self):

        raise Exception('Needs to be implemented in subclass')

def _spectrumViewHasChanged(data):
    """Change action icon colour and other changes when spectrumView changes.

    NB SpectrumView change notifiers are triggered when either DataSource or ApiSpectrumView change.
    """
    self = data[Notifier.OBJECT]

    if self.isDeleted:
        return

    spectrumDisplay = self.strip.spectrumDisplay
    apiDataSource = self.spectrum._wrappedData

    # Update action icol colour
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if action:
        pix = QtGui.QPixmap(QtCore.QSize(60/spectrumDisplay.devicePixelRatio(), 10/spectrumDisplay.devicePixelRatio()))
        if self._showContours:
            if spectrumDisplay.is1D:
                pix.fill(QtGui.QColor(self.sliceColour))
            else:
                pix.fill(QtGui.QColor(self.positiveContourColour))
        else:
            pix.fill(QtGui.QColor('gray'))
        action.setIcon(QtGui.QIcon(pix))

    # Update strip
    self.strip.update()

def _createdSpectrumView(data):
    """Set up SpectrumDisplay when new StripSpectrumView is created - for notifiers.
    This function adds the spectra buttons to the spectrumToolBar.
    """
    self = data[Notifier.OBJECT]

    spectrumDisplay = self.strip.spectrumDisplay

    # Set Z widgets for nD strips
    strip = self.strip
    if not spectrumDisplay.is1D:
        strip._setZWidgets()

    spectrumDisplay.spectrumToolBar._addSpectrumViewToolButtons(self)

        # # TODO:ED check here - used to catch undelete of spectrumView
        # if self.strip.plotWidget:
        #     scene = self.strip.plotWidget.scene()
        #     if self not in scene.items():  # This happens when you do an undo after deletion of spectrum(View)
        #         scene.addItem(self)
        #
        #         # TODO:ED ERROR HERE shouldn't need this soon be check
        #         # if spectrumDisplay.is1D:
        #         #   strip.viewBox.addItem(self.plot)

    # def _deletedSpectrumView(self):
    #     """Update interface when a spectrumView is deleted"""
    #     if self.strip.plotWidget:
    #         scene = self.strip.plotWidget.scene()
    #         scene.removeItem(self)
    #         if hasattr(self, 'plot'):  # 1d
    #             scene.removeItem(self.plot)

