"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:33 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from ccpn.core.lib.MoleculeLib import duplicateAtomBonds
from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr


boundAtomsTestData = collections.OrderedDict((
    ('A.1.CYS.C', ['CA', 'O', 'A.2.ASP.N']),
    ('A.1.CYS.CA', ['C', 'CB', 'HA', 'N']),
    ('A.1.CYS.CB', ['CA', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'QB', 'SG']),
    ('A.1.CYS.H%', ['N']),
    ('A.1.CYS.H1', ['N']),
    ('A.1.CYS.H2', ['N']),
    ('A.1.CYS.H3', ['N']),
    ('A.1.CYS.HA', ['CA']),
    ('A.1.CYS.HB%', ['CB']),
    ('A.1.CYS.HB2', ['CB']),
    ('A.1.CYS.HB3', ['CB']),
    ('A.1.CYS.HBx', ['CB']),
    ('A.1.CYS.HBy', ['CB']),
    ('A.1.CYS.HG', ['SG']),
    ('A.1.CYS.N', ['CA', 'H%', 'H1', 'H2', 'H3']),
    ('A.1.CYS.O', ['C']),
    ('A.1.CYS.QB', ['CB']),
    ('A.1.CYS.SG', ['CB', 'HG']),
    ('A.2.ASP.C', ['CA', 'O', 'A.3.LEU.N']),
    ('A.2.ASP.CA', ['C', 'CB', 'HA', 'N']),
    ('A.2.ASP.CB', ['CA', 'CG', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'QB']),
    ('A.2.ASP.CG', ['CB', 'OD1', 'OD2']),
    ('A.2.ASP.H', ['N']),
    ('A.2.ASP.HA', ['CA']),
    ('A.2.ASP.HB%', ['CB']),
    ('A.2.ASP.HB2', ['CB']),
    ('A.2.ASP.HB3', ['CB']),
    ('A.2.ASP.HBx', ['CB']),
    ('A.2.ASP.HBy', ['CB']),
    ('A.2.ASP.N', ['A.1.CYS.C', 'CA', 'H']),
    ('A.2.ASP.O', ['C']),
    ('A.2.ASP.OD1', ['CG']),
    ('A.2.ASP.OD2', ['CG']),
    ('A.2.ASP.QB', ['CB']),
    ('A.3.LEU.C', ['CA', 'O', 'OXT']),
    ('A.3.LEU.CA', ['C', 'CB', 'HA', 'N']),
    ('A.3.LEU.CB', ['CA', 'CG', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'QB']),
    ('A.3.LEU.CD%', ['CG', 'HD%']),
    ('A.3.LEU.CD1', ['CG', 'HD1%', 'HD11', 'HD12', 'HD13', 'MD1']),
    ('A.3.LEU.CD2', ['CG', 'HD2%', 'HD21', 'HD22', 'HD23', 'MD2']),
    ('A.3.LEU.CDx', ['CG', 'HDx%']),
    ('A.3.LEU.CDy', ['CG', 'HDy%']),
    ('A.3.LEU.CG', ['CB', 'CD%', 'CD1', 'CD2', 'CDx', 'CDy', 'HG']),
    ('A.3.LEU.H', ['N']),
    ('A.3.LEU.HA', ['CA']),
    ('A.3.LEU.HB%', ['CB']),
    ('A.3.LEU.HB2', ['CB']),
    ('A.3.LEU.HB3', ['CB']),
    ('A.3.LEU.HBx', ['CB']),
    ('A.3.LEU.HBy', ['CB']),
    ('A.3.LEU.HD%', ['CD%']),
    ('A.3.LEU.HD1%', ['CD1']),
    ('A.3.LEU.HD11', ['CD1']),
    ('A.3.LEU.HD12', ['CD1']),
    ('A.3.LEU.HD13', ['CD1']),
    ('A.3.LEU.HD2%', ['CD2']),
    ('A.3.LEU.HD21', ['CD2']),
    ('A.3.LEU.HD22', ['CD2']),
    ('A.3.LEU.HD23', ['CD2']),
    ('A.3.LEU.HDx%', ['CDx']),
    ('A.3.LEU.HDy%', ['CDy']),
    ('A.3.LEU.HG', ['CG']),
    ('A.3.LEU.MD1', ['CD1']),
    ('A.3.LEU.MD2', ['CD2']),
    ('A.3.LEU.N', ['A.2.ASP.C', 'CA', 'H']),
    ('A.3.LEU.O', ['C']),
    ('A.3.LEU.OXT', ['C']),
    ('A.3.LEU.QB', ['CB']),
    ('A.3.LEU.QD', []),
    ('B.1.PHE.C', ['CA', 'O', 'B.2.PRO.N']),
    ('B.1.PHE.CA', ['C', 'CB', 'HA', 'N']),
    ('B.1.PHE.CB', ['CA', 'CG', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'QB']),
    ('B.1.PHE.CD%', ['CE%', 'CG', 'HD%']),
    ('B.1.PHE.CD1', ['CE1', 'CG', 'HD1']),
    ('B.1.PHE.CD2', ['CE2', 'CG', 'HD2']),
    ('B.1.PHE.CDx', ['CEx', 'CG', 'HDx']),
    ('B.1.PHE.CDy', ['CEy', 'CG', 'HDy']),
    ('B.1.PHE.CE%', ['CD%', 'CZ', 'HE%']),
    ('B.1.PHE.CE1', ['CD1', 'CZ', 'HE1']),
    ('B.1.PHE.CE2', ['CD2', 'CZ', 'HE2']),
    ('B.1.PHE.CEx', ['CDx', 'CZ', 'HEx']),
    ('B.1.PHE.CEy', ['CDy', 'CZ', 'HEy']),
    ('B.1.PHE.CG', ['CB', 'CD%', 'CD1', 'CD2', 'CDx', 'CDy']),
    ('B.1.PHE.CZ', ['CE%', 'CE1', 'CE2', 'CEx', 'CEy', 'HZ']),
    ('B.1.PHE.H%', ['N']),
    ('B.1.PHE.H1', ['N']),
    ('B.1.PHE.H2', ['N']),
    ('B.1.PHE.H3', ['N']),
    ('B.1.PHE.HA', ['CA']),
    ('B.1.PHE.HB%', ['CB']),
    ('B.1.PHE.HB2', ['CB']),
    ('B.1.PHE.HB3', ['CB']),
    ('B.1.PHE.HBx', ['CB']),
    ('B.1.PHE.HBy', ['CB']),
    ('B.1.PHE.HD%', ['CD%']),
    ('B.1.PHE.HD%|HE%', []),
    ('B.1.PHE.HD1', ['CD1']),
    ('B.1.PHE.HD2', ['CD2']),
    ('B.1.PHE.HDx', ['CDx']),
    ('B.1.PHE.HDy', ['CDy']),
    ('B.1.PHE.HE%', ['CE%']),
    ('B.1.PHE.HE1', ['CE1']),
    ('B.1.PHE.HE2', ['CE2']),
    ('B.1.PHE.HEx', ['CEx']),
    ('B.1.PHE.HEy', ['CEy']),
    ('B.1.PHE.HZ', ['CZ']),
    ('B.1.PHE.N', ['CA', 'H%', 'H1', 'H2', 'H3']),
    ('B.1.PHE.O', ['C']),
    ('B.1.PHE.QB', ['CB']),
    ('B.1.PHE.QD', []),
    ('B.1.PHE.QE', []),
    ('B.1.PHE.QR', []),
    ('B.2.PRO.C', ['CA', 'O', 'B.3.CYS.N']),
    ('B.2.PRO.CA', ['C', 'CB', 'HA', 'N']),
    ('B.2.PRO.CB', ['CA', 'CG', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'QB']),
    ('B.2.PRO.CD', ['CG', 'HD%', 'HD2', 'HD3', 'HDx', 'HDy', 'N', 'QD']),
    ('B.2.PRO.CG', ['CB', 'CD', 'HG%', 'HG2', 'HG3', 'HGx', 'HGy', 'QG']),
    ('B.2.PRO.HA', ['CA']),
    ('B.2.PRO.HB%', ['CB']),
    ('B.2.PRO.HB2', ['CB']),
    ('B.2.PRO.HB3', ['CB']),
    ('B.2.PRO.HBx', ['CB']),
    ('B.2.PRO.HBy', ['CB']),
    ('B.2.PRO.HD%', ['CD']),
    ('B.2.PRO.HD2', ['CD']),
    ('B.2.PRO.HD3', ['CD']),
    ('B.2.PRO.HDx', ['CD']),
    ('B.2.PRO.HDy', ['CD']),
    ('B.2.PRO.HG%', ['CG']),
    ('B.2.PRO.HG2', ['CG']),
    ('B.2.PRO.HG3', ['CG']),
    ('B.2.PRO.HGx', ['CG']),
    ('B.2.PRO.HGy', ['CG']),
    ('B.2.PRO.N', ['B.1.PHE.C', 'CA', 'CD']),
    ('B.2.PRO.O', ['C']),
    ('B.2.PRO.QB', ['CB']),
    ('B.2.PRO.QD', ['CD']),
    ('B.2.PRO.QG', ['CG']),
    ('B.3.CYS.C', ['CA', 'O', 'OXT']),
    ('B.3.CYS.CA', ['C', 'CB', 'HA', 'N']),
    ('B.3.CYS.CB', ['CA', 'HB%', 'HB2', 'HB3', 'HBx', 'HBy', 'QB', 'SG']),
    ('B.3.CYS.H', ['N']),
    ('B.3.CYS.HA', ['CA']),
    ('B.3.CYS.HB%', ['CB']),
    ('B.3.CYS.HB2', ['CB']),
    ('B.3.CYS.HB3', ['CB']),
    ('B.3.CYS.HBx', ['CB']),
    ('B.3.CYS.HBy', ['CB']),
    ('B.3.CYS.HG', ['SG']),
    ('B.3.CYS.N', ['B.2.PRO.C', 'CA', 'H']),
    ('B.3.CYS.O', ['C']),
    ('B.3.CYS.OXT', ['C']),
    ('B.3.CYS.QB', ['CB']),
    ('B.3.CYS.SG', ['CB', 'HG']),
    ))

