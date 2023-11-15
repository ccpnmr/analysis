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
__dateModified__ = "$dateModified: 2023-11-15 11:58:48 +0000 (Wed, November 15, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Muredd $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
# from scipy.spatial.distance import cdist
from collections import defaultdict
# from scipy.optimize import linear_sum_assignment
# from scipy.optimize import curve_fit
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import  undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima
from ccpn.core.lib.SpectrumLib import  _1DRawDataDict
from scipy import spatial


# from ccpn.util.decorators import profile
# @profile('/Users/luca/Documents/V3-testings/profiling/')
def snap1DPeaksByGroup(peaks, ppmLimit=0.05, unsnappedLimit=1, increaseLimitStep=0.1, groupPpmLimit=0.2,  figOfMeritLimit=1,
                       doNeg=False, rawDataDict=None, offsetForSamePos=0.0005):
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
    spectra = set()

    _snap1DPeaksByGroup.count = 0
    for peak in peaks: # set the temp properties first.
        peak._temporaryPosition = peak.position
        peak._temporaryHeight = peak.height
        peak._temporaryHeightError = peak.heightError
        spectra.add(peak.spectrum)

    if rawDataDict is None:
        rawDataDict = _1DRawDataDict(spectra=spectra)
    ## Do the first snap with initial limits.
    _snap1DPeaksByGroup(peaks, ppmLimit=ppmLimit,  figOfMeritLimit=figOfMeritLimit, doNeg=doNeg, rawDataDict=rawDataDict)
    _snap1DPeaksByGroup.count = 1
    unsnappedPeaks = [p for p in peaks if p._temporaryHeightError and p._temporaryHeightError > 0 and p.figureOfMerit >= figOfMeritLimit]
    if False:
    # if len(unsnappedPeaks) > 0:
        ## Keep increasing the limits to a max until we find new maxima .
        for newLimit in np.arange(ppmLimit, unsnappedLimit + increaseLimitStep, increaseLimitStep):
            _snap1DPeaksByGroup(unsnappedPeaks, ppmLimit=newLimit, figOfMeritLimit=figOfMeritLimit,
                       doNeg=doNeg,  rawDataDict=rawDataDict)
            _snap1DPeaksByGroup.count += 1
            unsnappedPeaks = [p for p in unsnappedPeaks if p._temporaryHeightError and p._temporaryHeightError > 0 and p.figureOfMerit >= figOfMeritLimit]
            if len(unsnappedPeaks) == 0:
                break

    with undoBlockWithoutSideBar(): # set the final properties.
        with notificationEchoBlocking():
            for peak in peaks:
                peak.position = peak._temporaryPosition
                peak._temporaryPosition = None
                peak.height = float(peak._temporaryHeight)
                peak.heightError = peak._temporaryHeightError


###################################
####### Private library functions   #######
###################################

def _snap1DPeaksToClosestExtremum(peaks, maximumLimit=0.1, figOfMeritLimit=1, doNeg=True, rawDataDict=None, ):
    if len(peaks) > 0:
        peaks = list(peaks)
        peaks.sort(key=lambda pk: pk._temporaryPosition[-1], reverse=False)  # reorder peaks by position

        for peak in peaks:  # peaks can be from diff peakLists
            if peak is not None:
                position, height, error = _get1DClosestExtremum(peak, maximumLimit, doNeg=doNeg,  figOfMeritLimit=figOfMeritLimit, rawDataDict=rawDataDict)
                peak._temporaryPosition = position
                peak._temporaryHeight = height
                peak._temporaryHeightError = error


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

