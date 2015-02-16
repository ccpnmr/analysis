__author__ = 'simon'


from ccpncore.util import Io as ioUtil
import ccpn
import ccpnmr
# from ccpn import openProject, newProject

from ccpncore.gui.Application import Application

from ccpncore.util import Path
from ccpncore.util.AttrDict import AttrDict

from ccpnmrcore.Base import Base as GuiBase
from ccpnmrcore.Current import Current

import os, json

class AppBase(GuiBase):

  def __init__(self, apiProject):
    
    GuiBase.__init__(self, self) # yuk, two selfs, but it is that

    self.initProject(apiProject)
    self.setupPreferences()
    
  def initProject(self, apiProject):

    # Done this way to sneak the appBase in before creating the wrapper
    apiProject._appBase = self
    project = ccpn._wrapApiProject(apiProject)
    
    self.project = project
    project._appBase = self
    self.guiWindows = []
    
    self.current = Current()

    apiProject = project._wrappedData.parent
    apiWindowStore = apiProject.findFirstWindowStore()
    if apiWindowStore is None:
      apiWindowStore = apiProject.newWindowStore(nmrProject=apiProject.findFirstNmrProject())

    # MainWindow must always exist at this point
    self.mainWindow = mainWindow = project.getWindow('Main')
    mainWindow.raise_()

    if not apiProject.findAllGuiTasks(nmrProject=project._wrappedData):
      apiGuiTask = apiProject.newGuiTask(name='View', nmrProject=project._wrappedData,
      windows=(mainWindow,))

  def _closeProject(self):
    """Close project and clean up - should only be called wen opening another"""

    # NBNB TBD add code to save first, ask, etd. Somewhere

    ioUtil.cleanupProject(self.project)
    self.project.delete()
    self.project = None
    self.guiWindows.clear()
    self.mainWindow = None
    self.current = None

  def openProject(self, path):
    """Open new project from path"""
    self._closeProject()
    apiProject = ioUtil.loadProject(path)
    self.initProject(apiProject)
    self.setupPreferences()

  def newProject(self, name='default'):
    """Create new, empty project"""
    self._closeProject()
    apiProject = ioUtil.newProject(name)
    self.initProject(apiProject)
    self.setupPreferences()

  def saveProject(self):
    print("project saved")

  def setupPreferences(self):

    preferencesPath = os.path.expanduser('~/.ccpn/v3settings.json') # TBD: where should it go?
    print(preferencesPath)
    if not os.path.exists(preferencesPath):
      preferencesPath = os.path.join(Path.getPythonDirectory(), 'ccpnmrcore', 'app', 'defaultv3settings.json')
    fp = open(preferencesPath)
    self.preferences = json.load(fp, object_hook=AttrDict) ##TBD find a better way ?!?
    print(self.preferences)
    fp.close()
    
def startProgram(programClass, applicationName, applicationVersion, projectPath=None):

  if projectPath:
    apiProject = ioUtil.loadProject(projectPath)
  else:
    apiProject = ioUtil.newProject('default')

  app = Application(applicationName, applicationVersion)
  program = programClass(apiProject)
  app.start()
  
