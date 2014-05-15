# import sys
# print('sys.path=',sys.path)
from ccpn.testing.Testing import Testing

from ccpncore.api.ccp.nmr.Nmr import NmrProject

class OpenProjectTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)

  def test_id(self):
    print(self.project.id)
    
  def test_nmrproject_not_none(self):
      assert self.project.nmrProject is not None

  def test_project_is_nmrproject(self):
    assert isinstance(self.project.nmrProject, NmrProject)
    
  def test_name(self):
    assert self.project.name == self.project.nmrProject.name

  def test_spectra(self):
    assert len(self.project.spectra) == 3
  
  def test_chains(self):
    assert len(self.project.chains) == 0

  def test_atoms(self):
    assert len(self.project.atoms) == 0



