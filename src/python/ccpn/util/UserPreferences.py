"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-01-05 14:36:48 +0000 (Thu, January 05, 2023) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-07-20 19:12:45 +0000 (Tue, July 20, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import json
from ccpn.util.AttrDict import AttrDict
from ccpn.framework.PathsAndUrls import defaultPreferencesPath, userPreferencesPath


USEPROXY = 'useProxy'
USESYSTEMPROXY = 'useSystemProxy'
USEPROXYPASSWORD = 'useProxyPassword'
PROXYADDRESS = 'proxyAddress'
PROXYPORT = 'proxyPort'
PROXYUSERNAME = 'proxyUsername'
PROXYPASSWORD = 'proxyPassword'
VERIFYSSL = 'verifySSL'


def getPreferences(skipUserPreferences=False, defaultPath=None, userPath=None):
    """Read the preferences file and merge with user specific preferences
    """
    try:
        def _updateDict(d, u):
            import collections.abc

            # recursive update of dictionary
            # this deletes every key in u that is not in d
            # if we want every key regardless, then remove first if check below
            for k, v in u.items():
                if k not in d:
                    continue
                if isinstance(v, collections.abc.Mapping):
                    r = _updateDict(d.get(k, {}), v)
                    d[k] = r
                else:
                    d[k] = u[k]
            return d

        # read the default settings
        preferencesPath = defaultPath or defaultPreferencesPath
        with open(preferencesPath) as fp:
            preferences = json.load(fp, object_hook=AttrDict)

        # read user settings and update if not skipped
        if not skipUserPreferences:
            # from ccpn.framework.PathsAndUrls import userPreferencesPath

            preferencesPath = userPath or os.path.expanduser(userPreferencesPath)
            if os.path.isfile(preferencesPath):
                with open(preferencesPath) as fp:
                    userPreferences = json.load(fp, object_hook=AttrDict)
                preferences = _updateDict(preferences, userPreferences)
    except Exception:  #should we have the preferences hard coded as py dict for extra safety? if json goes wrong the whole project crashes!
        with open(defaultPreferencesPath) as fp:
            preferences = json.load(fp, object_hook=AttrDict)

    return preferences


def _message(*chars):
    return ''.join(list(map(chr, chars)))


ENCRYPTEDLIST = (_message(112, 114, 111, 120, 121, 80, 97, 115, 115, 119, 111, 114, 100),)
USERKEY = _message(117, 115, 101, 114, 75, 101, 121)


class UserPreferences():
    """
    Class to handle reading user information from the preferences file
    """

    def __init__(self, readPreferences=True):
        self._readPreferences = readPreferences
        self._preferences = getPreferences(False) if readPreferences else None

    @property
    def proxyDefined(self):
        """Return True if the settings contains the USEPROXY attribute
        """
        if self._preferences and self._preferences.proxySettings:
            return hasattr(self._preferences.proxySettings, USEPROXY)

    def _getPreferencesParameter(self, name):
        """Return a parameter from the preferences file
        """
        if self._preferences and self._preferences.proxySettings:
            return getattr(self._preferences.proxySettings, name, None)

    def _setPreferencesParameter(self, name, value):
        """Set a parameter in the preferences file
        """

    def setProxyFromCommandLine(self):
        pass

    @staticmethod
    def _decode(key, string):
        try:
            decoded_chars = []
            for i in range(len(string)):
                key_c = key[i % len(key)]
                decoded_c = chr(ord(string[i]) - ord(key_c) % 256)
                decoded_chars.append(decoded_c)
            return ''.join(decoded_chars)

        except Exception:
            return ''

    @staticmethod
    def _encode(key, string):
        try:
            encoded_chars = []
            for i in range(len(string)):
                key_c = key[i % len(key)]
                encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
                encoded_chars.append(encoded_c)
            return ''.join(encoded_chars)

        except Exception:
            return ''

    def decodeValue(self, string):
        """Decode a user value
        """
        return self._decode(USERKEY, string) if isinstance(string, str) else None

    def encodeValue(self, string):
        """Encode a user value
        """
        return self._encode(USERKEY, string) if isinstance(string, str) else None
