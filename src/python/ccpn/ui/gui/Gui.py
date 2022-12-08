"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-12-08 16:31:21 +0000 (Thu, December 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-16 18:20:01 +0000 (Thu, March 16, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import typing
import re
from PyQt5 import QtWidgets, QtCore, QtGui

from ccpn.core import _coreClassMap
from ccpn.core.Project import Project

from ccpn.framework.Application import getApplication
from ccpn.framework.PathsAndUrls import CCPN_EXTENSION
from ccpn.framework.lib.DataLoaders.DataLoaderABC import getDataLoaders, _checkPathForDataLoader

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.ContextManagers import \
    notificationEchoBlocking, \
    catchExceptions, \
    undoBlockWithoutSideBar, \
    logCommandManager

from ccpn.ui.Ui import Ui
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup, NewTermsConditionsPopup
from ccpn.ui.gui.widgets.Application import Application
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import FileDialog
from ccpn.ui.gui.popups.ImportStarPopup import StarImporterPopup

# This import initializes relative paths for QT style-sheets.  Do not remove! GWV ????
from ccpn.ui.gui.guiSettings import FontSettings
from ccpn.ui.gui.widgets.Font import getFontHeight, setWidgetFont

from ccpn.util.Logging import getLogger
from ccpn.util import Logging
from ccpn.util import Register
from ccpn.util.Path import aPath, Path
from ccpn.util.decorators import logCommand

from ccpnmodel.ccpncore.memops.ApiError import ApiError


#-----------------------------------------------------------------------------------------
# Subclass the exception hook fpr PyQT
#-----------------------------------------------------------------------------------------
def _ccpnExceptionhook(ccpnType, value, tback):
    """This because PyQT raises and catches exceptions,
    but doesn't pass them along instead makes the program crashing miserably.
    """
    application = getApplication()
    if application and application._isInDebugMode:
        sys.stderr.write('_ccpnExceptionhook: type = %s\n' % ccpnType)
        sys.stderr.write('_ccpnExceptionhook: value = %s\n' % value)
        sys.stderr.write('_ccpnExceptionhook: tback = %s\n' % tback)

    if application and application.hasGui:
        title = str(ccpnType)[8:-2] + ':'
        text = str(value)
        MessageDialog.showError(title=title, message=text)

    sys.__excepthook__(ccpnType, value, tback)

sys.excepthook = _ccpnExceptionhook
#-----------------------------------------------------------------------------------------



def qtMessageHandler(*errors):
    for err in errors:
        Logging.getLogger().warning('QT error: %s' % err)
# un/suppress messages
QtCore.qInstallMessageHandler(qtMessageHandler)

# REMOVEDEBUG = r'\(\w+\.\w+:\d+\)$'
REMOVEDEBUG = r'\(\S+\.\w+:\d+\)$'

MAXITEMLOGGING = 4

class _MyAppProxyStyle(QtWidgets.QProxyStyle):
    """Class to handle resizing icons in menus
    """

    def pixelMetric(self, QStyle_PixelMetric, option=None, widget=None):
        if QStyle_PixelMetric == QtWidgets.QStyle.PM_SmallIconSize:
            # change the size of the icons in menus - overrides checkBoxes in menus
            return (getFontHeight(size='SMALL') or 15) + 3
        elif QStyle_PixelMetric in (QtWidgets.QStyle.PM_IndicatorHeight,
                                    QtWidgets.QStyle.PM_IndicatorWidth,
                                    QtWidgets.QStyle.PM_ExclusiveIndicatorWidth,
                                    QtWidgets.QStyle.PM_ExclusiveIndicatorHeight,
                                    ):
            # change the size of checkBoxes and radioButtons
            return (getFontHeight(size='SMALL') or 15) - 2
        elif QStyle_PixelMetric == QtWidgets.QStyle.PM_MessageBoxIconSize:
            # change the icon size in messageDialog
            return getFontHeight(size='MAXIMUM') or 18

        return super().pixelMetric(QStyle_PixelMetric, option, widget)


