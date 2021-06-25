"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-25 15:32:38 +0100 (Fri, June 25, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from itertools import product
from collections import namedtuple
from PyQt5 import QtCore
from ccpn.util import Colour
from ccpnc.contour import Contourer2d
from ccpn.ui.gui.lib.GuiSpectrumView import GuiSpectrumView


_NEWCOMPILEDCONTOURS = True

AxisPlaneData = namedtuple('AxisPlaneData', 'startPoint endPoint pointCount')


#TODO:RASMUS: why is this function here when the wrapper has positiveLevels and negativeLevels
# attributes
def _getLevels(count: int, base: float, factor: float) -> list:
    "return a list with contour levels"
    levels = []
    if count > 0:
        levels = [base]
        for n in range(count - 1):
            levels.append(np.float32(factor * levels[-1]))
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

    def _buildGLContours(self, glList):
        """Build the contour arrays
        """
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

        colName = self._getColour('positiveContourColour') or '#E00810'
        if not colName.startswith('#'):
            # get the colour from the gradient table or a single red
            colListPos = tuple(Colour.scaledRgba(col) for col in Colour.colorSchemeTable[colName]) if colName in Colour.colorSchemeTable else ((1, 0, 0, 1),)
        else:
            colListPos = (Colour.scaledRgba(colName),)

        colName = self._getColour('negativeContourColour') or '#E00810'
        if not colName.startswith('#'):
            # get the colour from the gradient table or a single red
            colListNeg = tuple(Colour.scaledRgba(col) for col in Colour.colorSchemeTable[colName]) if colName in Colour.colorSchemeTable else ((1, 0, 0, 1),)
        else:
            colListNeg = (Colour.scaledRgba(colName),)

        glList.posColours = self.posColours = colListPos
        glList.negColours = self.negColours = colListNeg

        try:
            self._constructContours(self.posLevels, self.negLevels, glList=glList)
        except FileNotFoundError:
            self._project._logger.warning("No data file found for %s" % self)
            return

    def _constructContours(self, posLevels, negLevels, glList=None):
        """Construct the contours for this spectrum using an OpenGL display list
        The way this is done here, any change in contour level needs to call this function.
        """

        posLevelsArray = np.array(posLevels, np.float32)
        negLevelsArray = np.array(negLevels, np.float32)

        self.posLevelsPrev = list(posLevels)
        self.negLevelsPrev = list(negLevels)
        self.zRegionPrev = tuple([tuple(axis.region) for axis in self.strip.orderedAxes[2:]])

        posContoursAll = negContoursAll = None
        numDims = self.spectrum.dimensionCount

        if _NEWCOMPILEDCONTOURS:
            # new code for the recompiled glList

            # get the positive/negative contour colour lists
            _posColours = self._interpolateColours(self.posColours, posLevels)
            _negColours = self._interpolateColours(self.negColours, negLevels)

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
            else:

                specIndices = self.dimensionOrdering
                stripIndices = tuple(specIndices.index(ii) for ii in range(numDims))
                regionLimits = tuple(axis.region for axis in self.strip.orderedAxes)

                # get the spectrumLimits bounded by the first/last points
                axisLimits = {}
                for axisCode in self.spectrum.axisCodes:
                    lim = self.spectrum.getPpmArray(axisCode=axisCode)
                    axisLimits[axisCode] = (min(lim[0], lim[-1]),
                                            max(lim[0], lim[-1]))

                # fill the others in from the strip
                axisLimits.update(dict([(self.spectrum.axisCodes[ii], regionLimits[stripIndices[ii]])
                                        for ii in range(numDims) if stripIndices[ii] is not None and stripIndices[ii] > 1]))

                # use a single Nd dataArray and flatten to the visible axes - averages across the planes
                data = self.spectrum.getRegion(**axisLimits)

                if data is not None and data.size:
                    xyzDims = tuple((numDims - ind - 1) for ind in specIndices)
                    xyzDims = tuple(reversed(xyzDims))
                    tempDataArray = data.transpose(*xyzDims)

                    # flatten multidimensional arrays into single array
                    for maxCount in range(numDims - 2):
                        tempDataArray = np.max(tempDataArray.clip(0.0, 1e15), axis=0) + np.min(tempDataArray.clip(-1e12, 0.0), axis=0)

                    contourList = Contourer2d.contourerGLList((tempDataArray,),
                                                              posLevelsArray,
                                                              negLevelsArray,
                                                              np.array(_posColours, dtype=np.float32),
                                                              np.array(_negColours, dtype=np.float32))

            if contourList and contourList[1] > 0:
                # set the contour arrays for the GL object
                glList.numVertices = contourList[1]
                glList.indices = contourList[2]
                glList.vertices = contourList[3]
                glList.colors = contourList[4]
            else:
                # clear the arrays
                glList.numVertices = 0
                glList.indices = np.array((), dtype=np.uint32)
                glList.vertices = np.array((), dtype=np.float32)
                glList.colors = np.array((), dtype=np.float32)

        else:
            # old contouring
            doPosLevels = doNegLevels = True

            for position, dataArray in self._getPlaneData():
                if doPosLevels:
                    posContours = Contourer2d.contourer2d(dataArray, posLevelsArray)
                    if posContoursAll is None:
                        posContoursAll = posContours
                    else:
                        for n, contourData in enumerate(posContours):
                            if len(posContoursAll) == n:  # this can happen (if no contours at a given level then contourer immediately exits)
                                posContoursAll.append(contourData)
                            else:
                                posContoursAll[n].extend(contourData)

                if doNegLevels:
                    negContours = Contourer2d.contourer2d(dataArray, negLevelsArray)
                    if negContoursAll is None:
                        negContoursAll = negContours
                    else:
                        for n, contourData in enumerate(negContours):
                            if len(negContoursAll) == n:  # this can happen (if no contours at a given level then contourer immediately exits)
                                negContoursAll.append(contourData)
                            else:
                                negContoursAll[n].extend(contourData)

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

    def _interpolateColours(self, colourList, levels):
        colours = []
        stepX = len(levels) - 1
        step = stepX
        stepY = len(colourList) - 1
        jj = 0
        if stepX > 0:
            for ii in range(stepX + 1):
                _interp = (stepX - step) / stepX
                _intCol = Colour.interpolateColourRgba(colourList[min(jj, stepY)], colourList[min(jj + 1, stepY)],
                                                       _interp,
                                                       alpha=1.0)
                colours.extend(_intCol)
                step -= stepY
                while step < 0:
                    step += stepX
                    jj += 1
        else:
            colours = colourList[0]

        return colours

    #def getPlaneData(self, guiStrip):
    def _getPlaneData(self):

        # NBNB TODO FIXME - Wayne, please check through the modified code

        spectrum = self.spectrum
        dimensionCount = spectrum.dimensionCount
        dimIndices = self.dimensionOrdering
        xDim = dimIndices[0]
        yDim = dimIndices[1]
        orderedAxes = self._apiStripSpectrumView.strip.orderedAxes

        if dimensionCount == 2:
            planeData = spectrum.getPlaneData(xDim=xDim + 1, yDim=yDim + 1)
            position = [1, 1]
            yield position, planeData

        elif dimensionCount == 3:

            # start with the simple case
            axisData = self._getAxisInfo(orderedAxes, 2)
            if not axisData:
                return

            position = dimensionCount * [1]
            for z in range(axisData.startPoint, axisData.endPoint):
                position[dimIndices[2]] = (z % axisData.pointCount) + 1
                planeData = spectrum.getPlaneData(position, xDim=xDim + 1, yDim=yDim + 1)
                yield position, planeData

        elif dimensionCount >= 4:

            # get the axis information
            axes = [self._getAxisInfo(orderedAxes, dim) for dim in range(2, dimensionCount)]
            if None in axes:
                return

            # create a tuple of the ranges for the planes
            _loopArgs = tuple(range(axis.startPoint, axis.endPoint) for axis in axes)

            position = dimensionCount * [1]
            _offset = dimensionCount - len(_loopArgs)  # should always be 2?

            # iterate over all the axes
            for _plane in product(*_loopArgs):

                # get the axis position and put into the position vector
                for dim, pos in enumerate(_plane):
                    _axis = axes[dim]
                    position[dimIndices[dim + _offset]] = (pos % axes[dim].pointCount) + 1

                # get the plane data
                planeData = spectrum.getPlaneData(position, xDim=xDim + 1, yDim=yDim + 1)
                yield position, planeData

    def _getAxisInfo(self, orderedAxes, dim):
        """Get the information for the required axis
        """
        index = self.dimensionOrdering[dim]
        if index is None:
            return

        # get the axis region
        zPosition = orderedAxes[dim].position
        width = orderedAxes[dim].width
        axisCode = orderedAxes[dim].code

        # get the ppm range
        zPointCount = (self.spectrum.pointCounts)[index]
        zRegionValue = (zPosition + 0.5 * width, zPosition - 0.5 * width)  # Note + and - (axis backwards)

        # convert ppm- to point-range
        zPointFloat0 = self.spectrum.ppm2point(zRegionValue[0], axisCode=axisCode) - 1
        zPointFloat1 = self.spectrum.ppm2point(zRegionValue[1], axisCode=axisCode) - 1

        # convert to integers
        zPointInt0, zPointInt1 = (int(zPointFloat0 + (1 if zPointFloat0 >= 0 else 0)),  # this gives first and 1+last integer in range
                                  int(zPointFloat1 + (1 if zPointFloat1 >= 0 else 0)))  # and takes into account negative ppm2Point

        if zPointInt0 == zPointInt1:
            # only one plane visible, need to 2 points for range()
            if zPointFloat0 - (zPointInt0 - 1) < zPointInt1 - zPointFloat1:  # which is closest to an integer
                zPointInt0 -= 1
            else:
                zPointInt1 += 1
        elif (zPointInt1 - zPointInt0) >= zPointCount:
            # range is more than range of planes, set to maximum
            zPointInt0 = 0
            zPointInt1 = zPointCount

        return AxisPlaneData(zPointInt0, zPointInt1, zPointCount)

    def _getVisiblePlaneList(self, firstVisible=None, minimumValuePerPoint=None):

        spectrum = self.spectrum
        dimensionCount = spectrum.dimensionCount
        dimIndices = self.dimensionOrdering
        orderedAxes = self._apiStripSpectrumView.strip.orderedAxes

        if dimensionCount <= 2:
            return None, None, []

        planeList = ()
        planePointValues = ()

        for dim in range(2, dimensionCount):

            index = self.dimensionOrdering[dim]
            if index is None:
                return

            # make sure there is always a spectrumView to base visibility on
            # useFirstVisible = firstVisible if firstVisible else self
            zPosition = orderedAxes[dim].position
            axisCode = orderedAxes[dim].code

            # get the plane count from the widgets
            planeCount = self.strip.planeAxisBars[dim - 2].planeCount  #   .planeToolbar.planeCounts[dim - 2].value()

            zPointCount = (self.spectrum.pointCounts)[index]
            zValuePerPoint = (self.spectrum.valuesPerPoint)[index]
            # minSpectrumFrequency, maxSpectrumFrequency = (self.spectrum.spectrumLimits)[index]

            # pass in a smaller valuePerPoint - if there are differences in the z-resolution, otherwise just use local valuePerPoint
            minZWidth = 3 * zValuePerPoint
            zWidth = (planeCount + 2) * minimumValuePerPoint[dim - 2] if minimumValuePerPoint else (planeCount + 2) * zValuePerPoint
            zWidth = max(zWidth, minZWidth)

            zRegionValue = (zPosition + 0.5 * zWidth, zPosition - 0.5 * zWidth)  # Note + and - (axis backwards)

            # ppm position to point range
            zPointFloat0 = self.spectrum.ppm2point(zRegionValue[0], axisCode=axisCode) - 1
            zPointFloat1 = self.spectrum.ppm2point(zRegionValue[1], axisCode=axisCode) - 1

            # convert to integers
            zPointInt0, zPointInt1 = (int(zPointFloat0 + (1 if zPointFloat0 >= 0 else 0)),  # this gives first and 1+last integer in range
                                      int(zPointFloat1 + (1 if zPointFloat1 >= 0 else 0)))  # and takes into account negative ppm2Point

            if zPointInt0 == zPointInt1:
                # only one plane visible, need to 2 points for range()
                if zPointFloat0 - (zPointInt0 - 1) < zPointInt1 - zPointFloat1:  # which is closest to an integer
                    zPointInt0 -= 1
                else:
                    zPointInt1 += 1

            planeList = planeList + ((tuple((zz % zPointCount) for zz in range(zPointInt0, zPointInt1)),
                                      0, zPointCount),)

            # need to add 0.5 for the indexing in the api
            planePointValues = ()

            # not sure tha the ppm's are needed here
            # planePointValues = planePointValues + ((tuple(self.spectrum.ppm2point(zz + 0.5, axisCode=axisCode)
            #                                               for zz in range(zPointInt0, zPointInt1 + 1)), zPointOffset, zPointCount),)

        return planeList, planePointValues, dimIndices

    def getVisibleState(self, dimensionCount=None):
        """Get the visible state for the X/Y axes
        """
        if not dimensionCount:
            dimensionCount = self.spectrum.dimensionCount

        return tuple(self._getSpectrumViewParams(vParam) for vParam in range(0, dimensionCount))

    def refreshData(self):
        # spawn a rebuild in the openGL strip
        self.buildContours = True

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()
