"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
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
__dateModified__ = "$dateModified: 2023-12-01 14:25:36 +0000 (Fri, December 01, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 18:14:25 +0100 (Thu, September 08, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS, BORDERNOFOCUS
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.table._TableCommon import BORDER_ROLE, EDIT_ROLE
from ccpn.util.Logging import getLogger


_EDITOR_SETTER = ('setColor', 'selectValue', 'setData', 'set', 'setValue', 'setText', 'setFile')
_EDITOR_GETTER = ('get', 'value', 'text', 'getFile')


#=========================================================================================
# Table delegate to handle editing
#=========================================================================================

class _TableDelegate(QtWidgets.QStyledItemDelegate):
    """handle the setting of data when editing the table
    """

    _focusBorderWidth = 1
    _focusPen = None
    _noFocusPen = None

    def __init__(self, parent, *, objectColumn=None, focusBorderWidth=1):
        """Initialise the delegate
        :param parent - link to the handling table
        """
        super().__init__(parent)

        self.customWidget = None
        self._parent = parent
        self._objectColumn = objectColumn

        # set the colours
        self._focusPen = QtGui.QPen(QtGui.QColor(getColours()[BORDERFOCUS]))
        self._noFocusPen = QtGui.QPen(QtGui.QColor(getColours()[BORDERNOFOCUS]))

        # double the line-widths accounts for the device-pixel-ratio
        self._focusBorderWidth = focusBorderWidth
        self._focusPen.setWidthF(focusBorderWidth * 2.0)
        self._focusPen.setJoinStyle(QtCore.Qt.MiterJoin)  # square ends
        self._noFocusPen.setWidthF(2.0)

        # set the required alternative colour
        self._replaceAlternativeColor = QtGui.QColor(getColours()[BORDERFOCUS])

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> None:
        """Paint the contents of the cell.
        """
        painter.save()
        focus = (option.state & QtWidgets.QStyle.State_HasFocus)
        option.state = option.state & ~QtWidgets.QStyle.State_HasFocus

        super().paint(painter, option, index)

        if focus and self._focusBorderWidth:
            painter.setClipRect(option.rect)
            painter.setPen(self._focusPen)
            painter.drawRect(option.rect)

        painter.restore()

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
            raise RuntimeError(f'Widget {widget} does not expose a set method; required for table editing')

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
            raise RuntimeError(f'Widget {widget} does not expose a get method; required for table editing')

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

    def updateEditorGeometry(self, widget, itemStyle, index):
        """Display the required editor for the cell
        """
        if not self.customWidget:
            return super().updateEditorGeometry(widget, itemStyle, index)

        cellRect = itemStyle.rect
        pos = widget.mapToGlobal(cellRect.topLeft())
        x, y = pos.x(), pos.y()
        hint = widget.sizeHint()
        width = max(hint.width(), cellRect.width())
        height = max(hint.height(), cellRect.height())

        # force the pulldownList to be a popup - will always close when clicking outside
        widget.setParent(self._parent, QtCore.Qt.Popup)
        widget.setGeometry(x, y, width, height)

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
    """Handle the setting of data when editing the table
    """
    # NOTE:ED - this is required as setting the borders in the styleSheet disables the use of BackgroundRole in the table-model
    #   so need this alternative to add padding to the left of the cell :|
    _leftPadding = '  '  # 2 spaces should be enough

    _focusBorderWidth = 1
    _focusPen = None
    _noFocusPen = None

    def __init__(self, parent, focusBorderWidth=1):
        super().__init__(parent)

        self._parent = parent

        # set the colours
        self._focusPen = QtGui.QPen(QtGui.QColor(getColours()[BORDERFOCUS]))
        self._noFocusPen = QtGui.QPen(QtGui.QColor(getColours()[BORDERNOFOCUS]))

        # double the line-widths accounts for the device-pixel-ratio
        self._focusBorderWidth = focusBorderWidth
        self._focusPen.setWidthF(focusBorderWidth * 2.0)
        self._focusPen.setJoinStyle(QtCore.Qt.MiterJoin)  # square ends
        self._noFocusPen.setWidthF(2.0)

        # set the required alternative colour
        self._replaceAlternativeColor = QtGui.QColor(getColours()[BORDERFOCUS])

    def displayText(self, value, locale: QtCore.QLocale) -> str:
        """Add padding for editable cells.
        """
        value = super().displayText(value, locale)

        return (self._leftPadding + value)

    @staticmethod
    def _mergeColors(color1, color2, weight1=0.5, weight2=0.5):
        """
        Merge two QColor instances by calculating the weighted average of their color components.

        Parameters:
        - color1: First QColor instance
        - color2: Second QColor instance
        - weight1: Weight for color1 (default is 0.5)
        - weight2: Weight for color2 (default is 0.5)

        Returns:
        - Merged QColor instance
        """
        r = int(color1.red() * weight1 + color2.red() * weight2)
        g = int(color1.green() * weight1 + color2.green() * weight2)
        b = int(color1.blue() * weight1 + color2.blue() * weight2)
        a = int(color1.alpha() * weight1 + color2.alpha() * weight2)

        # Ensure the values are within the valid range (0-255)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        a = max(0, min(255, a))

        return QtGui.QColor(r, g, b, a)

    def paint(self, painter, option, index):
        """Paint the contents of the cell.
        """
        painter.save()

        # Remove dotted border on cell focus.  https://stackoverflow.com/a/55252650/3620725
        #   or put 'outline: 0px;' into the QTableView stylesheet
        focus = (option.state & QtWidgets.QStyle.State_HasFocus)
        option.state = option.state & ~QtWidgets.QStyle.State_HasFocus

        if option.state & QtWidgets.QStyle.State_Selected:
            # fade the background and paint over the top of selected cell
            # - ensures that different coloured backgrounds are still visible
            # - does, however, modify the foreground colour :|
            back = index.data(QtCore.Qt.BackgroundRole)
            fore = index.data(QtCore.Qt.ForegroundRole)
            back = self._mergeColors(back, option.palette.color(QtGui.QPalette.Highlight), 0.2, 0.8)
            fore = self._mergeColors(fore, option.palette.color(QtGui.QPalette.HighlightedText), 0.5, 0.5)
            # this might be better for changing the foreground/background colour - instead of model.data(COLOR_ROLE)
            option.palette.setColor(QtGui.QPalette.Highlight, back)
            option.palette.setColor(QtGui.QPalette.HighlightedText, fore)

        super().paint(painter, option, index)

        # alternative method to add selection border to the focussed cell
        # if (option.state & QtWidgets.QStyle.State_Selected) and (brush := index.data(QtCore.Qt.BackgroundRole)):
        #     # fade the background and paint over the top of selected cell
        #     # - ensures that different coloured backgrounds are still visible
        #     # - does, however, modify the foreground colour :|
        #     painter.setClipRect(option.rect)
        #     brush.setAlphaF(0.20)
        #     painter.setCompositionMode(painter.CompositionMode_SourceOver)
        #     painter.fillRect(option.rect, brush)
        #
        #     if focus:
        #         painter.setPen(self._focusPen)
        #         painter.drawRect(option.rect)
        #
        #     elif not focus and index.data(BORDER_ROLE):
        #         # move the focus rectangle drawing to after, otherwise, alternative-background-color is used
        #         painter.setPen(self._noFocusPen)
        #         painter.setRenderHint(QtGui.QPainter.Antialiasing)
        #         painter.drawRoundedRect(option.rect, 4, 4)

        if focus:
            painter.setClipRect(option.rect)
            painter.setPen(self._focusPen)
            painter.drawRect(option.rect)

        elif not focus and index.data(BORDER_ROLE):
            # move the focus rectangle drawing to after, otherwise, alternative-background-color is used
            painter.setClipRect(option.rect)
            painter.setPen(self._noFocusPen)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.drawRoundedRect(option.rect, 4, 4)

        painter.restore()

    def updateEditorGeometry(self, widget, itemStyle, index):
        """Fit editor geometry to the index
        """
        cellRect = itemStyle.rect
        widget.move(cellRect.topLeft())
        widget.setGeometry(cellRect)


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

class _SimplePulldownTableDelegate(QtWidgets.QStyledItemDelegate):
    """Handle the setting of data when editing the table
    """
    modelDataChanged = QtCore.pyqtSignal()

    def __init__(self, parent, *, objectColumn=None, focusBorderWidth=None):
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
