__author__ = 'simon'


from ccpn import openProject, newProject
from ccpncore.util import Path
from ccpncore.util.AttrDict import AttrDict
from ccpnmrcore.Base import Base as GuiBase
from ccpnmrcore.Current import Current
from ccpnmrcore.modules.MainWindow import MainWindow

import os, json

class AppBase(GuiBase):

  def __init__(self, project=None):
    self.project = project
    self.guiWindows = []
    self.current = Current()
    self.setupPreferences()
    ### TBD needs changing when GUI wrapper is available
    apiProject = project._wrappedData.parent
    apiWindowStore = apiProject.findFirstWindowStore()
    if apiWindowStore is None:
      apiWindowStore = apiProject.newWindowStore(nmrProject=apiProject.findFirstNmrProject())
    apiWindow = apiWindowStore.findFirstWindow()
    guiTask = apiProject.findFirstGuiTask(name='CcpnAssign') # TBD: what should the name be?? ask Rasmus
    if not guiTask:
      guiTask = apiProject.newGuiTask(name='CcpnAssign', nmrProjectName=apiProject.findFirstNmrProject().name)
    self.mainWindow = MainWindow(self, apiWindow)
    self.mainWindow.raise_()

  def openProject(self, path):
    self.project = openProject(path)
    self.setProject(isNew=False)
    # for window in self.project.windowStore.windows:
    #   if window.serial == 1:
    #     self.mainWindow.setProject()
    #   else:
    #     guiWindow = SubWindow(self, window)
    ##### need to work out how to handle multiple layouts

  def newProject(self, name=None):
    if name is None:
      self.project=newProject('defaultProject')
    else:
      self.project=newProject(name)
    self.setProject(isNew=True)

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