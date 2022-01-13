#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-13 17:00:00 +0000 (Thu, January 13, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import time as systime
#
#
# if not hasattr(systime, 'clock'):
#     # NOTE:ED - quick patch to fix bug in pyqt 5.9
#     systime.clock = systime.process_time

# how frequently to check if license dialog has closed when waiting to show the tip of the day
WAIT_EVENT_LOOP_EMPTY = 0
WAIT_LICENSE_DIALOG_CLOSE_TIME = 100

import json
import logging
import os
import platform
import sys
import tarfile
import tempfile
import re
import subprocess
from typing import Union, Optional
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from distutils.dir_util import copy_tree
from functools import partial

from typing import List, Tuple, Sequence

from tqdm import tqdm

from ccpn.core.IntegralList import IntegralList
from ccpn.core.PeakList import PeakList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import NotifierBase, Notifier
from ccpn.core.lib.Pid import Pid, PREFIXSEP

from ccpn.framework.Application import getApplication
from ccpn.framework import Version
from ccpn.framework.credits import printCreditsText
from ccpn.framework.Current import Current
from ccpn.framework.lib.pipeline.PipelineBase import Pipeline
from ccpn.framework.Translation import languages, defaultLanguage
from ccpn.framework.Translation import translator
from ccpn.framework.PathsAndUrls import userPreferencesPath
from ccpn.framework.PathsAndUrls import userPreferencesDirectory
from ccpn.framework.PathsAndUrls import macroPath
from ccpn.framework.lib.DataLoaders.DataLoaderABC import checkPathForDataLoader

from ccpn.ui import interfaces, defaultInterface
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FileDialog import ProjectFileDialog, DataFileDialog, NefFileDialog, \
    ArchivesFileDialog, MacrosFileDialog, CcpnMacrosFileDialog, LayoutsFileDialog, NMRStarFileDialog, SpectrumFileDialog, \
    ProjectSaveFileDialog
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup
from ccpn.util import Logging
from ccpn.util import Path
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Common import uniquify, isWindowsOS, isMacOS, isIterable
from ccpn.util.Logging import getLogger
from ccpn.util import Layout

from ccpn.ui.gui.Gui import Gui
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import catchExceptions, undoBlockWithoutSideBar, undoBlock, \
    notificationEchoBlocking, logCommandManager

from ccpn.ui.gui.widgets.Menu import SHOWMODULESMENU, CCPNMACROSMENU, TUTORIALSMENU, CCPNPLUGINSMENU, PLUGINSMENU
from ccpn.ui.gui.widgets.TipOfTheDay import TipOfTheDayWindow, MODE_KEY_CONCEPTS

from PyQt5.QtCore import QTimer

import faulthandler


faulthandler.enable()

_DEBUG = False

AnalysisAssign = 'AnalysisAssign'
AnalysisScreen = 'AnalysisScreen'
AnalysisMetabolomics = 'AnalysisMetabolomics'
AnalysisStructure = 'AnalysisStructure'
ApplicationNames = [AnalysisAssign, AnalysisScreen, AnalysisMetabolomics, AnalysisStructure]
interfaceNames = ('NoUi', 'Gui')
DataDirName = 'data'
SpectraDirName = 'spectra'
PluginDataDirName = 'pluginData'
ScriptsDirName = 'scripts'
MacrosDirName = 'macros'


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


def defineProgramArguments():
    """Define the arguments of the program
    return argparse instance
    """
    import argparse

    parser = argparse.ArgumentParser(description='Process startup arguments')
    # for component in componentNames:
    #   parser.add_argument('--'+component.lower(), dest='include'+component, action='store_true',
    #                                               help='Show %s component' % component.lower())
    parser.add_argument('--language',
                        help=('Language for menus, etc.; valid options = (%s); default=%s' %
                              ('|'.join(languages), defaultLanguage)))
    parser.add_argument('--interface',
                        help=('User interface, to use; one of  = (%s); default=%s' %
                              ('|'.join(interfaces), defaultInterface)),
                        default=defaultInterface)
    parser.add_argument('--skip-user-preferences', dest='skipUserPreferences', action='store_true',
                        help='Skip loading user preferences')
    parser.add_argument('--dark', dest='darkColourScheme', action='store_true',
                        help='Use dark colour scheme')
    parser.add_argument('--light', dest='lightColourScheme', action='store_true',
                        help='Use dark colour scheme')
    parser.add_argument('--nologging', dest='nologging', action='store_true', help='Do not log information to a file')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Set logging level to debug')
    parser.add_argument('--debug1', dest='debug', action='store_true', help='Set logging level to debug1 (=debug)')
    parser.add_argument('--debug2', dest='debug2', action='store_true', help='Set logging level to debug2')
    parser.add_argument('--debug3', dest='debug3', action='store_true', help='Set logging level to debug3')

    # Ccpn logging options - traceback can sometimes be masked in undo/redo
    # --disable-undo-exception removes the try:except to allow full traceback to occur
    parser.add_argument('--disable-undo-exception', dest='disableUndoException', action='store_true', help='Disable exception wrapping undo/redo actions, reserved for high-level debugging.')
    # log information at end of undo/redo if exception occurs (not called if --disable-undo-exception set), calls _logObjects
    parser.add_argument('--ccpn-logging', dest='ccpnLogging', action='store_true', help='Additional logging of some ccpn objects, reserved for high-level debugging.')

    parser.add_argument('projectPath', nargs='?', help='Project path')

    return parser


class Arguments:
    """Class for setting FrameWork input arguments directly"""
    language = defaultLanguage
    interface = 'NoUi'
    nologging = True
    debug = False
    debug2 = False
    debug3 = False
    skipUserPreferences = True
    projectPath = None
    _skipUpdates = False

    def __init__(self, projectPath=None, **kwds):

        # Dummy values
        for component in ApplicationNames:
            setattr(self, 'include' + component, None)

        self.projectPath = projectPath
        for tag, val in kwds.items():
            setattr(self, tag, val)


def createFramework(projectPath=None, **kwds):
    args = Arguments(projectPath=projectPath, **kwds)
    result = Framework('CcpNmr', Version.applicationVersion, args)
    result.start()
    #
    return result


from threading import Thread
from time import time, sleep


class AutoBackup(Thread):

    def __init__(self, q, backupFunction, sleepTime=1):
        super().__init__()
        self.sleepTime = sleepTime
        self.q = q
        self.backupProject = backupFunction
        self.startTime = None

    def run(self):
        self.startTime = time()
        while True:
            waitTime = None
            if not self.q.empty():
                waitTime = self.q.get()
            if waitTime is None:
                sleep(self.sleepTime)
            elif waitTime == 'kill':
                return
            elif (time() - self.startTime) < waitTime:
                sleep(self.sleepTime)
            else:
                self.startTime = time()
                try:
                    self.backupProject()
                except:
                    pass


