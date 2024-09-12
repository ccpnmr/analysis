"""
The top-level Gui class for all user interactions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-09-12 11:48:51 +0100 (Thu, September 12, 2024) $"
__version__ = "$Revision: 3.2.5 $"
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
import platform

from PyQt5 import QtWidgets, QtCore, QtGui

from ccpn.core.Project import Project

from ccpn.framework.Application import getApplication
from ccpn.framework.PathsAndUrls import CCPN_DIRECTORY_SUFFIX, CCPN_SAVEAS_SUB_DIRECTORIES
from ccpn.framework.lib.DataLoaders.DataLoaderABC import _checkPathForDataLoader

from ccpn.core.lib.ContextManagers import (
    notificationEchoBlocking, catchExceptions,
    logCommandManager, undoStackBlocking, busyHandler
)
from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC

from ccpn.ui.Ui import Ui
from ccpn.ui.gui import Layout
from ccpn.ui.gui.guiSettings import LIGHT, DARK

from ccpn.ui.gui.modules.CcpnModule import CcpnModule

from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup, NewTermsConditionsPopup
from ccpn.ui.gui.widgets.Application import Application as PyQtApplication
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import FileDialog
from ccpn.ui.gui.widgets.Font import getSystemFonts
from ccpn.ui.gui.popups.ImportStarPopup import StarImporterPopup

# This import initializes relative paths for QT style-sheets.  Do not remove! GWV ????
from ccpn.ui.gui.guiSettings import FontSettings, consoleStyle
from ccpn.ui.gui.widgets.Icon import Icon

from ccpn.util.Logging import getLogger
from ccpn.util import Register
from ccpn.util.Path import aPath, Path
from ccpn.util.decorators import logCommand

from ccpnmodel.ccpncore.memops.ApiError import ApiError

# _Gui_V3_V4 contains code shared between V3 and V4
from ccpn.ui.gui._Gui_V3_V4 import _Gui_V3_V4


#-----------------------------------------------------------------------------------------
# Subclass the exception hook for PyQT
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

    # this is crashing on Windows 10 Enterprise :|
    # if application and application.hasGui:
    #     title = f'{str(ccpnType)[8:-2]}:'
    #     text = str(value)
    #     MessageDialog.showError(title=title, message=text)

    if application.project and not application.project.isReadOnly:
        application.project._updateLoggerState(readOnly=False)  #, flush=True)

    sys.__excepthook__(ccpnType, value, tback)

sys.excepthook = _ccpnExceptionhook

#-----------------------------------------------------------------------------------------
# un/suppress QT messages
#-----------------------------------------------------------------------------------------
def _qtMessageHandler(*errors):
    for err in errors:
        getLogger().warning(f'{consoleStyle.fg.red}QT error: {err}{consoleStyle.reset}')

QtCore.qInstallMessageHandler(_qtMessageHandler)

#-----------------------------------------------------------------------------------------

MAXITEMLOGGING = 4
MAXITEMLOADING = 5
MAXITEMDEPTH = 5

#-----------------------------------------------------------------------------------------
# Gui Class
#-----------------------------------------------------------------------------------------

class Gui(Ui, _Gui_V3_V4):
    """Top class for the GUI interface
    _Gui_V3_V4 contains methods shared between V3 and V4
    """

    _hasGui = True

    def __init__(self, application):

        # sets self.mainWindow (None), self.application and self.pluginModules
        Ui.__init__(self, application)

        self._fontSettings = FontSettings(application.preferences)  # used by getFontSettings in Font.py
        self._colourScheme = self._getColourScheme()
        self._styleSheet = self._getStyleSheet(self._colourScheme)

        # Get menu definitions; _getMenuDefs() subclassed by various application-specific Gui's
        self._menuDefs = self._getMenuDefs()

        self._qtApp = self._initQtApp()

        # read the current system-fonts
        getSystemFonts()

    def initialize(self, mainWindow, project):
        """UI operations done after every project load/create
        """
        if mainWindow is None:
            raise ValueError('Gui.initialize(): Undefined mainWindow')

        super().initialize(mainWindow=mainWindow, project=project)

        with notificationEchoBlocking():
            with undoStackBlocking(debugText='Gui.initialize'):
                # Set up mainWindow
                self._setupMainWindow()
                self._restoreSpectrumDisplayModules()
                self._makeActiveWindow()

    def _restoreSpectrumDisplayModules(self):
        """Code from Framework/Project, restoring spectrumDisplay's
        """
        from ccpn.ui.gui.lib import GuiStrip

        project = self.project
        mainWindow = self.mainWindow
        current = self.application.current
        preferences = self.application.preferences

        # 20191113:ED Initial insertion of spectrumDisplays into the moduleArea
        try:
            insertPoint = mainWindow.moduleArea
            for spectrumDisplay in mainWindow.spectrumDisplays:
                # mainWindow.moduleArea.addModule(spectrumDisplay, position='right', relativeTo=insertPoint)
                mainWindow._addModule(module=spectrumDisplay, position='right', relativeTo=insertPoint)
                insertPoint = spectrumDisplay

        except Exception:
            getLogger().warning('Impossible to restore SpectrumDisplays')

        try:
            if preferences.general.restoreLayoutOnOpening and \
                    mainWindow.moduleLayouts:
                Layout.restoreLayout(mainWindow, mainWindow.moduleLayouts, restoreSpectrumDisplay=False)
        except Exception as e:
            getLogger().warning(f'Impossible to restore Layout {e}')

        # New LayoutManager implementation; awaiting completion
        # try:
        #     from ccpn.framework.LayoutManager import LayoutManager
        #     layout = LayoutManager(mainWindow)
        #     path = self.statePath / 'Layout.json'
        #     layout.restoreState(path)
        #     layout.saveState()
        #
        # except Exception as es:
        #     getLogger().warning('Error restoring layout: %s' % es)

        # check that the top moduleArea is correctly formed - strange special case when all modules have
        #   been moved to tempAreas
        mArea = mainWindow.moduleArea
        if mArea.topContainer is not None and mArea.topContainer._container is None:
            getLogger().debug('Correcting empty topContainer')
            mArea.topContainer = None

        try:
            # initialise any colour changes before generating gui strips
            self._correctColours()
        except Exception as es:
            getLogger().warning(f'Error setting colours - {es}')

        # Initialise Strips
        for spectrumDisplay in mainWindow.spectrumDisplays:
            try:
                _badStrip = False
                for si, strip in enumerate(spectrumDisplay.orderedStrips):

                    # temporary to catch bad strips from ordering bug
                    if not strip:
                        continue

                    # GWV 15/2/24: Adapted from Code in Project._restoreObject
                    if not strip.axes:
                        # set the border to red
                        spectrumDisplay.mainWidget.setStyleSheet('Frame { border: 3px solid #FF1234; }')
                        spectrumDisplay.mainWidget.setEnabled(False)
                        spectrumDisplay.setEnabled(False)

                        getLogger().error(
                                f'Strip {strip} contains bad axes - please close SpectrumDisplay {spectrumDisplay} outlined in red.'
                                )
                        _badStrip = True
                        break

                    # get the new tilePosition of the strip - tilePosition is always (x, y) relative to screen stripArrangement
                    #                                       changing screen arrangement does NOT require flipping tilePositions
                    #                                       i.e. Y = (across, down); X = (down, across)
                    #                                       - check delete/undo/redo strips
                    tilePosition = strip.tilePosition

                    # move to the correct place in the widget - check stripDirection to display as row or column
                    if spectrumDisplay.stripArrangement == 'Y':
                        if True:  # tilePosition is None:
                            spectrumDisplay.stripFrame.layout().addWidget(strip, 0, si)  #stripIndex)
                            strip.tilePosition = (0, si)
                        # else:
                        #     spectrumDisplay.stripFrame.layout().addWidget(strip, tilePosition[0], tilePosition[1])

                    elif spectrumDisplay.stripArrangement == 'X':
                        if True:  #tilePosition is None:
                            spectrumDisplay.stripFrame.layout().addWidget(strip, si, 0)  #stripIndex)
                            strip.tilePosition = (0, si)
                        # else:
                        #     spectrumDisplay.stripFrame.layout().addWidget(strip, tilePosition[1], tilePosition[0])

                    elif spectrumDisplay.stripArrangement == 'T':
                        # NOTE:ED - Tiled plots not fully implemented yet
                        getLogger().warning(f'Tiled plots not implemented for spectrumDisplay: {str(spectrumDisplay)}')
                    else:
                        getLogger().warning(
                            f'Strip direction is not defined for spectrumDisplay: {str(spectrumDisplay)}')

                    if not spectrumDisplay.is1D:
                        for _strip in spectrumDisplay.strips:
                            _strip._updatePlaneAxes()

                if spectrumDisplay.isGrouped:
                    # set up the spectrumGroup toolbar

                    spectrumDisplay.spectrumToolBar.hide()
                    spectrumDisplay.spectrumGroupToolBar.show()

                    _spectrumGroups = [project.getByPid(pid) for pid in spectrumDisplay._getSpectrumGroups()]

                    for group in _spectrumGroups:
                        spectrumDisplay.spectrumGroupToolBar._forceAddAction(group)

                else:
                    # set up the spectrum toolbar

                    spectrumDisplay.spectrumToolBar.show()
                    spectrumDisplay.spectrumGroupToolBar.hide()
                    spectrumDisplay._setToolbarButtons()

                # some strips may not be instantiated at this point
                # resize the stripFrame to the spectrumDisplay - ready for first resize event
                # spectrumDisplay.stripFrame.resize(spectrumDisplay.width() - 2, spectrumDisplay.stripFrame.height())
                spectrumDisplay.showAxes(stretchValue=True, widths=True,
                                         minimumWidth=GuiStrip.STRIP_MINIMUMWIDTH)

            except Exception as e:
                getLogger().warning(f'Impossible to restore spectrumDisplay(s) {e}')

        try:
            if current.strip is None and len(mainWindow.strips) > 0:
                current.strip = mainWindow.strips[0]
        except Exception as e:
            getLogger().warning(f'Error restoring current.strip: {e}')

    # GWV 07/08/2024: copied from Framework
    def _correctColours(self):
        """Autocorrect all colours that are too close to the background colour
        """
        from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND

        _app = self.application
        if _app.preferences.general.autoCorrectColours:
            project = _app.project
            # change sp colours
            for sp in project.spectra:
                if len(sp.axisCodes) > 1:
                    if sp.positiveContourColour and sp.positiveContourColour.startswith('#'):
                        sp.positiveContourColour = autoCorrectHexColour(sp.positiveContourColour,
                                                                        getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                    if sp.negativeContourColour and sp.negativeContourColour.startswith('#'):
                        sp.negativeContourColour = autoCorrectHexColour(sp.negativeContourColour,
                                                                        getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                elif sp.sliceColour and sp.sliceColour.startswith('#'):
                    sp.sliceColour = autoCorrectHexColour(sp.sliceColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            # change peakList colours
            for objList in project.peakLists:
                objList.textColour = autoCorrectHexColour(objList.textColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                objList.symbolColour = autoCorrectHexColour(objList.symbolColour,
                                                            getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            # change integralList colours
            for objList in project.integralLists:
                objList.textColour = autoCorrectHexColour(objList.textColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                objList.symbolColour = autoCorrectHexColour(objList.symbolColour,
                                                            getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            # change multipletList colours
            for objList in project.multipletLists:
                objList.textColour = autoCorrectHexColour(objList.textColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                objList.symbolColour = autoCorrectHexColour(objList.symbolColour,
                                                            getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            for mark in project.marks:
                mark.colour = autoCorrectHexColour(mark.colour,
                                                   getColours()[CCPNGLWIDGET_HEXBACKGROUND])

    # GWV 12/2/24; replaced by other implementation
    # def _updateCheckableMenuItems(self):
    #     # This has to be kept in sync with menu items below which are checkable,
    #     # and also with MODULE_DICT keys
    #     # The code is terrible because Qt has no easy way to get hold of menus / actions
    #
    #     mainWindow = self.mainWindow
    #     if mainWindow is None:
    #         # We have a UI with no mainWindow - nothing to do.
    #         return
    #
    #     menuChildren = mainWindow.menuBar().findChildren(QtWidgets.QMenu)
    #     if not menuChildren:
    #         return
    #
    #     topActionDict = {}
    #     for topMenu in menuChildren:
    #         mainActionDict = {mainAction.text(): mainAction for mainAction in topMenu.actions()}
    #
    #         topActionDict[topMenu.title()] = mainActionDict
    #
    #     openModuleKeys = set(mainWindow.moduleArea.modules.keys())
    #     for key, topActionText, mainActionText in (('SEQUENCE', 'Molecules', 'Show Sequence'),
    #                                                ('PYTHON CONSOLE', 'View', 'Python Console')):
    #         if key in openModuleKeys:
    #             if mainActionDict := topActionDict.get(topActionText):
    #                 if mainAction := mainActionDict.get(mainActionText):
    #                     mainAction.setChecked(True)

    def _makeActiveWindow(self):
        """Show and et self.mainWindow as the active window
        """
        # The next two lines are essential to have the QT main event loop associated
        # with the new mainWindow; without these, the program just terminates
        self.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(self.mainWindow)

    def startUi(self):
        """Start the UI
        """
        self._makeActiveWindow()
        self.application._initTipOfTheDay()

        # check whether to skip the execution loop for testing with mainWindow
        import builtins

        if not (_skip := getattr(builtins, '_skipExecuteLoop', False)):
            self._qtApp.start()

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
                popup = NewTermsConditionsPopup(self.mainWindow, trial=days,
                                                version=self.application.applicationVersion, modal=True)
            else:
                popup = RegisterPopup(self.mainWindow, trial=days, version=self.application.applicationVersion,
                                      modal=True)

            self.mainWindow.show()
            popup.exec_()
            self._qtApp.processEvents()

    def _setupMainWindow(self):
        """Set up mainWindow
        """
        _sideBar = self.mainWindow._getSideBar()
        _sideBar.buildTree(self.project, clear=True)
        # self.mainWindow._updateRestoreArchiveMenu()
        self.mainWindow.namespace['current'] = self.application.current

    def echoCommands(self, commands: typing.List[str]):
        """Echo commands strings, one by one, to logger
        and store them in internal list for perusal
        """
        REMOVEDEBUG = r'\(\S+\.\w+:\d+\)$'

        logger = getLogger()
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
        if pid is not None and pid.type in [PidLongClassName, PidShortClassName]:
            # get the GuiModule object By its Gid
            return self.application.mainWindow.moduleArea.modules.get(pid.id)

        return self.application.getByGid(gid)

    def _execUpdates(self):
        """Use the Update popup to execute any updates
        """
        from ccpn.framework.update.UpdatePopup import UpdatePopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            updatePopup = UpdatePopup(parent=self.mainWindow, mainWindow=self.mainWindow)
            updatePopup.exec_()

            # if updates have been installed then popup the quit dialog with no cancel button
            if updatePopup._updatesInstalled:
                self.mainWindow._closeWindowFromUpdate(disableCancel=True)

        else:
            MessageDialog.showWarning('Check For Updates',
                                      'Could not connect to the update server, please check your internet connection.')

    #-----------------------------------------------------------------------------------------
    # Helper methods
    #-----------------------------------------------------------------------------------------

    def _queryChoices(self, dataLoader: DataLoaderABC) -> tuple[DataLoaderABC, bool, bool]:
        """Query the user about his/her choice to import/new/cancel;
        set dataLoader.createNewProject
        :return (dataLoader, createNewProject:bool, ignore:bool) tuple
        """
        if not isinstance(dataLoader, DataLoaderABC):
            raise TypeError(f'Invalid dataLoader; got instance of {type(dataLoader)}')

        choices = ('Import', 'New project', 'Cancel')
        choice = MessageDialog.showMulti(
                f'Load {dataLoader.dataFormat}',
                f'How do you want to handle "{dataLoader.path}":',
                choices,
                parent=self.mainWindow,
                )

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

    def _getDataLoader(self, path, formatFilter=None, droppedOnSideBar=False) -> tuple[DataLoaderABC, bool, bool]:
        """Get dataLoader for path (or None if not present), optionally only testing for
        dataFormats defined in filter.
        Allows for reporting or checking through popups.
        Does not do the actual loading.

        :param path: the path to get a dataLoader for
        :param formatFilter: a list/tuple of optional dataFormat strings; filter optional dataLoaders for this
        :param: droppedOnSideBar: flag to indicate path dropped on the sidebar
        :returns a tuple (dataLoader, createNewProject, ignore)

        :raises RuntimeError in case of failure to define a proper dataLoader
        """
        # local import here
        from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader
        from ccpn.framework.lib.DataLoaders.SparkyDataLoader import SparkyDataLoader
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader
        from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import NmrPipeSpectrumLoader

        _path = aPath(path)
        if not _path.exists():
            raise RuntimeError(f'Path "{path}" does not exist')

        # get list of possible loaders;
        _loaders = _checkPathForDataLoader(path=path, formatFilter=formatFilter)
        if len(_loaders) == 0:
            raise RuntimeError(f'Unknown error finding a loader for {path}')


        # check the _loaders
        if _loaders[-1].isValid:
            # there is a valid one; use that
            dataLoader = _loaders[-1]
            errMsg = None

        else:
            dataLoader = None
            # We always get a loader back; report it here
            errMsg = f'{_loaders[-1].dataFormat} loader reported:\n\n{_loaders[-1].errorString}'

        # raise error if needed
        if errMsg:
            getLogger().warning(errMsg)
            raise RuntimeError(errMsg)

        createNewProject = dataLoader.createNewProject
        ignore = False
        path = dataLoader.path

        # Check that the path does not contain a bottom-level space
        if dataLoader.dataFormat in [CcpNmrV2ProjectDataLoader.dataFormat, CcpNmrV3ProjectDataLoader.dataFormat] and \
                ' ' in aPath(dataLoader.path).basename:
            MessageDialog.showWarning('Load Project', 'Encountered a problem loading:\n"%s"\n\n'
                                                      'Cannot load project folders where the project-name contains spaces.\n\n'
                                                      'Please rename the folder without spaces and try loading again.' % dataLoader.path)
            # skip loading bad projects
            ignore = True

        elif dataLoader.dataFormat == CcpNmrV2ProjectDataLoader.dataFormat:
            createNewProject = True
            dataLoader.createNewProject = True
            ok = MessageDialog.showYesNoWarning('Load Project',
                                                f'Project "{path.name}" was created with version-2 Analysis.\n'
                                                f'The project will be converted to a version-3 project in a temporary directory,\n'
                                                f'after which you can decide to save it.\n'
                                                '\n'
                                                'Do you want to continue loading? (Conversion may take a bit of time)')

            if not ok:
                # skip loading so that user can back-up/copy project
                getLogger().info(f'==> Cancelled loading ccpn project "{path}"')
                ignore = True

        elif dataLoader.dataFormat == CcpNmrV3ProjectDataLoader.dataFormat and dataLoader.projectNeedsUpgrade:
            createNewProject = True
            dataLoader.createNewProject = True

            DONT_OPEN = "Don't Open"
            CONTINUE = 'Continue'
            MAKE_ARCHIVE = 'Make a backup archive (.tgz) of the project'

            dataLoader.makeArchive = False
            ok = MessageDialog.showMulti(
                    'Load Project',
                    f'You are opening an older project (version {dataLoader.lastSavedVersion}) - {path.name}\n'
                    '\n'
                    f'When you save, it will be upgraded and will no longer be readable by program versions < {Project._LOWEST_COMPATIBLE_VERSION}\n',
                    texts=[DONT_OPEN, CONTINUE],
                    checkbox=MAKE_ARCHIVE, checked=False,
                    )

            if all(ss not in ok for ss in [DONT_OPEN, MAKE_ARCHIVE, CONTINUE]):
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
                                                f'"{dataLoader.dataSource.path}"\n'
                                                f'"{dataLoader.path}"\n'
                                                f'already exists in the project\n'
                                                '\n'
                                                'Do you want to load?'
                                                )

        elif dataLoader.dataFormat == NmrPipeSpectrumLoader.dataFormat:
            # NmrPipe file; check if it is large 3D/4D
            _ds = dataLoader.dataSource
            dims = _ds.dimensionCount
            expectedSize = _ds.expectedFileSizeInBytes / (1024 * 1024)
            if dims > 2 and expectedSize >= _ds.WARNING_FILE_SIZE and not _ds.bufferIsFilled:

                if droppedOnSideBar:
                    _txt1 = f'Loading Spectrum "{dataLoader.path}"'
                    _txt2 = f'The {dims}D NmrPipe file ({expectedSize:.1f} MB) will be automatically buffered when first displayed\n' \
                            f'Consider converting to Hdf5 format (Menu: Spectrum --> Convert to Hdf5)\n'
                    ok = MessageDialog.showOkCancel(_txt1, _txt2)
                    if not ok:
                        ignore = True

                else:
                    _txt1 = f'Displaying Spectrum "{dataLoader.path}"'
                    _txt2 = f'The {dims}D NmrPipe file ({expectedSize:.1f} MB) will be automatically buffered\n' \
                            f'Consider loading first and converting to Hdf5 format (Menu: Spectrum --> Convert to Hdf5)\n' \
                            '\n' \
                            'Do you want to display now? (the buffering may take a -little- while)'
                    ok = MessageDialog.showYesNoWarning(_txt1, _txt2)
                    if not ok:
                        ignore = True

        elif dataLoader.dataFormat == StarDataLoader.dataFormat and dataLoader:
            (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)
            if dataLoader and not ignore:
                title = 'New project from NmrStar' if createNewProject \
                         else 'Import from NmrStar'
                dataLoader.getDataBlock()  # this will read and parse the file
                popup = StarImporterPopup(dataLoader=dataLoader,
                                          parent=self.mainWindow,
                                          size=(700, 1000),
                                          title=title
                                          )
                popup.exec_()
                ignore = (popup.result == popup.CANCEL_PRESSED)

        elif dataLoader.dataFormat == DirectoryDataLoader.dataFormat:

            msg = None
            if dataLoader.count > MAXITEMLOADING or dataLoader.depth > MAXITEMDEPTH:
                _nSpectra = len([dl for dl in dataLoader.dataLoaders if dl.isSpectrumLoader and dl.isValid])
                _spectra = f', of which {_nSpectra} are spectra' if _nSpectra>0 else ''
                msg =  f'CAUTION: You are trying to load {dataLoader.count:d} items{_spectra}.\n'

                if dataLoader.depth > MAXITEMDEPTH:
                    msg += f'The folder is {dataLoader.depth}-subfolders deep.\n\n'

                msg += (f'It may take some time to load.\n\n'
                        f'Do you want to continue?')

            ignore = (bool(msg) and not MessageDialog.showYesNoWarning(f'Directory {dataLoader.path!r}\n', msg))

        dataLoader.createNewProject = createNewProject
        dataLoader.ignore = ignore
        return (dataLoader, createNewProject, ignore)

    #-----------------------------------------------------------------------------------------
    # Project and loading data related methods
    #-----------------------------------------------------------------------------------------

    @logCommand('application.')
    def newProject(self, name: str = 'newProject') -> Project | None:
        """Create a new project instance with name; create default project if name=None
        :return a Project instance or None
        """
        from ccpn.core.lib.ProjectLib import checkProjectName

        oldMainWindowPos = self.mainWindow.pos()
        if self.project and (self.project._undo is None or self.project._undo.isDirty()):
            # if not self.project.isTemporary:
            if self.project._undo is None or self.project._undo.isDirty():
                _CANCEL = 'Cancel'
                _OK = 'Discard and New'
                _SAVE = 'Save'
                msg = (f"The current project has been modified and requires saving. Do you want save the current "
                       f"project first, or discard the changes and continue creating a new project?")
                reply = MessageDialog.showMulti('New Project...', msg,
                                                texts=[_OK, _CANCEL, _SAVE],
                                                okText=_OK, cancelText=_CANCEL,
                                                parent=self.mainWindow)
                if reply == _CANCEL:
                    # cancel the new-operation
                    return
                elif reply == _SAVE:
                    # save first
                    if not self.saveProject():
                        # cancel the new-operation if there was an issue saving
                        return

        if (_name := checkProjectName(name, correctName=True)) != name:
            MessageDialog.showInfo('New Project',
                                   f'Project name changed from "{name}" to "{_name}"\nSee console/log for details',
                                   parent=self)

        with catchExceptions(errorStringTemplate='Error creating new project: %s'):
            if self.mainWindow:
                self.mainWindow.moduleArea._closeAll()
            newProject = self.application._newProject(name=_name)
            if newProject is None:
                raise RuntimeError('Unable to create new project')

            self.mainWindow.move(oldMainWindowPos)

            return newProject

    def _loadProject(self, dataLoader=None, path=None) -> Project | bool | None:
        """Helper function, loading project from dataLoader instance
        check and query for closing current project
        build the project Gui elements
        attempts to restore on failure to load a project

        :returns project instance or None
        """
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import checkPathForDataLoader

        if dataLoader is None and path is not None:
            if (dataLoader := checkPathForDataLoader(path)) is None:
                raise RuntimeError(f'Loading project: No suitable dataLoader found for {path}')
        if dataLoader is None:
            raise RuntimeError('Loading project: No suitable dataLoader')

        if dataLoader is None and path is not None:
            dataLoader = checkPathForDataLoader(path)
        if dataLoader is None:
            getLogger().error('No suitable dataLoader found')
            return None
        if not dataLoader.createNewProject:
            raise RuntimeError(f'DataLoader {dataLoader} does not create a new project')

        oldProjectLoader = None
        oldProjectIsTemporary = True
        oldMainWindowPos = self.mainWindow and self.mainWindow.pos()

        if self.project:
            # if not self.project.isTemporary:
            if self.project._undo is None or self.project._undo.isDirty():
                _CANCEL = 'Cancel'
                _OK = 'Discard and Load'
                _SAVE = 'Save'
                msg = (f"The current project has been modified and requires saving. Do you want save the current "
                       f"project first, or discard the changes and continue loading?")
                reply = MessageDialog.showMulti('Load Project...', msg,
                                                texts=[_OK, _CANCEL, _SAVE],
                                                okText=_OK, cancelText=_CANCEL,
                                                parent=self.mainWindow)
                if reply == _CANCEL:
                    # cancel the load-operation
                    return None
                elif reply == _SAVE:
                    # save first
                    if not self.saveProject():
                        # cancel the load-operation if there was an issue saving
                        return None

            # Some error recovery; store info to re-open the current project (or a new default)
            oldProjectLoader = CcpNmrV3ProjectDataLoader(self.project.path)
            oldProjectIsTemporary = self.project.isTemporary

        error = False
        try:
            if self.project:
                # NOTE:ED - getting a strange QT bug disabling the menu-bar from here
                #  I think because the main-window isn't visible on the first load :|
                with busyHandler(self.mainWindow, title='Loading',
                                 text=f'Loading project {dataLoader.path} ...', closeDelay=1000):
                    if not (_loaded := dataLoader.load()):
                        MessageDialog.showWarning('Loading Project',
                                                  f'There was a problem loading project {dataLoader.path}\n'
                                                  f'Please check the log for more information.',
                                                  parent=self.mainWindow)
                        return None
            else:
                # busy-status not required on the first load
                if not (_loaded := dataLoader.load()):
                    MessageDialog.showWarning('Loading Project',
                                              f'There was a problem loading project {dataLoader.path}\n'
                                              f'Please check the log for more information.',
                                              parent=self.mainWindow)
                    return None
            newProject = _loaded[0]

            # if the new project contains invalid spectra then open the popup to see them
            self.mainWindow._checkForBadSpectra(newProject)
            if oldMainWindowPos:
                self.mainWindow.move(oldMainWindowPos)

            error = False

        except (RuntimeError, ValueError, ApiError) as es:
            MessageDialog.showError('Error loading Project:', f'{es}', parent=self.mainWindow)
            error = True

        except NotImplementedError as es:
            MessageDialog.showError('Error loading Project:', f'{es}', parent=self.mainWindow)
            error = True

        finally:
            if error:
                # Try to restore the state
                # reload existing or create a new temporary one (as the original temporary
                # get deleted by the closing)
                newProject = None
                if oldProjectIsTemporary:
                    newProject = self.application._newProject()
                elif oldProjectLoader:
                    newProject = oldProjectLoader.load()[0]  # dataLoaders return a list

        return newProject

    # @logCommand('application.') # eventually decorated by  _loadData()
    def loadProject(self, path=None) -> Project | None:
        """Loads project defined by path
        :return a Project instance or None
        """
        if path is None:
            dialog = FileDialog.ProjectFileDialog(parent=self.mainWindow, acceptMode='open')
            dialog._show()

            if (path := dialog.selectedFile()) is None:
                return None

        with self.application.pauseAutoBackups():
            with catchExceptions(errorStringTemplate='Error loading project: %s'):
                dataLoader, createNewProject, ignore = self._getDataLoader(path)
                if ignore or dataLoader is None or not createNewProject:
                    return None

                # load the project using the dataLoader;
                # We'll ask framework who will pass it back to ui._loadProject
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
            _sideBar = self.mainWindow._getSideBar()
            _sideBar.clearSideBar()
            _sideBar.deleteLater()
            self.mainWindow.deleteLater()
            self._mainWindow = None

    @logCommand('application.')
    def saveProjectAs(self, newPath=None, overwrite: bool = False) -> bool:
        """Opens save Project to newPath.
        Optionally open file dialog.
        :param newPath: new path to save project (str | Path instance)
        :param overwrite: flag to indicate overwriting of existing path
        :return True if successful
        """
        from ccpn.core.lib.ProjectLib import checkProjectName

        title = 'Project SaveAs'
        oldPath = Path(self.project.path)

        if newPath is None:
            # try to create a new path from the old one
            if self.project.isTemporary:
                _newName = self.project.name
                _newPath = (aPath('~') / _newName).assureSuffix(CCPN_DIRECTORY_SUFFIX)
            else:
                _newName = f'{self.project.name}_new'
                _newPath = oldPath.with_name(_newName).assureSuffix(CCPN_DIRECTORY_SUFFIX)
            # query for this path
            dialog = FileDialog.ProjectSaveFileDialog(parent=self.mainWindow,
                                                      directory=_newPath.parent.asString(),
                                                      selectFile=_newPath.name,
                                                      acceptMode='save')
            dialog._show()
            if (newPath := dialog.selectedFile()) is None:
                return False
        newPath = aPath(newPath).assureSuffix(CCPN_DIRECTORY_SUFFIX)

        if newPath.exists() and \
                (newPath.is_file() or (newPath.is_dir() and len(newPath.listdir(excludeDotFiles=False)) > 0)) and \
                not overwrite:
            msg = f'Path "{newPath}" already exists; overwrite?'
            if not MessageDialog.showYesNo(title, msg):
                return False

        # check the project name derived from path; not all is allowed
        newName = newPath.basename
        if (_nameFromPath := checkProjectName(newName, correctName=True)) != newName:
            MessageDialog.showInfo(title,
                                   f'Project name will be changed from "{newName}" to "{_nameFromPath}"\n'
                                   f'See console/log for details',
                                   parent=self.mainWindow)
            newPath = (newPath.parent / _nameFromPath).assureSuffix(CCPN_DIRECTORY_SUFFIX)
            newName = _nameFromPath

        # Checking copy subdirectories
        _sizeDict = self.project._getSubdirectorySizes(CCPN_SAVEAS_SUB_DIRECTORIES, sizeInMB=True)
        _totalSize = sum(_sizeDict.values())
        _tmp = '%.1f' % _totalSize
        msg = f'Also copy sub-directories (data, archives, scripts, ...) ({_tmp} MB)?\n'

        # Check for any inside spectra
        _insideSpectra = [sp for sp in self.project.spectra if sp._isInside]
        _size = '%.1f' % (sum([sp.dataSource.expectedFileSizeInBytes for sp in _insideSpectra]) / (1024 * 1024))
        if len(_insideSpectra) == 1:
            msg += f'\nNote that the data of {_insideSpectra[0].pid} ({_size} MB) is in "{oldPath.name}/data/spectra"\n'
        elif len(_insideSpectra) > 1:
            msg += f'\nNote that the data of {len(_insideSpectra)} spectra ({_size} MB) are in "{oldPath.name}/data/spectra"\n'

        if self.project.isTemporary:
            copySubDirs = True
        else:
            if (copySubDirs := MessageDialog.showYesNoCancel(title, msg)) is None:
                # pressed "cancel"
                return False

        with catchExceptions(errorStringTemplate='Error saving project: %s'):
            with MessageDialog.progressManager(self.mainWindow, f'Saving project as {newPath} ... '):
                try:
                    if not self.application._saveProjectAs(newPath=newPath, overwrite=True,
                                                           copySubDirectories=copySubDirs):
                        txt = f"Saving project to {newPath} aborted; check log for details"
                        MessageDialog.showError("Project SaveAs", txt, parent=self.mainWindow)
                        return False

                except (PermissionError, FileNotFoundError):
                    msg = f'Folder {newPath} may be read-only'
                    MessageDialog.showWarning('Save project', msg)
                    return False

                except RuntimeWarning as es:
                    msg = f'Error saving {newPath}:\n{es}'
                    MessageDialog.showWarning('Save project', msg)
                    return False

        # ED: 2024/05/03 - logged from notifier
        return True

    @logCommand('application.')
    def saveProject(self) -> bool:
        """Save project.
        :return True if successful
        """
        if self.project.isTemporary:
            return self.saveProjectAs()

        if self.project.isReadOnly and not MessageDialog.showYesNo(
                'Save Project',
                'The project is marked as read-only.\n'
                'This can be changed by clicking the lock-icon in the bottom-right.\n\n'
                'Do you want to continue saving?\n',
                ):
            return True

        with catchExceptions(errorStringTemplate='Error saving project: %s'):
            with MessageDialog.progressManager(self.mainWindow, 'Saving project ... '):
                try:
                    if not self.application._saveProject():
                        return False
                except (PermissionError, FileNotFoundError):
                    msg = 'Folder may be read-only'
                    MessageDialog.showWarning('Save project', msg)
                    return True

        # ED: 2024/05/03 - logged from notifier
        return True

    def _loadData(self, dataLoader) -> list:
        """Load the data defined by dataLoader instance, catching errors
        and suspending sidebar.
        :return a list of loaded opjects
        """
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader

        result = []  # the load may fail
        errorStringTemplate = f'Loading "{dataLoader.path}" failed:\n\n%s'
        with catchExceptions(errorStringTemplate=errorStringTemplate):
            # For data loads that are possibly time-consuming, use progressManager
            if isinstance(dataLoader, (StarDataLoader, NefDataLoader)):
                with MessageDialog.progressManager(self.mainWindow, 'Importing data ... '):
                    result = dataLoader.load()
            else:
                result = dataLoader.load()
        return result

    # @logCommand('application.') # eventually decorated by  _loadData()
    def loadData(self, *paths, formatFilter: (list, tuple) = None) -> list:
        """Loads data from paths; query if none supplied
        Optionally filter for dataFormat(s)
        :param *paths: argument list of path's (str or Path instances)
        :param formatFilter: list/tuple of dataFormat strings
        :returns list of loaded objects
        """
        if not paths:
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
                MessageDialog.showError('Load Data', txt, parent=self)
                continue

            try:
                dataLoader, createNewProject, ignore = self._getDataLoader(path, formatFilter=formatFilter)

            except RuntimeError as es:
                MessageDialog.showError(f'Loading "{_path}"',
                                        f'{es}',
                                        parent=self.mainWindow)
                if len(paths) == 1:
                    return []
                else:
                    continue

            if ignore:
                continue

            dataLoaders.append(dataLoader)

        # load the project using the dataLoaders;
        # We'll ask framework who will pass it back as ui._loadData calls
        objs = self.application._loadData(dataLoaders)
        if len(objs) == 0:
            _pp = ','.join(f'"{p}"' for p in paths)
            txt = f'No objects were loaded from {_pp}'
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

        if not paths:
            # This only works with non-native file dialog; override the default behavior
            dialog = FileDialog.SpectrumFileDialog(parent=self.mainWindow, acceptMode='load',
                                                   useNative=False)
            dialog._show()
            paths = dialog.selectedFiles()

        if not paths:
            return []

        formatFilter = list(getSpectrumLoaders().keys())

        spectrumLoaders = []
        count = 0
        # Recursively search all paths
        for path in paths:
            _path = aPath(path)
            if _path.is_dir():
                dirLoader = DirectoryDataLoader(path, recursive=False, formatFilter=formatFilter)
                spectrumLoaders.append(dirLoader)
                count += len(dirLoader)

            elif (sLoader := checkPathForDataLoader(path, formatFilter=formatFilter)) is not None:
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

    @logCommand('ui.')
    def makeStripPlot(self, includePeakLists=True, includeNmrChains=True, includeNmrChainPullSelection=True):
        """Make a strip plot from peaks or nmrChains
        """
        from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup

        if not self.project.peaks and not self.project.nmrResidues and not self.project.nmrChains:
            getLogger().warning('Cannot make strip plot, nothing to display')
            MessageDialog.showWarning('Cannot make strip plot,', 'nothing to display')
            return

        if self.current.strip is None or self.current.strip.isDeleted:
            MessageDialog.showWarning('Make Strip Plot', 'No selected spectrumDisplay')
            return

        popup = StripPlotPopup(parent=self.mainWindow, mainWindow=self.mainWindow,
                               spectrumDisplay=self.current.strip.spectrumDisplay,
                               includePeakLists=includePeakLists,
                               includeNmrChains=includeNmrChains,
                               includeNmrChainPullSelection=includeNmrChainPullSelection,
                               includeSpectrumTable=False)
        popup.exec_()

    #-----------------------------------------------------------------------------------------
    # View
    #-----------------------------------------------------------------------------------------

    def _showModule(self, moduleClass, position: str = 'bottom', relativeTo = None,
                    selection: typing.Any = None, selectFirstItem: bool = True):
        """Helper function to avoid code duplication.
        Initiate and add an instance of moduleClass; optionally call setTable with selection
        :param moduleClass: module class to display an instance
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param selection: optional entry to select
        :param selectFirstItem: flag to select first item
        :return a new ModuleClass instance
        """
        if not issubclass(moduleClass, CcpnModule):
            raise TypeError(f'Expected subclass of {CcpnModule}; got {moduleClass}')

        _module = moduleClass(mainWindow=self.mainWindow, selectFirstItem=selectFirstItem)
        self.mainWindow._addModule(_module, position=position, relativeTo=relativeTo)
        if selection:
            _module.selectTable(selection)
        return _module

    @logCommand('ui.')
    def showChemicalShiftTable(self, position: str = 'bottom', relativeTo = None, chemicalShiftList=None):
        """Show the ChemicalShiftTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param chemicalShiftList: optional ChemicalShiftList to display
        """
        from ccpn.ui.gui.modules.ChemicalShiftTable import ChemicalShiftTableModule
        return self._showModule(ChemicalShiftTableModule, position=position, relativeTo=relativeTo,
                                selection=chemicalShiftList)

    @logCommand('ui.')
    def showNmrResidueTable(self, position='bottom', relativeTo = None, nmrChain=None):
        """Show the NmrResidueTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param nmrChain: optional NmrChain with NmrResidue's to display
        """
        from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTableModule
        return self._showModule(NmrResidueTableModule, position=position, relativeTo=relativeTo,
                                selection=nmrChain)

    @logCommand('ui.')
    def showResidueTable(self, position='bottom', relativeTo = None, chain=None):
        """Show the ResidueTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
       :param chain: optional chain with Residue's to display
        """
        from ccpn.ui.gui.modules.ResidueTable import ResidueTableModule
        return self._showModule(ResidueTableModule, position=position, relativeTo=relativeTo,
                                selection=chain)

    @logCommand('ui.')
    def showPeakTable(self, position='bottom', relativeTo = None, peakList=None):
        """Show the PeakTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param peakList: optional peakList with Peaks to display; default derived from current.peaks
        """
        from ccpn.ui.gui.modules.PeakTable import PeakTableModule
        _module = self._showModule(PeakTableModule, position=position, relativeTo=relativeTo)
        if not peakList and self.current.peak:
            peakList = self.current.peak.peakList
        if peakList:
            _module.selectTable(peakList)
            _module.selectPeaks(self.current.peaks)

    @logCommand('ui.')
    def showIntegralTable(self, position='bottom', relativeTo = None, integralList=None):
        """Show the IntegralTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param integralList: optional integralList to display
        """
        from ccpn.ui.gui.modules.IntegralTable import IntegralTableModule
        return self._showModule(IntegralTableModule, position=position, selection=integralList)

    @logCommand('ui.')
    def showMultipletTable(self, position='bottom', relativeTo = None, multipletList=None):
        """Show the MultipletTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param multipletList: optional multipletList to display
        """
        from ccpn.ui.gui.modules.MultipletTable import MultipletTableModule
        return self._showModule(MultipletTableModule, position=position, relativeTo=relativeTo,
                                selection=multipletList)

    @logCommand('ui.')
    def showDataTable(self, position='bottom', relativeTo = None, dataTable=None):
        """Show the DataTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param dataTable: optional dataTable to display
        """
        from ccpn.ui.gui.modules.DataTableModule import DataTableModule
        return self._showModule(DataTableModule, position=position, relativeTo=relativeTo,
                                selection=dataTable)

    @logCommand('ui.')
    def showRestraintTable(self, position='bottom', relativeTo=None, restraintTable=None):
        """Show the restraintTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param restraintTable: optional restraintTable to display
        """
        from ccpn.ui.gui.modules.RestraintTableModule import RestraintTableModule
        return self._showModule(RestraintTableModule, position=position, relativeTo=relativeTo,
                                selection=restraintTable)

    @logCommand('ui.')
    def showViolationTable(self, position='bottom', relativeTo=None, violationTable=None):
        """Show the restraintTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param violationTable: optional violationTable to display
        """
        from ccpn.ui.gui.modules.ViolationTableModule import ViolationTableModule
        return self._showModule(ViolationTableModule, position=position, relativeTo=relativeTo,
                                selection=violationTable)

    @logCommand('ui.')
    def showStructureEnsembleTable(self, position='bottom', relativeTo=None, structureEnsemble=None):
        """Show the structureEnsembleTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param structureEnsemble: optional structure ensemble to display
        """
        from ccpn.ui.gui.modules.StructureTable import StructureTableModule
        return self._showModule(StructureTableModule, position=position, relativeTo=relativeTo,
                                selection=structureEnsemble)

    def showChemicalShiftMapping(self, position: str = 'top', relativeTo = None):
        """Show the ChemicalShiftMapping module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        """
        from ccpn.ui.gui.modules.experimentAnalysis.ChemicalShiftMappingGuiModule import ChemicalShiftMappingGuiModule
        return self._showModule(ChemicalShiftMappingGuiModule, position=position, relativeTo=relativeTo)

    def showNotesEditor(self, position: str = 'top', relativeTo = None, note=None):
        """Show the Notes editor module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param note: optional note to display
        """
        from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule
        _module = self._showModule(NotesEditorModule, position=position, relativeTo=relativeTo)
        if note:
            _module.selectNote(note)
        return _module

    #-----------------------------------------------------------------------------------------
    # Molecules
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def showResidueInformation(self, position='bottom', relativeTo = None):
        """Displays Residue Information module.
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        """
        from ccpn.ui.gui.modules.ResidueInformation import ResidueInformation

        if not self.project.residues:
            getLogger().warning(
                'No Residues in project. Residue Information Module requires Residues in the project to launch.')
            MessageDialog.showWarning('No Residues in project.',
                                      'Residue Information Module requires Residues in the project to launch.')
            return

        _module = ResidueInformation(mainWindow=self.mainWindow)
        self.mainWindow._addModule(_module, position=position, relativeTo=relativeTo)
        return _module

    @logCommand('ui.')
    def showReferenceChemicalShifts(self, position='left', relativeTo = None):
        """Displays Reference Chemical Shifts module.
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
       """
        from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts

        _module = ReferenceChemicalShifts(mainWindow=self.mainWindow)
        self.mainWindow._addModule(_module, position=position, relativeTo=relativeTo)
        return _module

    #-----------------------------------------------------------------------------------------
    # Macro
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def newMacroEditor(self, path=None, position='top'):
        """Open a new Module to edit macros
        """
        # local to prevent circular import
        from ccpn.ui.gui.modules.MacroEditor import MacroEditor

        path = str(path) if path is not None else None
        macroEditor = MacroEditor(mainWindow=self.mainWindow, filePath=path, restore=False)
        self.mainWindow._addModule(macroEditor, position=position)
        return macroEditor

    @logCommand('ui.')
    def runMacro(self, path: str | Path = None):
        """
        Runs a python macro if a path is specified, or opens a dialog box for selection of a macro file and then
        runs the selected macro.
        :param path: optional path to python file to run as macro
        """
        if path is None:
            fType = '*.py'
            dialog = FileDialog.MacrosFileDialog(parent=self.mainWindow, acceptMode='run', fileFilter=fType)
            dialog._show()
            path = dialog.selectedFile()
            if not path:
                return

        # use application to run the macro
        self.application.runMacro(path)
