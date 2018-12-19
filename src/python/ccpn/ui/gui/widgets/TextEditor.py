"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
from ccpn.ui.gui.widgets.FileDialog import FileDialog

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.guiSettings import fixedWidthFont


class TextEditor(QtWidgets.QTextEdit, Base):
    editingFinished = QtCore.pyqtSignal()
    receivedFocus = QtCore.pyqtSignal()

    def __init__(self, parent=None, filename=None, **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        self.filename = filename
        self.setFont(fixedWidthFont)
        self._changed = False
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._handle_text_changed)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

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
        QtGui.TextEditor.setHtml(self, html)
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
                            filter='*.pdf')
        filename = dialog.selectedFile()
        if filename:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setColorMode(QtPrintSupport.QPrinter.Color)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            self.document().print_(printer)


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