def _snap1DPeaksByGroup(peaks, rawDataDict=None, ppmLimit=0.05, groupPpmLimit=0.05,  figOfMeritLimit=1,
                       doNeg=False,  maxRecursion=5 ):
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
        if not rawDataDict or not spectrum in rawDataDict:
            getLogger().warning(f'Raw data for {spectrum.pid}  not found')
            continue
        xValues, yValues = rawDataDict.get(spectrum)
        noiseLevel = spectrum.noiseLevel
        negativeNoiseLevel = spectrum.negativeNoiseLevel
        snappingPeaks = np.array(peaks)
        snappingPositions = np.array([pk._temporaryPosition[0] for pk in snappingPeaks])

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
                _snap1DPeaksToClosestExtremum(list(peakGroup), maximumLimit=ppmLimit, rawDataDict=rawDataDict)
            else:
                positions = np.array([pk._temporaryPosition[0] for pk in peakGroup])
                limits = np.min(positions), np.max(positions)
                searchingLimits = limits[0] - ppmLimit, limits[1] + ppmLimit
                # need to check if within these limits there are other peaks. and restrict the search. otherwise will "steal" the maximum from other closer peaks
                rounding = 4
                # otherPeaks = [round(p._temporaryPosition[0],rounding) for p in peakGroup[0].peakList.peaks if p not in peakGroup if p.position[0] if _isWithinLimits(p.position[0], searchingLimits)]

                xROItarget, yROItarget = _1DregionsFromLimits(xValues, yValues, limits=searchingLimits)
                maxValues, minValues = _find1DMaxima(yROItarget, xROItarget, positiveThreshold=noiseLevel,
                                                     negativeThreshold=negativeNoiseLevel, findNegative=doNeg)
                foundCoords = maxValues + minValues
                # foundCoords = _filterKnownPeakPositionsFromNewMaxima(foundCoords, knownPositions=otherPeaks, rounding=rounding)

                if len(foundCoords) == 0:
                    ## No new coords found. Recalculate height at position.
                    for peak in peakGroup:
                        peak._temporaryHeight = _getClosestHeight(xValues, yValues, peak._temporaryPosition, peak._temporaryHeight)
                        peak._temporaryHeightError = 1
                    continue
                if len(foundCoords) == len(peakGroup):
                    ## found the same count of new coords and peaks in the group. Order by position and snap sequentially.
                    peakGroup = list(peakGroup)
                    peakGroup.sort(key=lambda x: x._temporaryPosition[0], reverse=False)  # reorder peaks by position
                    foundCoords = list(foundCoords)
                    foundCoords.sort(key=lambda x: x[0], reverse=False)  # reorder peaks by  position p[0]  reverse=False;  or height [1] reverse=True
                    for peak, coord in zip(peakGroup, foundCoords):
                        peak._temporaryPosition = [coord[0], ]
                        peak._temporaryHeight = float(coord[1])
                        peak._temporaryHeightError = 0
                else:
                    ## found different count of new coords and peaks.
                    try:
                        _snap1DPeaksByGroup.count +=1
                    except Exception as err:
                        _snap1DPeaksByGroup.count = 0
                    if  _snap1DPeaksByGroup.count <= maxRecursion:
                        _snap1DPeaksByGroup(peakGroup, ppmLimit=ppmLimit / 2, rawDataDict=rawDataDict)
                    else:# cannot find any solution. snap one at the time
                        for peak in peakGroup:
                            _snap1DPeaksByGroup([peak], ppmLimit=ppmLimit, rawDataDict=rawDataDict)

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

def _ensureUniquePeakPosition(peak):
    """Prevent snapping multiple peaks to the exact ppm position, by adding a random offset around the spectrum-ppmPerPoints value"""
    position = peak._temporaryPosition
    height = peak._temporaryHeight
    rounding = 4
    ppmOffset = peak.spectrum.ppmPerPoints[0] / 10
    knownPositions = [round(p._temporaryPosition[0], rounding) for p in peak.peakList.peaks if p != peak]
    maxIter = 10
    it = 0
    while round(position[0], rounding) in knownPositions and it < maxIter:
        ppmOffset *= np.random.uniform(-1, 1, 1)[0]  # multiply by a random value between -1 and 1
        getLogger().debug(f'Peak snapping. An existing peak is already present at the best snapping position for {peak.pid}. Offsetting by ppm {ppmOffset}')
        position = [peak._temporaryPosition[0] + ppmOffset]
        height = peak.spectrum.getHeight(position)
        it += 1
    return position, height

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
    positions = [p._temporaryPosition[0] for p in peak.peakList.peaks]
    positions.sort()
    queryPos = peak._temporaryPosition[0]
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

def lineSmoothing(y, windowSize=15, mode="hanning", ):
    smoothingFuncs = {
                                    "rolling"    : lambda _len: np.ones(_len, "d"), # this is simply a rolling average.
                                    "hanning" : np.hanning,
                                    "hamming" : np.hamming,
                                    "bartlett": np.bartlett,
                                    "blackman": np.blackman
                                    }
    fallbackMode = 'hanning'
    if mode not in smoothingFuncs.keys():
        getLogger().warning(f'Smoothing function not available. use one of {smoothingFuncs.keys()}. Fallback: {fallbackMode}')
    s = np.r_[y[windowSize: 0 : -1], y, y[-1:-windowSize:]]
    f = smoothingFuncs.get(mode, fallbackMode)
    w = f(windowSize)
    ys = np.convolve(w / w.sum(), s, mode="same")
    ys = ys[windowSize:] ## make sure to be properly aligned as the smoothing  shifts by the window size
    ys = ys[:len(y)] ## make sure to have the same length as the input
    return ys

