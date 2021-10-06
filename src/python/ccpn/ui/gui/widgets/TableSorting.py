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
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-04-30 10:19:39 +0100 (Fri, April 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore
from pyqtgraph.widgets.TableWidget import TableWidgetItem
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.util.Logging import getLogger


class CcpnTableWidgetItem(TableWidgetItem):
    """
    Class implementing new sorting applied to TableWidgetItem using universalSortKey
    """

    def __lt__(self, other):
        # new routine to overload TableWidgetItem that crashes when sorting None
        if self.sortMode == 'index' and hasattr(other, 'index'):
            return self.index < other.index
        if self.sortMode == 'value' and hasattr(other, 'value'):
            return (universalSortKey(self.value) < universalSortKey(other.value))
        else:
            if self.text() and other.text():
                return (universalSortKey(self.text()) < universalSortKey(other.text()))
            else:
                return False

    def setDraggable(self, draggable):
        """
        Set whether this item is user-draggable.
        """
        if draggable:
            self.setFlags(self.flags() |
                          QtCore.Qt.ItemIsDragEnabled |
                          QtCore.Qt.ItemIsDropEnabled
                          )
        else:
            self.setFlags(self.flags() &
                          ~QtCore.Qt.ItemIsDragEnabled &
                          ~QtCore.Qt.ItemIsDropEnabled)

    def setEditable(self, editable):
        """
        Set whether this item is user-editable.
        """
        if editable:
            self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        else:
            self.setFlags(self.flags() & ~QtCore.Qt.ItemIsEditable)

    def setEnabled(self, enabled):
        """
        Set whether this item is enabled and selectable
        """
        if enabled:
            self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        else:
            self.removeFlags()
            self.setFlags(~QtCore.Qt.ItemIsEnabled)

    def setCheckable(self, checkable):
        """
        Set whether this item is checkable
        """
        if checkable:
            self.setEnabled(True)
            self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        else:
            self.setFlags(self.flags() & ~QtCore.Qt.ItemIsUserCheckable)

    def removeFlags(self):
        """
        Remove all flags
        """
        self.setFlags(QtCore.Qt.NoItemFlags)



class MultiColumnTableWidgetItem(CcpnTableWidgetItem):
    """
    Class implementing new sorting applied to TableWidgetItem using universalSortKey.

    Table will be sorted on the max/min of subgroups defined by column PIDCOLUMN.
    Subgrouped items always stay as a consecutive rows

    PIDCOLUMN defines the column containing duplicate items that form a subgroup.

    e.g.    can be sorted on int        - default behaviour
            ascending   descending
    AA 1        AA 5        CC 8
    AA 5        AA 4        CC 3
    CC 3        AA 1        CC 2
    CC 8        CC 8        AA 5
    AA 4        CC 3        AA 4
    CC 2        CC 2        AA 1

    Or sorting max/min can also apply to the subgroup
    e.g.    can be sorted on int
            ascending   descending
    AA 1        AA 5        AA 1
    AA 5        AA 4        AA 4
    CC 3        AA 1        AA 5
    CC 8        CC 8        CC 2
    AA 4        CC 3        CC 3
    CC 2        CC 2        CC 8

    Requires table._groups be defined to apply sorting to multiple columns.

    The following need to be defined in subclassed GuiTable:

        ITEMKLASS = CcpnTableWidgetItem     Class of sorting TabelWidgetItem

        MERGECOLUMN = 0                     Column number for duplicated items that define a group
        PIDCOLUMN = 0

        EXPANDERCOLUMN = 0                  Column containing the expander
        SPANCOLUMNS = ()                    List of columns that span is applied to
        MINSORTCOLUMN = 0                   Minimum column that check for group sorting
        enableMultiColumnSort = False       Enable/disable sorting with groups
        applySortToGroups = False           Apply sorting to groups - default is groups are always max->min

    """

    def __lt__(self, other):
        # new routine to overload TableWidgetItem that crashes when sorting None
        if self.sortMode == 'index' and hasattr(other, 'index'):
            return self.index < other.index
        if self.sortMode == 'value' and hasattr(other, 'value'):

            # need to compare the values of they are in the same group (i.e. same name)
            # need to compare the head/tail of the group if different groups

            col = self.column()
            table = self.tableWidget()

            if table.enableMultiColumnSort and col > table.MINSORTCOLUMN:
                if getattr(table, '_groups', None):
                    # get the duplicate group which should be in column PIDCOLUMN
                    dataSelf = table.indexFromItem(table.item(self.row(), table.PIDCOLUMN)).data()
                    dataOther = table.indexFromItem(table.item(other.row(), table.PIDCOLUMN)).data()

                    try:
                        if table.applySortToGroups:
                            # if need ascending/descending - group and subgroup
                            if dataSelf != dataOther:  # different name -> sort by min/max of each group
                                if table.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
                                    return table._groups[dataSelf]['min'][col] < table._groups[dataOther]['min'][col]
                                else:
                                    return table._groups[dataSelf]['max'][col] < table._groups[dataOther]['max'][col]

                        else:
                            # if need groups ascending/descending - subgroup always max->min
                            if dataSelf != dataOther:  # different name -> sort by min/max of each group
                                return table._groups[dataSelf]['max'][col] < table._groups[dataOther]['max'][col]

                            else:
                                if table.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
                                    return (universalSortKey(self.value) > universalSortKey(other.value))
                                else:
                                    return (universalSortKey(self.value) < universalSortKey(other.value))

                    except Exception as es:
                        # log warning and drop-out to default sorting
                        getLogger().warning(f'error sorting table on {dataSelf}({dataSelf in table._groups}):{dataOther}({dataOther in table._groups})\n{es}')

            return (universalSortKey(self.value) < universalSortKey(other.value))

        else:
            if self.text() and other.text():
                return (universalSortKey(self.text()) < universalSortKey(other.text()))
            else:
                return False
