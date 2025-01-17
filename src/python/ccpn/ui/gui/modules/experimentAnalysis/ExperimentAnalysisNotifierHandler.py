#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
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
__dateModified__ = "$dateModified: 2023-05-29 10:46:29 +0100 (Mon, May 29, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


from functools import partial
from ccpn.util.Logging import getLogger
from ccpn.core.Peak import Peak
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.DataTable import DataTable
from ccpn.core.Collection import Collection
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiManagers import ExperimentAnalysisHandlerABC
from ccpn.ui.gui.widgets.MessageDialog import showWarning
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces

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

            'onChangeSpectrum'      : Notifier(gm.project,
                                               [Notifier.CHANGE],
                                               targetName=Spectrum.className,
                                               callback=partial(CoreNotifiersHandler._spectrumChanged, gm),
                                               onceOnly=True),
            'onChangeSpectrumGroup' : Notifier(gm.project,
                                               [Notifier.CHANGE],
                                               targetName=SpectrumGroup.className,
                                               callback=partial(CoreNotifiersHandler._spectrumGroupChanged, gm),
                                               onceOnly=True),
            'onDeletePeak'          : Notifier(gm.project,
                                               [Notifier.DELETE],
                                               targetName=Peak.className,
                                               callback=partial(CoreNotifiersHandler._peakDeleted, gm),
                                               onceOnly=True),
            'onChangePeak'          : Notifier(gm.project,
                                               [Notifier.CHANGE],
                                               targetName=Peak.className,
                                               callback=partial(CoreNotifiersHandler._peakChanged, gm),
                                               onceOnly=True),
            'onDeleteCollection'    : Notifier(gm.project,
                                               [Notifier.DELETE],
                                               targetName=Collection.className,
                                               callback=partial(CoreNotifiersHandler._collectionDeleted, gm),
                                               onceOnly=True),
            'onChangeCollection'    : Notifier(gm.project,
                                               [Notifier.CHANGE],
                                               targetName=Collection.className,
                                               callback=partial(CoreNotifiersHandler._collectionChanged, gm),
                                               onceOnly=True),
            'onRenameCollection': Notifier(gm.project,
                                                [Notifier.RENAME],
                                                targetName=Collection.className,
                                                callback=partial(CoreNotifiersHandler._collectionRenamed, gm),
                                                onceOnly=True),
            'onDeleteNmrResidue': Notifier(gm.project,
                                                [Notifier.DELETE],
                                                targetName=NmrResidue.className,
                                                callback=partial(CoreNotifiersHandler._nmrResidueDeleted, gm),
                                                onceOnly=True),

            'onRenameNmrResidue': Notifier(gm.project,
                                               [Notifier.RENAME],
                                               targetName=NmrResidue.className,
                                               callback=partial(CoreNotifiersHandler._nmrResidueRenamed, gm),
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
    def _isPeakInSpectrumGroup(peak, spectrumGroup):
        return peak.spectrum in spectrumGroup.spectra

    @staticmethod
    def _setRebuildInputDataNotifier(guiModule, peaks=None):
        """ INTERNAL.  Rebuild the inputData after a new or deleted peak or update only a subset if peaks are only changed"""
        guiModule.setNeedRefitting()
        guiModule.setNeedRebuildingInputDataTables()

    @staticmethod
    def _spectrumChanged(guiModule, data):
        """Set Update Detected. E.g.: notify if the sliceColour has changed for the plotting colours"""
        spectrum = data[Notifier.OBJECT]
        if guiModule.backendHandler._isPidInDataTables(sv.SPECTRUMPID, spectrum.pid):
            getLogger().debug(f'Firing _spectrumChanged notifier from {guiModule.className}')
            guiModule._setUpdateDetected()

    @staticmethod
    def _spectrumGroupChanged(guiModule, data):
        """Set Rebuild flags."""
        spectrumGroup = data[Notifier.OBJECT]
        if spectrumGroup in guiModule.backendHandler.inputSpectrumGroups:
            getLogger().debug(f'Firing _spectrumGroupChanged notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)


    @staticmethod
    def _peakChanged(guiModule, data):
        """Set Rebuild flags."""
        peak = data[Notifier.OBJECT]
        if guiModule.backendHandler._isPidInDataTables(sv.PEAKPID, peak.pid):
            getLogger().debug(f'Firing peakChanged notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)

    @staticmethod
    def _peakDeleted(guiModule, data):
        """Set Rebuild flags."""
        peak = data[Notifier.OBJECT]
        if guiModule.backendHandler._isPidInDataTables(sv.PEAKPID, peak.pid):
            getLogger().debug(f'Firing peakDeleted notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)

    @staticmethod
    def _collectionChanged(guiModule, data):
        """Set Rebuild flags."""
        collection = data[Notifier.OBJECT]
        if guiModule.backendHandler._isPidInDataTables(sv.COLLECTIONPID, collection.pid):
            getLogger().debug(f'Firing collectionChanged notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)
        else:
            # check if is needed an update to inputCollection widget.
            tab = guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_SetupTab)
            if tab is not None:
                widget = tab.getWidget(guiNameSpaces.WidgetVarName_InputCollectionSelection)
                if widget:
                    widget.update()

    @staticmethod
    def _collectionDeleted(guiModule, data):
        """Set Rebuild flags."""
        collection = data[Notifier.OBJECT]
        if collection.isDeleted:
            pid = collection.pid.strip('-Deleted') # check why data doesn't give the oldValue (pid without -Deleted).
        else:
            pid = collection.pid
        if guiModule.backendHandler._isPidInDataTables(sv.COLLECTIONPID, collection.pid):
            getLogger().info(f'Firing _collectionDeleted notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)
        if guiModule.backendHandler.inputCollection == collection:
            guiModule.backendHandler.inputCollection = None
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)
            showWarning('Input Collection Removed', 'Removing the Input Collection will affect the module functionalities')

    @staticmethod
    def _collectionRenamed(guiModule, data):
        """Set Rebuild flags."""
        collection = data[Notifier.OBJECT]
        if guiModule.backendHandler._isPidInDataTables(sv.COLLECTIONPID, collection.pid):
            getLogger().debug(f'Firing _collectionRenamed notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)

    @staticmethod
    def _applyChangesToQueue(guiModule):
        pass

    #### DataTables ####
    @staticmethod
    def _dataTableCreated(guiModule, data):
        getLogger().debug('_dataTableCreated notifier not implemented')
        pass

    @staticmethod
    def _dataTableRenamed(guiModule, data):
        newSelectedObj = data.get('object')
        getLogger().debug('_dataTableRenamed notifier not implemented')
        pass

    @staticmethod
    def _dataTableDeleted(guiModule, data):
        """
        Called on deletion of a DataTable obj
        """
        deletedDataSet = data['object']
        getLogger().debug('_dataTableDeleted notifier not implemented')
        pass

    #### NmrResidue ####

    @staticmethod
    def _nmrResidueDeleted(guiModule, data):
        """Set Rebuild flags."""
        nmrResidue = data[Notifier.OBJECT]
        if guiModule.backendHandler._isPidInDataTables(sv.NMRRESIDUEPID, nmrResidue.pid):
            getLogger().info(f'Firing _nmrResidueDeleted notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)

    @staticmethod
    def _nmrResidueRenamed(guiModule, data):
        """Set Rebuild flags."""
        pid = data[Notifier.OLDPID]
        if guiModule.backendHandler._isPidInDataTables(sv.NMRRESIDUEPID, pid):
            getLogger().info(f'Firing _nmrResiduenRenamed notifier from {guiModule.className}')
            CoreNotifiersHandler._setRebuildInputDataNotifier(guiModule)
