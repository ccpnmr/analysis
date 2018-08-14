"""

"""


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
__version__ = "$Revision: 3.0.b3 $"
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
from typing import List
import numpy as np
import pandas as pd

class Pipe(ABC):
  """
  Pipeline step base class.

  """


  guiPipe = None #Only the class. it will be init later on the GuiPipeline
  autoGuiParams = None
  pipeName = ''
  isActive = False


  @classmethod
  def register(cls):
    """
    method to register the pipe in the loaded pipes to appear in the pipeline
    """
    from ccpn.pipes import loadedPipes
    loadedPipes.append(cls)


  def __init__(self, application=None):
    self._kwargs = {}
    self.inputData = None
    self.spectrumGroups = None
    self.pipeline = None
    self.project = None

    if self.pipeline is not None:
      self.inputData = self.pipeline.inputData
      self.spectrumGroups = self.pipeline.spectrumGroups

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


    self.customizeSetup()


  def _getSpectrumGroup(self, pid):
    if self.project is not None:
      return self.project.getByPid(pid)


  @abstractmethod
  def runPipe(self, data):
    return data


  def customizeSetup(self):
    '''
    Override this method to customize the UI auto-generation attributes
    '''
    pass


  def _updateRunArgs(self, arg, value):
    self._kwargs[arg] = value





class PandasPipe(Pipe):
  '''
  A pipe where the run method accepts a pandas dataframe and returns a pandas dataframe
  '''
  @abstractmethod
  def runPipe(self, dataframe:pd.DataFrame) -> pd.DataFrame:
    return dataframe


class SpectraPipe(Pipe):
  '''
  A pipe where the run method accepts a list of spectra and returns a list of spectra
  '''

  @abstractmethod
  def runPipe(self, spectra) -> List['Spectrum']:
    return spectra


class NumpyPipe(Pipe):
  '''
  A pipe where the run method accepts a numpy Array and returns a numpy Array
  '''
  @abstractmethod
  def runPipe(self, npArray:np.array) -> np.array:
    return npArray

