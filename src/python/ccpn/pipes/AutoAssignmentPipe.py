#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-01-16 17:48:55 +0000 (Tue, January 16, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-20 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Widget import Widget

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_ASSIGN
from ccpn.util.Logging import getLogger


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Automated Assignment'

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

Tolerances = {HToleranceMatches: DefaultHToleranceMatches,
              NToleranceMatches: DefaultNToleranceMatches,
              CToleranceMatches: DefaultCToleranceMatches}

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

    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(AutomatedAssignmentGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0
        modeLabel = Label(self.pipeFrame, text=Mode, grid=(row, 0))
        setattr(self, Mode, PulldownList(self.pipeFrame, texts=[Backbone, SideChain], grid=(row, 1)))

        row += 1
        tolerancesLabel = Label(self.pipeFrame, text=ToleranceMatches, grid=(row, 0), vAlign='t')
        holder = Widget(self.pipeFrame, grid=(row, 1), setLayout=True, vAlign='t')
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
    pipeCategory = PIPE_ASSIGN

    def runPipe(self, spectra, **kwargs):
        getLogger().warning('%s Has Not Been Implemented Yet' % PipeName)

        return spectra

# AutomatedAssignmentPipe.register() # Registers the pipe in the pipeline
#
#
# if __name__ == '__main__': # Gui Test
#   from ccpn.ui.gui.widgets.PipelineWidgets import testGuiPipe
#   testGuiPipe(AutomatedAssignmentGuiPipe)
