from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget

class PluginBasePopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'Demo Base Popup'

    def __init__(self, plugin, **kwargs):
        self.plugin = plugin
        super().__init__(None, windowTitle=plugin.name,  setLayout=True,  **kwargs)

