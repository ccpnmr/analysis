"""Code to add functions to API defined elsewhere

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

import importlib
import os

from ccpn.util import Path

# top level of API module
topApiModule = 'ccpnmodel.ccpncore.api'

def _addModuleFunctionsToApiClass(relModuleName, apiClass, rootModuleName='ccpnmodel.ccpncore.lib'):

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

