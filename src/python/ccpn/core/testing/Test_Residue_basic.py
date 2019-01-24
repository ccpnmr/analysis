#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:34 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting


class TestPhysicalResidueCreation(WrapperTesting):

    def test_MakeSingleResidueChain(self):
        ch = self.project.createChain(sequence='a', molType='protein')
        self.assertEqual(len(ch.residues), 1)

    def test_MakeTwoResidueChain_Length(self):
        ch = self.project.createChain(sequence='ga', molType='protein')
        self.assertRaises(Exception, len, ch)

    def test_MakeTwoResidueChain_ResiduesLength(self):
        ch = self.project.createChain(sequence='ga', molType='protein')
        self.assertEqual(len(ch.residues), 2)


class TestPhysicalResidueProperties(WrapperTesting):
    def setUp(self):
        with self.initialSetup():
            self.physicalChain = self.project.createChain(sequence='acd', molType='protein')
            self.r0, self.r1, self.r2 = self.physicalChain.residues

    def test_ResidueTypesOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.residueType, 'ALA')
        self.assertEqual(self.r1.residueType, 'CYS')
        self.assertEqual(self.r2.residueType, 'ASP')

    def test_NumberOfAtomsInMolecularResiduesInChain(self):
        self.assertEqual(sorted(x.name for x in self.r0.atoms),
                         ['C', 'CA', 'CB', 'H%', 'H1', 'H2', 'H3', 'HA', 'HB%', 'HB1', 'HB2', 'HB3', 'MB', 'N', 'O']
                         )
        self.assertEqual(sorted(x.name for x in self.r1.atoms),
                         ['C', 'CA', 'CB', 'H', 'HA', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'HG', 'N', 'O', 'QB', 'SG']
                         )
        self.assertEqual(sorted(x.name for x in self.r2.atoms),
                         ['C', 'CA', 'CB', 'CG', 'H', 'HA', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy',
                          'N', 'O', 'OD1', 'OD2', 'OXT', 'QB']
                         )

    def test_ShortNamesOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.shortName, 'A')
        self.assertEqual(self.r1.shortName, 'C')
        self.assertEqual(self.r2.shortName, 'D')

    def test_ShortClassNamesOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.shortClassName, 'MR')
        self.assertEqual(self.r1.shortClassName, 'MR')
        self.assertEqual(self.r2.shortClassName, 'MR')

    def test_ClassNamesOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.className, 'Residue')
        self.assertEqual(self.r1.className, 'Residue')
        self.assertEqual(self.r2.className, 'Residue')

    def test_IdsOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.id, 'A.1.ALA')
        self.assertEqual(self.r1.id, 'A.2.CYS')
        self.assertEqual(self.r2.id, 'A.3.ASP')

    def test_LinkingOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.linking, 'start')
        self.assertEqual(self.r1.linking, 'middle')
        self.assertEqual(self.r2.linking, 'end')

    def test_PidsOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.pid, 'MR:A.1.ALA')
        self.assertEqual(self.r1.pid, 'MR:A.2.CYS')
        self.assertEqual(self.r2.pid, 'MR:A.3.ASP')

    def test_LongPidsOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.longPid, 'Residue:A.1.ALA')
        self.assertEqual(self.r1.longPid, 'Residue:A.2.CYS')
        self.assertEqual(self.r2.longPid, 'Residue:A.3.ASP')

    def test_PreviousResiduesOfMolecularResiduesInChain(self):
        self.assertIsNone(self.r0.previousResidue)
        self.assertEqual(self.r1.previousResidue.pid, 'MR:A.1.ALA')
        self.assertEqual(self.r2.previousResidue.pid, 'MR:A.2.CYS')
        self.assertTrue(self.r1.previousResidue is self.r0)
        self.assertTrue(self.r2.previousResidue is self.r1)

    def test_NextResiduesOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.nextResidue.pid, 'MR:A.2.CYS')
        self.assertEqual(self.r1.nextResidue.pid, 'MR:A.3.ASP')
        self.assertIsNone(self.r2.nextResidue)
        self.assertTrue(self.r0.nextResidue is self.r1)
        self.assertTrue(self.r1.nextResidue is self.r2)

    def test_SequenceCodesOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.sequenceCode, '1')
        self.assertEqual(self.r1.sequenceCode, '2')
        self.assertEqual(self.r2.sequenceCode, '3')

    def test_NmrResidueOfMolecularResiduesInChain(self):
        self.assertIsNone(self.r0.nmrResidue)

        nmrChain = self.project.newNmrChain()

        obj = nmrChain.newNmrResidue()
        # self.r0.nmrResidue = obj
        nmrChain.assignSingleResidue(obj, self.r0)

        self.assertEqual(self.r0.nmrResidue.pid, 'NR:A.1.ALA')
        self.assertIsNone(self.r1.nmrResidue)
        self.assertIsNone(self.r2.nmrResidue)

    def test_ProjectNameOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.project.name, 'default')
        self.assertEqual(self.r1.project.name, 'default')
        self.assertEqual(self.r2.project.name, 'default')
        self.assertTrue(self.r0.project is self.r1.project)
        self.assertTrue(self.r0.project is self.r2.project)

    def test_ChainPidOfMolecularResiduesInChain(self):
        self.assertEqual(self.r0.chain.pid, 'MC:A')
        self.assertEqual(self.r1.chain.pid, 'MC:A')
        self.assertEqual(self.r2.chain.pid, 'MC:A')
        self.assertTrue(self.r0.chain is self.r1.chain)
        self.assertTrue(self.r0.chain is self.r2.chain)
