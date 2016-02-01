"""Module Documentation here
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
__author__ = "$Author: simon $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

import os
import json
import time

from PyQt4 import QtGui, QtCore

from ccpn.lib import Io as ccpnIo
from ccpncore.util import Io as ioUtil
from ccpncore.gui.Application import Application
from ccpncore.memops.metamodel import Util as metaUtil
from ccpncore.api.memops import Implementation
from ccpncore.gui import iconsNew
from ccpncore.gui import MessageDialog
from ccpncore.util import Path
from ccpncore.util.AttrDict import AttrDict
from ccpncore.util import Register
from ccpncore.util import Translation
from application.core.Base import Base as GuiBase
from application.core.Current import Current
from application.core.popups.RegisterPopup import RegisterPopup

# The following must be there even though the import is not used in this file.
from ccpncore.gui import resources_rc

class AppBase(GuiBase):

  def __init__(self, apiProject, applicationName, applicationVersion,  preferences, components=None):
    GuiBase.__init__(self, self) # yuk, two selfs, but it is that

    if not components:
      components = set()
      
    self.applicationName = applicationName

    self.applicationVersion = applicationVersion
    self.preferences = preferences
    self.components = components
    ###self.vLines = []
    ###self.hLines = []
    self.initProject(apiProject)
    self.colourIndex = 0

  def initProject(self, apiProject):

    # Reset remoteData DataStores to match preferences setting
    dataPath = self.preferences.general.dataPath
    if not dataPath or not os.path.isdir(dataPath):
      dataPath = os.path.expanduser('~')
    dataUrl = apiProject.root.findFirstDataLocationStore(name='standard').findFirstDataUrl(
      name='remoteData')
    dataUrl.url = Implementation.Url(path=dataPath)

    # Done this way to sneak the appBase in before creating the wrapper
    apiProject._appBase = self
    self.current = Current(project=None)

    project = ccpnIo._wrapApiProject(apiProject)
    project._appBase = self
    self.project = project
    self.current._project = project

    apiNmrProject = project._wrappedData
    apiWindowStore = apiNmrProject.windowStore
    if apiWindowStore is None:
      apiProject = apiNmrProject.parent
      apiWindowStore = apiProject.findFirstWindowStore()
      if apiWindowStore is None:
        apiWindowStore = apiProject.newWindowStore(nmrProject=apiProject.findFirstNmrProject())

      else:
        apiNmrProject.windowStore = apiWindowStore
    # MainWindow must always exist at this point
    mainWindow = project.getWindow('Main')
    # mainWindow = project._data2Obj[apiWindowStore.findFirstWindow(title='Main')]
    self.mainWindow = mainWindow
    project.getByPid('Window:Main').namespace['current'] = self.current
    mainWindow.raise_()
    mainWindow.namespace['current'] = self.current

    if not apiProject.findAllGuiTasks(nmrProject=project._wrappedData):
      apiGuiTask = apiProject.newGuiTask(name='View', nmrProject=project._wrappedData,
                                         windows=(mainWindow._wrappedData,))

    self.initGraphics()
    # Set up undo stack
    # The default values are as below. They can be changed if desired
    #project._resetUndo(maxWaypoints=20, maxOperations=10000)
    project._resetUndo()
    #
    return project

  def initGraphics(self):
    """Set up graphics system after loading - to be overridden in subclasses"""
    # for window in self.project.windows:
    #   window.initGraphics()
    pass

  def _closeProject(self):
    """Close project and clean up - should only be called when opening another"""

    # NBNB TBD add code to save first, ask, etd. Somewhere

    if self.project is not None:
      self.project._close()
      self.project = None
    if self.mainWindow:
      self.mainWindow.deleteLater()
    self.mainWindow = None
    self.current = None

  def loadProject(self, path):
    """Open new project from path"""
    self._closeProject()
    apiProject = ioUtil.loadProject(path)
    return self.initProject(apiProject)

  def newProject(self, name='default'):
    """Create new, empty project"""
    self._closeProject()
    apiProject = ioUtil.newProject(name)
    return self.initProject(apiProject)

  def saveProject(self, newPath=None, newProjectName=None, createFallback=True):
    ioUtil.saveProject(self.project._wrappedData.root, newPath=newPath, newProjectName=newProjectName, createFallback=createFallback)
    layout = self.mainWindow.dockArea.saveState()
    layoutPath = os.path.join(self.project.path, 'layouts')
    if not os.path.exists(layoutPath):
      os.makedirs(layoutPath)
    import yaml
    with open(os.path.join(layoutPath, "layout.yaml"), 'w') as stream:
      yaml.dump(layout, stream)
      stream.close()
    saveIconPath = os.path.join(Path.getPythonDirectory(),
                      'ccpncore', 'gui', 'iconsNew', 'save.png')
    MessageDialog.showMessage('Project saved', 'Project successfully saved!',
                              colourScheme=self.preferences.general.colourScheme, iconPath=saveIconPath)

def getPreferences(skipUserPreferences=False, defaultPreferencesPath=None, userPreferencesPath=None):

  def _readPreferencesFile(preferencesPath):
    fp = open(preferencesPath)
    preferences = json.load(fp, object_hook=AttrDict) ##TBD find a better way ?!?
    fp.close()
    return preferences
    
  def _updateDict(d, u):
    import collections
    # recursive update of dictionary
    # this deletes every key in u that is not in d
    # if we want every key regardless, then remove first if check below 
    for k, v in u.items():
      if k not in d:
        continue
      if isinstance(v, collections.Mapping):
        r = _updateDict(d.get(k, {}), v)
        d[k] = r
      else:
        d[k] = u[k]
    return d
      
  preferencesPath = defaultPreferencesPath if defaultPreferencesPath else os.path.join(Path.getPythonDirectory(),
                      'application', 'core', 'defaultv3settings.json')
  preferences = _readPreferencesFile(preferencesPath)

  if not skipUserPreferences:
    preferencesPath = userPreferencesPath if userPreferencesPath else os.path.expanduser('~/.ccpn/v3settings.json')
    if os.path.exists(preferencesPath):
      _updateDict(preferences, _readPreferencesFile(preferencesPath))

  return preferences
  
def getStyleSheet(preferences):
  
  colourScheme = preferences.general.colourScheme
  colourScheme = metaUtil.upperFirst(colourScheme)
  
  styleSheet = open(os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', '%sStyleSheet.qss' % colourScheme)).read()
  
  return styleSheet
  
def checkRegistration(applicationVersion):
  
  registrationDict = Register.loadDict()
  if Register.isNewRegistration(registrationDict):
    popup = RegisterPopup(version=applicationVersion, modal=True)
    popup.show()
    popup.raise_()
    popup.exec_()
    registrationDict = Register.loadDict()
    if Register.isNewRegistration(registrationDict):
      return False
  
  Register.updateServer(registrationDict, applicationVersion)
  
  return True
  
def getSaveDirectory(apiProject, preferences):
  """Opens save Project as dialog box and gets directory specified in the file dialog."""
  dialog = QtGui.QFileDialog(caption='Save Project As...')
  dialog.setFileMode(QtGui.QFileDialog.AnyFile)
  dialog.setAcceptMode(1)
  if not dialog.exec_():
    return ''
  fileNames = dialog.selectedFiles()
  if not fileNames:
    return ''
  newPath = fileNames[0]
  if newPath:
    newPath = ioUtil.ccpnProjectPath(newPath)
    if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
      # should not really need to check the second and third condition above, only
      # the Qt dialog stupidly insists a directory exists before you can select it
      # so if it exists but is empty then don't bother asking the question
      title = 'Overwrite path'
      msg ='Path "%s" already exists, continue?' % newPath
      if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.general.colourScheme):
        newPath = ''
    
  return newPath
    
def saveV2ToV3(apiProject, projectPath, preferences):
    
  projectPath = ioUtil.ccpnProjectPath(projectPath)
  
  needNewDirectory = False
  if os.path.exists(projectPath) and (os.path.isfile(projectPath) or os.listdir(projectPath)):
    # should not really need to check the second and third condition above, only
    # the Qt dialog stupidly insists a directory exists before you can select it
    # so if it exists but is empty then don't bother asking the question
    title = 'Overwrite path'
    msg ='Converting to V3 format, path "%s" already exists, overwrite?' % projectPath
    if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.general.colourScheme):
      needNewDirectory = True

  if not needNewDirectory:
    try:
      ioUtil.saveProject(apiProject, newPath=projectPath)
      MessageDialog.showMessage('Project save', 'Project saved in v3 format at %s' % projectPath,
                                colourScheme=preferences.general.colourScheme)
    except IOError as e:
      needNewDirectory = True
      MessageDialog.showMessage('Project save', 'Project could not be saved in V3 format at %s' % projectPath,
                                colourScheme=preferences.general.colourScheme)
    
  if needNewDirectory:
    projectPath = getSaveDirectory(apiProject, preferences)
    if projectPath:
      try:
        ioUtil.saveProject(apiProject, newPath=projectPath, overwriteExisting=True)
      except IOError as e:
        MessageDialog.showMessage('Project save', 'Project could not be saved in V3 format at %s, quitting' % projectPath,
                                  colourScheme=preferences.general.colourScheme)
        projectPath = ''
    
  return projectPath
  
def startProgram(programClass, applicationName, applicationVersion, components, projectPath=None,
                 language=None, skipUserPreferences=False, nologging=False):

  preferences = getPreferences(skipUserPreferences)
  
  if language:
    Translation.setTranslationLanguage(language)
    Translation.updateTranslationDict('application.core.gui')
    
  useFileLogger = not nologging
  
  # On the Mac (at least) it does not matter what you set the applicationName to be,
  # it will come out as the executable you are running (e.g. "python3")
  app = Application(applicationName, applicationVersion)
  splashPng = os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', 'ccpnmr-splash-screen.png')
  splashPix = QtGui.QPixmap(splashPng)
  splashImage = QtGui.QImage(splashPix.size(), QtGui.QImage.Format_ARGB32)
  splashImage.fill(QtCore.Qt.transparent)

  painter = QtGui.QPainter(splashImage)
  painter.setOpacity(0.1)
  painter.drawPixmap(0, 0, splashPix)
  painter.end()
  # splashPix2 = QtGui.QPixmap.fromImage(splashImage)
  # splash_pix.scaled(QtCore.QSize))

  # splash_pix.fill(QtGui.QColor('white'))
  # print(splashPng)
  # splashPix = QtGui.QPixmap(splashPng)
  splash = QtGui.QSplashScreen(splashPix)
  # splash.show()
  # app.processEvents()
  # time.sleep(10)

  splash.show()
  app.processEvents()
  time.sleep(3)

  splash.close()
  styleSheet = getStyleSheet(preferences)
  app.setStyleSheet(styleSheet)
  
  if projectPath:
    apiProject = ioUtil.loadProject(projectPath, useFileLogger=useFileLogger)
    if not projectPath.endswith(ioUtil.CCPN_DIRECTORY_SUFFIX):
      projectPath = saveV2ToV3(apiProject, projectPath, preferences)
      if not projectPath:
        return
      apiProject = ioUtil.loadProject(projectPath, useFileLogger=useFileLogger)
  else:
    apiProject = ioUtil.newProject('default', useFileLogger=useFileLogger)

  if checkRegistration(applicationVersion):
    program = programClass(apiProject, applicationName, applicationVersion, preferences, components)

  app.start()

