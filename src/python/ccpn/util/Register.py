"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import ast
import hashlib
import os
import sys
import uuid
import datetime
from ccpn.util import Logging
from ccpn.util import Url
import json
import platform
import re, uuid

from ccpn.framework.PathsAndUrls import ccpn2Url, userPreferencesDirectory, ccpnConfigPath

userAttributes = ('name', 'organisation', 'email')


def _registrationPath():
    return os.path.expanduser('~/.ccpn/register.txt')


def _registrationServerScript():
    return ccpn2Url + '/cgi-bin/register/updateRegistrationV3'


def _checkRegistrationServerScript():
    return ccpn2Url + '/cgi-bin/register/checkRegistrationV3'


def loadDict():
    path = _registrationPath()

    registrationDict = {}
    try:
        if os.path.isfile(path):
            with open(path) as fp:
                data = fp.read()
                registrationDict = ast.literal_eval(data)
    except Exception as e:
        sys.stderr.write('Error loading registration: %s\n' % e)

    return registrationDict


def saveDict(registrationDict):
    path = _registrationPath()
    directory = os.path.dirname(path)

    try:
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as fp:
            fp.write(str(registrationDict))
    except Exception as e:
        sys.stderr.write('Error saving registration: %s\n' % e)


def getHashCode(registrationDict):
    m = hashlib.md5()
    for attrib in userAttributes:
        value = registrationDict.get(attrib, '')
        m.update(value.encode('utf-8'))

    return m.hexdigest()


def setHashCode(registrationDict):
    registrationDict['hashcode'] = getHashCode(registrationDict)


def _build(*chars):
    return ''.join([c for c in map(chr, chars)])
_bF = _build(98, 117, 105, 108, 100, 70, 111, 114)
_hc = _build(104, 97, 115, 104, 99, 111, 100, 101)
_cS = _build(99, 104, 101, 99, 107, 83, 117, 109)
_nP = _build(110, 111, 110, 45, 112, 114, 111, 102, 105, 116)
_otherAttributes = (_hc, )


def _insertRegistration(registrationDict):
    val0, _, _, val1 = _getBuildID()
    return {_bF: val0, _cS: val1}


def isNewRegistration(registrationDict):
    for attrib in userAttributes:
        if not registrationDict.get(attrib):
            return True

    if _hc not in registrationDict:
        return True

    hashcode = getHashCode(registrationDict)

    return hashcode != registrationDict[_hc]


def updateServer(registrationDict, version='3'):
    url = _registrationServerScript()

    values = {}
    for attr in userAttributes + (_hc, ):
        value = []
        for c in registrationDict[attr]:
            value.append(c if 32 <= ord(c) < 128 else '_')
        values[attr] = ''.join(value)

    values['version'] = str(version)
    values['OSversion'] = platform.platform()
    values['systemInfo'] = ';'.join(platform.uname())
    values['ID'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    values['compileVersion'] = _getCompileVersion()
    var0, var1, var2, _ = _getBuildID()
    values[_build(98, 117, 105, 108, 100, 70, 111, 114)] = var0
    values[_build(108, 105, 99, 101, 110, 99, 101, 84, 121, 112, 101)] = var1
    values[_build(108, 105, 99, 101, 110, 99, 101, 73, 68)] = var2

    try:
        return Url.fetchUrl(url, values, timeout=2.0)
    except Exception as e:
        logger = Logging.getLogger()
        logger.warning('Could not update registration on server.')


def _getCompileVersion():
    """Get the compileVersion information from the compileVersion file
    """
    COMPILEVERSIONFILE = 'compileVersion.txt'

    lfile = os.path.join(ccpnConfigPath, COMPILEVERSIONFILE)
    if not os.path.exists(lfile):
        return 'noCompileVersionInformation'

    with open(lfile, 'r', encoding='UTF-8') as fp:
        try:
            # return the first line of the compileVersion information file - should be created by ./buildDistribution
            return fp.readlines()[0]
        except:
            return 'badCompileVersionInformation'


def _checkLicenceScript():
    return ccpn2Url + '/cgi-bin/register/checkLicence'


def _getBuildID():
    from ccpn.util import Data

    vals = []
    for val in (_build(98, 117, 105, 108, 100, 70, 111, 114), _build(108, 105, 99, 101, 110, 99, 101, 84, 121, 112, 101),
                _build(108, 105, 99, 101, 110, 99, 101, 73, 68), _build(99, 104, 101, 99, 107, 83, 117, 109)):
        vals.append(getattr(Data, val, ''))

    return vals[0], vals[1], vals[2], vals[3]

def checkServer(registrationDict, version='3'):
    """Check the registration status on the server
    """
    url = _checkRegistrationServerScript()

    values = {}
    for attr in userAttributes + (_hc, ):
        value = []
        if attr in registrationDict:
            for c in registrationDict[attr]:
                value.append(c if 32 <= ord(c) < 128 else '_')
            values[attr] = ''.join(value)

    values['version'] = str(version)
    values['OSversion'] = platform.platform()
    values['systemInfo'] = ';'.join(platform.uname())
    values['ID'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    values['compileVersion'] = _getCompileVersion()
    var0, var1, var2, _ = _getBuildID()
    values[_build(98, 117, 105, 108, 100, 70, 111, 114)] = var0
    values[_build(108, 105, 99, 101, 110, 99, 101, 84, 121, 112, 101)] = var1
    values[_build(108, 105, 99, 101, 110, 99, 101, 73, 68)] = var2

    try:
        found = Url.fetchUrl(url, values, timeout=2.0)
        # print('>>>>>>', found)
        return found.strip() == 'OK'

    except Exception as e:
        logger = Logging.getLogger()
        logger.warning('Could not check registration on server.')


def checkInternetConnection():
    try:
        return Url.checkInternetConnection()

    except:
        return False

def _fetchGraceFile(application):
    """
    :return: grace filepath used as time stamp
    """
    msg = 'If you are modifying this file it means you are a computer savvy! Please register and contribute to the project.'
    v = application.applicationVersion
    f = 'grace.json'
    path = os.path.join(userPreferencesDirectory,v+f)
    if not os.path.exists(path):

        with open(path, "w") as file:
            json.dump(msg, file)

        return path
    else:
        return path



def _graceCounter(apath, d=5):
    """

    :param path: a file which was created when the program (version) was started for the first time
    :param d: days of grace
    :return: days left
    """

    today = datetime.datetime.today()
    modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(apath))
    duration = today - modified_date
    return d - duration.days