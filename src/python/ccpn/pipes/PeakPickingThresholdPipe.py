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

PipeName = 'Peak Picking Thresholds'
ManualThresholdLimits = 'ManualThresholdLimits'
Auto = 'Auto'
Manual = 'Manual'
Modes = [Auto, Manual]
Mode = 'Mode'
DefaultMode = Auto
DefaultThreshold = [1e2, -1e2]
DefaultMultiplier = 1.41


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class PeakPickingThresholdGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(PeakPickingThresholdGuiPipe, self)
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
        self.noiseThresholdLabel = Label(self.pipeFrame, text=ManualThresholdLimits, grid=(i, 0))
        setattr(self, ManualThresholdLimits, GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application, colour='green',
                                                                     orientation='h', decimals=4,
                                                                     step=0.001, grid=(i, 1)))

        self._changeMode()

    def _changeMode(self, *args):
        modeWidget = _getWidgetByAtt(self, Mode)
        mode = modeWidget.get()
        if mode == Auto:
            self._disableManualNoiseThresholdWidget(True)
        else:
            self._disableManualNoiseThresholdWidget(False)

    def _disableManualNoiseThresholdWidget(self, value:bool):
        manualNoiseThresholdW = _getWidgetByAtt(self, ManualThresholdLimits)
        manualNoiseThresholdW.setDisabled(value)

    def _closePipe(self):
        'remove the lines from plotwidget if any'
        _getWidgetByAtt(self, ManualThresholdLimits)._turnOffPositionPicking()
        self.closePipe()


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class PeakPickingThresholdPipe(SpectraPipe):
    guiPipe = PeakPickingThresholdGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_GENERIC


    _kwargs = {
        ManualThresholdLimits: DefaultThreshold,
        Mode                 : DefaultMode,
        }

    def runPipe(self, spectra, **kwargs):
        '''
        Calculate the positiveContourBase/negativeContourBase which are used by the peakPickers as  the  peakPicking limits
        '''

        for spectrum in spectra:
            if spectrum is not None:
                if self._kwargs[Mode] == Auto:
                    positiveContourBase = spectrum.dataSource._estimateInitialContourBase()
                    negativeContourBase = -positiveContourBase
                else:
                    positiveContourBase =  max(self._kwargs[ManualThresholdLimits])
                    negativeContourBase = min(self._kwargs[ManualThresholdLimits])
                    if negativeContourBase > 0 or negativeContourBase == positiveContourBase:
                        negativeContourBase = -positiveContourBase

                # set the countourBase values which are used as peakPicking limits
                spectrum.positiveContourBase = positiveContourBase
                spectrum.negativeContourBase = negativeContourBase

            self.pipeline._kwargs.update(self._kwargs)

        return spectra


PeakPickingThresholdPipe.register()  # Registers the pipe in the pipeline
