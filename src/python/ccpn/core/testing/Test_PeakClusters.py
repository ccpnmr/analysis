"""
Core object peak cluster is deprecated.
Superseded by collection object.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-03-20 19:06:26 +0000 (Wed, March 20, 2024) $"
__version__ = "$Revision: 3.2.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting


# Properly done version of above
class PeakListCreationTest(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.spectrum1 = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N'), name='HN-hsqc')
            self.spectrum2 = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N'), name='HN-hsqc')

    def test_newPeakList_UndoRedo(self):
        peakList = self.spectrum1.newPeakList()

        self.assertEqual(len(self.spectrum1.peakLists), 2)
        self.undo.undo()
        self.assertEqual(len(self.spectrum1.peakLists), 1)

        self.undo.redo()
        self.assertEqual(len(self.spectrum1.peakLists), 2)
        self.assertIs(self.spectrum1.peakLists[1], peakList)

        peakList1 = self.spectrum1.peakLists[0]
        peakPos = [(0.1 * xx, 0.1 * xx) for xx in range(0, 5)]
        peakList1Peaks = [peakList1.newPeak(ppmPositions=pk) for pk in peakPos]

        peakList2 = self.spectrum2.peakLists[0]
        peakList2Peaks = [peakList2.newPeak(ppmPositions=pk) for pk in peakPos]

        peakList3 = self.spectrum1.peakLists[1]
        peakList3Peaks = [peakList3.newPeak(ppmPositions=pk) for pk in peakPos]

        self.project._newPeakCluster(peaks=peakList1.peaks)
        pkCluster = self.project._peakClusters[0]
        self.assertEqual(len(pkCluster.peaks), 5)
        self.assertListEqual(peakList1Peaks, list(pkCluster.peaks))

        pkCluster.addPeaks(peaks=peakList2.peaks)
        self.assertEqual(len(pkCluster.peaks), 10)
        self.assertListEqual(peakList1Peaks + peakList2Peaks, list(pkCluster.peaks))

        pkCluster.removePeaks(peaks=peakList1.peaks)
        self.assertEqual(len(pkCluster.peaks), 5)
        self.assertListEqual(peakList2Peaks, list(pkCluster.peaks))

        with self.assertRaisesRegex(ValueError, 'does not belong to peakCluster'):
            pkCluster.removePeaks(peaks=peakList3.peaks)

        with self.assertRaisesRegex(TypeError, 'is not of type Peak'):
            pkCluster.addPeaks(peaks=['not a peak'])

        with self.assertRaisesRegex(TypeError, 'is not of type Peak'):
            pkCluster.removePeaks(peaks=12)

        with self.assertRaisesRegex(TypeError, 'is not of type Peak'):
            # makeIterableList was modified to exclude traits
            pkCluster.removePeaks(peaks=peakList3)

        with self.assertRaisesRegex(TypeError, 'is not of type Peak'):
            pkCluster.removePeaks(peaks=['not a peak'])
