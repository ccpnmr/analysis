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
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Constants import ccpnmrJsonData


HEADERHEIGHT = 24
DEFAULTROWS = 15


class ListView(QtWidgets.QListView, Base):
    """
    Class to implement a ListView

    ListView can be set to show a maximum number of rows.
    Can also be minimised to the contents - this requires the container to be set.
        Also advisable to set the sizePolicy of the container:
        e.g. listViewContainer.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
    """
    def __init__(self, parent=None, mainWindow=None, fitToContents=False, listViewContainer=None,
                 maxmimumRows=DEFAULTROWS, **kwds):
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

    def _minRows(self, rc):
        """Return the number of rows to show
        """
        return min(rc, self._maximumRows)

    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        """Resize the listview to its contents or a maximum of DEFAULTROWS
        """
        if self._fitToContents:
            rc = self.model().rowCount()
            rh = self.sizeHintForRow(0) if rc else 0

            self.setMaximumHeight(self._minRows(rc) * rh)
            if self._listViewContainer:
                self._listViewContainer.setMaximumHeight((self._minRows(rc) * rh) + HEADERHEIGHT if rc else HEADERHEIGHT)

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
