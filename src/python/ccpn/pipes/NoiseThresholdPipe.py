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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe , _getWidgetByAtt
from ccpn.ui.gui.widgets.LinearRegionsPlot import TargetButtonSpinBoxes
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.core.lib.SpectrumLib import _oldEstimateNoiseLevel1D
import numpy as np

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Noise Threshold'
NoiseThreshold = 'Noise_Threshold'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'
DefaultEstimateNoiseThreshold = False
DefaultNoiseThreshold = [0,0]


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

def _getNoiseThreshold(spectrum, factor=5):
  if spectrum is not None:
    x, y = np.array(spectrum.positions), np.array(spectrum.intensities)
    return _oldEstimateNoiseLevel1D(y, factor=factor)


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################



class NoiseThresholdGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kwds):
    super(NoiseThresholdGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
    self._parent = parent

    self.estimateNoiseThresholdLabel = Label(self.pipeFrame, EstimateNoiseThreshold, grid=(0, 0))
    setattr(self, EstimateNoiseThreshold,
            CheckBox(self.pipeFrame, checked=DefaultEstimateNoiseThreshold, callback=self._manageButtons, grid=(0, 1)))

    self.noiseThresholdLabel = Label(self.pipeFrame, text=NoiseThreshold, grid=(1, 0))
    setattr(self, NoiseThreshold, GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application, colour='green',
                                                        orientation='h', grid=(1, 1)))
    self._manageButtons()

  def _manageButtons(self):
    checkBox = _getWidgetByAtt(self, EstimateNoiseThreshold)
    noiseThreshold = _getWidgetByAtt(self, NoiseThreshold)
    if checkBox.isChecked():
      noiseThreshold.setDisabled(True)
    else:
      noiseThreshold.setDisabled(False)

  def _closeBox(self):
    'remove the lines from plotwidget if any'
    _getWidgetByAtt(self, NoiseThreshold)._turnOffPositionPicking()
    self.closeBox()



########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class NoiseThresholdPipe(SpectraPipe):

  guiPipe = NoiseThresholdGuiPipe
  pipeName = PipeName

  _kwargs = {
             EstimateNoiseThreshold : DefaultEstimateNoiseThreshold,
             NoiseThreshold: DefaultNoiseThreshold
            }

  def runPipe(self, spectra):
    '''
    For Now this pipe is a special case because it doesn't return a new inputData for the next pipe, but set
    _kwargs in the pipeline and will be available for the next pipes they might need more then once.
    If this is run twice, the pipeline will use only the last set.
    Spectra is not really needed for this pipe. But is essential for the base class pipe.
    '''

    for spectrum in spectra:
      if spectrum is not None:
        if self._kwargs[EstimateNoiseThreshold]:
          spectrum.noiseLevel = _getNoiseThreshold(spectrum)
          self._kwargs.update({NoiseThreshold:[spectrum.noiseLevel,-spectrum.noiseLevel]})
        else:
          spectrum.noiseLevel = max(self._kwargs[NoiseThreshold])

      self.pipeline._kwargs.update(self._kwargs)

    return spectra



NoiseThresholdPipe.register() # Registers the pipe in the pipeline


