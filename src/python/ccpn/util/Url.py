"""Utilities for Url handling
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

def fetchUrl(url, data=None, headers=None, timeout=None):

  import urllib
  import urllib.parse
  import urllib.request

  if not headers:
    headers = {}

  if data:
    data = urllib.parse.urlencode(data)
    data = data.encode('utf-8')
  else:
    data = None
    
  request = urllib.request.Request(url, data, headers)
  response = urllib.request.urlopen(request, timeout=timeout)
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


