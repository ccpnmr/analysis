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
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_POSTPROCESSING
from ccpn.pipes.lib.Scale1Dspectra import scaleSpectraByRegion
from ccpn.util.Logging import getLogger

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Scale spectra'
ReferenceRegion = 'Reference_Region'
DefaultReferenceRegion = (0.5, -0.5)
EnginesVar = 'Engines'

Min = 'min'
Max = 'max'
Mean = 'mean'
Engines = [Mean, Min, Max]

DefaultEngine = 'mean'
NotAvailable = 'Not Available'


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class Scale1DGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kw):
        super(Scale1DGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw)
        self.parent = parent

        row = 0
        # target region
        self.tregionLabel = Label(self.pipeFrame, text=ReferenceRegion, grid=(row, 0))
        setattr(self, ReferenceRegion, GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application,
                                                               values=DefaultReferenceRegion, orientation='v',
                                                               decimals=4,
                                                               step=0.001,
                                                               grid=(row, 1)))

        row += 1
        #  Engines
        self.enginesLabel = Label(self.pipeFrame, EnginesVar, grid=(row, 0))
        setattr(self, EnginesVar, PulldownList(self.pipeFrame, texts=Engines, grid=(row, 1)))

    def _closePipe(self):
        'remove the lines from plotwidget if any'
        _getWidgetByAtt(self, ReferenceRegion)._turnOffPositionPicking()
        self.closePipe()


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class  Scale1DPipe(SpectraPipe):
    """
    Apply  phasing to all the spectra in the pipeline
    """

    guiPipe = Scale1DGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_POSTPROCESSING


    _kwargs = {
        ReferenceRegion: DefaultReferenceRegion,
        EnginesVar: DefaultEngine
        }

    def runPipe(self, spectra):
        '''
        :param spectra: inputData
        :return: scaled spectra
        '''
        referenceRegion = self._kwargs[ReferenceRegion]
        engine = self._kwargs[EnginesVar]

        if self.project is not None:
            if spectra:
                # scaleSpectraByStd(spectra)
                scaleSpectraByRegion(spectra, referenceRegion, engine,)
                getLogger().info('Scale 1D completed')

                return spectra
            else:
                getLogger().warning('Spectra not present. Add spectra first')
                return spectra

Scale1DPipe.register()  # Registers the pipe in the pipeline
