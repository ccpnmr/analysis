__author__ = 'TJ Ragan'

from abc import ABC
from abc import abstractmethod

from collections import OrderedDict
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox

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


  @abstractmethod
  def run(self, data):
    return data


  def _updateRunArgs(self, arg, value):
    self._kwargs[arg] = value


  def __init__(self, application=None):
    self._kwargs = {}
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



class GuiPipe(PipelineBox):

  widgetProperties = {
                      'CheckBox':      ('get',    'setChecked'),
                      'DoubleSpinbox': ('value',  'setValue'),
                      'Label':         ('get',    'setText'),
                      'LineEdit':      ('get',    'setText'),
                      'PulldownList':  ('currentText','set'),
                      'RadioButtons':  ('get',    'set'),
                      'Slider':        ('get',    'setValue'),
                      'Spinbox':       ('value',  'set'),
                      'TextEditor':    ('get',    'setText'),
                      }


  def __init__(self, parent=None, pipe=None, name=None, params=None, project=None, **kw):
    PipelineBox.__init__(self, name=name, )
    self.parent = parent
    self.pipeBoxName = name
    self.project = project
    self.params = params
    self.initialiseGui()
    self.pipe = pipe


  def initialiseGui(self):
    '''Define this function on the new pipe file'''
    pass

  def updatePipeParams(self):
    for key, value in self.getParams().items():
      self.pipe._updateRunArgs(key, value)

  def getParams(self):
    params = {}
    for item in self.variables:
      params[item] = self.getValue(item)
    return params

  def getValue(self, variable):
    widget = getattr(self, str(variable))
    if widget.__class__.__name__ in GuiPipe.widgetProperties.keys():
      return getattr(widget, GuiPipe.widgetProperties[widget.__class__.__name__][0])()

  def _setParams(self, **params):
    for variableName, value in params.items():
      try:
        widget = getattr(self, str(variableName))
        if widget.__class__.__name__ in GuiPipe.widgetProperties.keys():
          setWidget = getattr(widget, GuiPipe.widgetProperties[widget.__class__.__name__][1])
          setWidget(value)
      except:
        print('Impossible to restore %s value for %s. Check paramas dictionary in getWidgetParams' % (
        variableName, self.name()))


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
