"""

Basic Usage:
  
  define a list of Column(columnName, func, tipText=tipText) objects, 
  where func obtains the value for the object displayed in a row and
   tipText is optional;
  
  e.g. Column('index', lambda row: row.index, tipText='index of the row')
  
  define a list of objects (or empty):
  objectList = list(myObjects) if myObjects is not None else []
  
  define optional actionCallback and/or selectionCallback functions
  
  ObjectTable(parent=parent, columns=columnList, objects=objectList, 
              actionCallback=actionCallback, selectionCallback=selectionCallback,
              ....)
  
  use setObjects(objects) method to set objects
  use show() to show
  use clearTable() to clear the table


Inherited from QTableView (http://pyqt.sourceforge.net/Docs/PyQt5/qtableview.html)

QTableView Class Reference
[QtGui module]
The QTableView class provides a default model/view implementation of a table view. More...
Inherits QAbstractItemView.
Inherited by QTableWidget.

Methods

    __init__ (self, QWidget parent = None)
    clearSpans (self)
    int columnAt (self, int x)
    columnCountChanged (self, int oldCount, int newCount)
    columnMoved (self, int column, int oldIndex, int newIndex)
    columnResized (self, int column, int oldWidth, int newWidth)
    int columnSpan (self, int row, int column)
    int columnViewportPosition (self, int column)
    int columnWidth (self, int column)
    currentChanged (self, QModelIndex current, QModelIndex previous)
    Qt.PenStyle gridStyle (self)
    hideColumn (self, int column)
    hideRow (self, int row)
    QHeaderView horizontalHeader (self)
    int horizontalOffset (self)
    horizontalScrollbarAction (self, int action)
    QModelIndex indexAt (self, QPoint p)
    bool isColumnHidden (self, int column)
    bool isCornerButtonEnabled (self)
    bool isIndexHidden (self, QModelIndex index)
    bool isRowHidden (self, int row)
    bool isSortingEnabled (self)
    QModelIndex moveCursor (self, QAbstractItemView.CursorAction cursorAction, Qt.KeyboardModifiers modifiers)
    paintEvent (self, QPaintEvent e)
    resizeColumnsToContents (self)
    resizeColumnToContents (self, int column)
    resizeRowsToContents (self)
    resizeRowToContents (self, int row)
    int rowAt (self, int y)
    rowCountChanged (self, int oldCount, int newCount)
    int rowHeight (self, int row)
    rowMoved (self, int row, int oldIndex, int newIndex)
    rowResized (self, int row, int oldHeight, int newHeight)
    int rowSpan (self, int row, int column)
    int rowViewportPosition (self, int row)
    scrollContentsBy (self, int dx, int dy)
    scrollTo (self, QModelIndex index, QAbstractItemView.ScrollHint hint = QAbstractItemView.EnsureVisible)
    selectColumn (self, int column)
    list-of-QModelIndex selectedIndexes (self)
    selectionChanged (self, QItemSelection selected, QItemSelection deselected)
    selectRow (self, int row)
    setColumnHidden (self, int column, bool hide)
    setColumnWidth (self, int column, int width)
    setCornerButtonEnabled (self, bool enable)
    setGridStyle (self, Qt.PenStyle style)
    setHorizontalHeader (self, QHeaderView header)
    setModel (self, QAbstractItemModel model)
    setRootIndex (self, QModelIndex index)
    setRowHeight (self, int row, int height)
    setRowHidden (self, int row, bool hide)
    setSelection (self, QRect rect, QItemSelectionModel.SelectionFlags command)
    setSelectionModel (self, QItemSelectionModel selectionModel)
    setShowGrid (self, bool show)
    setSortingEnabled (self, bool enable)
    setSpan (self, int row, int column, int rowSpan, int columnSpan)
    setVerticalHeader (self, QHeaderView header)
    setWordWrap (self, bool on)
    showColumn (self, int column)
    bool showGrid (self)
    showRow (self, int row)
    int sizeHintForColumn (self, int column)
    int sizeHintForRow (self, int row)
    sortByColumn (self, int column)
    sortByColumn (self, int column, Qt.SortOrder order)
    timerEvent (self, QTimerEvent event)
    updateGeometries (self)
    QHeaderView verticalHeader (self)
    int verticalOffset (self)
    verticalScrollbarAction (self, int action)
    QStyleOptionViewItem viewOptions (self)
    QRect visualRect (self, QModelIndex index)
    QRegion visualRegionForSelection (self, QItemSelection selection)
    bool wordWrap (self)

"""
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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re

from PyQt5 import QtGui, QtWidgets, QtCore
import pandas as pd
import os
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.TableModel import ObjectTableModel
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Frame import Frame
from functools import partial

from collections import OrderedDict
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import undoBlock


BG_COLOR = QtGui.QColor('#E0E0E0')


