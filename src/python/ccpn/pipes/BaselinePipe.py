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
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe, _getWidgetByAtt

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
import numpy as np
from ccpn.util.Logging import getLogger, _debug3
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

    _kwargs = {

        }

    def runPipe(self, spectra):
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
