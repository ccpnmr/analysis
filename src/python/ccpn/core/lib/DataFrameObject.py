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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
import pyqtgraph as pg
from ccpn.ui.gui.widgets.Column import Column
from PyQt4 import QtGui, QtCore
from collections import OrderedDict
from ccpn.util.Logging import getLogger


class DataFrameObject(object):
  # class to handle pandas dataframe and matching object pid list
  def __init__(self, table=None, dataFrame=None, objectList=None, columnDefs=None, hiddenColumns=None):
    self._dataFrame = dataFrame
    # self._objectList = objectList
    self._objects = objectList.copy()
    # self._indexList = indexList
    self._columnDefinitions = columnDefs
    self._hiddenColumns = hiddenColumns
    self._table = table

  @property
  def dataFrame(self):
    return self._dataFrame

  @dataFrame.setter
  def dataFrame(self, dataFrame=None):
    self._dataFrame = dataFrame

  # @property
  # def objectList(self):
  #   return self._objectList
  #
  # @objectList.setter
  # def objectList(self, objectList=None):
  #   self._objectList = objectList

  @property
  def objects(self):
    return self._objects

  # @property
  # def indexList(self):
  #   return self._indexList
  #
  # @indexList.setter
  # def indexList(self, indexList=None):
  #   self._indexList = indexList

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
  def setEditValues(self):
    return self._columnDefinitions.setEditValues

  @property
  def table(self):
    return self._table

  @table.setter
  def table(self, table=None):
    self._table = table

  def removeObject(self, obj):
    # remove an object from the class
    # if obj.pid in self._objectList:
    if self.find(self._table, str(obj.pid), column='Pid') is not None:
      self._table.silenceCallBack = True
      # the object exists
      # index = self._objectList[obj.pid]
      # del self._objectList[obj.pid]   # remove from objectList
      # del self._indexList[str(index)]      # remove from indexList

      # remove from internal list
      self._objects.remove(obj)

      # now remove from dataFrame

      # self._removeDataFrame = self._dataFrame.ix[self._dataFrame['Index'] == index]
      # remove from dataFrame by Pid
      self._dataFrame = self._dataFrame.ix[self._dataFrame['Pid'] != obj.pid]

      # self._dataFrame.drop(df.index[[1, 3]], inplace=True)

      # df.drop(df.index[index], inplace=True)
      # self._dataFrame = self._dataFrame.take(self._dataFrame['Index'].isin([index]))
      # self._dataFrame = self._dataFrame.take(self._dataFrame['Index']-[index])      # good
      # self._dataFrame.drop(self._dataFrame['Index'].isin([index]), inplace=True)

      # indexes_to_keep = set(range(df.shape[0])) - set(index,)
      # df_sliced = df.take(list(indexes_to_keep))

      # remove from table by pid
      row = self.find(self._table, str(obj.pid), column='Pid')
      if row is not None:
        self._table.removeRow(row)

      self._table.silenceCallBack = False

# copy deleteSelectedRows from EnsembleData

  def find(self, table, text, column='Pid'):
    model = table.model()

    # change column to correct index
    columns = list(range(table.columnCount()))
    for c in columns:
      if column == table.horizontalHeaderItem(c).text():
        column = c
        break

    # search for 'text'
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
    # if obj.pid not in self._objectList:
    if self.find(self._table, str(obj.pid), column='Pid') is None:
      self._table.silenceCallBack = True

      # the object doesn't exist in list, so can be added
      listDict = OrderedDict()
      for header in self._columnDefinitions.columns:
        listDict[header.headerText] = header.getValue(obj)

      if self._dataFrame.empty:
        # need to create a new dataFrame, table with index of 0
        # set the table and column headings

        # self._indexList[str(listDict['Pid'])] = obj
        # self._objectList[obj.pid] = listDict['Pid']

        # keep internal list uptodate
        self._objects = [obj]
        self._dataFrame = pd.DataFrame([listDict], columns=self.headings)
        self._table.setData(self._dataFrame.values)
        self._table.setHorizontalHeaderLabels(self.headings)

        # needed after setting the column headings
        self._table.resizeColumnsToContents()
        self._table.showColumns(self)
        self._table.show()

      else:
        # append a new line to the end
        # newIndex = self._dataFrame['Pid'].max()+1
        # newIndex = self._dataFrame[0].max()+1       # next free index
        # newIndex = len(self._dataFrame.index)+1

        # TODO:ED Check 'Index' - not sure if necessary
        if 'Index' in self._dataFrame:
          newIndex = self._dataFrame['Index'].max()+1
          listDict['Index'] = newIndex
        # self._indexList[str(newIndex)] = obj
        # self._objectList[obj.pid] = newIndex

        # update internal list
        self._objects.append(obj)
        appendDataFrame = pd.DataFrame([listDict], columns=self.headings)

        self._dataFrame = self._dataFrame.append(appendDataFrame)
        # self._table.appendData(appendDataFrame.values)
        # self._table.update()
        self._table.appendRow(list(listDict.values()))
        # newIndex =len(df.index)
        # df = df[df.index != x]
        # desired_indices = [i for i in len(df.index) if i not in unwanted_indices]
        # desired_df = df.iloc[desired_indices]
      self._table.silenceCallBack = False

  def renameObject(self, obj, oldPid):
    # if oldPid in self._objectList:
    if self.find(self._table, str(oldPid), column='Pid') is not None:
      self._table.silenceCallBack = True

      # get the existing index and remove the items from the lists
      # index = self._objectList[oldPid]
      # del self._objectList[oldPid]
      # del self._indexList[str(index)]

      # insert the updated object and pid
      # self._indexList[str(index)] = obj
      # self._objectList[obj.pid] = index

      # check whether the pid is used anywhere in the table
      # this could be covered by the following change event
      self._table.hide()
      changeList = self._dataFrame.replace({oldPid:obj.pid}, regex=True)

      # self._dataFrame = changeList
      self._table.setData(changeList.values)
      # update table from diff
      self._table.setHorizontalHeaderLabels(self.headings)

      # needed after setting the column headings
      # self._table.resizeColumnsToContents()
      # self._table.showColumns(self)
      self._table.show()
      self._table.silenceCallBack = False

      # TODO:ED new functionality may be to use the label types in preferences in the tables

  def changeObject(self, obj):
    # if obj.pid in self._objectList:
    if self.find(self._table, str(obj.pid), column='Pid') is not None:
      self._table.silenceCallBack = True
      # update the values as 'Pid' may have changed
      # index = self._objectList[obj.pid]
      # del self._objectList[obj.pid]
      # del self._indexList[str(index)]

      # generate a new row
      listDict = OrderedDict()
      for header in self._columnDefinitions.columns:
        listDict[header.headerText] = header.getValue(obj)

      # update the pointers incase they have changed - set to original index
      # listDict['Pid'] = index
      # self._indexList[str(index)] = obj
      # self._objectList[obj.pid] = index

      # update the dataFrame
      self._dataFrame.loc[self._dataFrame['Pid'] == obj.pid] = list(listDict.values())
      # appendDataFrame = pd.DataFrame([listItem], columns=self.headings)

      # change row in table
      # self._removeDataFrame = self._dataFrame.ix[self._dataFrame['Pid'] == index]
      # self._dataFrame = self._dataFrame.ix[self._dataFrame['Pid'] != index]
      # df.columns.get_loc('Pid')
      row = self.find(self._table, str(obj.pid), column='Pid')
      if row is not None:
        self._table.setRow(row, list(listDict.values()))
      self._table.silenceCallBack = False
