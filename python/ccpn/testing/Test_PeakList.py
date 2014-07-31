from ccpn.testing.Testing import Testing

class PeakListTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1b', *args, **kw)
    self.spectrumName = 'HSQC'
    
  def test_newPeakList(self):
    spectrum = self.getSpectrum()
    peakList = spectrum.newPeakList()

