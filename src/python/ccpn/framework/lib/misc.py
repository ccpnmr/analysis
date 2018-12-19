"""Module Documentation here

"""
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
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import hashlib
import sys
import os
import json
from ccpn.util.Time import Time, now, day, week, year


def _codeFunc(version, valid, licenceType):
    m = hashlib.sha256()
    for value in version, valid, licenceType:
        m.update(bytes(str(value), 'utf-8'))

    return m.hexdigest()


def _decode(key, string):
    #string = string.decode()
    decoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        decoded_c = chr(ord(string[i]) - ord(key_c) % 256)
        decoded_chars.append(decoded_c)
    decoded_string = "".join(decoded_chars)
    return decoded_string


def _check(key=None, doDecode=True):
    from ccpn.framework.Version import applicationVersion

    def message(*chars):
        return ''.join([c for c in map(chr, chars)])

    message1 = message(69, 82, 82, 79, 82, 58, 32, 110, 111, 32, 118, 97, 108, 105, 100,
                       32, 108, 105, 99, 101, 110, 99, 101, 32, 102, 105, 108, 101, 10, 65, 98, 111, 114,
                       116, 105, 110, 103, 32, 112, 114, 111, 103, 114, 97, 109, 10)
    message2 = message(69, 82, 82, 79, 82, 58, 32, 105, 110, 118, 97, 108, 105, 100, 32,
                       108, 105, 99, 101, 110, 99, 101, 32, 102, 111, 114, 32, 65, 110, 97, 108, 121, 115,
                       105, 115, 45, 86, 51, 32, 118, 101, 114, 115, 105, 111, 110, 32, 110, 117, 109, 98,
                       101, 114, 32, 34, 37, 115, 34, 10, 65, 98, 111, 114, 116, 105, 110, 103, 32, 112, 114,
                       111, 103, 114, 97, 109, 10)
    message3 = message(69, 82, 82, 79, 82, 58, 32, 65, 110, 97, 108, 121, 115, 105, 115,
                       45, 86, 51, 32, 118, 101, 114, 115, 105, 111, 110, 32, 110, 117, 109, 98, 101, 114,
                       32, 34, 37, 115, 34, 32, 104, 97, 115, 32, 101, 120, 112, 105, 114, 101, 100, 32, 111,
                       110, 32, 37, 115, 10, 65, 98, 111, 114, 116, 105, 110, 103, 32, 112, 114, 111, 103,
                       114, 97, 109, 10)
    message4 = message(80, 114, 111, 103, 114, 97, 109, 32, 108, 105, 99, 101, 110, 99,
                       101, 32, 40, 37, 115, 41, 32, 118, 97, 108, 105, 100, 32, 117, 110, 116, 105, 108,
                       32, 37, 115, 10)

    if key is None:
        from ccpn.framework.PathsAndUrls import userPreferencesDirectory, ccpnConfigPath

        fname = message(108, 105, 99, 101, 110, 99, 101, 75, 101, 121, 46, 116, 120, 116)
        lfile = os.path.join(userPreferencesDirectory, fname)
        if not os.path.exists(lfile):
            lfile = os.path.join(ccpnConfigPath, fname)
        #print(fname)
        if not os.path.exists(lfile):
            sys.stderr.write(message1)
            sys.exit(1)
        with open(lfile, 'r', encoding='UTF-8') as fp:
            key = fp.readlines()[0]
            fp.close()

    try:
        if doDecode:
            key = _decode('ccpnVersion3', key)
        ldict = json.loads(key)
    except:
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    #print(ldict)

    if 'code' not in ldict or 'version' not in ldict or 'valid' not in ldict or 'licenceType' not in ldict:
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    if applicationVersion != ldict['version']:
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    if ldict['code'] != _codeFunc(ldict['version'], ldict['valid'], ldict['licenceType']):
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    if ldict['licenceType'] == 'developer':
        sys.stderr.write(message4 % (ldict['licenceType'], now() + year))
        return True

    valid = Time(ldict['valid'])
    if not now() < valid:
        sys.stderr.write(message3 % (applicationVersion, valid))
        sys.exit(1)
    else:
        sys.stderr.write(message4 % (ldict['licenceType'], valid))

    return True


_checked = _check(None, doDecode=True)
# _checked = True
