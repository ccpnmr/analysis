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


