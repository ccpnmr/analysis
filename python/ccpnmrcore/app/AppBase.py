
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
import ccpn
import ccpnmr
from ccpncore.util import Io as ioUtil
from ccpn.util import Io as ccpnIo

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

    self.setupPreferences()
    self.vLines = []
    self.hLines = []
    self.initProject(apiProject)


    
  def initProject(self, apiProject):

    # Done this way to sneak the appBase in before creating the wrapper
    self.current = Current()
    apiProject._appBase = self
    project = ccpnIo._wrapApiProject(apiProject)
    apiNmrProject = project._wrappedData
    self.project = project
    project._appBase = self

    apiWindowStore = apiNmrProject.windowStore
    if apiWindowStore is None:
      apiProject = apiNmrProject.parent
      apiWindowStore = apiProject.findFirstWindowStore()
      if apiWindowStore is None:
        apiWindowStore = apiProject.newWindowStore(nmrProject=apiProject.findFirstNmrProject())

      else:
        apiNmrProject.windowStore = apiWindowStore
    # MainWindow must always exist at this point
    # mainWindow = project.getWindow('Main')
    mainWindow = project._data2Obj[apiWindowStore.findFirstWindow(title='Main')]
    self.mainWindow = mainWindow
    mainWindow.raise_()

    if not apiProject.findAllGuiTasks(nmrProject=project._wrappedData):
      apiGuiTask = apiProject.newGuiTask(name='View', nmrProject=project._wrappedData,
                                         windows=(mainWindow._wrappedData,))

  def _closeProject(self):
    """Close project and clean up - should only be called when opening another"""

    # NBNB TBD add code to save first, ask, etd. Somewhere

    if self.project is not None:
      ioUtil.cleanupProject(self.project)
      self.project.delete()
      self.project = None
    self.mainWindow = None
    self.current = None

  def openProject(self, path):
    """Open new project from path"""
    self._closeProject()
    apiProject = ioUtil.loadProject(path)
    self.initProject(apiProject)

  def newProject(self, name='default'):
    """Create new, empty project"""
    self._closeProject()
    apiProject = ioUtil.newProject(name)
    self.initProject(apiProject)

  def saveProject(self):
    ioUtil.saveProject(self.project._wrappedData.root)
    print("project saved")

  def setupPreferences(self):

    preferencesPath = os.path.expanduser('~/.ccpn/v3settings.json') # TBD: where should it go?
    if not os.path.exists(preferencesPath):
      preferencesPath = os.path.join(Path.getPythonDirectory(), 'ccpnmrcore', 'app',
                                     'defaultv3settings.json')
    fp = open(preferencesPath)
    self.preferences = json.load(fp, object_hook=AttrDict) ##TBD find a better way ?!?
    fp.close()
    
def startProgram(programClass, applicationName, applicationVersion, projectPath=None):

  if projectPath:
    apiProject = ioUtil.loadProject(projectPath)
  else:
    apiProject = ioUtil.newProject('default')

  app = Application(applicationName, applicationVersion)
  program = programClass(apiProject)
  app.start()
  
