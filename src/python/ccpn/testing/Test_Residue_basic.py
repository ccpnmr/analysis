__author__ = 'TJ Ragan'

import unittest

from ccpn.testing.WrapperTesting import WrapperTesting


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
    self.assertEqual(len(self.r0.atoms), 15)
    self.assertEqual(len(self.r1.atoms), 15)
    self.assertEqual(len(self.r2.atoms), 17)

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
    self.r0.nmrResidue = obj
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
