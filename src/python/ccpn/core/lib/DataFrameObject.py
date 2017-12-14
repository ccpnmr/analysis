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

from ccpn.ui.gui.widgets.Column import Column
from PyQt4 import QtGui, QtCore
from collections import OrderedDict
import pandas as pd


class DataFrameObject(object):
  # class to handle pandas dataframe and matching object pid list
  def __init__(self, table=None, dataFrame=None, objectList=None, indexList=None, columnDefs=None, hiddenColumns=None):
    self._dataFrame = dataFrame
    self._objectList = objectList
    self._indexList = indexList
    self._columnDefinitions = columnDefs
    self._hiddenColumns = hiddenColumns
    self._table = table

  @property
  def dataFrame(self):
    return self._dataFrame

  @dataFrame.setter
  def dataFrame(self, dataFrame=None):
    self._dataFrame = dataFrame

  @property
  def objectList(self):
    return self._objectList

  @objectList.setter
  def objectList(self, objectList=None):
    self._objectList = objectList

  @property
  def indexList(self):
    return self._indexList

  @indexList.setter
  def indexList(self, indexList=None):
    self._indexList = indexList

  @property
  def hiddenColumns(self):
    return self._hiddenColumns

  @hiddenColumns.setter
  def hiddenColumns(self, hiddenColumns=None):
    self._hiddenColumns = hiddenColumns

  @property
  def columnDefinitions(self):
    return self._columnDefinitions

  @columnDefinitions.setter
  def columnDefinitions(self, columnDefinitions=None):
    self._columnDefinitions = columnDefinitions

  @property
  def columns(self):
    return self._columnDefinitions.columns

  @property
  def headings(self):
    return self._columnDefinitions.headings

  @property
  def table(self):
    return self._table

  @table.setter
  def table(self, table=None):
    self._table = table

  def removeObject(self, obj):
    # remove an object from the class

    if obj.pid in self._objectList:

      # the object exists
      index = self._objectList[obj.pid]

      del self._objectList[obj.pid]   # remove from objectList
      del self._indexList[str(index)]      # remove from indexList

      # now remove from dataFrame
      self._dataFrame = self._dataFrame.ix[self._dataFrame['Index'] != index]
      row = self.find(self._table, str(index))
      self._table.removeRow(row)

  def find(self, table, text, column=1):
    model = table.model()
    start = model.index(0, column)
    matches = model.match(
      start, QtCore.Qt.DisplayRole,
      text, 1, QtCore.Qt.MatchContains)
    if matches:
      return matches[0].row()
      # # index.row(), index.column()
      # self.table.selectionModel().select(
      #   index, QtGui.QItemSelectionModel.Select)

    return None

  def appendObject(self, obj):
    if obj.pid not in self._objectList:

      # the object doesn't exist in list, so can be added
      listItem = OrderedDict()
      for header in self._columnDefinitions.columns:
        listItem[header.headerText] = header.getValue(obj)

      # need to
      if not self._dataFrame.empty:
        newIndex = len(self._dataFrame.index)

        listItem['Index'] = newIndex
        self._indexList[str(newIndex)] = obj
        self._objectList[obj.pid] = newIndex

        appendDataFrame = pd.DataFrame([listItem], columns=self.headings)

        self._dataFrame.append(appendDataFrame)
        self._table.appendData(appendDataFrame.values)
      else:
        # set the table and column headings
        self._indexList[str(listItem['Index'])] = obj
        self._objectList[obj.pid] = listItem['Index']

        appendDataFrame = pd.DataFrame([listItem], columns=self.headings)

        self._dataFrame = appendDataFrame
        self._table.setData(self._dataFrame.values)
        self._table.setHorizontalHeaderLabels(self.headings)

        # needed after setting the column headings
        self._table.resizeColumnsToContents()
        self._table.showColumns(self._dataFrame)
        self._table.show()

