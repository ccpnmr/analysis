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
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-02-27 10:50:08 +0000 (Tue, February 27, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Muredd $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from scipy import spatial
from collections import defaultdict
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import  undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima, _find1DPositiveMaxima
from ccpn.core.lib.SpectrumLib import _1DRawDataDict
from ccpn.util.DataEnum import DataEnum

class _SnapFlag(DataEnum):
    """
    A set of flags set to (internal) peak after a snapping reflecting the snap outcome.
    """
    _0 = 0, 'New position and maximum above thresholds'
    _1 = 1, 'New position and maximum above thresholds after an "on-the-fly" local re-referencing'
    _3 = 3, 'New position and maximum below thresholds after an "on-the-fly" local re-referencing'
    _4 = 4, 'Same position and new maximum above thresholds'
    _2 = 2, 'New position and maximum below thresholds'
    _5 = 5, 'Same position and new maximum below thresholds'
    _6 = 6, 'Same position new maximum below thresholds but maxima candidates above thresholds near snapping boundaries'
    _7 = 7, 'Failed. Position and height are unchanged'

def snap1DPeaks(peaks, **kwargs):

    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            peaks = list(peaks)
            peaks.sort(key=lambda x: x.height, reverse=True)
            factor = 1
            minFactor = 0.5
            snapped, unsnapped = [], peaks
            while len(unsnapped) > 0 and factor >= minFactor:
                snapped, unsnapped = _find1DCoordsForPeaks(unsnapped, minimalHeightFactor=factor, **kwargs)
                factor -= 0.2



## ~~~~~~~~~~~~~ Lib Snapping Functions ~~~~~~~~~~~~~~~~ ##

def _getLimitsRange(peak, leftPpm, rightPpm, maxSteps=10):
    leftPopint = peak.spectrum.ppm2point(leftPpm, peak.spectrum.axisCodes[0])
    rightPoint = peak.spectrum.ppm2point(rightPpm, peak.spectrum.axisCodes[0])
    queryPointPos = float(peak.pointPositions[0])
    offset = 3  #otherwise the first range is exactly at the query pos,
    query2Left = np.linspace(queryPointPos-offset, leftPopint, maxSteps)
    query2Right =  np.linspace(queryPointPos+offset, rightPoint, maxSteps)
    limits = []
    for pointLeft, pointRight in zip(query2Left, query2Right):
        ppmLeft = peak.spectrum.point2ppm(pointLeft, peak.spectrum.axisCodes[0])
        ppmRight = peak.spectrum.point2ppm(pointRight, peak.spectrum.axisCodes[0])
        limits.append([ppmLeft, ppmRight])
    return limits


def _snap(peak, x,y, maxima, minimalHeightThreshold,  defaultLimitPpm=0.5, maxLimitPpm=1, figOfMeritLimit=0.5, deltaFactor=0.5, retry=True, ):
    # mainWindow.newMark(colour='#C71585', positions=[minimalHeightThreshold], axisCodes=['intensity'], style='simple', units=(), labels=(), strips=None)
    # peak.annotation = '' if not peak.annotation else peak.annotation
    maxT = 10
    positions, heights = maxima
    otherPeaksPointPosition = np.array([peak.pointPositions[0] for peak in peak.peakList.peaks if peak.figureOfMerit>=figOfMeritLimit])
    leftPpm, rightPpm = _getSnappingPeakLimits(peak, otherPeaksPointPosition=otherPeaksPointPosition, deltaFactor=deltaFactor, defaultLimitPpm=defaultLimitPpm, maxLimitPpm=maxLimitPpm)
    limitsRange = _getLimitsRange(peak, leftPpm, rightPpm, maxSteps=5)
    # nextColour = next(iterator_colours)
    columns = ['deltaPos', 'pickingThreshold','sn', 'ppm', 'height']
    dd = {i:[] for i in columns}
    seenPositions = []
    for i, limits in enumerate(limitsRange):
        ## progressivly increase the searching Limits until the next peak or the max allowed
        leftPpm, rightPpm = limits
        deltaLimit = abs(abs(leftPpm) - abs(rightPpm))
        maxHeightThreshold = float(np.max(y))
        pickingThresholds = np.linspace(minimalHeightThreshold+1, maxHeightThreshold-1, maxT)
        pickingThresholds = -np.sort(-pickingThresholds) #Largest first
        seenPos = None
        for h, pickingThreshold in enumerate(pickingThresholds):
            # mainWindow.newMark(colour=brush, positions=[pickingThreshold], axisCodes=['intensity'], style='simple', units=(), labels=(f'{h}'), strips=None)
            xPos4Region, yPos4Region =  _1DregionsFromLimits(positions, heights, limits)
            regionMaximaIndexes = np.argsort([yPos4Region > pickingThreshold]).flatten()
            pos = None
            for index in regionMaximaIndexes:
                pos = xPos4Region[index]
                if pos not in seenPositions:
                    height = yPos4Region[index]
                    deltaPos =  abs(abs(peak.position[0]) - abs(pos))
                    sn = height/minimalHeightThreshold
                    dd['deltaPos'].append(deltaPos)
                    dd['pickingThreshold'].append(pickingThreshold)
                    dd['sn'].append(sn)
                    dd['ppm'].append(pos)
                    dd['height'].append(height)
                    seenPos = pos
                    seenPositions.append(pos)
            if seenPos == pos:
                break
        # Don't break the  search. Let it explore all limits until the end.

    df = pd.DataFrame(dd)
    df = df[df['sn'] > 1.3]
    if len(df)>0:

        df.drop_duplicates(subset=['ppm', 'height'],  inplace=True)
        df = df.sort_values(['deltaPos', 'pickingThreshold', 'sn'], ascending=[True, False, False])
        pos = df['ppm'].values[0]
        height = df['height'].values[0]
        position = float(pos)
        height = float(height)
        heightError = 0
        peak.position =  [position]
        peak.height = height
        peak.heightError = heightError
        return [position], height, heightError

    if retry:
        return _snap(peak, x, y, maxima, minimalHeightThreshold,
                     defaultLimitPpm=defaultLimitPpm, maxLimitPpm=maxLimitPpm,
                     figOfMeritLimit=figOfMeritLimit, deltaFactor=0.1, retry=False,
                     )
    else:
        position = peak.position[0]
        height = float(_getClosestHeight(x, y, position, peak.height))
        heightError = 1
        # if 'STAY' not in peak.annotation:
        #     peak.annotation = f'{peak.annotation} -- STAY AT POS'
        peak.position = [position]
        peak.height = height
        peak.heightError = heightError
    return [position], height, heightError


def _find1DCoordsForPeaks(peaks,
                      rawDataDict=None,
                      ppmLimit=0.3,
                      figOfMeritLimit=0.5,
                      deltaFactor=0.5,
                      minimalHeightFactor=1.0):
    """
    :param peaks:
    :param rawDataDict:
    :param ppmLimit:
    :param additionalClusterPeakPpmLimit:  When auto-detecting a cluster, add a +/- ppm rangeLimits to the edges of a cluster region
    :param figOfMeritLimit:
    :param doNeg:
    :return: dict.
                        Keys: peak.
                        values: list of [ppmPosition, height, heightError]
    """
    ## peaks can be from different spectra, so let's group first
    snapped, unsnapped = [], []
    spectraPeaks = defaultdict(list)
    for _p in peaks:
        if _p.figureOfMerit >= figOfMeritLimit:
            spectraPeaks[_p.spectrum].append(_p)

    if rawDataDict is None:
        rawDataDict = _1DRawDataDict(list(spectraPeaks.keys()))

    ## Start the snapping routine
    for spectrum, grouppedPeaks in spectraPeaks.items():
        if spectrum not in rawDataDict:
            x,y = np.array(spectrum.positions), np.array(spectrum.intensities)
        else:
            x,y = rawDataDict.get(spectrum)

        ## peaks can be also different peakLists, so let's group first
        peaksByPeakList = defaultdict(list)
        for _p in grouppedPeaks:
                peaksByPeakList[_p.peakList].append(_p)

        ## Do a quick search of minimal height for a signal, the expected maxima, and calculate linewidths (pnts)
        minimalHeightThreshold = float(np.median(y) + minimalHeightFactor * np.std(y))
        mm, mx = _find1DPositiveMaxima(y, x, minimalHeightThreshold)
        positions = np.array(mm).T[0]
        heights = np.array(mm).T[1]
        for pl, subPeakGroup in peaksByPeakList.items():
            subPeakGroup = list(subPeakGroup)
            subPeakGroup.sort(key=lambda x: x.height, reverse=True)  #sort by the highest (first)
            for peak in subPeakGroup:
                _snap(peak, x=x, y=y,
                      maxima=[positions, heights],
                      minimalHeightThreshold=minimalHeightThreshold,
                      figOfMeritLimit=figOfMeritLimit,
                      defaultLimitPpm=ppmLimit,
                      deltaFactor=deltaFactor)
                if peak.heightError ==1:
                    unsnapped.append(peak)
                else:
                    snapped.append(peak)
    return snapped, unsnapped

































# ### NEW END =====

def _getSnappingPeakLimits(peak, otherPeaksPointPosition, deltaFactor = 0.5, defaultLimitPpm = 0.250, maxLimitPpm = 1.0):
    """
    :param peak:
    :param otherPeaksPointPosition:
    :param deltaFactor: smaller to be closer to the maximum limit
    :param defaultLimit:
    :param maxLimit:
    :return:
    """
    pointPositions = otherPeaksPointPosition
    ppmPerPoint = peak.spectrum.ppmPerPoints[0]
    defaultLimitPoints = defaultLimitPpm/ppmPerPoint
    maxLimitPoints = maxLimitPpm/ppmPerPoint
    queryPointPos = float(peak.pointPositions[0])

    right = pointPositions[pointPositions > queryPointPos] # upfield - more negative ppm Values
    left = pointPositions[pointPositions < queryPointPos]  # downfield - more positive ppm Values
    if len(left) == 0: # could be the last peak or the only one
        left = np.array([queryPointPos - defaultLimitPoints])
    if len(right) == 0:
        right = np.array([queryPointPos + defaultLimitPoints])

    closestLeft = left[np.argmin(abs(left - queryPointPos))]
    deltaLeft = closestLeft - queryPointPos
    leftLimit = closestLeft - (deltaLeft*deltaFactor) #use half delta to the nearest peak

    closestRight = right[np.argmin(abs(right) - queryPointPos)]
    deltaRight = closestRight - queryPointPos
    rightLimit = closestRight - (deltaRight * deltaFactor)

    if abs(deltaLeft) > maxLimitPoints:
        leftLimit = queryPointPos - (maxLimitPoints* deltaFactor)
    if abs(deltaRight) > maxLimitPoints:
        rightLimit = queryPointPos + (maxLimitPoints * deltaFactor)

    leftPpm = peak.spectrum.point2ppm(leftLimit, peak.spectrum.axisCodes[0])
    rightPpm = peak.spectrum.point2ppm(rightLimit, peak.spectrum.axisCodes[0])

    return leftPpm, rightPpm

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


def _getClosestHeight(x,y, pos, currentHeight):
    try:
        ax = x.reshape(len(x), 1)
        closestX = ax[spatial.KDTree(ax).query(pos)[1]]
        closestY = y[x==closestX]
        return float(closestY)
    except Exception as err:
        getLogger().warning('Could not find the closest', err)
    return float(currentHeight)

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
