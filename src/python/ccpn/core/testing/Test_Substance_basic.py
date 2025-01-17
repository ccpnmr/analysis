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
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class TestSubstanceCreation(WrapperTesting):
    """
    Test functions that do not require a valid Sample to be instantiated.
    """

    #=========================================================================================
    # test_newSubstance        valid names
    #=========================================================================================

    def test_newSubstance_WithFields(self):
        """
        Test that creating a new Substance with parameters creates a valid Substance.
        """
        s = self.project.newSubstance('testSubstance',
                                      userCode='test_userCode',
                                      smiles=';-)')

        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)
        self.assertEqual(s.pid, 'SU:testSubstance.')
        self.assertEqual(s.userCode, 'test_userCode')
        self.assertEqual(s.smiles, ';-)')

    def test_newSubstance_Int42(self):
        """
        Test that creating a new Substance with 42 (non-string) creates a substance with the name '42'
        """
        s = self.project.newSubstance(42)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)
        self.assertEqual(s.pid, 'SU:42.')

    def test_newSubstance_Int0(self):
        """
        Test that creating a new Substance with 0 (non-string) creates a substance with the name '0'
        """
        s = self.project.newSubstance(0)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)
        self.assertEqual(s.pid, 'SU:0.')

    def test_newSubstance_None(self):
        """
        Test that creating a new Substance with None creates a substance with name 'mySubstance_1'.
        """
        s = self.project.newSubstance(None)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)
        self.assertEqual(s.pid, 'SU:mySubstance.')

    def test_newSubstance_WithoutName(self):
        """
        Test that creating a new Substance with no parameter creates a substance with name 'mySubstance_1'.
        """
        s = self.project.newSubstance()
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)
        self.assertEqual(s.pid, 'SU:mySubstance.')

    #=========================================================================================
    # test_newSubstance_bad_name        invalid names
    #=========================================================================================

    def test_newSubstance_Badname(self):
        """
        Test that creating a new Substance with '^Badname' raises an error.
        ^ is a bad character and not to be included in strings.
        """
        with self.assertRaisesRegex(ValueError, 'Character'):
            self.project.newSubstance('^Badname')
        self.assertEqual(len(self.project.substances), 0)

    def test_newSubstance_Float(self):
        """
        Test that creating a new Substance with 42.0 (non-string) raises TypeError
        """
        with self.assertRaisesRegex(ValueError, 'must be a string'):
            s = self.project.newSubstance(42.0)
        self.assertEqual(len(self.project.substances), 0)

    def test_newSubstance_EmptyName(self):
        """
        Test that creating a new Substance with '' raises ValueError.
        """
        with self.assertRaisesRegex(ValueError, 'must be set'):
            self.project.newSubstance('')
        self.assertEqual(len(self.project.substances), 0)

    def test_newSubstance_WhitespaceName(self):
        """
        Test that creating a new Substance with leading/trailing whitespace raises ValueError.
        """
        with self.assertRaisesRegex(ValueError, 'not allowed in'):
            self.project.newSubstance(' newName ')
        self.assertEqual(len(self.project.substances), 0)

    def test_newSubstance_name(self):
        """
        Test that creating a new Substance with name 'testSubstance' creates a valid Substance.
        """
        s = self.project.newSubstance('testSubstance')

        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)
        self.assertEqual(s.pid, 'SU:testSubstance.')

        # same name and labelling as above
        s2 = self.project.newSubstance('testSubstance')
        self.assertEqual(s2.pid, 'SU:testSubstance_1.')

    def test_newSubstance_WhitespaceLabelling(self):
        """
        Test that creating a new Substance with leading/trailing whitespace raises ValueError.
        """
        with self.assertRaisesRegex(ValueError, 'not allowed in'):
            self.project.newSubstance('newName', ' whitespaceLabel ')
        self.assertEqual(len(self.project.substances), 0)


