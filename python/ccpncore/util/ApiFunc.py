"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
"""Code to add functions to API defined elsewhere
"""

import os

from ccpncore.util import Path

from ccpncore.util import Logging
logger = Logging.getLogger()

def addDirectoryFunctionsToApi(directory, rootDirectory=None):

  if not rootDirectory:
    rootDirectory = directory

  relfiles = os.listdir(directory)
  for relfile in relfiles:
    if relfile.startswith('_') or relfile.startswith('.'):
      continue
    absfile = os.path.join(directory, relfile)
    if os.path.isdir(absfile):
      if relfile not in ('testing',):
        addDirectoryFunctionsToApi(absfile, rootDirectory)
    elif os.path.isfile(absfile):
      addFileFunctionsToApi(absfile, rootDirectory) 

def addFileFunctionsToApi(filePath, rootDirectory=None):

  if not rootDirectory:
    rootDirectory = os.path.dirname(filePath)

  # below is a bit hacky but ought to work
  # look for matching modules

  if not filePath.endswith('.py'):
    return

  pythonDirectory = Path.getPythonDirectory()

  if not filePath.startswith(pythonDirectory):
    return

  if not filePath.startswith(rootDirectory):
    return

  n = len(rootDirectory)
  apiPath = filePath[n+1:-3]
  if not apiPath:
    return
  apiComponents = _getPathComponents(apiPath)
  apiClassName = apiComponents[-1]
  apiModuleName = '.'.join(apiComponents[:-1])
  if not apiModuleName:
    return
  apiModuleName = 'ccpncore.api.' + apiModuleName

  n = len(pythonDirectory)
  filePath = filePath[n+1:-3] # remove leading path and remove suffix
  if not filePath:
    return
  fileComponents = _getPathComponents(filePath)
  fileModuleName = '.'.join(fileComponents)

  try:
    apiModule = _getModule(apiModuleName)
    apiClazz = getattr(apiModule, apiClassName)
    fileModule = _getModule(fileModuleName)
    _addModuleFuncsToClass(fileModule, apiClazz)
    logger.debug('Added functions from %s to API' % filePath)
  except Exception as e:
    logger.warning('Error adding functions from %s to API: %s' % (filePath, e))

def _getModule(moduleName):
  """ Gets module in same way as __import__ but for modules of
  form x.y returns x.y not x (as __import__ does)
  """

  components = moduleName.split('.')
  head, tail = components[:-1], components[-1]
  head = '.'.join(head)
  module = __import__(head, globals(), locals(), [tail])
  module = getattr(module, tail)

  return module

def _getPathComponents(filePath):

  (head, tail) = os.path.split(filePath)
  
  if tail:
    components = _getPathComponents(head)
    components.append(tail)
  else:
    components = []

  return components

def _addModuleFuncsToClass(module, clazz):
  """adds functions from module into clazz which are directly in (rather
     than imported into) the module, and which do not start with an underscore"""

  name = module.__name__

  for key in dir(module):

    if key.startswith('_'):
      continue

    value = getattr(module, key)

    if hasattr(value, '__module__') and value.__module__ == name and callable(value):
      setattr(clazz, key, value)
