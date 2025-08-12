
import sys
from ccpn.api import PluginBase, PluginBasePopup


class MyPopup(PluginBasePopup):

    title = 'My Demo Base Popup'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MyPopupPlugin(PluginBase):

    def __init__(self, descriptor, application, *args, **kwargs):
        super().__init__(descriptor, application)
        self.ui = MyPopup


