
import sys
from ccpn.api import PluginBase, PluginGUIModule


class DemoGuiModule(PluginGUIModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class MyCcpnModule(PluginBase):
    def __init__(self,  descriptor, application):
        super().__init__(descriptor, application)
        self.ui = DemoGuiModule

