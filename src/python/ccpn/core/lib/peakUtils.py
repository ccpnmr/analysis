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
__dateModified__ = "$dateModified: 2021-01-22 15:44:47 +0000 (Fri, January 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Union
import numpy as np
from ccpn.util.Logging import getLogger
from collections import OrderedDict
from scipy.optimize import curve_fit
from ccpn.core.PeakList import GAUSSIANMETHOD, PARABOLICMETHOD
from ccpn.util.Common import makeIterableList as mi
from ccpn.core.lib.ContextManagers import newObject, undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
import pandas as pd
from pandas import MultiIndex as m_ix
from ccpn.util.Common import makeIterableList


POSITIONS = 'positions'
HEIGHT = 'height'
VOLUME = 'volume'
LINEWIDTHS = 'lineWidths'
RAW = 'raw'
DELTAS = 'deltas'
DELTA = '\u0394'
Delta = '\u03B4'
MODES = [POSITIONS, HEIGHT, VOLUME, LINEWIDTHS]
DISPLAYDATA = [DELTA + Delta, RAW]
OTHER = 'Other'
H = 'H'
N = 'N'
C = 'C'
DefaultAtomWeights = OrderedDict(((H, 7.00), (N, 1.00), (C, 4.00), (OTHER, 1.00)))
NR_ID='NR_ID'

