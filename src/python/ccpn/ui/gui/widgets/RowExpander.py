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
__dateModified__ = "$dateModified: 2021-04-28 18:21:41 +0100 (Wed, April 28, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-04-16 11:44:37 +0000 (Fri, April 16, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore
from ccpn.ui.gui.widgets.Label import ActiveLabel
from ccpn.ui.gui.widgets.Icon import Icon


class RowExpander(QtWidgets.QWidget):
    BUTTONSIZE = 16
    PIXMAPSIZE = 10
    CLOSEDICON = 'icons/caret-grey-right'
    OPENICON = 'icons/caret-grey-down'

    def __init__(self, parent, tableItem=None, expanded=True):
        """Initialise the object

        :param parent: parent for the icon - usually the table
                       should be set later with .setCellWidget
        :param tableItem: the cell item container from the table
        :param expanded:
        """
        super().__init__(parent)

        self._table = parent
        self._tableItem = tableItem
        self._expanded = expanded
        self._activeRow = None

        # create the pixmaps for the icon
        self._openPixmap = Icon(self.OPENICON).pixmap(self.PIXMAPSIZE, self.PIXMAPSIZE)
        self._closedPixmap = Icon(self.CLOSEDICON).pixmap(self.PIXMAPSIZE, self.PIXMAPSIZE)

        self._setWidgets()

    def _setWidgets(self):
        """Setup the widgets
        """
        # create a new button from an active label - doesn't have a button-click visual effect
        button = self._button = ActiveLabel(self)
        button.setSelectionCallback(self._expandItem)
        button.setFixedSize(self.BUTTONSIZE, self.BUTTONSIZE)

        # set the pixmap
        if self._expanded:
            button.setPixmap(self._openPixmap)
        else:
            button.setPixmap(self._closedPixmap)

    def _expandItem(self):
        """Expand/collapse the items attached to the button
        """
        row = self._activeRow
        if row is None:
            return

        span = self._table.rowSpan(row, self._tableItem.column())
        if span > 1:
            # a group of rows - set the state of the first row
            if self._table.isRowHidden(row + 1):
                hidden = False
                self._button.setPixmap(self._openPixmap)
            else:
                hidden = True
                self._button.setPixmap(self._closedPixmap)

            # change the state of the remaining rows
            for rr in range(row + 1, row + span):
                self._table.setRowHidden(rr, hidden)

    def updateCellWidget(self, row, visible, setPixMapState=None):
        """Update the expanded/collapsed state of the button

        :param row: First row of the group of spanned cells this cell is associated with
        :param visible: True/False - cell visibility
        :param setPixMap: True/False - set the cell pixmap as required
        :return:
        """
        self._button.setVisible(visible)
        self._activeRow = row
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, not visible)
        if setPixMapState is not None:
            if setPixMapState:
                self._button.setPixmap(self._openPixmap)
            else:
                self._button.setPixmap(self._closedPixmap)
