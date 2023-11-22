"""
In this file there are several functions needed for snapping 1D peaks.

WARNING:
    The 1D peak snapping algorithm is not simply the action of finding the closest maximum for an existing peak.
    It is highly optimised for screening routines following industrial collaborations and extensive testing.
    Do any refactoring with extra caution!

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
__dateModified__ = "$dateModified: 2023-11-22 18:46:46 +0000 (Wed, November 22, 2023) $"
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
from collections import defaultdict
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import  undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima
from ccpn.core.lib.SpectrumLib import  _1DRawDataDict
from scipy import spatial, signal

def snap1DPeaks(peaks, **kwargs):
    results = _find1DCoordsForPeaks(peaks, **kwargs)
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            for pk, values in results.items():
                position = values[0]
                height = float(values[1])
                error = values[2]
                pk.position = position
                pk.height = float(height)
                pk.heightError = error

## ~~~~~~~~~~~~~ Lib Snapping Functions ~~~~~~~~~~~~~~~~ ##

def _find1DCoordsForPeaks(peaks,
                      rawDataDict=None,
                      ppmLimit=0.3,
                      autoClusterPeaks = True,
                      additionalClusterPeakPpmLimit=0.1,
                      figOfMeritLimit=1,
                      doNeg=False):
    """
    :param peaks:
    :param rawDataDict:
    :param ppmLimit:
    :param additionalClusterPeakPpmLimit:  When detecting a cluster, add an additional +- limits to the edges of a cluster region
    :param figOfMeritLimit:
    :param doNeg:
    :return: dict.
                        Keys: peak.
                        values: list of [ppmPosition, height, heightError]
    """
    results = {peak:[peak.position, peak.height, peak.heightError] for peak in peaks}
    rounding = 4
    ## peaks can be from different spectra, so let's group first
    spectraPeaks = defaultdict(list)
    for _p in peaks:
        if _p.figureOfMerit >= figOfMeritLimit:
            spectraPeaks[_p.spectrum].append(_p)

    if rawDataDict is None:
        rawDataDict = _1DRawDataDict(list(spectraPeaks.keys()))

    ## Start the snapping routine
    for spectrum, grouppedPeaks in spectraPeaks.items():
        if spectrum not in rawDataDict:
            getLogger().warning(f'Raw data for {spectrum.pid}  not found')
            continue
        xValues, yValues = rawDataDict.get(spectrum)

        ## peaks can be also different peakLists, so let's group first

        peaksByPeakList = defaultdict(list)
        for _p in grouppedPeaks:
                peaksByPeakList[_p.peakList].append(_p)

        ## Do a quick search of minimal height for a signal, the expected maxima, and calculate linewidths (pnts)
        minimalHeightThreshold = float(np.median(yValues) + 0.5 * np.std(yValues))
        maximaIndices, _ = signal.find_peaks(yValues, height=minimalHeightThreshold)
        maximaHWHH = signal.peak_widths(yValues, maximaIndices, rel_height=0.5)[0]  # array of points

        ## use the largest signal linewdth as an initial windowSize needed later-on for lineSmoothing. Or a default value (100 pnts)
        if len(maximaHWHH) > 0:
            initialWindowSize = np.max(maximaHWHH) * 2
        else:
            initialWindowSize = 100

        for pl, subPeakGroup in peaksByPeakList.items():
            snappingPeaks = np.array(subPeakGroup)
            snappingPositions = np.array([pk.position[0] for pk in snappingPeaks])

            if autoClusterPeaks:
                ## Cluster peaks in groups by the ppmLimit. Consider a group of peaks if they fall within the ppmLimits,
                i = np.argsort(snappingPositions)
                snappingPositions = snappingPositions[i]
                snappingPeaks = snappingPeaks[i]
                mask = np.diff(snappingPositions, prepend=snappingPositions[0]) <= ppmLimit
                reverseMask = ~mask
                indices = np.nonzero(reverseMask)[0]
                peakGroups = np.split(snappingPeaks, indices)
                ## sort so to snap the smaller group first
                peakGroups.sort(key=len)
            else:
                ## Make groups of one. To snap each peak one at a time.
                peakGroups = [[pk] for pk in subPeakGroup]

            ## Start the snapping process
            for peakGroup in peakGroups[:]:
                if len(peakGroup) == 0:
                    continue
                _peak = peakGroup[0]
                peakGroup = np.array(peakGroup)
                knownPositions = np.array([p.position[0] for p in _peak.peakList.peaks if p not in peakGroup])

                ## if there is only one peak in the group then snap to closest coord:
                if len(peakGroup) == 1:
                    ## make the limits around the snapping peak. Reduce the limits if an existing peak(s) fall within the user-set ppmLimit. This avoid "stealing" maxima.
                    queryPos = float(_peak.position[0])
                    limits = np.array([queryPos - ppmLimit, queryPos + ppmLimit])
                    limitsFromKnownPositions = np.concatenate([knownPositions, limits])
                    left = limitsFromKnownPositions[limitsFromKnownPositions > queryPos]
                    right = limitsFromKnownPositions[limitsFromKnownPositions < queryPos]
                    closestLeft = left[np.argmin(left - queryPos)]
                    closestRight = right[np.argmin(abs(right) - queryPos)]

                    ## get the region of interest from the whole array
                    x_filtered, y_filtered = _1DregionsFromLimits(xValues, yValues, [closestLeft, closestRight])
                    coords = _getMaximaForRegion(y_filtered, x_filtered, minimalHeightThreshold=minimalHeightThreshold,
                                                 neededMaxima=1, initialWindowSize=initialWindowSize, totWindowSizeSteps=1000)
                    heightAtQuery = _getClosestHeight(xValues, yValues, queryPos, _peak.height)
                    if len(coords) > 0:
                        coord = coords[0]
                        ## round knownPositions.
                        existing = np.array([round(p.position[0], rounding) for p in _peak.peakList.peaks])
                        heights = np.array([coord[1], float(heightAtQuery)])
                        ## avoid a snap to an already taken maximum
                        if round(coord[0], rounding) in existing:
                            print('cannot snap here. Already one peak here', coord[0], 'THERE:', existing)
                            position = [queryPos]
                            height = heightAtQuery
                            error = 1
                        ## both the knew found value and the original are in the noise. so just keep at position
                        elif (heights < minimalHeightThreshold).all():
                            print('Found in noise .No Point snapping. ')
                            position = [queryPos]
                            height = heightAtQuery
                            error = 1
                        ## the new found solution has a S/N very low. is probably still noise
                        elif coord[1]/minimalHeightThreshold <= 2:
                            print('new found solution has a S/N very low. is probably still noise  ')
                            position = [queryPos]
                            height = heightAtQuery
                            error = 1
                        ## we found a good new solution
                        else:
                            position = [coord[0]]
                            height = coord[1]
                            error = None
                            print('Found a good new solution. ',)
                    else:
                        position = [queryPos]
                        height = heightAtQuery
                        error = 1
                    results[_peak] = [position, float(height), error]

                ## we have multiple peaks to snap at once.
                else:
                    groupPositions = np.array([pk.position[0] for pk in peakGroup])
                    ## define the search limits around snapping peaks:
                    ## 1) use the first and last peak position in the group as left-right limits
                    minGroupPos = np.min(groupPositions)
                    maxGroupPos = np.max(groupPositions)
                    leftLimit = minGroupPos - additionalClusterPeakPpmLimit
                    rightLimit =  maxGroupPos + additionalClusterPeakPpmLimit
                    clusterLimits = np.array([leftLimit, rightLimit])
                    limitsFromKnownPositions = np.concatenate([knownPositions, clusterLimits])
                    left = limitsFromKnownPositions[limitsFromKnownPositions > minGroupPos]
                    right = limitsFromKnownPositions[limitsFromKnownPositions < maxGroupPos]
                    closestLeft = left[np.argmin(left - minGroupPos)]
                    closestRight = right[np.argmin(abs(right) - maxGroupPos)]

                    # need to check if within these limits there are other peaks. and restrict the search. otherwise will "steal" the maximum from other closer peaks
                    rounding = 4
                    neededMaxima = len(peakGroup)
                    x_filtered, y_filtered = _1DregionsFromLimits(xValues, yValues, limits=[closestLeft, closestRight])
                    foundCoords = _getMaximaForRegion(y_filtered, x_filtered,
                                                      minimalHeightThreshold=minimalHeightThreshold,
                                                      neededMaxima=neededMaxima,
                                                      initialWindowSize=initialWindowSize, totWindowSizeSteps=1000)
                    print('foundCoords:', foundCoords)

                    ## Scenario 1: No new coords found. Recalculate height at position, no snapping required
                    if len(foundCoords) == 0:
                        print('No new coords found')
                        for peak in peakGroup:
                            position = peak.position
                            heightAtQuery = _getClosestHeight(xValues, yValues, peak.position, peak.height)
                            height = heightAtQuery
                            error = 1
                            results[peak] = [position, float(height), error]
                        continue

                    if len(foundCoords) == len(peakGroup):
                        print('found the same count of new coords and peaks in the group. Order by position and snap sequentially')
                        ## found the same count of new coords and peaks in the group. Order by position and snap sequentially.
                        peakGroup = list(peakGroup)
                        peakGroup.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
                        foundCoords = list(foundCoords)
                        foundCoords.sort(key=lambda x: x[0], reverse=False)  # reorder peaks by  position p[0]  reverse=False;  or height [1] reverse=True
                        for peak, coord in zip(peakGroup, foundCoords):
                            # we need to check if the height is ok as up
                            position = [coord[0], ]
                            height = float(coord[1])
                            error = 0
                            results[peak] = [position, float(height), error]
                    else:
                        ## found different count of new coords and peaks.
                        print('found different count of new coords and peaks.', foundCoords)
                        for peak in peakGroup:
                            _find1DCoordsForPeaks([peak], ppmLimit=ppmLimit, rawDataDict=rawDataDict)

    return results

def _1DregionsFromLimits(x, y, limits):
    """
    internal. convenient function.
    :param x: 1D array
    :param y: 1D array
    :param limits: list two values to find in x
    :return: x values witih the limits and its ys
    """
    point1, point2 = np.max(limits), np.min(limits)
    x_filtered = np.where((x <= point1) & (x >= point2))
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered

def _onePhaseDecayPlateau_func(x, rate=1.0, amplitude=1.0, plateau=0.0):
    """
    Duplicated function from series Analysis. Import from fitting models
    """
    result = (amplitude - plateau) * np.exp(-rate * x) + plateau
    return result

def _getMaximaForRegion(y, x, minimalHeightThreshold, neededMaxima, initialWindowSize=500, totWindowSizeSteps=1000):
    """
    This function is used to find maxima for an x,y region of interest.
    The Y lineshape is interactively smoothed to so to remove any false-positive peaks.
    The windows size starts large, and gets exponentially smaller and smaller until the needed maxima are satisfied.
    :param y:
    :param x:
    :param minimalHeightThreshold:
    :param neededMaxima:
    :param initialWindowSize:
    :param totWindowSizeSteps:
    :return:
    """
    unfilteredMaxima, unfilteredMinima = _find1DMaxima(y, x, minimalHeightThreshold)
    unfilteredMaximaPos = np.array([x[0] for x in unfilteredMaxima])
    unfilteredMaximaHeight = np.array([x[1] for x in unfilteredMaxima])

    windowSizesX = np.linspace(0, 1, totWindowSizeSteps)
    windowSizes = _onePhaseDecayPlateau_func(windowSizesX, rate=10, amplitude=initialWindowSize, plateau=1)

    coords = []
    for windowSize in windowSizes:  # keep reducing the window until we find smoothed peaks
        print(f'STARTING with windowSize: {windowSize}')

        y_smoothed = lineSmoothing(y, windowSize=int(windowSize))
        indexes, _ = signal.find_peaks(y_smoothed, )
        for index in indexes:
            try:
                pos = x[index]
                idx = (np.abs(unfilteredMaximaPos - pos)).argmin()
                nearestPos = unfilteredMaximaPos[idx]
                nearestHeight = unfilteredMaximaHeight[idx]
                coord = (nearestPos, nearestHeight)
                if coord not in coords:
                    coords.append(coord)
            except Exception as error:
                getLogger().warn(f'Something wrong snapping peak. {windowSize}')

        if len(coords) >= neededMaxima:
            print('DONE. Reached needed count')
            break

    if len(coords) >= neededMaxima:
        # take the highest of the solutions
        coords = sorted(coords, key=lambda x: x[1], reverse=True)  # sort by height
        coords = coords[:neededMaxima]
    return coords

def _getClosestHeight(x,y, pos, currentHeight):
    try:
        ax = x.reshape(len(x), 1)
        closestX = ax[spatial.KDTree(ax).query(pos)[1]]
        closestY = y[x==closestX]
        return closestY
    except Exception as err:
        getLogger().warning('Could not find the closest', err)
    return currentHeight

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
