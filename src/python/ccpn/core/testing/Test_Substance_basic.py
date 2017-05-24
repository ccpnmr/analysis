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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-05-24 16:28:34 +0100 (Wed, May 24, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
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
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class TestSubstanceCreation(WrapperTesting):
  """
  Test functions that do not require a valid Sample to be instantiated.
  """

  #=========================================================================================
  # test_newSubstance        valid names
  #=========================================================================================

  def test_newSubstance_WithoutName(self):
    """
    Test that creating a new Substance with no parameter raises TypeError.
    """
    with self.assertRaisesRegexp(TypeError, 'name must be a string'):
      self.project.newSubstance()
    self.assertEqual(len(self.project.substances), 0)

  def test_newSubstance_None(self):
    """
    Test that creating a new Substance with None raises ValueError.
    """
    with self.assertRaisesRegexp(TypeError, 'name must be a string'):
     self.project.newSubstance(None)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSubstance_EmptyName(self):
    """
    Test that creating a new Substance with '' raises ValueError.
    """
    with self.assertRaisesRegexp(ValueError, 'name must be set'):
     self.project.newSubstance('')
    self.assertEqual(len(self.project.substances), 0)

  def test_newSubstance_name(self):
    """
    Test that creating a new Substance with name 'test substance' creates a valid Substance.
    """
    s = self.project.newSubstance('test substance')

    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.substances[0], s)
    self.assertEqual(s.pid, 'SU:test substance.')

  def test_newSubstance_WithFields(self):
    """
    Test that creating a new Substance with parameters creates a valid Substance.
    """
    s = self.project.newSubstance('test substance',
                                  userCode='test_userCode',
                                  smiles=';-)')

    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.substances[0], s)
    self.assertEqual(s.pid, 'SU:test substance.')
    self.assertEqual(s.userCode, 'test_userCode')
    self.assertEqual(s.smiles, ';-)')

  #=========================================================================================
  # test_newSubstance_bad_name        invalid names
  #=========================================================================================

  def test_newSubstance_Badname(self):
    """
    Test that creating a new Substance with '^Badname' raises an error.
    ^ is a bad character and not to be included in strings.
    """
    with self.assertRaisesRegexp(ValueError, 'Character'):
      self.project.newSubstance('^Badname')
    self.assertEqual(len(self.project.substances), 0)

  def test_newSubstance_Int(self):
    """
    Test that creating a new Substance with 42 (non-string) raises an error.
    """
    # with self.assertRaisesRegexp(TypeError, 'argument of type'):
    #   self.project.newSubstance(42)
    #
    with self.assertRaisesRegexp(TypeError, 'name must be a string'):
      self.project.newSubstance(42)
    self.assertEqual(len(self.project.substances), 0)


class TestSubstance_CreationFetch(WrapperTesting):
  """
  Test functions that do not require a valid Sample to be instantiated.
  """

  #=========================================================================================
  # test_newSubstance        fetch operations
  #=========================================================================================

  def test_createPolymerSubstance(self):
    s = self.project.createPolymerSubstance('acd', name='test', molType='protein')

    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.substances[0], s)


  def test_fetchSubstanceThatAlreadyExists(self):
    s1 = self.project.newSubstance('test substance')
    s2 = self.project.fetchSubstance('test substance')
    self.assertIs(s1, s2)

  def test_fetchSubstanceNewSubstance(self):
    s1 = self.project.newSubstance('test substance')
    s2 = self.project.fetchSubstance('another test substance')

    self.assertEqual(s2.pid, 'SU:another test substance.')
    self.assertIsNot(s1, s2)


  def test_sampleComponentsMakesNewSubstances(self):
    self.assertEqual(len(self.project.substances), 0)

    sample = self.project.newSample('test sample')
    sample.newSampleComponent('test sample component')

    self.assertEqual(len(self.project.substances), 1)
    self.assertEqual(self.project.substances[0].pid, 'SU:test sample component.')


  def test_newPhysicalChainMakesNewSubstances(self):
    self.assertEqual(len(self.project.substances), 0)

    self.project.createChain('acd', molType='protein')

    self.assertEqual(len(self.project.substances), 1)
    self.assertEqual(self.project.substances[0].pid, 'SU:Molecule_1.')



