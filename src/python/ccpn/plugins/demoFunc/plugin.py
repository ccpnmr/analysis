


def run():

    from ccpn.api import getApplication, getLogger
    getLogger().info(f'\n Running my Plugin {__name__} \n')
    if application := getApplication():
        userName = application.getRegistrationDetails().get('name')
        if mainWindow := application.mainWindow:
            mainWindow.statusBar().showMessage(f"Hello {userName}", 10000)

