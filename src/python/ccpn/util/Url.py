"""Utilities for Url handling
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
__dateModified__ = "$dateModified: 2024-03-20 14:28:21 +0000 (Wed, March 20, 2024) $"
__version__ = "$Revision: 3.2.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

BAD_DOWNLOAD = 'Exception: '
from ccpn.util.Logging import getLogger


def fetchHttpResponse(method, url, data=None, headers=None, proxySettings=None):
    """Generate an http, and return the response
    """
    import os
    import ssl
    import certifi
    import urllib
    from urllib.request import getproxies
    import urllib3

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # create the options list for creating an http connection
    options = {
        'cert_reqs': 'CERT_REQUIRED',
        'ca_certs' : certifi.where(),
        # 'timeout'  : urllib3.Timeout(read=5.0),
        'retries'  : urllib3.Retry(1, redirect=False)
        }

    # check whether a proxy is required
    from ccpn.util.UserPreferences import UserPreferences, USEPROXY, USEPROXYPASSWORD, PROXYADDRESS, \
        PROXYPORT, PROXYUSERNAME, PROXYPASSWORD, USESYSTEMPROXY, VERIFYSSL

    def _getProxyIn(proxyDict):
        """Get the first occurrence of a proxy type in the supplied dict
        """
        # define a list of proxy identifiers
        proxyCheckList = ['HTTPS_PROXY', 'https', 'HTTP_PROXY', 'http']
        for pCheck in proxyCheckList:
            proxyUrl = proxyDict.get(pCheck, None)
            if proxyUrl:
                return proxyUrl

    if proxySettings:
        verifySSL = proxySettings.get(VERIFYSSL)
        if verifySSL:
            options.update(cert_reqs=ssl.CERT_REQUIRED)
        else:
            options.update(cert_reqs=ssl.CERT_NONE)
            urllib3.disable_warnings()
            getLogger().warning('SSL certificates validity check skipped.')

    if proxySettings and proxySettings.get(USEPROXY):

        # Use the user settings if set
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
        proxyUrl = "http://%s:%s/" % (str(proxyAddress), str(proxyPort)) if proxyAddress else None

    else:
        # read the environment/system proxies if exist
        proxyUrl = _getProxyIn(os.environ) or _getProxyIn(urllib.request.getproxies())

        # ED: issues - @"HTTPProxyAuthenticated" key on system?. If it exists, the value is a boolean (NSNumber) indicating whether or not the proxy is authentified,
        # get the username if the proxy is authenticated: check @"HTTPProxyUsername"

    # proxy may still not be defined
    if proxyUrl:
        http = urllib3.ProxyManager(proxyUrl, **options)
    else:
        http = urllib3.PoolManager(**options)

    try:
        # generate an http request
        response = http.request(method, url,
                                fields=data,
                                headers=headers,
                                # body=body,
                                # preload_content=True,
                                # decode_content=False
                                )

        # return the http response
        return response

    except Exception as es:
        getLogger().warning(f'Error getting connection - {es}')


def fetchUrl(url, data=None, headers=None, timeout=5, proxySettings=None, decodeResponse=True):
    """Fetch url request from the server
    """
    import logging
    from ccpn.core.lib.ContextManagers import Timeout as timer
    from ccpn.util.Common import isWindowsOS

    timeoutMessage = 'Could not connect to server. Check connection'
    if isWindowsOS():
        # Windows does not have signal.SIGALRM - temporary fix
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.CRITICAL)

        if not proxySettings:

            # read the proxySettings from the preferences
            from ccpn.util.UserPreferences import UserPreferences

            _userPreferences = UserPreferences(readPreferences=True)
            if _userPreferences.proxyDefined:
                proxyNames = ['useProxy', 'proxyAddress', 'proxyPort', 'useProxyPassword',
                              'proxyUsername', 'proxyPassword', 'verifySSL']
                proxySettings = {}
                for name in proxyNames:
                    proxySettings[name] = _userPreferences._getPreferencesParameter(name)

        response = fetchHttpResponse('POST', url, data=data, headers=headers,
                                     proxySettings=proxySettings)

    else:
        # use the timeout limited call
        with timer(seconds=timeout or 5, timeoutMessage=timeoutMessage):
            urllib3_logger = logging.getLogger('urllib3')
            urllib3_logger.setLevel(logging.CRITICAL)

            if not proxySettings:

                # read the proxySettings from the preferences
                from ccpn.util.UserPreferences import UserPreferences

                _userPreferences = UserPreferences(readPreferences=True)
                if _userPreferences.proxyDefined:
                    proxyNames = ['useProxy', 'proxyAddress', 'proxyPort', 'useProxyPassword',
                                  'proxyUsername', 'proxyPassword', 'verifySSL']
                    proxySettings = {}
                    for name in proxyNames:
                        proxySettings[name] = _userPreferences._getPreferencesParameter(name)

            response = fetchHttpResponse('POST', url, data=data, headers=headers,
                                         proxySettings=proxySettings)

    if response:
        return response.data.decode('utf-8') if decodeResponse else response


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
    """Check whether an internet conection is available by testing the CCPN weblink
    """
    from ccpn.framework.PathsAndUrls import ccpnUrl

    try:
        fetchUrl('/'.join([ccpnUrl, 'cgi-bin/checkInternet']))
        return True

    except Exception as es:
        getLogger().exception(es)
        return False