class TestExistingSubstancesWithSameNameReused(WrapperTesting):

  def test_sampleComponentsUsesSubstanceWithSameName(self):
    substance = self.project.newSubstance('test sample component')
    self.assertEqual(len(self.project.substances), 1)

    sample = self.project.newSample('test sample')
    sampleComponent = sample.newSampleComponent('test sample component')

    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(substance, sampleComponent.substance)


  def _test_chainTriesToUseSubstanceWithSameName(self):
    self.project.newSubstance('Molecule_1')
    self.assertRaises(Exception, self.project.createChain, compoundName='Molecule_1',
                      sequence='acd', molType='protein')


  def test_createChainFromExistingSubstance(self):
    physicalChain = self.project.createChain('acd', molType='protein')
    newPhysicalChain = physicalChain.substances[0].createChain()
    self.assertEquals(physicalChain.substances, newPhysicalChain.substances)
    self.assertIsNot(physicalChain, newPhysicalChain)


class SubstanceProperties(WrapperTesting):

  def test_bareSubstanceProperties(self):
    s = self.project.newSubstance('test substance')

    self.assertEqual(s.pid, 'SU:test substance.')
    self.assertEqual(s.longPid, 'Substance:test substance.')
    self.assertEqual(s.shortClassName, 'SU')
    self.assertEqual(s.className, 'Substance')
    self.assertEqual(s.name, 'test substance')
    self.assertEqual(s.labelling, None)
    self.assertEqual(s.id, 'test substance.')
    self.assertEqual(s.substanceType, 'Molecule')
    self.assertIs(s.project, self.project)

    self.assertEqual(s.chains, ())
    self.assertEqual(s.synonyms, ())
    self.assertEqual(s.referenceSpectra, ())
    self.assertEqual(s.sampleComponents, ())

    self.assertEqual(s.atomCount, 0)
    self.assertEqual(s.bondCount, 0)
    self.assertIsNone(s.casNumber)
    self.assertIsNone(s.comment)
    self.assertIsNone(s.logPartitionCoefficient)
    self.assertIsNone(s.empiricalFormula)
    self.assertEqual(s.hBondAcceptorCount, 0)
    self.assertIsNone(s.molecularMass)
    self.assertEqual(s.hBondDonorCount, 0)
    self.assertIsNone(s.inChi)
    self.assertIsNone(s.polarSurfaceArea)
    self.assertEqual(s.ringCount, 0)
    self.assertIsNone(s.sequenceString)
    self.assertIsNone(s.smiles)
    self.assertIsNone(s.userCode)

    # print(s.setdefault)
    # print(s.createChain)
    # print(s.clear)
    # print(s.delete)
    # print(s.items)
    # print(s.getByPid)
    # print(s.get)
    # print(s.rename)

  def test_bareMoleculeSubstanceProperties(self):
    s = self.project.newSubstance('test substance', substanceType='Molecule')

    self.assertEqual(s.pid, 'SU:test substance.')
    self.assertEqual(s.longPid, 'Substance:test substance.')
    self.assertEqual(s.shortClassName, 'SU')
    self.assertEqual(s.className, 'Substance')
    self.assertEqual(s.name, 'test substance')
    self.assertEqual(s.labelling, None)
    self.assertEqual(s.id, 'test substance.')
    self.assertEqual(s.substanceType, 'Molecule')
    self.assertIs(s.project, self.project)

    self.assertEqual(s.chains, ())
    self.assertEqual(s.synonyms, ())
    self.assertEqual(s.referenceSpectra, ())
    self.assertEqual(s.sampleComponents, ())

    self.assertEqual(s.atomCount, 0)
    self.assertEqual(s.bondCount, 0)
    self.assertIsNone(s.casNumber)
    self.assertIsNone(s.comment)
    self.assertIsNone(s.logPartitionCoefficient)
    self.assertIsNone(s.empiricalFormula)
    self.assertEqual(s.hBondAcceptorCount, 0)
    self.assertIsNone(s.molecularMass)
    self.assertEqual(s.hBondDonorCount, 0)
    self.assertIsNone(s.inChi)
    self.assertIsNone(s.polarSurfaceArea)
    self.assertEqual(s.ringCount, 0)
    self.assertIsNone(s.sequenceString)
    self.assertIsNone(s.smiles)
    self.assertIsNone(s.userCode)

  def test_MoleculeSubstanceWithSmilesProperties(self):
    """
    Test that the smiles property can be set.
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  smiles='CCCC')
    self.assertEqual(s.smiles, 'CCCC')
    s.smiles = 'DDDD'
    self.assertEqual(s.smiles, 'DDDD')

  def test_MoleculeSubstanceWithNoSmilesProperties(self):
    """
    Test that the smiles property cannot be set for no attribute
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule')
    with self.assertRaisesRegexp(TypeError, 'Substance has no attribute'):
      s.smiles = 'CCCC'

  def test_MoleculeSubstanceWithinChiProperties(self):
    """
    Test that the inChi property of Substance can be set
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  inChi='1/C2H6O/c1-2-3/h3H,2H2,1H3')
    self.assertEqual(s.inChi, '1/C2H6O/c1-2-3/h3H,2H2,1H3')
    s.inChi = '1/C2H6O/c1-2-3/h3H,2H2,1H4'
    self.assertEqual(s.inChi, '1/C2H6O/c1-2-3/h3H,2H2,1H4')

  def test_MoleculeSubstanceWithNoInChiProperties(self):
    """
    Test that the inChi property of Substance cannot be set for no attribute
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule')
    with self.assertRaisesRegexp(TypeError, 'Substance has no attribute'):
      s.inChi = '1/C2H6O/c1-2-3/h3H,2H2,1H4'

  def test_MoleculeSubstanceWithLabellingProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  labelling='anything')
    self.assertEqual(s.labelling, 'anything')

  def test_MoleculeSubstanceWithCasNumberProperties(self):
    """
    Test that the casNumber property of Substance can be set
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  casNumber='64-17-5')
    self.assertEqual(s.casNumber, '64-17-5')
    s.casNumber = '64-16-3'
    self.assertEqual(s.casNumber, '64-16-3')

  def test_MoleculeSubstanceWithNoCasNumberProperties(self):
    """
    Test that the casNumber property of Substance can be set
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule')
    s.casNumber = '64-16-3'
    with self.assertRaisesRegexp(TypeError, 'Substance has no attribute'):
      self.assertEqual(s.casNumber, '64-16-3')

  def test_MoleculeSubstanceWithUserCodeCasNumberProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  userCode='test code')
    self.assertEqual(s.userCode, 'test code')

  def test_MoleculeSubstanceWithEmpiricalFormulaProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  empiricalFormula='C6H12O6')
    self.assertEqual(s.empiricalFormula, 'C6H12O6')

  def test_MoleculeSubstanceWithMolecularMassProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  molecularMass=42.0)
    self.assertEqual(s.molecularMass, 42.0)

  def test_MoleculeSubstanceWithCommentProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  comment='random comment.')
    self.assertEqual(s.comment, 'random comment.')

  def test_MoleculeSubstanceWithSynonymsProperties(self):
    """
    Test that the synonyms property of Substance can be set
    """
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  synonyms=['syn1','syn2'])
    self.assertEqual(s.synonyms, ('syn1', 'syn2'))
    s.synonyms = ['syn1','syn3']
    self.assertEqual(s.synonyms, ('syn1', 'syn3'))

  def test_MoleculeSubstanceWithAtomCountProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  atomCount=12)
    self.assertEqual(s.atomCount, 12)

  def test_MoleculeSubstanceWithBondCountProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  bondCount=11)
    self.assertEqual(s.bondCount, 11)

  def test_MoleculeSubstanceWithRingCountProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  ringCount=3)
    self.assertEqual(s.ringCount, 3)

  def test_MoleculeSubstanceWithHBondDonorCountProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  hBondDonorCount=2)
    self.assertEqual(s.hBondDonorCount, 2)

  def test_MoleculeSubstanceWithHBondAcceptorCountProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  hBondAcceptorCount=2)
    self.assertEqual(s.hBondAcceptorCount, 2)

  def test_MoleculeSubstanceWithPolarSurfaceAreaProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  polarSurfaceArea=2)
    self.assertEqual(s.polarSurfaceArea, 2)

  def test_MoleculeSubstanceWithLogPartitionCoefficientProperties(self):
    s = self.project.newSubstance('test substance',
                                  substanceType='Molecule',
                                  logPartitionCoefficient=2)
    self.assertEqual(s.logPartitionCoefficient, 2)


  @unittest.skip
  def test_bareMaterialSubstanceProperties(self):
    s = self.project.newSubstance('test substance', substanceType='Material')

    # MOved below initialisation of 's'. Rasmus.
    self.assertIsNone(s.smiles)

    self.assertEqual(s.pid, 'SU:test substance.')
    self.assertEqual(s.longPid, 'Substance:test substance.')
    self.assertEqual(s.shortClassName, 'SU')
    self.assertEqual(s.className, 'Substance')
    self.assertEqual(s.name, 'test substance')
    self.assertEqual(s.labelling, None)
    self.assertEqual(s.id, 'test substance.')
    self.assertEqual(s.substanceType, 'Material')
    self.assertIs(s.project, self.project)


    self.assertEqual(s.chains, ())
    self.assertEqual(s.synonyms, ())
    self.assertEqual(s.referenceSpectra, ())
    self.assertEqual(s.sampleComponents, ())

    self.assertIsNone(s.atomCount)
    self.assertIsNone(s.bondCount)
    self.assertIsNone(s.casNumber)
    self.assertIsNone(s.comment)
    self.assertIsNone(s.logPartitionCoefficient)
    self.assertIsNone(s.empiricalFormula)
    self.assertIsNone(s.hBondAcceptorCount)
    self.assertIsNone(s.molecularMass)
    self.assertIsNone(s.hBondDonorCount)
    self.assertIsNone(s.inChi)
    self.assertIsNone(s.polarSurfaceArea)
    self.assertIsNone(s.ringCount)
    self.assertIsNone(s.sequenceString)
    self.assertIsNone(s.userCode)

  @unittest.skip
  def test_bareCellSubstanceProperties(self):
    # name, labelling, usercode, synonyms, details
    s = self.project.newSubstance('test substance', substanceType='Cell')

    self.assertEqual(s.pid, 'SU:test substance.')
    self.assertEqual(s.longPid, 'Substance:test substance.')
    self.assertEqual(s.shortClassName, 'SU')
    self.assertEqual(s.className, 'Substance')
    self.assertEqual(s.name, 'test substance')
    self.assertEqual(s.labelling, None)
    self.assertEqual(s.id, 'test substance.')
    self.assertEqual(s.substanceType, 'Cell')
    self.assertIs(s.project, self.project)

    self.assertEqual(s.chains, ())
    self.assertEqual(s.synonyms, ())
    self.assertEqual(s.referenceSpectra, ())
    self.assertEqual(s.sampleComponents, ())

    self.assertIsNone(s.atomCount)
    self.assertIsNone(s.bondCount)
    self.assertIsNone(s.casNumber)
    self.assertIsNone(s.comment)
    self.assertIsNone(s.logPartitionCoefficient)
    self.assertIsNone(s.empiricalFormula)
    self.assertIsNone(s.hBondAcceptorCount)
    self.assertIsNone(s.molecularMass)
    self.assertIsNone(s.hBondDonorCount)
    self.assertIsNone(s.inChi)
    self.assertIsNone(s.polarSurfaceArea)
    self.assertIsNone(s.ringCount)
    self.assertIsNone(s.sequenceString)
    self.assertIsNone(s.smiles)
    self.assertIsNone(s.userCode)

  @unittest.skip
  def test_bareCompositeSubstanceProperties(self):
    s = self.project.newSubstance('test substance', substanceType='Composite')

    self.assertEqual(s.pid, 'SU:test substance.')
    self.assertEqual(s.longPid, 'Substance:test substance.')
    self.assertEqual(s.shortClassName, 'SU')
    self.assertEqual(s.className, 'Substance')
    self.assertEqual(s.name, 'test substance')
    self.assertEqual(s.labelling, None)
    self.assertEqual(s.id, 'test substance.')
    self.assertEqual(s.substanceType, 'Composite')
    self.assertIs(s.project, self.project)

    self.assertEqual(s.chains, ())
    self.assertEqual(s.synonyms, ())
    self.assertEqual(s.referenceSpectra, ())
    self.assertEqual(s.sampleComponents, ())

    self.assertIsNone(s.atomCount)
    self.assertIsNone(s.bondCount)
    self.assertIsNone(s.casNumber)
    self.assertIsNone(s.comment)
    self.assertIsNone(s.logPartitionCoefficient)
    self.assertIsNone(s.empiricalFormula)
    self.assertIsNone(s.hBondAcceptorCount)
    self.assertIsNone(s.molecularMass)
    self.assertIsNone(s.hBondDonorCount)
    self.assertIsNone(s.inChi)
    self.assertIsNone(s.polarSurfaceArea)
    self.assertIsNone(s.ringCount)
    self.assertIsNone(s.sequenceString)
    self.assertIsNone(s.smiles)
    self.assertIsNone(s.userCode)

  # @unittest.expectedFailure
  def test_bareUndefinedSubstanceProperties(self):
    self.assertRaises(ValueError, self.project.newSubstance, name='test substance',
                      substanceType='other')

  def test_PolymerSubstanceWithLabellingProperties(self):
    s = self.project.createPolymerSubstance('acd',
                                            name='test polymer substance',
                                            molType='protein',
                                            labelling='H')
    self.assertEqual(s.labelling, 'H')

  def test_PolymerSubstanceWithUserCodeProperties(self):
    s = self.project.createPolymerSubstance('acd',
                                            name='test polymer substance',
                                            molType='protein',
                                            userCode='test code')
    self.assertEqual(s.userCode, 'test code')

  def test_PolymerSubstanceWithSmilesProperties(self):
    """
    Test that the smiles property of Substance can be set.
    """
    s = self.project.createPolymerSubstance('acd',
                                            name='test polymer substance',
                                            molType='protein',
                                            smiles='CCCC')
    self.assertEqual(s.smiles, 'CCCC')
    s.smiles = 'DDDD'
    self.assertEqual(s.smiles, 'DDDD')

  def test_PolymerSubstanceWithSynonymsProperties(self):
    s = self.project.createPolymerSubstance('acd',
                                            name='test polymer substance',
                                            molType='protein',
                                            synonyms=['syn1','syn2'])
    self.assertEqual(s.synonyms, ('syn1','syn2'))

  def test_PolymerSubstanceWithCommentsProperties(self):
    s = self.project.createPolymerSubstance('acd',
                                            name='test polymer substance',
                                            molType='protein',
                                            comment = 'test comment')
    self.assertEqual(s.comment, 'test comment')

  def _test_PolymerSubstanceWithStartNumberProperties(self):
    s = self.project.createPolymerSubstance('acd',
                                            name='test polymer substance',
                                            molType='protein',
                                            startNumber=7)
    # self.assertEqual(s.startNumber, 7)

