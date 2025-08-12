from ccpn.framework.lib.Plugin import Plugin

class NoUiDevPlugin(Plugin):
  PLUGINNAME = 'Development Test No Ui'

  def run(self):
    print('Run')

NoUiDevPlugin.register() # Registers the pipe in the pluginList
