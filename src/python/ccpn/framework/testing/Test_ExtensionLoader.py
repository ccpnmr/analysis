__author__ = 'TJ Ragan'

import unittest
import os

from ccpn.framework.lib.ExtensionLoader import getPlugins
from ccpn.util.Path import getPythonDirectory

# class TestExtensionLoader(unittest.TestCase):
#
#   def setUp(self):
#     self.testExtensionPath = os.path.join(getPythonDirectory(), 'ccpn', 'framework', 'testing')
#
#
#   def test(self):
#     extensions = getExtensions(self.testExtensionPath)
#     for e in extensions:
#       self.assertTrue(hasattr(e, 'METHODNAME'))
#       self.assertTrue(hasattr(e, 'runMethod'))
#       print(e().__class__)

class TestPluginLoader(unittest.TestCase):

  def test(self):
    Plugins = getPlugins()
    for Plugin in Plugins:
      plugin = Plugin()
      plugin.run()
