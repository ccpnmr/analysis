


def run():
    """
    Example entry point for a demo plugin.

    This function is automatically loaded when the program starts.
    To invoke it manually from the console: Main Menu > View > Python Console, type

        >>> from demoFunc.plugin import run
        >>> run()

    When executed, a message will appear in the MainWindow status bar.

    :return: None
    """
    from ccpn.api import getApplication, getLogger
    getLogger().info(f'\n Running my Plugin {__name__} \n')
    if application := getApplication():
        userName = application.getRegistrationDetails().get('name')
        if mainWindow := application.mainWindow:
            mainWindow.statusBar().showMessage(f"Hello {userName}", 10000)

