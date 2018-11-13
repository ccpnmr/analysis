
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

loadedPipes = []

import pkgutil as _pkgutil
for loader, name, isPpkg in _pkgutil.walk_packages(__path__):
  module = loader.find_module(name).load_module(name)




# def _pipeLoader():
#   loadedPipes = []
#
#   from ccpn.framework.lib.Pipe import Pipe
#   import pkgutil as _pkgutil
#   import inspect as _inspect
#
#   for loader, name, isPpkg in _pkgutil.walk_packages(__path__):
#     module = loader.find_module(name).load_module(name)
#     for name, obj in _inspect.getmembers(module):
#         if hasattr(obj, 'runPipe'):
#           if isinstance(obj, Pipe):
#             loadedPipes.append(obj)
#
#
#   return loadedPipes
