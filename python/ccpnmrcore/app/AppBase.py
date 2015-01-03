__author__ = 'simon'


from ccpn import openProject, newProject
from ccpncore.util import Path
from ccpncore.util import AttrDict
from ccpnmrcore.Base import Base as GuiBase
from ccpnmrcore.Current import Current

import os, json


class AppBase(GuiBase):

  def __init__(self, project=None):
    self.project = project
    self.guiWindows = []
    self.current = Current()
    self.setupPreferences()
    self.mainWindow = MainWindow(self)

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

  def setupPreferences(self):

    preferencesPath = os.path.expanduser('~/.ccpn/v3settings.json') # TBD: where should it go?
    if not os.path.exists('preferencesPath'):
      preferencesPath = os.path.join(Path.getPythonDirectory(), 'ccpnmrcore', 'app', 'defaultv3settings.json')

    fp = open(preferencesPath)
    self.preferences = json.load(fp, object_hook=AttrDict) ##TBD find a better way ?!?
    fp.close()