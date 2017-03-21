from ccpn.framework.lib.Plugin import Plugin

class NoUiDevPlugin(Plugin):
  PLUGINNAME = 'Development Plugin...No Ui'

  def run(self, **kwargs):
    print('Run', kwargs)