class Framework(NotifierBase):
    """
    The Framework class is the base class for all applications.
    """

    def __init__(self, applicationName, applicationVersion, args=Arguments()):

        self.args = args
        self.applicationName = applicationName
        self.applicationVersion = applicationVersion
        # NOTE:ED - what is revision for? there are no uses and causes a new error for sphinx documentation unless a string
        # self.revision = Version.revision

        self.plugins = []  # Hack for now, how should we store these?
        self.ccpnModules = []

        printCreditsText(sys.stderr, applicationName, applicationVersion)

        # self.setupComponents(args)

        self.useFileLogger = not self.args.nologging
        if self.args.debug3:
            self.level = Logging.DEBUG3
        elif self.args.debug2:
            self.level = Logging.DEBUG2
        elif self.args.debug:
            self.level = logging.DEBUG
        else:
            self.level = logging.INFO

        self.current = None

        self.preferences = None  # initialised by self._getUserPrefs
        self.layout = None  # initialised by self._getUserLayout
        self.styleSheet = None  # initialised by self.getStyleSheet
        self.colourScheme = None  # initialised by self.getStyleSheet

        # Necessary as attribute is queried during initialisation:
        self._mainWindow = None

        # This is needed to make project available in NoUi (if nothing else)
        self._project = None

        # Blocking level for command echo and logging
        self._echoBlocking = 0
        self._enableLoggingToConsole = True

        self._backupTimerQ = None
        self.autoBackupThread = None

        # Assure that .ccpn exists
        ccpnDir = Path.aPath(userPreferencesDirectory)
        if not ccpnDir.exists():
            ccpnDir.mkdir()
        self._getUserPrefs()

        if hasattr(self.args, 'darkColourScheme') and hasattr(self.args, 'lightColourScheme'):
            # set the preferences if added from the commandline
            # this causes errors when running the nose_tests
            if self.args.darkColourScheme:
                self.preferences.general.colourScheme = 'dark'
            elif self.args.lightColourScheme:
                self.preferences.general.colourScheme = 'light'

        self._tip_of_the_day = None
        self._initial_show_timer = None
        self._key_concepts = None

        self._registrationDict = {}
        self._setLanguage()
        self.styleSheet = None
        self.ui = self._getUI()
        self.setupMenus()
        self.feedbackPopup = None
        self.submitMacroPopup = None
        self.updatePopup = None
        self._disableUndoException = getattr(self.args, 'disableUndoException', False)
        self._ccpnLogging = getattr(self.args, 'ccpnLogging', False)

        # register dataLoaders for the first and only time
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import getDataLoaders

        self._dataLoaders = getDataLoaders()

        # register SpectrumDataSource formats for the first and only time
        from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import getDataFormats

        self._spectrumDataSourceFormats = getDataFormats()

    @property
    def _isInDebugMode(self) -> bool:
        """Return True if either of the debug flags has been set
        CCPNINTERNAL: used throughout to check
        """
        if self.level == Logging.DEBUG1 or self.level == Logging.DEBUG2 or self.level == Logging.DEBUG3:
            return True
        return False

    @property
    def hasGui(self) -> bool:
        """Return True if application has a gui"""
        return isinstance(self.ui, Gui)

    @property
    def mainWindow(self):
        """:returns: MainWindow instance if application has a Gui or None otherwise
        """
        if self.hasGui:
            return self.ui.mainWindow
        return None

    @property
    def project(self):
        """Return project"""
        return self._project

    def _testShortcuts0(self):
        print('>>> Testing shortcuts0')

    def _testShortcuts1(self):
        print('>>> Testing shortcuts1')

    def start(self):
        """Start the program execution
        """

        # register the programme for later
        from ccpn.framework.Application import ApplicationContainer

        container = ApplicationContainer()
        container.register(self)

        self._initialiseFonts()

        # NOTE:ED - there are currently issues when loading projects from the command line, or from test cases
        #   There is no project.application and project is None
        #   The Logger instantiated is the default logger, required adding extra methods so that, e.g., echoInfo worked
        #   logCommand has no self.project.application, and requires getApplication() instead
        #   There is NoUi instantiated yet, so temporarily added loadProject to Ui class called by loadProject below)
        # Load / create project
        projectPath = self.args.projectPath
        if projectPath:
            project = self.loadProject(projectPath)

        else:
            project = self.newProject()
        self._updateCheckableMenuItems()

        if self.preferences.general.checkUpdatesAtStartup and not getattr(self.args, '_skipUpdates', False):
            if not self.ui._checkUpdates():
                return

        if not self.ui._checkRegistration():
            return

        # Needed in case project load failed
        if not project:
            sys.stderr.write('==> No project, aborting ...\n')
            return

        self.updateAutoBackup()

        sys.stderr.write('==> Done, %s is starting\n' % self.applicationName)

        # self.project = project
        self.ui.start()
        self._cleanup()

    def updateAutoBackup(self):

        if self.preferences.general.autoBackupEnabled:
            self.setAutoBackupTime(self.preferences.general.autoBackupFrequency)
        else:
            self.setAutoBackupTime(None)

    def setAutoBackupTime(self, time):
        # TODO: Need to add logging...
        if self._backupTimerQ is None:
            from queue import Queue

            self._backupTimerQ = Queue(maxsize=1)
        if self._backupTimerQ.full():
            self._backupTimerQ.get()
        if isinstance(time, (float, int)):
            self._backupTimerQ.put(time * 60)
        else:
            self._backupTimerQ.put(time)
        if self.autoBackupThread is None:
            self.autoBackupThread = AutoBackup(q=self._backupTimerQ,
                                               backupFunction=self.backupProject)
            self.autoBackupThread.start()

    def _cleanup(self):
        self.setAutoBackupTime('kill')
        # project._resetUndo(debug=_DEBUG)
        pass

    def backupProject(self):
        apiIo.backupProject(self.project._wrappedData.parent)
        backupPath = self.project.backupPath

        backupStatePath = Path.fetchDir(backupPath, Layout.StateDirName)

        copy_tree(self.statePath, backupStatePath)
        layoutFile = os.path.join(backupStatePath, Layout.DefaultLayoutFileName)
        Layout.saveLayoutToJson(self.ui.mainWindow, layoutFile)
        self.current._dumpStateToFile(backupStatePath)

        #Spectra should not be copied over. Dangerous for disk space
        # backupDataPath = Path.fetchDir(backupPath, DataDirName)

        #   TODO add other files inside this dirs
        backupScriptsPath = Path.fetchDir(backupPath, ScriptsDirName)
        backupLogsPath = Path.fetchDir(backupPath, ScriptsDirName)

    def _initialiseProject(self, project: Project):
        """Initialise project and set up links and objects that involve it"""

        # Linkages
        self._project = project
        project._application = self
        # project._appBase = self  # _appBase is defined in project so the UI instantiation can happen

        # Logging
        logger = getLogger()
        Logging.setLevel(logger, self.level)
        logger.debug('Framework._initialiseProject>>>')

        # Set up current; we need it when restoring
        self.current = Current(project=project)

        # This wraps the underlying data, including the wrapped graphics data
        #  - the project is now ready to use
        project._initialiseProject()

        # Adapt project to preferences
        self.applyPreferences(project)

        # init application directory
        self.scriptsPath = self.scriptsPath
        self.pymolScriptsPath = Path.fetchDir(self.scriptsPath, 'pymol')
        self.statePath = self.statePath
        self.dataPath = self.dataPath
        self.pipelinePath = self.pipelinePath
        self.spectraPath = self.spectraPath
        self.pluginDataPath = self.pluginDataPath

        # restore current
        self.current._restoreStateFromFile(self.statePath)

        if self.hasGui:
            self.ui.initialize(self._mainWindow)
            # Get the mainWindow out of the application top level once it's been transferred to ui
            del self._mainWindow
        else:
            # The NoUi version has no mainWindow
            self.ui.initialize(None)

    # def _refreshAfterSave(self):
    #     """Refresh user interface after project save (which may have caused project rename)"""
    #
    #     mainWindow = self.ui.mainWindow
    #     if mainWindow is not None:
    #         # mainWindow.sideBar.setProjectName(self.project)
    #         mainWindow.sideBar.setProjectName(self.project)

    def _getUI(self):
        if self.args.interface == 'Gui':
            self.styleSheet = self.getStyleSheet()
            from ccpn.ui.gui.Gui import Gui

            ui = Gui(self)
            # ui.mainWindow is None upon initialization: gets filled later
            getLogger().debug('%s %s %s' % (self, ui, ui.mainWindow))
        else:
            from ccpn.ui.Ui import NoUi

            ui = NoUi(self)

        # Connect UI classes for chosen ui
        ui.setUp()

        return ui

    def getStyleSheet(self):
        """return Stylesheet as determined by arguments --dark, --light or preferences
        """
        colourScheme = None
        if self.args.darkColourScheme:
            colourScheme = 'dark'
        elif self.args.lightColourScheme:
            colourScheme = 'light'
        else:
            colourScheme = self.preferences.general.colourScheme

        if colourScheme is None:
            raise RuntimeError('invalid colourScheme')

        self.colourScheme = colourScheme

        with open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                               '%sStyleSheet.qss' % metaUtil.upperFirst(colourScheme))) as fp:
            styleSheet = fp.read()

        if platform.system() == 'Linux':
            with open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                   '%sAdditionsLinux.qss' % metaUtil.upperFirst(colourScheme))) as fp:
                additions = fp.read()

            styleSheet += additions
        return ''  # GST for debug this should not be comitted! styleSheet

    def _getUserPrefs(self):
        # user preferences
        if not self.args.skipUserPreferences:
            sys.stderr.write('==> Getting user preferences\n')
        self.preferences = getPreferences(self.args.skipUserPreferences)

    def _savePreferences(self):
        """Save the preferences to file"""
        with catchExceptions(application=self, errorStringTemplate='Error saving preferences; "%s"', printTraceBack=True):
            directory = os.path.dirname(userPreferencesPath)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(userPreferencesPath, 'w+') as prefFile:
                json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))

    def _getUserLayout(self, userPath=None):
        """defines the application.layout dictionary.
        For a saved project: uses the auto-generated during the saving process, if a user specified json file is given then
        is used that one instead.
        For a new project, it is used the default.
        """
        # try:
        if userPath:
            with open(userPath) as fp:
                layout = json.load(fp, object_hook=AttrDict)
                self.layout = layout
        else:
            # opens the autogenerated if an existing project
            savedLayoutPath = self._getAutogeneratedLayoutFile()
            if savedLayoutPath:
                with open(savedLayoutPath) as fp:
                    layout = json.load(fp, object_hook=AttrDict)
                    self.layout = layout
            else:  # opens the default
                Layout._createLayoutFile(self)
                self._getUserLayout()
        # except Exception as e:
        #   getLogger().warning('No layout found. %s' %e)

        return self.layout

    def saveLayout(self):
        Layout.updateSavedLayout(self.ui.mainWindow)
        getLogger().info('Layout saved')

    def saveLayoutAs(self):
        fp = self.getSaveLayoutPath()
        try:
            Layout.saveLayoutToJson(self.ui.mainWindow, jsonFilePath=fp)
            getLogger().info('Layout saved')
        except Exception as e:
            getLogger().warning('Impossible to save layout. %s' % e)

    def restoreLastSavedLayout(self):
        self.ui.mainWindow.moduleArea._closeAll()
        Layout.restoreLayout(self.ui.mainWindow, self.layout, restoreSpectrumDisplay=True)

    def restoreLayoutFromFile(self, jsonFilePath=None):
        if jsonFilePath is None:
            #asks with a dialog
            jsonFilePath = self.getSavedLayoutPath()
            if jsonFilePath and not os.path.exists(jsonFilePath):
                again = MessageDialog.showOkCancelWarning(title='File Does not exist', message='Try again?')
                if again:
                    self.restoreLayoutFromFile()
                else:
                    return
        try:
            self.ui.mainWindow.moduleArea._closeAll()
            self._getUserLayout(jsonFilePath)
            Layout.restoreLayout(self.ui.mainWindow, self.layout, restoreSpectrumDisplay=True)
        except Exception as e:
            getLogger().warning('Impossible to restore layout. %s' % e)

    def _getAutogeneratedLayoutFile(self):
        if self.project:
            layoutFile = Layout.getLayoutFile(self)
            return layoutFile

    def _setLanguage(self):
        # Language, check for command line override, or use preferences
        if self.args.language:
            language = self.args.language
        elif self.preferences.general.language:
            language = self.preferences.general.language
        else:
            language = defaultLanguage
        if not translator.setLanguage(language):
            self.preferences.general.language = language
        # translator.setDebug(True)
        sys.stderr.write('==> Language set to "%s"\n' % translator._language)

    # def _isRegistered(self):
    #   """return True if registered"""
    #   self._registrationDict = Register.loadDict()
    #   return not Register.isNewRegistration(self._registrationDict)
    #
    #
    # def _checkRegistration(self):
    #   """
    #   Display registration popup if there is a gui
    #   return True if ok
    #   return False on error
    #   """
    #   from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup
    #
    #   if self.ui:
    #     if not self._isRegistered():
    #       self.ui.mainWindow.show()
    #       QtWidgets.QApplication.processEvents()
    #       popup = RegisterPopup(self.ui.mainWindow, version=self.applicationVersion, modal=True)
    #       QtWidgets.QApplication.processEvents()
    #       popup.show()
    #       # popup.raise_()
    #       popup.exec_()
    #
    #   if not self._isRegistered():
    #     return False
    #
    #   Register.updateServer(self._registrationDict, self.applicationVersion)
    #   return True

    def applyPreferences(self, project):
        """Apply user preferences

        NBNB project should be implicit rather than a parameter (once reorganisation is finished)
        """
        # Reset remoteData DataStores to match preferences setting
        dataPath = self.preferences.general.dataPath
        if not dataPath or not os.path.isdir(dataPath):
            dataPath = os.path.expanduser('~')
        memopsRoot = project._wrappedData.root
        dataUrl = memopsRoot.findFirstDataLocationStore(name='standard').findFirstDataUrl(
                name='remoteData'
                )
        dataUrl.url = Implementation.Url(path=dataPath)

    def _correctColours(self):
        """Autocorrect all colours that are too close to the background colour
        """
        from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND

        if self.preferences.general.autoCorrectColours:
            project = self.project

            # change spectrum colours
            for spectrum in project.spectra:
                if len(spectrum.axisCodes) > 1:
                    if spectrum.positiveContourColour.startswith('#'):
                        spectrum.positiveContourColour = autoCorrectHexColour(spectrum.positiveContourColour,
                                                                              getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                    if spectrum.negativeContourColour.startswith('#'):
                        spectrum.negativeContourColour = autoCorrectHexColour(spectrum.negativeContourColour,
                                                                              getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                else:
                    if spectrum.sliceColour.startswith('#'):
                        spectrum.sliceColour = autoCorrectHexColour(spectrum.sliceColour,
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

    def _initGraphics(self):
        """Set up graphics system after loading
        """
        from ccpn.ui.gui.lib import GuiStrip

        project = self.project
        mainWindow = self.ui.mainWindow

        # 20191113:ED Initial insertion of spectrumDisplays into the moduleArea
        try:
            insertPoint = mainWindow.moduleArea
            for spectrumDisplay in mainWindow.spectrumDisplays:
                mainWindow.moduleArea.addModule(spectrumDisplay,
                                                position='right',
                                                relativeTo=insertPoint)
                insertPoint = spectrumDisplay
        except Exception as e:
            getLogger().warning('Impossible to restore SpectrumDisplays')

        try:
            if self.preferences.general.restoreLayoutOnOpening and \
                    mainWindow.moduleLayouts:
                Layout.restoreLayout(self._mainWindow, mainWindow.moduleLayouts, restoreSpectrumDisplay=False)
        except Exception as e:
            getLogger().warning('Impossible to restore Layout %s' % e)

        try:
            # Initialise colours
            # # for spectrumDisplay in project.windows[0].spectrumDisplays:  # there is exactly one window
            #
            # for spectrumDisplay in mainWindow.spectrumDisplays:  # there is exactly one window
            #     pass  # GWV: poor solution; removed the routine spectrumDisplay._resetRemoveStripAction()

            # initialise any colour changes before generating gui strips
            self._correctColours()
        except Exception as e:
            getLogger().warning('Impossible to restore colours')

        # Initialise Strips
        for spectrumDisplay in mainWindow.spectrumDisplays:
            try:
                for si, strip in enumerate(spectrumDisplay.strips):

                    # temporary to catch bad strips from ordering bug
                    if not strip:
                        continue

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
                        getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(spectrumDisplay))
                    else:
                        getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(spectrumDisplay))

                    if not spectrumDisplay.is1D:
                        strip._setPlaneAxisWidgets()

                if spectrumDisplay.isGrouped:
                    # setup the spectrumGroup toolbar

                    spectrumDisplay.spectrumToolBar.hide()
                    spectrumDisplay.spectrumGroupToolBar.show()

                    _spectrumGroups = [project.getByPid(pid) for pid in spectrumDisplay._getSpectrumGroups()]

                    for group in _spectrumGroups:
                        spectrumDisplay.spectrumGroupToolBar._forceAddAction(group)

                else:
                    # setup the spectrum toolbar

                    spectrumDisplay.spectrumToolBar.show()
                    spectrumDisplay.spectrumGroupToolBar.hide()
                    spectrumDisplay.setToolbarButtons()

                # some of the strips may not be instantiated at this point
                # resize the stripFrame to the spectrumDisplay - ready for first resize event
                # spectrumDisplay.stripFrame.resize(spectrumDisplay.width() - 2, spectrumDisplay.stripFrame.height())
                spectrumDisplay.showAxes(stretchValue=True, widths=True,
                                         minimumWidth=GuiStrip.STRIP_MINIMUMWIDTH)

            except Exception as e:
                getLogger().warning('Impossible to restore spectrumDisplay(s) %s' % e)

        try:
            if self.current.strip is None and len(mainWindow.strips) > 0:
                self.current.strip = mainWindow.strips[0]
        except Exception as e:
            getLogger().warning('Error restoring current.strip: %s' % e)

        # GST slightly complicated as we have to wait for anay license or other
        # startup dialogs to close before we display tip of the day
        self._tip_of_the_day_wait_dialogs = (RegisterPopup,)
        self._startupShowTipofTheDay()

    def _startupShowTipofTheDay(self):
        if self._shouldDisplayTipOfTheDay():
            self._initial_show_timer = QTimer(parent=self._mainWindow)
            self._initial_show_timer.timeout.connect(self._startupDisplayTipOfTheDayCallback)
            self._initial_show_timer.setInterval(0)
            self._initial_show_timer.start()

    def _canTipOfTheDayShow(self):
        result = True
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, self._tip_of_the_day_wait_dialogs) and widget.isVisible():
                result = False
                break
        return result

    def _startupDisplayTipOfTheDayCallback(self):

        is_first_time_tip_of_the_day = self.preferences['general'].setdefault('firstTimeShowKeyConcepts', True)

        # GST this waits till any inhibiting dialogs aren't show and then awaits till the event loop is empty
        # effectively it swaps between waiting for WAIT_LICENSE_DIALOG_CLOSE_TIME or until the event loop is empty
        if not self._canTipOfTheDayShow() or self._initial_show_timer.interval() == WAIT_LICENSE_DIALOG_CLOSE_TIME:
            if self._initial_show_timer.interval() == WAIT_EVENT_LOOP_EMPTY:
                self._initial_show_timer.setInterval(WAIT_LICENSE_DIALOG_CLOSE_TIME)
            else:
                self._initial_show_timer.setInterval(WAIT_EVENT_LOOP_EMPTY)

            self._initial_show_timer.start()
        else:
            # this should only happen when the event loop is empty...
            if is_first_time_tip_of_the_day:
                self._displayKeyConcepts()
                self.preferences['general']['firstTimeShowKeyConcepts'] = False
            else:
                self._displayTipOfTheDay()

            if self._initial_show_timer:
                self._initial_show_timer.stop()
                self._initial_show_timer.deleteLater()
                self._initial_show_timer = None

    def _displayKeyConcepts(self):
        if not self._key_concepts:
            self._key_concepts = TipOfTheDayWindow(mode=MODE_KEY_CONCEPTS)
        self._key_concepts.show()
        self._key_concepts.raise_()

    def _displayTipOfTheDay(self, standalone=False):

        # tip of the day allocated standalone already
        if self._tip_of_the_day and standalone and self._tip_of_the_day.isStandalone():
            self._tip_of_the_day.show()
            self._tip_of_the_day.raise_()

        # tip of the day hanging around from startup
        elif self._tip_of_the_day and standalone and not self._tip_of_the_day.isStandalone():

            self._tip_of_the_day.hide()
            self._tip_of_the_day.deleteLater()
            self._tip_of_the_day = None

        if not self._tip_of_the_day:
            dont_show_tips = not self.preferences['general']['showTipOfTheDay']

            seen_tip_list = []
            if not standalone:
                seen_tip_list = self.preferences['general']['seenTipsOfTheDay']

            self._tip_of_the_day = TipOfTheDayWindow(dont_show_tips=dont_show_tips,
                                                     seen_perma_ids=seen_tip_list, standalone=standalone)
            self._tip_of_the_day.dont_show.connect(self._tip_of_the_day_dont_show_callback)
            if not standalone:
                self._tip_of_the_day.seen_tips.connect(self._tip_of_the_day_seen_tips_callback)

            self._tip_of_the_day.show()
            self._tip_of_the_day.raise_()

    def _tip_of_the_day_dont_show_callback(self, dont_show):
        self.preferences['general']['showTipOfTheDay'] = not dont_show

    def _tip_of_the_day_seen_tips_callback(self, seen_tips):
        seen_tip_list = self.preferences['general']['seenTipsOfTheDay']
        previous_seen_tips = set(seen_tip_list)
        previous_seen_tips.update(seen_tips)
        seen_tip_list.clear()
        seen_tip_list.extend(previous_seen_tips)

    def _shouldDisplayTipOfTheDay(self):
        return self.preferences['general'].setdefault('showTipOfTheDay', True)

    def get(self, identifier):
        """General method to obtain object (either gui or data) from identifier (pid, gid, obj-string)
        """
        if identifier is None:
            raise ValueError('Expected str or Pid, got "None"')

        if not isinstance(identifier, (str, Pid)):
            raise ValueError('Expected str or Pid, got "%s" %s' % (identifier, type(identifier)))
        identifier = str(identifier)

        if len(identifier) == 0:
            raise ValueError('Expected str or Pid, got zero-length identifier')

        if len(identifier) >= 2 and identifier[0] == '<' and identifier[-1] == '>':
            identifier = identifier[1:-1]

        return self.project.getByPid(identifier)

    def getByPid(self, pid):
        """Convenience"""
        return self.project.getByPid(pid)
        # obj = self.project.getByPid(pid)
        # if obj:
        #     return obj
        # else:
        #     if isinstance(self.ui, Gui):
        #         if PREFIXSEP in pid:
        #             pid = Pid(pid)
        #             if pid:
        #                 return self.ui.mainWindow.moduleArea.modules.get(pid.id)

    def getByGid(self, gid):
        """Convenience"""
        return self.project.getByPid(gid)

    def addApplicationMenuSpec(self, spec, position=5):
        """Add an entirely new menu at specified position"""
        self._menuSpec.insert(position, spec)

    def addApplicationMenuItem(self, menuName, menuItem, position):
        """Add a new item to an existing menu at specified position"""
        for spec in self._menuSpec:
            if spec[0] == menuName:
                spec[1].insert(position, menuItem)
                return

        raise Exception('No menu with name %s' % menuName)

    def addApplicationMenuItems(self, menuName, menuItems, position):
        """Add a new items to an existing menu starting at specified position"""
        for n, menuItem in enumerate(menuItems):
            self.addApplicationMenuItem(menuName, menuItem, position + n)

    #########################################    Create sub dirs   ########################################################

    ## dirs are created with decorators because the project path can change dynamically.
    ##  When a project is saved in a new location, all the dirs get refreshed automatically'

    @property
    def statePath(self):
        return self._statePath

    @statePath.getter
    def statePath(self):
        return Path.fetchDir(self.project.path, Layout.StateDirName)

    @statePath.setter
    def statePath(self, path):
        self._statePath = path

    @property
    def pipelinePath(self):
        return self._pipelinePath

    @pipelinePath.getter
    def pipelinePath(self):
        return Path.fetchDir(self.statePath, Pipeline.className)

    @pipelinePath.setter
    def pipelinePath(self, path):
        self._pipelinePath = path

    @property
    def dataPath(self):
        return self._dataPath

    @dataPath.getter
    def dataPath(self):
        return Path.fetchDir(self.project.path, DataDirName)

    @dataPath.setter
    def dataPath(self, path):
        self._dataPath = path

    @property
    def spectraPath(self):
        return self._spectraPath

    @spectraPath.getter
    def spectraPath(self):
        return Path.fetchDir(self.dataPath, SpectraDirName)

    @spectraPath.setter
    def spectraPath(self, path):
        self._spectraPath = path

    @property
    def pluginDataPath(self):
        return self._pluginDataPath

    @pluginDataPath.getter
    def pluginDataPath(self):
        return Path.fetchDir(self.dataPath, PluginDataDirName)

    @pluginDataPath.setter
    def pluginDataPath(self, path):
        self._pluginDataPath = path

    @property
    def tempMacrosPath(self):
        return self._tempMacrosPath

    @tempMacrosPath.getter
    def tempMacrosPath(self):
        return Path.fetchDir(userPreferencesDirectory, MacrosDirName)

    @tempMacrosPath.setter
    def tempMacrosPath(self, path):
        self._tempMacrosPath = path

    @property
    def scriptsPath(self):
        return self._scriptsPath

    @scriptsPath.getter
    def scriptsPath(self):
        return Path.fetchDir(self.project.path, ScriptsDirName)

    @scriptsPath.setter
    def scriptsPath(self, path):
        self._scriptsPath = path

    #########################################    Start setup Menus      ############################

    def _updateCheckableMenuItems(self):
        # This has to be kept in sync with menu items below which are checkable,
        # and also with MODULE_DICT keys
        # The code is terrible because Qt has no easy way to get hold of menus / actions

        mainWindow = self.ui.mainWindow
        if mainWindow is None:
            # We have a UI with no mainWindow - nothing to do.
            return

        menuChildren = mainWindow.menuBar().findChildren(QtWidgets.QMenu)
        if not menuChildren:
            return

        topActionDict = {}
        for topMenu in menuChildren:
            mainActionDict = {}
            for mainAction in topMenu.actions():
                mainActionDict[mainAction.text()] = mainAction
            topActionDict[topMenu.title()] = mainActionDict

        openModuleKeys = set(mainWindow.moduleArea.modules.keys())
        for key, topActionText, mainActionText in (('SEQUENCE', 'Molecules', 'Show Sequence'),
                                                   ('PYTHON CONSOLE', 'View', 'Python Console')):
            if key in openModuleKeys:
                mainActionDict = topActionDict.get(topActionText)  # should always exist but play safe
                if mainActionDict:
                    mainAction = mainActionDict.get(mainActionText)
                    if mainAction:
                        mainAction.setChecked(True)

    def setupMenus(self):
        """Setup the menu specification.

        The menus are specified by a list of lists (actually, an iterable of iterables, but the term
        ‘list’ will be used here to mean any iterable).  Framework provides 7 menus: Project, Spectrum,
        Molecules, View, Macro, Plugins, Help.  If you want to create your own menu in a subclass of
        Framework, you need to create a list in the style described below, then call
        self.addApplicationMenuSpec and pass in your menu specification list.

        Menu specification lists are composed of two items, the first being a string which is the menu’s
        title, the second is a list of sub-menu items.  Each item can be zero, two or three items long.
        A zero-length list indicates a separator.  If the list is length two and the second item is a
        list, then it specifies a sub-menu in a recursive manner.  If the list is length two and the
        second item is callable, it specifies a menu action with the first item specifying the label
        and the second the callable that is triggered when the menu item is selected.  If the list is
        length three, it is treated as a menu item specification, with the third item a list of keyword,
        value pairs.

        The examples below may make this more clear…

        Create a menu called ‘Test’ with two items and a separator:

        | - Test
        |   | - Item One
        |   | - ------
        |   | - Item Two

        Where clicking on ‘Item One’ calls method self.itemOneMethod and clicking on ‘Item Two’
        calls self.itemTwoMethod

        |    def setupMenus(self):
        |      menuSpec = (‘Test’, [(‘Item One’, self.itemOneMethod),
        |                           (),
        |                           (‘Item Two’, self.itemTwoMethod),
        |                          ]
        |      self.addApplicationMenuSpec(menuSpec)



        More complicated menus are possible.  For example, to create the following menu

        | - Test
        |   | - Item A     ia
        |   | - ------
        |   | - Submenu B
        |      | - Item B1
        |      | - Item B2
        |   | - Item C     id

        where Item A can be activated using the two-key shortcut ‘ia’,
        Submenu B contains two static menu items, B1 and B2
        Submenu item B2 is checkable, but not checked by default
        Item C is disabled by default and has a shortcut of ‘ic’

        |   def setupMenus(self):
        |     subMenuSpecB = [(‘Item B1’, self.itemB1),
        |                     (‘Item B2’, self.itemB2, [(‘checkable’, True),
        |                                               (‘checked’, False)])
        |                    ]
        |
        |     menuSpec = (‘Test’, [(‘Item A’, self.itemA, [(‘shortcut’, ‘ia’)]),
        |                          (),
        |                          (‘Submenu B’, subMenuB),
        |                          (‘Item C’, self.itemA, [(‘shortcut’, ‘ic’),
        |                                                  (‘enabled’, False)]),
        |                         ]
        |     self.addApplicationMenuSpec(menuSpec)


        If we’re using the PyQt GUI, we can get the Qt action representing Item B2 somewhere in our code
        (for example, to change the checked status,) via:

        |   action = application.ui.mainWindow.getMenuAction(‘Test->Submenu B->Item B2’)
        |   action.setChecked(True)

        To see how to add items dynamically, see clearRecentProjects in this class and
        _fillRecentProjectsMenu in GuiMainWindow

        """
        self._menuSpec = ms = []

        ms.append(('File', [
            ("New", self._newProjectMenuCallback, [('shortcut', '⌃n')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (),
            ("Open...", self._openProjectMenuCallback, [('shortcut', '⌃o')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Open Recent", ()),

            ("Load Data...", lambda: self._loadDataFromMenu(text='Load Data'), [('shortcut', 'ld')]),
            (),
            ("Save", self.saveProject, [('shortcut', '⌃s')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Save As...", self.saveProjectAs, [('shortcut', 'sa')]),
            (),
            ("Import", (("Nef File", self._importNef, [('shortcut', 'in'), ('enabled', True)]),
                        ("NmrStar File", self._loadNMRStarFileCallback, [('shortcut', 'bi')]),
                        )),
            ("Export", (("Nef File", self._exportNEF, [('shortcut', 'ex'), ('enabled', True)]),
                        )),
            (),
            ("Layout", (("Save", self.saveLayout, [('enabled', True)]),
                        ("Save as...", self.saveLayoutAs, [('enabled', True)]),
                        (),
                        ("Restore last", self.restoreLastSavedLayout, [('enabled', True)]),
                        ("Restore from file...", self.restoreLayoutFromFile, [('enabled', True)]),
                        (),
                        ("Open pre-defined", ()),

                        )),
            ("Summary", self.displayProjectSummary),
            ("Archive", self.archiveProject, [('enabled', False)]),
            ("Restore From Archive...", self.restoreFromArchive, [('enabled', False)]),
            (),
            ("Preferences...", self.showApplicationPreferences, [('shortcut', '⌃,')]),
            (),
            ("Quit", self._closeEvent, [('shortcut', '⌃q')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ]
                   ))

        ms.append(('Edit', [
            ("Undo", self.undo, [('shortcut', '⌃z')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Redo", self.redo, [('shortcut', '⌃y')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (),

            ("Cut", self._nyi, [('shortcut', '⌃x'), ('enabled', False)]),
            ("Copy", self._nyi, [('shortcut', '⌃c'), ('enabled', False)]),
            ("Paste", self._nyi, [('shortcut', '⌃v'), ('enabled', False)]),
            ("Select all", self._nyi, [('shortcut', '⌃a'), ('enabled', False)]),
            ]
                   ))

        ms.append(('View', [
            ("Chemical Shift Table", partial(self.showChemicalShiftTable, selectFirstItem=True), [('shortcut', 'ct')]),
            ("NmrResidue Table", partial(self.showNmrResidueTable, selectFirstItem=True), [('shortcut', 'nt')]),
            ("Residue Table", partial(self.showResidueTable, selectFirstItem=True)),
            ("Peak Table", partial(self.showPeakTable, selectFirstItem=True), [('shortcut', 'pt')]),
            ("Integral Table", partial(self.showIntegralTable, selectFirstItem=True), [('shortcut', 'it')]),
            ("Multiplet Table", partial(self.showMultipletTable, selectFirstItem=True), [('shortcut', 'mt')]),
            ("Restraint Table", partial(self.showRestraintTable, selectFirstItem=True), [('shortcut', 'rt')]),
            ("Structure Table", partial(self.showStructureTable, selectFirstItem=True), [('shortcut', 'st')]),
            ("Data Table", partial(self.showDataTable, selectFirstItem=True), [('shortcut', 'dt')]),
            ("Violation Table", partial(self.showViolationTable, selectFirstItem=True), [('shortcut', 'vt')]),
            (),
            ("Restraint Analysis Table", partial(self.showRestraintAnalysisTable, selectFirstItem=True), [('shortcut', 'at')]),
            ("Chemical Shift Mapping", self.showChemicalShiftMapping, [('shortcut', 'cm')]),
            ("Notes Editor", partial(self.showNotesEditor, selectFirstItem=True), [('shortcut', 'no'),
                                                                                   ('icon', 'icons/null')]),
            (),
            ("In Active Spectrum Display", (("Show/Hide Toolbar", self.toggleToolbar, [('shortcut', 'tb')]),
                                            ("Show/Hide Spectrum Toolbar", self.toggleSpectrumToolbar, [('shortcut', 'sb')]),
                                            ("Show/Hide Phasing Console", self.togglePhaseConsole, [('shortcut', 'pc')]),
                                            (),
                                            ("Set Zoom...", self._setZoomPopup, [('shortcut', 'sz')]),
                                            ("Reset Zoom", self.resetZoom, [('shortcut', 'rz')]),
                                            (),
                                            ("New SpectrumDisplay with New Strip, Same Axes", self.copyStrip, []),
                                            (" .. with X-Y Axes Flipped", self._flipXYAxisCallback, [('shortcut', 'xy')]),
                                            (" .. with X-Z Axes Flipped", self._flipXZAxisCallback, [('shortcut', 'xz')]),
                                            (" .. with Y-Z Axes Flipped", self._flipYZAxisCallback, [('shortcut', 'yz')]),
                                            (" .. with Axes Flipped...", self.showFlipArbitraryAxisPopup, [('shortcut', 'fa')]),
                                            )),
            (),
            (SHOWMODULESMENU, ([
                ("None", None, [('checkable', True),
                                ('checked', False)])
                ])),
            ("Python Console", self._toggleConsoleCallback, [('shortcut', '  '),
                                                             ])
            ]
                   ))

        ms.append(('Spectrum', [
            ("Load Spectra...", self._loadSpectraCallback, [('shortcut', 'ls')]),
            (),
            # ("Spectrum Groups...", self.showSpectrumGroupsPopup, [('shortcut', 'ss')]), # multiple edit temporarly disabled
            ("Set Experiment Types...", self.showExperimentTypePopup, [('shortcut', 'et')]),
            ("Validate Paths...", self.showValidateSpectraPopup, [('shortcut', 'vp')]),
            (),
            ("Pick Peaks", (("Pick 1D Peaks...", self.showPeakPick1DPopup, [('shortcut', 'p1')]),
                            ("Pick ND Peaks...", self.showPeakPickNDPopup, [('shortcut', 'pp')])
                            )),
            ("Copy PeakList...", self.showCopyPeakListPopup, [('shortcut', 'cl')]),
            ("Copy Peaks...", self.showCopyPeaks, [('shortcut', 'cp')]),
            ("Estimate Volumes...", self.showEstimateVolumesPopup, [('shortcut', 'ev')]),
            ("Reorder PeakList Axes...", self.showReorderPeakListAxesPopup, [('shortcut', 'rl')]),
            (),
            ("Make Strip Plot...", self.makeStripPlotPopup, [('shortcut', 'sp')]),

            (),
            ("Make Projection...", self.showProjectionPopup, [('shortcut', 'pj')]),
            (),
            ("Print to File...", self.showPrintSpectrumDisplayPopup, [('shortcut', '⌃p')]),
            ]
                   ))

        ms.append(('Molecules', [
            ("Chain from FASTA...", lambda: self._loadDataFromMenu(text='Load FASTA')),
            (),
            ("New Chain...", self.showCreateChainPopup),
            ("Inspect...", self.inspectMolecule, [('enabled', False)]),
            (),
            ("Residue Information", self.showResidueInformation, [('shortcut', 'ri')]),
            (),
            ("Reference Chemical Shifts", self.showReferenceChemicalShifts, [('shortcut', 'rc')]),
            ]
                   ))

        ms.append(('Macro', [
            ("New Macro Editor", self._showMacroEditorCallback),
            (),
            ("Open User Macro...", self._openMacroCallback),
            ("Open CCPN Macro...", partial(self._openMacroCallback, directory=macroPath)),
            (),
            ("Run...", self.runMacro),
            ("Run Recent", ()),
            (CCPNMACROSMENU, ([
                ("None", None, [('checkable', True),
                                ('checked', False)])
                ])),
            (),
            ("Define Macro Shortcuts...", self.defineUserShortcuts, [('shortcut', 'du')]),
            ]
                   ))

        ms.append(('Plugins', [
            (CCPNPLUGINSMENU, ()),
            (PLUGINSMENU, ()),
            ]
                   ))

        ms.append(('Help', [
            (TUTORIALSMENU, ([

                ("None", None, [('checkable', True),
                                ('checked', False)])
                ])),
            ("Show Tip of the Day", partial(self._displayTipOfTheDay, standalone=True)),
            ("Key Concepts", self._displayKeyConcepts),
            ("Show Shortcuts", self.showShortcuts),
            ("Show API Documentation", self.showVersion3Documentation),
            ("Show License", self.showCcpnLicense),
            (),
            ("CcpNmr Homepage", self.showAboutCcpn),
            ("CcpNmr V3 Forum", self.showForum),
            (),
            # ("Inspect Code...", self.showCodeInspectionPopup, [('shortcut', 'gv'),
            #                                                    ('enabled', False)]),
            # ("Show Issues...", self.showIssuesList),
            ("Check for Updates...", self.showUpdatePopup),
            ("Register...", self.showRegisterPopup),
            (),
            ("About CcpNmr V3...", self.showAboutPopup),
            ]
                   ))

    ###################################################################################################################
    ## These will eventually move to gui (probably via a set of lambda functions.
    ###################################################################################################################

    ###################################################################################################################
    ## MENU callbacks:  Project
    ###################################################################################################################

    def _nyi(self):
        """Not yet implemented"""
        pass

    def _loadDataFromMenu(self, text='Load Data', filter=None):
        """Call loadData from the menu and trap errors.
        """
        dialog = DataFileDialog(parent=self.ui.mainWindow, acceptMode='load', fileFilter=filter)
        dialog._show()
        path = dialog.selectedFile()
        if not path:
            return
        paths = [path]

        try:
            result = self.loadData(paths)
        except Exception as es:
            MessageDialog.showWarning(str(self.ui.mainWindow.windowTitle()), str(es))
            if self._isInDebugMode:
                raise es

    def _newProjectMenuCallback(self):
        """Callback for creating new project"""
        with catchExceptions(application=self, errorStringTemplate='Error creating new project:', printTraceBack=True):
            okToContinue = self.ui.mainWindow._queryCloseProject(title='New Project',
                                                                 phrase='create a new')
            if okToContinue:
                self.ui.mainWindow.moduleArea._closeAll()
                newProject = self.newProject()
                if newProject is None:
                    raise RuntimeError('Unable to create new project')
                newProject._mainWindow.show()
                QtWidgets.QApplication.setActiveWindow(newProject._mainWindow)

    #@logCommand('application.') #cannot do, as project is not there yet
    def newProject(self, name='default'):
        """Create new, empty project; return Project instance
        """
        # local import to avoid cycles
        from ccpn.core.Project import _newProject

        newName = re.sub('[^0-9a-zA-Z]+', '', name)
        if newName != name:
            getLogger().info('Removing whitespace from name: %s' % name)

        sys.stderr.write('==> Creating new, empty project\n')
        # NB _closeProject includes a gui cleanup call
        self._closeProject()
        project = _newProject(self, name=newName)
        self._initialiseProject(project)  # This also set the linkages

        return project

    def _openProjectMenuCallback(self):
        """Just a stub for the menu setup to pass on to mainWindow, to be moved later
        """
        return self.ui.mainWindow._openProjectCallback()

    def _loadV2Project(self, path) -> List[Project]:
        """Actual V2 project loader
        CCPNINTERNAL: called from CcpNmrV2ProjectDataLoader
        """
        from ccpn.core._implementation.updates.update_v2 import updateProject_fromV2
        from ccpn.core.Project import _loadProject

        with logCommandManager('application.', 'loadProject', path):
            logger = getLogger()

            # always close first
            self._closeProject()
            project = _loadProject(application=self, path=str(path))
            self._initialiseProject(project)  # This also sets the linkages
            getLogger().info('==> Loaded ccpn project "%s"' % path)

            # Save the result
            try:
                project.save()
                logger.info('==> Saved %s as "%s"' % (project, project.path))
            except Exception as es:
                logger.warning('Failed saving %s (%s)' % (project, str(es)))

        return [project]

    def _loadV3Project(self, path) -> List[Project]:
        """Actual V3 project loader
        CCPNINTERNAL: called from CcpNmrV3ProjectDataLoader
        """
        from ccpn.core.lib.ProjectSaveHistory import getProjectSaveHistory
        from ccpn.core.Project import _loadProject

        if not isinstance(path, (Path.Path, str)):
            raise ValueError('invalid path "%s"' % path)

        with logCommandManager('application.', 'loadProject', path):

            _path = Path.aPath(path)
            if not _path.exists():
                raise ValueError('path "%s" does not exist' % path)

            # always close first
            self._closeProject()
            project = _loadProject(application=self, path=path)
            self._initialiseProject(project)  # This also set the linkages
            getLogger().info('==> Loaded ccpn project "%s"' % path)

        return [project]

    @logCommand('application.')
    def loadProject(self, path):
        """Just a stub for now; calling MainWindow methods as it initialises the Gui
        """
        # self.ui.mainWindow._openProject(path)
        return self.ui.loadProject(path)

    def _loadNefFile(self, path: str, makeNewProject=True) -> Project:
        """Load Project from NEF file at path, and do necessary setup"""

        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking
        from ccpn.core.lib import CcpnNefIo

        _nefReader = CcpnNefIo.CcpnNefReader(self)
        dataBlock = _nefReader.getNefData(path)

        if makeNewProject:
            self._closeProject()
            self._project = self.newProject(dataBlock.name)

        self.project.shiftAveraging = False

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                with catchExceptions(application=self, errorStringTemplate='Error loading Nef file: %s', printTraceBack=True):
                    # need datablock selector here, with subset selection dependent on datablock type

                    _nefReader.importNewProject(self.project, dataBlock)

        self.project.shiftAveraging = True

        getLogger().info('==> Loaded NEF file: "%s"' % (path,))
        return self.project

    def _loadNMRStarFileCallback(self, path=None, makeNewProject=False) -> Optional[Project]:
        if not path:
            dialog = NMRStarFileDialog(parent=self.ui.mainWindow, acceptMode='import')
            dialog._show()
            path = dialog.selectedFile()
            if not path:
                return

        from ccpn.ui.gui.popups.ImportStarPopup import StarImporterPopup
        from ccpn.core.lib import CcpnNefIo

        _nefReader = CcpnNefIo.CcpnNefReader(self)
        relativePath = os.path.dirname(os.path.realpath(path))
        dataBlock = _nefReader.getNMRStarData(path)

        self._importedStarDataBlock = dataBlock

        if makeNewProject:
            if self.project is not None:
                self._closeProject()
            self.project = self.newProject(dataBlock.name)

        self.project.shiftAveraging = False

        popup = StarImporterPopup(project=self.project, bmrbFilePath=path, directory=relativePath, dataBlock=dataBlock)
        popup.exec_()

        self.project.shiftAveraging = True

        getLogger().info('==> Loaded Star file: "%s"' % (path,))
        return self.project

    def _loadSparkyFile(self, path: str, createNewProject=True) -> Project:
        """Load Project from Sparky file at path, and do necessary setup
        :return Project-instance (either existing or newly created)

        CCPNINTERNAL: called from SparkyDataLoader
        """
        from ccpn.core.lib.CcpnSparkyIo import SPARKY_NAME, CcpnSparkyReader

        sparkyReader = CcpnSparkyReader(self)

        dataBlock = sparkyReader.parseSparkyFile(str(path))
        sparkyName = dataBlock.getDataValues(SPARKY_NAME, firstOnly=True)

        # Just a helper function for cleaner code below"
        def _importData(project):
            with undoBlockWithoutSideBar():
                with notificationEchoBlocking():
                    with catchExceptions(application=self, errorStringTemplate='Error loading Sparky file: %s',
                                         printTraceBack=True):
                        sparkyReader.importSparkyProject(project, dataBlock)

        #end def

        if createNewProject and (dataBlock.getDataValues('sparky', firstOnly=True) == 'project file'):
            with logCommandManager('application.', 'loadProject', path):
                self._closeProject()
                project = self.newProject(sparkyName)
                _importData(project)
                self.project.shiftAveraging = True
            getLogger().info('==> Created project from Sparky file: "%s"' % (path,))

        else:
            project = self.project
            with logCommandManager('application.', 'loadData', path):
                _importData(project)
            getLogger().info('==> Imported Sparky file: "%s"' % (path,))

        return project

    def _loadPythonFile(self, path):
        """Load python file path into the macro editor
        CCPNINTERNAL: called from PythonDataLoader
        """
        mainWindow = self.mainWindow
        with logCommandManager('application.', 'loadData', path):
            macroEditor = MacroEditor(mainWindow=mainWindow, filePath=str(path))
            mainWindow.moduleArea.addModule(macroEditor, position='top', relativeTo=mainWindow.moduleArea)
        return []

    def _loadHtmlFile(self, path):
        """Load html file path into a HtmlModule
        CCPNINTERNAL: called from HtmlDataLoader
        """
        mainWindow = self.mainWindow
        with logCommandManager('application.', 'loadData', path):
            path = Path.aPath(path)
            mainWindow.newHtmlModule(urlPath=str(path), position='top', relativeTo=mainWindow.moduleArea)
        return []

    def clearRecentProjects(self):
        self.preferences.recentFiles = []
        self.ui.mainWindow._fillRecentProjectsMenu()

    def clearRecentMacros(self):
        self.preferences.recentMacros = []
        self.ui.mainWindow._fillRecentMacrosMenu()

    def _loadSpectraCallback(self, paths=None, filter=None, askBeforeOpen_lenght=20):
        """
        Load all the spectra found in paths

        :param paths: list of str of paths
        :param filter:
        :param askBeforeOpen_lenght: how many spectra can open without asking first
        """
        from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import SpectrumDataLoader
        from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader

        if paths is None:
            dialog = SpectrumFileDialog(parent=self.ui.mainWindow, acceptMode='load', fileFilter=filter, useNative=False)

            dialog._show()
            paths = dialog.selectedFiles()

        if not paths:
            return

        spectrumLoaders = []
        count = 0
        # Recursively search all paths
        for path in paths:
            _path = Path.aPath(path)
            if _path.is_dir():
                dirLoader = DirectoryDataLoader(path, recursive=False,
                                                filterForDataFormats=(SpectrumDataLoader.dataFormat,))
                spectrumLoaders.append(dirLoader)
                count += len(dirLoader)

            elif (sLoader := SpectrumDataLoader.checkForValidFormat(path)) is not None:
                spectrumLoaders.append(sLoader)
                count += 1

        if count > askBeforeOpen_lenght:
            okToOpenAll = MessageDialog.showYesNo('Load data', 'The directory contains multiple items (%d).'
                                                               ' Do you want to open all?' % len(spectrumLoaders))
            if not okToOpenAll:
                return

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                for sLoader in tqdm(spectrumLoaders):
                    sLoader.load()

    @logCommand('application.')
    def loadData(self, *paths) -> list:
        """Loads data from paths.
        :returns list of loaded objects
        """
        objs = []
        for path in paths:
            dataLoader = checkPathForDataLoader(path)

            if dataLoader is None:
                getLogger().warning('Unable to load "%s"' % path)

            elif dataLoader.alwaysCreateNewProject:
                getLogger().warning('Loading of "%s" would create a new project; use application.loadProject() instead')

            else:
                dataLoader.createNewObject = False  # The loadData() method was used; No project created
                result = dataLoader.load()
                if not isIterable(result):
                    result = [result]
                objs.extend(result)

        return objs

    def _cloneSpectraToProjectDir(self):
        """ Keep a copy of spectra inside the project directory "myproject.ccpn/data/spectra".
        This is useful when saving the project in an external driver and want to keep the spectra together with the project.
        """
        from shutil import copyfile

        try:
            for spectrum in self.project.spectra:
                oldPath = spectrum.filePath
                # For Bruker need to keep all the tree structure.
                # Uses the fact that there is a folder called "pdata" and start to copy from the dir before.
                ss = oldPath.split('/')
                if 'pdata' in ss:
                    brukerDir = os.path.join(os.sep, *ss[:ss.index('pdata')])
                    brukerName = brukerDir.split('/')[-1]
                    os.mkdir(os.path.join(self.spectraPath, brukerName))
                    destinationPath = os.path.join(self.spectraPath, brukerName)
                    copy_tree(brukerDir, destinationPath)
                    clonedPath = os.path.join(destinationPath, *ss[ss.index('pdata'):])
                    # needs to repoint the path but doesn't seem to work!! troubles with $INSIDE!!
                    # spectrum.filePath = clonedPath
                else:
                    # copy the file and or other files containing params
                    from ntpath import basename

                    pathWithoutFileName = os.path.join(os.sep, *ss[:ss.index(basename(oldPath))])
                    fullpath = os.path.join(pathWithoutFileName, basename(oldPath))
                    import glob

                    otherFilesWithSameName = glob.glob(fullpath + ".*")
                    clonedPath = os.path.join(self.spectraPath, basename(oldPath))
                    for otherFileTocopy in otherFilesWithSameName:
                        otherFilePath = os.path.join(self.spectraPath, basename(otherFileTocopy))
                        copyfile(otherFileTocopy, otherFilePath)
                    if oldPath != clonedPath:
                        copyfile(oldPath, clonedPath)
                        # needs to repoint the path but doesn't seem to work!! troubles with $INSIDE!!
                        # spectrum.filePath = clonedPath

        except Exception as e:
            getLogger().debug(str(e))

    def _saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
        """Save project to newPath and return True if successful"""
        if self.preferences.general.keepSpectraInsideProject:
            self._cloneSpectraToProjectDir()

        successful = self.project.save(newPath=newPath, createFallback=createFallback,
                                       overwriteExisting=overwriteExisting)
        if not successful:
            failMessage = '==> Project save failed\n'
            sys.stderr.write(failMessage)
            self.ui.mainWindow.statusBar().showMessage(failMessage)

        else:
            successMessage = '==> Project successfully saved\n'
            self.ui.mainWindow._updateWindowTitle()
            self.ui.mainWindow.statusBar().showMessage(successMessage)
            self.ui.mainWindow.getMenuAction('File->Archive').setEnabled(True)
            self.ui.mainWindow._fillRecentProjectsMenu()
            # self._createApplicationPaths()
            self.current._dumpStateToFile(self.statePath)
            try:
                if self.preferences.general.autoSaveLayoutOnQuit:
                    Layout.saveLayoutToJson(self.ui.mainWindow)
            except Exception as e:
                getLogger().warning('Unable to save Layout %s' % e)

            # saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')
            sys.stderr.write(successMessage)
            # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
            #                            iconPath=saveIconPath)

        self._getUndo().markSave()
        return successful

    @logCommand('application.')
    def saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
        """Save project to newPath and return True if successful"""
        if self.project.isTemporary:
            return self.saveProjectAs()
        else:
            return self._saveProject(newPath=newPath, createFallback=createFallback,
                                     overwriteExisting=overwriteExisting)

    def _importNef(self, path=None):
        if not path:
            filter = '*.nef'
            dialog = NefFileDialog(parent=self.ui.mainWindow, acceptMode='import', fileFilter=filter)

            dialog._show()
            path = dialog.selectedFile()
            if not path:
                return

        path = Path.aPath(path)

        with catchExceptions(application=self, errorStringTemplate='Error Importing Nef File: %s', printTraceBack=True):
            with undoBlockWithoutSideBar():
                self._importNefFile(path=path, makeNewProject=False)
            self.ui.mainWindow.sideBar.buildTree(self.project)

    def _importNefFile(self, path: Union[str, Path.Path], makeNewProject=True) -> Project:
        """Load Project from NEF file at path, and do necessary setup"""

        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking
        from ccpn.ui.gui.popups.ImportNefPopup import ImportNefPopup, NEFFRAMEKEY_ENABLERENAME, \
            NEFFRAMEKEY_IMPORT, NEFFRAMEKEY_ENABLEMOUSEMENU, NEFFRAMEKEY_PATHNAME, \
            NEFFRAMEKEY_ENABLEFILTERFRAME, NEFFRAMEKEY_ENABLECHECKBOXES
        from ccpn.util.nef import NefImporter as Nef
        from ccpn.util.CcpnNefImporter import CcpnNefImporter
        from ccpn.framework.PathsAndUrls import nefValidationPath

        # dataBlock = self.nefReader.getNefData(path)

        # the loader can be subclassed if required, and the type passed as nefImporterClass
        # _loader = CcpnNefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)

        # _loader = Nef.NefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
        # _loader.loadFile(path)
        # _loader.loadValidateDictionary(nefValidationPath)

        # create/read the nef file
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import checkPathForDataLoader

        _dataLoader = checkPathForDataLoader(path)
        _loader = _dataLoader.readNefFile(path, nefValidationPath=nefValidationPath, errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)

        # verify popup here
        selection = None

        dialog = ImportNefPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow,
                                # nefImporterClass=CcpnNefImporter,
                                nefObjects=({NEFFRAMEKEY_IMPORT: self.project,
                                             },
                                            {NEFFRAMEKEY_IMPORT           : _loader,
                                             NEFFRAMEKEY_ENABLECHECKBOXES : True,
                                             NEFFRAMEKEY_ENABLERENAME     : True,
                                             NEFFRAMEKEY_ENABLEFILTERFRAME: True,
                                             NEFFRAMEKEY_ENABLEMOUSEMENU  : True,
                                             NEFFRAMEKEY_PATHNAME         : str(path),
                                             })
                                )
        with notificationEchoBlocking():
            dialog.fillPopup()

        dialog.setActiveNefWindow(1)
        if dialog.exec_():

            selection = dialog._saveFrameSelection
            _nefReader = dialog.getActiveNefReader()

            if makeNewProject:
                self._closeProject()
                self.project = self.newProject(_loader._nefDict.name)

            # import from the loader into the current project
            self.importFromLoader(_loader, reader=_nefReader)

            getLogger().info('==> Loaded NEF file: "%s"' % (path,))
            return self.project

    @logCommand('application.')
    def importFromLoader(self, loader, reader=None):
        """Read the selection from the nefImporter object into the current.project

        To use without the nef import dialog, requires the creation of a reader object
        If no reader is specified, then a default is created
        Selection of objects is specified through the loader before import

        :param loader: nef loader object created from a nef file
        """

        from ccpn.core.lib.ContextManagers import notificationEchoBlocking
        from ccpn.core.lib import CcpnNefIo
        from ccpn.util.nef import NefImporter as Nef

        # set a default if not specified
        reader = reader or CcpnNefIo.CcpnNefReader(self)

        # check the parameters
        if not isinstance(loader, Nef.NefImporter):
            raise ValueError(f'loader {loader} not defined correctly')
        if not isinstance(reader, CcpnNefIo.CcpnNefReader):
            raise ValueError(f'reader {reader} not defined correctly')

        self.project.shiftAveraging = False

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                with catchExceptions(application=self, errorStringTemplate='Error importing Nef file: %s', printTraceBack=True):
                    # need datablock selector here, with subset selection dependent on datablock type

                    reader.importNewProject(self.project, loader._nefDict)

        self.project.shiftAveraging = True

    def _exportNEF(self):
        """
        Export the current project as a Nef file
        Temporary routine because I don't know how else to do it yet
        """
        from ccpn.ui.gui.popups.ExportNefPopup import ExportNefPopup
        from ccpn.core.lib.CcpnNefIo import NEFEXTENSION

        _path = Path.aPath(self.preferences.general.userWorkingPath or '~').filepath / (self.project.name + NEFEXTENSION)
        dialog = ExportNefPopup(self.ui.mainWindow,
                                mainWindow=self.ui.mainWindow,
                                selectFile=_path,
                                fileFilter='*.nef',
                                minimumSize=(400, 550))

        # an exclusion dict comes out of the dialog as it
        result = dialog.exec_()

        if not result:
            return

        nefPath = result['filename']
        flags = result['flags']
        pidList = result['pidList']

        # flags are skipPrefixes, expandSelection
        skipPrefixes = flags['skipPrefixes']
        expandSelection = flags['expandSelection']

        self.project.exportNef(nefPath,
                               overwriteExisting=True,
                               skipPrefixes=skipPrefixes,
                               expandSelection=expandSelection,
                               pidList=pidList)

    def _getRecentFiles(self, oldPath=None) -> list:
        """Get and return a list of recent files, setting reference to
           self as first element, unless it is a temp project
           update the preferences with the new list

           CCPN INTERNAL: called by MainWindow
        """
        project = self.project
        path = project.path
        recentFiles = self.preferences.recentFiles

        if not project.isTemporary:
            if path in recentFiles:
                recentFiles.remove(path)
            elif oldPath in recentFiles:
                recentFiles.remove(oldPath)
            elif len(recentFiles) >= 10:
                recentFiles.pop()
            recentFiles.insert(0, path)
        recentFiles = uniquify(recentFiles)
        self.preferences.recentFiles = recentFiles
        return recentFiles

    def saveProjectAs(self):
        """Opens save Project as dialog box and saves project to path specified in the file dialog."""
        oldPath = self.project.path
        newPath = getSaveDirectory(self.ui.mainWindow, self.preferences)

        with catchExceptions(application=self, errorStringTemplate='Error saving project: %s', printTraceBack=True):
            if newPath:
                # Next line unnecessary, but does not hurt
                newProjectPath = apiIo.addCcpnDirectorySuffix(newPath)
                successful = self._saveProject(newPath=newProjectPath, createFallback=False)

                if not successful:
                    getLogger().warning("Saving project to %s aborted" % newProjectPath)
            else:
                successful = False
                getLogger().info("Project not saved - no valid destination selected")

            self._getRecentFiles(oldPath=oldPath)  # this will also update the list
            self.ui.mainWindow._fillRecentProjectsMenu()  # Update the menu

            return successful

    @logCommand('application.')
    def undo(self):
        if self.project._undo.canUndo():
            with MessageDialog.progressManager(self.ui.mainWindow, 'performing undo'):
                self.project._undo.undo()
        else:
            getLogger().warning('nothing to undo')

    @logCommand('application.')
    def redo(self):
        if self.project._undo.canRedo():
            with MessageDialog.progressManager(self.ui.mainWindow, 'performing redo'):
                self.project._undo.redo()
        else:
            getLogger().warning('nothing to redo.')

    def _getUndo(self):
        """Return the undo object for the project
        """
        if self.project:
            return self.project._undo
        else:
            raise RuntimeError('Error: undefined project')

    def _increaseNotificationBlocking(self):
        self._echoBlocking += 1

    def _decreaseNotificationBlocking(self):
        if self._echoBlocking > 0:
            self._echoBlocking -= 1
        else:
            raise RuntimeError('Error: decreaseNotificationBlocking, already at 0')

    def saveLogFile(self):
        pass

    def clearLogFile(self):
        pass

    def displayProjectSummary(self, position: str = 'left', relativeTo: CcpnModule = None):
        """
        Displays Project summary module on left of main window.
        """
        from ccpn.ui.gui.popups.ProjectSummaryPopup import ProjectSummaryPopup

        if self.ui:
            popup = ProjectSummaryPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, modal=True)
            popup.show()
            popup.raise_()
            popup.exec_()

    def archiveProject(self):

        project = self.project
        apiProject = project._wrappedData.parent
        fileName = apiIo.packageProject(apiProject, includeBackups=True, includeLogs=True,
                                        includeArchives=False, includeSummaries=True)

        MessageDialog.showInfo('Project Archived',
                               'Project archived to %s' % fileName, )

        self.ui.mainWindow._updateRestoreArchiveMenu()

    def _archivePaths(self):

        archivesDirectory = os.path.join(self.project.path, Path.CCPN_ARCHIVES_DIRECTORY)
        if os.path.exists(archivesDirectory):
            fileNames = os.listdir(archivesDirectory)
            paths = [os.path.join(archivesDirectory, fileName) for fileName in fileNames if fileName.endswith('.tgz')]
        else:
            paths = []

        return paths

    def restoreFromArchive(self, archivePath=None):
        """Restore a project from archive"""

        from ccpn.framework.lib._unpackCcpnTarFile import _unpackCcpnTarfile

        if not archivePath:
            archivesDirectory = Path.aPath(self.project.path) / Path.CCPN_ARCHIVES_DIRECTORY
            _filter = '*.tgz'
            dialog = ArchivesFileDialog(parent=self.ui.mainWindow, acceptMode='select', directory=archivesDirectory, fileFilter=_filter)
            dialog._show()
            archivePath = dialog.selectedFile()

        if archivePath:
            directoryPrefix = archivePath[:-4]  # -4 removes the .tgz
            outputPath, temporaryDirectory = _unpackCcpnTarfile(archivePath, outputPath=directoryPrefix)
            pythonExe = os.path.join(Path.getTopDirectory(), Path.CCPN_PYTHON)
            command = [pythonExe, sys.argv[0], outputPath]
            from subprocess import Popen

            Popen(command)

    # def _unpackCcpnTarfile(self, tarfilePath, outputPath=None, directoryPrefix='CcpnProject_'):
    #     """
    #     # CCPN INTERNAL - called in loadData method of Project
    #     """
    #
    #     if outputPath:
    #         if not os.path.exists(outputPath):
    #             os.makedirs(outputPath)
    #         temporaryDirectory = None
    #     else:
    #         temporaryDirectory = tempfile.TemporaryDirectory(prefix=directoryPrefix)
    #         outputPath = temporaryDirectory.name
    #
    #     cwd = os.getcwd()
    #     try:
    #         os.chdir(outputPath)
    #         tp = tarfile.open(tarfilePath)
    #         tp.extractall()
    #
    #         # look for a directory inside and assume the first found is the project directory (there should be exactly one)
    #         relfiles = os.listdir('.')
    #         for relfile in relfiles:
    #             fullfile = os.path.join(outputPath, relfile)
    #             if os.path.isdir(fullfile):
    #                 outputPath = fullfile
    #                 break
    #         else:
    #             raise IOError('Could not find project directory in tarfile')
    #
    #     finally:
    #         os.chdir(cwd)
    #
    #     return outputPath, temporaryDirectory

    def showApplicationPreferences(self):
        """
        Displays Application Preferences Popup.
        """
        from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup

        popup = PreferencesPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, preferences=self.preferences)
        popup.exec_()

    def getSavedLayoutPath(self):
        """Opens a saved Layout as dialog box and gets directory specified in the file dialog."""

        fType = 'JSON (*.json)'
        dialog = LayoutsFileDialog(parent=self.ui.mainWindow, acceptMode='open', fileFilter=fType)
        dialog._show()
        path = dialog.selectedFile()
        if not path:
            return
        if path:
            return path

    def getSaveLayoutPath(self):
        """Opens save Layout as dialog box and gets directory specified in the file dialog."""

        jsonType = '.json'
        fType = 'JSON (*.json)'
        dialog = LayoutsFileDialog(parent=self.ui.mainWindow, acceptMode='save', fileFilter=fType)
        dialog._show()
        newPath = dialog.selectedFile()
        if not newPath:
            return
        if newPath:

            if os.path.exists(newPath):
                # should not really need to check the second and third condition above, only
                # the Qt dialog stupidly insists a directory exists before you can select it
                # so if it exists but is empty then don't bother asking the question
                title = 'Overwrite path'
                msg = 'Path "%s" already exists, continue?' % newPath
                if not MessageDialog.showYesNo(title, msg):
                    newPath = ''
            if not newPath.endswith(jsonType):
                newPath += jsonType
            return newPath

    def _closeEvent(self, event=None):
        """
        Saves application preferences. Displays message box asking user to save project or not.
        Closes Application.
        """
        self.ui.mainWindow._closeEvent(event=event)

    def _closeMainWindows(self):
        tempModules = self.ui.mainWindow.application.ccpnModules
        if len(tempModules) > 0:
            for tempModule in tempModules:
                getLogger().debug('closing module: %s' % tempModule)
                try:
                    tempModule.close()
                except Exception as es:
                    # wrapped C/C++ object of type StripDisplay1d has been deleted
                    getLogger().debug(f'_closeMainWindows: {es}')

    def _closeExtraWindows(self):
        tempAreas = self.ui.mainWindow.moduleArea.tempAreas
        if len(tempAreas) > 0:
            for tempArea in tempAreas:
                getLogger().debug('closing external module: %s' % tempArea.window())
                try:
                    tempArea.window().close()
                except Exception as es:
                    # wrapped C/C++ object of type StripDisplay1d has been deleted
                    getLogger().debug(f'_closeExtraWindows: {es}')

    def _setMainWindowsVisible(self, value):
        """Set visibility of the main windows
        """
        tempModules = self.ui.mainWindow.application.ccpnModules
        if len(tempModules) > 0:
            for tempModule in tempModules:
                try:
                    tempModule.setVisible(value)
                except Exception as es:
                    # wrapped C/C++ object of type StripDisplay1d has been deleted
                    getLogger().debug(f'_setMainWindowsVisible: {es}')

    def _setExtraWindowsVisible(self, value):
        """Set visibility of the extra windows
        """
        tempAreas = self.ui.mainWindow.moduleArea.tempAreas
        if len(tempAreas) > 0:
            for tempArea in tempAreas:
                try:
                    tempArea.window().setVisible(value)
                except Exception as es:
                    # wrapped C/C++ object of type StripDisplay1d has been deleted
                    getLogger().debug(f'_setExtraWindowsVisible: {es}')

    def _closeProject(self):
        """Close project and clean up - when opening another or quitting application
        """

        # NB: this function must clean up both wrapper and ui/gui

        self.deleteAllNotifiers()
        if self.ui.mainWindow:
            # ui/gui cleanup
            self._setMainWindowsVisible(False)
            self._setExtraWindowsVisible(False)
            self._closeMainWindows()
            self._closeExtraWindows()
            self.ui.mainWindow.sideBar.deleteLater()
            self.ui.mainWindow.deleteLater()
            self.ui.mainWindow = None

        if self.current:
            self.current._unregisterNotifiers()
            self.current = None

        if self.project is not None:
            # Cleans up wrapper project, including graphics data objects (Window, Strip, etc.)
            self.project._close()
            self._project = None

    ###################################################################################################################
    ## MENU callbacks:  Spectrum
    ###################################################################################################################

    def showSpectrumGroupsPopup(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Specta. Spectrum groups cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Spectrum groups cannot be displayed')
        else:
            from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor

            if not self.project.spectrumGroups:
                #GST This seems to have problems MessageDialog wraps it which looks bad...
                # MessageDialog.showWarning('Project has no Spectrum Groups.',
                #                           'Create them using:\nSidebar → SpectrumGroups → <New SpectrumGroup>\n ')
                SpectrumGroupEditor(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, editMode=False).exec_()

            else:
                SpectrumGroupEditor(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, editMode=True, obj=self.project.spectrumGroups[0]).exec_()

    def showProjectionPopup(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Specta. Make Projection Popup cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Make Projection Popup cannot be displayed')
        else:
            from ccpn.ui.gui.popups.SpectrumProjectionPopup import SpectrumProjectionPopup

            popup = SpectrumProjectionPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def showExperimentTypePopup(self):
        """
        Displays experiment type popup.
        """
        if not self.project.spectra:
            getLogger().warning('Experiment Type Selection: Project has no Specta.')
            MessageDialog.showWarning('Experiment Type Selection', 'Project has no Spectra.')
        else:
            from ccpn.ui.gui.popups.ExperimentTypePopup import ExperimentTypePopup

            popup = ExperimentTypePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def showValidateSpectraPopup(self, spectra=None, defaultSelected=None):
        """
        Displays validate spectra popup.
        """
        if not self.project.spectra:
            getLogger().warning('Validate Spectrum Paths Selection: Project has no Specta.')
            MessageDialog.showWarning('Validate Spectrum Paths Selection', 'Project has no Spectra.')
        else:
            from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraPopup

            popup = ValidateSpectraPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, spectra=spectra, defaultSelected=defaultSelected)
            popup.exec_()

    def showPeakPick1DPopup(self):
        """
        Displays Peak Picking 1D Popup.
        """
        if not self.project.peakLists:
            getLogger().warning('Peak Picking: Project has no peakLists.')
            MessageDialog.showWarning('Peak Picking', 'Project has no peakLists.')
        else:
            spectra = [spec for spec in self.project.spectra if spec.dimensionCount == 1]
            if spectra:
                from ccpn.ui.gui.popups.PickPeaks1DPopup import PickPeak1DPopup

                popup = PickPeak1DPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
                popup.exec_()
            else:
                getLogger().warning('Peak Picking: Project has no 1d Specta.')
                MessageDialog.showWarning('Peak Picking', 'Project has no 1d Spectra.')

    def showPeakPickNDPopup(self):
        """
        Displays Peak Picking ND Popup.
        """
        if not self.project.peakLists:
            getLogger().warning('Peak Picking: Project has no peakLists.')
            MessageDialog.showWarning('Peak Picking', 'Project has no peakLists.')
        else:
            spectra = [spec for spec in self.project.spectra if spec.dimensionCount > 1]
            if spectra:
                from ccpn.ui.gui.popups.PeakFind import PeakFindPopup

                popup = PeakFindPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
                popup.exec_()
            else:
                getLogger().warning('Peak Picking: Project has no Nd Specta.')
                MessageDialog.showWarning('Peak Picking', 'Project has no Nd Spectra.')

    def showCopyPeakListPopup(self):
        if not self.project.peakLists:
            getLogger().warning('Project has no Peak Lists. Peak Lists cannot be copied')
            MessageDialog.showWarning('Project has no Peak Lists.', 'Peak Lists cannot be copied')
            return
        else:
            from ccpn.ui.gui.popups.CopyPeakListPopup import CopyPeakListPopup

            popup = CopyPeakListPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def showCopyPeaks(self):
        if not self.project.peakLists:
            getLogger().warning('Project has no Peak Lists. Peak Lists cannot be copied')
            MessageDialog.showWarning('Project has no Peak Lists.', 'Peak Lists cannot be copied')
            return
        else:
            from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

            popup = CopyPeaks(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            peaks = self.current.peaks
            popup._selectPeaks(peaks)
            popup.exec()
            popup.raise_()

    def showEstimateVolumesPopup(self):
        """
        Displays Estimate Volumes Popup.
        """
        if not self.project.peakLists:
            getLogger().warning('Estimate Volumes: Project has no peakLists.')
            MessageDialog.showWarning('Estimate Volumes', 'Project has no peakLists.')
        else:
            from ccpn.ui.gui.popups.EstimateVolumes import EstimateVolumes

            if self.current.strip and not self.current.strip.isDeleted:
                spectra = [specView.spectrum for specView in self.current.strip.spectrumDisplay.spectrumViews]
            else:
                spectra = self.project.spectra

            if spectra:
                popup = EstimateVolumes(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, spectra=spectra)
                popup.exec_()
            else:
                getLogger().warning('Peak Picking: no specta selected.')
                MessageDialog.showWarning('Peak Picking', 'no specta selected.')

    def makeStripPlotPopup(self, includePeakLists=True, includeNmrChains=True, includeNmrChainPullSelection=True):
        if not self.project.peaks and not self.project.nmrResidues and not self.project.nmrChains:
            getLogger().warning('Cannot make strip plot, nothing to display')
            MessageDialog.showWarning('Cannot make strip plot,', 'nothing to display')
            return
        else:
            if len(self.project.spectrumDisplays) == 0:
                MessageDialog.showWarning('', 'No SpectrumDisplay found')

            elif self.current.strip and not self.current.strip.isDeleted:
                from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup

                popup = StripPlotPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow,
                                       spectrumDisplay=self.current.strip.spectrumDisplay,
                                       includePeakLists=includePeakLists, includeNmrChains=includeNmrChains,
                                       includeNmrChainPullSelection=includeNmrChainPullSelection, includeSpectrumTable=False)
                popup.exec_()

    ################################################################################################
    ## MENU callbacks:  Molecule
    ################################################################################################

    @logCommand('application.')
    def showCreateChainPopup(self):
        """
        Displays sequence creation popup.
        """
        from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup

        popup = CreateChainPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
        popup.exec_()

    # @logCommand('application.')
    # def toggleSequenceModule(self):
    #     """
    #     Toggles whether Sequence Module is displayed or not
    #     """
    #     self.showSequenceModule()

    # @logCommand('application.')
    # def showSequenceModule(self, position='top', relativeTo=None):
    #     """
    #     Displays Sequence Module at the top of the screen.
    #     """
    #     from ccpn.ui.gui.modules.SequenceModule import SequenceModule
    #
    #     if SequenceModule._alreadyOpened is False:
    #         mainWindow = self.ui.mainWindow
    #         self.sequenceModule = SequenceModule(mainWindow=mainWindow)
    #         mainWindow.moduleArea.addModule(self.sequenceModule,
    #                                         position=position, relativeTo=relativeTo)
    #         action = self._findMenuAction('View', 'Show Sequence')
    #         if action:
    #             action.setChecked(True)
    #
    #         # set the colours of the currently highlighted chain in open sequenceGraph
    #         # should really be in the class, but doesn't fire correctly during __init__
    #         self.sequenceModule.populateFromSequenceGraphs()

    # @logCommand('application.')
    # def hideSequenceModule(self):
    #     """Hides sequence module"""
    #
    #     if hasattr(self, 'sequenceModule'):
    #         self.sequenceModule.close()
    #         delattr(self, 'sequenceModule')

    def inspectMolecule(self):
        pass

    @logCommand('application.')
    def showResidueInformation(self, position: str = 'bottom', relativeTo: CcpnModule = None):
        """Displays Residue Information module.
        """
        from ccpn.ui.gui.modules.ResidueInformation import ResidueInformation

        if not self.project.residues:
            getLogger().warning('No Residues in project. Residue Information Module requires Residues in the project to launch.')
            MessageDialog.showWarning('No Residues in project.',
                                      'Residue Information Module requires Residues in the project to launch.')
            return

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea  # ejb
        residueModule = ResidueInformation(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(residueModule, position=position, relativeTo=relativeTo)
        return residueModule

    @logCommand('application.')
    def showReferenceChemicalShifts(self, position='left', relativeTo=None):
        """Displays Reference Chemical Shifts module."""
        from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        refChemShifts = ReferenceChemicalShifts(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(refChemShifts, position=position, relativeTo=relativeTo)
        return refChemShifts

    ###################################################################################################################
    ## MENU callbacks:  VIEW
    ###################################################################################################################

    @logCommand('application.')
    def showChemicalShiftTable(self,
                               position: str = 'bottom',
                               relativeTo: CcpnModule = None,
                               chemicalShiftList=None, selectFirstItem=False):
        """Displays Chemical Shift table.
        """
        from ccpn.ui.gui.modules.ChemicalShiftTable import ChemicalShiftTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        chemicalShiftTableModule = ChemicalShiftTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(chemicalShiftTableModule, position=position, relativeTo=relativeTo)
        if chemicalShiftList:
            chemicalShiftTableModule.selectChemicalShiftList(chemicalShiftList)
        return chemicalShiftTableModule

    @logCommand('application.')
    def showNmrResidueTable(self, position='bottom', relativeTo=None,
                            nmrChain=None, selectFirstItem=False):
        """Displays Nmr Residue Table
        """
        from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        nmrResidueTableModule = NmrResidueTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(nmrResidueTableModule, position=position, relativeTo=relativeTo)
        if nmrChain:
            nmrResidueTableModule.selectNmrChain(nmrChain)
        return nmrResidueTableModule

    @logCommand('application.')
    def showResidueTable(self, position='bottom', relativeTo=None,
                         chain=None, selectFirstItem=False):
        """Displays  Residue Table
        """
        from ccpn.ui.gui.modules.ResidueTable import ResidueTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        residueTableModule = ResidueTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(residueTableModule, position=position, relativeTo=relativeTo)
        if chain:
            residueTableModule.selectChain(chain)
        return residueTableModule

    @logCommand('application.')
    def showPeakTable(self, position: str = 'left', relativeTo: CcpnModule = None,
                      peakList: PeakList = None, selectFirstItem=False):
        """Displays Peak table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.PeakTable import PeakTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        peakTableModule = PeakTableModule(mainWindow, selectFirstItem=selectFirstItem)
        if peakList:
            peakTableModule.selectPeakList(peakList)
        mainWindow.moduleArea.addModule(peakTableModule, position=position, relativeTo=relativeTo)
        return peakTableModule

    @logCommand('application.')
    def showMultipletTable(self, position: str = 'left', relativeTo: CcpnModule = None,
                           multipletList: MultipletList = None, selectFirstItem=False):
        """Displays multipletList table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.MultipletListTable import MultipletTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        multipletTableModule = MultipletTableModule(mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(multipletTableModule, position=position, relativeTo=relativeTo)
        if multipletList:
            multipletTableModule.selectMultipletList(multipletList)
        return multipletTableModule

    @logCommand('application.')
    def showIntegralTable(self, position: str = 'left', relativeTo: CcpnModule = None,
                          integralList: IntegralList = None, selectFirstItem=False):
        """Displays integral table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.IntegralTable import IntegralTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        integralTableModule = IntegralTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(integralTableModule, position=position, relativeTo=relativeTo)
        if integralList:
            integralTableModule.selectIntegralList(integralList)
        return integralTableModule

    @logCommand('application.')
    def showRestraintTable(self, position: str = 'bottom', relativeTo: CcpnModule = None,
                           restraintTable: PeakList = None, selectFirstItem=False):
        """Displays Peak table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.RestraintTableModule import RestraintTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        restraintTableModule = RestraintTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(restraintTableModule, position=position, relativeTo=relativeTo)
        if restraintTable:
            restraintTableModule.selectRestraintTable(restraintTable)
        return restraintTableModule

    @logCommand('application.')
    def showStructureTable(self, position='bottom', relativeTo=None,
                           structureEnsemble=None, selectFirstItem=False):
        """Displays Structure Table
        """
        from ccpn.ui.gui.modules.StructureTable import StructureTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        structureTableModule = StructureTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(structureTableModule, position=position, relativeTo=relativeTo)
        if structureEnsemble:
            structureTableModule.selectStructureEnsemble(structureEnsemble)
        return structureTableModule

    @logCommand('application.')
    def showDataTable(self, position='bottom', relativeTo=None,
                      dataTable=None, selectFirstItem=False):
        """Displays DataTable Table
        """
        from ccpn.ui.gui.modules.DataTableModuleABC import DataTableModuleBC

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        if dataTable:
            _dataTableModule = DataTableModuleBC(dataTable, name=dataTable.name, mainWindow=mainWindow)
            mainWindow.moduleArea.addModule(_dataTableModule, position=position, relativeTo=relativeTo)
            return _dataTableModule

    @logCommand('application.')
    def showViolationTable(self, position: str = 'bottom', relativeTo: CcpnModule = None,
                           violationTable: PeakList = None, selectFirstItem=False):
        """Displays Peak table on left of main window with specified list selected.
        """
        getLogger().debug('No ViolationTable module')
        # from ccpn.ui.gui.modules.ViolationTableModule import ViolationTableModule
        #
        # mainWindow = self.ui.mainWindow
        # if not relativeTo:
        #     relativeTo = mainWindow.moduleArea
        # violationTableModule = ViolationTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        # mainWindow.moduleArea.addModule(violationTableModule, position=position, relativeTo=relativeTo)
        # if violationTable:
        #     violationTableModule.selectViolationTable(violationTable)
        # return violationTableModule

    @logCommand('application.')
    def showCollectionModule(self, position='bottom', relativeTo=None,
                             collection=None, selectFirstItem=False):
        """Displays Collection Module
        """
        pass

    @logCommand('application.')
    def showNotesEditor(self, position: str = 'bottom', relativeTo: CcpnModule = None,
                        note=None, selectFirstItem=False):
        """Displays Notes Editing Table
        """
        from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        notesEditorModule = NotesEditorModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(notesEditorModule, position=position, relativeTo=relativeTo)
        if note:
            notesEditorModule.selectNote(note)
        return notesEditorModule

    @logCommand('application.')
    def showRestraintAnalysisTable(self,
                                   position: str = 'bottom',
                                   relativeTo: CcpnModule = None,
                                   peakList=None, selectFirstItem=False):
        """Displays restraint analysis table.
        """
        from ccpn.ui.gui.modules.RestraintAnalysisTable import RestraintAnalysisTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        restraintAnalysisTableModule = RestraintAnalysisTableModule(mainWindow=mainWindow, selectFirstItem=selectFirstItem)
        mainWindow.moduleArea.addModule(restraintAnalysisTableModule, position=position, relativeTo=relativeTo)
        if peakList:
            restraintAnalysisTableModule.selectPeakList(peakList)
        return restraintAnalysisTableModule

    def showPrintSpectrumDisplayPopup(self):
        """Show the print spectrumDisplay dialog
        """
        from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup

        if len(self.project.spectrumDisplays) == 0:
            MessageDialog.showWarning('', 'No SpectrumDisplay found')
        else:
            exportDialog = ExportStripToFilePopup(parent=self.ui.mainWindow,
                                                  mainWindow=self.ui.mainWindow,
                                                  strips=self.project.strips,
                                                  selectedStrip=self.current.strip
                                                  )
            exportDialog.exec_()

    def toggleToolbar(self):
        if self.current.strip is not None:
            self.current.strip.spectrumDisplay.toggleToolbar()
        else:
            getLogger().warning('No strip selected')

    def toggleSpectrumToolbar(self):
        if self.current.strip is not None:
            self.current.strip.spectrumDisplay.toggleSpectrumToolbar()
        else:
            getLogger().warning('No strip selected')

    def togglePhaseConsole(self):
        if self.current.strip is not None:
            self.current.strip.spectrumDisplay.togglePhaseConsole()
        else:
            getLogger().warning('No strip selected')

    def _setZoomPopup(self):
        if self.current.strip is not None:
            self.current.strip._setZoomPopup()
        else:
            getLogger().warning('No strip selected')

    def resetZoom(self):
        if self.current.strip is not None:
            self.current.strip.resetZoom()
        else:
            getLogger().warning('No strip selected')

    def copyStrip(self):
        if self.current.strip is not None:
            self.current.strip.copyStrip()
        else:
            getLogger().warning('No strip selected')

    def showFlipArbitraryAxisPopup(self):
        if self.current.strip is not None:

            if self.current.strip.spectrumDisplay.is1D:
                getLogger().warning('Function not permitted on 1D spectra')
            else:

                from ccpn.ui.gui.popups.CopyStripFlippedAxesPopup import CopyStripFlippedSpectraPopup

                popup = CopyStripFlippedSpectraPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow,
                                                     strip=self.current.strip, label=self.current.strip.id)
                popup.exec_()

        else:
            getLogger().warning('No strip selected')

    def showReorderPeakListAxesPopup(self):
        """
        Displays Reorder PeakList Axes Popup.
        """
        if not self.project.peakLists:
            getLogger().warning('Reorder PeakList Axes: Project has no peakLists.')
            MessageDialog.showWarning('Reorder PeakList Axes', 'Project has no peakLists.')
        else:
            from ccpn.ui.gui.popups.ReorderPeakListAxes import ReorderPeakListAxes

            popup = ReorderPeakListAxes(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _flipXYAxisCallback(self):
        """Callback to flip axes"""
        if self.current.strip is not None:
            self.current.strip.flipXYAxis()
        else:
            getLogger().warning('No strip selected')

    def _flipXZAxisCallback(self):
        """Callback to flip axes"""
        if self.current.strip is not None:
            self.current.strip.flipXZAxis()
        else:
            getLogger().warning('No strip selected')

    def _flipYZAxisCallback(self):
        """Callback to flip axes"""
        if self.current.strip is not None:
            self.current.strip.flipYZAxis()
        else:
            getLogger().warning('No strip selected')

    def _findMenuAction(self, menubarText, menuText):
        # not sure if this function will be needed more widely or just in console context
        # CCPN internal: now also used in SequenceModule._closeModule

        #GWV should not be here; moved to GuiMainWindow
        self.ui.mainWindow._findMenuAction(menubarText, menuText)

    def _toggleConsoleCallback(self):
        """Toggles whether python console is displayed at bottom of the main window.
        """
        self.ui.mainWindow.toggleConsole()

    def showChemicalShiftMapping(self, position: str = 'top', relativeTo: CcpnModule = None):
        from ccpn.ui.gui.modules.ChemicalShiftsMappingModule import ChemicalShiftsMapping

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        cs = ChemicalShiftsMapping(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(cs, position=position, relativeTo=relativeTo)
        return cs

    #################################################################################################
    ## MENU callbacks:  Macro
    #################################################################################################

    @logCommand('application.')
    def _showMacroEditorCallback(self):
        """Displays macro editor. Just handing down to MainWindow for now
        """
        self.mainWindow.newMacroEditor()

    def _openMacroCallback(self, directory=None):
        """ Select macro file and on MacroEditor.
        """
        mainWindow = self.ui.mainWindow
        dialog = MacrosFileDialog(parent=mainWindow, acceptMode='open', fileFilter='*.py', directory=directory)
        dialog._show()
        path = dialog.selectedFile()
        if path is not None:
            self.mainWindow.newMacroEditor(path=path)

    def defineUserShortcuts(self):

        from ccpn.ui.gui.popups.ShortcutsPopup import ShortcutsPopup

        ShortcutsPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()

    def runMacro(self, macroFile: str = None):
        """
        Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
        runs the selected macro.
        """
        if macroFile is None:
            fType = '*.py'
            dialog = MacrosFileDialog(parent=self.ui.mainWindow, acceptMode='run', fileFilter=fType)
            dialog._show()
            macroFile = dialog.selectedFile()
            if not macroFile:
                return

        if not macroFile in self.preferences.recentMacros:
            self.preferences.recentMacros.append(macroFile)
        self.ui.mainWindow.pythonConsole._runMacro(macroFile)

    ###################################################################################################################
    ## MENU callbacks:  Help
    ###################################################################################################################

    def _systemOpen(self, path):
        """Open path on system"""
        if isWindowsOS():
            os.startfile(path)
        elif isMacOS():
            subprocess.run(['open', path], check=True)
        else:
            linuxCommand = self.preferences.externalPrograms.PDFViewer
            # assume a linux and use the choice given in the preferences
            if linuxCommand:
                from ccpn.framework.PathsAndUrls import ccpnRunTerminal

                # NOTE:ED - this could be quite nasty, but can't think of another way to get Linux to open a pdf
                subprocess.run([ccpnRunTerminal, linuxCommand, path], check=True)
            else:
                raise TypeError('PDFViewer not defined for linux')

    def _showHtmlFile(self, title, urlPath):
        """Displays html files in program QT viewer or using native webbrowser depending on useNativeWebbrowser option"""

        mainWindow = self.ui.mainWindow

        if self.preferences.general.useNativeWebbrowser:
            import webbrowser
            import posixpath

            # may be a Path object
            urlPath = str(urlPath)

            urlPath = urlPath or ''
            if (urlPath.startswith('http://') or urlPath.startswith('https://')):
                pass
            elif urlPath.startswith('file://'):
                urlPath = urlPath[len('file://'):]
                if isWindowsOS():
                    urlPath = urlPath.replace(os.sep, posixpath.sep)
                else:
                    urlPath = 'file://' + urlPath
            else:
                if isWindowsOS():
                    urlPath = urlPath.replace(os.sep, posixpath.sep)
                else:
                    urlPath = 'file://' + urlPath

            webbrowser.open(urlPath)
            # self._systemOpen(path)
        else:
            # from ccpn.ui.gui.widgets.CcpnWebView import CcpnWebView
            #
            # _newModule = CcpnWebView(mainWindow=mainWindow, name=title, urlPath=urlPath)
            # self.ui.mainWindow.moduleArea.addModule(_newModule, position='top', relativeTo=mainWindow.moduleArea)
            mainWindow.newHtmlModule(urlPath=urlPath, position='top', relativeTo=mainWindow.moduleArea)

    def showBeginnersTutorial(self):
        from ccpn.framework.PathsAndUrls import beginnersTutorialPath

        self._systemOpen(beginnersTutorialPath)

    def showBackboneTutorial(self):
        from ccpn.framework.PathsAndUrls import backboneAssignmentTutorialPath

        self._systemOpen(backboneAssignmentTutorialPath)

    def showCSPtutorial(self):
        from ccpn.framework.PathsAndUrls import cspTutorialPath

        self._systemOpen(cspTutorialPath)

    def showScreenTutorial(self):
        from ccpn.framework.PathsAndUrls import screenTutorialPath

        self._systemOpen(screenTutorialPath)

    def showVersion3Documentation(self):
        """Displays CCPN wrapper documentation in a module."""
        from ccpn.framework.PathsAndUrls import documentationPath

        self._showHtmlFile("Analysis Version-3 Documentation", documentationPath)

    def showForum(self):
        """Displays Forum in a module."""
        from ccpn.framework.PathsAndUrls import ccpnForum

        self._showHtmlFile("Analysis Version-3 Forum", ccpnForum)

    def showShortcuts(self):
        from ccpn.framework.PathsAndUrls import shortcutsPath

        self._systemOpen(shortcutsPath)

    def showAboutPopup(self):
        from ccpn.ui.gui.popups.AboutPopup import AboutPopup

        popup = AboutPopup(parent=self.ui.mainWindow)
        popup.exec_()

    def showAboutCcpn(self):
        from ccpn.framework.PathsAndUrls import ccpnUrl

        # import webbrowser

        # webbrowser.open(ccpnUrl)
        self._showHtmlFile("About CCPN", ccpnUrl)

    def showCcpnLicense(self):
        from ccpn.framework.PathsAndUrls import ccpnLicenceUrl

        # import webbrowser

        # webbrowser.open(ccpnLicenceUrl)
        self._showHtmlFile("CCPN Licence", ccpnLicenceUrl)

    def showCodeInspectionPopup(self):
        # TODO: open a file browser to top of source directory
        pass

    def showIssuesList(self):
        from ccpn.framework.PathsAndUrls import ccpnIssuesUrl

        # import webbrowser

        # webbrowser.open(ccpnIssuesUrl)
        self._showHtmlFile("CCPN Issues", ccpnIssuesUrl)

    def showTutorials(self):
        from ccpn.framework.PathsAndUrls import ccpnTutorials

        # import webbrowser

        # webbrowser.open(ccpnTutorials)
        self._showHtmlFile("CCPN Tutorials", ccpnTutorials)

    def showUpdatePopup(self):
        """Open the update popup
        """
        from ccpn.framework.update.UpdatePopup import UpdatePopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            self.updatePopup = UpdatePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            self.updatePopup.exec_()

            # if updates have been installed then popup the quit dialog with no cancel button
            if self.updatePopup._numUpdatesInstalled > 0:
                self.ui.mainWindow._closeWindowFromUpdate(disableCancel=True)

        else:
            MessageDialog.showWarning('Check For Updates',
                                      'Could not connect to the update server, please check your internet connection.')

    def showRegisterPopup(self):
        """Open the registration popup
        """
        self.ui._registerDetails()

    def showFeedbackPopup(self):
        """Open the submit feedback popup
        """
        from ccpn.ui.gui.popups.FeedbackPopup import FeedbackPopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():

            # this is non-modal so you can copy/paste from the project as required
            if not self.feedbackPopup:
                self.feedbackPopup = FeedbackPopup(parent=self.ui.mainWindow)
            self.feedbackPopup.show()
            self.feedbackPopup.raise_()

        else:
            MessageDialog.showWarning('Submit Feedback',
                                      'Could not connect to the server, please check your internet connection.')

    def showSubmitMacroPopup(self):
        """Open the submit macro popup
        """
        from ccpn.ui.gui.popups.SubmitMacroPopup import SubmitMacroPopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            if not self.submitMacroPopup:
                self.submitMacroPopup = SubmitMacroPopup(parent=self.ui.mainWindow)
            self.submitMacroPopup.show()
            self.submitMacroPopup.raise_()

        else:
            MessageDialog.showWarning('Submit Macro',
                                      'Could not connect to the server, please check your internet connection.')

    def showLicense(self):
        from ccpn.framework.PathsAndUrls import licensePath

        # self._systemOpen(licensePath)
        self._showHtmlFile("CCPN Licence", licensePath)

    #########################################    End Menu callbacks   ##################################################

    def _initialiseFonts(self):

        from ccpn.ui.gui.guiSettings import fontSettings

        self._fontSettings = fontSettings(self.preferences)


def getSaveDirectory(parent, preferences=None):
    """Opens save Project as dialog box and gets directory specified in the file dialog."""

    dialog = ProjectSaveFileDialog(parent=parent, acceptMode='save')
    dialog._show()
    newPath = dialog.selectedFile()

    # if not iterable then ignore - dialog may return string or tuple(<path>, <fileOptions>)
    if isinstance(newPath, tuple) and len(newPath) > 0:
        newPath = newPath[0]

    # ignore if empty
    if not newPath:
        return

    if newPath:

        # native dialog returns a tuple: (path, ''); ccpn returns a string
        if isinstance(newPath, tuple):
            newPath = newPath[0]
            if not newPath:
                return None

        newPath = apiIo.addCcpnDirectorySuffix(newPath)
        if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
            # should not really need to check the second and third condition above, only
            # the Qt dialog stupidly insists a directory exists before you can select it
            # so if it exists but is empty then don't bother asking the question
            title = 'Overwrite path'
            msg = 'Path "%s" already exists, continue?' % newPath
            if not MessageDialog.showYesNo(title, msg):
                newPath = ''

        return newPath


########

def getPreferences(skipUserPreferences=False, defaultPath=None, userPath=None):
    from ccpn.framework.PathsAndUrls import defaultPreferencesPath

    try:
        def _updateDict(d, u):
            import collections

            # recursive update of dictionary
            # this deletes every key in u that is not in d
            # if we want every key regardless, then remove first if check below
            for k, v in u.items():
                if k not in d:
                    continue
                if isinstance(v, collections.Mapping):
                    r = _updateDict(d.get(k, {}), v)
                    d[k] = r
                else:
                    d[k] = u[k]
            return d

        # read the default settings
        preferencesPath = (defaultPath if defaultPath else defaultPreferencesPath)
        with open(preferencesPath) as fp:
            preferences = json.load(fp, object_hook=AttrDict)

        # read user settings and update if not skipped
        if not skipUserPreferences:
            # from ccpn.framework.PathsAndUrls import userPreferencesPath

            preferencesPath = (userPath if userPath else os.path.expanduser(userPreferencesPath))
            if os.path.isfile(preferencesPath):
                with open(preferencesPath) as fp:
                    userPreferences = json.load(fp, object_hook=AttrDict)
                preferences = _updateDict(preferences, userPreferences)
    except:  #should we have the preferences hard coded as py dict for extra safety? if json goes wrong the whole project crashes!
        with open(defaultPreferencesPath) as fp:
            preferences = json.load(fp, object_hook=AttrDict)

    return preferences


def testMain():
    # from sandbox.Geerten.Refactored.framework import Framework
    # from sandbox.Geerten.Refactored.programArguments import Arguments

    # from ccpn.framework.Framework import Framework
    # from ccpn.framework.Framework import Arguments

    _makeMainWindowVisible = False


    class MyProgramme(Framework):
        """My first app"""
        pass


    myArgs = Arguments()
    myArgs.noGui = False
    myArgs.debug = True

    application = MyProgramme('MyProgramme', '3.0.1', args=myArgs)
    ui = application.ui
    ui.initialize(ui.mainWindow)  # ui.mainWindow not needed for refactored?

    if _makeMainWindowVisible:
        ui.mainWindow._updateMainWindow(newProject=True)
        ui.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(ui.mainWindow)

    # register the programme
    from ccpn.framework.Application import ApplicationContainer

    container = ApplicationContainer()
    container.register(application)
    application.useFileLogger = True


if __name__ == '__main__':
    testMain()
