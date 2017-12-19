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
from ccpn.core.lib.Notifiers import Notifier
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
               hideIndex=True,
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
    self._silenceCallback = False
    self.doubleClicked.connect(self._doubleClickCallback)

    model = self.selectionModel()
    model.selectionChanged.connect(self._selectionTableCallback)

    self._tableData = {}
    self._tableNotifier = None
    self._rowNotifier = None
    self._cellNotifiers = []
    self._selectCurrentNotifier = None

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

        self._actionCallback(data)

  def _selectionTableCallback(self, itemSelection):
    # TODO:ED generate a callback dict for the selected item
    # data = OrderedDict()
    # data['OBJECT'] = return pid, key/values, row, col

    if not self._silenceCallback:
      objList = self.getSelectedObjects()
      # model = self.selectionModel()
      #
      # # selects all the items in the row
      # selection = model.selectedIndexes()
      #
      # if selection:
      #   # row = itemSelection.row()
      #   # col = itemSelection.column()
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

            # self.blockSignals(True)
            self._silenceCallback = True

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
    self._silenceCallback = True
    self.setData(dataFrameObject.dataFrame.values)
    self.setHorizontalHeaderLabels(dataFrameObject.headings)

    # needed after setting the column headings
    self.resizeColumnsToContents()
    self.showColumns(dataFrameObject)
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
                           , objectList=objects
                           # , indexList=indexList
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

  def _highLightObjs(self, selection):

    selectionModel = self.selectionModel()

    if selection:
      uniqObjs = set(selection)

      # disable callbacks while populating the table
      self._silenceCallback = True
      selectionModel.clearSelection()
      self.setUpdatesEnabled(False)

      for obj in uniqObjs:
        if obj in self._dataFrameObject.objects:
          # index = self._dataFrameObject.objectList[obj]

          row = self._dataFrameObject.find(self, str(obj.pid))
          selectionModel.select(self.model().index(row, 0)
                                         , selectionModel.Select | selectionModel.Rows)
          # selectionModel.setCurrentIndex(self.model().index(row, 0)
          #                                , selectionModel.SelectCurrent | selectionModel.Rows)

      self._silenceCallback = False
      self.setUpdatesEnabled(True)
      self.setFocus(QtCore.Qt.OtherFocusReason)

  def clearTable(self):
    "remove all objects from the table"
    self._silenceCallback = True
    self.clear()
    self._silenceCallback = False

  def _updateTableCallback(self, data):
    """
    Notifier callback for updating the table
    :param data:
    """
    thisTableList = getattr(data[Notifier.THEOBJECT]
                            , self._tableData['className'])   # get the chainList
    table = data[Notifier.OBJECT]

    self._silenceCallback = True
    if getattr(self, self._tableData['tableSelection']) in thisTableList:
      trigger = data[Notifier.TRIGGER]

      if table.pid == self._tableData['pullDownWidget'].getText() and trigger == Notifier.DELETE:

        self.clear()

      elif table.pid == self._tableData['pullDownWidget'].getText() and trigger == Notifier.CHANGE:

        # self.displayTableForNmrTable(table)
        self._tableData['changeFunc'](table)

      elif trigger == Notifier.RENAME:
        if table == getattr(self, self._tableData['tableSelection']):

          # self.displayTableForNmrTable(table)
          self._tableData['changeFunc'](table)

    else:
      self.clear()

    self._silenceCallback = False
    getLogger().debug('>updateTableCallback>', data['notifier']
                      , self._tableData['tableSelection']
                      , data['trigger'], data['object'])

  def _updateRowCallback(self, data):
    """
    Notifier callback for updating the table for change in nmrRows
    :param data:
    """
    thisTableList = getattr(data[Notifier.THEOBJECT]
                            , self._tableData['className'])   # get the tableList
    row = data[Notifier.OBJECT]
    trigger = data[Notifier.TRIGGER]

    self._silenceCallback = True
    thisRow = getattr(row, self._tableData['tableName'])

    try:
      # multiple delete from deleteObjFromTable messes with this
      # if thisRow.pid == self._tableData['pullDownWidget'].getText():

      # is the row in the table
      # TODO:ED move these into the table class

      if trigger == Notifier.DELETE:

          # remove item from self._dataFrameObject

        self._dataFrameObject.removeObject(row)

      elif trigger == Notifier.CREATE:

        # insert item into self._dataFrameObject

        tSelect = getattr(self, self._tableData['tableSelection'])
        rows = getattr(tSelect, self._tableData['rowClass']._pluralLinkName)

        if rows and len(rows) > 1:
          self._dataFrameObject.appendObject(row)
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

    except Exception as es:
      pass

    self._silenceCallback = False
    getLogger().debug('>updateRowCallback>', data['notifier']
                      , self._tableData['tableSelection']
                      , data['trigger'], data['object'])

  def _updateCellCallback(self, data):
    """
    Notifier callback for updating the table
    :param data:
    """
    thisTableList = getattr(data[Notifier.THEOBJECT]
                            , self._tableData['className'])   # get the tableList
    cell = data[Notifier.OBJECT]
    row = getattr(cell, self._tableData['rowName'])

    self._silenceCallback = True
    if getattr(row, self._tableData['tableName']).pid == self._tableData['pullDownWidget'].getText():

      # change the dataFrame for the updated nmrCell
      self._dataFrameObject.changeObject(row)

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
                         , selectCurrentCallBack=None):
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
    self._tableNotifier = Notifier(self._project
                                    , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                    , tableClass.__name__
                                    , self._updateTableCallback)
    self._rowNotifier = Notifier(self._project
                                  , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
                                  , rowClass.__name__
                                  , self._updateRowCallback
                                  , onceOnly=True)
    if isinstance(cellClassNames, list):
      for cellClass in cellClassNames:
        self._cellNotifiers.append(Notifier(self._project
                                            , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                            , cellClass[0].__name__
                                            , self._updateCellCallback
                                            , onceOnly=True))
    else:
      if cellClassNames:
        self._cellNotifiers.append(Notifier(self._project
                                            , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                            , cellClassNames[0].__name__
                                            , self._updateCellCallback
                                            , onceOnly=True))

      self._selectCurrentNotifier = Notifier(self._current
                                             , [Notifier.CURRENT]
                                             , rowClass._pluralLinkName
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
      for cell in self.cellNotifiers:
        if cell is not None:
          cell.unRegister()
    self._cellNotifiers = []
    if self._selectCurrentNotifier is not None:
      self._selectCurrentNotifier.unRegister()
