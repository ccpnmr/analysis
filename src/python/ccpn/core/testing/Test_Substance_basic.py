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
__dateModified__ = "$dateModified: 2017-07-07 16:32:35 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
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

        with self.assertRaisesRegexp(ValueError, 'already exists'):
            s2 = self.project.newSubstance('test substance')

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
        s1 = self.project.newSubstance('test substance')
        s2 = self.project.fetchSubstance('test substance')
        self.assertIs(s1, s2)

    def test_fetchSubstanceNewSubstance(self):
        """
        Test that the correct (different) Substance is fetched
        """
        s1 = self.project.newSubstance('test substance')
        s2 = self.project.fetchSubstance('another test substance')

        self.assertEqual(s2.pid, 'SU:another test substance.')
        self.assertIsNot(s1, s2)

    def test_sampleComponentsMakesNewSubstances(self):
        """
        Test that the new Substance initialises correctly
        """
        self.assertEqual(len(self.project.substances), 0)

        sample = self.project.newSample('test sample')
        sample.newSampleComponent('test sample component')

        self.assertEqual(len(self.project.substances), 1)
        self.assertEqual(self.project.substances[0].pid, 'SU:test sample component.')

    def test_newPhysicalChainMakesNewSubstances(self):
        """
        Test that the protein type initialises
        """
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

    def test_chainTriesToUseSubstanceWithSameName(self):
        self.project.newSubstance('Molecule_1')
        self.assertRaises(Exception, self.project.createChain, compoundName='Molecule_1',
                          sequence='acd', molType='protein')

    def test_createChainFromExistingSubstance(self):
        physicalChain = self.project.createChain('acd', molType='protein')
        newPhysicalChain = physicalChain.substances[0].createChain()
        self.assertEquals(physicalChain.substances, newPhysicalChain.substances)
        self.assertIsNot(physicalChain, newPhysicalChain)


#=========================================================================================
# SubstanceProperties        Test bare substances
#=========================================================================================

