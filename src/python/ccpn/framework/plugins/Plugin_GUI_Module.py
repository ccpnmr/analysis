from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.framework.Application import getApplication, getMainWindow, getCurrent, getProject


class PluginGUIModule(CcpnModule):
    maxSettingsState = 2
    settingsPosition = 'top'


    includeSettingsWidget = True

    def __init__(self, plugin, **kwargs):
            self.plugin = plugin
            self.mainWindow = getMainWindow()
            self.project = getProject()
            self.application = getApplication()
            self.current = getCurrent()
            super().__init__(mainWindow=self.mainWindow, name=self.plugin.name)


    def _closeModule(self):
        self.plugin.close()
        super()._closeModule()