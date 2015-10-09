"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

import os
import shutil
from ccpncore.util import Io as ioUtil

from ccpn.testing.WrapperTesting import WrapperTesting

# from ccpncore.api.ccp.nmr.Nmr import NmrProject

# class SimpleProjectTest(Testing):
#
#   # Path of project to load (None for new project)
#   projectPath = 'CcpnCourse1a'
#
#   def test_id(self):
#     print(self.project.id)
#
#   def test_nmrproject_not_none(self):
#       assert self.project._apiNmrProject is not None
#
#   def test_project_is_nmrproject(self):
#     assert isinstance(self.project._apiNmrProject, NmrProject)
#
#   def test_name(self):
#     assert self.project.name == self.project._apiNmrProject.name
#
#   def test_spectra(self):
#     assert len(self.project.spectra) == 3
#     print([x.id for x in self.project.spectra])
#
#   def test_chains(self):
#     assert len(self.project.chains) == 0
#
#   def test_atoms(self):
#     assert len(self.project.atoms) == 0


class ProjectTest2c(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse2c'

  def test_id(self):
    print(self.project.id)

    # # NBNB TEMP addition
    # root = self.project._apiNmrProject.root
    # for ccc in root.sortedChemCompCoords():
    #   cc = root.findFirstChemComp(molType=ccc.molType, ccpCode=ccc.ccpCode)
    #   if cc is None:
    #     if len(ccc.ccpCode) == 1:
    #       cc2 = root.findFirstChemComp(molType=ccc.molType, code1Letter=ccc.ccpCode)
    #       if cc2 is None:
    #        print("MISSING CC2:", ccc.molType, ccc.ccpCode, ccc)
    #       else:
    #         print("REMAP %s %s to %s" % (ccc.molType, ccc.ccpCode, cc2.ccpCode))
    #     else:
    #       print("MISSING CC :", ccc.molType, ccc.ccpCode, ccc)

  # def test_rename(self):
  #   print(self.project.name)
  #   self.project.rename('NEWNAME')
  #   print(self.project.name)

class ProjectTestRename(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_name_and_rename(self):
    apiNmrProject = self.project._apiNmrProject
    self.assertEqual(self.project.name, 'default')
    self.assertEqual(apiNmrProject.root.name, 'default')
    oldLocation =  apiNmrProject.root.findFirstRepository(name='userData').url.getDataLocation()
    self.assertTrue(os.path.isdir(oldLocation))

    # rename and check again
    newName = '_TEMPORARY_RENAMED'
    self.project.rename(newName)
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(apiNmrProject.root.name, newName)
    self.assertEqual(apiNmrProject.name, newName)
    self.assertEqual(self.project.name, newName)
    newLocation = apiNmrProject.root.findFirstRepository(name='userData').url.getDataLocation()
    self.assertEqual(newName, newLocation[-len(newName):])

class ProjectTestExperimentTypeMap(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_experimentTypeMap(self):
    experimentTypeMap = self.project._experimentTypeMap
    self.assertEqual(list(sorted(experimentTypeMap.keys())), [1,2,3,4,5,6])
    # for key, dd in experimentTypeMap.items():
    #   print("@~@~", key)
    #   for kk,vv in sorted(dd.items()):
    #     print ("       ", kk)
    #     for kk1,vv1 in sorted(vv.items()):
    #       print ("                    ", kk1, vv1)

    experimentTypeMap2 = self.project._experimentTypeMap
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs (experimentTypeMap, experimentTypeMap2)
