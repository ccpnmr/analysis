"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base
from ccpncore.gui.BasePopup import BasePopup
from ccpncore.gui.Splitter import Splitter
from ccpncore.gui.TableModel import ObjectTableModel
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

import re

BG_COLOR = QtGui.QColor('#E0E0E0')

class ObjectTable(QtGui.QTableView, Base):

  def __init__(self, parent, columns, objects=None, callback=None,
               multiSelect=True, selectRows=True, numberRows=False, **kw):

    QtGui.QTableView.__init__(self, parent)
    Base.__init__(self, **kw)

    self.graphPanel = None
    self.filterPanel = None
    self.model = None
    self.columns = columns
    self.objects = list(objects) or []
    self.callback = callback
    self.fontMetric = QtGui.QFontMetricsF(self.font())
    self.bbox = self.fontMetric.boundingRect
    self._silenceCallback = False
    self.selectRows = selectRows

    self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
    self.setHorizontalScrollMode(self.ScrollPerItem)
    self.setVerticalScrollMode(self.ScrollPerItem)
    self.setSortingEnabled(True)
    self.setAutoFillBackground(True)

    #self.setSizePolicy(QtGui.QSizePolicy.Preferred,
    #                   QtGui.QSizePolicy.Preferred)

    if multiSelect:
      self.setSelectionMode(self.ExtendedSelection)
      # + Continuous etc possible
    else:
      self.setSelectionMode(self.SingleSelection)

    if selectRows:
      self.setSelectionBehavior(self.SelectRows)
    else:
      self.setSelectionBehavior(self.SelectItems)
      # + Columns possible

    self._setupModel()
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

    if numberRows:
      header.setVisible(True)
    else:
      header.setVisible(False)

    header = ObjectHeaderView(QtCore.Qt.Horizontal, self)
    header.setMovable(True)
    header.setMinimumSectionSize(30)
    header.setDefaultSectionSize(30)
    #header.setSortIndicatorShown(False)
    #header.setStyleSheet('QHeaderView::down-arrow { image: url(icons/sort-up.png);} QHeaderView::up-arrow { image: url(icons/sort-down.png);}')

    self.setupHeaderStretch()

  def sizeHint(self):

    return QtCore.QSize(max(10, 30*len(self.columns)),200)

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

    if self.graphPanel and self.graphPanel.isVisible():
      graph = self.graphPanel.graph
      graph.coordsOff()
      rows = self.getSelectedRows()
      vLines = []
      hLines = []

      for row in rows:
        for dataSet in graph.dataSets:
          x, y = dataSet.dataPoints[row][:2]
          vLines.append(x)
          hLines.append(y)

      graph.drawVerticalLines(vLines)
      graph.drawHorizontalLines(hLines)

    elif self.callback:
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
          self.callback(obj, row, col)

      else:
        self.callback(None, row, col)

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

  def exportText(self):

    popup = ObjectTableExport(self)
    popup.show()
    popup.move(self.window().pos())

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

    self.setObjects([])
    self.setColumns(columns)
    self.setObjects(objects)


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

class ObjectTableExport(BasePopup):

  def __init__(self, table):

    BasePopup.__init__(self, title='Export Table Text', transient=True, modal=True)
    self.setWindowFlags(QtCore.Qt.Tool)

    self.table = table

    label = Label(self, 'Columns to export:', grid=(0,0), gridSpan=(1,2))

    labels = ['Row Number',] + [c.heading.replace('\n', ' ') for c in table.columns]
    values = [True] * len(labels)


    label = Label(self, 'Export format:', grid=(3,0))

    self.formatPulldown = PulldownList(self, EXPORT_FORMATS, grid=(3,1))



    self.setMaximumWidth(300)


SEARCH_MODES = [ 'Literal','Case Sensitive Literal','Regular Expression' ]


class ObjectTableFilter(BasePopup):

  def __init__(self, table):

    BasePopup.__init__(self, title='Filter Table')

    self.table = table
    self.status = None
    self.origObjects = table.objects

    label = Label(self, 'Filter Column', grid=(0,0))

    columns = table.columns

    texts = [c.heading for c in columns]
    objects = range(len(columns))

    tIndex = table.getCurrentIndex()
    if tIndex is None:
      index = 0
    else:
      index = tIndex.column()

    self.colPulldown = PulldownList(self, texts, objects, index=index, grid=(0,1))

    label = Label(self, 'Objects to filter', grid=(0,2))





    texts = ['Reset','Filter\nInclude','Filter\nExclude',None]
    callbacks = [self.unfilterTable, self.filterInclude,
                 self.filterExclude, self.close]
    icons = ['icons/edit-undo.png', None, None, 'icons/window-close.png']

    self.setWindowFlags(QtCore.Qt.Tool)
    self.setSize(300,100)

  def close(self):

    BasePopup.close(self)

  def unfilterTable(self):

    self.table.setObjects(self.origObjects)
    self.status = None

  def filterInclude(self, *event):

    self.filterTable(True)

  def filterExclude(self, *event):

    self.filterTable(False)

  def filterTable(self, includeMatches=True):

    if not self.origObjects:
      self.status = None
      return

    string = self.entry.get()
    if not string:
      self.status = None
      return

    self.status = includeMatches
    columns = self.table.columns
    objCol = columns[self.colPulldown.currentObject()]
    mode = self.filterModeRadio.get()
    flag = re.S

    def exclude(a,b,c):
      return not re.search(a,b,c)

    if includeMatches:
      find = re.search
    else:
      find = exclude

    if mode != SEARCH_MODES[2]:
      string = re.escape(string)

    if mode == SEARCH_MODES[0]:
      flag = re.I

    objects = []
    objectsAppend = objects.append

    if self.filterObjRadio.getIndex() == 0:
      filterObjs = self.origObjects
    else:
      filterObjs = self.table.getSelectedObjects()

    for  obj in filterObjs:
      value = u'%s' % (objCol.getValue(obj))
      match = find(string, value, flag)

      if match:
        objectsAppend(obj)

    self.table.clearSelection()
    self.table.setObjects(objects, None)

class Column:

  def __init__(self, heading, getValue, getEditValue=None, setEditValue=None,
               editClass=None, editArgs=None, editKw=None, tipText=None,
               getColor=None, getIcon=None, stretch=False, format=None,
               editDecimals=None, editStep=None, alignment=QtCore.Qt.AlignLeft,
               orderFunc=None):

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
    # Alignment combinations broken in PySide v1.1.1
    # Use better default than top left
    self.alignment = QtCore.Qt.AlignCenter
    self.orderFunc = orderFunc

    self.getIcon = getIcon or self._defaultIcon
    self.getColor = getColor or self._defaultColor
    self.tipText = tipText

    self._checkTextAttrs()

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

    return None

  def _defaultColor(self, obj):

    return BG_COLOR

  def _defaultIcon(self, obj):

    return self.defaultIcon
