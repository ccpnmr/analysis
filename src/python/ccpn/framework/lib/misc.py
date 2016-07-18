"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": gvuister $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

import sys
import os
import json
from ccpn.util.Time import Time, now, day, week, year

def decode(key, string):
    #string = string.decode()
    decoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        decoded_c = chr(ord(string[i]) - ord(key_c) % 256)
        decoded_chars.append(decoded_c)
    decoded_string = "".join(decoded_chars)
    return decoded_string

cyphers = {}
cyphers['3.0.a3'] = [1468679340.425289, 1468679340.423687]
cyphers['3.0.b1'] = [1468679340.425723, 1468679340.426897]

def _check(key=None, doDecode=True):
    from ccpn.framework.Version import applicationVersion
    
    def message(*chars):
        return ''.join([c for c in map(chr,chars)])
        
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
        lfile = os.path.join(userPreferencesDirectory,fname)
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
            key = decode('ccpnVersion3', key)
        ldict = json.loads(key)
    except:
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    #print(ldict)

    if 'cypher' not in ldict or \
        applicationVersion not in cyphers or \
        ldict['cypher'] not in cyphers[applicationVersion] :
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    if not applicationVersion == ldict['version']:
        sys.stderr.write(message2 % (applicationVersion))
        sys.exit(1)

    if ldict['type'] == 'developer':
        sys.stderr.write(message4 % (ldict['type'], now()+year))
        return True

    valid = Time(ldict['valid'])
    if not now()< valid:
        sys.stderr.write(message3 % (applicationVersion, valid))
        sys.exit(1)
    else:
        sys.stderr.write(message4 % (ldict['type'], valid))

    return True

_checked = _check(None,doDecode=True)


