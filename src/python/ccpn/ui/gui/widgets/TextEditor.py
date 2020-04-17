"""Module Documentation here

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
__dateModified__ = "$dateModified: 2020-04-17 16:48:35 +0100 (Fri, April 17, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import os
from PyQt5 import QtGui, QtWidgets, QtCore, QtPrintSupport
from ccpn.ui.gui.widgets.FileDialog import FileDialog, USERMACROSPATH
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Action import Action
# from ccpn.ui.gui.guiSettings import fixedWidthFont
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS, BORDERNOFOCUS


ATTRIBUTE_CHECK_LIST = ('_mouseStart', '_minimumWidth', '_widthStart', '_minimumHeight', '_heightStart')
ATTRIBUTE_HEIGHT_LIST = ('_minimumHeight')


class TextEditor(QtWidgets.QTextEdit, Base):
    editingFinished = QtCore.pyqtSignal()
    receivedFocus = QtCore.pyqtSignal()

    _minimumHeight = 25

    def __init__(self, parent=None, filename=None, **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        self.filename = filename

        from ccpn.framework.Application import getApplication

        getApp = getApplication()
        if getApp:
            self.setFont(getApp._fontSettings.fixedWidthFont)

        self._changed = False
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._handle_text_changed)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

        palette = self.viewport().palette()
        self._background = palette.color(self.viewport().backgroundRole())

        self._setFocusColour()

    def _setFocusColour(self, focusColour=None, noFocusColour=None):
        """Set the focus/noFocus colours for the widget
        """
        focusColour = getColours()[BORDERFOCUS]
        noFocusColour = getColours()[BORDERNOFOCUS]
        styleSheet = "QTextEdit { " \
                     "border: 1px solid;" \
                     "border-radius: 2px;" \
                     "border-color: %s;" \
                     "} " \
                     "QTextEdit:focus { " \
                     "border: 1px solid %s; " \
                     "border-radius: 2px; " \
                     "}" % (noFocusColour, focusColour)
        self.setStyleSheet(styleSheet)

    def _addGrip(self):
        # an idea to add a grip handle - can't thing of any other way
        self._gripIcon = Icon('icons/grip')
        self._gripLabel = Label(self)
        self._gripLabel.setPixmap(self._gripIcon.pixmap(16))
        self._gripLabel.mouseMoveEvent = self._mouseMoveEvent
        self._gripLabel.mousePressEvent = self._mousePressEvent
        self._gripLabel.mouseReleaseEvent = self._mouseReleaseEvent

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._gripLabel, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)

    def context_menu(self):
        a = self.createStandardContextMenu()
        actions = a.actions()
        edit = Action(a, text='Fonts', callback=self._setFont)
        a.insertAction(actions[3], edit)
        a.exec_(QtGui.QCursor.pos())

    def _setFont(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.font(), self)
        if ok:
            self.setFont(font)

    def focusInEvent(self, event):
        super(TextEditor, self).focusInEvent(event)
        self.receivedFocus.emit()

    def focusOutEvent(self, event):
        if self._changed:
            self.editingFinished.emit()
        super(TextEditor, self).focusOutEvent(event)

    def _handle_text_changed(self):
        self._changed = True

    def setTextChanged(self, state=True):
        self._changed = state

    def setHtml(self, html):
        self.setHtml(html)
        self._changed = False

    def get(self):
        return self.toPlainText()

    def set(self, value):
        self.setText(value)

    def zoom(self, delta):
        if delta < 0:
            self.zoomOut(1)
        elif delta > 0:
            self.zoomIn(5)

    def saveToPDF(self, fileName=None):

        dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                            acceptMode=FileDialog.AcceptSave, selectFile=fileName,
                            filter='*.pdf',
                            pathID=USERMACROSPATH)
        dialog._show()
        filename = dialog.selectedFile()
        if filename:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setColorMode(QtPrintSupport.QPrinter.Color)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            self.document().print_(printer)

    def _mousePressEvent(self, event):
        """Handle mouse press in the grip
        """
        super().mousePressEvent(event)
        self._resizing = True
        self._widthStart = self.width()
        self._heightStart = self.height()
        self._mouseStart = event.globalPos()

    def _mouseReleaseEvent(self, event):
        """Handle mouse release in the grip
        """
        super().mouseReleaseEvent(event)
        self._resizing = False

    def _mouseMoveEvent(self, event):
        """Update widget size as the grip is dragged
        """
        super().mouseMoveEvent(event)
        if self._resizing and all(hasattr(self, att) for att in ATTRIBUTE_CHECK_LIST):
            delta = event.globalPos() - self._mouseStart
            width = max(self._minimumWidth, self._widthStart + delta.x())
            height = max(self._minimumHeight, self._heightStart + delta.y())
            self.setMinimumSize(width, height)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(200, 20)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(200, 20)


class PlainTextEditor(QtWidgets.QPlainTextEdit, Base):
    editingFinished = QtCore.pyqtSignal()
    receivedFocus = QtCore.pyqtSignal()

    _minimumHeight = 25

    def __init__(self, parent=None, filename=None, fitToContents=False, **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        self.filename = filename
        self._fitToContents = fitToContents

        from ccpn.framework.Application import getApplication

        getApp = getApplication()
        if getApp:
            self.setFont(getApp._fontSettings.fixedWidthFont)

        self._changed = False
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._handle_text_changed)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

        palette = self.viewport().palette()
        self._background = palette.color(self.viewport().backgroundRole())

        self._setFocusColour()

        self._maxWidth = 0
        self._maxHeight = 0

    def _setFocusColour(self, focusColour=None, noFocusColour=None):
        """Set the focus/noFocus colours for the widget
        """
        focusColour = getColours()[BORDERFOCUS]
        noFocusColour = getColours()[BORDERNOFOCUS]
        styleSheet = "QPlainTextEdit { " \
                     "border: 1px solid;" \
                     "border-radius: 2px;" \
                     "border-color: %s;" \
                     "} " \
                     "QPlainTextEdit:focus { " \
                     "border: 1px solid %s; " \
                     "border-radius: 2px; " \
                     "}" % (noFocusColour, focusColour)
        self.setStyleSheet(styleSheet)

    def _addGrip(self):
        # an idea to add a grip handle - can't thing of any other way
        self._gripIcon = Icon('icons/grip')
        self._gripLabel = Label(self)
        self._gripLabel.setPixmap(self._gripIcon.pixmap(16))
        self._gripLabel.mouseMoveEvent = self._mouseMoveEvent
        self._gripLabel.mousePressEvent = self._mousePressEvent
        self._gripLabel.mouseReleaseEvent = self._mouseReleaseEvent

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._gripLabel, 0, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)

    def context_menu(self):
        a = self.createStandardContextMenu()
        actions = a.actions()
        edit = Action(a, text='Fonts', callback=self._setFont)
        a.insertAction(actions[3], edit)
        a.exec_(QtGui.QCursor.pos())

    def _setFont(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.font(), self)
        if ok:
            self.setFont(font)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.receivedFocus.emit()

    def focusOutEvent(self, event):
        if self._changed:
            self.editingFinished.emit()
        super().focusOutEvent(event)

    def _handle_text_changed(self):
        self._changed = True
        self._updateheight()

    def setTextChanged(self, state=True):
        self._changed = state

    def zoom(self, delta):
        if delta < 0:
            self.zoomOut(1)
        elif delta > 0:
            self.zoomIn(5)

    def get(self):
        return self.toPlainText()

    def set(self, value):
        self.setPlainText(value)

    def saveToPDF(self, fileName=None):

        dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                            acceptMode=FileDialog.AcceptSave, selectFile=fileName,
                            filter='*.pdf',
                            pathID=USERMACROSPATH)
        dialog._show()
        filename = dialog.selectedFile()
        if filename:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setColorMode(QtPrintSupport.QPrinter.Color)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            self.document().print_(printer)

    def _mousePressEvent(self, event):
        """Handle mouse press in the grip
        """
        super().mousePressEvent(event)
        self._resizing = True
        self._widthStart = self.width()
        self._heightStart = self.height()
        self._mouseStart = event.globalPos()

    def _mouseReleaseEvent(self, event):
        """Handle mouse release in the grip
        """
        super().mouseReleaseEvent(event)
        self._resizing = False

    def _mouseMoveEvent(self, event):
        """Update widget size as the grip is dragged
        """
        super().mouseMoveEvent(event)
        if self._resizing and all(hasattr(self, att) for att in ATTRIBUTE_CHECK_LIST) and self._fitToContents:
            delta = event.globalPos() - self._mouseStart
            _size = self.document().size().toSize()
            width = max(self._minimumWidth, self._widthStart + delta.x(), _size.width())
            height = max(self._minimumHeight, self._heightStart + delta.y(), _size.height())

            self.setMinimumSize(width, height)
            self.updateGeometry()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        self._updateheight()
        super(PlainTextEditor, self).resizeEvent(e)

    def _updateheight(self):
        # Override the resize event to fit to contents
        if self._fitToContents:
            rowHeight = QtGui.QFontMetrics(self.document().defaultFont()).height()
            lineCount = self.document().lineCount()

            minHeight = (rowHeight + 1) * (lineCount + 1)
            self._maxHeight = max(self._minimumHeight, minHeight)
            self.setMaximumHeight(self._maxHeight)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.ui.gui.widgets.Widget import Widget


    app = TestApplication()

    popup = CcpnDialog(windowTitle='Test widget', setLayout=True)
    widget = TextEditor(parent=popup, grid=(0, 0))

    popup.show()
    popup.raise_()
    app.start()
