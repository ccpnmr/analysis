"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2023-05-04 14:06:22 +0100 (Thu, May 04, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-09 18:02:40 +0100 (Fri, September 09, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore
from collections import OrderedDict
from functools import partial
from abc import ABC, abstractmethod
import typing
import pandas as pd

from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.SearchWidget import attachSimpleSearchWidget
from ccpn.ui.gui.widgets.FileDialog import TablesFileDialog
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard, NOTHING
from ccpn.util.OrderedSet import OrderedSet


#=========================================================================================
# ABCs
#=========================================================================================

class TableMenuABC(ABC):
    """Class to handle adding options to a right-mouse menu.
    """
    name: typing.Optional[str] = None
    type: str = 'TableMenu'
    _enabled: bool = False
    _parent: QtWidgets.QTableView = None

    # add internal labels here

    def __init__(self, parent: QtWidgets.QTableView, enabled: bool = NOTHING):
        """Initialise the menu object to the parent table.

        :param parent: QTableView object
        :param enabled: bool
        """
        if not isinstance(parent, QtWidgets.QTableView):
            raise TypeError(f'{self.__class__.__name__} parent must be a QTableView')
        if enabled is not NOTHING and not isinstance(enabled, bool):
            raise TypeError(f'{self.__class__.__name__} enabled must be True/False')

        self._parent = parent
        if enabled is not NOTHING:
            # revert to the class _enabled
            self._enabled = enabled

    @abstractmethod
    def addMenuOptions(self, menu: QtWidgets.QMenu):
        """Add options to the right-mouse menu on the table or headers.
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @abstractmethod
    def setMenuOptions(self, menu: QtWidgets.QMenu):
        """Update search options in the right-mouse menu
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def isEnabled(self) -> bool:
        """Return True if the options are enabled in the table menu
        """
        return self._enabled

    @property
    def enabled(self) -> bool:
        """Return True if the options are enabled in the table menu
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable/disable the option.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.enabled: value must be True/False')

        self._enabled = value

    #=========================================================================================
    # Class methods
    #=========================================================================================

    # pass methods through to the QTableView/QHeaderView

    def clearSelection(self):
        return self._parent.clearSelection()

    def update(self):
        return self._parent.update()

    def model(self) -> QtCore.QAbstractTableModel:
        return self._parent.model()

    def horizontalHeader(self) -> QtWidgets.QHeaderView:
        return self._parent.horizontalHeader()

    #=========================================================================================
    # Implementation
    #=========================================================================================

    ...


class TableHeaderABC(ABC):
    """Class to handle adding options to a right-mouse menu.
    """
    name: typing.Optional[str] = None
    type: str = 'TableHeaderMenu'
    _enabled: bool = True
    _parent: QtWidgets.QTableView = None

    # add internal labels here

    def __init__(self, parent: QtWidgets.QTableView, enabled: bool = NOTHING):
        """Initialise the menu object to the parent table.

        :param parent: QTableView object
        :param enabled: bool
        """
        if not isinstance(parent, QtWidgets.QTableView):
            raise TypeError(f'{self.__class__.__name__} parent must be a QTableView')
        if enabled is not NOTHING and not isinstance(enabled, bool):
            raise TypeError(f'{self.__class__.__name__} enabled must be True/False')

        self._parent = parent
        if enabled is not NOTHING:
            # revert to the class _enabled
            self._enabled = enabled

    def addMenuOptions(self, menu):
        """Add options to the right-mouse menu on the table or headers.
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def setMenuOptions(self, menu):
        """Update search options in the right-mouse menu
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    #=========================================================================================
    # Properties
    #=========================================================================================

    # pass methods through to the QTableView/QHeaderView

    #=========================================================================================
    # Class methods
    #=========================================================================================

    # pass methods through to the QTableView/QHeaderView

    def clearSelection(self):
        return self._parent.clearSelection()

    def update(self):
        return self._parent.update()

    def model(self) -> QtCore.QAbstractTableModel:
        return self._parent.model()

    def horizontalHeader(self) -> QtWidgets.QHeaderView:
        return self._parent.horizontalHeader()

    def resizeColumnsToContents(self):
        self._parent.resizeColumnsToContents()

    def resizeColumnToContents(self, section):
        self._parent.resizeColumnToContents(section)

    #=========================================================================================
    # Implementation
    #=========================================================================================

    ...


#=========================================================================================
# Table Menu - Copy cell
#=========================================================================================

_COPYCELL_OPTION = 'Copy clicked cell value'


class TableCopyCell(TableMenuABC):
    """Class to handle copy-cell option on a menu
    """
    name = "CopyCell"

    def addMenuOptions(self, menu: QtWidgets.QMenu):
        """Add copy-cell option to the right-mouse menu
        """
        self._copySelectedCellAction = menu.addAction(_COPYCELL_OPTION, self._copySelectedCell)

    def setMenuOptions(self, menu: QtWidgets.QMenu):
        """Update copy-cell option in the right-mouse menu
        """
        # disable the copyCell options if not available
        if (actions := [act for act in menu.actions() if act.text() == _COPYCELL_OPTION]):
            actions[0].setEnabled(self._enabled)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def isEnabled(self) -> bool:
        """Return True if the options are enabled in the table menu
        """
        return self._enabled

    @property
    def enabled(self) -> bool:
        """Return True if the options are enabled in the table menu
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable/disable the option.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.enabled: value must be True/False')

        self._enabled = value

    #=========================================================================================
    # Class methods
    #=========================================================================================

    pass

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def _copySelectedCell(self):
        """Copy the current cell-value to the clipboard
        """
        idx = self._parent.currentIndex()
        if idx is not None and (data := idx.data()) is not None:
            text = data.strip()
            copyToClipboard([text])


