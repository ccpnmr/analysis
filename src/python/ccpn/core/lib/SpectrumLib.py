"""Spectrum-related functions and utilities
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import typing
import collections

from ccpn.core.Project import Project
from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import getExpClassificationDict
from ccpnmodel.ccpncore.lib.Io import Formats

import numpy as np

MagnetisationTransferTuple = collections.namedtuple('MagnetisationTransferTuple',
  ['dimension1', 'dimension2', 'transferType', 'isIndirect']
)


def getExperimentClassifications(project:Project) -> dict:
  """
  Get a dictionary of dictionaries of dimensionCount:sortedNuclei:ExperimentClassification named tuples.
  """
  return getExpClassificationDict(project._wrappedData)


# def _oldEstimateNoiseLevel1D(x, y, factor=3):
#   '''
#   :param x,y:  spectrum.positions, spectrum.intensities
#   :param factor: optional. Increase factor to increase the STD and therefore the noise level threshold
#   :return: float of estimated noise threshold
#   '''
#
#   data = np.array([x, y])
#   dataStd = np.std(data)
#   data = np.array(data, np.float32)
#   data = data.clip(-dataStd, dataStd)
#   value = factor * np.std(data)
#   return value


def _oldEstimateNoiseLevel1D(y, factor=0.5):
  '''
  Estimates the noise threshold based on the max intensity of the first portion of the spectrum where
  only noise is present. To increase the threshold value: increase the factor.
  return:  float of estimated noise threshold
  '''
  if y is not None:
    # print('_oldEstimateNoiseLevel1D',max(y[:int(len(y)/20)]) * factor, 'STD, ')
    return max(y[:int(len(y)/20)]) * factor
  else:
    return 0


def _calibrateX1D(spectrum, currentPosition, newPosition):
  shift = newPosition - currentPosition
  spectrum.positions = spectrum.positions+shift


def _calibrateY1D(spectrum, currentPosition, newPosition):
  shift = newPosition - currentPosition
  spectrum.intensities = spectrum.intensities+shift


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


'''
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

'''




from scipy.sparse import csc_matrix, eye, diags
from scipy import sparse
from scipy.sparse.linalg import spsolve



'''
Asl algorithm
'''


def als(y, lam=10 ** 2, p=0.001, nIter=10):

  """Implements an Asymmetric Least Squares Smoothing
  baseline correction algorithm
  H C Eilers, Paul & F M Boelens, Hans. (2005). Baseline Correction with Asymmetric Least Squares Smoothing. Unpubl. Manuscr. . 

  y = signal
  lam = smoothness, 10**2 ≤ λ ≤ 10**9.
  p = asymmetry, 0.001 ≤ p ≤ 0.1 is a good choice for a signal with positive peaks.
  niter = Number of iteration , default 10.

  """

  L = len(y)
  D = sparse.csc_matrix(np.diff(np.eye(L), 2))
  w = np.ones(L)
  for i in range(nIter):
    W = sparse.spdiags(w, 0, L, L)
    Z = W + lam * D.dot(D.transpose())
    z = spsolve(Z, w*y)
    w = p * (y > z) + (1-p) * (y < z)
  return z




###################################################################################################


'''
Whittaker Smooth algorithm
'''


def WhittakerSmooth(y, w, lambda_, differences=1):
  '''
  no licence , source from web
  Penalized least squares algorithm for background fitting

  input
      x: input data (i.e. chromatogram of spectrum)
      w: binary masks (value of the mask is zero if a point belongs to peaks and one otherwise)
      lambda_: parameter that can be adjusted by user. The larger lambda is,  the smoother the resulting background
      differences: integer indicating the order of the difference of penalties

  output
      the fitted background vector
  '''
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

'''
airPLS algorithm
'''

def airPLS(y, lambda_=100, porder=1, itermax=15):
  '''
  no licence , source from web
  Adaptive iteratively reweighted penalized least squares for baseline fitting

  input
      x: input data (i.e. chromatogram of spectrum)
      lambda_: parameter that can be adjusted by user. The larger lambda is,  the smoother the resulting background, z
      porder: adaptive iteratively reweighted penalized least squares for baseline fitting

  output
      the fitted background vector
  '''
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


'''
polynomial Fit algorithm
'''


def polynomialFit(x, y, order:int=3):
  '''
  :param x: x values
  :param y: y values
  :param order: polynomial order
  :return: fitted baseline
  '''
  fit = np.polyval(np.polyfit(x, y, deg=order), x)
  return fit



###################################################################################################


'''
arPLS algorithm
'''


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

    E=eye(N,format='csc')
    # numpy.diff() does not work with sparse matrix. This is a workaround.
    # It creates the second order difference matrix.
    # [1 -2 1 ......]
    # [0 1 -2 1 ....]
    # [.............]
    # [.... 0 1 -2 1]
    D=E[:-2]-2*E[1:-1]+E[2:]

    H = lambda_*D.T*D
    Y = np.matrix(y)

    w = np.ones(N)

    for i in range(itermax+10):
        W=diags(w,0,shape=(N,N))
        Q = W+H
        B = W*Y.T

        z=spsolve(Q,B)
        d = y-z
        dn = d[d<0.0]

        m = np.mean(dn)
        if np.isnan(m):
            # add a tiny bit of noise to Y
            y2 = y.copy()
            if np.std(y) != 0.:
                y2 += (np.random.random(y.size)-0.5)*np.std(y)/1000.
            elif np.mean(y) != 0.0 :
                y2 += (np.random.random(y.size)-0.5)*np.mean(y)/1000.
            else:
                y2 += (np.random.random(y.size)-0.5)/1000.
            y = y2
            Y = np.matrix(y2)
            W=diags(w,0,shape=(N,N))
            Q = W+H
            B = W*Y.T

            z=spsolve(Q,B)
            d = y-z
            dn = d[d<0.0]

            m = np.mean(dn)
        s = np.std(dn,ddof=1)

        wt = 1./(1 + np.exp(2. * (d - (2*s-m))/s))

        # check exit condition
        condition = np.linalg.norm(w-wt) / np.linalg.norm(w)
        if condition < ratio:
            break
        if i > itermax:
            break
        w = wt

    return z




###################################################################################################


'''
Implementation of the  arPLS algorithm
'''


def arPLS_Implementation(y, lambdaValue=5.e4, maxValue=1e6, minValue=-1e6, itermax=10, interpolate=True):
  """
  maxValue = maxValue of the baseline noise
  minValue = minValue of the baseline noise
  interpolate: Where are the peaks: interpolate the points from neighbours otherwise set them to 0.

  """

  lenghtY = len(y)
  sparseMatrix=eye(lenghtY, format='csc')
  differenceMatrix = sparseMatrix[:-2] - 2*sparseMatrix[1:-1] + sparseMatrix[2:]
  H = lambdaValue * differenceMatrix.T * differenceMatrix

  Y = np.matrix(y)
  w = np.ones(lenghtY)

  for i in range(itermax):
    W=diags(w,1,shape=(lenghtY,lenghtY))
    Q = W+H
    B = W*Y.T
    z=spsolve(Q,B)
    mymask = (z >maxValue) | (z < minValue)
    b = np.ma.masked_where(mymask, z)
    if interpolate:
      c = np.interp(np.where(mymask)[0], np.where(~mymask)[0], b[np.where(~mymask)[0]])
      b[np.where(mymask)[0]] = c
    else:
      b = np.ma.filled(b, fill_value=0)

  return b


def lowess(x,y):
  '''
   LOWESS (Locally Weighted Scatterplot Smoothing)
  A lowess function that outs smoothed estimates of endog
  at the given exog values from points (exog, endog)
  To use this, you need to install statsmodels in your miniconda:
   - conda install statsmodels or pip install --upgrade --no-deps statsmodels
  '''

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
