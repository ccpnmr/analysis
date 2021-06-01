"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-06-01 12:39:28 +0100 (Tue, June 01, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-06-01 09:23:39 +0100 (Tue, June 1, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from typing import Sequence, List
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks
from ccpn.core.PeakList import PARABOLICMETHOD, GAUSSIANMETHOD


from ccpn.util.Common import percentage
from scipy.ndimage import maximum_filter, minimum_filter
from ccpn.util import Common as commonUtil
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList
from ccpn.core.lib.SpectrumLib import estimateNoiseLevel1D, _filtered1DArray
# from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util.Logging import getLogger
from ccpn.core._implementation.PMIListABC import PMIListABC


def _pickPeaksRegion(peakList, regionToPick: dict = {},
                     doPos: bool = True, doNeg: bool = True,
                     minLinewidth=None, exclusionBuffer=None,
                     minDropFactor: float = 0.1, checkAllAdjacent: bool = True,
                     fitMethod: str = PARABOLICMETHOD, excludedRegions=None,
                     excludedDiagonalDims=None, excludedDiagonalTransform=None,
                     estimateLineWidths=True):
    """
    DEPRECATED - please use spectrum.pickPeaks()
    
    Pick peaks in the region defined by the regionToPick dict.

    Axis limits are passed in as a dict containing the axis codes and the required limits.
    Each limit is defined as a key, value pair: (str, tuple),
    with the tuple supplied as (min,max) axis limits in ppm.

    For axisCodes that are not included, the limits will by taken from the aliasingLimits of the spectrum.

    Illegal axisCodes will raise an error.

    Example dict:

    ::

        {'Hn': (7.0, 9.0),
         'Nh': (110, 130)
         }

    doPos, doNeg - pick positive/negative peaks or both.

    exclusionBuffer defines the size to extend the region by in index units, e.g. [1, 1, 1]
                extends the region by 1 index point in all axes.
                Default is 1 in all axis directions.

    minDropFactor - minimum drop factor, value between 0.0 and 1.0
                Ratio of max value to adjacent values in dataArray. Default is 0.1
                i.e., difference between all adjacent values and local maximum must be greater than 10%
                for maximum to be considered as a peak.

    fitMethod - curve fitting method to find local maximum at peak location in dataArray.
                Current methods are ('gaussian', 'lorentzian').
                Default is gaussian.

    :param regionToPick: dict of axis limits
    :param doPos: pick positive peaks
    :param doNeg: pick negative peaks
    :param minLinewidth:
    :param exclusionBuffer: array of int
    :param minDropFactor: float defined on [0.0, 1.0] default is 0.1
    :param checkAllAdjacent: True/False, default True
    :param fitMethod: str in 'gaussian', 'lorentzian'
    :param excludedRegions:
    :param excludedDiagonalDims:
    :param excludedDiagonalTransform:
    :return: list of peaks.
    """

    print('>>>   _pickPeaksRegion')

    from ccpnc.peak import Peak as CPeak

    spectrum = peakList.spectrum
    dataSource = spectrum._apiDataSource
    numDim = dataSource.numDim

    # assert fitMethod in PICKINGMETHODS, 'pickPeaksRegion: fitMethod = %s, must be one of ("gaussian", "lorentzian", "parabolic")' % fitMethod
    # assert (minDropFactor >= 0.0) and (minDropFactor <= 1.0), 'pickPeaksRegion: minDropFactor %f not in range [0.0, 1.0]' % minDropFactor
    # method = PICKINGMETHODS.index(fitMethod)

    peaks = []

    if not minLinewidth:
        minLinewidth = [0.0] * numDim

    if not exclusionBuffer:
        exclusionBuffer = [1] * numDim
    else:
        if len(exclusionBuffer) != numDim:
            raise ValueError('Error: pickPeaksRegion, exclusion buffer length must match dimension of spectrum')
        for nDim in range(numDim):
            if exclusionBuffer[nDim] < 1:
                raise ValueError('Error: pickPeaksRegion, exclusion buffer must contain values >= 1')

    nonAdj = 1 if checkAllAdjacent else 0

    if not excludedRegions:
        excludedRegions = []

    if not excludedDiagonalDims:
        excludedDiagonalDims = []

    if not excludedDiagonalTransform:
        excludedDiagonalTransform = []

    posLevel = spectrum.positiveContourBase if doPos else None
    negLevel = spectrum.negativeContourBase if doNeg else None
    if posLevel is None and negLevel is None:
        return peaks

    # find the regions from the spectrum - sometimes returning None which gives an error
    foundRegions = peakList.spectrum.getRegionData(exclusionBuffer, **regionToPick)

    if not foundRegions:
        return peaks

    for region in foundRegions:
        if not region:
            continue

        dataArray, intRegion, \
        startPoints, endPoints, \
        startPointBufferActual, endPointBufferActual, \
        startPointIntActual, numPointInt, \
        startPointBuffer, endPointBuffer = region

        if dataArray.size:

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

            # exclusion code copied from Nmr/PeakList.py
            excludedRegionsList = [np.array(excludedRegion, dtype=np.float32) - startPointBuffer for excludedRegion in excludedRegions]
            excludedDiagonalDimsList = []
            excludedDiagonalTransformList = []
            for n in range(len(excludedDiagonalDims)):
                dim1, dim2 = excludedDiagonalDims[n]
                a1, a2, b12, d = excludedDiagonalTransform[n]
                b12 += a1 * startPointBuffer[dim1] - a2 * startPointBuffer[dim2]
                excludedDiagonalDimsList.append(np.array((dim1, dim2), dtype=np.int32))
                excludedDiagonalTransformList.append(np.array((a1, a2, b12, d), dtype=np.float32))

            doPos = posLevel is not None
            doNeg = negLevel is not None
            posLevel = posLevel or 0.0
            negLevel = negLevel or 0.0

            # print('>>dataArray', dataArray)
            # NOTE:ED requires an exclusionBuffer of 1 in all axis directions
            peakPoints = CPeak.findPeaks(dataArray, doNeg, doPos,
                                         negLevel, posLevel, exclusionBuffer,
                                         nonAdj, minDropFactor, minLinewidth,
                                         excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)

            peakPoints = [(np.array(position), height) for position, height in peakPoints]

            # only keep those points which are inside original region, not extended region
            peakPoints = [(position, height) for position, height in peakPoints if
                          ((startPoints - startPointIntActual) <= position).all() and (position < (endPoints - startPointIntActual)).all()]

            # check new found positions against existing ones
            existingPositions = []
            for apiPeak in peakList._wrappedData.peaks:
                position = np.array([peakDim.position for peakDim in apiPeak.sortedPeakDims()])  # ignores aliasing
                existingPositions.append(position - 1)  # -1 because API position starts at 1

            # NB we can not overwrite exclusionBuffer, because it may be used as a parameter in redoing
            # and 'if not exclusionBuffer' does not work on np arrays.
            npExclusionBuffer = np.array(exclusionBuffer)

            validPeakPoints = []
            for thisPeak in peakPoints:

                position, height = thisPeak

                position += startPointBufferActual

                for existingPosition in existingPositions:
                    delta = abs(existingPosition - position)

                    # TODO:ED changed to '<='
                    if (delta <= npExclusionBuffer).all():
                        break
                else:
                    validPeakPoints.append(thisPeak)

            allPeaksArray = None
            allRegionArrays = []
            regionArray = None

            # can I divide the peaks into subregions to make the solver more stable?

            for position, height in validPeakPoints:

                position -= startPointBufferActual
                numDim = len(position)

                # get the region containing this point
                firstArray = np.maximum(position - 2, 0)
                lastArray = np.minimum(position + 3, numPointInt)
                localRegionArray = np.array((firstArray, lastArray))
                localRegionArray = localRegionArray.astype(np.int32)

                # get the larger regionArray size containing all points so far
                firstArray = np.maximum(position - 3, 0)
                lastArray = np.minimum(position + 4, numPointInt)
                if regionArray is not None:
                    firstArray = np.minimum(firstArray, regionArray[0])
                    lastArray = np.maximum(lastArray, regionArray[1])

                peakArray = position.reshape((1, numDim))
                peakArray = peakArray.astype(np.float32)
                firstArray = firstArray.astype(np.int32)
                lastArray = lastArray.astype(np.int32)
                regionArray = np.array((firstArray, lastArray))

                if allPeaksArray is None:
                    allPeaksArray = peakArray
                else:
                    allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)
                allRegionArrays.append(localRegionArray)

            if allPeaksArray is not None:

                # parabolic - generate all peaks in one operation
                result = CPeak.fitParabolicPeaks(dataArray, regionArray, allPeaksArray)

                for height, centerGuess, linewidth in result:
                    center = np.array(centerGuess)

                    position = center + startPointBufferActual
                    peak = peakList.newPickedPeak(pointPositions=position, height=height,
                                              lineWidths=linewidth if estimateLineWidths else None,
                                              fitMethod=fitMethod)
                    peaks.append(peak)

                if fitMethod != PARABOLICMETHOD:
                    peakList.fitExistingPeaks(peaks, fitMethod=fitMethod, singularMode=True)

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
                #     peak = peakList._newPickedPeak(pointPositions=position, height=height,
                #                                lineWidths=linewidth, fitMethod=fitMethod)
                #     peaks.append(peak)
                #
        # plt.show()

    return peaks