class ObjectTable(QtWidgets.QTableView, Base):
    columnSizeHint = 30  # per collumn size hint (to be multiplied by number of collums)
    rowSizeHint = 200  # total size hint (total size for all rows)

    def __init__(self, parent, columns,
                 objects=None,
                 actionCallback=None, selectionCallback=None,
                 multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
                 enableExport=True, enableDelete=True,
                 **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        self._parent = parent
        self.graphPanel = None
        self.filterPanel = None
        self.model = None
        self.columns = columns
        self.objects = list(objects or [])
        self.callback = actionCallback
        self.fontMetric = QtGui.QFontMetricsF(self.font())
        self.bbox = self.fontMetric.boundingRect
        self._silenceCallback = False
        self.selectionCallback = selectionCallback
        self.doubleClicked.connect(self.actionCallback)
        self.setAlternatingRowColors(True)
        self.autoResize = autoResize
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.setHorizontalScrollMode(self.ScrollPerItem)
        self.setVerticalScrollMode(self.ScrollPerItem)
        self._hiddenColumns = []

        self.multiSelect = multiSelect
        if multiSelect:
            self.setSelectionMode(self.ExtendedSelection)
            # + Continuous etc possible
        else:
            self.setSelectionMode(self.SingleSelection)

        self.selectRows = selectRows
        if selectRows:
            self.setSelectionBehavior(self.SelectRows)
        else:
            self.setSelectionBehavior(self.SelectItems)
            # + Columns possible

        self._setupModel()

        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)

        delegate = ObjectTableItemDelegate(self)
        self.setItemDelegate(delegate)

        model = self.selectionModel()
        model.selectionChanged.connect(self._callback)
        #model.currentRowChanged.connect(self._callback)

        header = self.verticalHeader()
        header.setResizeMode(header.Interactive)
        header.setStretchLastSection(False)

        rowHeight = self.bbox('A').height() + 4
        header.setMinimumSectionSize(rowHeight)
        header.setDefaultSectionSize(rowHeight)

        # if numberRows:
        # header.setVisible(True)
        # else:
        header.setVisible(False)

        # header = ObjectHeaderView(QtCore.Qt.Horizontal, self)
        # header.setMovable(True)
        # header.setMinimumSectionSize(30)
        # header.setDefaultSectionSize(30)
        # #header.setSortIndicatorShown(False)
        # #header.setStyleSheet('QHeaderView::down-arrow { image: url(icons/sort-up.png);} QHeaderView::up-arrow { image: url(icons/sort-down.png);}')
        # self.header = header
        self.setupHeaderStretch()

        self.setDragEnabled(True)
        self.acceptDrops()
        self.setDragDropMode(self.InternalMove)
        self.setDropIndicatorShown(True)

        self.searchWidget = None
        self._setHeaderContextMenu()
        self._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            event.accept()
        else:
            super(ObjectTable, self).mousePressEvent(event)

    def _setHeaderContextMenu(self):
        headers = self.horizontalHeader()
        headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        self.tableMenu = QtWidgets.QMenu()
        if enableExport:
            self.tableMenu.addAction("Export Table", self.exportDialog)
        if enableDelete:
            self.tableMenu.addAction("Delete", self.deleteObjFromTable)

        # ejb - added these but don't think they are needed
        # self.tableMenu.addAction("Select All", self.selectAllObjects)
        self.tableMenu.addAction("Clear Selection", self.clearSelection)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._raiseTableContextMenu)

    def clearTable(self):
        "remove all objects from the table"
        self._silenceCallback = True
        self.setObjects([])
        self._silenceCallback = False

    def sizeHint(self):

        return QtCore.QSize(max(10, self.columnSizeHint * len(self.columns)), self.rowSizeHint)

    def _setupModel(self):

        if self.model:
            sortDetails = (self.model.sortColumn(), self.model.sortOrder())

        else:
            sortDetails = None

        objModel = ObjectTableModel(self)

        model = ObjectTableProxyModel(self)
        model.setSourceModel(objModel)

        if sortDetails is not None:
            column, order = sortDetails
            model.sort(column, order)

        self.setModel(model)
        self.model = model

        return model

    def resizeEvent(self, event):

        if self.graphPanel and self.graphPanel.isVisible():
            pos = self.graphPanel.pos()
            x = pos.x()
            y = pos.y()
            w = self.width() - x
            h = self.height()
            self.graphPanel.setGeometry(x, y, w, h)

        # If the table is connected to a qtgui Splitter it
        # should not resize unless it is specifically asked to.
        # This helps avoiding infinite repaint loops.
        if not (isinstance(self._parent, Splitter) or self._parent.__class__.__name__ == Splitter.__name__) or \
                self._parent.doResize == True:
            return QtWidgets.QTableView.resizeEvent(self, event)

    def clearSelection(self):

        model = self.selectionModel()
        model.clear()

    def _callback(self, itemSelection):

        if self._silenceCallback:
            return

        elif self.selectionCallback:
            index = self.getCurrentIndex()
            row = index.row()
            col = index.column()

            model = self.selectionModel()

            if self.selectRows:
                selection = model.selectedRows(column=0)
            else:
                selection = model.selectedIndexes()

            if selection:
                rows = [i.row() for i in selection]
                rows.sort()

                objs = []

                for row in rows:
                    if row not in rows:
                        row = rows[0]
                    if row >= 0:
                        index = self.model.index(row, 0)
                        row = self.model.mapToSource(index).row()
                        obj = self.objects[row]
                        objs.append(obj)

                        if not self.multiSelect:
                            self.selectionCallback(obj, row, col)
                        if self.multiSelect:
                            self.selectionCallback(objs, row, col)


            else:
                self.selectionCallback(None, row, col)

    def actionCallback(self, itemSelection):
        index = self.getCurrentIndex()
        row = index.row()
        col = index.column()

        model = self.selectionModel()

        if self.selectRows:
            selection = model.selectedRows(column=0)
        else:
            selection = model.selectedIndexes()

        if selection:
            rows = [i.row() for i in selection]
            rows.sort()
            if row not in rows:
                row = rows[0]

            index = self.model.index(row, 0)
            row = self.model.mapToSource(index).row()

            if row >= 0:
                obj = self.objects[row]
                if self.callback and not self.columns[col].setEditValue:  # ejb - editable fields don't actionCallback
                    self.callback(obj, row, col)

    def hideColumnName(self, name):
        self.hideColumn(self.getColumnInt(columnName=name))

    def showColumnName(self, name):
        self.showColumn(self.getColumnInt(columnName=name))

    def getCurrentIndex(self):

        model = self.selectionModel()
        index = model.currentIndex()
        index = self.model.mapToSource(index)

        return index

    def getCurrentObject(self):

        selectionModel = self.selectionModel()
        index = selectionModel.currentIndex()
        index = self.model.mapToSource(index)

        row = index.row()

        if row < 0:
            return
        else:
            return self.objects[row]

    def getCurrentRow(self):

        selectionModel = self.selectionModel()
        index = selectionModel.currentIndex()
        index = self.model.mapToSource(index)

        return index.row()

    def getSelectedRows(self):

        model = self.selectionModel()

        if self.selectRows:
            selection = model.selectedRows(column=0)
        else:
            selection = model.selectedIndexes()

        rows = [i.row() for i in selection]
        #rows = list(set(rows))
        #rows.sort()

        return rows

    def getSelectedObjects(self):

        model = self.selectionModel()
        if self.selectRows:
            selection = model.selectedRows(column=0)
        else:
            selection = model.selectedIndexes()

        objects = self.objects
        selectedObjects = []

        for index in selection:
            row = self.model.mapToSource(index).row()
            selectedObjects.append(objects[row])

        return selectedObjects

    def setCurrentRow(self, row):

        selectionModel = self.selectionModel()
        index = self.model.index(row, 0)
        self._silenceCallback = True
        selectionModel.clearSelection()
        self._silenceCallback = False
        selectionModel.select(index, selectionModel.Select | selectionModel.Rows)
        self.setFocus(QtCore.Qt.OtherFocusReason)

    def setCurrentObject(self, obj):

        if obj in self.objects:
            row = self.objects.index(obj)
            selectionModel = self.selectionModel()
            index = self.model.sourceModel().index(row, 0)
            index = self.model.mapFromSource(index)

            self._silenceCallback = True
            selectionModel.clearSelection()
            self._silenceCallback = False
            selectionModel.select(index, selectionModel.Select | selectionModel.Rows)
            self.setFocus(QtCore.Qt.OtherFocusReason)

    def selectRow(self, row):

        selectionModel = self.selectionModel()
        index = self.model.index(row, 0)
        self._silenceCallback = True
        selectionModel.clearSelection()
        self._silenceCallback = False
        selectionModel.setCurrentIndex(index, selectionModel.SelectCurrent | selectionModel.Rows)
        self.setFocus(QtCore.Qt.OtherFocusReason)

    def selectObject(self, obj):

        if obj in self.objects:
            row = self.objects.index(obj)
            selectionModel = self.selectionModel()
            index = self.model.sourceModel().index(row, 0)
            index = self.model.mapFromSource(index)

            self._silenceCallback = True
            selectionModel.clearSelection()
            self._silenceCallback = False
            selectionModel.setCurrentIndex(index, selectionModel.SelectCurrent | selectionModel.Rows)
            self.setFocus(QtCore.Qt.OtherFocusReason)

    def setSelectedObjects(self, selection):

        return self.setCurrentObjects(selection)

    def setCurrentObjects(self, selection):

        objects = self.objects
        selectionModel = self.selectionModel()

        rows = []
        uniqObjs = set(selection)

        for row, obj in enumerate(objects):
            if obj in uniqObjs:
                rows.append(row)

        if rows:
            self._silenceCallback = True
            selectionModel.clearSelection()
            self.setUpdatesEnabled(False)

            selectMode = selectionModel.Select | selectionModel.Rows
            select = selectionModel.select
            getIndex = self.model.sourceModel().index
            mapFromSource = self.model.mapFromSource

            for row in rows:
                index = getIndex(row, 0)
                index = mapFromSource(index)
                select(index, selectMode)

            self._silenceCallback = False
            self._callback(None)
            self.setUpdatesEnabled(True)

        self.setFocus(QtCore.Qt.OtherFocusReason)

    def _highLightObjs(self, selection):

        objects = self.objects

        selectionModel = self.selectionModel()

        rows = []
        uniqObjs = set(selection)

        for row, obj in enumerate(objects):
            if obj in uniqObjs:
                rows.append(row)

        if rows:
            self._silenceCallback = True
            selectionModel.clearSelection()
            self.setUpdatesEnabled(False)

            selectMode = selectionModel.Select | selectionModel.Rows
            select = selectionModel.select
            getIndex = self.model.sourceModel().index
            mapFromSource = self.model.mapFromSource

            for row in rows:
                index = getIndex(row, 0)
                index = mapFromSource(index)
                select(index, selectMode)

            self._silenceCallback = False
            # self._callback(None)
            self.setUpdatesEnabled(True)

            self.setFocus(QtCore.Qt.OtherFocusReason)

    def getColumnInt(self, columnName):
        for i, column in enumerate(self.columns):
            if column.heading == columnName:
                return i

    def getColumn(self, columnName):
        for column in self.columns:
            if column.heading == columnName:
                return column

    def setupHeaderStretch(self):

        columns = self.columns
        header = self.horizontalHeader()
        stretch = False
        objects = self.objects
        setColumnWidth = self.setColumnWidth
        bbox = self.bbox

        for i, column in enumerate(columns):
            if column.stretch:
                header.setResizeMode(i, header.Stretch)
                stretch = True

        if objects:
            minSize = bbox('MM').width()
            colSizes = [max(minSize, bbox(col.heading).width()) for col in columns]
            for i, objCol in enumerate(columns):
                for obj in objects[:35] + objects[-5:]:
                    value = objCol.getFormatValue(obj)

                    if isinstance(value, float):
                        value = '%.5f' % value
                    elif not isinstance(value, (str)):
                        value = str(value)

                    size = bbox(value).width()

                    if size > colSizes[i]:
                        colSizes[i] = size

            for i, width in enumerate(colSizes):
                setColumnWidth(i, width + 12)

        if not stretch:
            header.setStretchLastSection(True)

    def closeEvent(self, event):

        self.hideGraph()
        self.hideFilter()
        QtWidgets.QTableView.closeEvent(self, event)

    def destroy(self, *args):

        if self.filterPanel:
            self.filterPanel.destroy()

        if self.graphPanel:
            self.graphPanel.destroy()

        QtWidgets.QTableView.destroy(self, *args)

    def _raiseHeaderContextMenu(self, pos):
        if self.searchWidget is None:
            self._addSearchWidget()

        pos = QtCore.QPoint(pos.x(), pos.y() + 10)  #move the popup a bit down. Otherwise can trigger an event if the pointer is just on top the first item

        self.headerContextMenumenu = QtWidgets.QMenu()
        columnsSettings = self.headerContextMenumenu.addAction("Columns Settings...")
        searchSettings = None
        if self.searchWidget is not None:
            searchSettings = self.headerContextMenumenu.addAction("Search")
        action = self.headerContextMenumenu.exec_(self.mapToGlobal(pos))

        if action == columnsSettings:
            settingsPopup = ColumnViewSettingsPopup(parent=self._parent, hideColumns=self._hiddenColumns, table=self)
            settingsPopup.raise_()
            settingsPopup.exec_()  # exclusive control to the menu and return _hiddencolumns

        if action == searchSettings:
            self.showSearchSettings()

    def _addSearchWidget(self):
        # TODO:Luca Add search option for any table
        if self._parent is not None:
            parentLayout = None
            if isinstance(self._parent, Base):
                # if hasattr(self._parent, 'getLayout'):
                parentLayout = self._parent.getLayout()

            if isinstance(parentLayout, QtWidgets.QGridLayout):
                idx = parentLayout.indexOf(self)
                location = parentLayout.getItemPosition(idx)
                if location is not None:
                    if len(location) > 0:
                        row, column, rowSpan, columnSpan = location
                        self.searchWidget = ObjectTableFilter(table=self, grid=(0, 0), vAlign='B')
                        parentLayout.addWidget(self.searchWidget, row + 2, column, rowSpan + 2, columnSpan)
                        self.searchWidget.hide()
        return True

    def showSearchSettings(self):

        if self.searchWidget is not None:
            self.searchWidget.show()

    def _raiseTableContextMenu(self, pos):
        pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)
        action = self.tableMenu.exec_(self.mapToGlobal(pos))

    def exportDialog(self):

        self.saveDialog = FileDialog(directory='ccpn_Table.xlsx',  #default saving name
                                     fileMode=FileDialog.AnyFile,
                                     filter=".xlsx;; .csv;; .tsv;; .json ",
                                     text='Save as ',
                                     acceptMode=FileDialog.AcceptSave,
                                     preferences=None)
        path = self.saveDialog.selectedFile()
        if path:
            self.findExportFormats(path)

    def findExportFormats(self, path):
        formatTypes = OrderedDict([
            ('.xlsx', self.dataFrameToExcel),
            ('.csv', self.dataFrameToCsv),
            ('.tsv', self.dataFrameToTsv),
            ('.json', self.dataFrameToJson)
            ])

        extension = os.path.splitext(path)[1]
        if extension in formatTypes.keys():
            formatTypes[extension](self.tableToDataFrame(), path)
            return
        else:
            try:
                self.findExportFormats(str(path) + self.saveDialog.selectedNameFilter())
            except:
                print('Format file not supported')

    def dataFrameToExcel(self, dataFrame, path):
        dataFrame.to_excel(path, sheet_name='Table', index=False)

    def dataFrameToCsv(self, dataFrame, path):
        dataFrame.to_csv(path)

    def dataFrameToTsv(self, dataFrame, path):
        dataFrame.to_csv(path, sep='\t')

    def dataFrameToJson(self, dataFrame, path):
        dataFrame.to_json(path, orient='split')

    def tableToDataFrame(self):
        from pandas import DataFrame

        headers = [c.heading for c in self.columns]
        rows = []
        for obj in self.objects:
            rows.append([x.getValue(obj) for x in self.columns])
        dataFrame = DataFrame(rows, index=None, columns=headers)
        dataFrame.apply(pd.to_numeric, errors='ignore')
        return dataFrame

    def selectAllObjects(self):
        self.selectAll()

    def deleteObjFromTable(self):
        selected = self.getSelectedObjects()
        n = len(selected)
        title = 'Delete Item%s' % ('' if n == 1 else 's')
        msg = 'Delete %sselected item%s from the project?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
        if MessageDialog.showYesNo(title, msg):

            if hasattr(selected[0], 'project'):
                thisProject = selected[0].project

                # thisProject._startCommandEchoBlock('application.table.deleteFromTable', [sI.pid for sI in selected])
                with undoBlock():
                    try:

                        self.blockSignals(True)

                        for obj in selected:
                            if hasattr(obj, 'pid'):
                                # print ('>>> deleting', obj)
                                obj.delete()

                    except Exception as es:
                        getLogger().warning(str(es))
                    finally:

                        self.blockSignals(False)
                        # thisProject._endCommandEchoBlock()

            else:

                # TODO:ED this is deleting from PandasTable, check for another way to get project
                for obj in selected:
                    if hasattr(obj, 'pid'):
                        obj.delete()

    def filterRows(self):

        self.hideGraph()

        if not self.filterPanel:
            self.filterPanel = ObjectTableFilter(self)

        self.filterPanel.move(self.window().pos())
        self.filterPanel.show()

    def hideFilter(self):

        if self.filterPanel:
            self.filterPanel.close()

    def unfilter(self):

        if self.filterPanel:
            self.filterPanel.unfilterTable()

    def getObjects(self, filtered=False):

        if self.filterPanel:
            if filtered:
                return list(self.objects)

            else:
                return list(self.filterPanel.origObjects)

        else:
            return list(self.objects)

    def copyRow(self):
        objs = self.getSelectedObjects()
        if len(objs) > 0:

            rows = []
            for obj in objs:
                rows.append([x.getValue(obj) for x in self.columns])
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)

            rowsStr = ",".join(str(x) for x in rows)
            rowsStr = rowsStr.replace('],', ']\n')
            rowsStr = rowsStr.replace(']', '')
            rowsStr = rowsStr.replace('[', '')
            rowsStr = rowsStr.replace("'", '')

            cb.setText(rowsStr, mode=cb.Clipboard)

    def _syncFilterObjects(self, applyFilter=False):

        if self.filterPanel:
            if applyFilter is not None:
                self.filterPanel.origObjects = self.objects

            status = self.filterPanel.status
            if applyFilter and (status is not None):
                self.filterPanel.filterTable(status)

    def replaceCurrentObject(self, object):

        model = self.model
        selectionModel = self.selectionModel()
        row = selectionModel.currentIndex().row()  # the visible row
        indexA = model.index(row, 0)
        indexB = model.index(row, len(self.columns) - 1)
        index = model.mapToSource(indexA)  # the underlying, original

        if index.row() < 0:
            return

        self.objects[index.row()] = object
        self._syncFilterObjects()

        model.dataChanged.emit(indexA, indexB)

    def scrollToSelectedIndex(self):
        h = self.horizontalHeader()
        for i in range(h.count()):
            if not h.isSectionHidden(i) and h.sectionViewportPosition(i) >= 0:
                if self.getSelectedRows():
                    self.scrollTo(self.model.index(self.getSelectedRows()[0], i),
                                  self.PositionAtCenter)

    def setObject(self, i, object):
        """Replaces an object in the _underlying_ list"""

        model = self.model
        self.objects[i] = object
        self._syncFilterObjects()

        index = model.sourceModel().index(i, 0)  # the underlying, original
        indexA = model.mapFromSource(index)  # the visible row
        indexB = model.index(indexA.row(), len(self.columns) - 1)

        model.dataChanged.emit(indexA, indexB)

    def setRowObject(self, row, object):
        """Replaces an object in the _visible_ rows"""

        model = self.model
        indexA = model.index(row, 0)  # the visible row
        indexB = model.index(row, len(self.columns) - 1)  # the visible row
        index = model.mapToSource(indexA)  # the underlying, original

        self.objects[index.row()] = object
        self._syncFilterObjects()

        model.dataChanged.emit(indexA, indexB)

    def setObjectsAndColumns(self, objects, columns):
        self._silenceCallback = True
        # self.setObjects([])
        self.setColumns(columns)
        self.setObjects(objects)
        self._silenceCallback = False

    def setObjects(self, objects, applyFilter=False, filterApplied=False):
        if not filterApplied:
            if self.searchWidget is not None:
                self.searchWidget.updateSearchWidgets(self)

        selectedObjects = self.getSelectedObjects()  # get current selection
        getIndex = self.model.sourceModel().index
        # print('FRFF', getIndex)

        model = self.model
        sourceModel = model.sourceModel()
        selected = set(self.getSelectedObjects())
        current = self.getCurrentObject()

        n = len(objects)
        m = len(self.objects)
        c = len(self.columns)

        self.objects = list(objects)
        sourceModel.objects = self.objects

        if n > m:
            sourceModel.beginInsertRows(QtCore.QModelIndex(), m, n - 1)

        elif m > n:
            sourceModel.beginRemoveRows(QtCore.QModelIndex(), n, m - 1)

        indexA = model.index(0, 0)
        indexB = model.index(n - 1, c - 1)
        model.dataChanged.emit(indexA, indexB)  # the visible rows

        if n > m:
            sourceModel.endInsertRows()
        elif m > n:
            sourceModel.endRemoveRows()

        if selected:
            self._silenceCallback = True
            selectionModel = self.selectionModel()
            selectionModel.clearSelection()
            selectMode = selectionModel.Select | selectionModel.Rows
            select = selectionModel.select
            getIndex = self.model.sourceModel().index

            mapFromSource = self.model.mapFromSource

            for row, obj in enumerate(objects):
                if obj in selected:
                    index = getIndex(row, 0)
                    index = mapFromSource(index)

                    if obj is current:
                        selectionModel.setCurrentIndex(index, selectionModel.SelectCurrent)

                    select(index, selectMode)

            self._silenceCallback = False

        sortCol = model.sortColumn()
        sortOrder = model.sortOrder()

        if sortCol >= 0:
            model.sort(sortCol, sortOrder)

        self._syncFilterObjects(applyFilter)
        self.setupHeaderStretch()
        # if self.autoResize:

        self.setVisible(False)
        # self.setEnabled(False)
        self.blockSignals(True)
        # self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Interactive)
        # self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)
        # print ('  >>>setObjects')
        self.resizeColumnsToContents()
        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Interactive)
        self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)

        self._highLightObjs(selectedObjects)  # set back again if possible

        self.blockSignals(False)
        # self.setEnabled(True)
        self.setVisible(True)

    def setColumns(self, columns):

        model = self.model
        sourceModel = model.sourceModel()
        selected = self.getSelectedObjects()
        current = self.getCurrentObject()

        n = len(columns)
        m = len(self.columns)
        r = len(self.objects)

        self.columns = columns
        sourceModel.columns = columns

        if n > m:
            sourceModel.beginInsertColumns(QtCore.QModelIndex(), m, n - 1)

        elif m > n:
            sourceModel.beginRemoveColumns(QtCore.QModelIndex(), n, m - 1)

        indexA = model.index(0, 0)
        indexB = model.index(r - 1, n - 1)
        model.dataChanged.emit(indexA, indexB)  # the visible rows
        model.headerDataChanged.emit(QtCore.Qt.Horizontal, 0, n - 1)

        if n > m:
            sourceModel.endInsertColumns()

        elif m > n:
            sourceModel.endRemoveColumns()

        if selected:
            # may need to now highlight more columns
            selectionModel = self.selectionModel()
            for obj in selected:
                row = self.objects.index(obj)
                index = model.index(row, 0)

                if obj is current:
                    selectionModel.select(index, selectionModel.SelectCurrent | selectionModel.Rows)
                    selectionModel.setCurrentIndex(index, selectionModel.SelectCurrent | selectionModel.Rows)

                else:
                    selectionModel.select(index, selectionModel.Select | selectionModel.Rows)

        self.setupHeaderStretch()

    def getObject(self, row):

        return self.objects[row]

    # def dragEnterEvent(self, event):
    #     event.accept()
    #
    # def dragMoveEvent(self, event):
    #     event.accept()
    #
    # def startDrag(self, event):
    #     print("startDrag called")
    #     index = self.indexAt(event.pos())
    #     print(index)
    #     if not index.isValid():
    #         return
    #
    #     self.moved_data = self.getObject(index.row())
    #
    #     drag = QtGui.QDrag(self)
    #
    #     mimeData = QtCore.QMimeData()
    #     mimeData.setData("application/blabla", "")
    #     drag.setMimeData(mimeData)
    #
    #     pixmap = QtGui.QPixmap()
    #     pixmap = pixmap.grabWidget(self, self.visualRect(index))
    #     drag.setPixmap(pixmap)
    #
    #     result = drag.start(QtCore.Qt.MoveAction)
    #
    # # def dropEvent(self, event):
    # #   print("dropEvent called")
    # #   point = event.pos()
    # #   print(point)
    #
    # def mousePressEvent(self, event):
    #   if (event.button() == QtCore.Qt.LeftButton) and (
    #       event.modifiers() & QtCore.Qt.ControlModifier):
    #       print("mousePressEvent called")
    #       self.startDrag(event)
    #   else:
    #     QtWidgets.QTableView.mousePressEvent(self, event)


