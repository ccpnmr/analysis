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
__version__ = "$Revision: 3.0.b5 $"
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
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.LinearRegionsPlot import TargetButtonSpinBoxes
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Exclude Regions'
Region = 'Region_'
ExcludeRegions = 'Exclude_Regions'


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class ExcludeRegionsGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(ExcludeRegionsGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        self.plusIcon = Icon('icons/plus')
        self.minusIcon = Icon('icons/minus')

        self.addRemoveLabel = Label(self.pipeFrame, text="", grid=(0, 0))
        self.addRemoveButtons = ButtonList(self.pipeFrame, texts=['', ''], icons=[self.plusIcon, self.minusIcon],
                                           callbacks=[self._addRegion, self._deleteRegions], grid=(0, 1))
        self.addRemoveButtons.setMaximumHeight(20)
        self.count = 1

        self.excludeRegion1Label = Label(self.pipeFrame, text=Region + str(self.count), grid=(self.count, 0))
        setattr(self, Region + str(self.count), GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application,
                                                                        orientation='v', grid=(self.count, 1)))
        self.count += 1

    ############       Gui Callbacks      ###########

    def _addRegion(self):
        self.excludeRegionLabel = Label(self.pipeFrame, text=Region + str(self.count), grid=(self.count, 0))
        setattr(self, Region + str(self.count), GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application,
                                                                        orientation='v', grid=(self.count, 1)))

        self.count += 1

    def _deleteRegions(self):
        '''  delete the widget from layout. '''
        positions = []
        for row in range(self.count):
            positions.append((row, 0))
            positions.append((row, 1))
        if (len(positions)) > 1:
            positions = positions[2:]
            if len(positions) > 1:
                positions = positions[-2:]
                for position in positions:
                    item = self.pipeFrame.getLayout().itemAtPosition(*position)
                    if item:
                        w = item.widget()
                        if w:
                            if isinstance(w, GLTargetButtonSpinBoxes):
                                w._turnOffPositionPicking()
                            w.deleteLater()
                self.count -= 1

    def _closeBox(self):
        'remove the lines from plotwidget if any'
        for row in range(self.count - 1):
            self._deleteRegions()
        self.closeBox()


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class ExcludeRegionsPipe(SpectraPipe):
    guiPipe = ExcludeRegionsGuiPipe
    pipeName = PipeName

    _kwargs = {
        ExcludeRegions: [[], []]
        }

    def runPipe(self, spectra):
        '''
        get excluded region of the spectrum and add to the pipeline kwargs.
        Spectra is not really needed for this pipe. But is essential for the base class pipe.
        '''
        regions = []
        for i in self._kwargs.values():
            if isinstance(i, list):
                if len(i) == 2:
                    regions.append(i)

        self._kwargs = {ExcludeRegions: regions}
        self.pipeline._kwargs.update(self._kwargs)

        return spectra


ExcludeRegionsPipe.register()  # Registers the pipe in the pipeline
