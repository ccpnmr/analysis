#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:39 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
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
from ccpn.ui.gui.popups.PickPeaks1DPopup import ExcludeRegions as ER

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Exclude Solvent Regions'
ExcludeRegions = 'Exclude_Regions'
selectionLabel = "Select_Regions_or_solvents_to_exclude"


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

## NONE

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################

class ExcludeRegionsGuiPipe(GuiPipe):
    preferredPipe = False
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(ExcludeRegionsGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent
        setattr(self, ExcludeRegions, ER(self.pipeFrame, labelAlign='l', selectionLabel=selectionLabel, grid=(0, 0)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class ExcludeRegionsPipe(SpectraPipe):
    guiPipe = ExcludeRegionsGuiPipe
    pipeName = PipeName
    _kwargs = {
        ExcludeRegions: [[], []]
        }

    def runPipe(self, spectra):
        '''
        :get excluded region of the spectrum and add to the pipeline kwargs.
        Spectra is not really needed for this pipe. But is essential for the base class pipe.
        '''

        self.pipeline._kwargs.update(self._kwargs)
        return spectra


ExcludeRegionsPipe.register()  # Registers the pipe in the pipeline
