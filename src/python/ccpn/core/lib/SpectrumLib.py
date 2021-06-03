"""Spectrum-related functions and utilities
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
__dateModified__ = "$dateModified: 2021-05-13 19:27:55 +0100 (Thu, May 13, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import math
import random
import numpy as np
from typing import Tuple
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.util.Common import percentage, getAxisCodeMatchIndices
from ccpn.util.Logging import getLogger
from ccpn.core.lib._DistanceRestraintsLib import _getBoundResonances, longRangeTransfers


MagnetisationTransferTuple = collections.namedtuple('MagnetisationTransferTuple', 'dimension1 dimension2 transferType isIndirect')
NoiseEstimateTuple = collections.namedtuple('NoiseEstimateTuple', 'mean std min max noiseLevel')


# def _oldEstimateNoiseLevel1D(x, y, factor=3):
#   """
#   :param x,y:  spectrum.positions, spectrum.intensities
#   :param factor: optional. Increase factor to increase the STD and therefore the noise level threshold
#   :return: float of estimated noise threshold
#   """
#
#   data = np.array([x, y])
#   dataStd = np.std(data)
#   data = np.array(data, np.float32)
#   data = data.clip(-dataStd, dataStd)
#   value = factor * np.std(data)
#   return value


def _oldEstimateNoiseLevel1D(y, factor=0.5):
    """
    Estimates the noise threshold based on the max intensity of the first portion of the spectrum where
    only noise is present. To increase the threshold value: increase the factor.
    return:  float of estimated noise threshold
    """
    if y is not None:
        # print('_oldEstimateNoiseLevel1D',max(y[:int(len(y)/20)]) * factor, 'STD, ')
        return max(y[:int(len(y) / 20)]) * factor
    else:
        return 0


def _calibrateX1D(spectrum, currentPosition, newPosition):
    shift = newPosition - currentPosition
    spectrum.referenceValues = [spectrum.referenceValues[0] + shift]
    spectrum.positions = spectrum.positions + shift


def _calibrateY1D(spectrum, currentPosition, newPosition):
    shift = newPosition - currentPosition
    spectrum.intensities = spectrum.intensities + shift


def _calibrateXND(spectrum, strip, currentPosition, newPosition):
    from ccpn.util.Common import getAxisCodeMatchIndices

    # map the X change to the correct spectrum axis
    spectrumReferencing = list(spectrum.referenceValues)
    indices = getAxisCodeMatchIndices(strip.axisCodes, spectrum.axisCodes)

    # as modifying the spectrum, spectrum needs to be the second argument of getAxisCodeMatchIndices
    spectrumReferencing[indices[0]] = float(spectrumReferencing[indices[0]] + (newPosition - currentPosition))
    spectrum.referenceValues = spectrumReferencing


def _calibrateNDAxis(spectrum, axisIndex, currentPosition, newPosition):
    from ccpn.util.Common import getAxisCodeMatchIndices

    # map the X change to the correct spectrum axis
    spectrumReferencing = list(spectrum.referenceValues)

    # as modifying the spectrum, spectrum needs to be the second argument of getAxisCodeMatchIndices
    spectrumReferencing[axisIndex] = float(spectrumReferencing[axisIndex] + (newPosition - currentPosition))
    spectrum.referenceValues = spectrumReferencing


def _calibrateYND(spectrum, strip, currentPosition, newPosition):
    from ccpn.util.Common import getAxisCodeMatchIndices

    # map the Y change to the correct spectrum axis
    spectrumReferencing = list(spectrum.referenceValues)
    indices = getAxisCodeMatchIndices(strip.axisCodes, spectrum.axisCodes)

    # as modifying the spectrum, spectrum needs to be the second argument of getAxisCodeMatchIndices
    spectrumReferencing[indices[1]] = float(spectrumReferencing[indices[1]] + (newPosition - currentPosition))
    spectrum.referenceValues = spectrumReferencing


def _set1DRawDataFromCcpnInternal(spectrum):
    if not spectrum._ccpnInternalData['positions'] and not spectrum._ccpnInternalData['intensities']:
        return
    spectrum.positions = np.array(spectrum._ccpnInternalData['positions'])
    spectrum.intensities = np.array(spectrum._ccpnInternalData['intensities'])


def _negLogLikelihood(deltas, queryPeakPositions, kde):
    shifted = queryPeakPositions - deltas
    return -kde.logpdf(shifted.T)


def align2HSQCs(refSpectrum, querySpectrum, refPeakListIdx=-1, queryPeakListIdx=-1):
    # Get hold of the peakLists in the two spectra
    queryPeakList = querySpectrum.peakLists[queryPeakListIdx]
    refPeakList = refSpectrum.peakLists[refPeakListIdx]

    # Create numpy arrays containing the peak positions of
    # each peakList

    import numpy as np

    refPeakPositions = np.array([peak.position for peak in
                                 refPeakList.peaks])
    queryPeakPositions = np.array([peak.position for peak in queryPeakList.peaks])

    # Align the two numpy arrays by centre of mass
    refMean = np.mean(refPeakPositions, axis=0)
    queryMean = np.mean(queryPeakPositions, axis=0)
    roughShift = queryMean - refMean
    shiftedQueryPeakPositions = queryPeakPositions - roughShift

    # Define a log-likelihood target for fitting the query
    # peak positions
    from scipy.optimize import leastsq
    from scipy.stats import gaussian_kde

    # Create the Gaussian KDE
    kde = gaussian_kde(refPeakPositions.T, bw_method=0.1)

    # Get hold of the values to overlay the two spectra
    shifts, status = leastsq(_negLogLikelihood, roughShift,
                             args=(queryPeakPositions, kde))

    # Get hold of the reference values of the querySpectrum
    queryRefValues = queryPeakList.spectrum.referenceValues

    # Calculate the corrected reference values
    correctedValues = np.array(queryRefValues) - shifts

    return shifts, correctedValues


def _estimate1DSpectrumSNR(spectrum, engine='max'):
    """

    :param spectrum:
    :type spectrum:
    :param engine: max: calculate using the max intensity of all spectrum
    :type engine:
    :return:
    :rtype:
    """
    engines = {'max': np.max, 'mean': np.mean, 'std': np.std}

    if engine in engines:
        func = engines.get(engine)
    else:
        func = np.max
        print('Engine not recognised. Using Default')
    _snr = estimateSNR(noiseLevels=[spectrum.noiseLevel, spectrum.negativeNoiseLevel],
                       signalPoints=[func(spectrum.intensities)])

    return _snr[0]


# refSpectrum = project.spectra[]
# querySpectrum = project.spectra[]
# a = align2HSQCs(refSpectrum, querySpectrum, refPeakListIdx=-1, queryPeakListIdx=-1)
#
# for peak in querySpectrum.peakLists[-1].peaks:
#     p1,p2  = peak.position[0], peak.position[1]
#     p1x = p1-(a[0][0])
#     p2x = p2-(a[0][1])
#     peak.position = (p1x,p2x)


#------------------------------------------------------------------------------------------------------
# Spectrum projection
# GWV: Adapted from DataSource.py
#------------------------------------------------------------------------------------------------------

