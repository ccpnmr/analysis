#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-15 16:28:43 +0000 (Fri, May 15, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-15 16:28:42 +0000 (Fri, May 15, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


''' Testing functions to restore ccpn module layout. NB under development '''



def _ccpnModulesImporter(path):
  '''
  :param path: fullPath of the directory where are located the CcpnModules files
  :return: list of CcpnModule classes
  '''
  _ccpnModules = []
  import pkgutil as _pkgutil
  import inspect as _inspect
  from ccpn.ui.gui.modules.CcpnModule import CcpnModule

  for loader, name, isPpkg in _pkgutil.walk_packages(path):
    module = loader.find_module(name).load_module(name)
    for i, obj in _inspect.getmembers(module):
      if _inspect.isclass(obj):
        if issubclass(obj, CcpnModule):
          if hasattr(obj, 'className'):
            _ccpnModules.append(obj)
  return _ccpnModules

def _openCcpnModule(ccpnModules, className, mainWindow, name):
  if className in ccpnModules:
    try:
      newCcpnModule = ccpnModules[className](mainWindow=mainWindow, name=name)
      mainWindow.moduleArea.addModule(newCcpnModule)
    except Exception as e:
      mainWindow.project._logger.warning("Layout restore failed: %s" % e)


def _initialiseCcpnModules():
  from ccpn.AnalysisScreen import modules as sm
  from ccpn.AnalysisAssign import modules as am
  from ccpn.AnalysisMetabolomics.ui.gui import modules as mm
  from ccpn.ui.gui import modules as gm

  paths = [item.__path__ for item in [sm, am, mm, gm]]
  ccpnModules = [ccpnModule for path in paths for ccpnModule in _ccpnModulesImporter(path)]


