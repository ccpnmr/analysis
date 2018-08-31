"""Utilities for Url handling
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
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"


#=========================================================================================
# Start of code
#=========================================================================================

def fetchUrl(url, data=None, headers=None, timeout=None):
    import urllib
    import urllib.parse
    import urllib.request
    import ssl

    # testing urllib3 - not needed yet as server is not passing through POST body
    # import sys
    # import urllib3

    # import urllib3.contrib.pyopenssl
    # import certifi
    # import json
    #
    # urllib3.contrib.pyopenssl.inject_into_urllib3()
    # http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
    #                            ca_certs=certifi.where(),
    #                            timeout=urllib3.Timeout(connect=5.0, read=5.0),
    #                            retries=urllib3.Retry(3, redirect=False))
    # response = http.request('POST', url,
    #                         headers={'Content-Type': 'application/json'},
    #                         body=json.dumps(data),
    #                         preload_content=False)
    # print('>>>REGISTERurllib3', response.read().decode('utf-8'))

    if not headers:
        headers = {}

    if data:
        data = urllib.parse.urlencode(data)
        data = data.encode('utf-8')
    else:
        data = None

    # This restores the same behavior as before.
    context = ssl._create_unverified_context()

    # edit - added data to url as server not passing through POST data
    request = urllib.request.Request(url+'?'+str(data), data, headers)
    response = urllib.request.urlopen(request, timeout=timeout, context=context)
    result = response.read().decode('utf-8')

    return result


def uploadFile(url, fileName, data=None):
    import os

    if not data:
        data = {}

    fp = open(fileName, 'rb')
    fileData = fp.read()
    fp.close()

    data['fileName'] = os.path.basename(fileName)
    data['fileData'] = fileData

    return fetchUrl(url, data)
