__author__ = 'TJ Ragan'

import unittest
import os

from ccpn.framework.lib.ExtensionLoader import getExtensions
from ccpn.util.Path import getPythonDirectory

class TestExtensionLoader(unittest.TestCase):

  def setUp(self):
    self.testExtensionPath = os.path.join(getPythonDirectory(), 'ccpn', 'framework', 'testing')


  def test(self):
    extensions = getExtensions(self.testExtensionPath)
    for e in extensions:
      self.assertTrue(hasattr(e, 'METHODNAME'))
      self.assertTrue(hasattr(e, 'runMethod'))
      print(e().__class__)
