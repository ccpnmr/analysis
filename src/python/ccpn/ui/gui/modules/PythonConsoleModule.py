"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca $"
__date__ = "$Date: 2017-05-10 16:04:41 +0000 (Wed, May 10, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.util.Logging import getLogger


class PythonConsoleModule(CcpnModule):
    """
    Gui module to display the Ipyhton console within the program
    """

    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'PythonConsoleModule'

    def __init__(self, mainWindow, name='Python Console', closeFunc=None, **kwds):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name, closeFunc=closeFunc)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.pythonConsoleWidget = self.mainWindow.pythonConsole
        if self.pythonConsoleWidget is None:  # For some reason it can get destroid!
            self.mainWindow.pythonConsole = self.pythonConsoleWidget = IpythonConsole(self)
        self.mainWidget.getLayout().addWidget(self.pythonConsoleWidget)

        self.pythonConsoleWidget._startChannels()
        self.mainWindow.pythonConsoleModule = self
        self._menuAction = self.mainWindow._findMenuAction('View', 'Python Console')
        if self._menuAction:
            self._menuAction.setChecked(True)

        row = 0
        self.settingsEditorCheckBox = CheckBox(self.settingsWidget, checked=True, text='Show logging window', callback=self._toggleTextEditor,
                                               grid=(row, 0))
        # self._toggleTextEditor(False)

        row += 1
        self.settingsLoggingCheckBox = CheckBox(self.settingsWidget, checked=True, text='Enable logging', callback=self._toggleLogging,
                                               grid=(row, 0))

        # make the widget visible, it is hidden when first instantiated
        self.pythonConsoleWidget.show()
        self._toggleTextEditor(True)

    def _toggleTextEditor(self, isVisible):
        """Show/hide the logging window in the python console
        """
        try:
            if isVisible:
                self.pythonConsoleWidget.textEditor.show()
            else:
                self.pythonConsoleWidget.textEditor.hide()
        except RuntimeError as runError:
            getLogger().warning('PythonConsole module Error: %s'%runError)

    def _toggleLogging(self, value):
        """Enable/disable logging to the logging window of the python console
        """
        self.application._enableLoggingToConsole = value

    def enterEvent(self, event):
        # do nothing. Just keep the event.
        event.accept()
        # don't call super or you lose the cursor while typing, even when casually the mouse cursor
        # is on top of the inline documentation. Which is annoying and unproductive.

    def leaveEvent(self, event):
        # do nothing. Just keep the event.
        event.accept()
        # don't call super or you lose the cursor while typing, even when casually the mouse cursor
        # is on top of the inline documentation. Which is annoying and unproductive.

    def _closeModule(self):
        # self.pythonConsoleWidget._stopChannels()
        self.mainWindow.pythonConsoleModule = None
        if self._menuAction:
            self._menuAction.setChecked(False)
        super(PythonConsoleModule, self)._closeModule()