class Gui(Ui):
    """Top class for the GUI interface
    """
    # Factory functions for UI-specific instantiation of wrapped graphics classes
    _factoryFunctions = {}

    def __init__(self, application):

        # sets self.mainWindow (None), self.application and self.pluginModules
        Ui.__init__(self, application)

        # GWV: this is not ideal and needs to move into the Gui class
        application._fontSettings = FontSettings(application.preferences)
        application._setColourSchemeAndStyleSheet()
        application._setupMenus()

        self._initQtApp()

    def _initQtApp(self):
        # On the Mac (at least) it does not matter what you set the applicationName to be,
        # it will come out as the executable you are running (e.g. "python3")

        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

        # NOTE:ED - this is essential for multi-window applications
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)

        # fm = QtGui.QSurfaceFormat()
        # fm.setSamples(4)
        # # NOTE:ED - Do not do this, they cause QT to exhibit strange behaviour
        # # fm.setSwapInterval(0)  # disable VSync
        # # fm.setSwapBehavior(QtGui.QSurfaceFormat.DoubleBuffer)
        # QtGui.QSurfaceFormat.setDefaultFormat(fm)

        self.qtApp = Application(self.application.applicationName,
                                 self.application.applicationVersion,
                                 organizationName='CCPN', organizationDomain='ccpn.ac.uk')

        # patch for icon sizes in menus, etc.
        styles = QtWidgets.QStyleFactory()
        myStyle = _MyAppProxyStyle(styles.create('fusion'))
        self.qtApp.setStyle(myStyle)

        # # original - no patch for icon sizes
        # styles = QtWidgets.QStyleFactory()
        # self.qtApp.setStyle(styles.create('fusion'))

    def initialize(self, mainWindow):
        """UI operations done after every project load/create
        """
        with notificationEchoBlocking():
            # Set up mainWindow
            self.mainWindow = self._setupMainWindow(mainWindow)
            self.application._initGraphics()
            self.mainWindow._updateRestoreArchiveMenu()
            self.application._updateCheckableMenuItems()

    def startUi(self):
        """Start the UI
        """
        self.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(self.mainWindow)

        # check whether to skip the execution loop for testing with mainWindow
        import builtins

        _skip = getattr(builtins, '_skipExecuteLoop', False)
        if not _skip:
            self.qtApp.start()

    def _registerDetails(self, registered=False, acceptedTerms=False):
        """Display registration popup"""
        days = Register._graceCounter(Register._fetchGraceFile(self.application))
        # check valid internet connection first
        if not Register.checkInternetConnection():
            msg = 'Could not connect to the registration server, please check your internet connection. ' \
                  'Register within %s day(s) to continue using the software' % str(days)
            MessageDialog.showError('Registration', msg)

        else:
            if registered and not acceptedTerms:
                popup = NewTermsConditionsPopup(self.mainWindow, trial=days, version=self.application.applicationVersion, modal=True)
            else:
                popup = RegisterPopup(self.mainWindow, trial=days, version=self.application.applicationVersion, modal=True)

            self.mainWindow.show()
            popup.exec_()
            self.qtApp.processEvents()

    def _setupMainWindow(self, mainWindow):
        # Set up mainWindow

        project = self.application.project
        mainWindow.sideBar.buildTree(project, clear=True)

        # mainWindow.raise_()  # whaaaaaat? causes the menu-bar to be unresponsive
        mainWindow.namespace['current'] = self.application.current
        return mainWindow

    def echoCommands(self, commands: typing.List[str]):
        """Echo commands strings, one by one, to logger
        and store them in internal list for perusal
        """
        logger = Logging.getLogger()
        for command in commands:
            logger.echoInfo(command)

        if self.application.ui is not None and \
                self.application.ui.mainWindow is not None and \
                self.application._enableLoggingToConsole:

            console = self.application.ui.mainWindow.pythonConsole
            for command in commands:
                command = re.sub(REMOVEDEBUG, '', command)
                console._write(command + '\n')

    def getByGid(self, gid):

        from ccpn.ui.gui.modules.CcpnModule import PidShortClassName, PidLongClassName
        from ccpn.core.lib.Pid import Pid

        pid = Pid(gid)
        if pid is not None:
            if pid.type in [PidLongClassName, PidShortClassName]:
                # get the GuiModule object By its Gid
                return self.application.mainWindow.moduleArea.modules.get(pid.id)

        return self.application.getByGid(gid)

    def _execUpdates(self):
        """Use the Update popup to execute any updates
        """
        self.application._showUpdatePopup()

    #-----------------------------------------------------------------------------------------
    # Helper methods
    #-----------------------------------------------------------------------------------------

    def _queryChoices(self, dataLoader):
        """Query the user about his/her choice to import/new/cancel
        """
        choices = ('Import', 'New project', 'Cancel')
        choice = MessageDialog.showMulti('Load %s' % dataLoader.dataFormat,
                           'How do you want to handle "%s":' % dataLoader.path,
                           choices, parent=self.mainWindow)

        if choice == choices[0]:  # import
            dataLoader.createNewProject = False
            createNewProject = False
            ignore = False

        elif choice == choices[1]:  # new project
            dataLoader.createNewProject = True
            createNewProject = True
            ignore = False

        else:  # cancel
            dataLoader = None
            createNewProject = False
            ignore = True

        return (dataLoader, createNewProject, ignore)

    def _getDataLoader(self, path, pathFilter=None):
        """Get dataLoader for path (or None if not present), optionally only testing for
        dataFormats defined in filter.
        Allows for reporting or checking through popups.
        Does not do the actual loading.

        :param path: the path to get a dataLoader for
        :param pathFilter: a list/tuple of optional dataFormat strings; (defaults to all dataFormats)
        :returns a tuple (dataLoader, createNewProject, ignore)
        """
        # local import here
        from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader
        from ccpn.framework.lib.DataLoaders.SparkyDataLoader import SparkyDataLoader
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import _getPotentialDataLoaders

        if pathFilter is None:
            pathFilter =  tuple(getDataLoaders().keys())

        _loaders = _checkPathForDataLoader(path=path, pathFilter=pathFilter)
        if len(_loaders) > 0 and _loaders[-1].isValid:
            # found a valid one; use that
            dataLoader = _loaders[-1]

        # log errors
        elif len(_loaders) == 0:
            dataLoader = None
            txt = f'No valid loader found for {path}'

        elif len(_loaders) == 1 and not _loaders[0].isValid:
            dataLoader = None
            txt = f'No valid loader: {_loaders[0].errorString}'

        else:
            dataLoader = None
            txt = f'No valid loader found for {path}; tried {[dl.dataFormat for dl in _loaders]}'

        if dataLoader is None:
            getLogger().warning(txt)
            return (None, False, False)

        # if (dataLoader :=  checkPathForDataLoader(path, pathFilter=pathFilter)) is None:
        #     dataFormats = [dl.dataFormat for dl in _getPotentialDataLoaders(path)]
        #     txt = f'Loading "{path}" unsuccessful; tried all of {dataFormats}, but failed'
        #     getLogger().warning(txt)
        #     return (None, False, False)

        createNewProject = dataLoader.createNewProject
        ignore = False

        path = dataLoader.path
        if dataLoader.dataFormat == CcpNmrV2ProjectDataLoader.dataFormat:
            createNewProject = True
            dataLoader.createNewProject = True
            ok = MessageDialog.showYesNoWarning(f'Load Project',
                                                f'Project "{path.name}" was created with version-2 Analysis.\n'
                                                f'\n'
                                                f'CAUTION:\n'
                                                f'The project will be converted to a version-3 project and saved as a new directory with .ccpn extension.\n'
                                                f'\n'
                                                f'Do you want to continue loading?')

            if not ok:
                # skip loading so that user can backup/copy project
                getLogger().info('==> Cancelled loading ccpn project "%s"' % path)
                ignore = True

        elif dataLoader.dataFormat == CcpNmrV3ProjectDataLoader.dataFormat and Project._needsUpgrading(path):
            createNewProject = True
            dataLoader.createNewProject = True

            DONT_OPEN = "Don't Open"
            CONTINUE = 'Continue'
            MAKE_ARCHIVE = 'Make a backup archive (.tgz) of the project'

            dataLoader.makeArchive = False
            ok = MessageDialog.showMulti(f'Load Project',
                                         f'You are opening an older project (version 3.0.x) - {path.name}\n'
                                         f'\n'
                                         f'When you save, it will be upgraded and will not be readable by version 3.0.4\n',
                                         texts=[DONT_OPEN, CONTINUE],
                                         checkbox=MAKE_ARCHIVE, checked=False,
                                         )

            if not any(ss in ok for ss in [DONT_OPEN, MAKE_ARCHIVE, CONTINUE]):
                # there was an error from the dialog
                getLogger().debug(f'==> Cancelled loading ccpn project "{path}" - error in dialog')
                ignore = True

            if DONT_OPEN in ok:
                # user selection not to load
                getLogger().info(f'==> Cancelled loading ccpn project "{path}"')
                ignore = True

            elif MAKE_ARCHIVE in ok:
                # flag to make a backup archive
                dataLoader.makeArchive = True

        elif dataLoader.dataFormat == NefDataLoader.dataFormat:
            (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)
            if dataLoader and not createNewProject and not ignore:
                # we are importing; popup the import window
                ok = self.mainWindow._showNefPopup(dataLoader)
                if not ok:
                    ignore = True

        elif dataLoader.dataFormat == SparkyDataLoader.dataFormat:
            (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)

        elif dataLoader.isSpectrumLoader and dataLoader.existsInProject():
            ok = MessageDialog.showYesNoWarning('Loading Spectrum',
                                                f'"{dataLoader.path}"\n' 
                                                f'already exists in the project\n'
                                                '\n'
                                                'do you want to load?'
                               )
            if not ok:
                ignore = True

        elif dataLoader.dataFormat == StarDataLoader.dataFormat and dataLoader:
            (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)
            if dataLoader and not ignore:
                title = 'New project from NmrStar' if createNewProject else \
                        'Import from NmrStar'
                dataLoader.getDataBlock()  # this will read and parse the file
                popup = StarImporterPopup(dataLoader=dataLoader,
                                          parent=self.mainWindow,
                                          size=(700,1000),
                                          title=title
                                          )
                popup.exec_()
                ignore = (popup.result == popup.CANCEL_PRESSED)

        elif dataLoader.dataFormat == DirectoryDataLoader.dataFormat and len(dataLoader) > MAXITEMLOGGING:
            ok = MessageDialog.showYesNoWarning('Directory "%s"\n' %dataLoader.path,
                                                f'\n'
                                                'CAUTION: You are trying to load %d items\n'
                                                '\n'
                                                'Do you want to continue?' % (len(dataLoader,))
                                                )

            if not ok:
                ignore = True

        return (dataLoader, createNewProject, ignore)

    #-----------------------------------------------------------------------------------------
    # Project and loading data related methods
    #-----------------------------------------------------------------------------------------

    @logCommand('application.')
    def newProject(self, name:str = 'default') -> typing.Optional[Project]:
        """Create a new project instance with name.
        :return a Project instance or None
        """
        # if not self.project.isTemporary:
        if self.project and (self.project._undo is None or self.project._undo.isDirty()):
            message = f"Do you really want to create a new project (current project will be closed {' and any changes will be lost' if self.project.isModified else ''})?"

            if not (_ok := MessageDialog.showYesNo('New Project', message, parent=self.mainWindow)):
                return

        if (_name := Project._checkName(name, correctName=True)) != name:
            MessageDialog.showInfo('New Project', f'Project name changed from "{name}" to "{_name}"\nSee console/log for details', parent=self)

        with catchExceptions(errorStringTemplate='Error creating new project: %s'):
            if self.mainWindow:
                self.mainWindow.moduleArea._closeAll()
            newProject = self.application._newProject(name=_name)
            if newProject is None:
                raise RuntimeError('Unable to create new project')
            newProject._mainWindow.show()
            QtWidgets.QApplication.setActiveWindow(newProject._mainWindow)

            return newProject

    def _loadProject(self, dataLoader) -> typing.Union[Project, None]:
        """Helper function, loading project from dataLoader instance
        check and query for closing current project
        build the project Gui elements
        attempts to restore on failure to load a project

        :returns project instance or None
        """
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader

        if not dataLoader.createNewProject:
            raise RuntimeError('DataLoader %s does not create a new project')

        oldProjectLoader = None
        oldProjectIsTemporary = True
        oldMainWindowPos = self.mainWindow.pos()
        if self.project:
            # if not self.project.isTemporary:
            if self.project._undo is None or self.project._undo.isDirty():
                message = f"Do you really want to open a new project (current project will be closed" \
                              f"{' and any changes will be lost' if self.project.isModified else ''})?"

                if not (_ok := MessageDialog.showYesNo('Load Project', message, parent=self.mainWindow)):
                    return None

            # Some error recovery; store info to re-open the current project (or a new default)
            oldProjectLoader = CcpNmrV3ProjectDataLoader(self.project.path)
            oldProjectIsTemporary = self.project.isTemporary

        try:
            if self.project:
                # NOTE:ED - getting a strange QT bug disabling the menu-bar from here
                #  I think because the main-window isn't visible on the first load :|
                with MessageDialog.progressManager(self.mainWindow, f'Loading project {dataLoader.path} ... '):
                    _loaded = dataLoader.load()
                    if _loaded is None or len(_loaded) == 0:
                        return None
            else:
                # progress not required on the first load
                _loaded = dataLoader.load()
                if _loaded is None or len(_loaded) == 0:
                    return None

            newProject = _loaded[0]

            # # Note that the newProject has its own MainWindow; i.e. it is not self
            # newProject._mainWindow.sideBar.buildTree(newProject)
            # The next two lines are essential to have the QT main event loop associated
            # with the new window; without these, the programs just terminates
            newProject._mainWindow.show()
            QtWidgets.QApplication.setActiveWindow(newProject._mainWindow)

            # if the new project contains invalid spectra then open the popup to see them
            self.mainWindow._checkForBadSpectra(newProject)
            self.mainWindow.move(oldMainWindowPos)

        except (RuntimeError, ApiError) as es:
            MessageDialog.showError('Error loading Project:', f'{es}', parent=self.mainWindow)

            # Try to restore the state
            newProject = None
            if oldProjectIsTemporary:
                newProject = self.application._newProject()
            elif oldProjectLoader:
                newProject = oldProjectLoader.load()[0]  # dataLoaders return a list

            if newProject:
                # The next two lines are essential to have the QT main event loop associated
                # with the new window; without these, the programs just terminates
                newProject._mainWindow.show()
                QtWidgets.QApplication.setActiveWindow(newProject._mainWindow)

        return newProject

    # @logCommand('application.') # eventually decorated by  _loadData()
    def loadProject(self, path=None) -> typing.Union[Project, None]:
        """Loads project defined by path
        :return a Project instance or None
        """
        if path is None:
            dialog = FileDialog.ProjectFileDialog(parent=self.mainWindow, acceptMode='open')
            dialog._show()

            if (path := dialog.selectedFile()) is None:
                return None

        dataLoader, createNewProject, ignore = self._getDataLoader(path)
        if ignore or dataLoader is None or not createNewProject:
            return None

        # load the project using the dataLoader;
        # We'll ask framework, who will pass it back to ui._loadProject
        if (objs := self.application._loadData([dataLoader])):
            if len(objs) == 1:
                return objs[0]

        return None

    def _closeProject(self):
        """Do all gui-related stuff when closing a project
        CCPNINTERNAL: called from Framework._closeProject()
        """
        if self.mainWindow:
            # ui/gui cleanup
            self.mainWindow.deleteAllNotifiers()
            self.mainWindow._closeMainWindowModules()
            self.mainWindow._closeExtraWindowModules()
            self.mainWindow._stopPythonConsole()
            self.mainWindow.sideBar.clearSideBar()
            self.mainWindow.sideBar.deleteLater()
            self.mainWindow.deleteLater()
            self.mainWindow = None

    def saveProjectAs(self, newPath=None, overwrite:bool=False) -> bool:
        """Opens save Project to newPath.
        Optionally open file dialog.
        :param newPath: new path to save project (str | Path instance)
        :param overwrite: flag to indicate overwriting of existing path
        :return True if successful
        """
        oldPath = self.project.path
        if newPath is None:
            if (newPath := _getSaveDirectory(self.mainWindow)) is None:
                return False

        newPath = aPath(newPath).assureSuffix(CCPN_EXTENSION)
        title = 'Project SaveAs'

        if (  not overwrite and
              newPath.exists() and
             (newPath.is_file() or (newPath.is_dir() and len(newPath.listdir()) > 0))
           ):
            # should not really need to check the second and third condition above, only
            # the Qt dialog stupidly insists a directory exists before you can select it
            # so if it exists but is empty then don't bother asking the question
            msg = 'Path "%s" already exists; overwrite?' % newPath
            if not MessageDialog.showYesNo(title, msg):
                return False

        # check the project name derived from path
        newName = newPath.basename
        if (_name := self.project._checkName(newName, correctName=True)) != newName:
            newPath = newPath.parent / _name + CCPN_EXTENSION
            MessageDialog.showInfo(title, f'Project name changed from "{newName}" to "{_name}"\nSee console/log for details', parent=self)

        with catchExceptions(errorStringTemplate='Error saving project: %s'):
            with logCommandManager('application.', 'saveProjectAs', newPath, overwrite=overwrite):
                with MessageDialog.progressManager(self.mainWindow, f'Saving project {newPath} ... '):
                    if not self.application._saveProject(newPath=newPath,
                                                         createFallback=False,
                                                         overwriteExisting=True):
                        txt = "Saving project to %s aborted" % newPath
                        getLogger().warning(txt)
                        MessageDialog.showError("Project SaveAs", txt, parent=self.mainWindow)
                        return False

            self.mainWindow._updateWindowTitle()
            self.application._getRecentProjectFiles(oldPath=oldPath)  # this will also update the list
            self.mainWindow._fillRecentProjectsMenu() # Update the menu

            successMessage = 'Project successfully saved to "%s"' % self.project.path
            MessageDialog.showInfo("Project SaveAs", successMessage, parent=self.mainWindow)
            self.mainWindow.statusBar().showMessage(successMessage)
            getLogger().info(successMessage)

            return True

        # PyCharm thinks the next statement is unreachable; not true as the with catchExceptions does yield
        # and finish
        return False

    @logCommand('application.')
    def saveProject(self) -> bool:
        """Save project.
        :return True if successful
        """
        with catchExceptions(errorStringTemplate='Error saving project: %s'):
            with MessageDialog.progressManager(self.mainWindow, f'Saving project ... '):
                if not self.application._saveProject(newPath=None,
                                                     createFallback=True,
                                                     overwriteExisting=True):
                    return False

        successMessage = '==> Project successfully saved to "%s"' % self.project.path
        self.mainWindow.statusBar().showMessage(successMessage)
        getLogger().info(successMessage)

        return True

    def _loadData(self, dataLoader) -> list:
        """Load the data defined by dataLoader instance, catching errors
        and suspending sidebar.
        :return a list of loaded opjects
        """
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader

        result = []
        errorStringTemplate = 'Loading "%s" failed:' % dataLoader.path + '\n%s'
        with catchExceptions(errorStringTemplate=errorStringTemplate):
            # For data loads that are possibly time consuming, use progressManager
            if isinstance(dataLoader, (StarDataLoader, NefDataLoader)):
                with MessageDialog.progressManager(self.mainWindow, f'Importing data ... '):
                    result = dataLoader.load()
            else:
                result = dataLoader.load()
        return result

    # @logCommand('application.') # eventually decorated by  _loadData()
    def loadData(self, *paths, pathFilter=None) -> list:
        """Loads data from paths; query if none supplied
        Optionally filter for dataFormat(s)
        :param *paths: argument list of path's (str or Path instances)
        :param pathFilter: keyword argument: list/tuple of dataFormat strings
        :returns list of loaded objects
        """
        if len(paths) == 0:
            dialog = FileDialog.DataFileDialog(parent=self.mainWindow, acceptMode='load')
            dialog._show()
            if (path := dialog.selectedFile()) is None:
                return []
            paths = [path]

        dataLoaders = []
        for path in paths:

            _path = aPath(path)
            if not _path.exists():
                txt = f'"{path}" does not exist'
                getLogger().warning(txt)
                MessageDialog.showError('Load Data', txt, parent=self.mainWindow)
                if len(paths) == 1:
                    return []
                else:
                    continue

            dataLoader, createNewProject, ignore = self._getDataLoader(path, pathFilter=pathFilter)
            if ignore:
                continue

            if dataLoader is None:
                txt = f'Unable to load "{path}"'
                getLogger().warning(txt)
                MessageDialog.showError('Load Data', txt, parent=self.mainWindow)
                if len(paths) == 1:
                    return []
                else:
                    continue

            dataLoaders.append(dataLoader)

        # load the project using the dataLoaders;
        # We'll ask framework who will pass it back as ui._loadData calls
        objs = self.application._loadData(dataLoaders)
        if len(objs) == 0:
            txt = f'No objects were loaded from {paths}'
            getLogger().warning(txt)
            MessageDialog.showError('Load Data', txt, parent=self.mainWindow)

        return objs

    def loadSpectra(self, *paths) -> list:
        """Load all the spectra found in paths.
        Query in case path is empty.

        :param paths: list of paths
        :return a list of Spectra instances
        """
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import getSpectrumLoaders, checkPathForDataLoader
        from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader

        if len(paths) == 0:
            # This only works with non-native file dialog; override the default behavior
            dialog = FileDialog.SpectrumFileDialog(parent=self.mainWindow, acceptMode='load',
                                                   useNative=False)
            dialog._show()
            paths = dialog.selectedFiles()

        if not paths:
            return []

        pathFilter = list(getSpectrumLoaders().keys())

        spectrumLoaders = []
        count = 0
        # Recursively search all paths
        for path in paths:
            _path = aPath(path)
            if _path.is_dir():
                dirLoader = DirectoryDataLoader(path, recursive=False,
                                                pathFilter=pathFilter)
                spectrumLoaders.append(dirLoader)
                count += len(dirLoader)

            elif (sLoader := checkPathForDataLoader(path, pathFilter=pathFilter)) is not None:
                spectrumLoaders.append(sLoader)
                count += 1

        if count > MAXITEMLOGGING:
            okToOpenAll = MessageDialog.showYesNo('Load data', 'You selected %d items.'
                                                               ' Do you want to open all?' % count)
            if not okToOpenAll:
                return []

        with logCommandManager('application.', 'loadSpectra', *paths):
            result = self.application._loadData(spectrumLoaders)

        return result

