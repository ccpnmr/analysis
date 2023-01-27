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
__dateModified__ = "$dateModified: 2023-01-27 16:30:59 +0000 (Fri, January 27, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from pandas import MultiIndex as m_ix
from typing import Sequence, Union
from scipy.spatial.distance import cdist
from collections import defaultdict
from scipy.optimize import linear_sum_assignment
from scipy.optimize import curve_fit
from collections import OrderedDict
from ccpn.util.Logging import getLogger
from ccpn.core.PeakList import GAUSSIANMETHOD, PARABOLICMETHOD
from ccpn.core.lib.ContextManagers import newObject, undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util.Common import makeIterableList, percentage
from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima


# This variables will be moved to SeriesAnalysisVariables.py
_POSITION = 'position'
_POINTPOSITION = 'pointPosition'
_PPMPOSITION = 'ppmPosition'
_LINEWIDTH = 'lineWidth'
HEIGHT = 'height'
VOLUME = 'volume'
POSITIONS = f'{_POSITION}s'
LINEWIDTHS = f'{_LINEWIDTH}s'
POINTPOSITIONS = f'{_POINTPOSITION}s'
PPMPOSITIONS = f'{_PPMPOSITION}s'
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
NR_ID = 'NR_ID'


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

        elif unit == 'point':
            value = multiplet.pointPositions[dim]

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
            value = peak.pointPositions[dim]

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
        return separator.join([dna.pid.id for dna in peak.dimensionNmrAtoms[dim] if not dna.isDeleted])


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


def _pairIntersectionPoints(intersectionPoints):
    """ Yield successive pair chunks from list of intersectionPoints """
    for i in range(0, len(intersectionPoints), 2):
        pair = intersectionPoints[i:i + 2]
        if len(pair) == 2:
            yield pair


def _getIntersectionPoints(x, y, line):
    """
    :param line: x points of line to intersect y points
    :return: list of intersecting points
    """
    z = y - line
    dx = x[1:] - x[:-1]
    cross = np.sign(z[:-1] * z[1:])

    x_intersect = x[:-1] - dx / (z[1:] - z[:-1]) * z[:-1]
    negatives = np.where(cross < 0)
    points = x_intersect[negatives]

    return points


def estimate1DPeakFWHM(peak):
    """
    Estimate the 1D peak Full Width at Half Maximum.

    Returns
    -------
    width:  The width for the peak in points.
    widthHeight: The height of the contour lines at which the `width` was evaluated.
    limits: tuple, Interpolated positions of left and right intersection points of a
        horizontal line at the respective evaluation height.

    """
    from scipy.signal import peak_widths
    from ccpn.core.Peak import Peak
    import numpy as np

    if not isinstance(peak, Peak):
        return [None, None, (None, None)]

    if peak.spectrum.dimensionCount > 1:
        return [None, None, (None, None)]

    y = peak.spectrum.intensities
    pointPositions = np.array([int(peak.pointPosition[0])])
    widths, widthHeight, *limits = peak_widths(y, pointPositions, rel_height=0.5)
    limits = tuple(zip(*limits))
    if widths and len(widths) > 0:
        return widths[0], widthHeight[0], limits[0]
    return [None, None, (None, None)]


def _getAtomWeight(axisCode, atomWeights) -> float or int:
    """

    :param axisCode: str of peak axis code
    :param atomWeights: dictionary of atomWeights eg {'H': 7.00, 'N': 1.00, 'C': 4.00, 'Other': 1.00}
    :return: float or int from dict atomWeights
    """
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
    """used to flat the state in a long list """
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
    """

    :param nmrResidue:
    :param nmrAtomsNames: nmr Atoms to compare. str 'H', 'N', 'CA' etc
    :param spectra: compare peaks only from given spectra
    :param theProperty: 'height' or 'volume'
    :return:
    """

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
    """
    :param nmrResidue:
    :param nmrAtomsNames: nmr Atoms to compare. str 'H', 'N', 'CA' etc
    :param spectra: compare peaks only from given spectra
    :return:
    """
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
    """

    :param nmrResidue:
    :param nmrAtomsNames: nmr Atoms to compare. str 'H', 'N', 'CA' etc
    :param spectra: compare peaks only from given spectra
    :return:
    """

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
    # print(( xs, ys), '$$$')
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
    yScaled[np.isnan(yScaled)] = 0  # cannot fit nans
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


