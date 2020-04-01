"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-04-01 14:03:21 +0100 (Wed, April 01, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import time
import math
import numpy as np
from contextlib import contextmanager
from itertools import zip_longest
from typing import Tuple
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLVertexArray, GLRENDERMODE_DRAW, \
    GLRENDERMODE_REBUILD, GLRENDERMODE_RESCALE, ZOOMHISTORYSTORE, ZOOMTIMERDELAY
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import YAXISUNITS1D, SPECTRUM_VALUEPERPOINT
import ccpn.util.Phasing as Phasing
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_MATCHATOMTYPE, AXIS_ACTIVEAXES, \
    DOUBLEAXIS_ACTIVEAXES, DOUBLEAXIS_FULLATOMNAME, DOUBLEAXIS_MATCHATOMTYPE, MOUSEDICTSTRIP
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.ui.gui.lib.OpenGL import CcpnOpenGLDefs as GLDefs
from ccpn.util.Logging import getLogger
from ccpn.core.lib.peakUtils import movePeak

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_BACKGROUND, CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, \
    CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_INTEGRALSHADE, \
    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE, getColours, \
    CCPNGLWIDGET_HEXBACKGROUND, CCPNGLWIDGET_ZOOMAREA, CCPNGLWIDGET_PICKAREA, \
    CCPNGLWIDGET_SELECTAREA, CCPNGLWIDGET_ZOOMLINE, CCPNGLWIDGET_MOUSEMOVELINE, \
    CCPNGLWIDGET_HARDSHADE
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLSimpleLabels import GLSimpleStrings
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import GLViewports
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLWidgets import GLExternalRegion
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLGlobalData
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CURSOR_SOURCE_NONE, CURSOR_SOURCE_SELF, CURSOR_SOURCE_OTHER, PAINTMODES


class GuiNdWidget(CcpnGLWidget):
    is1D = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    SPECTRUMPOSCOLOUR = 'positiveContourColour'
    SPECTRUMNEGCOLOUR = 'negativeContourColour'
    AXIS_INSIDE = False

    def __init__(self, strip=None, mainWindow=None, stripIDLabel=None):
        super().__init__(strip=strip, mainWindow=mainWindow, stripIDLabel=stripIDLabel)

    def _mouseInPeak(self, xPosition, yPosition, firstOnly=False):
        """Find the peaks under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]
        if len(self._orderedAxes) > 2:
            zPositions = self._orderedAxes[2].region
        else:
            zPositions = None

        peaks = []

        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():

                    peakList = peakListView.peakList

                    spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
                    xAxis = spectrumIndices[0]
                    yAxis = spectrumIndices[1]

                    for peak in peakList.peaks:
                        if len(peak.axisCodes) > 2 and zPositions is not None:

                            zAxis = spectrumIndices[2]

                            if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):

                                # within the XY bounds so check whether inPlane
                                _isInPlane, _isInFlankingPlane, planeIndex, fade = self._GLPeaks.objIsInVisiblePlanes(spectrumView, peak)

                                # if zPositions[0] < float(peak.position[zAxis]) < zPositions[1]:
                                if _isInPlane:
                                    peaks.append(peak)
                                    if firstOnly:
                                        return peaks
                        else:
                            if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):
                                peaks.append(peak)
                                if firstOnly:
                                    return peaks if peak in self.current.peaks else []

        return peaks

    def _mouseInMultiplet(self, xPosition, yPosition, firstOnly=False):
        """Find the multiplets under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]

        if len(self._orderedAxes) > 2:
            zPositions = self._orderedAxes[2].region
        else:
            zPositions = None

        multiplets = []

        for spectrumView in self.strip.spectrumViews:

            for multipletListView in spectrumView.multipletListViews:
                if spectrumView.isVisible() and multipletListView.isVisible():

                    multipletList = multipletListView.multipletList

                    spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
                    xAxis = spectrumIndices[0]
                    yAxis = spectrumIndices[1]

                    for multiplet in multipletList.multiplets:
                        if not multiplet.position:
                            continue

                        if len(multiplet.axisCodes) > 2 and zPositions is not None:

                            zAxis = spectrumIndices[2]

                            if (xPositions[0] < float(multiplet.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(multiplet.position[yAxis]) < yPositions[1]):

                                # within the XY bounds so check whether inPlane
                                _isInPlane, _isInFlankingPlane, planeIndex, fade = self._GLMultiplets.objIsInVisiblePlanes(spectrumView, multiplet)

                                # if zPositions[0] < float(multiplet.position[zAxis]) < zPositions[1]:
                                if _isInPlane:
                                    multiplets.append(multiplet)
                                    if firstOnly:
                                        return multiplets
                        else:
                            if (xPositions[0] < float(multiplet.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(multiplet.position[yAxis]) < yPositions[1]):
                                multiplets.append(multiplet)
                                if firstOnly:
                                    return multiplets if multiplet in self.current.multiplets else []

        return multiplets

    def _mouseInIntegral(self, xPosition, yPosition, firstOnly=False):
        """Find the integrals under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        Currently not-defined for Nd integrals
        """
        return []

    def _updateVisibleSpectrumViews(self):
        """Update the list of visible spectrumViews when change occurs
        """

        # make the list of ordered spectrumViews
        self._ordering = self.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)

        self._ordering = [specView for specView in self._ordering if specView.spectrum.isValidPath]

        for specView in tuple(self._spectrumSettings.keys()):
            if specView not in self._ordering:
                del self._spectrumSettings[specView]

                # delete the 1d string relating to the spectrumView
                self._spectrumLabelling.removeString(specView)

        # make a list of the visible and not-deleted spectrumViews
        visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
        visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]

        self._visibleOrdering = visibleSpectrumViews

        # set the first visible, or the first in the ordered list
        self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
            0].isDeleted else None
        self.visiblePlaneList = {}
        self.visiblePlaneListPointValues = {}

        minList = [self._spectrumSettings[sp][SPECTRUM_VALUEPERPOINT] if SPECTRUM_VALUEPERPOINT in self._spectrumSettings[sp] else None
                   for sp in self._ordering if sp in self._spectrumSettings]
        minimumValuePerPoint = None

        # check the length of the min values, may have lower dimension spectra overlaid
        for val in minList:
            if minimumValuePerPoint and val is not None:
                minimumValuePerPoint = [min(ii, jj) for ii, jj in zip_longest(minimumValuePerPoint, val, fillvalue=0.0)]
            elif minimumValuePerPoint:
                # val is None so ignore
                pass
            else:
                # set the first value
                minimumValuePerPoint = val

        for visibleSpecView in self._ordering:
            self.visiblePlaneList[visibleSpecView], self.visiblePlaneListPointValues[visibleSpecView] = visibleSpecView._getVisiblePlaneList(
                    firstVisible=self._firstVisible,
                    minimumValuePerPoint=minimumValuePerPoint)

        # update the labelling lists
        self._GLPeaks.setListViews(self._ordering)
        self._GLIntegrals.setListViews(self._ordering)
        self._GLMultiplets.setListViews(self._ordering)

    def getPeakPositionFromMouse(self, peak, lastStartCoordinate, cursorPosition=None):
        """Get the centre position of the clicked peak
        """
        indices = getAxisCodeMatchIndices(self._axisCodes, peak.axisCodes)
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                lastStartCoordinate[ii] = peak.position[ind]
            else:
                lastStartCoordinate[ii] = cursorPosition[ii]

    def _movePeak(self, peak, deltaPosition):
        """Move the peak to new position
        """
        indices = getAxisCodeMatchIndices(self.axisCodes, peak.axisCodes)

        # get the correct coordinates based on the axisCodes
        p0 = list(peak.position)
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                p0[ind] += deltaPosition[ii]

        movePeak(peak, p0, updateHeight=True)