EDIT_ROLE = QtCore.Qt.EditRole


class ObjectTableItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):

        QtWidgets.QStyledItemDelegate.__init__(self, parent)
        self.customWidget = None
        self._parent = parent

    def createEditor(self, parentWidget, itemStyle, index):  # returns the edit widget

        col = index.column()
        objCol = self._parent.columns[col]

        if objCol.editClass:
            widget = objCol.editClass(None, *objCol.editArgs, **objCol.editKw)
            widget.setParent(parentWidget)
            self.customWidget = True
            return widget

        else:
            obj = self._parent.objects[index.row()]
            editValue = objCol.getEditValue(obj)

            if isinstance(editValue, (list, tuple)):
                widget = PulldownList(None)
                widget.setParent(parentWidget)
                self.customWidget = True
                return widget

            else:
                # Use the default, type-dependant factory
                # Deals with strings, bools, date time etc.
                self.customWidget = None
                editor = QtWidgets.QStyledItemDelegate.createEditor(self, parentWidget, itemStyle, index)

                if isinstance(editor, QtGui.QDoubleSpinBox):
                    numDecimals = objCol.editDecimals

                    if numDecimals is not None:
                        editor.setDecimals(numDecimals)

                        if objCol.editStep:
                            editor.setSingleStep(objCol.editStep)
                        else:
                            editor.setSingleStep(10 ** -numDecimals)

                if isinstance(editor, QtGui.QSpinBox):
                    if objCol.editStep:
                        editor.setSingleStep(objCol.editStep)

                return editor

    def setEditorData(self, widget, index):  # provides the widget with data

        if self.customWidget:
            model = index.model()
            value = model.data(index, EDIT_ROLE)

            if not isinstance(value, (list, tuple)):
                value = (value,)

            if hasattr(widget, 'setColor'):
                widget.setColor(*value)

            elif hasattr(widget, 'setData'):
                widget.setData(*value)

            elif hasattr(widget, 'set'):
                widget.set(*value)

            elif hasattr(widget, 'setValue'):
                widget.setValue(*value)

            elif hasattr(widget, 'setFile'):
                widget.setFile(*value)

            else:
                msg = 'Widget %s does not expose "setData", "set" or "setValue" method; ' % widget
                msg += 'required for table proxy editing'
                raise Exception(msg)


        else:
            return QtWidgets.QStyledItemDelegate.setEditorData(self, widget, index)

    def updateEditorGeometry(self, widget, itemStyle, index):  # ensures that the editor is displayed correctly

        if self.customWidget:
            cellRect = itemStyle.rect
            x = cellRect.x()
            y = cellRect.y()
            hint = widget.sizeHint()

            if hint.height() > cellRect.height():
                if isinstance(widget, QtWidgets.QComboBox):  # has a popup anyway
                    widget.move(cellRect.topLeft())

                else:
                    pos = widget.mapToGlobal(cellRect.topLeft())
                    widget.setParent(self._parent, QtCore.Qt.Popup)  # popup so not confined
                    widget.move(pos)

            else:
                width = max(hint.width(), cellRect.width())
                height = max(hint.height(), cellRect.height())
                widget.setGeometry(x, y, width, height)


        else:
            return QtWidgets.QStyledItemDelegate.updateEditorGeometry(self, widget, itemStyle, index)

    def setModelData(self, widget, mode, index):  #returns updated data

        if self.customWidget:

            if hasattr(widget, 'get'):
                value = widget.get()

            elif hasattr(widget, 'value'):
                value = widget.value()

            elif hasattr(widget, 'getFile'):
                files = widget.selectedFiles()

                if not files:
                    return

                value = files[0]

            else:
                msg = 'Widget %s does not expose "get" or "value" method; ' % widget
                msg += 'required for table proxy editing'
                raise Exception(msg)

            # del widget
            model = index.model()
            model.setData(index, value, EDIT_ROLE)


        else:
            return QtWidgets.QStyledItemDelegate.setModelData(self, widget, mode, index)


