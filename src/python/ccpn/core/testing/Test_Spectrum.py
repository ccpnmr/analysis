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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.util import Path


class SimpleSpectrumTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'CcpnCourse1b'

    def test_have_spectrum(self):
        assert self.project.getSpectrum('HSQC-115') is not None

    def test_id_is_spectrum(self):
        assert self.project.getSpectrum('HSQC-115').name == 'HSQC-115'
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()


class SpectrumTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'CcpnCourse1b'

    def test_dimensionCount(self):
        spectrum = self.project.getSpectrum('HSQC-115')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        assert spectrum.dimensionCount == spectrum._apiDataSource.numDim

    def test_pointCount(self):
        spectrum = self.project.getSpectrum('HSQC-115')
        numPoints = tuple([dataDim.numPoints for dataDim in spectrum._apiDataSource.sortedDataDims()])

        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        assert spectrum.pointCounts == numPoints

    def test_filePath(self):
        spectrum = self.project.getSpectrum('HSQC-115')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertTrue(spectrum.filePath.startswith(Path.getTopDirectory()))

    def test_rename(self):
        spectrum = self.project.getSpectrum('HSQC-115')
        peakList = spectrum.peakLists[0]
        spectrum.rename('NEWNAME')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(spectrum.pid, 'SP:NEWNAME')
        self.assertEqual(peakList.pid, 'PL:NEWNAME.1')
        self.assertEqual(peakList.peaks[0].pid, 'PK:NEWNAME.1.1')


class SpectrumIntensitiesTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'Ccpn1Dtesting'

    def test_intensities_get(self):
        self.project._wrappedData.root.checkAllValid(complete=True)
        spectrum = self.project.getSpectrum('1D-1')
        intensities = spectrum.intensities
        self.assertIs(intensities, spectrum.intensities)

    def test_intensities_set(self):
        spectrum = self.project.getSpectrum('1D-1')
        intensities = spectrum.intensities
        intensities[0] = 19.23
        constant1 = intensities[0]  # have to do as separate step o/w constant1 has type float instead of numpy.float32
        constant2 = spectrum.intensities[0]
        self.assertEqual(constant1, constant2)


class DummySpectrumTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_dummySpectrum(self):
        axisCodes = ('CO', 'Hn', 'Nh')
        spectrum = self.project.createDummySpectrum(axisCodes)
        self.assertEqual(spectrum.isotopeCodes, ('13C', '1H', '15N'))
        self.assertEqual(spectrum.name, 'COHnNh')
        spectrum1 = self.project.createDummySpectrum(axisCodes=['H', 'N', 'C'], name='testspec')
        self.assertEqual(spectrum1.name, 'testspec')
        spectrum2 = self.project.createDummySpectrum(axisCodes=['Hp', 'F', 'Ph', 'H'])
        self.assertEqual(spectrum2.name, 'HpFPhH')
        # Undo and redo all operations
        self.undo.undo()
        self.undo.undo()
        self.undo.undo()
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()

        self.project._wrappedData.root.checkAllValid(complete=True)

        self.assertEqual(spectrum.name, 'COHnNh')
        self.assertEqual(spectrum1.name, 'testspec')
        self.assertEqual(spectrum2.name, 'HpFPhH')
        self.assertEqual(spectrum.isotopeCodes, ('13C', '1H', '15N'))
        self.assertEqual(spectrum.spectrometerFrequencies, (10., 100., 10.))
        self.assertEqual(spectrum.spectralWidthsHz, (2560., 1280., 2560.))
        self.assertEqual(spectrum.totalPointCounts, (256, 128, 256))
        self.assertEqual(spectrum.pointCounts, (256, 128, 256))
        self.assertEqual(spectrum.experimentType, None)
        self.assertEqual(spectrum.dimensionCount, 3)
        self.assertEqual(spectrum.axisCodes, axisCodes)
        self.assertEqual(spectrum.referencePoints, (1., 1., 1.))
        self.assertEqual(spectrum.referenceValues, (236., 11.8, 236.))
