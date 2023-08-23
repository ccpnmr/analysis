"""
Simple 1D PeakPicker; for testing only
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-08-23 12:57:13 +0100 (Wed, August 23, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC, SimplePeak
from numba import jit
import numpy as np
# from ccpn.framework.Application import getApplication

# @jit(nopython=True, nogil=True)
def _find1DMaxima(y, x, positiveThreshold, negativeThreshold=None, findNegative=False):
    """
    from https://gist.github.com/endolith/250860#file-readme-md which was translated from
    http://billauer.co.il/peakdet.html Eli Billauer, 3.4.05.
    Explicitly not copyrighted and any uses allowed.
    """
    maxtab = []
    mintab = []
    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN
    lookformax = True
    if negativeThreshold is None: negativeThreshold = 0

    for i in np.arange(len(y)):
        this = y[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        if lookformax:
            if not findNegative:  # just positives
                this = abs(this)
            if this < mx - positiveThreshold:
                maxtab.append((float(mxpos), float(mx)))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn + positiveThreshold:
                mintab.append((float(mnpos), float(mn)))
                mx = this
                mxpos = x[i]
                lookformax = True
    filteredNeg = []
    for p in mintab:
        pos, height = p
        if height <= negativeThreshold:
            filteredNeg.append(p)
    filtered = []
    for p in maxtab:
        pos, height = p
        if height >= positiveThreshold:
            filtered.append(p)
    return filtered, filteredNeg

class PeakPicker1D(PeakPickerABC):
    """A peak picker based on  Eli Billauer, 3.4.05. algorithm (see _findMaxima function).
    """

    peakPickerType = "PeakPicker1D"
    onlyFor1D = True

    def __init__(self, spectrum):
        super().__init__(spectrum=spectrum)
        self.noise = None
        application = spectrum.project.application
        self._doNegativePeaks = application.preferences.general.negativePeakPick1D

    def _setThresholds(self):
        # first make sure the noiseLevel is set for the spectrum. Don't change this.
        if not self.spectrum.noiseLevel:
            self.spectrum.noiseLevel = self.spectrum.estimateNoise()
        if not self.spectrum.negativeNoiseLevel:
            self.spectrum.negativeNoiseLevel = -self.spectrum.noiseLevel
        if not self.positiveThreshold:
            self.positiveThreshold = self.spectrum.noiseLevel
        if not self.negativeThreshold:
            self.negativeThreshold = self.spectrum.negativeNoiseLevel
        # don't pick below the noise level.
        if self.positiveThreshold <= self.spectrum.noiseLevel:
            self.positiveThreshold = self.spectrum.noiseLevel
        if abs(self.negativeThreshold) <= abs(self.spectrum.negativeNoiseLevel):
            self.negativeThreshold = self.spectrum.negativeNoiseLevel

    def _isHeightWithinIntesityLimits(self, height):
        """ check if value is within the intensity limits. This is a different check from the noise Thresholds.
        Used when picking in a Gui Spectrum Display to make sure is picking only within the drawn box.
        """
        if self._intensityLimits is None or len(self._intensityLimits)==0:
            self._intensityLimits = (np.inf, -np.inf)
        value = min(self._intensityLimits) < height < max(self._intensityLimits)
        return value

    def _isPositionWithinLimits(self, pointValue):
        withinLimits = []
        ppmValue = self.spectrum.point2ppm(pointValue, axisCode=self.spectrum.axisCodes[0])
        excludePpmRegions = self._excludePpmRegions.get(self.spectrum.axisCodes[0])
        if excludePpmRegions is None:
            excludePpmRegions = [[0, 0], ]
        for limits in excludePpmRegions:
            if len(limits)>0:
                value = min(limits) < ppmValue < max(limits)
                withinLimits.append(not value)
        return all(withinLimits)


    def findPeaks(self, data):
        peaks = []
        start = int(self.spectrum.referencePoints[0])
        x = np.arange(start, start + len(data))
        self._setThresholds()
        maxValues, minValues = _find1DMaxima(y=data, x=x,
                                             positiveThreshold=self.positiveThreshold,
                                             negativeThreshold=self.negativeThreshold,
                                             findNegative=self._doNegativePeaks)
        for position, height in maxValues:
            if self._isHeightWithinIntesityLimits(height) and self._isPositionWithinLimits(position):
                points=(float(position - start),)
                pk = SimplePeak(points=points, height=float(height))
                peaks.append(pk)
        if self._doNegativePeaks:
            for position, height in minValues:
                if self._isHeightWithinIntesityLimits(height) and self._isPositionWithinLimits(position):
                    points = (float(position - start),)
                    pk = SimplePeak(points=(float(position),), height=float(height))
                    peaks.append(pk)

        return peaks

PeakPicker1D._registerPeakPicker()
