#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-10-10 15:28:07 +0100 (Mon, October 10, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

######## core imports ########
from functools import partial
from ccpn.util.Logging import getLogger
from ccpn.core.Peak import Peak
from ccpn.core.Substance import Substance
from ccpn.core.Spectrum import Spectrum
from ccpn.core.DataTable import DataTable
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiManagers import ExperimentAnalysisHandlerABC
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import PanelUpdateState

class CoreNotifiersHandler(ExperimentAnalysisHandlerABC):
    """
    A private class containing all Notifiers for the ExperimentAnalysis GuiModule
    """
    _notifiers = {}

    def start(self):
        """ Initialise all notifiers for the guiModule """
        if self.guiModule.mainWindow is not None:
            self._setupNotifiers(self.guiModule)
            getLogger().debug2(f'Setting up notifiers for {self.guiModule}')
        else:
            getLogger().debug(f'Cannot start notifiers for {self.guiModule}')

    def close(self):
        """ Unregister all notifiers for the guiModule """
        self._unRegisterNotifiers()
        getLogger().debug2(f'Unregistering notifiers for {self.guiModule}')

    @staticmethod
    def _setupNotifiers(gm):
        """
        :param gm: GuiModule instance
        :return: None. Set the Notifiers for the GuiModule
        """

        CoreNotifiersHandler._notifiers.update({
            'onCurrentPeak'         : Notifier(gm.current,
                                               [Notifier.CURRENT],
                                               targetName=Peak._currentAttributeName,
                                               callback=partial(CoreNotifiersHandler._onCurrentPeak, gm),
                                               onceOnly=True),
            'onCurrentNmrResidue'   : Notifier(gm.current,
                                               [Notifier.CURRENT],
                                               targetName=Substance._currentAttributeName,
                                               callback=partial(CoreNotifiersHandler.onCurrentNmrResidue, gm),
                                               onceOnly=True),
            'onDeletePeak'          : Notifier(gm.project,
                                               [Notifier.DELETE],
                                               targetName=Peak.className,
                                               callback=partial(CoreNotifiersHandler._peakDeleted, gm),
                                               onceOnly=True),
            'onCreatePeak'          : Notifier(gm.project,
                                               [Notifier.CREATE],
                                               targetName=Peak.className,
                                               callback=partial(CoreNotifiersHandler._peakCreated, gm),
                                               onceOnly=True),
            'onChangePeak'          : Notifier(gm.project,
                                               [Notifier.CHANGE],
                                               targetName=Peak.className,
                                               callback=partial(CoreNotifiersHandler._peakChanged, gm),
                                               onceOnly=True),
            'onCreateDataTable'     : Notifier(gm.project,
                                               [Notifier.CREATE],
                                               targetName=DataTable.className,
                                               callback=partial(CoreNotifiersHandler._dataTableCreated, gm),
                                               onceOnly=True),
            'onRenameDataTable'     : Notifier(gm.project,
                                               [Notifier.RENAME],
                                               targetName=DataTable.className,
                                               callback=partial(CoreNotifiersHandler._dataTableRenamed, gm),
                                               onceOnly=True),
            'onDeleteDataTable'     : Notifier(gm.project,
                                               [Notifier.DELETE],
                                               targetName=DataTable.className,
                                               callback=partial(CoreNotifiersHandler._dataTableDeleted, gm),
                                               )
        })

    @staticmethod
    def _unRegisterNotifiers():
        for k,v in CoreNotifiersHandler._notifiers.items():
            if v is not None:
                v.unRegister()

    #### PEAKS ####
    @staticmethod
    def _onCurrentPeak(guiModule, data):
        peak = data[Notifier.OBJECT]

        pass

    @staticmethod
    def _peakChanged(guiModule, data):
        peak = data[Notifier.OBJECT]
        backendHandler = guiModule.backendHandler
        settingsPanelHandler = guiModule.settingsPanelHandler
        inputSettings = settingsPanelHandler.getInputDataSettings()
        sgPids = inputSettings.get(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection, [None])
        if not sgPids:
            return
        spGroup = guiModule.project.getByPid(sgPids[-1])
        for inputData in backendHandler.inputDataTables:
            inputData.data.buildFromSpectrumGroup(spGroup, filteredPeaks=[peak])
        backendHandler._needsRefitting = True
        toolbar = guiModule.panelHandler.getToolBarPanel()
        if toolbar:
            toolbar.setUpdateState(PanelUpdateState.DETECTED)

    @staticmethod
    def _applyChangesToQueue(guiModule):
        pass

    @staticmethod
    def _peakDeleted(guiModule, data):
        """
        """
        peak = data[Notifier.OBJECT]
        getLogger().warn('_peakDeleted notifier not implemented. Please rebuild the inputData manually', peak)
        pass

    @staticmethod
    def _peakCreated(guiModule, data):
        """
        To be defined. Maybe automatically add a row in the main dataTable?
        """
        getLogger().warn('_peakCreated notifier not implemented')
        pass

    #### DataTables ####
    @staticmethod
    def _dataTableCreated(guiModule, data):
        getLogger().warn('_dataTableCreated notifier not implemented')
        pass

    @staticmethod
    def _dataTableRenamed(guiModule, data):
        newSelectedObj = data.get('object')
        getLogger().warn('_dataTableRenamed notifier not implemented')
        pass

    @staticmethod
    def _dataTableDeleted(guiModule, data):
        """
        Called on deletion of a DataTable obj
        """
        deletedDataSet = data['object']
        getLogger().warn('_dataTableDeleted notifier not implemented')
        pass

    #### SPECTRUM ####
    @staticmethod
    def _spectrumChanged(guiModule, data):
        """
        """
        getLogger().warn('_spectrumChanged notifier not implemented')

    #### NmrResidue ####
    @staticmethod
    def onCurrentNmrResidue(guiModule, data):
        """
        :param guiModule:
        :param data:
        :return:
        """
        getLogger().warn('onCurrentNmrResidue notifier not implemented')