def _pickPeaksNd(peakList, regionToPick: Sequence[float] = None,
                doPos: bool = True, doNeg: bool = True,
                fitMethod: str = GAUSSIANMETHOD, excludedRegions=None,
                excludedDiagonalDims=None, excludedDiagonalTransform=None,
                minDropFactor: float = 0.1):

    # TODO NBNB Add doc string and put type annotation on all parameters

    startPoint = []
    endPoint = []
    spectrum = peakList.spectrum
    dataDims = spectrum._apiDataSource.sortedDataDims()
    aliasingLimits = spectrum.aliasingLimits
    apiPeaks = []
    # for ii, dataDim in enumerate(dataDims):
    spectrumReferences = spectrum.spectrumReferences
    if None in spectrumReferences:
        # TODO if we want to pick in Sampeld fo FId dimensions, this must be added
        raise ValueError("pickPeaksNd() only works for Frequency dimensions"
                         " with defined primary SpectrumReferences ")
    if regionToPick is None:
        regionToPick = peakList.spectrum.aliasingLimits
    for ii, spectrumReference in enumerate(spectrumReferences):
        aliasingLimit0, aliasingLimit1 = aliasingLimits[ii]
        value0 = regionToPick[ii][0]
        value1 = regionToPick[ii][1]
        value0, value1 = min(value0, value1), max(value0, value1)
        if value1 < aliasingLimit0 or value0 > aliasingLimit1:
            break  # completely outside aliasing region
        value0 = max(value0, aliasingLimit0)
        value1 = min(value1, aliasingLimit1)
        # -1 below because points start at 1 in data model
        # position0 = dataDim.primaryDataDimRef.valueToPoint(value0) - 1
        # position1 = dataDim.primaryDataDimRef.valueToPoint(value1) - 1
        position0 = spectrumReference.valueToPoint(value0) - 1
        position1 = spectrumReference.valueToPoint(value1) - 1
        position0, position1 = min(position0, position1), max(position0, position1)
        # want integer grid points above position0 and below position1
        # add 1 to position0 because above
        # add 1 to position1 because doing start <= x < end not <= end
        # yes, this negates -1 above but they are for different reasons
        position0 = int(position0 + 1)
        position1 = int(position1 + 1)
        # startPoint.append((dataDim.dim, position0))
        # endPoint.append((dataDim.dim, position1))
        startPoint.append((spectrumReference.dimension, position0))
        endPoint.append((spectrumReference.dimension, position1))
    else:
        startPoints = [point[1] for point in sorted(startPoint)]
        endPoints = [point[1] for point in sorted(endPoint)]
        # print(isoOrdering, startPoint, startPoints, endPoint, endPoints)

        posLevel = spectrum.positiveContourBase if doPos else None
        negLevel = spectrum.negativeContourBase if doNeg else None

        # with logCommandBlock(get='peakList') as log:
        #     log('pickPeaksNd')
        #     with notificationBlanking():

        apiPeaks = pickNewPeaks(peakList._apiPeakList, startPoint=startPoints, endPoint=endPoints,
                                posLevel=posLevel, negLevel=negLevel, fitMethod=fitMethod,
                                excludedRegions=excludedRegions, excludedDiagonalDims=excludedDiagonalDims,
                                excludedDiagonalTransform=excludedDiagonalTransform, minDropfactor=minDropFactor)

    data2ObjDict = peakList._project._data2Obj
    result = [data2ObjDict[apiPeak] for apiPeak in apiPeaks]
    # for peak in result:
    #     peak._finaliseAction('create')

    return result


