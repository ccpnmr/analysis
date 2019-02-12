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
__dateModified__ = "$dateModified: 2017-07-07 16:32:33 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-03-30 15:03:06 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr
from ccpnmodel.ccpncore.memops.ApiError import ApiError


#=========================================================================================
# TestLabellingBasic_No_setUp
#=========================================================================================

class TestLabellingBasic_No_setUp(WrapperTesting):
    """
    Test functions that require a valid Sample and Chain to be instantiated.
    """

    #=========================================================================================
    # test_SampleComponentLabelling
    #=========================================================================================
    pass


#=========================================================================================
# TestLabellingBasic_setUp
#=========================================================================================

class TestLabellingBasic_setUp(WrapperTesting):
    """
    Test functions that require a valid Sample and Chain to be instantiated.
    """

    #=========================================================================================
    # setUp     Initialise a valid Sample with a valid Chain
    #=========================================================================================

    def setUp(self):
        """
        Create a valid Sample with the name 'ValidSample'.
        """
        with self.initialSetup():
            self.sample = self.project.newSample('ValidSample')
            # self.chain1 = self.project.createChain(sequence='QWERTYIPASDF', molType='protein',
            #                                        compoundName='typewriter')

    #=========================================================================================
    # checkNumComponents
    #=========================================================================================

    def checkNumComponents(self, num: int):
        """
        Test that sampleComponent and sjubstance are the required length.
        :param num:
        """
        self.assertEqual(len(self.project.sampleComponents), num)
        self.assertEqual(len(self.project.substances), num)

    #=========================================================================================
    # test_SampleComponent_good_name        Valid tests
    #=========================================================================================

    def test_SampleComponentLabelling(self):
        """
        Test that creating a new SampleComponent with name 'ValidSampleComponent' and
        Labelling as 'ValidLabelling' creates a valid sampleComponent.
        """
        self.newSC = self.sample.newSampleComponent('ValidSampleComponent', 'ValidLabelling')
        self.assertEqual(self.newSC.pid, 'SC:ValidSample.ValidSampleComponent.ValidLabelling')
        self.checkNumComponents(1)

    def test_SampleComponentLabelling_None(self):
        """
        Test that creating a new SampleComponent with name 'ValidSampleComponent' and
        Labelling as None creates a valid sampleComponent.
        """
        self.sample.newSampleComponent('ValidSampleComponent', None)
        self.checkNumComponents(1)

    #=========================================================================================
    # test_SampleComponent_bad_name   bad sampleComponent
    #=========================================================================================

    def test_SampleComponentLabelling_BadSC(self):
        """
        Test that creating a new SampleComponent with name '^Badname' and
        Labelling as a valid name raises an error and no component is added.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.sample.newSampleComponent('^Badname', 'ValidLabelling')
        self.checkNumComponents(0)

    def test_SampleComponentLabelling_Bad_ES(self):
        """
        Test that creating a new SampleComponent with name '^Badname' and
        Labelling as an empty string raises an error and no component is added.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.sample.newSampleComponent('^Badname', '')
        self.checkNumComponents(0)

    def test_SampleComponentLabelling_Bad_Badname(self):
        """
        Test that creating a new SampleComponent with name '^Badname' and
        Labelling as '^Badname' raises an error and no component is added.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.sample.newSampleComponent('^Badname', '^Badname')
        self.checkNumComponents(0)

    def test_SampleComponentLabelling_Bad_None(self):
        """
        Test that creating a new SampleComponent with name '^Badname' and
        Labelling as None raises an error and no component is added.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.sample.newSampleComponent('^Badname', None)
        self.checkNumComponents(0)

    def test_SampleComponentLabelling_Bad_Int(self):
        """
        Test that creating a new SampleComponent with name '^Badname' and
        Labelling as 42 (non-string) raises an error and no component is added.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.sample.newSampleComponent('^Badname', 42)
        self.checkNumComponents(0)

    #=========================================================================================
    # test_SampleComponent_bad_name   bad labelling
    #=========================================================================================

    def test_SampleComponentLabelling_ES(self):
        """
        Test that creating a new SampleComponent with Labelling as empty string raises an error
        and no component is added.
        """
        # with self.assertRaisesRegexp(ApiError, 'Empty string not allowed'):
        #   self.sample.newSampleComponent('ValidSampleComponent', '')
        #
        with self.assertRaisesRegexp(ValueError, "SampleComponent 'labelling' name must be set"):
            self.sample.newSampleComponent('ValidSampleComponent', '')
        self.checkNumComponents(0)

    def test_SampleComponentLabelling_Badname(self):
        """
        Test that creating a new SampleComponent with Labelling as '^Badname' raises an error
        and no component is added.
        ^ is a bad character and not to be included in strings.
        """
        # with self.assertRaisesRegexp(ValueError, 'Character'):
        #   self.sample.newSampleComponent('ValidSampleComponent', '^Badname')
        #
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.sample.newSampleComponent('ValidSampleComponent', '^Badname')
        self.checkNumComponents(0)

    def test_SampleComponentLabelling_Int(self):
        """
        Test that creating a new SampleComponent with Labelling as 42 (non-string) raises an error
        and no component is added.
        """
        # with self.assertRaisesRegexp(TypeError, 'not iterable'):
        #   self.sample.newSampleComponent('ValidSampleComponent', 42)
        #
        with self.assertRaisesRegexp(TypeError, "SampleComponent 'labelling' name must be a string"):
            self.sample.newSampleComponent('ValidSampleComponent', 42)
        self.checkNumComponents(0)
