"""Test code for NmrResidue

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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting, fixCheckAllValid, getProperties
from ccpn.core.lib import Pid
from ccpn.core.lib.AxisCodeLib import axisCodeMatch

class NmrAtomTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'V3ProjectForTests.ccpn'

    def setUp(self):
        with self.initialSetup():
            self.ile5 = self.project.getByPid('NR:A.5.ILE')
            self.nmr_atom = self.ile5.fetchNmrAtom('N')

            spectra = self.loadData('spectra/115.spc')
            self.spectrum = spectra[0] if spectra else None
            self.peakList = self.spectrum.newPeakList() if spectra else None
            _picker = self.spectrum.peakPicker
            self.peaks = self.spectrum.pickPeaks(peakList=self.peakList,
                                       positiveThreshold=12000.0, negativeThreshold=12000.0,
                                       H=(7.0, 7.2), N=(111.75, 112.2))

    def test_fetchNmrAtomReassign(self):
        atomN = self.ile5.fetchNmrAtom('N')
        self.assertEqual(atomN.pid, 'NA:A.5.ILE.N')

        atomNE = self.ile5.fetchNmrAtom('NE')
        atomNE2 = self.ile5.fetchNmrAtom('NE')
        self.assertIs(atomNE, atomNE2)

        atomCX = self.ile5.fetchNmrAtom('CX')
        atomNX = self.ile5.newNmrAtom(name='NX')
        # with self.assertRaises(ValueError):
        #     atomCX.rename('NX')
        atomCX.rename('CZ')

        atomCX = atomCX.assignTo(chainCode='A', sequenceCode='888')
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.CZ')

        atomCX = atomCX.assignTo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.CZ')

        atomCX.rename('Co')
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.Co')

        # fix the bad structure for the test
        # new pdb loader does not load the into the data model so there are no atoms defined
        # the corresponding dataMatrices therefore have dimension set to zero which causes a crash :|
        fixCheckAllValid(self.project)

        self.project._wrappedData.root.checkAllValid(complete=True)

        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.Co')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.CZ')
        self.undo.redo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.Co')

    def test_newNmrAtomReassign(self):
        nc = self.project.newNmrChain(shortName='X')
        self.assertEqual(nc.pid, 'NC:X')

        nr = nc.newNmrResidue(sequenceCode='101', residueType='VAL')
        self.assertEqual(nr.pid, 'NR:X.101.VAL')

        at1 = nr.newNmrAtom(name='N')
        self.assertEqual(at1.pid, 'NA:X.101.VAL.N')
        at1 = at1.assignTo(name='NE')
        self.assertEqual(at1.pid, 'NA:X.101.VAL.NE')
        at1 = at1.assignTo(sequenceCode='777')
        self.assertEqual(at1.pid, 'NA:X.777.VAL.NE')
        self.undo.undo()
        self.assertEqual(at1.pid, 'NA:X.101.VAL.NE')
        self.undo.undo()
        self.assertEqual(at1.pid, 'NA:X.101.VAL.N')
        self.undo.redo()
        self.assertEqual(at1.pid, 'NA:X.101.VAL.NE')
        self.undo.redo()
        self.assertEqual(at1.pid, 'NA:X.777.VAL.NE')

    def test_assignToMerge(self):
        """Test of assigning and merging using the assignTo method, including associated errors.
        """
        # creating nmrAtom
        na = self.ile5.fetchNmrAtom(name='NX')
        with self.assertRaises(ValueError) as cm:
            self.nmr_atom.assignTo(chainCode='A', sequenceCode='5', residueType='ILE', name='NX')
        err = str(cm.exception)
        self.assertEqual(err, 'New assignment clash with existing assignment, and merging is disallowed')

        self.peaks[0].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                      value=na)

        self.assertTrue(len(self.nmr_atom.assignedPeaks) == 1)

        self.nmr_atom = self.nmr_atom.assignTo(chainCode='A', sequenceCode='5', residueType='ILE',
                                               name='NX', mergeToExisting=True)

        self.assertTrue(len(self.nmr_atom.assignedPeaks) == 2)

    def test_assignToParamsError(self):
        """tests nmrAtoms cant be assigned invalid PID characters '^' using the toAssign() function

         Sequentially tests changing each parameter to the 'altCharacter', and checks the correct error
         is produced.
         """
        params = {'chainCode': 'A', 'sequenceCode': '5', 'residueType': 'ILE', 'name': 'name'}
        for key in params:
            temp_params = params.copy()
            temp_params[key] = Pid.altCharacter
            with self.assertRaises(ValueError) as cm:
                self.nmr_atom.assignTo(**temp_params)
            err = str(cm.exception)
            self.assertEqual(err, f"Character {Pid.altCharacter} not allowed in ccpn.NmrAtom id : "
                                  f"{'.'.join(temp_params.values())}")

    def test_mergeNmrAtoms(self):
        """Tests the mergeNmrAtom method

        Ensures functionality of input with NmrAtoms, NmrAtom Pid's or a list combining the two.
        Tests undo redo operations are completed successfully by comparing the objects PID
        """
        list_len = 1  # arbitrary list size
        nmrAtom_list = [self.ile5.fetchNmrAtom(name=f'N{na}') for na in range(list_len)]
        nmrAtom_list.append(str(self.ile5.fetchNmrAtom(name=f'N{list_len}').pid))

        for i, atom in enumerate(nmrAtom_list):
            self.peaks[i].assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                          value=atom)

        as_list = set(self.nmr_atom.assignedPeaks)

        for na in nmrAtom_list:
            if isinstance(na, str):
                na = self.project.getByPid(na)
                as_list |= set(na.assignedPeaks)
            else:
                as_list |= set(na.assignedPeaks)

        self.nmr_atom.mergeNmrAtoms(nmrAtom_list)


        as_list_t = set(self.nmr_atom.assignedPeaks)

        self.assertListEqual(list(as_list_t), list(as_list))

        # gross little hack :|
        del_l = ['NA:A.5.ILE.N10-Deleted' if isinstance(atom, str) else atom.pid for atom in nmrAtom_list]
        for atom in del_l:
            self.assertIn('Deleted', atom)

        # undo redo all operations
        self.undo.undo()
        for atom in nmrAtom_list[:-1]:
            self.assertNotIn('Deleted', atom.pid)
        self.assertNotIn('Deleted', nmrAtom_list[-1])
        self.undo.redo()
        # same gross little hack :|
        del_l = ['NA:A.5.ILE.N10-Deleted' if isinstance(atom, str) else atom.pid for atom in nmrAtom_list]
        for atom in del_l:
            self.assertIn('Deleted', atom)

    def test_mergeNmrAtomsErrors(self):
        """Test type errors associated with mergeNmrAtoms(), merging with self or non NmrAtoms"""
        with self.assertRaises(TypeError) as cm:
            self.nmr_atom.mergeNmrAtoms(self.nmr_atom)
        self.assertEqual(str(cm.exception), 'nmrAtom cannot be merged with itself')
        with self.assertRaises(TypeError) as cm:
            self.nmr_atom.mergeNmrAtoms(32)
        self.assertEqual(str(cm.exception), 'nmrAtoms can only contain items of type NmrAtom')

    def test_rename(self):
        # written by Luca Mureddu
        with self.assertRaises(ValueError):
            self.nmr_atom.rename(42)
        with self.assertRaises(ValueError):
            self.nmr_atom.rename(12.34)

        self.nmr_atom.rename('CZ')
        self.assertEqual(self.nmr_atom.pid, 'NA:A.5.ILE.CZ')

    def test_rename_undo_redo(self):
        """testing undo redo functionality of renaming nmrAtoms"""
        self.nmr_atom.rename('0')
        self.nmr_atom.rename('1')
        self.nmr_atom.rename('2')

        # undo redo all operations
        self.undo.undo()
        self.assertEqual('1', self.nmr_atom.name)
        self.undo.undo()
        self.assertEqual('0', self.nmr_atom.name)
        self.undo.redo()
        self.assertEqual('1', self.nmr_atom.name)
        self.undo.redo()
        self.assertEqual('2', self.nmr_atom.name)

    def test_delete(self):
        """Comprehensive test of NmrAtom's delete method, including undo redo"""
        atomX = self.ile5.fetchNmrAtom('X')

        self.nmr_atom.delete()
        atomX.delete()

        self.assertIn('Deleted', self.nmr_atom.pid)
        self.assertIn('Deleted', atomX.pid)
        self.assertEqual((), self.nmr_atom.chemicalShifts)

        # undo redo all operations
        self.undo.undo()
        self.assertNotIn('Deleted', atomX.pid)
        self.assertIn('Deleted', self.nmr_atom.pid)
        self.undo.undo()
        self.assertNotIn('Deleted', atomX.pid)
        self.assertNotIn('Deleted', self.nmr_atom.pid)
        self.undo.redo()
        self.assertNotIn('Deleted', atomX.pid)
        self.assertIn('Deleted', self.nmr_atom.pid)
        self.undo.redo()
        self.assertIn('Deleted', atomX.pid)
        self.assertIn('Deleted', self.nmr_atom.pid)
