__author__ = 'TJ Ragan'

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError

class TestSampleComponentCreation(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.sample = self.project.newSample('test sample')

  def _test_newSampleComponentWithoutName(self):
    self.assertRaises(TypeError, self.sample.newSampleComponent)
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSampleComponentEmptyName(self):
    self.assertRaises(ApiError, self.sample.newSampleComponent, '')
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSampleComponent(self):
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

    sc = self.sample.newSampleComponent('test sample component')

    self.assertEqual(sc.pid, 'SC:test sample.test sample component.std')
    self.assertEqual(len(self.project.sampleComponents), 1)
    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.sampleComponents[0], sc)
