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
__dateModified__ = "$dateModified: 2020-08-7 09:32:25 +0000 (Fri, August 7, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2020-08-7 09:30:25 +0000 (Fri, August 7, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================



#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_ANALYSIS
from ccpn.util.Logging import getLogger
from tqdm import tqdm


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Single Maximum Peak 1D'
ExcludeRegions = 'Exclude_Regions'
NoiseThreshold = 'Noise_Threshold'
DefaultNoiseThreshold = [0.0, 0.0]
DefaultExcludeRegions = [[0.0, 0.0], [0.0, 0.0]]
DefaultPeakListIndex = -1


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

# see in ccpn.core.PeakList.py function _pick1DsingleMaximum
# This algorithm uses noise threshold and excluded regions in ppm. Set these using other pipes

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class SingleMaximumPeak1DGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(SingleMaximumPeak1DGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent





########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class SingleMaximumPeak1DPipe(SpectraPipe):
    guiPipe = SingleMaximumPeak1DGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_ANALYSIS

    _kwargs = {
               ExcludeRegions  : DefaultExcludeRegions,
              }

    def runPipe(self, spectra):
        '''
        :param data:
        :return:
        '''
        getLogger().info(self._startedInfo)
        if ExcludeRegions in self.pipeline._kwargs:
            excludeRegions = self.pipeline._kwargs[ExcludeRegions]
        else:
            self._kwargs.update({ExcludeRegions: DefaultExcludeRegions})
            excludeRegions = self._kwargs[ExcludeRegions]
        from ccpn.core.lib.ContextManagers import  undoBlockWithoutSideBar, notificationEchoBlocking
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                for spectrum in tqdm(self.inputData):
                    if len(spectrum.peakLists) > 0:
                        if NoiseThreshold in self.pipeline._kwargs:
                            noiseThresholds = self.pipeline._kwargs[NoiseThreshold]
                            spectrum.noiseLevel = max(noiseThresholds) or None
                            spectrum.negativeNoiseLevel = min(noiseThresholds) or None

                        spectrum.peakLists[DefaultPeakListIndex]._pick1DsingleMaximum(maxNoiseLevel=spectrum.noiseLevel,
                                                                              minNoiseLevel=spectrum.negativeNoiseLevel,
                                                                              ignoredRegions=excludeRegions,
                                                                              )
                    else:
                        getLogger().warning('Error: PeakList not found for Spectrum: %s. Add a new PeakList first' % spectrum.pid)
        getLogger().info(self._finishedInfo)
        return spectra


SingleMaximumPeak1DPipe.register()  # Registers the pipe in the pipeline
