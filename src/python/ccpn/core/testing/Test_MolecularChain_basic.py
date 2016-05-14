__author__ = 'TJ Ragan'

from ccpn.core.testing.WrapperTesting import WrapperTesting


class TestPhysicalChainCreation(WrapperTesting):

  def test_createPhysicalChain(self):
    c = self.project.createChain('acd', molType='protein')

    self.assertEqual(len(self.project.chains), 1)
    self.assertIs(self.project.chains[0], c)
    self.assertEqual(c.pid, 'MC:A')


  def test_createPhysicalChainFromPolymerSubstance(self):
    s = self.project.createPolymerSubstance('acd', name='test', molType='protein')
    c = s.createChain()

    self.assertIs(self.project.chains[0], c)
    self.assertEqual(c.pid, 'MC:A')
    self.assertIs(c.substance, s)
