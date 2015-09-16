"""Code to add functions to API defined elsewhere

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

import importlib
import os

from ccpncore.util import Path

# top level of API module
topApiModule = 'ccpncore.api'

# def addModuleFunctionsToApi(moduleName, rootModuleName=None, testRun=True):
#   """ Add the functions in module (recursively including sub-modules) to API.
#       For example, moduleName = 'ccpncore.lib'.
#       It is assumed that moduleName represents a directory rather than a file.
#       rootModuleName should not generally be set by outside code.
#       It is what is chopped off the start of the module being added
#       to the API to get to the API equivalent. """
#
#   if rootModuleName is None:
#     rootModuleName = moduleName
#
#   # unfortunately importing a module does not import its submodules, so we have to
#   # loop over subdirectories to find the submodules rather than just looking at dir(module)
#
#   pythonDirectory = Path.getPythonDirectory()
#   moduleDirectory = os.path.join(pythonDirectory, os.sep.join(moduleName.split('.')))
#
#   for relfile in os.listdir(moduleDirectory):
#
#     for name in ('test', 'Test', '_', '.'):
#       if relfile.startswith(name):
#         break
#     else: # no match with above names, so investigate further
#
#       absfile = os.path.join(moduleDirectory, relfile)
#       if os.path.isdir(absfile):
#         subModuleName = '%s.%s' % (moduleName, relfile)
#         addModuleFunctionsToApi(subModuleName, rootModuleName, testRun=testRun)
#
#       elif relfile.endswith('.py'):
#         subModuleName = '%s.%s' % (moduleName, relfile[:-3])
#         packageName = subModuleName[len(rootModuleName)+1:]  # +1 because of extra '.'
#         apiClass =  _getApiClass(packageName)
#         if apiClass is not None:
#           foundModule = _addModuleFunctionsToApiClass(subModuleName, apiClass)
#
#
#
# def loadLibraryFunctions(packageName, rootModuleName='ccpncore.lib', testRun=True):
#   """Load utility functions into classes - to be run during first import only"""
#   apiClass =  _getApiClass(moduleName, rootModuleName)
#   if apiClass is not None:
#     foundModule = _addModuleFunctionsToApiClass(moduleName, apiClass)
#
# def _getApiClass(packageName):
#
#   # name = moduleName[len(rootModuleName)+1:]  # +1 because of extra '.'
#   components = packageName.split('.')
#   if len(components) > 1:
#     apiModuleName = topApiModule + '.' + '.'.join(components[:-1])
#     apiClassName = components[-1]
#     print ('Try importing: %s %s' % (apiModuleName, apiClassName))
#     try:
#       apiModule = importlib.import_module(apiModuleName)
#       return getattr(apiModule, apiClassName)
#     except ImportError:
#       print('~@~@ Import Failed %s' % apiModuleName)
#       return None
#   else:
#     return None

def _addModuleFunctionsToApiClass(relModuleName, apiClass, rootModuleName='ccpncore.lib'):
  moduleName = '%s.%s' % (rootModuleName, relModuleName)
  try:
    module = importlib.import_module(moduleName)
  except ImportError:
    ll = moduleName.split('.')
    ll[-1] += '.py'
    if os.path.exists(os.path.join(Path.getPythonDirectory(), *ll)):
      # The file exists, so there must be an error we should know about
      raise
    else:
      # This happens when there is just no library code for a class - quite common
      pass
    return

  for key in dir(module):

    if key.startswith('_'):
      continue

    value = getattr(module, key)
    # second condition below excludes functions defined in imported modules (like os, etc.)
    # third condition checks whether this is a function (rather than a class, etc.)
    if hasattr(value, '__module__') and value.__module__ == moduleName and callable(value):
      setattr(apiClass, key, value)

