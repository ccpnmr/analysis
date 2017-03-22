__author__ = "$Author: TJ Ragan $"

import unittest
from unittest.mock import Mock, patch
import os

from ccpn.framework.lib.Plugin import Plugin


class MinimalPlugin(Plugin):
  PLUGINNAME = 'testplugin'


class TestPluginBaseClass(unittest.TestCase):

  def test_missing_pluginname(self):
    '''Plugin requires you to override PLUGINNAME'''
    class Test(Plugin):
      pass

    with self.assertRaises(TypeError):
      p = Test(None)


  def test_ABC(self):
    p = MinimalPlugin()


# from ccpn.core.testing.WrapperTesting import WrapperTesting
# class Test(WrapperTesting):
#   def test(self):
#     p = os.path.split(self.project.path)[0]
#     p = os.path.join(p, 'plugins')
#     print(p)


class TestPlugin(unittest.TestCase):

  def setUp(self):
    self.application = Mock()
    self.application.current = Mock()
    self.application.preferences = Mock()
    self.application.undo = Mock()
    self.application.redo = Mock()
    self.application.ui = Mock()
    self.application.project = Mock()
    self.application.project.path = '/tmp/ccpntest/default'

  def test_PluginName(self):
      plugin = MinimalPlugin()
      self.assertEqual(plugin.name, MinimalPlugin.PLUGINNAME)

  def test_PluginPackage(self):
    plugin = MinimalPlugin()
    self.assertEqual(plugin.package, MinimalPlugin.PLUGINNAME)


  def test_localInfo(self):
    with patch('ccpn.framework.lib.Plugin.os.makedirs') as mock_makedirs:
      plugin = MinimalPlugin(self.application)
      localPath = plugin.localInfo
      mock_makedirs.assert_called_once_with(os.path.join('/tmp/ccpntest/', 'plugins', MinimalPlugin.PLUGINNAME))


  def _test__gui(self):
    plugin = MinimalPlugin()
    print(plugin._gui)
