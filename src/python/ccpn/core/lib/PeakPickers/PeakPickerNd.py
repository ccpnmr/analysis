"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-04-12 15:36:24 +0100 (Mon, April 12, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-02-08 11:42:15 +0000 (Mon, February 08, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
import numpy as np
from typing import Sequence
from collections import Counter
from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC, SimplePeak
from ccpnc.peak import Peak as CPeak
from ccpn.util.Logging import getLogger


GAUSSIANMETHOD = 'gaussian'
LORENTZIANMETHOD = 'lorentzian'
PARABOLICMETHOD = 'parabolic'
PICKINGMETHODS = (GAUSSIANMETHOD, LORENTZIANMETHOD, PARABOLICMETHOD)


class PeakPickerNd(PeakPickerABC):
    """A simple Nd peak picker for testing
    """

    peakPickerType = "PeakPickerNd"
    onlyFor1D = False

    def __init__(self, spectrum):
        super().__init__(spectrum=spectrum)
        self.noise = None
        self.positiveThreshold = spectrum.positiveContourBase if spectrum.includePositiveContours else None
        self.negativeThreshold = spectrum.negativeContourBase if spectrum.includeNegativeContours else None

        # set some defaults
        self.dropFactor = 0.1
        self.minimumLineWidth = None
        self.checkAllAdjacent = True
        self.fitMethod = PARABOLICMETHOD
        self.singularMode = True
        self.halfBoxFindPeaksWidth = 2
        self.halfBoxSearchWidth = 3
        self.halfBoxFitWidth = 3
        self.sarchBoxDoFit = True

        self._hbsWidth = None
        self._hbfWidth = None
        self.findFunc = None

    def findPeaks(self, data) -> list:
        """find the peaks in data (type numpy-array) and return as a list of SimplePeak instances
        note that SimplePeak.points are ordered z,y,x for nD, in accordance with the numpy nD data array

        called from the pickPeaks() method

        any required parameters that findPeaks method needs should be initialised/set before using the
        setParameters() method; i.e.:
                myPeakPicker = PeakPicker(spectrum=mySpectrum)
                myPeakPicker.setParameters(dropFactor=0.2, positiveThreshold=1e6, negativeThreshold=None)
                corePeaks = myPeakPicker.pickPeaks(axisDict={'H':(6.0,11.5),'N':(102.3,130.0)}, spectrum.peaklists[-1])

        :param data: nD numpy array
        :return list of SimplePeak instances
        """

        print(f'>>>  {self.peakPickerType}   findPeaks')

        # find the list of peaks in the region
        allPeaksArray, allRegionArrays, regionArray, _ = self._findPeaks(data, self.positiveThreshold, self.negativeThreshold)

        # if peaks exist then create a list of simple peaks
        if allPeaksArray is not None and allPeaksArray.size != 0:

            fitMethod = self.fitMethod
            singularMode = self.singularMode

            try:
                result = ()
                if fitMethod == PARABOLICMETHOD:  # and singularMode is True:

                    # parabolic - generate all peaks in one operation
                    result = CPeak.fitParabolicPeaks(data, regionArray, allPeaksArray)

                else:
                    method = 0 if fitMethod == GAUSSIANMETHOD else 1

                    # currently gaussian or lorentzian
                    if singularMode is True:

                        # fit peaks individually in small regions
                        for peakArray, localRegionArray in zip(allPeaksArray, allRegionArrays):
                            peakArray = peakArray.reshape((1, self.dimensionCount))
                            peakArray = peakArray.astype(np.float32)
                            localResult = CPeak.fitPeaks(data, localRegionArray, peakArray, method)

                            result += tuple(localResult)
                    else:

                        # fit all peaks in one operation
                        result = CPeak.fitPeaks(data, regionArray, allPeaksArray, method)

                func = self.findFunc
                return func(result)
                # return [SimplePeak(points=point[::-1], height=height, lineWidths=pointLineWidths)
                #         for height, point, pointLineWidths in result]

            except CPeak.error as es:
                getLogger().warning(f'Aborting peak fit: {es}')
                return []

        return []

    def _findPeaks(self, data, posThreshold, negThreshold):
        """find the peaks in data (type numpy-array) and return as a list of SimplePeak instances
        """
        # NOTE:ED - need to validate the parameters first

        if self.noise is None:
            getLogger().debug('spectrum.estimateNoise on findPeaks')
            self.noise = self.spectrum.estimateNoise()

        # set threshold values
        doPos = posThreshold is not None
        doNeg = negThreshold is not None
        posLevel = posThreshold or 0.0
        negLevel = negThreshold or 0.0

        # accounted for by pickPeaks in superclass
        exclusionBuffer = [0] * self.dimensionCount
        excludedRegionsList = []
        excludedDiagonalDimsList = []
        excludedDiagonalTransformList = []
        nonAdj = 1 if self.checkAllAdjacent else 0
        minLinewidth = [0.0] * self.dimensionCount if not self.minimumLineWidth else self.minimumLineWidth
        pointPeaks = CPeak.findPeaks(data, doNeg, doPos,
                                     negLevel, posLevel, exclusionBuffer,
                                     nonAdj,
                                     self.dropFactor,
                                     minLinewidth,
                                     excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)
        # the above can be replaced with the peak list for

        # get the peak maxima from pointPeaks
        pointPeaks = [(np.array(position), height) for position, height in pointPeaks]

        # ignore exclusion buffer for the minute
        validPointPeaks = [pk for pk in pointPeaks]

        allPeaksArray = None
        allRegionArrays = []
        regionArray = None

        # get the offset of the bottom left of the slice region
        startPoint = np.array([pp[0] for pp in self.sliceTuples])
        endPoint = np.array([pp[1] for pp in self.sliceTuples])
        numPointInt = (endPoint - startPoint) + 1

        for position, height in validPointPeaks:

            # get the region containing this point
            bLeft = np.maximum(position - self._hbsWidth, 0)
            tRight = np.minimum(position + self._hbsWidth + 1, numPointInt)
            localRegionArray = np.array((bLeft, tRight), dtype=np.int32)

            # get the larger regionArray size containing all points so far
            # the actual picked region may be huge, only need the bounds containing the maxima
            bLeftAll = np.maximum(position - self._hbsWidth - 1, 0)
            tRightAll = np.minimum(position + self._hbsWidth + 1, numPointInt)
            if regionArray is not None:
                bLeftAll = np.array(np.minimum(bLeftAll, regionArray[0]), dtype=np.int32)
                tRightAll = np.array(np.maximum(tRightAll, regionArray[1]), dtype=np.int32)

            # numpy arrays need tweaking to pass to the c code
            peakArray = position.reshape((1, self.dimensionCount))
            peakArray = peakArray.astype(np.float32)
            regionArray = np.array((bLeftAll, tRightAll), dtype=np.int32)

            if allPeaksArray is None:
                allPeaksArray = peakArray
            else:
                allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)
            allRegionArrays.append(localRegionArray)

        return allPeaksArray, allRegionArrays, regionArray, validPointPeaks

    def pickPeaks(self, axisDict, peakList) -> list:
        """Set the default functionality for picking simplePeaks from the region defined by axisDict
        """
        # NOTE:ED - verify parameters
        print(f'>>>  {self.peakPickerType}   pickPeaks')

        # set the correct parameters for the standard findPeaks
        self._hbsWidth = self.halfBoxFindPeaksWidth
        self.findFunc = self._returnSimplePeaks

        return super().pickPeaks(axisDict, peakList)

    def _returnSimplePeaks(self, foundPeaks):
        """Return a list of simple peaks from the height/point/lineWidth list
        """
        return [SimplePeak(points=point[::-1], height=height, lineWidths=pointLineWidths)
                for height, point, pointLineWidths in foundPeaks]

    def snapToExtremum(self, peak) -> list:
        """
        :param axisDict: Axis limits  are passed in as a dict of (axisCode, tupleLimit) key, value
                         pairs with the tupleLimit supplied as (start,stop) axis limits in ppm
                         (lower ppm value first).
        :param peakList: peakList instance to add newly pickedPeaks
        :return: list of core.Peak instances
        """
        print(f'>>>  {self.peakPickerType}   snapToExtremum')

        if self.spectrum is None:
            raise RuntimeError('%s.spectrum is None' % self.__class__.__name__)

        if not self.spectrum.hasValidPath():
            raise RuntimeError('%s.pickPeaks: spectrum %s, No valid spectral datasource defined' %
                               (self.__class__.__name__, self.spectrum))

        # set up the search box widths
        self._hbsWidth = self.halfBoxSearchWidth
        self._hbfWidth = self.halfBoxFitWidth

        pointPositions = peak.pointPositions
        spectrum = peak.spectrum
        valuesPerPoint = spectrum.valuesPerPoint
        axisCodes = spectrum.axisCodes

        # searchBox for Nd
        if self.searchBoxMode:

            boxWidths = []
            axisCodes = self.spectrum.axisCodes
            valuesPerPoint = self.spectrum.valuesPerPoint
            for axisCode, valuePerPoint in zip(axisCodes, valuesPerPoint):
                letterAxisCode = (axisCode[0] if axisCode != 'intensity' else axisCode) if axisCode else None
                if letterAxisCode in self.searchBoxWidths:
                    newWidth = math.floor(self.searchBoxWidths[letterAxisCode] / (2.0 * valuePerPoint))
                    boxWidths.append(max(1, newWidth))
                else:
                    # default to the given parameter value
                    boxWidths.append(max(1, self._hbsWidth or 1))
        else:
            boxWidths = []
            pointCounts = spectrum.pointCounts
            peakBoxWidths = peak.boxWidths
            for axisCode, pointCount, peakBWidth, valuePPoint in zip(axisCodes, pointCounts, peakBoxWidths, valuesPerPoint):
                _halfBoxWidth = pointCount / 100  # copied from V2
                boxWidths.append(max(_halfBoxWidth, 1, int((peakBWidth or 1) / 2)))

        # add the new boxWidths array as np.int32 type
        boxWidths = np.array(boxWidths, dtype=np.int32)
        pLower = np.floor(pointPositions).astype(np.int32)
        # find the co-ordinates of the lower corner of the data region
        startPoint = np.maximum(pLower - boxWidths, 0)

        self.sliceTuples = [(int(pos - bWidth), int(pos + bWidth + 1)) for pos, bWidth in zip(pointPositions, boxWidths)]
        data = self.spectrum.dataSource.getRegionData(self.sliceTuples, aliasingFlags=[1] * self.spectrum.dimensionCount)

        # getLogger().debug('%s.snapToExtremum: found %d peaks in spectrum %s; %r' %
        #                   (self.__class__.__name__, len(peaks), self.spectrum, axisDict))

        # get the height of the current peak (to stop peak flipping)
        height = spectrum.getPointValue(peak.pointPositions)
        scaledHeight = 0.5 * height  # this is so that have sensible pos/negLevel
        if height > 0:
            posLevel = scaledHeight
            negLevel = None
        else:
            posLevel = None
            negLevel = scaledHeight

        # find the list of peaks in the region
        allPeaksArray, allRegionArrays, regionArray, validPoints = self._findPeaks(data, posLevel, negLevel)

        # if peaks exist then create a list of simple peaks
        if allPeaksArray is not None and allPeaksArray.size != 0:

            # find the closest peak in the found list
            bestHeight = peakPoint = None
            bestFit = 0.0
            validPoints = sorted(validPoints, key=lambda val: abs(val[1]))
            for ii, findNextPeak in enumerate(validPoints):

                # find the highest peak to start from
                peakHeight = findNextPeak[1]
                peakDist = np.linalg.norm((np.array(findNextPeak[0]) - boxWidths) / boxWidths)
                peakFit = abs(height) / (1e-6 + peakDist)

                if height == None or peakFit > bestFit:
                    bestFit = peakFit
                    bestHeight = abs(peakHeight)
                    peakPoint = findNextPeak[0]

            # use this as the centre for the peak fitting
            peakPoint = np.array(peakPoint)
            peakArray = peakPoint.reshape((1, spectrum.dimensionCount))
            peakArray = peakArray.astype(np.float32)

            try:
                if self.searchBoxDoFit:
                    if self.fitMethod == PARABOLICMETHOD:
                        # parabolic - generate all peaks in one operation
                        result = CPeak.fitParabolicPeaks(data, regionArray, peakArray)

                    else:
                        method = 0 if self.fitMethod == GAUSSIANMETHOD else 1

                        # use the halfBoxFitWidth to give a close fit
                        firstArray = np.maximum(peakArray[0] - self._hbfWidth, regionArray[0])
                        lastArray = np.minimum(peakArray[0] + self._hbfWidth + 1, regionArray[1])
                        regionArray = np.array((firstArray, lastArray), dtype=np.int32)

                        # fit the single peak
                        result = CPeak.fitPeaks(data, regionArray, peakArray, method)
                else:
                    # take the maxima
                    result = ((bestHeight, peakPoint, None),)

                # if any results are found then set the new peak position/height
                if result:
                    height, center, linewidth = result[0]

                    _shape = data.shape[::-1]
                    newPos = list(peak.pointPositions)
                    for ii in range(len(center)):
                        if 0.5 < center[ii] < (_shape[ii] - 0.5):
                            newPos[ii] = center[ii] + startPoint[ii]

                    peak.pointPositions = newPos
                    peak.pointLineWidths = linewidth

                    if self.searchBoxDoFit:
                        peak.height = height
                    else:
                        # get the interpolated height
                        peak.height = spectrum.getPointValue(peak.pointPositions)

            except CPeak.error as es:
                getLogger().warning(f'Aborting peak fit: {es}')
                return []

        return []

    def fitExistingPeaks(self, peaks: Sequence['Peak']):
        """Refit the current selected peaks.
        Must be called with peaks that belong to this peakList
        """

        print(f'>>>  {self.peakPickerType}   fitExistingPeaks')

        if not peaks:
            return

        # set the correct parameters for the standard findPeaks
        self._hbsWidth = self.halfBoxFindPeaksWidth

        allPeaksArray = None
        allRegionArrays = []
        regionArray = None

        numLists = Counter([pk.peakList for pk in peaks])
        if len(numLists) > 1:
            raise ValueError('List contains peaks from more than one peakList.')

        # pointPositions = peaks[0].pointPositions
        spectrum = peaks[0].spectrum
        pointCounts = spectrum.pointCounts
        numDim = spectrum.dimensionCount

        for peak in peaks:
            pointPositions = peak.pointPositions

            # round up/down the position
            pLower = np.floor(pointPositions).astype(np.int32)
            pUpper = np.ceil(pointPositions).astype(np.int32)
            position = np.round(np.array(pointPositions))

            # generate a np array with the number of points per dimension
            numPoints = np.array(pointCounts)

            # consider for each dimension on the interval [point-3,point+4>, account for min and max
            # of each dimension
            if self.fitMethod == PARABOLICMETHOD or self.singularMode is True:
                firstArray = np.maximum(pLower - self._hbsWidth, 0)
                lastArray = np.minimum(pUpper + self._hbsWidth, numPoints)
            else:
                # extra plane in each direction increases accuracy of group fitting
                firstArray = np.maximum(pLower - self._hbsWidth - 1, 0)
                lastArray = np.minimum(pUpper + self._hbsWidth + 1, numPoints)

            # Cast to int for subsequent call
            firstArray = firstArray.astype(np.int32)
            lastArray = lastArray.astype(np.int32)
            localRegionArray = np.array((firstArray, lastArray), dtype=np.int32)

            if regionArray is not None:
                firstArray = np.minimum(firstArray, regionArray[0])
                lastArray = np.maximum(lastArray, regionArray[1])

            # requires reshaping of the array for use with CPeak.fitParabolicPeaks
            peakArray = position.reshape((1, numDim))
            peakArray = peakArray.astype(np.float32)
            regionArray = np.array((firstArray, lastArray), dtype=np.int32)

            if allPeaksArray is None:
                allPeaksArray = peakArray
            else:
                allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)
            allRegionArrays.append(localRegionArray)

        if allPeaksArray is not None and allPeaksArray.size != 0:

            # map to (0, 0)
            regionArray = np.array((firstArray - firstArray, lastArray - firstArray))

            self.sliceTuples = [(fst, lst) for fst, lst in zip(firstArray, lastArray)]
            data = self.spectrum.dataSource.getRegionData(self.sliceTuples, aliasingFlags=[1] * self.spectrum.dimensionCount)

            # update positions relative to the corner of the data array
            firstArray = firstArray.astype(np.float32)
            updatePeaksArray = None
            for pk in allPeaksArray:
                if updatePeaksArray is None:
                    updatePeaksArray = pk - firstArray
                    updatePeaksArray = updatePeaksArray.reshape((1, numDim))
                    updatePeaksArray = updatePeaksArray.astype(np.float32)
                else:
                    pk = pk - firstArray
                    pk = pk.reshape((1, numDim))
                    pk = pk.astype(np.float32)
                    updatePeaksArray = np.append(updatePeaksArray, pk, axis=0)

            try:
                result = ()
                # NOTE:ED - groupMode must be gaussian
                if self.fitMethod == PARABOLICMETHOD and self.singularMode is True:

                    # parabolic - generate all peaks in one operation
                    result = CPeak.fitParabolicPeaks(data, regionArray, updatePeaksArray)

                else:
                    method = 0 if self.fitMethod == GAUSSIANMETHOD else 1

                    # currently gaussian or lorentzian
                    if self.singularMode is True:

                        # fit peaks individually
                        for peakArray, localRegionArray in zip(allPeaksArray, allRegionArrays):
                            peakArray = peakArray - firstArray
                            peakArray = peakArray.reshape((1, numDim))
                            peakArray = peakArray.astype(np.float32)
                            localRegionArray = np.array((localRegionArray[0] - firstArray, localRegionArray[1] - firstArray), dtype=np.int32)

                            localResult = CPeak.fitPeaks(data, localRegionArray, peakArray, method)
                            result += tuple(localResult)
                    else:

                        # fit all peaks in one operation
                        result = CPeak.fitPeaks(data, regionArray, updatePeaksArray, method)

            except CPeak.error as e:

                # there could be some fitting error
                getLogger().warning("Aborting peak fit, Error for peak: %s:\n\n%s " % (peak, e))
                return

            for pkNum, peak in enumerate(peaks):
                height, center, linewidth = result[pkNum]

                _shape = data.shape[::-1]
                newPos = list(peak.pointPositions)
                for ii in range(len(center)):
                    if 0.5 < center[ii] < (_shape[ii] - 0.5):
                        newPos[ii] = center[ii] + firstArray[ii]

                peak.pointPositions = newPos
                peak.pointLineWidths = linewidth
                peak.height = height

    # NOTE:ED - example for plotting in pycharm - keep for the minute
    # # 20191004:ED testing - plot the dataArray during debugging
    # import np as np
    # from mpl_toolkits import mplot3d
    # import matplotlib.pyplot as plt
    #
    # fig = plt.figure(figsize=(10, 8), dpi=100)
    # ax = fig.gca(projection='3d')
    #
    # shape = dataArray.shape
    # rr = (np.max(dataArray) - np.min(dataArray)) * 100
    #
    # from ccpn.ui.gui.lib.GuiSpectrumViewNd import _getLevels
    # posLevels = _getLevels(spectrum.positiveContourCount, spectrum.positiveContourBase,
    #                             spectrum.positiveContourFactor)
    # posLevels = np.array(posLevels)
    #
    # dims = []
    # for ii in shape:
    #     dims.append(np.linspace(0, ii-1, ii))
    #
    # for ii in range(shape[0]):
    #     try:
    #         ax.contour(dims[2], dims[1], dataArray[ii] / rr, posLevels / rr, offset=(shape[0]-ii-1), cmap=plt.cm.viridis)
    #     except Exception as es:
    #         pass                    # trap stupid plot error
    #
    # ax.legend()
    # ax.set_xlim3d(-0.1, shape[2]-0.9)
    # ax.set_ylim3d(-0.1, shape[1]-0.9)
    # ax.set_zlim3d(-0.1, shape[0]-0.9)
    # # plt.show() is at the bottom of function

    # find new peaks

    # self.fitExistingPeaks(peaks, fitMethod=fitMethod, singularMode=True)

    # # 20191004:ED testing - plotting scatterplot of data
    # else:
    #
    # # result = CPeak.fitPeaks(dataArray, regionArray, allPeaksArray, method)
    # result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)
    #
    # for height, centerGuess, linewidth in result:
    #
    #     # clip the point to the exclusion area, to stop rogue peaks
    #     # center = np.array(centerGuess).clip(min=position - npExclusionBuffer,
    #     #                                        max=position + npExclusionBuffer)
    #     center = np.array(centerGuess)
    #
    #     # outofPlaneMinTest = np.array([])
    #     # outofPlaneMaxTest = np.array([])
    #     # for ii in range(numDim):
    #     #     outofPlaneMinTest = np.append(outofPlaneMinTest, 0.0)
    #     #     outofPlaneMaxTest = np.append(outofPlaneMaxTest, dataArray.shape[numDim-ii-1]-1.0)
    #     #
    #     # # check whether the new peak is outside of the current plane
    #     # outofPlaneCenter = np.array(centerGuess).clip(min=position - np.array(outofPlaneMinTest),
    #     #                      max=position + np.array(outofPlaneMaxTest))
    #     #
    #     # print(">>>", center, outofPlaneCenter, not np.array_equal(center, outofPlaneCenter))
    #
    #     # ax.scatter(*center, c='r', marker='^')
    #     #
    #     # x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax.get_proj())
    #     #
    #     # ax.text(*center, str(center), fontsize=12)
    #
    #     # except Exception as es:
    #     #     print('>>>error:', str(es))
    #     #     dimCount = len(startPoints)
    #     #     height = float(dataArray[tuple(position[::-1])])
    #     #     # have to reverse position because dataArray backwards
    #     #     # have to float because API does not like np.float32
    #     #     center = position
    #     #     linewidth = dimCount * [None]
    #
    #     position = center + startPointBufferActual
    #
    #     peak = self._newPickedPeak(pointPositions=position, height=height,
    #                                lineWidths=linewidth, fitMethod=fitMethod)
    #     peaks.append(peak)
    #
    # plt.show()


PeakPickerNd.register()
