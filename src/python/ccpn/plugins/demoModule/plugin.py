
from ccpn.api import PluginBase, PluginGUIModule
from collections import OrderedDict as od
import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget

SettingsWidgetFixedWidths = (200, 350, 350)

SOURCE_PEAKLIST = 'SOURCE_PEAKLIST'
RUN_BUTTON = 'RUN_BUTTON'


class DemoGuiModule(PluginGUIModule):


    def getWidgetDefinitions(self) :

        self.widgetDefinitions = od((
            (SOURCE_PEAKLIST,
             {'label': 'PeakList',
              'tipText': 'Select a PeakList',
              'callBack': None,
              'type': objectPulldowns.PeakListPulldown,
              'kwds': {'labelText': 'PeakList',
                       'tipText': 'Select a PeakList',
                       'filterFunction': None,
                       'showSelectName':True,
                       'objectName': SOURCE_PEAKLIST,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (RUN_BUTTON,
             {'label'   : 'Run The Plugin',
              'tipText' : 'Run The Plugin',
              'callBack': self._runCallback,
              'type'    : compoundWidget.ButtonCompoundWidget,
              '_init'   : None,
              'kwds'    : {'labelText'  : 'Run',
                           'text'       : 'Execute',  # this is the Button name
                           'hAlign'     : 'left',
                           'tipText'    : 'Run The Plugin',
                           'fixedWidths': SettingsWidgetFixedWidths}}),
            ))
        return self.widgetDefinitions



class MyCcpnModule(PluginBase):
    def __init__(self,  descriptor, application):
        super().__init__(descriptor, application)
        self.ui = DemoGuiModule

    def run(self, *args, **kwargs):
        print('KW', kwargs)