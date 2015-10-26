__author__ = 'TJ Ragan'

from ccpn.testing.WrapperTesting import WrapperTesting
from ccpncore.memops.ApiError import ApiError


class TestSampleCreation(WrapperTesting):

  def test_newSampleWithoutName(self):
    self.assertRaises(TypeError, self.project.newSample)
    self.assertEqual(len(self.project.samples), 0)

  def test_newSampleEmptyName(self):
    self.assertRaises(ApiError, self.project.newSample, '')
    self.assertEqual(len(self.project.samples), 0)

  def test_newSample(self):
    s = self.project.newSample('test sample')

    self.assertEqual(s.pid, 'SA:test sample')
    self.assertEqual(len(self.project.samples), 1)
    self.assertIs(self.project.samples[0], s)
