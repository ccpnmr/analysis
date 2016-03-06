__author__ = 'TJ Ragan'

from ccpn.testing.WrapperTesting import WrapperTesting
from ccpncore.memops.ApiError import ApiError


class TestSampleCreation(WrapperTesting):

  def test_newSampleWithoutName(self):
    # Creation function changed to provide default name
    # self.assertRaises(TypeError, self.project.newSample)
    newSample =  self.project.newSample()
    self.assertEqual(newSample.name, 'Sample_1')
    self.assertEqual(len(self.project.samples), 1)

  def test_newSampleEmptyName(self):
    self.assertRaises(ApiError, self.project.newSample, '')
    self.assertEqual(len(self.project.samples), 0)

  def test_newSample(self):
    s = self.project.newSample('test sample')

    self.assertEqual(s.pid, 'SA:test sample')
    self.assertEqual(len(self.project.samples), 1)
    self.assertIs(self.project.samples[0], s)


  def test_rename_sample(self):
    obj = self.project.newSample(name='patty')
    undo = self.project._undo
    undo.newWaypoint()
    obj.rename('cake')
    self.assertEqual(obj.name, 'cake')
    undo.undo()
    self.assertEqual(obj.name, 'patty')
    undo.redo()
    self.assertEqual(obj.name, 'cake')