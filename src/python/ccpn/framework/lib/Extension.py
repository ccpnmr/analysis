__author__ = 'TJ Ragan'

from abc import ABC
from abc import abstractmethod



class ExtensionABC(ABC):
  '''

  '''

  guiModule = None
  params = None
  _SPECTRADATAFRAMENAME = 'spectra dataframe'
  _SPECTRADATAFRAMEPARAMETER = 'df'


  @property
  @abstractmethod
  def METHODNAME(self):
    return str()


  @abstractmethod
  def runMethod(self, dataset):
    pass


  def __init__(self, application=None):
    self.application = application
    if self.guiModule is not None:
      self.guiModule = self.guiModule()
    else:
      self.guiModule = None

  def getSpectraDF(self, dataset):
    for data in dataset.data:
      if data.name == self._SPECTRADATAFRAMENAME:
        return data.parameters(self._SPECTRADATAFRAMEPARAMETER)



from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox

class GuiModule(PipelineBox):

  def __init__(self, parent=None, name=None, params=None, **kw):
    PipelineBox.__init__(self, name=name)
    self.parseParams(params)


  def parseParams(self, params):
    '''
    Parser for auto gui generation.  This should ultimeately behave the same as the
    Jupyter interact auto-generator.
    '''
    if params is not None:
      from collections import Mapping
      for name, param in params.items():
        if isinstance(param, str):
          print('parameter "{}" has a string value {}, should make a text entry box'.format(name, param))
        elif isinstance(param, Mapping):
          print('parameter "{}" is a mapping value{}, should make mapped drop-down box'.format(name, param))
        elif hasattr(param, '__iter__'):
          if len(param) > 0:
            if isinstance(param[0], int):
              print('parameter "{}" is an iterable of ints value {}, should make ranged spin box'.format(name, param))
            elif isinstance(param[0], float):
              print('parameter "{}" is an iterable of floats value {}, should make spin box'.format(name, param))
            else:
              print('parameter "{}" is an iterable value {}, should make drop-down box'.format(name, param))
        else:
          raise NotImplemented("Don't know how to automaticall handle {}".format(param))
