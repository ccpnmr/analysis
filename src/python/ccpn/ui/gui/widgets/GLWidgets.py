"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLGlobalData


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
__dateModified__ = "$dateModified: 2018-12-20 15:53:23 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
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
import numpy as np
from contextlib import contextmanager
from itertools import zip_longest
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLVertexArray, GLRENDERMODE_DRAW, \
    GLRENDERMODE_REBUILD, GLRENDERMODE_RESCALE, ZOOMHISTORYSTORE
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import YAXISUNITS1D, SPECTRUM_VALUEPERPOINT
import ccpn.util.Phasing as Phasing
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_MATCHATOMTYPE, AXIS_ACTIVEAXES, \
    DOUBLEAXIS_ACTIVEAXES, DOUBLEAXIS_FULLATOMNAME, DOUBLEAXIS_MATCHATOMTYPE, MOUSEDICTSTRIP
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.ui.gui.lib.OpenGL import CcpnOpenGLDefs as GLDefs
from ccpn.util.Logging import getLogger

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


class GuiNdWidget(CcpnGLWidget):
    is1D = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    SPECTRUMPOSCOLOUR = 'positiveContourColour'
    SPECTRUMNEGCOLOUR = 'negativeContourColour'

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

        minList = [self._spectrumSettings[sp][SPECTRUM_VALUEPERPOINT] for sp in self._ordering if sp in self._spectrumSettings]
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
            self.visiblePlaneList[visibleSpecView] = visibleSpecView._getVisiblePlaneList(firstVisible=self._firstVisible,
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

        peak.position = p0


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

        if not self._stackingMode and not(self.is1D and self.strip._isPhasingOn):
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

    AXIS_MARGINRIGHT = 50
    AXIS_MARGINBOTTOM = 25
    AXIS_LINE = 7
    AXIS_OFFSET = 3
    YAXISUSEEFORMAT = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    AXISLOCKEDBUTTON = True
    SPECTRUMXZOOM = 1.0e1
    SPECTRUMYZOOM = 1.0e1
    SHOWSPECTRUMONPHASING = True
    XAXES = GLDefs.XAXISUNITS
    YAXES = GLDefs.YAXISUNITS

    def __init__(self, parent, spectrumDisplay=None, mainWindow=None, antiAlias=4):

        super().__init__(parent)

        # GST add antiAliasing, no perceptible speed impact on my mac (intel iris graphics!)
        # samples = 4 is good enough but 8 also works well in terms of speed...
        try:
            fmt = QtGui.QSurfaceFormat()
            fmt.setSamples(antiAlias)
            self.setFormat(fmt)

            samples = self.format().samples() # GST a use for the walrus
            if samples != antiAlias:
                getLogger().warning('hardware changed antialias level, expected %i got %i...' % (samples,antiAlias))
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

        # set the pyqtsignal responders
        self.GLSignals = GLNotifier(parent=self, strip=None)
        self.GLSignals.glXAxisChanged.connect(self._glXAxisChanged)
        self.GLSignals.glYAxisChanged.connect(self._glYAxisChanged)
        self.GLSignals.glAllAxesChanged.connect(self._glAllAxesChanged)
        self.GLSignals.glMouseMoved.connect(self._glMouseMoved)
        self.GLSignals.glEvent.connect(self._glEvent)
        self.GLSignals.glAxisLockChanged.connect(self._glAxisLockChanged)
        self.GLSignals.glAxisUnitsChanged.connect(self._glAxisUnitsChanged)

    def paintGL(self):
        """Handle the GL painting
        """
        if self._blankDisplay:
            return

        if self.spectrumDisplay.isDeleted:
            return

        with self.glBlocking():
            self._buildGL()
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

    def between(self, val, l, r):
        return (l - val) * (r - val) <= 0

    def _buildAxes(self, gridGLList, axisList=None, scaleGrid=None, r=0.0, g=0.0, b=0.0, transparency=256.0,
                   _includeDiagonal=False, _diagonalList=None):
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
        boundY = (self.h - self.AXIS_MARGINBOTTOM) if self._drawBottomAxis else self.h
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
                                    includeGrid = not (self.XMode == self._intFormat and d[0] < 1 and abs(p1[0]-int(p1[0])) > d[0]/2.0)
                                else:
                                    includeGrid = not (self.YMode == self._intFormat and d[1] < 1 and abs(p1[1]-int(p1[1])) > d[1]/2.0)
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

                # draw the diagonal x=y if required - need to determine the origin
                # OR draw on the spectrum bounding box
                if _includeDiagonal and _diagonalList:

                    _diagVertexList = ()

                    if self.between(axisLimitB, axisLimitL, axisLimitR):
                        _diagVertexList += (valueToRatio(axisLimitB, axisLimitL, axisLimitR),
                                            0.0)

                    if self.between(axisLimitL, axisLimitB, axisLimitT):
                        _diagVertexList += (0.0,
                                            valueToRatio(axisLimitL, axisLimitB, axisLimitT))

                    if self.between(axisLimitT, axisLimitL, axisLimitR):
                        _diagVertexList += (valueToRatio(axisLimitT, axisLimitL, axisLimitR),
                                            1.0)

                    if self.between(axisLimitR, axisLimitB, axisLimitT):
                        _diagVertexList += (1.0,
                                            valueToRatio(axisLimitR, axisLimitB, axisLimitT))

                    if len(_diagVertexList) == 4:
                        # indexList += (index, index + 1)
                        # vertexList += diag
                        #
                        # alpha = min([1.0, (30.0 + (len(scaleGrid) * 20)) / transparency])
                        # colorList += (r, g, b, alpha, r, g, b, alpha)
                        #
                        # gridGLList.numVertices += 2
                        # index += 2

                        alpha = min([1.0, (30.0 + (len(scaleGrid) * 20)) / transparency])

                        _diagIndexList = (0, 1)
                        _diagonalList.numVertices = 2
                        _diagonalList.vertices = np.array(_diagVertexList, dtype=np.float32)
                        _diagonalList.indices = np.array((0, 1), dtype=np.uint32)
                        _diagonalList.colors = np.array((r, g, b, alpha, r, g, b, alpha), dtype=np.float32)

                    else:
                        _diagonalList.numVertices = 0
                        _diagonalList.indices = np.array((), dtype=np.uint32)

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

        # only call if the axes have changed
        if not self._updateAxes:
            return
        self._updateAxes = False

        # determine whether the isotopeCodes of the first two visible axes are matching
        self._matchingIsotopeCodes = False

        if not self.spectrumDisplay.is1D:
            for specView in self._ordering:

                # check whether the spectrumView is still active
                if specView.isDeleted or specView._flaggedForDelete:
                    continue

                spec = specView.spectrum

                # inside the paint event, so sometimes specView may not exist
                if specView in self._spectrumSettings:
                    pIndex = self._spectrumSettings[specView][GLDefs.SPECTRUM_POINTINDEX]

                    if spec.isotopeCodes[pIndex[0]] == spec.isotopeCodes[pIndex[1]]:
                        self._matchingIsotopeCodes = True
                        break

        # build the axes
        self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[0], axisList=[0, 1],
                                                                 scaleGrid=[1, 0],
                                                                 r=self.foreground[0],
                                                                 g=self.foreground[1],
                                                                 b=self.foreground[2],
                                                                 transparency=300.0,
                                                                 _includeDiagonal=self._matchingIsotopeCodes,
                                                                 _diagonalList=self.diagonalGLList)

        if self.axesChanged:
            if self.highlighted:
                self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0], r=self.highlightColour[0],
                                g=self.highlightColour[1],
                                b=self.highlightColour[2], transparency=32.0)
                self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0], r=self.highlightColour[0],
                                g=self.highlightColour[1],
                                b=self.highlightColour[2], transparency=32.0)
            else:
                self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0], r=self.foreground[0],
                                g=self.foreground[1],
                                b=self.foreground[2], transparency=32.0)
                self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0], r=self.foreground[0],
                                g=self.foreground[1],
                                b=self.foreground[2], transparency=32.0)

            # buffer the lists to VBOs
            for gr in self.gridList:
                gr.defineIndexVBO(enableVBO=True)

            # buffer the diagonal GL line
            self.diagonalGLList.defineIndexVBO(enableVBO=True)

    def drawGrid(self):
        # set to the mainView and draw the grid
        # self.buildGrid()

        GL.glEnable(GL.GL_BLEND)
        GL.glLineWidth(1.0 * self.viewports._devicePixelRatio)

        # draw the main grid
        if self._gridVisible:
            self.viewports.setViewport(self._currentView)
            self.gridList[0].drawIndexVBO(enableVBO=True)

        # draw the diagonal line - independent of viewing the grid
        if self._matchingIsotopeCodes and self.diagonalGLList:
            # viewport above may not be set
            if not self._gridVisible:
                self.viewports.setViewport(self._currentView)
            self.diagonalGLList.drawIndexVBO(enableVBO=True)

        # draw the axes tick marks (effectively the same grid in smaller viewport)
        if self._axesVisible:
            if self._drawRightAxis:
                # draw the grid marks for the right axis
                self.viewports.setViewport(self._currentRightAxisView)
                self.gridList[1].drawIndexVBO(enableVBO=True)

            if self._drawBottomAxis:
                # draw the grid marks for the bottom axis
                self.viewports.setViewport(self._currentBottomAxisView)
                self.gridList[2].drawIndexVBO(enableVBO=True)

    def _buildGL(self):
        """Separate the building of the display from the paint event; not sure that this is required
        """
        self.buildGrid()


    def _paintGL(self):
        w = self.w
        h = self.h

        if self._updateBackgroundColour:
            self._updateBackgroundColour = False
            self.setBackgroundColour(self.background, silent=True)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glEnable(GL.GL_MULTISAMPLE)

        currentShader = self.globalGL._shaderProgramTex.makeCurrent()
        self.enableTextClientState()
        self._setViewPortFontScale()

        # make the overlay/axis solid
        currentShader.setBlendEnabled(0)
        self.drawAxisLabels()
        currentShader.setBlendEnabled(1)

        self.disableTextClientState()
        self.disableTexture()

        # use the current viewport matrix to display the last bit of the axes
        currentShader = self.globalGL._shaderProgram1.makeCurrent()
        currentShader.setProjectionAxes(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, -1, h - self.AXIS_MARGINBOTTOM,
                                        -1.0, 1.0)

        self.viewports.setViewport(self._currentView)

        # why are these labelled the other way round?
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uVMatrix)
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        # need to draw the axis tick marks?

        # # cheat for the moment to draw the axes (if visible)
        # if self.highlighted:
        #     colour = self.highlightColour
        # else:
        #     colour = self.foreground
        #
        # with self._disableGLAliasing():
        #     GL.glDisable(GL.GL_BLEND)
        #     GL.glColor4f(*colour)
        #     GL.glBegin(GL.GL_LINES)
        #
        #     if self._drawBottomAxis:
        #         GL.glVertex2d(0, 0)
        #         GL.glVertex2d(w - self.AXIS_MARGINRIGHT, 0)
        #
        #     if self._drawRightAxis:
        #         GL.glVertex2d(w - self.AXIS_MARGINRIGHT, 0)
        #         GL.glVertex2d(w - self.AXIS_MARGINRIGHT, h - self.AXIS_MARGINBOTTOM)
        #
        #     GL.glEnd()

    @pyqtSlot(dict)
    def _glAxisUnitsChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # read values from dataDict and set units
            if aDict[GLNotifier.GLVALUES]:      # and aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]:

                self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]

                aL = aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]
                uFA = aDict[GLNotifier.GLVALUES][GLDefs.AXISUSEFIXEDASPECTRATIO]
                if self._axisLocked != aL or self._useFixedAspect != uFA:

                    # self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                    # self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]
                    self._axisLocked = aL
                    self._useFixedAspect = uFA

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

        self.gridList = []
        self._gridVisible = self._preferences.showGrid
        self._crosshairVisible = self._preferences.showCrosshair

        self.diagonalGLList = None
        self._updateAxes = True

        self._axesVisible = True
        self._axisLocked = False
        self._useFixedAspect = False
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

        self._applyXLimit = self._preferences.zoomXLimitApply
        self._applyYLimit = self._preferences.zoomYLimitApply
        self._intensityLimit = self._preferences.intensityLimit

        self._GLIntegralLists = {}
        self._GLIntegralLabels = {}

        self._marksAxisCodes = []

        self._regions = []
        self._infiniteLines = []
        self._buildTextFlag = True

        self._buildMouse = True
        self._mouseCoords = [-1.0, -1.0]
        self.mouseString = None
        self.diffMouseString = None
        self.peakLabelling = 0

        self._contourList = {}

        self._hTraces = {}
        self._vTraces = {}
        self._staticHTraces = []
        self._staticVTraces = []
        self._currentTraces = []
        self._axisXLabelling = []
        self._axisYLabelling = []
        self._axisScaleLabelling = []

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
        self._visibleSpectrumViewsChange = False
        self._matchingIsotopeCodes = False

        self._glClientIndex = 0
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
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match only the scale for the X axis
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]

            if self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):
                diff = (axisR - axisL) / 2.0
                mid = (self.axisR + self.axisL) / 2.0
                self.axisL = mid - diff
                self.axisR = mid + diff
                self._rescaleXAxis()
                self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAxisLockChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:
            self._axisLocked = aDict[GLNotifier.GLVALUES][0]
            self._useFixedAspect = aDict[GLNotifier.GLVALUES][1]

            if self._axisLocked:

                # check which is the primary axis and update the opposite axis - similar to wheelEvent
                if self.spectrumDisplay.stripArrangement == 'Y':

                    # strips are arranged in a row
                    self._scaleToYAxis()

                elif self.spectrumDisplay.stripArrangement == 'X':

                    # strips are arranged in a column
                    self._scaleToXAxis()
            else:
                # paint to update lock button colours
                self.update()

    @pyqtSlot(dict)
    def _glAxisUnitsChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # read values from dataDict and set units
            if aDict[GLNotifier.GLVALUES]:      # and aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]:

                self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]

                aL = aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]
                uFA = aDict[GLNotifier.GLVALUES][GLDefs.AXISUSEFIXEDASPECTRATIO]
                if self._axisLocked != aL or self._useFixedAspect != uFA:

                    # self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                    # self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]
                    self._axisLocked = aL
                    self._useFixedAspect = uFA

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

    @pyqtSlot(dict)
    def _glYAxisChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match the Y axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]):
                self.axisB = axisB
                self.axisT = axisT
                self._rescaleYAxis()
                self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAllAxesChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        sDisplay = aDict[GLNotifier.GLSPECTRUMDISPLAY]
        source = aDict[GLNotifier.GLSOURCE]

        if source != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match the values for the Y axis, and scale for the X axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]) and \
                    self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):

                if self.spectrumDisplay.stripArrangement == 'Y':

                    # strips are arranged in a row
                    diff = (axisR - axisL) / 2.0
                    mid = (self.axisR + self.axisL) / 2.0
                    self.axisL = mid - diff
                    self.axisR = mid + diff
                    self.axisB = axisB
                    self.axisT = axisT

                elif self.spectrumDisplay.stripArrangement == 'X':

                    # strips are arranged in a column
                    diff = (axisT - axisB) / 2.0
                    mid = (self.axisT + self.axisB) / 2.0
                    self.axisB = mid - diff
                    self.axisT = mid + diff
                    self.axisL = axisL
                    self.axisR = axisR

                else:
                    # currently ignore - warnings will be logged elsewhere
                    pass

                self._rescaleAllAxes()
                self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glMouseMoved(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self:
            # self.cursorCoordinate = aDict[GLMOUSECOORDS]
            # self.update()

            mouseMovedDict = aDict[GLNotifier.GLMOUSEMOVEDDICT]

            if self._crosshairVisible:  # or self._updateVTrace or self._updateHTrace:

                # print('>>>>>>', self.strip, time.time())

                exactMatch = (self._preferences.matchAxisCode == AXIS_FULLATOMNAME)
                indices = getAxisCodeMatchIndices(self._axisCodes[:2], mouseMovedDict[AXIS_ACTIVEAXES], exactMatch=exactMatch)

                for n in range(2):
                    if indices[n] is not None:

                        axis = mouseMovedDict[AXIS_ACTIVEAXES][indices[n]]
                        self.cursorCoordinate[n] = mouseMovedDict[AXIS_FULLATOMNAME][axis]

                        # coordinates have already been flipped
                        # self.doubleCursorCoordinate[n] = mouseMovedDict[DOUBLEAXIS_FULLATOMNAME][axis]
                        self.doubleCursorCoordinate[1-n] = self.cursorCoordinate[n]

                    else:
                        self.cursorCoordinate[n] = None
                        self.doubleCursorCoordinate[1-n] = None

                self.current.cursorPosition = (self.cursorCoordinate[0], self.cursorCoordinate[1])

                # only need to redraw if we can see the cursor
                # if self._updateVTrace or self._updateHTrace:
                #   self.updateTraces()
                # self.makeCurrent()
                self.update()
                # self.doneCurrent()

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

        # define the main viewports
        self.viewports.addViewport(GLDefs.MAINVIEW, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.MAINVIEWFULLWIDTH, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.MAINVIEWFULLHEIGHT, self, (0, 'a'), (0, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (0, 'h'))

        # define the viewports for the right axis bar
        self.viewports.addViewport(GLDefs.RIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                   (self.AXIS_MARGINBOTTOM, 'a'),
                                   (self.AXIS_LINE, 'a'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.RIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'),
                                   (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                   (0, 'a'),
                                   (self.AXIS_LINE, 'a'), (0, 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'),
                                   (0, 'w'), (0, 'h'))

        # define the viewports for the bottom axis bar
        self.viewports.addViewport(GLDefs.BOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_LINE, 'a'))

        self.viewports.addViewport(GLDefs.BOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (self.AXIS_LINE, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                   (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # define the full viewport
        self.viewports.addViewport(GLDefs.FULLVIEW, self, (0, 'a'), (0, 'a'), (0, 'w'), (0, 'h'))

        # # define the remaining corner
        # self.viewports.addViewport(GLDefs.AXISCORNER, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'), (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))


        # This is the correct blend function to ignore stray surface blending functions
        GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)
        self.setBackgroundColour(self.background, silent=True)
        self.globalGL._shaderProgramTex.setBlendEnabled(0)

        # check that the screen device pixel ratio is correct
        self.refreshDevicePixelRatio()

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


class GuiNdWidgetAxis(Gui1dWidgetAxis):
    """Testing a widget that only contains a right axis
    """

    pass