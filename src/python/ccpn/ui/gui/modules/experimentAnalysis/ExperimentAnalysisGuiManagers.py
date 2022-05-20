#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-05-20 18:40:05 +0100 (Fri, May 20, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import weakref
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel, _panelPositionsAttr
from ccpn.ui.gui.widgets.Tabs import Tabs

class ExperimentAnalysisManager(object):
    """
    This object manages a dedicated part of a ExperimentAnalysis GuiModule instance:
        - backend management (ExperimentAnalysis base class)
        - settings management
        - panels management (tables, plotting etc)
        - file manager (I/O)

    Managers are created internally when you create a ExperimentAnalysis GuiModule.
    You interact with them later, e.g. when you want to start the backend
    process or when you want to install/retrieve a mode or a panel.

    ::
        ea = ExperimentAnalysis()

        # use the backend manager to start the backend server
        ea.backend.start(...)
        ea.backend.calculate(...)

        # use the panels controller to install a panel
        ea.panels.install(MyPanel(), MyPanel.Position.Right)
        panel = editor.panels.get(MyPanel)
        # and so on

    """

    @property
    def guiModule(self):
        """
        Return a reference to the parent code edit widget.
        """
        return self._guiModule

    def __init__(self, guiModule):
        """
        :param guiModule: The GuiModule instance to control
        """
        self._guiModule = guiModule


class PanelsManager(ExperimentAnalysisManager):
    """
    Manages the list of panels and adds them to the GuiModule.
    """
    def __init__(self, guiModule):
        super(PanelsManager, self).__init__(guiModule)
        self._marginSizes = (0, 0, 0, 0)

        for position in _panelPositionsAttr:
            setattr(self, position, -1)
        self._panels = {k:{} for k in GuiPanel.PanelPosition.values()}

    def _updateViewport(self):
        pass

    def _update(self):
        pass

    def append(self, panel, position=GuiPanel.PanelPosition.LEFT):
        """
        Installs a panel on the editor.

        :param panel: Panel to install
        :param position: Position where the panel must be installed.
        :return: The installed panel
        """

        # panel.order_in_zone = len(self._panels[position])

        self._panels[position][panel.name] = panel
        panel.position = position
        panel.onInstall()
        return panel

    def remove(self, name_or_klass):
        """
        Removes the specified panel.

        :param name_or_klass: Name or class of the panel to remove.
        :return: The removed panel
        """
        panel = self.get(name_or_klass)
        panel.on_uninstall()
        panel.hide()
        panel.setParent(None)
        return self._panels[panel.position].pop(panel.name, None)

    def clear(self):
        """
        Removes all panel from the Module.
        """
        pass

    def get(self, name_or_klass):
        """
        Gets a specific panel instance.

        :param name_or_klass: Name or class of the panel to retrieve.
        :return: The specified panel instance.
        """
        if not isinstance(name_or_klass, str):
            name_or_klass = name_or_klass.__name__
        for zone in range(4):
            try:
                panel = self._panels[zone][name_or_klass]
            except KeyError:
                pass
            else:
                return panel
        raise KeyError(name_or_klass)

    def __iter__(self):
        lst = []
        for zone, zone_dict in self._panels.items():
            for name, panel in zone_dict.items():
                lst.append(panel)
        return iter(lst)

    def __len__(self):
        lst = []
        for zone, zone_dict in self._panels.items():
            for name, panel in zone_dict.items():
                lst.append(panel)
        return len(lst)



class SettingsPanelManager(ExperimentAnalysisManager):
    """
    Manages the list of Tab settings and adds them to the GuiModule settingsWidget.
    """
    def __init__(self, guiModule):
        super(SettingsPanelManager, self).__init__(guiModule)
        self._marginSizes = (5, 5, 5, 5)
        self._panels = {}
        self.settingsWidget = self.guiModule.settingsWidget
        self.settingsWidget.setContentsMargins(*self._marginSizes)
        self.settingsTabWidget = Tabs(self.settingsWidget, setLayout=True, grid=(0, 0))

    def append(self, panel):
        # add tab to gui
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel import GuiSettingPanel
        if not isinstance(panel, GuiSettingPanel):
            raise RuntimeError(f'{panel} is not of instance: {GuiSettingPanel}')
        self.settingsTabWidget.insertTab(panel.tabPosition, panel, panel.tabName)
        self._panels.update({panel.tabPosition:panel})
