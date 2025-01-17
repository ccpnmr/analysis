"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-03-20 19:06:26 +0000 (Wed, March 20, 2024) $"
__version__ = "$Revision: 3.2.2.1 $"
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
