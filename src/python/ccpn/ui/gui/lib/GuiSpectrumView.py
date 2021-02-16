"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-16 13:01:27 +0000 (Tue, February 16, 2021) $"
__version__ = "$Revision: 3.0.3 $"
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
from typing import Optional, Tuple


SpectrumViewParams = collections.namedtuple('SpectrumViewParams', 'valuePerPoint pointCount minAliasedFrequency maxAliasedFrequency '
                                                                  'minSpectrumFrequency maxSpectrumFrequency')
TraceParameters = collections.namedtuple('TraceParameters', 'inRange pointPositions startPoint, endPoint')


class GuiSpectrumView(QtWidgets.QGraphicsObject):

    #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
    def __init__(self):
        """ spectrumPane is the parent
            spectrum is the Spectrum object
            dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
            (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
        """

        QtWidgets.QGraphicsItem.__init__(self)

        self.spectrumGroupsToolBar = None

        action = self.strip.spectrumDisplay.spectrumActionDict.get(self.spectrum)
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
    # i.e larger then initial MainWindow size; reduced to (900, 700); but (100, 150) appears
    # to give less flicker in Scrolled Strips.

    # override of Qt setVisible
    def setVisible(self, visible):
        QtWidgets.QGraphicsItem.setVisible(self, visible)
        try:
            if self:  # ejb - ?? crashes on table update otherwise
                action = self.strip.spectrumDisplay.spectrumActionDict.get(self.spectrum)
                if action:
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

    def _getSpectrumViewParams(self, axisDim: int) -> Optional[Tuple]:
        """Get position, width, totalPointCount, minAliasedFrequency, maxAliasedFrequency
        for axisDimth axis (zero-origin)"""

        ii = self.dimensionOrdering[axisDim]
        if ii is not None:
            minAliasedFrequency, maxAliasedFrequency = (self.spectrum.aliasingLimits)[ii]
            minSpectrumFrequency, maxSpectrumFrequency = sorted(self.spectrum.spectrumLimits[ii])
            pointCount = (self.spectrum.pointCounts)[ii]
            valuePerPoint = (self.spectrum.valuesPerPoint)[ii]

            return SpectrumViewParams(valuePerPoint, pointCount,
                                      minAliasedFrequency, maxAliasedFrequency,
                                      minSpectrumFrequency, maxSpectrumFrequency)

    def getTraceParameters(self, position, dim):
        # dim  = spectrumView index, i.e. 0 for X, 1 for Y

        _indices = self.dimensionOrdering
        index = _indices[dim]
        if index is None:
            getLogger().warning('getTraceParameters: bad index')
            return

        pointCount = self.spectrum.pointCounts[index]
        minSpectrumFrequency, maxSpectrumFrequency = sorted(self.spectrum.spectrumLimits[index])

        inRange = (minSpectrumFrequency <= position[index] <= maxSpectrumFrequency)
        pointPos = (self.spectrum.ppm2point(position[index], dimension=index + 1) - 1) % pointCount

        return TraceParameters(inRange, pointPos, 0, pointCount - 1)

    def _getColour(self, colourAttr, defaultColour=None):

        colour = getattr(self, colourAttr)
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

    # Update action icon colour
    action = spectrumDisplay.spectrumActionDict.get(self.spectrum)
    if action:
        # add spectrum action for non-grouped action
        _addActionIcon(action, self, spectrumDisplay)

    if spectrumDisplay.isGrouped and self in spectrumDisplay.spectrumViews:
        if hasattr(self, '_guiChanged'):
            del self._guiChanged

            from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

            GLSignals = GLNotifier(parent=self)

            self.buildContoursOnly = True

            # repaint
            GLSignals.emitPaintEvent()

    # Update strip
    self.strip.update()


def _addActionIcon(action, self, spectrumDisplay):
    _iconX = int(60 / spectrumDisplay.devicePixelRatio())
    _iconY = int(10 / spectrumDisplay.devicePixelRatio())
    pix = QtGui.QPixmap(QtCore.QSize(_iconX, _iconY))

    if getattr(self, '_showContours', True) or spectrumDisplay.isGrouped:
        if spectrumDisplay.is1D:
            _col = self.sliceColour
        else:
            _col = self.positiveContourColour

        if _col and _col.startswith('#'):
            pix.fill(QtGui.QColor(_col))

        elif _col in Colour.colorSchemeTable:
            colourList = Colour.colorSchemeTable[_col]

            step = _iconX
            stepX = _iconX
            stepY = len(colourList) - 1
            jj = 0
            painter = QtGui.QPainter(pix)

            for ii in range(_iconX):
                _interp = (stepX - step) / stepX
                _intCol = Colour.interpolateColourHex(colourList[min(jj, stepY)], colourList[min(jj + 1, stepY)],
                                                      _interp)

                painter.setPen(QtGui.QColor(_intCol))
                painter.drawLine(ii, 0, ii, _iconY)
                step -= stepY
                while step < 0:
                    step += stepX
                    jj += 1

            painter.end()

        else:
            pix.fill(QtGui.QColor('gray'))
    else:
        pix.fill(QtGui.QColor('gray'))

    action.setIcon(QtGui.QIcon(pix))
