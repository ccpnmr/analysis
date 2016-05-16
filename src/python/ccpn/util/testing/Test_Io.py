"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
import os
import shutil

# from ccpnmodel.ccpncore.lib import ApiPath
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting

class IoTest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse1a'
    
  def test_project_save(self):
    
    apiIo.saveProject(self.project)

  def test_project_save_as(self):
    
    newPath = os.environ.get('HOME') or os.getcwd()
    newPath = os.path.join(newPath, 'tmpCcpnTestProject')
    newPath = apiIo.ccpnProjectPath(newPath)
    if os.path.exists(newPath):
      shutil.rmtree(newPath)
    apiIo.saveProject(self.project, newPath)
    # pathToCheck = os.path.join(ApiPath.getTopObjectPath(self.project), 'memops', 'Implementation')
    pathToCheck = os.path.join(newPath, 'memops', 'Implementation')
    assert os.path.exists(pathToCheck), 'path "%s" does not exist' % pathToCheck

