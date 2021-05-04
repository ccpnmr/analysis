"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-05-04 17:48:25 +0100 (Tue, May 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT


class ColumnViewSettingsPopup(CcpnDialogMainWidget):

    FIXEDHEIGHT = False
    FIXEDWIDTH = True
    USESCROLLWIDGET = True

    def __init__(self, dataFrameObject=None, parent=None, hideColumns=None, title='Column Settings', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, minimumSize=(250, 250), **kwds)

        self.dataFrameObject = dataFrameObject
        self.widgetColumnViewSettings = ColumnViewSettings(self.mainWidget, dataFrameObject=dataFrameObject, grid=(0, 0))

        self.setCloseButton(callback=self._close, tipText='Close')
        self.setDefaultButton(self.CLOSEBUTTON)
        self.__postInit__()

    def _close(self):
        """Save the hidden columns to the table class. So it remembers when you open again the popup
        """
        hiddenColumns = self.widgetColumnViewSettings._getHiddenColumns()
        self.dataFrameObject.hiddenColumns = hiddenColumns
        self.reject()
        return hiddenColumns


SEARCH_MODES = ['Literal', 'Case Sensitive Literal', 'Regular Expression']
CheckboxTipText = 'Select column to be visible on the table.'


class ColumnViewSettings(Frame):
    """ hide show check boxes corresponding to the table columns """

    def __init__(self, parent=None, dataFrameObject=None, direction='v', hideColumns=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        self.direction = direction
        self.dataFrameObject = dataFrameObject
        self.checkBoxes = []
        self._hideColumnWidths = {}
        self.filterLabel = Label(self, text='Display Columns', grid=(0, 0))
        self.widgetFrame = Frame(self, setLayout=True, margins=(5,5,5,5), grid=(1, 0))
        Spacer(self, 5, 5, 'fixed', 'expanding', grid=(2, 0))

        self.initCheckBoxes()

    def initCheckBoxes(self):

        columns = self.dataFrameObject.headings  #   self.table._columns
        hiddenColumns = self.dataFrameObject.hiddenColumns or []

        if columns:
            for i, colum in enumerate(columns):

                # always ignore the special column
                if colum != DATAFRAME_OBJECT:
                    if self.direction == 'v':
                        i += 1
                        cb = CheckBox(self.widgetFrame, text=colum, grid=(i, 1), callback=self.checkBoxCallBack,
                                      checked=True if colum not in hiddenColumns else False,
                                      hAlign='l', tipText=CheckboxTipText, )
                    else:
                        cb = CheckBox(self.widgetFrame, text=colum, grid=(1, i), callback=self.checkBoxCallBack,
                                      checked=True if colum not in hiddenColumns else False,
                                      hAlign='l', tipText=CheckboxTipText, )

                    self.checkBoxes.append(cb)

    def _getHiddenColumns(self):
        return self.dataFrameObject.hiddenColumns

    def checkBoxCallBack(self):
        currentCheckBox = self.sender()
        name = currentCheckBox.text()
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
        else:
            # always display at least one columns, disables the last checkbox
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
        self.dataFrameObject.table.hideColumn(i)
        if name not in self.dataFrameObject.hiddenColumns:
            self.dataFrameObject.hiddenColumns.append(name)

    def _showColumn(self, i, name):
        self.dataFrameObject.table.showColumn(i)
        self.dataFrameObject.table.resizeColumnToContents(i)
        if name in self.dataFrameObject.hiddenColumns:
            self.dataFrameObject.hiddenColumns.remove(name)

    def showColumns(self):
        # show/hide the columns in the list
        columns = self.dataFrameObject.headings

        for i, colName in enumerate(columns):
            if colName in self.dataFrameObject.hiddenColumns:
                self._hideColumn(i, colName)
            else:
                self._showColumn(i, colName)
