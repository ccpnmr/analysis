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

import re

from PyQt4 import QtGui, QtCore
import pandas as pd
from pyqtgraph import TableWidget
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
from functools import partial
from collections import OrderedDict

from collections import OrderedDict
from ccpn.util.Logging import getLogger

# BG_COLOR = QtGui.QColor('#E0E0E0')
# TODO:ED add some documentation here


class QuickTable(TableWidget, Base):

  def __init__(self, parent=None,
               mainWindow=None,
               dataFrameObject=None,      # collate into a single object that can be changed quickly
               actionCallback=None, selectionCallback=None,
               multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
               enableExport=True, enableDelete=True,
               hideIndex=False,
               **kw):
    """
    Create a new instance of a TableWidget with an attached Pandas dataFrame

    :param parent - parent container:
    :param dataFrame - attached dataFrame:
    :param columns:
    :param objects:
    :param actionCallback:
    :param selectionCallback:
    :param multiSelect:
    :param selectRows:
    :param numberRows:
    :param autoResize:
    :param enableExport:
    :param enableDelete:
    :param kw:
    """
    TableWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self._parent = parent

    # set the application specfic links
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    # initialise the internal data storage
    self._dataFrameObject = dataFrameObject
    # self._dataFrame = dataFrame
    # self._columns = columns
    # self._objects = list(objects or [])

    # set the prefered scrolling behaviour
    self.setHorizontalScrollMode(self.ScrollPerItem)
    self.setVerticalScrollMode(self.ScrollPerItem)
    # self._hiddenColumns = hiddenColumns

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

    # set all the elements to the same size
    self.hideIndex = hideIndex
    self._setDefaultRowHeight()

    # enable sorting and sort on the first column
    self.setSortingEnabled(True)
    self.sortByColumn(0, QtCore.Qt.AscendingOrder)

    # enable drag and drop operations on the table
    self.setDragEnabled(True)
    self.acceptDrops()
    self.setDragDropMode(self.InternalMove)
    self.setDropIndicatorShown(True)

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
    self.doubleClicked.connect(self._doubleClickCallback)

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

      data = {}
      for iSelect in selection:
        col = iSelect.column()
        colName = self.horizontalHeaderItem(col).text()
        data[colName] = model.model().data(iSelect)

      objIndex = data['Index']
      obj = self._dataFrameObject.indexList[objIndex]    # item.index needed

      data = CallBack(theObject = self._dataFrameObject
                      , object = obj
                      , index = objIndex
                      , targetName = obj.className
                      , trigger = CallBack.DOUBLECLICK
                      , row = row
                      , col = col
                      , rowItem = data)

      self._actionCallback(data)

  def showColumns(self, dataFrameObject):
    # show the columns in the list
    for i, colName in enumerate(dataFrameObject.headings):
      if colName in dataFrameObject.hiddenColumns:
        self.hideColumn(i)
      else:
        self.showColumn(i)

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
    else:
      super(QuickTable, self).mousePressEvent(event)

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
    # if self.searchWidget is None:
      # self._addSearchWidget()

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

            self.blockSignals(True)

            for obj in selected:
              if hasattr(obj, 'pid'):

                # print ('>>> deleting', obj)
                obj.delete()

          except Exception as es:
            getLogger().warning(str(es))
          finally:

            self.blockSignals(False)

            thisProject._endCommandEchoBlock()
        else:

          # TODO:ED this is deleting from PandasTable, check for another way to get project
          for obj in selected:
            if hasattr(obj, 'pid'):
              obj.delete()

  def _addSearchWidget(self):
    # TODO:Luca Add search option for any table
    if self._parent is not None:
      parentLayout = None
      if isinstance(self._parent, Base):
      # if hasattr(self._parent, 'getLayout'):
        parentLayout = self._parent.getLayout()

      if isinstance(parentLayout, QtGui.QGridLayout):
        idx = parentLayout.indexOf(self)
        location = parentLayout.getItemPosition(idx)
        if location is not None:
          if len(location)>0:
            row, column, rowSpan, columnSpan = location
            self.searchWidget = ObjectTableFilter(table=self, grid=(0,0), vAlign='B')
            parentLayout.addWidget(self.searchWidget, row+2, column, rowSpan+2, columnSpan)
            self.searchWidget.hide()
    return True

  def setTableFromDataFrameObject(self, dataFrameObject):
    # populate the table from the the Pandas dataFrame
    self._dataFrameObject = dataFrameObject

    self.hide()

    # TODO:ED this shouldn't need to be here
    # check for the existence of 'Index' and 'comment' in the values
    # numRows = len(dataFrame.index)
    # if 'Index' not in dataFrame:
    #   dataFrame['Index'] = [x for x in range(1, numRows+1)]
    # if 'comment' not in dataFrame:
    #   dataFrame['comment'] = [''] * numRows
    #
    # # and reorder the 'Index' to the front
    # cols = dataFrame.columns.tolist()
    # cols.insert(0, cols.pop(cols.index('Index')))
    # dataFrame = dataFrame.reindex(columns=cols)

    # set the table and column headings
    self.setData(dataFrameObject.dataFrame.values)
    self.setHorizontalHeaderLabels(dataFrameObject.headings)

    # needed after setting the column headings
    self.resizeColumnsToContents()
    self.showColumns(dataFrameObject)
    self.show()

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
    objectList = {}
    indexList = {}

    for col, obj in enumerate(buildList):
      listItem = OrderedDict()
      for header in colDefs.columns:
        listItem[header.headerText] = header.getValue(obj)

      allItems.append(listItem)
      # indexList[str(listItem['Index'])] = obj
      # objectList[obj.pid] = listItem['Index']
      indexList[str(col)] = obj
      objectList[obj.pid] = col

    return DataFrameObject(dataFrame=pd.DataFrame(allItems, columns=colDefs.headings)
                           , objectList=objectList
                           , indexList=indexList
                           , columnDefs=colDefs
                           , hiddenColumns=hiddenColumns
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
    objectList = {}
    indexList = {}

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
                           , objectList=objectList
                           , indexList=indexList
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
        if colName == 'Index':

          if row not in rows:
            rows.append(row)
            objIndex = model.model().data(iSelect)
            obj = self._dataFrameObject.indexList[objIndex]  # item.index needed
            selectedObjects.append(obj)

      return selectedObjects
    else:
      return None

