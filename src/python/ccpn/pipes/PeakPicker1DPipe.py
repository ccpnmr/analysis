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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.LinearRegionsPlot import TargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Label import Label
import pyqtgraph as pg

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import Pipe
from functools import partial




########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################



########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################




class PeakPicker1DGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = 'Peak Picker 1D'

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(PeakPicker1DGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    gridRow = 0
    self.pickNegativeLabel = Label(self.pipeFrame, text='Pick negative peaks', grid=(gridRow, 0))
    self.pickNegative = CheckBox(self.pipeFrame, text='', checked=True, grid=(gridRow, 1))


    gridRow += 1
    self.maximumFilterSize = Label(self.pipeFrame, text="Select Maximum Filter Size", grid=(gridRow, 0))
    self.maximumFilterSize = Spinbox(self.pipeFrame, grid=(gridRow, 1))
    self.maximumFilterSize.setValue(5)
    self.maximumFilterSize.setMaximum(15)

    gridRow += 1
    modes = ['wrap', 'reflect', 'constant', 'nearest', 'mirror']
    self.maximumFilterMode = Label(self.pipeFrame, text="Select Maximum Filter Mode", grid=(gridRow, 0))
    self.maximumFilterMode = PulldownList(self.pipeFrame, texts=modes, grid=(gridRow, 1))




########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class PeakPicker1DPipe(Pipe):

  guiPipe = PeakPicker1DGuiPipe
  pipeName = PeakPicker1DGuiPipe.pipeName

  defaultParams = {'excludeRegions': [[0.0, 0.0], [0.0, 0.0]],
                   'noiseRegions': [0.0, 0.0],
                   'maximumFilterSize': 5,
                   'maximumFilterMode': 'wrap',
                   'noiseLevelMode': 'Estimated',
                   'pickNegative': True
                   }

  def runPipe(self, params):
    '''
    :param data:
    :return:
    '''
    if self.inputData is not None:
      if 'maximumFilterSize' in self._kwargs:
        maximumFilterSize = self._kwargs['maximumFilterSize']
      else:
        maximumFilterSize = self.defaultParams['maximumFilterSize']

      if 'maximumFilterMode' in self._kwargs:
        maximumFilterMode = self._kwargs['maximumFilterMode']
      else:
        maximumFilterMode = self.defaultParams['maximumFilterMode']

      try:
        if 'noiseThreshold' in self.pipeline._kwargs:
          positiveNoiseThreshold = max(self.pipeline._kwargs['noiseThreshold'])
          negativeNoiseThreshold = min(self.pipeline._kwargs['noiseThreshold'])
        else:
          positiveNoiseThreshold = max(self.defaultParams['noiseThreshold'])
          negativeNoiseThreshold = min(self.defaultParams['noiseThreshold'])
      except:
        positiveNoiseThreshold = None
        negativeNoiseThreshold = None

      try:
        if 'excludeRegions' in self.pipeline._kwargs:
          excludeRegions = self.pipeline._kwargs['excludeRegions']
        else:
          excludeRegions = self.defaultParams['excludeRegions']
      except:
        excludeRegions = None

      if 'pickNegative' in self._kwargs:
        pickNegative = self._kwargs['pickNegative']
      else:
        pickNegative = self.defaultParams['pickNegative']

      for spectrum in self.inputData:
        spectrum.peakLists[0].pickPeaks1dFiltered(size=maximumFilterSize, mode=maximumFilterMode,
                                                  positiveNoiseThreshold=positiveNoiseThreshold,
                                                  negativeNoiseThreshold=negativeNoiseThreshold,
                                                  excludeRegions= excludeRegions,
                                                  negativePeaks=pickNegative)


PeakPicker1DPipe.register() # Registers the pipe in the pipeline


