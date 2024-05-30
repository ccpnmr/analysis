"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Daniel Thompson $"
__dateModified__ = "$dateModified: 2024-05-29 12:25:08 +0100 (Wed, May 29, 2024) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"

import contextlib
#=========================================================================================
# Start of code
#=========================================================================================

import os

from ccpn.framework import Framework
from ccpn.util.Path import aPath
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.framework.Application import defineProgramArguments
from ccpn.AnalysisAssign.AnalysisAssign import Assign as Application
from ccpn.framework.PathsAndUrls import userPreferencesDirectory
from ccpn.ui.gui.widgets.Application import newTestApplication
import unittest
from unittest import mock


# def test_get_preferences():
#     preferences = Framework.getPreferences()
#
#     print(preferences)
#
#
# def test_get_preferences_default():
#     defaultPath = os.path.join(os.path.dirname(__file__), 'defaultv3settingsTest.json')
#     preferences = Framework.getPreferences(defaultPath=defaultPath)
#     print(preferences)
#
#
# def test_get_preferences_user():
#     userPath = os.path.join(os.path.dirname(__file__), 'userv3settingsTest.json')
#     preferences = Framework.getPreferences(userPath=userPath)
#     print(preferences)
#
#
# def test_get_preferences_default_user():
#     defaultPath = os.path.join(os.path.dirname(__file__), 'defaultv3settingsTest.json')
#     userPath = os.path.join(os.path.dirname(__file__), 'userv3settingsTest.json')
#     preferences = Framework.getPreferences(defaultPath=defaultPath, userPath=userPath)
#     print(preferences)

TEST_PATH = r'C:\Users\work\Projects\AnalysisV3\src\python\ccpn\framework\testing\defaultv3settingsTest.json'

KEYS = {'general', 'proxySettings', 'externalPrograms',
        'appearance', 'printSettings', 'recentMacros',
        'shortcuts', 'spectra', 'recentFiles', 'popups',
        '_applicationVersion', '_lastPath'}

class TestDefaultPrefs(WrapperTesting):

    @contextlib.contextmanager
    def initialSetup(self):
        """A more minimal setup which also skips user preferences"""
        self.framework = Framework.createFramework(projectPath=None,
                                                   noLogging=self.noLogging,
                                                   noDebugLogging=self.noDebugLogging,
                                                   noEchoLogging=self.noEchoLogging,
                                                   interface='NoUi',
                                                   skipUserPreferences=True,
                                                   _skipUpdates=True)
        self.project = self.framework.project
        if self.project is None:
            self.tearDown()
            raise RuntimeError(f"No project")

        self.project._resetUndo(debug=True, application=self.framework)
        self.undo = self.project._undo
        self.undo.debug = True
        try:
            yield
        except Exception:
            self.tearDown()

        self.prefs = self.framework.preferences

    def testReadPreferencesFile(self):
        """Test _readPreferencesFile().

        Tests:

        - Reads a file correctly
        - Returns None on a non-existent path
        """
        readPrefs = self.prefs._readPreferencesFile(TEST_PATH)
        self.assertIn('general', readPrefs)
        self.assertIn('colourScheme', readPrefs.general)
        self.assertTrue(readPrefs.general.colourScheme == "dark")

        self.assertIsNone(self.prefs._readPreferencesFile('non/existent/path'))

    def testGetDefaultPreferences(self):
        """Test _getDefaultPreferences().

        Tests all default preference keys are present
        """

        self.prefs._getDefaultPreferences()
        self.assertTrue(self.prefs.keys() == KEYS)

    def testRecursiveUpdate(self):
        """Test _recursiveUpdate().
        Tests loaded values can be changed from an update dict
        """

        gen = self.prefs.general
        updateDict = {'general': {
            "useNative"               : 'true',
            "useNativeWebbrowser"     : 'true',
            }}

        self.assertFalse(gen.useNative)
        self.assertTrue(gen.useNativeWebbrowser)

        self.prefs._recursiveUpdate(self.prefs, updateDict)

        self.assertTrue(gen.useNative)
        self.assertTrue(gen.useNativeWebbrowser)

    def testGet(self):
        """Test get().

        Tests:

        - Will get a 'dotted' value
        - Returns None for non existent key
        - KeyError for non string values and empty strings
        """
        self.assertEqual(self.prefs.get('general.editor'), "default")
        self.assertEqual(self.prefs.get('falseKey'), None)

        with self.assertRaises(KeyError):
            self.prefs.get(4)

        with self.assertRaises(KeyError):
            self.prefs.get('')
