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
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_PROCESSING
from ccpn.util.Logging import getLogger

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'DEMO4 DI'


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class DIGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kw):
        super(DIGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw)
        self.parent = parent


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class DIPipe(SpectraPipe):
    """
    Apply  phasing to all the spectra in the pipeline
    """

    guiPipe = DIGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_PROCESSING

    _kwargs = {
        }

    def runPipe(self, spectra, **kwargs):
        """
        Discard the imaginaries
        """

        if self.project is not None:
            if spectra:
                for spectrum in spectra:
                    if spectrum:
                        data = None
                        # spectrum.intensities = ng.proc_base.di(spectrum.intensities)
                getLogger().info('DI Demo completed')

                return spectra
            else:
                getLogger().warning('DI failed. Returned original spectra')
                return spectra


# DIPipe.register()  # Registers the pipe in the pipeline
