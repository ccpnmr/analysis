"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

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
    
  # def test_rank(self):  # not implemented yet
  #   spectrum = self.project.getSpectrum('HSQC-115')
  #   # Undo and redo all operations
  #   self.undo.undo()
  #   self.undo.redo()
  #   self.assertTrue(hasattr(spectrum, 'rank'))

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


class DummySpectrumTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_dummySpectrum(self):
    axisCodes = ('CO','Hn','Nh')
    spectrum = self.project.createDummySpectrum(axisCodes)
    self.assertEqual(spectrum.isotopeCodes, ('13C', '1H', '15N'))
    spectrum1 = self.project.createDummySpectrum(axisCodes=['H','N','C'], name='testspec')
    self.assertEqual(spectrum1.name, 'testspec')
    spectrum2 = self.project.createDummySpectrum(axisCodes = ['Hp','F', 'Ph', 'H'])
    self.assertEqual(spectrum2.name, 'HpFPhH@3')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

    self.assertEqual(spectrum.name, 'COHnNh@1')
    self.assertEqual(spectrum.isotopeCodes, ('13C', '1H', '15N'))
    self.assertEqual(spectrum.spectrometerFrequencies, (10.,100.,10.))
    self.assertEqual(spectrum.spectralWidthsHz, (2560.,1280.,2560.))
    self.assertEqual(spectrum.totalPointCounts, (256,128,256))
    self.assertEqual(spectrum.pointCounts, (256,128,256))
    self.assertEqual(spectrum.experimentType, None)
    self.assertEqual(spectrum.dimensionCount, 3)
    self.assertEqual(spectrum.axisCodes, axisCodes)
    self.assertEqual(spectrum.referencePoints, (0.,0.,0.))
    self.assertEqual(spectrum.referenceValues, (236., 11.8, 236.))
