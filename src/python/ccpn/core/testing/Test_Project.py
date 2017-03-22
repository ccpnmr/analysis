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

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.lib.Io import Api as apiIo


class ProjectTestRename(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_name_and_rename(self):
    apiNmrProject = self.project._apiNmrProject
    self.assertEqual(self.project.name, 'default')
    self.assertEqual(apiNmrProject.root.name, 'default')
    oldLocation =  apiNmrProject.root.findFirstRepository(name='userData').url.getDataLocation()
    self.assertTrue(os.path.isdir(oldLocation))


class ProjectTestExperimentTypeMap(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_experimentTypeMap(self):
    experimentTypeMap = self.project._experimentTypeMap
    self.assertEqual(list(sorted(experimentTypeMap.keys())), [1,2,3,4,5,6])

    experimentTypeMap2 = self.project._experimentTypeMap
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs (experimentTypeMap, experimentTypeMap2)

class ProjectTestIo(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse2b'

  def test_name(self):

    project = self.project
    self.assertTrue(project.name.startswith('CcpnCourse2b'))
    baseDir, projDir = os.path.split(project.path)
    self.assertEquals(projDir[-5:], '.ccpn')
    self.assertTrue(projDir.startswith('CcpnCourse2b'))

    self.assertTrue(project.save(newPath=os.path.join(baseDir, '_SAVED_TO_NAME.ccpn'),
                                 overwriteExisting=True))
    self.assertTrue(project.name.startswith('_SAVED_TO_NAME'))
    self.assertTrue(project.name == '_SAVED_TO_NAME' or project.name[14] == '_')