"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:02 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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
        self.assertTrue(apiIo.saveProject(self.project))

    def test_project_save_as(self):
        newPath = os.environ.get('HOME') or os.getcwd()
        newPath = os.path.join(newPath, 'tmpCcpnTestProject')
        newPath = apiIo.addCcpnDirectorySuffix(newPath)
        if os.path.exists(newPath):
            shutil.rmtree(newPath)
        self.assertTrue(apiIo.saveProject(self.project, newPath))
        # pathToCheck = os.path.join(ApiPath.getTopObjectPath(self.project), 'memops', 'Implementation')
        pathToCheck = os.path.join(newPath, 'ccpnv3', 'memops', 'Implementation')
        assert os.path.exists(pathToCheck), 'path "%s" does not exist' % pathToCheck
