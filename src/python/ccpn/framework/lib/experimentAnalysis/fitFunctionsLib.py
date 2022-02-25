"""
This module defines the various fitting functions for Series Analysis
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-02-25 15:14:19 +0000 (Fri, February 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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

## a series of Fittingls. Called recursively with from the Minimiser
gaussian_func    = ls.gaussian
lorentzian_func  = ls.lorentzian
linear_func      = ls.linear
parabolic_func   = ls.parabolic
exponential_func = ls.exponential
lognormal_func   = ls.lognormal
pearson7_func    = ls.pearson7
students_t_func  = ls.students_t
powerlaw_func    = ls.powerlaw


def fractionBound_func(p, l, kd):
    """
    #FittingFunc. Called recursively with from the  Minimiser
    Eq. 6 from  M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
    :param p:
    :param l:
    :param kd:
    :return: l, kd
    """
    qd = np.sqrt(((p + l + kd) ** 2) - 4 * p * l)
    return ((p + l + kd - qd) / 2)

def oneSiteBinding_func(x, kd, bmax):
    """
    #FittingFunc. Called recursively with from the Minimiser
    :param x: 1d array
    :param kd: the initial kd value
    :param bmax:
    :return:
    """
    return (bmax * x) / (x + kd)

########################################################################################################################
########################                     Various Calculation Functions                   ###########################
########################################################################################################################

def r2_func(y, redchi):
    """
    Calculate the R2 (called from the minimiser results).
    :param redchi: Chi-square. From the Minimiser Obj can be retrieved as "result.redchi"
    :return: r2
    """
    r2 = 1 - redchi / np.var(y, ddof=2)
    return r2

def euclideanDistance_func(array1, array2, alphaFactors):
    """
    Calculate the  Euclidean Distance of two set of coordinates using scaling factors. Used in CSM DeltaDeltas
    :param array1: (1d array), coordinate 1
    :param array2: (1d array), coordinate 2 of same shape of array1
    :param alphaFactors: the scaling factors.  same shape of array1 and 2.
    :return: float
    Ref.: Eq.(9) from: M.P. Williamson Progress in Nuclear Magnetic Resonance Spectroscopy 73 (2013) 1–16
    """
    deltas = []
    for a, b, factor in zip(array1, array2, alphaFactors):
        delta = a - b
        delta *= factor
        delta **= 2
        deltas.append(delta)
    return np.sqrt(np.sum(np.array(deltas)))
