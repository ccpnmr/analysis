#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:37 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

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
