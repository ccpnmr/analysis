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
__dateModified__ = "$dateModified: 2022-09-20 18:54:09 +0100 (Tue, September 20, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 18:14:25 +0100 (Thu, September 08, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore, QtGui
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS
from ccpn.util.Logging import getLogger


ORIENTATIONS = {'h'                 : QtCore.Qt.Horizontal,
                'horizontal'        : QtCore.Qt.Horizontal,
                'v'                 : QtCore.Qt.Vertical,
                'vertical'          : QtCore.Qt.Vertical,
                QtCore.Qt.Horizontal: QtCore.Qt.Horizontal,
                QtCore.Qt.Vertical  : QtCore.Qt.Vertical,
                }

# define a role to return a cell-value
DTYPE_ROLE = QtCore.Qt.UserRole + 1000
VALUE_ROLE = QtCore.Qt.UserRole + 1001
INDEX_ROLE = QtCore.Qt.UserRole + 1002

EDIT_ROLE = QtCore.Qt.EditRole
_EDITOR_SETTER = ('setColor', 'selectValue', 'setData', 'set', 'setValue', 'setText', 'setFile')
_EDITOR_GETTER = ('get', 'value', 'text', 'getFile')
_replaceAlternativeColor = QtGui.QColor(getColours()[BORDERFOCUS])


#=========================================================================================
# Table delegate to handle editing
#=========================================================================================

class _TableDelegate(QtWidgets.QStyledItemDelegate):
    """handle the setting of data when editing the table
    """

    def __init__(self, parent=None, objectColumn=None):
        """Initialise the delegate
        :param parent - link to the handling table
        """
        super().__init__(parent)
        self.customWidget = None
        self._parent = parent
        self._objectColumn = objectColumn

    def createEditor(self, parentWidget, itemStyle, index):  # returns the edit widget
        """Create the editor widget
        """
        col = index.column()
        objCol = self._parent._columnDefs.columns[col]

        if objCol.editClass:
            widget = objCol.editClass(None, *objCol.editArgs, **objCol.editKw)
            widget.setParent(parentWidget)
            # widget.activated.connect(partial(self._pulldownActivated, widget))

            self.customWidget = widget

            return widget

        else:
            self.customWidget = None

            return super().createEditor(parentWidget, itemStyle, index)

    def setEditorData(self, widget, index) -> None:
        """populate the editor widget when the cell is edited
        """
        model = index.model()
        value = model.data(index, EDIT_ROLE)

        if not isinstance(value, (list, tuple)):
            value = (value,)

        for attrib in _EDITOR_SETTER:
            # get the method from the widget, and call with appropriate parameters
            if (func := getattr(widget, attrib, None)):
                if not callable(func):
                    raise TypeError(f"widget.{attrib} is not callable")

                func(*value)
                break

        else:
            raise Exception(f'Widget {widget} does not expose a set method; required for table editing')

    def setModelData(self, widget, mode, index):
        """Set the object to the new value
        :param widget - typically a lineedit handling the editing of the cell
        :param mode - editing mode:
        :param index - QModelIndex of the cell
        """
        for attrib in _EDITOR_GETTER:
            if (func := getattr(widget, attrib, None)):
                if not callable(func):
                    raise TypeError(f"widget.{attrib} is not callable")

                value = func()
                break

        else:
            raise Exception(f'Widget {widget} does not expose a get method; required for table editing')

        row, col = index.row(), index.column()
        try:
            # get the sorted element from the dataFrame
            df = self._parent._df
            iRow = self._parent.model()._sortIndex[row]
            iCol = df.columns.get_loc(self._objectColumn)
            # get the object
            obj = df.iat[iRow, iCol]

            # set the data which will fire notifiers to populate all tables (including this)
            func = self._parent._dataFrameObject.setEditValues[col]
            if func and obj:
                func(obj, value)

        except Exception as es:
            getLogger().debug('Error handling cell editing: %i %i - %s    %s    %s' % (row, col, str(es), self._parent.model()._sortIndex, value))

    def updateEditorGeometry(self, widget, itemStyle, index):  # ensures that the editor is displayed correctly

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

            # # QT delay to popup ensures that focus is correct when opening
            # # - requires subclass of pulldown to delay closing in double-click
            # QtCore.QTimer.singleShot(0, widget.showPopup)

        else:
            return super().updateEditorGeometry(widget, itemStyle, index)

    def _returnPressedCallback(self, widget):
        """Capture the returnPressed event from the widget, because the setModeData event seems to be a frame behind the widget
        when getting the text()
        """

        # check that it is a QLineEdit - check for other types later (see old table class)
        if isinstance(widget, QtWidgets.QLineEdit):
            self._editorValue = widget.text()
            self._returnPressed = True


#=========================================================================================
# Table delegate to handle cell-painting
#=========================================================================================

class _TableDelegateABC(QtWidgets.QStyledItemDelegate):
    """handle the setting of data when editing the table
    """

    def paint(self, painter, option, index):
        """Paint the contents of the cell.
        """
        # Remove dotted border on cell focus.  https://stackoverflow.com/a/55252650/3620725
        #   or put 'outline: 0px;' into the QTableView stylesheet
        focus = False
        if option.state & QtWidgets.QStyle.State_HasFocus:
            option.state = option.state ^ QtWidgets.QStyle.State_HasFocus
            focus = True

        super().paint(painter, option, index)

        if (brush := index.data(QtCore.Qt.BackgroundRole)) and (option.state & QtWidgets.QStyle.State_Selected):
            painter.save()
            # fade the background and paint over the top of selected cell
            # - ensures that different coloured backgrounds are still visible
            # - does, however, modify the foreground colour :|
            brush.setAlphaF(0.20)
            painter.setCompositionMode(painter.CompositionMode_SourceOver)
            painter.fillRect(option.rect, brush)
            if focus:
                # move the focus rectangle drawing to after, otherwise, alternative-background-color is used
                painter.setPen(_replaceAlternativeColor)
                painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
            painter.restore()

        elif focus:
            # move the focus rectangle drawing to after, otherwise, alternative-background-color is used
            painter.save()
            painter.setPen(_replaceAlternativeColor)
            painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
            painter.restore()
