"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2025-08-12 19:40:42 +0100 (Tue, August 12, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Any, Optional, Iterable
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.CcpNmrTraits import Unicode, Dict, List, Bool, Int, Float
from ccpn.framework.plugins import pluginNamespaces as pluginVariables
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger



class PluginBase(TraitBase):
    """
        Base class for all CcpNmr plugins.

        This class provides:
          • A handle to the plugin's **descriptor** (metadata parsed from `plugin_descriptor.json`)
          • A clean runtime API (initialise, shutdown, run) with sensible defaults
          • Optional integration with a UI delegate (`plugin.ui`)

        ────────────────────────────────────────────────────────────────
        HOW TO USE
        ────────────────────────────────────────────────────────────────
        1. **Subclass PluginBase**
           Create your own subclass and override at least one of:
             • `run(self, **kwargs)` – main action logic
             • `initialise(self)` – prepare state/resources when plugin is loaded
             • `shutdown(self)` – clean up before unload

        2. **Access metadata**
           Your plugin automatically has read-only properties from its descriptor:
             • `self.name` – unique plugin name
             • `self.version` – version string
             • `self.author` – author name
             • `self.entryPoint` – dotted import path to callable/module
             • `self.enabledByDefault` – boolean flag from descriptor
             • `self.loadLevel` – 'startup', 'ui', or 'onDemand'

           These values come from the plugin’s `plugin_descriptor.json` file.

        3. **Optional UI**
           If your plugin needs a GUI:
             • Set `self.ui` to a GUI delegate object with a `.show(parent)` method.
             • The application will create and attach this delegate when the UI is ready.
             • You can supply your own UI factory or let the system build one automatically.

        4. **Lifecycle**
           • The PluginManager instantiates your plugin with:
                 PluginBase(descriptor, application)
             `application` is a handle to the host app/context (optional).
           • Plugins are loaded according to `loadLevel` and user preferences.
           • `initialise()` is called when the plugin becomes active.
           • `shutdown()` is called before it is unloaded.

        5. **Example**
           ```python
           from ccpn.framework.plugins.PluginBase import PluginBase

           class MyPlugin(PluginBase):
               def run(self, **kwargs):
                   print(f"{self.name} running with {kwargs}")
           ```

        ────────────────────────────────────────────────────────────────
        Notes:
           • Keep `PluginBase` subclasses headless (no Qt imports); put UI code in a separate delegate.
           • Traitlets in your subclass automatically become configurable UI fields (if UI). Use _ (underscore) to don't show on UI
           • The PluginManager controls when your plugin is loaded/unloaded; do not import it directly.
        """

    classVersion = 1.0

    def __init__(self, descriptor, application) -> None:
        super().__init__()
        self._descriptor = descriptor
        self.application = application
        self.ui = None

    # explicit core fields
    @property
    def name(self) -> str:
        return self._descriptor.name

    @property
    def version(self) -> str:
        return self._descriptor.version

    @property
    def author(self) -> str:
        return self._descriptor.author

    @property
    def entryPoint(self) -> str:
        return self._descriptor.entryPoint

    @property
    def enabledByDefault(self) -> bool:
        return self._descriptor.enabledByDefault

    @property
    def loadLevel(self) -> int:
        return self._descriptor.loadLevel

    # ~~~~~ lifecycle hooks ~~~~~~

    def buildGUI(self):
        pass

    def show(self) -> None:
        from ccpn.framework.plugins.Plugin_GUI_Module import PluginGUIModule
        from ccpn.framework.plugins.Plugin_GUI_Popup import PluginBasePopup

        from ccpn.framework.Application import getMainWindow
        if self.ui is None:
            return

        if issubclass(self.ui, PluginGUIModule):
            mainWindow = getMainWindow()
            guiModule = self.ui(self)
            mainWindow.moduleArea.addModule(guiModule)

        if issubclass(self.ui, PluginBasePopup):
            popup = self.ui(self)
            popup.show()
            popup.raise_()

    def close(self) -> None:
        pass

    # ~~~~~ main action ~~~~~~

    def run(self, **kwargs: Any) -> Optional[Any]:
        return None

    # ~~~~~ internals ~~~~~~

    # descriptor fallback
    def __getattr__(self, name: str) -> Any:
        if hasattr(self._descriptor, name):
            return getattr(self._descriptor, name)
        raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")


    # read-only guard for descriptor-backed attrs
    def __setattr__(self, name: str, value: Any) -> None:
        # allow internal/private + during early init
        if name.startswith("_") or not hasattr(self, "_descriptor"):
            return object.__setattr__(self, name, value)

        # block writes to any attribute that exists on the descriptor
        if hasattr(self._descriptor, name):
            raise AttributeError(f"'{name}' is read-only (provided by PluginDescriptor)")

        # otherwise normal set (traits, runtime state, etc.)
        return object.__setattr__(self, name, value)

