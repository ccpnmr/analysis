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
__dateModified__ = "$dateModified: 2017-07-07 16:32:37 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

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
  widgetsState = None
  UiPlugin = False

  @property
  @abstractmethod
  def PLUGINNAME(self):
    return str()

  @classmethod
  def register(cls):
    """
    method to register the pipe in the loaded pipes to appear in the pipeline
    """
    from ccpn.plugins import loadedPlugins
    loadedPlugins.append(cls)

  def __init__(self, application=None):
    self.guiModule = self.__class__.guiModule
    self.params = self.__class__.params
    self.settings = self.__class__.settings

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

    self.customizeSetup()

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


  def customizeSetup(self):
    '''
    Override this method to customize the UI auto-generation attributes
    '''
    pass


  def run(self, **kwargs):
    '''
    This is the method that automatically gets called for No-UI and Auto-generated UI plugins.
    '''
    pass


  def cleanup(self):
    pass