#-----------------------------------------------------------------------------------------
# Helper code
#-----------------------------------------------------------------------------------------

def _getSaveDirectory(mainWindow):
    """Opens save Project as dialog box and gets directory specified in
    the file dialog.
    :return path instance or None
    """

    dialog = FileDialog.ProjectSaveFileDialog(parent=mainWindow, acceptMode='save')
    dialog._show()
    newPath = dialog.selectedFile()

    # if not iterable then ignore - dialog may return string or tuple(<path>, <fileOptions>)
    if isinstance(newPath, tuple) and len(newPath) > 0:
        newPath = newPath[0]

    # ignore if empty
    if not newPath:
        return None

    return newPath


#######################################################################################
#
#  Ui classes that map ccpn.ui._implementation
#
#######################################################################################


## Window class
_coreClassWindow = _coreClassMap['Window']
from ccpn.ui.gui.lib.GuiMainWindow import GuiMainWindow as _GuiMainWindow


class MainWindow(_coreClassWindow, _GuiMainWindow):
    """GUI main window, corresponds to OS window"""

    def __init__(self, project: Project, wrappedData: 'ApiWindow'):
        _coreClassWindow.__init__(self, project, wrappedData)

        logger = Logging.getLogger()

        logger.debug('MainWindow>> project: %s' % project)
        logger.debug('MainWindow>> project.application: %s' % project.application)

        application = project.application
        _GuiMainWindow.__init__(self, application=application)

        # hide the window here and make visible later
        self.hide()

        # patches for now:
        project._mainWindow = self
        # logger.debug('MainWindow>> project._mainWindow: %s' % project._mainWindow)

        application._mainWindow = self
        application.ui.mainWindow = self
        # logger.debug('MainWindow>> application: %s' % application)
        # logger.debug('MainWindow>> application.project: %s' % application.project)
        # logger.debug('MainWindow>> application._mainWindow: %s' % application._mainWindow)
        # logger.debug('MainWindow>> application.ui.mainWindow: %s' % application.ui.mainWindow)

        setWidgetFont(self, )


