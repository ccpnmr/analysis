"""
This file contains the Preference object and related methods;
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-05 15:09:56 +0000 (Sat, February 05, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json

from ccpn.util.AttrDict import AttrDict
from ccpn.util.decorators import singleton
from ccpn.util.Path import Path, aPath
from ccpn.util.Common import uniquify

from ccpn.framework.PathsAndUrls import \
    userPreferencesPath, \
    userPreferencesDirectory, \
    defaultPreferencesPath

from ccpn.framework.Application import getApplication

ARIA_PATH ='externalPrograms.aria'
CYANA_PATH ='externalPrograms.cyana'
XPLOR_NIH_PATH = 'externalPrograms.xplor'
TALOS_PATH ='externalPrograms.talos'
PYMOL_PATH = 'externalPrograms.pymol'

USER_DATA_PATH = 'general.dataPath'
USER_MACRO_PATH = 'general.userMacroPath'
USER_PLUGIN_PATH = 'general.userPluginPath'
USER_PIPES_PATH = 'general.userPipesPath'
USER_LAYOUTS_PATH = 'general.userLayoutsPath'

PRINT_OPTIONS = 'printSettings.printOptions'

USE_PROJECT_PATH = 'general.useProjectPath'


def getPreferences():
    """Return the Preferences instance"""
    if (app := getApplication()) is None:
        raise RuntimeError('getPreferences: application has not registered itself!')
    return app.preferences


@singleton
class Preferences(AttrDict):
    """A singleton class to hold the preferences,
    implemented as a AttrDict of AttrDict of AttrDict
    """

    def __init__(self, application):
        super().__init__()

        self._applicationVersion = str(application.applicationVersion)
        self._lastPath = None

        if not userPreferencesPath.exists():
            userPreferencesDirectory.mkdir()

        # read the default preference and populate self so all valid keys
        # are defined
        _prefs = self._readPreferencesFile(defaultPreferencesPath)
        self.update(_prefs)

    def _readPreferencesFile(self, path):
        """Read the preference from the json file path,
        :return the json encoded preferences object
        """
        path = aPath(path)
        if not path.exists():
            raise ValueError('Preferences._readPreferences: path %s does not exist' % path)

        with path.open(mode='r') as fp:
            _prefs = json.load(fp, object_hook=AttrDict)
        self._lastPath = str(path)
        return _prefs

    def _getUserPreferences(self):
        """Read the user preferences file, updating the current values
        """
        _prefs = self._readPreferencesFile(userPreferencesPath)
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
            raise ValueError('Preferences._recursiveUpdate: invalid dict  %s' % theDict )

        if not isinstance(updateDict, (dict, AttrDict)):
            raise ValueError('Preferences._recursiveUpdate: invalid updateDict  %s' % updateDict )

        for key, value in theDict.items():
            # check and update for any keys in theDict that are in updateDict
            if key in updateDict:
                updateValue = updateDict[key]

                if isinstance(value, (dict, AttrDict)):
                    self._recursiveUpdate(value, updateValue)

                else:
                    theDict[key] = updateValue

    dashes = '-'*5
    def _recursivePrint(self, theDict, keys=None):
        """print (key, value) of theDict, recursively expanding key for dict-like value's
        """
        if keys is None:
            keys = []

        for key, value in theDict.items():
            _keys = keys[:] + [key]

            if isinstance(value, AttrDict) and len(_keys) < 2:
                self._recursivePrint(value, keys=_keys )

            else:
                _keyStr = '.'.join(_keys)
                print('%-40s : %r' % (_keyStr, value))  \

    def get(self, key, default=None):
        """Return the value for key if key is in the dictionary, else default.
        Check for key to be a "dotted" one; e.g. "aap.noot" If so, recusively
        decent.
        """
        if key is None or not isinstance(key, str) or len(key) == 0:
            raise KeyError('invalid key %r' % key)

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
            raise KeyError('invalid key %r; unable to decode' % key)

    def print(self):
        """Print items of self
        """
        print(self.dashes, self, self.dashes)
        self._recursivePrint(self)

    def __str__(self):
        return '<Preferences: %r>' % self._lastPath



