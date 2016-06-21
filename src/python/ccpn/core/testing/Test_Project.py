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


# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrProject

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


# class ProjectTest2c(WrapperTesting):
#
#   # Path of project to load (None for new project)
#   projectPath = 'CcpnCourse2c'
#
#   def test_id(self):
#     print(self.project.id)

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
    newPath = self.project.path
    nn = len(apiIo.CCPN_DIRECTORY_SUFFIX)
    self.assertEqual(newName, newPath[-len(newName)-nn:-nn])

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

class ProjectTestIo(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse2b'

  def test_name(self):

    project = self.project
    print('@~@~1', project.name, project.path)
    project.rename('_TEMPORARY_RENAMED')
    print('@~@~2', project.name, project.path)
    project.save(newProjectName='_SAVED_TO_NAME')
    print('@~@~3', project.name, project.path)
    inPath = os.path.dirname(project.path)
    newPath = os.path.join(inPath, '_SAVED_TO_DIR.ccpn')
    project.save(newPath)
    print('@~@~4', project.name, project.path)
    newPath = os.path.join(inPath, '_SAVED_TO_DIR')
    project.save(newPath)
    print('@~@~5', project.name, project.path)

    self.assertEqual("Rename functionality needs redoing and testing", "not done yet")