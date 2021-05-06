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
__dateModified__ = "$dateModified: 2021-05-06 14:04:51 +0100 (Thu, May 06, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import Frame
from functools import partial
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.util.Logging import getLogger
import operator as op

VISIBLESEARCH = '<Visible Table>'

GreaterThan = '>'
LessThan = '<'
GreaterThanInclude = '>='
LessThanInclude = '<='
Equal = 'Equal'
Include = 'Include'


SearchConditionsDict = {
                        Equal: op.eq,
                        Include: op.contains,
                        GreaterThan: op.gt,
                        GreaterThanInclude: op.ge,
                        LessThan: op.lt,
                        LessThanInclude: op.le,
                        }

def _compareKeys(a, b, condition):
    """
    :param a: first value
    :param b: second value
    :param condition: Any key of SearchConditionsDict.
    :return:
    """
    if not condition in list(SearchConditionsDict.keys()):
        getLogger().debug('Condition %s  not available  for GuiTable filters.' %condition)
    try:
        if condition == Equal:
            return SearchConditionsDict.get(Equal)(a, b)
        if condition == Include:
            return SearchConditionsDict.get(Include)(a, b)
        else:
            a,b, = float(a), float(b)
            return SearchConditionsDict.get(condition)(a,b)
    except Exception as ex:
        getLogger().debug('Error in comparing values for GuiTable filters.', ex)
    return False