from ccpn.ui.gui.lib.GuiWindow import GuiWindow as _GuiWindow


class SideWindow(_coreClassWindow, _GuiWindow):
    """GUI side window, corresponds to OS window"""

    def __init__(self, project: Project, wrappedData: 'ApiWindow'):
        _coreClassWindow.__init__(self, project, wrappedData)
        _GuiWindow.__init__(self, project.application)


def _factoryFunction(project: Project, wrappedData):
    """create Window, dispatching to subtype depending on wrappedData"""
    if wrappedData.title == 'Main':
        return MainWindow(project, wrappedData)
    else:
        return SideWindow(project, wrappedData)


Gui._factoryFunctions[_coreClassWindow.className] = _factoryFunction

## Task class
# There is no special GuiTask, so nothing needs to be done

## Mark class - put in namespace for documentation
Mark = _coreClassMap['Mark']

## SpectrumDisplay class
_coreClassSpectrumDisplay = _coreClassMap['SpectrumDisplay']
from ccpn.ui.gui.modules.SpectrumDisplay1d import SpectrumDisplay1d as _SpectrumDisplay1d


class StripDisplay1d(_coreClassSpectrumDisplay, _SpectrumDisplay1d):
    """1D bound display"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Local override init for Qt subclass"""
        Logging.getLogger().debug('StripDisplay1d>> project: %s, project.application: %s' %
                                  (project, project.application))
        _coreClassSpectrumDisplay.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        _SpectrumDisplay1d.__init__(self, mainWindow=self.application.ui.mainWindow)


