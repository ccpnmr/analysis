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
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_ANALYSIS
from ccpn.core.lib.AssignmentLib import refitPeaks
from ccpn.core.lib.peakUtils import estimateVolumes

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Refit Peaks'
PeakListIndice = 'PeakList_Indice'
DefaultPeakListIndice = -1
EstimateVolume = 'Estimate_Volume'
DefaultEstimateVolumes = True



########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class RefitPeaksGuiPipe(GuiPipe):
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kw):
        super(RefitPeaksGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw)
        self.parent = parent

        row = 0

        self.indPeakListsLabel = Label(self.pipeFrame, PeakListIndice, grid=(row, 0))
        setattr(self, PeakListIndice, Label(self.pipeFrame, 'Last created (Default)', grid=(row, 1)))

        row += 1
        self.volumesLabel = Label(self.pipeFrame, EstimateVolume, grid=(row, 0))
        setattr(self, EstimateVolume, CheckBox(self.pipeFrame, checked=DefaultEstimateVolumes, callback=None, grid=(row, 1)))





########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class  RefitPeaksPipe(SpectraPipe):
    """
    Apply  phasing to all the spectra in the pipeline
    """

    guiPipe = RefitPeaksGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_ANALYSIS

    _kwargs = {
                EstimateVolume: DefaultEstimateVolumes,
                PeakListIndice: DefaultPeakListIndice,
               }

    def runPipe(self, spectra, **kwargs):
        '''
        :param spectra: inputData
        :return: spectra
        '''

        if self.project is not None:
            for spectrum in spectra:
                if len(spectrum.peakLists)>0:
                    peakList = spectrum.peakLists[DefaultPeakListIndice]
                    refitPeaks(peakList.peaks)
                    if self._kwargs[EstimateVolume]:
                        estimateVolumes(peakList.peaks)
            return spectra


RefitPeaksPipe.register()  # Registers the pipe in the pipeline
