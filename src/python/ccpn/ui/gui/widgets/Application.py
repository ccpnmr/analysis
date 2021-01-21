"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-21 17:13:43 +0000 (Thu, January 21, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtGui, QtWidgets


class Application(QtWidgets.QApplication):

    def __init__(self, applicationName, applicationVersion, organizationName='CCPN', organizationDomain='ccpn.ac.uk'):
        super().__init__([applicationName, ])

        self.setApplicationVersion(applicationVersion)
        self.setOrganizationName(organizationName)
        self.setOrganizationDomain(organizationDomain)

    def start(self):
        self.exec_()


class TestApplication(Application):

    def __init__(self):
        Application.__init__(self, 'testApplication', '1.0')


def newTestApplication(projectPath=None, useTestProjects=False,
                       nologging=False, interface='NoUi', debug=True,
                       noApplication=False):
    """Create a full application for testing.
    This will contain an empty project and preferences.

    If interface is specified as 'NoUi' no mainWindow will be created,
    but a full application and project will be created.

    if interface is specified as 'Gui' a mainWindow will be created,
    but the event execution loop will not be started.

    Popups can be instantiated with exec_ which will automatically show the mainWindow.

    The mainWindow can be instantiated manually with app.start(); however, any code after this cannot be guaranteed to
    run after closing mainWindow.

    Set noApplication=True for a basic test that only creates a QApplication; a Ccpn application will not be created.

    :param projectPath: str or Path object, path of project to load on startup
    :param useTestProjects: bool, True uses the Ccpn testing folder as the root for the project to load
    :param nologging: bool, enable or disable lopgging
    :param interface: 'NoUi' or 'Gui', determines whether mainWindow is created
    :param debug: bool, enable/disable debugging
    :param noApplication: bool, enable/disable creation of CCpn application
    :return: instance of new application
    """
    app = None

    def _makeApp():
        # create a new application
        _app = TestApplication()
        _app.colourScheme = 'light'

        return _app

    # don't create anything else - for the fastest testing
    if noApplication:
        return _makeApp()

    from ccpn.framework import Framework
    from ccpn.util.Path import Path, aPath
    from ccpnmodel.ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH

    app = _makeApp()

    if not isinstance(useTestProjects, bool):
        raise TypeError('useProjects must be a bool')
    if not isinstance(nologging, bool):
        raise TypeError('nologging must be a bool')
    if not interface in ['NoUi', 'Gui']:
        raise TypeError('interface must be NoUi|Gui')
    if not isinstance(debug, bool):
        raise TypeError('debug must be a bool')

    # check if a projectPath has been specified
    if projectPath is not None:
        if not isinstance(projectPath, (str, Path)):
            raise TypeError('projectPath must be str or Path object')
        projectPath = aPath(projectPath)

        if useTestProjects:
            # if useTestProjects is True then prefix with the test project folder
            projectPath = TEST_PROJECTS_PATH / projectPath

    if interface == 'Gui':
        # store temporary variable so that the qtApp event execution loop can be skipped
        # allows flow to continue after creation of mainWindow
        import builtins
        builtins._skipExecuteLoop = True

    # build new ccpn application/project
    _framework = Framework.createFramework(projectPath=projectPath, nologging=nologging, _skipUpdates=True,
                                           interface=interface, debug=debug,
                                           lightColourScheme=True, darkColourScheme=False)
    _project = _framework.project
    if _project is None:
        raise RuntimeError("No project found for project path %s" % projectPath)

    # initialise the undo stack
    _project._resetUndo(debug=True, application=_framework)
    _project._undo.debug = True

    app.project = _project

    # return the new project
    return app


if __name__ == '__main__':
    app = TestApplication()
    w = QtWidgets.QWidget()
    w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle('testApplication')
    w.show()

    app.start()