class ObjectHeaderView(QtWidgets.QHeaderView):

    def __init__(self, orient, parent):
        QtWidgets.QHeaderView.__init__(self, orient, parent)
        self.table = parent

    #def sizeHint(self):

    #  return QtCore.QSize(30*len(self.table.columns), self.table.bbox('A').height())

    #def minimumSize(self):
    #
    #  return QtCore.QSize(30*len(self.table.columns), self.table.bbox('A').height())


LESS_THAN = QtCore.QSortFilterProxyModel.lessThan


class ObjectTableProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self, parent):

        QtCore.QSortFilterProxyModel.__init__(self, parent=parent)
        self.table = parent

    def lessThan(self, leftIndex, rightIndex):

        table = self.table
        columns = table.columns
        objCol = columns[leftIndex.column()]

        if objCol.orderFunc:
            objects = table.objects
            objA = objects[leftIndex.row()]
            objB = objects[rightIndex.row()]

            return objCol.orderFunc(objA, objB)

        else:
            return LESS_THAN(self, leftIndex, rightIndex)


TAB_FORMAT = 'Tab-separated'
COMMA_FORMAT = 'Comma-separated'
EXPORT_FORMATS = (TAB_FORMAT, COMMA_FORMAT)


class ObjectTableExport(QtWidgets.QDialog, Base):

    def __init__(self, table=None, **kwds):
        super().__init__(table)
        Base._init(self, **kwds)

        self.setWindowFlags(QtCore.Qt.Tool)
        self.table = table
        label = Label(self, 'Columns to export:', grid=(0, 0), gridSpan=(1, 2))

        labels = ['Row Number', ] + [c.heading.replace('\n', ' ') for c in table.columns]
        values = [True] * len(labels)
        label = Label(self, 'Export format:', grid=(3, 0))
        self.formatPulldown = PulldownList(self, EXPORT_FORMATS, grid=(3, 1))
        self.setMaximumWidth(300)


