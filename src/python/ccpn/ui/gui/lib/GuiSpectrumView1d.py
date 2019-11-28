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

import numpy as np

from PyQt5 import QtCore

import pyqtgraph as pg

from ccpn.ui.gui.lib.GuiSpectrumView import GuiSpectrumView

from ccpn.util.Colour import spectrumColours
from ccpn.util import Phasing


class GuiSpectrumView1d(GuiSpectrumView):

    hPhaseTrace = None
    buildContours = True  # trigger the first build
    buildContoursOnly = False

    #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
    def __init__(self):
        """ spectrumPane is the parent
            spectrum is the Spectrum name or object
            """
        """ old comment
            region is in units of parent, ordered by spectrum dimensions
            dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
            (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
        """

        GuiSpectrumView.__init__(self)

        self._application = self.strip.spectrumDisplay.mainWindow.application

        self.data = self.spectrum.positions, self.spectrum.intensities
        # print('>>>filePath', self.spectrum.filePath, self.spectrum.positions, self.spectrum.intensities)

        # for strip in self.strips:
        if self.spectrum.sliceColour is None:
            if len(self.strip.spectrumViews) < 12:
                self.spectrum.sliceColour = list(spectrumColours.keys())[len(self.strip.spectrumViews) - 1]
            else:
                self.spectrum.sliceColour = list(spectrumColours.keys())[(len(self.strip.spectrumViews) % 12) - 1]

        # have to add in two steps because simple plot() command draws all other data even if currently not visible
        ##self.plot = self.strip.plotWidget.plot(self.data[0], self.data[1], pen=self.spectrum.sliceColour)
        # self.plot = pg.PlotDataItem(x=self.data[0], y=self.data[1], pen=self.spectrum.sliceColour)
        # self.plot.setObjectName(self.spectrum.pid)
        # self.strip.viewBox.addItem(self.plot)

        # self.plot.curve.setClickable(True)
        # self.plot.sigClicked.connect(self._clicked)
        # below causes a problem because wrapper not ready yet at this point
        #for peakList in self.spectrum.peakLists:
        #  self.strip.showPeaks(peakList)

        self.hPhaseTrace = None
        self.buildContours = True  # trigger the first build
        self.buildContoursOnly = False
        # self.buildSymbols = True
        # self.buildLabels = True
        # self.buildSymbols = True
        # self.buildLabels = True
        # self.buildSymbols = True
        # self.buildLabels = True

        # self.strip.viewBox.autoRange()
        # self.strip.zoomYAll()

    def _getValues(self, dimensionCount = None):
        # ejb - get some spectrum information for scaling the display
        return [self._getSpectrumViewParams(0)]

    def _turnOnPhasing(self):

        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():
            if self.hPhaseTrace:
                self.hPhaseTrace.setVisible(True)
            else:
                self._newPhasingTrace()

    def _turnOffPhasing(self):

        if self.hPhaseTrace:
            self.hPhaseTrace.setVisible(False)

    def _newPhasingTrace(self):
        """
        # CCPN INTERNAL - called in newPhasingTrace methods of GuiWindow and GuiStrip
        """
        # print('>>>_newPhasingTrace')
        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible() and not self.hPhaseTrace:
            if not self.strip.haveSetHPhasingPivot:
                viewParams = self._getSpectrumViewParams(0)
                # valuePerPoint, pointCount, minAliasedFrequency, maxAliasedFrequency, dataDim,
                # minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(0)
                self.strip.hPhasingPivot.setPos(0.5 * (viewParams.minSpectrumFrequency +
                                                       viewParams.maxSpectrumFrequency))
                self.strip.hPhasingPivot.setVisible(True)
                self.strip.haveSetHPhasingPivot = True
            trace = pg.PlotDataItem()
            self.strip.plotWidget.addItem(trace)
            self.hPhaseTrace = trace
            self._updatePhasing()

    def removePhasingTraces(self):

        trace = self.hPhaseTrace
        if trace:
            self.strip.plotWidget.scene().removeItem(trace)
            self.hPhaseTrace = None

    # def _updatePhasing(self):
    #     # print('_updatePhasing 1D')
    #     return
    #
    #     if not self.isVisible():
    #         return
    #
    #     trace = self.hPhaseTrace
    #     if not trace:
    #         return
    #
    #     position = [axis.position for axis in self.strip.orderedAxes]
    #
    #     phasingFrame = self.strip.spectrumDisplay.phasingFrame
    #     phasingFrame.applyCallback = self._applyPhasing
    #
    #     phasingFrame.applyButton.setEnabled(True)
    #
    #     ph0 = phasingFrame.slider0.value() if phasingFrame.isVisible() else 0
    #     ph1 = phasingFrame.slider1.value() if phasingFrame.isVisible() else 0
    #
    #     hPhasingPivot = self.strip.hPhasingPivot
    #     if hPhasingPivot.isVisible():
    #         xAxisIndex = self._displayOrderSpectrumDimensionIndices[0]
    #         pivot = self.spectrum.mainSpectrumReferences[xAxisIndex].valueToPoint(hPhasingPivot.getXPos())
    #         # dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[0]
    #         # pivot = dataDim.primaryDataDimRef.valueToPoint(hPhasingPivot.getXPos())
    #     else:
    #         pivot = 1
    #
    #     positionPoint = QtCore.QPointF(position[0], 0.0)
    #     positionPixel = self.strip.viewBox.mapViewToScene(positionPoint)
    #     positionPixel = (positionPixel.x(), positionPixel.y())
    #     inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, = self._getTraceParams(position)
    #     if inRange:
    #         self._updateHTraceData(point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, trace, ph0, ph1, pivot)

    def _getTraceParams(self, position):
        # position is in ppm (intensity in y)

        inRange = True
        point = []
        for n, pos in enumerate(position):  # n = 0 is x, n = 1 is y, etc.
            if n != 1:

                try:
                    # valuePerPoint, totalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim,
                    # minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(n)
                    valuePerPoint, totalPointCount, _, _, dataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(n)
                except:
                    # skip if the dimension doesn't exist
                    break

                if dataDim:
                    if n == 0:
                        xDataDim = dataDim
                        # -1 below because points start at 1 in data model
                        xMinFrequency = int(dataDim.primaryDataDimRef.valueToPoint(maxSpectrumFrequency) - 1)
                        xMaxFrequency = int(dataDim.primaryDataDimRef.valueToPoint(minSpectrumFrequency) - 1)
                        xNumPoints = totalPointCount
                    else:
                        inRange = (minSpectrumFrequency <= pos <= maxSpectrumFrequency)
                        if not inRange:
                            break
                    pnt = (dataDim.primaryDataDimRef.valueToPoint(pos) - 1) % totalPointCount
                    pnt += (dataDim.pointOffset if hasattr(dataDim, "pointOffset") else 0)
                    point.append(pnt)

        return inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints

    # def _updateHTraceData(self, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, hTrace, ph0=None, ph1=None, pivot=None):
    #     return
    #
    #     # unfortunately it looks like we have to work in pixels, not ppm, yuck
    #     strip = self.strip
    #     plotWidget = strip.plotWidget
    #     plotItem = plotWidget.plotItem
    #     viewBox = strip.viewBox
    #     viewRegion = plotWidget.viewRange()
    #
    #     pointInt = [1 + int(pnt + 0.4999) for pnt in point]
    #     data = self.spectrum.intensities
    #     if ph0 is not None and ph1 is not None and pivot is not None:
    #         data0 = np.array(data)
    #         data = Phasing.phaseRealData(data, ph0, ph1, pivot)
    #         data1 = np.array(data)
    #     x = np.array([xDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(xMinFrequency, xMaxFrequency + 1)])
    #     # scale from ppm to pixels
    #     pixelViewBox0 = plotItem.getAxis('left').width()
    #     pixelViewBox1 = pixelViewBox0 + viewBox.width()
    #     region1, region0 = viewRegion[0]
    #     x -= region0
    #     x *= (pixelViewBox1 - pixelViewBox0) / (region1 - region0)
    #     x += pixelViewBox0
    #
    #     pixelViewBox1 = plotItem.getAxis('bottom').height()
    #     pixelViewBox0 = pixelViewBox1 + viewBox.height()
    #
    #     yintensity0, yintensity1 = viewRegion[1]
    #     #v = positionPixel[1] - (pixelViewBox1-pixelViewBox0) * numpy.array([data[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency+1)])
    #     v = pixelViewBox0 + (pixelViewBox1 - pixelViewBox0) * (
    #                 np.array([data[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)]) - yintensity0) / (yintensity1 - yintensity0)
    #
    #     colour = '#e4e15b' if self._application.colourScheme == 'dark' else '#000000'
    #     hTrace.setPen({'color': colour})
    #     hTrace.setData(x, v)

    #
    # def _clicked(self):
    #   print(self.plot.objectName())

    # # TBD: should function below be removed???
    # def getSliceData(self, spectrum=None):
    #   """
    #   Gets slice data for drawing 1d spectrum using specified spectrum.
    #   """
    #   if spectrum is None:
    #     apiDataSource = self._apiDataSource
    #   else:
    #     apiDataSource = spectrum._apiDataSource
    #   return apiDataSource.get1dSpectrumData()

    # def _setBorderItemHidden(self, checked):
    #     """
    #     # CCPN INTERNAL - called by _toggleGeneralOptions method of PreferencesPopup.
    #     """
    #     pass
    #     # self.borderItem.setVisible(self._application.preferences.general.showSpectrumBorder and self.isVisible())

    # def update(self):
    #     self.plot.curve.setData(self.data[0], self.data[1])

    def refreshData(self):
        # self.spectrum._intensities = None  # UGLY, but need to force data to be reloaded
        self.data = self.spectrum.positions, self.spectrum.intensities

        # spawn a rebuild in the openGL strip
        self.buildContoursOnly = True
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()
        # self.update()

    # def setSliceColour(self):
    #     self.plot.curve.setPen(self.spectrum.sliceColour)

    def _buildGLContours(self, glList, firstShow=False):
        # build a glList for the spectrum
        glList.clearArrays()

        numVertices = len(self.spectrum.positions)
        # glList.indices = numVertices
        glList.numVertices = numVertices
        # glList.indices = np.arange(numVertices, dtype=np.uint32)

        colour = self._getColour('sliceColour', '#AAAAAA')
        colR = int(colour.strip('# ')[0:2], 16) / 255.0
        colG = int(colour.strip('# ')[2:4], 16) / 255.0
        colB = int(colour.strip('# ')[4:6], 16) / 255.0

        glList.colors = np.array([colR, colG, colB, 1.0] * numVertices, dtype=np.float32)
        glList.vertices = np.zeros(numVertices * 2, dtype=np.float32)

        try:
            # may be empty
            glList.vertices[::2] = self.spectrum.positions
            glList.vertices[1::2] = self.spectrum.intensities
        except:
            pass

    def _paintContoursNoClip(self, plotHeight=0.0):

        # EJB not sure how to handle this
        pass

        # # xTranslate, xScale, xTotalPointCount, xClipPoint0, xClipPoint1 = self._getTranslateScale(0)
        # # yTranslate, yScale, yTotalPointCount, yClipPoint0, yClipPoint1 = self._getTranslateScale(1)
        # #
        # # GL.glPushMatrix()
        # # # GL.glScale(1.0, -1.0, 1.0)
        # # # GL.glTranslate(0.0, -plotHeight, 0.0)
        # # GL.glTranslate(-xTranslate, -yTranslate, 0.0)
        # # GL.glScale(xScale, yScale, 1.0)
        # for (colour, levels, displayLists) in ((self.posColour, self.posLevels, self.posDisplayLists),
        #                                        (self.negColour, self.negLevels, self.negDisplayLists)):
        #   for n, level in enumerate(levels):
        #     GL.glColor4f(*colour)
        #     # TBD: scaling, translating, etc.
        #     GL.glCallList(displayLists[n])
        # # GL.glPopMatrix()
