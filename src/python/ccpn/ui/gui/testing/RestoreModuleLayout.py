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
import json
import os


# to Move in gui/framework
def _saveToJson(self, jsonPath, data):
  with open(jsonPath, 'w') as fp:
    json.dump(data, fp, indent=2)
    fp.close()

# to Move in gui/framework
def _saveLayout(self):
  layoutState = self.ui.mainWindow.moduleArea.layoutState
  layoutPath = os.path.join(self.project.path, 'layouts')
  if not os.path.exists(layoutPath):
    os.makedirs(layoutPath)
  jsonPath = os.path.join(layoutPath, "layout.json")
  self._saveToJson(jsonPath, layoutState)

# to Move in gui/framework
def _openJsonFile(self, path):
  if path is not None:
    with open(str(path), 'r') as jf:
      data = json.load(jf)
    return data
# to Move in gui/framework
def _initLayout(self):
  jsonPath = os.path.join(self.project.path, 'layouts', 'layout.json')
  if os.path.exists(jsonPath):
    layoutState = self._openJsonFile(jsonPath)
    from ccpn.ui.gui.testing.RestoreModuleLayout import _initialiseCcpnModulesLayout
    currentModules = self.ui.mainWindow.moduleArea.currentModules

    _initialiseCcpnModulesLayout(self.ui.mainWindow, layoutState)


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

def _openCcpnModule(mainWindow, ccpnModules, className, moduleName):
  for ccpnModule in ccpnModules:
    if ccpnModule is not None:
      if ccpnModule.className == className:
        try:
          newCcpnModule = ccpnModule(mainWindow=mainWindow, name=moduleName)
          mainWindow.moduleArea.addModule(newCcpnModule, position='top', relativeTo=None)
        except Exception as e:
          mainWindow.project._logger.warning("Layout restore failed: %s" % e)

def _openJsonFile(path):
  if path is not None:
    with open(str(path), 'r') as jf:
      data = json.load(jf)
    return data

def _getModules(mainWindow):
  '''init imports. try except as some applications may not be distribuited '''
  modules = []
  try:
    from ccpn.AnalysisScreen import modules as aS
    modules.append(aS)
  except Exception as e:
    mainWindow.project._logger.warning("Import Error, %s" % e)

  try:
    from ccpn.AnalysisAssign import modules as aA
    modules.append(aA)
  except Exception as e:
    mainWindow.project._logger.warning("Import Error, %s" % e)

  try:
    from ccpn.AnalysisMetabolomics.ui.gui import modules as aM
    modules.append(aM)
  except Exception as e:
    mainWindow.project._logger.warning("Import Error, %s" % e)

  try:
    from ccpn.AnalysisStructure import modules as aS
    modules.append(aS)
  except Exception as e:
    mainWindow.project._logger.warning("Import Error, %s" % e)

  from ccpn.ui.gui import modules as gM
  modules.append(gM)

  return modules

def _initialiseCcpnModulesLayout(mainWindow, layoutState):

  ## 1) import all the ccpnModules classes
  paths = [item.__path__ for item in _getModules(mainWindow)]

  ccpnModules = [ccpnModule for path in paths for ccpnModule in _ccpnModulesImporter(path)]

  ## 2) load json file containing the ccpnModules layout state

  modulesNamesDict, state = layoutState

  ## 3) try to open only the ccpnModules referred in the json

  for className, moduleName in modulesNamesDict.items():
    print(className, moduleName)
    _openCcpnModule(mainWindow, ccpnModules, className, moduleName)

  # 4) restore the layout positions and sizes

  try:
    mainWindow.moduleArea.restoreState(state)
  except Exception as e:
    mainWindow.project._logger.warning("Layout error: %s" % e)
