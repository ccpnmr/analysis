"""
Module Documentation here
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
import numpy as np
from PyQt5 import QtWidgets
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLVertexArray, GLRENDERMODE_DRAW, \
    GLRENDERMODE_REBUILD, GLRENDERMODE_RESCALE
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import YAXISUNITS1D, SPECTRUM_VALUEPERPOINT
import ccpn.util.Phasing as Phasing
from ccpn.util.Common import getAxisCodeMatchIndices

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)


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

        # GWV: removed as new data reader returns zeros; blank spectra can be displayed
        # self._ordering = [specView for specView in self._ordering if specView.spectrum.hasValidPath()]

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
        for val in minList:
            if minimumValuePerPoint and val is not None:
                minimumValuePerPoint = [min(ii, jj) for ii, jj in zip(minimumValuePerPoint, val)]
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
        visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
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

class Gui1dWidgetAxis(Gui1dWidget):
    pass


class GuiNdWidgetAxis(Gui1dWidget):
    """Testing a widget that only contains a right axis
    """

    def paintGL(self):
        w = self.w
        h = self.h
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        if self._blankDisplay:
            return

        if self.strip.isDeleted:
            return

        # check whether the visible spectra list needs updating
        if self._visibleSpectrumViewsChange:
            self._visibleSpectrumViewsChange = False
            self._updateVisibleSpectrumViews()

        # if there are no spectra then skip the paintGL event
        if not self._ordering:
            return

        # stop notifiers interfering with paint event
        self.project.blankNotification()

        # start with the grid mapped to (0..1, 0..1) to remove zoom errors here
        currentShader.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        # draw the grid components
        self.drawGrid()

        currentShader = self.globalGL._shaderProgramTex.makeCurrent()
        self.enableTexture()
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

        # re-enable notifiers
        self.project.unblankNotification()
