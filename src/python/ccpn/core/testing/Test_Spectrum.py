"""Module Documentation here

"""
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-11-10 11:33:33 +0000 (Sun, November 10, 2024) $"
__version__ = "$Revision: 3.2.10.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from numpy import ones
from ccpn.core.testing.WrapperTesting import WrapperTesting, fixCheckAllValid
from ccpn.util import Path, Constants
from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource
from ccpn.util.Common import Sentinel


class SimpleSpectrumTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'V3ProjectForTests.ccpn'

    def test_get_spectrum(self):
        self.assertTrue(self.project.getSpectrum('hsqc_115') is not None)

    def test_id_is_spectrum(self):
        self.assertEqual(self.project.getSpectrum('hsqc_115').name, 'hsqc_115')


class SpectrumTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'V3ProjectForTests.ccpn'

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.getSpectrum('hsqc_115')
            # Undo and redo all operations (?)
            # self.undo.undo()
            # self.undo.redo()

    def test_dimensionCount(self):
        self.assertEqual(self.spectrum.dimensionCount, self.spectrum._apiDataSource.numDim)

    def test_pointCount(self):
        numPoints = [dataDim.numPoints for dataDim in self.spectrum._apiDataSource.sortedDataDims()]
        self.assertEqual(self.spectrum.pointCounts, numPoints)

    def test_filePath(self):
        self.assertTrue(self.spectrum.filePath.startswith('$ALONGSIDE'))
        self.assertTrue(self.spectrum.dataSource.dataFile.startswith(Path.getTopDirectory()))

    def test_rename(self):
        peakList = self.spectrum.peakLists[0]
        initial_name = self.spectrum.name
        self.spectrum.rename('NEWNAME')

        def name_tester(name):
            self.assertEqual(self.spectrum.pid, f'SP:{name}')
            self.assertEqual(peakList.pid, f'PL:{name}.1')
            self.assertEqual(peakList.peaks[0].pid, f'PK:{name}.1.1')

        name_tester('NEWNAME')

        self.undo.undo()
        name_tester(initial_name)
        self.undo.redo()
        name_tester('NEWNAME')
        self.spectrum.rename(initial_name)


class SpectrumCcpNmrPropertiesTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'V3ProjectForTests.ccpn'

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.getSpectrum('hsqc_115')

    def assertEqualForAttribute(self, attribute, value1, value2=Sentinel):
        """Helper routine to test the value of attribute of self.spectrum:
        - assert it is equal to value1
        - set to value2
        - assert it is equal to value2
        - undo
        - assert it is equal to value1
        - redo
        - assert it is equal to value2
        - undo
        """
        _obj = self.spectrum
        super().assertEqualForAttribute(obj=_obj,
                                        attribute=attribute,
                                        value1=value1,
                                        value2=value2
                                        )

    def assertEqualForAttributeItem(self, attribute, value1, value2=Sentinel, itemIndex=0):
        """Perform a test check for setting the item of attribute of self.spectrum:
        """
        _obj = self.spectrum
        super().assertEqualForAttributeItem(obj=_obj,
                                            attribute=attribute,
                                            value1=value1,
                                            value2=value2,
                                            itemIndex=itemIndex
                                            )

    def test_chemicalShiftList(self):
        _clDefault = self.project.chemicalShiftLists[0]
        _cl = self.project.chemicalShiftLists[1]
        self.assertEqualForAttribute('chemicalShiftList', _clDefault, _cl)
        # check pid, str; can't use general routine as it compares to "value1/2" and the
        # actual set value is converted from Pid/str to the object. Hence, the comparison will fail
        self.spectrum.chemicalShiftList = _cl.pid
        self.assertEqual(self.spectrum.chemicalShiftList, _cl)
        self.spectrum.chemicalShiftList = str(_clDefault.pid)
        self.assertEqual(self.spectrum.chemicalShiftList, _clDefault)

    def test_sliceColour(self):
        self.assertEqualForAttribute('sliceColour', '#008080', '#FFFFFF')

    def test_spinningRate(self):
        self.assertEqualForAttribute('spinningRate', None, 1001)

    def test_acquisitionAxisCode(self):
        self.assertEqualForAttribute('acquisitionAxisCode', None)

    def test_positiveContourCount(self):
        self.assertEqualForAttribute('positiveContourCount', 10, 15)

    def test_positiveContourBase(self):
        self.assertEqualForAttribute('positiveContourBase', 1231687.956148175, 1e6)

    def test_positiveContourFactor(self):
        self.assertEqualForAttribute('positiveContourFactor', 1.414214, 1.2)

    def test_positiveContourColour(self):
        self.assertEqualForAttribute('positiveContourColour', '#008080', '#FF00FF')

    def test_includePositiveContours(self):
        self.assertEqualForAttribute('includePositiveContours', True, False)

    def test_negativeContourCount(self):
        self.assertEqualForAttribute('negativeContourCount', 10, 15)

    def test_negativeContourBase(self):
        self.assertEqualForAttribute('negativeContourBase', -1231687.956148175, -1e6)

    def test_negativeContourFactor(self):
        self.assertEqualForAttribute('negativeContourFactor', 1.414214, 1.2)

    def test_negativeContourColour(self):
        self.assertEqualForAttribute('negativeContourColour', '#DA70D6', '#FF00FF')

    def test_includeNegativeContours(self):
        self.assertEqualForAttribute('includeNegativeContours', True, False)

    def test_displayFoldedContours(self):
        self.assertEqualForAttribute('displayFoldedContours', True, False)

    def test_name(self):
        self.assertEqualForAttribute('name', 'hsqc_115', 'test')

    def test_experimentType(self):
        self.assertEqualForAttribute('experimentType', None, 'H[N]')

    # GWV: the experimentName seems to have been set oddly in the test project!
    def test_experimentName(self):
        self.assertEqualForAttribute('experimentName', '115', 'test')

    def test_referenceExperimentDimensions(self):
        self.assertEqualForAttribute('referenceExperimentDimensions', [None, None], ['HN', 'N2'])
        self.assertEqualForAttributeItem('referenceExperimentDimensions', [None, None], ['H', 'N2'], itemIndex=1)

    def test_magnetizationTransfers(self):
        self.assertEqualForAttribute('_magnetisationTransfers', [], [(1, 2, 'onebond', False)])


    # dimensional ones depending on TypedList
    def test_isComplex(self):
        self.assertEqualForAttribute('isComplex', [False, False],[True, False])
        self.assertEqualForAttributeItem('isComplex', [False, False],[True, False], 0)

    # dimensional ones depending on TypedList
    def test_isAcquisition(self):
        self.assertEqualForAttribute('isAcquisition', [False, False],[True, False])
        self.assertEqualForAttributeItem('isAcquisition', [False, False],[True, False], 0)

    def test_axisCodes(self):
        self.assertEqualForAttribute('axisCodes', ['H', 'N'], ['HN', 'N2'])
        self.assertEqualForAttributeItem('axisCodes', ['H', 'N'], ['H', 'N2'], itemIndex=1)

    def test_dimensionTypes(self):
        self.assertEqualForAttribute('dimensionTypes', ['Frequency', 'Frequency'], ['Frequency', 'Time'])

class SpectrumIntensitiesTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'V3ProjectForTests.ccpn'

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.getSpectrum('1H_1D')
            self.intensities = self.spectrum.intensities

    def tearDown(self):
        self.intensities = self.spectrum.intensities

    def test_intensities_get(self):
        # fix the bad structure for the test
        # new pdb loader does not load the into the data model so there are no atoms defined
        # the corresponding dataMatrices therefore have dimension set to zero which causes a crash :|
        # ==================================== REMOVED ========================================= #
        # fixCheckAllValid(self.project)
        # self.project._wrappedData.root.checkAllValid(complete=True)
        # ====================================================================================== #
        self.assertIs(self.intensities, self.spectrum.intensities)

    def test_intensities_set(self):
        self.intensities[0] = 19.23
        # have to do as separate step o/w constant1 has type float instead of numpy.float32
        constant1 = self.intensities[0]
        constant2 = self.spectrum.intensities[0]
        self.assertEqual(constant1, constant2)

    def test_intensitiesNone_set_get(self):
        self.spectrum.intensities = ones(32768)
        spect_ones = self.spectrum.intensities[0]
        self.spectrum.intensities = None
        spect_none = self.spectrum.intensities[0]
        self.assertNotEqual(spect_ones, spect_none)
        self.assertEqual(self.spectrum.getSliceData()[0], spect_none)

        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(self.spectrum.intensities[0], spect_ones)
        self.undo.undo()
        self.assertEqual(self.spectrum.intensities[0], spect_none)
        self.undo.redo()
        self.assertEqual(self.spectrum.intensities[0], spect_ones)
        self.undo.redo()
        self.assertEqual(self.spectrum.intensities[0], spect_none)


class DummySpectrumTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_dummySpectrum(self):
        # Double check these test after refactoring DummySpectrum
        axisCodes = ['CO', 'Hn', 'Nh']
        spectrum = self.project.newEmptySpectrum(isotopeCodes=('13C','1H', '15N'), name='COHnNh')
        spectrum.axisCodes = axisCodes

        isotopeCodes = ['13C', '1H', '15N']
        self.assertEqual(spectrum.isotopeCodes, isotopeCodes)
        self.assertEqual(spectrum.name, 'COHnNh')

        spectrum1 = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N', '13C'), name='testspec')
        self.assertEqual(spectrum1.name, 'testspec')

        spectrum2 = self.project.newEmptySpectrum(isotopeCodes=('1H', '19F', '31P', '1H'), name='HpFPhH')
        self.assertEqual(spectrum2.name, 'HpFPhH')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(len(self.project.spectra), 2)
        self.undo.undo()
        self.assertEqual(len(self.project.spectra), 1)
        self.undo.undo()
        self.assertEqual(len(self.project.spectra), 0)
        self.undo.redo()
        self.assertEqual(len(self.project.spectra), 1)
        self.undo.redo()
        self.assertEqual(len(self.project.spectra), 2)
        self.undo.redo()
        self.assertEqual(len(self.project.spectra), 3)

        self.project._wrappedData.root.checkAllValid(complete=True)

        self.assertEqual(spectrum.name, 'COHnNh')
        self.assertEqual(spectrum1.name, 'testspec')
        self.assertEqual(spectrum2.name, 'HpFPhH')

        self.assertEqual(spectrum.isotopeCodes, ['13C', '1H', '15N'])

        # get the default parameters from the empty spectrum class
        numPoints = [EmptySpectrumDataSource.isotopeDefaultDataDict[ic]['pointCount'] for ic in isotopeCodes]
        sw = [EmptySpectrumDataSource.isotopeDefaultDataDict[ic]['spectralRange'] for ic in isotopeCodes]
        # sf = tuple([EmptySpectrumDataSource.isotopeDefaultDataDict[ic]['sf'] for ic in isotopeCodes])
        # refppm = tuple([EmptySpectrumDataSource.isotopeDefaultDataDict[ic]['refppm'] for ic in isotopeCodes])
        # refpt = tuple([EmptySpectrumDataSource.isotopeDefaultDataDict[ic]['refpt'] for ic in isotopeCodes])

        # self.assertEqual(spectrum.spectralWidthsHz, sw)
        self.assertEqual(spectrum.pointCounts, numPoints)
        self.assertEqual(spectrum.experimentType, None)
        self.assertEqual(spectrum.dimensionCount, 3)
        self.assertEqual(spectrum.axisCodes, axisCodes)
        # self.assertEqual(spectrum.spectrometerFrequencies, sf)
        # self.assertEqual(spectrum.referencePoints, refpt)
        # self.assertEqual(spectrum.referenceValues, refppm)
