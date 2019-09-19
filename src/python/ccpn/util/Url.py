"""Utilities for Url handling
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
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

BAD_DOWNLOAD = 'Exception: '


def fetchHttpResponse(method, url, data=None, headers=None, proxySettings=None):
    """Generate an http, and return the response
    """
    import ssl
    import certifi
    import urllib3.contrib.pyopenssl
    from urllib.parse import urlencode, quote

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    if not headers:
        headers = {'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8'}
    body = urlencode(data, quote_via=quote).encode('utf-8') if data else None

    urllib3.contrib.pyopenssl.inject_into_urllib3()

    # create the options list for creating an http connection
    options = {'cert_reqs': 'CERT_REQUIRED',
               'ca_certs' : certifi.where(),
               'timeout'  : urllib3.Timeout(connect=3.0, read=3.0),
               'retries'  : urllib3.Retry(1, redirect=False)
               }

    # check whether a proxy is required
    from ccpn.util.UserPreferences import UserPreferences, USEPROXY, USEPROXYPASSWORD, PROXYADDRESS, \
        PROXYPORT, PROXYUSERNAME, PROXYPASSWORD

    if proxySettings and proxySettings.get(USEPROXY):

        useProxyPassword = proxySettings.get(USEPROXYPASSWORD)
        proxyAddress = proxySettings.get(PROXYADDRESS)
        proxyPort = proxySettings.get(PROXYPORT)
        proxyUsername = proxySettings.get(PROXYUSERNAME)
        proxyPassword = proxySettings.get(PROXYPASSWORD)

        if useProxyPassword:
            # grab the decode from the userPreferences
            _userPreferences = UserPreferences(readPreferences=False)

            options.update({'headers': urllib3.make_headers(proxy_basic_auth='%s:%s' %
                                                                             (proxyUsername,
                                                                              _userPreferences.decodeValue(proxyPassword)))})

        http = urllib3.ProxyManager("http://%s:%s/" % (str(proxyAddress), str(proxyPort)),
                                    **options)

    else:
        http = urllib3.PoolManager(**options)

    # generate an http request
    response = http.request(method, url,
                            headers=headers,
                            body=body,
                            preload_content=False)

    return response


def fetchUrl(url, data=None, headers=None, timeout=None, proxySettings=None):
    """Fetch url request from the server
    """
    # import urllib3.contrib.pyopenssl
    # from urllib.parse import urlencode, quote
    # import certifi
    # import ssl
    import logging

    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.CRITICAL)

    response = fetchHttpResponse('POST', url, data=data, headers=None, proxySettings=proxySettings)

    # print('>>>>>>response', proxySettings, response.data.decode('utf-8'))
    return response.data.decode('utf-8')


def uploadFile(url, fileName, data=None):
    import os

    if not data:
        data = {}

    with open(fileName, 'rb') as fp:
        fileData = fp.read()

    data['fileName'] = os.path.basename(fileName)
    data['fileData'] = fileData

    try:
        return fetchUrl(url, data)
    except:
        return None


def checkInternetConnection():
    from ccpn.framework.PathsAndUrls import ccpnUrl
    import os.path

    try:
        fetchUrl(os.path.join(ccpnUrl, 'cgi-bin/checkInternet'))
        return True

    except Exception as es:
        return False