def snapToExtremum(peak: 'Peak', halfBoxSearchWidth: int = 4, halfBoxFitWidth: int = 4,
                   minDropFactor: float = 0.1, fitMethod: str = PARABOLICMETHOD,
                   searchBoxMode=False, searchBoxDoFit=False):
    """Snap the position of the peak the nearest extremum.
    Assumes called with an existing peak, will fit within a box ±halfBoxSearchWidth about the current peak position.
    """
    from ccpn.framework.Application import getApplication

    spectrum = peak.spectrum
    numDim = spectrum.dimensionCount
    getApp = getApplication()

    if numDim == 1:
        # do the fit for 1D here
        doNeg = getApp.preferences.general.negativePeakPick1D
        snap1DPeaksByGroup([peak], ppmLimit=0.1, doNeg=doNeg)

    else:
        from ccpn.core.lib.PeakPickers.PeakPickerNd import PeakPickerNd

        spectrum = peak.spectrum
        myPeakPicker = PeakPickerNd(spectrum=spectrum)
        myPeakPicker.setParameters(dropFactor=minDropFactor,
                                   fitMethod=fitMethod,
                                   searchBoxMode=searchBoxMode,
                                   searchBoxDoFit=searchBoxDoFit,
                                   halfBoxSearchWidth=halfBoxSearchWidth,
                                   halfBoxFitWidth=halfBoxFitWidth,
                                   searchBoxWidths=getApp.preferences.general.searchBoxWidthsNd,
                                   )

        myPeakPicker.snapToExtremum(peak)


def peakParabolicInterpolation(peak: 'Peak', update=False):
    """
    return a (position, height, heightError) tuple using parabolic interpolation
    of the peak.position

    :param peak: a core.Peak instance or Pid or valid pid-string
    :param update: flag indicating peak position and height to be updated

    :return: (position, height) tuple;  position is a list with length
                                        spectrum.dimensionCount
    """
    import numpy
    from ccpn.core.Peak import Peak
    from ccpn.core.lib.Pid import Pid
    from ccpn.framework.Application import getApplication
    from ccpn.util.Parabole import Parabole

    if isinstance(peak, Peak):
        pass
    elif isinstance(peak, (Pid, str)):
        _peak = getApplication().project.getByPid(peak)
        if _peak is None:
            raise ValueError('Error retrieving valid peak instance from "%s"' % peak)
        peak = _peak
    else:
        raise ValueError('Expected a Peak, Pid or valid pid-string for the "peak" argument')

    spectrum = peak.peakList.spectrum
    spectrum.checkValidPath()

    # get the position as the nearest grid point
    position = [int(p + 0.5) for p in peak.pointPositions]
    # # get the data +/-1 point along each axis
    # sliceTuples = [(p - 1, p + 1) for p in position]  # nb: sliceTuples run [1,n] with n inclusive

    _valuesPerPoint = spectrum.ppmPerPoints
    _axisCodes = spectrum.axisCodes
    _regionData = {axisCode: (ppm - valPerPoint / 2, ppm + valPerPoint / 2,) for axisCode, ppm, valPerPoint in zip(_axisCodes, peak.ppmPositions, _valuesPerPoint)}
    data = spectrum.getRegion(**_regionData)

    heights = [0.0] * spectrum.dimensionCount
    newPosition = position[:]
    for axis in range(spectrum.dimensionCount):
        # get the three y-values along axis, but centered for the other axes
        slices = [slice(1, 2) for d in range(spectrum.dimensionCount)]
        slices[axis] = slice(0, 3)
        yValues = data[tuple(slices[::-1])].flatten()
        # create points list for the Parabole method
        point = position[axis]
        points = [(p, yValues[i]) for i, p in enumerate((point - 1, point, point + 1))]
        parabole = Parabole.fromPoints(points)
        newPosition[axis], heights[axis] = parabole.maxValue()

    arr = numpy.array(heights)
    height = float(numpy.average(arr))
    heightError = np.max(arr) - np.min(arr)
    if update:
        peak.pointPositions = newPosition
        peak.height = height
        peak.heightError = heightError
    return newPosition, height, heightError


