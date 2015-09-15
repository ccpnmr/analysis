"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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

from ccpn.testing.WrapperTesting import WrapperTesting

class SpectrumTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_createDummySpectrum(self, *args, **kw):
    spectrum = self.project.createDummySpectrum(axisCodes=['H','N','C'], name='testspec')
    self.assertEqual(spectrum.name, 'testspec')
    spectrum = self.project.createDummySpectrum(axisCodes = ['Hp','F', 'Ph', 'H'])
    self.assertEqual(spectrum.name, 'HpFPhH@2')

