"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-30 11:22:08 +0000 (Wed, November 30, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-11-24 12:32:46 +0100 (Thu, November 24, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtCore, QtWidgets
from functools import partial
import pandas as pd
import time
from ccpn.ui.gui.widgets.Font import setWidgetFont
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Column import ColumnClass, Column
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.table.TableABC import TableABC
from ccpn.util.Logging import getLogger


METADATACOLUMNS = ['name', 'parameter']


#=========================================================================================
# MetadataTable
#=========================================================================================

class MetadataTable(TableABC):
    """A table to contain metadata of a core object.
    """
    tableChanged = QtCore.pyqtSignal()

    def __init__(self, parent, obj=None, *args, **kwds):
        """Initialise the table

        :param parent: parent widget.
        :param spectrum: target spectrum.
        :param args: additional arguments to pass to table-initialisation.
        :param kwds: additional keywords to pass to table-initialisation.
        """
        super().__init__(parent, *args, **kwds)

        # set the core-object specific information
        self.obj = obj

        # set the table _columns
        self._columnDefs = ColumnClass([])
        self._columnDefs._columns = [Column(col, lambda row: True) for col in METADATACOLUMNS]

        # set the delegate for editing
        delegate = _SimplePulldownTableDelegate(self, objectColumn=None)
        self.setItemDelegate(delegate)

        self._rightClickedTableIndex = None  # last selected item in a table before raising the context menu. Enabled with mousePress event filter

    @property
    def _df(self):
        """Return the Pandas-dataFrame holding the data.
        """
        return self.model().df

    #=========================================================================================
    # methods
    #=========================================================================================

    def getMetadata(self):
        """Get the metadata from the table.
        """
        return tuple(self._df.itertuples(index=False))

    def populateTable(self, metadata=None, editable=True):
        """Populate the table from the current core-object.
        If metadata are not specified, then existing values are used.

        :param metadata: dict of metadata.
        :param editable: True/False, for enabling/disabling editing, defaults to True.
        :return:
        """
        if metadata is not None:
            self._metadata = metadata

        if self._metadata is not None:
            df = pd.DataFrame(self._metadata, columns=METADATACOLUMNS)

        else:
            df = pd.DataFrame(columns=METADATACOLUMNS)

        self.updateDf(df, resize=True, setHeightToRows=True, setWidthToColumns=True, setOnHeaderOnly=True)

        self.setTableEnabled(editable)
        self.model().dataChanged.connect(self._dataChanged)

    def _dataChanged(self, *args):
        """Emit tableChanged signal if the table has been edited.

        :param args: catch optional arguments from event.
        :return:
        """
        self.tableChanged.emit()

    def setTableEnabled(self, value):
        """Enable/Disable the table.

        :param value: True/False.
        :return:
        """
        self.setEnabled(value)
        # not sure whether to disable the table or just disable the editing and menu items
        self.setEditable(value)
        for action in self._actions:
            action.setEnabled(value)

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    def setTableMenu(self):
        """Set up the context menu for the main table.
        """
        self._thisTableMenu = menu = Menu('', self, isFloatWidget=True)
        setWidgetFont(menu, )

        # no options from the super-class are required
        self._actions = [menu.addAction('New', self._newTransfer),
                         menu.addAction('Remove selected', self._removeTransfer)
                         ]

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._raiseTableContextMenu)

        return menu


#=========================================================================================
# _SmallPulldown
#=========================================================================================

class _SmallPulldown(PulldownList):
    """Pulldown popup to hold the pulldown lists for editing the table cell,
    modified to block closing until after the double-click interval has elapsed.
    This make the table editing cleaner.
    """

    def __init__(self, parent, mainWindow=None, project=None, *args, **kwds):
        super().__init__(parent, *args, **kwds)

        self.mainWindow = mainWindow
        self.project = project
        self._popupTimer = time.perf_counter()
        self._interval = QtWidgets.QApplication.instance().doubleClickInterval() / 1e3

    def showPopup(self):
        """Show the popup and store the popup time.
        """
        self._popupTimer = time.perf_counter()
        super().showPopup()

    def hidePopup(self) -> None:
        """Hide the popup if event occurs after the double-click interval
        """
        diff = time.perf_counter() - self._popupTimer
        if diff > self._interval:
            # disable the hidePopup until after the double-click interval
            # prevents the popup showing/hiding when double-clicked
            return super().hidePopup()