def _pickPeaks1d(peakList, dataRange, intensityRange, peakFactor1D=1) -> List['Peak']:
    """
    Pick 1D peaks from a dataRange
    """
    from ccpn.core.lib.peakUtils import simple1DPeakPicker, _1DregionsFromLimits

    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            spectrum = peakList.spectrum
            x, y = spectrum.positions, peakList.spectrum.intensities
            maxIrange, minIrange = max(intensityRange), min(intensityRange)
            xR, yR = _1DregionsFromLimits(spectrum.positions, peakList.spectrum.intensities, dataRange)
            noiseLevel = spectrum.noiseLevel
            negativeNoiseLevel = spectrum.negativeNoiseLevel

            if negativeNoiseLevel is None and spectrum.noiseLevel is not None:
                negativeNoiseLevel = -spectrum.noiseLevel

            if not noiseLevel and not negativeNoiseLevel:
                noiseLevel, negativeNoiseLevel = estimateNoiseLevel1D(y)
                spectrum.noiseLevel = noiseLevel
                spectrum.negativeNoiseLevel = negativeNoiseLevel
            currentPositions = [p.position[0] for p in peakList.peaks]  # don't add peaks if already there
            pdd = percentage(peakFactor1D, noiseLevel)
            ndd = percentage(peakFactor1D, negativeNoiseLevel)
            maxValues, minValues = simple1DPeakPicker(yR, xR, noiseLevel + pdd, negDelta=negativeNoiseLevel + ndd, negative=True)
            for position, height in maxValues + minValues:
                if minIrange < height < maxIrange:
                    if position not in currentPositions:
                        peak = peakList.newPeak(ppmPositions=[position], height=height)

