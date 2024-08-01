"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Vicky Higman $"
__dateModified__ = "$dateModified: 2024-07-31 15:42:58 +0100 (Wed, July 31, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-02-08 11:42:15 +0000 (Mon, February 08, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.PeakPickers.PeakPickerNd import PeakPickerNd
import itertools

class PeakPicker2DDQ(PeakPickerNd):
    peakPickerType = "PeakPicker2DDQ"
    onlyFor1D = False


    def pickPeaks(self, sliceTuples, peakList, positiveThreshold=None, negativeThreshold=None) -> list:
        """Set the default functionality for picking simplePeaks from the region defined by axisDict
        """
        # set the correct parameters for the standard findPeaks
        self._hbsWidth = self.halfBoxFindPeaksWidth
        self.findFunc = self._returnSimplePeaks

        peaks = super().pickPeaks(sliceTuples=sliceTuples, peakList=peakList,
                                 positiveThreshold=positiveThreshold, negativeThreshold=negativeThreshold)
        if peaks[0].spectrum.dimensionCount == 2:
            self._addDQPeaks(peaks)
        return peaks


    def _addDQPeaks(self, peaks):
        if len(peaks) >= 1:
            for pk in peaks:
                if 'DQ' in pk.spectrum.coherenceOrders and 'SQ' in pk.spectrum.coherenceOrders:
                    for i, co in enumerate(pk.spectrum.coherenceOrders):
                        if co == 'SQ':
                            sqdim = i
                        elif co == 'DQ':
                            dqdim = i
                    if dqdim == 0:
                        pk.peakList.newPeak([pk.ppmPositions[dqdim], pk.ppmPositions[dqdim] - pk.ppmPositions[sqdim]])
                    elif dqdim == 1:
                        pk.peakList.newPeak([pk.ppmPositions[dqdim] - pk.ppmPositions[sqdim], pk.ppmPositions[dqdim]])
        else:
            return


PeakPicker2DDQ._registerPeakPicker()