def estimateVolumes(peaks: Sequence[Union[str, 'Peak']], volumeIntegralLimit=2.0, noWarning=False):
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
        elif not noWarning:
            getLogger().warning('Peak %s contains undefined height/lineWidths' % str(pp))


def movePeak(peak, ppmPositions, updateHeight=True):
    """Move a peak based on it's delta shift and optionally update to the height at the new position
    """
    with undoBlockWithoutSideBar():
        peak.position = ppmPositions

        if updateHeight:
            # get the interpolated height at this position
            peak.height = peak.peakList.spectrum.getHeight(ppmPositions)


def updateHeight(peak):
    with undoBlockWithoutSideBar():
        peak.height = peak.peakList.spectrum.getHeight(peak.position)


# added for pipelines


def _1Dregions(x, y, value, lim=0.01):
    # centre of position, peak position
    # lim in ppm where to look left and right
    referenceRegion = [value - lim, value + lim]
    point1, point2 = np.max(referenceRegion), np.min(referenceRegion)
    x_filtered = np.where((x <= point1) & (x >= point2))  # only the region of interest for the reference spectrum
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered


def _1DregionsFromLimits(x, y, limits):
    # centre of position, peak position
    # lim in ppm where to look left and right

    point1, point2 = np.max(limits), np.min(limits)
    x_filtered = np.where((x <= point1) & (x >= point2))  # only the region of interest for the reference spectrum
    y_filtered = y[x_filtered]
    x_filtered = x[x_filtered]
    return x_filtered, y_filtered


def _snap1DPeaksToExtremaSimple(peaks, limit=0.003):
    for peak in peaks:  # peaks can be from diff peakLists
        if peak is not None:
            x = peak.peakList.spectrum.positions
            y = peak.peakList.spectrum.intensities
            x_filtered, y_filtered = _1Dregions(x, y, peak.position[0], lim=limit)
            if len(y_filtered) > 0:
                idx = y_filtered.argmax()
                peakHeight = y_filtered[idx]
                peakPos = x[x_filtered[0][idx]]  # ppm positions
                peak.height = float(peakHeight)
                peak.position = [float(peakPos), ]


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def snap1DPeaksToExtrema(peaks, maximumLimit=0.1, figOfMeritLimit=1, doNeg=True):
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            if len(peaks) > 0:
                peaks.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
                for peak in peaks:  # peaks can be from diff peakLists
                    if peak is not None:
                        _snap1DPeakToClosestExtremum(peak, maximumLimit=maximumLimit,
                                                     figOfMeritLimit=figOfMeritLimit,
                                                     doNeg=doNeg)


def recalculatePeaksHeightAtPosition(peaks):
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            if len(peaks) > 0:
                for peak in peaks:  # peaks can be from diff peakLists
                    if peak is not None:
                        height = peak.peakList.spectrum.getHeight(peak.position)
                        peak.height = height


def updatePeaksFigureOfMerits(peaks, newMerit=0):
    """Set the figure of merit to the given value if the peak height is below the Noise threshold """
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            if len(peaks) > 0:
                for peak in peaks:  # peaks can be from diff peakLists
                    if peak is not None:
                        noiseLevel = peak.spectrum.noiseLevel or peak.spectrum.estimateNoise()
                        if peak.height < noiseLevel:
                            peak.figureOfMerit = newMerit


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

    binCount = binCount or int(len(y) / 2)
    statistics, edges, binNumbers = binned_statistic(y, y, bins=binCount, statistic='median')
    mostCommonBinNumber = np.argmax(np.bincount(binNumbers))
    highestValues = y[binNumbers == mostCommonBinNumber]  # values corresponding to most frequent binNumber
    fittedCurve = _fitBins(y, edges)
    fittedCurveExtremum = edges[np.argmax(fittedCurve)]  # value at the Extremum of the fitted curve
    return statistics, edges, binNumbers, fittedCurve, mostCommonBinNumber, highestValues, fittedCurveExtremum


