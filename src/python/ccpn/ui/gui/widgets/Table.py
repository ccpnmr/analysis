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


Inherited from QTableView (http://pyqt.sourceforge.net/Docs/PyQt4/qtableview.html)

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
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:44 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re

from PyQt4 import QtGui, QtCore
import pandas as pd
import os
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.BasePopup import BasePopup
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.TableModel import ObjectTableModel
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CheckBox import CheckBox

from collections import OrderedDict

# BG_COLOR = QtGui.QColor('#E0E0E0')

class ObjectTable(QtGui.QTableView, Base):

  columnSizeHint = 30  # per collumn size hint (to be multiplied by number of collums)
  rowSizeHint = 200  # total size hint (total size for all rows)

  def __init__(self, parent, columns,
               objects=None,
               actionCallback=None, selectionCallback=None,
               multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
               **kw):

    QtGui.QTableView.__init__(self, parent)
    Base.__init__(self, **kw)

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
    # context menu on header
    # headers = self.horizontalHeader()
    # headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    # headers.customContextMenuRequested.connect(lambda: self.tableContextMenu())

    self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.customContextMenuRequested.connect(self.tableContextMenu)

  def clearTable(self):
    "remove all objects from the table"
    self._silenceCallback = True
    self.setObjects([])
    self._silenceCallback = False

  def sizeHint(self):

    return QtCore.QSize(max(10, self.columnSizeHint*len(self.columns)), self.rowSizeHint)

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
      w = self.width()-x
      h = self.height()
      self.graphPanel.setGeometry(x, y, w, h)

    # If the table is connected to a qtgui Splitter it
    # should not resize unless it is specifically asked to.
    # This helps avoiding infinite repaint loops.
    if not (isinstance(self.parent, Splitter) or self.parent.__class__.__name__ == Splitter.__name__) or \
           self.parent.doResize == True:
      return QtGui.QTableView.resizeEvent(self, event)

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
        if self.callback:
          self.callback(obj, row, col)


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
        setColumnWidth(i, width+12)

    if not stretch:
      header.setStretchLastSection(True)

  def closeEvent(self, event):

    self.hideGraph()
    self.hideFilter()
    QtGui.QTableView.closeEvent(self, event)

  def destroy(self, *args):

    if self.filterPanel:
      self.filterPanel.destroy()

    if self.graphPanel:
      self.graphPanel.destroy()

    QtGui.QTableView.destroy(self, *args)

  def tableContextMenu(self, pos):

    menu = QtGui.QMenu()
    # copyMenu =  menu.addAction("Copy Selected")
    exportMenu = menu.addAction("Export Table")
    # searchMenu = menu.addAction("Search")

    action = menu.exec_(self.mapToGlobal(pos))
    if action == exportMenu:
      self.exportDialog()


  def exportDialog(self):

    self.saveDialog = FileDialog(directory='ccpn_Table.xlsx', #default saving name
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
    dataFrame.to_json(path, orient = 'split')

  def tableToDataFrame(self):
    from pandas import DataFrame
    headers = [c.heading for c in self.columns]
    rows = []
    for obj in self.objects:
      rows.append([x.getValue(obj) for x in self.columns])
    dataFrame = DataFrame(rows, index=None, columns=headers)
    dataFrame.apply(pd.to_numeric, errors='ignore')
    return dataFrame

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
    if len(objs)>0:

      rows = []
      for obj in objs:
        rows.append([x.getValue(obj) for x in self.columns])
      cb = QtGui.QApplication.clipboard()
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
    row = selectionModel.currentIndex().row() # the visible row
    indexA = model.index(row, 0)
    indexB = model.index(row, len(self.columns)-1)
    index = model.mapToSource(indexA) # the underlying, original

    if index.row() < 0:
      return

    self.objects[index.row()] = object
    self._syncFilterObjects()

    model.dataChanged.emit(indexA,indexB)


  def setObject(self, i, object):
    """Replaces an object in the _underlying_ list"""

    model = self.model
    self.objects[i] = object
    self._syncFilterObjects()

    index = model.sourceModel().index(i, 0) # the underlying, original
    indexA = model.mapFromSource(index) # the visible row
    indexB = model.index(indexA.row(), len(self.columns)-1)

    model.dataChanged.emit(indexA,indexB)


  def setRowObject(self, row, object):
    """Replaces an object in the _visible_ rows"""

    model = self.model
    indexA = model.index(row, 0) # the visible row
    indexB = model.index(row, len(self.columns)-1) # the visible row
    index = model.mapToSource(indexA) # the underlying, original

    self.objects[index.row()] = object
    self._syncFilterObjects()

    model.dataChanged.emit(indexA,indexB)


  def setObjectsAndColumns(self, objects, columns):
    self._silenceCallback = True
    self.setObjects([])
    self.setColumns(columns)
    self.setObjects(objects)
    self._silenceCallback = False


  def setObjects(self, objects, applyFilter=False):

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
      sourceModel.beginInsertRows(QtCore.QModelIndex(), m, n-1)

    elif m > n:
      sourceModel.beginRemoveRows(QtCore.QModelIndex(), n, m-1)

    indexA = model.index(0, 0)
    indexB = model.index(n-1, c-1)
    model.dataChanged.emit(indexA,indexB) # the visible rows

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
    if self.autoResize:
      self.resizeColumnsToContents()

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
      sourceModel.beginInsertColumns(QtCore.QModelIndex(), m, n-1)

    elif m > n:
      sourceModel.beginRemoveColumns(QtCore.QModelIndex(), n, m-1)

    indexA = model.index(0, 0)
    indexB = model.index(r-1, n-1)
    model.dataChanged.emit(indexA,indexB) # the visible rows
    model.headerDataChanged.emit(QtCore.Qt.Horizontal, 0,n-1)

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
  #     QtGui.QTableView.mousePressEvent(self, event)


EDIT_ROLE = QtCore.Qt.EditRole

class ObjectTableItemDelegate(QtGui.QStyledItemDelegate):

  def __init__(self, parent):

    QtGui.QStyledItemDelegate.__init__(self, parent)
    self.customWidget = None
    self.parent = parent

  def createEditor(self, parentWidget, itemStyle, index): # returns the edit widget

    col = index.column()
    objCol = self.parent.columns[col]

    if objCol.editClass:
      widget = objCol.editClass(None, *objCol.editArgs, **objCol.editKw)
      widget.setParent(parentWidget)
      self.customWidget = True
      return widget

    else:
      obj = self.parent.objects[index.row()]
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
        editor = QtGui.QStyledItemDelegate.createEditor(self, parentWidget, itemStyle, index)

        if isinstance(editor, QtGui.QDoubleSpinBox):
          numDecimals = objCol.editDecimals

          if numDecimals is not None:
            editor.setDecimals(numDecimals)

            if objCol.editStep:
              editor.setSingleStep(objCol.editStep)
            else:
              editor.setSingleStep(10**-numDecimals)

        if isinstance(editor, QtGui.QSpinBox):
          if objCol.editStep:
            editor.setSingleStep(objCol.editStep)

        return editor


  def setEditorData(self, widget, index): # provides the widget with data

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
      return QtGui.QStyledItemDelegate.setEditorData(self, widget, index)

  def updateEditorGeometry(self, widget, itemStyle, index):# ensures that the editor is displayed correctly

    if self.customWidget:
      cellRect = itemStyle.rect
      x = cellRect.x()
      y = cellRect.y()
      hint = widget.sizeHint()

      if hint.height() > cellRect.height():
        if isinstance(widget, QtGui.QComboBox): # has a popup anyway
          widget.move(cellRect.topLeft())

        else:
          pos = widget.mapToGlobal(cellRect.topLeft())
          widget.setParent(self.parent, QtCore.Qt.Popup) # popup so not confined
          widget.move(pos)

      else:
        width = max(hint.width(), cellRect.width())
        height = max(hint.height(), cellRect.height())
        widget.setGeometry(x, y, width, height)


    else:
      return QtGui.QStyledItemDelegate.updateEditorGeometry(self, widget, itemStyle, index)

  def setModelData(self, widget, mode, index):#returns updated data

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

      del widget
      model = index.model()
      model.setData(index, value, EDIT_ROLE)

    else:
      return QtGui.QStyledItemDelegate.setModelData(self, widget, mode, index)


class ObjectHeaderView(QtGui.QHeaderView):

  def __init__(self, orient, parent):

    QtGui.QHeaderView.__init__(self, orient, parent)
    self.table = parent

  #def sizeHint(self):

  #  return QtCore.QSize(30*len(self.table.columns), self.table.bbox('A').height())

  #def minimumSize(self):
  #
  #  return QtCore.QSize(30*len(self.table.columns), self.table.bbox('A').height())

LESS_THAN = QtGui.QSortFilterProxyModel.lessThan


class ObjectTableProxyModel(QtGui.QSortFilterProxyModel):

  def __init__(self, parent):

    QtGui.QSortFilterProxyModel.__init__(self, parent=parent)
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

class ObjectTableExport(QtGui.QDialog, Base):

  def __init__(self, table=None, **kw):
    super(ObjectTableExport, self).__init__(table)
    # BasePopup.__init__(self, title='Export Table Text', transient=True, modal=True)
    Base.__init__(self, **kw)
    self.setWindowFlags(QtCore.Qt.Tool)

    self.table = table
    label = Label(self, 'Columns to export:', grid=(0, 0), gridSpan=(1, 2))

    labels = ['Row Number',] + [c.heading.replace('\n', ' ') for c in table.columns]
    values = [True] * len(labels)
    label = Label(self, 'Export format:', grid=(3,0))
    self.formatPulldown = PulldownList(self, EXPORT_FORMATS, grid=(3,1))
    self.setMaximumWidth(300)


SEARCH_MODES = [ 'Literal','Case Sensitive Literal','Regular Expression' ]

class ColumnViewSettings(Widget):
  ''' hide show check boxes corresponding to the table columns '''

  def __init__(self, table, parent=None, **kw):
    Widget.__init__(self, parent, setLayout=True, **kw)
    # Base.__init__(self, **kw)
    self.table = table
    self.checkBoxes = []
    self.initCheckBoxes()
    self.filterLabel =  Label(self, 'Display Columns', grid=(0,0), vAlign='b')
  def initCheckBoxes(self):
    columns = self.table.columns
    if columns:
      for i, colum in enumerate(columns):
        tipTex = 'Hide/Show %s column' % colum.heading
        cb = CheckBox(self, text=colum.heading, grid=(1, i), callback=self.checkBoxCallBack,  checked=True,
                      hAlign='c',tipText= tipTex,)

        cb.setMinimumSize(cb.sizeHint()*1.3)

        self.checkBoxes.append(cb)


  def checkBoxCallBack(self):
    checkBox = self.sender()
    name = checkBox.text()
    if checkBox.isChecked():
      self.table._showColumn(name)
    else:
      self.table._hideColumn(name)

  def updateWidgets(self, table):
    self.table = table
    if self.checkBoxes:
      print(self.checkBoxes)
      for cb in self.checkBoxes:
        cb.deleteLater()
    self.checkBoxes = []
    self.initCheckBoxes()




class ObjectTableFilter(Widget):

  def __init__(self, table, parent=None, **kw):
    Widget.__init__(self, parent, setLayout=True, **kw)
    self.table = table

    self.origObjects = self.table.objects

    labelColumn = Label(self, 'Search in', grid=(0,0), hAlign='c')

    self.colPulldown = PulldownList(self, grid=(0,1), hAlign='c')

    labelObjects = Label(self, 'Search for', grid=(0,2), hAlign='c')

    self.edit = LineEdit(self,grid=(0,3), hAlign='c')


    self.searchButtons = ButtonList(self, texts=['Reset','Search'],
                       tipTexts=['Restore Table','Search'],
                       callbacks=[self.restoreTable,self.findOnTable ],
                       grid=(0, 4), hAlign='c')

    self.msg = Label(self, text='Not Found', grid=(1, 0))
    self.msg.hide()
    self.setColumnPullDown()

  def setColumnPullDown(self):
    columns = self.table.columns
    texts = [c.heading for c in columns]
    objectsRange = range(len(columns))

    self.colPulldown.addItem('Whole Table', object=None)
    for i, text in enumerate(texts):
      self.colPulldown.addItem(text, objectsRange[i])
    self.colPulldown.setIndex(0)

  def updateColumnPullDown(self, table):
    self.table = table
    self.origObjects = self.table.objects
    self.setColumnPullDown()




  def restoreTable(self):
    # origObjects =  [obj for obj in self.origObjects if obj is not None]
    print(self.origObjects)
    self.table.setObjects(self.origObjects)
    self.msg.hide()
    self.edit.clear()

  def findOnTable(self):
    if self.edit.text() == '' or None:
      self.msg.show()
      return
    self.table.setObjects(self.origObjects)
    self.hideNotFoundMsg()

    text = self.edit.text()
    columns = self.table.columns

    if self.colPulldown.currentObject() is None:
      # serch in the whole table
      objs = [o for o in self.colPulldown.objects if o is not None]
      allMatched = []
      for obj in objs:
        objCol = columns[obj]
        matched = self.searchMatches(objCol, text)
        allMatched.append(matched)
      # matched = [i for m in allMatched for i in m]   #making a single list of matching objs
      matched = set([i for m in allMatched for i in m])   #making a single list of matching objs
      print(len(matched))
    else:
      objCol = columns[self.colPulldown.currentObject()]

      matched = self.searchMatches(objCol, text)

    if matched:
      self.table.setObjects(matched)
    else:
      self.showNotFoundMsg()


  def searchMatches(self, objCol, text):
    matched = []
    objs = self.table.objects
    for obj in objs:
      value = u'%s' % (objCol.getValue(obj))
      if str(text) in str(value):
        matched.append(obj)
      elif str(text) == str(value):
        matched.append(obj)
    return  matched




  def setFilteredObjects(self):
    selected = self.table.getSelectedObjects()
    self.table.setObjects(selected)

  def hideNotFoundMsg(self):
    self.msg.hide()

  def showNotFoundMsg(self):
    self.msg.show()

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
    # Alignment combinations broken in PyQt4 v1.1.1
    # Use better default than top left
    self.alignment = QtCore.Qt.AlignCenter
    # self.orderFunc = orderFunc

    self.getIcon = getIcon or self._defaultIcon
    self.getColor = getColor or self._defaultColor
    self.tipText = tipText

    self._checkTextAttrs()

  def orderFunc(self, objA, objB):
    return ( universalSortKey(self.getValue(objA)) < universalSortKey(self.getValue(objB)) )


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
      self.getValue = lambda obj: getattr(obj,attr)

    if isinstance(self.getEditValue, str):
      attr = self.getEditValue
      self.getEditValue = lambda obj: getattr(obj,attr)

    if isinstance(self.setEditValue, str):
      attr = self.setEditValue
      self.setEditValue = lambda obj, value: setattr(obj,attr,value)

    if isinstance(self.getIcon, QtGui.QIcon):
      self.defaultIcon = self.getIcon
      self.getIcon = self._defaultIcon

  def _defaultText(self, obj):

    return ' '

  def _defaultColor(self, obj):

    return BG_COLOR

  def _defaultIcon(self, obj):

    return self.defaultIcon
