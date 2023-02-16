"""
This module defines the various calculation/fitting functions for
Spectral density mapping  in the Series Analysis module.

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
__dateModified__ = "$dateModified: 2023-02-16 17:44:59 +0000 (Thu, February 16, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from lmfit import lineshapes as ls
import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.experimentConstants as constants
from math import pi
from random import random, randint
from math import sqrt, exp
import pandas as pd


############################################################
########## Reduced Spectral Density Mapping analysis   #############
############################################################

def calculateSigmaNOE(noe, r1, gx, gh):
    """Calculate the sigma NOE value.
    Eq. 16 Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474"""

    return (noe - 1.0) * r1 * (gx / gh)

def calculateJ0(noe, r1, r2, d, c, gx, gh):
    """Calculate J(0).
     Eq. 13 Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474
    """
    sigmaNOE = calculateSigmaNOE(noe, r1, gx, gh)
    j0 = 3/(2*(3*d + c)) * (-(1/2)*r1 + r2 - (3/5)*sigmaNOE)
    return j0

def calculateJWx(noe, r1, r2, d, c, gx, gh):
    """Calculate J(wx).
     Eq. 14 Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474
    """
    sigmaNOE = calculateSigmaNOE(noe, r1, gx, gh)
    jwx = 1.0 / (3.0 * d + c) * (r1 - (7/5) * sigmaNOE)
    return jwx

def calculateJWH(noe, r1, r2, d, c, gx, gh):
    """Calculate J(wH).
     Eq. 15 Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474
    """
    sigmaNOE = calculateSigmaNOE(noe, r1, gx, gh)
    jwh = sigmaNOE / (5.0*d)
    return jwh

def _polifitJs(j0, jw, order=1):
    """ Fit J0 and Jw(H or N) to a first order polynomial, Return the slope  and intercept  from the fit, and the new fitted Y  """

    coef = slope, intercept = np.polyfit(j0, jw, order)
    poly1d_fn_coefJ0JWH = np.poly1d(coef)
    fittedY = poly1d_fn_coefJ0JWH(j0)
    return slope, intercept, fittedY

def _calculateMolecularTumblingCorrelationTime(omega, alpha, beta):
    """
    solve the Polynomial Structure -> ax^3 + bx^2 + cx + d = 0
    from eq. 18  Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474
    :param omega:
    :param alpha: the slope for the fitting J0 vs JwN
    :param beta: the intercept for the fitting J0 vs JwN
    :return:
    """
    a = 2 * alpha * (omega**2)
    b = 5 * beta * (omega**2)
    c = 2 * (alpha-1)
    d = 5 * beta
    values = np.roots([a,b,c,d])
    return values


############################################################
############      Estimate S2 and Tc  analysis         #################
############################################################

def _filterLowNoeFromR1R2(r1, r2, noe, noeExclusionLimit=0.65):
    mask = np.argwhere(noe > noeExclusionLimit).flatten()
    r1 = r1[mask]
    r2 = r2[mask]
    return r1, r2

def estimateAverageS2(r1, r2, func=np.median, noe=None, noeExclusionLimit=0.65):
    """
    Estimate the average generalized order parameters Sav2
    from experimentally observed R1R2.
    If Noe are given, filter out residues with Noes < noeExclusionLimit
    Eq 3. from  Effective Method for the Discrimination of
    Motional Anisotropy and Chemical Exchange Kneller et al. 2001.
    10.1021/ja017461k

    s2Av = sqRoot [ median(r1*r2) / max(r1*r2)  ]

    :param r1: array of R1 values
    :param r2: array of R2 values
    :param noe: array of  NOE values
    :param func: a calculation function to compute the  r1*r2. One of np.mean or np.median.
                            default: median
    :return: float: S2
    """
    if func not in [np.mean, np.median]:
        func =  np.median
    if noe is not None:
        r1, r2 = _filterLowNoeFromR1R2(r1, r2, noe, noeExclusionLimit)
    _pr = r1*r2
    _func = func(_pr)
    _max = np.max(_pr)
    sAv = np.sqrt(_func/_max)
    return sAv

def estimateOverallCorrelationTimeFromR1R2(r1, r2, spectrometerFrequency):
    """
    Ref:  Equation 6 from Fushman. Backbone dynamics of ribonuclease
    T1 and its complex with   2'GMP studied by
    two-dimensional heteronuclear N M R
    spectroscopy. Journal of Biomolecular NMR, 4 (1994) 61-78 .

    tc = [1 / (2omegaN) ]  * sqRoot[ (6*T1/ T2 ) -7 ]

    :param r1: array of R1 values
    :param r2: array of R2 values
    :return:  float.:  an estimation of the Overall Correlation Time Tc
    """
    t1 = 1/r1
    t2 = 1/r2
    omegaN = calculateOmegaN(spectrometerFrequency, scalingFactor=1e6)
    part1 =  1/(2*omegaN)
    part2 = np.sqrt( ((6*t1)/t2) - 7 )

    return  part1 * part2

############################################################
############   Lipari-Szabo (Model Free) analysis   #################
############################################################

# Original Isotropic model

def calculateOmegaH(spectrometerFrequency, scalingFactor=1e6):
    """
    :param spectrometerFrequency: float, the spectrometer Frequency in Mz
    :param scalingFactor:  float
    :return: float, OmegaH in Rad/s
    """
    return spectrometerFrequency * 2 * np.pi * scalingFactor  # Rad/s

def calculateOmegaN(spectrometerFrequency, scalingFactor=1e6):
    """
    :param spectrometerFrequency: float, the spectrometer Frequency in Mz
    :param scalingFactor:  float
    :return: float, OmegaN in Rad/s
    """
    omegaH = calculateOmegaH(spectrometerFrequency, scalingFactor)
    omegaN = omegaH * constants.GAMMA_N / constants.GAMMA_H
    return omegaN

def calculateOmegaC(spectrometerFrequency, scalingFactor=1e6):
    """
    :param spectrometerFrequency: float, the spectrometer Frequency in Mz
    :param scalingFactor:  float
    :return: float, OmegaC  (13C)  in Rad/s
    """
    omegaH = calculateOmegaH(spectrometerFrequency, scalingFactor)
    omegaC = omegaH * constants.GAMMA_C / constants.GAMMA_H
    return omegaC

def calculateIsotropicSpectralDensity(s2, rct, ict, w):
    """
    Calculate the J(w) using the original  Lipari-Szabo model
    for an isotropic system .
    eq. 11  Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474

    :param s2:  The generalised order parameter
    :param rct: the global rotational correlation time
    :param ict:  The effective internal correlation time
    :param w: omega
    :return: j

    """

    r = 1.0 / rct + 1.0 / ict
    t = 1.0 / r
    j = (s2 * rct) / (1.0 + w * w * rct * rct)
    j += ((1.0 - s2) * t) / (1.0 + w * w * t * t)
    return j * 0.4

def calculateIsotropicSpectralDensityExtended(s2, rct, w, s2f=1.0, ictfast=0, ictslow=0 ):
    """
    Calculate the J(w) using the extended  Lipari-Szabo model
    for an isotropic system .
    eq 8.  Backbone dynamics of Barstar: A 15N NMR relaxation study.
    Udgaonkar et al 2000. Proteins: 41:460-474
    :param s2:  The generalised order parameter
    :param rct:  or tm, the global rotational correlation time
    :param ict:  or te, The effective internal correlation time
    :param w: omega w for a given nuclei (eg. wN)
    :param s2f: The generalised order parameter for the faster motion
    :param ictfast: The effective internal correlation time for the faster motion.
    :param ictslow: The effective internal correlation time for the slower motion.
    :return: j
    """
    if ictfast == 0.0:
        ict_fast_p = 0.0
    else:
        ict_fast_p = 1.0 / (1.0 / rct + 1.0 / ictfast)

    if ictslow == 0.0:
        ict_slow_p = 0.0
    else:
        ict_slow_p = 1.0 / (1.0 / rct + 1.0 / ictslow)

    # The spectral density value
    _1 = s2 * rct / (1.0 + (rct * w) ** 2)
    _2 = (1.0 - s2f) * ict_fast_p / (1.0 + (ict_fast_p * w) ** 2)
    _3 = (s2f - s2) * ict_slow_p / (1.0 + (ict_slow_p * w) ** 2)
    j = 0.4 * (_1 + _2 + _3)
    
    return j

def calculate_d_factor(rNH,  cubicAngstromFactor=1e30):
    A = constants.REDUCED_PERM_VACUUM * constants.REDUCED_PLANK * constants.GAMMA_N * constants.GAMMA_H * cubicAngstromFactor
    A /= rNH ** 3.0
    A = A * A / 4.0
    return A

def calculate_c_factor(omegaN, csaN):
    C = omegaN * omegaN * csaN * csaN
    C /= 3.0
    return C

def _calculateR1(A, jN, jHpN, jHmN, C):
    """
    Calculate the longitudinal relaxation rate (R1)
    :param A: d_factor
    :param jN:
    :param jHpN:
    :param jHmN:
    :param C: c_factor
    :return:  R1
    """
    r1 = A * ((3 * jN) + (6 * jHpN) + jHmN) + C * jN
    return r1

def _calculateR2(A, C, j0, jH, jHmN, jHpN, jN, rex=0):
    """
    Calculate the transverse relaxation rate (R2)
    :param A: d_factor
    :param C: c_factor
    :param j0:
    :param jH:
    :param jHmN:
    :param jHpN:
    :param jN:
    :param rex:
    :return:  R2
    """
    r2 = 0.5 * A * ((4 * j0) + (3 * jN) + (6 * jHpN) + (6 * jH) + jHmN) + C * (2 * j0 / 3.0 + 0.5 * jN) + rex
    return r2

def _calculateNOEp(A, gammaHN, t1, jHpN, jHmN):
    """
    Calculate the steady-state NOE enhancement
    :param A: d_factor
    :param gammaHN:
    :param t1:
    :param jHpN:
    :param jHmN:
    :return:
    """
    return 1.0 + (A * gammaHN * t1 * ((6 * jHpN) - jHmN))

##### calculate the Ssquared, Te and Exchange from T1 T2 NOE using the original model-free

def calculateSpectralDensityContourLines(spectrometerFrequency=600.130,
                                         lenNh=1.0150,   ict=50.0,  csaN=-160.0,
                                         minS2=0.3,  maxS2=1.0, stepS2=0.1,
                                         minRct=5.0,  maxRct=14.0, stepRct=1.0,
                                         rctScalingFactor =  1e-9,
                                         ictScalingFactor = 1e-12):
    """
    Calculate the contouring lines using the isotropic model for S2 and the rotational correlation Time  (rct).
    Used to overlay with the T1 vs T2  in a scatter  plot.
    :param spectrometerFrequency:  default 600.130
    :param lenNh: NH bond Length. default 1.0150 Armstrong
    :param ict: the internalCorrelationTime Te
    :param csaN: value of the axially symmetric chemical shift tensor for 15N. Default -160 ppm
    :param minS2: minimum S2 contours value
    :param maxS2: max S2 contours value
    :param stepS2: single step on the curve
    :param minRct: minimum rotational correlation Time  (rct) contours value
    :param maxRct: max rct contours value
    :param stepRct: single step on the curve
    :return: tuple  rctLines, s2Lines
    """
    rctLines = []
    s2Lines = []
    omegaH = calculateOmegaH(spectrometerFrequency, scalingFactor=1e6)  # Rad/s
    omegaN = calculateOmegaN(spectrometerFrequency, scalingFactor=1e6)
    csaN /= 1e6  # Was  ppm
    A = calculate_d_factor(lenNh)
    C = calculate_c_factor(omegaN, csaN)
    rct = maxRct
    ict *= ictScalingFactor  # Seconds

    while rct >= minRct:
        line = []
        s2 = 50
        while s2 > 0.1:
            rctB = rct * rctScalingFactor  # Seconds
            jH = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaH)
            jN = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaN)
            jHpN = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaH + omegaN)
            jHmN = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaH - omegaN)
            j0 = calculateIsotropicSpectralDensity(s2, rctB, ict, 0.0)
            r1 = _calculateR1(A, jN, jHpN, jHmN, C)
            r2 = _calculateR2(A, C, j0, jH, jHmN, jHpN, jN)
            t1 = 1e3 / r1  # ms
            t2 = 1e3 / r2  # ms
            line.append([t1, t2])
            s2 /= 1.4
        rctLines.append([rct, line])
        rct -= stepRct

    s2 = maxS2
    while s2 >= minS2:
        line = []
        rct = 0.05
        while rct < 50:
            rctB = rct * rctScalingFactor  # Nanoseconds
            jH = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaH)
            jN = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaN)
            jHpN = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaH + omegaN)
            jHmN = calculateIsotropicSpectralDensity(s2, rctB, ict, omegaH - omegaN)
            j0 = calculateIsotropicSpectralDensity(s2, rctB, ict, 0.0)
            r1 = _calculateR1(A, jN, jHpN, jHmN, C)
            r2 = _calculateR2(A, C, j0, jH, jHmN, jHpN, jN)
            t1 = 1e3 / r1  # ms
            t2 = 1e3 / r2  # ms
            line.append([t1, t2])
            rct += 0.1
        s2Lines.append([s2, line])
        s2 -= stepS2

    return rctLines, s2Lines

def fitIsotropicModel(t1, t2, noe, sf, tmFix=None, teFix=None, s2Fix=None,
                      tmMin=1e-9, tmMax=100e-9, teMin=1e-12, teMax=1e-9,
                      csaN = 160 * 1e-6 , rNH = 1.015,
                      rexFix=None, rexMax=15.0, niter=10000):

    # rNH = 1.015
    # csaN = 160 * 1e-6  # 160 ppm
    omegaH = calculateOmegaH(sf, scalingFactor=1e6)
    omegaN = calculateOmegaN(sf, scalingFactor=1e6)
    gammaHN = constants.GAMMA_H /  constants.GAMMA_N

    A = calculate_d_factor(rNH)
    C = calculate_c_factor(omegaN, csaN)

    # Init params
    if s2Fix is None:
        s2Start = [x * 0.05 for x in range(1, 20)]
    else:
        s2Start = [s2Fix, ]

    if teFix is None:
        teStart = [x * 1e-12 for x in [10, 30, 70, 100, 300, 700, 1000]]
    else:
        teStart = [teFix, ]

    if tmFix is None:
        tmStart = [x * 1e-9 for x in range(1, 30)]
    else:
        tmStart = [tmFix, ]

    if rexFix is None:
        rexStart = [float(x) for x in range(int(rexMax))]
    else:
        rexStart = [rexFix, ]

    # Init ensemble of solutions
    ensemble = []
    for s2 in s2Start:
        for te in teStart:
            for tm in tmStart:
                for rex in rexStart:
                    ensemble.append((None, s2, te, tm, rex))

    # Init scores
    for k, (score, s2, te, tm, rex) in enumerate(ensemble):
        jH = calculateIsotropicSpectralDensity(s2, tm, te, omegaH)
        jN = calculateIsotropicSpectralDensity(s2, tm, te, omegaN)
        jHpN = calculateIsotropicSpectralDensity(s2, tm, te, omegaH + omegaN)
        jHmN = calculateIsotropicSpectralDensity(s2, tm, te, omegaH - omegaN)
        j0 = calculateIsotropicSpectralDensity(s2, tm, te, 0.0)

        r1 = _calculateR1(A, jN, jHpN, jHmN, C )
        r2 = _calculateR2(A, C, j0, jH, jHmN, jHpN, jN, rex)

        t1p = 1.0 / r1
        t2p = 1.0 / r2

        d1 = (t1p - t1) / t1
        d2 = (t2p - t2) / t2

        score = (d1 * d1) + (d2 * d2)

        if noe is None:
            noep = 0.0

        else:
            noep = _calculateNOEp(A, gammaHN, t1, jHpN, jHmN)
            dn = (noep - noe) / 2.0
            score += (dn * dn)

        ensemble[k] = (score, s2, te, tm, rex, t1p, t2p, noep)

    ensemble.sort()
    ensemble = ensemble[:10]
    ensembleSize = len(ensemble)

    bestScore = 1e99

    for i in range(niter):

        f = i / float(niter)
        f = exp(-10.0 * f)
        # Mutate

        ensemble.sort()
        prevScore, s2, te, tm, rex, t1p, t2p, noep = ensemble[-1]  # Biggest is worst

        if ensemble[0][0] < 1e-10:
            break

        if not s2Fix:
            # d = ((random() + 0.618 - 1.0) * f) + 1.0
            d = ((random() - 0.382) * f) + 1.0
            s2 = max(0.0, min(1.0, s2 * d))

        if not tmFix:
            d = ((random() - 0.382) * f) + 1.0
            tm = max(tmMin, min(tmMax, tm * d))

        if not teFix:
            d = ((random() - 0.382) * f) + 1.0
            te = max(teMin, min(teMax, te * d))

        d = ((random() - 0.382) * f) + 1.0
        rex = max(0.0, min(rexMax, rex * d))

        jH = calculateIsotropicSpectralDensity(s2, tm, te, omegaH)
        jN = calculateIsotropicSpectralDensity(s2, tm, te, omegaN)
        jHpN = calculateIsotropicSpectralDensity(s2, tm, te, omegaH + omegaN)
        jHmN = calculateIsotropicSpectralDensity(s2, tm, te, omegaH - omegaN)
        j0 = calculateIsotropicSpectralDensity(s2, tm, te, 0.0)

        r1 = _calculateR1(A, jN, jHpN, jHmN, C)
        r2 = _calculateR2(A, C, j0, jH, jHmN, jHpN, jN, rex)

        t1p = 1.0 / r1
        t2p = 1.0 / r2

        d1 = (t1p - t1) / t1
        d2 = (t2p - t2) / t2

        score = (d1 * d1) + (d2 * d2)
        if noe is None:
            noep = 0.0
        else:
            noep = _calculateNOEp(A, gammaHN, t1, jHpN, jHmN)
            dn = (noep - noe) / 2.0
            score += (dn * dn)

        ratio = exp(prevScore - score)

        if ratio > 1.0:  # random():
            ensemble[-1] = (score, s2, te, tm, rex, t1p, t2p, noep)
        else:
            k = randint(0, ensembleSize - 1)
            score, s2, te, tm, rex, t1p, t2p, noep = ensemble[k]
            ensemble[-1] = (score, s2, te, tm, rex, t1p, t2p, noep)

        if score < bestScore:
            bestScore = score

    return i, ensemble


def _fitIsotropicModelFromT1T2NOE(resultRSDM_dataframe, spectrometerFrequency=500.010, unit='s'):
    """
    :param resultRSDM_dataframe:
    :param spectrometerFrequency:
    :return:
    """
    T1 = np.array([])
    T2 = np.array([])
    NOE = np.array([])
    CODES = np.array([])

    resultDf = pd.DataFrame()
    initialDf = pd.DataFrame()

    if sv.T1 in resultRSDM_dataframe.columns:
        T1 = resultRSDM_dataframe[sv.T1].values
        T2 = resultRSDM_dataframe[sv.T2].values
        NOE = resultRSDM_dataframe[sv.HETNOE].values

    if sv.R1 in resultRSDM_dataframe.columns:
        R1 = resultRSDM_dataframe[sv.R1].values
        R2 = resultRSDM_dataframe[sv.R2].values
        NOE =  resultRSDM_dataframe[sv.HETNOE].values
        CODES = resultRSDM_dataframe[sv.NMRRESIDUECODE].values
        T1 = 1 / R1
        T2 = 1 / R2

    sf = spectrometerFrequency

    t1Unit = constants.MS_UNIT_MULTIPLIERS[unit]
    t2Unit = constants.MS_UNIT_MULTIPLIERS[unit]

    n = len(T1)
    n2 = n - 1
    jj = range(n)
    s2Best = [0.0] * n
    teBest = [0.0] * n
    rexBest = [0.0] * n

    t1s = [v for v in T1 if v]
    t2s = [v for v in T2 if v]
    noes = [v for v in NOE if v]

    m = len(t1s)

    t1 = sum(t1s) / float(m)
    t2 = sum(t2s) / float(m)
    noe = sum(noes) / float(m)

    t12 = [v / t2s[i] for i, v in enumerate(t1s) if v]
    t12m = sum(t12) / float(len(t12))
    deltas = [abs(v - t12m) / t12m for v in t12]
    w = [1.0 / (v * v) for v in deltas]

    t1 = sum([t1s[j] * w[j] for j in range(m)]) / sum(w)
    t2 = sum([t2s[j] * w[j] for j in range(m)]) / sum(w)

    if noes:
        noe = sum([noes[j] * w[j] for j in range(m)]) / sum(w)
    else:
        noe = None

    i, ensemble = fitIsotropicModel(t1, t2, noe, sf, tmFix=None, teFix=None, s2Fix=None,
                                    tmMin=1e-9, tmMax=100e-9, teMin=1e-12, teMax=1e-10,
                                    rexFix=0.0)
    ensemble.sort()
    score, s2, te0, tm0, rex, t1t, t2t, noet = ensemble[0]

    initialDf.loc['mean', sv.S2] = s2
    initialDf.loc['mean', sv.TE] = te0 * 1e12
    initialDf.loc['mean', sv.REX] = rex
    initialDf.loc['mean', sv.TM] = tm0 * 1e9
    initialDf.loc['mean', 'score'] = score

    # Do the individual
    for j in jj:
        t1 = T1[j]
        t2 = T2[j]
        noe = NOE[j]

        if t1 is None:
            continue

        seqCode = CODES[j]

        i, ensemble = fitIsotropicModel(t1, t2, noe, sf, tmFix=tm0, teFix=None, s2Fix=None,
                                        tmMin=tm0 * 0.1, tmMax=tm0 * 5, teMin=te0 / 100, teMax=te0 * 20,
                                        rexFix=0.0, rexMax=15.0)
        ensemble.sort()
        score, s2, te, tm, rex, t1t, t2t, noet = ensemble[0]

        if s2 > 0.995:
            i, ensemble = fitIsotropicModel(t1, t2, noe, sf, tmFix=tm0, teFix=None, s2Fix=None,
                                            teMin=te / 10, teMax=te * 10,
                                            rexFix=None, rexMax=15.0)
            ensemble.sort()
            score, s2, te, tm, rex, t1t, t2t, noet = ensemble[0]

        teBest[j] = te
        s2Best[j] = s2
        rexBest[j] = rex

        # data = (s2, te * 1e12, tm * 1e9, rex, t1, t1t, t2, t2t, noe or 0.0, noet, score, i)
        # print(seqCode,
        #       'S2: %5.3f Te: %5.1f Tm: %5.3f Rex: %5.3f T1: %5.3f %5.3f T2: %5.3f %5.3f NOE: %5.3f %5.3f %e %6d' % data)
        resultDf.loc[j, sv.NMRRESIDUECODE] = seqCode
        resultDf.loc[j, sv.S2] = s2
        resultDf.loc[j, sv.TE] = te * 1e12
        resultDf.loc[j, sv.REX] = rex
        resultDf.loc[j, sv.TM] = tm * 1e9
        resultDf.loc[j, 'iteration'] = i
        resultDf.loc[j, 'score'] = score

    return resultDf, initialDf #could put in the same df, with the initialDf as first row
