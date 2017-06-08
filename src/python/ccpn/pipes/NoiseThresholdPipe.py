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
from ccpn.ui.gui.popups.PickPeaks1DPopup import ExcludeRegions

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import Pipe
from functools import partial
import copy

defaultParams = {

                 }


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
    self.noiseThreshold = TargetButtonSpinBoxes(self.pipeFrame, application=self.application, orientation='h',
                                              grid=(0, 1))



  ############       Gui Callbacks      ###########



########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class NoiseThresholdPipe(Pipe):

  guiPipe = NoiseThresholdGuiPipe
  pipeName = guiPipe.pipeName



  def runPipe(self, params):
    '''
    :param data:
    :return:
    '''

    self.pipeline._kwargs.update(self._kwargs)
    print(self.pipeline._kwargs,)





NoiseThresholdPipe.register() # Registers the pipe in the pipeline