class TestSubstance_CreationFetch(WrapperTesting):
    """
    Test functions that do not require a valid Sample to be instantiated.
    """

    #=========================================================================================
    # test_newSubstance        fetch operations
    #=========================================================================================

    def test_createPolymerSubstance(self):
        """
        Test that creating a new Substance populates the array
        """
        s = self.project.createPolymerSubstance('acd', name='test', molType='protein')

        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.substances[0], s)

    def test_fetchSubstanceThatAlreadyExists(self):
        """
        Test that the correct Substance is fetched
        """
        s1 = self.project.newSubstance('testSubstance')
        s2 = self.project.fetchSubstance('testSubstance')
        self.assertIs(s1, s2)

    def test_fetchSubstanceNewSubstance(self):
        """
        Test that the correct (different) Substance is fetched
        """
        s1 = self.project.newSubstance('testSubstance')
        s2 = self.project.fetchSubstance('anotherTestSubstance')

        self.assertEqual(s2.pid, 'SU:anotherTestSubstance.')
        self.assertIsNot(s1, s2)

    def test_sampleComponentsMakesNewSubstances(self):
        """
        Test that the new Substance initialises correctly
        """
        self.assertEqual(len(self.project.substances), 0)

        sample = self.project.newSample('testSample')
        sample.newSampleComponent('testSampleComponent')

        self.assertEqual(len(self.project.substances), 1)
        self.assertEqual(self.project.substances[0].pid, 'SU:testSampleComponent.')

    def test_newPhysicalChainMakesNewSubstances(self):
        """
        Test that the protein type initialises
        """
        self.assertEqual(len(self.project.substances), 0)

        self.project.createChain('ACD', molType='protein')

        self.assertEqual(len(self.project.substances), 1)
        self.assertEqual(self.project.substances[0].pid, 'SU:mySubstance.')


class TestExistingSubstancesWithSameNameReused(WrapperTesting):

    def test_sampleComponentsUsesSubstanceWithSameName(self):
        substance = self.project.newSubstance('testSampleComponent')
        self.assertEqual(len(self.project.substances), 1)

        sample = self.project.newSample('testSample')
        sampleComponent = sample.newSampleComponent('testSampleComponent')

        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(substance, sampleComponent.substance)

    def test_chainTriesToUseSubstanceWithSameName(self):
        self.project.newSubstance('Molecule_1')
        self.assertRaises(Exception, self.project.createChain, compoundName='Molecule_1',
                          sequence='acd', molType='protein')

    def test_createChainFromExistingSubstance(self):
        physicalChain = self.project.createChain('ACD', molType='protein')
        newPhysicalChain = physicalChain.substances[0].createChain()
        self.assertEqual(physicalChain.substances, newPhysicalChain.substances)
        self.assertIsNot(physicalChain, newPhysicalChain)


#=========================================================================================
# SubstanceProperties        Test bare substances
#=========================================================================================

