#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-11-14 17:24:16 +0000 (Tue, November 14, 2023) $"
__version__ = "$Revision: 3.2.0 $"
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
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_GENERIC
from ccpn.core.lib.SpectrumLib import _filterROI1Darray

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Noise Threshold'
ManualNoiseThreshold = 'Noise_Threshold'
UseRegion = 'Calibration_region'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'
PickingMultiplier = 'PickingMultiplier'
Auto = 'Auto'
Manual = 'Manual'
Modes = [Auto, Manual]
Mode = 'Mode'
DefaultMode = Auto
DefaultNoiseThreshold = [0, 0]
DefaultMultiplier = 1.41


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class NoiseThresholdGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(NoiseThresholdGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent
        i=0

        self.modeCalculationLabel = Label(self.pipeFrame, Mode, grid=(i, 0))
        setattr(self, Mode, RadioButtons(self.pipeFrame,
                                                    texts=Modes, selectedInd=0,
                                                    callback=self._changeMode,
                                                    direction='v', grid=(i, 1)))

        # manual noise widgets
        i += 1
        self.noiseThresholdLabel = Label(self.pipeFrame, text=ManualNoiseThreshold, grid=(i, 0))
        setattr(self, ManualNoiseThreshold, GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application, colour='green',
                                                                    orientation='h', decimals=4,
                                                                    step=0.001, grid=(i, 1)))

        i += 1
        self.peakPickingMultiplierLabel = Label(self.pipeFrame, text='Peak Picking Threshold Multiplier', grid=(i, 0))
        setattr(self, PickingMultiplier, DoubleSpinbox(self.pipeFrame, application=self.application,
                                                       value = DefaultMultiplier,
                                                       decimals=2,
                                                        step=0.1, grid=(i, 1)))
        self._changeMode()

    def _changeMode(self, *args):
        modeWidget = _getWidgetByAtt(self, Mode)
        mode = modeWidget.get()
        if mode == Auto:
            self._disableManualNoiseThresholdWidget(True)
        else:
            self._disableManualNoiseThresholdWidget(False)

    def _disableManualNoiseThresholdWidget(self, value:bool):
        manualNoiseThresholdW = _getWidgetByAtt(self, ManualNoiseThreshold)
        manualNoiseThresholdW.setDisabled(value)

    def _closePipe(self):
        'remove the lines from plotwidget if any'
        _getWidgetByAtt(self, ManualNoiseThreshold)._turnOffPositionPicking()
        self.closePipe()


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class NoiseThresholdPipe(SpectraPipe):
    guiPipe = NoiseThresholdGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_GENERIC


    _kwargs = {
        ManualNoiseThreshold: DefaultNoiseThreshold,
        Mode                : DefaultMode,
        PickingMultiplier :DefaultMultiplier
        }

    def runPipe(self, spectra):
        '''
        For Now this pipe is a special case because it doesn't return a new inputData for the next pipe, but set
        _kwargs in the pipeline and will be available for the next pipes they might need more then once.
        If this is run twice, the pipeline will use only the last set.
        Spectra is not really needed for this pipe. But is essential for the base class pipe.
        '''

        for spectrum in spectra:
            if spectrum is not None:
                if self._kwargs[Mode] == Auto:
                    spectrum.noiseLevel = spectrum.estimateNoise()
                    spectrum.negativeNoiseLevel =  -spectrum.noiseLevel
                else:
                    noiseLevel =  max(self._kwargs[ManualNoiseThreshold])
                    negativeNoiseLevel = min(self._kwargs[ManualNoiseThreshold])
                    if negativeNoiseLevel > 0 or negativeNoiseLevel == noiseLevel:
                        negativeNoiseLevel = -noiseLevel
                    spectrum.noiseLevel = noiseLevel
                    spectrum.negativeNoiseLevel = negativeNoiseLevel
                # set the countourBase values which are used as peakPicking limits
                pickingMultiplier = self._kwargs.get(PickingMultiplier, 1)
                noiseLevel = spectrum.noiseLevel or 0
                negativeNoiseLevel = spectrum.negativeNoiseLevel or 0
                spectrum.positiveContourBase = noiseLevel * pickingMultiplier
                spectrum.negativeContourBase = negativeNoiseLevel * pickingMultiplier

                self._kwargs.update({ManualNoiseThreshold: [spectrum.noiseLevel, spectrum.negativeNoiseLevel]})
            self.pipeline._kwargs.update(self._kwargs)

        return spectra


NoiseThresholdPipe.register()  # Registers the pipe in the pipeline
