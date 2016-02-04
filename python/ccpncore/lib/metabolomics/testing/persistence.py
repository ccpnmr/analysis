
__author__ = 'TJ Ragan'

import unittest
from ccpncore.lib.metabolomics import persistence


class TestMetabolomicsPersistenceDict(unittest.TestCase):
  def setUp(self):
    self.pd = persistence.MetabolomicsPersistenceDict()


  def test_MetabolomicsPersistenceDict_shares_state(self):
    self.pd['1'] = 1
    test = persistence.MetabolomicsPersistenceDict(('1', 1))

    self.assertIn('1', self.pd)
    self.assertIn('1', test)


if __name__ == '__main__':
  unittest.main()
