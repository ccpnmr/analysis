"""
This Module implements the main graphics window functionality
It works in concert with a wrapper object for storing/retrieving attibute values

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__dateModified__ = "$dateModified: 2021-07-20 21:57:02 +0100 (Tue, July 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-04 09:51:15 +0100 (Tue, April 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import os
import sys
from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QSize
from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import catchExceptions
from ccpn.ui.gui.widgets.MessageDialog import progressManager
from ccpn.util.Logging import getLogger
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

from ccpn.util.Svg import Svg
from ccpn.ui.gui.lib.mouseEvents import SELECT, setCurrentMouseMode, getCurrentMouseMode
from ccpn.ui.gui.lib import GuiSpectrumDisplay
from ccpn.ui.gui.lib import GuiSpectrumView
from ccpn.ui.gui.lib import GuiStrip
from ccpn.ui.gui.lib import GuiPeakListView
from ccpn.ui.gui.lib.GuiWindow import GuiWindow

from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.FileDialog import ProjectFileDialog
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.ui.gui.widgets.Menu import Menu, MenuBar, SHOWMODULESMENU, CCPNMACROSMENU, \
    USERMACROSMENU, TUTORIALSMENU, PLUGINSMENU, CCPNPLUGINSMENU, HOWTOSMENU
from ccpn.ui.gui.widgets.SideBar import SideBar  #,SideBar
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Font import setWidgetFont, getWidgetFontHeight
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showMulti

from ccpn.util.Common import uniquify, camelCaseToString
from ccpn.util import Logging
#from ccpn.util.Logging import getLogger
from ccpn.util import Path
from ccpn.util.Path import aPath
from ccpn.util.Common import isIterable
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking

from ccpn.framework.lib.DataLoaders.DataLoaderABC import checkPathForDataLoader

from ccpn.core.lib.Notifiers import NotifierBase, Notifier
from ccpn.core.Peak import Peak
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication


#from collections import OrderedDict

from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.MenuActions import _openItemObject


# For readability there should be a class:
# _MainWindowShortCuts which (Only!) has the shortcut definitions and the callbacks to initiate them.
# The latter should all be private methods!
# For readability there should be a class:
# _MainWindowMenus which (Only!) has menu instantiations, the callbacks to initiate them, + relevant methods
# The latter should all be private methods!
#
# The docstring of GuiMainWindow should detail how this setup is

MAXITEMLOGGING = 4


class GuiMainWindow(GuiWindow, QtWidgets.QMainWindow):
    # inherits NotifierBase

    def __init__(self, application=None):

        # super(GuiMainWindow, self).__init__(parent=None)
        GuiWindow.__init__(self, application)
        QtWidgets.QMainWindow.__init__(self)

        # format = QtGui.QSurfaceFormat()
        # format.setSwapInterval(0)
        # QtGui.QSurfaceFormat.setDefaultFormat(format)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        # Layout
        layout = self.layout()

        logger = Logging.getLogger()
        logger.debug('GuiMainWindow: layout: %s' % layout)

        if layout is not None:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        self.setGeometry(200, 40, 1100, 900)

        # connect a close event, cleaning up things as needed
        self.closeEvent = self._closeEvent
        # self.connect(self, QtCore.PYQT_SIGNAL('triggered()'), self._closeEvent)
        # self.triggered.connect(self._closeEvent)    # ejb

        # GuiWindow.__init__(self, application)
        self.application = application

        # Module area
        self.moduleArea = CcpnModuleArea(mainWindow=self)
        self._hiddenModules = CcpnModuleArea(mainWindow=self)
        self._hiddenModules.setVisible(False)

        logger.debug('GuiMainWindow.moduleArea: layout: %s' % self.moduleArea.layout)  ## pyqtgraph object
        self.moduleArea.setGeometry(0, 0, 1000, 800)
        # GST can't seem to do this with style sheets...
        self.moduleArea.setContentsMargins(0, 2, 2, 0)
        self.setCentralWidget(self.moduleArea)
        self._shortcutsDict = {}

        self._setupWindow()
        self._setupMenus()
        self._initProject()
        self._setShortcuts()
        self._setUserShortcuts(preferences=self.application.preferences, mainWindow=self)
        # Notifiers
        self._setupNotifiers()

        self.feedbackPopup = None
        self.updatePopup = None

        self.fileIcon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon, None, self)
        self.disabledFileIcon = self.makeDisabledFileIcon(self.fileIcon)

        # blank display opened later by the _initLayout if there is nothing to show otherwise
        self.pythonConsoleModule = None
        self.statusBar().showMessage('Ready')
        setCurrentMouseMode(SELECT)
        self.show()

        self._project._undo.undoChanged.add(self._undoChangeCallback)

        # install handler to resize when moving between displays
        self.window().windowHandle().screenChanged.connect(self._screenChangedEvent)

    @property
    def project(self):
        """The current project"""
        return self._project

    def makeDisabledFileIcon(self, icon):
        return icon

    def _undoChangeCallback(self, message):

        amDirty = self._project._undo.isDirty()
        self.setWindowModified(amDirty)

        if not self.project.isTemporary:
            self.setWindowFilePath(self.application.project.path)
        else:
            self.setWindowFilePath("")

        if self.project.isTemporary:
            self.setWindowIcon(QtGui.QIcon())
        elif amDirty:
            self.setWindowIcon(self.disabledFileIcon)
        else:
            self.setWindowIcon(self.fileIcon)

    @pyqtSlot()
    def _screenChangedEvent(self, *args):
        self._screenChanged(*args)
        self.update()

    def _screenChanged(self, *args):
        getLogger().debug2('mainWindow screenchanged')
        project = self.application.project
        for spectrumDisplay in project.spectrumDisplays:
            for strip in spectrumDisplay.strips:
                strip.refreshDevicePixelRatio()

            # NOTE:ED - set pixelratio for extra axes
            if hasattr(spectrumDisplay, '_rightGLAxis'):
                spectrumDisplay._rightGLAxis.refreshDevicePixelRatio()
            if hasattr(spectrumDisplay, '_bottomGLAxis'):
                spectrumDisplay._bottomGLAxis.refreshDevicePixelRatio()

    @property
    def modules(self):
        """Return tuple of modules currently displayed
        """
        return tuple([m for m in self.moduleArea.modules.values()])

    def _setupNotifiers(self):
        """Setup notifiers connecting gui to current and project
        """
        # Marks
        self.setNotifier(self.application.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Mark', GuiStrip._updateDisplayedMarks)
        # current notifiers
        self.setNotifier(self.application.current, [Notifier.CURRENT], 'strip', self._highlightCurrentStrip)
        self.setNotifier(self.application.current, [Notifier.CURRENT], 'peaks', GuiStrip._updateSelectedPeaks)
        self.setNotifier(self.application.current, [Notifier.CURRENT], 'integrals', GuiStrip._updateSelectedIntegrals)
        self.setNotifier(self.application.current, [Notifier.CURRENT], 'multiplets', GuiStrip._updateSelectedMultiplets)
        self.setNotifier(self.application.project, [Notifier.CHANGE], 'SpectrumDisplay', self._spectrumDisplayChanged)

    def _activatedkeySequence(self, ev):
        key = ev.key()
        self.statusBar().showMessage('key: %s' % str(key))

    def _ambiguouskeySequence(self, ev):
        key = ev.key()
        self.statusBar().showMessage('key: %s' % str(key))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowMinimized:

                # don't do anything on minimising
                pass

            elif event.oldState() & QtCore.Qt.WindowMinimized:

                # TODO:ED changeEvent: Normal/Maximised/FullScreen - call populate all modules
                pass

        event.ignore()

    def _initProject(self):
        """
        Puts relevant information from the project into the appropriate places in the main window.
        """
        project = self.application.project
        isNew = project.isNew

        path = project.path
        self.namespace['project'] = project
        self.namespace['runMacro'] = self.pythonConsole._runMacro

        msg = path + (' created' if isNew else ' opened')
        self.statusBar().showMessage(msg)
        msg2 = 'project = %sProject("%s")' % (('new' if isNew else 'open'), path)

        self._fillRecentProjectsMenu()
        self.pythonConsole.setProject(project)
        self._updateWindowTitle()
        if self.application.project.isTemporary:
            self.getMenuAction('Project->Archive').setEnabled(False)
        else:
            self.getMenuAction('Project->Archive').setEnabled(True)

        from copy import deepcopy

        # get the project layout as soon as mainWindow is initialised
        if self.application.preferences.general.restoreLayoutOnOpening:
            self.moduleLayouts = self.application._getUserLayout()
            self._spectrumModuleLayouts = deepcopy(self.moduleLayouts)
        else:
            self._spectrumModuleLayouts = self.moduleLayouts = None

    def _updateWindowTitle(self):
        """
        #CCPN INTERNAL - called in saveProject method of Framework
        """
        applicationName = self.application.applicationName
        version = self.application.applicationVersion

        #GST certainly on osx i would even remove the app name as it should be in the menu
        #GST switched order file name first its the most important info and on osx it
        # appears next to the proxy icon
        if not self.project.isTemporary:
            filename = self.application.project.name
            windowTitle = '{} - {}[{}][*]'.format(filename, applicationName, version)
        else:
            windowTitle = '{}[{}][*]'.format(applicationName, version)

        self.setWindowTitle(windowTitle)

    def getMenuAction(self, menuString, topMenuAction=None):
        from ccpn.framework.Translation import translator

        if topMenuAction is None:
            topMenuAction = self._menuBar
        splitMenuString = menuString.split('->')
        splitMenuString = [translator.translate(text) for text in splitMenuString]
        if len(splitMenuString) > 1:
            topMenuAction = self.getMenuAction('->'.join(splitMenuString[:-1]), topMenuAction)
        for a in topMenuAction.actions():
            # print ('>>>', menuString, a.text())
            if a.text() == splitMenuString[-1]:
                return a.menu() or a
        raise ValueError('Menu item not found.')

    def searchMenuAction(self, menuString, topMenuAction=None):
        from ccpn.framework.Translation import translator

        found = None
        if topMenuAction is None:
            topMenuAction = self._menuBar
        splitMenuString = menuString.split('->')
        splitMenuString = [translator.translate(text) for text in splitMenuString]
        if len(splitMenuString) > 1:
            topMenuAction = self.getMenuAction('->'.join(splitMenuString[:-1]), topMenuAction)
        for a in topMenuAction.actions():
            # print ('>>>', menuString, a.text())
            if a.text() == splitMenuString[-1]:
                found = a.menu() if a.menu() else a
                break
            else:
                if a.menu():
                    found = self.searchMenuAction(menuString, topMenuAction=a.menu())
                    if found:
                        break
        return found

    def _setupWindow(self):
        """
        Sets up SideBar, python console and splitters to divide up main window properly.

        """
        self.namespace = {'application': self.application,
                          'current'    : self.application.current,
                          'preferences': self.application.preferences,
                          'redo'       : self.application.redo,
                          'undo'       : self.application.undo,
                          'get'        : self.application.get,

                          'ui'         : self.application.ui,
                          'mainWindow' : self,
                          'project'    : self.application.project,
                          'loadProject': self.application.loadProject,
                          # 'newProject' : self.application.newProject,
                          'info'       : getLogger().info,
                          'warning'    : getLogger().warning,
                          }
        self.pythonConsole = IpythonConsole(self)

        # create the sidebar
        self._sideBarFrame = Frame(self, setLayout=True)  # in this frame is inserted the search widget
        self._sideBarFrame.setContentsMargins(4, 2, 0, 0)

        # create a splitter for the sidebar
        self._sidebarSplitter = Splitter(self._sideBarFrame, horizontal=False)
        self._sidebarSplitter.setContentsMargins(0, 0, 0, 0)
        self._sideBarFrame.getLayout().addWidget(self._sidebarSplitter, 0, 0)  # must be inserted this way

        # create 2 more containers for the search bar and the results
        self.searchWidgetContainer = Frame(self._sideBarFrame, setLayout=True, grid=(1, 0))  # in this frame is inserted the search widget
        self.searchResultsContainer = Frame(self, setLayout=True)  # in this frame is inserted the search widget
        self.searchResultsContainer.setMinimumHeight(100)

        # create a SideBar pointing to the required containers
        self.sideBar = SideBar(parent=self, mainWindow=self,
                               searchWidgetContainer=self.searchWidgetContainer,
                               searchResultsContainer=self.searchResultsContainer)

        # insert into the splitter
        self._sidebarSplitter.insertWidget(0, self.sideBar)
        self._sidebarSplitter.insertWidget(1, self.searchResultsContainer)
        self._sidebarSplitter.setChildrenCollapsible(False)

        # # GST resizing the splitter by hand causes problems so currently disable it!
        # for i in range(self._sidebarSplitter.count()):
        #     self._sidebarSplitter.handle(i).setEnabled(False)

        # create a splitter to put the sidebar on the left
        self._horizontalSplitter = Splitter(horizontal=True)

        self._horizontalSplitter.addWidget(self._sideBarFrame)
        self._horizontalSplitter.addWidget(self.moduleArea)
        self.setCentralWidget(self._horizontalSplitter)

        self._temporaryWidgetStore = Frame(parent=self, showBorder=None, setLayout=False)
        self._temporaryWidgetStore.hide()

    def _setupMenus(self):
        """
        Creates menu bar for main window and creates the appropriate menus according to the arguments
        passed at startup.

        This currently pulls info on what menus to create from Framework.  Once GUI and Project are
        separated, Framework should be able to call a method to set the menus.
        """

        self._menuBar = self.menuBar()
        for m in self.application._menuSpec:
            self._createMenu(m)
        self._menuBar.setNativeMenuBar(self.application.preferences.general.useNativeMenus)

        self._fillRecentProjectsMenu()
        self._fillPredefinedLayoutMenu()
        self._fillRecentMacrosMenu()
        #TODO:ED needs fixing
        self._reloadCcpnPlugins()
        # self._fillCcpnPluginsMenu()
        # self._fillUserPluginsMenu()

        self._attachModulesMenuAction()
        self._attachCCPNMacrosMenuAction()
        # self._attachUserMacrosMenuAction()
        self._attachTutorialsMenuAction()

    def _attachModulesMenuAction(self):
        # add a connect to call _fillModulesMenu when the menu item is about to show
        # so it is always up-to-date
        modulesMenu = self.searchMenuAction(SHOWMODULESMENU)
        modulesMenu.aboutToShow.connect(self._fillModulesMenu)

    def _attachCCPNMacrosMenuAction(self):
        # add a connect to call _fillCCPNMacrosMenu when the menu item is about to show
        # so it is always up-to-date
        modulesMenu = self.searchMenuAction(CCPNMACROSMENU)
        modulesMenu.aboutToShow.connect(self._fillCCPNMacrosMenu)

    def _attachUserMacrosMenuAction(self):
        # add a connect to call _fillUserMacrosMenu when the menu item is about to show
        # so it is always up-to-date
        modulesMenu = self.searchMenuAction(USERMACROSMENU)
        modulesMenu.aboutToShow.connect(self._fillUserMacrosMenu)

    def _attachTutorialsMenuAction(self):
        # add a connect to call _fillTutorialsMenu when the menu item is about to show
        # so it is always up-to-date
        modulesMenu = self.searchMenuAction(TUTORIALSMENU)
        modulesMenu.aboutToShow.connect(self._fillTutorialsMenu)

    def _createMenu(self, spec, targetMenu=None):
        menu = self._addMenu(spec[0], targetMenu)
        setWidgetFont(menu)
        self._addMenuActions(menu, spec[1])

    def _addMenu(self, menuTitle, targetMenu=None):
        if targetMenu is None:
            targetMenu = self._menuBar
        if isinstance(targetMenu, MenuBar):
            menu = Menu(menuTitle, self)
            targetMenu.addMenu(menu)
        else:
            menu = targetMenu.addMenu(menuTitle)
        return menu

    def _storeShortcut(self, twoLetters, thecallable):
        if twoLetters is not None:
            twoLetters = twoLetters.replace(', ', '')
            twoLetters = twoLetters.lower()
            if twoLetters not in self._shortcutsDict:
                self._shortcutsDict[twoLetters] = thecallable
            else:
                alreadyUsed = self._shortcutsDict.get(twoLetters)
                getLogger().warning(" Ambiguous shortcut overload: %s. \n Assigning to: %s. \nAlready in use for: \n %s." %
                                    (twoLetters, thecallable, alreadyUsed))

    def _storeMainMenuShortcuts(self, actions):
        for action in actions:
            if len(action) == 3:
                name, thecallable, shortCutDefs = action
                kwDict = dict(shortCutDefs)
                twoLetters = kwDict.get('shortcut')
                self._storeShortcut(twoLetters, thecallable)

    def _addMenuActions(self, menu, actions):
        self._storeMainMenuShortcuts(actions)
        for action in actions:
            if len(action) == 0:
                menu.addSeparator()
            elif len(action) == 2:
                if callable(action[1]):
                    _action = Action(self, action[0], callback=action[1])
                    menu.addAction(_action)
                else:
                    self._createMenu(action, menu)
            elif len(action) == 3:
                kwDict = dict(action[2])
                for k, v in kwDict.items():
                    if (k == 'shortcut') and v.startswith('⌃'):  # Unicode U+2303, NOT the carrot on your keyboard.
                        kwDict[k] = QKeySequence('Ctrl+{}'.format(v[1:]))
                menuAction = Action(self, action[0], callback=action[1], **kwDict)
                menu.addAction(menuAction)

    # def _isTemporaryProject(self):
    #     """Return true if the project is temporary, i.e., not saved or updated.
    #     """
    #     return self.project.isTemporary


    def _checkForBadSpectra(self, project):
        """Report bad spectra in a popup
        """
        badSpectra = [str(spectrum) for spectrum in project.spectra if not spectrum.hasValidPath()]
        if badSpectra:
            text = 'Detected invalid Spectrum file path(s) for:\n\n'
            for sp in badSpectra:
                text += '%s\n' % str(sp)
            text += '\nUse menu "Spectrum --> Validate paths.." or "VP" shortcut to correct\n'
            showWarning('Spectrum file paths', text)

    # def _loadProjectSingleTry(self, projectDir):
    #     """Load/Reload project after load dialog.
    #     """
    #     from ccpn.ui.gui.widgets.MessageDialog import showWarning
    #
    #     project = self.application.loadProject(projectDir)
    #     if project is None:
    #         showWarning('Load Project', 'Error loading project "%s"' % projectDir)
    #
    #     else:
    #         project._mainWindow.sideBar.buildTree(project)
    #         project._mainWindow.show()
    #         QtWidgets.QApplication.setActiveWindow(project._mainWindow)
    #
    #         # if the new project contains invalid spectra then open the popup to see them
    #         badSpectra = [str(spectrum) for spectrum in project.spectra if not spectrum.hasValidPath()]
    #         if badSpectra:
    #             text = 'Detected invalid Spectrum file path(s) for:\n\n'
    #             for sp in badSpectra:
    #                 text += '%s\n' % str(sp)
    #             text += '\nUse menu "Spectrum --> Validate paths.." or "VP" shortcut to correct\n'
    #             showWarning('Spectrum file paths', text)
    #
    #     return project

    # def _loadProjectLastValid(self, projectDir):
    #     """Try and load a new project, if error try and load the last valid project.
    #     """
    #     lastValidProject = self.project.path
    #     lastProjectisTemporary = self.project.isTemporary
    #
    #     # try and load the new project
    #     # try:
    #     project = self._loadProjectSingleTry(projectDir)
    #     if project:
    #         undo = self._project._undo
    #         if undo is not None:
    #             undo.markClean()
    #         return project

        # except Exception as es:
        #     MessageDialog.showError('loadProject', 'Error loading project:\n%s\n\n%s\n\nReloading last saved position.' % (str(projectDir), str(es)))
        #     Logging.getLogger().warning('Error loading project: %s - Reloading last saved position.' % str(projectDir))
        #
        #     if not lastProjectisTemporary:
        #         # try and load the previous project (only one try)
        #         try:
        #             project = self._loadProjectSingleTry(lastValidProject)
        #             return project
        #
        #         except Exception as es:
        #             MessageDialog.showError('loadProject', 'Error loading last project:\n%s\n\n%s' % (str(lastValidProject), str(es)))
        #             Logging.getLogger().warning('Error loading last project: %s' % str(lastValidProject))
        #     else:
        #         # open a new project again
        #         project = self.application.newProject()
        #         project._mainWindow.sideBar.buildTree(project)
        #         project._mainWindow.show()
        #         QtWidgets.QApplication.setActiveWindow(project._mainWindow)
        #         return project

    def showNefPopup(self, path=None):
        """
        Opens the Nef import popup
        If path specified then opens popup to the file otherwise opens load dialog
        """
        path = Path.aPath(path) if path else None

        self.application._importNef(path)

    def _fillRecentProjectsMenu(self):
        """
        Populates recent projects menu with 10 most recently loaded projects
        specified in the preferences file.
        """
        recentFileLocations = self.application._getRecentFiles()
        recentFileMenu = self.getMenuAction('Project->Open Recent')
        recentFileMenu.clear()
        for recentFile in recentFileLocations:
            # action = Action(self, text=recentFile, translate=False,
            #                callback=partial(self.application.loadProject, path=recentFile))

            action = Action(self, text=recentFile, translate=False,
                            callback=partial(self._openProject, projectDir=recentFile))
            recentFileMenu.addAction(action)
        recentFileMenu.addSeparator()
        recentFileMenu.addAction(Action(recentFileMenu, text='Clear',
                                        callback=self.application.clearRecentProjects))

    def _fillPredefinedLayoutMenu(self):
        """
        Populates predefined Layouts
        """
        from ccpn.util import Layout
        from ccpn.framework.PathsAndUrls import predefinedLayouts

        userDefinedLayoutDirPath = self.application.preferences.general.get('userLayoutsPath')
        prelayouts = Layout._dictLayoutsNamePath(Layout._getPredefinedLayouts(predefinedLayouts))
        prelayoutMenu = self.getMenuAction('Project->Layout->Open pre-defined')
        prelayoutMenu.clear()
        for name, path in prelayouts.items():
            action = Action(self, text=name, translate=False,
                            callback=partial(self.application.restoreLayoutFromFile, path))
            prelayoutMenu.addAction(action)
        prelayoutMenu.addSeparator()
        userLayouts = Layout._dictLayoutsNamePath(Layout._getPredefinedLayouts(userDefinedLayoutDirPath))
        for name, path in userLayouts.items():
            action = Action(self, text=name, translate=False,
                            callback=partial(self.application.restoreLayoutFromFile, path))
            prelayoutMenu.addAction(action)
        prelayoutMenu.addSeparator()
        action = Action(self, text='Update', translate=False,
                        callback=self._fillPredefinedLayoutMenu)
        prelayoutMenu.addAction(action)

    def _fillMacrosMenu(self):
        """
        Populates recent macros menu with last ten macros ran.
        """
        #TODO: make sure that running a macro adds it to the prefs and calls this function

        recentMacrosMenu = self.getMenuAction('Macro->Run Recent')
        recentMacrosMenu.clear()

        from ccpn.framework.PathsAndUrls import macroPath as ccpnMacroPath

        try:
            ccpnMacros = os.listdir(ccpnMacroPath)
            ccpnMacros = [f for f in ccpnMacros if
                          os.path.isfile(os.path.join(ccpnMacroPath, f))]
            ccpnMacros = [f for f in ccpnMacros if f.split('.')[-1] == 'py']
            ccpnMacros = [f for f in ccpnMacros if not f.startswith('.')]
            ccpnMacros = [f for f in ccpnMacros if not f.startswith('_')]
            ccpnMacros = sorted(ccpnMacros)

            recentMacrosMenu.clear()
            for macro in ccpnMacros:
                action = Action(self, text=macro, translate=False,
                                callback=partial(self.runMacro,
                                                 macroFile=os.path.join(ccpnMacroPath, macro)))
                recentMacrosMenu.addAction(action)
            if len(ccpnMacros) > 0:
                recentMacrosMenu.addSeparator()
        except FileNotFoundError:
            pass

    def _fillRecentMacrosMenu(self):
        """
        Populates recent macros menu with last ten macros ran.
        TODO: make sure that running a macro adds it to the prefs and calls this function
        """
        recentMacrosMenu = self.getMenuAction('Macro->Run Recent')
        recentMacros = self.application.preferences.recentMacros
        if len(recentMacros) < 0:
            self._fillMacrosMenu()  #uses the default Macros

        else:
            recentMacros = recentMacros[-10:]
            recentMacrosMenu.clear()
            for recentMacro in sorted(recentMacros, reverse=True):
                action = Action(self, text=recentMacro, translate=False,
                                callback=partial(self.application.runMacro, macroFile=recentMacro))
                recentMacrosMenu.addAction(action)
            recentMacrosMenu.addSeparator()

        recentMacrosMenu.addAction(Action(recentMacrosMenu, text='Refresh',
                                          callback=self._fillRecentMacrosMenu))
        recentMacrosMenu.addAction(Action(recentMacrosMenu, text='Browse...',
                                          callback=self.application.runMacro))
        recentMacrosMenu.addAction(Action(recentMacrosMenu, text='Clear',
                                          callback=self.application.clearRecentMacros))

    def _addPluginSubMenu(self, MENU, Plugin):
        targetMenu = pluginsMenu = self.searchMenuAction(MENU)
        if '...' in Plugin.PLUGINNAME:
            package, name = Plugin.PLUGINNAME.split('...')
            try:
                targetMenu = self.getMenuAction(package, topMenuAction=pluginsMenu)
            except ValueError:
                targetMenu = self._addMenu(package, targetMenu=pluginsMenu)
        else:
            name = Plugin.PLUGINNAME
        action = Action(self, text=name, translate=False,
                        callback=partial(self.startPlugin, Plugin=Plugin))
        targetMenu.addAction(action)

    def _fillModulesMenu(self):
        modulesMenu = self.searchMenuAction(SHOWMODULESMENU)
        modulesMenu.clear()

        moduleSize = self.sideBar.size()
        visible = moduleSize.width() != 0 and moduleSize.height() != 0 and self.sideBar.isVisible()
        modulesMenu.addAction(Action(modulesMenu, text='Sidebar',
                                     checkable=True, checked=visible,
                                     # callback=partial(self._showSideBarModule, self._sideBarFrame, self, visible)))
                                     callback=partial(self._showSideBarModule, self._sideBarFrame, self, visible)))

        for module in self.moduleArea.ccpnModules:
            visible = module.isVisible()
            modulesMenu.addAction(Action(modulesMenu, text=module.name(),
                                         checkable=True, checked=visible,
                                         callback=partial(self._showModule, module)))

    def _showModule(self, module):
        try:
            menuItem = self.searchMenuAction(module.name())
            if menuItem:
                module.setVisible(not module.isVisible())

        except Exception as es:
            Logging.getLogger().warning('Error expanding module: %s', module.name())

    def _fillCCPNMacrosMenu(self):
        modulesMenu = self.searchMenuAction(CCPNMACROSMENU)
        modulesMenu.clear()

        from ccpn.framework.PathsAndUrls import macroPath
        from os import walk

        # read the macros file directory - only top level
        macroFiles = []
        for (dirpath, dirnames, filenames) in walk(os.path.expanduser(macroPath)):
            macroFiles.extend([os.path.join(dirpath, filename) for filename in filenames])
            break

        for file in macroFiles:
            filename, fileExt = os.path.splitext(file)

            if fileExt == '.py':
                modulesMenu.addAction(Action(modulesMenu, text=os.path.basename(filename),
                                             callback=partial(self._runCCPNMacro, file, self)))

    def _fillUserMacrosMenu(self):
        modulesMenu = self.searchMenuAction(USERMACROSMENU)
        modulesMenu.clear()

        macroPath = self.application.preferences.general.userMacroPath
        from os import walk

        # read the macros file directory - only top level
        macroFiles = []
        for (dirpath, dirnames, filenames) in walk(os.path.expanduser(macroPath)):
            macroFiles.extend([os.path.join(dirpath, filename) for filename in filenames])
            break

        for file in macroFiles:
            filename, fileExt = os.path.splitext(file)

            if fileExt == '.py':
                modulesMenu.addAction(Action(modulesMenu, text=os.path.basename(filename),
                                             callback=partial(self._runUserMacro, file, self)))

    def _runCCPNMacro(self, filename, modulesMenu):
        """Run a CCPN macro from the populated menu
        """
        try:
            self.application.runMacro(filename)

        except Exception as es:
            Logging.getLogger().warning('Error running CCPN Macro: %s' % str(filename))

    def _runUserMacro(self, filename, modulesMenu):
        """Run a User macro from the populated menu
        """
        try:
            self.application.runMacro(filename)

        except Exception as es:
            Logging.getLogger().warning('Error running User Macro: %s' % str(filename))

    def _fillTutorialsMenu(self):
        modulesMenu = self.searchMenuAction(TUTORIALSMENU)
        modulesMenu.clear()
        import ccpn.framework.PathsAndUrls as pa
        from ccpn.util.Path import aPath

        importantList = (('Beginners Tutorial', pa.beginnersTutorialPath),
                         ('Backbone Assignment Tutorial', pa.backboneAssignmentTutorialPath),
                         ('Chemical Shift Perturbation Tutorial', pa.cspTutorialPath),
                         ('Solid State Peptide Tutorial', pa.solidStatePeptideTutorialPath),
                         ('Solid State SH3 Tutorial', pa.solidStateSH3TutorialPath),
                         ('Screen Tutorial', pa.analysisScreenTutorialPath))

        # add link to website videos
        modulesMenu.addAction(Action(modulesMenu, text='Video Tutorials && Manual', callback=self._showCCPNTutorials))
        modulesMenu.addSeparator()

        # add the main tutorials
        for text, file in importantList:
            filePath = aPath(file)
            if filePath.exists() and filePath.suffix == '.pdf':
                modulesMenu.addAction(Action(modulesMenu, text=text, callback=partial(self._showTutorial, file, self)))
        modulesMenu.addSeparator()

        # add the remaining tutorials from the tutorials top directory
        tutorialsFiles = aPath(pa.tutorialsPath).listDirFiles('pdf')
        for filePath in sorted(tutorialsFiles, key=lambda ff: ff.basename):
            if filePath not in [ff[1] for ff in importantList]:
                _label = camelCaseToString(filePath.basename)
                _label = _label.replace('Chem Build', 'ChemBuild')
                modulesMenu.addAction(Action(modulesMenu, text=_label,
                                             callback=partial(self._showTutorial, filePath, self)))
        modulesMenu.addSeparator()

        # add the How-Tos submenu
        howtosMenu = self._addMenu(HOWTOSMENU, modulesMenu)
        howtosFiles = aPath(pa.howTosPath).listDirFiles('pdf')
        for filePath in sorted(howtosFiles, key=lambda ff: ff.basename):
            _label = camelCaseToString(filePath.basename)
            howtosMenu.addAction(Action(howtosMenu, text=_label, callback=partial(self._showTutorial, filePath, self)))


    def _showCCPNTutorials(self):
        from ccpn.framework.PathsAndUrls import ccpnVideos

        # import webbrowser

        # webbrowser.open(ccpnVideos)
        self.application._showHtmlFile('Video Tutorials', ccpnVideos)

    def _showTutorial(self, filename, modulesMenu):
        """Run a CCPN macro from the populated menu
        """
        try:
            self.application._systemOpen(filename)

        except Exception as es:
            Logging.getLogger().warning('Error opening tutorial: %s' % str(filename))

    def _showSideBarModule(self, module, modulesMenu, visible):
        try:
            # if module.size().height() != 0 and module.size().width() != 0:  #menuItem.isChecked():    # opposite as it has toggled

            if visible:
                module.hide()
            else:
                module.show()
        except Exception as es:
            Logging.getLogger().warning('Error expanding module: sideBar')

    def keyPressEvent(self, e):

        if e.key() == QtCore.Qt.Key_Escape:
            # Reset Mouse Mode
            mode = getCurrentMouseMode()
            if mode != SELECT:
                self.setMouseMode(SELECT)

    def _fillCcpnPluginsMenu(self):

        from ccpn.plugins import loadedPlugins

        pluginsMenu = self.searchMenuAction(CCPNPLUGINSMENU)
        pluginsMenu.clear()
        for Plugin in loadedPlugins:
            self._addPluginSubMenu(CCPNPLUGINSMENU, Plugin)
        pluginsMenu.addSeparator()
        pluginsMenu.addAction(Action(pluginsMenu, text='Reload',
                                     callback=self._reloadCcpnPlugins))

    def _reloadCcpnPlugins(self):
        from ccpn import plugins
        from importlib import reload
        from ccpn.util.Path import aPath

        reload(plugins)

        pluginUserPath = self.application.preferences.general.userPluginPath
        import importlib.util

        filePaths = [(aPath(r) / file) for r, d, f in os.walk(aPath(pluginUserPath)) for file in f if os.path.splitext(file)[1] == '.py']

        for filePath in filePaths:
            # iterate and load the .py files in the plugins directory
            spec = importlib.util.spec_from_file_location(".", filePath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        self._fillCcpnPluginsMenu()
        self._fillUserPluginsMenu()

    def _fillUserPluginsMenu(self):

        from ccpn.plugins import loadedUserPlugins

        pluginsMenu = self.searchMenuAction(PLUGINSMENU)
        pluginsMenu.clear()
        for Plugin in loadedUserPlugins:
            self._addPluginSubMenu(PLUGINSMENU, Plugin)
        pluginsMenu.addSeparator()
        pluginsMenu.addAction(Action(pluginsMenu, text='Reload',
                                     callback=self._reloadUserPlugins))

    def _reloadUserPlugins(self):
        self._reloadCcpnPlugins()

    def startPlugin(self, Plugin):
        plugin = Plugin(application=self.application)
        self.application.plugins.append(plugin)
        if plugin.guiModule is None:
            if not plugin.UiPlugin:
                plugin.run()
                return
            else:
                from ccpn.ui.gui.modules.PluginModule import AutoGeneratedPluginModule

                pluginModule = AutoGeneratedPluginModule(mainWindow=self,
                                                         plugin=plugin,
                                                         application=self.application)  # ejb

        else:
            pluginModule = plugin.guiModule(name=plugin.PLUGINNAME, parent=self,
                                            plugin=plugin, application=self.application,
                                            mainWindow=self)
        plugin.ui = pluginModule
        if not pluginModule.aborted:
            self.application.ui.pluginModules.append(pluginModule)
            self.moduleArea.addModule(pluginModule)
        # TODO: open as pop-out, not as part of MainWindow
        # self.moduleArea.moveModule(pluginModule, position='above', neighbor=None)

    def _updateRestoreArchiveMenu(self):

        action = self.getMenuAction('Project->Restore From Archive...')
        action.setEnabled(bool(self.application._archivePaths()))

    def undo(self):
        self._project._undo.undo()

    def redo(self):
        self._project._undo.redo()

    def saveLogFile(self):
        pass

    def clearLogFile(self):
        pass

    def displayProjectSummary(self):
        info = MessageDialog.showInfo('Not implemented yet',
                                      'This function has not been implemented in the current version')

    def _closeWindowFromUpdate(self, event=None, disableCancel=True):
        # set the active window to mainWindow so that the quit popup centres correctly.
        self._closeWindow(event=event, disableCancel=disableCancel)
        os._exit(0)

    def _closeEvent(self, event=None, disableCancel=False):
        # set the active window to mainWindow so that the quit popup centres correctly.
        self._closeWindow(event=event, disableCancel=disableCancel)

    def _closeWindow(self, event=None, disableCancel=False):
        """
        Saves application preferences. Displays message box asking user to save project or not.
        Closes Application.
        """
        #GWV 20181214: moved to Framework._savePreferences
        #from ccpn.framework.PathsAndUrls import userPreferencesPath
        #prefPath = os.path.expanduser("~/.ccpn/v3settings.json")
        # directory = os.path.dirname(userPreferencesPath)
        # if not os.path.exists(directory):
        #     try:
        #         os.makedirs(directory)
        #     except Exception as e:
        #         self._project._logger.warning('Preferences not saved: %s' % (directory, e))
        #         return
        #
        # prefFile = open(userPreferencesPath, 'w+')
        # json.dump(self.application.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
        # prefFile.close()

        undos = self.application.project._undo

        # set the active window to mainWindow so that the quit popup centres correctly.
        QtWidgets.QApplication.setActiveWindow(self)

        QUIT = 'Quit Program'
        MESSAGE = QUIT
        CANCEL = 'Cancel'
        QUIT_WITHOUT_SAVING = 'Quit without saving'
        SAVE_DATA = 'Save changes'
        DETAIL = "Do you want to save changes before quitting?"

        if disableCancel:
            if undos.isDirty():
                reply = MessageDialog.showMulti(MESSAGE, DETAIL, [QUIT], checkbox=SAVE_DATA, okText=QUIT,
                                                checked=True)
            else:
                reply = QUIT_WITHOUT_SAVING

        else:
            if undos.isDirty():
                reply = MessageDialog.showMulti(MESSAGE, DETAIL, [QUIT, CANCEL], checkbox=SAVE_DATA, okText=QUIT,
                                                checked=True)
            else:
                reply = QUIT_WITHOUT_SAVING

        if (QUIT in reply) and (SAVE_DATA in reply):
            if event:
                event.accept()
            # prefFile = open(userPreferencesPath, 'w+')
            # json.dump(self.application.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
            # prefFile.close()

            self.application._savePreferences()
            success = self.application.saveProject()
            if success is True:
                # Close and clean up project
                self.deleteAllNotifiers()
                self.application._closeProject()  # close if saved
                QtWidgets.QApplication.quit()
                os._exit(0)

            else:
                if event:  # ejb - don't close the project
                    event.ignore()

        elif (QUIT in reply and SAVE_DATA not in reply) or (reply == QUIT_WITHOUT_SAVING):
            if event:
                event.accept()
            # prefFile = open(userPreferencesPath, 'w+')
            # json.dump(self.application.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
            # prefFile.close()

            self.application._savePreferences()
            self.deleteAllNotifiers()
            self.application._closeProject()
            QtWidgets.QApplication.quit()
            os._exit(0)

        else:
            if event:
                event.ignore()

    def newMacroFromLog(self):
        """
        Displays macro editor with contents of the log.
        """
        editor = MacroEditor(self.moduleArea, self, "Macro Editor")
        with open(self.project._logger.logPath, 'r') as fp:
            l = fp.readlines()
        text = ''.join([line.strip().split(':', 6)[-1] + '\n' for line in l])
        editor.textBox.setText(text)

    def _highlightCurrentStrip(self, data:Notifier):
        """Callback on current to highlight the strip
        """
        previousStrip = data[Notifier.PREVIOUSVALUE]
        currentStrip = data[Notifier.VALUE]

        if previousStrip == currentStrip:
            return

        if previousStrip and not (previousStrip.isDeleted or previousStrip._flaggedForDelete):
            previousStrip._highlightStrip(False)
            previousStrip.spectrumDisplay._highlightAxes(previousStrip, False)

        if currentStrip and not (currentStrip.isDeleted or currentStrip._flaggedForDelete):
            currentStrip._highlightStrip(True)
            currentStrip._attachZPlaneWidgets()
            currentStrip.spectrumDisplay._highlightAxes(currentStrip, True)

    def _spectrumDisplayChanged(self, data):
        """Callback on spectrumDisplay change
        """
        trigger = data[Notifier.TRIGGER]
        spectrumDisplay = data[Notifier.OBJECT]

        if trigger == Notifier.CHANGE:
            getLogger().debug(f'>>> SPECTRUMDISPLAY CHANGED  -  {spectrumDisplay}')
            spectrumDisplay.setZWidgets()

    def printToFile(self):
        self.application.showPrintSpectrumDisplayPopup()

    def _mousePositionMoved(self, strip: GuiStrip.GuiStrip, position: QtCore.QPointF):
        """ CCPN INTERNAL: called from ViewBox
        This is called when the mouse cursor position has changed in some strip
        :param strip: The strip the mouse cursor is hovering over
        :param position: The cursor position in "natural" (e.g. ppm) units
        :return: None
        """
        assert 0 == 1

    # def _processUrl(self, url) -> list:
    #     """Handle the dropped url
    #     return a tuple ([objs], errorText)
    #     """
    #     # CCPNINTERNAL. Called also from module area and GuiStrip. They should have same behaviour
    #
    #     url = str(url)
    #     getLogger().debug('>>> dropped: ' + url)
    #
    #     objs = []
    #
    #     dataLoader = checkPathForDataLoader(url)
    #
    #     if dataLoader is None:
    #         txt = 'Loading "%s" failed; unrecognised type' % url
    #         getLogger().warning(txt)
    #         # MessageDialog.showError('Load Data', txt, parent=self)
    #         return ([], txt)
    #
    #     if dataLoader.createsNewProject:
    #         if not self._queryCloseProject(title='Load %s project' % dataLoader.dataFormat,
    #                                        phrase='create a new'):
    #             return ([], None)
    #
    #         newProject = self._loadProject(dataLoader=dataLoader)
    #         if newProject is not None:
    #             objs.append(newProject)
    #
    #     else:
    #         with undoBlockWithoutSideBar():
    #             result = dataLoader.load()
    #             objs.extend(result)
    #
    #     return (objs, None)

    def _getDataLoader(self, url):
        """Get dataLoader for the url (or None if not present)
        Allows for reporting or checking through popups
        does not do the actual loading
        :returns a tuple (dataLoader, createNewProject)
        """
        dataLoader = checkPathForDataLoader(url)

        if dataLoader is None:
            txt = 'Loading "%s" failed; unrecognised type' % url
            getLogger().warning(txt)
            return (None, False)

        createNewProject = dataLoader.createNewProject

        # local import here, as checkPathForDataLoaders needs to be called first to assure proper import orer
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader
        from ccpn.framework.lib.DataLoaders.SparkyDataLoader import SparkyDataLoader
        # check-for and set any specific attributes of the dataLoader instance
        # depending on the dataFormat
        if dataLoader.dataFormat == NefDataLoader.dataFormat or \
           dataLoader.dataFormat == SparkyDataLoader.dataFormat:
            choices = ['Import', 'New project', 'Cancel']
            choice = showMulti('Load %s' % dataLoader.dataFormat,
                               'How do you want to handle the file:',
                               choices, parent=self)
            if choice == choices[0]:
                dataLoader.createNewProject = False
                createNewProject = False
            elif choice == choices[1]:
                dataLoader.createNewProject = True
                createNewProject = True
            else:
                dataLoader = None
                createNewProject = False

        return (dataLoader, createNewProject)

    def _processDroppedItems(self, data):
        """Handle the dropped urls
        """
        # CCPNINTERNAL. Called also from module area and GuiStrip. They should have same behaviour
        # use an undoBlockWithoutSideBar, and ignore logging if MAXITEMLOGGING or more items
        # to stop overloading of the log

        urls = [str(url) for url in data.get(DropBase.URLS, []) if len(url)>0]
        if urls is None:
            return []

        getLogger().info('Handling urls...')

        # A list of (url, dataLoader, createsNewProject) tuples. (createsNew to modify behavior, eg. for NEF)
        dataLoaders = []
        # analyse the Urls
        for url in urls:
            dataLoader, createsNewProject = self._getDataLoader(url)
            dataLoaders.append( (url, dataLoader, createsNewProject) )

        # analyse for potential errors
        errorUrls = [url for url, dl, createNew in dataLoaders if dl is None]
        if len(errorUrls) == 1:
            MessageDialog.showError('Load Data', 'Dropped item "%s" was not unrecognised' % errorUrls[0], parent=self)
        elif len(errorUrls) > 1:
            MessageDialog.showError('Load Data', '%d dropped items were not recognised (see log for details)' % \
                                    len(errorUrls), parent=self)

        # Analyse if any Url would create a new project
        createNewProject = any([createNew for url, dl, createNew in dataLoaders])
        if createNewProject and not self._queryCloseProject(title='Load project', phrase='create a new'):
                return []

        # load the url's with valid handlers
        urlsToLoad = [(url, dl, createNew) for url, dl, createNew in dataLoaders if dl is not None]
        doEchoBlocking = len(urlsToLoad) > MAXITEMLOGGING

        # just a helper function to avoid code duplication
        def _getResult(dLoader, createNew):
            if createNew:
                result = [self._loadProject(dataLoader=dLoader)]
            else:
                with undoBlockWithoutSideBar():
                    result = dLoader.load()
            return result
        #end def

        objs = []
        for url, dataLoader, createNewProject in urlsToLoad:
            try:
                if doEchoBlocking:
                    with notificationEchoBlocking():
                        result = _getResult(dataLoader, createNewProject)
                else:
                    result = _getResult(dataLoader, createNewProject)

                if result is not None:
                    objs.extend(result)

            except RuntimeError as es:
                showWarning("Load data", 'Error loading "%s" \n(%s)' % (url, str(es)), parent=self)

        return objs

    def _processPids(self, data, position=None, relativeTo=None):
        """Handle the urls passed to the drop event
        """
        # CCPNINTERNAL. Called also from CcpnModule and CcpnModuleArea. They should have same behaviour

        pids = data[DropBase.PIDS]
        if pids and len(pids) > 0:
            getLogger().debug('>>> dropped pids...')

            objs = [self.project.getByPid(pid) for pid in pids]

            # check whether a new spectrumDisplay is needed, check axisOrdering
            # add show popup for ordering if required
            from ccpn.ui.gui.popups.AxisOrderingPopup import checkSpectraToOpen

            checkSpectraToOpen(self, objs)
            _openItemObject(self, objs, position=position, relativeTo=relativeTo)

    # def _checkUrlsForProject(self, urls):
    #     """Check whether there is a project in the dropped url list,
    #     and return the first project
    #     """
    #     for url in urls:
    #         getLogger().debug('>>> dropped: ' + str(url))
    #
    #         dataType, subType, usePath = ioFormats.analyseUrl(url)
    #         if dataType == 'Project' and subType in (ioFormats.CCPN,
    #                                                  ioFormats.NEF,
    #                                                  ioFormats.NMRSTAR,
    #                                                  ioFormats.SPARKY):
    #             return url

    def _queryCloseProject(self, title, phrase):
        """Query if project can be closed; always True for temporary projects
        :returns True/False
        """
        if self.project.isTemporary:
            return True

        message = 'Do you really want to %s project (current project will be closed %s)?' % \
                  (phrase, (' and any changes will be lost' if self.project.isModified else ''))
        result = MessageDialog.showYesNo(title, message, parent=self)
        return bool(result)

    def _openProject(self, projectDir=None):
        """
        Opens a OpenProject dialog box if project directory is not specified.
        Loads the selected project.
        :returns new project instance or None
        """
        if not self._queryCloseProject(title='Open Project', phrase='open another'):
            return None

        lastValidProject = self.project.path
        project = None

        if projectDir is None:
            dialog = ProjectFileDialog(parent=self, acceptMode='open')
            dialog._show()
            projectDir = dialog.selectedFile()

        if projectDir:
            # try and load the new project
            project = self._loadProject(path=projectDir)

            if self.application.preferences.general.useProjectPath:
                Logging.getLogger().debug2('mainWindow - setting current path %s' % Path.Path(projectDir).parent)
                # this dialog doesn't need to be seen, required to set initialPath
                _dialog = ProjectFileDialog(parent=self, acceptMode='open')
                _dialog.initialPath = Path.Path(projectDir).parent

            # except (ValueError, RuntimeError) as es:
            #     MessageDialog.showError('loadProject', 'Fatal error loading project:\n%s' % str(projectDir))
            #     Logging.getLogger().warning('Fatal error loading project: %s' % str(projectDir))
            #     raise es

            # try:
            #     project = self._loadProject(projectDir)
            #
            # except Exception as es:
            #     MessageDialog.showError('loadProject', 'Fatal error loading project:\n%s\nReloading last saved position.' % str(projectDir))
            #     Logging.getLogger().warning('Fatal error loading project: %s - Reloading last saved position.' % str(projectDir))
            #
            #     # try and load the previous project (only one try)
            #     try:
            #         project = self._loadProject(lastValidProject)
            #
            #     except Exception as es:
            #         MessageDialog.showError('loadProject', 'Fatal error loading previous project:\n%s' % str(lastValidProject))
            #         Logging.getLogger().warning('Fatal error loading previous project: %s' % str(lastValidProject))

        # undo = self._project._undo
        # if undo is not None:
        #     undo.markClean()

        return project

    def _loadProject(self, dataLoader=None, path=None):
        """Load a project either from a dataLoader instance or from path;
        build the project Gui elements
        :returns project instance or None
        """
        if dataLoader is None and path is not None:
            dataLoader = checkPathForDataLoader(path)

        if dataLoader is None:
            MessageDialog.showError('Load Project', 'No suitable dataLoader found', parent=self)
            return None

        if not dataLoader.createNewProject:
            MessageDialog.showError('Load Project', '"%s" does not yield a new project' % dataLoader.path,
                                    parent=self
                                    )
            return None

        # Some error recovery; store info to re-open the current project (or a new default)
        oldProjectPath = self.project.path
        oldProjectIsTemporary = self.project.isTemporary

        try:
            with progressManager(self, 'Loading project %s ... ' % dataLoader.path):
                newProject = dataLoader.load()[0]
                # Note that the newProject has its own MainWindow; i.e. it is not self
                newProject._mainWindow.sideBar.buildTree(newProject)
                newProject._mainWindow.show()
                QtWidgets.QApplication.setActiveWindow(newProject._mainWindow)

            # if the new project contains invalid spectra then open the popup to see them
            self._checkForBadSpectra(newProject)

        except RuntimeError as es:
            MessageDialog.showError('Load Project', '"%s" did not yield a valid new project (%s)' % \
                                    (dataLoader.path, str(es)), parent=self
                                   )

            # First get to a defined state
            self.application.newProject()
            if not oldProjectIsTemporary:
                self.application.loadProject(oldProjectPath)
            return None

        return newProject

    # def _processUrls(self, urls):
    #     """Handle the dropped urls
    #     """
    #     # CCPNINTERNAL. Called also from module area and GuiStrip. They should have same behaviour
    #
    #     objs = []
    #     for url in urls:
    #         url = str(url)
    #         getLogger().debug('>>> dropped: ' + url)
    #
    #         dataLoader = checkPathForDataLoader(url)
    #
    #         if dataLoader is None:
    #             txt = 'Loading "%s" failed' % url
    #             MessageDialog.showError('Load Data', txt)
    #             getLogger().warning(txt)
    #
    #         if dataLoader.createsNewProject:
    #             okToContinue = self._queryCloseProject(title='Load %s project' % dataLoader.dataFormat,
    #                                                     phrase='create a new')
    #             if okToContinue:
    #                 with progressManager(self, 'Loading project... ' + url):
    #                     obj = self._loadProjectLastValid(url)

            # dataType, subType, usePath = ioFormats.analyseUrl(url)
            # if subType == ioFormats.NMRSTAR:  # NMRStar file is available only as import of metadata not as stand alone project
            #     self.application._loadNMRStarFile(url)
            #     return objs
            #
            # if subType == ioFormats.NEF and self.application.preferences.appearance.openImportPopupOnDroppedNef:
            #     self.application._importNef(url)
            #     return objs
            #
            # if dataType == 'Project' and subType in (ioFormats.CCPN,
            #                                          ioFormats.NEF,
            #                                          ioFormats.SPARKY):
            #
            #     try:
            #         okToContinue = self._queryCloseProject(title='Load %s project' % subType,
            #                                                phrase='create a new')
            #         if okToContinue:
            #             with progressManager(self, 'Loading project... ' + url):
            #                 obj = None
            #                 obj = self._loadProjectLastValid(url)
            #
            #     except Exception as es:
            #         MessageDialog.showError('Load Project', 'loadProject Error: %s' % str(es))
            #         getLogger().warning('loadProject Error: %s' % str(es), )
            #         getLogger().exception(str(es))
            #
            # else:
            #     # with progressManager(self.mainWindow, 'Loading data... ' + url):
            #     try:  #  Why do we need this try?
            #         spectraPathsCount = len(ioFormats._searchSpectraPathsInSubDir(url))
            #         askBeforeOpen_lenght = 20  # Ask user if want to open all (spectra) before start loading the full set.
            #         if spectraPathsCount > askBeforeOpen_lenght:
            #             okToOpenAll = MessageDialog.showYesNo('Load data', 'The directory contains multiple items (~%s).'
            #                                                                ' Do you want to open all?' % str(spectraPathsCount))
            #             if not okToOpenAll:
            #                 continue
            #         with notificationEchoBlocking():
            #             data = self.project.loadData(url)
            #             if data:
            #                 objs.extend(data)
            #
            #     except Exception as es:
            #         MessageDialog.showError('Load Data', 'Loading "%s" encountered error: %s' % (url,str(es)))
            #         getLogger().warning('loadData Error: %s' % str(es))
        # return objs

