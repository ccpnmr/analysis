"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import glob
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.util.AttrDict import AttrDict
import json
from collections import defaultdict


# TODO: Deal With Blank displays opening more then once.
# TODO: Deal With empty spaces when a module could not be restored. Needs to Fill all available places.
# TODO: Save restore displays

LayoutDirName = 'layout'
DefaultLayoutFileName = 'v3Layout.json'
Warning =  "warning"
WarningMessage =  "Warning. Any changes in this file will be overwritten when saving a new layout."
General = "general"
ApplicationName = "applicationName"
ApplicationVersion = "applicationVersion"
GuiModules = "guiModules"
ClassNameModuleName = "class_And_Module_Names"
LayoutState =  "layoutState"

DefaultLayoutFile = {
                    Warning:  WarningMessage,
                    General:
                              {
                                ApplicationName: "",
                                ApplicationVersion: ""
                              },
                    GuiModules:
                              {
                                ClassNameModuleName: [()]
                              },

                    LayoutState:
                              {

                              }

                   }


def createLayoutDirectory(project):
  '''

  :param project:
  :return: creates a new folder : layout, where all the layout json files will be contained
  '''
  if project is not None:
    layoutDirectory = os.path.join(project.path, LayoutDirName)
    if not os.path.exists(layoutDirectory):
      os.makedirs(layoutDirectory)
      return layoutDirectory

def _createLayoutFile(project):
  try:
    path =  getLayoutDirectoryPath(project.path)+'/'+DefaultLayoutFileName
    file = open(path, "w")
    json.dump(DefaultLayoutFile, file, sort_keys=False, indent=4, separators=(',', ': '))
    file.close()
  except Exception as e:
    getLogger().warning('Impossible to create a layout File.', e)


def getLayoutDirectoryPath(projectPath):
  return os.path.join(projectPath, LayoutDirName)


def getLayoutFile(projectPath):
  if projectPath:
    fileType = '.json'
    layoutDirPath = getLayoutDirectoryPath(projectPath)
    if layoutDirPath:
      layoutFilepaths = glob.glob(layoutDirPath + "/*" + fileType)  # * means all if need specific format then *.fileType
      if len(layoutFilepaths)>0:
        latest_file = max(layoutFilepaths, key=os.path.getctime)
        getLogger().debug('Loaded User Layout')
        return latest_file

def _updateGeneral(mainWindow, layout):
  application = mainWindow.application
  applicationName = application.applicationName
  applicationVersion = application.applicationVersion
  if General in layout:
    if ApplicationName in layout.general:
      setattr(layout.general, ApplicationName, applicationName)
    if ApplicationVersion in layout.general:
      setattr(layout.general, ApplicationVersion, applicationVersion)

def _updateGuiModules(mainWindow, layout):
  """
  
  :param mainWindow: 
  :param layout: 
  :return: #updates classNameModuleNameTupleList on layout with list of tuples [(className, ModuleName), (className, ModuleName)]
  list of tuples because a multiple modules of the same class type can exist. E.g. two peakListTable modules! 
  """
  guiModules = mainWindow.moduleArea.openedModules

  classNames_ModuleNames = [] #list of tuples [(className, ModuleName), (className, ModuleName)]
  for module in guiModules:
    if not isinstance(module, GuiSpectrumDisplay): # Displays are not stored here but in the DataModel
      classNames_ModuleNames.append((module.className, module.name()))

  if GuiModules in layout:
    if ClassNameModuleName in layout.guiModules:
        setattr(layout.guiModules, ClassNameModuleName, classNames_ModuleNames )

def _updateLayoutState(mainWindow, layout):
  if LayoutState in layout:
    setattr(layout, LayoutState, mainWindow.moduleArea.saveState())

def _updateWarning(mainWindow, layout):
  if Warning in layout:
    setattr(layout, Warning, WarningMessage)

def updateSavedLayout(mainWindow):
  """
  Updates the application.layout Dict
  :param mainWindow: needed to get application
  :return: an up to date layout dictionary with the current state of GuiModules
  """
  layout = mainWindow.application.layout
  
  _updateGeneral(mainWindow, layout)
  _updateGuiModules(mainWindow, layout)
  _updateLayoutState(mainWindow, layout)
  _updateWarning(mainWindow, layout)


