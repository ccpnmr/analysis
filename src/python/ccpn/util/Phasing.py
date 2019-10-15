"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy
from scipy import signal

from typing import Sequence


def phaseRealData(data: Sequence[float], ph0: float = 0.0, ph1: float = 0.0,
                  pivot: float = 1.0) -> Sequence[float]:
    # data is the (1D) spectrum data (real)
    # ph0 and ph1 are in degrees

    data = numpy.array(data)
    data = signal.hilbert(data)  # convert real to complex data in best way possible
    data = phaseComplexData(data, ph0, ph1, pivot)
    data = data.real

    return data


def phaseComplexData(data: Sequence[complex], ph0: float = 0.0, ph1: float = 0.0,
                     pivot: float = 1.0) -> Sequence[complex]:
    # data is the (1D) spectrum data (complex)
    # ph0 and ph1 are in degrees

    data = numpy.array(data)

    ph0 *= numpy.pi / 180.0
    ph1 *= numpy.pi / 180.0
    pivot -= 1  # points start at 1 but code below assumes starts at 0

    npts = len(data)
    angles = ph0 + (numpy.arange(npts) - pivot) * ph1 / npts
    multipliers = numpy.exp(-1j * angles)

    data *= multipliers

    return data


def autoPhaseReal(data, fn, p0=0.0, p1=0.0):
    """
    Automatic linear phase correction from NmrGlue
    Parameters
    ----------
    data : ndarray
        Array of NMR intensity data.
    fn : str or function
        Algorithm to use for phase scoring. Built in functions can be
        specified by one of the following strings: "acme", "peak_minima"
    p0 : float
        Initial zero order phase in degrees.
    p1 : float
        Initial first order phase in degrees.

    Returns
    -------
    ndata : ndarray
        Phased NMR data.

    """
    import nmrglue as ng

    data = signal.hilbert(data)  # convert real to complex data in best way possible
    data = ng.proc_autophase.autops(data, fn, p0=p0, p1=p1)
    data = data.real
    return data
