#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:36 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
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

from collections import OrderedDict
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe

class Pipe(ABC):
  '''
  Pipeline step base class.


  For Autogeneration of Gui:
  In order to genenerate a (crude) gui, you'll need to populate the params class variable.
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

  guiModule = None
  params = None


  @property
  @abstractmethod
  def METHODNAME(self):
    return str()


  def __init__(self, application=None):
    self._kwargs = {}

    self.guiModule = self.__class__.guiModule

    self.params = self.__class__.params

    self.active = False

    if application is not None:
      self.application = application
      self.current = self.application.current
      self.preferences = self.application.preferences
      self.undo = self.application.undo                 # Do we really want pipes to have this?
      self.redo = self.application.redo                 # Do we really want pipes to have this?
      self.ui = self.application.ui
      self.project = self.application.project
      try:
        self.mainWindow = self.ui.mainWindow
      except AttributeError:
        pass
      # Adding the _runMacro function here is very difficult, do we need to?

    self.customizeSetup()


  @abstractmethod
  def run(self, data):
    return data


  def customizeSetup(self):
    '''
    Override this method to customize the UI auto-generation attributes
    '''
    pass


  def _updateRunArgs(self, arg, value):
    self._kwargs[arg] = value



try:

  import pandas as pd
  class PandasPipe(Pipe):
    '''
    A pipe where the run method accepts a pandas dataframe and returns a pandas dataframe
    '''
    @abstractmethod
    def run(self, dataframe:pd.DataFrame) -> pd.DataFrame:
      return dataframe

except ImportError:
  pass
