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
__dateModified__ = "$dateModified: 2020-06-09 01:56:08 +0100 (Tue, June 09, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import datetime
import os
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog, USERMACROSPATH
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.QPythonEditor import PyCodeEditor
from ccpn.framework.PathsAndUrls import macroPath
from pyqode.python.widgets import PyConsole, PyInteractiveConsole
import sys
from pyqode.core.api import TextHelper


class MacroEditor(CcpnModule):
    """
    Macro editor will run Python Files only.
    Other text files

    """
    includeSettingsWidget = False
    className = 'MacroEditor'

    def __init__(self, mainWindow=None, name='Macro Editor', filePath=None, useCcpnMacros=False):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        self.mainWindow = mainWindow
        self.application = None
        self.project = None
        self.current = None
        self.preferences = None
        self._pythonConsole = None
        self.macroPath = ''
        self._editor_windows = []

        if self.mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            self.preferences = self.application.preferences
            self._pythonConsole = self.mainWindow.pythonConsole
            if self._pythonConsole is None:
                self._pythonConsole = IpythonConsole(self.mainWindow)

        self._DIALOGID = USERMACROSPATH
        if useCcpnMacros:
            self.macroPath = macroPath
        else:
            if self.preferences:
                self.macroPath = self.preferences.general.userMacroPath

        self._isTempMacro = True
        self._originalOpenedFile = None

        self.mainWidget.layout().setSpacing(5)
        self.mainWidget.layout().setContentsMargins(10, 10, 10, 10)

        hGrid = 0

        self.namelabel = Label(self.mainWidget, 'Macro Name', grid=(hGrid, 0))
        self.nameLineEdit = LineEdit(self.mainWidget, grid=(0, 1))
        # self.nameLineEdit.editingFinished().connect(self._changedName)

        hGrid += 1
        # macro editing area
        self.textEditor = PyCodeEditor(self.mainWidget, grid=(hGrid, 0), acceptDrops=True, gridSpan=(1, 2))

        hGrid += 1
        self.buttonBox = ButtonList(self, texts=['Open', 'save', 'Save As', 'Run'],
                                    callbacks=[self._openMacroFile, self._saveMacro, self._saveMacroAs, self._runMacro], grid=(hGrid, 1))

        self.filePath = filePath
        if self.filePath:  # if  a path is specified then opens it
            self._openPath(self.filePath)

        self._setFileName(self.filePath)

        # self.textEditor.editingFinished.connect(self._saveMacro)  # automatic saving
        # self.nameLineEdit.editingFinished.connect(self._macroNameChanged)  # automatic renaming the fileName

        self.droppedNotifier = GuiNotifier(self.textEditor,
                                           [GuiNotifier.DROPEVENT], [DropBase.URLS],
                                           self._processDroppedItems)

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
                    self._openPath(filePath)
                    self._setFileName(filePath)
                else:
                    return
            else:
                self._openPath(filePath)
                self._setFileName(filePath)
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

    def _openEditor(self, path, line):
        '''
        used for navigating to error in the macro.
        '''
        editor = self.textEditor
        editor.file.restore_cursor = False
        editor.file.open(path)
        TextHelper(editor).goto_line(line)
        editor.show()
        self._editor_windows.append(editor)

    def _runOnTempIPythonConsole(self):
        console = PyInteractiveConsole()
        console.open_file_requested.connect(self._openEditor)
        console.start_process(sys.executable, [os.path.join(os.getcwd(), self.filePath)])
        console.show()

    def _runMacro(self):
        if self._pythonConsole is not None:
            if self.filePath:
                # self._pythonConsole._runMacro(self.filePath)
                if not self.filePath in self.preferences.recentMacros and not self._isTempMacro:
                    self.preferences.recentMacros.append(self.filePath)

            self.filePath = self._createTemporaryFile()
            self._saveTextToFile(self.filePath)
            self._pythonConsole._runMacro(self.filePath)
            self._deleteTempMacro(self.filePath)
        else:
            # Used when running the editor outiside of Analyis. Run from an external IpythonConsole
            self._runOnTempIPythonConsole()

    def _saveMacro(self):
        """
        Saves the text inside the textbox to a file, if a file path is not specified, a save file dialog
        appears for specification of the file path.
        """

        if not self.filePath:
            self._saveMacroAs()

        if self._originalOpenedFile:
            if self._getFileNameFromPath(self._originalOpenedFile) != self.nameLineEdit.get():
                self._saveMacroAs()
            else:
                self._saveTextToFile(self._originalOpenedFile)

    def _macroNameChanged(self):
        if self.filePath:
            if self.nameLineEdit.get() != '':
                self.filePath = self.filePath.replace(self._getFileNameFromPath(self.filePath), self.nameLineEdit.get())
                self._saveMacro()

    def _deleteTempMacro(self, filePath):
        if os.path.exists(filePath):
            os.remove(filePath)
            self.filePath = None
        else:
            getLogger().debug("Trying to remove a temporary Macro file which does not exist")

    def saveToPdf(self):
        self.textEditor.saveToPDF()

    def _saveTextToFile(self, filePath):
        if filePath:
            with open(filePath, 'w') as f:
                f.write(self.textEditor.toPlainText())
                f.close()

    def _saveMacroAs(self):
        """
        Opens a save file dialog and saves the text inside the textbox to a file specified in the dialog.
        """

        newText = self.textEditor.toPlainText()
        dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                            acceptMode=FileDialog.AcceptSave, selectFile=self.nameLineEdit.text(),
                            # directory=self.macroPath,
                            filter='*.py',
                            preferences=self.preferences,
                            initialPath=self.macroPath,
                            pathID=self._DIALOGID)
        dialog._show()
        filePath = dialog.selectedFile()

        if filePath:
            if not filePath.endswith('.py'):
                filePath += '.py'
            with open(filePath, 'w') as f:
                f.write(newText)
                f.close()

        if filePath:
            self.nameLineEdit.set(self._getFileNameFromPath(filePath))
            self.filePath = filePath

    def _openMacroFile(self):
        """
        Opens a file dialog box at the macro path specified in the application preferences and loads the
        contents of the macro file into the textbox.
        """

        dialog = FileDialog(self, text='Open Macro', fileMode=FileDialog.ExistingFile,
                            acceptMode=FileDialog.AcceptOpen,
                            # directory=self.macroPath,
                            filter='*.py',
                            preferences=self.preferences,
                            initialPath=self.macroPath,
                            pathID=self._DIALOGID)
        dialog._show()
        filePath = dialog.selectedFile()
        self._openPath(filePath)
        self._setFileName(filePath)

    def _openPath(self, filePath):

        if filePath:
            if filePath.endswith('.py'):
                with open(filePath, 'r') as f:
                    self.textEditor.clear()
                    for line in f.readlines():
                        self.textEditor.insertPlainText(line)
                    self.macroFile = f
                    self.filePath = filePath
                    self._originalOpenedFile = filePath
                    self._isTempMacro = False
            else:
                MessageDialog.showMessage('Format Not Supported.', 'On MacroEditor you can only use a *.py file type')

    def _setFileName(self, filePath):

        fileName = self._getFileNameFromPath(filePath)
        self.nameLineEdit.set(str(fileName))

    def _getFileNameFromPath(self, filePath):
        if isinstance(filePath, str):
            if filePath.endswith('.py'):
                path = filePath.split('/')
                fileName = path[-1].split('.')[0]
                return fileName

    def _closeModule(self):
        """Re-implementation of closeModule  """
        ok = MessageDialog.showYesNoWarning('Close Macro', 'Do you want save?')
        if ok:
            self._saveMacro()

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
    module = MacroEditor(mainWindow=None, filePath=tf)

    moduleArea.addModule(module)

    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
    win.close()
