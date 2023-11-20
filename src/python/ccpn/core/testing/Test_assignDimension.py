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
__modifiedBy__ = "$modifiedBy: Daniel Thompson $"
__dateModified__ = "$dateModified: 2023-11-20 12:07:56 +0000 (Mon, November 20, 2023) $"
__version__ = "$Revision: 3.2.1 $"
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


def undo_redo_tester(self, undo_obj):
    """tests undo redo functionality by comparing change in object representations/PIDs"""
    undo_obj_id = undo_obj.__repr__()
    self.undo.undo()
    self.assertNotEqual(undo_obj_id, undo_obj.__repr__())
    self.undo.redo()
    self.assertEqual(undo_obj_id, undo_obj.__repr__())

class Test_makeNmrAtom(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_createNmrAtom_withIsotopeCode(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.newNmrAtom(isotopeCode='15N')
        self.assertEqual(a.isotopeCode, '15N')

        # Test undo redo using PID
        undo_redo_tester(self, a)

    def test_createNmrAtom_withName(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.newNmrAtom(name='CA')
        self.assertEqual(a.name, 'CA')

        # Undo and redo all operations
        undo_redo_tester(self, a)

    def test_fetchNmrAtom(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        # test fetching
        created_a = r.newNmrAtom(name='CB')
        self.assertEqual(created_a.name, 'CB')
        fetched_a = r.fetchNmrAtom(name='CB')
        self.assertEqual(fetched_a, created_a)

        # Undo and redo all operations
        undo_redo_tester(self, fetched_a)




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

    def testPeaks(self):
        # peaks = self.peakList.pickPeaksNd([[7.0, 7.2], [111.75, 112.2]])
        _picker = self.spectrum.peakPicker
        return self.spectrum.pickPeaks(peakList=self.peakList,
                                             positiveThreshold=12000.0, negativeThreshold=12000.0,
                                             H=(7.0, 7.2), N=(111.75, 112.2))

    def test_assignDimensionNmrAtom(self):
        peaks = self.testPeaks()

        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=self.atom)
        sl = self.shiftList.getChemicalShift(self.atom)
        self.assertIsNotNone(sl)

        # Undo and redo all operations
        undo_redo_tester(self, sl)

    def test_assignDimensionPID(self):
        peaks = self.testPeaks()

        atom_pid = self.atom.pid
        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=atom_pid)
        sl = self.shiftList.getChemicalShift(self.atom)
        self.assertIsNotNone(sl)

        # Undo and redo all operations
        undo_redo_tester(self, sl)

    def test_assignDimensionNone(self):
        peaks = self.testPeaks()

        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=None)
        sl = self.shiftList.getChemicalShift(self.atom)
        self.assertIsNone(sl)

    def test_assignDimensionAxisCodeError(self):
        peaks = self.testPeaks()
        with self.assertRaises(ValueError) as cm:
            peaks[0].assignDimension(axisCode='invalid axis code',
                                     value=self.atom)
        err = cm.exception
        self.assertEqual(str(err), 'axisCode invalid axis code not recognised')
