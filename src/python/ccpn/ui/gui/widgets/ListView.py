"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-04 15:06:02 +0000 (Wed, November 04, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-26 14:50:42 +0000 (Tue, May 26, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSize
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Constants import ccpnmrJsonData
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS, BORDERNOFOCUS
from ccpn.ui.gui.lib.mouseEvents import makeDragEvent


HEADERHEIGHT = 24
MIN_ROWS = 4


class ListView(QtWidgets.QListView, Base):
    """
    Class to implement a ListView

    ListView can be set to show a maximum number of rows.
    Can also be minimised to the contents - this requires the container to be set.
        Also advisable to set the sizePolicy of the container:
        e.g. listViewContainer.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
    """

    def __init__(self, parent=None, mainWindow=None, fitToContents=False, listViewContainer=None,
                 maximumRows=200, headerHeight=None, minRowCount=None, multiSelect=False, **kwds):
        """Initialise the class
        """
        super().__init__(parent)
        Base._init(self, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self._parent = parent
        self._fitToContents = fitToContents
        self._listViewContainer = listViewContainer
        self._maximumRows = maximumRows

        self.multiSelect = multiSelect
        if self.multiSelect:
            self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        else:
            self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.setDragEnabled(True)
        self.setDragDropMode(self.DragDrop)

        self._headerHeight = HEADERHEIGHT if headerHeight is None else headerHeight
        self._minRowCount = MIN_ROWS if minRowCount is None else minRowCount
        self._setFocusColour()

    def _setFocusColour(self, focusColour=None, noFocusColour=None):
        """Set the focus/noFocus colours for the widget
        """
        focusColour = getColours()[BORDERFOCUS]
        noFocusColour = getColours()[BORDERNOFOCUS]
        styleSheet = "ListView { " \
                     "border: 1px solid;" \
                     "border-radius: 1px;" \
                     "border-color: %s;" \
                     "} " \
                     "ListView:focus { " \
                     "border: 1px solid %s; " \
                     "border-radius: 1px; " \
                     "}" % (noFocusColour, focusColour)
        self.setStyleSheet(styleSheet)

    def _minRows(self, rc):
        """Return the number of rows to show
        """
        #GST actually it appears maximum rows is effectivey ignored as long as its large...
        result = min(rc, self._maximumRows)
        if result > 0 and result <= self._minRowCount:
            result = self._minRowCount
        return result

    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        """Resize the listview to its contents
        """
        if self._fitToContents:
            rc = self.model().rowCount()
            if rc > 0:
                rc = self._minRowCount if rc < self._minRowCount else rc
            rh = self.sizeHintForRow(0) + 1  # allow padding between rows
            fh = self.frameWidth() * 2

            maxListHeight = (self._minRows(rc) * rh) + fh
            maxContainerHeight = maxListHeight + self._headerHeight
            maxContainerHeight = max(maxContainerHeight, self._listViewContainer.minimumHeight())
            # GST 4 rows is a good height as it gves a sensible scrollbar
            # left in for future improvments: user adjustable results size
            # minListHeight = (self._minRowCount * rh) + fh
            # minContainerHeight = minListHeight + self._headerHeight

            if self._listViewContainer:
                self._listViewContainer.setMaximumHeight(maxContainerHeight if rc else 0)
                # GST currently disabled due to bugs
                # self._listViewContainer.setMinimumHeight(minContainerHeight if rc else 0)

        super(ListView, self).resizeEvent(ev)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Keep a list of the selected items when the left mouse button is pressed
        """
        # call superclass to update selected items
        super().mousePressEvent(event)

        if event.button() == QtCore.Qt.LeftButton:
            # keep the list if left button pressed
            self._dragStartPosition = event.pos()

            pids = []
            for item in sorted(self.selectionModel().selectedRows(0), key=lambda val: val.row()):
                if item is not None:
                    dataPid = item.data()  #item.data(0, QtCore.Qt.DisplayRole)
                    # dataPid = item.indexes()[0].data()  #item.data(0, QtCore.Qt.DisplayRole)
                    if self.project and self.project.getByPid(dataPid):
                        pids.append(str(dataPid))

            self._pids = list(pids) or None
        else:
            self._dragStartPosition = None
            self._pids = None

        self._mouseButton = event.button()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Create a mouse drag event with the selected items when dragging with the left button
        """
        if self._mouseButton == QtCore.Qt.LeftButton and self._pids:
            if (event.pos() - self._dragStartPosition).manhattanLength() >= QtWidgets.QApplication.startDragDistance():
                makeDragEvent(self, {'pids': self._pids}, self._pids, '\n'.join(self._pids))
