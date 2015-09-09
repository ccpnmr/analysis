"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.testing.Testing import Testing

from ccpncore.util import Path

class SimpleSpectrumTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1b', *args, **kw)
    self.spectrumName = 'HSQC-115'

  def test_have_spectrum(self):
    assert self.getSpectrum() is not None
  
  def test_id_is_spectrum(self):
    assert self.getSpectrum() is self.project.getSpectrum(self.spectrumName)

class SpectrumTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1b', *args, **kw)
    self.spectrumName = 'HSQC-115'
    
  def test_name(self):
    spectrum = self.getSpectrum()
    assert spectrum.name == self.spectrumName

  def test_dimensionCount(self):
    spectrum = self.getSpectrum()
    assert spectrum.dimensionCount == spectrum._apiDataSource.numDim
    
  def test_pointCount(self):
    spectrum = self.getSpectrum()
    numPoints = tuple([dataDim.numPoints for dataDim in spectrum._apiDataSource.sortedDataDims()])
    assert spectrum.pointCounts == numPoints

  def test_filePath(self):
    spectrum = self.getSpectrum()
    spectrum.filePath.startswith(Path.getTopDirectory())
    
  def test_rank(self):  # not implemented yet
    spectrum = self.getSpectrum()
    print(hasattr(spectrum, 'rank'))
