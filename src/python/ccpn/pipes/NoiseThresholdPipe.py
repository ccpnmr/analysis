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
from ccpn.ui.gui.widgets.LinearRegionsPlot import TargetButtonSpinBoxes
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.core.PeakList import _filterROI1Darray, estimateNoiseLevel1D
import numpy as np


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Noise Threshold'
NoiseThreshold = 'Noise_Threshold'
UseRegion = 'Calibration_region'
EstimateNoiseThreshold = 'Estimate_Noise_Threshold'
IncreaseBySTD = 'Add_STD'

DefaultEstimateNoiseThreshold = True
DefaultNoiseThreshold = [0, 0]
DefaultCalibration_region = [14,12]
DefaultIncreaseBySTD = 0.50

########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

def _getNoiseThreshold(spectrum, roi, stdFactor):
    if spectrum is not None:
        x, y =spectrum.positions, spectrum.intensities
        xRoi, yRoi = _filterROI1Darray(x,y,roi)
        maxNL, minNL = estimateNoiseLevel1D(yRoi, f=100, stdFactor=stdFactor)
        return maxNL, minNL




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
        self.estimateNoiseThresholdLabel = Label(self.pipeFrame, EstimateNoiseThreshold, grid=(i, 0))
        setattr(self, EstimateNoiseThreshold,
                CheckBox(self.pipeFrame, checked=DefaultEstimateNoiseThreshold, callback=self._manageButtons, grid=(i, 1)))
        i += 1
        # auto noise widgets
        self.noiseThresholdLabel = Label(self.pipeFrame, text=UseRegion, grid=(i, 0))
        setattr(self, UseRegion,
                GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application, colour='red',
                                        orientation='v', values=DefaultCalibration_region, grid=(i, 1)))

        i += 1
        self.addError = Label(self.pipeFrame, IncreaseBySTD, grid=(i, 0))
        setattr(self, IncreaseBySTD,
                DoubleSpinbox(self.pipeFrame, value=DefaultIncreaseBySTD, min=0.0, max=None,
                              step=0.5, prefix=None, suffix=None, showButtons=True, decimals=3, grid=(i, 1)))

        # manual noise widgets
        i += 1
        self.noiseThresholdLabel = Label(self.pipeFrame, text=NoiseThreshold, grid=(i, 0))
        setattr(self, NoiseThreshold, GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application, colour='green',
                                                              orientation='h', grid=(i, 1)))
        self._manageButtons()

    def _manageButtons(self):
        checkBox = _getWidgetByAtt(self, EstimateNoiseThreshold)
        noiseThreshold = _getWidgetByAtt(self, NoiseThreshold)
        calibrRegion = _getWidgetByAtt(self, UseRegion)
        addStd = _getWidgetByAtt(self, IncreaseBySTD)

        if checkBox.isChecked():
            noiseThreshold.setDisabled(True)
            calibrRegion.setDisabled(False)
            addStd.setDisabled(False)

        else:
            noiseThreshold.setDisabled(False)
            calibrRegion.setDisabled(True)
            addStd.setDisabled(True)

    def _closePipe(self):
        'remove the lines from plotwidget if any'
        _getWidgetByAtt(self, NoiseThreshold)._turnOffPositionPicking()
        _getWidgetByAtt(self, UseRegion)._turnOffPositionPicking()
        self.closePipe()


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class NoiseThresholdPipe(SpectraPipe):
    guiPipe = NoiseThresholdGuiPipe
    pipeName = PipeName

    _kwargs = {
        EstimateNoiseThreshold: DefaultEstimateNoiseThreshold,
        NoiseThreshold        : DefaultNoiseThreshold,
        UseRegion             : DefaultCalibration_region,
        IncreaseBySTD         : DefaultIncreaseBySTD,
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
                if self._kwargs[EstimateNoiseThreshold]:
                    roi = self._kwargs[UseRegion]
                    stdFactor = self._kwargs[IncreaseBySTD]
                    maxNL, minNL = _getNoiseThreshold(spectrum, roi, stdFactor)
                    spectrum.noiseLevel = maxNL
                    spectrum.negativeNoiseLevel = minNL
                    self._kwargs.update({NoiseThreshold: [spectrum.noiseLevel, minNL]})
                else:
                    spectrum.noiseLevel = max(self._kwargs[NoiseThreshold])

            self.pipeline._kwargs.update(self._kwargs)

        return spectra


NoiseThresholdPipe.register()  # Registers the pipe in the pipeline
