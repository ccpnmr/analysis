"""
Simple 1D PeakPicker; for testing only
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC, SimplePeak
from ccpn.util.Logging import getLogger

class Simple1DPeakPicker(PeakPickerABC):
    """A simple peak picker for testing
    """

    peakPickerType = "Simple1D"
    onlyFor1D = True

    def __init__(self, spectrum):
        super().__init__(spectrum=spectrum)
        self.noise = None

    def findPeaks(self, data) -> list:
        """Find the local (positive) maxima in the numpy data;
        return a list with SimplePeak instances; note that SimplePeak.points are ordered z,y,x for nD,
        in accordance with the numpy data array
        """
        if self.noise is None:
            self.noise = self.spectrum.estimateNoise()

        peaks = []
        i = 1
        while i < len(data)-1:
            if data[i] > self.noise and data[i] > data[i-1] and data[i] > data[i+1]:
                # found a local maximum above the noise
                pk = SimplePeak(points=(float(i),), height=float(data[i]))
                peaks.append(pk)
                i += 2
            else:
                i += 1

        return peaks

Simple1DPeakPicker._register()