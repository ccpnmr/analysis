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
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName =  'Peak Picker 1D'

ExcludeRegions = 'Exclude_Regions'
NoiseThreshold = 'Noise_Threshold'
NegativePeaks =  'Negative_Peaks'
MaximumFilterSize =  'Maximum_Filter_Size'
MaximumFilterMode =  'Maximum_Filter_Mode'
MinimalLineWidth =  'Minimal_LineWidth'
Modes = ['wrap', 'reflect', 'constant', 'nearest', 'mirror']

DefaultNoiseThreshold = [0.0, 0.0]
DefaultExcludeRegions = [[0.0, 0.0], [0.0, 0.0]]
########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################



########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################




class PeakPicker1DGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(PeakPicker1DGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    gridRow = 0
    self.pickNegativeLabel = Label(self.pipeFrame, text=NegativePeaks, grid=(gridRow, 0))
    setattr(self, NegativePeaks, CheckBox(self.pipeFrame, text='', checked=True, grid=(gridRow, 1)))

    gridRow += 1
    self.maximumFilterSize = Label(self.pipeFrame, text=MaximumFilterSize, grid=(gridRow, 0))
    setattr(self, MaximumFilterSize, Spinbox(self.pipeFrame, value=5, max=15, grid=(gridRow, 1)))
    gridRow += 1

    self.maximumFilterMode = Label(self.pipeFrame, text=MaximumFilterMode, grid=(gridRow, 0))
    setattr(self, MaximumFilterMode, PulldownList(self.pipeFrame, texts=Modes, grid=(gridRow, 1)))



########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class PeakPicker1DPipe(SpectraPipe):

  guiPipe = PeakPicker1DGuiPipe
  pipeName = PipeName

  _kwargs =   {
               ExcludeRegions: DefaultExcludeRegions,
               NoiseThreshold: DefaultNoiseThreshold,
               MaximumFilterSize: 5,
               MaximumFilterMode: Modes[0],
               NegativePeaks: True
              }

  def runPipe(self, spectra):
    '''
    :param data:
    :return:
    '''
    print(self._kwargs)
    maximumFilterSize = self._kwargs[MaximumFilterSize]
    maximumFilterMode = self._kwargs[MaximumFilterMode]
    negativePeaks = self._kwargs[NegativePeaks]

    if NoiseThreshold in self.pipeline._kwargs:
      positiveNoiseThreshold = max(self.pipeline._kwargs[NoiseThreshold])
      negativeNoiseThreshold = min(self.pipeline._kwargs[NoiseThreshold])
    else:
      self._kwargs.update({ NoiseThreshold: DefaultNoiseThreshold})
      positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])
      negativeNoiseThreshold = min(self._kwargs[NoiseThreshold])

    if ExcludeRegions in self.pipeline._kwargs:
      excludeRegions = self.pipeline._kwargs[ExcludeRegions]
    else:
      self._kwargs.update({ExcludeRegions: DefaultExcludeRegions})
      excludeRegions = self._kwargs[ExcludeRegions]

    for spectrum in self.inputData:
      spectrum.peakLists[0].pickPeaks1dFiltered(size=maximumFilterSize, mode=maximumFilterMode,
                                                positiveNoiseThreshold=positiveNoiseThreshold,
                                                negativeNoiseThreshold=negativeNoiseThreshold,
                                                excludeRegions= excludeRegions,
                                                negativePeaks=negativePeaks)

    return spectra



PeakPicker1DPipe.register() # Registers the pipe in the pipeline


