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
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_POSTPROCESSING
import numpy as np
from ccpn.util.Logging import getLogger
from ccpn.util import Phasing


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Phasing Spectra'
Ph0 = 'Ph0'
Ph1 = 'Ph1'
Pivot = 'Pivot'
Auto = 'Automatic'
DefaultAutoValue = True
DefaultPh0 = 0.0
DefaultPh1 = 0.0
DefaultPivot = 1.0
_paramList = [(Ph0, DefaultPh0), (Ph1, DefaultPh1), (Pivot, DefaultPivot)]


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

def phasing1D(spectrum, ph0, ph1, pivot):
    """

    :param spectrum:
    :param ph0: degrees
    :param ph1:
    :param pivot: in points
    :return: intensities
    """
    data = spectrum.intensities
    pivot = spectrum.spectrumReferences[0].valueToPoint(pivot)
    data = Phasing.phaseRealData(data, ph0, ph1, pivot)
    data1 = np.array(data)

    return data1


def autoPhasing(spectrum, engine='peak_minima'):
    data = spectrum.intensities
    data = Phasing.autoPhaseReal(data, engine)
    return data


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class PhasingSpectraGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kw):
        super(PhasingSpectraGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw)
        self.parent = parent
        i = 0
        Label(self.pipeFrame, Auto, grid=(i, 0))
        setattr(self, Auto, CheckBox(self.pipeFrame, checked=DefaultAutoValue, callback=None,
                                     grid=(i, 1)))
        i += 1
        for i, params in enumerate(_paramList):
            i += 1
            Label(self.pipeFrame, params[0], grid=(i, 0))
            setattr(self, params[0], DoubleSpinbox(self.pipeFrame, value=params[1],
                                                   max=1000, min=-1000,
                                                   decimals=2, step=0.1,
                                                   grid=(i, 1)))

    def _toggleManualSettings(self):
        for i, params in enumerate(_paramList):
            w = getattr(self, params[0])
            w.setEnabled(not w.isEnabled())


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class Phasing1DPipe(SpectraPipe):
    """
    Apply  phasing to all the spectra in the pipeline
    """

    guiPipe = PhasingSpectraGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_POSTPROCESSING

    _kwargs = {
        Ph0  : DefaultPh0,
        Ph1  : DefaultPh0,
        Pivot: DefaultPivot,
        Auto : DefaultAutoValue
        }

    def runPipe(self, spectra, **kwargs):
        '''
        :param spectra: inputData
        :return: aligned spectra
        '''
        ph0 = self._kwargs[Ph0]
        ph1 = self._kwargs[Ph1]
        pivot = self._kwargs[Pivot]
        auto = self._kwargs[Auto]
        if self.project is not None:
            if spectra:
                for spectrum in spectra:
                    if spectrum:
                        if auto:
                            intensities = autoPhasing(spectrum)
                        else:
                            intensities = phasing1D(spectrum, ph0, ph1, pivot)
                        spectrum.intensities = intensities

                getLogger().info('Phasing pipe completed.')

                return spectra
            else:
                getLogger().warning('Spectra not phased. Returned original spectra')
                return spectra


Phasing1DPipe.register()  # Registers the pipe in the pipeline
