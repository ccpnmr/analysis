"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2018-12-20 15:53:22 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.util.Logging import getLogger
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT


class ColumnViewSettingsPopup(CcpnDialog):
    # def __init__(self, table=None, parent=None, hideColumns=None, title='Column Settings', **kwds):
    def __init__(self, dataFrameObject=None, parent=None, hideColumns=None, title='Column Settings', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)
        self.setContentsMargins(5, 5, 5, 5)
        self.dataFrameObject = dataFrameObject
        # self.widgetColumnViewSettings = ColumnViewSettings(parent=self, table=table, hideColumns=hideColumns, grid=(0,0))
        self.widgetColumnViewSettings = ColumnViewSettings(parent=self, dataFrameObject=dataFrameObject, grid=(0, 0))
        buttons = ButtonList(self, texts=['Close'], callbacks=[self._close], grid=(1, 0), hAlign='c')
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def _close(self):
        'Save the hidden columns to the table class. So it remembers when you open again the popup'
        hiddenColumns = self.widgetColumnViewSettings._getHiddenColumns()
        self.dataFrameObject.hiddenColumns = hiddenColumns
        self.reject()
        return hiddenColumns


SEARCH_MODES = ['Literal', 'Case Sensitive Literal', 'Regular Expression']
CheckboxTipText = 'Select column to be visible on the table.'


class ColumnViewSettings(Widget):
    ''' hide show check boxes corresponding to the table columns '''

    def __init__(self, parent=None, dataFrameObject=None, direction='v', hideColumns=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)
        self.direction = direction
        # self.table = table
        self.dataFrameObject = dataFrameObject
        self.checkBoxes = []
        # self.hiddenColumns = []
        # self.hideColumns = hideColumns or []      # list of column names
        self._hideColumnWidths = {}
        self.initCheckBoxes()
        self.filterLabel = Label(self, 'Display Columns', grid=(0, 1), vAlign='t', hAlign='l')

    def initCheckBoxes(self):
        columns = self.dataFrameObject.headings  #   self.table._columns
        hiddenColumns = self.dataFrameObject.hiddenColumns or []

        if columns:
            for i, colum in enumerate(columns):

                # always ignore the special column
                if colum != DATAFRAME_OBJECT:
                    if self.direction == 'v':
                        i += 1
                        cb = CheckBox(self, text=colum, grid=(i, 1), callback=self.checkBoxCallBack,
                                      checked=True if colum not in hiddenColumns else False,
                                      hAlign='l', tipText=CheckboxTipText, )
                    else:
                        cb = CheckBox(self, text=colum, grid=(1, i), callback=self.checkBoxCallBack,
                                      checked=True if colum not in hiddenColumns else False,
                                      hAlign='l', tipText=CheckboxTipText, )

                    cb.setMinimumSize(cb.sizeHint() * 1.3)

                    self.checkBoxes.append(cb)
                    # if colum not in self.hideColumns:
                    #   self._showColumn(i, colum)
                    # else:
                    #   self._hideColumn(i, colum)

    def _getHiddenColumns(self):
        return self.dataFrameObject.hiddenColumns

    def checkBoxCallBack(self):
        currentCheckBox = self.sender()
        name = currentCheckBox.text()
        # i = self.table._columns.index(name)
        i = self.dataFrameObject.headings.index(name)

        checkedBoxes = []

        for checkBox in self.checkBoxes:
            checkBox.setEnabled(True)
            if checkBox.isChecked():
                checkedBoxes.append(checkBox)
        if len(checkedBoxes) > 0:
            if currentCheckBox.isChecked():
                self._showColumn(i, name)
            else:
                self._hideColumn(i, name)
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

    def _hideColumn(self, i, name):
        self.dataFrameObject.table.hideColumn(i)  #self.table.getColumnInt(columnName=name))
        # self._hideColumnWidths[name] = self.table.columnWidth(self.table.getColumnInt(columnName=name))
        if name not in self.dataFrameObject.hiddenColumns:
            self.dataFrameObject.hiddenColumns.append(name)
        # self.hiddenColumns.append(name)

    def _showColumn(self, i, name):
        self.dataFrameObject.table.showColumn(i)  #self.table.getColumnInt(columnName=name))
        # if name in self._hideColumnWidths:
        #   self.table.setColumnWidth(self.table.getColumnInt(columnName=name), self._hideColumnWidths[name])
        self.dataFrameObject.table.resizeColumnToContents(i)
        if name in self.dataFrameObject.hiddenColumns:
            self.dataFrameObject.hiddenColumns.remove(name)

    def showColumns(self):
        # hide the columns in the list
        columns = self.dataFrameObject.headings

        for i, colName in enumerate(columns):
            if colName in self.dataFrameObject.hiddenColumns:
                self._hideColumn(i, colName)
            else:
                self._showColumn(i, colName)
