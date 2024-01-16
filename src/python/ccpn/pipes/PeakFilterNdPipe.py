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
__dateModified__ = "$dateModified: 2024-01-16 17:48:56 +0000 (Tue, January 16, 2024) $"
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
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_ANALYSIS
from ccpn.util.Logging import getLogger


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Peak Filter ND'

FilterFactor = 'Filter_Factor'  # NB Mock Paramater
DeletePeaks = 'Delete_Peaks'  # NB Mock Paramater

DefaultFilterFactor = 5.7
DefaultPeakListIndex = -1
DefaultDeletePeaks = False


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

# This Pipe has not been implemented yet. Gui Mock type only

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################

# This Pipe has not been implemented yet. Gui Mock type only


class PeakFilterNdGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(PeakFilterNdGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0
        filterFactorLabel = Label(self.pipeFrame, text=FilterFactor, grid=(row, 0))
        setattr(self, FilterFactor, DoubleSpinbox(self.pipeFrame, value=DefaultFilterFactor, min=0.01, step=0.1, grid=(row, 1)))

        row += 1
        deletePeakLabel = Label(self.pipeFrame, text=DeletePeaks, grid=(row, 0))
        setattr(self, DeletePeaks, CheckBox(self.pipeFrame, text='', checked=True, grid=(row, 1)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################

# This Pipe has not been implemented yet. Gui Mock type only


class PeakFilterNdPipe(SpectraPipe):
    guiPipe = PeakFilterNdGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_ANALYSIS


    _kwargs = {
        FilterFactor: DefaultFilterFactor,
        DeletePeaks : DefaultDeletePeaks,
        }

    def runPipe(self, spectra, **kwargs):
        getLogger().warning('%s Has Not Been Implemented Yet' % PipeName)

        return spectra

# PeakFilterNdPipe.register() # Registers the pipe in the pipeline
