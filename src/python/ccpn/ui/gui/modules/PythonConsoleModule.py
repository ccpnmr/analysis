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
__modifiedBy__ = "$modifiedBy: Luca $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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


class PythonConsoleModule(CcpnModule):
    """
    This class implements the module by wrapping a PeakListTable instance
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

        self.settingsEditorCheckBox = CheckBox(self.settingsWidget, checked=True, text='Log Display', callback=self._toggleTextEditor,
                                               grid=(0, 0))

        # make the widget visible, it is hidden when first instantiated
        self.pythonConsoleWidget.show()

    def _toggleTextEditor(self, value):
        if value:
            self.pythonConsoleWidget.textEditor.show()
        else:
            self.pythonConsoleWidget.textEditor.hide()

    def _closeModule(self):
        # self.pythonConsoleWidget._stopChannels()
        self.mainWindow.pythonConsoleModule = None
        if self._menuAction:
            self._menuAction.setChecked(False)
        super(PythonConsoleModule, self)._closeModule()