from ccpn.core.testing.WrapperTesting import WrapperTesting


#=========================================================================================
# ChainTest
#=========================================================================================

class ChainTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = None

    #=========================================================================================
    # test_rename_chain
    #=========================================================================================

    def test_rename_chain(self):

        chain = self.project.createChain('ACDC', shortName='A', molType='protein')
        nmrChain = self.project.newNmrChain(shortName='A')
        undo = self.project._undo
        self.project.newUndoPoint()
        chain.rename('B')
        self.assertEqual(chain.shortName, 'B')
        self.assertEqual(nmrChain.shortName, 'B')
        undo.undo()
        self.assertEqual(chain.shortName, 'A')
        self.assertEqual(nmrChain.shortName, 'A')
        undo.redo()
        self.assertEqual(chain.shortName, 'B')
        self.assertEqual(nmrChain.shortName, 'B')

    #=========================================================================================
    # testBoundAtoms
    #=========================================================================================

    def testBoundAtoms(self):
        project = self.project
        chaina = project.createChain('CDL', compoundName='cdl', molType='protein')
        chainb = project.createChain('FPC', compoundName='fpc', molType='protein')
        for chain in chaina, chainb:
            for atom in chain.atoms:
                self.assertEquals(boundAtomsTestData.get(atom._id, []),
                                  [(x.name if x.residue is atom.residue else x._id)
                                   for x in atom.boundAtoms])

    #=========================================================================================
    # testCrosslinkAtoms
    #=========================================================================================

    def testCrosslinkAtoms(self):
        project = self.project
        project._wrappedData.checkAllValid(complete=True)
        chaina = project.createChain('CDL', compoundName='cdl', molType='protein')
        chainb = project.createChain('FPC', compoundName='fpc', molType='protein')
        project.getByPid('MA:A.1.CYS.HG').delete()
        project.getByPid('MA:B.3.CYS.HG').delete()
        atom1 = project.getByPid('MA:A.1.CYS.SG')
        atom2 = project.getByPid('MA:B.3.CYS.SG')
        atom1.addInterAtomBond(atom2)
        self.assertEquals([x._id for x in atom1.boundAtoms], ['A.1.CYS.CB', 'B.3.CYS.SG'])
        self.assertEquals([x._id for x in atom2.boundAtoms], ['A.1.CYS.SG', 'B.3.CYS.CB'])

        chainc = chaina.clone()

        # first error here
        # constraint
        # linking_and_descriptor_must_be_consistent_with_Atoms_and_LinkEnds
        # violated: < ccp.molecule.MolSystem.Residue['default', 'C', 3] >

        chaind = chainb.clone()
        duplicateAtomBonds(({chaina: chainc, chainb: chaind}))
        project._wrappedData.checkAllValid(complete=True)
        atom1 = project.getByPid('MA:C.1.CYS.SG')
        atom2 = project.getByPid('MA:D.3.CYS.SG')
        atom3 = project.getByPid('MA:C.1.CYS.HG')
        atom4 = project.getByPid('MA:D.3.CYS.HG')
        self.assertEquals([x._id for x in atom1.boundAtoms], ['C.1.CYS.CB', 'D.3.CYS.SG'])
        self.assertEquals([x._id for x in atom2.boundAtoms], ['C.1.CYS.SG', 'D.3.CYS.CB'])
        self.assertIsNone(atom3)
        self.assertIsNone(atom4)


