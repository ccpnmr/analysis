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

from unittest import expectedFailure
from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class TestSampleComponentCreation(WrapperTesting):
    """
    Test functions that require a valid Sample to be instantiated.
    """

    #=========================================================================================
    # setUp     Initialise a valid Sample
    #=========================================================================================

    def setUp(self):
        """
        Create a valid Sample with the name 'ValidSample'
        This is required to attach the sampleComponents.
        """
        with self.initialSetup():
            self.sample = self.project.newSample('ValidSample')

    #=========================================================================================
    # test_newSampleComponent_bad_name
    #=========================================================================================

    def test_newSampleComponent_Badname(self):
        """
        Test that creating a new SampleComponent '^Badname' raises an error and
        no component is added.
        ^ is a bad character and not to be included in strings.
        """
        with self.assertRaisesRegex(ValueError, 'Character'):
            self.sample.newSampleComponent('^Badname')
        self.assertEqual(len(self.project.sampleComponents), 0)
        self.assertEqual(len(self.project.substances), 0)

    def test_newSampleComponent_Int(self):
        """
        Test that creating a new SampleComponent with 42 (non-string) raises an error and
        no component is added.
        """
        # with self.assertRaisesRegex(TypeError, 'not iterable'):
        #   self.sample.newSampleComponent(42)
        #
        with self.assertRaisesRegex(ValueError, 'must be a string'):
            self.sample.newSampleComponent(42)
        self.assertEqual(len(self.project.sampleComponents), 0)
        self.assertEqual(len(self.project.substances), 0)

    #=========================================================================================
    # test_newSampleComponent_good_name
    #=========================================================================================

    def test_newSampleComponent_good_name(self):
        """
        Test that the new sampleComponent has been created and added to the component list, and the
        first element in the list is the correct sampleComponent.
        """
        self.assertEqual(len(self.project.sampleComponents), 0)
        self.assertEqual(len(self.project.substances), 0)

        with self.assertRaisesRegex(ValueError, 'not allowed in'):
            newSC = self.sample.newSampleComponent('Valid SampleComponent')

        newSC = self.sample.newSampleComponent('ValidSampleComponent')
        self.assertEqual(newSC.pid, 'SC:ValidSample.ValidSampleComponent.')
        self.assertEqual(len(self.project.sampleComponents), 1)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.sampleComponents[0], newSC)

    def test_newSampleComponent(self):
        """
        Test that creating a new SampleComponent with no parameter gives the standard new name.
        Check that second creation is given a unique name.
        """
        newSC = self.sample.newSampleComponent()
        self.assertEqual(newSC.pid, 'SC:ValidSample.mySampleComponent.')
        self.assertEqual(len(self.project.sampleComponents), 1)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.sampleComponents[0], newSC)
        newSC2 = self.sample.newSampleComponent()
        self.assertEqual(newSC2.pid, 'SC:ValidSample.mySampleComponent_1.')
        self.assertEqual(len(self.project.sampleComponents), 2)
        self.assertEqual(len(self.project.substances), 2)
        self.assertIs(self.project.sampleComponents[1], newSC2)
        newSC3 = self.sample.newSampleComponent(name='test', labelling='label')
        self.assertEqual(newSC3.pid, 'SC:ValidSample.test.label')
        self.assertEqual(len(self.project.sampleComponents), 3)
        self.assertEqual(len(self.project.substances), 3)
        self.assertIs(self.project.sampleComponents[2], newSC3)
        newSC4 = self.sample.newSampleComponent(name='test', labelling='label')
        self.assertEqual(newSC4.pid, 'SC:ValidSample.test_1.label')
        self.assertEqual(len(self.project.sampleComponents), 4)
        self.assertEqual(len(self.project.substances), 4)
        self.assertIs(self.project.sampleComponents[3], newSC4)

    def test_newSampleComponent_ES(self):
        """
        Test that creating a new SampleComponent with an empty string gives the standard new name.
        """
        with self.assertRaisesRegex(ValueError, 'must be set'):
            newSC = self.sample.newSampleComponent('')
        newSC = self.sample.newSampleComponent()
        self.assertEqual(newSC.pid, 'SC:ValidSample.mySampleComponent.')
        self.assertEqual(len(self.project.sampleComponents), 1)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.sampleComponents[0], newSC)

    def test_newSampleComponent_None(self):
        """
        Test that creating a new SampleComponent with None gives the standard new name.
        """
        newSC = self.sample.newSampleComponent(None)
        self.assertEqual(newSC.pid, 'SC:ValidSample.mySampleComponent.')
        self.assertEqual(len(self.project.sampleComponents), 1)
        self.assertEqual(len(self.project.substances), 1)
        self.assertIs(self.project.sampleComponents[0], newSC)


