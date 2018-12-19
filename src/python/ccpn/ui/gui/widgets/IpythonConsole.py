"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.guiSettings import fixedWidthFont

from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from ccpn.util.Logging import getLogger


class IpythonConsole(Widget):

    def __init__(self, mainWindow, namespace=None, **kwds):

        if namespace is None:
            namespace = mainWindow.namespace

        super().__init__(parent=mainWindow, setLayout=True, **kwds)
        # Base._init(self, setLayout=True, **kwds)

        km = QtInProcessKernelManager()
        km.start_kernel()
        km.kernel.gui = 'qt4'

        self.mainWindow = mainWindow
        self.mainWindow.pythonConsole = self

        self.ipythonWidget = RichJupyterWidget(self, gui_completion='plain')
        #TODO:GEERTEN: Sort Stylesheet issues
        self.setStyleSheet(self.mainWindow.styleSheet())
        self.ipythonWidget._set_font(fixedWidthFont)
        self.ipythonWidget.kernel_manager = km
        # self.ipythonWidget.kernel_client = km.client()
        #TODO:LUCA:The Widget class already has a layout: can just do grid=(row,col)
        #use getLayout() of the widget class to get hold of the widget layout in case you need to do something special

        self.setMinimumHeight(100)

        self.textEditor = TextEditor(self)
        self.textEditor.setReadOnly(True)
        # if this is called here then keyboard input gets
        # sucked into Python console even if it is not opened
        # so instead call _startChannels() when opened
        ###self.ipythonWidget.kernel_client.start_channels()

        self.getLayout().setSpacing(1)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.textEditor)

        self.consoleFrame = Frame(self, setLayout=True)
        self.splitter.addWidget(self.consoleFrame)
        # self.consoleFrame.addLayout(consoleLayout, 1, 0)
        # self.consoleFrame.addLayout(buttonLayout, 2, 0)

        self.consoleFrame.layout().addWidget(self.ipythonWidget, 0, 0)

        # runMacroButton = QtWidgets.QPushButton()
        # runMacroButton.clicked.connect(self._runMacro)
        # runMacroButton.setText('Run Macro')
        # buttonLayout.addWidget(runMacroButton)
        #
        # historyButton = QtWidgets.QPushButton()
        # historyButton.clicked.connect(self._showHistory)
        # historyButton.setText('Show History')
        # buttonLayout.addWidget(historyButton, 0, 1)

        # THIS Buttons are broken. There is actually no reason to have a run macro here.
        # We have the full menu menu item for macros!
        # self.buttons = ButtonList(self.consoleFrame,
        #                         texts=['Open Macro', 'Show History'],
        #                         callbacks=[self._runMacro, self._showHistory],
        #                         direction='H', hAlign='c',
        #                         grid=(1,0))

        self.splitter.setStretchFactor(1, 8)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: gray }")
        self.getLayout().addWidget(self.splitter)

        namespace['runMacro'] = self._runMacro
        km.kernel.shell.push(namespace)

        self._startChannels()  # this is important, otherwise the console does't run anything

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
                # self.textEditor.textCursor().insertHtml("</div><br><div style='font-weight: normal; background-color: #FFF;'>")
                self.textEditor.insertPlainText(msg)
                # self.textEditor.insertPlainText('\n')
                self.mainWindow.statusBar().showMessage(msg)
            if self.mainWindow.recordingMacro is True:
                try:
                    self.mainWindow.editor.textBox.insertPlainText(msg)
                except:
                    getLogger().warning('Warning: macro editor does not exist')
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
