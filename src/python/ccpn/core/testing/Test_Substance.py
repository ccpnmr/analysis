"""Module Documentation here

"""
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
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr


#=========================================================================================
# SubstanceTest
#=========================================================================================

class SubstanceTest(WrapperTesting):
    """
    Test the links between Substance and SampleComponent
    """

    # Path of project to load (None for new project)
    projectPath = None

    def test_simple_create(self):
        """
        Test creation and undo functions
        """
        substance1 = self.project.newSubstance('MolComp1', userCode='userCode', smiles=':-)')
        self.assertEqual(substance1.id, 'MolComp1.')
        self.assertEqual(substance1.smiles, ':-)')
        self.assertEqual(substance1.substanceType, 'Molecule')

        substance2 = self.project.newSubstance('Cell1', substanceType='Cell', labelling='moxy',
                                               smiles=':-)')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(substance2.id, 'Cell1.moxy')
        self.assertEqual(substance2.smiles, None)
        self.assertEqual(substance2.substanceType, 'Cell')

    def test_substance_rename_1(self):
        """
        Test renaming of Substance and links
        """
        chain1 = self.project.createChain(sequence='ACDC', compoundName='hardrock', shortName='X',
                                          molType='protein')
        substance1 = chain1.substances[0]
        chain2 = substance1.createChain(shortName='Y')
        self.assertEqual(len(substance1.chains), 2)
        self.assertEqual(substance1._id, 'hardrock.')
        self.assertEqual(chain2.compoundName, 'hardrock')
        self.assertEqual(substance1.chains, (chain1, chain2))

        sample1 = self.project.newSample(name='S1')
        sc1 = sample1.newSampleComponent(name='hardrock')
        sample1 = self.project.newSample(name='S2')
        sc2 = sample1.newSampleComponent(name='hardrock', labelling='adhesive')
        self.assertEqual(sc1._id, 'S1.hardrock.')
        self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
        self.assertEqual(substance1.sampleComponents, (sc1,))
        self.project.newUndoPoint()
        substance1.rename(name='electrical', labelling='cafe')
        self.assertEqual(substance1._id, 'electrical.cafe')
        self.assertEqual(sc1._id, 'S1.electrical.cafe')
        self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
        self.assertEqual(substance1.sampleComponents, (sc1,))
        self.project._undo.undo()
        self.assertEqual(substance1._id, 'hardrock.')
        self.assertEqual(sc1._id, 'S1.hardrock.')
        self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
        self.assertEqual(substance1.sampleComponents, (sc1,))
        self.project._undo.redo()
        self.assertEqual(substance1._id, 'electrical.cafe')
        self.assertEqual(sc1._id, 'S1.electrical.cafe')
        self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
        self.assertEqual(substance1.sampleComponents, (sc1,))
        substance1.rename(name='notmuch', labelling=None)
        self.assertEqual(substance1._id, 'notmuch.')
        self.assertEqual(sc1._id, 'S1.notmuch.')

        # with self.assertRaisesRegexp(TypeError, 'ccpn.Substance.name must be a string'):
        #   substance1.rename(name=None, labelling=None)

        substance1.rename(name=None, labelling='noName')
        self.assertEqual(substance1._id, 'notmuch.noName')
        self.assertEqual(sc1._id, 'S1.notmuch.noName')
        self.project._undo.undo()

        self.assertEqual(substance1._id, 'notmuch.')
        self.assertEqual(sc1._id, 'S1.notmuch.')
        self.project._undo.undo()
        self.assertEqual(substance1._id, 'electrical.cafe')
        self.assertEqual(sc1._id, 'S1.electrical.cafe')
        self.project._undo.undo()
        self.assertEqual(substance1._id, 'hardrock.')
        self.assertEqual(sc1._id, 'S1.hardrock.')
        self.project._undo.redo()
        self.project._undo.redo()
        self.assertEqual(substance1._id, 'notmuch.')
        self.assertEqual(sc1._id, 'S1.notmuch.')

        with self.assertRaisesRegexp(ValueError, 'Substance name must be set'):
            substance1.rename(name='', labelling=None)
        self.assertEqual(sc1._id, 'S1.notmuch.')

        with self.assertRaisesRegexp(ValueError, 'not allowed in Substance'):
            substance1.rename(name='^Badname', labelling=None)
        self.assertEqual(sc1._id, 'S1.notmuch.')

        with self.assertRaisesRegexp(TypeError, 'Substance name must be a string'):
            substance1.rename(name=12, labelling=None)
        self.assertEqual(sc1._id, 'S1.notmuch.')

        #TODO:ED have changed substance to allow None in the Labelling
        # with self.assertRaisesRegexp(ValueError, 'ccpn.Substance.labelling must be set'):
        substance1.rename(name='notmuch', labelling='')
        self.assertEqual(sc1._id, 'S1.notmuch.')

        with self.assertRaisesRegexp(ValueError, 'not allowed in Labelling name'):
            substance1.rename(name='notmuch', labelling='^Badname')
        self.assertEqual(sc1._id, 'S1.notmuch.')

        with self.assertRaisesRegexp(TypeError, 'Labelling name must be a string'):
            substance1.rename(name='notmuch', labelling=12)
        self.assertEqual(sc1._id, 'S1.notmuch.')


