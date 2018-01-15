"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import re

from PyQt4 import QtGui, QtCore
import pandas as pd
from pyqtgraph import TableWidget
from pyqtgraph.widgets.TableWidget import _defersort
import os
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.DataFrameObject import DataFrameObject
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
from ccpn.ui.gui.widgets.TableFilter import ObjectTableFilter
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets.TableModel import ObjectTableModel
from ccpn.ui.gui.widgets.SearchWidget import attachSearchWidget
from ccpn.core.lib.Notifiers import Notifier
from functools import partial
from collections import OrderedDict

from collections import OrderedDict
from ccpn.util.Logging import getLogger

# BG_COLOR = QtGui.QColor('#E0E0E0')
# TODO:ED add some documentation here


class QuickTable(TableWidget, Base):
  ICON_FILE = os.path.join(os.path.dirname(__file__), 'icons', 'editable.png')

  @staticmethod
  def _getCommentText(obj):
    """
    CCPN-INTERNAL: Get a comment from QuickTable
    """
    try:
      if obj.comment == '' or not obj.comment:
        return ''
      else:
        return obj.comment
    except:
      return ''

  @staticmethod
  def _setComment(obj, value):
    """
    CCPN-INTERNAL: Insert a comment into QuickTable
    """
    # ejb - why is it blanking a notification here?
    # NmrResidueTable._project.blankNotification()
    obj.comment = value
    # NmrResidueTable._project.unblankNotification()

  def __init__(self, parent=None,
               mainWindow=None,
               dataFrameObject=None,      # collate into a single object that can be changed quickly
               actionCallback=None, selectionCallback=None, checkBoxCallback = None,
               multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
               enableExport=True, enableDelete=True,
               hideIndex=True, stretchLastSection=True,
               **kw):
    """
    Create a new instance of a TableWidget with an attached Pandas dataFrame
    :param parent:
    :param mainWindow:
    :param dataFrameObject:
    :param actionCallback:
    :param selectionCallback:
    :param multiSelect:
    :param selectRows:
    :param numberRows:
    :param autoResize:
    :param enableExport:
    :param enableDelete:
    :param hideIndex:
    :param kw:
    """
    TableWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self._parent = parent

    # set the application specfic links
    self.mainWindow = mainWindow
    self.application = None
    self.project = None
    self.current = None

    if self.mainWindow:
      self.application = mainWindow.application
      self.project = mainWindow.application.project
      self.current = mainWindow.application.current

    # initialise the internal data storage
    self._dataFrameObject = dataFrameObject

    # set the preferred scrolling behaviour
    self.setHorizontalScrollMode(self.ScrollPerItem)
    self.setVerticalScrollMode(self.ScrollPerItem)

    # define the multiselection behaviour
    self.multiSelect = multiSelect
    if multiSelect:
      self.setSelectionMode(self.ExtendedSelection)
    else:
      self.setSelectionMode(self.SingleSelection)

    # define the set selection behaviour
    self.selectRows = selectRows
    if selectRows:
      self.setSelectionBehavior(self.SelectRows)
    else:
      self.setSelectionBehavior(self.SelectItems)

    self._checkBoxCallback = checkBoxCallback
    # set all the elements to the same size
    self.hideIndex = hideIndex
    self._setDefaultRowHeight()

    # enable sorting and sort on the first column
    self.setSortingEnabled(True)
    self.sortByColumn(0, QtCore.Qt.AscendingOrder)

    # enable drag and drop operations on the table - why not working?
    self.setDragEnabled(True)
    self.acceptDrops()
    self.setDragDropMode(self.InternalMove)
    self.setDropIndicatorShown(True)

    # set the last column to expanding
    self.horizontalHeader().setStretchLastSection(stretchLastSection)

    # enable the right click menu
    self.searchWidget = None
    self._setHeaderContextMenu()
    self._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)

    # populate if a dataFrame has been passed in
    if dataFrameObject:
      self.setTableFromDataFrame(dataFrameObject.dataFrame)
      self.showColumns()

    # enable callbacks
    self._actionCallback = actionCallback
    self._selectionCallback = selectionCallback
    self._silenceCallback = False
    if self._actionCallback:
      self.doubleClicked.connect(self._doubleClickCallback)
    else:
      self.doubleClicked.connect(self._defaultDoubleClick)
    if self._selectionCallback:
      # self.cellClicked.connect(self._cellClicked)
      self.itemClicked.connect(self._cellClicked)

    # set the delegate for editing
    delegate = QuickTableDelegate(self)
    self.setItemDelegate(delegate)

    # set the callback for changing selection on table
    model = self.selectionModel()
    model.selectionChanged.connect(self._selectionTableCallback)

    # set internal flags
    self._mousePressed = False
    self._tableData = {}
    self._tableNotifier = None
    self._rowNotifier = None
    self._cellNotifiers = []
    self._selectCurrentNotifier = None
    self._icons = [self.ICON_FILE]
    self._stretchLastSection = stretchLastSection

    # set the minimum size the table can collapse to
    self.setMinimumSize(30, 30)
    self.searchWidget = None
    self._parent.layout().setVerticalSpacing(0)
  #
  # def _cellClicked(self, row, col):
  #   self._currentRow = row
  #   self._currentCol = col

  def _cellClicked(self, item):
    if item:
      if isinstance(item.value, bool):

        self._checkBoxTableCallback(item)
      try:
        if self._selectionCallback:
          self._currentRow = item.row()
          self._currentCol = item.column()
      except:
        # Fixme
        # item has been deleted error
        pass
    #
  def _checkBoxCallback(self, data):
      pass

  def _defaultDoubleClick(self, itemSelection):

    model = self.selectionModel()

    # selects all the items in the row
    selection = model.selectedIndexes()

    if selection:
      row = itemSelection.row()
      col = itemSelection.column()
      if self._dataFrameObject.columnDefinitions.setEditValues[col]:  # ejb - editable fields don't actionCallback:

        item = self.item(row, col)
        item.setEditable(True)
        # self.itemDelegate().closeEditor.connect(partial(self._changeMe, row, col))
        # item.textChanged.connect(partial(self._changeMe, item))
        self.editItem(item)

  def _doubleClickCallback(self, itemSelection):
    # TODO:ED generate a callback dict for the selected item
    # data = OrderedDict()
    # data['OBJECT'] = return pid, key/values, row, col

    model = self.selectionModel()

    # selects all the items in the row
    selection = model.selectedIndexes()

    if selection:
      row = itemSelection.row()
      col = itemSelection.column()
      # row = self._currentRow        # read from the cellClicked connect
      # col = self._currentCol

      data = {}
      for iSelect in selection:
        colPid = iSelect.column()
        colName = self.horizontalHeaderItem(colPid).text()
        data[colName] = model.model().data(iSelect)

      objIndex = data['Pid']
      # obj = self._dataFrameObject.indexList[objIndex]    # item.index needed

      obj = self.project.getByPid(objIndex)

      if obj:
        data = CallBack(theObject = self._dataFrameObject
                        , object = obj
                        , index = objIndex
                        , targetName = obj.className
                        , trigger = CallBack.DOUBLECLICK
                        , row = row
                        , col = col
                        , rowItem = data)

        if self._actionCallback and not self._dataFrameObject.columnDefinitions.setEditValues[col]:    # ejb - editable fields don't actionCallback
          self._actionCallback(data)
        elif self._dataFrameObject.columnDefinitions.setEditValues[col]:    # ejb - editable fields don't actionCallback:
          item = self.item(row, col)
          item.setEditable(True)
          # self.itemDelegate().closeEditor.connect(partial(self._changeMe, row, col))
          # item.textChanged.connect(partial(self._changeMe, item))
          self.editItem(item)         # enter the editing mode

  @_defersort
  def setRow(self, row, vals):
    if row > self.rowCount() - 1:
      self.setRowCount(row + 1)
    for col in range(len(vals)):
      val = vals[col]
      item = self.itemClass(val, row)
      item.setEditable(self.editable)
      sortMode = self.sortModes.get(col, None)
      if sortMode is not None:
        item.setSortMode(sortMode)
      format = self._formats.get(col, self._formats[None])
      item.setFormat(format)
      self.items.append(item)
      self.setItem(row, col, item)

      # item.setValue(val)  # Required--the text-change callback is invoked
      # when we call setItem.
      if isinstance(val, bool): # this will create a check box if the value is a bool
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        state = 2 if val else 0
        item.setCheckState(state)

      if isinstance(val, list or tuple):
        pulldown = PulldownList(None, )
        pulldown.setData(*val)
        self.setCellWidget(row, col, pulldown)


      else:
        item.setValue(val)


  def _changeMe(self, row, col, widget, endEditHint):
    text = widget.text()
    # TODO:ED process setting of object in here

    item = self.item(row, col)

    print ('>>>changeMe', row, col)

    # obj = self._dataFrameObject.objects[row]
    # self._dataFrameObject.columnDefinitions.setEditValues[col](obj, text)
    pass

  def _selectionTableCallback(self, itemSelection):
    # TODO:ED generate a callback dict for the selected item
    # data = OrderedDict()
    # data['OBJECT'] = return pid, key/values, row, col

    if not self._silenceCallback:
    # if not self._mousePressed:
      objList = self.getSelectedObjects()
      # model = self.selectionModel()
      #
      # # selects all the items in the row
      # selection = model.selectedIndexes()
      #
      # if selection:
      # row = itemSelection.row()
      # col = itemSelection.column()
      #
      #   data = {}
      #   objList = []
      #   for iSelect in selection:
      #     col = iSelect.column()
      #     colName = self.horizontalHeaderItem(col).text()
      #     data[colName] = model.model().data(iSelect)
      #
      #     objIndex = data['Pid']
      #     obj = self.project.getByPid(objIndex)
      #     if obj:
      #       objList.append(obj)

      if objList:
        data = CallBack(theObject = self._dataFrameObject
                        , object = objList
                        , index = 0
                        , targetName = objList[0].className
                        , trigger = CallBack.DOUBLECLICK
                        , row = 0
                        , col = 0
                        , rowItem = None)

        self._selectionCallback(data)


  def _checkBoxTableCallback(self, itemSelection):
    state = True if itemSelection.checkState() == 2 else False
    value = itemSelection.value
    if not state == value:
      if not self._silenceCallback:
        selectionModel = self.selectionModel()
        selectionModel.clearSelection()
        selectionModel.select(self.model().index(itemSelection.row(), 0)
                              , selectionModel.Select | selectionModel.Rows)
        objList = self.getSelectedObjects()

        if objList:
          data = CallBack(theObject = self._dataFrameObject
                          , object = objList
                          , index = 0
                          , targetName = objList[0].className
                          , trigger = CallBack.DOUBLECLICK
                          , row = itemSelection.row()
                          , col = itemSelection.column()
                          , rowItem = itemSelection
                          , checked = state)
          textHeader = self.horizontalHeaderItem(itemSelection.column()).text()
          if textHeader:
            self._dataFrameObject.setObjAttr(textHeader, objList[0], state)
            # setattr(objList[0], textHeader, state)
        else:
          data = CallBack(theObject=self._dataFrameObject
                          , object=None
                          , index=0
                          , targetName=None
                          , trigger=CallBack.DOUBLECLICK
                          , row=itemSelection.row()
                          , col=itemSelection.column()
                          , rowItem=itemSelection
                          , checked = state)
        self._checkBoxCallback(data)

  def showColumns(self, dataFrameObject):
    # show the columns in the list
    for i, colName in enumerate(dataFrameObject.headings):
      if dataFrameObject.hiddenColumns:
        if colName in dataFrameObject.hiddenColumns:
          self.hideColumn(i)
        else:
          self.showColumn(i)

          if dataFrameObject.columnDefinitions.setEditValues[i]:

            # need to put it into the header
            header = self.horizontalHeaderItem(i)

            icon = QtGui.QIcon(self._icons[0])
            # item = self.item(0, i)
              # TableWidget.QTableWidgetItem(icon, 'Boing')  # Second argument
            # if item:
            #   item.setIcon(icon)
            #   self.setItem(0, i, item)
            if header:
              header.setIcon(icon)

  def _setDefaultRowHeight(self):
    # set a minimum height to the rows based on the fontmetrics of a generic character
    self.fontMetric = QtGui.QFontMetricsF(self.font())
    self.bbox = self.fontMetric.boundingRect
    rowHeight = self.bbox('A').height() + 4

    headers = self.verticalHeader()
    headers.setResizeMode(QtGui.QHeaderView.Fixed)
    headers.setDefaultSectionSize(rowHeight)

    # and hide the row labels
    if self.hideIndex:
      headers.hide()

    # for qt5 and above
    # QHeaderView * verticalHeader = myTableView->verticalHeader();
    # verticalHeader->setSectionResizeMode(QHeaderView::Fixed);
    # verticalHeader->setDefaultSectionSize(24);

  def mousePressEvent(self, event):
    # handle a mouse button press to popup context menu
    if event.button() == QtCore.Qt.RightButton:
      # stops the selection from the table when the right button is clicked
      event.accept()
    elif event.button() == QtCore.Qt.LeftButton:

      # we are selecting from the table
      self._mousePressed = True
      event.ignore()
      super(QuickTable, self).mousePressEvent(event)
    else:
      event.ignore()
      super(QuickTable, self).mousePressEvent(event)

  def mouseReleaseEvent(self, event):
    self._mousePressed = False
    super(QuickTable, self).mouseReleaseEvent(event)

  def _setHeaderContextMenu(self):
    headers = self.horizontalHeader()
    headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)

  def _setContextMenu(self, enableExport=True, enableDelete=True):
    self.tableMenu = QtGui.QMenu()
    if enableExport:
      self.tableMenu.addAction("Export Table", self.exportDialog )
    if enableDelete:
      self.tableMenu.addAction("Delete", self.deleteObjFromTable)

    # ejb - added these but don't think they are needed
    # self.tableMenu.addAction("Select All", self.selectAllObjects)
    self.tableMenu.addAction("Clear Selection", self.clearSelection)

    self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.customContextMenuRequested.connect(self._raiseTableContextMenu)

  def _raiseTableContextMenu(self, pos):
    pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)
    action = self.tableMenu.exec_(self.mapToGlobal(pos))

  def _raiseHeaderContextMenu(self, pos):
    if self.searchWidget is None:
      if not attachSearchWidget(self):
        getLogger().warning('Search option not available')

    pos = QtCore.QPoint(pos.x(), pos.y()+10) #move the popup a bit down. Otherwise can trigger an event if the pointer is just on top the first item

    self.headerContextMenumenu = QtGui.QMenu()
    columnsSettings = self.headerContextMenumenu.addAction("Columns Settings...")
    searchSettings = None
    if self.searchWidget is not None:
      searchSettings = self.headerContextMenumenu.addAction("Search")
    action = self.headerContextMenumenu.exec_(self.mapToGlobal(pos))

    if action == columnsSettings:
      settingsPopup = ColumnViewSettingsPopup(parent=self._parent, dataFrameObject=self._dataFrameObject)   #, hideColumns=self._hiddenColumns, table=self)
      settingsPopup.raise_()
      settingsPopup.exec_()  # exclusive control to the menu and return _hiddencolumns

    if action == searchSettings:
      self.showSearchSettings()

  def showSearchSettings(self):
    if self.searchWidget is not None:
      self.searchWidget.show()

  # def _addSearchWidget(self):
  #   # TODO:Luca Add search option for any table
  #   if self.parent is not None:
  #     parentLayout = None
  #     if isinstance(self._parent, Base):
  #     # if hasattr(self.parent, 'getLayout'):
  #       parentLayout = self._parent.getLayout()
  #
  #     if isinstance(parentLayout, QtGui.QGridLayout):
  #       idx = parentLayout.indexOf(self)
  #       location = parentLayout.getItemPosition(idx)
  #       if location is not None:
  #         if len(location)>0:
  #           row, column, rowSpan, columnSpan = location
  #           self.searchWidget = QuickTableFilter(table=self, grid=(0,0), vAlign='B')
  #           parentLayout.addWidget(self.searchWidget, row+1, column, rowSpan+1, columnSpan)
  #           self.searchWidget.hide()
  #   return True
  #
  def deleteObjFromTable(self):
    selected = self.getSelectedObjects()
    if selected:
      n = len(selected)
      title = 'Delete Item%s' % ('' if n == 1 else 's')
      msg = 'Delete %sselected item%s from the project?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
      if MessageDialog.showYesNo(title, msg):

        if hasattr(selected[0], 'project'):
          thisProject = selected[0].project
          thisProject._startCommandEchoBlock('application.table.deleteFromTable', [sI.pid for sI in selected])
          try:

            # self.blockSignals(True)
            self._silenceCallback = True

            # TODO:ED check why this does not undo as single event
            for obj in selected:
              if hasattr(obj, 'pid'):

                # print ('>>> deleting', obj)
                obj.delete()

          except Exception as es:
            getLogger().warning(str(es))
          finally:

            self._silenceCallback = False
            # self.blockSignals(False)

            thisProject._endCommandEchoBlock()

        else:

          # TODO:ED this is deleting from PandasTable, check for another way to get project
          for obj in selected:
            if hasattr(obj, 'pid'):
              obj.delete()

  def refreshTable(self):
    self.setTableFromDataFrameObject(self._dataFrameObject)

  def refreshHeaders(self):
    self.hide()
    self._silenceCallback = True

    self.setColumnCount(self._dataFrameObject.numColumns)
    self.setHorizontalHeaderLabels(self._dataFrameObject.headings)
    self.showColumns(self._dataFrameObject)
    self.resizeColumnsToContents()
    self.horizontalHeader().setStretchLastSection(self._stretchLastSection)

    self.show()
    self._silenceCallback = False

  def setTableFromDataFrameObject(self, dataFrameObject):
    # populate the table from the the Pandas dataFrame
    self._dataFrameObject = dataFrameObject

    self.hide()
    self._silenceCallback = True

    # keep the original sorting method
    sortOrder = self.horizontalHeader().sortIndicatorOrder()
    sortColumn = self.horizontalHeader().sortIndicatorSection()

    if not dataFrameObject.dataFrame.empty:
      self.setData(dataFrameObject.dataFrame.values)
    else:
      self.clearTable()
      self.setColumnCount(dataFrameObject.numColumns)

    self.setData(dataFrameObject.dataFrame.values)

    self.setHorizontalHeaderLabels(dataFrameObject.headings)

    # needed after setting the column headings
    self.showColumns(dataFrameObject)
    self.resizeColumnsToContents()
    self.horizontalHeader().setStretchLastSection(self._stretchLastSection)

    # re-sort the table
    if sortColumn < self.columnCount():
      self.sortByColumn(sortColumn, sortOrder)

    self.show()
    self._silenceCallback = False

  def getDataFrameFromList(self, table=None
                           , buildList=None
                           , colDefs=None
                           , hiddenColumns=None):
    """
    Return a Pandas dataFrame from an internal list of objects
    The columns are based on the 'func' functions in the columnDefinitions

    :param buildList:
    :param colDefs:
    :return pandas dataFrameObject:
    """
    allItems = []
    objects = []

    # objectList = {}
    # indexList = {}

    for col, obj in enumerate(buildList):
      listItem = OrderedDict()
      for header in colDefs.columns:
        listItem[header.headerText] = header.getValue(obj)

      allItems.append(listItem)
      objects.append(obj)

      # indexList[str(listItem['Index'])] = obj
      # objectList[obj.pid] = listItem['Index']

      # indexList[str(col)] = obj
      # objectList[obj.pid] = col

      # indexList[str(col)] = obj
      # objectList[obj.pid] = col

    return DataFrameObject(dataFrame=pd.DataFrame(allItems, columns=colDefs.headings)
                           , objectList=objects or []
                           # , indexList=indexList
                           , columnDefs=colDefs or []
                           , hiddenColumns=hiddenColumns or []
                           , table=table)

  def getDataFrameFromRows(self, table=None
                           , dataFrame=None
                           , colDefs=None
                           , hiddenColumns=None):
    """
    Return a Pandas dataFrame from the internal rows of an internal Pandas dataFrame
    The columns are based on the 'func' functions in the columnDefinitions

    :param buildList:
    :param colDefs:
    :return pandas dataFrame:
    """
    allItems = []
    objects = []
    # objectList = None
    # indexList = {}

    buildList = dataFrame.as_namedtuples()
    for ind, obj in enumerate(buildList):
      listItem = OrderedDict()
      for header in colDefs.columns:
        listItem[header.headerText] = header.getValue(obj)

      allItems.append(listItem)

    #   # TODO:ED need to add object links in here, but only the top object exists so far
    #   if 'Index' in listItem:
    #     indexList[str(listItem['Index'])] = obj
    #     objectList[obj.pid] = listItem['Index']
    #   else:
    #     indexList[str(ind)] = obj
    #     objectList[obj.pid] = ind

    return DataFrameObject(dataFrame=pd.DataFrame(allItems, columns=colDefs.headings)
                           , objectList=objects
                           # , indexList=indexList
                           , columnDefs=colDefs
                           , hiddenColumns=hiddenColumns
                           , table=table)

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
       formatTypes[extension](self._dataFrameObject.dataFrame, path)
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

  def scrollToSelectedIndex(self):
    h = self.horizontalHeader()
    for i in range(h.count()):
      if not h.isSectionHidden(i) and h.sectionViewportPosition(i) >= 0:
        if self.getSelectedRows():
          self.scrollTo(self.model().index(self.getSelectedRows()[0], i),
                                        self.PositionAtCenter)

  def getSelectedRows(self):

    model = self.selectionModel()

    # selects all the items in the row
    selection = model.selectedIndexes()

    # if self.selectRows:
    #   selection = model.selectedRows(column=0)
    # else:
    #   selection = model.selectedIndexes()

    rows = [i.row() for i in selection]
    #rows = list(set(rows))
    #rows.sort()

    return rows

  def getSelectedObjects(self):

    model = self.selectionModel()

    # selects all the items in the row
    selection = model.selectedIndexes()

    if selection:
      selectedObjects = []
      rows = []

      for iSelect in selection:
        row = iSelect.row()
        col = iSelect.column()
        colName = self.horizontalHeaderItem(col).text()
        if colName == 'Pid':

          if row not in rows:
            rows.append(row)
            objIndex = model.model().data(iSelect)

            # if str(objIndex) in self._dataFrameObject.indexList:
              # obj = self._dataFrameObject.indexList[str(objIndex)]  # item.index needed
              # selectedObjects.append(obj)

            obj = self.project.getByPid(objIndex)
            if obj:
              selectedObjects.append(obj)

      return selectedObjects
    else:
      return None

  def clearSelection(self):
    selectionModel = self.selectionModel()
    selectionModel.clearSelection()

  def selectObjects(self, objList:list, setUpdatesEnabled:bool=False):
    """
    Selection the object in the table
    """
    # skip if the table is empty
    if not self._dataFrameObject:
      return

    selectionModel = self.selectionModel()

    if objList:
      # disable callbacks while populating the table

      self._silenceCallback = True
      # self.blockSignals(True)
      self.setUpdatesEnabled(setUpdatesEnabled)

      if not self._mousePressed:
        selectionModel.clearSelection()       # causes a clear problem here
                                              # strange tablewidget cmd/selection problem

      for obj in objList:
        row = self._dataFrameObject.find(self, str(obj.pid))
        if row:
          selectionModel.select(self.model().index(row, 0)
                                         , selectionModel.Select | selectionModel.Rows)

      self.setUpdatesEnabled(True)
      # self.blockSignals(False)
      self._silenceCallback = False

      self.setFocus(QtCore.Qt.OtherFocusReason)

  def _highLightObjs(self, selection):

    # skip if the table is empty
    if not self._dataFrameObject:
      return

    selectionModel = self.selectionModel()

    if selection:
      uniqObjs = set(selection)

      rowObjs = []
      for obj in uniqObjs:
        if obj in self._dataFrameObject.objects:
          rowObjs.append(obj)

      # disable callbacks while populating the table
      self._silenceCallback = True
      # self.blockSignals(True)
      if not self._mousePressed:
        selectionModel.clearSelection()       # causes a clear problem here
                                              # strange tablewidget cmd/selection problem
      self.setUpdatesEnabled(False)

      for obj in rowObjs:
        row = self._dataFrameObject.find(self, str(obj.pid))
        selectionModel.select(self.model().index(row, 0)
                                       , selectionModel.Select | selectionModel.Rows)
        # selectionModel.setCurrentIndex(self.model().index(row, 0)
        #                                , selectionModel.SelectCurrent | selectionModel.Rows)

      self.setUpdatesEnabled(True)
      # self.blockSignals(False)
      self._silenceCallback = False
      self.setFocus(QtCore.Qt.OtherFocusReason)

  def clearTable(self):
    "remove all objects from the table"
    self._silenceCallback = True
    self.clearContents()
    self.verticalHeadersSet = True
    self.horizontalHeadersSet = True
    self.items = []
    self.setRowCount(0)
    self.sortModes = {}

    if self._dataFrameObject:
      self.setHorizontalHeaderLabels(self._dataFrameObject.headings)
      self.showColumns(self._dataFrameObject)
      self.resizeColumnsToContents()
      self.horizontalHeader().setStretchLastSection(self._stretchLastSection)

    self._silenceCallback = False

  def _updateTableCallback(self, data):
    """
    Notifier callback for updating the table
    """
    thisTableList = getattr(data[Notifier.THEOBJECT]
                            , self._tableData['className'])   # get the table list
    table = data[Notifier.OBJECT]

    self._silenceCallback = True
    if getattr(self, self._tableData['tableSelection']) in thisTableList:
      trigger = data[Notifier.TRIGGER]

      # keep the original sorting method
      sortOrder = self.horizontalHeader().sortIndicatorOrder()
      sortColumn = self.horizontalHeader().sortIndicatorSection()

      if table.pid == self._tableData['pullDownWidget'].getText() and trigger == Notifier.DELETE:

        self.clearTable()

      elif table.pid == self._tableData['pullDownWidget'].getText() and trigger == Notifier.CHANGE:

        # self.displayTableForNmrTable(table)
        self._tableData['changeFunc'](table)

      elif trigger == Notifier.RENAME:
        if table == getattr(self, self._tableData['tableSelection']):

          # self.displayTableForNmrTable(table)
          self._tableData['changeFunc'](table)

      # re-sort the table
      if sortColumn < self.columnCount():
        self.sortByColumn(sortColumn, sortOrder)

    else:
      self.clearTable()

    self._silenceCallback = False
    getLogger().debug('>updateTableCallback>', data['notifier']
                      , self._tableData['tableSelection']
                      , data['trigger'], data['object'])

  def _updateRowCallback(self, data):
    """
    Notifier callback for updating the table for change in nmrRows
    :param data:
    """
    # thisTableList = getattr(data[Notifier.THEOBJECT]
    #                         , self._tableData['className'])   # get the tableList

    row = data[Notifier.OBJECT]
    trigger = data[Notifier.TRIGGER]

    self._silenceCallback = True
    thisTable = getattr(row, self._tableData['tableName'])

    try:
      # multiple delete from deleteObjFromTable messes with this
      # if thisRow.pid == self._tableData['pullDownWidget'].getText():

      # is the row in the table
      # TODO:ED move these into the table class

      # keep the original sorting method
      sortOrder = self.horizontalHeader().sortIndicatorOrder()
      sortColumn = self.horizontalHeader().sortIndicatorSection()

      if trigger == Notifier.DELETE:

        # remove item from self._dataFrameObject

        self._dataFrameObject.removeObject(row)

      elif trigger == Notifier.CREATE:

        # insert item into self._dataFrameObject

        if self._tableData['tableSelection']:
          tSelect = getattr(self, self._tableData['tableSelection'])
          if tSelect:
            rows = getattr(tSelect, self._tableData['rowClass']._pluralLinkName)

            if rows and len(rows) > 1:
              self._dataFrameObject.appendObject(row)
              self.update()
            else:
              # self._update(self.nmrTable)
              self._tableData['updateFunc'](tSelect)

      elif trigger == Notifier.CHANGE:

        # modify the line in the table
        self._dataFrameObject.changeObject(row)

      elif trigger == Notifier.RENAME:
        # get the old pid before the rename
        oldPid = data[Notifier.OLDPID]

        # modify the oldPid in the objectList, change to newPid
        self._dataFrameObject.renameObject(row, oldPid)

      self.update()
      # re-sort the table
      if sortColumn < self.columnCount():
        self.sortByColumn(sortColumn, sortOrder)

    except Exception as es:
      getLogger().warning(str(es))

    self._silenceCallback = False
    getLogger().debug('>updateRowCallback>', data['notifier']
                      , self._tableData['tableSelection']
                      , data['trigger'], data['object'])

  def _updateCellCallback(self, attr, data):
    """
    Notifier callback for updating the table
    :param data:
    """
    # thisTableList = getattr(data[Notifier.THEOBJECT]
    #                         , self._tableData['className'])   # get the tableList

    cell = data[Notifier.OBJECT]
    # row = getattr(cell, self._tableData['rowName'])
    rows = getattr(cell, attr)

    if not isinstance(rows, (list, tuple)):
      rows = [rows]

    self._silenceCallback = True
    for row in rows:
      if getattr(row, self._tableData['tableName']).pid == self._tableData['pullDownWidget'].getText():

        # keep the original sorting method
        sortOrder = self.horizontalHeader().sortIndicatorOrder()
        sortColumn = self.horizontalHeader().sortIndicatorSection()

        # change the dataFrame for the updated nmrCell
        self._dataFrameObject.changeObject(row)

        # re-sort the table
        if sortColumn < self.columnCount():
          self.sortByColumn(sortColumn, sortOrder)

    self._silenceCallback = False
    getLogger().debug('>updateCellCallback>', data['notifier']
                      , self._tableData['tableSelection']
                      , data['trigger'], data['object'])

  def _selectCurrentCallBack(self, data):
    """
    Callback to handle selection on the table, linked to user defined function
    :param data:
    """
    self._tableData['selectCurrentCallBack'](data)

  def setTableNotifiers(self, tableClass=None, rowClass=None, cellClassNames=None
                         , tableName=None, rowName=None, className=None
                         , changeFunc=None, updateFunc=None
                         , tableSelection=None, pullDownWidget=None
                         , callBackClass=None, selectCurrentCallBack=None):
    """
    Set a Notifier to call when an object is created/deleted/renamed/changed
    rename calls on name
    change calls on any other attribute

    :param tableClass - class of table object, selected by pulldown:
    :param rowClass - class identified by a row in the table:
    :param cellClassNames - list of tuples (cellClass, cellClassName):
                            class that affects row when changed
    :param tableName - name of attribute for parent name of row:
    :param rowName - name of attribute for parent name of cell:
    :param changeFunc:
    :param updateFunc:
    :param tableSelection:
    :param pullDownWidget:
    :return:
    """
    self.clearTableNotifiers()

    if tableClass:
      self._tableNotifier = Notifier(self.project
                                      , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                      , tableClass.__name__
                                      , self._updateTableCallback
                                      , onceOnly=True)
    if rowClass:

      # TODO:ED check OnceOnly residue notifiers
      # 'i-1' residue spawns a rename but the 'i' residue only fires a change
      self._rowNotifier = Notifier(self.project
                                    , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
                                    , rowClass.__name__
                                    , self._updateRowCallback
                                    , onceOnly=False)           # should be True, be doesn't work
                                                                # for 'i-1' nmrResidues
    if isinstance(cellClassNames, list):
      for cellClass in cellClassNames:
        self._cellNotifiers.append(Notifier(self.project
                                            , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                            , cellClass[0].__name__
                                            , partial(self._updateCellCallback, cellClass[1])
                                            , onceOnly=False))
    else:
      if cellClassNames:
        self._cellNotifiers.append(Notifier(self.project
                                            , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                            , cellClassNames[0].__name__
                                            , partial(self._updateCellCallback, cellClassNames[1])
                                            , onceOnly=False))

    if selectCurrentCallBack:
      self._selectCurrentNotifier = Notifier(self.current
                                             , [Notifier.CURRENT]
                                             , callBackClass._pluralLinkName
                                             , self._selectCurrentCallBack)

    self._tableData = {'updateFunc': updateFunc
                        , 'changeFunc': changeFunc
                        , 'tableSelection': tableSelection
                        , 'pullDownWidget': pullDownWidget
                        , 'tableClass': tableClass
                        , 'rowClass': rowClass
                        , 'cellClassNames': cellClassNames
                        , 'tableName': tableName
                        , 'rowName': rowName
                        , 'className': className
                        , 'selectCurrentCallBack': selectCurrentCallBack}

  def clearTableNotifiers(self):
    """
    clean up the notifiers
    """
    if self._tableNotifier is not None:
      self._tableNotifier.unRegister()
    if self._rowNotifier is not None:
      self._rowNotifier.unRegister()
    if self._cellNotifiers:
      for cell in self._cellNotifiers:
        if cell is not None:
          cell.unRegister()
    self._cellNotifiers = []
    if self._selectCurrentNotifier is not None:
      self._selectCurrentNotifier.unRegister()

  # def dragEnterEvent(self, event):
  #   ccpnmrJsonData = 'ccpnmr-json'
  #
  #   if event.mimeData().hasUrls():
  #     event.accept()
  #   else:
  #     pids = []
  #     for item in self.selectedItems():
  #       if item is not None:
  #
  #         # TODO:ED check the list of selected as with getSelectedObjects to get pids..
  #         # trouble is, this is working as a dropevent
  #         objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
  #         if objFromPid is not None:
  #           pids.append(objFromPid.pid)
  #
  #     itemData = json.dumps({'pids':pids})
  #     event.mimeData().setData(ccpnmrJsonData, itemData)
  #     event.mimeData().setText(itemData)
  #     event.accept()


