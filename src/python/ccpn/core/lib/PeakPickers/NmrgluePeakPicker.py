"""
Nmrglue-based PeakPicker;
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-22 09:51:59 +0100 (Tue, June 22, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC, SimplePeak
from ccpn.util.Logging import getLogger

from nmrglue.analysis.peakpick import pick as nmrgluePeakPick
#FIXME: code fix required in peakpick line 398 of extract_1d(data, location, axis) function
#
# tuple required:
#    return np.atleast_1d(np.squeeze(data[tuple(s)]))

class NmrgluePeakPicker(PeakPickerABC):
    """A peak picker using the Nmrglue peak picking code
    """
    #=========================================================================================
    peakPickerType = "Nmrglue"
    onlyFor1D = False
    #=========================================================================================

    def __init__(self, spectrum, autoFit:bool=True):
        """Initialise; NB autoFit default is opposite to PeakPickerABC
        """
        from ccpn.core.Spectrum import Spectrum

        if not isinstance(spectrum, Spectrum):
            raise ValueError('%s: spectrum is not of Spectrum class' % self.__class__.__name__)

        super().__init__(spectrum=spectrum, autoFit=autoFit)
        self.positiveThreshold = spectrum.positiveContourBase if spectrum.includePositiveContours else None
        self.negativeThreshold = spectrum.negativeContourBase if spectrum.includeNegativeContours else None

    def findPeaks(self, data) -> list:
        """Find the peaks in the numpy data;
        return a list with SimplePeak instances; note that SimplePeak.points are ordered z,y,x for nD,
        in accordance with the numpy data array

        :param data: numpy nD array
        :return list with SimplePeak instances
        """
        table = nmrgluePeakPick(data=data, pthres=self.positiveThreshold, nthres=self.negativeThreshold,
                                cluster=True, table=True)
        peaks = []
        for item in table:
            values = item.tolist()

            idx = 0
            points = values[0:self.dimensionCount]
            idx += self.dimensionCount

            clusterId = values[idx]
            idx += 1

            lineWidths = values[idx:idx+self.dimensionCount]
            idx += self.dimensionCount

            volume = values[idx]

            pk = SimplePeak(points=points, height=None, lineWidths=lineWidths, volume=volume, clusterId=clusterId)
            peaks.append(pk)

        return peaks
# end class

NmrgluePeakPicker._registerPeakPicker()
