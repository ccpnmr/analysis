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
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_FOREGROUND, getColours
from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLSymbolArray, GLVertexArray, GLRENDERMODE_DRAW, GLRENDERMODE_RESCALE, \
    GLRENDERMODE_REBUILD, GLREFRESHMODE_REBUILD
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import LENCOLORS, LENPID
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation
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
        super(GuiNdWidget, self).__init__(strip=strip,
                                          mainWindow=mainWindow,
                                          stripIDLabel=stripIDLabel)


class Gui1dWidget(CcpnGLWidget):
    AXIS_MARGINRIGHT = 65
    YAXISUSEEFORMAT = True
    INVERTXAXIS = True
    INVERTYAXIS = False
    AXISLOCKEDBUTTON = True
    is1D = True
    SPECTRUMPOSCOLOUR = 'sliceColour'
    SPECTRUMNEGCOLOUR = 'sliceColour'
    SPECTRUMXZOOM = 1.0e2
    SPECTRUMYZOOM = 1.0e6

    def __init__(self, strip=None, mainWindow=None, stripIDLabel=None):
        super(Gui1dWidget, self).__init__(strip=strip,
                                          mainWindow=mainWindow,
                                          stripIDLabel=stripIDLabel)

    def _selectPeak(self, xPosition, yPosition):
        """
        (de-)Select first peak near cursor xPosition, yPosition
        if peak already was selected, de-select it
        """
        xPeakWidth = abs(self.pixelX) * self.peakWidthPixels
        yPeakWidth = abs(self.pixelY) * self.peakWidthPixels
        xPositions = [xPosition - 0.5 * xPeakWidth, xPosition + 0.5 * xPeakWidth]
        yPositions = [yPosition - 0.5 * yPeakWidth, yPosition + 0.5 * yPeakWidth]

        peaks = list(self.current.peaks)
        for spectrumView in self.strip.spectrumViews:

            # TODO:ED could change this to actually use the pids in the drawList
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():
                    # for peakList in spectrumView.spectrum.peakLists:
                    peakList = peakListView.peakList
                    if not isinstance(peakList, PeakList):  # it could be an IntegralList
                        continue

                    for peak in peakList.peaks:
                        if (xPositions[0] < float(peak.position[0]) < xPositions[1]
                                and yPositions[0] < float(peak.height) < yPositions[1]):

                            # if peak in self.current.peaks:
                            #   self.current._peaks.remove(peak)
                            # else:
                            #   self.current.addPeak(peak)
                            if peak in peaks:
                                peaks.remove(peak)
                            else:
                                peaks.append(peak)

        self.current.peaks = peaks

    def _selectMultiplet(self, xPosition, yPosition):
        """
        (de-)Select first multiplet near cursor xPosition, yPosition
        if multiplet already was selected, de-select it
        """
        xMultipletWidth = abs(self.pixelX) * self.peakWidthPixels
        yMultipletWidth = abs(self.pixelY) * self.peakWidthPixels
        xPositions = [xPosition - 0.5 * xMultipletWidth, xPosition + 0.5 * xMultipletWidth]
        yPositions = [yPosition - 0.5 * yMultipletWidth, yPosition + 0.5 * yMultipletWidth]

        multiplets = list(self.current.multiplets)
        for spectrumView in self.strip.spectrumViews:

            # TODO:ED could change this to actually use the pids in the drawList
            for multipletListView in spectrumView.multipletListViews:
                if spectrumView.isVisible() and multipletListView.isVisible():
                    # for multipletList in spectrumView.spectrum.multipletLists:
                    multipletList = multipletListView.multipletList

                    for multiplet in multipletList.multiplets:
                        if (xPositions[0] < float(multiplet.position[0]) < xPositions[1]
                                and yPositions[0] < float(multiplet.height) < yPositions[1]):

                            if multiplet in multiplets:
                                multiplets.remove(multiplet)
                            else:
                                multiplets.append(multiplet)

        self.current.multiplets = multiplets

    def _newStatic1DTraceData(self, spectrumView, tracesDict,
                              point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel,
                              ph0=None, ph1=None, pivot=None):

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
                                            renderMode=GLRENDERMODE_REBUILD,
                                            blendMode=False,
                                            drawMode=GL.GL_LINE_STRIP,
                                            dimension=2,
                                            GLContext=self))

            numVertices = len(x)
            hSpectrum = tracesDict[-1]
            hSpectrum.indices = numVertices
            hSpectrum.numVertices = numVertices
            hSpectrum.indices = np.arange(numVertices, dtype=np.uint)
            hSpectrum.colors = np.array((self._phasingTraceColour) * numVertices, dtype=np.float32)
            hSpectrum.vertices = np.zeros((hSpectrum.numVertices * 2), dtype=np.float32)

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
                                xNumPoints, positionPixel]
            hSpectrum.spectrumView = spectrumView

        except Exception as es:
            print('>>>', str(es))
            tracesDict = []

    def buildSpectra(self):
        if self.strip.isDeleted:
            return

        # self._spectrumSettings = {}
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
