"""
Module Documentation here
"""
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
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-08-05 15:53:24 +0000 (,  05, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-08-05 15:53:24 +0000 (,  05, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


from pyqode.qt import QtWidgets, QtCore
from ccpn.ui.gui.modules.macroEditorUtil.CompletionProviders import getJediInterpreter
from pyqode.python import panels as pypanels
from pyqode.core.api import TextHelper
from pyqode.python.modes.calltips import CalltipsMode



def _quickDoc(request_data):
    """
    Worker that returns the documentation of the symbol under cursor.
    """
    code = request_data['code']
    line = request_data['line'] + 1
    column = request_data['column']
    path = request_data['path']
    encoding = 'utf-8'
    script = getJediInterpreter(text=code, line=line, column=column, path=path, encoding=encoding)
    try:
        definitions = script.goto_definitions()
    except Exception as ex:
        return []
    else:
        ret_val = [d.docstring() for d in definitions]
        return ret_val

class CcpnQuickDocPanel(pypanels.QuickDocPanel):
    """ Shows the python documentation for the word under the text cursor.

    This panel quickly shows the documentation of the symbol under
    cursor.
    """
    def _on_action_quick_doc_triggered(self):
        tc = TextHelper(self.editor).word_under_cursor(select_whole_word=True)
        request_data = {
            'code': self.editor.toPlainText(),
            'line': tc.blockNumber(),
            'column': tc.columnNumber(),
            'path': self.editor.file.path,
            'encoding': self.editor.file.encoding
        }
        self.editor.backend.send_request(
            _quickDoc, request_data, on_receive=self._on_results_available)


def _getCalltips(data):
    """
    Worker that returns a list of calltips.

    A calltips is a tuple made of the following parts:
      - module_name: name of the module of the function invoked
      - call_name: name of the function that is being called
      - params: the list of parameter names.
      - index: index of the current parameter
      - bracket_start

    :returns tuple(module_name, call_name, params)
    """
    code = data['code']
    line = data['line'] + 1
    column = data['column']
    path = data['path']
    # encoding = request_data['encoding']
    encoding = 'utf-8'
    # use jedi to get call signatures
    try:
        script = getJediInterpreter(text=code, line=line, column=column, path=path, encoding=encoding)
    except ValueError:
        # Is triggered when an the position is invalid, for example if the
        # column is larger or equal to the line length. This may be due to a
        # bug elsewhere in PyQode, but this at least suppresses the error
        # message, and does not seem to hve any adverse side effects.
        return []
    signatures = script.call_signatures()
    for sig in signatures:
        results = (str(sig.module_name), str(sig.name),
                   [p.description for p in sig.params], sig.index,
                   sig.bracket_start, column)
        return results
    return []


class CcpnCalltipsMode(CalltipsMode):
    """ Shows function calltips.

    This mode shows function/method call tips in a QToolTip using
    :meth:`jedi.Script.call_signatures`.
    """
    __requestCnt = 0

    def _on_key_released(self, event):
        if (event.key() == QtCore.Qt.Key_ParenLeft or
                event.key() == QtCore.Qt.Key_Comma):
            tc = self.editor.textCursor()
            line = tc.blockNumber()
            col = tc.columnNumber()
            fn = self.editor.file.path
            encoding = self.editor.file.encoding
            source = self.editor.toPlainText()
            # jedi has a bug if the statement has a closing parenthesis
            # remove it!
            lines = source.splitlines()
            try:
                l = lines[line].rstrip()
            except IndexError:
                # at the beginning of the last line (empty)
                return
            if l.endswith(")"):
                lines[line] = l[:-1]
            source = "\n".join(lines)
            self._request_calltip(source, line, col, fn, encoding)
        elif (event.key() in [
                QtCore.Qt.Key_ParenRight,
                QtCore.Qt.Key_Return,
                QtCore.Qt.Key_Left,
                QtCore.Qt.Key_Right,
                QtCore.Qt.Key_Up,
                QtCore.Qt.Key_Down,
                QtCore.Qt.Key_End,
                QtCore.Qt.Key_Home,
                QtCore.Qt.Key_PageDown,
                QtCore.Qt.Key_PageUp,
                QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete]):
            QtWidgets.QToolTip.hideText()

    def _request_calltip(self, source, line, col, fn, encoding):
        if self.__requestCnt == 0:
            self.__requestCnt += 1
            self.editor.backend.send_request(
                _getCalltips,
                {'code': source, 'line': line, 'column': col, 'path': None,
                 'encoding': encoding}, on_receive=self._on_results_available)

    def _on_results_available(self, results):
        if results:
            call = {"call.module.name": results[0],
                    "call.call_name": results[1],
                    "call.params": results[2],
                    "call.index": results[3],
                    "call.bracket_start": results[4]}
            self.tooltipDisplayRequested.emit(call, results[5])

    def _display_tooltip(self, call, col):
        if not call or self._is_last_chard_end_of_word():
            return
        # create a formatted calltip (current index appear in bold)
        calltip = "<p style='white-space:pre'>{0}.{1}(".format(
            call['call.module.name'], call['call.call_name'])
        for i, param in enumerate(call['call.params']):
            if i < len(call['call.params']) - 1 and not param.endswith(','):
                param += ", "
            if param.endswith(','):
                param += ' '  # pep8 calltip
            if i == call['call.index']:
                calltip += "<b>"
            calltip += param
            if i == call['call.index']:
                calltip += "</b>"
        calltip += ')</p>'
        # set tool tip position at the start of the bracket
        char_width = self.editor.fontMetrics().width('A')
        w_offset = (col - call['call.bracket_start'][1]) * char_width
        position = QtCore.QPoint(
            self.editor.cursorRect().x() - w_offset,
            self.editor.cursorRect().y() + char_width +
            self.editor.panels.margin_size(0))
        position = self.editor.mapToGlobal(position)
        # show tooltip
        calltip = calltip.replace(',', ',\n')
        QtWidgets.QToolTip.showText(position, calltip, self.editor)


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
