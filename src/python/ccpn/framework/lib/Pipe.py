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



class Pipe(ABC):
  '''
  Pipeline step base class.

  '''

  guiPipe = None
  autoGuiParams = None
  pipeName = ''




  def __init__(self, name = pipeName, application=None, ):
    self._kwargs = {}

    self.active = False

    if application is not None:
      self.application = application
      self.current = self.application.current
      self.preferences = self.application.preferences
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