def snap1DPeaksByGroup(peaks, ppmLimit=0.05, figOfMeritLimit=1,
                       doNeg=False, unsnappedLimit=1, increaseLimitStep=0.1):
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
        unsnappedPeaks = [p for p in peaks if p.heightError is not None]
        if len(unsnappedPeaks) == 0:
            return
        print('RESNAPPING at', newLimit, unsnappedPeaks)
        _snap1DPeaksByGroup(unsnappedPeaks, ppmLimit=newLimit, figOfMeritLimit=figOfMeritLimit,
                       doNeg=doNeg)


def _snap1DPeaksByGroup(peaks, ppmLimit=0.05, figOfMeritLimit=1,
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

        for peakGroup in peakGroups[:]:
            peakGroup = np.array(peakGroup)
            if len(peakGroup) == 1:
                ## if there is only one peak in the group then snap normally to closest:
                snap1DPeaksToExtrema(list(peakGroup), maximumLimit=ppmLimit)
            else:
                positions = np.array([pk.position[0] for pk in peakGroup])
                limits = np.min(positions), np.max(positions)
                searchingLimits = limits[0] - ppmLimit, limits[1] + ppmLimit
                xROItarget, yROItarget = _1DregionsFromLimits(xValues, yValues, limits=searchingLimits)
                maxValues, minValues = _find1DMaxima(yROItarget, xROItarget, positiveThreshold=noiseLevel,
                                                     negativeThreshold=negativeNoiseLevel, findNegative=doNeg)
                foundCoords = np.array(maxValues + minValues)
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
                    foundCoords.sort(key=lambda x: x[0], reverse=False)  # reorder peaks by position
                    for peak, coord in zip(peakGroup, foundCoords):
                        peak.position = [coord[0], ]
                        peak.height = float(coord[1])
                        peak.heightError = None
                else:
                    ## found different count of new coords and peaks. Order by distanceMatrix and snap to best fit.
                    snap1DPeaksByGroup(peaks, ppmLimit=ppmLimit / 2)




def snap1DPeaksAndRereferenceSpectrum(peaks, maximumLimit=0.1, useAdjacientPeaksAsLimits=False,
                                      doNeg=False, figOfMeritLimit=1, spectrum=None, autoRereferenceSpectrum=False):
    """
    Snap all peaks to closest maxima

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


def _add(x, y):
    if y > 0:
        return _add(x, y - 1) + 1
    elif y < 0:
        return _add(x, y + 1) - 1
    else:
        return x


def _sub(x, y):
    if y > 0:
        return _sub(x, y - 1) - 1
    elif y < 0:
        return _sub(x, y + 1) + 1
    else:
        return x


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


def _snap1DPeakToClosestExtremum(peak, maximumLimit=0.1, doNeg=False, figOfMeritLimit=0):
    """
    It snaps a peak to its closest extremum, that can be considered as a peak.
    it uses adjacent peak positions as boundaries. However if no adjacent peaks then uses the maximumlimits.
    Uses peak
    :param peak: obj peak
    :param maximumLimit: maximum tolerance left or right from the peak position (ppm)
    """
    position, height, error = _get1DClosestExtremum(peak, maximumLimit, doNeg=doNeg, figOfMeritLimit=figOfMeritLimit)
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            peak.position = position
            peak.height = height
            peak.heightError = error


def getSpectralPeakHeights(spectra, peakListIndexes: list = None) -> pd.DataFrame:
    return _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=HEIGHT, peakListIndexes=peakListIndexes)


def getSpectralPeakVolumes(spectra, peakListIndexes: list = None) -> pd.DataFrame:
    return _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=VOLUME, peakListIndexes=peakListIndexes)


def getSpectralPeakHeightForNmrResidue(spectra, peakListIndexes: list = None) -> pd.DataFrame:
    """
    return: Pandas DataFrame with the following structure:
            Index:  ID for the nmrResidue(s) assigned to the peak ;
            Columns => Spectrum series values sorted by ascending values, if series values are not set, then the
                       spectrum name is used instead.

                   |   SP1     |    SP2    |   SP3
        NR_ID      |           |           |
       ------------+-----------+-----------+----------
        A.1.ARG    |    10     |  100      | 1000

        """
    df = getSpectralPeakHeights(spectra, peakListIndexes)
    newDf = df[df[NR_ID] != '']  # remove rows if NR_ID is not defined
    newDf = newDf.reset_index(drop=True).groupby(NR_ID).max()
    return newDf


def getSpectralPeakVolumeForNmrResidue(spectra, peakListIndexes: list = None) -> pd.DataFrame:
    """
    return: Pandas DataFrame with the following structure:
            Index:  ID for the nmrResidue(s) assigned to the peak ;
            Columns => Spectrum series values sorted by ascending values, if series values are not set, then the
                       spectrum name is used instead.

                   |   SP1     |    SP2    |   SP3
        NR_ID      |           |           |
       ------------+-----------+-----------+----------
        A.1.ARG    |    10     |  100      | 1000

        """
    df = getSpectralPeakVolumes(spectra, peakListIndexes)
    newDf = df[df[NR_ID] != '']  # remove rows if NR_ID is not defined
    newDf = newDf.reset_index(drop=True).groupby(NR_ID).max()
    return newDf


def _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=HEIGHT, NR_ID=NR_ID, peakListIndexes: list = None):
    """
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
    """
    dfs = []
    if peakListIndexes is None: peakListIndexes = [-1] * len(spectra)
    for spectrum, ix in zip(spectra, peakListIndexes):
        positions = []
        values = []
        nmrResidues = []
        serieValue = spectrum.name  # use spectrumName as default. if series defined use that instead.
        if len(spectrum.spectrumGroups) > 0:
            sGserieValue = spectrum._getSeriesItem(spectrum.spectrumGroups[-1])
            if sGserieValue is not None:
                serieValue = sGserieValue
        peaks = spectrum.peakLists[ix].peaks
        peaks.sort(key=lambda x: x.position, reverse=True)
        for peak in peaks:
            positions.append(peak.position)
            values.append(getattr(peak, peakProperty, None))
            assignedResidues = list(set(filter(None, map(lambda x: x.nmrResidue.id,
                                                         makeIterableList(peak.assignments)))))
            nmrResidues.append(", ".join(assignedResidues))
        _df = pd.DataFrame(values, columns=[serieValue], index=m_ix.from_tuples(positions, names=spectrum.axisCodes))
        _df[NR_ID] = nmrResidues
        _df = _df[~_df.index.duplicated()]
        dfs.append(_df)
    df = pd.concat(dfs, axis=1, levels=0)
    df[NR_ID] = df.T[df.columns.values == NR_ID].apply(lambda x: ' '.join(set([item for item in x[x.notnull()]])))
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
    # if not negativeNoiseLevel and noiseLevel:
    if negativeNoiseLevel is None and noiseLevel is not None:
        negativeNoiseLevel = - noiseLevel if noiseLevel > 0 else noiseLevel * 2
        spectrum.negativeNoiseLevel = negativeNoiseLevel
        getLogger().warning('Spectrum Negative noise not defined for %s. Estimated default' % spectrum.pid)

    # if not noiseLevel:  # estimate it
    if noiseLevel is None:  # estimate it
        noiseLevel = spectrum.estimateNoise()
        negativeNoiseLevel = -noiseLevel
        spectrum.noiseLevel, spectrum.negativeNoiseLevel = noiseLevel, negativeNoiseLevel
        getLogger().warning('Spectrum noise level(s) not defined for %s. Estimated default' % spectrum.pid)

    if peak.height is None:
        updateHeight(peak)
        _getPeakSNRatio(peak)

    snr = estimateSNR(noiseLevels=[noiseLevel, negativeNoiseLevel], signalPoints=[peak.height], factor=factor)
    return snr[0]  ## estimateSNR return a list with a length always > 0