def _get1DClosestExtremum(peak, maximumLimit=0.1,  doNeg=False,
                          figOfMeritLimit=1, windowSize=15, rawDataDict=None ):
    """
    :param peak:
    :param maximumLimit: don't snap peaks over this threshold in ppm
    :param doNeg: include negative peaks as solutions
    :param figOfMeritLimit: skip if below this threshold and give only height at position.
    :return: position, height : position is a list of length 1,  height is a float

    search  maxima close to a given peak based on the maximumLimit (left/right) or using the adjacent peaks position as limits.
     return the nearest coordinates position, height

    """
    spectrum = peak.peakList.spectrum
    if rawDataDict is not None:
        if spectrum in rawDataDict:
            x, y = rawDataDict.get(spectrum)
        else:
            x = spectrum.positions
            y = spectrum.intensities
    else:
        x = spectrum.positions
        y = spectrum.intensities
    position, height, heightError = peak._temporaryPosition, peak.height, peak.heightError
    if peak.figureOfMerit < figOfMeritLimit:
        return position, height, heightError

    a, b = peak._temporaryPosition[0] - maximumLimit, peak._temporaryPosition[0] + maximumLimit

    # find closest maxima
    pcb, ncb = spectrum.positiveContourBase, spectrum.negativeContourBase

    x_filtered, y_filtered = _1DregionsFromLimits(x, y, [a, b])
    maxValues, minValues = _find1DMaxima(y_filtered, x_filtered, positiveThreshold=pcb, negativeThreshold=ncb, findNegative=doNeg)
    allValues = np.array(maxValues + minValues)
    # allValues = _filterKnownPeakPositionsFromNewMaxima(allValues, peak, rounding=4)

    if len(allValues) > 1:
        ## do a line smoothing to remove noise and shoulder peaks.
        y_smoothed = lineSmoothing(y_filtered, windowSize=windowSize)
        maxValues, minValues = _find1DMaxima(y_smoothed, x_filtered, positiveThreshold=pcb, negativeThreshold=ncb, findNegative=doNeg)
        allValuesSmooth = np.array(maxValues + minValues)
        if allValuesSmooth.ndim == 2:
            positions = allValues[:, 0]
            heights = allValues[:, 1]
            positionsSmooth = allValuesSmooth[:, 0]
            heightsSmooth = allValuesSmooth[:, 1]
            nearestPositionSmooth = find_nearest(positionsSmooth, peak._temporaryPosition[0])
            #find the real position and not the smoothed pos
            nearestPosition = find_nearest(positions, nearestPositionSmooth)
            nearestHeight = heights[positions == nearestPosition]

            position = [float(nearestPosition), ]
            height = nearestHeight
            height = _getClosestHeight(x, y, position, height)
            heightError = 0
        else:
            height = _getClosestHeight(x, y, peak._temporaryPosition, peak._temporaryHeight)
            heightError = 1

    elif len(allValues) == 1: # we found just a sigle maxima
        allValues = np.array(allValues)
        positions = allValues[:, 0]
        heights = allValues[:, 1]
        nearestPosition = find_nearest(positions, peak._temporaryPosition[0])
        nearestHeight = heights[positions == nearestPosition]
        position = [float(nearestPosition), ]
        height = nearestHeight
        heightError = 0
    else:
        height = _getClosestHeight(x,y, peak._temporaryPosition, peak._temporaryHeight)
        heightError = 1

    height = _correctNegativeHeight(height, doNeg)  # Very important. don't return a negative height if doNeg is False.
    return position, float(height), heightError


def _getClosestHeight(x,y, pos, currentHeight):
    try:
        ax = x.reshape(len(x), 1)
        closestX = ax[spatial.KDTree(ax).query(pos)[1]]
        closestY = y[x==closestX]
        return closestY
    except Exception as err:
        getLogger().warning('Could not find the closest', err)
    return currentHeight

def _filterKnownPeakPositionsFromNewMaxima(newMaxima, peak,   rounding=4):
    """Remove known positions from the newly found maxima to avoid snapping to an existing peak except to itself."""
    newMaxima = list(newMaxima)
    knownPositions = [round(p._temporaryPosition[0], rounding) for p in peak.peakList.peaks]
    for maximum in newMaxima:
        pos, intens = maximum
        if round(pos, rounding) == round(peak._temporaryPosition[0], rounding):
            continue # Don't remove if  a maximum is equal to the current position.
        if round(pos, rounding) in knownPositions:
            newMaxima.remove(maximum)
    return np.array(newMaxima)

def _filterLowSNFromNewMaxima(newMaxima, noiseLevel, negativeNoise,  snThreshold=0.5):
    """Remove los s/n maxima from the newly found maxima to avoid snapping to noise"""
    for maximum in newMaxima:
        pos, intens = maximum
        ratio = None
        if intens > 0:
            ratio = intens/noiseLevel
        if intens < 0:
            ratio = intens/negativeNoise
        if ratio is None:
            continue
        if ratio  <= snThreshold:
            newMaxima.remove(maximum)
    return newMaxima


def _filterShouldersFromNewMaxima(newMaxima, x,y, proximityTollerance=1e5 ):
    """Remove a positions from the newly found maxima to avoid snapping to a shoulder peak (not the real maximum)"""
    for maximum in newMaxima:
        pos, intens = maximum
        if intens ==  y[0] or intens == [-1]:
            newMaxima.remove(maximum)

    return newMaxima
