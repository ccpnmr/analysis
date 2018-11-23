"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import numpy as np
from PyQt5 import QtWidgets
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLVertexArray, GLRENDERMODE_DRAW, \
    GLRENDERMODE_REBUILD, GLRENDERMODE_RESCALE
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import YAXISUNITS1D
import ccpn.util.Phasing as Phasing


try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
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
        xPeakWidth = abs(self.pixelX) * self.peakWidthPixels
        yPeakWidth = abs(self.pixelY) * self.peakWidthPixels
        xPositions = [xPosition - 0.5 * xPeakWidth, xPosition + 0.5 * xPeakWidth]
        yPositions = [yPosition - 0.5 * yPeakWidth, yPosition + 0.5 * yPeakWidth]
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

                                if zPositions[0] < float(peak.position[zAxis]) < zPositions[1]:
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
        xMultipletWidth = abs(self.pixelX) * self.peakWidthPixels
        yMultipletWidth = abs(self.pixelY) * self.peakWidthPixels
        xPositions = [xPosition - 0.5 * xMultipletWidth, xPosition + 0.5 * xMultipletWidth]
        yPositions = [yPosition - 0.5 * yMultipletWidth, yPosition + 0.5 * yMultipletWidth]
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

                                if zPositions[0] < float(multiplet.position[zAxis]) < zPositions[1]:
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
        xPeakWidth = abs(self.pixelX) * self.peakWidthPixels
        yPeakWidth = abs(self.pixelY) * self.peakWidthPixels
        xPositions = [xPosition - 0.5 * xPeakWidth, xPosition + 0.5 * xPeakWidth]
        yPositions = [yPosition - 0.5 * yPeakWidth, yPosition + 0.5 * yPeakWidth]

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
        xMultipletWidth = abs(self.pixelX) * self.peakWidthPixels
        yMultipletWidth = abs(self.pixelY) * self.peakWidthPixels
        xPositions = [xPosition - 0.5 * xMultipletWidth, xPosition + 0.5 * xMultipletWidth]
        yPositions = [yPosition - 0.5 * yMultipletWidth, yPosition + 0.5 * yMultipletWidth]

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

        # self._spectrumSettings = {}
        rebuildFlag = False
        for spectrumView in self.strip.spectrumViews:

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
                spectrumView._buildGLContours(self._contourList[spectrumView])

                self._buildSpectrumSetting(spectrumView=spectrumView)
                rebuildFlag = True

                # define the VBOs to pass to the graphics card
                self._contourList[spectrumView].defineIndexVBO(enableVBO=True)

        # rebuild the traces as the spectrum/plane may have changed
        if rebuildFlag:
            self.rebuildTraces()