def saveLayoutToJson(mainWindow, jsonFilePath=None):
  """

  :param application:
  :param jsonFilePath: User defined file path where to save the layout. Default is in .ccpn/layout/v3Layout.json
  :return: None
  """
  try:
    updateSavedLayout(mainWindow)
    layout = mainWindow.application.layout
    project = mainWindow.application.project
    if not jsonFilePath:
      jsonFilePath = getLayoutDirectoryPath(project.path) + '/' + DefaultLayoutFileName
    file = open(jsonFilePath, "w")
    json.dump(layout, file, sort_keys=False, indent=4, separators=(',', ': '))
    file.close()
  except Exception as e:
    getLogger().warning('Impossitble to save Layout %s' %e)


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


def _openCcpnModule(mainWindow, ccpnModules, className, moduleName=None):
  for ccpnModule in ccpnModules:
    if ccpnModule is not None:
      if ccpnModule.className == className:
        try:
          newCcpnModule = ccpnModule(mainWindow=mainWindow, name=moduleName)
          newCcpnModule._restored = True

          mainWindow.moduleArea.addModule(newCcpnModule)
        except Exception as e:
          getLogger().warning("Layout restore failed: %s" % e)


def _getApplicationSpecificModules(mainWindow, applicationName):
  '''init imports. try except as some applications may not be distribuited '''
  modules = []
  from ccpn.framework.Framework import AnalysisAssign, AnalysisMetabolomics, AnalysisStructure, AnalysisScreen

  if applicationName == AnalysisScreen:
    try:
      from ccpn.AnalysisScreen import modules as aS
      modules.append(aS)
    except Exception as e:
      getLogger().warning("Import Error, %s" % e)

  if applicationName == AnalysisAssign:
    try:
      from ccpn.AnalysisAssign import modules as aA
      modules.append(aA)
    except Exception as e:
      getLogger().warning("Import Error, %s" % e)

  if applicationName == AnalysisMetabolomics:
    try:
      from ccpn.AnalysisMetabolomics.ui.gui import modules as aM
      modules.append(aM)
    except Exception as e:
      getLogger().warning("Import Error, %s" % e)

  if applicationName == AnalysisStructure:
    try:
      from ccpn.AnalysisStructure import modules as aS
      modules.append(aS)
    except Exception as e:
      getLogger().warning("Import Error, %s" % e)

  return modules


def _getAvailableModules(mainWindow, layout):
  from ccpn.ui.gui import modules as gM
  if General in layout:
    if ApplicationName in layout.general:

      applicationName = getattr(layout.general, ApplicationName)
      modules = []
      if applicationName != mainWindow.application.applicationName:
        # TODO Needs to go in the logger
        getLogger().debug('Same modules could not be loaded. Different application. Start a new project with %s' %applicationName)
      else:
        modules = _getApplicationSpecificModules(mainWindow, applicationName)
      modules.append(gM)
      paths = [item.__path__ for item in modules]
      ccpnModules = [ccpnModule for path in paths for ccpnModule in _ccpnModulesImporter(path)]
      return ccpnModules


def restoreLayout(mainWindow, layout):
  ## import all the ccpnModules classes specific for the application.
  # mainWindow.moduleArea._closeAll()
  try:
    ccpnModules = _getAvailableModules(mainWindow, layout)
    # mainWindow.moduleArea._closeAll()
    if GuiModules in layout:
      if ClassNameModuleName in layout.guiModules:
        classNameGuiModuleNameList = getattr(layout.guiModules, ClassNameModuleName)
        for classNameGuiModuleName in classNameGuiModuleNameList:
          if len(classNameGuiModuleName) == 2:
            className, guiModuleName = classNameGuiModuleName
            _openCcpnModule(mainWindow, ccpnModules, className, moduleName=guiModuleName)

  except Exception as e:
    getLogger().warning("Failed to restore Layout")

  ## restore the layout positions and sizes
  try:
    if LayoutState in layout:
      state = getattr(layout, LayoutState)
      mainWindow.moduleArea.restoreState(state)

  except Exception as e:
    getLogger().warning("Layout error: %s" % e)
