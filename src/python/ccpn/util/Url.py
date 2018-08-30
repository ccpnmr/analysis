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

  import sys
  import urllib
  import urllib.parse
  import urllib.request
  import ssl

  # This restores the same behavior as before.
  context = ssl._create_unverified_context()

  if not headers:
    headers = {}

  if data:
    data = urllib.parse.urlencode(data)
    data = data.encode('utf-8')
  else:
    data = None

  request = urllib.request.Request(url, data, headers)
  response = urllib.request.urlopen(request, timeout=timeout, context=context)
  result = response.read().decode('utf-8')

  # TESTING
  print('>>>REGISTER', result)
  sys.exit()

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