#=========================================================================================
# Test_Properties
#=========================================================================================

class Test_Properties(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    #=========================================================================================
    # setUp       initialise a new chain and nmrChain
    #=========================================================================================

    def setUp(self):
        """
        Create a valid chain and nmrChain
        """
        with self.initialSetup():
            self.chain = self.project.createChain('ACDC', shortName='A', molType='protein')
            self.nmrChain = self.project.newNmrChain(shortName='A')

    #=========================================================================================
    # Test_properties
    #=========================================================================================

    def test_Properties_shortName(self):
        self.shortName = self.chain.shortName

    def test_Properties_compoundName(self):
        self.compoundName = self.chain.compoundName

    def test_Properties_cyclic(self):
        self.cyclic = self.chain.isCyclic

    def test_Properties_role(self):
        checkGetSetAttr(self, obj=self.chain, attrib='role', value='free')

    def test_Properties_comment(self):
        checkGetSetAttr(self, obj=self.chain, attrib='comment', value='free')

    #=========================================================================================
    # Test_renameChain
    #=========================================================================================

    def test_renameChain_WithoutName(self):
        """
        Test that renaming a Chain with no parameter raises TypeError.
        """
        with self.assertRaisesRegexp(TypeError, 'required positional argument'):
            self.chain.rename()

    def test_renameChain_None(self):
        """
        Test that renaming a Chain with None raises TypeError.
        """
        with self.assertRaisesRegexp(TypeError, 'must be a string'):
            self.chain.rename(None)

    def test_renameChain_Int(self):
        """
        Test that renaming a Chain with 42 raises TypeError.
        """
        with self.assertRaisesRegexp(TypeError, 'must be a string'):
            self.chain.rename(42)

    def test_renameChain_ES(self):
        """
        Test that renaming a Chain with '' raises ValueError.
        """
        with self.assertRaisesRegexp(ValueError, 'must be set'):
            self.chain.rename('')

    def test_renameChain_Badname(self):
        """
        Test that renaming a Chain with ^Badname raises ValueError.
        """
        with self.assertRaisesRegexp(ValueError, 'not allowed'):
            self.chain.rename('^Badname')

    def test_renameChain_Whitespace(self):
        """
        Test that renaming a Chain with whitespace raises ValueError.
        """
        with self.assertRaisesRegexp(ValueError, 'whitespace not allowed'):
            self.chain.rename('not found')

    #=========================================================================================
    # Test_NewChain
    #=========================================================================================

    def test_newChain_WithoutName(self):
        """
        Test that creating a new Chain with no parameter - no error
        """
        self.newChain = self.project.createChain('ACDC', molType='protein')
        self.assertEqual(len(self.project.chains), 2)

    def test_newChain_None(self):
        """
        Test that creating a new Chain with None - no error .
        """
        self.newChain = self.project.createChain('ACDC', shortName=None, molType='protein')
        self.assertEqual(len(self.project.chains), 2)

    def test_newChain_Int(self):
        """
        Test that creating a new Chain with 42 raises TypeError.
        """
        with self.assertRaisesRegexp(TypeError, 'must be a string'):
            self.newChain = self.project.createChain('ACDC', shortName=42, molType='protein')
        self.assertEqual(len(self.project.chains), 1)

    def test_newChain_Badname(self):
        """
        Test that creating a new Chain with ^Badname raises ValueError.
        """
        with self.assertRaisesRegexp(ValueError, 'not allowed in'):
            self.newChain = self.project.createChain('ACDC', shortName='^Badname', molType='protein')
        self.assertEqual(len(self.project.chains), 1)

    def test_newChain_Exists(self):
        """
        Test that creating a new Chain with existing raises ValueError.
        """
        self.newChain = self.project.createChain('ACDC', shortName='exists', molType='protein')
        with self.assertRaisesRegexp(ValueError, 'already exists'):
            self.newChain = self.project.createChain('ACDC', shortName='exists', molType='protein')
        self.assertEqual(len(self.project.chains), 2)
