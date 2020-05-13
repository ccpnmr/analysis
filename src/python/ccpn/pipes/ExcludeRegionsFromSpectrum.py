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
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_GENERIC

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Exclude Regions'
Region = 'Region_'
ExcludeRegions = 'Exclude_Regions'
_STORE = '_storeCount'

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
        self.maximumTargetButtonWidgetSize = 25

        self.plusIcon = Icon('icons/plus')
        self.minusIcon = Icon('icons/minus')

        self.addRemoveLabel = Label(self.pipeFrame, text="", grid=(0, 0))
        self.addRemoveButtons = ButtonList(self.pipeFrame, texts=['', ''], icons=[self.plusIcon, self.minusIcon],
                                           callbacks=[self._addRegion, self._deleteRegions], grid=(0, 1))
        self.addRemoveButtons.setMaximumHeight(self.maximumTargetButtonWidgetSize)
        self.count = 1

        # GLSpinboxes start from count = 1 -> 'Region_1'
        # self.excludeRegion1Label = Label(self.pipeFrame, text=Region + str(self.count), grid=(self.count, 0))

        setattr(self, ExcludeRegions + str(self.count), Label(self.pipeFrame, text=Region + str(self.count), grid=(self.count, 0)))
        setattr(self, Region + str(self.count), GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application,
                                                                        orientation='v', decimals=3, grid=(self.count, 1)))

        setattr(self, _STORE, Spinbox(self.pipeFrame, value=self.count, grid=(0, 0), hidden=True)) # used to store how many entries there are

    ############       Gui Callbacks      ###########

    def _addRegion(self):
        print(self.sizeHint().height(), 'before')

        """Also called upon restoring widget state """
        self.count += 1
        # _increase layout size to accommodate the new widgets
        self.setMaximumHeight(self.sizeHint().height() + self.maximumTargetButtonWidgetSize)
        setattr(self, ExcludeRegions + str(self.count), Label(self.pipeFrame, text=Region + str(self.count), grid=(self.count, 0)))
        setattr(self, Region + str(self.count), GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application,
                                                                        decimals=3, orientation='v', grid=(self.count, 1)))
        # self.count += 1
        getattr(self, _STORE).set(self.count)

    def _deleteRegions(self):
            """ delete the widget from layout. """

            # remove GLTargetButtonSpinBoxes and labels
            widgets = [_getWidgetByAtt(self, Region + str(ii+1)) for ii in range(self.count) if _getWidgetByAtt(self, Region + str(ii+1))]
            if widgets:

                # delete the spinbox
                widgets[-1]._turnOffPositionPicking()
                widgets[-1].deleteLater()

                # remove Labels - should correspond to spinboxes above
                labels = [_getWidgetByAtt(self, ExcludeRegions + str(ii+1)) for ii in range(self.count) if _getWidgetByAtt(self, ExcludeRegions + str(ii+1))]
                if labels:
                    labels[-1].deleteLater()

                # update the count
                self.count -= 1
                getattr(self, _STORE).set(self.count)
                # decrease layout sizes
                self.setMaximumHeight(self.sizeHint().height() - self.maximumTargetButtonWidgetSize)


    def _closePipe(self):
        """remove the lines from plotwidget if any"""
        for row in range(self.count):
            self._deleteRegions()
        self.closePipe()

    def restoreWidgetsState(self, **widgetsState):
        """Restore the gui params.
        overide the default function first to recreate the correct number of boxes. Then call the super to restore values.
        """
        count = 0
        for variableName, value in widgetsState.items():
            if variableName == _STORE:  # find the widget which stores the box count
                count = value-1         # remove one as the first is always created as default on init
        if count>1:                     # if more then the first, then create all the rest
            for i in range(count):
                self._addRegion()
        super().restoreWidgetsState(**widgetsState)


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class ExcludeRegionsPipe(SpectraPipe):
    guiPipe = ExcludeRegionsGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_GENERIC

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
