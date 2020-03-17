#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-03-17 01:55:31 +0000 (Tue, March 17, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time as systime
if not hasattr(systime, 'clock'):
    # NOTE:ED - quick patch to fix bug in pyqt 5.9
    systime.clock = systime.process_time

import json
import logging
import os
import platform
import sys
import tarfile
import tempfile
import re
import subprocess
from PyQt5 import QtWidgets
from distutils.dir_util import copy_tree
from functools import partial
from ccpn.core.IntegralList import IntegralList
from ccpn.core.PeakList import PeakList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Project import Project
from ccpn.core._implementation import Io as coreIo
from ccpn.core.lib import CcpnNefIo, CcpnSparkyIo
from ccpn.core.lib.Notifiers import NotifierBase, Notifier
from ccpn.core.lib.Pid import Pid
from ccpn.framework import Version
from ccpn.framework.Current import Current
from ccpn.framework.lib.Pipeline import Pipeline
from ccpn.framework.Translation import languages, defaultLanguage
from ccpn.framework.Translation import translator
from ccpn.framework.PathsAndUrls import userPreferencesPath
from ccpn.framework.PathsAndUrls import userPreferencesDirectory
from ccpn.ui import interfaces, defaultInterface
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.lib.GuiSpectrumView import _createdSpectrumView
from ccpn.util import Logging
from ccpn.util import Path
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Common import uniquify, isWindowsOS
from ccpn.util.Logging import getLogger
from ccpn.util import Layout
from ccpn.ui.gui.Gui import Gui
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import catchExceptions
from ccpn.ui.gui.widgets.Menu import SHOWMODULESMENU, CCPNMACROSMENU, TUTORIALSMENU, PLUGINSMENU, CCPNPLUGINSMENU

import faulthandler
faulthandler.enable()

# from functools import partial

_DEBUG = False

# componentNames = ('Assignment', 'Screening', 'Structure')

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


def _ccpnExceptionhook(type, value, tback):
    '''This because PyQT raises and catches exceptions,
    but doesn't pass them along instead makes the program crashing miserably.'''
    sys.__excepthook__(type, value, tback)


sys.excepthook = _ccpnExceptionhook


