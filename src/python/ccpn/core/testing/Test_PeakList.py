"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-05-30 15:51:32 +0100 (Thu, May 30, 2024) $"
__version__ = "$Revision: 3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting


# Properly done version of above
class PeakListCreationTest(WrapperTesting):

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H',), name='H')
            self.spectrum1 = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N'), name='HN-hsqc')
            self.spectrum2 = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N'), name='HN-hsqc')

    def test_newPeakList(self):
        self.assertEqual(len(self.spectrum.peakLists), 1)

        peakList = self.spectrum.newPeakList()

        self.assertEqual(len(self.spectrum.peakLists), 2)
        self.assertEqual(peakList.className, 'PeakList')
        self.assertIs(self.spectrum.peakLists[1], peakList)

    def test_newPeakList_UndoRedo(self):
        # these cause a huge amount of logging :|
        peakList = self.spectrum.newPeakList()

        self.assertEqual(len(self.spectrum.peakLists), 2)
        self.undo.undo()
        self.assertEqual(len(self.spectrum.peakLists), 1)

        self.undo.redo()
        self.assertEqual(len(self.spectrum.peakLists), 2)
        self.assertIs(self.spectrum.peakLists[1], peakList)

        peakList = self.spectrum1.newPeakList()
        peakList1 = self.spectrum1.peakLists[0]
        peakPos = [(0.1 * xx, 0.1 * xx) for xx in range(5)]
        peakList1Peaks = [peakList1.newPeak(ppmPositions=pk) for pk in peakPos]

        peakList2 = self.spectrum2.peakLists[0]
        peakList2Peaks = [peakList2.newPeak(ppmPositions=pk) for pk in peakPos]

        peakList3 = self.spectrum1.peakLists[1]
        peakList3Peaks = [peakList3.newPeak(ppmPositions=pk) for pk in peakPos]

        peakList4 = peakList1.copyTo(self.spectrum2)
        peakList5 = peakList2.copyTo(self.spectrum1)

        with self.assertRaisesRegex(TypeError, 'missing a required argument'):
            peakList1.copyTo()

        with self.assertRaisesRegex(TypeError, 'targetSpectrum is not of type Spectrum'):
            peakList1.copyTo(12)

        with self.assertRaisesRegex(TypeError, 'targetSpectrum not defined'):
            peakList1.copyTo('not defined')

        # with self.assertRaisesRegex(ValueError, 'Cannot copy'):
        peakList1.copyTo(self.spectrum)


class PeakListTest2(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'CCPN_H1GI_clean_extended.nef'

    singleValueTags = ['isSimulated', 'symbolColour', 'symbolStyle', 'textColour', 'textColour',
                       'title']

    def test_PeakList_copy(self):
        peakList = self.project.getPeakList('3dNOESY-182.3')
        spectrum = peakList.spectrum
        peakList2 = peakList.copyTo(spectrum)

        self.assertEqual(peakList2.serial, 4)
        # self.assertEqual(peakList2.comment,
        #                   """Copy of PeakList:3dNOESY-182.3
        #                   ARIA2_NOE_Peaks_run1_it8_auto1195328348.86|6|1|2"""
        #                   )
        self.assertEqual(peakList2.comment,
                         "Copy of PeakList:3dNOESY-182.3\n" +
                         "ARIA2_NOE_Peaks_run1_it8_auto1195328348.86|6|1|2"
                         )

        for tag in self.singleValueTags:
            self.assertEqual((tag, getattr(peakList, tag)), (tag, getattr(peakList2, tag)))

    def test_PeakList_copy_keyparameters(self):
        peakList = self.project.getPeakList('3dNOESY-182.3')
        spectrum = peakList.spectrum

        params = {
            'title'       : 'ATITLE',
            'comment'     : 'ACOMMENT',
            'symbolStyle' : '+',
            'symbolColour': 'RED',
            'textColour'  : 'dish',
            'isSynthetic' : True,
            }
        peakList2 = peakList.copyTo(spectrum, **params)

        self.assertEqual(peakList2.serial, 4)
        self.assertEqual(peakList2.comment, 'ACOMMENT')

        for tag, val in params.items():
            self.assertEqual(val, getattr(peakList2, tag))

    def test_PeakList_copy_exo(self):
        peakList = self.project.getPeakList('3dNOESY-182.3')
        spectrum = self.project.getSpectrum('3dTOCSY-181')
        peakList2 = peakList.copyTo(spectrum)

        self.assertIs(peakList2._parent, spectrum)

        self.assertEqual(peakList2.serial, 2)
        self.assertEqual(peakList2.comment,
                          "Copy of PeakList:3dNOESY-182.3\n" +
                          "ARIA2_NOE_Peaks_run1_it8_auto1195328348.86|6|1|2"
                          )

        for tag in self.singleValueTags:
            self.assertEqual((tag, getattr(peakList, tag)), (tag, getattr(peakList2, tag)))
