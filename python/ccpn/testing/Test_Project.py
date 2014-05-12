from ccpn.testing.Testing import Testing

class OpenProjectTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)

  def test_name(self):
    #assert self.project.name == 'CcpnCourse1a'
    assert self.project.name == 'CcpnDemo001'

  def test_spectra(self):
    print('number of spectra = %d' % self.project.spectra)


