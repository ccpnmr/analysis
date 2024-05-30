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

from ccpn.core.lib.AxisCodeLib import axisCodeMatch
from ccpn.core.testing.WrapperTesting import WrapperTesting


def _undo_redo_tester(obj, undo_obj):
    """tests undo redo functionality by testing for 'Deleted' string in object representations/PIDs"""
    obj.assertNotIn('Deleted', repr(undo_obj))
    obj.undo.undo()
    # check repr change ('deleted' included on end)
    obj.assertIn('Deleted', repr(undo_obj))
    obj.undo.redo()
    # repr should revert to original (no 'deleted' on end)
    obj.assertNotIn('Deleted', repr(undo_obj))


class Test_makeNmrAtom(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_createNmrAtom_withIsotopeCode(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.newNmrAtom(isotopeCode='15N')
        self.assertEqual(a.isotopeCode, '15N')

        # Test undo redo using PID
        _undo_redo_tester(self, a)

    def test_createNmrAtom_withName(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.newNmrAtom(name='CA')
        self.assertEqual(a.name, 'CA')

        # Undo and redo all operations
        _undo_redo_tester(self, a)

    def test_fetchNmrAtom(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        # test fetching
        created_a = r.newNmrAtom(name='CB')
        self.assertEqual(created_a.name, 'CB')
        fetched_a = r.fetchNmrAtom(name='CB')
        self.assertEqual(fetched_a, created_a)

        # Undo and redo all operations
        _undo_redo_tester(self, fetched_a)


class Test_chemicalShift(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            spectra = self.loadData('spectra/115.spc')
            self.spectrum = spectra[0] if spectra else None
            if len(self.project.chemicalShiftLists) < 1:
                self.project.newChemicalShiftList()
            c = self.project.newNmrChain()
            r = c.newNmrResidue()
            self.atom = r.newNmrAtom(isotopeCode='15N')
            # NBNB The first shiftList, called 'default' is created automatically
            self.shiftList = self.project.chemicalShiftLists[0]
            self.peakList = self.spectrum.newPeakList() if spectra else None
        # peaks = self.peakList.pickPeaksNd([[7.0, 7.2], [111.75, 112.2]])
        _picker = self.spectrum.peakPicker
        self.peaks = self.spectrum.pickPeaks(peakList=self.peakList,
                                             positiveThreshold=12000.0, negativeThreshold=12000.0,
                                             H=(7.0, 7.2), N=(111.75, 112.2))

    def test_assignDimensionNmrAtom(self):
        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        self.peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=self.atom)
        sl = self.shiftList.getChemicalShift(self.atom)
        self.assertIsNotNone(sl)

        # Undo and redo all operations
        _undo_redo_tester(self, sl)

    def test_assignDimensionPID(self):
        atom_pid = self.atom.pid
        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        self.peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=atom_pid)
        sl = self.shiftList.getChemicalShift(self.atom)
        self.assertIsNotNone(sl)

        # Undo and redo all operations
        _undo_redo_tester(self, sl)

    def test_assignDimensionNone(self):
        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        self.peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=None)
        sl = self.shiftList.getChemicalShift(self.atom)
        self.assertIsNone(sl)

    def test_assignDimensionAxisCodeError(self):
        with self.assertRaises(ValueError) as cm:
            self.peaks[0].assignDimension(axisCode='invalid axis code',
                                     value=self.atom)
        err = cm.exception
        self.assertEqual(str(err), 'axisCode invalid axis code not recognised')
