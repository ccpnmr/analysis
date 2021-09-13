#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-09-13 19:25:09 +0100 (Mon, September 13, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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


class Test_makeNmrAtom(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_createNmrAtom_withIsotopeCode(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.newNmrAtom(isotopeCode='15N')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(a.isotopeCode, '15N')

    def test_createNmrAtom_withName(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.newNmrAtom(name='CA')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(a.name, 'CA')

    def test_fetchNmrAtom(self):
        c = self.project.newNmrChain()
        r = c.newNmrResidue()
        a = r.fetchNmrAtom(name='CB')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(a.name, 'CB')


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

    def test_assignDimension(self):
        # peaks = self.peakList.pickPeaksNd([[7.0, 7.2], [111.75, 112.2]])
        _picker = self.spectrum.peakPicker
        peaks = self.spectrum.pickPeaks(peakList=self.peakList,
                                        positiveThreshold=12000.0, negativeThreshold=12000.0,
                                        H=(7.0, 7.2), N=(111.75, 112.2))

        peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                 value=self.atom)
        # Undo and redo all operations
        self.assertIsNotNone(self.shiftList.getChemicalShift(self.atom))
        self.undo.undo()
        self.assertIsNone(self.shiftList.getChemicalShift(self.atom))
        self.undo.redo()
        self.assertIsNotNone(self.shiftList.getChemicalShift(self.atom))