#=========================================================================================
# Table Header Menu
#=========================================================================================

_COLUMN_SETTINGS = 'Column Settings...'


class TableHeaderColumns(TableHeaderABC):
    """Class to handle column-settings on a header-menu
    """
    name = "Columns"
    _parent = None
    _defaultHiddenColumns = None
    _internalColumns = None
    _menuItemVisible = True

    def __init__(self, *args, **kwds):
        super(TableHeaderColumns, self).__init__(*args, **kwds)

        # initialise the hidden/internal columns
        self._defaultHiddenColumns = set()
        self._internalColumns = set()

    def addMenuOptions(self, menu):
        """Add table-header items to the right-mouse menu
        """
        menu.addSeparator()
        self._columnSettingsAction = menu.addAction(_COLUMN_SETTINGS, self._showColumnsPopup)

    def setMenuOptions(self, menu):
        """Update the state of options in the right-mouse menu
        """
        self._columnSettingsAction.setEnabled(self._enabled)
        self._columnSettingsAction.setVisible(self._menuItemVisible)

    #=========================================================================================
    # Properties
    #=========================================================================================

    # pass methods through to the QTableView/QHeaderView

    @property
    def hiddenColumns(self):
        """Set/clear the hidden columns
        """
        header = list(self._parent._df.columns)
        return [col for cc, col in enumerate(header) if self._parent.isColumnHidden(cc)]

    @hiddenColumns.setter
    def hiddenColumns(self, columns):
        header = list(self._parent._df.columns)
        for cc, col in enumerate(header):
            if col in columns or col in self._internalColumns:
                self.hideColumn(cc)
            else:
                self.showColumn(cc)

    #=========================================================================================
    # Class methods
    #=========================================================================================

    # pass methods through to the QTableView/QHeaderView

    def model(self) -> QtCore.QAbstractTableModel:
        return self._parent.model()

    def horizontalHeader(self) -> QtWidgets.QHeaderView:
        return self._parent.horizontalHeader()

    def showColumn(self, col):
        # not sure if this is being caught every time
        if col in (cols := self.columnTexts):
            self._defaultHiddenColumns |= {cols[col]}
        self._parent.showColumn(col)

    def hideColumn(self, col):
        if col in (cols := self.columnTexts):
            self._defaultHiddenColumns -= {cols[col]}
        self._parent.hideColumn(col)

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def setInternalColumns(self, texts, update=True):
        """set a list of internal column-headers that are always hidden.
        """
        self._internalColumns = set(texts or [])
        if update:
            self.refreshHiddenColumns()

    def setDefaultColumns(self, texts, update=True):
        """set a list of default column-headers that are hidden when first shown.
        """
        self._defaultHiddenColumns = set(texts or [])
        if update:
            self.refreshHiddenColumns()

    def hideInternalColumns(self):
        """If the table is empty then check visible headers against the last header hidden list
        """
        for i, columnName in enumerate(self.columnTexts):
            # remember to hide the special column
            if columnName in self._internalColumns:
                self.hideColumn(i)

    @property
    def columnTexts(self):
        """return a list of column texts.
        """
        try:
            return list(self._parent._df.columns)
        except Exception:
            return []

    def refreshHiddenColumns(self):
        """Refresh the visible columns
        """
        hiCols = set(self.hiddenColumns) | self._internalColumns | self._defaultHiddenColumns

        # show the columns in the list
        for col, colName in enumerate(self.columnTexts):
            # always hide the internal columns
            if colName in hiCols:
                self._hideColumnName(colName)
            else:
                width = self._parent.columnWidth(col)
                self._showColumnName(colName)
                if not width:
                    self._parent.resizeColumnToContents(col)

    def _showColumnName(self, name):
        if name not in self.columnTexts:
            return

        if 0 <= (i := self.columnTexts.index(name)):
            self.showColumn(i)

    def _hideColumnName(self, name):
        if name not in self.columnTexts:
            return

        if 0 <= (i := self.columnTexts.index(name)):
            self.hideColumn(i)

    def _showColumnsPopup(self):
        """Show the columns popup-menu
        """
        settingsPopup = ColumnViewSettingsPopup(parent=self._parent, table=self,
                                                dataFrameObject=self._parent._df,  # NOTE:ED - need to remove dataFrameObject :|
                                                hiddenColumns=self.hiddenColumns,
                                                )
        settingsPopup.exec_()  # pass exclusive control to the menu and return hidden-columns

    def isColumnInternal(self, column):
        """Return True if the column is internal and not for external viewing
        """
        if 0 <= column < len(self.columnTexts):
            return self.columnTexts[column] in self._internalColumns

        return False

    @property
    def allHiddenColumns(self):
        """Return a list of all the hidden/internal columns
        """
        return set(self.hiddenColumns) | self._internalColumns