class ColumnViewSettingsPopup(CcpnDialog):
    def __init__(self, table, parent=None, hideColumns=None, title='Column Settings', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)
        self.setContentsMargins(20, 20, 20, 20)
        self.table = table
        self.widgetColumnViewSettings = ColumnViewSettings(parent=self, table=table, hideColumns=hideColumns, grid=(0, 0))
        buttons = ButtonList(self, texts=['Close'], callbacks=[self._close], grid=(1, 0), hAlign='c')
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def _close(self):
        'Save the hidden columns to the table class. So it remembers when you open again the popup'
        hiddenColumns = self.widgetColumnViewSettings._getHiddenColumns()
        self.table._hiddenColumns = hiddenColumns
        self.reject()
        return hiddenColumns


SEARCH_MODES = ['Literal', 'Case Sensitive Literal', 'Regular Expression']
CheckboxTipText = 'Select column to be visible on the table.'


class ColumnViewSettings(Widget):
    ''' hide show check boxes corresponding to the table columns '''

    def __init__(self, table, parent=None, direction='v', hideColumns=None, **kwds):
        Widget.__init__(self, parent, setLayout=True, **kwds)
        self.direction = direction
        self.table = table
        self.checkBoxes = []
        # self.hiddenColumns = []
        self.hideColumns = hideColumns or []  # list of column names
        self._hideColumnWidths = {}
        self.initCheckBoxes()
        self.filterLabel = Label(self, 'Display Columns', grid=(0, 1), vAlign='t', hAlign='l')

    def initCheckBoxes(self):
        columns = self.table.columns

        if columns:
            for i, colum in enumerate(columns):

                if self.direction == 'v':
                    i += 1
                    cb = CheckBox(self, text=colum.heading, grid=(i, 1), callback=self.checkBoxCallBack,
                                  checked=True if colum.heading not in self.hideColumns else False,
                                  hAlign='l', tipText=CheckboxTipText, )
                else:
                    cb = CheckBox(self, text=colum.heading, grid=(1, i), callback=self.checkBoxCallBack,
                                  checked=True if colum.heading not in self.hideColumns else False,
                                  hAlign='l', tipText=CheckboxTipText, )

                cb.setMinimumSize(cb.sizeHint() * 1.3)

                self.checkBoxes.append(cb)
                if colum.heading not in self.hideColumns:
                    self._showColumn(colum.heading)
                else:
                    self._hideColumn(colum.heading)
        # self.table._hiddenColumns = []

    def _getHiddenColumns(self):
        return self.hideColumns

    def checkBoxCallBack(self):
        currentCheckBox = self.sender()
        name = currentCheckBox.text()
        checkedBoxes = []

        for checkBox in self.checkBoxes:
            checkBox.setEnabled(True)
            if checkBox.isChecked():
                checkedBoxes.append(checkBox)
        if len(checkedBoxes) > 0:
            if currentCheckBox.isChecked():
                self._showColumn(name)
            else:
                self._hideColumn(name)
        else:  #always display at least one columns, disables the last checkbox
            currentCheckBox.setEnabled(False)
            currentCheckBox.setChecked(True)

    def updateWidgets(self, table):
        self.table = table
        if self.checkBoxes:
            for cb in self.checkBoxes:
                cb.deleteLater()
        self.checkBoxes = []
        self.initCheckBoxes()

    def _hideColumn(self, name):
        self.table.hideColumn(self.table.getColumnInt(columnName=name))
        # self._hideColumnWidths[name] = self.table.columnWidth(self.table.getColumnInt(columnName=name))
        if name not in self.hideColumns:
            self.hideColumns.append(name)
        # self.hiddenColumns.append(name)

    def _showColumn(self, name):
        self.table.showColumn(self.table.getColumnInt(columnName=name))
        # if name in self._hideColumnWidths:
        #   self.table.setColumnWidth(self.table.getColumnInt(columnName=name), self._hideColumnWidths[name])
        self.table.resizeColumnToContents(self.table.getColumnInt(columnName=name))
        if name in self.hideColumns:
            self.hideColumns.remove(name)


