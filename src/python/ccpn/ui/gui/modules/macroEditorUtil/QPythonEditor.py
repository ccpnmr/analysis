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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-07-19 14:32:43 +0100 (Wed, July 19, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2020-05-15 09:30:25 +0000 (Fri, May 15, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtPrintSupport
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog
from pyqode.python.widgets import PyCodeEdit
from ccpn.ui.gui.modules.macroEditorUtil import MacroEditorServer
from ccpn.ui.gui.modules.macroEditorUtil import MacroEditorNativeServer
from pyqode.python import panels as pypanels
from pyqode.core import api
from pyqode.python.modes.calltips import CalltipsMode
from ccpn.ui.gui.modules.macroEditorUtil.workers import CcpnQuickDocPanel, CcpnCalltipsMode
from pyqode.core.modes.code_completion import CodeCompletionMode
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.macroEditorUtil.CompletionProviders import CcpnNameSpacesProvider
from pyqode.core.cache import Cache


marginColour = QtGui.QColor('lightgrey')
marginPosition = 100
SEL_BACKGROUND_COLOUR = (255, 219, 179)
#########################################################################################
################################  Editor Widget  ########################################
#########################################################################################

class PyCodeEditor(PyCodeEdit, Base):

    useNativeCompletion = False # use the original completion without Ccpn Namespace

    def __init__(self, parent=None, application=None, **kwds):

        if self.useNativeCompletion:
            serverScript = MacroEditorNativeServer.__file__
        else:
            serverScript = MacroEditorServer.__file__
        super().__init__(parent,  server_script=serverScript)
        Base._init(self, **kwds)
        self.rightMarginMode = self.modes.get('RightMarginMode')
        if self.rightMarginMode:
            self.rightMarginMode.color = marginColour
            self.rightMarginMode.position = marginPosition

        self.application = application
        self.completionMode = self.modes.get(CodeCompletionMode.__name__)
        self.maxCompletionWaiting = 1 # seconds before aborting a completion request (avoid long waiting)
        if self.application and not self.useNativeCompletion:
            self.backend.stop()
            self.completionMode.request_completion = self._requestCompletion
            self.completionMode._insert_completion = self._insertCompletion

        self.panels.remove(pypanels.QuickDocPanel)
        self.docPanel = CcpnQuickDocPanel()
        self.panels.append(self.docPanel, api.Panel.Position.BOTTOM)
        self.modes.remove(CalltipsMode)
        self.modes.append(CcpnCalltipsMode())
        # self.docPanel.setVisible(True)

    def _init_style(self):
        """ Refactor to keep consistent with Ccpn style """
        self._background = QtGui.QColor('white')
        self._foreground = QtGui.QColor('black')
        self._whitespaces_foreground = QtGui.QColor('light gray')
        app = QtWidgets.QApplication.instance()
        self._sel_background = QtGui.QColor(*SEL_BACKGROUND_COLOUR)
        self._sel_foreground = app.palette().highlightedText().color()
        self._font_size = 10
        self.font_name = ""


    def _requestCompletion(self, *args, **kwargs):
        """
        re-implemetation of completion to insert ccpn Namespaces from application
        without sending requests to threads.
        """
        from ccpn.core.lib.ContextManagers import Timeout as timeout
        completionMode = self.completionMode
        line = completionMode._helper.current_line_nbr()
        column = completionMode._helper.current_column_nbr() - len(completionMode.completion_prefix)
        same_context = (line == completionMode._last_cursor_line and column == completionMode._last_cursor_column)
        if same_context:
            if completionMode._request_id - 1 == completionMode._last_request_id:
                completionMode._show_popup()
            else:
                # same context but result not yet available
                pass
            return True
        else:
            try:
                code = completionMode.editor.toPlainText()
                line = line
                column = column
                path = completionMode.editor.file.path
                encoding = completionMode.editor.file.encoding
                prefix = completionMode.completion_prefix
                request_id = completionMode._request_id
                results = [(line, column, request_id), []]
                with timeout(seconds=self.maxCompletionWaiting,
                             timeoutMessage='MacroEditor: Completion aborted\n',
                             loggingType='debug3'):
                    cw = CcpnNameSpacesProvider()
                    completions = cw.complete(code, line, column, path, encoding, prefix)
                    results = [(line, column, request_id), completions]
            except (Exception, TimeoutError) as es:
                return False
            else:
                completionMode._last_cursor_column = column
                completionMode._last_cursor_line = line
                completionMode._request_id += 1
                completionMode._on_results_available(results)
                return True

    def _insertCompletion(self, completion):
        completionMode = self.completionMode
        cursor = completionMode._helper.word_under_cursor(select_whole_word=False)
        cursor.insertText(completion)
        self.setTextCursor(cursor)
        if self.docPanel.isVisible():
            self.docPanel._on_action_quick_doc_triggered()

    def get(self):
        return self.toPlainText()

    def set(self, value):
        self.setPlainText(value)

    def saveToPDF(self, fileName=None):
        fType = '*.pdf'
        dialog = MacrosFileDialog(parent=self, acceptMode='save', selectFile=fileName, fileFilter=fType)
        dialog.exec()
        filename = dialog.selectedFile()
        if filename:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setColorMode(QtPrintSupport.QPrinter.Color)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            self.document().print_(printer)

    def enterEvent(self, event):
        self.setFocus()
        super(PyCodeEditor, self).enterEvent(event)

    def close(self, clear=False):

        """
        Closes the editor, stops the backend and removes any installed
        mode/panel.

        This is also where we cache the cursor position.

        :param clear: True to clear the editor content before closing.
        """
        if self._tooltips_runner:
            self._tooltips_runner.cancel_requests()
            self._tooltips_runner = None
        self.decorations.clear()
        self.backend.stop()
        Cache().set_cursor_position(
                self.file.path, self.textCursor().position())


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog

  app = TestApplication()
  popup = CcpnDialog(windowTitle='Test widget', setLayout=True)
  editor = PyCodeEditor(popup, grid=[0,0])
  editor.set('print("Hello")')
  editor.get()


  popup.show()
  popup.raise_()
  app.start()



