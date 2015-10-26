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


from ccpncore.testing.CoreTesting import CoreTesting
import os
from ccpncore.util import Path
from ccpncore.util import Io
TEST_PROJECTS_PATH = os.path.join(Path.getTopDirectory(), 'data/testProjects')
from ccpncore.memops.ApiError import ApiError

class NaNtest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def testNaN(self):
    spectrum = self.nmrProject.createDummySpectrum(name='nanTest', axisCodes=('Hn', 'Nh', 'CO'))
    self.assertEqual(spectrum.scale, 1.0)
    self.assertEqual(spectrum.name, 'nanTest')

    # test NaN
    self.assertRaises(ApiError,setattr, spectrum, 'scale', float('NaN'))