#=========================================================================================
# Test_Substance_SpectrumLink
#=========================================================================================

class Test_Substance_SpectrumLink(WrapperTesting):
    """
    Test Cross-Link to Spectrum
    """
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            self.spectrum1 = self.project.createDummySpectrum(axisCodes=['CO', 'Hn', 'Nh'])
            self.assertEqual(self.spectrum1.isotopeCodes, ('13C', '1H', '15N'))
            self.assertEqual(self.spectrum1.name, 'COHnNh')

            self.chain1 = self.project.createChain(sequence='ACDC', compoundName='sequence1', shortName='cC1',
                                                   molType='protein')

            self.spectrum2 = self.project.createDummySpectrum(axisCodes=['Hp', 'F', 'Ph', 'H'])
            self.assertEqual(self.spectrum2.isotopeCodes, ('1H', '19F', '31P', '1H'))
            self.assertEqual(self.spectrum2.name, 'HpFPhH')

            self.chain2 = self.project.createChain(sequence='ACDC', compoundName='sequence2', shortName='cC2',
                                                   molType='protein')

            self.substance1 = self.chain1.substances[0]
            self.substance2 = self.chain2.substances[0]

    def test_Substance_SpectrumLink(self):
        checkGetSetAttr(self, obj=self.spectrum1, attrib='referenceSubstance', value=self.substance1)

        ref1 = self.substance1.referenceSpectra
        self.assertEqual(ref1[0], self.spectrum1)

        self.substance1.referenceSpectra = ref1
        self.substance2.referenceSpectra = ref1

        self.substance1.clearSpecificAtomLabelling()

    def test_Substance_GetAtomLabelling(self):
        with self.assertRaisesRegexp(ValueError, 'Atom with ID None does not exist'):
            atomLabel = self.substance1.getSpecificAtomLabelling('X.1.ALA.CA')
        atomLabel = self.substance1.getSpecificAtomLabelling('cC1.1.ALA.CA')

        with self.assertRaisesRegexp(ValueError, 'chain do not match the Substance'):
            atomLabel = self.substance2.getSpecificAtomLabelling('cC1.1.ALA.CA')

    def _test_Substance_removeAtomLabelling(self):
        # TODO the error raised seems to be different to the test. Fix?
        with self.assertRaisesRegexp(ValueError, 'does not exist'):
            atomLabel = self.substance1.removeSpecificAtomLabelling('X.1.ALA.CA')

        with self.assertRaisesRegexp(ValueError, 'chain do not match the Substance'):
            atomLabel = self.substance2.removeSpecificAtomLabelling('cC1.1.ALA.CA')

        atomLabel = self.substance1.removeSpecificAtomLabelling('cC1.1.ALA.CA')
        self.assertEqual(atomLabel, None)

    def test_Substance_SetAtomLabelling(self):
        with self.assertRaisesRegexp(ValueError, 'Atom with ID None does not exist'):
            atomLabel = self.substance1.setSpecificAtomLabelling('X.1.ALA.CA', {'12C': 0.32, '13C': 0.68})

        with self.assertRaisesRegexp(ValueError, 'chain do not match the Substance'):
            atomLabel = self.substance2.setSpecificAtomLabelling('cC1.1.ALA.CA', {'12C': 0.32, '13C': 0.68})

        atomLabel = self.substance1.setSpecificAtomLabelling('cC1.1.ALA.CA', {'12C': 0.32, '13C': 0.68})
        pass

    def test_Substance_SpecificAtomLabelling(self):
        atomLabel = self.substance1.specificAtomLabelling

    def test_Substance_updateSpecificAtomLabelling(self):
        atomLabel = self.substance1.specificAtomLabelling


#=========================================================================================
# Test_Substance_SpectrumLink
#=========================================================================================

class Test_Substance_LoadSubstanceRename(WrapperTesting):
    """
    Test renaming loaded file with spectrumHits
    """
    projectPath = None

    def _test_Substance_LoadRename(self):
        """
        Test renaming of Substance and links
        """
        self.loadData('../../../data/testProjects/AnalysisScreen_Demo1/Lookup_Demo.xls')
        self.assertGreater(len(self.project.substances), 0)
