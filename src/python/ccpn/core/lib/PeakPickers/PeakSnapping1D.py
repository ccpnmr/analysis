"""
In this file there are several functions needed for snapping 1D peaks.

WARNING:
    1D peak snapping is a very complex problem.
    It is not simply finding the closest maximum for an existing peak.
    It is highly optimised for screening routines following industrial collaborations requests.
    There is a very high number of cases to be covered, therefore
    refactoring and/or "simplification" can have massive impact in the intended and designed behaviour.

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-03-31 13:26:28 +0100 (Fri, March 31, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Muredd $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from scipy.spatial.distance import cdist
from collections import defaultdict
from scipy.optimize import linear_sum_assignment
from scipy.optimize import curve_fit
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import  undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima


def snap1DPeaksToExtrema(peaks, maximumLimit=0.1, figOfMeritLimit=1, doNeg=True):
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            if len(peaks) > 0:
                peaks.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
                for peak in peaks:  # peaks can be from diff peakLists
                    if peak is not None:
                        position, height, error = _get1DClosestExtremum(peak, maximumLimit, doNeg=doNeg,  figOfMeritLimit=figOfMeritLimit)
                        peak.position = position
                        peak.height = height
                        peak.heightError = error

def snap1DPeaksByGroup(peaks, ppmLimit=0.05, unsnappedLimit=1, increaseLimitStep=0.1, groupPpmLimit=0.2,  figOfMeritLimit=1,
                       doNeg=False,):
    """
    Snap the peaks by group. Use the ppmLimit to define limits of groups.
    Use the ppmLimit to explore left/right new maxima.
    If a new extremum is not found, then increase progressively the ppmLimits until the unsnappedLimit

    :param peaks:
    :param ppmLimit:
    :param figOfMeritLimit:
    :param doNeg:
    :param unsnappedLimit:
    :param increaseLimitStep:
    :return:
    """
    _snap1DPeaksByGroup(peaks, ppmLimit=ppmLimit,  figOfMeritLimit=figOfMeritLimit,
                       doNeg=doNeg)

    for newLimit in np.arange(ppmLimit, unsnappedLimit+increaseLimitStep, increaseLimitStep):
        unsnappedPeaks = [p for p in peaks if p.heightError is not None and p.figureOfMerit >= figOfMeritLimit  ]
        if len(unsnappedPeaks) == 0:
            return
        _snap1DPeaksByGroup(unsnappedPeaks, ppmLimit=newLimit, figOfMeritLimit=figOfMeritLimit,
                       doNeg=doNeg)


def snap1DPeaksAndRereferenceSpectrum(peaks, maximumLimit=0.1, useAdjacientPeaksAsLimits=False,
                                      doNeg=False, figOfMeritLimit=1, spectrum=None, autoRereferenceSpectrum=False):
    """
    Snap all peaks to the closest maxima

    Steps:
    - reorder the peaks by heights to give higher peaks priority to the snap
    - 1st iteration: search for nearest maxima and calculate delta positions (don't set peak.position here yet)
    - use deltas to fit patterns of shifts and detect the most probable global shift
    - use the global shift to re-reference the spectrum
    - 2nd iteration: re-search for nearest maxima
    - set newly detected position to peak if found better fits
    - re-set the spectrum referencing to original (if not requested as argument)

    :param peaks: list of peaks to snap
    :param maximumLimit: float to use as + left-right limits from peak position where to search new maxima
    :param useAdjacientPeaksAsLimits: bool. use adj peak position as left-right limits. don't search maxima after adjacent peaks
    :param doNeg: snap also negative peaks
    :param figOfMeritLimit: float. don't snap peaks with FOM below limit threshold
    :param spectrum: the spectum obj. optional if all peaks belong to the same spectrum
    :return:
    """
    if not peaks:
        getLogger().warning('Cannot snap peaks. No peaks found')
        return []
    if not spectrum:
        spectrum = peaks[0].peakList.spectrum

    # - reorder the peaks by heights to give higher peaks priority to the snap
    peaks = list(peaks)
    peaks.sort(key=lambda x: x.height, reverse=True)  # reorder peaks by height
    oPositions, oHeights = [x.position for x in peaks], [x.height for x in peaks]
    nPositions, nHeights, nHErrors = [], [], []

    # - 1st iteration: search for nearest maxima and calculate deltas
    for peak in peaks:
        if peak is not None:
            position, height, hError = _get1DClosestExtremum(peak, maximumLimit=maximumLimit,
                                                     useAdjacientPeaksAsLimits=useAdjacientPeaksAsLimits, doNeg=doNeg,
                                                     figOfMeritLimit=figOfMeritLimit)
            nPositions.append(position)
            nHeights.append(height)
            nHErrors.append(hError)
    deltas = np.array(nPositions) - np.array(oPositions)
    deltas = deltas.flatten()

    if len(peaks) == 1:
        peaks[0].position = nPositions[0]
        peaks[0].height = nHeights[0]
        peaks[0].heightError = nHErrors[0]
        return deltas[0]

    # - use deltas to fit patterns of shifts and detect the most probable global shift
    stats, edges, binNumbers, fittedCurve, mostCommonBinNumber, highestValues, fittedCurveExtremum = _getBins(deltas)
    shift = max(highestValues)
    oReferenceValues = spectrum.referenceValues
    oPositions = spectrum.positions
    #  - use the global shift to re-reference the spectrum
    spectrum.referenceValues = [spectrum.referenceValues[0] - shift]
    spectrum.positions = spectrum.positions - shift

    #  - 2nd iteration: re-search for nearest maxima
    for peak in peaks:
        if peak is not None:
            oPosition = peak.position
            peak.position = [peak.position[0] + shift, ]  #  - use the shift to re-reference the peak to the moved spectrum
            position, height, error = _get1DClosestExtremum(peak, maximumLimit=maximumLimit,
                                                     useAdjacientPeaksAsLimits=useAdjacientPeaksAsLimits, doNeg=doNeg,
                                                     figOfMeritLimit=figOfMeritLimit)
            #  - set newly detected position if found better fits
            if peak.position == position:  # Same position detected. Revert
                peak.height = peak.peakList.spectrum.getHeight(oPosition)
                peak.position = oPosition
                peak.heightError = error
            else:
                peak.position = position
                peak.height = height
                peak.heightError = error
    # - re-set the spectrum referencing to original (if not requested as argument)
    if not autoRereferenceSpectrum:
        spectrum.referenceValues = oReferenceValues
        spectrum.positions = oPositions
    # check for missed maxima or peaks snapped to height@position but had other unpicked maxima close-by
    return shift

###################################
####### Private library functions   #######
###################################

def _getRereferencingParamsFromDeltas(sourcePeaks, destinationPeaks, sortBy=None, snr=3, fom=0.5):
    """
    Calculate the best global alignment shift from two sets of peaks. E.g. before and after snapping peaks.

    :param sourcePeaks: list of peaks
    :param destinationPeaks:  list of peaks. same length as source
    :param sortBy: str or None. one of: position, height
    :param snr: float. signal-to-noise ratio threshold limit. include peaks only if the snr is greater than this value
    :param fom: float. figure of merit threshold limit. include peaks only if the fom is greater than this value
    :return: dict of optimisation parameters and results.
    """
    if len(sourcePeaks) != len(destinationPeaks):
        raise RuntimeError('source and destination peaks must be of the same count')
    # do some sorting/filtering
    sourcePeaks = list(sourcePeaks)
    destinationPeaks = list(destinationPeaks)
    if sortBy in ['position', 'height']:
        sourcePeaks.sort(key=lambda x: x.sortBy, reverse=True)
        destinationPeaks.sort(key=lambda x: x.sortBy, reverse=True)
    sourcePositions, destinationPositions = [], []
    for sourcePeak, destinationPeak in zip(sourcePeaks, destinationPeaks):
        if sourcePeak.figureOfMerit < fom or destinationPeak.figureOfMerit < fom:
            continue
        if sourcePeak.signalToNoiseRatio < snr or destinationPeak.signalToNoiseRatio < snr:
            continue
        sourcePositions.append(sourcePeak.position)
        destinationPositions.append(destinationPeak.position)

    # do the calculations
    deltas = np.array(sourcePositions) - np.array(destinationPositions)
    deltas = deltas.flatten()
    # - use deltas to fit patterns of shifts and detect the most probable global shift
    stats, edges, binNumbers, fittedCurve, mostCommonBinNumber, highestValues, fittedCurveExtremum = _getBins(deltas)
    shift = np.max(np.abs(highestValues))
    statsDict = {
        'shift': shift,
        'deltas': deltas,
        'stats': stats,
        'edges': edges,
        'binNumbers': binNumbers,
        'fittedCurve': fittedCurve,
        'mostCommonBinNumber': mostCommonBinNumber,
        'highestValues': highestValues,
        'fittedCurveExtremum': fittedCurveExtremum}
    return statsDict

def _snap1DPeaksByGroup(peaks, ppmLimit=0.05, groupPpmLimit=0.05,  figOfMeritLimit=1,
                       doNeg=False, ):
    """
    :param peaks: 1D peaks to be snapped.
    :param ppmLimit: float. imit in ppm to define a searching window.
    :param figOfMeritLimit: float. don't snap peaks with FOM below limit threshold
    :param doNeg: If to include also negative maxima as a solution.

    :return: None
    """
    ## peaks can be from different spectra, so let's group first.
    spectraPeaks = defaultdict(list)
    for peak in peaks:
        if peak.figureOfMerit >= figOfMeritLimit:
            spectraPeaks[peak.spectrum].append(peak)

    ## Start the snapping routine
    for spectrum, peaks in spectraPeaks.items():
        xValues, yValues = spectrum.positions, spectrum.intensities
        noiseLevel = spectrum.noiseLevel
        negativeNoiseLevel = spectrum.negativeNoiseLevel
        snappingPeaks = np.array(peaks)
        snappingPositions = np.array([pk.position[0] for pk in snappingPeaks])

        ## Cluster peaks in groups by the ppmLimit. Consider a group of peaks if they fall within the ppmLimits,
        i = np.argsort(snappingPositions)
        snappingPositions = snappingPositions[i]
        snappingPeaks = snappingPeaks[i]
        mask = np.diff(snappingPositions, prepend=snappingPositions[0]) <= ppmLimit
        reverseMask = ~mask
        indices = np.nonzero(reverseMask)[0]
        peakGroups = np.split(snappingPeaks, indices)
        peakGroups.sort(key=len) #snap the smaller group first
        for peakGroup in peakGroups[:]:
            peakGroup = np.array(peakGroup)
            if len(peakGroup) == 1:
                ## if there is only one peak in the group then snap normally to closest:
                snap1DPeaksToExtrema(list(peakGroup), maximumLimit=ppmLimit)
            else:
                positions = np.array([pk.position[0] for pk in peakGroup])
                limits = np.min(positions), np.max(positions)
                searchingLimits = limits[0] - ppmLimit, limits[1] + ppmLimit
                # need to check if within these limits there are other peaks. and restrict the search. otherwise will "steal" the maximum from other closer peaks
                rounding = 4
                # otherPeaks = [round(p.position[0],rounding) for p in peakGroup[0].peakList.peaks if p not in peakGroup if p.position[0] if _isWithinLimits(p.position[0], searchingLimits)]

                xROItarget, yROItarget = _1DregionsFromLimits(xValues, yValues, limits=searchingLimits)
                maxValues, minValues = _find1DMaxima(yROItarget, xROItarget, positiveThreshold=noiseLevel,
                                                     negativeThreshold=negativeNoiseLevel, findNegative=doNeg)
                foundCoords = maxValues + minValues
                # foundCoords = _filterKnownPeakPositionsFromNewMaxima(foundCoords, knownPositions=otherPeaks, rounding=rounding)

                if len(foundCoords) == 0:
                    ## No new coords found. Recalculate height at position.
                    for peak in peakGroup:
                        peak.height = peak.spectrum.getHeight(peak.position)
                        peak.heightError =1
                    continue
                if len(foundCoords) == len(peakGroup):
                    ## found the same count of new coords and peaks in the group. Order by position and snap sequentially.
                    peakGroup = list(peakGroup)
                    peakGroup.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
                    foundCoords = list(foundCoords)
                    foundCoords.sort(key=lambda x: x[0], reverse=False)  # reorder peaks by  position p[0]  reverse=False;  or height [1] reverse=True
                    for peak, coord in zip(peakGroup, foundCoords):
                        peak.position = [coord[0], ]
                        peak.height = float(coord[1])
                        peak.heightError = None
                else:
                    ## found different count of new coords and peaks. Order by distanceMatrix and snap to best fit.
                    _snap1DPeaksByGroup(peaks, ppmLimit=ppmLimit / 2)

def _1Dregion(x, y, value, lim=0.01):
    # centre of position, peak position
    # lim in ppm where to look left and right
    referenceRegion = [value - lim, value + lim]
    point1, point2 = np.max(referenceRegion), np.min(referenceRegion)
    x_filtered = np.where((x <= point1) & (x >= point2))  # only the region of interest for the reference spectrum
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered

def _isWithinLimits(position, limits):
    position = abs(position)
    limits = np.array(limits)
    limits = np.abs(limits)
    point1, point2 = np.max(limits), np.min(limits)
    return (abs(position) <= point1) & (position >= point2)

def _1DregionsFromLimits(x, y, limits):
    # centre of position, peak position
    # lim in ppm where to look left and right
    point1, point2 = np.max(limits), np.min(limits)
    x_filtered = np.where((x <= point1) & (x >= point2))  # only the region of interest for the reference spectrum
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def _fitBins(y, bins):
    # fit a gauss curve over the bins
    mu = np.mean(y)
    sigma = np.std(y)
    fittedCurve = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(bins - mu) ** 2 / (2 * sigma ** 2))
    return fittedCurve

def _getBins(y, binCount=None):
    """
    :param y:
    :return:
    ### plot example:
    import matplotlib.pyplot as plt  # to plot
    plt.hist(y, bins=int(len(y)/2), density=True)
    plt.plot(edges, fittedCurve, linewidth=2, color='r')
    plt.show()
    """
    from scipy.stats import binned_statistic

    binCount = binCount or int(len(y) / 2)
    statistics, edges, binNumbers = binned_statistic(y, y, bins=binCount, statistic='median')
    mostCommonBinNumber = np.argmax(np.bincount(binNumbers))
    highestValues = y[binNumbers == mostCommonBinNumber]  # values corresponding to most frequent binNumber
    fittedCurve = _fitBins(y, edges)
    fittedCurveExtremum = edges[np.argmax(fittedCurve)]  # value at the Extremum of the fitted curve
    return statistics, edges, binNumbers, fittedCurve, mostCommonBinNumber, highestValues, fittedCurveExtremum

def _getAdjacentPeakPositions1D(peak):
    positions = [p.position[0] for p in peak.peakList.peaks]
    positions.sort()
    queryPos = peak.position[0]
    tot = len(positions)
    idx = positions.index(queryPos)
    previous, next = True, True
    previousPeakPosition, nextPeakPosition = None, None
    if idx == 0:
        previous = False
    if idx == tot - 1:
        next = False
    if previous:
        previousPeakPosition = positions[positions.index(queryPos) - 1]
    if next:
        nextPeakPosition = positions[positions.index(queryPos) + 1]
    return previousPeakPosition, nextPeakPosition

def _correctNegativeHeight(height, doNeg=False):
    """return height either Positive or Negative value if doNEg=True. If height is negative and doNeg=False:
    return the smallest positive number (non-zero) like 4.9e-324."""
    if height < 0:
        if not doNeg:
            return np.nextafter(0, 1)
    return height

def _get1DClosestExtremum(peak, maximumLimit=0.1, useAdjacientPeaksAsLimits=False, doNeg=False,
                          figOfMeritLimit=1):
    """
    :param peak:
    :param maximumLimit: don't snap peaks over this threshold in ppm
    :param useAdjacientPeaksAsLimits: stop a peak to go over pre-existing peaks (to the left/right)
    :param doNeg: include negative peaks as solutions
    :param figOfMeritLimit: skip if below this threshold and give only height at position
    :return: position, height : position is a list of length 1,  height is a float

    search  maxima close to a given peak based on the maximumLimit (left/right) or using the adjacent peaks position as limits.
     return the nearest coordinates position, height

    """
    from ccpn.core.lib.SpectrumLib import estimateNoiseLevel1D
    from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima

    spectrum = peak.peakList.spectrum
    x = spectrum.positions
    y = spectrum.intensities
    position, height, heightError = peak.position, peak.height, peak.heightError
    if peak.figureOfMerit < figOfMeritLimit:
        height = peak.peakList.spectrum.getHeight(peak.position)
        height = _correctNegativeHeight(height, doNeg)
        heightError = 1
        return position, height, heightError

    if useAdjacientPeaksAsLimits:  #  a left # b right limit
        a, b = _getAdjacentPeakPositions1D(peak)
        if not a:  # could not find adjacient peaks if the snapping peak is the first or last
            if peak.position[0] > 0:  #it's positive
                a = peak.position[0] - maximumLimit
            else:
                a = peak.position[0] + maximumLimit
        if not b:
            if peak.position[0] > 0:  # it's positive
                b = peak.position[0] + maximumLimit
            else:
                b = peak.position[0] - maximumLimit
    else:
        a, b = peak.position[0] - maximumLimit, peak.position[0] + maximumLimit

    # refind maxima
    noiseLevel = spectrum.noiseLevel
    negativeNoiseLevel = spectrum.negativeNoiseLevel
    if not noiseLevel:  # estimate as you can from the spectrum
        spectrum.noiseLevel, spectrum.negativeNoiseLevel = noiseLevel, negativeNoiseLevel = estimateNoiseLevel1D(y)
    if not negativeNoiseLevel:
        noiseLevel, negativeNoiseLevel = estimateNoiseLevel1D(y)
        spectrum.negativeNoiseLevel = negativeNoiseLevel

    x_filtered, y_filtered = _1DregionsFromLimits(x, y, [a, b])

    maxValues, minValues = _find1DMaxima(y_filtered, x_filtered, positiveThreshold=noiseLevel, negativeThreshold=negativeNoiseLevel, findNegative=doNeg)
    allValues = maxValues + minValues
    allValues =  _filterLowSNFromNewMaxima(allValues, noiseLevel, negativeNoiseLevel,  snThreshold=2)
    allValues = _filterShouldersFromNewMaxima(allValues, x_filtered, y_filtered)
    allValues = _filterKnownPeakPositionsFromNewMaxima(allValues, peak, rounding=4)

    if len(allValues) > 0:
        allValues = np.array(allValues)
        positions = allValues[:, 0]
        heights = allValues[:, 1]
        nearestPosition = find_nearest(positions, peak.position[0])
        nearestHeight = heights[positions == nearestPosition]

        if useAdjacientPeaksAsLimits:
            if a == nearestPosition or b == nearestPosition:  # avoid snapping to an existing peak, as it might be a wrong snap.
                height = peak.peakList.spectrum.getHeight(peak.position)
                heightError = 1
            # elif abs(nearestPosition) > abs(peak.position[0] + maximumLimit):  # avoid snapping on the noise if not maximum found
            # peak.height = peak.peakList.spectrum.getHeight(peak.position)

            else:
                position = [float(nearestPosition), ]
                height = nearestHeight
                heightError = None
        else:
            a, b = _getAdjacentPeakPositions1D(peak)
            if float(nearestPosition) in (a, b):  # avoid snapping to an existing peak,
                height = peak.peakList.spectrum.getHeight(peak.position)
                heightError = 1

            else:
                position = [float(nearestPosition), ]
                height = nearestHeight
                heightError = None
    else:
        height = peak.peakList.spectrum.getHeight(peak.position)
        heightError = 1

    height = _correctNegativeHeight(height, doNeg)  # Very important. don't return a negative height if doNeg is False.
    return position, float(height), heightError

def _filterKnownPeakPositionsFromNewMaxima(newMaxima, peak=None,  knownPositions = None, rounding=4):
    """Remove known positions from the newly found maxima to avoid snapping to an existing peak"""
    if knownPositions is None and peak:
        knownPositions = [round(p.position[0], rounding) for p in peak.peakList.peaks]
    for maximum in newMaxima:
        pos, intens = maximum
        if round(pos, rounding) in knownPositions:
            newMaxima.remove(maximum)
    return newMaxima

def _filterLowSNFromNewMaxima(newMaxima, noiseLevel, negativeNoise,  snThreshold=1.5):
    """Remove known positions from the newly found maxima to avoid snapping to an existing peak"""
    for maximum in newMaxima:
        pos, intens = maximum
        ratio = None
        if intens > 0:
            ratio = intens/noiseLevel
        if intens <0:
            ratio = intens/negativeNoise
        if ratio is None:
            continue
        if ratio  <= snThreshold:
            newMaxima.remove(maximum)
    return newMaxima


def _filterShouldersFromNewMaxima(newMaxima, x,y, proximityTollerance=1e5 ):
    """Remove known positions from the newly found maxima to avoid snapping to an existing peak"""
    for maximum in newMaxima:
        pos, intens = maximum
        if intens ==  y[0] or intens == [-1]:
            newMaxima.remove(maximum)

    return newMaxima
