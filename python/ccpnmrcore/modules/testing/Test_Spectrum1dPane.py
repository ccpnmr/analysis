from ccpnmrcore.testing.Testing import Testing

from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem

from PySide import QtCore, QtGui

import sys



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



if __name__ == '__main__':
 def testMain():

   spectrum = Spectrum1dPaneTest()
   w = QtGui.QWidget()
   layout = QtGui.QGridLayout()
   spectrumPane=Spectrum1dPane()
   widget = spectrumPane.widget
   layout.addWidget(widget)
   widget.plot(spectrum.test_spectrum1dPane())
   widget.plotItem.layout.setContentsMargins(0, 0, 0, 0)
   w.setLayout(layout)
   w.show()
   w.raise_()
   sys.exit(spectrum.exec_())
 testMain()