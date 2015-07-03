"""Module Documentation here

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
"""
import ccpn
import ccpnmr
from ccpncore.util import Io as ioUtil
from ccpn.util import Io as ccpnIo

from ccpncore.gui.Application import Application

from ccpncore.util import Path
from ccpncore.util.AttrDict import AttrDict
from ccpncore.util import Translation
from ccpncore.util.Undo import Undo

from ccpnmrcore.Base import Base as GuiBase
from ccpnmrcore.Current import Current

import os, json

from PyQt4 import QtGui

class AppBase(GuiBase):

  def __init__(self, apiProject, applicationName, applicationVersion):
    GuiBase.__init__(self, self) # yuk, two selfs, but it is that

    self.applicationName = applicationName
    self.applicationVersion = applicationVersion
    
    self.setupPreferences()
    ###self.vLines = []
    ###self.hLines = []
    self.initProject(apiProject)

    
  def initProject(self, apiProject):

    # Done this way to sneak the appBase in before creating the wrapper
    self.current = Current()
    apiProject._appBase = self
    project = ccpnIo._wrapApiProject(apiProject)
    apiNmrProject = project._wrappedData
    self.project = project
    self.current.project = project
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

    # Set up undo stack
    # The default values are as below. They can be changed if desired
    #project._resetUndo(maxWaypoints=20, maxOperations=10000)
    project._resetUndo()


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

  def saveProject(self, newPath=None):
    ioUtil.saveProject(self.project._wrappedData.root, newPath=newPath)
    print("project saved")
    
  def setupPreferences(self):

    preferencesPath = os.path.expanduser('~/.ccpn/v3settings.json') # TBD: where should it go?
    if not os.path.exists(preferencesPath):
      preferencesPath = os.path.join(Path.getPythonDirectory(), 'ccpnmrcore', 'app',
                                     'defaultv3settings.json')
    fp = open(preferencesPath)
    self.preferences = json.load(fp, object_hook=AttrDict) ##TBD find a better way ?!?
    fp.close()
    
def startProgram(programClass, applicationName, applicationVersion, projectPath=None, language=None):

  if language:
    Translation.setTranslationLanguage(language)
    Translation.updateTranslationDict('ccpnmrcore.gui')
    
  if projectPath:
    apiProject = ioUtil.loadProject(projectPath)
  else:
    apiProject = ioUtil.newProject('default')

  styleSheet = open(os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', 'DarkStyleSheet.qss')).read()
  # On the Mac (at least) it does not matter what you set the applicationName to be,
  # it will come out as the executable you are running (e.g. "python3")
  app = Application(applicationName, applicationVersion)
  app.setStyleSheet(styleSheet)
  program = programClass(apiProject, applicationName, applicationVersion)
  app.start()
  
