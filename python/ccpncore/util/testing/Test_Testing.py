from ccpncore.util.Testing import Testing

class SimpleTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)

  def test_name(self):
    assert self.project.name == 'CcpnCourse1a'

  def test_experimentCount(self):
    assert len(self.nmrProject.experiments) == 3

