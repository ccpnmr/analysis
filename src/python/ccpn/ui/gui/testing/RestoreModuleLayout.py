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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
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


DefaultLayout = []




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

def _openCcpnModule(mainWindow, ccpnModules, className):
  for ccpnModule in ccpnModules:
    if ccpnModule is not None:
      if ccpnModule.className == className:
        try:
          newCcpnModule = ccpnModule(mainWindow=mainWindow, )
          mainWindow.moduleArea.addModule(newCcpnModule, position='top', relativeTo=None)
        except Exception as e:
          mainWindow.project._logger.warning("Layout restore failed: %s" % e)


def _getApplicationSpecificModules(mainWindow, applicationName):
  '''init imports. try except as some applications may not be distribuited '''
  modules = []
  from ccpn.framework.Framework import AnalysisAssign, AnalysisMetabolomics, AnalysisStructure, AnalysisScreen

  if applicationName == AnalysisScreen:
    try:
      from ccpn.AnalysisScreen import modules as aS
      modules.append(aS)
    except Exception as e:
      mainWindow.project._logger.warning("Import Error, %s" % e)

  if applicationName == AnalysisAssign:
    try:
      from ccpn.AnalysisAssign import modules as aA
      modules.append(aA)
    except Exception as e:
      mainWindow.project._logger.warning("Import Error, %s" % e)


  if applicationName == AnalysisMetabolomics:
    try:
      from ccpn.AnalysisMetabolomics.ui.gui import modules as aM
      modules.append(aM)
    except Exception as e:
      mainWindow.project._logger.warning("Import Error, %s" % e)

  if applicationName == AnalysisStructure:
    try:
      from ccpn.AnalysisStructure import modules as aS
      modules.append(aS)
    except Exception as e:
      mainWindow.project._logger.warning("Import Error, %s" % e)

  return modules

def _getAvailableModules(mainWindow, layout):
  from ccpn.ui.gui import modules as gM
  applicationName = layout.general.applicationName
  modules = []
  if applicationName != mainWindow.application.applicationName:
    # TODO Needs to go in the logger
    print('Same modules could not be loaded. Different application. Start a new project with ', applicationName)
  else:
    modules = _getApplicationSpecificModules(mainWindow, applicationName)
  modules.append(gM)
  paths = [item.__path__ for item in modules]
  ccpnModules = [ccpnModule for path in paths for ccpnModule in _ccpnModulesImporter(path)]
  return ccpnModules

def _initialiseCcpnModulesLayout(mainWindow, layout):
  pass
  ## 1) import all the ccpnModules classes specific for the application.
  # ccpnModules =_getAvailableModules(mainWindow, layout)
  #
  #
  #
  # ## 3) try to open only the ccpnModules referred in the json
  # guiModules = layout.guiModules

  # for className, moduleName in nonDisplaysModules.items():
  #   print(className, moduleName)
  #   #
  # for m in ccpnModules:
  #   _openCcpnModule(mainWindow, ccpnModules, m.className,)

  # #
  # # # 4) restore the layout positions and sizes
  # #
  # # try:
  # #   mainWindow.moduleArea.restoreState(state)
  # # except Exception as e:
  # #   mainWindow.project._logger.warning("Layout error: %s" % e)
