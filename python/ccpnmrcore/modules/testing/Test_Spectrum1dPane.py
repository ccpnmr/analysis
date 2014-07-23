"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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