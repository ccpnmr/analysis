from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.CcpnModule import CcpnModule


class CustomDevPlugin(Plugin):
  PLUGINNAME = 'Development Test Custom Gui'
  guiModule = CcpnModule

CustomDevPlugin.register() # Registers the pipe in the pluginList
