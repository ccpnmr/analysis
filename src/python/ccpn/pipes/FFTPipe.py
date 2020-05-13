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
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
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

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_PROCESSING
from ccpn.util.Logging import getLogger

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'DEMO2 FFT'


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class FFTGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kw):
        super(FFTGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw)
        self.parent = parent


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class FFT1DPipe(SpectraPipe):
    """
    Apply  phasing to all the spectra in the pipeline
    """

    guiPipe = FFTGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_PROCESSING

    _kwargs = {
        }

    def runPipe(self, spectra):
        '''
        FFT
        '''

        if self.project is not None:
            if spectra:
                for spectrum in spectra:
                    if spectrum:
                        data = None
                        # spectrum.intensities = ng.proc_base.fft(spectrum.intensities)

                getLogger().info('fft Demo completed')

                return spectra
            else:
                getLogger().warning('fft failed. Returned original spectra')
                return spectra


# FFT1DPipe.register()  # Registers the pipe in the pipeline
