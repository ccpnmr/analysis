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
__author__ = "$Author: CCPN $"
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
  :return: #updates classNameModuleNameTupleList on SavedLayout with list of tuples [(className, ModuleName), (className, ModuleName)]
  list of tuples because a multiple modules of the same class type can exist. E.g. two peakListTable modules! 
  """
  guiModules = mainWindow.moduleArea.currentModules

  classNames_ModuleNames = [] #list of tuples [(className, ModuleName), (className, ModuleName)]
  for module in guiModules:
    if not isinstance(module, GuiSpectrumDisplay): # Displays are not stored here but in the DataModel
      classNames_ModuleNames.append((module.className, module.name()))

  if GuiModules in  layout:
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
  Updates the application.savedLayout Dict
  :param mainWindow: needed to get application
  :return: an up to date savedLayout dictionary with the current state of GuiModules
  """
  layout = mainWindow.application.savedLayout
  
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
  updateSavedLayout(mainWindow)
  layout = mainWindow.application.savedLayout
  project = mainWindow.application.project
  if not jsonFilePath:
    jsonFilePath = getLayoutDirectoryPath(project.path) + '/' + DefaultLayoutFileName
  file = open(jsonFilePath, "w")
  json.dump(layout, file, sort_keys=False, indent=4, separators=(',', ': '))
  file.close()