#=========================================================================================
# Table Menu - Export
#=========================================================================================

_EXPORT_OPTION_VISIBLE = 'Export Visible Table'
_EXPORT_OPTION_ALL = 'Export All Columns'


class TableExport(TableMenuABC):
    """Class to handle export options on a menu
    """
    name = "Export"

    def addMenuOptions(self, menu):
        """Add export options to the right-mouse menu
        """
        menu.addSeparator()
        self._exportActionVisible = menu.addAction(_EXPORT_OPTION_VISIBLE, partial(self._exportTableDialog, exportAll=False))
        self._exportActionAll = menu.addAction(_EXPORT_OPTION_ALL, partial(self._exportTableDialog, exportAll=True))

    def setMenuOptions(self, menu):
        """Update export options in the right-mouse menu
        """
        # disable the export options if not available
        if (actions := [act for act in menu.actions() if act.text() == _EXPORT_OPTION_VISIBLE]):
            actions[0].setEnabled(self._enabled)
        if (actions := [act for act in menu.actions() if act.text() == _EXPORT_OPTION_ALL]):
            actions[0].setEnabled(self._enabled)

    #=========================================================================================
    # Properties
    #=========================================================================================

    ...

    #=========================================================================================
    # Class methods
    #=========================================================================================

    ...

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def _exportTableDialog(self, exportAll=True):
        """export the contents of the table to a file
        The actual data values are exported, not the visible items which may be rounded due to the table settings

        :param exportAll: True/False - True implies export whole table - but in visible order
                                    False, export only the visible table
        """
        model = self.model()
        df = model._df
        rows, cols = df.shape[0], df.shape[1]

        if df is None or df.empty:
            MessageDialog.showWarning('Export Table to File', 'Table does not contain a dataFrame')

        else:
            if model._filterIndex is None:
                rowList = [model._sortIndex[row] for row in range(rows)]
            else:
                # need to map to the sorted indexes
                rowList = list(OrderedSet(model._sortIndex[row] for row in range(rows)) & OrderedSet(model._sortIndex[ii] for ii in model._filterIndex))

            if exportAll:
                colList = list(df.columns)  # assumes that the dataFrame column-headings match the table
            else:
                colList = [col for ii, col, in enumerate(list(df.columns)) if not self.horizontalHeader().isSectionHidden(ii)]

            self._showExportTableDialog(df, rowList=rowList, colList=colList)

    #=========================================================================================
    # Exporters
    #=========================================================================================

    @staticmethod
    def _dataFrameToExcel(dataFrame, path, sheet_name='Table', columns=None):
        if dataFrame is not None:
            path = aPath(path)
            path = path.assureSuffix('xlsx')
            if columns is not None and isinstance(columns, list):  #this is wrong. columns can be a 1d array

                indx = isinstance(dataFrame.columns, pd.MultiIndex)
                dataFrame.to_excel(path, sheet_name=sheet_name, columns=columns, index=indx)

            else:
                dataFrame.to_excel(path, sheet_name=sheet_name, index=False)

    @staticmethod
    def _dataFrameToCsv(dataFrame, path, *args):
        dataFrame.to_csv(path)

    @staticmethod
    def _dataFrameToTsv(dataFrame, path, *args):
        dataFrame.to_csv(path, sep='\t')

    @staticmethod
    def _dataFrameToJson(dataFrame, path, *args):
        dataFrame.to_json(path, orient='split', default_handler=str)

    def _findExportFormats(self, path, dataFrame, sheet_name='Table', filterType=None, columns=None):
        formatTypes = OrderedDict([
            ('.xlsx', self._dataFrameToExcel),
            ('.csv', self._dataFrameToCsv),
            ('.tsv', self._dataFrameToTsv),
            ('.json', self._dataFrameToJson)
            ])

        # extension = os.path.splitext(path)[1]
        extension = aPath(path).suffix
        if not extension:
            extension = '.xlsx'
        if extension in formatTypes.keys():
            formatTypes[extension](dataFrame, path, sheet_name, columns)
            return
        else:
            try:
                self._findExportFormats(str(path) + filterType, sheet_name)
            except Exception:
                MessageDialog.showWarning('Could not export', 'Format file not supported or not provided.'
                                                              '\nUse one of %s' % ', '.join(formatTypes))
                getLogger().warning('Format file not supported')

    def _showExportTableDialog(self, dataFrame, rowList=None, colList=None):

        self.saveDialog = TablesFileDialog(parent=None, acceptMode='save', selectFile='ccpnTable.xlsx',
                                           fileFilter=".xlsx;; .csv;; .tsv;; .json ")
        self.saveDialog._show()
        if path := self.saveDialog.selectedFile():
            if dataFrame is not None and not dataFrame.empty:

                if colList:
                    dataFrame = dataFrame[colList]  # returns a new dataFrame
                if rowList:
                    dataFrame = dataFrame[:].iloc[rowList]

                ft = self.saveDialog.selectedNameFilter()

                sheet_name = 'Table'
                self._findExportFormats(path, dataFrame, sheet_name=sheet_name, filterType=ft, columns=colList)


