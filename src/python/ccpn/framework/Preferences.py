"""
This file contains the Preference object and related methods;
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-05-10 18:58:37 +0100 (Fri, May 10, 2024) $"
__version__ = "$Revision: 3.2.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json

from ccpn.ui.gui.guiSettings import FONTLIST
from ccpn.util.AttrDict import AttrDict
from ccpn.util.decorators import singleton
from ccpn.util.Path import aPath
from ccpn.util.Common import uniquify, isMacOS, isLinux

from ccpn.framework.PathsAndUrls import (userPreferencesPath,
                                         userPreferencesDirectory,
                                         defaultPreferencesPath)
from ccpn.framework.Application import getApplication


ARIA_PATH = 'externalPrograms.aria'
CYANA_PATH = 'externalPrograms.cyana'
XPLOR_NIH_PATH = 'externalPrograms.xplor'
TALOS_PATH = 'externalPrograms.talos'
PYMOL_PATH = 'externalPrograms.pymol'

USER_DATA_PATH = 'general.dataPath'
USER_MACRO_PATH = 'general.userMacroPath'
USER_PLUGIN_PATH = 'general.userPluginPath'
USER_PIPES_PATH = 'general.userPipesPath'
USER_LAYOUTS_PATH = 'general.userLayoutsPath'

PRINT_OPTIONS = 'printSettings.printOptions'
USE_PROJECT_PATH = 'general.useProjectPath'
APPEARANCE = 'appearance'


def getPreferences():
    """Return the Preferences instance"""
    if (app := getApplication()) is None:
        raise RuntimeError('getPreferences: application has not registered itself!')
    return app.preferences


@singleton
class Preferences(AttrDict):
    """A singleton class to hold the preferences,
    implemented as a AttrDict-of-AttrDict-of-AttrDict
    """

    def __init__(self, application):
        super().__init__()

        self._applicationVersion = str(application.applicationVersion)
        self._lastPath = None

        if not userPreferencesDirectory.exists():
            userPreferencesDirectory.mkdir()

        # read the default preference and populate self so all valid keys
        # are defined
        if not (_prefs := self._readPreferencesFile(defaultPreferencesPath)):
            raise ValueError(f'Preferences._readPreferences: path {defaultPreferencesPath} does not exist')

        self.update(_prefs)

    def _readPreferencesFile(self, path):
        """Read the preference from the json file path,
        :return the json encoded preferences object
        """
        path = aPath(path)
        if not path.exists():
            return None

        with path.open(mode='r') as fp:
            _prefs = json.load(fp, object_hook=AttrDict)

        self._lastPath = str(path)

        self._overrideDefaults(_prefs)

        return _prefs

    def _getUserPreferences(self):
        """Read the user preferences file, updating the current values
        """
        if (_prefs := self._readPreferencesFile(userPreferencesPath)):
            self._recursiveUpdate(theDict=self, updateDict=_prefs)

        # just some patches to the data
        self.recentMacros = uniquify(self.recentMacros)

    def _saveUserPreferences(self):
        """Save the current preferences to the user preferences file
        """
        with userPreferencesPath.open(mode='w') as fp:
            json.dump(self, fp, indent=4)

    def _recursiveUpdate(self, theDict, updateDict):
        """update theDict with key,value from updateDict, if key exists in theDict
        Recursively update, by expanding any dict-like value first
        """
        if not isinstance(theDict, (dict, AttrDict)):
            raise ValueError(f'Preferences._recursiveUpdate: invalid dict  {theDict}')

        if not isinstance(updateDict, (dict, AttrDict)):
            raise ValueError(f'Preferences._recursiveUpdate: invalid updateDict  {updateDict}')

        for key, value in theDict.items():
            # check and update for any keys in theDict that are in updateDict
            if key in updateDict:
                updateValue = updateDict[key]

                if isinstance(value, (dict, AttrDict)):
                    self._recursiveUpdate(value, updateValue)

                else:
                    theDict[key] = updateValue

    dashes = '-' * 5

    def _recursivePrint(self, theDict, keys=None):
        """print (key, value) of theDict, recursively expanding key for dict-like value's
        """
        if keys is None:
            keys = []

        for key, value in theDict.items():
            _keys = keys[:] + [key]

            if isinstance(value, AttrDict) and len(_keys) < 2:
                self._recursivePrint(value, keys=_keys)

            else:
                _keyStr = '.'.join(_keys)
                print(f'{_keyStr:40} : {repr(value)}')

    def get(self, key, default=None):
        """Return the value for key if key is in the dictionary, else default.
        Check for key to be a "dotted" one; e.g. "aap.noot" If so, recusively
        decent.
        """
        if key is None or not isinstance(key, str) or len(key) == 0:
            raise KeyError(f'invalid key {repr(key)}')

        _keys = key.split('.')
        _value = AttrDict.get(self, _keys[0], default)

        if _value is None or \
                len(_keys) == 1 or \
                len(_keys) > 1 and len(_keys[1]) == 0:
            return _value

        elif isinstance(_value, (dict, AttrDict)):
            # Re
            return Preferences.get(_value, '.'.join(_keys[1:]), default=default)

        else:
            raise KeyError(f'invalid key {repr(key)}; unable to decode')

    def print(self):
        """Print items of self
        """
        print(self.dashes, self, self.dashes)
        self._recursivePrint(self)

    def __str__(self):
        return f'<Preferences: {repr(self._lastPath)}>'

    @staticmethod
    def _overrideDefaults(prefs):
        """Override any settings that are currently causing problems
        """
        # NOTE:ED - there is a bug in pyqt5.12.3 that causes a crash when using QWebEngineView
        prefs.general.useNativeWebbrowser = True
        if (pr := prefs.get(APPEARANCE)) is None:
            # appearance is not in very early settings
            return

        pr.useOnlineDocumentation = False
        # if the fonts have not been defined, copy from the OS-specific settings
        if isMacOS():
            fontPrefix = 'MacOS'
        elif isLinux():
            fontPrefix = 'Linux'
        else:
            fontPrefix = 'MS'
        # iterate through the current fonts
        for fontNum, fontName in enumerate(FONTLIST):
            prefFont = f'font{fontNum}'
            frmFont = f'{fontPrefix}{prefFont}'
            # set from the default for the OS-specific
            if not pr.get(prefFont):
                pr[prefFont] = pr.get(frmFont, '')
