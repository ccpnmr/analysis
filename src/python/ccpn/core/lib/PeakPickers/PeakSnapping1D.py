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
__dateModified__ = "$dateModified: 2023-11-22 14:41:53 +0000 (Wed, November 22, 2023) $"
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
from scipy import spatial, signal



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
        positiveContourBase = spectrum.positiveContourBase
        negativeContourBase = spectrum.negativeContourBase
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
                maxValues, minValues = _find1DMaxima(yROItarget, xROItarget, positiveThreshold=positiveContourBase,
                                                     negativeThreshold=negativeContourBase, findNegative=doNeg)
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

def _onePhaseDecayPlateau_func(x, rate=1.0, amplitude=1.0, plateau=0.0):
    """
    Duplicated function from series Analysis. Import from fitting models
    """
    result = (amplitude - plateau) * np.exp(-rate * x) + plateau
    return result

def _getMaximaForRegion(y, x, minimalHeightThreshold, neededMaxima, initialWindowSize=500, totWindowSizeSteps=1000):
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


def _get1DClosestExtremum(peak, maximumLimit=0.1,  doNeg=False,
                          figOfMeritLimit=1, initialWindowSize=100, rawDataDict=None ):
    """

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

    rounding = 4
    a, b = peak._temporaryPosition[0] - maximumLimit, peak._temporaryPosition[0] + maximumLimit
    knownPositions = np.array([p._temporaryPosition[0] for p in peak.peakList.peaks if p is not peak])
    limits = np.array([a, b])
    queryPos = peak.position[0]
    knownPositions = np.concatenate([knownPositions, limits])
    left = knownPositions[knownPositions > queryPos]
    right = knownPositions[knownPositions < queryPos]
    closestLeft = left[np.argmin(left - queryPos)]
    closestRight = right[np.argmin(abs(right) - queryPos)]

    minimalHeightThreshold = float(np.median(y) + 0.5 * np.std(y))
    x_filtered, y_filtered = _1DregionsFromLimits(x, y, [closestLeft, closestRight])
    regionSize = len(y_filtered)
    maximaIndices, _ = signal.find_peaks(y, height=minimalHeightThreshold)
    maximaHalf = signal.peak_widths(y, maximaIndices, rel_height=0.5)[0]
    if len(maximaHalf) > 0:
        initialWindowSize = np.max(maximaHalf) * 2
    else:
        initialWindowSize = regionSize/2 if regionSize > 100 else 100  # don't make the initial Window too huge
    coords = _getMaximaForRegion(y_filtered, x_filtered,  minimalHeightThreshold=minimalHeightThreshold, neededMaxima=1, initialWindowSize=initialWindowSize, totWindowSizeSteps=1000)
    heightAtQuery = _getClosestHeight(x, y, queryPos, peak.height)
    if len(coords) > 0:
        coord = coords[0]
        existing = np.array([round(p._temporaryPosition[0], rounding) for p in peak.peakList.peaks])
        heights = np.array([coord[1], float(heightAtQuery)])
        if round(coord[0], rounding) in existing:
            print('cannot snap here. Already one peak here', coord[0], 'THERE:', existing)
            return [queryPos], heightAtQuery, 1
        elif (heights < minimalHeightThreshold).all(): #both the knew found value and the original are in the noise. so just keep at position
            print('Found in noise .No Point snapping. ')
            return [queryPos], heightAtQuery, 1
        else:
            return [coord[0]], coord[1], None
    else:
        return [queryPos], heightAtQuery, 1



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



def _filterShouldersFromNewMaxima(newMaxima, x,y, proximityTollerance=1e5 ):
    """Remove a positions from the newly found maxima to avoid snapping to a shoulder peak (not the real maximum)"""
    for maximum in newMaxima:
        pos, intens = maximum
        if intens ==  y[0] or intens == [-1]:
            newMaxima.remove(maximum)

    return newMaxima


def _snapPeaksByGroup(peaks, rawDataDict=None, ppmLimit=0.3,
                      autoClusterPeaks = True,
                      additionalClusterPeakPpmLimit=0.1,
                      figOfMeritLimit=1, doNeg=False):
    """

    :param peaks:
    :param rawDataDict:
    :param ppmLimit:
    :param additionalClusterPeakPpmLimit:  When detecting a cluster, add an additional +- limits to the edges of a cluster region
    :param figOfMeritLimit:
    :param doNeg:
    :return:
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
                    # otherPeaks = [round(p.position[0],rounding) for p in peakGroup[0].peakList.peaks if p not in peakGroup if p.position[0] if _isWithinLimits(p.position[0], searchingLimits)]
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
                            position = [coord[0], ]
                            height = float(coord[1])
                            error = 0
                            results[peak] = [position, float(height), error]
                    else:
                        ## found different count of new coords and peaks.
                        print('found different count of new coords and peaks.', foundCoords)
                        for peak in peakGroup:
                            _snapPeaksByGroup([peak], ppmLimit=ppmLimit, rawDataDict=rawDataDict)

    return results
