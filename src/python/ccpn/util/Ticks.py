"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
"""Ticks-related utilities
"""

import math


def _calcTicks(s0, s1, w, delta):
    if delta <= 0:
        return []

    n0 = int(math.ceil((s0 + w) / delta))
    n1 = int(math.floor((s1 - w) / delta))

    ticks = [x * delta for x in range(n0, n1 + 1)]

    return ticks


def _numberTicks(s0, s1, w, delta):
    return int(math.floor((s1 - s0 - 2 * w) / delta))


def findTicks(region):
    maxMajor = 5
    maxMinor = 25
    minDecimalPlaces = 0

    (r0, r1) = region
    s0 = float(min(r0, r1))
    s1 = float(max(r0, r1))
    d = s1 - s0
    dd = float(max(abs(r0), abs(r1)))

    A = 0.999
    B = 0.001
    w = B * d

    n = int(math.floor(math.log(A * d) / math.log(10)))
    deltaMajor = pow(10.0, n)
    t = 0
    if 5 * deltaMajor < d:
        deltaMajor = 5 * deltaMajor
        t = 2
    elif 2 * deltaMajor < d:
        deltaMajor = 2 * deltaMajor
        t = 1

    nticks = _numberTicks(s0, s1, w, deltaMajor)
    d = deltaMajor
    while 1:
        if t == 2:
            d = (2 * d) / 5
        else:
            d = d / 2
        nticks = _numberTicks(s0, s1, w, d)
        if nticks > maxMajor:
            break
        if t == 0:
            n = n - 1
        deltaMajor = d
        t = (t - 1) % 3

    majorTicks = _calcTicks(s0, s1, w, deltaMajor)

    if dd >= 1000:
        nn = int(math.floor(math.log(A * dd) / log(10)))
        numberDecimals = max(0, nn - n)
        majorFormat = '%%.%de' % numberDecimals
    else:
        numberDecimals = max(minDecimalPlaces, -n)
        majorFormat = '%%.%df' % numberDecimals

    d = deltaMinor = deltaMajor
    if t == 2:
        d = d / 5
    else:
        d = d / 2
    while 1:
        nticks = _numberTicks(s0, s1, w, d)
        if nticks > maxMinor:
            break
        deltaMinor = d
        t = (t - 1) % 3
        if (t == 2):
            d = (2 * d) / 5
        else:
            d = d / 2

    minorTicks = _calcTicks(s0, s1, w, deltaMinor)  # this includes majorTicks (so could remove those)

    return majorTicks, minorTicks, majorFormat