#=========================================================================================
# Table Menu - Delete/Clear
#=========================================================================================

_DELETE_OPTION = 'Delete Selection'
_CLEAR_OPTION = 'Clear Selection'


class TableDelete(TableMenuABC):
    """Class to handle delete options on a menu
    """
    name = "Delete"

    def addMenuOptions(self, menu):
        """Add delete options to the right-mouse menu
        """
        menu.addSeparator()
        self._deleteAction = menu.addAction(_DELETE_OPTION, self.deleteSelectionFromTable)
        self._clearAction = menu.addAction(_CLEAR_OPTION, self._clearSelection)

    def setMenuOptions(self, menu):
        """Update delete options in the right-mouse menu
        """
        # disable the delete options if not available
        if (actions := [act for act in menu.actions() if act.text() == _DELETE_OPTION]):
            actions[0].setEnabled(self._enabled)

    #=========================================================================================
    # Properties
    #=========================================================================================

    ...

    #=========================================================================================
    # Class methods
    #=========================================================================================

    ...

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def deleteSelectionFromTable(self):
        """Delete all objects in the selection from the project
        """
        self._parent.deleteSelectionFromTable()

    def _clearSelection(self):
        """Clear the table-selection
        """
        self._parent.clearSelection()


#=========================================================================================
# Table Menu - Search
#=========================================================================================

