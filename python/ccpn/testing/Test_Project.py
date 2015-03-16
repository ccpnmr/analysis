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
from ccpn.testing.Testing import Testing

from ccpncore.api.ccp.nmr.Nmr import NmrProject

# class SimpleProjectTest(Testing):
#
#   def __init__(self, *args, **kw):
#     Testing.__init__(self, 'CcpnCourse1a', *args, **kw)
#
#   def test_id(self):
#     print(self.project.id)
#
#   def test_nmrproject_not_none(self):
#       assert self.project.nmrProject is not None
#
#   def test_project_is_nmrproject(self):
#     assert isinstance(self.project.nmrProject, NmrProject)
#
#   def test_name(self):
#     assert self.project.name == self.project.nmrProject.name
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


class ProjectTest2c(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse2c', *args, **kw)

  def test_id(self):
    print(self.project.id)


