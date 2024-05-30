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
__dateModified__ = "$dateModified: 2024-05-30 13:47:13 +0100 (Thu, May 30, 2024) $"
__version__ = "$Revision: 3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import unittest

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class TestNmrAtomCreation(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.nmrChain = self.project.newNmrChain()
            self.nmrResidue = self.nmrChain.newNmrResidue()

    def tearDown(self):
        super().tearDown()
        dd = self.nmrChain._wrappedData.__class__._notifies
        dd = self.nmrResidue._wrappedData.__class__._notifies
        del self.nmrResidue
        del self.nmrChain

    ## deassign methods needs to be revisited from 3.1
    # def test_deassign_unknown(self):
    #     nmrAtom = self.nmrResidue.fetchNmrAtom(name='churl')
    #     self.assertEqual(nmrAtom.pid, 'NA:@2.@1..churl')
    #     self.assertEqual(nmrAtom.isotopeCode, '?')
    #     nmrAtom.deassign()
    #     self.assertEqual(nmrAtom.pid, 'NA:@2.@1..?@1')
    #
    # def test_deassign_carbon(self):
    #     nmrAtom = self.nmrResidue.fetchNmrAtom(name='Churl')
    #     self.assertEqual(nmrAtom.pid, 'NA:@2.@1..Churl')
    #     nmrAtom.deassign()
    #     self.assertEqual(nmrAtom.pid, 'NA:@2.@1..C@1')
    #
    # def test_deassign_calcium(self):
    #     nmrAtom = self.nmrResidue.newNmrAtom(name='Carl', isotopeCode='43Ca')
    #     self.assertEqual(nmrAtom.pid, 'NA:@2.@1..Carl')
    #     self.assertEqual(nmrAtom.isotopeCode, '43Ca')
    #     nmrAtom.deassign()
    #     self.assertEqual(nmrAtom.pid, 'NA:@2.@1..CA@1')


    def test_CreateNmrAtomWithArbitraryNameAndXenonIsotopeCode(self):
        a = self.nmrResidue.newNmrAtom(name='Arbitrary', isotopeCode='129Xe')
        self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary')

    def test_CreateNmrAtomWithArbitraryName(self):
        a = self.nmrResidue.newNmrAtom(name='Arbitrary')
        self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary')
        self.assertEqual(a.isotopeCode, None)

    def test_CreateNmrAtomWithArbitraryDottedName(self):
        a = self.nmrResidue.newNmrAtom(name='Arbitrary.Name')
        self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary^Name')
        self.assertEqual(a.isotopeCode, None)

    def test_CreateNmrAtomWithArbitraryHattedName(self):
        with self.assertRaisesRegex(ValueError, r"Character \'\^\' not allowed"):
            a = self.nmrResidue.newNmrAtom(name='Arbitrary^Name')

    def test_CreateNmrAtomWithArbitraryNameAndArbitraryIsotopeCode(self):
        with self.assertRaisesRegex(ValueError, 'Invalid isotopeCode'):
            a = self.nmrResidue.newNmrAtom(name='Arbitrary', isotopeCode='Arbitrary_Isotope')
        # self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary')

    def test_CreateNmrAtomWithArbitraryIsotopeWithSpace(self):
        with self.assertRaisesRegex(ValueError, 'Invalid isotopeCode'):
            a = self.nmrResidue.newNmrAtom(name='Arbitrary', isotopeCode='Arbitrary Isotope')
        # self.assertEqual(a.isotopeCode, None)

    def test_CreateTwoNmrAtomsWithSameName(self):
        self.nmrResidue.newNmrAtom(name='H')
        nmr_atom = self.nmrResidue.newNmrAtom(name='H')
        self.assertEqual('H_1', nmr_atom.name)

    def test_CreateNmrAtomByFetchingFromResidue(self):
        self.assertEqual(self.nmrResidue.nmrAtoms, [])
        newNmrAtom = self.nmrResidue.fetchNmrAtom(name='H')
        self.assertEqual(newNmrAtom.pid, 'NA:@2.@1..H')
        self.assertEqual(self.nmrResidue.nmrAtoms, [newNmrAtom])

    def test_CreateNmrAtomByProducingFromProjectByPid(self):
        self.assertEqual(self.nmrResidue.nmrAtoms, [])

        newNmrAtom1 = self.project.produceNmrAtom(name='HX')
        newNmrAtom2 = self.project.produceNmrAtom(name='HX')

        self.assertEqual(newNmrAtom1.pid, 'NA:@-.@2..HX')
        self.assertEqual(newNmrAtom2.pid, 'NA:@-.@3..HX')

        self.assertEqual(self.project.nmrAtoms, [newNmrAtom1, newNmrAtom2])

    def test_CreateNmrAtomByProducingFromProjectWithParametersMismatchedType(self):
        self.assertRaises(ValueError, self.project.produceNmrAtom, '@2.@1.ARG.NE')
        # newNmrAtom1 = self.project.produceNmrAtom(atomId='@2.@1.ARG.NE')
        # self.assertEqual(newNmrAtom1.pid, 'NA:@2.@1..NE')

    def test_CreateNmrAtomByProducingFromProjectByPidWithChain(self):
        self.assertEqual(self.nmrResidue.nmrAtoms, [])

        newNmrAtom = self.project.produceNmrAtom('@2.@1..NE')

        self.assertEqual(newNmrAtom.pid, 'NA:@2.@1..NE')
        self.assertEqual(self.project.nmrAtoms, [newNmrAtom])
        self.assertIs(self.nmrResidue, newNmrAtom.nmrResidue)
        self.assertEqual(self.project.nmrResidues, [self.nmrResidue])

    def test_CreateNmrAtomByProducingFromProjectWithParameters(self):
        self.assertEqual(self.nmrResidue.nmrAtoms, [])

        newNmrAtom = self.project.produceNmrAtom(chainCode='@2',
                                                 sequenceCode='@1',
                                                 name='NE')

        self.assertEqual(newNmrAtom.pid, 'NA:@2.@1..NE')
        self.assertEqual(self.project.nmrAtoms, [newNmrAtom])
        self.assertIs(self.nmrResidue, newNmrAtom.nmrResidue)
        self.assertEqual(self.project.nmrResidues, [self.nmrResidue])

    def test_CreateNmrAtomAndNmrResidueByProducingFromProjectWithParameters(self):
        self.assertEqual(self.nmrResidue.nmrAtoms, [])
        self.assertEqual(len(self.project.nmrResidues), 1)

        newNmrAtom = self.project.produceNmrAtom(chainCode='A',
                                                 sequenceCode='11',
                                                 name='NE')

        self.assertEqual(newNmrAtom.pid, 'NA:A.11..NE')
        self.assertEqual(self.project.nmrAtoms, [newNmrAtom])
        self.assertEqual(len(self.project.nmrResidues), 2)
        self.assertIn(newNmrAtom.nmrResidue, self.project.nmrResidues)

    def test_CreateNmrAtomByProducingFromProjectWithPid(self):
        self.assertEqual(self.nmrResidue.nmrAtoms, [])

        newNmrAtom = self.project.produceNmrAtom('NA:A.11.ARG.NE')

        self.assertEqual(newNmrAtom.pid, 'NA:A.11.ARG.NE')
        self.assertEqual(self.project.nmrAtoms, [newNmrAtom])


class TestNmrAtomProperties(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.nmrChain = self.project.newNmrChain()
            self.nmrResidue = self.nmrChain.newNmrResidue()
            self.nmrAtom = self.nmrResidue.newNmrAtom(isotopeCode='1H')

    def tearDown(self):
        super().tearDown()
        del self.nmrResidue
        del self.nmrChain
        del self.nmrAtom

    def test_AnonymousNmrAtom_id(self):
        self.assertEqual(self.nmrAtom.id, '@2.@1..@_0')

    def test_AnonymousNmrAtom_pid(self):
        self.assertEqual(self.nmrAtom.pid, 'NA:@2.@1..@_0')

    def test_AnonymousNmrAtom_longPid(self):
        self.assertEqual(self.nmrAtom.longPid, 'NmrAtom:@2.@1..@_0')

    def test_AnonymousNmrAtom_project(self):
        self.assertTrue(self.project is self.nmrAtom.project)

    def test_AnonymousNmrAtom_nmrResidue(self):
        self.assertTrue(self.nmrResidue is self.nmrAtom.nmrResidue)

    @unittest.expectedFailure
    def test_AnonymousNmrAtom_name(self):
        self.assertTrue('name' not in self.nmrAtom.keys())

    def _test_AnonymousNmrAtom_apiResonance(self):
        print(self.nmrAtom.apiResonance)

    def _test_AnonymousNmrAtom_atom(self):
        print(self.nmrAtom.atom)

    def _test_AnonymousNmrAtom_assignedPeaks(self):
        self.assertEqual(self.nmrAtom.assignedPeaks, [[]])


class TestNmrAtomMethods(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.nmrChain = self.project.newNmrChain()
            self.nmrResidue = self.nmrChain.newNmrResidue()
            self.nmrAtom = self.nmrResidue.newNmrAtom(name='H')

    def tearDown(self):
        super().tearDown()
        del self.nmrResidue
        del self.nmrChain
        del self.nmrAtom

    def test_NmrAtom_Get(self):
        self.assertEqual(self.nmrAtom.id, self.nmrAtom.id)

    def test_NmrAtom_GetByPid(self):
        atomPid = self.nmrAtom.pid
        self.assertTrue(self.nmrAtom is self.nmrAtom.getByPid(atomPid))
        self.assertTrue(self.nmrAtom is self.nmrResidue.getByPid(atomPid))
        self.assertTrue(self.nmrAtom is self.nmrChain.getByPid(atomPid))
        self.assertTrue(self.nmrAtom is self.project.getByPid(atomPid))

    def test_ReassignNmrAtomSequenceCode(self):
        self.assertEqual(len(self.project.nmrResidues), 1)

        atom1 = self.project.produceNmrAtom(name='HX')
        res1 = atom1.nmrResidue
        self.assertEqual(atom1.pid, 'NA:@-.@2..HX')
        self.assertEqual(res1.pid, 'NR:@-.@2.')

        self.assertEqual(len(res1.nmrAtoms), 1)
        self.assertEqual(len(self.project.nmrResidues), 2)

        atom1 = atom1.assignTo(sequenceCode=101)

        self.assertEqual(atom1.pid, 'NA:@-.101..HX')
        self.assertEqual(res1.pid, 'NR:@-.@2.')
        self.assertEqual(len(res1.nmrAtoms), 0)
        self.assertEqual(len(self.project.nmrResidues), 3)

    def test_ReassignNmrAtomName(self):
        self.assertEqual(len(self.project.nmrResidues), 1)

        atom1 = self.project.produceNmrAtom('X.101.VAL.N')
        res1 = atom1.nmrResidue
        self.assertEqual(atom1.pid, 'NA:X.101.VAL.N')
        self.assertEqual(res1.pid, 'NR:X.101.VAL')

        self.assertEqual(len(res1.nmrAtoms), 1)
        self.assertEqual(len(self.project.nmrResidues), 2)

        atom1 = atom1.assignTo(name='NE')

        self.assertEqual(atom1.pid, 'NA:X.101.VAL.NE')
        self.assertEqual(res1.pid, 'NR:X.101.VAL')
        self.assertEqual(len(res1.nmrAtoms), 1)
        self.assertEqual(len(self.project.nmrResidues), 2)

    def test_RenameAtom(self):
        self.assertEqual(self.nmrAtom.id, '@2.@1..H')
        self.nmrAtom.rename('N')
        self.assertEqual(self.nmrAtom.id, '@2.@1..N')

    def test_DeleteAtom(self):
        print(self.nmrAtom.delete())


class TestNmrAtomReceivedProperties(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.nmrChain = self.project.newNmrChain()
            self.nmrResidue = self.nmrChain.newNmrResidue()
            self.nmrAtom = self.nmrResidue.newNmrAtom(name='H')

    def tearDown(self):
        super().tearDown()
        del self.nmrResidue
        del self.nmrChain
        del self.nmrAtom

    def test_ProjectName(self):
        self.assertEqual(self.nmrAtom.project.name, 'default')

    def test_NmrResiduePid(self):
        self.assertEqual(self.nmrAtom.nmrResidue.pid, 'NR:@2.@1.')

    def test_NmrResidueName(self):
        self.assertEqual(self.nmrAtom.nmrResidue.residueType, '')

    @unittest.skip('ISSUE: Is there any way to pair Atom with NmrAtom other than by residue? - linking no longer allowed')
    # sort-of, move to new residue and link that
    def test_AtomAtom(self):
        self.assertIsNone(self.nmrAtom.atom)
        ch = self.project.createChain(sequence='ag', molType='protein')
        self.nmrResidue.residue = ch.residues[1]
        self.assertEqual(self.nmrAtom.atom.pid, 'MA:A.2.GLY.H')

    def test_className(self):
        self.assertEqual(self.nmrAtom.className, 'NmrAtom')

    def test_ShortClassName(self):
        self.assertEqual(self.nmrAtom.shortClassName, 'NA')

    def test_AssignedPeaks(self):
        self.assertEqual(self.nmrAtom.assignedPeaks, ())


class TestAtomShifts(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.nmrChain = self.project.newNmrChain()
            self.nmrResidue = self.nmrChain.newNmrResidue()

    def tearDown(self):
        super().tearDown()
        del self.nmrResidue
        del self.nmrChain

    @unittest.skip('ISSUE: Must be able to create an empty spectrum to create peaks.')
    def test_GetShiftsFromNmrAtom(self):
        a = self.nmrResidue.newNmrAtom()
        print(a.shifts)
