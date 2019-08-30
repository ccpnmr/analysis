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
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe, _getWidgetByAtt
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox, DoubleSpinbox
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from scipy import signal
import numpy as np
from scipy import stats
from ccpn.util.Logging import getLogger, _debug3


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Referencing Spectra'
Shift = 'Shift'
Origin = 'Origin'
Target = 'Target'

DefaultOrigin = 0.10
DefaultTarget = 0.00


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


def addShiftToSpectra(spectra, shift):
    alignedSpectra = []
    for sp in spectra:
        if shift is not None:
            sp.positions -= float(shift)
            alignedSpectra.append(sp)
    return alignedSpectra


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class ReferencingSpectraGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(ReferencingSpectraGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        _paramList = [(Origin, DefaultOrigin), (Target, DefaultTarget)]
        for i, params in enumerate(_paramList):
            Label(self.pipeFrame, params[0], grid=(i, 0))
            setattr(self, params[0], DoubleSpinbox(self.pipeFrame, value=params[1],
                                                   max=1000, min=-1000,
                                                   decimals=5, step=0.1,
                                                   grid=(i, 1)))


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class ReferencingSpectra(SpectraPipe):
    """
    Add a shift value to all the spectra in the pipeline
    """

    guiPipe = ReferencingSpectraGuiPipe
    pipeName = PipeName

    _kwargs = {
        Origin: DefaultOrigin,
        Target: DefaultTarget
        }

    def runPipe(self, spectra):
        '''
        :param spectra: inputData
        :return: aligned spectra
        '''
        origin = self._kwargs[Origin]
        target = self._kwargs[Target]

        if self.project is not None:
            if spectra:
                shift = origin - target
                return addShiftToSpectra(spectra, shift)
            else:
                getLogger().warning('Spectra not Aligned. Returned original spectra')
                return spectra


ReferencingSpectra.register()  # Registers the pipe in the pipeline