#========================================================================================
# TestSampleComponentLinks
#=========================================================================================

class TestSampleComponentLinks(WrapperTesting):

    #========================================================================================
    # setUp         Initialise a new Sample for testing cross links
    #=========================================================================================

    def setUp(self):
        """
        Create a valid Sample with the name 'ValidSample'
        This is required to attach the sampleComponents.
        """
        with self.initialSetup():
            self.sample = self.project.newSample('ValidSample')

    #=========================================================================================
    # test_crosslinks
    #=========================================================================================

    def test_crosslinks(self):
        """
        Test that the cross-links are created correctly.
        """
        chain1 = self.project.createChain(sequence='QWERTYIPASDF', molType='protein',
                                          compoundName='typewriter')
        dna = self.project.createPolymerSubstance(sequence='ATTACGCAT', name='attackcat',
                                                  molType='DNA', )


#=========================================================================================
# TestSampleComponent_properties
#=========================================================================================

class TestSampleComponent_properties(WrapperTesting):
    """
    Test functions that require a valid Sample and attached SampleComponent to be instantiated.
    """

    #========================================================================================
    # setUp         Initialise a new Sample and SampleComponent
    #=========================================================================================

    def setUp(self):
        """
        Create a valid Sample with the name 'ValidSample' and a
        SampleComponent with the name 'ValidSampleComponent'.
        """
        with self.initialSetup():
            self.sample = self.project.newSample('ValidSample')
            self.newSampleComponent = self.sample.newSampleComponent(name='ValidSampleComponent')

    #=========================================================================================
    # test_properties_SampleComponent
    #=========================================================================================

    def test_properties_SampleComponent_labelling(self):
        """
        Test that SampleComponent attribute .labelling is populated.
        Read the attribute, if it not populated then an error is raised.
        """
        labelling = self.newSampleComponent.labelling

    def test_properties_SampleComponent_role(self):
        """
        Test that SampleComponent attribute .role is populated.
        Read the attribute, if it not populated then an error is raised.
        If no error, then test the setter by setting and then getting to check consistent.
        Similarly for all set/get properties.
        """
        checkGetSetAttr(self, self.newSampleComponent, 'role', 'solvent')

    def test_properties_SampleComponent_concentration(self):
        """
        Test that SampleComponent attribute .concentration is populated.
        """
        checkGetSetAttr(self, self.newSampleComponent, 'concentration', 0.5)

    def test_properties_SampleComponent_concentrationError(self):
        """
        Test that SampleComponent attribute .concentrationError is populated.
        """
        checkGetSetAttr(self, self.newSampleComponent, 'concentrationError', 0.5)

    def test_properties_SampleComponent_concentrationUnit(self):
        """
        Test that SampleComponent attribute .concentrationUnit is populated.
        """
        checkGetSetAttr(self, self.newSampleComponent, 'concentrationUnit', 'mole')

    def test_properties_SampleComponent_purity(self):
        """
        Test that SampleComponent attribute .purity is populated.
        """
        checkGetSetAttr(self, self.newSampleComponent, 'purity', 0.5)

    def test_properties_SampleComponent_comment(self):
        """
        Test that SampleComponent attribute .comment is populated.
        """
        checkGetSetAttr(self, self.newSampleComponent, 'comment', 'Comment')

    def test_properties_SampleComponent_spectrumHits(self):
        """
        Test that SampleComponent attribute .spectrumHits is populated.
        """
        spectrumHits = self.newSampleComponent.spectrumHits

    #=========================================================================================
    # test_properties_SampleComponent   expectedFailure
    #=========================================================================================

    # @expectedFailure
    def test_properties_SampleComponent_isotopeCode2Fraction(self):
        """
        Test that SampleComponent attribute .isotopeCode2Fraction is populated.
        """
        isotopeCode2Fraction = self.newSampleComponent.isotopeCode2Fraction
