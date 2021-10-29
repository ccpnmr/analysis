"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-10-29 17:04:30 +0100 (Fri, October 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-29 16:38:09 +0100 (Fri, October 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import pandas as pd
# from ccpn.core.lib.CallBack import CallBack
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
# from ccpn.ui.gui.widgets.Spacer import Spacer
# from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.GuiTable import GuiTable
# from ccpn.core.lib.Notifiers import Notifier
# from ccpn.ui.gui.widgets.PulldownListsForObjects import StructureEnsemblePulldown
# from ccpn.ui.gui.widgets.Column import ColumnClass
# from PyQt5 import QtWidgets
# from ccpn.ui.gui.widgets.MessageDialog import showWarning
# from ccpn.core.StructureEnsemble import StructureEnsemble
# from ccpn.util.Logging import getLogger


ALL = '<all>'


class DataTableModule(CcpnModule):
    """
    This class implements the module by wrapping a DataTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'DataTableModule'
    _allowRename = True

    activePulldownClass = None  # e.g., can make the table respond to current collection

    def __init__(self, mainWindow=None, name='Data Table',
                 dataTable=None, selectFirstItem=False):
        """
        Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        # main window
        self.dataTable = DataTableWidget(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         moduleParent=self,
                                         setLayout=True,
                                         grid=(0, 0))

        if dataTable is not None:
            self.selectDataTable(dataTable)
        elif selectFirstItem:
            self.dataTable.dtWidget.selectFirstItem()

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.dataTable._maximise()

    def selectDataTable(self, dataTable=None):
        """
        Manually select a dataTable from the pullDown
        """
        self.dataTable._selectDataTable(dataTable)

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.dataTable._close()
        super()._closeModule()


class DataTableWidget(GuiTable):
    """
    Class to present a DataTable
    """
    className = 'DataTableWidget'
    attributeName = 'dataTables'