_SEARCH_OPTION = 'Filter...'


class TableSearchMenu(TableMenuABC):
    """Class to handle search options from a right-mouse menu.
    """
    tableAboutToBeSearched = QtCore.pyqtSignal(list)
    tableSearched = QtCore.pyqtSignal(list)

    name = "Search"
    _searchWidget = None

    def addMenuOptions(self, menu):
        """Add search options to the right-mouse menu
        """
        menu.addSeparator()
        self._searchAction = menu.addAction(_SEARCH_OPTION, self.showSearchSettings)

    def setMenuOptions(self, menu):
        """Update search options in the right-mouse menu
        """
        self._initSearchWidget()

        # disable the search action if not available
        if (actions := [act for act in menu.actions() if act.text() == _SEARCH_OPTION]):
            actions[0].setEnabled(self._searchWidget is not None)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def searchWidget(self):
        """Return the search-widget
        """
        return self._searchWidget

    @searchWidget.setter
    def searchWidget(self, value):
        self._searchWidget = value

    #=========================================================================================
    # Class methods
    #=========================================================================================

    def showSearchSettings(self):
        """Display the search frame in the table
        """
        self._initSearchWidget()

        if self._searchWidget is not None:
            if not self._searchWidget.isVisible():
                self._searchWidget.show()
            else:
                self._searchWidget.hideSearch()

    def hideSearchWidget(self):
        if self._searchWidget is not None:
            self._searchWidget.hide()

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def _initSearchWidget(self):
        if self._enabled and self._searchWidget is None:
            # always assumes that the parent-table is contained within a frame
            if not (widget := attachSimpleSearchWidget(self._parent, self)):
                getLogger().warning('Filter option not available')

            elif (model := self.model()):
                model.resetFilter()

            self._searchWidget = widget

        self.update()

    def refreshTable(self):
        """Refresh the table from the search-widget
        """

        if (model := self.model()) and model._df is not None:
            model.resetFilter()

            model.layoutChanged.emit()
            self._parent.tableChanged.emit()

        else:
            getLogger().debug(f'{self.__class__.__name__}.refreshTable: defaultDf is not defined')

    def setDataFromSearchWidget(self, rows):
        """Set the data from the search-widget
        """
        if (model := self.model()) and model._df is not None:

            model.beginResetModel()
            if model._filterIndex is not None:
                model._filterIndex = sorted(set(model._filterIndex) & {model._sortIndex.index(ii) for ii in rows})
            else:
                model._filterIndex = sorted(model._sortIndex.index(ii) for ii in rows)

            model.endResetModel()

            model.layoutChanged.emit()

        # import numpy as np
        # NOTE:ED - keep for the minute
        # # must have unique indices - otherwise ge arrays for multiple rows in here
        # idx = self._df.index
        # lastIdx = list(df.index)
        #
        # if (mapping := [idx.get_loc(cc) for cc in lastIdx if cc in idx]):
        #     newMapping = np.zeros(len(lastIdx), dtype=np.int32)
        #
        #     # remove any duplicated rows - there SHOULDN'T be any, but could be a generic df
        #     for ind, rr in enumerate(mapping):
        #         if isinstance(rr, int):
        #             newMapping[ind] = rr
        #         elif isinstance(rr, np.ndarray):
        #             # get the index of the first duplicate - may not be the correct order with other matching index :|
        #             indT = list(rr).index(True)
        #             newMapping[ind] = indT
        #             for mm in mapping[ind + 1:]:
        #                 if isinstance(mm, np.ndarray):
        #                     mm[indT] = False
        #         else:
        #             # anything else is a missing row
        #             raise RuntimeError(f'{self.__class__.__name__}.df: new df is not a sub-set of the original')
        #
        #     if (model := self.model()) and model._df is not None:
        #         # self.updateDf(model._defaultDf)
        #         if model._filterIndex is not None:
        #             model._filterIndex = sorted(model._filterIndex[ft] for ft in newMapping)
        #         else:
        #             model._filterIndex = sorted(newMapping)
        #
        # self.update()

    def refreshFilter(self):
        """Refresh the search-widget if the contents of the table have changed
        """
        self._searchWidget and self._searchWidget.refreshFilter()