class GuiTableFilter(ScrollArea):
    def __init__(self, table, parent=None, **kwds):
        # super().__init__(parent, setLayout=True, showBorder=False, **kwds)
        super().__init__(parent, scrollBarPolicies=('never', 'never'), **kwds)

        self.table = table
        self._parent = parent

        # self._widgetScrollArea = ScrollArea(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self.setWidgetResizable(True)
        self._widget = Frame(self, setLayout=True, showBorder=False)
        self.getLayout().setHorizontalSpacing(0)
        self.getLayout().setVerticalSpacing(0)
        self.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        labelColumn = Label(self._widget, 'Filter in', grid=(1, 0), gridSpan=(1, 2))
        self.columnOptions = PulldownList(self._widget, grid=(1, 2))

        self.columnOptions.setMinimumWidth(40)

        self.conditionWidget = PulldownList(self._widget, texts=list(SearchConditionsDict.keys()), grid=(0, 0))
        self.edit = LineEdit(self._widget, grid=(0, 1), gridSpan=(1, 5), backgroundText='Filter by Item')
        self.searchLabel = Button(self._widget, grid=(0, 4), icon=Icon('icons/edit-find'),
                                  callback=partial(self.findOnTable, self.table))
        self.searchLabel.setFlat(True)

        self.searchButtons = ButtonList(self._widget, texts=['Reset', 'Close'], tipTexts=['Restore Table', 'Close Filter'],
                                        callbacks=[partial(self.restoreTable, self.table),
                                                   self.hideSearch],
                                        grid=(1, 3), gridSpan=(1, 2))

        Spacer(self._widget, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
               grid=(0, 2), gridSpan=(1, 1))

        self.edit.returnPressed.connect(partial(self.findOnTable, self.table))

        self.searchButtons.getButton('Reset').setEnabled(False)

        # fix the sizes of the widgets
        self.setFixedHeight(self.sizeHint().height() + 10)

        labelColumn.setFixedWidth(labelColumn.sizeHint().width())
        self.searchLabel.setFixedWidth(self.searchLabel.sizeHint().width())
        self.searchButtons.setFixedWidth(self.searchButtons.sizeHint().width())

        self.setColumnOptions()

        self.setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

        # initialise search list
        self._listRows = None

    def setColumnOptions(self):
        # columns = self.table._dataFrameObject.columns
        # texts = [c.heading for c in columns]
        # objectsRange = range(len(columns))

        texts = self.table._dataFrameObject.userHeadings
        objectsRange = range(len(texts))

        self.columnOptions.clear()
        self.columnOptions.addItem(VISIBLESEARCH, object=None)
        for i, text in enumerate(texts):
            self.columnOptions.addItem(text, objectsRange[i])
        self.columnOptions.setIndex(0)

    def updateSearchWidgets(self, table):
        self.table = table
        self.setColumnOptions()
        self.searchButtons.getButton('Reset').setEnabled(False)

    def hideSearch(self):
        self.restoreTable(self.table)
        if self.table.searchWidget is not None:
            self.table.searchWidget.hide()

    def restoreTable(self, table):
        self.table.refreshTable()
        self.edit.clear()
        self.searchButtons.getButton('Reset').setEnabled(False)
        self._listRows = None

    def findOnTable(self, table, matchExactly=False, ignoreNotFound=False):
        if self.edit.text() == '' or None:
            self.restoreTable(table)
            return

        self.table = table
        text = self.edit.text()

        # testing = self.table.itemDelegateForColumn(5)
        #
        # def _test(test, x):
        #
        #     # index.model()->data(index, Qt::EditRole).toDouble
        #
        #     if test in str(x):
        #         print('>>>', test, str(x))
        #
        #     return test in str(x)
        #
        # if matchExactly:
        #     func = lambda x: text == str(x)
        # else:
        #     func = lambda x: text in str(x)
        #
        # columns = self.table._dataFrameObject.headings

        # if self.columnOptions.currentObject() is None:
        #
        #     df = self.table._dataFrameObject.dataFrame
        #     # idx = df[columns[0]].apply(func)
        #
        #     # for col in range(1, len(columns)):
        #     #     idx = idx | df[columns[col]].apply(func)
        #
        #     visHeadings = self.table._dataFrameObject.visibleColumnHeadings
        #     if visHeadings:
        #
        #         # add the first search column
        #         idx = df[visHeadings[0]].apply(func)
        #         # add the rest (if exist)
        #         for colName in visHeadings[1:]:
        #             idx = idx | df[colName].apply(func)
        #
        #         self._searchedDataFrame = df.loc[idx]
        #
        #     else:
        #         # make an empty dataFrame
        #         self._searchedDataFrame = df.loc[None]
        #
        # else:
        #     objCol = columns[self.columnOptions.currentObject()]
        #
        #     df = self.table._dataFrameObject.dataFrame
        #     self._searchedDataFrame = df.loc[df[objCol].apply(func)]

        # check using the actual table - not the underlying dataframe
        df = self.table._dataFrameObject.dataFrame
        rows = OrderedSet()

        searchColumn = self.columnOptions.getText()
        visHeadings = self.table._dataFrameObject.visibleColumnHeadings if (searchColumn == VISIBLESEARCH) else searchColumn

        for row in range(self.table.rowCount()):

            for column in range(self.table.columnCount()):
                if self.table.horizontalHeaderItem(column).text() in visHeadings:
                    item = table.item(row, column)
                    cellText =  item.data(QtCore.Qt.DisplayRole)
                    condition = self.conditionWidget.getText()
                    match = _compareKeys(cellText, text, condition)

                    # if matchExactly:
                    #     match = item and (text == item.data(QtCore.Qt.DisplayRole))
                    # else:
                    #     match = item and (text in item.data(QtCore.Qt.DisplayRole))
                    if match:
                        if self._listRows is not None:
                            rows.add(list(self._listRows)[item.index])
                        else:
                            rows.add(item.index)

        self._searchedDataFrame = df.loc[list(rows)]
        self._listRows = rows

        if not self._searchedDataFrame.empty:

            with self.table._guiTableUpdate(self.table._dataFrameObject):
                # self.table.setData(self._searchedDataFrame.values)
                self.table.setDataFromSearchWidget(self._searchedDataFrame)

            # self.table.refreshHeaders()
            self.searchButtons.getButton('Reset').setEnabled(True)
        else:
            self.searchButtons.getButton('Reset').setEnabled(False)
            self.restoreTable(table)
            if not ignoreNotFound:
                MessageDialog.showWarning('Not found', text)

    def selectSearchOption(self, sourceTable, columnObject, value):
        try:
            self.columnOptions.setCurrentText(columnObject.__name__)
            self.edit.setText(value)
            self.findOnTable(self.table, matchExactly=False, ignoreNotFound=True)
        except Exception as es:
            getLogger().debug('column not found in table')


def attachSearchWidget(parent, table):
    """
    Attach the search widget to the bottom of the table widget
    """
    returnVal = False
    try:
        parentLayout = table.parent().getLayout()

        if isinstance(parentLayout, QtWidgets.QGridLayout):
            idx = parentLayout.indexOf(table)
            location = parentLayout.getItemPosition(idx)
            if location is not None:
                if len(location) > 0:
                    row, column, rowSpan, columnSpan = location
                    table.searchWidget = GuiTableFilter(parent=parent, table=table, vAlign='b')
                    parentLayout.addWidget(table.searchWidget, row + 1, column, 1, columnSpan)
                    table.searchWidget.hide()

                returnVal = True

    except Exception as es:
        getLogger().warning('Error attaching search widget: %s' % str(es))
    finally:
        return returnVal