from ccpn.ui.gui.modules.SpectrumDisplayNd import SpectrumDisplayNd as _SpectrumDisplayNd


#TODO: Need to check on the consequences of hiding name from the wrapper

# NB: GWV had to comment out the name property to make it work
# conflicts existed between the 'name' and 'window' attributes of the two classes
# the pyqtgraph descendents need name(), GuiStripNd had 'window', but that could be replaced with
# mainWindow throughout

class SpectrumDisplayNd(_coreClassSpectrumDisplay, _SpectrumDisplayNd):
    """ND bound display"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Local override init for Qt subclass"""
        Logging.getLogger().debug('SpectrumDisplayNd>> project: %s, project.application: %s' % (project, project.application))
        _coreClassSpectrumDisplay.__init__(self, project, wrappedData)

        # hack for now;
        self.application = project.application

        _SpectrumDisplayNd.__init__(self, mainWindow=self.application.ui.mainWindow)


#old name
StripDisplayNd = SpectrumDisplayNd


def _factoryFunction(project: Project, wrappedData):
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    if wrappedData.is1d:
        return StripDisplay1d(project, wrappedData)
    else:
        return StripDisplayNd(project, wrappedData)


Gui._factoryFunctions[_coreClassSpectrumDisplay.className] = _factoryFunction