def printCreditsText(fp, programName, version):
    """Initial text to terminal """
    from ccpn.framework.PathsAndUrls import ccpnLicenceUrl

    lines = []  # ejb
    lines.append("%s, version: %s" % (programName, version))
    lines.append("")
    # lines.append("%s" % __copyright__[0:__copyright__.index('-')] + '- 2016')
    lines.append("%s" % __copyright__)
    lines.append("")
    lines.append("CCPN licence. See %s. Not to be distributed without prior consent!" % ccpnLicenceUrl)
    lines.append("")

    try:
        if isinstance(__credits__, str):
            lines.append("Developed by: %s" % __credits__)
        else:
            if isinstance(__credits__, tuple):
                lines.append("Developed by: %s" % __credits__[0])
                for crLine in __credits__[1:]:
                    lines.append("              %s" % crLine)
    except:
        pass

    lines.append("")
    try:
        if isinstance(__reference__, str):
            lines.append("Please cite:  %s" % __reference__)
        else:
            if isinstance(__reference__, tuple):
                lines.append("Please cite:  %s" % __reference__[0])
                for refLine in __reference__[1:]:
                    lines.append("              %s" % refLine)
    except:
        pass

    lines.append("")
    lines.append("DISCLAIMER:   This program is offered 'as-is'. Under no circumstances will the authors, CCPN,")
    lines.append("              the Department of Molecular and Cell Biology, or the University of Leicester be")
    lines.append("              liable of any damage, loss of data, loss of revenue or any other undesired")
    lines.append("              consequences originating from the usage of this software.")

    # print with aligning '|'s
    maxlen = max(map(len, lines))
    fp.write('%s\n' % ('=' * (maxlen + 8)))
    for line in lines:
        fp.write('|   %s ' % line + ' ' * (maxlen - len(line)) + '  |\n')
    fp.write('%s\n' % ('=' * (maxlen + 8)))


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
        self.revision = Version.revision
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

        self.preferences = None  # intialised by self._getUserPrefs
        self.layout = None  # intialised by self._getUserLayout
        self.styleSheet = None  # intialised by self.getStyleSheet
        self.colourScheme = None  # intialised by self.getStyleSheet

        # Necessary as attribute is queried during initialisation:
        self._mainWindow = None

        # This is needed to make project available in NoUi (if nothing else)
        self.project = None

        # Blocking level for command echo and logging
        self._echoBlocking = 0
        self._enableLoggingToConsole = True

        # NEF reader
        self.nefReader = CcpnNefIo.CcpnNefReader(self)

        # SPARKY reader - ejb
        self.sparkyReader = CcpnSparkyIo.CcpnSparkyReader(self)

        self._backupTimerQ = None
        self.autoBackupThread = None

        # NBNB TODO The following block should maybe be moved into _getUi
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

        self._registrationDict = {}
        self._setLanguage()
        self.styleSheet = None
        self.ui = self._getUI()
        self.setupMenus()
        self.feedbackPopup = None
        self.submitMacroPopup = None
        self.updatePopup = None

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
        "Return True if application has a gui"
        return isinstance(self.ui, Gui)

    def _testShortcuts0(self):
        print('>>> Testing shortcuts0')

    def _testShortcuts1(self):
        print('>>> Testing shortcuts1')

    def start(self):
        """Start the program execution"""

        # register the programme for later
        from ccpn.framework.Application import ApplicationContainer

        container = ApplicationContainer()
        container.register(self)

        self._initialiseFonts()

        # Load / create project
        projectPath = self.args.projectPath
        if projectPath:
            project = self.loadProject(projectPath)

        else:
            project = self.newProject()
        self._updateCheckableMenuItems()

        if not self.ui._checkRegistration():
            return

        # if not self.ui._checkUpdates():
        #   return

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

        self.project = project

        # Pass an instance of framework to project so the UI instantiation can happen
        project._appBase = self

        # Set up current
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

        self.project = project
        if hasattr(self, '_mainWindow'):
            Logging.getLogger().debug('>>>framework._initialiseProject')

            project._blockSideBar = True
            self.ui.initialize(self._mainWindow)
            project._blockSideBar = False

            # Get the mainWindow out of the application top level once it's been transferred to ui
            del self._mainWindow
        else:
            # The NoUi version has no mainWindow
            self.ui.initialize(None)

    def _refreshAfterSave(self):
        """Refresh user interface after project save (which may have caused project rename)"""

        mainWindow = self.ui.mainWindow
        if mainWindow is not None:
            # mainWindow.sideBar.setProjectName(self.project)
            mainWindow.sideBar.setProjectName(self.project)

    def _getUI(self):
        if self.args.interface == 'Gui':
            self.styleSheet = self.getStyleSheet()
            from ccpn.ui.gui.Gui import Gui

            ui = Gui(self)
            ui.qtApp._ccpnApplication = self
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
        "Save the preferences to file"
        with catchExceptions(application=self, errorStringTemplate='Error saving preferences; "%s"'):
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
            if not os.path.exists(jsonFilePath):
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

    def correctColours(self):
        """Autocorrect all colours that are too close to the background colour
        """
        from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND

        if self.preferences.general.autoCorrectColours:
            project = self.project

            # change spectrum colours
            for spectrum in project.spectra:
                if len(spectrum.axisCodes) > 1:
                    spectrum.positiveContourColour = autoCorrectHexColour(spectrum.positiveContourColour,
                                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                    spectrum.negativeContourColour = autoCorrectHexColour(spectrum.negativeContourColour,
                                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                else:
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

    def initGraphics(self):
        """Set up graphics system after loading
        """
        from ccpn.ui.gui.lib import GuiStrip

        project = self.project

        # 20191113:ED Initial insertion of spectrumDisplays into the moduleArea
        insertPoint = self.ui.mainWindow.moduleArea
        for spectrumDisplay in project.spectrumDisplays:
            self.ui.mainWindow.moduleArea.addModule(spectrumDisplay,
                                                    position='right',
                                                    relativeTo=insertPoint)
            insertPoint = spectrumDisplay

        try:
            if self.preferences.general.restoreLayoutOnOpening:
                layout = self._getUserLayout()
                if layout:
                    Layout.restoreLayout(self._mainWindow, layout)
        except Exception as e:
            getLogger().warning('Impossible to restore Layout %s' % e)

        # Initialise displays
        for spectrumDisplay in project.windows[0].spectrumDisplays:  # there is exactly one window
            pass  # GWV: poor solution; removed the routine spectrumDisplay._resetRemoveStripAction()

        # initialise any colour changes before generating gui strips
        self.correctColours()

        # Initialise strips
        for strip in project.strips:
            GuiStrip._setupGuiStrip(project, strip._wrappedData)

            # if isinstance(strip, GuiStripNd) and not strip.haveSetupZWidgets:
            #   strip.setZWidgets()

        # Initialise SpectrumViews
        for spectrumDisplay in project.spectrumDisplays:

            strips = spectrumDisplay.orderedStrips
            for si, strip in enumerate(strips):

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

                    if True:            # tilePosition is None:
                        spectrumDisplay.stripFrame.layout().addWidget(strip, 0, si)  #stripIndex)
                        strip.tilePosition = (0, si)
                    else:
                        spectrumDisplay.stripFrame.layout().addWidget(strip, tilePosition[0], tilePosition[1])

                elif spectrumDisplay.stripArrangement == 'X':

                    if True:            #tilePosition is None:
                        spectrumDisplay.stripFrame.layout().addWidget(strip, si, 0)  #stripIndex)
                        strip.tilePosition = (0, si)
                    else:
                        spectrumDisplay.stripFrame.layout().addWidget(strip, tilePosition[1], tilePosition[0])

                elif spectrumDisplay.stripArrangement == 'T':

                    # NOTE:ED - Tiled plots not fully implemented yet
                    getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(spectrumDisplay))

                else:
                    getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(spectrumDisplay))

                if not spectrumDisplay.isGrouped:

                    # spectra are not grouped
                    specViews = strip.spectrumViews
                    # for iSV, spectrumView in enumerate(strip.orderedSpectrumViews(includeDeleted=False)):

                    for iSV, spectrumView in enumerate(spectrumDisplay.orderedSpectrumViews(specViews)):
                        _createdSpectrumView({Notifier.OBJECT: spectrumView})
                        # for peakList in spectrumView.spectrum.peakLists:
                        #     strip.showPeaks(peakList)

                else:
                    # spectra are grouped
                    specViews = strip.spectrumViews

                    for iSV, spectrumView in enumerate(spectrumDisplay.orderedSpectrumViews(specViews)):
                        _createdSpectrumView({Notifier.OBJECT: spectrumView})

                    spectrumDisplay.spectrumToolBar.hide()
                    spectrumDisplay.spectrumGroupToolBar.show()

                    _spectrumGroups = [project.getByPid(pid) for pid in spectrumDisplay._getSpectrumGroups()]

                    for group in _spectrumGroups:
                        spectrumDisplay.spectrumGroupToolBar._forceAddAction(group)

            # some of the strips may not be instantiated at this point
            # resize the stripFrame to the spectrumDisplay - ready for first resize event
            # spectrumDisplay.stripFrame.resize(spectrumDisplay.width() - 2, spectrumDisplay.stripFrame.height())
            spectrumDisplay.showAxes(stretchValue=True, widths=True,
                                     minimumWidth=GuiStrip.STRIPMINIMUMWIDTH)

        #~~~~~~~~~~~~~~~~
        #
        # # Initialise SpectrumDisplays, SpectrumViews
        # for spectrumDisplay in project.spectrumDisplays:
        #
        #   # self.moduleArea.addModule(spectrumDisplay, position='right')
        #   strips = spectrumDisplay.strips
        #   for strip in strips:
        #
        #     # move to the correct place in the widget
        #     stripIndex = strips.index(strip)
        #     spectrumDisplay.stripFrame.layout().addWidget(strip, 0, stripIndex)
        #
        #     specViews = strip.spectrumViews
        #     # for iSV, spectrumView in enumerate(spectrumDisplay.orderedSpectrumViews(specViews)):
        #     for iSV, spectrumView in enumerate(specViews):
        #
        #       # set up the Z widgets and add new toolbar button
        #       spectrumDisplay._createdSpectrumView({Notifier.OBJECT: spectrumView})  #iSV)
        #
        #       for peakList in spectrumView.spectrum.peakLists:
        #         strip.showPeaks(peakList)
        #
        #   # some of the strips may no be instantiated at this point
        #   spectrumDisplay.showAxes()
        #   spectrumDisplay.setColumnStretches(True)
        #
        #~~~~~~~~~~~~~~~~

        if self.current.strip is None:
            if len(self.project.strips) > 0:
                self.current.strip = self.project.strips[0]

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

        return self.getByPid(identifier)

    def getByPid(self, pid):
        "Convenience"
        obj = self.project.getByPid(pid)
        if obj:
            return obj
        else:
            modules = [module for module in self.ui.mainWindow.modules if module.pid == pid] if isinstance(self.ui, Gui) else None
            return modules[0] if modules else None

    def getByGid(self, gid):
        "Convenience"
        return self.ui.getByGid(gid)

    # def _startCommandBlock(self, command: str, quiet: bool = False, **objectParameters):
    #     """Start block for command echoing, set undo waypoint, and echo command to ui and logger
    #
    #     MUST be paired with _endCommandBlock call - use try ... finally to ensure both are called
    #
    #     Set keyword:value objectParameters to point to the relevant objects in setup commands,
    #     and pass setup commands and command proper to ui for echoing
    #
    #     Example calls:
    #
    #     _startCommandBlock("application.createSpectrumDisplay(spectrum)", spectrum=spectrumOrPid)
    #
    #     _startCommandBlock(
    #        "newAssignment = peak.assignDimension(axisCode=%s, value=[newNmrAtom]" % axisCode,
    #        peak=peakOrPid)"""
    #
    #     undo = self.project._undo
    #     if undo is not None:  # ejb - changed from if undo:
    #         # set undo step
    #         undo.newWaypoint()  # DO NOT CHANGE
    #
    #         # _blockedSideBar is a project override
    #         if not self.project._blockSideBar and not undo._blocked:
    #             if undo._waypointBlockingLevel < 1 and self.ui and self.ui.mainWindow:
    #                 self.ui.mainWindow.sideBar._saveExpandedState()
    #
    #         undo.increaseWaypointBlocking()
    #
    #     if not self._echoBlocking:
    #         self.project.suspendNotification()
    #
    #         # Get list of command strings
    #         commands = []
    #         for parameter, value in sorted(objectParameters.items()):
    #             if value is not None:
    #                 if not isinstance(value, str):
    #                     value = value.pid
    #                 commands.append("%s = project.getByPid(%s)\n" % (parameter, repr(value)))
    #         commands.append(command)  # ED: newLine NOT needed here
    #
    #         # echo command strings
    #         # added 'quiet' mode to keep full functionality to 'startCommandEchoBLock'
    #         # but without the screen output
    #         if not quiet:
    #             self.ui.echoCommands(commands)
    #
    #     self._increaseNotificationBlocking()
    #     getLogger().debug2('command=%s, echoBlocking=%s, undo.blocking=%s'
    #                        % (command, self._echoBlocking, undo.blocking))

    # #TODO:TJ: Why is this a private method; it is and should be used all over the code?
    # def _endCommandBlock(self):
    #     """End block for command echoing,
    #
    #     MUST be paired with _startCommandBlock call - use try ... finally to ensure both are called"""
    #
    #     getLogger().debug2('echoBlocking=%s' % self._echoBlocking)
    #     undo = self.project._undo
    #
    #     # if self._echoBlocking > 0:
    #     #     self._echoBlocking -= 1
    #     self._decreaseNotificationBlocking()
    #
    #     if not self._echoBlocking:
    #         self.project.resumeNotification()
    #
    #     if undo is not None:  # ejb - changed from if undo:
    #         undo.decreaseWaypointBlocking()
    #
    #         if not self.project._blockSideBar and not undo._blocked:
    #             if undo._waypointBlockingLevel < 1 and self.ui and self.ui.mainWindow:
    #                 self.ui.mainWindow.sideBar._restoreExpandedState()
    #
    #     # if self._echoBlocking > 0:
    #     #   # If statement should always be True, but to avoid weird behaviour in error situations we check
    #     #   self._echoBlocking -= 1
    #     # # self.project.resumeNotification()

    def addApplicationMenuSpec(self, spec, position=3):
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

        ms.append(('Project', [
            ("New", self.createNewProject, [('shortcut', '⌃n')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (),
            ("Open...", self.openProject, [('shortcut', '⌃o')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Open Recent", ()),

            #      ("Load Spectrum...", lambda: self.loadData(text='Load Spectrum'), [('shortcut', 'ls')]),
            ("Load Data...", self.loadData, [('shortcut', 'ld')]),
            (),
            ("Save", self.saveProject, [('shortcut', '⌃s')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Save As...", self.saveProjectAs, [('shortcut', 'sa')]),
            (),
            ("Import", (("Nef File", self._importNef, [('shortcut', 'in'), ('enabled', True)]),
                        ("NmrStar File", self._loadNMRStarFile, [('shortcut', 'bi')]),
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
            (),
            ("Undo", self.undo, [('shortcut', '⌃z')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Redo", self.redo, [('shortcut', '⌃y')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (),
            ("Summary", self.displayProjectSummary),
            ("Archive", self.archiveProject, [('enabled', False)]),
            ("Restore From Archive...", self.restoreFromArchive, [('enabled', False)]),
            (),
            ("Preferences...", self.showApplicationPreferences, [('shortcut', '⌃,')]),
            (),
            ("Quit", self._closeEvent, [('shortcut', '⌃q')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ]
                   ))

        ms.append(('Spectrum', [
            ("Load Spectra...", self.loadSpectra, [('shortcut', 'ls')]),
            (),
            ("Spectrum Groups...", self.showSpectrumGroupsPopup, [('shortcut', 'ss')]),
            ("Set Experiment Types...", self.showExperimentTypePopup, [('shortcut', 'et')]),
            ("Validate Paths...", self.showValidateSpectraPopup, [('shortcut', 'vp')]),
            (),
            ("Pick Peaks", (("Pick 1D Peaks...", self.showPeakPick1DPopup, [('shortcut', 'p1')]),
                            ("Pick ND Peaks...", self.showPeakPickNDPopup, [('shortcut', 'pp')])
                            )),
            ("Copy PeakList...", self.showCopyPeakListPopup, [('shortcut', 'cl')]),
            ("Copy Peaks...", self.showCopyPeaks, [('shortcut', 'cp')]),
            ("Estimate Volumes...", self.showEstimateVolumesPopup, [('shortcut', 'ev')]),
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
            ("Generate Chain...", self.showCreateChainPopup),
            ("Inspect...", self.inspectMolecule, [('enabled', False)]),
            (),
            ("Residue Information", self.showResidueInformation, [('shortcut', 'ri')]),
            (),
            ("Reference Chemical Shifts", self.showRefChemicalShifts, [('shortcut', 'rc')]),
            ]
                   ))

        ms.append(('View', [
            ("Chemical Shift Table", partial(self.showChemicalShiftTable, selectFirstItem=True), [('shortcut', 'ct')]),
            ("NmrResidue Table", partial(self.showNmrResidueTable, selectFirstItem=True), [('shortcut', 'nt')]),
            # ("Structure Table", partial(self.showStructureTable, selectFirstItem=True), [('shortcut', 'st')]),
            ("Residue Table", partial(self.showResidueTable, selectFirstItem=True)),
            ("Peak Table", partial(self.showPeakTable, selectFirstItem=True), [('shortcut', 'pt')]),
            ("Integral Table", partial(self.showIntegralTable, selectFirstItem=True), [('shortcut', 'it')]),
            ("Multiplet Table", partial(self.showMultipletTable, selectFirstItem=True), [('shortcut', 'mt')]),
            ("Restraint Table", partial(self.showRestraintTable, selectFirstItem=True), [('shortcut', 'rt')]),
            ("Structure Table", partial(self.showStructureTable, selectFirstItem=True), [('shortcut', 'st')]),
            (),
            ("Chemical Shift Mapping", self.showChemicalShiftMapping, [('shortcut', 'cm')]),
            ("Notes Editor", partial(self.showNotesEditor, selectFirstItem=True), [('shortcut', 'no'),
                                                                                   ('icon', 'icons/null')]),
            (),
            # (),
            ###("Sequence Graph", self.showSequenceGraph, [('shortcut', 'sg')]),
            ###("Atom Selector", self.showAtomSelector, [('shortcut', 'as')]),
            ###(),

            # sequenceModule has been incorporated into sequence graph
            # ("Show Sequence", self.toggleSequenceModule, [('shortcut', 'sq'),
            #                                               ('checkable', True),
            #                                               ('checked', False)
            #                                               ]),
            (),
            ("Current", (("Show/Hide Toolbar", self.toggleToolbar, [('shortcut', 'tb')]),
                         ("Show/Hide Spectrum Toolbar", self.toggleSpectrumToolbar, [('shortcut', 'sb')]),
                         ("Show/Hide Phasing Console", self.togglePhaseConsole, [('shortcut', 'pc')]),
                         (),
                         ("Set Zoom...", self._setZoomPopup, [('shortcut', 'sz')]),
                         ("Reset Zoom", self.resetZoom, [('shortcut', 'rz')]),
                         (),
                         ("New SpectrumDisplay with strip", self.copyStrip, []),
                         ("Copy with X-Y Axes flipped", self.flipXYAxis, [('shortcut', 'xy')]),
                         ("Copy with X-Z Axes flipped", self.flipXZAxis, [('shortcut', 'xz')]),
                         ("Copy with Y-Z Axes flipped", self.flipYZAxis, [('shortcut', 'yz')]),
                         ("Copy with Axes Flipped...", self.flipArbitraryAxis, [('shortcut', 'fa')]),
                         )),
            (),
            (SHOWMODULESMENU, ([
                ("None", None, [('checkable', True),
                                ('checked', False)])
                ])),
            ("Python Console", self._toggleConsole, [('shortcut', '  '),
                                                     ('checkable', True),
                                                     ('checked', False)])
            ]
                   ))

        ms.append(('Macro', [
            ("New", self.showMacroEditor),
            # ("New from Console", self.newMacroFromConsole, [('enabled', False)]),  #Not available yet
            # ("New from Log", None, [('enabled', False)]),  #Not available yet
            (),
            ("Open...", self.openMacroOnEditor),
            (),
            ("Run...", self.runMacro),
            ("Run Recent", ()),
            ("Open CCPN Macros...", self.openCcpnMacroOnEditor),
            (CCPNMACROSMENU, ([
                ("None", None, [('checkable', True),
                                ('checked', False)])
                ])),
            (),
            ("Define Macro Shortcuts...", self.defineUserShortcuts, [('shortcut', 'du')]),
            ("Submit Macro...", self.showSubmitMacroPopup)
            ]
                   ))

        ms.append(('Plugins', [
            # (PLUGINSMENU, ()),
            (CCPNPLUGINSMENU, ()),
            ]
                   ))

        ms.append(('Help', [
            (TUTORIALSMENU, ([

                ("None", None, [('checkable', True),
                                ('checked', False)])
                ])),

            # # Submenu
            # ("Beginners Tutorial", self.showBeginnersTutorial),
            # ("Backbone Tutorial", self.showBackboneTutorial),
            # ("CSP Tutorial", self.showCSPtutorial),
            # ("More...", self.showTutorials)
            # ])),

            ("Show Shortcuts", self.showShortcuts),
            ("Show CcpNmr V3 Documentation", self.showVersion3Documentation),
            (),
            ("About CcpNmr V3...", self.showAboutPopup),
            ("About CCPN...", self.showAboutCcpn),
            ("Show License...", self.showCcpnLicense),
            (),
            # ("Inspect Code...", self.showCodeInspectionPopup, [('shortcut', 'gv'),
            #                                                    ('enabled', False)]),
            # ("Show Issues...", self.showIssuesList),

            ("Check for Updates...", self.showUpdatePopup),
            ("Register...", self.showRegisterPopup),
            (),
            ("Submit Feedback...", self.showFeedbackPopup),
            # ("Submit Macro...", self.showSubmitMacroPopup)
            ]
                   ))

    ###################################################################################################################
    ## These will eventually move to gui (probably via a set of lambda functions.
    ###################################################################################################################
    ###################################################################################################################
    ## MENU callbacks:  Project
    ###################################################################################################################

    def _loadDataFromMenu(self, text=None):
        """Call loadData from the menu and trap errors.
        """
        try:

            self.loadData(text=text)

        except Exception as es:
            MessageDialog.showWarning(str(self.ui.mainWindow.windowTitle()), str(es))
            if self._isInDebugMode:
                raise es

    def createNewProject(self):
        "Callback for creating new project"
        with catchExceptions(application=self, errorStringTemplate='Error creating new project:'):
            okToContinue = self.ui.mainWindow._queryCloseProject(title='New Project',
                                                                 phrase='create a new')
            if okToContinue:
                project = self.newProject()
                if project is None:
                    raise RuntimeError('Unable to create new project')
                project._mainWindow.show()
                QtWidgets.QApplication.setActiveWindow(project._mainWindow)

    def newProject(self, name='default'):
        """Create new, empty project; return Project instance
        """

        # NB _closeProject includes a gui cleanup call

        if self.project is not None:
            self._closeProject()

        project = None
        sys.stderr.write('==> Creating new, empty project\n')
        newName = re.sub('[^0-9a-zA-Z]+', '', name)
        if newName != name:
            getLogger().info('Removing whitespace from name: %s' % name)

        project = coreIo.newProject(name=newName, useFileLogger=self.useFileLogger, level=self.level)
        project._isNew = True
        # Needs to know this for restoring the GuiSpectrum Module. Could be removed after decoupling Gui and Data!
        # GST note change of order required for undo dirty system not consistent
        # order in other place elsewhise
        project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)
        self._initialiseProject(project)

        # 20190424:ED reset the flag so that spectrumDisplays open correctly again
        project._isNew = None

        return project

    def openProject(self, path=None):
        project = self.ui.mainWindow.loadProject(projectDir=path)
        if project:
            try:
                project._mainWindow.show()
                QtWidgets.QApplication.setActiveWindow(project._mainWindow)

            except Exception as es:
                getLogger().warning('Error opening project:', str(es))
            finally:
                return project
        else:
            return None

    def loadProject(self, path=None):
        """
           Load project from path
           If not path then opens a file dialog box and loads project from selected file.

           ReturnsProject instance or None on error
        """
        if not path:
            dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.Directory, text='Load Project',
                                acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general)
            path = dialog.selectedFile()
            if not path:
                return None

        dataType, subType, usePath = ioFormats.analyseUrl(path)
        project = None

        if dataType == 'Project' and subType in (ioFormats.CCPN,
                                                 ioFormats.NEF,
                                                 # ioFormats.NMRSTAR,
                                                 ioFormats.SPARKY):

            # if subType != ioFormats.NEF:    # ejb - only reset project for CCPN files
            #   if self.project is not None:
            #     self._closeProject()

            if subType == ioFormats.CCPN:
                sys.stderr.write('==> Loading %s project "%s"\n' % (subType, path))

                if self.project is not None:  # always close for Ccpn
                    self._closeProject()
                project = coreIo.loadProject(path, useFileLogger=self.useFileLogger, level=self.level)
                project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)
                self._initialiseProject(project)
                project._undo.clear()
            elif subType == ioFormats.NEF:
                sys.stderr.write('==> Loading %s NEF project "%s"\n' % (subType, path))
                project = self._loadNefFile(path, makeNewProject=True)  # RHF - new by default
                project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

            # elif subType == ioFormats.NMRSTAR: This is all Broken!
            #     sys.stderr.write('==> Loading %s NMRStar project "%s"\n' % (subType, path))
            #     project = self._loadNMRStarFile(path, makeNewProject=True)  # RHF - new by default
            #     project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

            elif subType == ioFormats.SPARKY:
                sys.stderr.write('==> Loading %s Sparky project "%s"\n' % (subType, path))
                project = self._loadSparkyProject(path, makeNewProject=True)  # RHF - new by default
                project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

            project._validateDataUrlAndFilePaths()

            return project

        # elif dataType == 'NefFile' and subType in (ioFormats.NEF):
        # # ejb - testing - 24/6/17 hopefully this will insert into project
        # #                 is caught by the test above
        # #                 need to deciode whether it is a 'project' or 'NefFile' load
        #
        #   sys.stderr.write('==> Loading %s NefFile "%s"\n' % (subType, path))
        #   project = self._loadNefFile(path, makeNewProject=False)
        #   project._resetUndo(debug=_DEBUG)
        #
        #   return project

        else:
            sys.stderr.write('==> Could not recognise "%s" as a project; loading into default project\n' % path)
            self.project = self.newProject()
            self.loadData(paths=[path])
            return self.project

    def _loadNefFile(self, path: str, makeNewProject=True) -> Project:
        """Load Project from NEF file at path, and do necessary setup"""

        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking

        dataBlock = self.nefReader.getNefData(path)

        if makeNewProject:
            if self.project is not None:
                self._closeProject()
            self.project = self.newProject(dataBlock.name)

        self.project._wrappedData.shiftAveraging = False
        # with suspendSideBarNotifications(project=self.project):

        with undoBlock():
            with notificationEchoBlocking():
                with catchExceptions(application=self, errorStringTemplate='Error loading Nef file: %s'):
                    self.nefReader.importNewProject(self.project, dataBlock)
                # try:
                #     self.nefReader.importNewProject(self.project, dataBlock)
                # except Exception as es:
                #     getLogger().warning('Error loading Nef file: %s' % str(es))
                #     if self._isInDebugMode:
                #         raise es
                # # finally:

        self.project._wrappedData.shiftAveraging = True

        getLogger().info('==> Loaded NEF file: "%s"' % (path,))
        return self.project

    def _loadNMRStarFile(self, path=None):
        if not path:
            text = 'Import NMR-Star File into Project'
            dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text=text,
                                acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general)
            path = dialog.selectedFile()
            if not path:
                return
        from ccpn.ui.gui.popups.ImportStarPopup import StarImporterPopup

        relativePath = os.path.dirname(os.path.realpath(path))
        dataBlock = self.nefReader.getNMRStarData(path)
        self._importedStarDataBlock = dataBlock

        popup = StarImporterPopup(project=self.project, bmrbFilePath=path, directory=relativePath, dataBlock=dataBlock)
        popup.show()
        popup.raise_()

    #     # FIXME Below is broken. This does not create a project! Looks like a copy-paste from NEF code.
    # """Load Project from NEF file at path, and do necessary setup"""
    #
    # from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking
    #
    # dataBlock = self.nefReader.getNMRStarData(path)

    # if makeNewProject:
    #     if self.project is not None:
    #         self._closeProject()
    #     self.project = self.newProject(dataBlock.name)
    #
    # self.project._wrappedData.shiftAveraging = False
    #
    # # with suspendSideBarNotifications(project=self.project):
    # with undoBlock():
    #     with notificationEchoBlocking():
    #         # with catchExceptions(application=self, errorStringTemplate='Error loading NMRStar file: %s'):
    #             self.nefReader.importNewProject(self.project, dataBlock)

    # with undoBlock():
    #     try:
    #         self.nefReader.importNewNMRStarProject(self.project, dataBlock)
    #     except Exception as es:
    #         getLogger().warning('Error loading NMRStar file: %s' % str(es))

    # self.project._wrappedData.shiftAveraging = True

    # getLogger().info('==> Loaded NmrStar file: "%s"' % (path,))
    # return self.project

    def _loadSparkyProject(self, path: str, makeNewProject=True) -> Project:
        """Load Project from Sparky file at path, and do necessary setup"""

        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking

        # read data files
        from ccpn.core.lib.CcpnSparkyIo import SPARKY_NAME

        dataBlock = self.sparkyReader.parseSparkyFile(path)
        sparkyName = dataBlock.getDataValues(SPARKY_NAME, firstOnly=True)

        if makeNewProject and (dataBlock.getDataValues('sparky', firstOnly=True) == 'project file'):
            if self.project is not None:
                self._closeProject()
            self.project = self.newProject(sparkyName)

        self.project._wrappedData.shiftAveraging = True

        # with suspendSideBarNotifications(project=self.project):
        with undoBlock():
            with notificationEchoBlocking():
                with catchExceptions(application=self, errorStringTemplate='Error loading Sparky file: %s'):
                    self.sparkyReader.importSparkyProject(self.project, dataBlock)

        # with undoBlock():
        #     try:
        #         # insert file into project
        #
        #         self.sparkyReader.importSparkyProject(self.project, dataBlock)
        #         sys.stderr.write('==> Loaded Sparky project files: "%s", building project\n' % (path,))
        #     except Exception as es:
        #         getLogger().warning('Error loading Sparky file: %s' % str(es))
        #

        self.project._wrappedData.shiftAveraging = True

        getLogger().info('==> Loaded Sparky project files: "%s", building project' % (path,))
        return self.project

    def clearRecentProjects(self):
        self.preferences.recentFiles = []
        self.ui.mainWindow._fillRecentProjectsMenu()

    def clearRecentMacros(self):
        self.preferences.recentMacros = []
        self.ui.mainWindow._fillRecentMacrosMenu()

    def loadSpectra(self, paths=None, filter=None, askBeforeOpen_lenght=20):
        """
        :param paths: list of str of paths
        :param filter:
        :param askBeforeOpen_lenght: how many spectra can open without asking first

        """
        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking
        from tqdm import tqdm

        if paths is None:
            if self.preferences.general.useNative:
                m = 'Native dialog not available on multiple selections. ' \
                    'For loading a single file (not Dir) through a native dialog please use: Project > Load Data...'
                getLogger().info(m)
            dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.ExistingFiles, text='Load Spectra',
                                acceptMode=FileDialog.AcceptOpen, multiSelection=True,
                                filter=filter, useNative=False)
            paths = dialog._customMultiSelectedFiles

        spectraPaths = []
        for path in paths:
            path = str(path)
            subPaths = ioFormats._searchSpectraPathsInSubDir(path)  # Filter only spectra files
            if len(subPaths) > 0:
                spectraPaths += subPaths

        if len(spectraPaths) < len(paths):
            notRecognised = [i for i in paths if i not in spectraPaths if not os.path.isdir(i)]
            getLogger().warning('Not valid spectrum Path(s): ' + str(notRecognised))

        if len(spectraPaths) > askBeforeOpen_lenght:
            okToOpenAll = MessageDialog.showYesNo('Load data', 'The directory contains multiple items (~%s).'
                                                               ' Do you want to open all?' % str(len(spectraPaths)))
            if not okToOpenAll:
                return
        with undoBlock():
            with notificationEchoBlocking():
                for spectrumPath in tqdm(spectraPaths):
                    self.project.loadData(str(spectrumPath))

    def loadData(self, paths=None, text=None, filter=None):
        """
        Opens a file dialog box and loads data from selected file.
        """
        if text is None:
            text = 'Load Data'

        if paths is None:
            #TODO:LIST-AS-ISSUE: This fails for native file dialogs on OSX when trying to select a project (i.e. a directory)
            # NBNB TBD I assume here that path is either a string or a list lf string paths.
            # NBNB #FIXME if incorrect
            dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text=text,
                                acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                                filter=filter)
            path = dialog.selectedFile()
            if not path:
                return
            paths = [path]

        elif isinstance(paths, str):
            paths = [paths]

        for path in paths:
            self.project.loadData(path)

    def _cloneSpectraToProjectDir(self):
        ''' Keep a copy of spectra inside the project directory "myproject.ccpn/data/spectra".
        This is useful when saving the project in an external driver and want to keep the spectra together with the project.
        '''
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
            # NBNB TODO Gui should pre-check newPath and/or pop up something in case of failure

        else:
            successMessage = '==> Project successfully saved\n'
            self.ui.mainWindow._updateWindowTitle()
            self.ui.mainWindow.statusBar().showMessage(successMessage)
            self.ui.mainWindow.getMenuAction('Project->Archive').setEnabled(True)
            self.ui.mainWindow._fillRecentProjectsMenu()
            # self._createApplicationPaths()
            self.current._dumpStateToFile(self.statePath)
            try:
                if self.preferences.general.autoSaveLayoutOnQuit:
                    Layout.saveLayoutToJson(self.ui.mainWindow)
            except Exception as e:
                getLogger().warning('Impossible to save Layout %s' % e)

            # saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')
            sys.stderr.write(successMessage)
            # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
            #                            iconPath=saveIconPath)

        self._getUndo().markSave()
        return successful

    def _importNef(self):
        #TODO:ED add import routine here, dangerous so add warnings

        ok = MessageDialog.showOkCancelWarning('WARNING',
                                               'Importing Nef file will merge the Nef file with'
                                               ' the current project. This can cause conflicts with'
                                               ' existing objects. USE WITH CAUTION')

        if ok:
            text = 'Import Nef File into Project'
            filter = '*.nef'
            dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text=text,
                                acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                                filter=filter)
            path = dialog.selectedFile()
            if not path:
                return

            with catchExceptions(application=self, errorStringTemplate='Error Importing Nef File: %s'):
                self._loadNefFile(path=path, makeNewProject=False)

            # try:
            #     for path in paths:
            #         self._loadNefFile(path=path, makeNewProject=False)
            # except Exception as es:
            #     getLogger().warning('Error Importing Nef File: %s' % str(es))
            #     if self._isInDebugMode:
            #         raise es

    def _exportNEF(self):
        """
        Export the current project as a Nef file
        Temporary routine because I don't know how else to do it yet
        """
        from ccpn.ui.gui.popups.ExportNefPopup import ExportNefPopup

        dialog = ExportNefPopup(self.ui.mainWindow,
                                mainWindow=self.ui.mainWindow,
                                fileMode=FileDialog.AnyFile,
                                text="Export to Nef File",
                                acceptMode=FileDialog.AcceptSave,
                                preferences=self.preferences.general,
                                selectFile=self.project.name + '.nef',  # new flag to populate dialog,
                                filter='*.nef')

        # an exclusion list comes out of the dialog as it
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

    def saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
        """Save project to newPath and return True if successful"""
        # TODO: convert this to a save and call self.project.save()
        if hasattr(self.project._wrappedData.root, '_temporaryDirectory'):
            return self.saveProjectAs()
        else:
            return self._saveProject(newPath=newPath, createFallback=createFallback,
                                     overwriteExisting=overwriteExisting)

    # GWV: This routine should not be used as it calls the graphics mainWindow routine
    # Instead: The graphics part now calls _getRecentFiles
    #
    # def _updateRecentFiles(self, oldPath=None):
    #   project = self.project
    #   path = project.path
    #   recentFiles = self.preferences.recentFiles
    #   mainWindow = self.ui.mainWindow or self._mainWindow
    #
    #   if not hasattr(project._wrappedData.root, '_temporaryDirectory'):
    #     if path in recentFiles:
    #       recentFiles.remove(path)
    #     elif oldPath in recentFiles:
    #       recentFiles.remove(oldPath)
    #     elif len(recentFiles) >= 10:
    #       recentFiles.pop()
    #     recentFiles.insert(0, path)
    #   recentFiles = uniquify(recentFiles)
    #   mainWindow._fillRecentProjectsMenu()
    #   self.preferences.recentFiles = recentFiles

    def _getRecentFiles(self, oldPath=None) -> list:
        """Get and return a list of recent files, setting reference to
           self as first element, unless it is a temp project
           update the preferences with the new list

           CCPN INTERNAL: called by MainWindow
        """
        project = self.project
        path = project.path
        recentFiles = self.preferences.recentFiles

        #TODO:RASMUS: replace by new function on project: isTemporary()
        if not hasattr(project._wrappedData.root, '_temporaryDirectory'):
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
        newPath = getSaveDirectory(self.ui.mainWindow, self.preferences.general)

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

        # NBNB TODO Consider appropriate failure handling. Is this OK?

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

    # def undo(self):
    #     if self.project._undo.canUndo():
    #         with MessageDialog.progressManager(self.ui.mainWindow, 'performing Undo'):
    #
    #             self.ui.echoCommands(['application.undo()'])
    #             self._echoBlocking += 1
    #
    #             self.ui.mainWindow.sideBar._saveExpandedState()
    #             self.project._undo.undo()
    #             self.ui.mainWindow.sideBar._restoreExpandedState()
    #
    #             # TODO:ED this is a hack until guiNotifiers are working
    #             try:
    #                 self.ui.mainWindow.moduleArea.repopulateModules()
    #             except:
    #                 getLogger().info('application has no Gui')
    #
    #             self._echoBlocking -= 1
    #     else:
    #         getLogger().warning('nothing to undo')
    #
    # def redo(self):
    #     if self.project._undo.canRedo():
    #         with MessageDialog.progressManager(self.ui.mainWindow, 'performing Redo'):
    #             self.ui.echoCommands(['application.redo()'])
    #             self._echoBlocking += 1
    #
    #             self.ui.mainWindow.sideBar._saveExpandedState()
    #             self.project._undo.redo()
    #             self.ui.mainWindow.sideBar._restoreExpandedState()
    #
    #             # TODO:ED this is a hack until guiNotifiers are working
    #             try:
    #                 self.ui.mainWindow.moduleArea.repopulateModules()
    #             except:
    #                 getLogger().info('application has no Gui')
    #
    #             self._echoBlocking -= 1
    #     else:
    #         getLogger().warning('nothing to redo.')

    def _getUndo(self):
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

        if not archivePath:
            archivesDirectory = os.path.join(self.project.path, Path.CCPN_ARCHIVES_DIRECTORY)
            dialog = FileDialog(self.ui.mainWindow, fileMode=FileDialog.ExistingFile, text="Select Archive",
                                acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                                directory=archivesDirectory, filter='*.tgz')
            archivePath = dialog.selectedFile()

        if archivePath:
            directoryPrefix = archivePath[:-4]  # -4 removes the .tgz
            outputPath, temporaryDirectory = self._unpackCcpnTarfile(archivePath, outputPath=directoryPrefix)
            pythonExe = os.path.join(Path.getTopDirectory(), Path.CCPN_PYTHON)
            command = [pythonExe, sys.argv[0], outputPath]
            from subprocess import Popen

            Popen(command)

    def _unpackCcpnTarfile(self, tarfilePath, outputPath=None, directoryPrefix='CcpnProject_'):
        """
        # CCPN INTERNAL - called in loadData method of Project
        """

        if outputPath:
            if not os.path.exists(outputPath):
                os.makedirs(outputPath)
            temporaryDirectory = None
        else:
            temporaryDirectory = tempfile.TemporaryDirectory(prefix=directoryPrefix)
            outputPath = temporaryDirectory.name

        cwd = os.getcwd()
        try:
            os.chdir(outputPath)
            tp = tarfile.open(tarfilePath)
            tp.extractall()

            # look for a directory inside and assume the first found is the project directory (there should be exactly one)
            relfiles = os.listdir('.')
            for relfile in relfiles:
                fullfile = os.path.join(outputPath, relfile)
                if os.path.isdir(fullfile):
                    outputPath = fullfile
                    break
            else:
                raise IOError('Could not find project directory in tarfile')

        finally:
            os.chdir(cwd)

        return outputPath, temporaryDirectory

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
        dialog = FileDialog(fileMode=FileDialog.AnyFile, text='Open Saved Layout',
                            acceptMode=FileDialog.AcceptOpen, filter=fType)
        path = dialog.selectedFile()
        if not path:
            return
        if path:
            return path

    def getSaveLayoutPath(self):
        """Opens save Layout as dialog box and gets directory specified in the file dialog."""
        jsonType = '.json'
        fType = 'JSON (*.json)'
        dialog = FileDialog(fileMode=FileDialog.AnyFile, text='Save Layout As',
                            acceptMode=FileDialog.AcceptSave, filter=fType)
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

        # prefPath = os.path.expanduser("~/.ccpn/v3settings.json")
        # directory = os.path.dirname(prefPath)
        # if not os.path.exists(directory):
        #     try:
        #         os.makedirs(directory)
        #     except Exception as e:
        #         getLogger().warning('Preferences not saved: %s' % (directory, e))
        #         return
        #
        # prefFile = open(prefPath, 'w+')
        # json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
        # prefFile.close()
        #
        # reply = MessageDialog.showMulti("Quit Program", "Do you want to save changes before quitting?",
        #                                 ['Save and Quit', 'Quit without Saving', 'Cancel'])  # ejb
        # if reply == 'Save and Quit':
        #     if event:
        #         event.accept()
        #     prefFile = open(prefPath, 'w+')
        #     json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
        #     prefFile.close()
        #
        #     success = self.saveProject()
        #     if success is True:
        #         # Close and clean up project
        #         self._closeProject()
        #         QtWidgets.QApplication.quit()
        #         os._exit(0)
        #
        #     else:
        #         if event:  # ejb - don't close the project
        #             event.ignore()
        #
        # elif reply == 'Quit without Saving':
        #     if event:
        #         event.accept()
        #     prefFile = open(prefPath, 'w+')
        #     json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
        #     prefFile.close()
        #     self._closeProject()
        #
        #     QtWidgets.QApplication.quit()
        #     os._exit(0)
        #
        # else:
        #     if event:
        #         event.ignore()

    def _closeMainWindows(self):
        tempModules = self.ui.mainWindow.application.ccpnModules
        if len(tempModules) > 0:
            for tempModule in tempModules:
                getLogger().debug('closing module: %s' % tempModule)
                try:
                    tempModule.close()
                except:
                    # wrapped C/C++ object of type StripDisplay1d has been deleted
                    pass

    def _closeExtraWindows(self):
        tempAreas = self.ui.mainWindow.moduleArea.tempAreas
        if len(tempAreas) > 0:
            for tempArea in tempAreas:
                getLogger().debug('closing external module: %s' % tempArea.window())
                try:
                    tempArea.window().close()
                except:
                    # wrapped C/C++ object of type StripDisplay1d has been deleted
                    pass

    def _closeProject(self):
        """Close project and clean up - when opening another or quitting application"""

        # NB: this function must clean up both wrapper and ui/gui

        self.deleteAllNotifiers()
        if self.ui.mainWindow:
            # ui/gui cleanup
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
            self.project = None

        # self.ui.mainWindow = None
        # self.project = None

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

                if self.current.strip:
                    popup = PeakFindPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
                    popup.exec_()
                else:
                    getLogger().warning('Pick Nd Peaks, no strip selected')
                    MessageDialog.showWarning('Pick Nd Peaks', 'No strip selected')
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

    def showCreateChainPopup(self):
        """
        Displays sequence creation popup.
        """
        from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup

        self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showCreateChainPopup()")
        getLogger().info("application.showCreateChainPopup()")
        popup = CreateChainPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()

    def toggleSequenceModule(self):
        """Toggles whether Sequence Module is displayed or not"""
        from ccpn.ui.gui.modules.SequenceModule import SequenceModule

        # openList = [m for m in SequenceModule.getInstances()]
        # if openList:
        #   openList[0].close()
        #   # SequenceModule._alreadyOpened = False
        # # if SequenceModule._alreadyOpened is True:
        # #   if SequenceModule._currentModule is not None:
        # #     SequenceModule._currentModule.close()
        # #     SequenceModule._alreadyOpened = False
        # else:
        self.showSequenceModule()

        # if hasattr(self, 'sequenceModule'):
        #   if self.sequenceModule.isVisible():
        #     self.hideSequenceModule()
        # else:
        #   self.showSequenceModule()
        self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.toggleSequenceModule()")
        getLogger().info("application.toggleSequenceModule()")

    def showSequenceModule(self, position='top', relativeTo=None):
        """
        Displays Sequence Module at the top of the screen.
        """
        from ccpn.ui.gui.modules.SequenceModule import SequenceModule

        # if not hasattr(self, 'sequenceModule'):

        if SequenceModule._alreadyOpened is False:
            mainWindow = self.ui.mainWindow
            self.sequenceModule = SequenceModule(mainWindow=mainWindow)
            mainWindow.moduleArea.addModule(self.sequenceModule,
                                            position=position, relativeTo=relativeTo)
            action = self._findMenuAction('View', 'Show Sequence')
            if action:  # should be True
                action.setChecked(True)

            # set the colours of the currently highlighted chain in open sequenceGraph
            # should really be in the class, but doesn't fire correctly during __init__
            self.sequenceModule.populateFromSequenceGraphs()

        return self.sequenceModule

    def hideSequenceModule(self):
        """Hides sequence module"""

        if hasattr(self, 'sequenceModule'):
            self.sequenceModule.close()
            delattr(self, 'sequenceModule')

    def inspectMolecule(self):
        pass

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
        self.residueModule = ResidueInformation(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(self.residueModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showResidueInformation()")
        getLogger().info("application.showResidueInformation()")

    def showRefChemicalShifts(self, position='left', relativeTo=None):
        """Displays Reference Chemical Shifts module."""
        from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.refChemShifts = ReferenceChemicalShifts(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(self.refChemShifts, position=position, relativeTo=relativeTo)

    ###################################################################################################################
    ## MENU callbacks:  VIEW
    ###################################################################################################################

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
        self.chemicalShiftTableModule = ChemicalShiftTableModule(mainWindow=mainWindow,
                                                                 chemicalShiftList=chemicalShiftList, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.chemicalShiftTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")
        getLogger().info("application.showChemicalShiftTable()")
        return self.chemicalShiftTableModule

    def showNmrResidueTable(self, position='bottom', relativeTo=None,
                            nmrChain=None, selectFirstItem=False):
        """Displays Nmr Residue Table
        """
        from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.nmrResidueTableModule = NmrResidueTableModule(mainWindow=mainWindow,
                                                           nmrChain=nmrChain, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.nmrResidueTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")
        getLogger().info("application.showNmrResidueTable()")
        return self.nmrResidueTableModule

    def showResidueTable(self, position='bottom', relativeTo=None,
                         chain=None, selectFirstItem=False):
        """Displays  Residue Table
        """
        from ccpn.ui.gui.modules.ResidueTable import ResidueTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.residueTableModule = ResidueTableModule(mainWindow=mainWindow,
                                                     chain=chain, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.residueTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showResidueTable()")
        getLogger().info("application.showResidueTable()")
        return self.residueTableModule

    # def showStructureTable(self, position='bottom', relativeTo=None,
    #                         structureEnsemble=None, selectFirstItem=False):
    #   """Displays Structure Table
    #   """
    #   from ccpn.ui.gui.modules.StructureTable import StructureTableModule
    #
    #   mainWindow = self.ui.mainWindow
    #   if not relativeTo:
    #     relativeTo = mainWindow.moduleArea
    #   self.structureTableModule = StructureTableModule(mainWindow=mainWindow,
    #                                               structureEnsemble=structureEnsemble, selectFirstItem=selectFirstItem)
    #   mainWindow.moduleArea.addModule(self.structureTableModule, position=position, relativeTo=relativeTo)
    #
    #   mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()")
    #   logger.info("application.showStructureTable()")
    #   return self.structureTableModule
    #
    def showPeakTable(self, position: str = 'left', relativeTo: CcpnModule = None,
                      peakList: PeakList = None, selectFirstItem=False):
        """Displays Peak table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.PeakTable import PeakTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.peakTableModule = PeakTableModule(mainWindow,
                                               peakList=peakList, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.peakTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showPeakTable()")
        getLogger().info("application.showPeakTable()")
        return self.peakTableModule

    def showMultipletTable(self, position: str = 'left', relativeTo: CcpnModule = None,
                           multipletList: MultipletList = None, selectFirstItem=False):
        """Displays multipletList table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.MultipletListTable import MultipletTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.multipletTableModule = MultipletTableModule(mainWindow,
                                                         multipletList=multipletList, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.multipletTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showMultipletTable()")
        getLogger().info("application.showMultipletTable()")
        return self.multipletTableModule

    def showIntegralTable(self, position: str = 'left', relativeTo: CcpnModule = None,
                          integralList: IntegralList = None, selectFirstItem=False):
        """Displays integral table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.IntegralTable import IntegralTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.integralTableModule = IntegralTableModule(mainWindow=mainWindow,
                                                       integralList=integralList, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.integralTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showIntegralTable()")
        getLogger().info("application.showIntegralTable()")
        return self.integralTableModule

    def showRestraintTable(self, position: str = 'bottom', relativeTo: CcpnModule = None,
                           restraintList: PeakList = None, selectFirstItem=False):
        """Displays Peak table on left of main window with specified list selected.
        """
        from ccpn.ui.gui.modules.RestraintTable import RestraintTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.restraintTableModule = RestraintTableModule(mainWindow=mainWindow,
                                                         restraintList=restraintList, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.restraintTableModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showRestraintTable()")
        getLogger().info("application.showRestraintTable()")
        return self.restraintTableModule

    def showStructureTable(self, position='bottom', relativeTo=None,
                           structureEnsemble=None, selectFirstItem=False):
        """Displays Structure Table
        """
        from ccpn.ui.gui.modules.StructureTable import StructureTableModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.structureTableModule = StructureTableModule(mainWindow=mainWindow,
                                                         structureEnsemble=structureEnsemble, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.structureTableModule, position=position, relativeTo=relativeTo)

        mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()")
        getLogger().info("application.showStructureTable()")
        return self.structureTableModule

    def showNotesEditor(self, position: str = 'bottom', relativeTo: CcpnModule = None,
                        note=None, selectFirstItem=False):
        """Displays Notes Editing Table
        """
        from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        self.notesEditorModule = NotesEditorModule(mainWindow=mainWindow,
                                                   note=note, selectFirstItem=selectFirstItem)

        mainWindow.moduleArea.addModule(self.notesEditorModule, position=position, relativeTo=relativeTo)
        mainWindow.pythonConsole.writeConsoleCommand("application.showNotesEditorTable()")
        getLogger().info("application.showNotesEditorTable()")
        return self.notesEditorModule

    def showPrintSpectrumDisplayPopup(self):
        # from ccpn.ui.gui.popups.PrintSpectrumPopup import SelectSpectrumDisplayPopup #,PrintSpectrumDisplayPopup

        from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup

        if len(self.project.spectrumDisplays) == 0:
            MessageDialog.showWarning('', 'No SpectrumDisplay found')
        else:
            exportDialog = ExportStripToFilePopup(parent=self.ui.mainWindow,
                                                  mainWindow=self.ui.mainWindow,
                                                  strips=self.project.strips,
                                                  preferences=self.ui.mainWindow.application.preferences.general)
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

    def flipArbitraryAxis(self):
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

    def flipXYAxis(self):
        if self.current.strip is not None:
            self.current.strip.flipXYAxis()
        else:
            getLogger().warning('No strip selected')

    def flipXZAxis(self):
        if self.current.strip is not None:
            self.current.strip.flipXZAxis()
        else:
            getLogger().warning('No strip selected')

    def flipYZAxis(self):
        if self.current.strip is not None:
            self.current.strip.flipYZAxis()
        else:
            getLogger().warning('No strip selected')

    def _findMenuAction(self, menubarText, menuText):
        # not sure if this function will be needed more widely or just in console context
        # CCPN internal: now also used in SequenceModule._closeModule

        #GWV should not be here; moved to GuiMainWindow
        self.ui.mainWindow._findMenuAction(menubarText, menuText)

        #
        # for menuBarAction in self.ui.mainWindow._menuBar.actions():
        #   if menuBarAction.text() == menubarText:
        #     break
        # else:
        #   return None
        #
        # for menuAction in menuBarAction.menu().actions():
        #   if menuAction.text() == menuText:
        #     return menuAction
        #
        # return None

    def _toggleConsole(self):
        """
        Toggles whether python console is displayed at bottom of the main window.
        """

        self.ui.mainWindow.toggleConsole()

    def showChemicalShiftMapping(self, position: str = 'top', relativeTo: CcpnModule = None):
        from ccpn.ui.gui.modules.ChemicalShiftsMappingModule import ChemicalShiftsMapping

        mainWindow = self.ui.mainWindow
        if not relativeTo:
            relativeTo = mainWindow.moduleArea
        cs = ChemicalShiftsMapping(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(cs, position=position, relativeTo=relativeTo)

    #################################################################################################
    ## MENU callbacks:  Macro
    #################################################################################################

    def showMacroEditor(self):
        """
        Displays macro editor.
        """
        mainWindow = self.ui.mainWindow
        self.editor = MacroEditor(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
        # mainWindow.pythonConsole.writeConsoleCommand("application.showMacroEditor()")
        # getLogger().info("application.showMacroEditor()")

    def openMacroOnEditor(self):
        """
        Displays macro editor.
        """
        mainWindow = self.ui.mainWindow
        self.editor = MacroEditor(mainWindow=mainWindow)
        mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
        self.editor._openMacroFile()
        # mainWindow.pythonConsole.writeConsoleCommand("application.showMacroEditor()")
        # getLogger().info("application.showMacroEditor()")

    def openCcpnMacroOnEditor(self):
        """
        Displays macro editor.
        """
        mainWindow = self.ui.mainWindow
        self.editor = MacroEditor(mainWindow=mainWindow, useCcpnMacros=True)
        mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
        self.editor._openMacroFile()
        # mainWindow.pythonConsole.writeConsoleCommand("application.showMacroEditor()")
        # getLogger().info("application.showMacroEditor()")

    def newMacroFromConsole(self):
        """
        Displays macro editor with contents of python console inside.
        """
        # editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
        #FIXME:ED - haven't checked this properly
        mainWindow = self.ui.mainWindow
        self.editor = MacroEditor(mainWindow=mainWindow)
        self.editor.textBox.set(mainWindow.pythonConsole.textEditor.toPlainText())
        mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)

    # FIXME:ED - haven't checked this properly. Broken
    def newMacroFromLog(self):
        """
        Displays macro editor with contents of the log.
        """
        # editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
        #FIXME:ED - haven't checked this properly
        mainWindow = self.ui.mainWindow
        self.editor = MacroEditor(mainWindow=mainWindow)
        with open(getLogger().logPath, 'r') as fp:
            l = fp.readlines()
        text = ''.join([line.strip().split(':', 6)[-1] + '\n' for line in l])
        self.editor.textBox.setText(text)
        mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)

    def defineUserShortcuts(self):

        from ccpn.ui.gui.popups.ShortcutsPopup import ShortcutsPopup

        ShortcutsPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()

    def runMacro(self, macroFile: str = None):
        """
        Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
        runs the selected macro.
        """
        if macroFile is None:
            dialog = FileDialog(self.ui.mainWindow, fileMode=FileDialog.ExistingFile, text="Run Macro",
                                acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                                directory=self.preferences.general.userMacroPath, filter='*.py')
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
        else:
            subprocess.run(['open', path], check=True)

    def _showHtmlFile(self, title, path):
        "Displays html files in program QT viewer or using native webbrowser depending on useNativeWebbrowser option"

        mainWindow = self.ui.mainWindow

        if self.preferences.general.useNativeWebbrowser:
            self._systemOpen(path)
        else:
            from ccpn.ui.gui.widgets.CcpnWebView import CcpnWebView

            self.newModule = CcpnWebView(mainWindow=mainWindow, name=title, urlPath=path)

            # self.newModule = CcpnModule(mainWindow=mainWindow, name=title)
            # view = CcpnWebView(path)
            # self.newModule.addWidget(view, 0, 0, 1, 1)      # make it the first item
            # self.newModule.mainWidget = view      # ejb

            self.ui.mainWindow.moduleArea.addModule(self.newModule, position='top', relativeTo=mainWindow.moduleArea)

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

    def showShortcuts(self):
        from ccpn.framework.PathsAndUrls import shortcutsPath

        self._systemOpen(shortcutsPath)

    def showAboutPopup(self):
        from ccpn.ui.gui.popups.AboutPopup import AboutPopup

        popup = AboutPopup(parent=self.ui.mainWindow)
        popup.exec_()

    def showAboutCcpn(self):
        from ccpn.framework.PathsAndUrls import ccpnUrl
        import webbrowser

        webbrowser.open(ccpnUrl)

    def showCcpnLicense(self):
        from ccpn.framework.PathsAndUrls import ccpnLicenceUrl
        import webbrowser

        webbrowser.open(ccpnLicenceUrl)

    def showCodeInspectionPopup(self):
        # TODO: open a file browser to top of source directory
        pass

    def showIssuesList(self):
        from ccpn.framework.PathsAndUrls import ccpnIssuesUrl
        import webbrowser

        webbrowser.open(ccpnIssuesUrl)

    def showTutorials(self):
        from ccpn.framework.PathsAndUrls import ccpnTutorials
        import webbrowser

        webbrowser.open(ccpnTutorials)

    def showUpdatePopup(self):
        """Open the update popup
        """
        from ccpn.framework.update.UpdatePopup import UpdatePopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            if not self.updatePopup:
                self.updatePopup = UpdatePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            self.updatePopup.show()
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

        self._systemOpen(licensePath)

    #########################################    End Menu callbacks   ##################################################

    # def printToFile(self, spectrumDisplay=None):
    #
    #   current = self.current
    #   # if not spectrumDisplay:
    #   #   spectrumDisplay = current.spectrumDisplay
    #   if not spectrumDisplay and current.strip:
    #     spectrumDisplay = current.strip.spectrumDisplay
    #   if not spectrumDisplay and self.spectrumDisplays:
    #     spectrumDisplay = self.spectrumDisplays[0]
    #   if spectrumDisplay:
    #     dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text='Print to File',
    #                         acceptMode=FileDialog.AcceptSave, preferences=self.preferences.general, filter='SVG (*.svg)')
    #     path = dialog.selectedFile()
    #     if not path:
    #       return
    #     spectrumDisplay.printToFile(path)

    def _initialiseFonts(self):

        from ccpn.ui.gui.guiSettings import fontSettings
        self._fontSettings = fontSettings(self.preferences)


def isValidPath(projectName, stripFullPath=True, stripExtension=True):
    """Check whether the project name is valid after stripping fullpath and extension
    Can only contain alphanumeric characters and underscores

    :param projectName: name of project to check
    :param stripFullPath: set to true to remove leading directory
    :param stripExtension: set to true to remove extension
    :return: True if valid else False
    """
    if not projectName:
        return

    if isinstance(projectName, str):

        name = os.path.basename(projectName) if stripFullPath else projectName
        name = os.path.splitext(name)[0] if stripExtension else name

        STRIPCHARS = '_'
        for ss in STRIPCHARS:
            name = name.replace(ss, '')

        if name.isalnum():
            return True


def getSaveDirectory(parent, preferences=None):
    """Opens save Project as dialog box and gets directory specified in the file dialog."""

    dialog = FileDialog(parent=parent, fileMode=FileDialog.AnyFile, text='Save Project As',
                        acceptMode=FileDialog.AcceptSave, preferences=preferences,
                        restrictDirToFilter=False)
    newPath = dialog.selectedFile()

    # if not iterable then ignore - dialog may return string or tuple(<path>, <fileOptions>)
    if isinstance(newPath, tuple) and len(newPath) > 0:
        newPath = newPath[0]

    # ignore if empty
    if not newPath:
        return

    # check validity of the newPath
    if not isValidPath(newPath, stripFullPath=True, stripExtension=True):
        getLogger().warning('Filename can only contain alphanumeric characters and underscores')
        MessageDialog.showWarning('Save Project', 'Filename can only contain alphanumeric characters and underscores')
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
