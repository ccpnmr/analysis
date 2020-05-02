#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-01 17:08:42 +0100 (Fri, May 01, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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
from ccpn.framework.lib.Pipe import SpectraPipe, PIPE_GENERIC


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################


## Widget variables and/or _kwargs keys


## defaults
ReplaceInputData = 'Replace_Input_Data'
DefaultReplaceInputData = False

## PipeName
PipeName = 'Duplicate Spectra'


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class DuplicateSpectrumGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName
    _alreadyOpened = False

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(DuplicateSpectrumGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent
        DuplicateSpectrumGuiPipe._alreadyOpened = True

        row = 0
        tipText = 'Use the duplicated spectra as new inputData and remove the original spectra from the pipeline.'
        self.replaceInputDataLabel = Label(self.pipeFrame, text=ReplaceInputData, grid=(row, 0))
        setattr(self, ReplaceInputData, CheckBox(self.pipeFrame, text='', checked=DefaultReplaceInputData, tipText=tipText,
                                                 grid=(row, 1)))

    def _updateWidgets(self):
        pass

    def _closePipe(self):
        'reset alreadyOpened flag '
        DuplicateSpectrumGuiPipe._alreadyOpened = False
        self.closePipe()


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class DuplicateSpectrumPipe(SpectraPipe):
    guiPipe = DuplicateSpectrumGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_GENERIC

    _kwargs = {
        ReplaceInputData: DefaultReplaceInputData
        }

    def runPipe(self, spectra):
        '''
        :param spectra: inputData
        :return: new spectra
        '''
        newSpectra = set()
        for spectrum in spectra:
            newspectrum = spectrum._clone1D()
            newSpectra.update([newspectrum])
            newspectrum.spectrumGroups = ()

        replaceInputData = self._kwargs[ReplaceInputData]
        if replaceInputData:
            self.pipeline.updateInputData = True
            self.pipeline.inputData = newSpectra
            return newSpectra
        else:
            spectra = set(spectra)
            spectra.update(newSpectra)
            return spectra


DuplicateSpectrumPipe.register()  # Registers the pipe in the pipeline
