"""Module Documentation here

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
__dateModified__ = "$dateModified: 2020-09-09 18:03:57 +0100 (Wed, September 09, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy
import numpy as np
from OpenGL import GL
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from ccpn.util import Colour
from ccpnc.contour import Contourer2d
from ccpn.ui.gui.lib.GuiSpectrumView import GuiSpectrumView
from ccpn.util.Logging import getLogger
# from ccpn.core.lib.SpectrumLib import setContourLevelsFromNoise


_NEWCOMPILEDCONTOURS = True


#TODO:RASMUS: why is this function here when the wrapper has positiveLevels and negativeLevels
# attributes
def _getLevels(count: int, base: float, factor: float) -> list:
    "return a list with contour levels"
    levels = []
    if count > 0:
        levels = [base]
        for n in range(count - 1):
            levels.append(numpy.float32(factor * levels[-1]))
    return levels


class GuiSpectrumViewNd(GuiSpectrumView):

    ###PeakListItemClass = PeakListNdItem

    #sigClicked = QtCore.Signal(object, object)

    #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None, region=None, **kwds):
    def __init__(self):
        """ guiSpectrumDisplay is the parent
            apiSpectrumView is the (API) SpectrumView object
        """
        """ old comment
            region is in units of parent, ordered by spectrum dimensions
            dimMapping is from spectrum numerical dimensions to guiStrip numerical dimensions
            (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
        """

        self.setAcceptedMouseButtons = QtCore.Qt.LeftButton
        self.posLevelsPrev = []
        self.negLevelsPrev = []
        self.xDataDimPrev = None
        self.yDataDimPrev = None
        self.zRegionPrev = None
        self.posDisplayLists = []
        self.negDisplayLists = []
        self._traceScale = 1.0e-7  # TBD: need a better way of setting this
        self.okDataFile = True  # used to keep track of warning message that data file does not exist

        dimensionCount = len(self.strip.axisCodes)
        self.previousRegion = dimensionCount * [None]

        # have to have this set before _setupBorderItem called
        self._application = self.strip.spectrumDisplay.mainWindow.application

        GuiSpectrumView.__init__(self)

        self.setZValue(-1)  # this is so that the contours are drawn on the bottom

        self.buildContours = True
        self.buildContoursOnly = False

    def _turnOnPhasing(self):
        """
        # CCPN INTERNAL - called by turnOnPhasing method of GuiStrip.
        """
        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():
            direction = phasingFrame.getDirection()
            traces = self.hPhaseTraces if direction == 0 else self.vPhaseTraces
            for trace, line in traces:
                trace.setVisible(True)
                line.setVisible(True)

    def _turnOffPhasing(self):
        """
        # CCPN INTERNAL - called by turnOffPhasing method of GuiStrip.
        """
        for traces in self.hPhaseTraces, self.vPhaseTraces:
            for trace, line in traces:
                trace.setVisible(False)
                line.setVisible(False)

    def _newPhasingTrace(self):

        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():
            trace = pg.PlotDataItem()
            direction = phasingFrame.getDirection()
            if direction == 0:
                angle = 0
                phaseTraces = self.hPhaseTraces
                position = self.strip.mousePosition[1]
                if not self.strip.haveSetHPhasingPivot:
                    viewParams = self._getSpectrumViewParams(0)
                    self.strip.hPhasingPivot.setPos(0.5 * (viewParams.minSpectrumFrequency +
                                                           viewParams.maxSpectrumFrequency))
                    self.strip.hPhasingPivot.setVisible(True)
                    self.strip.haveSetHPhasingPivot = True
            else:
                angle = 90
                phaseTraces = self.vPhaseTraces
                position = self.strip.mousePosition[0]
                if not self.strip.haveSetVPhasingPivot:
                    viewParams = self._getSpectrumViewParams(1)
                    self.strip.vPhasingPivot.setPos(0.5 * (viewParams.minSpectrumFrequency +
                                                           viewParams.maxSpectrumFrequency))
                    self.strip.vPhasingPivot.setVisible(True)
                    self.strip.haveSetVPhasingPivot = True

            line = pg.InfiniteLine(angle=angle, pos=position, movable=True)
            line.sigPositionChanged.connect(lambda phasingLine: self._updatePhasing())
            self.strip.plotWidget.scene().addItem(trace)
            self.strip.plotWidget.addItem(line)
            trace.setVisible(True)
            line.setVisible(True)
            phaseTraces.append((trace, line))
            self._updatePhasing()

    def removePhasingTraces(self):

        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():
            direction = phasingFrame.getDirection()
            if direction == 0:
                for trace, line in self.hPhaseTraces:
                    self.strip.plotWidget.scene().removeItem(trace)
                    self.strip.plotWidget.removeItem(line)
                self.hPhaseTraces = []
            else:
                for trace, line in self.vPhaseTraces:
                    self.strip.plotWidget.scene().removeItem(trace)
                    self.strip.plotWidget.removeItem(line)
                self.vPhaseTraces = []

    def _changedPhasingDirection(self):

        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        direction = phasingFrame.getDirection()
        if direction == 0:
            for trace, line in self.hPhaseTraces:
                trace.setVisible(True)
                line.setVisible(True)
            for trace, line in self.vPhaseTraces:
                trace.setVisible(False)
                line.setVisible(False)
        else:
            for trace, line in self.hPhaseTraces:
                trace.setVisible(False)
                line.setVisible(False)
            for trace, line in self.vPhaseTraces:
                trace.setVisible(True)
                line.setVisible(True)

        self._updatePhasing()

    def _updatePhasing(self):
        """
        # CCPN INTERNAL - called in _updatePhasing method of GuiStrip
        """
        if not self.isVisible():
            return

    def _getTraceParams(self, position):
        # position is in ppm

        inRange = True
        point = len(position) * [0]

        xDataDim = xMinFrequency = xMaxFrequency = xPointCount = yDataDim = yMinFrequency = yMaxFrequency = yPointCount = None

        for n, pos in enumerate(position):  # n = 0 is x, n = 1 is y, etc.
            # spectrumPos, width, totalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim = self._getSpectrumViewParams(n)

            try:
                valuePerPoint, _, pointCount, _, _, dataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(n)
            except:
                # skip if the dimension doesn't exist
                break

            if dataDim:
                if n == 0:
                    xDataDim = dataDim
                    # -1 below because points start at 1 in data model
                    xMinFrequency = int(dataDim.primaryDataDimRef.valueToPoint(maxSpectrumFrequency) - 1)
                    xMaxFrequency = int(dataDim.primaryDataDimRef.valueToPoint(minSpectrumFrequency) - 1)
                    xPointCount = pointCount
                elif n == 1:
                    yDataDim = dataDim
                    yMinFrequency = int(dataDim.primaryDataDimRef.valueToPoint(maxSpectrumFrequency) - 1)
                    yMaxFrequency = int(dataDim.primaryDataDimRef.valueToPoint(minSpectrumFrequency) - 1)
                    yPointCount = pointCount
                else:
                    inRange = (minSpectrumFrequency <= pos <= maxSpectrumFrequency)
                    if not inRange:
                        break
                pnt = (dataDim.primaryDataDimRef.valueToPoint(pos) - 1) % pointCount
                pnt += (dataDim.pointOffset if hasattr(dataDim, "pointOffset") else 0)

                try:
                    point[dataDim.dim - 1] = pnt
                except Exception as es:
                    # error here if the axis code can't be found in the array, e.g. when viewing 2d overlaid on Nd spectra
                    continue

        return inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xPointCount, yDataDim, yMinFrequency, yMaxFrequency, yPointCount

    def _updateTrace(self, position, positionPixel, updateHTrace=True, updateVTrace=True):

        if not (updateHTrace or updateVTrace) or not self.isVisible():
            self.hTrace.setData([], [])
            self.vTrace.setData([], [])
            return

        inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, yDataDim, yMinFrequency, yMaxFrequency, yNumPoints = self._getTraceParams(position)
        # xDataDim and yDataDim should always be set here, because all spectra in strip should at least match in x, y

        if inRange and updateHTrace:
            self._updateHTraceData(point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, self.hTrace)
        else:
            self.hTrace.setData([], [])

        if inRange and updateVTrace:
            self._updateVTraceData(point, yDataDim, yMinFrequency, yMaxFrequency, yNumPoints, positionPixel, self.vTrace)
        else:
            self.vTrace.setData([], [])

        self.strip.plotWidget.plotItem.update()

    @property
    def traceScale(self) -> float:
        """Scale for trace in this spectrumView"""
        return self._traceScale

    @traceScale.setter
    def traceScale(self, value):
        """Setter for scale for trace in this spectrumView"""
        self._traceScale = value
        self.strip._updateTraces()
        self._updatePhasing()

    def _printContourData(self, printer, contourData, colour, xTile0, xTile1, yTile0, yTile1, xTranslate, xScale, xTotalPointCount, yTranslate, yScale,
                          yTotalPointCount):

        for xTile in range(xTile0, xTile1):
            for yTile in range(yTile0, yTile1):

                # the below is because the y axis goes from top to bottom
                #GL.glScale(1.0, -1.0, 1.0)
                #GL.glTranslate(0.0, -self.strip.plotWidget.height(), 0.0)

                # the below makes sure that spectrum points get mapped to screen pixels correctly
                #GL.glTranslate(xTranslate, yTranslate, 0.0)
                #GL.glScale(xScale, yScale, 1.0)

                #GL.glTranslate(xTotalPointCount*xTile, yTotalPointCount*yTile, 0.0)
                #GL.glClipPlane(GL.GL_CLIP_PLANE0, (1.0, 0.0, 0.0, - (xClipPoint0 - xTotalPointCount*xTile)))
                #GL.glClipPlane(GL.GL_CLIP_PLANE1, (-1.0, 0.0, 0.0, xClipPoint1 - xTotalPointCount*xTile))
                #GL.glClipPlane(GL.GL_CLIP_PLANE2, (0.0, 1.0, 0.0, - (yClipPoint0 - yTotalPointCount*yTile)))
                #GL.glClipPlane(GL.GL_CLIP_PLANE3, (0.0, -1.0, 0.0, yClipPoint1 - yTotalPointCount*yTile))

                for contour in contourData:
                    n = len(contour) // 2
                    contour = contour.copy()
                    contour = contour.reshape((n, 2))
                    contour[:, 0] += xTotalPointCount * xTile
                    contour[:, 0] *= xScale
                    contour[:, 0] += xTranslate
                    contour[:, 1] += yTotalPointCount * yTile
                    contour[:, 1] *= yScale
                    contour[:, 1] += yTranslate
                    printer.writePolyline(contour, colour)

    def _buildGLContours(self, glList, firstShow=True):

        ##self.drawContoursCounter += 1
        ##print('***drawContours counter (%s): %d' % (self, self.drawContoursCounter))

        # GWV 02122020: Should always have been set on newObject or restored object

        # if not self.spectrum.noiseLevel and firstShow:
        #     getLogger().info("estimating noise level for spectrum %s" % str(self.spectrum.pid))
        #     setContourLevelsFromNoise(self.spectrum, setNoiseLevel=True,
        #                               setPositiveContours=True, setNegativeContours=True,
        #                               useSameMultiplier=True)

        if self.spectrum.positiveContourBase is None or self.spectrum.positiveContourBase == 0.0:
            raise RuntimeError('Positive Contour Base is not defined')

        if self.spectrum.negativeContourBase is None or self.spectrum.negativeContourBase == 0.0:
            raise RuntimeError('Negative Contour Base is not defined')

        if self.spectrum.includePositiveContours:  # .displayPositiveContours:
            self.posLevels = _getLevels(self.positiveContourCount, self.positiveContourBase,
                                        self.positiveContourFactor)
        else:
            self.posLevels = []

        if self.spectrum.includeNegativeContours:  # .displayNegativeContours:
            self.negLevels = _getLevels(self.negativeContourCount, self.negativeContourBase,
                                        self.negativeContourFactor)
        else:
            self.negLevels = []

        # if not self.posLevels and not self.negLevels:
        #   return

        # self.posColour = Colour.scaledRgba(self._getColour('positiveContourColour'))  # TBD: for now assume only one colour
        # self.negColour = Colour.scaledRgba(self._getColour('negativeContourColour'))  # and assumes these attributes are set
        # glList.posColour = self.posColour
        # glList.negColour = self.negColour

        colName = self._getColour('positiveContourColour')
        if not colName.startswith('#'):
            # get the colour from the gradient table or a single red
            colListPos = tuple(Colour.scaledRgba(col) for col in Colour.colorSchemeTable[colName]) if colName in Colour.colorSchemeTable else ((1, 0, 0, 1),)
        else:
            colListPos = (Colour.scaledRgba(colName),)

        colName = self._getColour('negativeContourColour')
        if not colName.startswith('#'):
            # get the colour from the gradient table or a single red
            colListNeg = tuple(Colour.scaledRgba(col) for col in Colour.colorSchemeTable[colName]) if colName in Colour.colorSchemeTable else ((1, 0, 0, 1),)
        else:
            colListNeg = (Colour.scaledRgba(colName),)

        glList.posColours = self.posColours = colListPos
        glList.negColours = self.negColours = colListNeg

        try:
            self._constructContours(self.posLevels, self.negLevels, glList=glList, doRefresh=True)
        except FileNotFoundError:
            self._project._logger.warning("No data file found for %s" % self)
            return

    #def drawContours(self, painter, guiStrip):
    def _buildContours(self, painter):

        ##self.drawContoursCounter += 1
        ##print('***drawContours counter (%s): %d' % (self, self.drawContoursCounter))

        # print('>>>_buildContours %s' % self)

        if self.spectrum.positiveContourBase is None or self.spectrum.positiveContourBase == 0.0:
            raise RuntimeError('Positive Contour Base is not defined')

        if self.spectrum.negativeContourBase is None or self.spectrum.negativeContourBase == 0.0:
            raise RuntimeError('Negative Contour Base is not defined')

        if self.spectrum.includePositiveContours:  # .displayPositiveContours:
            self.posLevels = _getLevels(self.positiveContourCount, self.positiveContourBase,
                                        self.positiveContourFactor)
        else:
            self.posLevels = []

        if self.spectrum.includeNegativeContours:  # .displayNegativeContours:
            self.negLevels = _getLevels(self.negativeContourCount, self.negativeContourBase,
                                        self.negativeContourFactor)
        else:
            self.negLevels = []

        # if not self.posLevels and not self.negLevels:
        #     return

        try:
            self._constructContours(self.posLevels, self.negLevels)
        except FileNotFoundError:
            self._project._logger.warning("No data file found for %s" % self)
            return

        self.posColour = Colour.scaledRgba(self._getColour('positiveContourColour'))  # TBD: for now assume only one colour
        self.negColour = Colour.scaledRgba(self._getColour('negativeContourColour'))  # and assumes these attributes are set

    def _paintContours(self, painter, skip=False):
        if not skip:
            painter.beginNativePainting()  # this puts OpenGL back in its default coordinate system instead of Qt one

        try:

            xTranslate, xScale, xTotalPointCount, xClipPoint0, xClipPoint1 = self._getTranslateScale(0)
            yTranslate, yScale, yTotalPointCount, yClipPoint0, yClipPoint1 = self._getTranslateScale(1)

            xTile0 = xClipPoint0 // xTotalPointCount
            xTile1 = 1 + (xClipPoint1 - 1) // xTotalPointCount
            yTile0 = yClipPoint0 // yTotalPointCount
            yTile1 = 1 + (yClipPoint1 - 1) // yTotalPointCount

            # GL.glEnable(GL.GL_CLIP_PLANE0)
            GL.glEnable(GL.GL_CLIP_PLANE1)
            GL.glEnable(GL.GL_CLIP_PLANE2)
            # GL.glEnable(GL.GL_CLIP_PLANE3)

            # TODO:ED - why am I displaying a series of tiles?
            # xTile1 = 1
            # yTile1 = 1

            # for xTile in range(xTile0, xTile1):
            #   for yTile in range(yTile0, yTile1):

            xTile = 0  # ejb - temp to only draw one set
            yTile = 0

            if not skip:
                GL.glLoadIdentity()
                GL.glPushMatrix()

                # the below is because the y axis goes from top to bottom
                GL.glScale(1.0, -1.0, 1.0)
                GL.glTranslate(0.0, -self.strip.plotWidget.height(), 0.0)

                # the below makes sure that spectrum points get mapped to screen pixels correctly
                GL.glTranslate(xTranslate, yTranslate, 0.0)
                GL.glScale(xScale, yScale, 1.0)

                GL.glTranslate(xTotalPointCount * xTile, yTotalPointCount * yTile, 0.0)

            # GL.glClipPlane(GL.GL_CLIP_PLANE0, (1.0, 0.0, 0.0, - (xClipPoint0 - xTotalPointCount*xTile)))
            GL.glClipPlane(GL.GL_CLIP_PLANE1, (-1.0, 0.0, 0.0, xClipPoint1 - xTotalPointCount * xTile))
            GL.glClipPlane(GL.GL_CLIP_PLANE2, (0.0, 1.0, 0.0, - (yClipPoint0 - yTotalPointCount * yTile)))
            # GL.glClipPlane(GL.GL_CLIP_PLANE3, (0.0, -1.0, 0.0, yClipPoint1 - yTotalPointCount*yTile))

            for (colour, levels, displayLists) in ((self.posColour, self.posLevels, self.posDisplayLists),
                                                   (self.negColour, self.negLevels, self.negDisplayLists)):
                for n, level in enumerate(levels):
                    GL.glColor4f(*colour)
                    # TBD: scaling, translating, etc.
                    GL.glCallList(displayLists[n])

            if not skip:
                GL.glPopMatrix()

            # GL.glDisable(GL.GL_CLIP_PLANE0)
            GL.glDisable(GL.GL_CLIP_PLANE1)
            GL.glDisable(GL.GL_CLIP_PLANE2)
            # GL.glDisable(GL.GL_CLIP_PLANE3)

        finally:
            if not skip:
                painter.endNativePainting()

    # from ccpn.util.decorators import profile
    # @profile
    def _constructContours(self, posLevels, negLevels, doRefresh=False, glList=None):
        """ Construct the contours for this spectrum using an OpenGL display list
            The way this is done here, any change in contour level needs to call this function.
        """
        xDataDim, yDataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[:2]

        if (doRefresh or xDataDim is not self.xDataDimPrev or yDataDim is not self.yDataDimPrev
                or self.zRegionPrev != tuple([tuple(axis.region) for axis in self.strip.orderedAxes[2:]])):
            # self._releaseDisplayLists(self.posDisplayLists)
            # self._releaseDisplayLists(self.negDisplayLists)
            doPosLevels = doNegLevels = True
        else:
            if list(posLevels) == self.posLevelsPrev:
                doPosLevels = False
            else:
                # self._releaseDisplayLists(self.posDisplayLists)
                doPosLevels = posLevels and True
            if list(negLevels) == self.negLevelsPrev:
                doNegLevels = False
            else:
                # self._releaseDisplayLists(self.negDisplayLists)
                doNegLevels = negLevels and True

        ###self.previousRegion = self.guiSpectrumDisplay.region[:]  # TBD: not quite right, should be looking at the strip(s)

        # do the contouring and store results in display list
        if doPosLevels:
            posLevelsArray = numpy.array(posLevels, numpy.float32)
            # print(posLevelsArray)
            # self._createDisplayLists(posLevelsArray, self.posDisplayLists)

        if doNegLevels:
            negLevelsArray = numpy.array(negLevels, numpy.float32)
            # self._createDisplayLists(negLevelsArray, self.negDisplayLists)

        self.posLevelsPrev = list(posLevels)
        self.negLevelsPrev = list(negLevels)
        self.xDataDimPrev = xDataDim
        self.yDataDimPrev = yDataDim
        self.zRegionPrev = tuple([tuple(axis.region) for axis in self.strip.orderedAxes[2:]])

        # if not doPosLevels and not doNegLevels:
        #     return

        #for position, dataArray in self.getPlaneData(guiStrip):
        posContoursAll = negContoursAll = None

        numDims = self.spectrum.dimensionCount

        if _NEWCOMPILEDCONTOURS:
            # new code for the recompiled glList
            # test = None

            # get the positive contour colour list
            _posColours = []
            stepX = len(posLevels) - 1
            step = stepX
            stepY = len(self.posColours) - 1
            jj = 0
            if stepX > 0:
                for ii in range(stepX + 1):
                    _interp = (stepX - step) / stepX
                    _intCol = Colour.interpolateColourRgba(self.posColours[min(jj, stepY)], self.posColours[min(jj + 1, stepY)],
                                                           _interp,
                                                           alpha=1.0)
                    _posColours.extend(_intCol)
                    step -= stepY
                    while step < 0:
                        step += stepX
                        jj += 1
            else:
                _posColours = self.posColours[0]

            # get the positive contour colour list
            _negColours = []
            stepX = len(negLevels) - 1
            step = stepX
            stepY = len(self.negColours) - 1
            jj = 0
            if stepX > 0:
                for ii in range(stepX + 1):
                    _interp = (stepX - step) / stepX
                    _intCol = Colour.interpolateColourRgba(self.negColours[min(jj, stepY)], self.negColours[min(jj + 1, stepY)],
                                                           _interp,
                                                           alpha=1.0)
                    _negColours.extend(_intCol)
                    step -= stepY
                    while step < 0:
                        step += stepX
                        jj += 1
            else:
                _negColours = self.negColours[0]

            contourList = None
            if numDims < 3 or self._application.preferences.general.generateSinglePlaneContours:
                dataArrays = tuple()
                for position, dataArray in self._getPlaneData():
                    dataArrays += (dataArray,)

                contourList = Contourer2d.contourerGLList(dataArrays,
                                                          posLevelsArray,
                                                          negLevelsArray,
                                                          np.array(_posColours, dtype=np.float32),
                                                          np.array(_negColours, dtype=np.float32))
                # np.array(self.posColour * len(posLevels), dtype=np.float32),
                # np.array(self.negColour * len(negLevels), dtype=np.float32))
            else:

                specIndices = self._displayOrderSpectrumDimensionIndices
                stripIndices = tuple(specIndices.index(ii) for ii in range(numDims))
                regionLimits = tuple(axis.region for axis in self.strip.orderedAxes)

                axisLimits = dict([(self.spectrum.axisCodes[ii], regionLimits[stripIndices[ii]])
                                   for ii in range(numDims) if stripIndices[ii] is not None and stripIndices[ii] > 1])

                # this isn't fully tested and still has an offset of -1
                # cheat to move the spectrum by 1 point by adding buffer to visible XY axes
                exclusionBuffer = [0 if stripIndices[ii] > 1 else 1 for ii in range(numDims)]

                foundRegions = self.spectrum.getRegionData(exclusionBuffer=exclusionBuffer, minimumDimensionSize=1, **axisLimits)

                if foundRegions:
                    # just use the first region
                    for region in foundRegions[:1]:
                        dataArray, intRegion, *rest = region

                        if dataArray.size:
                            xyzDims = tuple((numDims - ind - 1) for ind in specIndices)
                            xyzDims = tuple(reversed(xyzDims))
                            tempDataArray = dataArray.transpose(*xyzDims)

                            # flatten multidimensional arrays into single array
                            for maxCount in range(numDims - 2):
                                tempDataArray = np.max(tempDataArray.clip(0.0, 1e15), axis=0) + np.min(tempDataArray.clip(-1e12, 0.0), axis=0)

                            contourList = Contourer2d.contourerGLList((tempDataArray,),
                                                                      posLevelsArray,
                                                                      negLevelsArray,
                                                                      np.array(_posColours, dtype=np.float32),
                                                                      np.array(_negColours, dtype=np.float32))
                            # np.array(self.posColour * len(posLevels), dtype=np.float32),
                            # np.array(self.negColour * len(negLevels), dtype=np.float32))

            if contourList and contourList[1] > 0:
                # set the contour arrays for the GL object
                glList.numVertices = contourList[1]
                glList.indices = contourList[2]
                glList.vertices = contourList[3]
                glList.colors = contourList[4]
                # min1x = np.min(glList.vertices[::2])
                # max1x = np.max(glList.vertices[::2])
                # min1y = np.min(glList.vertices[1::2])
                # max1y = np.max(glList.vertices[1::2])
                # print('>>>min, max', min1x, max1x, min1y, max1y)
            else:
                # clear the arrays
                glList.numVertices = 0
                glList.indices = np.array((), dtype=np.uint32)
                glList.vertices = np.array((), dtype=np.float32)
                glList.colors = np.array((), dtype=np.float32)

        else:
            for position, dataArray in self._getPlaneData():
                if doPosLevels:
                    posContours = Contourer2d.contourer2d(dataArray, posLevelsArray)
                    #print("posContours", posContours)
                    if posContoursAll is None:
                        posContoursAll = posContours
                    else:
                        for n, contourData in enumerate(posContours):
                            if len(posContoursAll) == n:  # this can happen (if no contours at a given level then contourer immediately exits)
                                posContoursAll.append(contourData)
                            else:
                                posContoursAll[n].extend(contourData)
                            # print(contourData)

                if doNegLevels:
                    negContours = Contourer2d.contourer2d(dataArray, negLevelsArray)
                    #print("negContours", len(negContours))
                    if negContoursAll is None:
                        negContoursAll = negContours
                    else:
                        for n, contourData in enumerate(negContours):
                            if len(negContoursAll) == n:  # this can happen (if no contours at a given level then contourer immediately exits)
                                negContoursAll.append(contourData)
                            else:
                                negContoursAll[n].extend(contourData)
                            # print(contourData)

            glList.clearArrays()

            if posContoursAll:
                for n, contourData in enumerate(posContoursAll):
                    for contour in contourData:
                        glList.numVertices += len(contour)

            if negContoursAll:
                for n, contourData in enumerate(negContoursAll):
                    for contour in contourData:
                        glList.numVertices += len(contour)

            glList.vertices = np.empty(glList.numVertices, dtype=np.float32)
            glList.indices = np.empty(glList.numVertices, dtype=np.uint32)
            glList.colors = np.empty(2 * glList.numVertices, dtype=np.float32)

            thisIndex = 0
            thisVertex = 0
            thisColor = 0
            indexCount = 0

            if posContoursAll:
                for n, contourData in enumerate(posContoursAll):
                    for contour in contourData:
                        count = len(contour)
                        thisNumVertices = count // 2
                        colCount = 2 * count

                        glList.indices[thisIndex:thisIndex + count] = tuple((((ll + 1) // 2) % thisNumVertices) + indexCount for ll in range(count))
                        glList.vertices[thisVertex:thisVertex + count] = contour
                        glList.colors[thisColor:thisColor + colCount] = self.posColour * thisNumVertices
                        indexCount += thisNumVertices
                        thisIndex += count
                        thisVertex += count
                        thisColor += colCount

            if negContoursAll:
                for n, contourData in enumerate(negContoursAll):
                    for contour in contourData:
                        count = len(contour)
                        thisNumVertices = count // 2
                        colCount = 2 * count

                        glList.indices[thisIndex:thisIndex + count] = tuple((((ll + 1) // 2) % thisNumVertices) + indexCount for ll in range(count))
                        glList.vertices[thisVertex:thisVertex + count] = contour
                        glList.colors[thisColor:thisColor + colCount] = self.negColour * thisNumVertices
                        indexCount += thisNumVertices
                        thisIndex += count
                        thisVertex += count
                        thisColor += colCount

    def _releaseDisplayLists(self, displayLists):

        for displayList in displayLists:
            GL.glDeleteLists(displayList, 1)
        displayLists[:] = []

    def _createDisplayLists(self, levels, displayLists):

        # could create them in one go but more likely to get fragmentation that way
        for level in levels:
            displayLists.append(GL.glGenLists(1))

    #def getPlaneData(self, guiStrip):
    def _getPlaneData(self):

        # NBNB TODO FIXME - Wayne, please check through the modified code

        spectrum = self.spectrum
        dimensionCount = spectrum.dimensionCount
        dimIndices = self._displayOrderSpectrumDimensionIndices
        xDim = dimIndices[0]
        yDim = dimIndices[1]
        orderedAxes = self._apiStripSpectrumView.strip.orderedAxes

        # apiSpectrumView = self._apiStripSpectrumView.spectrumView
        # orderedAxes = self._apiStripSpectrumView.strip.orderedAxes
        # dataDims = apiSpectrumView.orderedDataDims
        # ll = apiSpectrumView.dataSource.sortedDataDims()
        # # NB Not all dataDIms must match spectrum e.g. 2D spectra in a 3D display
        # dimIndices = [x and ll.index(x) for x in dataDims]
        # xDim = dimIndices[0]
        # yDim = dimIndices[1]
        # # xDim = dataDims[0].dim - 1  # -1 because dataDim.dim starts at 1
        # # yDim = dataDims[1].dim - 1
        # spectrum = self.spectrum
        # dimensionCount = spectrum.dimensionCount

        if dimensionCount == 2:
            planeData = spectrum.getPlaneData(xDim=xDim + 1, yDim=yDim + 1)
            position = [1, 1]
            yield position, planeData
        elif dimensionCount == 3:
            # zDim = dataDims[2].dim - 1
            # zDataDim = dataDims[2]
            # zPosition, width, zTotalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim = self._getSpectrumViewParams(2)
            valuePerPoint, _, zPointCount, _, _, zDataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(2)
            zPosition = orderedAxes[2].position
            width = orderedAxes[2].width

            if not (minSpectrumFrequency <= zPosition <= maxSpectrumFrequency):
                getLogger().debug2('skipping plane depth out-of-range test')
                # return

            zRegionValue = (zPosition + 0.5 * width, zPosition - 0.5 * width)  # Note + and - (axis backwards)
            # zPoint0, zPoint1 = spectrum.getDimPointFromValue(zDim, zRegionValue)
            valueToPoint = zDataDim.primaryDataDimRef.valueToPoint
            # -1 below because points start at 1 in data model
            zPointFloat0 = valueToPoint(zRegionValue[0]) - 1
            zPointFloat1 = valueToPoint(zRegionValue[1]) - 1

            zPoint0, zPoint1 = (int(zPointFloat0 + (1 if zPointFloat0 >= 0 else 0)),  # this gives first and 1+last integer in range
                                int(zPointFloat1 + (1 if zPointFloat1 >= 0 else 0)))  # and take into account negative valueToPoint
            if zPoint0 == zPoint1:
                if zPointFloat0 - (zPoint0 - 1) < zPoint1 - zPointFloat1:  # which is closest to an integer
                    zPoint0 -= 1
                else:
                    zPoint1 += 1

            # ensures that the plane valueToPoint is always positive - but conflicts with aliasing in the zPlane
            if (zPoint1 - zPoint0) >= zPointCount:
                zPoint0 = 0
                zPoint1 = zPointCount
            else:
                zPoint0 %= zPointCount
                zPoint1 %= zPointCount
                if zPoint1 < zPoint0:
                    zPoint1 += zPointCount

            # zPointOffset = spectrum.pointOffsets[zDim]
            # zPointCount = spectrum.pointCounts[zDim]
            zPointOffset = zDataDim.pointOffset if hasattr(zDataDim, "pointOffset") else 0
            zNumPoints = zDataDim.numPoints

            position = dimensionCount * [1]
            for z in range(zPoint0, zPoint1):
                zPosition = z % zPointCount
                zPosition -= zPointOffset
                if 0 <= zPosition < zNumPoints:
                    position[dimIndices[2]] = zPosition + 1
                    planeData = spectrum.getPlaneData(position, xDim=xDim + 1, yDim=yDim + 1)
                    yield position, planeData

        elif dimensionCount == 4:
            # zDim = dataDims[2].dim - 1
            # zDataDim = dataDims[2]
            # zPosition, width, zTotalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim = self._getSpectrumViewParams(2)
            valuePerPoint, _, zPointCount, _, _, zDataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(2)
            zPosition = orderedAxes[2].position
            width = orderedAxes[2].width

            if not (minSpectrumFrequency <= zPosition <= maxSpectrumFrequency):
                getLogger().debug2('skipping plane depth out-of-range test')
                # return

            zRegionValue = (zPosition + 0.5 * width, zPosition - 0.5 * width)  # Note + and - (axis backwards)
            # zPoint0, zPoint1 = spectrum.getDimPointFromValue(zDim, zRegionValue)
            valueToPoint = zDataDim.primaryDataDimRef.valueToPoint
            # -1 below because points start at 1 in data model
            zPointFloat0 = valueToPoint(zRegionValue[0]) - 1
            zPointFloat1 = valueToPoint(zRegionValue[1]) - 1

            zPoint0, zPoint1 = (int(zPointFloat0 + (1 if zPointFloat0 >= 0 else 0)),  # this gives first and 1+last integer in range
                                int(zPointFloat1 + (1 if zPointFloat1 >= 0 else 0)))  # and take into account negative valueToPoint
            if zPoint0 == zPoint1:
                if zPointFloat0 - (zPoint0 - 1) < zPoint1 - zPointFloat1:  # which is closest to an integer
                    zPoint0 -= 1
                else:
                    zPoint1 += 1

            if (zPoint1 - zPoint0) >= zPointCount:
                zPoint0 = 0
                zPoint1 = zPointCount
            else:
                zPoint0 %= zPointCount
                zPoint1 %= zPointCount
                if zPoint1 < zPoint0:
                    zPoint1 += zPointCount

            zPointOffset = zDataDim.pointOffset if hasattr(zDataDim, "pointOffset") else 0
            zNumPoints = zDataDim.numPoints

            # wDim = dataDims[3].dim - 1
            # wDataDim = dataDims[3]
            # wPosition, width, wTotalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim = self._getSpectrumViewParams(3)
            valuePerPoint, _, wPointCount, _, _, wDataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(3)
            wPosition = orderedAxes[3].position
            width = orderedAxes[3].width

            if not (minSpectrumFrequency <= wPosition <= maxSpectrumFrequency):
                return

            wRegionValue = (wPosition + 0.5 * width, wPosition - 0.5 * width)  # Note + and - (axis backwards)
            # wPoint0, wPoint1 = spectrum.getDimPointFromValue(wDim, wRegionValue)
            valueToPoint = wDataDim.primaryDataDimRef.valueToPoint
            # -1 below because points start at 1 in data model
            wPointFloat0 = valueToPoint(wRegionValue[0]) - 1
            wPointFloat1 = valueToPoint(wRegionValue[1]) - 1

            wPoint0, wPoint1 = (int(wPointFloat0 + 1), int(wPointFloat1 + 1))  # this gives first and 1+last integer in range
            if wPoint0 == wPoint1:
                if wPointFloat0 - (wPoint0 - 1) < wPoint1 - wPointFloat1:  # which is closest to an integer
                    wPoint0 -= 1
                else:
                    wPoint1 += 1

            if (wPoint1 - wPoint0) >= wPointCount:
                wPoint0 = 0
                wPoint1 = wPointCount
            else:
                wPoint0 %= wPointCount
                wPoint1 %= wPointCount
                if wPoint1 < wPoint0:
                    wPoint1 += wPointCount

            # wPointOffset = spectrum.pointOffsets[wDim]
            # wPointCount = spectrum.pointCounts[wDim]
            wPointOffset = wDataDim.pointOffset if hasattr(zDataDim, "pointOffset") else 0
            wNumPoints = wDataDim.numPoints

            position = dimensionCount * [1]
            for z in range(zPoint0, zPoint1):
                zPosition = z % zPointCount
                zPosition -= zPointOffset
                if 0 <= zPosition < zNumPoints:
                    position[dimIndices[2]] = zPosition + 1
                    for w in range(wPoint0, wPoint1):
                        wPosition = w % wPointCount
                        wPosition -= wPointOffset
                        if 0 <= wPosition < wNumPoints:
                            position[dimIndices[3]] = wPosition + 1
                            planeData = spectrum.getPlaneData(position, xDim=xDim + 1, yDim=yDim + 1)
                            yield position, planeData

    def _getVisiblePlaneList(self, firstVisible=None, minimumValuePerPoint=None):

        # NBNB TODO FIXME - Wayne, please check through the modified code

        spectrum = self.spectrum
        dimensionCount = spectrum.dimensionCount
        dimIndices = self._displayOrderSpectrumDimensionIndices
        xDim = dimIndices[0]
        yDim = dimIndices[1]
        orderedAxes = self._apiStripSpectrumView.strip.orderedAxes

        if dimensionCount <= 2:
            return None, None

        else:

            planeList = ()
            planePointValues = ()

            for dim in range(2, dimensionCount):

                # make sure there is always a spectrumView to base visibility on
                # useFirstVisible = firstVisible if firstVisible else self
                zPosition = orderedAxes[dim].position

                # check as there could be more dimensions
                # planeCount = self.strip.planeToolbar.planeCounts[dim - 2].value()
                planeCount = self.strip.planeAxisBars[dim - 2].planeCount  #   .planeToolbar.planeCounts[dim - 2].value()

                # valuePerPoint, _, _, _, _ = useFirstVisible._getSpectrumViewParams(2)
                # zRegionValue = (zPosition + 0.5 * (planeCount+2) * valuePerPoint, zPosition - 0.5 * (planeCount+2) * valuePerPoint)  # Note + and - (axis backwards)

                # now get the z bounds for this spectrum
                valuePerPoint, _, _, _, _, zDataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(dim)

                # pass in a smaller valuePerPoint - if there are differences in the z-resolution, otherwise just use local valuePerPoint
                minZWidth = 3 * valuePerPoint
                zWidth = (planeCount + 2) * minimumValuePerPoint[dim - 2] if minimumValuePerPoint else (planeCount + 2) * valuePerPoint

                zWidth = max(zWidth, minZWidth)

                zRegionValue = (zPosition + 0.5 * zWidth, zPosition - 0.5 * zWidth)  # Note + and - (axis backwards)
                if not (minSpectrumFrequency <= zPosition <= maxSpectrumFrequency):
                    getLogger().debug('skipping plane depth out-of-range test')
                    # return

                if hasattr(zDataDim, 'primaryDataDimRef'):
                    ddr = zDataDim.primaryDataDimRef
                    valueToPoint = ddr and ddr.valueToPoint
                    pointToValue = ddr and ddr.pointToValue
                else:
                    valueToPoint = zDataDim.valueToPoint
                    pointToValue = zDataDim.pointToValue

                # -1 below because points start at 1 in data model
                zPointFloat0 = valueToPoint(zRegionValue[0]) - 1
                zPointFloat1 = valueToPoint(zRegionValue[1]) - 1

                zPoint0, zPoint1 = (int(zPointFloat0 + (1 if zPointFloat0 >= 0 else 0)),  # this gives first and 1+last integer in range
                                    int(zPointFloat1 + (1 if zPointFloat1 >= 0 else 0)))  # and take into account negative valueToPoint
                if zPoint0 == zPoint1:
                    if zPointFloat0 - (zPoint0 - 1) < zPoint1 - zPointFloat1:  # which is closest to an integer
                        zPoint0 -= 1
                    else:
                        zPoint1 += 1

                # ensures that the plane valueToPoint is always positive - but conflicts with aliasing in the zPlane
                # if (zPoint1 - zPoint0) >= zTotalPointCount:
                #     # set to the full range
                #     zPoint0 = 0
                #     zPoint1 = zTotalPointCount
                # else:
                #     zPoint0 %= zTotalPointCount
                #     zPoint1 %= zTotalPointCount
                #     if zPoint1 < zPoint0:
                #         zPoint1 += zTotalPointCount

                zPointOffset = zDataDim.pointOffset if hasattr(zDataDim, "pointOffset") else 0
                zPointCount = zDataDim.numPoints

                planeList = planeList + ((tuple(zz for zz in range(zPoint0, zPoint1)), zPointOffset, zPointCount),)

                # need to add 0.5 for the indexing in the api
                planePointValues = planePointValues + ((tuple(pointToValue(zz + 0.5) for zz in range(zPoint0, zPoint1 + 1)), zPointOffset, zPointCount),)

            # return (tuple(zz for zz in range(zPoint0, zPoint1)), zPointOffset, zPointCount)
            return planeList, planePointValues

    def _getValues(self, dimensionCount=None):
        # ejb - get some spectrum information for scaling the display
        if not dimensionCount:
            dimensionCount = self.spectrum.dimensionCount

        return [self._getSpectrumViewParams(vParam) for vParam in range(0, dimensionCount)]

    def refreshData(self):
        # spawn a rebuild in the openGL strip
        self.buildContours = True

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

