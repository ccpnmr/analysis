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
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe, _getWidgetByAtt
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.core.lib.SpectrumLib import _estimateNoiseLevel1D
import numpy as np

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Calculate Integrals'
IntegralListIndex = 'Add_To_Integral'
NoiseThreshold = 'Noise_Threshold'
MinimalLineWidth = 'Minimal_LineWidth'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'

DefaultMinimalLineWidth =  0.01
DefaultNoiseThreshold = [0.0, 0.0]
DefaultIntegralListIndex = 0

########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################




########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################




class CalculateAreaGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(CalculateAreaGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    row = 0
    integralListLabel = Label(self.pipeFrame, IntegralListIndex, grid=(row, 0))
    setattr(self, IntegralListIndex, Spinbox(self.pipeFrame, value=0, max=10, grid=(row, 1)))
    row += 1

    self.mlwLabel = Label(self.pipeFrame, MinimalLineWidth, grid=(row, 0))
    setattr(self, MinimalLineWidth, DoubleSpinbox(self.pipeFrame, value=DefaultMinimalLineWidth, grid=(row, 1)))




########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class CalculateAreaPipe(SpectraPipe):

  guiPipe = CalculateAreaGuiPipe
  pipeName = PipeName

  _kwargs =       {
                    NoiseThreshold: DefaultNoiseThreshold,
                    MinimalLineWidth: DefaultMinimalLineWidth,
                    IntegralListIndex : DefaultIntegralListIndex,
                    EstimateNoiseThreshold: True,
                   }


  def runPipe(self, spectra):
    '''
    :param data:
    :return:
    '''

    if NoiseThreshold not in self._kwargs:
      self._kwargs.update({NoiseThreshold: DefaultNoiseThreshold})

    minimalLineWidth = self._kwargs[MinimalLineWidth]
    positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])

    for spectrum in spectra:
      if EstimateNoiseThreshold in self.pipeline._kwargs:
        if self.pipeline._kwargs[EstimateNoiseThreshold]:
          if spectrum.noiseLevel is not None:
            positiveNoiseThreshold = spectrum.noiseLevel
          else:
            positiveNoiseThreshold = _estimateNoiseLevel1D(np.array(spectrum.positions), np.array(spectrum.intensities))
      else:
        positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])

      if positiveNoiseThreshold == 0.0:
        positiveNoiseThreshold = _estimateNoiseLevel1D(np.array(spectrum.positions), np.array(spectrum.intensities))

      iLIndex = self._kwargs[IntegralListIndex]
      if len(spectrum.integralLists) > iLIndex:
        spectrum.integralLists[iLIndex].automaticIntegral1D(minimalLineWidth=float(minimalLineWidth), noiseThreshold=positiveNoiseThreshold)
      print('Integral List does not exist')

    return spectra


CalculateAreaPipe.register() # Registers the pipe in the pipeline