class SubstanceProperties(WrapperTesting):

    def test_bareSubstanceProperties(self):
        """
        Test that a bare Substance initiates correctly
        """
        s = self.project.newSubstance('testSubstance')

        self.assertEqual(s.pid, 'SU:testSubstance.')
        self.assertEqual(s.longPid, 'Substance:testSubstance.')
        self.assertEqual(s.shortClassName, 'SU')
        self.assertEqual(s.className, 'Substance')
        self.assertEqual(s.name, 'testSubstance')
        self.assertEqual(s.labelling, None)
        self.assertEqual(s.id, 'testSubstance.')
        self.assertEqual(s.substanceType, 'Molecule')
        self.assertIs(s.project, self.project)

        self.assertEqual(s.chains, ())
        self.assertEqual(s.synonyms, ())
        self.assertEqual(s.referenceSpectra, ())
        self.assertEqual(s.sampleComponents, ())

        self.assertEqual(s.atomCount, 0)
        self.assertEqual(s.bondCount, 0)
        self.assertIsNone(s.casNumber)
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')  # comments now use None2Str
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
        """
        Test that a Molecule type Substance initiates correctly
        """
        s = self.project.newSubstance('testSubstance', substanceType='Molecule')

        self.assertEqual(s.pid, 'SU:testSubstance.')
        self.assertEqual(s.longPid, 'Substance:testSubstance.')
        self.assertEqual(s.shortClassName, 'SU')
        self.assertEqual(s.className, 'Substance')
        self.assertEqual(s.name, 'testSubstance')
        self.assertEqual(s.labelling, None)
        self.assertEqual(s.id, 'testSubstance.')
        self.assertEqual(s.substanceType, 'Molecule')
        self.assertIs(s.project, self.project)

        self.assertEqual(s.chains, ())
        self.assertEqual(s.synonyms, ())
        self.assertEqual(s.referenceSpectra, ())
        self.assertEqual(s.sampleComponents, ())

        self.assertEqual(s.atomCount, 0)
        self.assertEqual(s.bondCount, 0)
        self.assertIsNone(s.casNumber)
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')  # comments now use None2Str
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

    # @unittest.skip
    def test_bareMaterialSubstanceProperties(self):
        """
        Test that a Material type Substance initiates correctly
        """
        s = self.project.newSubstance('testSubstance', substanceType='Material')

        # Moved below initialisation of 's'. Rasmus.
        self.assertIsNone(s.smiles)

        self.assertEqual(s.pid, 'SU:testSubstance.')
        self.assertEqual(s.longPid, 'Substance:testSubstance.')
        self.assertEqual(s.shortClassName, 'SU')
        self.assertEqual(s.className, 'Substance')
        self.assertEqual(s.name, 'testSubstance')
        self.assertEqual(s.labelling, None)
        self.assertEqual(s.id, 'testSubstance.')
        self.assertEqual(s.substanceType, 'Material')
        self.assertIs(s.project, self.project)

        self.assertEqual(s.chains, ())
        self.assertEqual(s.synonyms, ())
        self.assertEqual(s.referenceSpectra, ())
        self.assertEqual(s.sampleComponents, ())

        self.assertIsNone(s.atomCount)
        self.assertIsNone(s.bondCount)
        self.assertIsNone(s.casNumber)
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')  # comments now use None2Str
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

    # @unittest.skip
    def test_bareCellSubstanceProperties(self):
        """
        Test that a Cell type Substance initiates correctly
        with name, labelling, usercode, synonyms, details
        """
        s = self.project.newSubstance('testSubstance', substanceType='Cell')

        self.assertEqual(s.pid, 'SU:testSubstance.')
        self.assertEqual(s.longPid, 'Substance:testSubstance.')
        self.assertEqual(s.shortClassName, 'SU')
        self.assertEqual(s.className, 'Substance')
        self.assertEqual(s.name, 'testSubstance')
        self.assertEqual(s.labelling, None)
        self.assertEqual(s.id, 'testSubstance.')
        self.assertEqual(s.substanceType, 'Cell')
        self.assertIs(s.project, self.project)

        self.assertEqual(s.chains, ())
        self.assertEqual(s.synonyms, ())
        self.assertEqual(s.referenceSpectra, ())
        self.assertEqual(s.sampleComponents, ())

        self.assertIsNone(s.atomCount)
        self.assertIsNone(s.bondCount)
        self.assertIsNone(s.casNumber)
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')  # comments now use None2Str
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

    # @unittest.skip
    def test_bareCompositeSubstanceProperties(self):
        """
        Test that a Composite type Substance initiates correctly
        """
        s = self.project.newSubstance('testSubstance', substanceType='Composite')

        self.assertEqual(s.pid, 'SU:testSubstance.')
        self.assertEqual(s.longPid, 'Substance:testSubstance.')
        self.assertEqual(s.shortClassName, 'SU')
        self.assertEqual(s.className, 'Substance')
        self.assertEqual(s.name, 'testSubstance')
        self.assertEqual(s.labelling, None)
        self.assertEqual(s.id, 'testSubstance.')
        self.assertEqual(s.substanceType, 'Composite')
        self.assertIs(s.project, self.project)

        self.assertEqual(s.chains, ())
        self.assertEqual(s.synonyms, ())
        self.assertEqual(s.referenceSpectra, ())
        self.assertEqual(s.sampleComponents, ())

        self.assertIsNone(s.atomCount)
        self.assertIsNone(s.bondCount)
        self.assertIsNone(s.casNumber)
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')  # comments now use None2Str
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


#=========================================================================================
# Test_MoleculeSubstance        Molecule type testing
#=========================================================================================

