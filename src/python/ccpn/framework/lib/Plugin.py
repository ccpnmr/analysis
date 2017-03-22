__author__ = "$Author: TJ Ragan $"

from abc import ABC
from abc import abstractmethod
import os


class NoUI:
  def issueMessage(self, message):
    print(message)


class Plugin(ABC):
  '''
  Plugin base class.

  For Autogeneration of Gui:
  In order to genenerate a (crude) gui, you'll need to populate the params and settings class variables.
    First, make it an iterable:
      params = []
    Now, add variables in the order you want the input boxes to show up.
    Every variable is declared in a mapping (generally a dictionary) with two required keys:
      'variable' : The keyward parameter that will be used when the function is called.
      'value' : the possible values.  See below.
    In addition to the required keys, several optional keys can be used:
      label : the label used.  If this is left out, the variable name will be used instead.
      default : the default value
      stepsize : the stepsize for spinboxes.  If you include this for non-spinboxes it will be ignored

    The 'value' entry:
      The type of widget generated is controled by the value of this entry,
      if the value is an iterable, the type of widget is controlled by the first item in the iterable
      strings are not considered iterables here.
        value type                       : type of widget
        string                           : LineEdit
        boolean                          : Checkbox
        Iterable(strings)                : PulldownList
        Iterable(int, int)               : Spinbox
        Iterable(float, float)           : DoubleSpinbox
        Iterable(Iterables(str, object)) : PulldownList where the object is passed instead of the string

  '''


  guiModule = None  # Specify subclass of CcpnModule here OR
  params = None  # Populate this to have an auto-generated gui
  settings = None  # Break out the settings into another variable so pipelines are portable


  @property
  @abstractmethod
  def PLUGINNAME(self):
    return str()


  def __init__(self, application=None):

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

    self.ui = NoUI()


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


  def run(self, **kwargs):
    self.ui.issueMessage('run() called with:', kwargs)


  def cleanup(self):
    pass


  # # TODO: Move to ui.gui
  # @property
  # def _ui(self):
  #   if self._uiElement is None:
  #     self._uiElement = self.guiModule(self)
  #   return self._uiElement