class Dictlist(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(Dictlist, self).__setitem__(key, [])
        self[key].append(value)


def getMultipletPosition(multiplet, dim, unit='ppm'):
    try:
        # skip if the position is None, otherwise check for dimensions
        if multiplet.position is None:
            return

        if multiplet.position[dim] is None:
            value = None  #"*NOT SET*"

        elif unit == 'ppm':
            value = multiplet.position[dim]

        #  NOT implemented for multiplets
        # elif unit == 'point':
        #   value = multiplet.pointPosition[dim]

        elif unit == 'Hz':
            value = multiplet.position[dim] * multiplet.multipletList.spectrum.spectrometerFrequencies[dim]

        else:  # sampled
            raise ValueError("Unit passed to getPeakPosition must be 'ppm', 'point', or 'Hz', was %s"
                             % unit)

        if not value:
            return

        if isinstance(value, (int, float, np.float32, np.float64)):
            return float(value)  # '{0:.2f}'.format(value)

    except Exception as e:
        getLogger().warning('Error on setting Position. %s' % e)


# return None

def getMultipletLinewidth(peak, dim):
    if dim < len(peak.lineWidths):
        lw = peak.lineWidths[dim]
        if lw:
            return float(lw)


def getPeakPosition(peak, dim, unit='ppm'):
    if len(peak.dimensionNmrAtoms) > dim:
        # peakDim = peak.position[dim]

        if peak.position[dim] is None:
            value = None  #"*NOT SET*"

        elif unit == 'ppm':
            value = peak.position[dim]

        elif unit == 'point':
            value = peak.pointPosition[dim]

        elif unit == 'Hz':
            value = peak.position[dim] * peak.peakList.spectrum.spectrometerFrequencies[dim]

        else:  # sampled
            raise ValueError("Unit passed to getPeakPosition must be 'ppm', 'point', or 'Hz', was %s"
                             % unit)

        if isinstance(value, (int, float, np.float32, np.float64)):
            return float(value)  # '{0:.4f}'.format(value)

        return None

        # if isinstance(value, [int, float]):
        # # if type(value) is int or type(value) in (float, float32, float64):
        #   return '%7.2f' % float(value)


def getPeakAnnotation(peak, dim, separator=', '):
    if len(peak.dimensionNmrAtoms) > dim:
        return separator.join([dna.pid.id for dna in peak.dimensionNmrAtoms[dim] if not (dna.isDeleted or dna._flaggedForDelete)])


def getPeakLinewidth(peak, dim):
    """Return the lineWidth in dimension 'dim' for the peakTable entries
    """
    lineWidths = peak.lineWidths
    if lineWidths and dim < len(lineWidths):
        lw = peak.lineWidths[dim]
        if lw is not None:
            return float(lw)

    # need to return this as a string otherwise the table changes between 'None' and 'nan'
    return 'None'


def _get1DPeaksPosAndHeightAsArray(peakList):
    import numpy as np

    positions = np.array([peak.position[0] for peak in peakList.peaks])
    heights = np.array([peak.height for peak in peakList.peaks])
    return [positions, heights]


import sys
from numpy import NaN, Inf, arange
from numba import jit


@jit(nopython=True, nogil=True)
def simple1DPeakPicker(y, x, delta, negDelta=None, negative=False):
    """
    from https://gist.github.com/endolith/250860#file-readme-md which was translated from
    http://billauer.co.il/peakdet.html Eli Billauer, 3.4.05.
    Explicitly not copyrighted and any uses allowed.
    """

    maxtab = []
    mintab = []
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN
    lookformax = True
    if negDelta is None: negDelta = 0

    for i in arange(len(y)):
        this = y[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        if lookformax:
            if not negative:  # just positives
                this = abs(this)
            if this < mx - delta:
                maxtab.append((float(mxpos), float(mx)))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn + delta:
                mintab.append((float(mnpos), float(mn)))
                mx = this
                mxpos = x[i]
                lookformax = True

    filteredNeg = []
    for p in mintab:
        pos, height = p
        if height <= negDelta:
            filteredNeg.append(p)
    filtered = []
    for p in maxtab:
        pos, height = p
        if height >= delta:
            filtered.append(p)

    return filtered, filteredNeg


def _estimateDeltaPeakDetect(y, xPercent=10):
    import numpy as np

    deltas = y[1:] - y[:-1]
    delta = np.std(np.absolute(deltas))
    # just on the noisy part of spectrum
    partialYpercent = (len(y) * xPercent) / 100
    partialY = y[:int(partialYpercent)]
    partialDeltas = partialY[1:] - partialY[:-1]
    partialDelta = np.std(np.absolute(partialDeltas))
    diff = abs(partialDelta + delta) / 2
    return delta


def _estimateDeltaPeakDetectSTD(y, xPercent=10):
    '''
    :param y: intensities of spectrum
    :param xPercent: the percentage of the spectra points to use as training to calculate delta.
    :return: a delta intesities of the required percentage of the spectra
    '''

    import numpy as np

    # just on the noisy part of spectrum
    partialYpercent = (len(y) * xPercent) / 100
    partialY = y[:int(partialYpercent)]
    partialDeltas = partialY[1:] - partialY[:-1]
    partialDelta = np.amax(np.absolute(partialDeltas))

    return partialDelta


def _pairIntersectionPoints(intersectionPoints):
    """ Yield successive pair chunks from list of intersectionPoints """
    for i in range(0, len(intersectionPoints), 2):
        pair = intersectionPoints[i:i + 2]
        if len(pair) == 2:
            yield pair


def _getIntersectionPoints(x, y, line):
    '''
    :param line: x points of line to intersect y points
    :return: list of intersecting points
    '''
    z = y - line
    dx = x[1:] - x[:-1]
    cross = np.sign(z[:-1] * z[1:])

    x_intersect = x[:-1] - dx / (z[1:] - z[:-1]) * z[:-1]
    negatives = np.where(cross < 0)
    points = x_intersect[negatives]

    return points


def _getAtomWeight(axisCode, atomWeights) -> float or int:
    '''

    :param axisCode: str of peak axis code
    :param atomWeights: dictionary of atomWeights eg {'H': 7.00, 'N': 1.00, 'C': 4.00, 'Other': 1.00}
    :return: float or int from dict atomWeights
    '''
    value = 1.0
    if len(axisCode) > 0:
        firstLetterAxisCode = axisCode[0]
        if firstLetterAxisCode in atomWeights:
            value = atomWeights[firstLetterAxisCode]
        else:
            if OTHER in atomWeights:
                if atomWeights[OTHER] != 1:
                    value = atomWeights[OTHER]
            else:
                value = 1.0

    return value


def _traverse(o, tree_types=(list, tuple)):
    '''used to flat the state in a long list '''
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in _traverse(value, tree_types):
                yield subvalue
    else:
        yield o


def _getPeaksForNmrResidueByNmrAtomNames(nmrResidue, nmrAtomsNames, spectra):
    peaks = []
    nmrAtoms = []

    peakLists = [sp.peakLists[-1] if len(sp.peakLists) > 0 else getLogger().warning('No PeakList for %s' % sp)
                 for sp in spectra]  # take only the last peakList if more then 1
    for nmrAtomName in nmrAtomsNames:
        nmrAtom = nmrResidue.getNmrAtom(str(nmrAtomName))
        if nmrAtom is not None:
            nmrAtoms.append(nmrAtom)
    filteredPeaks = []
    nmrAtomsNamesAvailable = []
    for nmrAtom in nmrAtoms:
        for peak in nmrAtom.assignedPeaks:
            if peak.peakList.spectrum in spectra:
                if nmrAtom.name in nmrAtomsNames:
                    if peak.peakList in peakLists:
                        filteredPeaks.append(peak)
                        nmrAtomsNamesAvailable.append(nmrAtom.name)

    if len(list(set(filteredPeaks))) == len(spectra):  # deals when a residue is assigned to multiple peaks
        if len(list(set(nmrAtomsNamesAvailable))) == len(nmrAtomsNames):
            peaks += filteredPeaks
    else:
        for peak in filteredPeaks:
            assignedNmrAtoms = _traverse(peak.assignedNmrAtoms)
            if all(assignedNmrAtoms):
                assignedNmrAtoms = [na.name for na in assignedNmrAtoms]
                if len(assignedNmrAtoms) > 1:
                    if list(assignedNmrAtoms) == nmrAtomsNames:
                        peaks += [peak]
                if len(nmrAtomsNames) == 1:
                    if nmrAtomsNames[0] in assignedNmrAtoms:
                        peaks += [peak]
    return list(OrderedDict.fromkeys(peaks))


def getNmrResiduePeakProperty(nmrResidue, nmrAtomsNames, spectra, theProperty='height'):
    '''

    :param nmrResidue:
    :param nmrAtomsNames: nmr Atoms to compare. str 'H', 'N', 'CA' etc
    :param spectra: compare peaks only from given spectra
    :param theProperty: 'height' or 'volume'
    :return:
    '''

    ll = []

    if len(spectra) <= 1:
        return
    if not theProperty in ['height', 'volume']:
        getLogger().warning('Property not currently available %s' % theProperty)
        return
    peaks = _getPeaksForNmrResidueByNmrAtomNames(nmrResidue, nmrAtomsNames, spectra)
    if len(peaks) > 0:
        for peak in peaks:
            if peak.peakList.spectrum in spectra:
                p = getattr(peak, theProperty)
                ll.append(p)
    return ll, peaks


def getNmrResiduePeakHeight(nmrResidue, nmrAtomsNames, spectra):
    '''
    :param nmrResidue:
    :param nmrAtomsNames: nmr Atoms to compare. str 'H', 'N', 'CA' etc
    :param spectra: compare peaks only from given spectra
    :return:
    '''
    getLogger().warning('Deprecated. Used getNmrResiduePeakProperty with theProperty = "height"')
    return getNmrResiduePeakProperty(nmrResidue, nmrAtomsNames, spectra, theProperty='height')


def getRawDataFrame(nmrResidues, nmrAtomsNames, spectra, theProperty):
    dfs = []
    names = [sp.name for sp in spectra]
    for nmrResidue in nmrResidues:
        if not '-' in nmrResidue.sequenceCode.replace('+', '-'):  # not consider the +1 and -1 residues
            ll = getNmrResiduePeakProperty(nmrResidue, nmrAtomsNames, spectra, theProperty)
            if len(ll) > 0:
                df = pd.DataFrame([ll], index=[nmrResidue.pid], columns=names)
                dfs.append(df)
    data = pd.concat(dfs)
    return data


def _getPeaksForNmrResidue(nmrResidue, nmrAtomsNames, spectra):
    if len(spectra) <= 1:
        return
    _peaks = _getPeaksForNmrResidueByNmrAtomNames(nmrResidue, nmrAtomsNames, spectra)
    usepeaks = []
    if len(_peaks) > 0:
        for peak in _peaks:
            if peak.peakList.spectrum in spectra:
                usepeaks.append(peak)
    return usepeaks


def getNmrResidueDeltas(nmrResidue, nmrAtomsNames, spectra, mode=POSITIONS, atomWeights=None):
    '''

    :param nmrResidue:
    :param nmrAtomsNames: nmr Atoms to compare. str 'H', 'N', 'CA' etc
    :param spectra: compare peaks only from given spectra
    :return:
    '''

    deltas = []

    if len(spectra) <= 1:
        return
    peaks = _getPeaksForNmrResidueByNmrAtomNames(nmrResidue, nmrAtomsNames, spectra)

    if atomWeights is None:
        atomWeights = DefaultAtomWeights

    if len(peaks) > 0:
        for peak in peaks:
            if peak.peakList.spectrum in spectra:
                # try:  #some None value can get in here
                if mode == POSITIONS:
                    deltaTemp = []
                    for i, axisCode in enumerate(peak.axisCodes):
                        if len(axisCode) > 0:
                            if any(s.startswith(axisCode[0]) for s in nmrAtomsNames):
                                weight = _getAtomWeight(axisCode, atomWeights)
                                if peaks[0] != peak:  # dont' compare to same peak
                                    delta = peak.position[i] - peaks[0].position[i]
                                    delta = delta ** 2
                                    delta = delta * weight
                                    deltaTemp.append(delta)
                                    # deltaInts.append(((peak.position[i] - list(peaks)[0].position[i]) * weight) ** 2)
                                    # delta += ((list(peaks)[0].position[i] - peak.position[i]) * weight) ** 2
                    if len(deltaTemp) > 0:
                        delta = sum(deltaTemp) ** 0.5
                        deltas += [delta]

                if mode == VOLUME:
                    if list(peaks)[0] != peak:  # dont' compare to same peak
                        if not peak.volume or not peaks[0].volume or peaks[0].volume == 0:
                            getLogger().warning('Volume has to be set for peaks: %s, %s' % (peak, peaks[0]))
                            break

                        delta1Atoms = (peak.volume / list(peaks)[0].volume)
                        deltas += [((delta1Atoms) ** 2) ** 0.5, ]

                if mode == HEIGHT:
                    if list(peaks)[0] != peak:  # dont' compare to same peak
                        if not peak.height or not peaks[0].height or peaks[0].height == 0:
                            getLogger().warning('Height has to be set for peaks: %s, %s' % (peak, peaks[0]))
                            break

                        delta1Atoms = (peak.height / list(peaks)[0].height)
                        deltas += [((delta1Atoms) ** 2) ** 0.5, ]

                if mode == LINEWIDTHS:
                    deltaTemp = []
                    for i, axisCode in enumerate(peak.axisCodes):
                        if list(peaks)[0] != peak:  # dont' compare to same peak
                            if axisCode:
                                if len(axisCode) > 0:
                                    if any(s.startswith(axisCode[0]) for s in nmrAtomsNames):
                                        weight = _getAtomWeight(axisCode, atomWeights)
                                        if not peak.lineWidths[i] or not peaks[0].lineWidths[i]:
                                            getLogger().warning('lineWidth has to be set for peaks: %s, %s' % (peak, peaks[0]))
                                            break
                                        delta = ((peak.lineWidths[i] - list(peaks)[0].lineWidths[i]) * weight) ** 2
                                        deltaTemp.append(delta)
                    if len(deltaTemp) > 0:
                        delta = sum(deltaTemp) ** 0.5
                        deltas += [delta]

            # except Exception as e:
            #     message = 'Error for calculation mode: %s on %s and %s. ' % (mode, peak.pid, list(peaks)[0].pid) + str(e)
            #     getLogger().debug(message)

    if deltas and not None in deltas:
        return round(float(np.mean(deltas)), 3)
    return


def _getKd(func, x, y):
    if len(x) <= 1:
        return
    try:
        param = curve_fit(func, x, y, maxfev=6000)
        bindingUnscaled, bmax = param[0]
        yScaled = y / bmax

        paramScaled = curve_fit(func, x, yScaled, maxfev=6000)
        kd, bmax = paramScaled[0]
    except Exception as err:
        getLogger().warning('Impossible to estimate Kd values. %s' % err)
        kd, bmax = [None, None]
    return kd


def oneSiteBindingCurve(x, kd, bmax):
    return (bmax * x) / (x + kd)


def exponenial_func(x, a, b):
    return a * np.exp(-b * x)


def _fit1SiteBindCurve(bindingCurves, aFunc=oneSiteBindingCurve, xfStep=0.01, xfPercent=30):
    """
    :param bindingCurves: DataFrame as: Columns -> float or int.
                                                  Used as xs points (e.g. concentration/time/etc value)
                                        rows    -> float or int.
                                                  Used as ys points (e.g. Deltadelta in ppm)
                                                  the actual curve points
                                        index   -> obj. E.g. nmrResidue obj. used as identifier for the curve origin

                                        | index          |    1   |   2   |
                                        |----------------+--------|-------|
                                        | obj1           |    1.0 |   1.1 |
                                        | obj2           |    2.0 |   1.2 |

    :param aFunc:  Default: oneSiteBindingCurve.
    :param xfStep: number of x points for generating the fitted curve.
    :param xfPercent: percent to add to max X value of the fitted curve, so to have a longer curve after the last
                    experimental value.

    :return: tuple of parameters for plotting fitted curves.
             x_atHalf_Y: the x value for half of Y. Used as estimated  kd
             xs: array of xs. Original xs points from the dataFrame columns
             yScaled: array of yScaled. Scaled to have values 0 to 1
             xf: array of x point for the new fitted curve. A range from 0 to max of xs.
             yf: array the fitted curve
    """
    from scipy.optimize import curve_fit
    from ccpn.util.Common import percentage

    errorValue = (None,) * 6
    if aFunc is None or not callable(aFunc):
        getLogger().warning("Error. Fitting curve %s is not callable" % aFunc)
        return errorValue
    if bindingCurves is None:
        getLogger().warning("Error. Binding curves not found")
        return errorValue

    data = bindingCurves.replace(np.nan, 0)
    ys = data.values.flatten(order='F')  #puts all y values in a single 1d array.
    xss = np.array([data.columns] * data.shape[0])
    xs = xss.flatten(order='F')  # #puts all x values in a 1d array preserving the original y positions (order='F').
    if len(xs) <= 1:
        return errorValue  #not enough datapoints
    try:
        param = curve_fit(aFunc, xs, ys)
        xhalfUnscaled, bMaxUnscaled = param[0]
        yScaled = ys / bMaxUnscaled  #scales y to have values 0-1
        paramScaled = curve_fit(aFunc, xs, yScaled)

        xfRange = np.max(xs) - np.min(xs)
        xfPerc = percentage(xfPercent, xfRange)
        xfMax = np.max(xs) + xfPerc
        xf = np.arange(0, xfMax, step=xfStep)
        yf = aFunc(xf, *paramScaled[0])
        x_atHalf_Y, bmax = paramScaled[0]
        return (x_atHalf_Y, bmax, xs, yScaled, xf, yf)
    except Exception as err:
        getLogger().warning('Impossible to estimate Kd value %s' % (err))
    return errorValue


def _fitExpDecayCurve(bindingCurves, aFunc=exponenial_func, xfStep=0.01, xfPercent=80, p0=(1, 0.1)):
    """
    :param TODO
    """

    from ccpn.util.Common import percentage

    errorValue = (None,) * 6
    if aFunc is None or not callable(aFunc):
        getLogger().warning("Error. Fitting curve %s is not callable" % aFunc)
        return errorValue
    if bindingCurves is None:
        getLogger().warning("Error. Binding curves not found")
        return errorValue

    data = bindingCurves.replace(np.nan, 0)
    ys = data.values.flatten(order='F')  #puts all y values in a single 1d array.
    xss = np.array([data.columns] * data.shape[0])
    xs = xss.flatten(order='F')  # #puts all x values in a 1d array preserving the original y positions (order='F').
    if len(xs) <= 1:
        return errorValue  #not enough datapoints
    # try:

    popt, pcov = curve_fit(aFunc, xs, ys, p0=p0)

    interc, slope = popt
    # yScaled = ys / interc  # scales y to have values 0-1
    # poptScaled, pcov  = curve_fit(aFunc, xs, yScaled)
    yScaled = (ys - np.min(ys)) / (np.max(ys) - np.min(ys))
    popt, pcov = curve_fit(exponenial_func, xs, yScaled, p0=popt)
    interc, slope = popt
    xfRange = np.max(xs) - np.min(xs)
    xfPerc = percentage(xfPercent, xfRange)
    xfMax = np.max(xs) + xfPerc
    xf = np.arange(0, xfMax, step=xfStep)
    yf = aFunc(xf, *popt)
    return (xs, yScaled, xf, yf, *popt)
    # except Exception as err:
    #     getLogger().warning('Impossible to estimate Kd value %s' % (err))
    # return errorValue


def snapToExtremum(peak: 'Peak', halfBoxSearchWidth: int = 3, halfBoxFitWidth: int = 3,
                   minDropFactor: float = 0.1, fitMethod: str = PARABOLICMETHOD,
                   searchBoxMode=False, searchBoxDoFit=False):
    """Snap the position of the peak the nearest extremum.
    Assumes called with an existing peak, will fit within a box ±halfBoxSearchWidth about the current peak position.
    """

    import math
    from ccpn.core.Peak import Peak
    from ccpnc.peak import Peak as CPeak
    from ccpn.framework.Application import getApplication

    getApp = getApplication()

    # error checking - that the peak is a valid peak
    peak = getApp.project.getByPid(peak) if isinstance(peak, str) else peak
    if not isinstance(peak, Peak):
        raise TypeError('%s is not of type Peak' % peak)

    apiPeak = peak._wrappedData

    dataSource = apiPeak.peakList.dataSource
    numDim = dataSource.numDim
    peakDims = apiPeak.sortedPeakDims()

    if numDim == 1:
        _snap1DPeakToClosestExtremum(peak, maximumLimit=0.1)
        return

    if searchBoxMode and numDim > 1:
        # NOTE:ED get the peakDim axisCode here and define the new half boxwidths based on the ValuePerPoint
        searchBoxWidths = getApp.preferences.general.searchBoxWidthsNd

        boxWidths = []
        axisCodes = peak.axisCodes
        for peakDim, axisCode in zip(peakDims, axisCodes):
            dataDim = peakDim.dataDim
            if hasattr(dataDim, 'primaryDataDimRef'):
                ddr = dataDim.primaryDataDimRef
                pointToValue = ddr and ddr.pointToValue
            else:
                pointToValue = dataDim.pointToValue

            letterAxisCode = (axisCode[0] if axisCode != 'intensity' else axisCode) if axisCode else None
            if letterAxisCode in searchBoxWidths:
                newWidth = math.floor(searchBoxWidths[letterAxisCode] / (2.0 * abs(pointToValue(1) - pointToValue(0))))
                boxWidths.append(max(1, newWidth))
            else:
                # default to the given parameter value
                boxWidths.append(max(1, halfBoxSearchWidth or 1))
    else:

        boxWidths = []
        axisCodes = peak.axisCodes
        for peakDim, axisCode in zip(peakDims, axisCodes):
            dataDim = peakDim.dataDim
            if dataDim.className == 'FreqDataDim':

                peakBoxWidth = peakDim.boxWidth or 1
                halfBoxWidth = dataDim.numPoints / 100  # a bit of a hack copied from V2
                boxWidths.append(max(halfBoxWidth, 1, int(peakBoxWidth / 2)))

                # from V2 - seems to give individual boxWidths per peak
                # boxWidth = peakDim.boxWidth
                # if not boxWidth:  # if None (or even if 0)
                #     boxWidth = getPeakFindBoxwidth(dataDim)
                # halfBoxWidth = dataDim.numPoints / 100  # a bit of a hack
                # halfBoxWidth = max(halfBoxWidth, 1, int(boxWidth / 2))
                # first[i] = max(0, int(math.floor(position[i] - halfBoxWidth)))
                # last[i] = min(dataDim.numPoints, int(math.ceil(position[i] + 1 + halfBoxWidth)))
                # buff[i] = buf
            else:

                # NOTE:ED - check this with v2
                boxWidths.append(max(1, halfBoxSearchWidth or 1))

                # first[i] = max(0, int(math.floor(position[i] + 0.5)))
                # last[i] = min(dataDim.numPoints, first[i] + 1)
                # buff[i] = 0

    # add the new boxWidths array as np.int32 type
    boxWidths = np.array(boxWidths, dtype=np.int32)

    # get the height - remember not to use (position-1) because function does that
    height = dataSource.getPositionValue([peakDim.position for peakDim in peakDims])

    # generate a np array with the position of the peak in points rounded to integers
    position = [peakDim.position - 1 for peakDim in peakDims]  # API position starts at 1

    # round up/down the position
    pLower = np.floor(position).astype(np.int32)
    pUpper = np.ceil(position).astype(np.int32)
    position = np.round(position)

    # generate a np array with the number of points per dimension
    # numPoints = [peakDim.dataDim.numPoints for peakDim in peakDims]
    numPoints = np.array([peakDim.dataDim.numPoints for peakDim in peakDims], dtype=np.int32)

    # extra plane in each direction increases accuracy of group fitting
    # startPoint = np.maximum(pLower - halfBoxSearchWidth, 0)
    # endPoint = np.minimum(pUpper + halfBoxSearchWidth, numPoints)
    startPoint = np.maximum(pLower - boxWidths, 0)
    endPoint = np.minimum(pUpper + boxWidths, numPoints)

    # map to co-ordinates to a (0,0) cornered box
    regionArray = np.array((startPoint - startPoint, endPoint - startPoint), dtype=np.int32)

    # Get the data; note that arguments have to be cast to int32s/float32s for the C routines
    dataArray, intRegion = dataSource.getRegionData(startPoint, endPoint)

    if not (dataArray is not None and dataArray.size != 0):
        getLogger().warning('no region found')
        return

    scaledHeight = 0.5 * height  # this is so that have sensible pos/negLevel
    if height > 0:
        doPos = True
        doNeg = False
        posLevel = scaledHeight
        negLevel = 0  # arbitrary - not necessary
    else:
        doPos = False
        doNeg = True
        posLevel = 0  # arbitrary - not necessary
        negLevel = scaledHeight

    exclusionBuffer = [1] * numDim

    nonAdj = 0
    minLinewidth = [0.0] * numDim

    excludedRegionsList = []
    excludedDiagonalDimsList = []
    excludedDiagonalTransformList = []

    peakPoints = CPeak.findPeaks(dataArray, doNeg, doPos,
                                 negLevel, posLevel, exclusionBuffer,
                                 nonAdj, minDropFactor, minLinewidth,
                                 excludedRegionsList, excludedDiagonalDimsList, excludedDiagonalTransformList)

    if not peakPoints:
        getLogger().warning('no points found')
        return

    # catch any C errors
    try:

        # find the closest peak in the found list
        bestHeight = bestDist = peakPoint = None
        bestFit = 0.0
        for findNextPeak in peakPoints:

            # find the highest peak to start from
            peakHeight = findNextPeak[1]
            peakDist = np.linalg.norm((np.array(findNextPeak[0]) - boxWidths) / boxWidths)
            peakFit = abs(peakHeight / (1.0 + peakDist))

            if height == None or peakFit > bestFit:
                bestFit = peakFit
                bestHeight = abs(peakHeight)
                bestDist = peakDist
                peakPoint = findNextPeak[0]

        # use this as the centre for the peak fitting
        peakPoint = np.array(peakPoint)
        peakArray = peakPoint.reshape((1, numDim))
        peakArray = peakArray.astype(np.float32)

        if searchBoxDoFit:
            if fitMethod == PARABOLICMETHOD:
                # parabolic - generate all peaks in one operation
                result = CPeak.fitParabolicPeaks(dataArray, regionArray, peakArray)

            else:
                method = 0 if fitMethod == GAUSSIANMETHOD else 1

                # use the halfBoxFitWidth to give a close fit
                firstArray = np.maximum(peakArray[0] - halfBoxFitWidth, regionArray[0])
                lastArray = np.minimum(peakArray[0] + halfBoxFitWidth + 1, regionArray[1])
                regionArray = np.array((firstArray, lastArray), dtype=np.int32)

                # fit the single peak
                result = CPeak.fitPeaks(dataArray, regionArray, peakArray, method)
        else:
            # take the maxima
            result = ((bestHeight, peakPoint, None),)

    except CPeak.error as e:
        # there could be some fitting error
        getLogger().warning("Aborting peak fit, Error for peak: %s" % peak)
        return

    # if any results are found then set the new peak position/height
    if result:
        height, center, linewidth = result[0]

        # work on the _wrappedData
        apiPeak = peak._wrappedData
        peakDims = apiPeak.sortedPeakDims()

        dataSource = apiPeak.peakList.dataSource
        dataDims = dataSource.sortedDataDims()

        for i, peakDim in enumerate(peakDims):
            newPos = min(max(center[i], 0.5), dataArray.shape[i] - 1.5)

            # NOTE:ED - ignore if out of range - might not need any more
            dist = abs(newPos - center[i])
            if dist < boxWidths[i]:
                peakDim.position = center[i] + startPoint[i] + 1.0  # API position starts at 1
            if linewidth and len(linewidth) > i:
                peakDim.lineWidth = dataDims[i].valuePerPoint * linewidth[i]

        if searchBoxDoFit:
            # apiPeak.height = dataSource.scale * height
            apiPeak.height = height
        else:
            # get the interpolated height
            peak.height = peak.peakList.spectrum.getHeight(peak.ppmPositions)


def getSpectrumData(peak: 'Peak', halfBoxWidth: int = 3):
    """Get a region of the spectrum data centred on the peak.
    Will return the smallest region containing the peak ±halfBoxWidth about the current peak position.

    returns a tuple of the form (dataArray, region, position, planePosition)

        dataArray is the numpy array surrounding the peak, ordered by spectrum axisCodes
        region is a tuple (bottomLeft, topRight)
        position is the float32 relative position of the peak in dataArray
        planePosition is the int32 position of the nearest planes to the peak

    where bottomLeft is the co-ordinates of the bottom-left corner of the region
            topRight is the co-ordinates of the top-right corner of the region

            Co-ordinates are indexed from (0, 0)

            Note: screen point co-ordinates are indexed from (1, 1)

    The region will be cropped to the bounds of the spectrum, in which case position will not correspond to the centre
    if no region is found, returns None
    """

    from ccpn.core.Peak import Peak
    from ccpn.framework.Application import getApplication

    # error checking - that the peak is a valid peak
    peak = getApplication().project.getByPid(peak) if isinstance(peak, str) else peak
    if not isinstance(peak, Peak):
        raise TypeError('%s is not of type Peak' % peak)

    apiPeak = peak._wrappedData

    dataSource = apiPeak.peakList.dataSource
    peakDims = apiPeak.sortedPeakDims()

    # generate a np array with the position of the peak in points rounded to integers
    position = [peakDim.position - 1 for peakDim in peakDims]  # API position starts at 1

    # round up/down the position to give the square containing the peak
    pLower = np.floor(position).astype(np.int32)
    pUpper = np.ceil(position).astype(np.int32)
    position = np.array(position, dtype=np.float32)

    # generate a np array with the number of points per dimension
    # numPoints = [peakDim.dataDim.numPoints for peakDim in peakDims]
    numPoints = np.array([peakDim.dataDim.numPoints for peakDim in peakDims], dtype=np.int32)

    # add extra points in each direction
    startPoint = np.maximum(pLower - halfBoxWidth, 0)
    endPoint = np.minimum(pUpper + halfBoxWidth, numPoints)

    # Get the data; note that arguments has to be cast to ints for the C routines
    dataArray, intRegion = dataSource.getRegionData(startPoint, endPoint)

    if not (dataArray is not None and dataArray.size != 0):
        getLogger().warning('no region found')
        return

    return (dataArray, intRegion, list(position - startPoint), list(np.round(position).astype(np.int32)))


def estimateVolumes(peaks: Sequence[Union[str, 'Peak']], volumeIntegralLimit=2.0):
    """Estimate the volumes for the peaks
    :param peaks: list of peaks as pids or strings
    :param volumeIntegralLimit: integral width as a multiple of lineWidth (FWHM)
    """
    # move to peakList

    from ccpn.core.Peak import Peak
    from ccpn.framework.Application import getApplication

    if not getApplication() and not getApplication().project:
        raise RuntimeError('There is no project')

    getByPid = getApplication().project.getByPid

    # error checking - that the peaks are valid
    peakList = makeIterableList(peaks)
    pks = [getByPid(peak) if isinstance(peak, str) else peak for peak in peakList]

    for pp in pks:
        if not isinstance(pp, Peak):
            raise TypeError('%s is not of type Peak' % str(pp))

    # estimate the volume for each peak
    for pp in pks:
        height = pp.height
        lineWidths = pp.lineWidths
        if lineWidths and None not in lineWidths and height:
            pp.estimateVolume(volumeIntegralLimit=volumeIntegralLimit)
        else:
            getLogger().warning('Peak %s contains undefined height/lineWidths' % str(pp))


def _findPeakHeight(peak):
    """may need this later
    """
    spectrum = peak.peakList.spectrum
    numDim = spectrum.dimensionCount

    exclusionBuffer = [1] * numDim
    valuesPerPoint = spectrum.valuesPerPoint
    regionToPick = dict((code, (pos-value/2, pos+value/2)) for code, pos, value in zip(spectrum.axisCodes, peak.position, valuesPerPoint))

    foundRegions = spectrum.getRegionData(exclusionBuffer, minimumDimensionSize=0, **regionToPick)

    if not foundRegions:
        return

    for region in foundRegions:
        if not region:
            continue

        dataArray, intRegion, \
        startPoints, endPoints, \
        startPointBufferActual, endPointBufferActual, \
        startPointIntActual, numPointInt, \
        startPointBuffer, endPointBuffer = region

        if dataArray.size:
            print('>>> here', regionToPick, dataArray)
            # now do a fit at this position


def movePeak(peak, ppmPositions, updateHeight=True):
    """Move a peak based on it's delta shift and opionally update to the height at the new position
    """
    with undoBlock():
        peak.position = ppmPositions

        if updateHeight:
            # get the interpolated height at this position
            if peak.peakList.spectrum.dimensionCount == 1:
                peak.height = peak.peakList.spectrum.getIntensity(ppmPositions[:1])
            else:
                peak.height = peak.peakList.spectrum.getHeight(ppmPositions)

def updateHeight(peak):
    with undoBlock():
        if peak.peakList.spectrum.dimensionCount == 1:
            peak.height = peak.peakList.spectrum.getIntensity(peak.position[:1])
        else:
            peak.height = peak.peakList.spectrum.getHeight(peak.position)

# added for pipelines


def _1Dregions(x,y, value, lim=0.01):
    # centre of position, peak position
    # lim in ppm where to look left and right
    referenceRegion = [value - lim, value + lim]
    point1, point2 = np.max(referenceRegion), np.min(referenceRegion)
    x_filtered = np.where((x <= point1) & (x >= point2))  # only the region of interest for the reference spectrum
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered

def _1DregionsFromLimits(x,y, limits):
    # centre of position, peak position
    # lim in ppm where to look left and right

    point1, point2 = np.max(limits), np.min(limits)
    x_filtered = np.where((x <= point1) & (x >= point2))  # only the region of interest for the reference spectrum
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered

def _snap1DPeaksToExtremaSimple(peaks, limit=0.003):

    for peak in peaks: # peaks can be from diff peakLists
        if peak is not None:
            x = peak.peakList.spectrum.positions
            y = peak.peakList.spectrum.intensities
            x_filtered, y_filtered = _1Dregions(x,y, peak.position[0], lim=limit)
            if len(y_filtered)>0:
                idx = y_filtered.argmax()
                peakHeight = y_filtered[idx]
                peakPos = x[x_filtered[0][idx]] # ppm positions
                peak.height = float(peakHeight)
                peak.position = [float(peakPos),]

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def snap1DPeaksToExtrema(peaks, maximumLimit=0.1, figOfMeritLimit=1,):
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            if len(peaks) > 0:
                peaks.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
                for peak in peaks:  # peaks can be from diff peakLists
                    if peak is not None:
                        _snap1DPeakToClosestExtremum(peak, maximumLimit=maximumLimit,
                                                         figOfMeritLimit=figOfMeritLimit)



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
    # import matplotlib.pyplot as plt  # to plot
    # plt.hist(y, bins=int(len(y)/2), density=True)
    # plt.plot(edges, fittedCurve, linewidth=2, color='r')
    # plt.show()
    """
    from scipy.stats import binned_statistic
    binCount = binCount or int(len(y)/2)
    statistics, edges, binNumbers = binned_statistic(y, y, bins=binCount, statistic='mean')
    mostCommonBinNumber = np.argmax(np.bincount(binNumbers))
    highestValues = y[binNumbers==mostCommonBinNumber] # values corresponding to most frequent binNumber
    fittedCurve = _fitBins(y, edges)
    fittedCurveExtremum = edges[np.argmax(fittedCurve)] # value at the Extremum of the fitted curve
    return statistics, edges, binNumbers, fittedCurve, mostCommonBinNumber, highestValues, fittedCurveExtremum


def snap1DPeaksAndRereferenceSpectrum(peaks, maximumLimit=0.1, useAdjacientPeaksAsLimits=False,
                                    doNeg=True, figOfMeritLimit=1):

    spectrum = peaks[0].peakList.spectrum
    peaks.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
    oPositions, oHeights = [x.position for x in peaks], [x.height for x in peaks]
    nPositions, nHeights = [], []
    for peak in peaks:
        if peak is not None:
            position, height = _get1DClosestExtremum(peak, maximumLimit=maximumLimit,
                                                     useAdjacientPeaksAsLimits=useAdjacientPeaksAsLimits, doNeg=doNeg,
                                                     figOfMeritLimit=figOfMeritLimit)
            nPositions.append(position)
            nHeights.append(height)
    deltas = np.array(nPositions) - np.array(oPositions)
    deltas = deltas.flatten()
    stats, edges, binNumbers, fittedCurve, mostCommonBinNumber, highestValues, fittedCurveExtremum = _getBins(deltas)
    shift = max(highestValues)
    spectrum.referenceValues = [spectrum.referenceValues[0] - shift]
    spectrum.positions = spectrum.positions - shift
    for peak in peaks:
        if peak is not None:
            peak.position = [peak.position[0] + shift,]
            position, height = _get1DClosestExtremum(peak, maximumLimit=maximumLimit,
                                                     useAdjacientPeaksAsLimits=useAdjacientPeaksAsLimits, doNeg=doNeg,
                                                     figOfMeritLimit=figOfMeritLimit)
            peak.position = position
            peak.height = height
    return shift

# def add(x,y):
#     if y > 0:
#         return add(x, y-1) + 1
#     elif y < 0:
#         return add(x, y+1) - 1
#     else:
#         return x
#
# def sub(x,y):
#     if y > 0:
#         return sub(x, y-1) - 1
#     elif y < 0:
#         return sub(x, y+1) + 1
#     else:
#         return x

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
    if idx == tot-1:
        next = False
    if previous:
        previousPeakPosition = positions[positions.index(queryPos) - 1]
    if next:
        nextPeakPosition = positions[positions.index(queryPos) + 1]
    return previousPeakPosition, nextPeakPosition

# def _snap1DPeaksToBestFitExtrema(peaks, maximumLimit=0.1, doNeg=True):
#     UNDER implementation
#     from ccpn.core.lib.SpectrumLib import estimateNoiseLevel1D
#     from ccpn.util.Logging import getLogger
#     if not peaks: return
#     peak = peaks[-1]
#     if len(peaks) == 1:
#         _snap1DPeakToClosestExtremum(peak, maximumLimit=maximumLimit, doNeg=doNeg)
#         return
#     spectrum = peak.peakList.spectrum
#     if not all([peak.peakList.spectrum == spectrum for peak in peaks]):
#         getLogger().info('All peaks must be from same spectrum')
#         return
#     x = spectrum.positions
#     y = spectrum.intensities
#
#     #adjaciant peaks to first and last in group
#     a1, b1 = _getAdjacentPeakPositions1D(peaks[0])
#     a2, b2 = _getAdjacentPeakPositions1D(peaks[-1])
#     print(a1, b1, a2,b2, 'ADJUST')
#
#     if not a1:
#         a =  sub(peak.position[0], maximumLimit)
#     if not b2:
#         b = add(peak.position[0], maximumLimit)
#
#     noiseLevel, minNoiseLevel = spectrum.noiseLevel, spectrum.negativeNoiseLevel
#     if not noiseLevel: #estimate as you can from the spectrum
#         spectrum.noiseLevel, spectrum.negativeNoiseLevel =  noiseLevel, minNoiseLevel = estimateNoiseLevel1D(y)
#

def _get1DClosestExtremum(peak, maximumLimit=0.1, useAdjacientPeaksAsLimits=False, doNeg=True, figOfMeritLimit=1):
    from ccpn.core.lib.SpectrumLib import estimateNoiseLevel1D
    from ccpn.util.Logging import getLogger
    spectrum = peak.peakList.spectrum
    x = spectrum.positions
    y = spectrum.intensities
    position, height  = peak.position, peak.height

    if peak.figureOfMerit < figOfMeritLimit:
        height = peak.peakList.spectrum.getIntensity(peak.position)
        return position, height

    if useAdjacientPeaksAsLimits: #  a left # b right limit
        a, b = _getAdjacentPeakPositions1D(peak)
        if not a: # could not find adjacient peaks if the snapping peak is the first or last
            if peak.position[0] > 0: #it's positive
                a = peak.position[0] - maximumLimit
            else:
                a = peak.position[0] + maximumLimit
        if not b:
            if peak.position[0] > 0: # it's positive
                b = peak.position[0] + maximumLimit
            else:
                b = peak.position[0] - maximumLimit
    else:
        a, b = peak.position[0] - maximumLimit, peak.position[0] + maximumLimit

    # refind maxima
    noiseLevel = spectrum.noiseLevel
    minNoiseLevel = spectrum.negativeNoiseLevel
    if not noiseLevel:  # estimate as you can from the spectrum
        # noiseLevel, minNoiseLevel = estimateNoiseLevel1D(y)
        spectrum.noiseLevel, spectrum.negativeNoiseLevel = noiseLevel, minNoiseLevel = estimateNoiseLevel1D(y)

    x_filtered, y_filtered = _1DregionsFromLimits(x, y, [a, b])
    maxValues, minValues = simple1DPeakPicker(y_filtered, x_filtered, noiseLevel, negDelta=minNoiseLevel,
                                              negative=doNeg)
    allValues = maxValues + minValues

    if len(allValues) > 0:
        allValues = np.array(allValues)
        positions = allValues[:, 0]
        heights = allValues[:, 1]
        nearestPosition = find_nearest(positions, peak.position[0])
        nearestHeight = heights[positions == nearestPosition]
        if useAdjacientPeaksAsLimits:
            if a == nearestPosition or b == nearestPosition:  # avoid snapping to an existing peak, as it might be a wrong snap.
                height = peak.peakList.spectrum.getIntensity(peak.position)
            # elif abs(nearestPosition) > abs(peak.position[0] + maximumLimit):  # avoid snapping on the noise if not maximum found
            #
            #     # peak.height = peak.peakList.spectrum.getIntensity(peak.position)
            #     print('#####', peak.pid,)
            #     print('nearestPosition', nearestPosition, 'abs(peak.position[0] + maximumLimit)', abs(peak.position[0] + maximumLimit))
            else:
                position = [float(nearestPosition), ]
                height = nearestHeight[0]
        else:
            position = [float(nearestPosition), ]
            height = nearestHeight[0]

    else:
        height = peak.peakList.spectrum.getIntensity(peak.position)

    return position, height

def _snap1DPeakToClosestExtremum(peak, maximumLimit=0.1, doNeg=True, figOfMeritLimit=1):
    '''
    It snaps a peak to its closest extremum, that can be considered as a peak.
    it uses adjacent peak positions as boundaries. However if no adjacent peaks then uses the maximumlimits.
    Uses peak
    :param peak: obj peak
    :param maximumLimit: maximum tolerance left or right from the peak position (ppm)
    '''
    position, height = _get1DClosestExtremum(peak, maximumLimit, doNeg=doNeg, figOfMeritLimit=figOfMeritLimit)
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            peak.position = position
            peak.height = height

def getSpectralPeakHeights(spectra, peakListIndexes:list=None) -> pd.DataFrame:
    return _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=HEIGHT, peakListIndexes=peakListIndexes)

def getSpectralPeakVolumes(spectra, peakListIndexes:list=None) -> pd.DataFrame:
    return _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=VOLUME, peakListIndexes=peakListIndexes)

def getSpectralPeakHeightForNmrResidue(spectra, peakListIndexes:list=None) -> pd.DataFrame:
    '''
    return: Pandas DataFrame with the following structure:
            Index:  ID for the nmrResidue(s) assigned to the peak ;
            Columns => Spectrum series values sorted by ascending values, if series values are not set, then the
                       spectrum name is used instead.

                   |   SP1     |    SP2    |   SP3
        NR_ID      |           |           |
       ------------+-----------+-----------+----------
        A.1.ARG    |    10     |  100      | 1000

        '''
    df = getSpectralPeakHeights(spectra, peakListIndexes)
    newDf = df[df[NR_ID] != ''] # remove rows if NR_ID is not defined
    newDf = newDf.reset_index(drop=True).groupby(NR_ID).max()
    return newDf

def _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=HEIGHT, NR_ID=NR_ID, peakListIndexes:list=None):
    '''
    :param spectra: list of spectra
    :param peakProperty: 'height'or'volume'
    :param NR_ID: columnName for the NmrResidue ID
    :param peakListIndex: list of peakList indexes for getting the right peakList from the given spectra,
                         default: the last peakList available
    :return: Pandas DataFrame with the following structure:
            Index: multiIndex => axisCodes as levels;
            Columns => NR_ID: the nmrResidue(s) assigned for the peak if available
                       Spectrum series values sorted by ascending values, if series values are not set, then the
                       spectrum name is used instead.

                    |  NR_ID  |   SP1     |    SP2    |   SP3
        H     N     |         |           |           |
       -------------+-------- +-----------+-----------+---------
        7.5  104.3  | A.1.ARG |    10    |  100       | 1000

    to sort the dataframe by an axisCode, eg 'H' use:
    df = df.sort_index(level='H')
    '''
    dfs = []
    if peakListIndexes is None: peakListIndexes = [-1]*len(spectra)
    for spectrum, ix in zip(spectra, peakListIndexes):
        positions = []
        values = []
        nmrResidues = []
        serieValue = spectrum.name # use spectrumName as default. if series defined use that instead.
        if len(spectrum.spectrumGroups)>0:
            sGserieValue = spectrum._getSeriesItem(spectrum.spectrumGroups[-1])
            if sGserieValue is not None:
                serieValue = sGserieValue
        peaks = spectrum.peakLists[ix].peaks
        peaks.sort(key=lambda x: x.position, reverse=True)
        for peak in peaks:
            positions.append(peak.position)
            values.append(getattr(peak, peakProperty, None))
            assignedResidues = list(set(filter(None, map(lambda x: x.nmrResidue.id, mi(peak.assignments)))))
            nmrResidues.append(", ".join(assignedResidues))
        _df = pd.DataFrame(values, columns=[serieValue], index=m_ix.from_tuples(positions, names=spectrum.axisCodes))
        _df[NR_ID] = nmrResidues
        _df = _df[~_df.index.duplicated()]
        dfs.append(_df)
    df = pd.concat(dfs, axis=1, levels=0)
    df[NR_ID] = df.T[df.columns.values == NR_ID].apply(lambda x:' '.join(set([item for item in x[x.notnull()]])))
    df = df.loc[:, ~df.columns.duplicated()]
    cols = list(df.columns)
    resColumn = cols.pop(cols.index(NR_ID))
    sortedCols = sorted(cols, reverse=False)
    sortedCols.insert(0, resColumn)
    return df[sortedCols]


def _getPeakSNRatio(peak, factor=2.5):
    """
    Estimate the Signal to Noise ratio based on the spectrum Positive and Negative noise values.
    If Noise thresholds are not defined in the spectrum, then they are estimated as well.
    If only the positive noise threshold is defined, the negative noise threshold will be the inverse of the positive.
        SNratio = |factor*(height/|NoiseMax-NoiseMin|)|
                height is the peak height
                NoiseMax is the spectrum positive noise threshold
                NoiseMin is the spectrum negative noise threshold
    :param factor: float, multiplication factor.
    :return: float, SignalToNoise Ratio value for the peak
    """
    spectrum = peak._parent.spectrum
    from ccpn.core.lib.SpectrumLib import estimateNoiseLevel1D
    from ccpn.core.lib.SpectrumLib import estimateSNR
    noiseLevel, negativeNoiseLevel = spectrum.noiseLevel, spectrum.negativeNoiseLevel
    if negativeNoiseLevel is None and noiseLevel is not None:
        negativeNoiseLevel = - noiseLevel if noiseLevel >0 else noiseLevel*2
        spectrum.negativeNoiseLevel = negativeNoiseLevel
        getLogger().warning('Spectrum Negative noise not defined for %s. Estimated default' % spectrum.pid)
    if noiseLevel is None: # estimate it
        if spectrum.dimensionCount == 1:
            noiseLevel, negativeNoiseLevel = estimateNoiseLevel1D(spectrum.intensities)
            spectrum.noiseLevel, spectrum.negativeNoiseLevel = noiseLevel, negativeNoiseLevel
            getLogger().warning('Spectrum noise level(s) not defined for %s. Estimated default' % spectrum.pid)
        else:
            getLogger().warning('Not implemented yet')
            return None
    if peak.height is None:
        updateHeight(peak)
        _getPeakSNRatio(peak)
    snr = estimateSNR(noiseLevels=[noiseLevel, negativeNoiseLevel], signalPoints=[peak.height], factor=factor)
    return snr[0] ## estimateSNR return a list with a lenght always > 0
