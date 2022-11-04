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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-04 10:41:26 +0000 (Fri, November 04, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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

class _TableMenuABC(QtWidgets.QTableView):
    """Class to handle adding options to a right-mouse menu.
    """

    # add internal labels here

    def addTableMenuOptions(self, menu):
        """Add options to the right-mouse menu on the table or headers.
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def setTableMenuOptions(self, menu):
        """Update search options in the right-mouse menu
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    #=========================================================================================
    # Properties
    #=========================================================================================

    pass

    #=========================================================================================
    # Class methods
    #=========================================================================================

    pass

    #=========================================================================================
    # Implementation
    #=========================================================================================

    pass


class _TableHeaderABC(QtWidgets.QTableView):
    """Class to handle adding options to a right-mouse menu.
    """

    # add internal labels here

    def addHeaderMenuOptions(self, menu):
        """Add options to the right-mouse menu on the table or headers.
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def setHeaderMenuOptions(self, menu):
        """Update search options in the right-mouse menu
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    #=========================================================================================
    # Properties
    #=========================================================================================

    pass

    #=========================================================================================
    # Class methods
    #=========================================================================================

    pass

    #=========================================================================================
    # Implementation
    #=========================================================================================

    pass


#=========================================================================================
# Table Menu - Copy cell
#=========================================================================================

_COPYCELL_OPTION = 'Copy clicked cell value'


class _TableCopyCell(_TableMenuABC):
    """Class to handle copy-cell option on a menu
    """
    _enableCopyCell = True

    def _init(self, enableCopyCell=NOTHING):
        """Initialise the Copy-cell state
        """
        if enableCopyCell is not NOTHING:
            self.setCopyCellEnabled(enableCopyCell)

    def addTableMenuOptions(self, menu):
        """Add copy-cell option to the right-mouse menu
        """
        self._copySelectedCellAction = menu.addAction(_COPYCELL_OPTION, self._copySelectedCell)

    def setTableMenuOptions(self, menu):
        """Update copy-cell option in the right-mouse menu
        """
        # disable the copyCell options if not available
        if (actions := [act for act in menu.actions() if act.text() == _COPYCELL_OPTION]):
            actions[0].setEnabled(self._enableCopyCell)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def enableCopyCell(self):
        """Return True of the copy-cell options are enabled in the table menu
        """
        return self._enableCopyCell

    #=========================================================================================
    # Class methods
    #=========================================================================================

    def setCopyCellEnabled(self, value):
        """Enable/disable the copy-cell option from the right-mouse menu.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.setCopyCellEnabled: value must be True/False')

        self._enableCopyCell = value

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def _copySelectedCell(self):
        """Copy the current cell-value to the clipboard
        """
        idx = self.currentIndex()
        if idx is not None and (data := idx.data()) is not None:
            text = data.strip()
            copyToClipboard([text])


#=========================================================================================
# Table Header Menu
#=========================================================================================

_COLUMN_SETTINGS = 'Column Settings...'


class _TableHeaderColumns(_TableHeaderABC):
    """Class to handle column-settings on a header-menu
    """
    _parent = None
    _df = None
    _internalColumns = []
    _hiddenColumns = []
    _showColumns = True
    _enableColumns = True

    def addHeaderMenuOptions(self, menu):
        """Add table-header items to the right-mouse menu
        """
        menu.addSeparator()
        self._columnSettingsAction = menu.addAction(_COLUMN_SETTINGS, self._showColumnsPopup)

    def setHeaderMenuOptions(self, menu):
        """Update the state of options in the right-mouse menu
        """
        self._columnSettingsAction.setEnabled(self._enableColumns)
        self._columnSettingsAction.setVisible(self._showColumns)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def enableColumns(self):
        """Return True of the columnSettings option is enabled in the right-mouse menu
        """
        return self._enableColumns

    #=========================================================================================
    # Class methods
    #=========================================================================================

    def setColumnsEnabled(self, value):
        """Enable/disable the columns option from the right-mouse menu.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.setColumnsEnabled: value must be True/False')

        self._enableColumns = value

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def getHiddenColumns(self):
        """
        get a list of currently hidden columns
        """
        hiddenColumns = self._hiddenColumns
        ll = list(set(hiddenColumns))
        return [x for x in ll if x in self.columnTexts]

    def setHiddenColumns(self, texts, update=True):
        """
        set a list of columns headers to be hidden from the table.
        """
        ll = [x for x in texts if x in self.columnTexts and x not in self._internalColumns]
        self._hiddenColumns = ll
        if update:
            self.showColumns(None)

    def hideDefaultColumns(self):
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
            return list(self._df.columns)
        except Exception:
            return []

    def showColumns(self, df):
        # show the columns in the list
        hiddenColumns = self.getHiddenColumns()

        for colName in self.columnTexts:
            # always hide the internal columns
            if colName in (hiddenColumns + self._internalColumns):
                self._hideColumn(colName)
            else:
                self._showColumn(colName)

    def _showColumn(self, name):
        if name not in self.columnTexts:
            return
        if name in self._hiddenColumns:
            self._hiddenColumns.remove(name)
        i = self.columnTexts.index(name)
        self.showColumn(i)

    def _hideColumn(self, name):
        if name not in self.columnTexts:
            return
        if name not in (self._hiddenColumns + self._internalColumns):
            self._hiddenColumns.append(name)
        i = self.columnTexts.index(name)
        self.hideColumn(i)

    def _showColumnsPopup(self):
        """Show the columns popup-menu
        """
        settingsPopup = ColumnViewSettingsPopup(parent=self._parent, table=self,
                                                dataFrameObject=self._df,  # NOTE:ED - need to remove this
                                                hiddenColumns=self.getHiddenColumns(),
                                                )
        hiddenColumns = settingsPopup.getHiddenColumns()
        self.setHiddenColumns(texts=hiddenColumns, update=False)
        settingsPopup.exec_()  # exclusive control to the menu and return hidden-columns


#=========================================================================================
# Table Menu - Export
#=========================================================================================

_EXPORT_OPTION_VISIBLE = 'Export Visible Table'
_EXPORT_OPTION_ALL = 'Export All Columns'


class _TableExport(_TableMenuABC):
    """Class to handle export options on a menu
    """
    _enableExport = True

    def _init(self, enableExport=NOTHING):
        """Initialise the export-state
        """
        if enableExport is not NOTHING:
            self.setExportEnabled(enableExport)

    def addTableMenuOptions(self, menu):
        """Add export options to the right-mouse menu
        """
        menu.addSeparator()
        self._exportActionVisible = menu.addAction(_EXPORT_OPTION_VISIBLE, partial(self._exportTableDialog, exportAll=False))
        self._exportActionAll = menu.addAction(_EXPORT_OPTION_ALL, partial(self._exportTableDialog, exportAll=True))

    def setTableMenuOptions(self, menu):
        """Update export options in the right-mouse menu
        """
        # disable the export options if not available
        if (actions := [act for act in menu.actions() if act.text() == _EXPORT_OPTION_VISIBLE]):
            actions[0].setEnabled(self._enableExport)
        if (actions := [act for act in menu.actions() if act.text() == _EXPORT_OPTION_ALL]):
            actions[0].setEnabled(self._enableExport)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def enableExport(self):
        """Return True of the export options are enabled in the table menu
        """
        return self._enableExport

    #=========================================================================================
    # Class methods
    #=========================================================================================

    def setExportEnabled(self, value):
        """Enable/disable the export option from the right-mouse menu.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.setExportEnabled: value must be True/False')

        self._enableExport = value

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
                dataFrame.to_excel(path, sheet_name=sheet_name, columns=columns, index=False)
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


class _TableDelete(_TableMenuABC):
    """Class to handle delete options on a menu
    """
    _enableDelete = True

    def _init(self, enableDelete=NOTHING):
        """Initialise the delete-state
        """
        if enableDelete is not NOTHING:
            self.setDeleteEnabled(enableDelete)

    def addTableMenuOptions(self, menu):
        """Add delete options to the right-mouse menu
        """
        menu.addSeparator()
        self._deleteAction = menu.addAction(_DELETE_OPTION, self.deleteSelectionFromTable)
        self._clearAction = menu.addAction(_CLEAR_OPTION, self._clearSelection)

    def setTableMenuOptions(self, menu):
        """Update delete options in the right-mouse menu
        """
        # disable the delete options if not available
        if (actions := [act for act in menu.actions() if act.text() == _DELETE_OPTION]):
            actions[0].setEnabled(self._enableDelete)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def enableDelete(self):
        """Return True of the delete options are enabled in the table menu
        """
        return self._enableDelete

    #=========================================================================================
    # Class methods
    #=========================================================================================

    def setDeleteEnabled(self, value):
        """Enable/disable the delete option from the right-mouse menu.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.setDeleteEnabled: value must be True/False')

        self._enableDelete = value

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def deleteSelectionFromTable(self):
        """Delete all objects in the selection from the project
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _clearSelection(self):
        """Clear the table-selection
        """
        self.clearSelection()


#=========================================================================================
# Table Menu - Search
#=========================================================================================

_SEARCH_OPTION = 'Filter...'


class _TableSearch(_TableMenuABC):
    """Class to handle search options from a right-mouse menu.
    """
    tableAboutToBeSearched = QtCore.pyqtSignal(list)
    tableSearched = QtCore.pyqtSignal(list)

    _enableSearch = True
    _searchWidget = None

    def _init(self, enableSearch=NOTHING):
        """Initialise the search-state
        """
        if enableSearch is not NOTHING:
            self.setSearchEnabled(enableSearch)

    def addTableMenuOptions(self, menu):
        """Add search options to the right-mouse menu
        """
        menu.addSeparator()
        self._searchAction = menu.addAction(_SEARCH_OPTION, self.showSearchSettings)

    def setTableMenuOptions(self, menu):
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
    def enableSearch(self):
        """Return True of the search options are enabled in the table menu
        """
        return self._enableSearch

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

    def setSearchEnabled(self, value):
        """Enable/disable the search option from the right-mouse menu.

        :param bool value: enabled True/False
        """
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.setSearchEnabled: value must be True/False')

        self._enableSearch = value

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
        if self._enableSearch and self._searchWidget is None:
            if not attachSimpleSearchWidget(self._parent, self):
                getLogger().warning('Filter option not available')

            elif (model := self.model()):
                model.resetFilter()

        self.update()

    def refreshTable(self):
        """Refresh the table from the search-widget
        """

        if (model := self.model()) and model._df is not None:
            model.resetFilter()

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