## Strip class
_coreClassStrip = _coreClassMap['Strip']
from ccpn.ui.gui.lib.GuiStrip1d import GuiStrip1d as _GuiStrip1d


class Strip1d(_coreClassStrip, _GuiStrip1d):
    """1D strip"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):
        """Local override init for Qt subclass"""

        _coreClassStrip.__init__(self, project, wrappedData)

        Logging.getLogger().debug('Strip1d>> spectrumDisplay: %s' % self.spectrumDisplay)
        _GuiStrip1d.__init__(self, self.spectrumDisplay)

        # cannot add the Frame until fully done
        strips = self.spectrumDisplay.orderedStrips
        if self in strips:
            stripIndex = strips.index(self)
        else:
            stripIndex = len(strips)
            Logging.getLogger().warning('Strip ordering not defined for %s in %s' % (str(self.pid), str(self.spectrumDisplay.pid)))

        tilePosition = self.tilePosition

        if self.spectrumDisplay.stripArrangement == 'Y':

            # strips are arranged in a row
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[0], tilePosition[1])

        elif self.spectrumDisplay.stripArrangement == 'X':

            # strips are arranged in a column
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[1], tilePosition[0])

        elif self.spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            Logging.getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

        else:
            Logging.getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))


from ccpn.ui.gui.lib.GuiStripNd import GuiStripNd as _GuiStripNd


class StripNd(_coreClassStrip, _GuiStripNd):
    """ND strip """

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):
        """Local override init for Qt subclass"""

        _coreClassStrip.__init__(self, project, wrappedData)

        Logging.getLogger().debug('StripNd>> spectrumDisplay=%s' % self.spectrumDisplay)
        _GuiStripNd.__init__(self, self.spectrumDisplay)

        # cannot add the Frame until fully done
        strips = self.spectrumDisplay.orderedStrips
        if self in strips:
            stripIndex = strips.index(self)
        else:
            stripIndex = len(strips)
            Logging.getLogger().warning('Strip ordering not defined for %s in %s' % (str(self.pid), str(self.spectrumDisplay.pid)))

        tilePosition = self.tilePosition

        if self.spectrumDisplay.stripArrangement == 'Y':

            # strips are arranged in a row
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[0], tilePosition[1])

        elif self.spectrumDisplay.stripArrangement == 'X':

            # strips are arranged in a column
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[1], tilePosition[0])

        elif self.spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            Logging.getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

        else:
            Logging.getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))


def _factoryFunction(project: Project, wrappedData):
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    apiSpectrumDisplay = wrappedData.spectrumDisplay
    if apiSpectrumDisplay.is1d:
        return Strip1d(project, wrappedData)
    else:
        return StripNd(project, wrappedData)


Gui._factoryFunctions[_coreClassStrip.className] = _factoryFunction

## Axis class - put in namespace for documentation
Axis = _coreClassMap['Axis']

# Any Factory function to _implementation or abstractWrapper
#
## SpectrumView class
_coreClassSpectrumView = _coreClassMap['SpectrumView']
from ccpn.ui.gui.lib.GuiSpectrumView1d import GuiSpectrumView1d as _GuiSpectrumView1d


class _SpectrumView1d(_coreClassSpectrumView, _GuiSpectrumView1d):
    """1D Spectrum View"""

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        """Local override init for Qt subclass"""
        _coreClassSpectrumView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        Logging.getLogger().debug('SpectrumView1d>> %s' % self)
        _GuiSpectrumView1d.__init__(self)


from ccpn.ui.gui.lib.GuiSpectrumViewNd import GuiSpectrumViewNd as _GuiSpectrumViewNd


class _SpectrumViewNd(_coreClassSpectrumView, _GuiSpectrumViewNd):
    """ND Spectrum View"""

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        """Local override init for Qt subclass"""
        _coreClassSpectrumView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        Logging.getLogger().debug('SpectrumViewNd>> self=%s strip=%s' % (self, self.strip))
        _GuiSpectrumViewNd.__init__(self)


def _factoryFunction(project: Project, wrappedData):
    """create SpectrumView, dispatching to subtype depending on wrappedData"""
    if 'intensity' in wrappedData.strip.spectrumDisplay.axisCodes:
        # 1D display
        return _SpectrumView1d(project, wrappedData)
    else:
        # ND display
        return _SpectrumViewNd(project, wrappedData)


Gui._factoryFunctions[_coreClassSpectrumView.className] = _factoryFunction

## PeakListView class
_coreClassPeakListView = _coreClassMap['PeakListView']
from ccpn.ui.gui.lib.GuiPeakListView import GuiPeakListView as _GuiPeakListView


class _PeakListView(_coreClassPeakListView, _GuiPeakListView):
    """Peak List View for 1D or nD PeakList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripPeakListView'):
        """Local override init for Qt subclass"""
        _coreClassPeakListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        _GuiPeakListView.__init__(self)
        self._init()


