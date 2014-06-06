from ccpnmrcore.testing.Testing import Testing

from ccpnmrcore.modules.SpectrumNdPane import SpectrumNdPane

class SpectrumPaneTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)
    self.spectrumName = 'HSQC'

  def test_spectrumNdPane(self):

    spectrumPane = SpectrumNdPane(self.project, self.frame)
    spectrum = self.getSpectrum()
    spectrumPane.addSpectrum(spectrum)
