"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: VickyAH $"
__dateModified__ = "$dateModified: 2023-05-19 13:55:07 +0100 (Fri, May 19, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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

class PeakPicker2DMultiplets(PeakPickerNd):
    peakPickerType = "PeakPicker2DMultiplets"
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
            self._clusterPeaksIntoMultiplets(peaks)
        return peaks


    def _placePeaksInMultiplet(self, peaks):
        spectrum = peaks[0].spectrum
        if not spectrum.multipletLists:
            ml = spectrum.newMultipletList(title=None, symbolColour=None, textColour=None, lineColour=None, multipletAveraging=None, comment=None, multiplets=None)
        else:
            ml = spectrum.multipletLists[-1]
        ml.newMultiplet(peaks = peaks, comment=None)


    def _clusterPeaksIntoMultiplets(self, peaks):
        if len(peaks) > 1:
            self._clusterByAlgorithm(peaks)
        else:
            return


    def _singleCluster(self, peaks):
        # simplest version where all peaks are put into one multiplet
        self._placePeaksInMultiplet(peaks)


    def _getTolerance(self, peak, dim, splitDim):
        tolNonSplitDim = {'1H': 0.015, '13C': 0.05, '15N': 0.05}
        tolSplitDim = {'1H': 0.015, '13C': 0.1, '15N': 0.1}
        iCde = peak.spectrum.getByDimensions('isotopeCodes', [dim])[0]
        if splitDim:
            tol = tolSplitDim.get(iCde)
        else:
            tol = tolNonSplitDim.get(iCde)
        return tol


    def _clusterByAlgorithm(self, peaks):
        # try an algorithmic version looking for groups of peaks which are very close in one dim
        clusterNums = {}
        for i, pk in enumerate(peaks):
            clusterNums[pk] = i
        for pk1, pk2 in itertools.combinations(peaks, 2):
            dim = 2
            diff = abs(pk1.getByDimensions('ppmPositions', [dim])[0] - pk2.getByDimensions('ppmPositions', [dim])[0])
            tol = self._getTolerance(pk1, dim, splitDim=False)
            if diff < tol:
                dim = 1
                diff = abs(
                    pk1.getByDimensions('ppmPositions', [dim])[0] - pk2.getByDimensions('ppmPositions', [dim])[0])
                tol = self._getTolerance(pk1, dim, splitDim=True)
                if diff < tol:
                    clusterNums[pk2] = clusterNums[pk1]
        clusters = {}
        for pk, num in clusterNums.items():
            if num not in clusters:
                clusters[num] = [pk]
            else:
                clusters[num].append(pk)
        for i in clusters:
            clusterPeaks = clusters.get(i)
            if len(clusterPeaks) > 1:
                self._placePeaksInMultiplet(clusterPeaks)




PeakPicker2DMultiplets._registerPeakPicker()
