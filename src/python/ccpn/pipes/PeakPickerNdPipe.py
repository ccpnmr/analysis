#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:39 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.pipes.lib._getNoiseLevel import _getNoiseLevelForPipe
from ccpn.util.Logging import getLogger, _debug3


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

    _kwargs = {
        DropFactor: DefaultDropFactor,
        NegativePeaks: DefaultNegativePeaks,

        }

    def runPipe(self, spectra):
        '''
        :param data:
        :return:
        '''

        negativePeaks = self._kwargs[NegativePeaks]
        dropFactor = self._kwargs[DropFactor]

        for spectrum in self.inputData:
            if len(spectrum.peakLists) > 0:
                spectrum.peakLists[DefaultPeakListIndex].pickPeaksNd(minDropfactor=dropFactor, doNeg=negativePeaks)
            else:
                getLogger().warning('Error: PeakList not found for Spectrum: %s. Add a new PeakList first' % spectrum.pid)

        return spectra


PeakPickerNdPipe.register()  # Registers the pipe in the pipeline
