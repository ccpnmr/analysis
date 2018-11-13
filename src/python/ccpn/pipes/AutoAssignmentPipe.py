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
__date__ = "$Date: 2017-05-20 10:28:42 +0000 (Sun, May 28, 2017) $"
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
from ccpn.ui.gui.widgets.Widget import Widget

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.pipes.lib._getNoiseLevel import _getNoiseLevelForPipe
from ccpn.util.Logging import getLogger , _debug3

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName =  'Automated Assignment'

Mode = 'Mode'
ToleranceMatches = 'Tolerances'
HToleranceMatches = 'H'
CToleranceMatches = 'C'
NToleranceMatches = 'N'
Backbone = 'Backbone'
SideChain = 'Sidechain'
Iterations = 'Iterations'
MinAccuracy = 'MinAccuracy'

DefaultMode = Backbone
DefaultHToleranceMatches = 0.01
DefaultCToleranceMatches = 0.1
DefaultNToleranceMatches = 0.1
DefaultOthersToleranceMatches = 1.0

Tolerances = {HToleranceMatches:DefaultHToleranceMatches,
              NToleranceMatches:DefaultNToleranceMatches,
              CToleranceMatches:DefaultCToleranceMatches}

DefaultMinAccuracy = 10
DefaultIterations = 15000
DefaultEngine = 'CCPN 1'


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

# This Pipe has not been implemented yet. Gui Mock type only

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################

# This Pipe has not been implemented yet. Gui Mock type only



class AutomatedAssignmentGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kwds):
    super(AutomatedAssignmentGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
    self._parent = parent

    row = 0
    modeLabel = Label(self.pipeFrame, text=Mode, grid=(row, 0))
    setattr(self, Mode, PulldownList(self.pipeFrame, texts=[Backbone,SideChain], grid=(row, 1)))

    row += 1
    tolerancesLabel = Label(self.pipeFrame, text=ToleranceMatches, grid=(row, 0), vAlign='t')
    holder = Widget(self.pipeFrame, grid=(row, 1), setLayout=True,  vAlign='t')
    for i, (key, value) in enumerate(Tolerances.items()):
      setattr(self, ToleranceMatches, DoubleSpinbox(holder, prefix=key, value=value, grid=(i, 1)))

    row += 1
    accuracyLabel = Label(self.pipeFrame, text=MinAccuracy, grid=(row, 0))
    setattr(self, ToleranceMatches, DoubleSpinbox(self.pipeFrame, value=DefaultMinAccuracy, grid=(row, 1)))

    row += 1
    iterationsLabel = Label(self.pipeFrame, text=Iterations, grid=(row, 0))
    setattr(self, Iterations, DoubleSpinbox(self.pipeFrame, value=DefaultIterations, grid=(row, 1)))

########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################

# This Pipe has not been implemented yet. Gui Mock type only



class AutomatedAssignmentPipe(SpectraPipe):

  guiPipe = AutomatedAssignmentGuiPipe
  pipeName = PipeName


  def runPipe(self, spectra):

    getLogger().warning('%s Has Not Been Implemented Yet' %PipeName)

    return spectra



# AutomatedAssignmentPipe.register() # Registers the pipe in the pipeline
#
#
# if __name__ == '__main__': # Gui Test
#   from ccpn.ui.gui.widgets.PipelineWidgets import testGuiPipe
#   testGuiPipe(AutomatedAssignmentGuiPipe)