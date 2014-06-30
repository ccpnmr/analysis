from ccpnmrcore.testing.Testing import Testing

from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem



import ccpn

class Spectrum1dPaneTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, projectPath='Ccpn1Dtesting', *args, **kw)
    self.spectrumName = '1D'
    self.project = ccpn.openProject(self.projectPath)
    self.test_spectrum1dPane()


  def test_spectrum1dPane(self):

    spectrumPane = Spectrum1dPane()
    spectrum = self.getSpectrum()
    data = Spectrum1dItem(spectrumPane,spectrum).spectralData
    return data


  def testIntegration(self):
    spectrumPane = Spectrum1dPane()
    spectrum = self.getSpectrum()
    return Spectrum1dItem(spectrumPane,spectrum).integrals