def _pickPeaks1d_(peakList, dataRange, intensityRange=None, size: int = 3, mode: str = 'wrap') -> List['Peak']:
    """
    Pick 1D peaks from a dataRange
    """
    from ccpn.ui.gui.widgets.MessageDialog import _stoppableProgressBar
    from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning

    # maxValues, minValues = simple1DPeakPicker(y=filteredY, x=filteredX, delta=maxNoiseLevel + deltaAdjustment,
    #                                           negative=False)
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():

            if dataRange[0] < dataRange[1]:
                dataRange[0], dataRange[1] = dataRange[1], dataRange[0]
            # code below assumes that dataRange[1] > dataRange[0]
            peaks = []
            spectrum = peakList.spectrum
            # data1d = spectrum._apiDataSource.get1dSpectrumData()
            data1d = np.array([peakList.spectrum.positions, peakList.spectrum.intensities])
            selectedData = data1d[:, (data1d[0] < dataRange[0]) * (data1d[0] > dataRange[1])]

            if selectedData.size == 0:
                return peaks
            x, y = selectedData

            maxFilter = maximum_filter(selectedData[1], size=size, mode=mode)
            boolsMax = selectedData[1] == maxFilter
            indices = np.argwhere(boolsMax)

            minFilter = minimum_filter(selectedData[1], size=size, mode=mode)
            boolsMin = selectedData[1] == minFilter
            negBoolsPeak = boolsMin
            indicesMin = np.argwhere(negBoolsPeak)

            fullIndices = np.append(indices, indicesMin)  # True positional indices
            values = []
            for position in fullIndices:
                peakPosition = [float(selectedData[0][position])]
                height = selectedData[1][position]
                if intensityRange is None or intensityRange[0] <= height <= intensityRange[1]:
                    values.append((float(height), peakPosition), )
            found = len(values)
            if found > 10:
                title = 'Found %s peaks on %s' % (found, peakList.spectrum.name)
                msg = 'Do you want continue? \n\n\n\nTo filter out more peaks: Increase the peak factor from preferences:' \
                      '\nProject > Preferences... > Spectrum > 1D Peak Picking Factor.\nAlso, try to select above the noise region'

                proceed = showYesNoWarning(title, msg)
                if not proceed:
                    return []
            for height, position in _stoppableProgressBar(values):
                peaks.append(peakList.newPeak(height=float(height), ppmPositions=position))

        return peaks


