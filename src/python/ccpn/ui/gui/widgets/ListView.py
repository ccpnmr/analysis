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
__dateModified__ = "$dateModified: 2020-10-07 17:12:47 +0100 (Wed, October 07, 2020) $"
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
                 maxmimumRows=200, headerHeight=None, minRowCount = None, **kwds):
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
        self._maximumRows = maxmimumRows

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
                rc  = self._minRowCount if rc < self._minRowCount else rc
            rh = self.sizeHintForRow(0)
            fh = self.frameWidth() * 2

            maxListHeight = (self._minRows(rc) * rh) + fh
            maxContainerHeight = maxListHeight + self._headerHeight

            # GST 4 rows is a good height as it gves a sensible scrollbar
            # left in for future improvments: user adjustable results size
            # minListHeight = (self._minRowCount * rh) + fh
            # minContainerHeight = minListHeight + self._headerHeight


            if self._listViewContainer:
                self._listViewContainer.setMaximumHeight(maxContainerHeight if rc else 0)
                # GST currently disabled due to bugs
                # self._listViewContainer.setMinimumHeight(minContainerHeight if rc else 0)

        super(ListView, self).resizeEvent(ev)

    def dragEnterEvent(self, event):
        """Handle drag enter event to create a new drag/drag item.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            pids = []
            for item in self.selectionModel().selection():
                if item is not None:

                    dataPid = item.indexes()[0].data()          #item.data(0, QtCore.Qt.DisplayRole)
                    if self.project and self.project.getByPid(dataPid):
                        pids.append(str(dataPid))

            itemData = json.dumps({'pids': pids})

            tempData = QtCore.QByteArray()
            stream = QtCore.QDataStream(tempData, QtCore.QIODevice.WriteOnly)
            stream.writeQString(itemData)
            event.mimeData().setData(ccpnmrJsonData, tempData)
            event.mimeData().setText(itemData)

            event.accept()
