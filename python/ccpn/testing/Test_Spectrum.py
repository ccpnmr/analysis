from ccpn.testing.Testing import Testing

from ccpncore.util import Path

class SimpleSpectrumTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1b', *args, **kw)
    self.spectrumName = 'HSQC'

  def test_have_spectrum(self):
    assert self.getSpectrum() is not None
  
  def test_id_is_spectrum(self):
    assert self.getSpectrum() is self.project.getSpectrum(self.spectrumName)

class SpectrumTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1b', *args, **kw)
    self.spectrumName = 'HSQC'
    
  def test_name(self):
    spectrum = self.getSpectrum()
    assert spectrum.name == self.spectrumName

  def test_dimensionCount(self):
    spectrum = self.getSpectrum()
    assert spectrum.dimensionCount == spectrum.ccpnSpectrum.numDim
    
  def test_pointCount(self):
    spectrum = self.getSpectrum()
    numPoints = tuple([dataDim.numPoints for dataDim in spectrum.ccpnSpectrum.sortedDataDims()])
    assert spectrum.pointCount == numPoints

  def test_filePath(self):
    spectrum = self.getSpectrum()
    spectrum.filePath.startswith(Path.getTopDirectory())
