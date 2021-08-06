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
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-04 12:07:37 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.Font import setWidgetFont, getFont, CONSOLEFONT
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Splitter import Splitter
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from ccpn.util.Logging import getLogger
from ccpn.util.Common import isWindowsOS


class IpythonConsole(Widget):
    focusedIn = QtCore.pyqtSignal(QtGui.QFocusEvent)
    mouseMoved = QtCore.pyqtSignal(QtGui.QMouseEvent)

    def __init__(self, mainWindow, namespace=None, **kwds):

        if namespace is None:
            namespace = mainWindow.namespace

        super().__init__(parent=mainWindow, setLayout=True, **kwds)
        # Base._init(self, setLayout=True, **kwds)

        # NOTE:ED - check that this is working for Linux/MacOS
        if isWindowsOS():
            import asyncio

            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        km = QtInProcessKernelManager()
        km.start_kernel()
        km.kernel.gui = 'qt4'
        self.mainWindow = mainWindow
        self.mainWindow.pythonConsole = self
        self.ipythonWidget = RichJupyterWidget(self, gui_completion='plain')
        self.setStyleSheet(self.mainWindow.styleSheet())

        self.ipythonWidget.kernel_manager = km
        self.setMinimumHeight(100)
        self.textEditor = TextEditor(self)
        self.textEditor.setReadOnly(True)
        setWidgetFont(self.textEditor, CONSOLEFONT)
        # if this is called here then keyboard input gets
        # sucked into Python console even if it is not opened
        # so instead call _startChannels() when opened
        ###self.ipythonWidget.kernel_client.start_channels()

        self.getLayout().setSpacing(1)

        # self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter = Splitter(horizontal=False)
        self.splitter.addWidget(self.textEditor)

        self.consoleFrame = Frame(self, setLayout=True, margins=(1, 1, 1, 1), spacing=(0, 0))
        self.splitter.addWidget(self.consoleFrame)
        # self.consoleFrame.addLayout(consoleLayout, 1, 0)
        # self.consoleFrame.addLayout(buttonLayout, 2, 0)

        self.consoleFrame.layout().addWidget(self.ipythonWidget, 0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        # self.splitter.setStyleSheet("QSplitter::handle { background-color: gray }")

        self.getLayout().addWidget(self.splitter)
        namespace['runMacro'] = self._runMacro
        km.kernel.shell.push(namespace)

        _font = getFont(name=CONSOLEFONT)
        self.ipythonWidget.setStyleSheet(f'font-family: {_font.fontName}; font-size: {_font.pointSize()}pt;')

        self._startChannels()  # this is important, otherwise the console doesn't run anything

        # hide this widget, it may be visible before the pythonConsoleModule has been instantiated
        self.hide()

    def setProject(self, project):
        self.project = project

    def _runMacro(self, macroFile: str):
        """
        # CCPN INTERNAL - called in runMacro method of GuiMainWindow.
        Executes the specified macro file in the python console.
        """
        if macroFile:
            self.ipythonWidget.execute('%run -i {}'.format(macroFile))

        try:
            self.mainWindow._fillRecentMacrosMenu()
        except Exception as e:
            getLogger().debug('Impossible to fill the menus with recent macros %s' % e)

    def _runMacroProfiler(self, macroFile: str, extraCommands):
        """
        # CCPN INTERNAL - called in runMacro method of GuiMainWindow.
        Executes the specified macro file in the python console with a profiler.
        Execute the command: %run -p [prof_opts] filename.py [args to program]
        see https://ipython.readthedocs.io/en/stable/interactive/magics.html for more info
        """
        if macroFile:
            self.ipythonWidget.execute(f'%run {" ".join(extraCommands)} {macroFile}')
        try:
            self.mainWindow._fillRecentMacrosMenu()
        except Exception as e:
            getLogger().debug('Impossible to fill the menus with recent macros %s' % e)

    def _startChannels(self):
        """
        # CCPN INTERNAL - called in constructor of PythonConsoleModule.
        """
        self.ipythonWidget.kernel_client = self.ipythonWidget.kernel_manager.client()
        self.ipythonWidget.kernel_client.start_channels()

    def _stopChannels(self):
        """
        # CCPN INTERNAL - called in constructor of PythonConsoleModule.
        """
        self.ipythonWidget.kernel_client.stop_channels()
        self.ipythonWidget.kernel_client = None

    def _showHistory(self):
        """
        Shows the history of commands executed inside the python console.
        """
        self.ipythonWidget.execute('%history')

    def _write(self, msg: str = None, html=False):
        """
        writes the specified string to the python console text box.
        """
        try:
            self.textEditor.moveCursor(QtGui.QTextCursor.End)
            if html:
                self.textEditor.textCursor().insertHtml(msg)
            else:
                self.textEditor.insertPlainText(msg)
                self.mainWindow.statusBar().showMessage(msg)

        except Exception as e:
            getLogger().warning('Error on IpythonConsole: %s' % e)

    def _setUndoWaypoint(self):
        """Set Undo waypoint, if undo is present"""
        if hasattr(self, 'project'):
            undo = self.project._undo
            if undo is not None:
                self.project.newUndoPoint()

    def writeConsoleCommand(self, command: str, **objectParameters):
        """Set keyword:value objectParameters to point to the relevant objects,
        echo command in console, and set Undo

        Example calls:

        writeConsoleCommand("application.createSpectrumDisplay(spectrum)", spectrum=spectrumOrPid)

        writeConsoleCommand(
           "newAssignment = peak.assignDimension(axisCode=%s, value=[newNmrAtom]" % axisCode,
           peak=peakOrPid)
        """

        # write lines getting objects by their Pids

        for parameter in sorted(objectParameters):
            value = objectParameters[parameter]
            if not isinstance(value, str):
                value = value.pid
            self._write("%s = project.getByPid('%s')\n" % (parameter, value))

        # execute command
        self._write(msg=command + '\n')  # ED: newLine IS needed here

        # set undo step
        self._setUndoWaypoint()
