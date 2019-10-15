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
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe, _getWidgetByAtt
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.pipes.lib._getNoiseLevel import _getNoiseLevelForPipe
from ccpn.util.Logging import getLogger, _debug3


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Calculate Integrals'
IntegralListIndex = 'Add_To_Integral'
NoiseThreshold = 'Noise_Threshold'
MinimalLineWidth = 'Minimal_LineWidth'
FindPeak = 'Find_peak'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'

DefaultMinimalLineWidth = 0.01
DefaultNoiseThreshold = [0.0, 0.0]
DefaultIntegralListIndex = -1
DefaultFindPeak = True


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class CalculateAreaGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(CalculateAreaGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0

        self.mlwLabel = Label(self.pipeFrame, MinimalLineWidth, grid=(row, 0))
        setattr(self, MinimalLineWidth, DoubleSpinbox(self.pipeFrame, value=DefaultMinimalLineWidth, grid=(row, 1)))

        row += 1
        self.peakLabel = Label(self.pipeFrame, FindPeak, grid=(row, 0))
        setattr(self, FindPeak, CheckBox(self.pipeFrame, checked=DefaultFindPeak, grid=(row, 1)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class CalculateAreaPipe(SpectraPipe):
    guiPipe = CalculateAreaGuiPipe
    pipeName = PipeName

    _kwargs = {
        NoiseThreshold        : DefaultNoiseThreshold,
        MinimalLineWidth      : DefaultMinimalLineWidth,
        EstimateNoiseThreshold: True,
        FindPeak              : DefaultFindPeak
        }

    def runPipe(self, spectra):
        '''
        :param data:
        :return:
        '''

        if NoiseThreshold not in self._kwargs:
            self._kwargs.update({NoiseThreshold: DefaultNoiseThreshold})

        minimalLineWidth = self._kwargs[MinimalLineWidth]
        positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])
        findPeak = self._kwargs[FindPeak]

        for spectrum in spectra:
            noiseThreshold = _getNoiseLevelForPipe(cls=self, spectrum=spectrum,
                                                   estimateNoiseThreshold_var=EstimateNoiseThreshold,
                                                   noiseThreshold_var=NoiseThreshold)
            if noiseThreshold:
                positiveNoiseThreshold = noiseThreshold[1]

            if len(spectrum.integralLists) > 0:
                spectrum.integralLists[DefaultIntegralListIndex].automaticIntegral1D(minimalLineWidth=float(minimalLineWidth),
                                                                                     noiseThreshold=positiveNoiseThreshold,
                                                                                     findPeak=findPeak)

            else:
                integralList = spectrum.newIntegralList()
                integralList.automaticIntegral1D(minimalLineWidth=float(minimalLineWidth), noiseThreshold=positiveNoiseThreshold,
                                                 findPeak=findPeak)

        return spectra


CalculateAreaPipe.register()  # Registers the pipe in the pipeline
