"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import copy
from ccpn.framework import Framework
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.core.lib import CcpnNefIo

def test_nef_maps():

  # Validity check
  # Check that elements in nef2CcpnMap match saveFrameOrder
  # and that all contents are present and reached from saveframes in saveFrameOrder
  copyMap = copy.deepcopy(CcpnNefIo.nef2CcpnMap)
  for category in CcpnNefIo.saveFrameOrder:
    map1 = copyMap.pop(category)
    for tag, val in map1.items():
      if val == CcpnNefIo._isALoop:
        copyMap.pop(tag)
  if copyMap:
    raise TypeError("Coding Error - Data in nef2CcpnMap not reached from saveFrameOrder:\n%s"
                  % list(copyMap.keys()))



class NefIoTest(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = 'CcpnCourse2b'

  def test_nef_write_read(self):
    nefPath = self.project.path + '.out.nef'
    CcpnNefIo.saveNefProject(self.project, nefPath)
    application = self.project._appBase
    application.loadProject(nefPath)