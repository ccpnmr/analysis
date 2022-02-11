"""
This Module implements the main graphics window functionality
It works in concert with a wrapper object for storing/retrieving attibute values

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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-11 11:45:57 +0000 (Fri, February 11, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-04 09:51:15 +0100 (Tue, April 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import pyqtSlot

from ccpn.core.Project import Project

from ccpn.ui.gui.widgets.Icon import Icon

from ccpn.ui.gui.lib.mouseEvents import SELECT, setCurrentMouseMode, getCurrentMouseMode
from ccpn.ui.gui.lib import GuiStrip
from ccpn.ui.gui.lib.GuiWindow import GuiWindow

from ccpn.ui.gui.modules.MacroEditor import MacroEditor

from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.ui.gui.widgets.Menu import Menu, MenuBar, SHOWMODULESMENU, CCPNMACROSMENU, \
    USERMACROSMENU, TUTORIALSMENU, PLUGINSMENU, CCPNPLUGINSMENU, HOWTOSMENU
from ccpn.ui.gui.widgets.SideBar import SideBar  #,SideBar
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Font import setWidgetFont

from ccpn.util.Common import camelCaseToString
from ccpn.util.Logging import getLogger

from ccpn.core.lib.Notifiers import Notifier

from ccpn.ui.gui.widgets.PlotterWidget import PlotterWidget

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

    WindowMaximiseMinimise = QtCore.pyqtSignal(bool)

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

        logger = getLogger()
        logger.debug('GuiMainWindow: layout: %s' % layout)

        if layout is not None:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        self.setGeometry(200, 40, 1100, 900)

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

        self.setWindowIcon(Icon('icons/ccpn-icon'))
        # self.fileIcon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon, None, self)
        # self.disabledFileIcon = self.makeDisabledFileIcon(self.fileIcon)

        # blank display opened later by the _initLayout if there is nothing to show otherwise
        self.pythonConsoleModule = None
        self.statusBar().showMessage('Ready')
        setCurrentMouseMode(SELECT)
        self.show()

        self._project._undo.undoChanged.add(self._undoChangeCallback)

        # install handler to resize when moving between displays
        self.window().windowHandle().screenChanged.connect(self._screenChangedEvent)
        # self.setUnifiedTitleAndToolBarOnMac(True) #uncomment this to remove the extra title bar on osx 10.14+

    @property
    def ui(self):
        """The application.ui instance; eg. the gui
        """
        return self.application.ui

    @property
    def project(self) -> Project:
        """The current project"""
        #NB this linkage is set by the model (for now)
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

        ## Why do we need to set this icons? Very odd behaviour.
        # if self.project.isTemporary:
        #     self.setWindowIcon(QtGui.QIcon())
        # elif amDirty:
        #     self.setWindowIcon(self.disabledFileIcon)
        # else:
        #     self.setWindowIcon(self.fileIcon)

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
        return tuple(self.moduleArea.ccpnModules)

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

                self.WindowMaximiseMinimise.emit(False)
                # don't do anything on minimising
                pass

            elif event.oldState() & QtCore.Qt.WindowMinimized:

                self.WindowMaximiseMinimise.emit(True)
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
            self.getMenuAction('File->Archive').setEnabled(False)
        else:
            self.getMenuAction('File->Archive').setEnabled(True)

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
        raise ValueError('Menu item %r not found' % menuString)

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
                          'plot'       : PlotterWidget()
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

        # hide this option for now
        modulesMenu = self.searchMenuAction(SHOWMODULESMENU)
        modulesMenu.setVisible(False)

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
        badSpectra = [str(spectrum.pid) for spectrum in project.spectra if not spectrum.hasValidPath()]

        if badSpectra:
            text = 'Use menu "Spectrum --> Validate paths..." Or "VP" shortcut to correct.\n'
            text += 'Please inspect file path(s) for:\n'
            for sp in badSpectra:  # these can be >1000 lines message. Added in a scrollable area.
                text += '%s\n' % str(sp)
            title = 'Detected invalid Spectrum file paths'
            MessageDialog.showWarning(title=title, message=text, scrollableMessage=True)

    def _showNefPopup(self, dataLoader):
        """Helper function; it allows the user to select the elements
        and set the dataLoader._nefReader instance accordingly

        :return False in case of 'cancel'
        """
        from ccpn.ui.gui.popups.ImportNefPopup import ImportNefPopup
        dialog = ImportNefPopup(parent=self,
                                mainWindow=self,
                                project=self.project,
                                dataLoader=dataLoader,
                                )
        if dialog.exec_():
            _nefReader = dialog.getActiveNefReader()
            dataLoader.createNewProject = False
            dataLoader._nefReader = _nefReader
            return True

        return False

    def showNefPopup(self, path=None):
        """
        Query for a Nef file if path is None
        Opens the Nef import popup
        If path specified then opens popup to the file otherwise opens load dialog
        """
        from ccpn.ui.gui.widgets.FileDialog import NefFileDialog
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader

        if path is None:
            filter = '*.nef'
            dialog = NefFileDialog(parent=self.ui.mainWindow, acceptMode='import', fileFilter=filter)
            dialog._show()
            path = dialog.selectedFile()

        if path is None:
            return

        if dataLoader := NefDataLoader(path) is None:
            return None

        if self._showNefPopup(dataLoader):
            with MessageDialog.progressManager(self, 'Loading Nef file %s ... ' % dataLoader.path):
                dataLoader.load()

    def _clearRecentProjects(self):
        self.application.preferences.recentFiles = []
        self._fillRecentProjectsMenu()

    def _fillRecentProjectsMenu(self):
        """
        Populates recent projects menu with 10 most recently loaded projects
        specified in the preferences file.
        """
        recentFileLocations = self.application._getRecentProjectFiles()
        recentFileMenu = self.getMenuAction('File->Open Recent')
        recentFileMenu.clear()
        for recentFile in recentFileLocations:
            # action = Action(self, text=recentFile, translate=False,
            #                callback=partial(self.application.loadProject, path=recentFile))

            action = Action(self, text=recentFile, translate=False,
                            callback=partial(self.ui.loadProject, path=recentFile))
            recentFileMenu.addAction(action)
        recentFileMenu.addSeparator()
        recentFileMenu.addAction(Action(recentFileMenu, text='Clear',
                                        callback=self._clearRecentProjects))

    def _fillPredefinedLayoutMenu(self):
        """
        Populates predefined Layouts
        """
        from ccpn.ui.gui import Layout
        from ccpn.framework.PathsAndUrls import predefinedLayouts

        userDefinedLayoutDirPath = self.application.preferences.general.get('userLayoutsPath')
        prelayouts = Layout._dictLayoutsNamePath(Layout._getPredefinedLayouts(predefinedLayouts))
        prelayoutMenu = self.getMenuAction('File->Layout->Open pre-defined')
        prelayoutMenu.clear()
        for name, path in prelayouts.items():
            action = Action(self, text=name, translate=False,
                            callback=partial(self.application._restoreLayoutFromFile, path))
            prelayoutMenu.addAction(action)
        prelayoutMenu.addSeparator()
        userLayouts = Layout._dictLayoutsNamePath(Layout._getPredefinedLayouts(userDefinedLayoutDirPath))
        for name, path in userLayouts.items():
            action = Action(self, text=name, translate=False,
                            callback=partial(self.application._restoreLayoutFromFile, path))
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

    def _clearRecentMacros(self):
        self.application.preferences.recentMacros = []
        self._fillRecentMacrosMenu()

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
                                          callback=self._clearRecentMacros))

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
            getLogger().warning('Error expanding module: %s', module.name())

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
            getLogger().warning('Error running CCPN Macro: %s' % str(filename))

    def _runUserMacro(self, filename, modulesMenu):
        """Run a User macro from the populated menu
        """
        try:
            self.application.runMacro(filename)

        except Exception as es:
            getLogger().warning('Error running User Macro: %s' % str(filename))

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
            getLogger().warning('Error opening tutorial: %s' % str(filename))

    def _showSideBarModule(self, module, modulesMenu, visible):
        try:
            # if module.size().height() != 0 and module.size().width() != 0:  #menuItem.isChecked():    # opposite as it has toggled

            if visible:
                module.hide()
            else:
                module.show()
        except Exception as es:
            getLogger().warning('Error expanding module: sideBar')

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
        self.application._plugins.append(plugin)
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

        action = self.getMenuAction('File->Restore From Archive...')
        action.setEnabled(bool(self._project._getArchivePaths()))

    def undo(self):
        self._project._undo.undo()

    def redo(self):
        self._project._undo.redo()

    def saveLogFile(self):
        pass

    def clearLogFile(self):
        pass

    def _closeMainWindowModules(self):
        """Close modules in main window;
        CCPNINTERNAL: also called from Framework
        """
        for module in self.moduleArea.ccpnModules:
            getLogger().debug('closing module: %s' % module)
            try:
                module.setVisible(False)  # GWV not sure why, but this was the effect of prior code
                module.close()
            except Exception as es:
                # wrapped C/C++ object of type StripDisplay1d has been deleted
                getLogger().debug(f'_closeMainWindowModules: {es}')

    def _closeExtraWindowModules(self):
        """Close modules in any extra window;
        CCPNINTERNAL: also called from Framework
        """
        for module in self.moduleArea.tempAreas:
            getLogger().debug('closing module: %s' % module)
            try:
                module.setVisible(False)  # GWV not sure why, but this was the effect of prior code
                module.close()
            except Exception as es:
                # wrapped C/C++ object of type StripDisplay1d has been deleted
                getLogger().debug(f'_closeExtraWindowModules: {es}')

    def _closeWindowFromUpdate(self, event=None, disableCancel=True):
        # set the active window to mainWindow so that the quit popup centres correctly.
        self._closeWindow(event=event, disableCancel=disableCancel)
        os._exit(0)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """handle close event from the X button
        """
        event.ignore()
        # pass control to _closeEvent - this cleans up the focus between windows/popups
        QtCore.QTimer.singleShot(0, self._closeWindow)

    def _closeEvent(self, event=None, disableCancel=False):
        """Handle close event from other methods
        """
        self._closeWindow(event=event, disableCancel=disableCancel)

    def _closeWindow(self, event=None, disableCancel=False):
        """
        Saves application preferences. Displays message box asking user to save project or not.
        Closes Application.
        """

        undos = self.application.project._undo

        # set the active window to mainWindow so that the quit popup centres correctly.
        QtWidgets.QApplication.setActiveWindow(self)

        QUIT = 'Quit Program'
        SAVE_QUIT = 'Save and Quit'
        SAVE = 'Save'
        MESSAGE = QUIT
        CANCEL = 'Cancel'
        QUIT_WITHOUT_SAVING = 'Quit without saving'
        SAVE_DATA = 'Save changes'
        DETAIL = "Do you want to save changes before quitting?"
        # add to preferences SAVE_DATA .
        if disableCancel:
            if undos.isDirty():
                reply = MessageDialog.showMulti(MESSAGE, DETAIL, [QUIT], checkbox=SAVE_DATA, okText=QUIT,
                                                checked=False)
                # reply = MessageDialog.showMulti(MESSAGE, DETAIL, [QUIT, SAVE_QUIT], parent=self, okText=QUIT)
            else:
                reply = QUIT_WITHOUT_SAVING

        else:
            if undos.isDirty():
                reply = MessageDialog.showMulti(MESSAGE, DETAIL, [QUIT, CANCEL], checkbox=SAVE_DATA, okText=QUIT,
                                                checked=False)
                # reply = MessageDialog.showMulti(MESSAGE, DETAIL, texts=[QUIT, SAVE_QUIT, CANCEL], parent=self, okText=QUIT)
            else:
                reply = QUIT_WITHOUT_SAVING

        if (QUIT in reply) and (SAVE_DATA in reply or SAVE_QUIT in reply):
            # if (reply in [SAVE_QUIT, SAVE_DATA, SAVE]):
            if event:
                event.accept()

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
            # elif (reply in [QUIT, QUIT_WITHOUT_SAVING]):
            if event:
                event.accept()

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

    def _highlightCurrentStrip(self, data: Notifier):
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
            for strip in self.strips:
                strip._updatePlaneAxes()
            # spectrumDisplay._setPlaneAxisWidgets()

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

    # def _queryChoices(self, dataLoader):
    #     """Query the user about his/her choice to import/new/cancel
    #     """
    #     choices = ('Import', 'New project', 'Cancel')
    #     choice = MessageDialog.showMulti('Load %s' % dataLoader.dataFormat,
    #                        'How do you want to handle "%s":' % dataLoader.path,
    #                        choices, parent=self)
    #
    #     if choice == choices[0]:  # import
    #         dataLoader.createNewProject = False
    #         createNewProject = False
    #         ignore = False
    #     elif choice == choices[1]:  # new project
    #         dataLoader.createNewProject = True
    #         createNewProject = True
    #         ignore = False
    #     else:  # cancel
    #         dataLoader = None
    #         createNewProject = False
    #         ignore = True
    #
    #     return (dataLoader, createNewProject, ignore)

    # def _getDataLoader(self, path, include=None):
    #     """Get dataLoader for path (or None if not present), optionally only testing for
    #     dataFormats defined in include.
    #     Allows for reporting or checking through popups.
    #     Does not do the actual loading.
    #
    #     :param path: the path to get a dataLoader for
    #     :param include: a list/tuple of optional dataFormat strings; (defaults to all dataFormats)
    #     :returns a tuple (dataLoader, createNewProject, ignore)
    #     """
    #     # local import here
    #     from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
    #     from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
    #     from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader
    #     from ccpn.framework.lib.DataLoaders.SparkyDataLoader import SparkyDataLoader
    #     from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import SpectrumDataLoader
    #     from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader
    #
    #     if include is None:
    #         include =  tuple(getDataLoaders().keys())
    #     dataLoader = checkPathForDataLoader(path, include=include)
    #
    #     if dataLoader is None:
    #         txt = 'Loading "%s" unsuccessful; unrecognised type, should be one of %r' % \
    #               (path, include)
    #         getLogger().warning(txt)
    #         return (None, False, False)
    #
    #     createNewProject = dataLoader.createNewProject
    #     ignore = False
    #
    #     if dataLoader.dataFormat == CcpNmrV2ProjectDataLoader.dataFormat:
    #         createNewProject = True
    #         dataLoader.createNewProject = True
    #         ok = MessageDialog.showYesNoWarning('Load Project',
    #                                             f'Project "{path}" was created with version-2 Analysis.\n'
    #                                             '\n'
    #                                             'CAUTION:\n'
    #                                             '\tThe project will be converted to a version-3 project and saved '
    #                                             '\tas a new directory with .cppn extension.\n'
    #                                             '\n'
    #                                             'Do you want to continue loading?')
    #
    #         if not ok:
    #             # skip loading so that user can backup/copy project
    #             getLogger().debug('==> Cancelled loading ccpn project "%s"' % path)
    #             ignore = True
    #
    #     elif dataLoader.dataFormat == CcpNmrV3ProjectDataLoader.dataFormat and Project._needsUpgrading(path):
    #         createNewProject = True
    #         dataLoader.createNewProject = True
    #         ok = MessageDialog.showYesNoWarning('Load Project',
    #                                             f'Project "%s" was saved with an earlier version of AnalysisV3, '
    #                                             'and will be converted to version %s.\n'
    #                                             '\n'
    #                                             'CAUTION:\n'
    #                                             '\tAfter saving, it can NO LONGER be loaded in earlier AnalysisV3 versions.\n'
    #                                             '\t(If you are in any doubt, use "File --> Save As..)\n'
    #                                             '\n'
    #                                             'Do you want to continue loading?' % (
    #                                                 path, self.application.applicationVersion.withoutRelease())
    #                                             )
    #
    #         if not ok:
    #             # skip loading so that user can backup/copy project
    #             getLogger().info('==> Cancelled loading ccpn project "%s"' % path)
    #             ignore = True
    #
    #     elif dataLoader.dataFormat == NefDataLoader.dataFormat:
    #         (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)
    #         if dataLoader and not createNewProject and not ignore:
    #             # we are importing; popup the import window
    #             self._showNefPopup(dataLoader)
    #
    #     elif dataLoader.dataFormat == SparkyDataLoader.dataFormat:
    #         (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)
    #
    #     elif dataLoader.dataFormat == SpectrumDataLoader.dataFormat and dataLoader.existsInProject():
    #         ok = MessageDialog.showYesNoWarning('Spectrum "%s"' % dataLoader.path,
    #                                             f'already exists in the project\n'
    #                                             '\n'
    #                                             'do you want to load?'
    #                            )
    #         if not ok:
    #             ignore = True
    #
    #     elif dataLoader.dataFormat == DirectoryDataLoader.dataFormat and len(dataLoader) > MAXITEMLOGGING:
    #         ok = MessageDialog.showYesNoWarning('Directory "%s"\n' %dataLoader.path,
    #                                             f'\n'
    #                                             'CAUTION: You are trying to load %d items\n'
    #                                             '\n'
    #                                             'Do you want to continue?' % (len(dataLoader,))
    #                                             )
    #
    #         if not ok:
    #             ignore = True
    #
    #     return (dataLoader, createNewProject, ignore)

    def _processDroppedItems(self, data) -> list:
        """Handle the dropped urls
        :return list of loaded objects
        """
        # CCPNINTERNAL. Called also from module area and GuiStrip. They should have same behaviour
        # use an undoBlockWithoutSideBar, and ignore logging if MAXITEMLOGGING or more items
        # to stop overloading of the log

        urls = [str(url) for url in data.get(DropBase.URLS, []) if len(url) > 0]
        if urls is None:
            return []

        getLogger().info('Handling urls...')

        # dataLoaders: A list of (url, dataLoader, createsNewProject, ignore) tuples.
        # createsNewProject: to evaluate later call _loadProject; eg. for NEF
        # ignore: user opted to skip this one; e.g. a spectrum already present
        dataLoaders = []
        # analyse the Urls
        for url in urls:
            # try finding a data loader, catch any errors for recognised but
            # incomplete/invalid url's (i.e. incomplete spectral data)
            try:
                dataLoader, createsNewProject, ignore = self.ui._getDataLoader(url)
                dataLoaders.append((url, dataLoader, createsNewProject, ignore))
            except (RuntimeError, ValueError) as es:
                MessageDialog.showError('Load Data',
                                        'While examining %s:\n%s' % (url, str(es)),
                                        parent=self)

        # All ignored urls
        urlsToIgnore = [(url, dl, createNew) for url, dl, createNew, ignore in dataLoaders if
                         (ignore)]
        # All valid urls
        allUrlsToLoad = [(url, dl, createNew) for url, dl, createNew, ignore in dataLoaders if
                         (not ignore)]

        # Error urls
        errorUrls = [(url, dl, createNew) for url, dl, createNew in allUrlsToLoad if
                         (dl is None)]
        # Project url's
        newProjectUrls = [(url, dl, createNew) for url, dl, createNew in allUrlsToLoad if
                          (dl is not None and createNew)]
        # Data url's
        dataUrls = [(url, dl, createNew) for url, dl, createNew in allUrlsToLoad if
                          (dl is not None and not createNew)]

        if len(urlsToIgnore) == len(dataLoaders):
            return []

        if len(errorUrls) == len(allUrlsToLoad):
            MessageDialog.showError('Load Data', 'No dropped items were not recognised (see log for details)', parent=self)
            return []

        if len(errorUrls) == 1:
            MessageDialog.showError('Load Data', 'Dropped item "%s" was not recognised' % errorUrls[0][0], parent=self)
        elif len(errorUrls) > 1:
            MessageDialog.showError('Load Data', '%d dropped items were not recognised (see log for details)' % \
                                    len(errorUrls), parent=self)

        if len(newProjectUrls) > 1:
            MessageDialog.showError('Load Data', 'More than one (%d) dropped items create a new project' % \
                                    len(newProjectUrls), parent=self)
            return []

        if len(newProjectUrls) + len(dataUrls) == 0:
            MessageDialog.showError('Load Data', 'No dropped items can be loaded', parent=self)
            return []

        _dLoaders = [dl for url, dl, createNew in allUrlsToLoad]
        result = self.application._loadData(_dLoaders)
        return result

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

    # def _queryCloseProject(self, title, phrase):
    #     """Query if project can be closed; always True for temporary projects
    #     :returns True/False
    #     """
    #     if self.project.isTemporary:
    #         return True
    #
    #     message = 'Do you really want to %s project (current project will be closed %s)?' % \
    #               (phrase, (' and any changes will be lost' if self.project.isModified else ''))
    #     result = MessageDialog.showYesNo(title, message, parent=self)
    #     return bool(result)

    # def _loadProject(self, dataLoader=None, path=None):
    #     """Load a project either from a dataLoader instance or from path;
    #     check and query for all load-project related issue
    #     build the project Gui elements
    #     :returns project instance or None
    #     """
    #     if path is None and dataLoader is None:
    #         MessageDialog.showError('Load Project', 'Undefined path', parent=self)
    #         return None
    #
    #     if dataLoader is None and path is not None:
    #         # Try to get a dataLoader instance, checking for path first
    #         _path = aPath(path)
    #         if not _path.exists():
    #             MessageDialog.showError('Load Project', 'Path "%s" does not exist\n(Has the project been moved?)' % path, parent=self)
    #             return None
    #         dataLoader, _tmp, _tmp2 = self._getDataLoader(path)
    #
    #     # By now, we should have a dataLoader instance
    #     if dataLoader is None:
    #         MessageDialog.showError('Load Project', 'No suitable dataLoader found', parent=self)
    #         return None
    #
    #     if not dataLoader.createNewProject:
    #         MessageDialog.showError('Load Project', '"%s" does not yield a new project' % dataLoader.path,
    #                                 parent=self
    #                                 )
    #         return None
    #
    #     return self.ui._loadProject(dataLoader)

        # from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
        # from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader

        #===> To ED: moved to Gui._getDataLoader() method

        # path = dataLoader.path
        # if dataLoader.dataFormat == CcpNmrV2ProjectDataLoader.dataFormat:
        #     ok = MessageDialog.showYesNoWarning('Load Project',
        #                                         f'Project "{path}" was created with version-2 Analysis.\n'
        #                                         '\n'
        #                                         'CAUTION:\n'
        #                                         '\tThe project will be converted to a version-3 project and saved '
        #                                         '\tas a new directory with .cppn extension.\n'
        #                                         '\n'
        #                                         'Do you want to continue loading?')
        #
        #     if not ok:
        #         # skip loading so that user can backup/copy project
        #         getLogger().info('==> Cancelled loading ccpn project "%s"' % path)
        #         return None
        #
        # elif dataLoader.dataFormat == CcpNmrV3ProjectDataLoader.dataFormat and Project._needsUpgrading(path):
        #     ok = MessageDialog.showYesNoWarning('Load Project',
        #                                         f'Project "%s" was saved with an earlier version of AnalysisV3, '
        #                                         'and will be converted to version %s.\n'
        #                                         '\n'
        #                                         'CAUTION:\n'
        #                                         '\tAfter saving, it can NO LONGER be loaded in earlier AnalysisV3 versions.\n'
        #                                         '\t(If you are in any doubt, use "File --> Save As..)\n'
        #                                         '\n'
        #                                         'Do you want to continue loading?' % (
        #                                             path, self.application.applicationVersion.withoutRelease())
        #                                         )
        #
        #     if not ok:
        #         # skip loading so that user can backup/copy project
        #         getLogger().info('==> Cancelled loading ccpn project "%s"' % path)
        #         return None

        # if not self._queryCloseProject(title='Load Project', phrase='open another'):
        #     return None
        #
        # # Some error recovery; store info to re-open the current project (or a new default)
        # oldProjectPath = self.project.path
        # oldProjectIsTemporary = self.project.isTemporary
        #
        # try:
        #     with MessageDialog.progressManager(self, 'Loading project %s ... ' % dataLoader.path):
        #         _loaded = dataLoader.load()
        #         if not _loaded:
        #             return None
        #
        #         newProject = _loaded[0]
        #         # Note that the newProject has its own MainWindow; i.e. it is not self
        #         newProject._mainWindow.sideBar.buildTree(newProject)
        #         newProject._mainWindow.show()
        #         QtWidgets.QApplication.setActiveWindow(newProject._mainWindow)
        #
        #     # if the new project contains invalid spectra then open the popup to see them
        #     self._checkForBadSpectra(newProject)
        #
        # except RuntimeError as es:
        #     MessageDialog.showError('Load Project', '"%s" did not yield a valid new project (%s)' % \
        #                             (dataLoader.path, str(es)), parent=self
        #                             )
        #
        #     # First get to a defined state
        #     self.application._newProject()
        #     if not oldProjectIsTemporary:
        #         self.application.loadProject(oldProjectPath)
        #     return None
        #
        # return newProject