def _pickPeaks1dFiltered(peakList, size: int = 9, mode: str = 'wrap', factor=10, excludeRegions=None,
                        positiveNoiseThreshold=None, negativeNoiseThreshold=None, negativePeaks=True, stdFactor=0.5):
    """
    Pick 1D peaks from data in peakList.spectrum.
    """
    with undoBlockWithoutSideBar():
        if excludeRegions is None:
            excludeRegions = [[-20.1, -19.1]]
        excludeRegions = [sorted(pair, reverse=True) for pair in excludeRegions]
        peaks = []
        spectrum = peakList.spectrum
        # data = spectrum._apiDataSource.get1dSpectrumData()
        data = np.array([spectrum.positions, spectrum.intensities])
        ppmValues = data[0]
        estimateNoiseLevel1D(spectrum.intensities, f=factor, stdFactor=0.5)

        if positiveNoiseThreshold == 0.0 or positiveNoiseThreshold is None:
            positiveNoiseThreshold, negativeNoiseThreshold = estimateNoiseLevel1D(spectrum.intensities,
                                                                                  f=factor, stdFactor=stdFactor)
        spectrum.noiseLevel = positiveNoiseThreshold
        spectrum.negativeNoiseLevel = negativeNoiseThreshold
        #     positiveNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
        #     if spectrum.noiseLevel is None:
        #         positiveNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
        #         negativeNoiseThreshold = -positiveNoiseThreshold
        #
        # if negativeNoiseThreshold == 0.0 or negativeNoiseThreshold is None:
        #     negativeNoiseThreshold = _oldEstimateNoiseLevel1D(spectrum.intensities, factor=factor)
        #     if spectrum.noiseLevel is None:
        #         negativeNoiseThreshold = -positiveNoiseThreshold

        masks = []
        for region in excludeRegions:
            mask = (ppmValues > region[0]) | (ppmValues < region[1])
            masks.append(mask)
        fullmask = [all(mask) for mask in zip(*masks)]
        newArray2 = (np.ma.MaskedArray(data, mask=np.logical_not((fullmask, fullmask))))

        if (newArray2.size == 0) or (data.max() < positiveNoiseThreshold):
            return peaks

        posBoolsVal = newArray2[1] > positiveNoiseThreshold
        maxFilter = maximum_filter(newArray2[1], size=size, mode=mode)
        boolsMax = newArray2[1] == maxFilter
        boolsPeak = posBoolsVal & boolsMax
        indices = np.argwhere(boolsPeak)

        if negativePeaks:
            minFilter = minimum_filter(data[1], size=size, mode=mode)
            boolsMin = newArray2[1] == minFilter
            negBoolsVal = newArray2[1] < negativeNoiseThreshold
            negBoolsPeak = negBoolsVal & boolsMin
            indicesMin = np.argwhere(negBoolsPeak)
            indices = np.append(indices, indicesMin)

        for position in indices:
            peakPosition = [float(newArray2[0][position])]
            height = newArray2[1][position]
            peak = peakList.newPeak(height=float(height), ppmPositions=peakPosition)
            snr = peak.signalToNoiseRatio
            peaks.append(peak)
    return peaks


