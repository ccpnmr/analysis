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
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_POSTPROCESSING
from ccpn.util.Logging import getLogger
from ccpn.core.lib.SpectrumLib import nmrGlueBaselineCorrector


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Baseline Correction'
Window = 'Window'
DefaultWindow = 20


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class BaselineCorrectionGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kw):
        super(BaselineCorrectionGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw)
        self.parent = parent
        # i = 0
        # Label(self.pipeFrame, Auto, grid=(i, 0))
        # setattr(self, Auto, CheckBox(self.pipeFrame, checked=DefaultAutoValue, callback=self._toggleManualSettings,
        #                              grid=(i, 1)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class BaselineCorrection1DPipe(SpectraPipe):
    """
    Apply  phasing to all the spectra in the pipeline
    """

    guiPipe = BaselineCorrectionGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_POSTPROCESSING

    _kwargs = {

        }

    def runPipe(self, spectra, **kwargs):
        '''
        :param spectra: inputData
        :return: aligned spectra
        '''

        if self.project is not None:
            if spectra:
                for spectrum in spectra:
                    if spectrum:
                        intensities = nmrGlueBaselineCorrector(spectrum.intensities)
                        spectrum.intensities = intensities

                getLogger().info('Baseline Correction completed')

                return spectra
            else:
                getLogger().warning('Spectra not phased. Returned original spectra')
                return spectra


BaselineCorrection1DPipe.register()  # Registers the pipe in the pipeline