class ObjectTableFilter(Widget):

    def __init__(self, table, parent=None, **kwds):
        Widget.__init__(self, parent, setLayout=False, **kwds)
        self.table = table

        self.origObjects = self.table.objects

        labelColumn = Label(self, 'Search in', )
        self.columnOptions = PulldownList(self, )
        self.columnOptions.setMinimumWidth(self.columnOptions.sizeHint().width() * 2)
        self.searchLabel = Label(self, 'Search for', )
        self.edit = LineEdit(self, )
        self.searchButtons = ButtonList(self, texts=['Close', 'Reset', 'Search'], tipTexts=['Close Search', 'Restore Table', 'Search'],
                                        callbacks=[self.hideSearch, partial(self.restoreTable, self.table),
                                                   partial(self.findOnTable, self.table)])
        self.searchButtons.buttons[1].setEnabled(False)

        self.widgetLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.widgetLayout)
        ws = [labelColumn, self.columnOptions, self.searchLabel, self.edit, self.searchButtons]
        for w in ws:
            self.widgetLayout.addWidget(w)
        self.setColumnOptions()

    def setColumnOptions(self):
        columns = self.table.columns
        texts = [c.heading for c in columns]
        objectsRange = range(len(columns))

        self.columnOptions.clear()
        self.columnOptions.addItem('Whole Table', object=None)
        for i, text in enumerate(texts):
            self.columnOptions.addItem(text, objectsRange[i])
        self.columnOptions.setIndex(0)

    def updateSearchWidgets(self, table):
        self.table = table
        self.origObjects = self.table.objects
        self.setColumnOptions()
        self.searchButtons.buttons[1].setEnabled(False)

    def hideSearch(self):
        self.restoreTable(self.table)
        if self.table.searchWidget is not None:
            self.table.searchWidget.hide()

    def restoreTable(self, table):
        #TODO:ED this works for all objects in the project EXCEPT PandasDataframes which
        # don't have _parent

        if len(self.table.objects) > 0:
            if hasattr(self.table.objects[0], '_parent'):
                parentObjects = self.table.objects[0]._parent
                if parentObjects is not None:
                    if hasattr(parentObjects, '_childClasses'):
                        cC = parentObjects._childClasses
                        if len(cC) > 0:
                            if hasattr(parentObjects._childClasses[0], '_pluralLinkName'):
                                names = parentObjects._childClasses[0]._pluralLinkName
                                originalObjects = getattr(parentObjects, names)
                                table.setObjects(originalObjects)

        self.edit.clear()
        self.searchButtons.buttons[1].setEnabled(False)

    def findOnTable(self, table):

        if self.edit.text() == '' or None:
            self.restoreTable(table)
            return

        self.table = table
        self.origObjects = self.table.objects
        self.table.setObjects(self.origObjects, filterApplied=True)

        text = self.edit.text()
        columns = self.table.columns

        if self.columnOptions.currentObject() is None:
            allMatched = []
            for i in range(len(columns)):
                objCol = columns[i]
                matched = self.searchMatches(objCol, text)
                allMatched.append(matched)
            matched = set([i for m in allMatched for i in m])  #making a single list of matching objs

        else:
            objCol = columns[self.columnOptions.currentObject()]
            matched = self.searchMatches(objCol, text)

        if matched:
            self.table.setObjects(matched, filterApplied=True)
            self.searchButtons.buttons[1].setEnabled(True)
        else:
            self.searchButtons.buttons[1].setEnabled(False)
            self.restoreTable(table)
            MessageDialog.showWarning('Not found', '')

    def searchMatches(self, objCol, text):
        matched = []
        objs = self.table.objects
        for obj in objs:
            value = u'%s' % (objCol.getValue(obj))
            if str(text) in str(value):
                matched.append(obj)
            elif str(text) == str(value):
                matched.append(obj)
        return matched

    def setFilteredObjects(self):
        selected = self.table.getSelectedObjects()
        self.table.setObjects(selected)


