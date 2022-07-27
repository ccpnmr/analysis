"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-07-27 12:22:56 +0100 (Wed, July 27, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-29 16:52:01 +0100 (Fri, April 29, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from collections import OrderedDict
from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChainPulldown
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning, showNotImplementedMessage
from ccpn.ui.gui.widgets.GuiTable import GuiTable, GuiTableFrame
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.Atom import Atom
from PyQt5 import QtWidgets
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT, DataFrameObject
from ccpn.core.lib.CallBack import CallBack
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.lib.StripLib import navigateToNmrResidueInDisplay, navigateToNmrAtomsInStrip
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableViewProjectSpecific, _updateSimplePandasTable
from ccpn.util.Logging import getLogger


#=========================================================================================
# _NewResidueTableWidget
#=========================================================================================

class _CoreTableWidgetABC(_SimplePandasTableViewProjectSpecific):
    """Class to present a table for core objects
    """

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 hiddenColumns=None,
                 enableExport=True, enableDelete=True, enableSearch=False,
                 showHorizontalHeader=True, showVerticalHeader=False,
                 **kwds):
        """Initialise the widgets for the module.
        """

        self._hiddenColumns = [self.columnHeaders.get(col) or col for col in hiddenColumns] if hiddenColumns else \
            [self.columnHeaders.get(col) or col for col in self.defaultHidden]
        # self.dataFrameObject = None

        super().__init__(parent=parent,
                         mainWindow=mainWindow,
                         moduleParent=moduleParent,
                         multiSelect=True,
                         showHorizontalHeader=showHorizontalHeader,
                         showVerticalHeader=showVerticalHeader,
                         setLayout=True,
                         **kwds)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def _sourceObjects(self):
        """Return the list of source objects, e.g., _table.peaks/_table.nmrResidues
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._sourceObjects not implemented')

    @_sourceObjects.setter
    def _sourceObjects(self, value):
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._sourceObjects not implemented')

    @property
    def _sourceCurrent(self):
        """Return the list of source objects in the current list, e.g., current.peaks/current.nmrResidues
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._sourceCurrent not implemented')

    @_sourceCurrent.setter
    def _sourceCurrent(self, value):
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._sourceCurrent not implemented')

    #=========================================================================================
    # Action callbacks
    #=========================================================================================

    # def actionCallback(self, data):
    #     """Not implemented yet
    #     """
    #     pass

    def selectionCallback(self, data):
        """set as current the selected core-objects on the table
        """
        objs = data[Notifier.OBJECT]
        self._sourceCurrent = objs

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

    def _newRowFromUniqueId(self, df, obj, uniqueId):
        """Create a new row to insert into the dataFrame or replace row
        """
        # generate a new row
        listItem = OrderedDict()
        for header in self._columnDefs.columns:
            try:
                listItem[header.headerText] = header.getValue(obj)
            except Exception as es:
                # NOTE:ED - catch any nasty surprises in tables - empty string stops tables changing column-type
                listItem[header.headerText] = ''

        return list(listItem.values())

    def _derivedFromObject(self, obj):
        """Get a tuple of derived values from obj
        Not very generic yet - column class now seems redundant
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._derivedFromObject not implemented')

    def buildTableDataFrame(self):
        """Return a Pandas dataFrame from an internal list of objects.
        The columns are based on the 'func' functions in the columnDefinitions.
        :return pandas dataFrame
        """
        allItems = []
        objects = []

        if self._table:
            self._columnDefs = self._getTableColumns(self._table)

            for col, obj in enumerate(self._sourceObjects):
                listItem = OrderedDict()
                for header in self._columnDefs.columns:
                    try:
                        listItem[header.headerText] = header.getValue(obj)
                    except Exception as es:
                        # NOTE:ED - catch any nasty surprises in tables
                        getLogger().debug2(f'Error creating table information {es}')
                        listItem[header.headerText] = None

                allItems.append(listItem)
                objects.append(obj)

            df = pd.DataFrame(allItems, columns=self._columnDefs.headings)

        else:
            self._columnDefs = self._getTableColumns()
            df = pd.DataFrame(columns=self._columnDefs.headings)

        # use the object as the index, object always exists even if isDeleted
        df.set_index(df[self.OBJECTCOLUMN], inplace=True, )

        _dfObject = DataFrameObject(dataFrame=df,
                                    columnDefs=self._columnDefs or [],
                                    table=self)

        return _dfObject

    def refreshTable(self):
        # subclass to refresh the groups
        if self._defaultDf is not None:
            _updateSimplePandasTable(self, self._defaultDf)
        else:
            getLogger().warning(f'{self.__class__.__name__}.refreshTable: defaultDf is not defined')
        # self.updateTableExpanders()

    def setDataFromSearchWidget(self, dataFrame):
        """Set the data for the table from the search widget
        """
        _updateSimplePandasTable(self, dataFrame)
        # self._updateGroups(dataFrame)
        # self.updateTableExpanders()

    # def _updateTableCallback(self, data):
    #     # print(f'>>> _updateTableCallback')
    #     pass

    def getCellToRows(self, cellItem, attribute=None):
        """Get the list of objects which cellItem maps to for this table
        To be subclassed as required
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.getCellToRows not implemented')

    def _updateCellCallback(self, data):
        """Notifier callback for updating the table
        :param data:
        """
        # print(f'>>> _updateCellCallback')
        with self._blockTableSignals('_updateCellCallback'):
            cellData = data[Notifier.OBJECT]

            rowObjs = []
            _triggerType = Notifier.CHANGE

            if (attr := self.cellClassNames.get(type(cellData))):
                rowObjs, _triggerType = self.getCellToRows(cellData, attr)

            # update the correct row by calling row handler
            for rowObj in rowObjs:
                rowData = {Notifier.OBJECT : rowObj,
                           Notifier.TRIGGER: _triggerType or data[Notifier.TRIGGER],
                           }

                self._updateRowCallback(rowData)

    def _updateRowCallback(self, data):
        """Notifier callback for updating the table for change in chemicalShifts
        :param data: notifier content
        """
        # print(f'>>> _updateRowCallback')
        with self._blockTableSignals('_updateRowCallback'):
            obj = data[Notifier.OBJECT]

            # check that the dataframe and object are valid
            if self._df is None:
                getLogger().debug2(f'{self.__class__.__name__}._updateRowCallback: dataFrame is None')
                return
            if obj is None:
                getLogger().debug2(f'{self.__class__.__name__}._updateRowCallback: callback object is undefined')
                return

            trigger = data[Notifier.TRIGGER]
            try:
                df = self._df
                objSet = set(self._sourceObjects)  # objects in the list
                if df is not None and not df.empty:
                    tableSet = set(df[self.OBJECTCOLUMN])  # objects currently in the table
                else:
                    # # populate here or in CREATE?
                    # self.populateTable()
                    # return
                    # current table is empty
                    tableSet = set()

                if trigger == Notifier.DELETE:
                    # uniqueIds in the visible table
                    if obj in (tableSet - objSet):
                        # remove from the table
                        self.model()._deleteRow(obj)
                        self._reindexTable()

                elif trigger == Notifier.CREATE:
                    # uniqueIds in the visible table
                    if obj in (objSet - tableSet):
                        if df is None or df.empty:
                            # create a new table from the list
                            #   required here as the peak tables can be different widths
                            self.populateTable()
                        else:
                            # insert into the table
                            newRow = self._newRowFromUniqueId(df, obj, None)
                            self.model()._insertRow(obj, newRow)
                            self._reindexTable()

                elif trigger == Notifier.CHANGE:
                    # uniqueIds in the visible table
                    if obj in (objSet & tableSet):
                        # visible table dataframe update - object MUST be in the table
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._updateRow(obj, newRow)

                elif trigger == Notifier.RENAME:
                    if obj in (objSet & tableSet):
                        # visible table dataframe update
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._updateRow(obj, newRow)

                    elif obj in (objSet - tableSet):
                        # insert renamed object INTO the table
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._insertRow(obj, newRow)
                        self._reindexTable()

                    elif obj in (tableSet - objSet):
                        # remove renamed object OUT of the table
                        self.model()._deleteRow(obj)
                        self._reindexTable()

            except Exception as es:
                getLogger().debug2(f'{self.__class__.__name__}._updateRowCallback: Error updating row in table - {es}')

    def _reindexTable(self):
        """Reset the index column for the table
        Not required for most core-object tables, but residues and nmrResidues have an order
        """
        if self._INDEX is not None:
            # must be done after the insert/delete as the object-column will have changed
            df = self._df
            objs = tuple(self._sourceObjects)  # objects in the list
            tableObjs = tuple(df[self.OBJECTCOLUMN])  # objects currently in the table

            # table will automatically replace this on the update
            df[self._INDEX] = [objs.index(obj) if obj in objs else 0 for obj in tableObjs]

    # def _searchCallBack(self, data):
    #     # print(f'>>> _searchCallBack')
    #     pass

    def _selectCurrentCallBack(self, data):
        """Callback from a notifier to highlight the current objects
        :param data:
        """
        if self._tableBlockingLevel:
            return

        objs = data['value']
        self._selectOnTableCurrent(objs)

    def _selectionChangedCallback(self, selected, deselected):
        """Handle item selection as changed in table - call user callback
        Includes checking for clicking below last row
        """
        self._changeTableSelection(None)

    def _selectOnTableCurrent(self, objs):
        """Highlight the list of objects on the table
        :param objs:
        """
        self.highlightObjects(objs)

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    #=========================================================================================
    # Table functions
    #=========================================================================================

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets
        """
        self._update()

    def _update(self):
        """Display the objects on the table for the selected list.
        """
        if self._table and self._sourceObjects:
            self.populateTable(selectedObjects=self._sourceCurrent)
        else:
            self.populateEmptyTable()

    def queueFull(self):
        """Method that is called when the queue is deemed to be too big.
        Apply overall operation instead of all individual notifiers.
        """
        self._update()

    #=========================================================================================
    # object properties
    #=========================================================================================


#=========================================================================================
# _CoreTableFrameABC
#=========================================================================================

class _CoreTableFrameABC(Frame):
    """Frame containing the pulldown and the table widget
    """
    _TableKlass = _CoreTableWidgetABC
    _PulldownKlass = None

    _activePulldownClass = None
    _activeCheckbox = None

    def __init__(self, parent, mainWindow=None, moduleParent=None,
                 obj=None, selectFirstItem=False, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None
        # self._table = None
        self.moduleParent = moduleParent

        # add the widgets
        self._setWidgets(mainWidget=self)

        if obj is not None:
            self.selectTable(obj)
        elif selectFirstItem:
            self._modulePulldown.selectFirstItem()

    def _setWidgets(self, mainWidget=None):
        """Set up the widgets for the module
        """
        # add to main widget area
        _topWidget = mainWidget

        # main widgets at the top
        row = 0
        Spacer(_topWidget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self._modulePulldown = self._PulldownKlass(parent=_topWidget,
                                                   mainWindow=self.mainWindow,
                                                   grid=(row, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                   showSelectName=True,
                                                   sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                   callback=self._selectionPulldownCallback)
        self._addWidgetRow = row
        self._addWidgetCol = gridHPos + 2

        # fixed height for the pulldown
        self._modulePulldown.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        self.spacer = Spacer(_topWidget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 1), gridSpan=(1, 1))

        # main window
        # _hidden = ['Pid', 'Chain']

        row += 1
        self._tableWidget = self._TableKlass(parent=_topWidget,
                                             mainWindow=self.mainWindow,
                                             grid=(row, 0), gridSpan=(1, 6),
                                             # hiddenColumns=_hidden,
                                             )
        _topWidget.getLayout().setColumnStretch(5, 2)

        # set policy to fill the frame - still required?
        self._tableWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

    def setActivePulldownClass(self, coreClass, checkBox):
        """Set up the callback properties for changing the current object from the pulldown
        """
        self._activePulldownClass = coreClass
        self._activeCheckbox = checkBox

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def _tableCurrent(self):
        """Return the list of source objects, e.g., _table.peaks/_table.nmrResidues
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._tableCurrent not implemented')

    @_tableCurrent.setter
    def _tableCurrent(self, value):
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._tableCurrent not implemented')

    @property
    def table(self):
        """Return the source table
        """
        return self._tableWidget._table

    @property
    def guiTable(self):
        """Return the table widget
        """
        return self._tableWidget

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def selectTable(self, table=None):
        """Manually select a table from the pullDown
        """
        if table is None:
            self._modulePulldown.selectFirstItem()
        else:
            if not isinstance(table, self._tableWidget.tableClass):
                getLogger().warning(f'select: Object is not of type {self._tableWidget.tableName}')
                raise TypeError(f'select: Object is not of type {self._tableWidget.tableName}')
            else:
                self._modulePulldown.select(table.pid)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """Convenience to add a widget to the top of the table; col >= 2
        """
        if col < self._addWidgetCol:
            raise RuntimeError(f'Col has to be >= {self._addWidgetCol}')
        self.getLayout().addWidget(widget, self._addWidgetRow, col, 1, colSpan)

    def addWidgetToPos(self, widget, row=0, col=2, rowSpan=1, colSpan=1, overrideMinimum=False, alignment=None):
        """Convenience to add a widget to the top of the table; col >= 2
        """
        if col < self._addWidgetCol and not overrideMinimum:
            raise RuntimeError(f'Col has to be >= {self._addWidgetCol}')
        self.getLayout().addWidget(widget, row, col, rowSpan, colSpan)

    def _closeFrame(self):
        """CCPN-INTERNAL: used to close the module
        """
        self._modulePulldown.unRegister()
        self._tableWidget._close()

    #=========================================================================================
    # Process dropped items
    #=========================================================================================

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        if self._tableWidget and data:
            pids = data.get('pids', [])
            self._handleDroppedItems(pids, self._tableWidget.tableClass, self._modulePulldown)

    def _handleDroppedItems(self, pids, objType, pulldown):
        """handle dropping pids onto the table
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle, e.g. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        from ccpn.ui.gui.lib.MenuActions import _openItemObject

        objs = [self.project.getByPid(pid) for pid in pids]

        selectableObjects = [obj for obj in objs if isinstance(obj, objType)]
        others = [obj for obj in objs if not isinstance(obj, objType)]
        if len(selectableObjects) > 0:
            _openItemObject(self.mainWindow, selectableObjects[1:])
            pulldown.select(selectableObjects[0].pid)

        else:
            from ccpn.ui.gui.widgets.MessageDialog import showYesNo

            othersClassNames = list(set([obj.className for obj in others if hasattr(obj, 'className')]))
            if len(othersClassNames) > 0:
                if len(othersClassNames) == 1:
                    title, msg = 'Dropped wrong item.', 'Do you want to open the %s in a new module?' % ''.join(othersClassNames)
                else:
                    title, msg = 'Dropped wrong items.', 'Do you want to open items in new modules?'
                openNew = showYesNo(title, msg)
                if openNew:
                    _openItemObject(self.mainWindow, others)

    #=========================================================================================
    # Widget/Notifier Callbacks
    #=========================================================================================

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting object from the pull down menu
        """
        _table = self._tableWidget._table = self._modulePulldown.getSelectedObject()
        self._tableWidget._update()

        # update the current object from the pulldown
        if self._activePulldownClass and self._activeCheckbox and _table != self._tableCurrent and self._activeCheckbox.isChecked():
            self._tableCurrent = _table

    def _selectCurrentPulldownClass(self, data):
        """Respond to change in current activePulldownClass
        """
        if self._activePulldownClass and self._activeCheckbox and self._activeCheckbox.isChecked():
            _table = self._tableWidget._table = self._tableCurrent
            self._tableWidget._update()

            if _table:
                self._modulePulldown.select(_table.pid, blockSignals=True)
            else:
                self._modulePulldown.setIndex(0, blockSignals=True)
