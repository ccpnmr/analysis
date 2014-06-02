from ccpn.testing.Testing import Testing

from ccpn.lib import Spectrum

class SpectrumTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)
    self.spectrumName = 'HSQC'

  def test_getPlaneData(self):
    spectrum = self.getSpectrum()
    # TB:D should have planeData = spectrum.getPlaneData()
    planeData = Spectrum.getPlaneData(spectrum)
    print('planeData.shape =', planeData.shape)
    print('planeData =', planeData[508:,2045:])
    
  def test_getSliceData(self):
    spectrum = self.getSpectrum()
    # TBD: should have sliceData = spectrum.getSliceData()
    sliceData = Spectrum.getSliceData(spectrum)
    print('sliceData.shape =', sliceData.shape)
    print('sliceData =', sliceData)
    