class Test_MoleculeSubstance(WrapperTesting):
    """
    Test Substances of type Molecule
    """

    def test_MoleculeSubstanceWithSmilesProperties(self):
        """
        Test that the smiles property can be set.
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      smiles='CCCC')
        self.assertEqual(s.smiles, 'CCCC')
        s.smiles = 'DDDD'
        self.assertEqual(s.smiles, 'DDDD')

    def test_MoleculeSubstanceWithinChiProperties(self):
        """
        Test that the inChi property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      inChi='1/C2H6O/c1-2-3/h3H,2H2,1H3')
        self.assertEqual(s.inChi, '1/C2H6O/c1-2-3/h3H,2H2,1H3')
        s.inChi = '1/C2H6O/c1-2-3/h3H,2H2,1H4'
        self.assertEqual(s.inChi, '1/C2H6O/c1-2-3/h3H,2H2,1H4')

    def test_MoleculeSubstanceWithLabellingProperties(self):
        """
        Test that the labelling property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      labelling='anything')
        self.assertEqual(s.labelling, 'anything')

    def test_MoleculeSubstanceWithLabellingProperties_None(self):
        """
        Test that the labelling property of Substance can be set to None
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      labelling=None)
        self.assertEqual(s.labelling, None)

    def test_MoleculeSubstanceWithLabellingProperties_ES(self):
        """
        Test that Substance can be set with labelling as empty string
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      labelling='')
        self.assertEqual(s.labelling, None)

    def test_MoleculeSubstanceWithLabellingProperties_Badname(self):
        """
        Test that the Substance set with ^badname raises an error
        Substance is not initialised
        """
        with self.assertRaisesRegex(ValueError, 'not allowed in'):
            s = self.project.newSubstance('testSubstance',
                                          substanceType='Molecule',
                                          labelling='^Badname')
        self.assertEqual(len(self.project.substances), 0)

    def test_MoleculeSubstanceWithLabellingProperties_Int(self):
        """
        Test that the Substance set with non-string raises an error
        Substance is not initialised
        """
        with self.assertRaisesRegex(ValueError, 'must be a string'):
            s = self.project.newSubstance('testSubstance',
                                          substanceType='Molecule',
                                          labelling=12)
        self.assertEqual(len(self.project.substances), 0)

    def test_MoleculeSubstanceWithCasNumberProperties(self):
        """
        Test that the casNumber property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      casNumber='64-17-5')
        self.assertEqual(s.casNumber, '64-17-5')
        s.casNumber = '64-16-3'
        self.assertEqual(s.casNumber, '64-16-3')

    def test_MoleculeSubstanceWithUserCodeCasNumberProperties(self):
        """
        Test that the userCode property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      userCode='test code')
        self.assertEqual(s.userCode, 'test code')
        s.userCode = 'another test'
        self.assertEqual(s.userCode, 'another test')

    def test_MoleculeSubstanceWithEmpiricalFormulaProperties(self):
        """
        Test that the empiricalFormula property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      empiricalFormula='C6H12O6')
        self.assertEqual(s.empiricalFormula, 'C6H12O6')
        s.empiricalFormula = 'C6H10O4'
        self.assertEqual(s.empiricalFormula, 'C6H10O4')

    def test_MoleculeSubstanceWithMolecularMassProperties(self):
        """
        Test that the molecularMass property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      molecularMass=42.0)
        self.assertEqual(s.molecularMass, 42.0)
        s.molecularMass = 43.0
        self.assertEqual(s.molecularMass, 43.0)

    def test_MoleculeSubstanceWithCommentProperties(self):
        """
        Test that the comment property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      comment='random comment.')
        self.assertEqual(s.comment, 'random comment.')
        s.comment = 'changed comment'
        self.assertEqual(s.comment, 'changed comment')

    def test_MoleculeSubstanceWithSynonymsProperties(self):
        """
        Test that the synonyms property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      synonyms=['syn1', 'syn2'])
        self.assertEqual(s.synonyms, ('syn1', 'syn2'))
        s.synonyms = ['syn1', 'syn3']
        self.assertEqual(s.synonyms, ('syn1', 'syn3'))

    def test_MoleculeSubstanceWithAtomCountProperties(self):
        """
        Test that the atomCount property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      atomCount=12)
        self.assertEqual(s.atomCount, 12)
        s.atomCount = 15
        self.assertEqual(s.atomCount, 15)

    def test_MoleculeSubstanceWithBondCountProperties(self):
        """
        Test that the bondCount property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      bondCount=11)
        self.assertEqual(s.bondCount, 11)
        s.bondCount = 15
        self.assertEqual(s.bondCount, 15)

    def test_MoleculeSubstanceWithRingCountProperties(self):
        """
        Test that the ringCount property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      ringCount=3)
        self.assertEqual(s.ringCount, 3)
        s.ringCount = 5
        self.assertEqual(s.ringCount, 5)

    def test_MoleculeSubstanceWithHBondDonorCountProperties(self):
        """
        Test that the hBondDonorCount property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      hBondDonorCount=2)
        self.assertEqual(s.hBondDonorCount, 2)
        s.hBondDonorCount = 3
        self.assertEqual(s.hBondDonorCount, 3)

    def test_MoleculeSubstanceWithHBondAcceptorCountProperties(self):
        """
        Test that the hBondAcceptCount property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      hBondAcceptorCount=2)
        self.assertEqual(s.hBondAcceptorCount, 2)
        s.hBondAcceptorCount = 3
        self.assertEqual(s.hBondAcceptorCount, 3)

    def test_MoleculeSubstanceWithPolarSurfaceAreaProperties(self):
        """
        Test that the polarSurfaceArea property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      polarSurfaceArea=2)
        self.assertEqual(s.polarSurfaceArea, 2)
        s.polarSurfaceArea = 3
        self.assertEqual(s.polarSurfaceArea, 3)

    def test_MoleculeSubstanceWithLogPartitionCoefficientProperties(self):
        """
        Test that the logPartitionCoefficient property of Substance can be set
        """
        s = self.project.newSubstance('testSubstance',
                                      substanceType='Molecule',
                                      logPartitionCoefficient=2)
        self.assertEqual(s.logPartitionCoefficient, 2)
        s.logPartitionCoefficient = 3
        self.assertEqual(s.logPartitionCoefficient, 3)


#=========================================================================================
# Test_PolymerSubstance        Polymer type testing
#=========================================================================================

class Test_PolymerSubstance(WrapperTesting):
    """
    Test Substances of type Polymer
    """

    def test_bareUndefinedSubstanceProperties(self):
        """
        Test that an undefined Substance raises an error
        """
        with self.assertRaises(ValueError):
            s = self.project.newSubstance(name='testSubstance', substanceType='other')

    def test_PolymerSubstance_noSequence(self):
        """
        Test that the labelling property of Substance can be set.
        """
        # with self.assertRaisesRegex(ValueError, 'createPolymerSubstance requires non-empty sequence'):
        s = self.project.createPolymerSubstance(None,
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                labelling='H')
        self.assertEqual(len(self.project.substances), 1)

        # s = self.project.createPolymerSubstance('acd',
        #                                         name='testPolymerSubstance',
        #                                         molType='protein',
        #                                         labelling='H')
        # with self.assertRaisesRegex(ValueError, 'already exists'):
        #     s = self.project.createPolymerSubstance('acd',
        #                                             name='testPolymerSubstance',
        #                                             molType='protein',
        #                                             labelling='H')
        # with self.assertRaisesRegex(ValueError, 'already in use'):
        #     s = self.project.createPolymerSubstance('acd',
        #                                             name='testPolymerSubstance',
        #                                             molType='protein',
        #                                             labelling='K')
        # self.assertEqual(len(self.project.substances), 1)

    def test_PolymerSubstanceWithLabellingProperties(self):
        """
        Test that the labelling property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                labelling='H')
        self.assertEqual(s.labelling, 'H')
        s2 = self.project.fetchSubstance(name='testPolymerSubstance', labelling='H')
        self.assertIs(s, s2)
        s3 = self.project.fetchSubstance(name='testPolymerSubstance', labelling='K')
        self.assertIsNot(s, s3)

    def test_PolymerSubstanceWithLabellingProperties_None(self):
        """
        Test that the labelling property of Substance can be set as None.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                labelling=None)
        self.assertEqual(s.labelling, None)
        self.assertEqual(len(self.project.substances), 1)

        # with self.assertRaisesRegex(ValueError, 'already exists'):
        #     s = self.project.createPolymerSubstance('acd',
        #                                             name='testPolymerSubstance',
        #                                             molType='protein',
        #                                             labelling=None)
        # self.assertEqual(len(self.project.substances), 1)
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                labelling=None)
        self.assertEqual(len(self.project.substances), 2)
        self.assertEqual(s.id, 'testPolymerSubstance_1.')

    def test_PolymerSubstanceWithLabellingProperties_ES(self):
        """
        Test that the labelling property of Substance can be set as empty string.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                labelling='')
        self.assertEqual(s.labelling, None)
        self.assertEqual(len(self.project.substances), 1)

    def test_PolymerSubstanceWithLabellingProperties_Badname(self):
        """
        Test that the labelling property of Substance can be set.
        """
        # with self.assertRaisesRegex(ValueError, 'not allowed in '):
        with self.assertRaisesRegex(ValueError, 'not allowed in '):
            s = self.project.createPolymerSubstance('acd',
                                                    name='testPolymerSubstance',
                                                    molType='protein',
                                                    labelling='^Badname')
        self.assertEqual(len(self.project.substances), 0)

    def test_PolymerSubstanceWithLabellingProperties_WhitespaceName(self):
        """
        Test that the labelling property of Substance can be set.
        """
        # with self.assertRaisesRegex(ValueError, 'not allowed in '):
        with self.assertRaisesRegex(ValueError, 'not allowed in'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='testPolymerSubstance',
                                                    molType='protein',
                                                    labelling=' whitespaceName ')
        self.assertEqual(len(self.project.substances), 0)

    def test_PolymerSubstanceWithLabellingProperties_Int(self):
        """
        Test that the labelling property of Substance can be set.
        """
        with self.assertRaisesRegex(ValueError, 'must be a string'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='testPolymerSubstance',
                                                    molType='protein',
                                                    labelling=12)
        self.assertEqual(len(self.project.substances), 0)

    def test_PolymerSubstanceWithUserCodeProperties(self):
        """
        Test that the userCode property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                userCode='test code')
        self.assertEqual(s.userCode, 'test code')
        s.userCode = 'changed code'
        self.assertEqual(s.userCode, 'changed code')

    def test_PolymerSubstanceWithSmilesProperties(self):
        """
        Test that the smiles property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                smiles='CCCC')
        self.assertEqual(s.smiles, 'CCCC')
        s.smiles = 'DDDD'
        self.assertEqual(s.smiles, 'DDDD')

    def test_PolymerSubstanceWithSynonymsProperties(self):
        """
        Test that the synonyms property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                synonyms=['syn1', 'syn2'])
        self.assertEqual(s.synonyms, ('syn1', 'syn2'))
        s.synonyms = ['syn3', 'syn4']
        self.assertEqual(s.synonyms, ('syn3', 'syn4'))

    def test_PolymerSubstanceWithCommentsProperties(self):
        """
        Test that the comment property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='testPolymerSubstance',
                                                molType='protein',
                                                comment='test comment')
        self.assertEqual(s.comment, 'test comment')
        s.comment = 'changed comment'
        self.assertEqual(s.comment, 'changed comment')

    # property doesn't exists
    # def _test_PolymerSubstanceWithStartNumberProperties(self):
    #   """
    #   Test that the startNumber property of Substance can be set.
    #   """
    #   s = self.project.createPolymerSubstance('acd',
    #                                           name='testPolymerSubstance',
    #                                           molType='protein',
    #                                           startNumber=7)
    #   self.assertEqual(s.startNumber, 7)
    #   s.startNumber = 8
    #   self.assertEqual(s.startNumber, 8)

    def test_SubstanceExists(self):
        """
        Test creation of substances of different type with the same name/different label
        """
        s = self.project.newSubstance('testSubstanceMolecule', substanceType='Molecule')

        self.assertEqual(s.pid, 'SU:testSubstanceMolecule.')
        self.assertEqual(s.longPid, 'Substance:testSubstanceMolecule.')
        self.assertEqual(s.shortClassName, 'SU')

        with self.assertRaisesRegex(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('testSubstanceMolecule', substanceType='Material', labelling='different')

        with self.assertRaisesRegex(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('testSubstanceMolecule', substanceType='Cell', labelling='different')

        with self.assertRaisesRegex(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('testSubstanceMolecule', substanceType='Composite', labelling='different')

        s = self.project.newSubstance('testSubstanceMaterial', substanceType='Material')
        s = self.project.newSubstance('testSubstanceComposite', substanceType='Composite')
        s = self.project.newSubstance('testSubstanceCell', substanceType='Cell')

        self.assertEqual(s.pid, 'SU:testSubstanceCell.')
        self.assertEqual(s.longPid, 'Substance:testSubstanceCell.')
        self.assertEqual(s.shortClassName, 'SU')

        with self.assertRaisesRegex(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('testSubstanceCell', substanceType='Molecule', labelling='different')

    def test_Substance_atom(self):
        """
        Test that the spectrumHits are correct
        """
        pass