Gui._factoryFunctions[_coreClassPeakListView.className] = _PeakListView

## IntegralListView class
_coreClassIntegralListView = _coreClassMap['IntegralListView']
from ccpn.ui.gui.lib.GuiIntegralListView import GuiIntegralListView as _GuiIntegralListView


class _IntegralListView(_coreClassIntegralListView, _GuiIntegralListView):
    """Integral List View for 1D or nD IntegralList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripIntegralListView'):
        """Local override init for Qt subclass"""
        _coreClassIntegralListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        _GuiIntegralListView.__init__(self)
        self._init()


Gui._factoryFunctions[_coreClassIntegralListView.className] = _IntegralListView

## MultipletListView class
_coreClassMultipletListView = _coreClassMap['MultipletListView']
from ccpn.ui.gui.lib.GuiMultipletListView import GuiMultipletListView as _GuiMultipletListView


class _MultipletListView(_coreClassMultipletListView, _GuiMultipletListView):
    """Multiplet List View for 1D or nD MultipletList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripMultipletListView'):
        """Local override init for Qt subclass"""
        _coreClassMultipletListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        _GuiMultipletListView.__init__(self)
        self._init()


Gui._factoryFunctions[_coreClassMultipletListView.className] = _MultipletListView

# Delete what we do not want in namespace
del _factoryFunction
# del coreClass