#=========================================================================================
# Table delegate to handle editing
#=========================================================================================

EDIT_ROLE = QtCore.Qt.EditRole


class _SimplePulldownTableDelegate(QtWidgets.QStyledItemDelegate):
    """Handle the setting of data when editing the table
    """
    modelDataChanged = QtCore.pyqtSignal()

    def __init__(self, parent, objectColumn=None):
        """Initialise the delegate.

        :param parent: link to the handling table.
        :param objectColumn: name of the column containing the objects for referencing.
        """
        super().__init__(parent)
        self.customWidget = None
        self._parent = parent
        self._objectColumn = objectColumn

    def createEditor(self, parentWidget, itemStyle, index):
        """Returns the edit widget.

        :param parentWidget: the table widget.
        :param itemStyle: style to apply to the editor.
        :param index: QModelIndex of the cell in the table.
        :return: editor widget defined by the editClass.
        """
        col = index.column()
        objCol = self._parent._columnDefs.columns[col]

        if objCol.editClass:
            widget = objCol.editClass(None, *objCol.editArgs, **objCol.editKw)
            widget.setParent(parentWidget)
            widget.activated.connect(partial(self._pulldownActivated, widget))
            widget.closeOnLineEditClick = False

            self.customWidget = widget
            return widget

        self.customWidget = None

        return super().createEditor(parentWidget, itemStyle, index)

    def setEditorData(self, widget, index) -> None:
        """Populate the editor widget when the cell is edited.

        :param widget: the editor widget.
        :param index: QModelIndex of the cell in the table.
        :return:
        """
        if self.customWidget:
            model = index.model()
            value = model.data(index, EDIT_ROLE)

            if not isinstance(value, (list, tuple)):
                value = (value,)

            if hasattr(widget, 'selectValue'):
                widget.selectValue(*value)
            else:
                raise RuntimeError(f'Widget {widget} does not expose a set method; required for table editing')

        else:
            super().setEditorData(widget, index)

    def setModelData(self, widget, mode, index):
        """Set the object to the new value.

        :param widget: the editor widget.
        :param mode: editing mode.
        :param index: QModelIndex of the cell in the table.
        """
        if self.customWidget:
            if hasattr(widget, 'get'):
                value = widget.get()
            else:
                raise RuntimeError(f'Widget {widget} does not expose a get method; required for table editing')

            try:
                model = index.model()
                model.setData(index, value)

            except Exception as es:
                getLogger().debug(f'Error handling cell editing: {index.row()} {index.column()} - {es}  {self._parent.model()._sortIndex}  {value}')

        else:
            super(_SimplePulldownTableDelegate, self).setModelData(widget, mode, index)

    def updateEditorGeometry(self, widget, itemStyle, index):
        """Ensures that the editor is displayed correctly.

        :param widget: the editor widget.
        :param itemStyle: style to apply to the editor.
        :param index: QModelIndex of the cell in the table.
        :return:
        """
        if self.customWidget:
            cellRect = itemStyle.rect
            pos = widget.mapToGlobal(cellRect.topLeft())
            x, y = pos.x(), pos.y()
            hint = widget.sizeHint()
            width = max(hint.width(), cellRect.width())
            height = max(hint.height(), cellRect.height())

            # force the pulldownList to be a popup - will always close when clicking outside
            widget.setParent(self._parent, QtCore.Qt.Popup)
            widget.setGeometry(x, y, width, height)
            # QT delay to popup ensures that focus is correct when opening
            QtCore.QTimer.singleShot(0, widget.showPopup)

        else:
            super().updateEditorGeometry(widget, itemStyle, index)

    @staticmethod
    def _pulldownActivated(widget):
        """Close the editor widget.

        :param widget: editor widget.
        :return:
        """
        # stop the closed-pulldownList from staying visible after selection
        widget.close()
