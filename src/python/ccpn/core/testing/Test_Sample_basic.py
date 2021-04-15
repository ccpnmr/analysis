#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-04 12:07:31 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import datetime
from unittest import expectedFailure
from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr
from ccpnmodel.ccpncore.memops.ApiError import ApiError


#=========================================================================================
# TestSample_No_setUp
#=========================================================================================

class TestSample_No_setUp(WrapperTesting):
    """
    Test functions that do not require a valid Sample to be instantiated.
    """

    #=========================================================================================
    # test_newSample        valid names
    #=========================================================================================

    def test_newSample_NS(self):
        """
        Test that creating a new Sample with no parameter creates a valid Sample.
        """
        newSample = self.project.newSample()
        self.assertEqual(newSample.name, 'mySample_1')
        self.assertEqual(len(self.project.samples), 1)

    def test_newSample_None(self):
        """
        Test that creating a new Sample with None creates a valid Sample.
        """
        newSample = self.project.newSample(None)
        self.assertEqual(newSample.name, 'mySample_1')
        self.assertEqual(len(self.project.samples), 1)

    #=========================================================================================
    # test_newSample_bad_name       invalid names
    #=========================================================================================

    def test_newSample_ES(self):
        """
        Test that creating a new Sample with '' raises an error.
        """
        # with self.assertRaisesRegexp(ApiError, 'Empty string not allowed'):
        #   self.project.newSample('')
        #
        self.project.newSample('')
        self.assertEqual(len(self.project.samples), 1)

    def test_newSample_Badname(self):
        """
        Test that creating a new Sample with '^Badname' raises an error.
        ^ is a bad character and not to be included in strings.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.project.newSample('^Badname')
        self.assertEqual(len(self.project.samples), 0)

    def test_newSample_Int(self):
        """
        Test that creating a new Sample with 42 (non-string) raises an error.
        """
        # with self.assertRaisesRegexp(TypeError, 'argument of type'):
        #   self.project.newSample(42)
        #
        with self.assertRaisesRegexp(TypeError, 'Sample.name must be a string'):
            self.project.newSample(42)
        self.assertEqual(len(self.project.samples), 0)


#=========================================================================================
# TestSample_setUp
#=========================================================================================

class TestSample_setUp(WrapperTesting):
    """
    Test functions that require a valid Sample to be instantiated.
    """

    #=========================================================================================
    # setUp       initialise a new Sample
    #=========================================================================================

    def setUp(self):
        """
        Create a valid Sample with the name 'ValidSample'
        """
        with self.initialSetup():
            self.newSample = self.project.newSample(name='ValidSample')

    #=========================================================================================
    # test_rename_Sample
    #=========================================================================================

    def test_rename_Sample_ES(self):
        """
        Test that renaming to '' raises an error and does not alter the original Sample.
        """
        with self.assertRaisesRegexp(ValueError, 'must be set'):
            self.newSample.rename('')
        self.assertEqual(self.newSample.name, 'ValidSample')

    def test_rename_Sample_Badname(self):
        """
        Test that renaming to '^Badname' raises an error and does not alter the original Sample.
        ^ is a bad character and not to be included in strings.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.newSample.rename('^Badname')
        self.assertEqual(self.newSample.name, 'ValidSample')

    def test_rename_Sample_None(self):
        """
        Test that renaming to None raises an error and does not alter the original Sample.
        """
        # with self.assertRaisesRegexp(ValueError, 'Sample name must be set'):
        #   self.newSample.rename(None)
        #
        with self.assertRaisesRegexp(ValueError, 'None not allowed in'):
            self.newSample.rename(None)
        self.assertEqual(self.newSample.name, 'ValidSample')

    def test_rename_Sample_Int(self):
        """
        Test that renaming to 42 (non-string) raises an error and does not alter the original Sample.
        """
        # with self.assertRaisesRegexp(TypeError, 'argument of type'):
        #   self.newSample.rename(42)
        #
        with self.assertRaisesRegexp(TypeError, 'must be a string'):
            self.newSample.rename(42)
        self.assertEqual(self.newSample.name, 'ValidSample')

    #=========================================================================================
    # test_undo_Sample
    #=========================================================================================

    def test_undo_Sample(self):
        """
        Create an Undo point and check that the original/changed names are correct.
        """
        undo = self.project._undo
        newUndoPoint = self.project.newUndoPoint
        newUndoPoint()  # create a recovery point

        self.newSample.rename('Changed')  # new valid name
        self.assertEqual(self.newSample.name, 'Changed')

        undo.undo()
        self.assertEqual(self.newSample.name, 'ValidSample')  # original name

        undo.redo()
        self.assertEqual(self.newSample.name, 'Changed')

    #=========================================================================================
    # test_newSample
    #=========================================================================================

    def test_newSample(self):
        """
        Test that the new Sample is created and populated.
        """
        self.assertEqual(self.newSample.pid, 'SA:ValidSample')
        self.assertEqual(len(self.project.samples), 1)
        self.assertIs(self.project.samples[0], self.newSample)

    #=========================================================================================
    # test_properties_Sample
    #=========================================================================================

    def test_properties_Sample(self):
        """
        Test that Sample attribute .serial is populated.
        Read the attribute, if it not populated then an error is raised.
        """
        self.assertEqual(self.newSample.serial, 1)

    def test_properties_Sample_pH(self):
        """
        Test that Sample attribute .pH is populated.
        Read the attribute, if it not populated then an error is raised.
        If no error, then test the setter by setting and then getting to check consistent.
        Similarly for all set/get properties.
        """
        # pH = self.newSample.pH
        # self.newSample.pH = 0.5
        # self.assertEqual(self.newSample.pH, 0.5)
        #
        checkGetSetAttr(self, self.newSample, 'pH', 0.5)

    def test_properties_Sample_ionicStrength(self):
        """
        Test that Sample attribute .ionicStrength is populated.
        """
        checkGetSetAttr(self, self.newSample, 'ionicStrength', 0.5)

    def test_properties_Sample_amount(self):
        """
        Test that Sample attribute .amount is populated.
        """
        checkGetSetAttr(self, self.newSample, 'amount', 0.5)

    def test_properties_Sample_amountUnit(self):
        """
        Test that Sample attribute .amountUnit is populated.
        """
        checkGetSetAttr(self, self.newSample, 'amountUnit', 'mole')

    def test_properties_Sample_isVirtual(self):
        """
        Test that Sample attribute .isVirtual is populated.
        """
        checkGetSetAttr(self, self.newSample, 'isVirtual', True)

    def test_properties_Sample_plateIdentifier(self):
        """
        Test that Sample attribute .plateIdentifier is populated.
        """
        checkGetSetAttr(self, self.newSample, 'plateIdentifier', 'Identity')

    def test_properties_Sample_rowNumber(self):
        """
        Test that Sample attribute .rowNumber is populated.
        """
        checkGetSetAttr(self, self.newSample, 'rowNumber', 1)

    def test_properties_Sample_columnNumber(self):
        """
        Test that Sample attribute .columnNumber is populated.
        """
        checkGetSetAttr(self, self.newSample, 'columnNumber', 1)

    def test_properties_Sample_comment(self):
        """
        Test that Sample attribute .comment is populated.
        """
        checkGetSetAttr(self, self.newSample, 'comment', 'ValidComment')

    def test_properties_Sample_spectra(self):
        """
        Test that Sample attribute .spectra is populated.
        """
        self.assertEqual(str(self.newSample.spectra), '()')

    def test_properties_Sample_spectrumHits(self):
        """
        Test that Sample attribute .spectrumHits is populated.
        """
        self.assertEqual(str(self.newSample.spectrumHits), '()')

    def test_properties_Sample_pseudoDimensions(self):
        """
        Test that Sample attribute .pseudoDimensions is populated.
        """
        self.assertEqual(str(self.newSample.pseudoDimensions), '()')

    #=========================================================================================
    # test_properties_Sample    expectedFailure
    #=========================================================================================

    def test_properties_Sample_iH(self):
        """
        Test that Sample attribute .isHazardous is populated..

        This is an expectedFailure as .isHazardous has not been populated.
        """
        checkGetSetAttr(self, self.newSample, 'isHazardous', False)

    def test_properties_Sample_bI(self):
        """
        Test that Sample attribute .batchIdentifier is populated..

        This is an expectedFailure as .batchIdentifier has not been populated.
        """
        checkGetSetAttr(self, self.newSample, 'batchIdentifier', '#124345')

    def test_properties_Sample_creationDate(self):
        """
        Test that Sample attribute .creationDate can be set.

        This is an expectedFailure as .creationDate is 'frozen'.
        """
        # creationDate = self.newSample.creationDate
        # creationDate = datetime.datetime.now()
        # self.newSample.creationDate = creationDate
        # self.assertEqual(self.newSample.creationDate, creationDate)
        #
        checkGetSetAttr(self, self.newSample, 'creationDate', datetime.datetime.now())