class Gui1dWidget(CcpnGLWidget):
    AXIS_MARGINRIGHT = 80
    YAXISUSEEFORMAT = True
    INVERTXAXIS = True
    INVERTYAXIS = False
    AXISLOCKEDBUTTON = True
    is1D = True
    SPECTRUMPOSCOLOUR = 'sliceColour'
    SPECTRUMNEGCOLOUR = 'sliceColour'
    SPECTRUMXZOOM = 1.0e2
    SPECTRUMYZOOM = 1.0e6
    SHOWSPECTRUMONPHASING = False
    YAXES = YAXISUNITS1D

    def __init__(self, strip=None, mainWindow=None, stripIDLabel=None):
        super(Gui1dWidget, self).__init__(strip=strip,
                                          mainWindow=mainWindow,
                                          stripIDLabel=stripIDLabel)

    def _mouseInPeak(self, xPosition, yPosition, firstOnly=False):
        """Find the peaks under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]

        peaks = []
        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():

                    peakList = peakListView.peakList

                    for peak in peakList.peaks:
                        if (xPositions[0] < float(peak.position[0]) < xPositions[1]
                                and yPositions[0] < float(peak.height) < yPositions[1]):

                            peaks.append(peak)
                            if firstOnly:
                                return peaks if peak in self.current.peaks else []

        return peaks

    def _mouseInIntegral(self, xPosition, yPosition, firstOnly=False):
        """Find the integrals under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        integrals = []

        if not self._stackingMode and not (self.is1D and self.strip._isPhasingOn):
            for reg in self._GLIntegrals._GLSymbols.values():
                if not reg.integralListView.isVisible() or not reg.spectrumView.isVisible():
                    continue
                integralPressed = self.mousePressIn1DArea(reg._regions)
                if integralPressed:
                    for ilp in integralPressed:
                        obj = ilp[0]._object
                        integrals.append(obj)
                        if firstOnly:
                            return integrals if obj in self.current.integrals else []

        return integrals

    def _mouseInMultiplet(self, xPosition, yPosition, firstOnly=False):
        """Find the multiplets under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]

        multiplets = []
        for spectrumView in self.strip.spectrumViews:
            for multipletListView in spectrumView.multipletListViews:
                if spectrumView.isVisible() and multipletListView.isVisible():

                    multipletList = multipletListView.multipletList

                    for multiplet in multipletList.multiplets:
                        if not multiplet.position:
                            continue

                        if (xPositions[0] < float(multiplet.position[0]) < xPositions[1]
                                and yPositions[0] < float(multiplet.height) < yPositions[1]):

                            multiplets.append(multiplet)
                            if firstOnly:
                                return multiplets if multiplet in self.current.multiplets else []

        return multiplets

    def _newStatic1DTraceData(self, spectrumView, tracesDict,
                              point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, position,
                              ph0=None, ph1=None, pivot=None):
        """Create a new static 1D phase trace
        """
        try:
            # ignore for 1D if already in the traces list
            for thisTrace in tracesDict:
                if spectrumView == thisTrace.spectrumView:
                    return

            pointInt = [1 + int(pnt + 0.5) for pnt in point]
            # data = spectrumView.spectrum.getSliceData()
            # data = spectrumView.spectrum.get1dSpectrumData()

            # TODO:ED this does not change the data model
            data = spectrumView.spectrum.intensities

            preData = data

            if ph0 is not None and ph1 is not None and pivot is not None:
                preData = Phasing.phaseRealData(data, ph0, ph1, pivot)

            # x = np.array([xDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(xMinFrequency, xMaxFrequency)])
            x = spectrumView.spectrum.positions

            # y = np.array([preData[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)])

            # y = positionPixel[1] + spectrumView._traceScale * (self.axisT-self.axisB) * \
            #     np.array([preData[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)])

            colour = spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
            colR = int(colour.strip('# ')[0:2], 16) / 255.0
            colG = int(colour.strip('# ')[2:4], 16) / 255.0
            colB = int(colour.strip('# ')[4:6], 16) / 255.0

            tracesDict.append(GLVertexArray(numLists=1,
                                            renderMode=GLRENDERMODE_RESCALE,
                                            blendMode=False,
                                            drawMode=GL.GL_LINE_STRIP,
                                            dimension=2,
                                            GLContext=self))

            numVertices = len(x)
            hSpectrum = tracesDict[-1]
            hSpectrum.indices = numVertices
            hSpectrum.numVertices = numVertices
            hSpectrum.indices = np.arange(numVertices, dtype=np.uint32)

            if self._showSpectraOnPhasing:
                hSpectrum.colors = np.array(self._phasingTraceColour * numVertices, dtype=np.float32)
            else:
                hSpectrum.colors = np.array((colR, colG, colB, 1.0) * numVertices, dtype=np.float32)

            hSpectrum.vertices = np.empty(hSpectrum.numVertices * 2, dtype=np.float32)

            # x = np.append(x, [xDataDim.primaryDataDimRef.pointToValue(xMaxFrequency + 1),
            #                   xDataDim.primaryDataDimRef.pointToValue(xMinFrequency)])
            # # y = np.append(y, [positionPixel[1], positionPixel[1]])
            # hSpectrum.colors = np.append(hSpectrum.colors, ((colR, colG, colB, 1.0),
            #                                       (colR, colG, colB, 1.0)))

            hSpectrum.vertices[::2] = x
            hSpectrum.vertices[1::2] = preData

            # store the pre-phase data
            hSpectrum.data = data
            hSpectrum.values = [spectrumView, point, xDataDim,
                                xMinFrequency, xMaxFrequency,
                                xNumPoints, positionPixel, position]
            hSpectrum.spectrumView = spectrumView

        except Exception as es:
            # print('>>>', str(es))
            tracesDict = []

    @property
    def showSpectraOnPhasing(self):
        return self._showSpectraOnPhasing

    @showSpectraOnPhasing.setter
    def showSpectraOnPhasing(self, visible):
        self._showSpectraOnPhasing = visible
        self._updatePhasingColour()
        self.update()

    def toggleShowSpectraOnPhasing(self):
        self._showSpectraOnPhasing = not self._showSpectraOnPhasing
        self._updatePhasingColour()
        self.update()

    def _updatePhasingColour(self):
        for trace in self._staticHTraces:
            colour = trace.spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
            colR = int(colour.strip('# ')[0:2], 16) / 255.0
            colG = int(colour.strip('# ')[2:4], 16) / 255.0
            colB = int(colour.strip('# ')[4:6], 16) / 255.0

            numVertices = trace.numVertices
            if self._showSpectraOnPhasing:
                trace.colors = np.array(self._phasingTraceColour * numVertices, dtype=np.float32)
            else:
                trace.colors = np.array((colR, colG, colB, 1.0) * numVertices, dtype=np.float32)

            trace.renderMode = GLRENDERMODE_RESCALE

    def buildSpectra(self):
        """set the GL flags to build spectrum contour lists
        """
        if self.strip.isDeleted:
            return

        stackCount = 0

        # self._spectrumSettings = {}
        rebuildFlag = False
        for stackCount, spectrumView in enumerate(self._ordering):  # .strip.spectrumViews:
            if spectrumView.isDeleted:
                continue

            if spectrumView.buildContours or spectrumView.buildContoursOnly:

                # flag the peaks for rebuilding
                if not spectrumView.buildContoursOnly:
                    for peakListView in spectrumView.peakListViews:
                        peakListView.buildSymbols = True
                        peakListView.buildLabels = True
                    for integralListView in spectrumView.integralListViews:
                        integralListView.buildSymbols = True
                        integralListView.buildLabels = True
                    for multipletListView in spectrumView.multipletListViews:
                        multipletListView.buildSymbols = True
                        multipletListView.buildLabels = True

                spectrumView.buildContours = False
                spectrumView.buildContoursOnly = False

                # rebuild the contours
                if spectrumView not in self._contourList.keys():
                    self._contourList[spectrumView] = GLVertexArray(numLists=1,
                                                                    renderMode=GLRENDERMODE_DRAW,
                                                                    blendMode=False,
                                                                    drawMode=GL.GL_LINE_STRIP,
                                                                    dimension=2,
                                                                    GLContext=self)
                spectrumView._buildGLContours(self._contourList[spectrumView],
                                              firstShow=self._preferences.automaticNoiseContoursOnFirstShow)

                self._buildSpectrumSetting(spectrumView=spectrumView, stackCount=stackCount)
                # if self._stackingMode:
                #     stackCount += 1
                rebuildFlag = True

                # define the VBOs to pass to the graphics card
                self._contourList[spectrumView].defineIndexVBO(enableVBO=True)

        # rebuild the traces as the spectrum/plane may have changed
        if rebuildFlag:
            self.rebuildTraces()

    def _updateVisibleSpectrumViews(self):
        """Update the list of visible spectrumViews when change occurs
        """

        # make the list of ordered spectrumViews
        self._ordering = self.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)

        self._ordering = [specView for specView in self._ordering]

        for specView in tuple(self._spectrumSettings.keys()):
            if specView not in self._ordering:
                # print('>>>_updateVisibleSpectrumViews delete', specView, id(specView))
                # print('>>>', [id(spec) for spec in self._ordering])
                del self._spectrumSettings[specView]

                # delete the 1d string relating to the spectrumView
                self._spectrumLabelling.removeString(specView)

        # make a list of the visible and not-deleted spectrumViews
        # visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
        visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]

        self._visibleOrdering = visibleSpectrumViews

        # set the first visible, or the first in the ordered list
        self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
            0].isDeleted else None

        # update the labelling lists
        self._GLPeaks.setListViews(self._ordering)
        self._GLIntegrals.setListViews(self._ordering)
        self._GLMultiplets.setListViews(self._ordering)

    def getPeakPositionFromMouse(self, peak, lastStartCoordinate, cursorPosition=None):
        """Get the centre position of the clicked 1d peak
        """
        indices = getAxisCodeMatchIndices(self._axisCodes, peak.axisCodes)

        # check that the mappings are okay
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                lastStartCoordinate[ii] = peak.position[ind]
            else:
                lastStartCoordinate[ii] = peak.height

    def _movePeak(self, peak, deltaPosition):
        """Move the peak to new position
        """
        indices = getAxisCodeMatchIndices(self.axisCodes, peak.axisCodes)

        # get the correct coordinates based on the axisCodes
        p0 = list(peak.position)
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                p0[ind] += deltaPosition[ii]

        # update height - taken from peakPickPosition
        spectrum = peak.peakList.spectrum
        pp = spectrum.mainSpectrumReferences[0].valueToPoint(p0[0])
        frac = pp % 1
        if spectrum.intensities is not None and spectrum.intensities.size != 0:
            # need to interpolate between pp-1, and pp
            peak.height = spectrum.intensities[int(pp) - 1] + \
                          frac * (spectrum.intensities[int(pp)] - spectrum.intensities[int(pp) - 1])

        peak.position = p0


class Gui1dWidgetAxis(QtWidgets.QOpenGLWidget):
    is1D = True
    AXIS_MARGINRIGHT = 80
    AXIS_MARGINBOTTOM = 25
    AXIS_LINE = 7
    AXIS_OFFSET = 3
    AXIS_INSIDE = False
    YAXISUSEEFORMAT = True
    INVERTXAXIS = True
    INVERTYAXIS = True
    AXISLOCKEDBUTTON = False
    SPECTRUMXZOOM = 1.0e1
    SPECTRUMYZOOM = 1.0e1
    SHOWSPECTRUMONPHASING = False
    XAXES = GLDefs.XAXISUNITS
    YAXES = YAXISUNITS1D
    AXIS_MOUSEYOFFSET = AXIS_MARGINBOTTOM + (0 if AXIS_INSIDE else AXIS_LINE)

    def __init__(self, parent, spectrumDisplay=None, mainWindow=None, antiAlias=4):

        super().__init__(parent)

        # GST add antiAliasing, no perceptible speed impact on my mac (intel iris graphics!)
        # samples = 4 is good enough but 8 also works well in terms of speed...
        try:
            fmt = QtGui.QSurfaceFormat()
            fmt.setSamples(antiAlias)
            self.setFormat(fmt)

            samples = self.format().samples()  # GST a use for the walrus
            if samples != antiAlias:
                getLogger().warning('hardware changed antialias level, expected %i got %i...' % (samples, antiAlias))
        except Exception as es:
            getLogger().warning('error during anti aliasing setup %s, anti aliasing disabled...' % str(es))

        # flag to display paintGL but keep an empty screen
        self._blankDisplay = False
        self.setAutoFillBackground(False)

        if not spectrumDisplay:  # don't initialise if nothing there
            return

        self.spectrumDisplay = spectrumDisplay

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self._preferences = self.application.preferences.general
        self.globalGL = None

        # add a flag so that scaling cannot be done until the gl attributes are initialised
        self.glReady = False

        self.setMouseTracking(True)  # generate mouse events when button not pressed

        # always respond to mouse events
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # initialise all attributes
        self._initialiseAll()

        # set a minimum size so that the strips resize nicely
        self.setMinimumSize(self.AXIS_MARGINRIGHT + 10, self.AXIS_MARGINBOTTOM + 10)

        # initialise the pyqtsignal notifier
        self.GLSignals = GLNotifier(parent=self, strip=None)

        # # set the pyqtsignal responders
        # self.GLSignals.glXAxisChanged.connect(self._glXAxisChanged)
        # self.GLSignals.glYAxisChanged.connect(self._glYAxisChanged)
        # self.GLSignals.glAllAxesChanged.connect(self._glAllAxesChanged)
        # self.GLSignals.glMouseMoved.connect(self._glMouseMoved)
        # self.GLSignals.glEvent.connect(self._glEvent)
        # self.GLSignals.glAxisLockChanged.connect(self._glAxisLockChanged)
        # self.GLSignals.glAxisUnitsChanged.connect(self._glAxisUnitsChanged)

        self.lastPixelRatio = None
        # self.setFixedWidth(self.AXIS_MARGINRIGHT+self.AXIS_LINE)

    @property
    def tilePosition(self) -> Tuple[int, int]:
        """Returns a tuple of the tile coordinates (from top-left)
        tilePosition = (x, y)
        """
        if self.spectrumDisplay.stripArrangement == 'Y':
            return self._tilePosition
        else:
            # return the flipped position
            return (self._tilePosition[1], self._tilePosition[0])

    @tilePosition.setter
    def tilePosition(self, value):
        """Setter for tilePosition
        tilePosition must be a tuple of int (x, y)
        """
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple for tilePosition')
        if len(value) != 2:
            raise ValueError('Tuple must be (x, y)')
        if any(type(vv) != int for vv in value):
            raise ValueError('Tuple must be of type int')

        self._tilePosition = value

    def setAxisType(self, dimension):
        """Set the current axis type for the axis widget
        0 = X Axis type, 1 = Y Axis type
        Only the required axis is drawn and the widget dimensions are fixed in the other axis
        """
        if type(dimension) != int:
            raise TypeError('dimension must be an int')
        if not (0 <= dimension < 2):
            raise TypeError('dimension is out of range')

        self._axisType = dimension
        if dimension == 1:
            self.setFixedWidth(self.AXIS_MARGINRIGHT + (0 if self.AXIS_INSIDE else self.AXIS_LINE))
        else:
            self.setFixedHeight(self.AXIS_MARGINBOTTOM + (0 if self.AXIS_INSIDE else self.AXIS_LINE))

    def getSmallFont(self, transparent=False):
        # GST tried this, it wrong sometimes, also sometimes its a float?
        # scale =  int(self.viewports._devicePixelRatio)
        scale = self.devicePixelRatio()

        fontName = self.globalGL.glSmallTransparentFont if transparent else self.globalGL.glSmallFont

        size = self.globalGL.glSmallFontSize
        font = '%s-%i' % (fontName, size)

        return self.globalGL.fonts[font, scale]

    def paintGL(self):
        """Handle the GL painting
        """
        if self._blankDisplay:
            return

        if self.spectrumDisplay.isDeleted:
            return

        # NOTE:ED - testing, remove later
        self._paintMode = PAINTMODES.PAINT_ALL

        if self._paintMode == PAINTMODES.PAINT_NONE:

            # do nothing
            pass

        elif (self._paintMode == PAINTMODES.PAINT_ALL) or self._leavingWidget:

            # check whether the visible spectra list needs updating
            if self._visibleSpectrumViewsChange:
                self._visibleSpectrumViewsChange = False
                self._updateVisibleSpectrumViews()

            # if there are no spectra then skip the paintGL event
            if not self._ordering:
                return

            with self.glBlocking():
                # simple profile of building all
                self._buildGL()
                self._paintGL()

            # make all following paint events into mouse only
            # so only paints a single frame from an update event
            self._paintMode = PAINTMODES.PAINT_MOUSEONLY
            self._paintLastFrame = True
            self._leavingWidget = False

        elif self._paintMode == PAINTMODES.PAINT_MOUSEONLY:
            self._paintLastFrame = False
            self._leavingWidget = False

            # only need to paint the mouse cursor
            # self._paintGLMouseOnly()
            self._paintGL()

    @contextmanager
    def glBlocking(self):
        try:
            # stop notifiers and logging interfering with paint event
            self.project.blankNotification()
            self.application._increaseNotificationBlocking()

            yield

        finally:
            # re-enable notifiers
            self.application._decreaseNotificationBlocking()
            self.project.unblankNotification()

    def _round_sig(self, x, sig=6, small_value=1.0e-9):
        return 0 if x == 0 else round(x, sig - int(math.floor(math.log10(max(abs(x), abs(small_value))))) - 1)

    def between(self, val, l, r):
        return (l - val) * (r - val) <= 0

    def _floatFormat(self, f=0.0, prec=3):
        """return a float string, remove trailing zeros after decimal
        """
        return (('%.' + str(prec) + 'f') % f).rstrip('0').rstrip('.')

    def _intFormat(self, ii=0, prec=0):
        """return an integer string
        """
        return self._floatFormat(ii, 1)
        # return '%i' % ii

    def _eFormat(self, f=0.0, prec=4):
        """return an exponential with trailing zeroes removed
        """
        s = '%.*e' % (prec, f)
        if 'e' in s:
            mantissa, exp = s.split('e')
            mantissa = mantissa.rstrip('0')
            if mantissa.endswith('.'):
                mantissa += '0'
            exp = exp.lstrip('0+')
            if exp:
                if exp.startswith('-'):
                    return '%se%d' % (mantissa, int(exp))
                else:
                    return '%se+%d' % (mantissa, int(exp))
            else:
                return '%s' % mantissa

        else:
            return ''

    def _buildAxes(self, gridGLList, axisList=None, scaleGrid=None, r=0.0, g=0.0, b=0.0, transparency=256.0,
                   _includeDiagonal=False, _diagonalList=None, _includeAxis=True):
        """Build the grid
        """

        def check(ll):
            # check if a number ends in an even digit
            val = '%.0f' % (ll[3] / ll[4])
            valLen = len(val)
            if val[valLen - 1] in '02468':
                return True

        def valueToRatio(val, x0, x1):
            return (val - x0) / (x1 - x0)

        labelling = {'0': [], '1': []}
        axesChanged = False

        # check if the width is too small to draw too many grid levels
        boundX = (self.w - self.AXIS_MARGINRIGHT) if self._drawRightAxis else self.w
        boundY = (self.h - self.AXIS_MOUSEYOFFSET) if self._drawBottomAxis else self.h
        scaleBounds = (boundX, boundY)

        if gridGLList.renderMode == GLRENDERMODE_REBUILD:

            # get the list of visible spectrumViews, or the first in the list
            visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
            thisSpecView = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
                0].isDeleted else None

            if thisSpecView:
                thisSpec = thisSpecView.spectrum

                # generate different axes depending on units - X Axis
                if self.XAXES[self._xUnits] == GLDefs.AXISUNITSPPM:
                    axisLimitL = self.axisL
                    axisLimitR = self.axisR
                    self.XMode = self._floatFormat

                elif self.XAXES[self._xUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        if self.is1D:
                            axisLimitL = self.axisL * thisSpec.spectrometerFrequencies[0]
                            axisLimitR = self.axisR * thisSpec.spectrometerFrequencies[0]

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]
                            axisLimitL = self.axisL * thisSpec.spectrometerFrequencies[indices[0]]
                            axisLimitR = self.axisR * thisSpec.spectrometerFrequencies[indices[0]]

                    else:
                        # error trap all spectra deleted
                        axisLimitL = self.axisL
                        axisLimitR = self.axisR
                    self.XMode = self._floatFormat

                else:
                    if self._ordering:

                        if self.is1D:
                            axisLimitL = thisSpec.mainSpectrumReferences[0].valueToPoint(self.axisL)
                            axisLimitR = thisSpec.mainSpectrumReferences[0].valueToPoint(self.axisR)

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]

                            # map to a point
                            axisLimitL = thisSpec.mainSpectrumReferences[indices[0]].valueToPoint(self.axisL)
                            axisLimitR = thisSpec.mainSpectrumReferences[indices[0]].valueToPoint(self.axisR)

                    else:
                        # error trap all spectra deleted
                        axisLimitL = self.axisL
                        axisLimitR = self.axisR
                    self.XMode = self._intFormat

                # generate different axes depending on units - Y Axis, always use first option for 1d
                if self.is1D:
                    axisLimitT = self.axisT
                    axisLimitB = self.axisB
                    self.YMode = self._eFormat  # '%.6g'

                elif self.YAXES[self._yUnits] == GLDefs.AXISUNITSPPM:
                    axisLimitT = self.axisT
                    axisLimitB = self.axisB
                    self.YMode = self._floatFormat  # '%.3f'

                elif self.YAXES[self._yUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]
                        axisLimitT = self.axisT * thisSpec.spectrometerFrequencies[indices[1]]
                        axisLimitB = self.axisB * thisSpec.spectrometerFrequencies[indices[1]]

                    else:
                        # error trap all spectra deleted
                        axisLimitT = self.axisT
                        axisLimitB = self.axisB
                    self.YMode = self._floatFormat  # '%.3f'

                else:
                    if self._ordering:

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]

                        # map to a point
                        axisLimitT = thisSpec.mainSpectrumReferences[indices[1]].valueToPoint(self.axisT)
                        axisLimitB = thisSpec.mainSpectrumReferences[indices[1]].valueToPoint(self.axisB)

                    else:
                        # error trap all spectra deleted
                        axisLimitT = self.axisT
                        axisLimitB = self.axisB
                    self.YMode = self._intFormat  # '%i'

                # ul = np.array([min(self.axisL, self.axisR), min(self.axisT, self.axisB)])
                # br = np.array([max(self.axisL, self.axisR), max(self.axisT, self.axisB)])

                minX = min(axisLimitL, axisLimitR)
                maxX = max(axisLimitL, axisLimitR)
                minY = min(axisLimitT, axisLimitB)
                maxY = max(axisLimitT, axisLimitB)
                ul = np.array([minX, minY])
                br = np.array([maxX, maxY])

                gridGLList.renderMode = GLRENDERMODE_DRAW
                axesChanged = True

                gridGLList.clearArrays()

                vertexList = ()
                indexList = ()
                colorList = ()

                index = 0
                for scaleOrder, i in enumerate(scaleGrid):  #  [2,1,0]:   ## Draw three different scales of grid
                    dist = br - ul
                    nlTarget = 10. ** i
                    d = 10. ** np.floor(np.log10(abs(dist / nlTarget)) + 0.5)

                    ul1 = np.floor(ul / d) * d
                    br1 = np.ceil(br / d) * d
                    dist = br1 - ul1
                    nl = (dist / d) + 0.5

                    for ax in axisList:  #   range(0,2):  ## Draw grid for both axes

                        # # skip grid lines for point grids - not sure this is working
                        # if d[0] <= 0.1 and ax == 0 and self.XMode == self._intFormat:
                        #     print('>>>', d[0], d[1])
                        #     continue
                        # if d[1] <= 0.1 and ax == 1 and self.YMode == self._intFormat:
                        #     print('>>>', d[0], d[1])
                        #     continue

                        # # ignore narrow grids
                        # if self.w * (scaleOrder+1) < 250 or self.h * (scaleOrder+1) < 250:
                        #     continue
                        #
                        c = 30.0 + (scaleOrder * 20)
                        bx = (ax + 1) % 2

                        for x in range(0, int(nl[ax])):
                            p1 = np.array([0., 0.])
                            p2 = np.array([0., 0.])
                            p1[ax] = ul1[ax] + x * d[ax]
                            p2[ax] = p1[ax]
                            p1[bx] = ul[bx]
                            p2[bx] = br[bx]
                            if p1[ax] < min(ul[ax], br[ax]) or p1[ax] > max(ul[ax], br[ax]):
                                continue

                            if i == 1:  # should be largest scale grid
                                d[0] = self._round_sig(d[0], sig=4)
                                d[1] = self._round_sig(d[1], sig=4)

                                if ax == 0:
                                    includeGrid = not (self.XMode == self._intFormat and d[0] < 1 and abs(p1[0] - int(p1[0])) > d[0] / 2.0)
                                else:
                                    includeGrid = not (self.YMode == self._intFormat and d[1] < 1 and abs(p1[1] - int(p1[1])) > d[1] / 2.0)
                                # includeGrid = True

                                if includeGrid:
                                    if '%.5f' % p1[0] == '%.5f' % p2[0]:  # check whether a vertical line - x axis

                                        # xLabel = str(int(p1[0])) if d[0] >=1 else self.XMode % p1[0]
                                        labelling[str(ax)].append((i, ax, valueToRatio(p1[0], axisLimitL, axisLimitR),
                                                                   p1[0], d[0]))
                                    else:
                                        # num = int(p1[1]) if d[1] >=1 else self.XMode % p1[1]
                                        labelling[str(ax)].append((i, ax, valueToRatio(p1[1], axisLimitB, axisLimitT),
                                                                   p1[1], d[1]))

                                    # append the new points to the end of nparray, ignoring narrow grids
                                    if scaleBounds[ax] * (scaleOrder + 1) > 225:
                                        indexList += (index, index + 1)
                                        vertexList += (valueToRatio(p1[0], axisLimitL, axisLimitR),
                                                       valueToRatio(p1[1], axisLimitB, axisLimitT),
                                                       valueToRatio(p2[0], axisLimitL, axisLimitR),
                                                       valueToRatio(p2[1], axisLimitB, axisLimitT))

                                        alpha = min([1.0, c / transparency])
                                        # gridGLList.colors = np.append(gridGLList.colors, (r, g, b, alpha, r, g, b, alpha))
                                        colorList += (r, g, b, alpha, r, g, b, alpha)

                                        gridGLList.numVertices += 2
                                        index += 2

                # add the extra axis lines
                if _includeAxis:
                    for ax in axisList:

                        offset = 0.02 if self.AXIS_INSIDE else 0.98
                        if ax == 0:
                            # add the x axis line
                            indexList += (index, index + 1)
                            vertexList += (0.0, offset, 1.0, offset)
                            colorList += (r, g, b, 1.0, r, g, b, 1.0)
                            gridGLList.numVertices += 2
                            index += 2

                        elif ax == 1:
                            # add the y axis line
                            indexList += (index, index + 1)
                            vertexList += (1.0 - offset, 0.0, 1.0 - offset, 1.0)
                            colorList += (r, g, b, 1.0, r, g, b, 1.0)
                            gridGLList.numVertices += 2
                            index += 2

                # copy the arrays the the GLstore
                gridGLList.vertices = np.array(vertexList, dtype=np.float32)
                gridGLList.indices = np.array(indexList, dtype=np.uint32)
                gridGLList.colors = np.array(colorList, dtype=np.float32)

                # restrict the labelling to the maximum without overlap based on width
                # should be dependent on font size though
                while len(labelling['0']) > (self.w / 60.0):
                    #restrict X axis labelling
                    lStrings = labelling['0']
                    if check(lStrings[0]):
                        labelling['0'] = lStrings[0::2]  # [ls for ls in lStrings if check(ls)]
                    else:
                        labelling['0'] = lStrings[1::2]  # [ls for ls in lStrings if check(ls)]

                # # clean up strings if in _intFormat
                # if self.XMode == self._intFormat:
                #     for ll in labelling['0'][::-1]:
                #         if round(ll[3], 5) != int(ll[3]):
                #             # remove the item
                #             labelling['0'].remove(ll)

                while len(labelling['1']) > (self.h / 20.0):
                    #restrict Y axis labelling
                    lStrings = labelling['1']
                    if check(lStrings[0]):
                        labelling['1'] = lStrings[0::2]  # [ls for ls in lStrings if check(ls)]
                    else:
                        labelling['1'] = lStrings[1::2]  # [ls for ls in lStrings if check(ls)]

                # # clean up strings if in _intFormat
                # if self.YMode == self._intFormat:
                #     for ll in labelling['1'][::-1]:
                #         if round(ll[3], 5) != int(ll[3]):
                #             # remove the item
                #             labelling['1'].remove(ll)

        return labelling, axesChanged

    def buildGrid(self):
        """Build the grids for the mainGrid and the bottom/right axes
        """
        # build the axes
        if self.highlighted:
            if self._axisType == 1:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0],
                                                                       r=self.highlightColour[0],
                                                                       g=self.highlightColour[1],
                                                                       b=self.highlightColour[2], transparency=32.0)
            else:  # self._axisType == 0:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0],
                                                                       r=self.highlightColour[0],
                                                                       g=self.highlightColour[1],
                                                                       b=self.highlightColour[2], transparency=32.0)
        else:
            if self._axisType == 1:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0],
                                                                       r=self.foreground[0],
                                                                       g=self.foreground[1],
                                                                       b=self.foreground[2], transparency=32.0)
            else:  # self._axisType == 0:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0],
                                                                       r=self.foreground[0],
                                                                       g=self.foreground[1],
                                                                       b=self.foreground[2], transparency=32.0)

        # buffer the lists to VBOs
        for gr in self.gridList[1:]:
            gr.defineIndexVBO(enableVBO=True)

    def drawGrid(self):
        # set to the mainView and draw the grid
        # self.buildGrid()

        GL.glEnable(GL.GL_BLEND)
        GL.glLineWidth(1.0 * self.viewports._devicePixelRatio)

        # draw the axes tick marks (effectively the same grid in smaller viewport)
        if self._axesVisible:
            if self._drawRightAxis and self._axisType == 1:
                # draw the grid marks for the right axis
                self.viewports.setViewport(self._currentRightAxisView)
                self.gridList[1].drawIndexVBO(enableVBO=True)

            if self._drawBottomAxis and self._axisType == 0:
                # draw the grid marks for the bottom axis
                self.viewports.setViewport(self._currentBottomAxisView)
                self.gridList[2].drawIndexVBO(enableVBO=True)

    @contextmanager
    def _disableGLAliasing(self):
        """Disable aliasing for the contained routines
        """
        try:
            GL.glDisable(GL.GL_MULTISAMPLE)
            yield
        finally:
            GL.glEnable(GL.GL_MULTISAMPLE)

    @contextmanager
    def _enableGLAliasing(self):
        """Enable aliasing for the contained routines
        """
        try:
            GL.glEnable(GL.GL_MULTISAMPLE)
            yield
        finally:
            GL.glDisable(GL.GL_MULTISAMPLE)

    def _buildSpectrumSetting(self, spectrumView, stackCount=0):
        # if spectrumView.spectrum.headerSize == 0:
        #     return

        self._spectrumSettings[spectrumView] = {}

        self._spectrumValues = spectrumView._getValues()

        # set defaults for undefined spectra
        if not self._spectrumValues[0].pointCount:
            dx = -1.0 if self.INVERTXAXIS else -1.0
            fx0, fx1 = 1.0, -1.0
            dxAF = fx0 - fx1
            xScale = dx * dxAF

            dy = -1.0 if self.INVERTYAXIS else -1.0
            fy0, fy1 = 1.0, -1.0
            dyAF = fy0 - fy1
            yScale = dy * dyAF

            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fx0 - fx1))
            self._maxXRange = max(self._maxXRange, (fx0 - fx1))
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fy0 - fy1))
            self._maxYRange = max(self._maxYRange, (fy0 - fy1))

        else:

            # get the bounding box of the spectra
            dx = -1.0 if self.INVERTXAXIS else -1.0  # self.sign(self.axisR - self.axisL)
            fx0, fx1 = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency

            # check tolerances
            if not self._widthsChangedEnough((fx0, 0.0), (fx1, 0.0), tol=1e-10):
                fx0, fx1 = 1.0, -1.0

            dxAF = fx0 - fx1
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            if spectrumView.spectrum.dimensionCount > 1:
                dy = -1.0 if self.INVERTYAXIS else -1.0  # self.sign(self.axisT - self.axisB)
                fy0, fy1 = self._spectrumValues[1].maxSpectrumFrequency, self._spectrumValues[1].minSpectrumFrequency

                # check tolerances
                if not self._widthsChangedEnough((fy0, 0.0), (fy1, 0.0), tol=1e-10):
                    fy0, fy1 = 1.0, -1.0

                dyAF = fy0 - fy1
                yScale = dy * dyAF / self._spectrumValues[1].pointCount

                # set to nD limits to twice the width of the spectrum and a few data points
                self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fx0 - fx1) / self._spectrumValues[0].pointCount)
                self._maxXRange = max(self._maxXRange, (fx0 - fx1))
                self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fy0 - fy1) / self._spectrumValues[1].pointCount)
                self._maxYRange = max(self._maxYRange, (fy0 - fy1))

            else:
                dy = -1.0 if self.INVERTYAXIS else -1.0  # dy = self.sign(self.axisT - self.axisB)

                if spectrumView.spectrum.intensities is not None and spectrumView.spectrum.intensities.size != 0:
                    fy0, fy1 = np.max(spectrumView.spectrum.intensities), np.min(spectrumView.spectrum.intensities)
                else:
                    fy0, fy1 = 0.0, 0.0

                # check tolerances
                if not self._widthsChangedEnough((fy0, 0.0), (fy1, 0.0), tol=1e-10):
                    fy0, fy1 = 1.0, -1.0

                dyAF = fy0 - fy1
                yScale = dy * dyAF / 1.0

                # set to 1D limits to twice the width of the spectrum and the intensity limit
                self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fx0 - fx1) / max(self._spectrumValues[0].pointCount, self.SPECTRUMXZOOM))
                self._maxXRange = max(self._maxXRange, (fx0 - fx1))
                # self._minYRange = min(self._minYRange, 3.0 * (fy0 - fy1) / self.SPECTRUMYZOOM)
                self._minYRange = min(self._minYRange, self._intensityLimit)
                self._maxYRange = max(self._maxYRange, (fy0 - fy1))

                self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX] = np.zeros((16,), dtype=np.float32)

                # if self._stackingMode:
                stX = stackCount * self._stackingValue[0]
                stY = stackCount * self._stackingValue[1]
                # stackCount += 1
                self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX][0:16] = [1.0, 0.0, 0.0, 0.0,
                                                                                             0.0, 1.0, 0.0, 0.0,
                                                                                             0.0, 0.0, 1.0, 0.0,
                                                                                             stX, stY, 0.0, 1.0]
                self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIXOFFSET] = (stX, stY)

                # else:
                #     self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX][0:16] = [1.0, 0.0, 0.0, 0.0,
                #                                                                                  0.0, 1.0, 0.0, 0.0,
                #                                                                                  0.0, 0.0, 1.0, 0.0,
                #                                                                                  0.0, 0.0, 0.0, 1.0]

        self._rangeXDefined = True
        self._rangeYDefined = True

        # create modelview matrix for the spectrum to be drawn
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX] = np.zeros((16,), dtype=np.float32)

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX][0:16] = [xScale, 0.0, 0.0, 0.0,
                                                                              0.0, yScale, 0.0, 0.0,
                                                                              0.0, 0.0, 1.0, 0.0,
                                                                              fx0, fy0, 0.0, 1.0]
        # setup information for the horizontal/vertical traces
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXXALIAS] = fx0
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINXALIAS] = fx1
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXYALIAS] = fy0
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINYALIAS] = fy1
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DXAF] = dxAF
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DYAF] = dyAF
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XSCALE] = xScale
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YSCALE] = yScale
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SPINNINGRATE] = spectrumView.spectrum.spinningRate

        # indices = getAxisCodeMatchIndices(spectrumView.spectrum.axisCodes, self.strip.axisCodes)
        indices = getAxisCodeMatchIndices(self.spectrumDisplay.axisCodes, spectrumView.spectrum.axisCodes)

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YSCALE] = yScale

        if len(self._spectrumValues) > 2:
            # store a list for the extra dimensions
            vPP = ()
            dDim = ()
            vTP = ()
            for dim in range(2, len(self._spectrumValues)):
                specVal = self._spectrumValues[dim]
                specDataDim = specVal.dataDim

                vPP = vPP + (specVal.valuePerPoint,)
                dDim = dDim + (specDataDim,)

                # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = specVal.valuePerPoint
                # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DATADIM] = specVal.dataDim

                if hasattr(specDataDim, 'primaryDataDimRef'):
                    ddr = specDataDim.primaryDataDimRef
                    valueToPoint = ddr and ddr.valueToPoint
                else:
                    valueToPoint = specDataDim.valueToPoint

                vTP = vTP + (valueToPoint,)
                # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUETOPOINT] = valueToPoint

            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = vPP
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DATADIM] = dDim
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUETOPOINT] = vTP

        else:
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = None
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DATADIM] = None
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUETOPOINT] = None

        self._maxX = max(self._maxX, fx0)
        self._minX = min(self._minX, fx1)
        self._maxY = max(self._maxY, fy0)
        self._minY = min(self._minY, fy1)

    def buildSpectra(self):
        if self.spectrumDisplay.isDeleted:
            return

        # self._spectrumSettings = {}
        rebuildFlag = False
        for spectrumView in self._ordering:  # strip.spectrumViews:
            if spectrumView.isDeleted:
                continue

            self._buildSpectrumSetting(spectrumView=spectrumView)
            rebuildFlag = True

    def _buildGL(self):
        """Separate the building of the display from the paint event; not sure that this is required
        """
        # only call if the axes have changed
        # self._updateAxes = True

        if self._updateAxes:
            self.buildGrid()
            self._updateAxes = False

        self.buildSpectra()

    def _paintGLMouseOnly(self):
        """paintGL event - paint only the mouse in Xor mode
        """
        # No mouse cursor
        pass

    def _paintGL(self):
        w = self.w
        h = self.h

        if self._updateBackgroundColour:
            self._updateBackgroundColour = False
            self.setBackgroundColour(self.background, silent=True)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glEnable(GL.GL_MULTISAMPLE)

        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        # start with the grid mapped to (0..1, 0..1) to remove zoom errors here
        currentShader.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        with self._disableGLAliasing():
            # draw the grid components
            self.drawGrid()

        currentShader = self.globalGL._shaderProgramTex.makeCurrent()

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 1.0, 1.0]
        currentShader.setGLUniform4fv('axisScale', 1, self._axisScale)

        # draw the text to the screen
        self.enableTexture()
        self.enableTextClientState()
        self._setViewPortFontScale()

        # make the overlay/axis solid
        currentShader.setBlendEnabled(0)
        self.drawAxisLabels()
        currentShader.setBlendEnabled(1)

        self.disableTextClientState()
        self.disableTexture()

        # # use the current viewport matrix to display the last bit of the axes
        # currentShader = self.globalGL._shaderProgram1.makeCurrent()
        # currentShader.setProjectionAxes(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, -1, h - self.AXIS_MOUSEYOFFSET,
        #                                 -1.0, 1.0)
        #
        # self.viewports.setViewport(self._currentView)
        #
        # # why are these labelled the other way round?
        # currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uVMatrix)
        # currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

    @pyqtSlot(dict)
    def _glAxisUnitsChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # read values from dataDict and set units
            if aDict[GLNotifier.GLVALUES]:  # and aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]:

                self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]

                aL = aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]
                uFA = aDict[GLNotifier.GLVALUES][GLDefs.AXISUSEDEFAULTASPECTRATIO]
                if self._axisLocked != aL or self._useDefaultAspect != uFA:
                    # self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                    # self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]
                    self._axisLocked = aL
                    self._useDefaultAspect = uFA

                    aDict = {GLNotifier.GLSOURCE         : None,
                             GLNotifier.GLSPECTRUMDISPLAY: self.spectrumDisplay,
                             GLNotifier.GLVALUES         : (aL, uFA)
                             }
                    self._glAxisLockChanged(aDict)

            # spawn rebuild event for the grid
            self._updateAxes = True
            if self.gridList:
                for gr in self.gridList:
                    gr.renderMode = GLRENDERMODE_REBUILD
            self.update()

    def _initialiseAll(self):
        """Initialise all attributes for the display
        """
        # if self.glReady: return

        self.w = self.width()
        self.h = self.height()

        self._threads = {}
        self._threadUpdate = False

        self.lastPos = QtCore.QPoint()
        self._mouseX = 0
        self._mouseY = 0
        self._mouseStart = (0.0, 0.0)
        self._mouseEnd = (0.0, 0.0)

        self.pixelX = 1.0
        self.pixelY = 1.0
        self.deltaX = 1.0
        self.deltaY = 1.0
        self.symbolX = 1.0
        self.symbolY = 1.0

        self.peakWidthPixels = 16

        # set initial axis limits - should be changed by strip.display..
        self.axisL = -1.0
        self.axisR = 1.0
        self.axisT = 1.0
        self.axisB = -1.0
        self.storedZooms = []
        self._currentZoom = 0
        self._zoomHistory = [None] * ZOOMHISTORYSTORE
        self._zoomHistoryCurrent = 0
        self._zoomHistoryHead = 0
        self._zoomTimerLast = time.time()

        self.base = None
        self.spectrumValues = []

        self.highlighted = False
        self._drawSelectionBox = False
        self._drawMouseMoveLine = False
        self._drawDeltaOffset = False
        self._selectionMode = 0
        self._startCoordinate = None
        self._endCoordinate = None
        self.cursorSource = CURSOR_SOURCE_NONE  # can be CURSOR_SOURCE_NONE / CURSOR_SOURCE_SELF / CURSOR_SOURCE_OTHER
        self.cursorCoordinate = np.zeros((4,), dtype=np.float32)
        self.doubleCursorCoordinate = np.zeros((4,), dtype=np.float32)

        self._shift = False
        self._command = False
        self._key = ''
        self._isSHIFT = ''
        self._isCTRL = ''
        self._isALT = ''
        self._isMETA = ''

        self._lastClick = None
        self._mousePressed = False
        self._draggingLabel = False

        self.buildMarks = True
        self._marksList = None
        self._infiniteLines = []
        self._regionList = None
        self._orderedAxes = None
        self._axisOrder = None
        self._axisCodes = None
        self._refreshMouse = False
        self._successiveClicks = None  # GWV: Store successive click events for zooming; None means first click not set
        self._dottedCursorCoordinate = None
        self._dottedCursorVisible = None
        self._spectrumBordersVisible = True

        self.gridList = []
        self._gridVisible = True  #self._preferences.showGrid
        self._crosshairVisible = True  #self._preferences.showCrosshair
        self._doubleCrosshairVisible = True  #self._preferences.showDoubleCrosshair
        self._sideBandsVisible = True

        self.diagonalGLList = None
        self.diagonalSideBandsGLList = None
        self.boundingBoxes = None
        self._updateAxes = True

        self._axesVisible = True
        self._useLockedAspect = False
        self._useDefaultAspect = False
        self._aspectRatios = {}

        self._fixedAspectX = 1.0
        self._fixedAspectY = 1.0

        self._showSpectraOnPhasing = False
        self._xUnits = 0
        self._yUnits = 0

        self._drawRightAxis = True
        self._drawBottomAxis = True
        self.modeDecimal = [False, False]

        # here for completeness, although they should be updated in rescale
        self._currentView = GLDefs.MAINVIEW
        self._currentRightAxisView = GLDefs.RIGHTAXIS
        self._currentRightAxisBarView = GLDefs.RIGHTAXISBAR
        self._currentBottomAxisView = GLDefs.BOTTOMAXIS
        self._currentBottomAxisBarView = GLDefs.BOTTOMAXISBAR

        self._oldStripIDLabel = None
        self.stripIDString = None
        self._spectrumSettings = {}
        self._newStripID = False

        self._setColourScheme()

        self._updateHTrace = False
        self._updateVTrace = False
        self._lastTracePoint = {}  # [-1, -1]
        self.showActivePhaseTrace = True

        self._applyXLimit = True  #.zoomXLimitApply
        self._applyYLimit = True  #self._preferences.zoomYLimitApply
        self._intensityLimit = True  #self._preferences.intensityLimit

        self._GLIntegralLists = {}
        self._GLIntegralLabels = {}

        self._marksAxisCodes = []

        self._regions = []
        self._infiniteLines = []
        self._buildTextFlag = True

        self._buildMouse = True
        self._mouseCoords = [-1.0, -1.0]
        self.mouseString = None
        # self.diffMouseString = None
        self._symbolLabelling = 0
        self._symbolType = 0
        self._symbolSize = 0
        self._symbolThickness = 0

        self._contourList = {}

        self._hTraces = {}
        self._vTraces = {}
        self._staticHTraces = []
        self._staticVTraces = []
        self._currentTraces = []
        self._axisXLabelling = []
        self._axisYLabelling = []
        self._axisScaleLabelling = []
        self._axisType = 0

        self._stackingValue = (0.0, 0.0)
        self._stackingMode = False
        self._hTraceVisible = False
        self._vTraceVisible = False
        self.w = 0
        self.h = 0

        self._uPMatrix = np.zeros((16,), dtype=np.float32)
        self._uMVMatrix = np.zeros((16,), dtype=np.float32)
        self._uVMatrix = np.zeros((16,), dtype=np.float32)
        self._dataMatrix = np.zeros((16,), dtype=np.float32)
        self._aMatrix = np.zeros((16,), dtype=np.float32)
        self._IMatrix = np.zeros((16,), dtype=np.float32)
        self._IMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                               0.0, 1.0, 0.0, 0.0,
                               0.0, 0.0, 1.0, 0.0,
                               0.0, 0.0, 0.0, 1.0]

        self.vInv = None
        self.mouseTransform = None

        self._useTexture = np.zeros((1,), dtype=np.int)
        self._axisScale = np.zeros((4,), dtype=np.float32)
        self._background = np.zeros((4,), dtype=np.float32)
        self._parameterList = np.zeros((4,), dtype=np.int32)
        self._view = np.zeros((4,), dtype=np.float32)
        self._updateBackgroundColour = True

        # get information from the parent class (strip)
        # self.orderedAxes = self.spectrumDisplay.orderedAxes
        self.axisOrder = self.spectrumDisplay.axisOrder
        self.axisCodes = self.spectrumDisplay.axisCodes

        self._dragRegions = set()

        self.resetRangeLimits()

        self._ordering = []
        self._visibleOrdering = []
        self._firstVisible = None
        self.visiblePlaneList = {}
        self.visiblePlaneListPointValues = {}
        self._visibleSpectrumViewsChange = False
        self._matchingIsotopeCodes = False

        self._glClientIndex = 0
        self._menuActive = False
        self.glReady = True

    def _setColourScheme(self):
        """Update colours from colourScheme
        """
        self.colours = getColours()
        self.hexBackground = self.colours[CCPNGLWIDGET_HEXBACKGROUND]
        self.background = self.colours[CCPNGLWIDGET_BACKGROUND]
        self.foreground = self.colours[CCPNGLWIDGET_FOREGROUND]
        self.mousePickColour = self.colours[CCPNGLWIDGET_PICKCOLOUR]
        self.gridColour = self.colours[CCPNGLWIDGET_GRID]
        self.highlightColour = self.colours[CCPNGLWIDGET_HIGHLIGHT]
        self._labellingColour = self.colours[CCPNGLWIDGET_LABELLING]
        self._phasingTraceColour = self.colours[CCPNGLWIDGET_PHASETRACE]

        self.zoomAreaColour = self.colours[CCPNGLWIDGET_ZOOMAREA]
        self.pickAreaColour = self.colours[CCPNGLWIDGET_PICKAREA]
        self.selectAreaColour = self.colours[CCPNGLWIDGET_SELECTAREA]
        self.zoomLineColour = self.colours[CCPNGLWIDGET_ZOOMLINE]
        self.mouseMoveLineColour = self.colours[CCPNGLWIDGET_MOUSEMOVELINE]

        self.zoomAreaColourHard = (*self.colours[CCPNGLWIDGET_ZOOMAREA][0:3], CCPNGLWIDGET_HARDSHADE)
        self.pickAreaColourHard = (*self.colours[CCPNGLWIDGET_PICKAREA][0:3], CCPNGLWIDGET_HARDSHADE)
        self.selectAreaColourHard = (*self.colours[CCPNGLWIDGET_SELECTAREA][0:3], CCPNGLWIDGET_HARDSHADE)

    def resetRangeLimits(self, allLimits=True):
        # reset zoom limits for the display
        self._minXRange, self._maxXRange = GLDefs.RANGELIMITS
        self._minYRange, self._maxYRange = GLDefs.RANGELIMITS
        self._maxX, self._minX = GLDefs.AXISLIMITS
        self._maxY, self._minY = GLDefs.AXISLIMITS
        if allLimits:
            self._rangeXDefined = False
            self._rangeYDefined = False
            self._minXReached = False
            self._minYReached = False
            self._maxXReached = False
            self._maxYReached = False

            self._minReached = False
            self._maxReached = False

    @pyqtSlot(dict)
    def _glXAxisChanged(self, aDict):
        if self._useLockedAspect or self._useDefaultAspect:
            self._glAllAxesChanged(aDict)

        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match only the scale for the X axis
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]
            row = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPROW]
            col = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPCOLUMN]

            tilePos = self.tilePosition

            if self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):
                if self.spectrumDisplay.stripArrangement == 'Y':
                    if tilePos[1] == col:
                        self.axisL = axisL
                        self.axisR = axisR
                    else:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'X':
                    if tilePos[0] == row:
                        self.axisL = axisL
                        self.axisR = axisR
                    else:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff
                else:
                    raise
                self._rescaleXAxis()
                # self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAxisLockChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:
            self._useLockedAspect = aDict[GLNotifier.GLVALUES][0]
            self._useDefaultAspect = aDict[GLNotifier.GLVALUES][1]

            if (self._useLockedAspect or self._useDefaultAspect):

                # check which is the primary axis and update the opposite axis - similar to wheelEvent
                if self.spectrumDisplay.stripArrangement == 'Y':

                    # strips are arranged in a row
                    self._scaleToYAxis()

                elif self.spectrumDisplay.stripArrangement == 'X':

                    # strips are arranged in a column
                    self._scaleToXAxis()

                elif self.spectrumDisplay.stripArrangement == 'T':

                    # NOTE:ED - Tiled plots not fully implemented yet
                    getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

                else:
                    getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

            else:
                # paint to update lock button colours
                self.update()

    @pyqtSlot(dict)
    def _glAxisUnitsChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        # update the list of visible spectra
        self._updateVisibleSpectrumViews()

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # read values from dataDict and set units
            if aDict[GLNotifier.GLVALUES]:  # and aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]:

                self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]

                aL = aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]
                uFA = aDict[GLNotifier.GLVALUES][GLDefs.AXISUSEDEFAULTASPECTRATIO]
                if self._useLockedAspect != aL or self._useDefaultAspect != uFA:
                    # self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                    # self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]
                    self._useLockedAspect = aL
                    self._useDefaultAspect = uFA

                    changeDict = {GLNotifier.GLSOURCE         : None,
                                  GLNotifier.GLSPECTRUMDISPLAY: self.spectrumDisplay,
                                  GLNotifier.GLVALUES         : (aL, uFA)
                                  }
                    self._glAxisLockChanged(changeDict)

                self._aspectRatios.update(aDict[GLNotifier.GLVALUES][GLDefs.AXISASPECTRATIOS])
                if uFA:
                    self._rescaleAllZoom(rescale=True)

            # spawn rebuild event for the grid
            self._updateAxes = True
            if self.gridList:
                for gr in self.gridList:
                    gr.renderMode = GLRENDERMODE_REBUILD
            self.update()

    def _widthsChangedEnough(self, r1, r2, tol=1e-5):
        if len(r1) != len(r2):
            raise ValueError('WidthsChanged must be the same length')

        for ii in zip(r1, r2):
            if abs(ii[0] - ii[1]) > tol:
                return True

    @pyqtSlot(dict)
    def _glYAxisChanged(self, aDict):
        if self._useLockedAspect or self._useDefaultAspect:
            self._glAllAxesChanged(aDict)

        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match the Y axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]
            row = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPROW]
            col = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPCOLUMN]

            tilePos = self.tilePosition

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]):
                if self.spectrumDisplay.stripArrangement == 'Y':
                    if tilePos[0] == row:
                        self.axisB = axisB
                        self.axisT = axisT
                    else:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'X':
                    if tilePos[1] == col:
                        self.axisB = axisB
                        self.axisT = axisT
                    else:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff
                else:
                    raise

                self._rescaleYAxis()
                # self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAllAxesChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        sDisplay = aDict[GLNotifier.GLSPECTRUMDISPLAY]
        source = aDict[GLNotifier.GLSOURCE]

        if source != self and sDisplay == self.spectrumDisplay:

            # match the values for the Y axis, and scale for the X axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]
            row = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPROW]
            col = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPCOLUMN]

            tilePos = self.tilePosition

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]) and \
                    self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):

                # # do the matching row and column only unless _useLockedAspect or self._useDefaultAspect are set
                # if not (tilePos[0] == row or tilePos[1] == col) and \
                #         not (self._useLockedAspect or self._useDefaultAspect):
                #     return

                if self.spectrumDisplay.stripArrangement == 'Y':

                    # strips are arranged in a row
                    if tilePos[1] == col:
                        self.axisL = axisL
                        self.axisR = axisR
                    elif self._useLockedAspect or self._useDefaultAspect:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff

                    if tilePos[0] == row:
                        self.axisB = axisB
                        self.axisT = axisT
                    elif self._useLockedAspect or self._useDefaultAspect:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'X':

                    # strips are arranged in a column
                    if tilePos[1] == col:
                        self.axisB = axisB
                        self.axisT = axisT
                    elif self._useLockedAspect or self._useDefaultAspect:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff

                    if tilePos[0] == row:
                        self.axisL = axisL
                        self.axisR = axisR
                    elif self._useLockedAspect or self._useDefaultAspect:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'T':

                    # NOTE:ED - Tiled plots not fully implemented yet
                    pass

                else:
                    # currently ignore - warnings will be logged elsewhere
                    pass

                self._rescaleAllAxes()
                # self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glMouseMoved(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self:
            # self.cursorCoordinate = aDict[GLMOUSECOORDS]
            # self.update()

            mouseMovedDict = aDict[GLNotifier.GLMOUSEMOVEDDICT]

            if self._crosshairVisible:  # or self._updateVTrace or self._updateHTrace:

                exactMatch = (self._preferences.matchAxisCode == AXIS_FULLATOMNAME)
                indices = getAxisCodeMatchIndices(self.spectrumDisplay.axisCodes[:2], mouseMovedDict[AXIS_ACTIVEAXES], exactMatch=exactMatch)

                for n in range(2):
                    if indices[n] is not None:

                        axis = mouseMovedDict[AXIS_ACTIVEAXES][indices[n]]
                        self.cursorSource = CURSOR_SOURCE_OTHER
                        self.cursorCoordinate[n] = mouseMovedDict[AXIS_FULLATOMNAME][axis]

                        # coordinates have already been flipped
                        self.doubleCursorCoordinate[1 - n] = self.cursorCoordinate[n]

                    else:
                        self.cursorSource = CURSOR_SOURCE_OTHER
                        self.cursorCoordinate[n] = None
                        self.doubleCursorCoordinate[1 - n] = None

                self.current.cursorPosition = (self.cursorCoordinate[0], self.cursorCoordinate[1])

                # only need to redraw if we can see the cursor
                # if self._updateVTrace or self._updateHTrace:
                #   self.updateTraces()

                # self._renderCursorOnly()

                # force a redraw to only paint the cursor
                # self._paintMode = PAINTMODES.PAINT_MOUSEONLY
                # self.update(mode=PAINTMODES.PAINT_ALL)
                self.update(mode=PAINTMODES.PAINT_MOUSEONLY)

    def update(self, mode=PAINTMODES.PAINT_ALL):
        """Update the glWidget with the correct refresh mode
        """
        self._paintMode = mode
        super().update()

    @pyqtSlot(dict)
    def _glEvent(self, aDict):
        """Process events from the application/popups and other strips
        :param aDict - dictionary containing event flags:
        """
        if self.spectrumDisplay.isDeleted:
            return

        if not self.globalGL:
            return

        if aDict:
            if aDict[GLNotifier.GLSOURCE] != self:

                # check the params for actions and update the display
                triggers = aDict[GLNotifier.GLTRIGGERS]
                targets = aDict[GLNotifier.GLTARGETS]

                if triggers or targets:

                    if GLNotifier.GLRESCALE in triggers:
                        self._rescaleXAxis(update=False)

                    if GLNotifier.GLPREFERENCES in triggers:
                        self._preferencesUpdate()
                        self._rescaleXAxis(update=False)

        # repaint
        self.update()

    def initializeGL(self):
        # GLversionFunctions = self.context().versionFunctions()
        # GLversionFunctions.initializeOpenGLFunctions()
        # self._GLVersion = GLversionFunctions.glGetString(GL.GL_VERSION)

        # initialise a common to all OpenGL windows
        self.globalGL = GLGlobalData(parent=self, strip=None, spectrumDisplay=self.spectrumDisplay)
        self._glClientIndex = self.globalGL.getNextClientIndex()

        # initialise the arrays for the grid and axes
        self.gridList = []
        for li in range(3):
            self.gridList.append(GLVertexArray(numLists=1,
                                               renderMode=GLRENDERMODE_REBUILD,
                                               blendMode=False,
                                               drawMode=GL.GL_LINES,
                                               dimension=2,
                                               GLContext=self))

        self.viewports = GLViewports()
        self._initialiseViewPorts()

        # This is the correct blend function to ignore stray surface blending functions
        GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)
        self.setBackgroundColour(self.background, silent=True)
        self.globalGL._shaderProgramTex.setBlendEnabled(0)

        self.updateVisibleSpectrumViews()
        self.initialiseAxes()
        self._attachParentStrip()

        # set the painting mode
        self._paintMode = PAINTMODES.PAINT_ALL
        self._paintLastFrame = True
        self._leavingWidget = False

        # check that the screen device pixel ratio is correct
        self.refreshDevicePixelRatio()

        # set the pyqtsignal responders
        self.GLSignals.glXAxisChanged.connect(self._glXAxisChanged)
        self.GLSignals.glYAxisChanged.connect(self._glYAxisChanged)
        self.GLSignals.glAllAxesChanged.connect(self._glAllAxesChanged)
        self.GLSignals.glMouseMoved.connect(self._glMouseMoved)
        self.GLSignals.glEvent.connect(self._glEvent)
        self.GLSignals.glAxisLockChanged.connect(self._glAxisLockChanged)
        self.GLSignals.glAxisUnitsChanged.connect(self._glAxisUnitsChanged)

    def _attachParentStrip(self):
        self._parentStrip.stripResized.connect(self._parentResize)

    def _parentResize(self, size):
        return
        if self._axisType == 0:
            # axis widget is an X widget so grab connected width
            self.setMaximumWidth(size[0])

        else:
            # axis widget is a Y widget so grab connected height
            self.setMaximumHeight(size[1])

    # def _clearGLCursorQueue(self):
    #     for glBuf in self._glCursorQueue:
    #         glBuf.clearArrays()
    #     self._glCursorHead = 0
    #     self._glCursorTail = (self._glCursorHead - 1) % self._numBuffers
    #
    # def _advanceGLCursor(self):
    #     """Advance the pointers for the cursor glLists
    #     """
    #     self._glCursorHead = (self._glCursorHead + 1) % self._numBuffers
    #     self._glCursorTail = (self._glCursorHead - 1) % self._numBuffers

    def initialiseAxes(self, strip=None):
        """setup the correct axis range and padding
        """

        # need to get the matching strip at the correct tilePosition
        tilePos = self._tilePosition

        if tilePos[1] == -1:
            # this should be the axes to the right of a row

            if self.spectrumDisplay.stripArrangement == 'Y':
                stripList = self.spectrumDisplay.stripRow(tilePos[0])
            else:
                stripList = self.spectrumDisplay.stripColumn(tilePos[0])

        elif tilePos[0] == -1:
            # this should be the axis at the bottom of a column

            if self.spectrumDisplay.stripArrangement == 'Y':
                stripList = self.spectrumDisplay.stripColumn(tilePos[1])
            else:
                stripList = self.spectrumDisplay.stripRow(tilePos[1])
        else:
            raise ValueError('Badly defined axisWidget position')

        if not stripList:
            getLogger().warning('Error initialising axis widget, no strips found')

        self._orderedAxes = stripList[0].axes
        self._axisCodes = stripList[0].axisCodes
        self._axisOrder = stripList[0].axisOrder

        # use this to link to the parent height/width
        self._parentStrip = stripList[0]

        axis = self._orderedAxes[0]
        if self.INVERTXAXIS:
            self.axisL = max(axis.region[0], axis.region[1])
            self.axisR = min(axis.region[0], axis.region[1])
        else:
            self.axisL = min(axis.region[0], axis.region[1])
            self.axisR = max(axis.region[0], axis.region[1])

        axis = self._orderedAxes[1]
        if self.INVERTYAXIS:
            self.axisB = max(axis.region[0], axis.region[1])
            self.axisT = min(axis.region[0], axis.region[1])
        else:
            self.axisB = min(axis.region[0], axis.region[1])
            self.axisT = max(axis.region[0], axis.region[1])
        self.update()

    def _initialiseViewPorts(self):
        """Initialise all the viewports for the widget
        """
        self.viewports.clearViewports()

        # define the main viewports
        if self.AXIS_INSIDE:
            self.viewports.addViewport(GLDefs.MAINVIEW, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLWIDTH, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLHEIGHT, self, (0, 'a'), (0, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (0, 'h'))
        else:
            self.viewports.addViewport(GLDefs.MAINVIEW, self, (0, 'a'), (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLWIDTH, self, (0, 'a'), (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (0, 'w'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLHEIGHT, self, (0, 'a'), (0, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (0, 'h'))

        # define the viewports for the right axis bar
        if self.AXIS_INSIDE:
            self.viewports.addViewport(GLDefs.RIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                       (self.AXIS_MARGINBOTTOM, 'a'),
                                       (self.AXIS_LINE, 'a'), (-self.AXIS_MARGINBOTTOM, 'h'))
            self.viewports.addViewport(GLDefs.RIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'),
                                       (self.AXIS_MARGINBOTTOM, 'a'),
                                       (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        else:
            self.viewports.addViewport(GLDefs.RIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                       (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (self.AXIS_LINE, 'a'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

            self.viewports.addViewport(GLDefs.RIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'),
                                       (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (0, 'w'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                   (0, 'a'),
                                   (self.AXIS_LINE, 'a'), (0, 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'),
                                   (0, 'w'), (0, 'h'))

        # define the viewports for the bottom axis bar
        if self.AXIS_INSIDE:
            self.viewports.addViewport(GLDefs.BOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_LINE, 'a'))

            self.viewports.addViewport(GLDefs.BOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))
        else:
            self.viewports.addViewport(GLDefs.BOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (self.AXIS_LINE, 'a'))

            self.viewports.addViewport(GLDefs.BOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (self.AXIS_LINE, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                   (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # define the full viewport
        self.viewports.addViewport(GLDefs.FULLVIEW, self, (0, 'a'), (0, 'a'), (0, 'w'), (0, 'h'))

        # define the remaining corner
        self.viewports.addViewport(GLDefs.AXISCORNER, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'), (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # define an empty view (for printing mainly)
        self.viewports.addViewport(GLDefs.BLANKVIEW, self, (0, 'a'), (0, 'a'), (0, 'a'), (0, 'a'))

    def refreshDevicePixelRatio(self):
        """refresh the devicePixelRatio for the viewports
        """
        newPixelRatio = self.devicePixelRatio()
        if newPixelRatio != self.lastPixelRatio:
            self.lastPixelRatio = newPixelRatio
            if hasattr(self, GLDefs.VIEWPORTSATTRIB):
                self.viewports._devicePixelRatio = newPixelRatio
            self.update()

    def _preferencesUpdate(self):
        """update GL values after the preferences have changed
        """
        self._preferences = self.application.preferences.general
        self._setColourScheme()

        # set the new limits
        self._applyXLimit = self._preferences.zoomXLimitApply
        self._applyYLimit = self._preferences.zoomYLimitApply
        self._intensityLimit = self._preferences.intensityLimit

        # set the flag to update the background in the paint event
        self._updateBackgroundColour = True

    def setBackgroundColour(self, col, silent=False):
        """
        set all background colours in the shaders
        :param col - vec4, 4 element list e.g.: [0.05, 0.05, 0.05, 1.0], very dark gray
        """
        GL.glClearColor(*col)
        self.background = np.array(col, dtype=np.float32)

        self.globalGL._shaderProgram1.makeCurrent()
        self.globalGL._shaderProgram1.setBackground(self.background)
        self.globalGL._shaderProgramTex.makeCurrent()
        self.globalGL._shaderProgramTex.setBackground(self.background)
        if not silent:
            self.update()

    def enableTextClientState(self):
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glEnableVertexAttribArray(self._glClientIndex)

    def disableTextClientState(self):
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableVertexAttribArray(self._glClientIndex)

    def _setViewPortFontScale(self):
        # set the scale for drawing the overlay text correctly
        self._axisScale[0:4] = [self.deltaX, self.deltaY, 1.0, 1.0]
        self.globalGL._shaderProgramTex.setGLUniform4fv('axisScale', 1, self._axisScale)
        self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0, 1.0, -1.0, 1.0)
        self.globalGL._shaderProgramTex.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

    def buildAxisLabels(self, refresh=False):
        # build axes labelling
        if refresh or self.axesChanged:

            self._axisXLabelling = []
            self._axisScaleLabelling = []

            if self.highlighted:
                labelColour = self.highlightColour
            else:
                labelColour = self.foreground

            smallFont = self.getSmallFont()
            fScale = smallFont.scale

            if self._drawBottomAxis and self._axisType == 0:
                # create the X axis labelling
                for axLabel in self.axisLabelling['0']:
                    axisX = axLabel[2]
                    axisXLabel = axLabel[3]

                    # axisXText = str(int(axisXLabel)) if axLabel[4] >= 1 else str(axisXLabel)
                    axisXText = self._intFormat(axisXLabel) if axLabel[4] >= 1 else self.XMode(axisXLabel)

                    self._axisXLabelling.append(GLString(text=axisXText,
                                                         font=smallFont,
                                                         x=axisX - (0.4 * smallFont.width * self.deltaX * len(
                                                                 axisXText) / fScale),
                                                         y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * smallFont.height / fScale,

                                                         colour=labelColour, GLContext=self,
                                                         obj=None))

                # append the axisCode
                self._axisXLabelling.append(GLString(text=self.axisCodes[0],
                                                     font=smallFont,
                                                     x=GLDefs.AXISTEXTXOFFSET * self.deltaX,
                                                     y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * smallFont.height / fScale,
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))
                # and the axis dimensions
                xUnitsLabels = self.XAXES[self._xUnits]
                self._axisXLabelling.append(GLString(text=xUnitsLabels,
                                                     font=smallFont,
                                                     x=1.0 - (self.deltaX * len(xUnitsLabels) * smallFont.width / fScale),
                                                     y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * smallFont.height / fScale,
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))

            self._axisYLabelling = []

            if self._drawRightAxis and self._axisType == 1:
                # create the Y axis labelling
                for xx, ayLabel in enumerate(self.axisLabelling['1']):
                    axisY = ayLabel[2]
                    axisYLabel = ayLabel[3]

                    if self.YAXISUSEEFORMAT:
                        axisYText = self.YMode(axisYLabel)
                    else:
                        # axisYText = str(int(axisYLabel)) if ayLabel[4] >= 1 else str(axisYLabel)
                        axisYText = self._intFormat(axisYLabel) if ayLabel[4] >= 1 else self.YMode(axisYLabel)

                    self._axisYLabelling.append(GLString(text=axisYText,
                                                         font=smallFont,
                                                         x=self.AXIS_OFFSET,
                                                         y=axisY - (GLDefs.AXISTEXTYOFFSET * self.deltaY),
                                                         colour=labelColour, GLContext=self,
                                                         obj=None))

                # append the axisCode
                self._axisYLabelling.append(GLString(text=self.axisCodes[1],
                                                     font=smallFont,
                                                     x=self.AXIS_OFFSET,
                                                     y=1.0 - (GLDefs.TITLEYOFFSET * smallFont.height * self.deltaY / fScale),
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))
                # and the axis dimensions
                yUnitsLabels = self.YAXES[self._yUnits]
                self._axisYLabelling.append(GLString(text=yUnitsLabels,
                                                     font=smallFont,
                                                     x=self.AXIS_OFFSET,
                                                     y=1.0 * self.deltaY,
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))

    def drawAxisLabels(self):
        # draw axes labelling

        if self._axesVisible:
            self.buildAxisLabels()

            if self._drawBottomAxis and self._axisType == 0:
                # put the axis labels into the bottom bar
                self.viewports.setViewport(self._currentBottomAxisBarView)

                # self._axisScale[0:4] = [self.pixelX, 1.0, 1.0, 1.0]
                self._axisScale[0:4] = [self.deltaX, 1.0, 1.0, 1.0]

                self.globalGL._shaderProgramTex.setGLUniform4fv('axisScale', 1, self._axisScale)
                self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0,
                                                                  self.AXIS_MARGINBOTTOM, -1.0, 1.0)
                self.globalGL._shaderProgramTex.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

                for lb in self._axisXLabelling:
                    lb.drawTextArrayVBO(enableVBO=True)

            if self._drawRightAxis and self._axisType == 1:
                # put the axis labels into the right bar
                self.viewports.setViewport(self._currentRightAxisBarView)

                # self._axisScale[0:4] = [1.0, self.pixelY, 1.0, 1.0]
                self._axisScale[0:4] = [1.0, self.deltaY, 1.0, 1.0]

                self.globalGL._shaderProgramTex.setGLUniform4fv('axisScale', 1, self._axisScale)
                self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0, self.AXIS_MARGINRIGHT,
                                                                  0.0, 1.0, -1.0, 1.0)
                self.globalGL._shaderProgramTex.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

                for lb in self._axisYLabelling:
                    lb.drawTextArrayVBO(enableVBO=True)

    def enableTexture(self):
        GL.glEnable(GL.GL_BLEND)
        # GL.glEnable(GL.GL_TEXTURE_2D)
        # GL.glBindTexture(GL.GL_TEXTURE_2D, smallFont.textureId)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.getSmallFont().textureId)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.getSmallFont(transparent=True).textureId)

        # # specific blend function for text overlay
        # GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_DST_COLOR, GL.GL_ONE, GL.GL_ONE)

    def disableTexture(self):
        GL.glDisable(GL.GL_BLEND)

        # # reset blend function
        # GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)

    def _testAxisLimits(self, setLimits=False):
        xRange = abs(self.axisL - self.axisR) / 3.0
        yRange = abs(self.axisT - self.axisB) / 3.0
        self._minXReached = False
        self._minYReached = False
        self._maxXReached = False
        self._maxYReached = False

        if xRange < self._minXRange and self._rangeXDefined and self._applyXLimit:
            if setLimits:
                xMid = (self.axisR + self.axisL) / 2.0
                self.axisL = xMid - self._minXRange * np.sign(self.pixelX)
                self.axisR = xMid + self._minXRange * np.sign(self.pixelX)
            self._minXReached = True

        if yRange < self._minYRange and self._rangeYDefined and self._applyYLimit:
            if setLimits:
                yMid = (self.axisT + self.axisB) / 2.0
                self.axisT = yMid + self._minYRange * np.sign(self.pixelY)
                self.axisB = yMid - self._minYRange * np.sign(self.pixelY)
            self._minYReached = True

        if xRange > self._maxXRange and self._rangeXDefined and self._applyXLimit:
            if setLimits:
                xMid = (self.axisR + self.axisL) / 2.0
                self.axisL = xMid - self._maxXRange * np.sign(self.pixelX)
                self.axisR = xMid + self._maxXRange * np.sign(self.pixelX)
            self._maxXReached = True

        if yRange > self._maxYRange and self._rangeYDefined and self._applyYLimit:
            if setLimits:
                yMid = (self.axisT + self.axisB) / 2.0
                self.axisT = yMid + self._maxYRange * np.sign(self.pixelY)
                self.axisB = yMid - self._maxYRange * np.sign(self.pixelY)
            self._maxYReached = True

        self._minReached = self._minXReached or self._minYReached
        self._maxReached = self._maxXReached or self._maxYReached

    def _rescaleAllZoom(self, rescale=True):
        """Reset the zoomto fit the spectra, including aspect checking
        """
        _useFirstDefault = getattr(self.spectrumDisplay, '_useFirstDefault', False)
        if (self._useLockedAspect or self._useDefaultAspect or _useFirstDefault):

            # check which is the primary axis and update the opposite axis - similar to wheelEvent
            if self.spectrumDisplay.stripArrangement == 'Y':

                # strips are arranged in a row
                self._scaleToYAxis(rescale=rescale)

            elif self.spectrumDisplay.stripArrangement == 'X':

                # strips are arranged in a column
                self._scaleToXAxis(rescale=rescale)

            elif self.spectrumDisplay.stripArrangement == 'T':

                # NOTE:ED - Tiled plots not fully implemented yet
                getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

            else:
                getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

        self.rescale()

        # put stuff in here that will change on a resize
        self._updateAxes = True
        for gr in self.gridList:
            gr.renderMode = GLRENDERMODE_REBUILD
        # self._GLPeaks.rescale()
        # self._GLMultiplets.rescale()

        # self._clearAndUpdate(clearKeys=True)
        self.update()

    def _rescaleAllAxes(self, mouseMoveOnly=False, update=True):
        self._testAxisLimits()

        # spawn rebuild event for the grid
        self._updateAxes = True
        for gr in self.gridList:
            gr.renderMode = GLRENDERMODE_REBUILD
        if update:
            self.update()

    def _rescaleXAxis(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticHTraces=False)

        # spawn rebuild event for the grid
        self._updateAxes = True
        if self.gridList:
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD

        if update:
            self.update()

    def _rescaleYAxis(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticVTraces=False)

        # spawn rebuild event for the grid
        self._updateAxes = True
        if self.gridList:
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD

        if update:
            self.update()

    def _storeZoomHistory(self):
        """Store the current axis state to the zoom history
        """
        currentAxis = (self.axisL, self.axisR, self.axisB, self.axisT)

        # store the current value if current zoom has not been set
        if self._zoomHistory[self._zoomHistoryHead] is None:
            self._zoomHistory[self._zoomHistoryHead] = currentAxis

        if self._widthsChangedEnough(currentAxis, self._zoomHistory[self._zoomHistoryHead], tol=1e-8):

            for stored in self.storedZooms:
                if not self._widthsChangedEnough(currentAxis, self._zoomHistory[self._zoomHistoryHead], tol=1e-8):
                    break
            else:
                currentTime = time.time()
                if currentTime - self._zoomTimerLast < ZOOMTIMERDELAY:

                    # still on the current zoom item - write new value
                    self._zoomHistory[self._zoomHistoryHead] = currentAxis

                else:

                    # increment the head of the zoom history
                    self._zoomHistoryHead = (self._zoomHistoryHead + 1) % len(self._zoomHistory)
                    self._zoomHistory[self._zoomHistoryHead] = currentAxis
                    self._zoomHistoryCurrent = self._zoomHistoryHead

                # reset the timer so you have to wait another 5 seconds
                self._zoomTimerLast = currentTime

    def getCurrentCursorCoordinate(self):

        if self.cursorSource == None or self.cursorSource == 'self':
            currentPos = self.mapFromGlobal(QtGui.QCursor.pos())
            # print('updated current pos', currentPos.x(),currentPos.y())

            # calculate mouse coordinate within the mainView
            _mouseX = currentPos.x()
            if self._drawBottomAxis:
                _mouseY = self.height() - currentPos.y() - self.AXIS_MOUSEYOFFSET
                _top = self.height() - self.AXIS_MOUSEYOFFSET
            else:
                _mouseY = self.height() - currentPos.y()
                _top = self.height()

            # translate from screen (0..w, 0..h) to NDC (-1..1, -1..1) to axes (axisL, axisR, axisT, axisB)
            result = self.mouseTransform.dot([_mouseX, _mouseY, 0.0, 1.0])
        else:
            result = self.cursorCoordinate

        return result

    def mouseMoveEvent(self, event):

        self.cursorSource = CURSOR_SOURCE_SELF

        if self.spectrumDisplay.isDeleted:
            return
        if not self._ordering:  # strip.spectrumViews:
            return
        if self._draggingLabel:
            return

        if abs(self.axisL - self.axisR) < 1.0e-6 or abs(self.axisT - self.axisB) < 1.0e-6:
            return

        # reset on the first mouseMove - frees the locked/default axis
        setattr(self.spectrumDisplay, '_useFirstDefault', False)

        currentPos = self.mapFromGlobal(QtGui.QCursor.pos())

        dx = currentPos.x() - self.lastPos.x()
        dy = currentPos.y() - self.lastPos.y()
        self.lastPos = currentPos
        cursorCoordinate = self.getCurrentCursorCoordinate()

        try:
            mouseMovedDict = self.current.mouseMovedDict
        except:
            # initialise a new mouse moved dict
            mouseMovedDict = {MOUSEDICTSTRIP          : None,
                              AXIS_MATCHATOMTYPE      : {},
                              AXIS_FULLATOMNAME       : {},
                              AXIS_ACTIVEAXES         : (),
                              DOUBLEAXIS_MATCHATOMTYPE: {},
                              DOUBLEAXIS_FULLATOMNAME : {},
                              DOUBLEAXIS_ACTIVEAXES   : ()
                              }

        xPos = yPos = 0
        dxPos = dyPos = dPos = 0
        activeOther = []
        activeX = activeY = '<None>'

        for n, axisCode in enumerate(self.spectrumDisplay.axisCodes):
            if n == 0:
                xPos = pos = cursorCoordinate[0]
                activeX = axisCode  #[0]

                # double cursor
                dPos = cursorCoordinate[1]
            elif n == 1:
                yPos = pos = cursorCoordinate[1]
                activeY = axisCode  #[0]

                # double cursor
                dPos = cursorCoordinate[0]

            else:
                dPos = pos = self._orderedAxes[n].position  # if n in self._orderedAxes else 0
                # dPos = pos = self.spectrumDisplay.axes[n].position  # if n in self._orderedAxes else 0

                activeOther.append(axisCode)  #[0])

            # populate the mouse moved dict
            mouseMovedDict[AXIS_MATCHATOMTYPE][axisCode[0]] = pos
            mouseMovedDict[AXIS_FULLATOMNAME][axisCode] = pos
            mouseMovedDict[DOUBLEAXIS_MATCHATOMTYPE][axisCode[0]] = dPos
            mouseMovedDict[DOUBLEAXIS_FULLATOMNAME][axisCode] = dPos

        mouseMovedDict[AXIS_ACTIVEAXES] = (activeX, activeY) + tuple(activeOther)  # changed to full axisCodes
        mouseMovedDict[DOUBLEAXIS_ACTIVEAXES] = (activeY, activeX) + tuple(activeOther)

        self.current.cursorPosition = (xPos, yPos)
        self.current.mouseMovedDict = mouseMovedDict

        if int(event.buttons() & (Qt.LeftButton | Qt.RightButton)):
            # Main mouse drag event - handle moving the axes with the mouse
            self.axisL -= dx * self.pixelX
            self.axisR -= dx * self.pixelX
            self.axisT += dy * self.pixelY
            self.axisB += dy * self.pixelY

            tilePos = self.tilePosition
            self.GLSignals._emitAllAxesChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                               axisB=self.axisB, axisT=self.axisT,
                                               axisL=self.axisL, axisR=self.axisR,
                                               row=tilePos[0], column=tilePos[1])
            # self._selectionMode = 0
            self._rescaleAllAxes(mouseMoveOnly=True)
            # self._storeZoomHistory()

        elif not int(event.buttons()):
            self.GLSignals._emitMouseMoved(source=self, coords=cursorCoordinate, mouseMovedDict=mouseMovedDict, mainWindow=self.mainWindow)

        self.update()

    def _resizeGL(self, w, h):
        self.w = w
        self.h = h

        self._rescaleAllZoom(False)

    def sign(self, x):
        return 1.0 if x >= 0 else -1.0

    def _scaleToXAxis(self, rescale=True):
        _useFirstDefault = getattr(self.spectrumDisplay, '_useFirstDefault', False)
        if (self._useLockedAspect or self._useDefaultAspect or _useFirstDefault):
            mby = 0.5 * (self.axisT + self.axisB)

            if self._useDefaultAspect or _useFirstDefault:
                ax0 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[0])
                ax1 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[1])
            else:
                ax0 = self.pixelX
                ax1 = self.pixelY

            # width = (self.w - self.AXIS_MARGINRIGHT) if self._drawRightAxis else self.w
            # height = (self.h - self.AXIS_MOUSEYOFFSET) if self._drawBottomAxis else self.h

            width, height = self.spectrumDisplay.strips[0].mainViewSize()

            ratio = (height / width) * 0.5 * abs((self.axisL - self.axisR) * ax1 / ax0)
            self.axisB = mby + ratio * self.sign(self.axisB - mby)
            self.axisT = mby - ratio * self.sign(mby - self.axisT)

        if rescale:
            self._rescaleAllAxes()

    def _scaleToYAxis(self, rescale=True):
        _useFirstDefault = getattr(self.spectrumDisplay, '_useFirstDefault', False)
        if (self._useLockedAspect or self._useDefaultAspect or _useFirstDefault):
            mbx = 0.5 * (self.axisR + self.axisL)

            if self._useDefaultAspect or _useFirstDefault:
                ax0 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[0])
                ax1 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[1])
            else:
                ax0 = self.pixelX
                ax1 = self.pixelY

            # width = (self.w - self.AXIS_MARGINRIGHT) if self._drawRightAxis else self.w
            # height = (self.h - self.AXIS_MOUSEYOFFSET) if self._drawBottomAxis else self.h

            width, height = self.spectrumDisplay.strips[0].mainViewSize()

            ratio = (width / height) * 0.5 * abs((self.axisT - self.axisB) * ax0 / ax1)
            self.axisL = mbx + ratio * self.sign(self.axisL - mbx)
            self.axisR = mbx - ratio * self.sign(mbx - self.axisR)

        if rescale:
            self._rescaleAllAxes()

    def _getValidAspectRatio(self, axisCode):
        va = [ax for ax in self._preferences.aspectRatios.keys() if ax.upper()[0] == axisCode.upper()[0]]
        return self._preferences.aspectRatios[va[0]]

    def resizeGL(self, w, h):
        # must be set here to catch the change of screen
        self.refreshDevicePixelRatio()
        self._resizeGL(w, h)

    def rescale(self, rescaleOverlayText=True, rescaleMarksRulers=True,
                rescaleIntegralLists=True, rescaleRegions=True,
                rescaleSpectra=True, rescaleStaticHTraces=True,
                rescaleStaticVTraces=True, rescaleSpectrumLabels=True,
                rescaleLegend=True):
        """Change to axes of the view, axis visibility, scale and rebuild matrices when necessary
        to improve display speed
        """
        if self.spectrumDisplay.isDeleted or not self.globalGL:
            return

        # use the updated size
        w = self.w
        h = self.h

        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        # set projection to axis coordinates
        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        # needs to be offset from (0,0) for mouse scaling
        if self._drawRightAxis and self._drawBottomAxis:

            self._currentView = GLDefs.MAINVIEW
            self._currentRightAxisView = GLDefs.RIGHTAXIS
            self._currentRightAxisBarView = GLDefs.RIGHTAXISBAR
            self._currentBottomAxisView = GLDefs.BOTTOMAXIS
            self._currentBottomAxisBarView = GLDefs.BOTTOMAXISBAR

            # vp = self.viewports.getViewportFromWH(self._currentView, w, h)
            #
            # # currentShader.setViewportMatrix(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, 0, h - self.AXIS_MOUSEYOFFSET,
            # #                                 -1.0, 1.0)
            # # self.pixelX = (self.axisR - self.axisL) / max((w - self.AXIS_MARGINRIGHT), 1)
            # # self.pixelY = (self.axisT - self.axisB) / max((h - self.AXIS_MOUSEYOFFSET), 1)
            # # self.deltaX = 1.0 / max((w - self.AXIS_MARGINRIGHT), 1)
            # # self.deltaY = 1.0 / max((h - self.AXIS_MOUSEYOFFSET), 1)
            #
            # currentShader.setViewportMatrix(self._uVMatrix, 0, vp.width, 0, vp.height,
            #                                 -1.0, 1.0)
            # self.pixelX = (self.axisR - self.axisL) / vp.width
            # self.pixelY = (self.axisT - self.axisB) / vp.height
            # self.deltaX = 1.0 / vp.width
            # self.deltaY = 1.0 / vp.height

        elif self._drawRightAxis and not self._drawBottomAxis:

            self._currentView = GLDefs.MAINVIEWFULLHEIGHT
            self._currentRightAxisView = GLDefs.FULLRIGHTAXIS
            self._currentRightAxisBarView = GLDefs.FULLRIGHTAXISBAR

            # vp = self.viewports.getViewportFromWH(self._currentView, w, h)
            #
            # # currentShader.setViewportMatrix(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, 0, h, -1.0, 1.0)
            # # self.pixelX = (self.axisR - self.axisL) / max((w - self.AXIS_MARGINRIGHT), 1)
            # # self.pixelY = (self.axisT - self.axisB) / h
            # # self.deltaX = 1.0 / max((w - self.AXIS_MARGINRIGHT), 1)
            # # self.deltaY = 1.0 / h
            #
            # currentShader.setViewportMatrix(self._uVMatrix, 0, vp.width, 0, h, -1.0, 1.0)
            # self.pixelX = (self.axisR - self.axisL) / max(vp.width, 1)
            # self.pixelY = (self.axisT - self.axisB) / h
            # self.deltaX = 1.0 / max(vp.width, 1)
            # self.deltaY = 1.0 / h

        elif not self._drawRightAxis and self._drawBottomAxis:

            self._currentView = GLDefs.MAINVIEWFULLWIDTH
            self._currentBottomAxisView = GLDefs.FULLBOTTOMAXIS
            self._currentBottomAxisBarView = GLDefs.FULLBOTTOMAXISBAR

            # vp = self.viewports.getViewportFromWH(self._currentView, w, h)
            #
            # # currentShader.setViewportMatrix(self._uVMatrix, 0, w, 0, h - self.AXIS_MOUSEYOFFSET, -1.0, 1.0)
            # # self.pixelX = (self.axisR - self.axisL) / w
            # # self.pixelY = (self.axisT - self.axisB) / max((h - self.AXIS_MOUSEYOFFSET), 1)
            # # self.deltaX = 1.0 / w
            # # self.deltaY = 1.0 / max((h - self.AXIS_MOUSEYOFFSET), 1)
            #
            # currentShader.setViewportMatrix(self._uVMatrix, 0, w, 0, vp.height, -1.0, 1.0)
            # self.pixelX = (self.axisR - self.axisL) / w
            # self.pixelY = (self.axisT - self.axisB) / max(vp.height, 1)
            # self.deltaX = 1.0 / w
            # self.deltaY = 1.0 / max(vp.height, 1)

        else:

            self._currentView = GLDefs.FULLVIEW

            # vp = self.viewports.getViewportFromWH(self._currentView, w, h)
            #
            # currentShader.setViewportMatrix(self._uVMatrix, 0, w, 0, h, -1.0, 1.0)
            # self.pixelX = (self.axisR - self.axisL) / w
            # self.pixelY = (self.axisT - self.axisB) / h
            # self.deltaX = 1.0 / w
            # self.deltaY = 1.0 / h

        # self.symbolX = abs(self._symbolSize * self.pixelX)
        # self.symbolY = abs(self._symbolSize * self.pixelY)

        vp = self.viewports.getViewportFromWH(self._currentView, w, h)
        currentShader.setViewportMatrix(self._uVMatrix, 0, vp.width, 0, vp.height,
                                        -1.0, 1.0)
        self.pixelX = (self.axisR - self.axisL) / vp.width
        self.pixelY = (self.axisT - self.axisB) / vp.height
        self.deltaX = 1.0 / vp.width
        self.deltaY = 1.0 / vp.height

        self._dataMatrix[0:16] = [self.axisL, self.axisR, self.axisT, self.axisB,
                                  self.pixelX, self.pixelY, w, h,
                                  0.2, 1.0, 0.4, 1.0,
                                  0.3, 0.1, 1.0, 1.0]
        currentShader.setGLUniformMatrix4fv('dataMatrix', 1, GL.GL_FALSE, self._dataMatrix)
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        # map mouse coordinates to world coordinates - only needs to change on resize, move soon
        currentShader.setViewportMatrix(self._aMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)

        # calculate the screen to axes transform
        self.vInv = np.linalg.inv(self._uVMatrix.reshape((4, 4)))
        self.mouseTransform = np.matmul(self._aMatrix.reshape((4, 4)), self.vInv)

        self.modelViewMatrix = (GL.GLdouble * 16)()
        self.projectionMatrix = (GL.GLdouble * 16)()
        self.viewport = (GL.GLint * 4)()

        # change to the text shader
        currentShader = self.globalGL._shaderProgramTex.makeCurrent()

        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB, self.axisT, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 1.0, 1.0]
        # self._view[0:4] = [w - self.AXIS_MARGINRIGHT, h - self.AXIS_MOUSEYOFFSET, 1.0, 1.0]
        self._view[0:4] = [vp.width, vp.height, 1.0, 1.0]

        # self._axisScale[0:4] = [1.0/(self.axisR-self.axisL), 1.0/(self.axisT-self.axisB), 1.0, 1.0]
        currentShader.setGLUniform4fv('axisScale', 1, self._axisScale)
        currentShader.setGLUniform4fv('viewport', 1, self._view)

    def _updateVisibleSpectrumViews(self):
        """Update the list of visible spectrumViews when change occurs
        """

        # make the list of ordered spectrumViews
        self._ordering = self.spectrumDisplay.orderedSpectrumViews(self.spectrumDisplay.strips[0].spectrumViews)

        self._ordering = [specView for specView in self._ordering]

        for specView in tuple(self._spectrumSettings.keys()):
            if specView not in self._ordering:
                # print('>>>_updateVisibleSpectrumViews delete', specView, id(specView))
                # print('>>>', [id(spec) for spec in self._ordering])
                del self._spectrumSettings[specView]

        # make a list of the visible and not-deleted spectrumViews
        # visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
        visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]

        self._visibleOrdering = visibleSpectrumViews

        # set the first visible, or the first in the ordered list
        self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
            0].isDeleted else None

    def updateVisibleSpectrumViews(self):
        self._visibleSpectrumViewsChange = True
        self.update()

    def wheelEvent(self, event):
        # def between(val, l, r):
        #   return (l-val)*(r-val) <= 0

        if self.spectrumDisplay and not self._ordering:  # strip.spectrumViews:
            event.accept()
            return

        # check the movement of the wheel first
        numPixels = event.pixelDelta()
        numDegrees = event.angleDelta()
        zoomCentre = self._preferences.zoomCentreType

        zoomScale = 0.0
        scrollDirection = 0
        if numPixels:

            # always seems to be numPixels - check with Linux
            # the Shift key automatically returns the x-axis
            scrollDirection = numPixels.x() if self._isSHIFT else numPixels.y()
            zoomScale = 8.0

            # stop the very sensitive movements
            if abs(scrollDirection) < 1:
                event.ignore()
                return

        elif numDegrees:

            # this may work when using Linux
            scrollDirection = (numDegrees.x() / 4) if self._isSHIFT else (numDegrees.y() / 4)
            zoomScale = 8.0

            # stop the very sensitive movements
            if abs(scrollDirection) < 1:
                event.ignore()
                return

        else:
            event.ignore()
            return

        # if self._isSHIFT or self._isCTRL:
        #
        #     # process wheel with buttons here
        #     # transfer event to the correct widget for changing the plane OR raising base contour level...
        #
        #     if self._isSHIFT:
        #         # raise/lower base contour level - should be strip I think
        #         if scrollDirection > 0:
        #             self.strip.spectrumDisplay.raiseContourBase()
        #         else:
        #             self.strip.spectrumDisplay.lowerContourBase()
        #
        #     elif self._isCTRL:
        #         # scroll through planes
        #         pT = self.strip.planeAxisBars if hasattr(self.strip, 'planeAxisBars') else None
        #         activePlaneAxis = self.strip.activePlaneAxis
        #         if pT and activePlaneAxis is not None and (activePlaneAxis - 2) < len(pT):
        #             # pass the event to the correct double spinbox
        #             pT[activePlaneAxis - 2].scrollPpmPosition(event)
        #
        #     event.accept()
        #     return

        # test whether the limits have been reached in either axis
        if (scrollDirection > 0 and self._minReached and (self._useLockedAspect or self._useDefaultAspect)) or \
                (scrollDirection < 0 and self._maxReached and (self._useLockedAspect or self._useDefaultAspect)):
            event.accept()
            return

        zoomIn = (100.0 + zoomScale) / 100.0
        zoomOut = 100.0 / (100.0 + zoomScale)

        h = self.h
        w = self.w

        # find the correct viewport
        if (self._drawRightAxis and self._drawBottomAxis):
            ba = self.viewports.getViewportFromWH(GLDefs.BOTTOMAXISBAR, w, h)
            ra = self.viewports.getViewportFromWH(GLDefs.RIGHTAXISBAR, w, h)

        elif (self._drawBottomAxis):
            ba = self.viewports.getViewportFromWH(GLDefs.FULLBOTTOMAXISBAR, w, h)
            ra = (0, 0, 0, 0)

        elif (self._drawRightAxis):
            ba = (0, 0, 0, 0)
            ra = self.viewports.getViewportFromWH(GLDefs.FULLRIGHTAXISBAR, w, h)

        else:  # no axes visible
            ba = (0, 0, 0, 0)
            ra = (0, 0, 0, 0)

        mx = event.pos().x()
        my = self.height() - event.pos().y()

        tilePos = self.tilePosition

        if self.between(mx, ba[0], ba[0] + ba[2]) and self.between(my, ba[1], ba[1] + ba[3]):

            # in the bottomAxisBar, so zoom in the X axis

            # check the X limits
            if (scrollDirection > 0 and self._minXReached) or (scrollDirection < 0 and self._maxXReached):
                event.accept()
                return

            if zoomCentre == 0:  # centre on mouse
                mb = (mx - ba[0]) / (ba[2] - ba[0])
            else:  # centre on the screen
                mb = 0.5

            mbx = self.axisL + mb * (self.axisR - self.axisL)

            if scrollDirection < 0:
                self.axisL = mbx + zoomIn * (self.axisL - mbx)
                self.axisR = mbx - zoomIn * (mbx - self.axisR)
            else:
                self.axisL = mbx + zoomOut * (self.axisL - mbx)
                self.axisR = mbx - zoomOut * (mbx - self.axisR)

            if not (self._useLockedAspect or self._useDefaultAspect):
                self.GLSignals._emitXAxisChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                 axisB=self.axisB, axisT=self.axisT,
                                                 axisL=self.axisL, axisR=self.axisR,
                                                 row=tilePos[0], column=tilePos[1])

                self._rescaleXAxis()
                # self._storeZoomHistory()

            else:
                self._scaleToXAxis()

                self.GLSignals._emitAllAxesChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                   axisB=self.axisB, axisT=self.axisT,
                                                   axisL=self.axisL, axisR=self.axisR,
                                                   row=tilePos[0], column=tilePos[1])

                # self._storeZoomHistory()

        elif self.between(mx, ra[0], ra[0] + ra[2]) and self.between(my, ra[1], ra[1] + ra[3]):

            # in the rightAxisBar, so zoom in the Y axis

            # check the Y limits
            if (scrollDirection > 0 and self._minYReached) or (scrollDirection < 0 and self._maxYReached):
                event.accept()
                return

            if zoomCentre == 0:  # centre on mouse
                mb = (my - ra[1]) / (ra[3] - ra[1])
            else:  # centre on the screen
                mb = 0.5

            mby = self.axisB + mb * (self.axisT - self.axisB)

            if scrollDirection < 0:
                self.axisB = mby + zoomIn * (self.axisB - mby)
                self.axisT = mby - zoomIn * (mby - self.axisT)
            else:
                self.axisB = mby + zoomOut * (self.axisB - mby)
                self.axisT = mby - zoomOut * (mby - self.axisT)

            if not (self._useLockedAspect or self._useDefaultAspect):
                self.GLSignals._emitYAxisChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                 axisB=self.axisB, axisT=self.axisT,
                                                 axisL=self.axisL, axisR=self.axisR,
                                                 row=tilePos[0], column=tilePos[1])

                self._rescaleYAxis()
                # self._storeZoomHistory()

            else:
                self._scaleToYAxis()

                self.GLSignals._emitAllAxesChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                   axisB=self.axisB, axisT=self.axisT,
                                                   axisL=self.axisL, axisR=self.axisR,
                                                   row=tilePos[0], column=tilePos[1])

                # self._storeZoomHistory()

        event.accept()


class GuiNdWidgetAxis(Gui1dWidgetAxis):
    """Testing a widget that only contains a right axis
    """
    is1D = False
    AXIS_MARGINRIGHT = 50
    AXIS_MARGINBOTTOM = 25
    AXIS_LINE = 7
    AXIS_OFFSET = 3
    AXIS_INSIDE = False
    YAXISUSEEFORMAT = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    AXISLOCKEDBUTTON = True
    SPECTRUMXZOOM = 1.0e1
    SPECTRUMYZOOM = 1.0e1
    SHOWSPECTRUMONPHASING = True
    XAXES = GLDefs.XAXISUNITS
    YAXES = GLDefs.YAXISUNITS
    AXIS_MOUSEYOFFSET = AXIS_MARGINBOTTOM + (0 if AXIS_INSIDE else AXIS_LINE)
