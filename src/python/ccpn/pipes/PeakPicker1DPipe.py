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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:39 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.pipes.lib._getNoiseLevel import _getNoiseLevelForPipe
from ccpn.util.Logging import getLogger , _debug3

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName =  'Peak Picker 1D'

ExcludeRegions = 'Exclude_Regions'
NoiseThreshold = 'Noise_Threshold'
NegativePeaks =  'Negative_Peaks'
NoiseLevelFactor = 'Noise_Level_Factor'
MaximumFilterSize =  'Maximum_Filter_Size'
MaximumFilterMode =  'Maximum_Filter_Mode'
MinimalLineWidth =  'Minimal_LineWidth'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'
Modes = ['wrap', 'reflect', 'constant', 'nearest', 'mirror']

DefaultNoiseThresholdFactor = 10
DefaultNoiseThreshold = [0.0, 0.0]
DefaultExcludeRegions = [[0.0, 0.0], [0.0, 0.0]]
DefaultPeakListIndex = -1
########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################



########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################




class PeakPicker1DGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kwds):
    super(PeakPicker1DGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
    self.parent = parent

    row = 0
    self.pickNegativeLabel = Label(self.pipeFrame, text=NegativePeaks, grid=(row, 0))
    setattr(self, NegativePeaks, CheckBox(self.pipeFrame, text='', checked=True, grid=(row, 1)))

    row += 1
    self.noiseLevelFactorLabel = Label(self.pipeFrame, text=NoiseLevelFactor, grid=(row, 0))
    setattr(self, NoiseLevelFactor, DoubleSpinbox(self.pipeFrame, value=10.0, min=0.01, step=0.1, grid=(row, 1)))

    row += 1
    self.maximumFilterSize = Label(self.pipeFrame, text=MaximumFilterSize, grid=(row, 0))
    setattr(self, MaximumFilterSize, Spinbox(self.pipeFrame, value=10, max=1000, grid=(row, 1)))
    row += 1

    self.maximumFilterMode = Label(self.pipeFrame, text=MaximumFilterMode, grid=(row, 0))
    setattr(self, MaximumFilterMode, PulldownList(self.pipeFrame, texts=Modes, grid=(row, 1)))




########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class PeakPicker1DPipe(SpectraPipe):

  guiPipe = PeakPicker1DGuiPipe
  pipeName = PipeName

  _kwargs =   {
               ExcludeRegions: DefaultExcludeRegions,
               NoiseThreshold: DefaultNoiseThreshold,
               EstimateNoiseThreshold: True,
               NoiseLevelFactor: DefaultNoiseThresholdFactor,
               MaximumFilterSize: 5,
               MaximumFilterMode: Modes[0],
               NegativePeaks: True,

              }

  def runPipe(self, spectra):
    '''
    :param data:
    :return:
    '''
    if NoiseThreshold not in self._kwargs:
      self._kwargs.update({NoiseThreshold: DefaultNoiseThreshold})

    maximumFilterSize = self._kwargs[MaximumFilterSize]
    maximumFilterMode = self._kwargs[MaximumFilterMode]
    negativePeaks = self._kwargs[NegativePeaks]
    positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])
    negativeNoiseThreshold = min(self._kwargs[NoiseThreshold])
    noiseLevelFactor = self._kwargs[NoiseLevelFactor]

    if ExcludeRegions in self.pipeline._kwargs:
      excludeRegions = self.pipeline._kwargs[ExcludeRegions]
    else:
      self._kwargs.update({ExcludeRegions: DefaultExcludeRegions})
      excludeRegions = self._kwargs[ExcludeRegions]

    for spectrum in self.inputData:
      noiseThreshold = _getNoiseLevelForPipe(cls=self, spectrum=spectrum, estimateNoiseThreshold_var=EstimateNoiseThreshold,
                                             noiseThreshold_var=NoiseThreshold)
      if noiseThreshold:
        negativeNoiseThreshold = noiseThreshold[0]
        positiveNoiseThreshold = noiseThreshold[1]

      # print('Peak Picker @@@ noiseThreshold', noiseThreshold)

      if len(spectrum.peakLists) > 0:
        spectrum.peakLists[DefaultPeakListIndex].pickPeaks1dFiltered(size=maximumFilterSize, mode=maximumFilterMode,
                                                  positiveNoiseThreshold=positiveNoiseThreshold,
                                                  negativeNoiseThreshold=negativeNoiseThreshold,
                                                  excludeRegions= excludeRegions,
                                                  negativePeaks=negativePeaks,
                                                  factor=noiseLevelFactor)
      else:
        getLogger().warning('Error: PeakList not found. Add a new PeakList first')

    return spectra



PeakPicker1DPipe.register() # Registers the pipe in the pipeline


