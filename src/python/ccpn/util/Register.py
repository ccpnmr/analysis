"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import ast
import hashlib
import os
import uuid

from ccpn.util import Logging

from ccpn.util import Url

userAttributes = ('name', 'organisation', 'email')

def _registrationPath():

  return os.path.expanduser('~/.ccpn/register.txt')

def _registrationServerScript():

  return 'http://www2.ccpn.ac.uk/cgi-bin/register/registerV3'

def loadDict():

  path = _registrationPath()

  registrationDict = {}
  try:
    # if os.path.exists(path) and os.path.isfile(path):
    # exists call is reduncant with isfile call
    if os.path.isfile(path):
      data = fp = open(path)
      data = fp.read()
      fp.close()
      registrationDict = ast.literal_eval(data)
  except:
    pass

  return registrationDict

def saveDict(registrationDict):

  path = _registrationPath()

  try:
    fp = open(path, 'w')
    fp.write(str(registrationDict))
    fp.close()
  except:
    pass

def getHashCode(registrationDict):
  
  macAddress = uuid.getnode()

  m = hashlib.md5()
  for attrib in userAttributes:
    value = registrationDict.get(attrib, '')
    m.update(value.encode('utf-8'))

  return m.hexdigest()
  
def setHashCode(registrationDict):
  
  registrationDict['hashcode'] = getHashCode(registrationDict)
  
def isNewRegistration(registrationDict):
  
  if 'hashcode' not in registrationDict:
    return True
    
  hashcode = getHashCode(registrationDict)
  
  return hashcode != registrationDict['hashcode']
  
def updateServer(registrationDict, version='3'):

  url = _registrationServerScript()

  values = {}
  for attr in userAttributes + ('hashcode',):
    value = []
    for c in registrationDict[attr]:
      value.append(c if 32 <= ord(c) < 128 else '_')
    values[attr] = ''.join(value)

  values['version'] = str(version)
  
  try:
    return Url.fetchUrl(url, values, timeout=2.0)
  except Exception as e:
    logger = Logging.getLogger()
    logger.warning('Could not update registration on server: %s' % e)


