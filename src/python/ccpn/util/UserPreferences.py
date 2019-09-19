"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import json
from ccpn.util import Path
from ccpn.util.AttrDict import AttrDict


# CCPN code
ccpnCodePath                    = Path.getTopDirectory()
ccpnConfigPath                  = os.path.join(ccpnCodePath, 'config')
defaultPreferencesPath          = os.path.join(ccpnConfigPath, 'defaultv3settings.json')

# User settings
userPreferencesDirectory        = os.path.expanduser('~/.ccpn')
userPreferencesPath             = os.path.join(userPreferencesDirectory,'v3settings.json')


def getPreferences(skipUserPreferences=False, defaultPath=None, userPath=None):
    """Read the preferences file and merge with user specific preferences
    """
    try:
        def _updateDict(d, u):
            import collections

            # recursive update of dictionary
            # this deletes every key in u that is not in d
            # if we want every key regardless, then remove first if check below
            for k, v in u.items():
                if k not in d:
                    continue
                if isinstance(v, collections.Mapping):
                    r = _updateDict(d.get(k, {}), v)
                    d[k] = r
                else:
                    d[k] = u[k]
            return d

        # read the default settings
        preferencesPath = (defaultPath if defaultPath else defaultPreferencesPath)
        with open(preferencesPath) as fp:
            preferences = json.load(fp, object_hook=AttrDict)

        # read user settings and update if not skipped
        if not skipUserPreferences:
            # from ccpn.framework.PathsAndUrls import userPreferencesPath

            preferencesPath = (userPath if userPath else os.path.expanduser(userPreferencesPath))
            if os.path.isfile(preferencesPath):
                with open(preferencesPath) as fp:
                    userPreferences = json.load(fp, object_hook=AttrDict)
                preferences = _updateDict(preferences, userPreferences)
    except:  #should we have the preferences hard coded as py dict for extra safety? if json goes wrong the whole project crashes!
        with open(defaultPreferencesPath) as fp:
            preferences = json.load(fp, object_hook=AttrDict)

    return preferences


def _message(*chars):
    return ''.join([c for c in map(chr, chars)])
ENCRYPTEDLIST = (_message(112, 114, 111, 120, 121, 80, 97, 115, 115, 119, 111, 114, 100),)
USERKEY = _message(117, 115, 101, 114, 75, 101, 121)


class UserPreferences():
    """
    Class to handle reading user information from the preferences file
    """
    def __init__(self, readPreferences=True):
        self._readPreferences = readPreferences
        self._preferences = getPreferences(False) if readPreferences else None

    def _getPreferencesParameter(self, name):
        """Return a paramter from the preferences file
        """
        value = getattr(self._preferences, name, None)
        if value and name in ENCRYPTEDLIST:
            return self._decode(USERKEY, value)

        return value

    def _setPreferencesParameter(self, name, value):
        """Set a parameter in the preferences file
        """

    def setProxyFromCommandLine(self):
        pass

    def _decode(self, key, string):
        try:
            decoded_chars = []
            for i in range(len(string)):
                key_c = key[i % len(key)]
                decoded_c = chr(ord(string[i]) - ord(key_c) % 256)
                decoded_chars.append(decoded_c)
            decoded_string = "".join(decoded_chars)
            return decoded_string
        except:
            return ''

    def _encode(self, key, string):
        try:
            encoded_chars = []
            for i in range(len(string)):
                key_c = key[i % len(key)]
                encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
                encoded_chars.append(encoded_c)
            encoded_string = "".join(encoded_chars)
            #return encoded_string.encode()
            return encoded_string
        except:
            return ''

    def decodeValue(self, string):
        """Decode a user value
        """
        if not isinstance(string, str):
            return None
        return self._decode(USERKEY, string)

    def encodeValue(self, string):
        """Encode a user value
        """
        if not isinstance(string, str):
            return None
        return self._encode(USERKEY, string)
