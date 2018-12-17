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
__version__ = "$Revision: 3.0.b4 $"
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
from PyQt5 import QtCore, QtWidgets
from collections import OrderedDict
from ccpn.util.Logging import getLogger


DATAFRAME_OBJECT = '_object'
DATAFRAME_PID = 'Pid'
DATAFRAME_HASH = '#'
DATAFRAME_INDEX = 'Index'


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
    def numColumns(self):
        return self._columnDefinitions.numColumns

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
    def visibleColumnHeadings(self):
        return [col for col in self._columnDefinitions.headings if col not in self._hiddenColumns and col != DATAFRAME_OBJECT]

    @property
    def userHeadings(self):
        return [col for col in self._columnDefinitions.headings if col != DATAFRAME_OBJECT]

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

    def find(self, table, text, column='Pid'):
        model = table.model()

        # change column to correct index
        columns = list(range(table.columnCount()))
        columnNum = None
        for c in columns:
            if column == table.horizontalHeaderItem(c).text():
                columnNum = c
                break

        # search for 'text'
        if columnNum is not None:
            start = model.index(0, columnNum)
            matches = model.match(
                    start, QtCore.Qt.DisplayRole,
                    text, 1, QtCore.Qt.MatchExactly)

            # start = model.index(0, columnNum)
            # matches2 = model.match(
            #   start, QtCore.Qt.UserRole,
            #   text, 1, QtCore.Qt.MatchExactly)
            #
            # print ([table.item(rr, columnNum).value for rr in range(table.rowCount())])

            if matches:
                return matches[0].row()
                # # index.row(), index.column()
                # self.table.selectionModel().select(
                #   index, QtGui.QItemSelectionModel.Select)

        return None

    def findObject(self, table, obj, column='_object'):
        # model = table.model()

        # change column to correct index
        columns = list(range(table.columnCount()))
        columnNum = None
        for c in columns:
            if column == table.horizontalHeaderItem(c).text():
                columnNum = c
                break
        else:
            return None

        foundObjs = [table.item(rr, columnNum).value for rr in range(table.rowCount())]
        if obj in foundObjs:
            return foundObjs.index(obj)

    def removeObject(self, obj):
        # remove an object from the class
        row = self.find(self._table, str(obj.pid), column='Pid')
        if row is not None:
            self._table.silenceCallBack = True

            try:
                # remove from internal list
                self._objects.remove(obj)

                # remove from dataFrame by obj
                self._dataFrame = self._dataFrame.ix[self._dataFrame[DATAFRAME_OBJECT] != obj]

                # remove from table by pid
                row = self.find(self._table, str(obj.pid), column='Pid')
                if row is not None:
                    self._table.removeRow(row)

            except Exception as es:
                getLogger().warning(str(es))
            finally:
                self._table.silenceCallBack = False

    def appendObject(self, obj, multipleAttr=None):
        row = self.find(self._table, str(obj.pid), column='Pid')

        # check that the object doesn't already exists in the table
        if row is None:
            self._table.silenceCallBack = True

            try:
                # the object doesn't exist in list, so can be added
                listDict = OrderedDict()
                for header in self._columnDefinitions.columns:
                    listDict[header.headerText] = header.getValue(obj)

                if self._dataFrame.empty:
                    # need to create a new dataFrame, table with index of 0
                    # set the table and column headings

                    # set the initial objects; dataFrame needed to populate the first table
                    self._objects = [obj]
                    self._dataFrame = pd.DataFrame([listDict], columns=self.headings)

                    with self._table._quickTableUpdate(self):
                        self._table.setData(self._dataFrame.values)

                else:
                    # append a new line to the end

                    # set Index to next available - will change later
                    if not self._dataFrame.empty and 'Index' in self._dataFrame:
                        newIndex = self._dataFrame['Index'].max() + 1
                        if 'Index' in listDict.keys():
                            listDict['Index'] = newIndex

                    # update internal list
                    self._objects.append(obj)
                    appendDataFrame = pd.DataFrame([listDict], columns=self.headings)
                    self._dataFrame = self._dataFrame.append(appendDataFrame)

                    with self._table._quickTableUpdate(self):  # keep the column widths
                        self._table.appendRow(list(listDict.values()))

                    # # get indexing from pulldown selection and set in dataFrame/table
                    # # change to a finishing routine called updateTableIndexing when
                    # if multipleAttr:
                    #   newIndex = [multipleAttr.index(rr) for rr in self._objects]
                    #
                    #   objCol = indCol = None
                    #   for cc in range(self._table.columnCount()):
                    #     colName = self._table.horizontalHeaderItem(cc).text()
                    #     if colName == DATAFRAME_INDEX:
                    #       indCol = cc
                    #       print (DATAFRAME_INDEX, cc)
                    #     elif colName == DATAFRAME_OBJECT:
                    #       objCol = cc
                    #       print (DATAFRAME_OBJECT, cc)
                    #   if objCol and indCol:
                    #     print ('INDEXING')
                    #     print (multipleAttr)
                    #     for rr in range(self._table.rowCount()):
                    #
                    #       thisObj = self._table.item(rr, objCol).value
                    #       if thisObj in multipleAttr:
                    #         self._table.item(rr, indCol).setValue(multipleAttr.index(thisObj))

            except Exception as es:
                getLogger().warning(str(es))
            finally:
                self._table.silenceCallBack = False
                return True

    def renameObject(self, obj, oldPid):
        row = self.find(self._table, str(oldPid), column='Pid')
        # row = self.find(self._table, obj, column='_object')
        if row is not None:
            self._table.silenceCallBack = True

            try:
                # generate a new row
                listDict = OrderedDict()
                for header in self._columnDefinitions.columns:
                    listDict[header.headerText] = header.getValue(obj)

                self._dataFrame_foundPid = self._dataFrame.ix[self._dataFrame[DATAFRAME_OBJECT] == obj]
                self._dataFrame = self._dataFrame.ix[self._dataFrame[DATAFRAME_OBJECT] != obj]

                # keep the Index if it exists
                if not self._dataFrame_foundPid.empty and 'Index' in self._dataFrame_foundPid:
                    newIndex = self._dataFrame_foundPid['Index'].iloc[0]
                    if 'Index' in listDict.keys():
                        listDict['Index'] = newIndex

                # store to the table
                self._table.setRow(row, list(listDict.values()))

                # store the actual object in the dataFrame
                # if 'Pid' in listDict.keys():
                #   listDict['Pid'] = obj
                appendDataFrame = pd.DataFrame([listDict], columns=self.headings)
                self._dataFrame = self._dataFrame.append(appendDataFrame)

            except Exception as es:
                getLogger().warning(str(es))
            finally:
                self._table.silenceCallBack = False
                return True

    def objAttr(self, headerText, obj):
        for header in self._columnDefinitions.columns:
            if header.headerText == headerText:
                return header.getValue(obj)

    def setObjAttr(self, headerText, obj, value):
        for header in self._columnDefinitions.columns:
            if header.headerText == headerText:
                header.setEditValue(obj, value)

    def changeObject(self, obj):
        # row = self.find(self._table, str(obj.pid), column='Pid')
        row = self.findObject(self._table, obj, column='_object')
        _update = False
        if row is not None:
            self._table.silenceCallBack = True

            # try:

            # generate a new row
            listDict = OrderedDict()
            for header in self._columnDefinitions.columns:
                listDict[header.headerText] = header.getValue(obj)

            self._dataFrame_foundPid = self._dataFrame.ix[self._dataFrame[DATAFRAME_OBJECT] == obj]
            self._dataFrame = self._dataFrame.ix[self._dataFrame[DATAFRAME_OBJECT] != obj]

            # keep the Index if it exists
            if not self._dataFrame_foundPid.empty and 'Index' in self._dataFrame_foundPid:
                newIndex = self._dataFrame_foundPid['Index'].iloc[0]
                if 'Index' in listDict.keys():
                    listDict['Index'] = newIndex

            # store to the table
            with self._table._quickTableUpdate(self):
                self._table.setRow(row, list(listDict.values()))

            # store the actual object in the dataFrame
            # if 'Pid' in listDict.keys():
            #   listDict['Pid'] = obj
            appendDataFrame = pd.DataFrame([listDict], columns=self.headings)
            self._dataFrame = self._dataFrame.append(appendDataFrame)

            # except Exception as es:
            #   getLogger().warning(str(es))
            # finally:
            self._table.silenceCallBack = False
            return True

    def objectExists(self, obj):
        return self.find(self._table, str(obj.pid), column='Pid') is not None

    def emptyRow(self):
        """
        Create a blank row for populating undefined tables
        :return dict - based on headings:
        """
        headerDict = {}
        for h, header in enumerate(self._columnDefinitions.headings):
            headerDict[header] = h

        return headerDict
