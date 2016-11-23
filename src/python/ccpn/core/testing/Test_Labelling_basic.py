__author__ = 'TJ Ragan'

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError

class TestLabellingBasic(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.sample = self.project.newSample('test sample')
      self.chain1 = self.project.createChain(sequence='QWERTYIPASDF', molType='protein',
                                             compoundName='typewriter')

  def testUniformLabelling(self):
    sc1 = self.sample.newSampleComponent(name='acomponent')


  def _test_newSampleComponentWithoutName(self):
    self.assertRaises(TypeError, self.sample.newSampleComponent)
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 1)

  def test_newSampleComponentEmptyName(self):
    self.assertRaises(ApiError, self.sample.newSampleComponent, '')
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 1)

  def test_newSampleComponent(self):
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 1)

    sc = self.sample.newSampleComponent('test sample component')

    self.assertEqual(sc.pid, 'SC:test sample.test sample component.')
    self.assertEqual(len(self.project.sampleComponents), 1)
    self.assertEqual(len(self.project.substances), 2)
    self.assertIs(self.project.sampleComponents[0], sc)

  def test_newSampleComponent2(self):
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 1)

    sc = self.sample.newSampleComponent('typewriter')
    self.assertEqual(sc.pid, 'SC:test sample.typewriter.')
    self.assertEqual(len(self.project.sampleComponents), 1)
    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.sampleComponents[0], sc)

    sc2 = self.sample.newSampleComponent('typewriter', 'italic')
    self.assertEqual(sc2.pid, 'SC:test sample.typewriter.italic')
    self.assertEqual(len(self.project.sampleComponents), 2)
    self.assertEqual(len(self.project.substances), 2)
    self.assertIs(self.project.sampleComponents[1], sc2)
