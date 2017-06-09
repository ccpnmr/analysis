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
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.LinearRegionsPlot import TargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Label import Label

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import Pipe


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################



########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################



class NoiseThresholdGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = 'Noise Threshold'

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(NoiseThresholdGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    self.noiseThresholdLabel = Label(self.pipeFrame, text="Select Noise threshold", grid=(0, 0))
    self.noiseThreshold = TargetButtonSpinBoxes(self.pipeFrame, application=self.application, orientation='h', grid=(0, 1))




########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class NoiseThresholdPipe(Pipe):

  guiPipe = NoiseThresholdGuiPipe
  pipeName = guiPipe.pipeName



  def runPipe(self, params):
    '''

    For Now this pipe is a special case because it doesn't return a new inputData for the next pipe, but set
    _kwargs in the pipeline and will be available for the next pipes they might need more then once.
    If this is run twice, the pipeline will use only the last set.

    '''

    self.pipeline._kwargs.update(self._kwargs)





NoiseThresholdPipe.register() # Registers the pipe in the pipeline