PROJECTION_METHODS = ('max', 'max above threshold', 'min', 'min below threshold',
                      'sum', 'sum above threshold', 'sum below threshold')


def _getProjection(spectrum: 'Spectrum', axisCodes: tuple,
                   method: str = 'max', threshold=None):
    """Get projected plane defined by axisCodes using method and optional threshold
    return projected data array

    NB Called by Spectrum.getProjection
    """

    if method not in PROJECTION_METHODS:
        raise ValueError('For spectrum projection, method must be one of %s' % (PROJECTION_METHODS,))

    if method.endswith('threshold') and threshold is None:
        raise ValueError('For spectrum projection method "%s", threshold parameter must be defined' % (method,))

    projectedData = None
    for position, planeData in spectrum.allPlanes(axisCodes, exactMatch=True):

        if method == 'sum above threshold' or method == 'max above threshold':
            lowIndices = planeData < threshold
            planeData[lowIndices] = 0
        elif method == 'sum below threshold' or method == 'min below threshold':
            lowIndices = planeData > -threshold
            planeData[lowIndices] = 0

        if projectedData is None:
            # first plane
            projectedData = planeData
        elif method == 'max' or method == 'max above threshold':
            projectedData = np.maximum(projectedData, planeData)
        elif method == 'min' or method == 'min below threshold':
            projectedData = np.minimum(projectedData, planeData)
        else:
            projectedData += planeData

    return projectedData


###################################################################################################
##################             Baseline Correction for 1D spectra                ##################
###################################################################################################


"""
14/2/2017

Baseline Correction for 1D spectra.
Multiple algorithms comparison:

-Asl
-Whittaker Smooth
-AirPls
-ArPls
-Lowess
-Polynomial Fit

NB: Yet To be tested the newest algorithm found in literature based on machine learning:
“Estimating complicated baselines in analytical signals using the iterative training of
Bayesian regularized artificial neural networks. Abolfazl Valadkhani et al.
Analytica Chimica Acta. September 2016 DOI: 10.1016/j.aca.2016.08.046

"""

from scipy.sparse import csc_matrix, eye, diags
from scipy import sparse
from scipy.sparse.linalg import spsolve


"""
Asl algorithm
"""