EDIT_ROLE = QtCore.Qt.EditRole

class QuickTableDelegate(QtGui.QStyledItemDelegate):
  """
  handle the setting of data when editing the table
  """
  def __init__(self, parent):
    """
    Initialise the delegate
    :param parent - link to the handling table:
    """
    QtGui.QStyledItemDelegate.__init__(self, parent)
    self.customWidget = False
    self._parent = parent

  def setModelData(self, widget, mode, index):
    """
    Set the object to the new value
    :param widget - typically a lineedit handling the editing of the cell:
    :param mode - editing mode:
    :param index - QModelIndex of the cell:
    """
    text = widget.text()
    row = index.row()
    col = index.column()

    try:
      rowData = []
      # read the row from the table to get the pid
      for ii in range(self._parent.columnCount()):
        rowData.append(self._parent.item(row, ii).text())

      pidCol = self._parent._dataFrameObject.headings.index('Pid')
      thisPid = rowData[pidCol]
      obj = self._parent.project.getByPid(thisPid)

      # set the data which will fire notifiers to populate all tables
      func = self._parent._dataFrameObject.setEditValues[col]
      if func:
        func(obj, text)

    except Exception as es:
      getLogger().warning('Error handling cell editing: %i %i %s' % (row, col, str(es)))

    # return QtGui.QStyledItemDelegate.setModelData(self, widget, mode, index)


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Icon import Icon

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  from ccpn.util import Colour
  from ccpn.ui.gui.widgets.Column import ColumnClass, Column


  app = TestApplication()

  class mockObj(object):
    'Mock object to test the table widget editing properties'
    pid = ''
    integer = 3
    exampleFloat = 3.1 # This will create a double spin box
    exampleBool = True # This will create a check box
    string = 'white' # This will create a line Edit
    exampleList = [('Mock', 'Test'),] # This will create a pulldown
    color = QtGui.QColor('Red')
    icon = Icon('icons/warning')
    r= Colour.colourNameToHexDict['red']
    y = Colour.colourNameToHexDict['yellow']
    b = Colour.colourNameToHexDict['blue']
    colouredIcons = [None, Icon(color=r),Icon(color=y),Icon(color=b)]

    flagsList = [['']*len(colouredIcons),[Icon]*len(colouredIcons),1,colouredIcons ]  # This will create a pulldown. Make a list with the
                                                                                      # same structure of pulldown setData function: (texts=None, objects=None, index=None,
                                                                                      # icons=None, clear=True, headerText=None, headerEnabled=False, headerIcon=None)

    def editBool(self, value):
      mockObj.exampleBool =  value

    def editFloat(self, value):
      mockObj.exampleFloat = value


    def editPulldown(self, value):
      mockObj.exampleList = value



    def editFlags(self, value):
      print(value)


  def _checkBoxCallBack(data):
    print(data['checked'])

  popup = CcpnDialog(windowTitle='Test Table', setLayout=True)

  columns = ColumnClass([
                        (
                        'Float',
                        lambda i: mockObj.exampleFloat,
                        'TipText: Float',
                        lambda mockObj, value: mockObj.editFloat(mockObj, value)
                        ),

                        (
                        'Bool',
                        lambda i: mockObj.exampleBool,
                        'TipText: Bool',
                        lambda mockObj, value: mockObj.editBool(mockObj, value),
                        ),

                        (
                        'Pulldown',
                        lambda i: mockObj.exampleList,
                        'TipText: Pulldown',
                        lambda mockObj, value: mockObj.editPulldown(mockObj, value),
                        ),

                        (
                        'Flags',
                        lambda i: mockObj.flagsList,
                        'TipText: Flags',
                        lambda mockObj, value: mockObj.editFlags(mockObj, value),
                        )
                      ])
  table = QuickTable(parent=popup, dataFrameObject=None, checkBoxCallback=_checkBoxCallBack,  grid=(0, 0))
  df = table.getDataFrameFromList(table, [mockObj]*5,colDefs=columns )

  table.setTableFromDataFrameObject(dataFrameObject=df)
  table.item(0,0).setBackground(QtGui.QColor(100,100,150)) #color the first item
  combo = QtGui.QComboBox()
  table.setCellWidget(0, 0, combo)
  # table.item(0, 0).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
  # table.item(0, 0).setCheckState(QtCore.Qt.Unchecked)
  # table.item(0,0).setFormat(float(table.item(0,0).format))
  # print(table.item(0,0)._format)

  print('AA',table.horizontalHeaderItem(1).text())
  table.horizontalHeaderItem(1).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
  table.horizontalHeaderItem(1).setCheckState(QtCore.Qt.Checked)


  popup.show()
  popup.raise_()
  app.start()
