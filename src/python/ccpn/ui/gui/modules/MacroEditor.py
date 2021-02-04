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
__dateModified__ = "$dateModified: 2021-02-04 12:07:34 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time as systime


if not hasattr(systime, 'clock'):
    # NOTE:ED - quick patch to fix bug in pyqt 5.9
    systime.clock = systime.process_time

import datetime
import os
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.QPythonEditor import PyCodeEditor
from ccpn.framework.PathsAndUrls import macroPath as ccpnMacroPath
from pyqode.python.widgets import PyConsole, PyInteractiveConsole
from ccpn.ui.gui.widgets.CheckBox import EditableCheckBox, CheckBox
import sys
from pyqode.core.api import TextHelper
from collections import OrderedDict as od
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Action import Action
import ntpath
import tempfile
from pathlib import Path
from ccpn.util.Path import aPath


_filenameLineEdit = '_filenameLineEdit'


class MacroEditor(CcpnModule):
    """
    Macro editor will run Python Files only.
    """
    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'MacroEditor'

    def __init__(self, mainWindow=None, name='Macro Editor', filePath=None):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        self.mainWindow = mainWindow
        self.application = None
        self.project = None
        self.current = None
        self.preferences = None
        self._pythonConsole = None
        self.ccpnMacroPath = ccpnMacroPath
        self._editor_windows = []  # used when running the macro externally on Analysis
        self.autoOpenPythonConsole = False  # When run: always open the PythonConsole module to see the output.
        self._preEditorText = ''  # text as appeared the first time the file was opened
        self._lastTimestp = None  # used to check if the file has been changed externally
        self._lastSaved = None
        self.filePath = filePath  # working filePath. If None, it will be created
        self._tempFile = None  # a temp file holder, used when the filePath is not specified
        self.userMacroDirPath = None  # dir path containing user Macros. from preferences if defined otherwise from .ccpn/macros

        if self.mainWindow:  # is running in Analysis
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            self.preferences = self.application.preferences
            self._pythonConsole = self.mainWindow.pythonConsole
            if self._pythonConsole is None:
                self._pythonConsole = IpythonConsole(self.mainWindow)

        if self.preferences:
            self.userMacroDirPath = self.preferences.general.userMacroPath
        if self.userMacroDirPath is None and self.application:
            self.userMacroDirPath = self.application.tempMacrosPath

        if not self.filePath:
            if self.userMacroDirPath is None:
                self._tempFile = tempfile.NamedTemporaryFile(suffix='.py')
                self._tempFile.close()
                self.filePath = self._tempFile.name
            else:
                if not os.path.exists(aPath(self.userMacroDirPath)):
                    from ccpn.ui.gui.widgets.MessageDialog import showYesNo

                    title, msg = "User macro path doesn't exist", "Do you want to create the folder?\n(no will revert to a temporary folder)"
                    openNew = showYesNo(title, msg)
                    if openNew:
                        # recursively create folder
                        os.makedirs(aPath(self.userMacroDirPath))

                if os.path.exists(aPath(self.userMacroDirPath)):
                    self._tempFile = tempfile.NamedTemporaryFile(prefix='macro_', dir=aPath(self.userMacroDirPath), suffix='.py')
                else:
                    self._tempFile = tempfile.NamedTemporaryFile(suffix='.py')

                # within AnalysisV3
                self._tempFile.close()
                self.filePath = self._tempFile.name

            with open(aPath(self.filePath), 'w'):
                pass

        self._setupWidgets()
        self.openPath(self.filePath)
        self._setFileName()
        self._setToolBar()
        self._createWidgetSettings()
        self.droppedNotifier = GuiNotifier(self.textEditor,
                                           [GuiNotifier.DROPEVENT], [DropBase.URLS],
                                           self._processDroppedItems)

    def _setupWidgets(self):
        """Setup the main widgets
        """
        _spacing = 4
        self.mainWidget.getLayout().setSpacing(_spacing)
        self.mainWidget.getLayout().setContentsMargins(_spacing, _spacing, _spacing, _spacing)
        hGrid = 0
        self.toolbar = ToolBar(self.mainWidget, grid=(hGrid, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')
        hGrid += 1
        self.filePathLabel = Label(self.mainWidget, hAlign='l', grid=(hGrid, 0))
        self._fileNameButtons = ButtonList(self.mainWidget, texts=['Save As...'],
                                           callbacks=[self.saveMacroAs],
                                           icons=[Icon('icons/saveAs')],
                                           hAlign='r',
                                           grid=(hGrid, 1))
        self._filenameLineEdit = LineEdit(self.mainWidget, grid=(hGrid, 1))
        self._filenameLineEdit.hide()
        setattr(self, _filenameLineEdit, LineEdit(self.mainWidget, grid=(hGrid, 1)))
        getattr(self, _filenameLineEdit).hide()  #  this is used only to store and restore the widgets
        hGrid += 1
        # macro editing area
        self.textEditor = PyCodeEditor(self.mainWidget, grid=(hGrid, 0), acceptDrops=True, gridSpan=(1, 2))
        self.searchReplacePanel = self.textEditor.panels.get('SearchAndReplacePanel')
        self.fileWatcher = self.textEditor.modes.get('FileWatcherMode')
        if self.fileWatcher:
            self.fileWatcher.on_state_changed(False)
        self.textEditor.focused_in.connect(self._focusInEvent)
        self.textEditor.textChanged.connect(self._textedChanged)

    def _createWidgetSettings(self):
        hGrid = 0
        self.autoOpenPythonConsoleLabel = Label(self.settingsWidget, 'Auto-Open PythonConsole', grid=(hGrid, 0), )
        self.autoOpenPythonConsoleCB = CheckBox(self.settingsWidget,
                                                checked=self.autoOpenPythonConsole,
                                                callback=self._setAutoOpenPythonConsole, grid=(hGrid, 1))

    def _setAutoOpenPythonConsole(self, value):
        self.autoOpenPythonConsole = value

    def run(self):
        if self._pythonConsole is not None:
            if self.autoOpenPythonConsole:
                self._openPythonConsoleModule()
            if self.filePath:
                self.preferences.recentMacros.append(self.filePath)
                self._pythonConsole._runMacro(self.filePath)
        else:
            # Used when running the editor outiside of Analyis. Run from an external IpythonConsole
            self._runOnTempIPythonConsole()

    def saveMacro(self):
        """
        Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
        appears for specification of the file path.
        """
        if not self.filePath:
            self.saveMacroAs()

        else:
            self._saveTextToFile()

    def saveMacroAs(self):
        """
        Opens a save file dialog and saves the text inside the textbox to a file specified in the dialog.
        """
        fType = '*.py'
        dialog = MacrosFileDialog(parent=self, acceptMode='save', directory=self.userMacroDirPath, selectFile=self.filePath, fileFilter=fType)
        dialog._show()
        filePath = dialog.selectedFile()
        if filePath is not None:
            if not filePath.endswith('.py'):
                filePath += '.py'
            if self.filePath != filePath:
                self._removeMacroFromCurrent()
                self._deleteTempFile()
            self.filePath = filePath
            self._saveTextToFile()
            self.openPath(filePath)
        else:
            self._checkFileStauts()

    def exportToPdf(self):
        self.textEditor.saveToPDF()

    def openPath(self, filePath):

        if filePath:
            if filePath.endswith('.py'):
                if self._isInCurrent(filePath):
                    MessageDialog.showMessage('Already Opened.', 'This file is already opened in the project')
                    return
                else:
                    with open(aPath(filePath), 'r') as f:
                        self.textEditor.textChanged.disconnect()
                        self.textEditor.clear()
                        for line in f.readlines():
                            self.textEditor.insertPlainText(line)
                        # self.macroFile = f
                        self._removeMacroFromCurrent()
                        self.filePath = filePath
                        self._preEditorText = self.textEditor.get()
                        self._lastTimestp = None
                        self._setCurrentMacro()
                        self._setFileName()
                        self.textEditor.textChanged.connect(self._textedChanged)
            else:
                MessageDialog.showMessage('Format Not Supported.', 'On MacroEditor you can only use a *.py file type')

    def revertChanges(self):
        self.textEditor.clear()
        self.textEditor.insertPlainText(self._preEditorText)

    def _textedChanged(self, *args):
        self.saveMacro()
        self.textEditor._on_text_changed()
        self._lastTimestp = os.stat(self.filePath).st_mtime

    def _focusInEvent(self, *ags):
        self._checkFileStauts(*ags)

    def _checkFileStauts(self, *args):
        nf = 'File not found. Deleted or renamed externally. It will be recreated automatically'
        if not os.path.exists(self.filePath):
            getLogger().warning(nf)
            self.saveMacro()
            return
        if self.filePath is None:
            getLogger().warning(nf)
            self.saveMacro()
            return
        if os.path.exists(self.filePath):
            now = os.stat(self.filePath).st_mtime
            kc = "Keep current version"
            sa = "Save as..."
            rf = "Reload file"
            if self._lastTimestp:
                if now != self._lastTimestp:
                    self._lastTimestp = now
                    reply = MessageDialog.showMulti(title='Warning', message='Detected an external change to the file.'
                                                    , texts=[kc, sa, rf])
                    if kc in reply:
                        self.saveMacro()
                    if sa in reply:
                        self.saveMacroAs()
                    if rf in reply:
                        self._removeMacroFromCurrent()
                        self.openPath(self.filePath)
                return

    def _getToolBarDefs(self):

        toolBarDefs = (
            ['Open', od([
                ['text', 'Open'],
                ['toolTip', 'Open a Python File'],
                ['icon', Icon('icons/document_open_recent')],
                ['callback', self._openMacroFile],
                ['enabled', True]
                ])],
            ['Export', od([
                ['text', 'Export'],
                ['toolTip', 'Export code to PDF'],
                ['icon', Icon('icons/pdf')],
                ['callback', self.exportToPdf],
                ['enabled', True]
                ])],
            ['Add to shortcut', od([
                ['text', 'Add to shortcut'],
                ['toolTip', 'Add macro to a shortcut'],
                ['icon', Icon('icons/shortcut')],
                ['callback', self._addToShortcuts],
                ['enabled', True]
                ])],
            (),
            ['Find', od([
                ['text', 'Find'],
                ['toolTip', ''],
                ['icon', Icon('icons/find')],
                ['callback', self._showFindWidgets],
                ['enabled', True]
                ])],
            ['Replace', od([
                ['text', 'Find and Replace'],
                ['toolTip', 'Find and Replace'],
                ['icon', Icon('icons/find-replace')],
                ['callback', self._showFindReplaceWidgets],
                ['enabled', True]
                ])],
            (),
            ['Undo', od([
                ['text', 'Undo'],
                ['toolTip', ''],
                ['icon', Icon('icons/undo')],
                ['callback', self.textEditor.undo],
                ['enabled', True]
                ])],
            ['Redo', od([
                ['text', 'Redo'],
                ['toolTip', ''],
                ['icon', Icon('icons/redo')],
                ['callback', self.textEditor.redo],
                ['enabled', True]
                ])],
            ['Revert', od([
                ['text', 'Revert'],
                ['toolTip', 'Revert all changes to initial state'],
                ['icon', Icon('icons/revert4')],
                ['callback', self.revertChanges],
                ['enabled', True]
                ])],
            (),
            ['Run', od([
                ['text', 'Run'],
                ['toolTip', 'Run the macro in the IpythonConsole.\nShortcut: cmd(ctrl)+r'],
                ['icon', Icon('icons/play')],
                ['callback', self.run],
                ['enabled', True],
                ['shortcut', '⌃r']
                ])],
            )
        return toolBarDefs

    def _showFindWidgets(self):
        if self.searchReplacePanel:
            self.searchReplacePanel.on_search()

    def _showFindReplaceWidgets(self):
        if self.searchReplacePanel:
            self.searchReplacePanel.on_search_and_replace()

    def _setToolBar(self):
        for v in self._getToolBarDefs():
            if len(v) == 2:
                if isinstance(v[1], od):
                    action = Action(self, **v[1])
                    action.setObjectName(v[0])
                    self.toolbar.addAction(action)
            else:
                self.toolbar.addSeparator()

    def _addToShortcuts(self):
        if self.application:
            from ccpn.ui.gui.popups.ShortcutsPopup import ShortcutsPopup

            sp = ShortcutsPopup(self, mainWindow=self.mainWindow)
            sp.shortcutWidget._addToFirstAvailableShortCut(self.filePath)
            sp.exec()
        else:
            MessageDialog.showMessage('Set shortcuts', 'This option is availble only within Analysis')

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        urls = data.get('urls', [])
        if len(urls) == 1:
            filePath = urls[0]
            if len(self.textEditor.get()) > 0:
                ok = MessageDialog.showYesNoWarning('Open new macro', 'Replace the current macro?')
                if ok:
                    if self.filePath != filePath:
                        self._removeMacroFromCurrent()
                        self._deleteTempFile()
                    self.openPath(filePath)
                    self._setFileName()
                else:
                    return
            else:
                if self.filePath != filePath:
                    self._removeMacroFromCurrent()
                    self._deleteTempFile()
                self.openPath(filePath)
                self._setFileName()
        else:
            MessageDialog.showMessage('', 'Drop only a file at the time')

    def _createTemporaryFile(self, name=None):
        if name is None:
            dateTime = datetime.datetime.now().strftime("%y-%m-%d-%H:%M:%S")
            tempName = 'Macro' + dateTime
            name = tempName
        filePath = self.application.tempMacrosPath + '/' + name
        if filePath:
            if not filePath.endswith('.py'):
                filePath += '.py'
            with open(filePath, 'w') as f:
                f.write('')
                f.close()
        self.filePath = filePath
        return filePath

    def _openTemp(self, path, line):
        """
        used for navigating to error in the macro.
        """
        editor = self.textEditor
        editor.file.restore_cursor = False
        editor.file.open(path)
        TextHelper(editor).goto_line(line)
        editor.show()
        self._editor_windows.append(editor)

    def _runOnTempIPythonConsole(self):
        console = PyInteractiveConsole()
        console.open_file_requested.connect(self._openTemp)
        console.start_process(sys.executable, [os.path.join(os.getcwd(), self.filePath)])
        console.show()

    def _openPythonConsoleModule(self):
        from ccpn.ui.gui.modules.PythonConsoleModule import PythonConsoleModule

        if self.mainWindow.pythonConsoleModule is None:  # No pythonConsole module detected, so create one.
            self.mainWindow.moduleArea.addModule(PythonConsoleModule(self.mainWindow), 'bottom')

    def _deleteTempMacro(self, filePath):
        if os.path.exists(filePath):
            os.remove(filePath)
            self.filePath = None
        else:
            getLogger().debug("Trying to remove a temporary Macro file which does not exist")

    def _saveTextToFile(self):
        filePath = self.filePath
        if filePath:
            if not filePath.endswith('.py'):
                filePath += '.py'
            with open(aPath(filePath), 'w') as f:
                f.write(self.textEditor.toPlainText())
                f.close()
        if self.filePath:
            self._lastSaved = self.textEditor.toPlainText()
            self._lastTimestp = os.stat(self.filePath).st_mtime
            self._setFileName()

    def _openMacroFile(self):
        """
        Opens a file dialog box at the macro path specified in the application preferences and loads the
        contents of the macro file into the textbox.
        """
        fType = '*.py'
        dialog = MacrosFileDialog(parent=self, acceptMode='open', directory=self.userMacroDirPath, fileFilter=fType)
        dialog._show()

        filePath = dialog.selectedFile()
        self.openPath(filePath)
        self._setFileName()

    def _setFileName(self):
        if self.filePath:
            self._filenameLineEdit.set(str(self.filePath))
            self.filePathLabel.set(str(self.filePath))

    def _isInCurrent(self, filePath):
        if self.current:
            if filePath in self.current.macroFiles:
                return True
        return False

    def _setCurrentMacro(self):
        if self.current:
            self.current.macroFiles += (self.filePath,)

    def _removeMacroFromCurrent(self):
        if self._isInCurrent(self.filePath):
            self.current.removeMacroFile(self.filePath)

    def _isDirty(self):

        if self._preEditorText != self.textEditor.get():
            if self._lastSaved == self.textEditor.get():
                return False
            return True
        return False

    def _deleteTempFile(self):
        if self._tempFile and self._tempFile.name == self.filePath:
            if self.textEditor.get() == '':  # delete empty temp
                if os.path.exists(self.filePath):
                    os.remove(self.filePath)

    def restoreWidgetsState(self, **widgetsState):
        """
        Restore the gui params. To Call it: _setParams(**{"variableName":"value"})
        :param widgetsState:
        """
        self._setNestedWidgetsAttrToModule()
        widgetsState = od(sorted(widgetsState.items()))
        for variableName, value in widgetsState.items():
            try:
                widget = getattr(self, str(variableName))
                if variableName == _filenameLineEdit:
                    if isinstance(widget, LineEdit):
                        if value is not None:
                            if self.filePath != value:
                                self._removeMacroFromCurrent()
                                self._deleteTempFile()
                            self.openPath(value)
                        continue
            except Exception as e:
                getLogger().debug('Impossible to restore %s value for %s. %s' % (variableName, self.name(), e))

    def _closeModule(self):
        """Re-implementation of closeModule  """
        if self._isDirty():
            ok = MessageDialog.showYesNoWarning('Close Macro', 'Do you want save?')
            if ok:
                self.saveMacro()
        self._deleteTempFile()
        self._removeMacroFromCurrent()
        super()._closeModule()


if __name__ == '__main__':
    from PyQt5 import QtGui, QtWidgets
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    from ccpn.ui.gui.widgets.CheckBox import EditableCheckBox, CheckBox


    app = TestApplication()
    win = QtWidgets.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None)
    tf = '/Users/luca/AnalysisV3/src/python/ccpn/ui/gui/widgets/TestModule.py'
    module = MacroEditor(mainWindow=None, filePath=None)

    moduleArea.addModule(module)

    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
    win.close()

    if sys.platform[:3].lower() == 'win':
        os._exit(0)
