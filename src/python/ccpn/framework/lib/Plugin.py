__author__ = "$Author: TJ Ragan $"

from abc import ABC
from abc import abstractmethod
import os



def _autoGenPluginGui(objMethod):
  from ccpn.ui.gui.lib.GuiGenerator import generateWidget
  return generateWidget(objMethod,)  # add Container=CcpnModule bit


def _issueGuiInstantiatedMessage(objMethod):
  print('Instantiated', str(objMethod))


class Plugin(ABC):
  '''
  Plugin base class.
  '''


  guiModule = None  # Specify subclass of CcpnModule here
  params = None  # Populate this to have an auto-generated gui
  settings = None  # Break out the settings into another variable so pipelines are portable


  @property
  @abstractmethod
  def PLUGINNAME(self):
    return str()


  def __init__(self, application=None):
    if self.guiModule is None:
      if self.params is not None:
        self.guiModule = _autoGenPluginGui
      else:
        self.guiModule = self._issueGuiInstantiatedMessage

    self._uiWindow = None

    if application is not None:
      self.application = application
      self.current = self.application.current
      self.preferences = self.application.preferences
      self.undo = self.application.undo
      self.redo = self.application.redo
      self.ui = self.application.ui
      self.project = self.application.project
      try:
        self.mainWindow = self.ui.mainWindow
      except AttributeError:
        pass


  @property
  def package(self):
    return self.PLUGINNAME.split('...')[0]


  @property
  def name(self):
    return self.PLUGINNAME.split('...')[-1]


  @property
  def localInfo(self):
    if self.application is not None:
      pth = os.path.split(self.application.project.path)[0]
    else:
      pth = os.getcwd()
    pth = os.path.join(pth, 'plugins', self.package)
    if '...' in self.PLUGINNAME:
      pth = os.path.join(pth, self.name)
    if not os.path.exists(pth):
      os.makedirs(pth)
    return pth


  def cleanup(self):
    pass


  @property
  def _gui(self):
    if self._uiWindow is None:
      self._uiWindow = self.guiModule(self)
    return self._uiWindow