def als(y, lam=10 ** 2, p=0.001, nIter=10):
    """Implements an Asymmetric Least Squares Smoothing
    baseline correction algorithm
    H C Eilers, Paul & F M Boelens, Hans. (2005). Baseline Correction with Asymmetric Least Squares Smoothing. Unpubl. Manuscr. .

    y = signal
    lam = smoothness, 10**2 ≤ λ ≤ 10**9.
    p = asymmetry, 0.001 ≤ p ≤ 0.1 is a good choice for a signal with positive peaks.
    niter = Number of iteration, default 10.

    """

    L = len(y)
    D = sparse.csc_matrix(np.diff(np.eye(L), 2))
    w = np.ones(L)
    for i in range(nIter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return z


###################################################################################################


"""
Whittaker Smooth algorithm
"""


def WhittakerSmooth(y, w, lambda_, differences=1):
    """
    no licence, source from web
    Penalized least squares algorithm for background fitting

    input
        x: input data (i.e. chromatogram of spectrum)
        w: binary masks (value of the mask is zero if a point belongs to peaks and one otherwise)
        lambda_: parameter that can be adjusted by user. The larger lambda is,  the smoother the resulting background
        differences: integer indicating the order of the difference of penalties

    output
        the fitted background vector
    """
    X = np.matrix(y)
    m = X.size
    i = np.arange(0, m)
    E = eye(m, format='csc')
    D = E[1:] - E[:-1]  # numpy.diff() does not work with sparse matrix. This is a workaround.
    W = diags(w, 0, shape=(m, m))
    A = csc_matrix(W + (lambda_ * D.T * D))
    B = csc_matrix(W * X.T)
    background = spsolve(A, B)
    return np.array(background)


###################################################################################################

"""
airPLS algorithm
"""


def airPLS(y, lambda_=100, porder=1, itermax=15):
    """
    no licence, source from web
    Adaptive iteratively reweighted penalized least squares for baseline fitting

    input
        x: input data (i.e. chromatogram of spectrum)
        lambda_: parameter that can be adjusted by user. The larger lambda is,  the smoother the resulting background, z
        porder: adaptive iteratively reweighted penalized least squares for baseline fitting

    output
        the fitted background vector
    """
    m = y.shape[0]
    w = np.ones(m)
    for i in range(1, itermax + 1):
        z = WhittakerSmooth(y, w, lambda_, porder)
        d = y - z
        dssn = np.abs(d[d < 0].sum())
        if (dssn < 0.001 * (abs(y)).sum() or i == itermax):
            if (i == itermax): print('WARING max iteration reached!')
            break
        w[d >= 0] = 0  # d>0 means that this point is part of a peak, so its weight is set to 0 in order to ignore it
        w[d < 0] = np.exp(i * np.abs(d[d < 0]) / dssn)
        w[0] = np.exp(i * (d[d < 0]).max() / dssn)
        w[-1] = w[0]
    return z


###################################################################################################


"""
polynomial Fit algorithm
"""


def polynomialFit(x, y, order: int = 3):
    """
    :param x: x values
    :param y: y values
    :param order: polynomial order
    :return: fitted baseline
    """
    fit = np.polyval(np.polyfit(x, y, deg=order), x)
    return fit


###################################################################################################


"""
arPLS algorithm
"""


def arPLS(y, lambda_=5.e5, ratio=1.e-6, itermax=50):
    """
    Baseline correction using asymmetrically reweighted penalized least squares
    smoothing.

    http://pubs.rsc.org/en/Content/ArticleLanding/2015/AN/C4AN01061B#!divAbstract



    :param y: The 1D spectrum
    :param lambda_: (Optional) Adjusts the balance between fitness and smoothness.
                    A smaller lamda_ favors fitness.
                    Default is 1.e5.
    :param ratio: (Optional) Iteration will stop when the weights stop changing.
                    (weights_(i) - weights_(i+1)) / (weights_(i)) < ratio.
                    Default is 1.e-6.
    :param log: (Optional) True to debug log. Default False.
    :returns: The smoothed baseline of y.
    """
    y = np.array(y)

    N = y.shape[0]

    E = eye(N, format='csc')
    # numpy.diff() does not work with sparse matrix. This is a workaround.
    # It creates the second order difference matrix.
    # [1 -2 1 ......]
    # [0 1 -2 1 ....]
    # [.............]
    # [.... 0 1 -2 1]
    D = E[:-2] - 2 * E[1:-1] + E[2:]

    H = lambda_ * D.T * D
    Y = np.matrix(y)

    w = np.ones(N)

    for i in range(itermax + 10):
        W = diags(w, 0, shape=(N, N))
        Q = W + H
        B = W * Y.T

        z = spsolve(Q, B)
        d = y - z
        dn = d[d < 0.0]

        m = np.mean(dn)
        if np.isnan(m):
            # add a tiny bit of noise to Y
            y2 = y.copy()
            if np.std(y) != 0.:
                y2 += (np.random.random(y.size) - 0.5) * np.std(y) / 1000.
            elif np.mean(y) != 0.0:
                y2 += (np.random.random(y.size) - 0.5) * np.mean(y) / 1000.
            else:
                y2 += (np.random.random(y.size) - 0.5) / 1000.
            y = y2
            Y = np.matrix(y2)
            W = diags(w, 0, shape=(N, N))
            Q = W + H
            B = W * Y.T

            z = spsolve(Q, B)
            d = y - z
            dn = d[d < 0.0]

            m = np.mean(dn)
        s = np.std(dn, ddof=1)

        wt = 1. / (1 + np.exp(2. * (d - (2 * s - m)) / s))

        # check exit condition
        condition = np.linalg.norm(w - wt) / np.linalg.norm(w)
        if condition < ratio:
            break
        if i > itermax:
            break
        w = wt

    return z


###################################################################################################


"""
Implementation of the  arPLS algorithm
"""


def arPLS_Implementation(y, lambdaValue=5.e4, maxValue=1e6, minValue=-1e6, itermax=10, interpolate=True):
    """
    maxValue = maxValue of the baseline noise
    minValue = minValue of the baseline noise
    interpolate: Where are the peaks: interpolate the points from neighbours otherwise set them to 0.

    """

    lenghtY = len(y)
    sparseMatrix = eye(lenghtY, format='csc')
    differenceMatrix = sparseMatrix[:-2] - 2 * sparseMatrix[1:-1] + sparseMatrix[2:]
    H = lambdaValue * differenceMatrix.T * differenceMatrix

    Y = np.matrix(y)
    w = np.ones(lenghtY)

    for i in range(itermax):
        W = diags(w, 1, shape=(lenghtY, lenghtY))
        Q = W + H
        B = W * Y.T
        z = spsolve(Q, B)
        mymask = (z > maxValue) | (z < minValue)
        b = np.ma.masked_where(mymask, z)
        if interpolate:
            c = np.interp(np.where(mymask)[0], np.where(~mymask)[0], b[np.where(~mymask)[0]])
            b[np.where(mymask)[0]] = c
        else:
            b = np.ma.filled(b, fill_value=0)

    return b


def lowess(x, y):
    """
    LOWESS (Locally Weighted Scatterplot Smoothing).
    A lowess function that outs smoothed estimates of endog
    at the given exog values from points (exog, endog)
    To use this, you need to install statsmodels in your miniconda:
     - conda install statsmodels or pip install --upgrade --no-deps statsmodels
    """

    from scipy.interpolate import interp1d
    import statsmodels.api as sm

    # introduce some floats in our x-values

    # lowess will return our "smoothed" data with a y value for at every x-value
    lowess = sm.nonparametric.lowess(y, x, frac=.3)

    # unpack the lowess smoothed points to their values
    lowess_x = list(zip(*lowess))[0]
    lowess_y = list(zip(*lowess))[1]

    # run scipy's interpolation. There is also extrapolation I believe
    f = interp1d(lowess_x, lowess_y, bounds_error=False)

    # this this generate y values for our xvalues by our interpolator
    # it will MISS values outsite of the x window (less than 3, greater than 33)
    # There might be a better approach, but you can run a for loop
    # and if the value is out of the range, use f(min(lowess_x)) or f(max(lowess_x))
    ynew = f(x)
    return ynew


def nmrGlueBaselineCorrector(data, wd=20):
    """
    :param data: 1D ndarray
        One dimensional NMR data with real value (intensities)
        wd : float  Median window size in pts.
    :return: same as data
    """
    import nmrglue as ng

    data = ng.process.proc_bl.baseline_corrector(data, wd=wd)
    return data


def _getDefaultApiSpectrumColours(spectrum: 'Spectrum') -> Tuple[str, str]:
    """Get the default colours from the core spectrum class
    """
    # from ccpn.util.Colour import spectrumHexColours
    from ccpn.ui.gui.guiSettings import getColours, SPECTRUM_HEXCOLOURS, SPECTRUM_HEXDEFAULTCOLOURS
    from ccpn.util.Colour import hexToRgb, findNearestHex, invertRGBHue, rgbToHex

    dimensionCount = spectrum.dimensionCount
    serial = spectrum._serial
    expSerial = spectrum.experiment.serial

    spectrumHexColours = getColours().get(SPECTRUM_HEXCOLOURS)
    spectrumHexDefaultColours = getColours().get(SPECTRUM_HEXDEFAULTCOLOURS)

    # use different colour lists for 1d and Nd
    if dimensionCount < 2:
        colorCount = len(spectrumHexColours)
        step = ((colorCount // 2 - 1) // 2)
        kk = colorCount // 7
        index = expSerial - 1 + step * (serial - 1)
        posCol = spectrumHexColours[(kk * index + 10) % colorCount]
        negCol = spectrumHexColours[((kk + 1) * index + 10) % colorCount]

    else:
        try:
            # try and get the colourPalette number from the preferences, otherwise use 0
            from ccpn.framework.Application import getApplication

            colourPalette = getApplication().preferences.general.colourPalette
        except:
            colourPalette = 0

        if colourPalette == 0:
            # colours for Vicky :)
            colorCount = len(spectrumHexDefaultColours)
            step = ((colorCount // 2 - 1) // 2)
            index = expSerial - 1 + step * (serial - 1)
            posCol = spectrumHexDefaultColours[(2 * index) % colorCount]
            negCol = spectrumHexDefaultColours[(2 * index + 1) % colorCount]

        else:
            # automatic colours
            colorCount = len(spectrumHexColours)
            step = ((colorCount // 2 - 1) // 2)
            kk = 11  #colorCount // 11
            index = expSerial - 1 + step * (serial - 1)
            posCol = spectrumHexColours[(kk * index + 10) % colorCount]

            # invert the colour by reversing the ycbcr palette
            rgbIn = hexToRgb(posCol)
            negRGB = invertRGBHue(*rgbIn)
            oppCol = rgbToHex(*negRGB)
            # get the nearest one in the current colour list, so colourName exists
            negCol = findNearestHex(oppCol, spectrumHexColours)

    return (posCol, negCol)


def getDefaultSpectrumColours(self: 'Spectrum') -> Tuple[str, str]:
    """Get default positivecontourcolour, negativecontourcolour for Spectrum
    (calculated by hashing spectrum properties to avoid always getting the same colours
    Currently matches getDefaultColours in dataSource that is set through the api
    """
    return _getDefaultApiSpectrumColours(self)


def get1DdataInRange(x, y, xRange):
    """

    :param x:
    :param y:
    :param xRange:
    :return: x,y within the xRange (minXrange,maxXrange)

    """
    if xRange is None:
        return x, y
    point1, point2 = np.max(xRange), np.min(xRange)
    x_filtered = np.where((x <= point1) & (x >= point2))
    y_filtered = y[x_filtered]

    return x_filtered, y_filtered


def _recurseData(ii, dataList, startCondition, endCondition):
    """Iterate over the dataArray, subdividing each iteration
    """
    for data in dataList:

        if not data.size:
            continue

        # calculate the noise values
        flatData = data.flatten()

        SD = np.std(flatData)
        max = np.max(flatData)
        min = np.min(flatData)
        mn = np.mean(flatData)
        noiseLevel = mn + 3.5 * SD

        if not startCondition:
            startCondition[:] = [ii, data.shape, SD, max, min, mn, noiseLevel]
            endCondition[:] = startCondition[:]

        if SD < endCondition[2]:
            endCondition[:] = [ii, data.shape, SD, max, min, mn, noiseLevel]

        # stop iterating when all dimensions are <= 64 elements
        if any(dim > 64 for dim in data.shape):

            newData = [data]
            for jj in range(len(data.shape)):
                newData = [np.array_split(dd, 2, axis=jj) for dd in newData]
                newData = [val for sublist in newData for val in sublist]

            _recurseData(ii + 1, newData, startCondition, endCondition)

# keep for a minute - example of how to call _recurseData
# # iterate over the array to calculate noise at each level
# dataList = [dataArray]
# startCondition = []
# endCondition = []
# _recurseData(0, dataList, startCondition, endCondition)



# def _setApiContourLevelsFromNoise(apiSpectrum, setNoiseLevel=True,
#                                   setPositiveContours=True, setNegativeContours=True,
#                                   useSameMultiplier=True):
#     """Calculate the noise level, base contour level and positive/negative multipliers for the given apiSpectrum
#     """
#     # NOTE:ED - method doesn't seem to be used?
#     project = apiSpectrum.topObject
#
#     # the core objects should have been initialised at this point
#     if project and apiSpectrum in project._data2Obj:
#         spectrum = project._data2Obj[apiSpectrum]
#         if spectrum.dimensionCount == 1: return
#         setContourLevelsFromNoise(spectrum, setNoiseLevel=setNoiseLevel,
#                                   setPositiveContours=setPositiveContours, setNegativeContours=setNegativeContours,
#                                   useSameMultiplier=useSameMultiplier)


DEFAULTMULTIPLIER = 1.414214
DEFAULTLEVELS = 10
DEFAULTCONTOURBASE = 10000.0


def setContourLevelsFromNoise(spectrum, setNoiseLevel=True,
                              setPositiveContours=True, setNegativeContours=True,
                              useDefaultMultiplier=True, useDefaultLevels=True, useDefaultContourBase=False,
                              useSameMultiplier=True,
                              defaultMultiplier=DEFAULTMULTIPLIER, defaultLevels=DEFAULTLEVELS, defaultContourBase=DEFAULTCONTOURBASE):
    """Calculate the noise level, base contour level and positive/negative multipliers for the given spectrum
    """

    # parameter error checking
    if not isinstance(setNoiseLevel, bool):
        raise TypeError('setNoiseLevel is not boolean.')
    if not isinstance(setPositiveContours, bool):
        raise TypeError('setPositiveContours is not boolean.')
    if not isinstance(setNegativeContours, bool):
        raise TypeError('setNegativeContours is not boolean.')
    if not isinstance(useDefaultMultiplier, bool):
        raise TypeError('useDefaultMultiplier is not boolean.')
    if not isinstance(useDefaultLevels, bool):
        raise TypeError('useDefaultLevels is not boolean.')
    if not isinstance(useDefaultContourBase, bool):
        raise TypeError('useDefaultContourBase is not boolean.')
    if not isinstance(useSameMultiplier, bool):
        raise TypeError('useSameMultiplier is not boolean.')

    if not (isinstance(defaultMultiplier, float) and defaultMultiplier > 0):
        raise TypeError('defaultMultiplier is not a positive float.')
    if not (isinstance(defaultLevels, int) and defaultLevels > 0):
        raise TypeError('defaultLevels is not a positive int.')
    if not (isinstance(defaultContourBase, float) and defaultContourBase > 0):
        raise TypeError('defaultContourBase is not a positive float.')

    if spectrum.dimensionCount == 1:
        return

    # exit if nothing set
    if not (setNoiseLevel or setPositiveContours or setNegativeContours):
        return

    if any(x != 'Frequency' for x in spectrum.dimensionTypes):
        raise NotImplementedError("setContourLevelsFromNoise not implemented for processed frequency spectra, dimension types were: {}".format(spectrum.dimensionTypes, ))

    getLogger().info("estimating noise level for spectrum %s" % str(spectrum.pid))
    if setNoiseLevel:
        # get noise level using random sampling method - may be slow for large spectra
        noise = getNoiseEstimate(spectrum)
        base = spectrum.noiseLevel = noise.noiseLevel
    else:
        base = spectrum.noiseLevel
        # need to generate a min/max
        noise = getContourEstimate(spectrum)

    # noise => noise.mean, noise.std, noise.min, noise.max, noise.noiseLevel

    if useDefaultLevels:
        posLevels = defaultLevels
        negLevels = defaultLevels
    else:
        # get from the spectrum
        posLevels = spectrum.positiveContourCount
        negLevels = spectrum.negativeContourCount

    if useDefaultMultiplier:
        # use default as root2
        posMult = negMult = defaultMultiplier
    else:
        # calculate multiplier to give contours across range of spectrum; trap base = 0
        mx = noise.max
        mn = noise.min

        posMult = pow(abs(mx / base), 1 / posLevels) if base else 0.0
        if useSameMultiplier:
            negMult = posMult
        else:
            negMult = pow(abs(mn / base), 1 / negLevels) if base else 0.0

    if setPositiveContours:
        try:
            spectrum.positiveContourBase = base
            spectrum.positiveContourFactor = posMult
        except Exception as es:

            # set to defaults if an error occurs
            spectrum.positiveContourBase = defaultContourBase
            spectrum.positiveContourFactor = defaultMultiplier
            getLogger().warning('Error setting contour levels - %s', str(es))

        spectrum.positiveContourCount = posLevels

    if setNegativeContours:
        try:
            spectrum.negativeContourBase = -base
            spectrum.negativeContourFactor = negMult
        except Exception as es:

            # set to defaults if an error occurs
            spectrum.negativeContourBase = -defaultContourBase
            spectrum.negativeContourFactor = defaultMultiplier
            getLogger().warning('Error setting contour levels - %s', str(es))

        spectrum.negativeContourCount = negLevels

    return


def getContourLevelsFromNoise(spectrum,
                              setPositiveContours=False, setNegativeContours=False,
                              useDefaultMultiplier=True, useDefaultLevels=True, useDefaultContourBase=False,
                              useSameMultiplier=True,
                              defaultMultiplier=DEFAULTMULTIPLIER, defaultLevels=DEFAULTLEVELS, defaultContourBase=DEFAULTCONTOURBASE):
    """Calculate the noise level, base contour level and positive/negative multipliers for the given spectrum
    """

    # parameter error checking
    if not isinstance(setPositiveContours, bool):
        raise TypeError('setPositiveContours is not boolean.')
    if not isinstance(setNegativeContours, bool):
        raise TypeError('setNegativeContours is not boolean.')
    if not isinstance(useDefaultMultiplier, bool):
        raise TypeError('useDefaultMultiplier is not boolean.')
    if not isinstance(useDefaultLevels, bool):
        raise TypeError('useDefaultLevels is not boolean.')
    if not isinstance(useDefaultContourBase, bool):
        raise TypeError('useDefaultContourBase is not boolean.')
    if not isinstance(useSameMultiplier, bool):
        raise TypeError('useSameMultiplier is not boolean.')

    if not (isinstance(defaultMultiplier, float) and defaultMultiplier > 0):
        raise TypeError('defaultMultiplier is not a positive float.')
    if not (isinstance(defaultLevels, int) and defaultLevels > 0):
        raise TypeError('defaultLevels is not a positive int.')
    if not (isinstance(defaultContourBase, float) and defaultContourBase > 0):
        raise TypeError('defaultContourBase is not a positive float.')

    if spectrum.dimensionCount == 1:
        return [None] * 6

    if any(x != 'Frequency' for x in spectrum.dimensionTypes):
        raise NotImplementedError("getContourLevelsFromNoise not implemented for processed frequency spectra, dimension types were: {}".format(spectrum.dimensionTypes, ))

    # need to generate a min/max
    noise = getContourEstimate(spectrum)

    # noise => noise.mean, noise.std, noise.min, noise.max, noise.noiseLevel

    if useDefaultLevels:
        posLevels = defaultLevels
        negLevels = defaultLevels
    else:
        # get from the spectrum
        posLevels = spectrum.positiveContourCount
        negLevels = spectrum.negativeContourCount

    if useDefaultContourBase:
        posBase = defaultContourBase
    else:
        # calculate the base levels
        posBase = spectrum.noiseLevel
    negBase = -posBase if posBase else 0.0

    if useDefaultMultiplier:
        # use default as root2
        posMult = negMult = defaultMultiplier
    else:
        # calculate multiplier to give contours across range of spectrum; trap base = 0
        mx = noise.max
        mn = noise.min

        posMult = pow(abs(mx / posBase), 1 / posLevels) if posBase else 0.0
        if useSameMultiplier:
            negMult = posMult
        else:
            negMult = pow(abs(mn / negBase), 1 / negLevels) if negBase else 0.0

    if not setPositiveContours:
        posBase = posMult = posLevels = None

    if not setNegativeContours:
        negBase = negMult = negLevels = None

    return posBase, negBase, posMult, negMult, posLevels, negLevels


def getNoiseEstimateFromRegion(spectrum, strip):
    """
    Get the noise estimate from the visible region of the strip

    :param spectrum:
    :param strip:
    :return:
    """

    # calculate the region over which to estimate the noise
    selectedRegion = [strip.getAxisRegion(0), strip.getAxisRegion(1)]
    for n in strip.orderedAxes[2:]:
        selectedRegion.append((n.region[0], n.region[1]))
    sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]

    # get indexing for spectrum onto strip.axisCodes
    indices = getAxisCodeMatchIndices(spectrum.axisCodes, strip.axisCodes)

    if None in indices:
        return

    # map the spectrum selectedRegions to the strip
    axisCodeDict = collections.OrderedDict((code, sortedSelectedRegion[indices[ii]])
                                           for ii, code in enumerate(spectrum.axisCodes) if indices[ii] is not None)

    # add an exclusion buffer to ensure that getRegionData always returns a region,
    # otherwise region may be 1 plain thick which will contradict error trapping for peak fitting
    # (which requires at least 3 points in each dimension)
    # exclusionBuffer = [1] * spectrum.dimensionCount
    # however, this shouldn't be needed of the range is > valuePrePoint in each dimension

    foundRegions = spectrum.getRegionData(minimumDimensionSize=1, **axisCodeDict)

    if foundRegions:

        # just use the first region
        for region in foundRegions[:1]:
            dataArray, intRegion, *rest = region

            if dataArray.size:
                # calculate the noise values
                flatData = dataArray.flatten()

                std = np.std(flatData)
                max = np.max(flatData)
                min = np.min(flatData)
                mean = np.mean(flatData)

                value = NoiseEstimateTuple(mean=mean,
                                           std=std * 1.1 if std != 0 else 1.0,
                                           min=min, max=max,
                                           noiseLevel=None)

                # noise function is defined here, but needs cleaning up
                return _noiseFunc(value)


def getSpectrumNoise(spectrum):
    """
    Get the noise level for a spectrum. If the noise level is not already set it will
    be set at an estimated value.

    .. describe:: Input

    spectrum

    .. describe:: Output

    Float
    """
    if not spectrum.noiseLevel:
        noise = getNoiseEstimate(spectrum)
        spectrum.noiseLevel = noise.noiseLevel

    return noise


def getNoiseEstimate(spectrum):
    """Get an estimate of the noiseLevel from the spectrum

    noiseLevel is calculated as abs(mean) + 3.5 * SD

    Calculated from a random subset of points
    """
    # NOTE:ED more detail needed

    fractPerAxis = 0.04
    subsetFract = 0.25
    fract = 0.1
    maxSamples = 10000

    npts = spectrum.pointCounts

    # take % of points in each axis
    _fract = (fractPerAxis ** len(npts))
    nsamples = min(int(np.prod(npts) * _fract), maxSamples)
    nsubsets = max(1, int(nsamples * subsetFract))

    with notificationEchoBlocking():
        return _getNoiseEstimate(spectrum, nsamples, nsubsets, fract)


def getContourEstimate(spectrum):
    """Get an estimate of the contour settings from the spectrum
    Calculated from a random subset of points
    """

    fractPerAxis = 0.04
    subsetFract = 0.01
    fract = 0.1
    maxSamples = 10000

    npts = spectrum.pointCounts

    # take % of points in each axis
    _fract = (fractPerAxis ** len(npts))
    nsamples = min(int(np.prod(npts) * _fract), maxSamples)
    nsubsets = max(1, int(nsamples * subsetFract))

    with notificationEchoBlocking():
        return _getContourEstimate(spectrum, nsamples, nsubsets, fract)


def _noiseFunc(value):
    # take the 'value' NoiseEstimateTuple and add the noiseLevel
    return NoiseEstimateTuple(mean=value.mean,
                              std=value.std,
                              min=value.min, max=value.max,
                              noiseLevel=abs(value.mean) + 3.5 * value.std)


def _getNoiseEstimate(spectrum, nsamples=1000, nsubsets=10, fraction=0.1):
    """
    Estimate the noise level for a spectrum.

    'nsamples' random samples are taken from the spectrum
    'nsubsets' is the number of random permutations of data taken from the
    and finding subsets with the lowest standard deviation

    A tuple (mean, SD, min, max noiseLevel) is returned from the subset with the lowest standard deviation.
    mean is the mean of the minimum random subset, SD is the standard deviation, min/max are the minimum/maximum values,
    and noiseLevel is the estimated noiseLevel caluated as abs(mean) + 3.5 * SD

    :param spectrum: input spectrum
    :param nsamples: number reandom samples
    :param nsubsets: number of subsets
    :param fraction: subset fraction
    :return: tuple(mean, SD, min, max, noiseLevel)
    """

    npts = spectrum.pointCounts
    if not isinstance(nsamples, int):
        raise TypeError('nsamples must be an int')
    if not (0 < nsamples <= np.prod(npts)):
        raise ValueError(f'nsamples must be in range [1, {np.prod(npts)}]')
    if not isinstance(nsubsets, int):
        raise TypeError('nsubsets must be an int')
    if not (0 < nsubsets <= nsamples):
        # not strictly necessary but stops huge values
        raise ValueError(f'nsubsets must be in range [1, {nsamples}]')
    if not isinstance(fraction, float):
        raise TypeError('fraction must be a float')
    if not (0 < fraction <= 1.0):
        raise ValueError('fraction must be i the range (0, 1]')

    # create a list of random points in the spectrum, get only points that are not nan/inf
    # getPositionValue is the slow bit
    allPts = [[min(n - 2, int(n * random.random())) for n in npts] for i in range(nsamples)]
    _list = np.array([spectrum.getPositionValue(pt) for pt in allPts], dtype=np.float32)
    data = _list[np.isfinite(_list)]
    fails = nsamples - len(data)

    if fails:
        getLogger().warning(f'Attempt to access {fails} non-existent data points in spectrum {spectrum}')

    # check whether there are too many bad numbers in the data
    good = nsamples - fails
    if good == 0:
        getLogger().warning(f'Spectrum {spectrum} contains all bad points')
        return NoiseEstimateTuple(mean=None, std=None, min=None, max=None, noiseLevel=1.0)
    elif good < 10:  # arbitrary number of bad points
        getLogger().warning(f'Spectrum {spectrum} contains minimal data')
        maxValue = max([abs(x) for x in data])
        if maxValue > 0:
            return NoiseEstimateTuple(mean=None, std=None, min=None, max=None, noiseLevel=0.1 * maxValue)
        else:
            return NoiseEstimateTuple(mean=None, std=None, min=None, max=None, noiseLevel=1.0)

    m = max(1, int(nsamples * fraction))

    def meanStd():
        # take m random values from data, and return mean/SD
        y = np.random.choice(data, m)
        return NoiseEstimateTuple(mean=np.mean(y), std=np.std(y), min=np.min(y), max=np.max(y), noiseLevel=None)

    # generate 'nsubsets' noiseEstimates and take the one with the minimum standard deviation
    value = min((meanStd() for i in range(nsubsets)), key=lambda mSD: mSD.std)
    value = NoiseEstimateTuple(mean=value.mean,
                               std=value.std * 1.1 if value.std != 0 else 1.0,
                               min=value.min, max=value.max,
                               noiseLevel=None)

    value = _noiseFunc(value)

    return value


def _getContourEstimate(spectrum, nsamples=1000, nsubsets=10, fraction=0.1):
    """
    Estimate the contour levels for a spectrum.

    'nsamples' random samples are taken from the spectrum
    'nsubsets' is the number of random permutations of data taken from the
    and finding subsets with the lowest standard deviation

    A tuple (mean, SD, min, max noiseLevel) is returned from the subset with the lowest standard deviation.
    mean is the mean of the minimum random subset, SD is the standard deviation, min/max are the minimum/maximum values,
    and noiseLevel is the estimated noiseLevel caluated as abs(mean) + 3.5 * SD

    :param spectrum: input spectrum
    :param nsamples: number reandom samples
    :param nsubsets: number of subsets
    :param fraction: subset fraction
    :return: tuple(mean, SD, min, max, noiseLevel)
    """

    npts = spectrum.pointCounts
    if not isinstance(nsamples, int):
        raise TypeError('nsamples must be an int')
    if not (0 < nsamples <= np.prod(npts)):
        raise ValueError(f'nsamples must be in range [1, {np.prod(npts)}]')
    if not isinstance(nsubsets, int):
        raise TypeError('nsubsets must be an int')
    if not (0 < nsubsets <= nsamples):
        # not strictly necessary but stops huge values
        raise ValueError(f'nsubsets must be in range [1, {nsamples}]')
    if not isinstance(fraction, float):
        raise TypeError('fraction must be a float')
    if not (0 < fraction <= 1.0):
        raise ValueError('fraction must be i the range (0, 1]')

    # create a list of random points in the spectrum, get only points that are not nan/inf
    # getPositionValue is the slow bit
    allPts = [[min(n - 2, int(n * random.random())) for n in npts] for i in range(nsamples)]
    _list = np.array([spectrum.getPositionValue(pt) for pt in allPts], dtype=np.float32)
    data = _list[np.isfinite(_list)]
    fails = nsamples - len(data)

    if fails:
        getLogger().warning(f'Attempt to access {fails} non-existent data points in spectrum {spectrum}')

    # check whether there are too many bad numbers in the data
    good = nsamples - fails
    if good == 0:
        getLogger().warning(f'Spectrum {spectrum} contains all bad points')
        return NoiseEstimateTuple(mean=None, std=None, min=None, max=None, noiseLevel=1.0)
    elif good < 10:  # arbitrary number of bad points
        getLogger().warning(f'Spectrum {spectrum} contains minimal data')
        maxValue = max([abs(x) for x in data])
        if maxValue > 0:
            return NoiseEstimateTuple(mean=None, std=None, min=None, max=None, noiseLevel=0.1 * maxValue)
        else:
            return NoiseEstimateTuple(mean=None, std=None, min=None, max=None, noiseLevel=1.0)

    value = NoiseEstimateTuple(mean=None,
                               std=None,
                               min=np.min(data), max=np.max(data),
                               noiseLevel=None)

    return value


def _signalToNoiseFunc(noise, signal):
    snr = math.log10(abs(np.mean(signal) ** 2 / np.mean(noise) ** 2))
    return snr


def estimateSignalRegion(y, nlMax=None, nlMin=None):
    if y is None: return 0
    if nlMax is None or nlMin is None:
        nlMax, nlMin = estimateNoiseLevel1D(y)
    eS = np.where(y >= nlMax)
    eSN = np.where(y <= nlMin)
    eN = np.where((y < nlMax) & (y > nlMin))
    estimatedSignalRegionPos = y[eS]
    estimatedSignalRegionNeg = y[eSN]
    estimatedSignalRegion = np.concatenate((estimatedSignalRegionPos, estimatedSignalRegionNeg))
    estimatedNoiseRegion = y[eN]
    lenghtESR = len(estimatedSignalRegion)
    lenghtENR = len(estimatedNoiseRegion)
    if lenghtESR > lenghtENR:
        l = lenghtENR
    else:
        l = lenghtESR
    if l == 0:
        return np.array([])
    else:
        noise = estimatedNoiseRegion[:l - 1]
        signalAndNoise = estimatedSignalRegion[:l - 1]
        signal = abs(signalAndNoise - noise)
        signal[::-1].sort()  # descending
        noise[::1].sort()
        if hasattr(signal, 'compressed') and hasattr(noise, 'compressed'):
            signal = signal.compressed()  # remove the mask
            noise = noise.compressed()  # remove the mask
        s = signal[:int(l / 2)]
        n = noise[:int(l / 2)]
        if len(signal) == 0:
            return np.array([])
        else:
            return s


def estimateSNR(noiseLevels, signalPoints, factor=2.5):
    """
    SNratio = factor*(height/|NoiseMax-NoiseMin|)
    :param noiseLevels: (max, min) floats
    :param signalPoints: iterable of floats estimated to be signal or peak heights
    :param factor: default 2.5
    :return: array of snr for each point compared to the delta noise level
    """
    maxNL = np.max(noiseLevels)
    minNL = np.min(noiseLevels)
    dd = abs(maxNL - minNL)
    pp = np.array([s for s in signalPoints])
    if dd != 0 and dd is not None:
        snRatios = (factor * pp) / dd
        return abs(snRatios)
    return [None] * len(signalPoints)


def estimateNoiseLevel1D(y, f=10, stdFactor=0.5):
    """

    :param y: the y region of the spectrum.
    :param f: percentage of the spectrum to use. If given a portion known to be just noise, set it to 100.
    :param increaseBySTD: increase the estimated by the STD for the y region
    :param stdFactor: 0 to don't adjust the initial guess.
    :return:   (float, float) of estimated noise threshold  as max and min
    """

    eMax, eMin = 0, 0
    if stdFactor == 0:
        stdFactor = 0.01
        getLogger().warning('stdFactor of value zero is not allowed.')
    if y is None:
        return eMax, eMin
    percent = percentage(f, int(len(y)))
    fy = y[:int(percent)]

    stdValue = np.std(fy) * stdFactor

    eMax = np.max(fy) + stdValue
    eMin = np.min(fy) - stdValue
    return eMax, eMin


def _filterROI1Darray(x, y, roi):
    """ Return region included in the ROI ppm position"""
    mask = _getMaskedRegionInsideLimits(x, roi)
    return x[mask], y[mask]

def _getMaskedRegionInsideLimits(x, limits):
    """
    Return an array of Booleans for the condition.
    True if the point in the array is within the limits, False otherwise.
    Limits and Array can be positives and/or negatives
    """
    import numpy.ma as ma
    mask = ma.masked_inside(x, *limits)
    return mask.mask


def _filtered1DArray(data, ignoredRegions):
    # returns an array without ignoredRegions. Used for automatic 1d peak picking
    ppmValues = data[0]
    masks = []
    ignoredRegions = [sorted(pair, reverse=True) for pair in ignoredRegions]
    for region in ignoredRegions:
        mask = (ppmValues > region[0]) | (ppmValues < region[1])
        masks.append(mask)
    fullmask = [all(mask) for mask in zip(*masks)]
    newArray = (np.ma.MaskedArray(data, mask=np.logical_not((fullmask, fullmask))))
    return newArray


def _initExpBoundResonances(experiment):
    """
    # CCPNInternal  - API Level routine -
    Refresh the covalently bound status for any resonances connected
    via peaks in a given experiment.
    """
    resonances = {}
    for spectrum in experiment.dataSources:
        for peakList in spectrum.peakLists:
            for peak in peakList.peaks:
                for peakDim in peak.peakDims:
                    for contrib in peakDim.peakDimContribs:
                        resonances[contrib.resonance] = None
    for resonance in resonances.keys():
        _getBoundResonances(resonance, recalculate=True)


def _setApiExpTransfers(experiment, overwrite=True):
    """
    # CCPNInternal  - API Level routine -
    Set up the ExpTransfers for an experiment using available refExperiment
    information. Boolean option to remove any existing transfers.
    List of Nmr.ExpTransfers
    """

    if not experiment.refExperiment:
        for expTransfer in experiment.expTransfers:
            expTransfer.delete()

        _initExpBoundResonances(experiment)
        return

    if experiment.expTransfers:
        if not overwrite:
            return list(experiment.expTransfers)
        else:
            for expTransfer in experiment.expTransfers:
                expTransfer.delete()

    visibleSites = {}
    for expDim in experiment.expDims:
        for expDimRef in expDim.expDimRefs:
            if not expDimRef.refExpDimRef:
                continue

            measurement = expDimRef.refExpDimRef.expMeasurement
            if measurement.measurementType in ('Shift', 'shift', 'MQShift'):
                for atomSite in measurement.atomSites:
                    if atomSite not in visibleSites:
                        visibleSites[atomSite] = []

                    visibleSites[atomSite].append(expDimRef)

    transferDict = {}
    for atomSite in visibleSites:
        expDimRefs = visibleSites[atomSite]

        for expTransfer in atomSite.expTransfers:
            atomSiteA, atomSiteB = expTransfer.atomSites

            if (atomSiteA in visibleSites) and (atomSiteB in visibleSites):
                if transferDict.get(expTransfer) is None:
                    transferDict[expTransfer] = []
                transferDict[expTransfer].extend(expDimRefs)

    # Indirect transfers, e.g. Ch_hC.NOESY or H_hC.NOESY
    indirectTransfers = set()
    for expGraph in experiment.refExperiment.nmrExpPrototype.expGraphs:
        for expTransfer in expGraph.expTransfers:
            if (expTransfer not in transferDict) and \
                    (expTransfer.transferType in longRangeTransfers):
                atomSiteA, atomSiteB = expTransfer.atomSites

                if atomSiteA not in visibleSites:
                    for expTransferA in atomSiteA.expTransfers:
                        if expTransferA.transferType != 'onebond':
                            continue

                        atomSites = list(expTransferA.atomSites)
                        atomSites.remove(atomSiteA)
                        atomSiteC = atomSites[0]

                        if atomSiteC in visibleSites:
                            atomSiteA = atomSiteC
                            break

                if atomSiteB not in visibleSites:
                    for expTransferB in atomSiteB.expTransfers:
                        if expTransferB.transferType != 'onebond':
                            continue

                        atomSites = list(expTransferB.atomSites)
                        atomSites.remove(atomSiteB)
                        atomSiteD = atomSites[0]

                        if atomSiteD in visibleSites:
                            atomSiteB = atomSiteD
                            break

                if (atomSiteA in visibleSites) and (atomSiteB in visibleSites):
                    expDimRefsA = visibleSites[atomSiteA]
                    expDimRefsB = visibleSites[atomSiteB]
                    transferDict[expTransfer] = expDimRefsA + expDimRefsB
                    indirectTransfers.add(expTransfer)

    expTransfers = []
    for refTransfer in transferDict.keys():
        expDimRefs = frozenset(transferDict[refTransfer])
        if len(expDimRefs) == 2:
            transferType = refTransfer.transferType
            expTransfer = experiment.findFirstExpTransfer(expDimRefs=expDimRefs)

            if expTransfer:
                # normally this would not need setting
                # but we renamed NOESY to through-space so this catches that situation
                expTransfer.transferType = transferType
            else:
                expTransfer = experiment.newExpTransfer(transferType=transferType,
                                                        expDimRefs=expDimRefs)

            if refTransfer in indirectTransfers:
                isDirect = False
            else:
                isDirect = True

            expTransfer.isDirect = isDirect
            expTransfers.append(expTransfer)

    _initExpBoundResonances(experiment)
    return expTransfers


def _getAcqRefExpDimRef(refExperiment):
    """
    # CCPNInternal  - API Level routine -
    RefExpDimRef that corresponds to acquisition dimension
    """

    # get acquisition measurement
    expGraph = refExperiment.nmrExpPrototype.findFirstExpGraph()
    # even if there are several the acquisition dimension should be common.
    ll = [(expStep.stepNumber, expStep) for expStep in expGraph.expSteps]
    expSteps = [x[1] for x in sorted(ll)]
    if refExperiment.isReversed:
        acqMeasurement = expSteps[0].expMeasurement
    else:
        acqMeasurement = expSteps[-1].expMeasurement

    # get RefExpDimRef that fits measurement
    ll = []
    for refExpDim in refExperiment.sortedRefExpDims():
        for refExpDimRef in refExpDim.sortedRefExpDimRefs():
            if refExpDimRef.expMeasurement is acqMeasurement:
                ll.append(refExpDimRef)

    if len(ll) == 1:
        return ll[0]
    else:
        raise RuntimeError("%s has no unambiguous RefExpDimRef for acqMeasurement (%s)"
                           % (refExperiment, acqMeasurement))


def _getAcqExpDim(experiment, ignorePreset=False):
    """
    # CCPNInternal  - API Level routine -
    ExpDim that corresponds to acquisition dimension. NB uses heuristics
    """

    ll = experiment.findAllExpDims(isAcquisition=True)
    if len(ll) == 1 and not ignorePreset:
        # acquisition dimension set - return it
        result = ll.pop()

    else:
        # no reliable acquisition dimension set
        result = None

        dataSources = experiment.sortedDataSources()
        if dataSources:
            dataSource = dataSources[0]
            for ds in dataSources[1:]:
                # more than one data source. Pick one of the largest.
                if ds.numDim > dataSource.numDim:
                    dataSource = ds

            # Take dimension with most points
            useDim = None
            currentVal = -1
            for dd in dataSource.sortedDataDims():
                if hasattr(dd, 'numPointsOrig'):
                    val = dd.numPointsOrig
                else:
                    val = dd.numPoints
                if val > currentVal:
                    currentVal = val
                    useDim = dd

            if useDim is not None:
                result = useDim.expDim

        if result is None:
            # no joy so far - just take first ExpDim
            ll = experiment.sortedExpDims()
            if ll:
                result = ll[0]

    return result


def _getRefExpDim4ExpDim(expDim):
    """
    get the link between refExpDim and expDim through their children refExpDimRef and expDimRef.
    """
    refExpDim = None
    for expDimRef in expDim.expDimRefs:
        if expDimRef.refExpDimRef:
            refExpDim = expDimRef.refExpDimRef.refExpDim
            break
    return refExpDim


def _tempLinkRefExpDim2ExpDim(expDim, refExpDim):
    """
    Temporary link expDim and refExpDim through their sorted children refExpDimRefs and expDimRefs.
    The match refExpDimRef-expDimRef will be redone by isotope code.
    """
    if len(expDim.sortedExpDimRefs()) == len(refExpDim.sortedRefExpDimRefs()):
        for expDimRef, refExpDimRef in zip(expDim.sortedExpDimRefs(), refExpDim.sortedRefExpDimRefs()):
            expDimRef.setRefExpDimRef(refExpDimRef)


def _clearLinkToRefExp(experiment):
    for expDim in experiment.expDims:
        refExpDim = _getRefExpDim4ExpDim(expDim)
        if refExpDim:
            for expDimRef in expDim.expDimRefs:
                if expDimRef is not None:
                    if expDimRef.refExpDimRef:
                        expDimRef.setRefExpDimRef(None)


def _setApiRefExperiment(experiment, refExperiment):
    """
    # CCPNInternal  - API Level routine -
    Sets the reference experiment for an existing experiment
    and tries to map the ExpDims to RefExpDims appropriately.

    This routine is very convoluted. Should be simplified/reimplemented.
    We are only trying to make this link: expDimRef.refExpDimRef = refExpDimRef

        experiment------ expDim(s)-------expDimRef(s)
                                             *
        refExperiment---refExpDim(s)----refExpDimRef(s)

    """

    _clearLinkToRefExp(experiment)

    experiment.setRefExperiment(refExperiment)
    if refExperiment is None:
        return

    refExpDims = refExperiment.sortedRefExpDims()
    if not refExpDims:
        # Something is wrong with the reference data
        return

    expDims = experiment.sortedExpDims()
    if not expDims:
        # Something is wrong with the experiment
        return

    acqRefExpDim = _getAcqRefExpDimRef(refExperiment).refExpDim
    acqExpDim = _getAcqExpDim(experiment, ignorePreset=True)

    if ((refExpDims.index(acqRefExpDim) * 2 < len(refExpDims)) !=
            (expDims.index(acqExpDim) * 2 < len(expDims))):
        # acqRefExpDim and acqExpDim are at opposite ends of their
        # respective lists. reverse refExpDims so that acquisition
        # dimensions will more likely get mapped to each other.
        refExpDims.reverse()

    # Rasmus 12/7/12. Must be set to None, as otherwise it is never reset below.
    # We do not want the heuristic _getAcqExpDim to override everything else.
    acqExpDim = None

    for expDim in expDims:
        expData = []

        for expDimRef in expDim.expDimRefs:
            isotopes = frozenset(expDimRef.isotopeCodes)

            if isotopes:
                mType = expDimRef.measurementType.lower()
                expData.append((mType, isotopes))

        if not expData:
            continue

        for refExpDim in refExpDims:
            refData = []

            for refExpDimRef in refExpDim.refExpDimRefs:
                expMeasurement = refExpDimRef.expMeasurement
                isotopes = frozenset([x.isotopeCode for x in expMeasurement.atomSites])
                mType = expMeasurement.measurementType.lower()
                refData.append((mType, isotopes))

            if expData == refData:
                # expDim.refExpDim = refExpDim # this link is not anymore in the v3 API.  set refExpDimRefs and expDimRefs directly
                _tempLinkRefExpDim2ExpDim(expDim, refExpDim)
                refExpDims.remove(refExpDim)

                if refExpDim is acqRefExpDim:
                    if not acqExpDim:
                        expDim.isAcquisition = True
                        acqExpDim = expDim

                break
    for expDim in expDims:
        if not expDim.expDimRefs:
            continue

        if not _getRefExpDim4ExpDim(expDim):
            if len(refExpDims)>0:
                refExpDim = refExpDims.pop(0)
                _tempLinkRefExpDim2ExpDim(expDim, refExpDim)

        # set reference data comparison list
        _refExpDim = _getRefExpDim4ExpDim(expDim)
        if _refExpDim:
            refExpDimRefs = list(_refExpDim.refExpDimRefs)
            refData = []
            for refExpDimRef in refExpDimRefs:
                expMeasurement = refExpDimRef.expMeasurement
                atomSites = expMeasurement.atomSites
                refData.append((frozenset(x.isotopeCode for x in atomSites),
                                expMeasurement.measurementType.lower(),
                                frozenset(x.name for x in atomSites),
                                refExpDimRef))

            # set experiment data comparison list
            inData = []
            for expDimRef in expDim.expDimRefs:
                inData.append((frozenset(expDimRef.isotopeCodes),
                               expDimRef.measurementType.lower(),
                               frozenset(((expDimRef.displayName),)),
                               expDimRef))

            # match expDimRef to refExpDimRef. comparing isotopeCodes,
            # if equal measurementTypes, if equal name/displayname
            for end in (-1, -2, -3):
                for ii in range(len(inData) - 1, -1, -1):
                    for jj in range(len(refData) - 1, -1, -1):
                        if inData[ii][:end] == refData[jj][:end]:
                            expDimRef = inData[ii][-1]
                            expDimRef.refExpDimRef = refData[jj][-1]
                            expDimRef.measurementType = refData[jj][-1].expMeasurement.measurementType
                            del inData[ii]
                            del refData[jj]
                            break
