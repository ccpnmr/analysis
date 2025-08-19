
import sys
from ccpn.api import PluginBase, PluginBasePopup


class MyPopup(PluginBasePopup):
    """
    Popup-based GUI implementation of the plugin.

    Inherits from `PluginBasePopup`. Subclasses can override base
    methods to customise behaviour — for example:
      • Creating and arranging custom widgets
      • Intercepting `runCallback` to add error checking or extra logic

    See the base class for a full list of extension points.
    """

    title = 'My Demo Base Popup'


class MyPopupPlugin(PluginBase):

    def __init__(self, descriptor, application, *args, **kwargs):
        """
                Plugin initialisation. Called automatically by the PluginManager.

                Framework-provided arguments:
                      :param descriptor: Metadata object describing the plugin (name, version, entry point, etc.).
                      :param application: Reference to the main application instance, used to access
                                          shared services such as project data, managers, and configuration.
                Notes:
                  - These parameters are injected by the plugin manager and are not intended to be supplied by end users.

                subclass the Init if you want to add custom logics.

                See the base class for a full list of extension points and/or other plugins for examples.
                """
        super().__init__(descriptor, application)
        self.ui = MyPopup


    def run(self, *args, **kwargs):
        """
        Default entry point for executing a plugin action.
        This method is called automatically when the user clicks *Run* in the plugin’s GUI if there is a GUI element.
        By default this method does nothing. Subclasses should override it
        to implement the plugin’s behaviour. Typical uses include:

          • Running an external command or script via the provided process runner
          • Attaching a file watcher to monitor results and feed them back into the project
          • Performing a direct action on the current project (e.g. adding, updating, or analysing data)

        The keyword arguments (`kwargs`) are automatically populated from
        the plugin’s GUI layer, based on the widgets defined in
        `getWidgetDefinitions()`. Each widget contributes its value under
        the symbolic name you assigned there.
        """
        sys.stdout.write(f"\n Run method called with arguments: {kwargs}")