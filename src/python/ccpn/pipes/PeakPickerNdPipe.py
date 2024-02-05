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

PipeName = 'Peak Picker ND'

NoiseThreshold = 'Noise_Threshold'
DropFactor = 'Drop_Factor'
NegativePeaks = 'Negative_Peaks'
ExcludeRegions = 'Exclude_Regions'

DefaultDropFactor = 0.1
DefaultExcludeRegions = [[0.0, 0.0], [0.0, 0.0]]
DefaultPeakListIndex = -1
DefaultNegativePeaks = False


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

# see in ccpn.core.PeakList.py function peakFinder1D

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class PeakPickerNdGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(PeakPickerNdGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0
        self.pickNegativeLabel = Label(self.pipeFrame, text=NegativePeaks, grid=(row, 0))
        setattr(self, NegativePeaks, CheckBox(self.pipeFrame, text='', checked=True, grid=(row, 1)))

        row += 1
        self.noiseLevelFactorLabel = Label(self.pipeFrame, text=DropFactor, grid=(row, 0))
        setattr(self, DropFactor, DoubleSpinbox(self.pipeFrame, value=DefaultDropFactor, min=0.01, step=0.1, grid=(row, 1)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class PeakPickerNdPipe(SpectraPipe):
    guiPipe = PeakPickerNdGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_ANALYSIS

    _kwargs = {
        DropFactor   : DefaultDropFactor,
        NegativePeaks: DefaultNegativePeaks,

        }

    def runPipe(self, spectra, **kwargs):
        """
        :param data:
        :return:
        """

        negativePeaks = self._kwargs[NegativePeaks]
        dropFactor = self._kwargs[DropFactor]

        for spectrum in self.inputData:
            if len(spectrum.peakLists) > 0:
                # spectrum.peakLists[DefaultPeakListIndex].pickPeaksNd(minDropFactor=dropFactor, doNeg=negativePeaks)

                peakList = spectrum.peakLists[DefaultPeakListIndex]
                # may create a peakPicker instance if not defined, subject to settings in preferences
                _peakPicker = spectrum.peakPicker
                if _peakPicker:
                    _peakPicker.dropFactor = dropFactor
                    _peakPicker.setLineWidths = True
                    spectrum.pickPeaks(peakList,
                                        spectrum.positiveContourBase,
                                        spectrum.negativeContourBase if negativePeaks else None)

            else:
                getLogger().warning('Error: PeakList not found for Spectrum: %s. Add a new PeakList first' % spectrum.pid)

        return spectra


PeakPickerNdPipe.register()  # Registers the pipe in the pipeline