class Column:

    def __init__(self, heading, getValue, getEditValue=None, setEditValue=None,
                 editClass=None, editArgs=None, editKw=None, tipText=None,
                 getColor=None, getIcon=None, stretch=False, format=None,
                 editDecimals=None, editStep=None, alignment=QtCore.Qt.AlignLeft):
        # editDecimals=None, editStep=None, alignment=QtCore.Qt.AlignLeft,
        # orderFunc=None):

        self.heading = heading
        self.getValue = getValue or self._defaultText
        self.getEditValue = getEditValue or getValue
        self.setEditValue = setEditValue
        self.editClass = editClass
        self.editArgs = editArgs or []
        self.editKw = editKw or {}
        self.stretch = stretch
        self.format = format
        self.editDecimals = editDecimals
        self.editStep = editStep
        self.defaultIcon = None
        #self.alignment = ALIGN_OPTS.get(alignment, alignment) | Qt.AlignVCenter
        # Alignment combinations broken in PyQt5 v1.1.1
        # Use better default than top left
        self.alignment = QtCore.Qt.AlignCenter
        # self.orderFunc = orderFunc

        self.getIcon = getIcon or self._defaultIcon
        self.getColor = getColor or self._defaultColor
        self.tipText = tipText

        self._checkTextAttrs()

    def orderFunc(self, objA, objB):
        return (universalSortKey(self.getValue(objA)) < universalSortKey(self.getValue(objB)))

    def getFormatValue(self, obj):

        value = self.getValue(obj)
        format = self.format
        if format and (value is not None):
            return format % value
        else:
            return value

    def _checkTextAttrs(self):

        if isinstance(self.getValue, str):
            attr = self.getValue
            self.getValue = lambda obj: getattr(obj, attr)

        if isinstance(self.getEditValue, str):
            attr = self.getEditValue
            self.getEditValue = lambda obj: getattr(obj, attr)

        if isinstance(self.setEditValue, str):
            attr = self.setEditValue
            self.setEditValue = lambda obj, value: setattr(obj, attr, value)

        if isinstance(self.getIcon, QtGui.QIcon):
            self.defaultIcon = self.getIcon
            self.getIcon = self._defaultIcon

    def _defaultText(self, obj):

        return ' '

    def _defaultColor(self, obj):

        return BG_COLOR

    def _defaultIcon(self, obj):

        return self.defaultIcon


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Icon import Icon

    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.util import Colour


    app = TestApplication()


    class mockObj(object):
        'Mock object to test the table widget editing properties'
        exampleStr = 'exampleStr'
        integer = 3
        exampleFloat = 3.1  # This will create a double spin box
        exampleBool = True  # This will create a check box
        string = 'white'  # This will create a line Edit
        exampleList = (('Mock', 'Test'),)  # This will create a pulldown
        color = QtGui.QColor('Red')
        icon = Icon('icons/warning')
        r = Colour.colourNameToHexDict['red']
        y = Colour.colourNameToHexDict['yellow']
        b = Colour.colourNameToHexDict['blue']
        colouredIcons = [None, Icon(color=r), Icon(color=y), Icon(color=b)]

        flagsList = [[''] * len(colouredIcons), [Icon] * len(colouredIcons), 1, colouredIcons]  # This will create a pulldown. Make a list with the

        # same structure of pulldown setData function: (texts=None, objects=None, index=None,
        # icons=None, clear=True, headerText=None, headerEnabled=False, headerIcon=None)

        def editBool(self, value):
            mockObj.exampleBool = value

        def editFloat(self, value):
            mockObj.exampleFloat = value

        def editPulldown(self, value):
            mockObj.exampleList = value

        def editStr(self, value):
            mockObj.exampleStr = value

        def editFlags(self, value):
            print('test')


    popup = CcpnDialog(windowTitle='Test Table', setLayout=True)

    cString = Column(heading='Str',
                     getValue=lambda i: mockObj.exampleStr,
                     setEditValue=lambda mockObj, value: mockObj.editStr(mockObj, value),
                     getColor=lambda i: mockObj.y,
                     )

    cFloat = Column(heading='Float',
                    getValue=lambda i: mockObj.exampleFloat,
                    setEditValue=lambda mockObj, value: mockObj.editFloat(mockObj, value),
                    editDecimals=3, editStep=0.1,
                    getColor=lambda i: mockObj.r,
                    )
    cBool = Column(heading='Bool',
                   getValue=lambda i: mockObj.exampleBool,
                   setEditValue=lambda mockObj, value: mockObj.editBool(mockObj, value),
                   getColor=lambda i: mockObj.b,
                   )

    cPulldown = Column(heading='Pulldown',
                       getValue=lambda i: mockObj.exampleList,
                       setEditValue=lambda mockObj, value: mockObj.editPulldown(mockObj, value),
                       )
    cIcon = Column(heading='Icon',
                   getValue=None,
                   getIcon=lambda i: mockObj.icon,
                   )
    cFlags = Column(heading='Flags',
                    getValue=lambda i: mockObj.flagsList,
                    setEditValue=lambda mockObj, value: mockObj.editFlags(mockObj, value),
                    getColor=lambda i: mockObj.color,
                    )

    table = ObjectTable(parent=popup, columns=[cString, cFloat, cBool, cPulldown, cIcon, cFlags], objects=None, grid=(0, 0))
    table.setObjects([mockObj] * 5)
    print(table.model.index)
    popup.show()
    popup.raise_()
    app.start()