class SubstanceProperties(WrapperTesting):

    def test_bareSubstanceProperties(self):
        """
        Test that a bare Substance initiates correctly
        """
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
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')                    # comments now use None2Str
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
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')                    # comments now use None2Str
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
        s = self.project.newSubstance('test substance', substanceType='Material')

        # Moved below initialisation of 's'. Rasmus.
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
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')                    # comments now use None2Str
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
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')                    # comments now use None2Str
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
        # self.assertIsNone(s.comment)
        self.assertEqual(s.comment, '')                    # comments now use None2Str
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
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      smiles='CCCC')
        self.assertEqual(s.smiles, 'CCCC')
        s.smiles = 'DDDD'
        self.assertEqual(s.smiles, 'DDDD')

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

    def test_MoleculeSubstanceWithLabellingProperties(self):
        """
        Test that the labelling property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      labelling='anything')
        self.assertEqual(s.labelling, 'anything')

    def test_MoleculeSubstanceWithLabellingProperties_None(self):
        """
        Test that the labelling property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      labelling=None)
        self.assertEqual(s.labelling, None)

    def test_MoleculeSubstanceWithLabellingProperties_ES(self):
        """
        Test that Substance can be set with labelling
        """
        with self.assertRaisesRegexp(ValueError, 'name must be set'):
            s = self.project.newSubstance('test substance',
                                          substanceType='Molecule',
                                          labelling='')
        self.assertEqual(len(self.project.substances), 0)

    def test_MoleculeSubstanceWithLabellingProperties_Badname(self):
        """
        Test that the Substance set with ^badname raises an error
        Substance is not initialised
        """
        with self.assertRaisesRegexp(ValueError, 'not allowed in ccpn.Substance'):
            s = self.project.newSubstance('test substance',
                                          substanceType='Molecule',
                                          labelling='^Badname')
        self.assertEqual(len(self.project.substances), 0)

    def test_MoleculeSubstanceWithLabellingProperties_Int(self):
        """
        Test that the Substance set with non-string raises an error
        Substance is not initialised
        """
        with self.assertRaisesRegexp(TypeError, 'name must be a string'):
            s = self.project.newSubstance('test substance',
                                          substanceType='Molecule',
                                          labelling=12)
        self.assertEqual(len(self.project.substances), 0)

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

    def test_MoleculeSubstanceWithUserCodeCasNumberProperties(self):
        """
        Test that the userCode property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      userCode='test code')
        self.assertEqual(s.userCode, 'test code')
        s.userCode = 'another test'
        self.assertEqual(s.userCode, 'another test')

    def test_MoleculeSubstanceWithEmpiricalFormulaProperties(self):
        """
        Test that the empiricalFormula property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      empiricalFormula='C6H12O6')
        self.assertEqual(s.empiricalFormula, 'C6H12O6')
        s.empiricalFormula = 'C6H10O4'
        self.assertEqual(s.empiricalFormula, 'C6H10O4')

    def test_MoleculeSubstanceWithMolecularMassProperties(self):
        """
        Test that the molecularMass property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      molecularMass=42.0)
        self.assertEqual(s.molecularMass, 42.0)
        s.molecularMass = 43.0
        self.assertEqual(s.molecularMass, 43.0)

    def test_MoleculeSubstanceWithCommentProperties(self):
        """
        Test that the comment property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      comment='random comment.')
        self.assertEqual(s.comment, 'random comment.')
        s.comment = 'changed comment'
        self.assertEqual(s.comment, 'changed comment')

    def test_MoleculeSubstanceWithSynonymsProperties(self):
        """
        Test that the synonyms property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      synonyms=['syn1', 'syn2'])
        self.assertEqual(s.synonyms, ('syn1', 'syn2'))
        s.synonyms = ['syn1', 'syn3']
        self.assertEqual(s.synonyms, ('syn1', 'syn3'))

    def test_MoleculeSubstanceWithAtomCountProperties(self):
        """
        Test that the atomCount property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      atomCount=12)
        self.assertEqual(s.atomCount, 12)
        s.atomCount = 15
        self.assertEqual(s.atomCount, 15)

    def test_MoleculeSubstanceWithBondCountProperties(self):
        """
        Test that the bondCount property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      bondCount=11)
        self.assertEqual(s.bondCount, 11)
        s.bondCount = 15
        self.assertEqual(s.bondCount, 15)

    def test_MoleculeSubstanceWithRingCountProperties(self):
        """
        Test that the ringCount property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      ringCount=3)
        self.assertEqual(s.ringCount, 3)
        s.ringCount = 5
        self.assertEqual(s.ringCount, 5)

    def test_MoleculeSubstanceWithHBondDonorCountProperties(self):
        """
        Test that the hBondDonorCount property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      hBondDonorCount=2)
        self.assertEqual(s.hBondDonorCount, 2)
        s.hBondDonorCount = 3
        self.assertEqual(s.hBondDonorCount, 3)

    def test_MoleculeSubstanceWithHBondAcceptorCountProperties(self):
        """
        Test that the hBondAcceptCount property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      hBondAcceptorCount=2)
        self.assertEqual(s.hBondAcceptorCount, 2)
        s.hBondAcceptorCount = 3
        self.assertEqual(s.hBondAcceptorCount, 3)

    def test_MoleculeSubstanceWithPolarSurfaceAreaProperties(self):
        """
        Test that the polarSurfaceArea property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
                                      substanceType='Molecule',
                                      polarSurfaceArea=2)
        self.assertEqual(s.polarSurfaceArea, 2)
        s.polarSurfaceArea = 3
        self.assertEqual(s.polarSurfaceArea, 3)

    def test_MoleculeSubstanceWithLogPartitionCoefficientProperties(self):
        """
        Test that the logPartitionCoefficient property of Substance can be set
        """
        s = self.project.newSubstance('test substance',
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
            s = self.project.newSubstance(name='test substance', substanceType='other')

    def test_PolymerSubstance_noSequence(self):
        """
        Test that the labelling property of Substance can be set.
        """
        with self.assertRaisesRegexp(ValueError, 'createPolymerSubstance requires non-empty sequence'):
            s = self.project.createPolymerSubstance(None,
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling='H')
        self.assertEqual(len(self.project.substances), 0)

        s = self.project.createPolymerSubstance('acd',
                                                name='test polymer substance',
                                                molType='protein',
                                                labelling='H')
        with self.assertRaisesRegexp(ValueError, 'already exists'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling='H')
        with self.assertRaisesRegexp(ValueError, 'already in use'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling='K')
        self.assertEqual(len(self.project.substances), 1)

    def test_PolymerSubstanceWithLabellingProperties(self):
        """
        Test that the labelling property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='test polymer substance',
                                                molType='protein',
                                                labelling='H')
        self.assertEqual(s.labelling, 'H')
        s2 = self.project.fetchSubstance(name='test polymer substance', labelling='H')
        self.assertIs(s, s2)
        s3 = self.project.fetchSubstance(name='test polymer substance', labelling='K')
        self.assertIsNot(s, s3)

    def test_PolymerSubstanceWithLabellingProperties_None(self):
        """
        Test that the labelling property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='test polymer substance',
                                                molType='protein',
                                                labelling=None)
        self.assertEqual(s.labelling, None)
        self.assertEqual(len(self.project.substances), 1)

        with self.assertRaisesRegexp(ValueError, 'already exists'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling=None)
        self.assertEqual(len(self.project.substances), 1)

    def test_PolymerSubstanceWithLabellingProperties_ES(self):
        """
        Test that the labelling property of Substance can be set.
        """
        with self.assertRaisesRegexp(ValueError, 'name must be set'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling='')
        self.assertEqual(len(self.project.substances), 0)

    def test_PolymerSubstanceWithLabellingProperties_Badname(self):
        """
        Test that the labelling property of Substance can be set.
        """
        # with self.assertRaisesRegexp(ValueError, 'not allowed in ccpn.Substance'):
        with self.assertRaisesRegexp(ValueError, 'not allowed in ccpn.Substance'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling='^Badname')
        self.assertEqual(len(self.project.substances), 0)

    def test_PolymerSubstanceWithLabellingProperties_Int(self):
        """
        Test that the labelling property of Substance can be set.
        """
        with self.assertRaisesRegexp(TypeError, 'name must be a string'):
            s = self.project.createPolymerSubstance('acd',
                                                    name='test polymer substance',
                                                    molType='protein',
                                                    labelling=12)
        self.assertEqual(len(self.project.substances), 0)

    def test_PolymerSubstanceWithUserCodeProperties(self):
        """
        Test that the userCode property of Substance can be set.
        """
        s = self.project.createPolymerSubstance('acd',
                                                name='test polymer substance',
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
                                                name='test polymer substance',
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
                                                name='test polymer substance',
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
                                                name='test polymer substance',
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
    #                                           name='test polymer substance',
    #                                           molType='protein',
    #                                           startNumber=7)
    #   self.assertEqual(s.startNumber, 7)
    #   s.startNumber = 8
    #   self.assertEqual(s.startNumber, 8)

    def test_SubstanceExists(self):
        """
        Test creation of substances of different type with the same name/different label
        """
        s = self.project.newSubstance('test substance Molecule', substanceType='Molecule')

        self.assertEqual(s.pid, 'SU:test substance Molecule.')
        self.assertEqual(s.longPid, 'Substance:test substance Molecule.')
        self.assertEqual(s.shortClassName, 'SU')

        with self.assertRaisesRegexp(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('test substance Molecule', substanceType='Material', labelling='different')

        with self.assertRaisesRegexp(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('test substance Molecule', substanceType='Cell', labelling='different')

        with self.assertRaisesRegexp(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('test substance Molecule', substanceType='Composite', labelling='different')

        s = self.project.newSubstance('test substance Material', substanceType='Material')
        s = self.project.newSubstance('test substance Composite', substanceType='Composite')
        s = self.project.newSubstance('test substance Cell', substanceType='Cell')

        self.assertEqual(s.pid, 'SU:test substance Cell.')
        self.assertEqual(s.longPid, 'Substance:test substance Cell.')
        self.assertEqual(s.shortClassName, 'SU')

        with self.assertRaisesRegexp(ValueError, 'clashes with substance of different type'):
            s = self.project.newSubstance('test substance Cell', substanceType='Molecule', labelling='different')

    def test_Substance_atom(self):
        """
        Test that the spectrumHits are correct
        """
        pass