def _peakFinder1D(peakList, maxNoiseLevel=None, minNoiseLevel=None,
                 ignoredRegions=[[20, 19]], negativePeaks=False,
                 eNoiseThresholdFactor=1.5,
                 recalculateSNR=True,
                 deltaPercent=10,
                 useXRange=1):

    from ccpn.core.lib.peakUtils import simple1DPeakPicker
    from ccpn.core.lib.SpectrumLib import _estimate1DSpectrumSNR

    peaks = []
    # with undoBlockWithoutSideBar():
    #     with notificationEchoBlocking():
    spectrum = peakList.spectrum

    x, y = spectrum.positions, spectrum.intensities
    masked = _filtered1DArray(np.array([x, y]), ignoredRegions)
    filteredX, filteredY = masked[0].compressed(), masked[1].compressed()
    deltaAdjustment = 0
    if maxNoiseLevel is None or minNoiseLevel is None:
        maxNoiseLevel, minNoiseLevel = estimateNoiseLevel1D(y, f=useXRange, stdFactor=eNoiseThresholdFactor)
        spectrum.noiseLevel = float(maxNoiseLevel)
        spectrum.negativeNoiseLevel = float(minNoiseLevel)
        deltaAdjustment = percentage(deltaPercent, maxNoiseLevel)
    maxValues, minValues = simple1DPeakPicker(y=filteredY, x=filteredX, delta=maxNoiseLevel + deltaAdjustment, negDelta=minNoiseLevel + deltaAdjustment, negative=negativePeaks)
    spectrum.noiseLevel = float(maxNoiseLevel)
    spectrum.negativeNoiseLevel = float(minNoiseLevel)

    for position, height in maxValues:
        peak = peakList.newPeak(ppmPositions=[position], height=height)
        peaks.append(peak)
    if negativePeaks:
        for position, height in minValues:
            peak = peakList.newPeak(ppmPositions=[position], height=height)
            peaks.append(peak)
    return peaks


def _fitExistingPeaks(peakList, peaks: Sequence['Peak'], fitMethod: str = GAUSSIANMETHOD, singularMode: bool = True,
                     halfBoxSearchWidth: int = 2, halfBoxFitWidth: int = 2):
    """Refit the current selected peaks.
    Must be called with peaks that belong to this peakList
    """
    # DEPRECATED

    from ccpn.core.lib.PeakPickers.PeakPickerNd import PeakPickerNd
    from ccpn.framework.Application import getApplication

    getApp = getApplication()

    if peaks:

        badPeaks = [peak for peak in peaks if peak.peakList is not peakList]
        if badPeaks:
            raise ValueError('List contains peaks that are not in the same peakList.')

        myPeakPicker = PeakPickerNd(spectrum=peakList.spectrum)
        myPeakPicker.setParameters(dropFactor=getApp.preferences.general.peakDropFactor,
                                   fitMethod=fitMethod,
                                   searchBoxMode=getApp.preferences.general.searchBoxMode,
                                   searchBoxDoFit=getApp.preferences.general.searchBoxDoFit,
                                   halfBoxSearchWidth=halfBoxSearchWidth,
                                   halfBoxFitWidth=halfBoxFitWidth,
                                   searchBoxWidths=getApp.preferences.general.searchBoxWidthsNd,
                                   singularMode=singularMode
                                   )

        myPeakPicker.fitExistingPeaks(peaks)
