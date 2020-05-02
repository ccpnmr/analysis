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
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe, PIPE_ANALYSIS
from ccpn.pipes.lib._getNoiseLevel import _getNoiseLevelForPipe
from ccpn.pipes.lib.AreaCalculation import _addAreaValuesToPeaks
from ccpn.util.Logging import getLogger


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Find Multiplets'

ExcludeRegions = 'Exclude_Regions'
ReferencePeakList = 'Reference_PeakList'
NoiseThreshold = 'Noise_Threshold'
NegativePeaks = 'Negative_Peaks'
MinimalLineWidth = 'Minimal_LineWidth'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'

DefaultMinimalLineWidth = 0.01
DefaultReferencePeakList = -1
DefaultNoiseThreshold = [0.0, 0.0]
DefaultExcludeRegions = [[0.0, 0.0], [0.0, 0.0]]

INFO = "This Pipe will group existing peaks in Multiplets. Volume, lineWidths," \
       " and position will be calculated for new multiplets or derived from the peaks values."


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class FindMultipletsGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName
    info = INFO

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(FindMultipletsGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0
        # self.peakListLabel = Label(self.pipeFrame, ReferencePeakList, grid=(row, 0))
        # setattr(self, ReferencePeakList, Spinbox(self.pipeFrame, value=0, max=0, grid=(row, 1)))
        # row += 1
        self.peakListLabel = Label(self.pipeFrame, MinimalLineWidth, grid=(row, 0))
        setattr(self, MinimalLineWidth, DoubleSpinbox(self.pipeFrame, value=DefaultMinimalLineWidth, grid=(row, 1)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class FindMultipletsPipe(SpectraPipe):
    guiPipe = FindMultipletsGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_ANALYSIS

    _kwargs = {

        ExcludeRegions  : DefaultExcludeRegions,
        NoiseThreshold  : DefaultNoiseThreshold,
        NegativePeaks   : False,
        MinimalLineWidth: DefaultMinimalLineWidth,
        }

    def runPipe(self, spectra):
        '''
        :param data:
        :return:
        '''
        if NoiseThreshold not in self._kwargs:
            self._kwargs.update({NoiseThreshold: DefaultNoiseThreshold})

        positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])
        minimalLineWidth = self._kwargs[MinimalLineWidth]

        for spectrum in spectra:
            noiseThreshold = _getNoiseLevelForPipe(cls=self, spectrum=spectrum, estimateNoiseThreshold_var=EstimateNoiseThreshold,
                                                   noiseThreshold_var=NoiseThreshold)
            if noiseThreshold and len(noiseThreshold) >= 1:
                positiveNoiseThreshold = noiseThreshold[1]

            peakListIndex = int(DefaultReferencePeakList)
            if len(spectrum.peakLists) >= peakListIndex:
                referencePeakList = spectrum.peakLists[peakListIndex]
                if referencePeakList is not None:
                    if referencePeakList.peaks:
                        _addAreaValuesToPeaks(spectrum, referencePeakList, noiseThreshold=positiveNoiseThreshold, minimalLineWidth=minimalLineWidth)
                    else:
                        getLogger().warning('Error: Found no peaks to assign a volume value. Pick peaks first.')
            else:
                getLogger().warning('Error: PeakLists not found. Add a new PeakList first')

        return spectra


FindMultipletsPipe.register()  # Registers the pipe in the pipeline
