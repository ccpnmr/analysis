#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-04 12:07:38 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2020-05-15 09:30:25 +0000 (Fri, May 15, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtGui
from pyqode.qt import QtWidgets, QtCore
from PyQt5 import QtPrintSupport
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog
from pyqode.python.widgets import PyCodeEdit
from pyqode.core import modes as modes
from ccpn.ui.gui.modules.macroEditorUtil import MacroEditorServer
from pyqode.core.backend import NotRunning
from pyqode.core import backend
from ccpn.ui.gui.modules.macroEditorUtil.CompletionProviders import CcpnNameSpacesProvider
from ccpn.framework.Application import getApplication

# import warnings
# with warnings.catch_warnings():
#     warnings.filterwarnings("ignore", message='Unimplemented completion icon_type:')

marginColour = QtGui.QColor('lightgrey')
marginPosition = 100



#
# class CcpnNamespaceCompletionMode(modes.CodeCompletionMode):
#     """
#     Extend base code completion mode to insert the completion in the buffer of the
#     input handler.
#
#     """
#     namespace = {}
#     ccpnCompleter = CcpnNameSpacesProvider()
#
#
#     def request_completion(self):
#         line = self._helper.current_line_nbr()
#         column = self._helper.current_column_nbr() - \
#             len(self.completion_prefix)
#         same_context = (line == self._last_cursor_line and
#                         column == self._last_cursor_column)
#         if same_context:
#             if self._request_id - 1 == self._last_request_id:
#                 # context has not changed and the correct results can be
#                 # directly shown
#                 self._show_popup()
#             else:
#                 # same context but result not yet available
#                 pass
#             return True
#         else:
#
#             data = {
#                 'code': self.editor.toPlainText(),
#                 'line': line,
#                 'column': column,
#                 'path': self.editor.file.path,
#                 'encoding': self.editor.file.encoding,
#                 'prefix': self.completion_prefix,
#                 'request_id': self._request_id
#             }
#             print('data ===>', data)
#             application = getApplication()
#             if application:
#                 self.namespace = application.mainWindow.namespace
#             result = []
#             try:
#                 self.ccpnCompleter.namespace = self.namespace
#                 result = self.ccpnCompleter.complete(code = self.editor.toPlainText(),
#                                                 line = line,
#                                                 column = column,
#                                                 path = self.editor.file.path,
#                                                 encoding = self.editor.file.encoding,
#                                                 prefix = self.completion_prefix,)
#                 print('=RESULTS ===>',result)
#             except NotRunning:
#                 return False
#             else:
#                 self._last_cursor_column = column
#                 self._last_cursor_line = line
#                 self._on_results_available([[line, column, self._request_id], result])
#                 self._request_id += 1
#
#                 return True
#
#     def _on_results_available(self, results):
#         context = results[0]
#         results = results[1:]
#         if not results: return
#         line, column, request_id = context
#
#         self._last_request_id = request_id
#         if (line == self._last_cursor_line and
#                 column == self._last_cursor_column):
#             if self.editor:
#                 all_results = []
#                 for res in results:
#                     all_results += res
#                 self._show_completions(all_results)
#         else:
#
#             print('>>>_on_results_available >> outdated request, dropping')


#########################################################################################
################################  Editor Widget  ########################################
#########################################################################################

class PyCodeEditor(PyCodeEdit, Base):
    def __init__(self, parent=None, application=None, **kwds):
        super().__init__(parent,  server_script=MacroEditorServer.__file__)
        Base._init(self, **kwds)
        self.rightMarginMode = self.modes.get('RightMarginMode')
        if self.rightMarginMode:
            self.rightMarginMode.color = marginColour
            self.rightMarginMode.position = marginPosition

        self.application = application
        # if self.application:
        #     self.modes.remove(modes.CodeCompletionMode) #remove the default completion. the replacing ccpnCompletion includes the default plus its own.
        #     namespace = self.application.mainWindow.namespace
        #     ccpnNamespaceCompletionMode = CcpnNamespaceCompletionMode()
        #     ccpnNamespaceCompletionMode.namespace = namespace
        #     self.modes.append(ccpnNamespaceCompletionMode)

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



