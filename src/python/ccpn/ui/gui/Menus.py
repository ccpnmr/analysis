"""
    The menus are specified by a (recursive) list composed of either:

    - Action: triggered when the menu item is selected;
      signature:
        Action(name, callback, checkEnabled=None, **options)

      deprecated tuple-based signature:
        (name, callable) tuple or
        (name, callable, options) tuple or
        (name, callable, options, checkEnabled) tuple

        options is a dict of (option, value) pairs.
        Valid options (from Action widget):
            :param shortcut: optional two letter shortcut
            :param checked: optional checked flag (if checkable, default: True)
            :param checkable: optional checkable flag (default: False)
            :param icon: optional icon
            :param enabled: optional enable flag (default: True)
            :param toolTip: optional tooltip

        Signature checkEnabled, returning True if should be enabled:
            checkEnabled(node:MenuNode) -> bool

    - Menu: A menu (list) with items;
      Signature:
        Menu(name, *items, checkEnabled=None)

    - DynamicMenu: a dynamically filled menu
      Signature:
        DynamicMenu(name, checkEnabled=None)

        Signature checkEnabled: see above

    - A section defining operation with signature:
        Section(name)

    - A separator defining operation with signature.
        Separator()

Use insertAfter() or insertBefore() methods to dynamically add to the MenuDefs instance

---------------------------------------------------------------------------------------

This code replaces:

gui. -->
    _updateCheckableMenuItems called from Gui.initialize

mainWindow.
    dynamic menus:; uses aboutToShow PyQt signal
    _fill ....

    -->
    _createMenu
    _addMenu
    _setupMenus
    _storeShortcut
    _storeMainMenuShortcuts
    _addMenuActions
    _addPluginSubMenu
    _attachModulesMenuAction
    _attachCCPNMacrosMenuAction
    _attachTutorialsMenuAction
    _updateRestoreArchiveMenu
    getMenuAction
    searchMenuAction
    findeMenuAction
    _clearRecentProjects
    _clearRecentMacros
    _showModule

GuiMainWindow.  -->
    _attacheTutorialsMenuAction
    _fillTutorialsMenu
        --> How-to's menu
    _fillCcpnPluginsMenu
    _fillUserPluginsMenu
    _fillPredefinedLayoutMenu
    _fillMacrosMenu (Never reached/Used!)
    _fillRecentProjectsMenu
    _fillRecentMacrosMenu
    _fillModulesMenu
    _fillCCPNMacrosMenu
    _fillUserMacrosMenu
    _fillTutorialsMenu
    _runCCPNMacro
    _runUserMacro
    _reloadUserPlugins
    _reloadCCPNPlugins
    _addPluginSubMenu

FrameWork.  -->
    _getProjectFiles
    lots of callbacks

---------------------------------------------------------------------------------------

STRANGE:
In GuiMainWindow.__init__
        self._project._undo.undoChanged.add(self._undoChangeCallback)
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
__dateModified__ = "$dateModified: 2024-08-09 10:17:58 +0100 (Fri, August 09, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"

#=========================================================================================
# Start of code
#=========================================================================================

import os
import platform

from functools import partial
from typing import Optional, Callable, Any, TypeAlias

CallableOrNone = Optional[Callable]


from ccpn.framework.PathsAndUrls import \
    macroPath, \
    widgetsPath, \
    CCPN_ARCHIVES_DIRECTORY
from ccpn.framework.Application import getApplication, getProject, getCurrent

from ccpn.util.Common import isWindowsOS
from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath
from ccpn.util.decorators import singleton
from ccpn.util.Tree import Tree

import ccpn.ui.gui.Layout as Layout
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FileDialog import \
    ArchivesFileDialog, \
    LayoutsFileDialog, \
    NMRStarFileDialog
from ccpn.ui.gui.widgets.Menu import Menu as MenuWidget
from ccpn.ui.gui.widgets.Action import Action as ActionWidget


FILE_MENU = 'File'
FILE_OPEN_RECENT = 'Open Recent'
FILE_LAYOUT = 'Layout'
FILE_LAYOUT_OPEN_PREDEFINED = 'Open pre-defined'

EDIT_MENU = 'Edit'

VIEW_MENU = 'View'
VIEW_SHOW_MODULES = 'Show/hide Modules'
VIEW_CHEMICAL_SHIFT_MAPPING = 'Chemical Shift Mapping (Beta)'

SPECTRUM_MENU = 'Spectrum'
SPECTRUM_LOAD_SPECTRA = 'Load Spectra...'

MOLECULES_MENU = 'Molecules'

MACRO_MENU = 'Macro'
MACRO_RUN_CCPN = 'Run CCPN Macros'
MACRO_RUN_RECENT = 'Run Recent'

PLUGINS_MENU = 'Plugins'
USER_PLUGINS = 'User Plugins'
CCPN_PLUGINS = 'CCPN Plugins'

HELP_MENU = 'Help'
HELP_TUTORIALS = 'Tutorials'
HELP_HOWTOS = 'How-Tos'

DEVELOPMENT_MENU = 'Development'
DEVELOPMENT_DEBUG = 'Debug'


def _optionsDict(**kwds) -> dict:
    """Create and return an options dict
    """
    kwds.setdefault('enabled', True)
    kwds.setdefault('checkable', False)
    kwds.setdefault('checked', True)

    validOptions = 'shortcut enabled checkable checked icon toolTip'.split()
    errors = [option for option in kwds.keys() if option not in validOptions]
    if len(errors) > 0:
        raise ValueError(f'Invalid options: {errors!r}')
    return kwds


def Separator() -> tuple:
    """Convenience; avoids tuple errors
    """
    return ()


def Section(name) -> tuple:
    """Convenience; avoids tuple errors
    """
    return (name,)


def Action(name: str, callback: Callable, checkEnabled: CallableOrNone = None, **options) -> tuple:
    """Create an action defining tuple
    """
    result = [name, callback, _optionsDict(**options)]
    if checkEnabled:
        result.append(checkEnabled)
    return tuple(result)


class Menu(list):
    """A class representing a menu definition
    """
    def __init__(self, name, *items, checkEnabled: CallableOrNone = None):
        super().__init__(items)
        self.name = name
        self.checkEnabled: CallableOrNone = checkEnabled
        self.fillCallable: CallableOrNone = None


class DynamicMenu(Menu):
    """A class representing a dynamic menu definition
    """
    def __init__(self, name, *items, checkActive: Callable = None, fillCallable: Callable = None):
        super().__init__(name, *items, checkEnabled=checkActive)
        self.fillCallable = fillCallable


def getMenuDefs():
    """:return The MenuDefs (singleton) instance
    """
    app = getApplication()
    return MenusDefs(application=app)


@singleton
class MenusDefs(list):
    """A class (list) to implement the menu definitions and callback routines
    Used by MainWindow to initialise the menuBar
    """

    def __init__(self, application):
        super().__init__()
        self.application = application
        self._defineMenus()

    @property
    def project(self):
        return self.application.project

    @property
    def current(self):
        return self.application.current

    @property
    def mainWindow(self):
        return self.application.mainWindow

    @property
    def ui(self):
        return self.application.ui

    def _defineMenus(self):
        """Set up the menu specification.
        """
        app = self.application
        ui = self.application.ui

        # Populate self
        self.clear()
        self.extend([

    #-----------------------------------------------------------------------------------------
    # The actual Menu definitions
    #-----------------------------------------------------------------------------------------
    Menu(FILE_MENU,

         # Unicode U+2303, NOT the carrot on your keyboard.
         Action("New", self._newProjectCallback, shortcut='⌃n'),

         Separator(),
         Action("Open...", self._openProjectCallback, shortcut='⌃o'),  # Unicode U+2303
         DynamicMenu(FILE_OPEN_RECENT),
         Action("Load Data...", self._loadDataCallback, shortcut='ld'),

         Separator(),
         Action("Save", self._saveCallback, shortcut='⌃s', checkEnabled=_projectCanBeSaved),  # Unicode U+2303
         Action("Save As...", self._saveAsCallback, shortcut='sa'),

         Separator(),
         Menu("Import",
            Action("NEF File", self._importNefCallback, shortcut='in'),
            Action("NmrStar File", self._loadNMRStarFileCallback, shortcut='bi'),
        ),
         Menu("Export",
            Action("NEF File", self._exportNEFCallback, shortcut='ex'),
        ),

         Separator(),
         Menu(FILE_LAYOUT,
              Action("Save", self._saveLayoutCallback, checkEnabled=_projectCanBeSaved),
              Action("Save as...", self._saveLayoutAsCallback, checkEnabled=_projectCanBeSaved),

              Separator(),
              Action("Restore last", self._restoreLastSavedLayoutCallback),
              Action("Restore from file...", self._restoreLayoutFromFileCallback),

              Separator(),
              DynamicMenu(FILE_LAYOUT_OPEN_PREDEFINED),
              ),
         Action("Summary", self._showProjectSummaryPopup),

         Separator(),
         Action('Archive', self._archiveProjectCallback, checkEnabled=_projectCanBeSaved),
         Action('Restore From Archive...', self._restoreFromArchiveCallback, checkEnabled=_projectHasArchives),

         Separator(),
         Action("Preferences...", self._showApplicationPreferences, shortcut='⌃,'),

         Separator(),
         Action("Quit", self._quitCallback, shortcut='⌃q'),  # Unicode U+2303,
         ),

    Menu(EDIT_MENU,

        Action("Undo", self._undoCallback, shortcut='⌃z'),  # Unicode U+2303,
        Action("Redo", self._redoCallback, shortcut='⌃y'),  # Unicode U+2303,

        Separator(),
        Action("Cut", self._nyi, shortcut='⌃x', enabled=False),
        Action("Copy", self._nyi, shortcut='⌃c', enabled=False),
        Action("Paste", self._nyi, shortcut='⌃v', enabled=False),
        Action("Select all", self._nyi, shortcut='⌃a', enabled=False),
    ),

    Menu(VIEW_MENU,

         Action("Chemical Shift Table", self._showChemicalShiftTableCallback, shortcut='ct'),
         Action("NmrResidue Table", self._showNmrResidueTableCallback, shortcut='nt'),
         Action("Residue Table", self._showResidueTableCallback, checkEnabled=_projectHasChains),
         Action("Peak Table", self._showPeakTableCallback, shortcut='pt', checkEnabled=_projectHasSpectra),
         Action("Integral Table", self._showIntegralTableCallback, shortcut='it', checkEnabled=_projectHasSpectra),
         Action("Multiplet Table", self._showMultipletTableCallback, shortcut='mt', checkEnabled=_projectHasSpectra),
         Action("Data Table", self._showDataTableCallback, shortcut='dt'),

         Separator(),
         Action("Restraint Table", partial(app.showRestraintTable, selectFirstItem=True), shortcut='rt'),
         Action("Violation Table", partial(app.showViolationTable, selectFirstItem=True), shortcut='vt'),
         Action("Structure Table", partial(app.showStructureTable, selectFirstItem=True), shortcut='st'),
         Action("Restraint Analysis Inspector", self._showRestraintAnalysisInspectorCallback, shortcut='at'),

         Separator(),
         Action(VIEW_CHEMICAL_SHIFT_MAPPING, self._showChemicalShiftMappingCallback, shortcut='cm'),
         Action("Relaxation Analysis (Beta)", app.showRelaxationModule, shortcut='ra'),
         Action("Notes Editor", partial(app.showNotesEditor, selectFirstItem=True), shortcut='no'),

         Separator(),
         Menu("In Active SpectrumDisplay",

              Section("Show/Hide"),
              Action("Toolbar", self._toggleToolbarCallback, shortcut='tb'),
              Action("Spectrum Toolbar", self._toggleSpectrumToolbarCallback, shortcut='sb'),
              Action("Phasing Console", self._togglePhaseConsoleCallback, shortcut='pc'),
              Action("Crosshairs", self._toggleCrosshairCallback, shortcut='ch'),

              Section("Zoom"),
              Action("Set Zoom...", self._setZoomCallback, shortcut='sz'),
              Action("Reset", self._resetZoomCallback, shortcut='rz'),

              Section("New SpectrumDisplay with"),
              Action("Same Axes", self._copyStripCallback),
              Action("X-Y Axes Flipped", self._flipXYAxisCallback, shortcut='xy'),
              Action("X-Z Axes Flipped", self._flipXZAxisCallback, shortcut='xz'),
              Action("Y-Z Axes Flipped", self._flipYZAxisCallback, shortcut='yz'),
              Action("Axes Flipped...", self._flipArbitraryAxesCallback, shortcut='fa'),

              Section("Labels"),
              Action("Auto-arrange", self._arrangeLabelsCallback, shortcut='av'),
              Action("Reset", self._resetLabelsCallback, shortcut='rv'),

              checkEnabled=_hasActiveDisplay
         ),

         Separator(),
         DynamicMenu(VIEW_SHOW_MODULES, checkActive=_updateShowHideModules),
         Action("Show/hide Sidebar", self._toggleSidebarCallback,
                                     shortcut=' s', checkable=True, checked=True
         ),
         Action("Show/hide Python Console", self._toggleConsoleCallback,
                shortcut='  ', checkable=True, checked=True,
                checkEnabled=_updatePythonConsole
         ),
    ),

    Menu(SPECTRUM_MENU,

        Action(SPECTRUM_LOAD_SPECTRA, self._loadSpectraCallback, shortcut='ls'),
        # Action("Spectrum Groups...", self._spectrumGroupsCallback, shortcut ='ss'), # multiple edit temporarly disabled
        # Separator(),
        Action("Validate Paths...", self._validatePathsCallback, shortcut='vp', checkEnabled=_projectHasSpectra),
        Action("Set Experiment Types...", self._experimentTypesCallback, shortcut='et', checkEnabled=_projectHasSpectra),
        Action("Copy into Project...", self._copyToProjectCallback, checkEnabled=_projectHasSpectra),

        Separator(),
        Menu("Pick Peaks",
             Action("Pick 1D Peaks...", self._peakPick1DCallback, shortcut='p1', checkEnabled=_projectHasSpectra),
             Action("Pick nD Peaks...", self._peakPickNDCallback, shortcut='pp', checkEnabled=_projectHasSpectra),
             checkEnabled=_projectHasSpectra
             ),
        Action("Copy PeakList...", self._copyPeakListCallback, shortcut='cl', checkEnabled=_projectHasSpectra),
        Action("Copy Peaks...", self._copyPeaksCallback, shortcut='cp', checkEnabled=_projectHasPeaks),
        Action("Peak Collections...", self._peakCollectionsCallback, shortcut='sc', checkEnabled=_projectHasPeaks),
        Action("Estimate Peak Volumes...", self._estimateVolumesCallback, shortcut='ev', checkEnabled=_projectHasPeaks),
        Action("Estimate Current Peak Volumes", self._estimateCurrentVolumesCallback, shortcut='ec', checkEnabled=_projectHasPeaks),
        Action("Reorder PeakList Axes...", self._reorderPeakListAxesCallback, shortcut='rl', checkEnabled=_projectHasSpectra),

        Separator(),
        Action("Pseudo-Spectrum to SpectrumGroup...", self._pseudoSpectrumCallback, checkEnabled=_projectHasSpectra),
        Action("Make Projection...", self._makeProjectionCallback, shortcut='pj', checkEnabled=_projectHasSpectra),
        Action("Convert...", self._convertSpectrumCallback, checkEnabled=_projectHasSpectra),

        Separator(),
        Action("Make Strip Plot...", ui.makeStripPlot, shortcut='sp', checkEnabled=_projectHasSpectra),
        Action("Print to File...", self._printToFileCallback, shortcut='⌃p', checkEnabled=_projectHasSpectra),

    ),

    Menu(MOLECULES_MENU,

         Action("New Chain...", self._createChainCallback),
         Action("New Chain from FASTA...", self._loadDataCallback),

         Separator(),
         Action("Load ChemComp from Xml...", self._loadDataCallback),
         Action("Edit Molecular Bonds...", self._editMolecularBondsCallback, checkEnabled=_projectHasChains),
         # Action("Inspect...", self.inspectMolecule, enabled=False),

         Separator(),
         Action("Show Residue Information", self._showResidueInformationCallback, shortcut='ri', checkEnabled=_projectHasChains),
         Action("Show Reference Chemical Shifts", self._showReferenceChemicalShiftsCallback, shortcut='rc'),

         ),

    Menu(MACRO_MENU,

        Action("New Macro Editor", self._showMacroEditorCallback, shortcut='nm'),

        Separator(),
        Action("Open User Macro...", self._openMacroCallback, shortcut='om'),
        Action("Open CCPN Macro...", partial(self._openMacroCallback, directory=macroPath)),

        Separator(),
        Action("Run...", self._runMacroCallback, shortcut='rm'),
        DynamicMenu(MACRO_RUN_RECENT),
        DynamicMenu(MACRO_RUN_CCPN),

        Separator(),
        Action("Define Macro Shortcuts...", self._defineUserShortcutsCallback, shortcut='du'),

    ),

    Menu(PLUGINS_MENU,

        DynamicMenu(CCPN_PLUGINS),
        DynamicMenu(USER_PLUGINS),

        Separator(),
        Action("Reload", app._reloadPlugins),

    ),

    Menu(HELP_MENU,

        DynamicMenu(HELP_TUTORIALS),
        DynamicMenu(HELP_HOWTOS),

        Section('Handies'),
        Action("Tip of the Day", partial(app._displayTipOfTheDay, standalone=True)),
        Action("Key Concepts", app._displayKeyConcepts),
        Action("Show Shortcuts", self._showShortcuts),

        Section('CCPN web pages'),
        Action("Homepage", self._showAboutCcpn),
        Action("V3 Forum", self._showForum),
        Action("CcpNmr API Documentation", self._showVersion3Documentation),

        Section('Programme'),
        # Action("Inspect Code...", self.showCodeInspectionPopup, shortcut='gv', enabled=False),
        # Action("Show Issues...", self.showIssuesList),
        Action("Check for Updates...", ui._checkForUpdates),
        Action("Register...", self._showRegisterPopup),
        Action("Show License...", self._showCcpnLicense),
        Action("About CcpNmr V3...", self._showAboutPopup),

    ),

    #-----------------------------------------------------------------------------------------
    ])  # end extend

        # Development Menu
        _devMenu = Menu(DEVELOPMENT_MENU,
                        DynamicMenu(DEVELOPMENT_DEBUG),
        )
        # optionally add development menu before Help menu
        if app._isInDebugMode:
            self.insertBefore([HELP_MENU], menuDef=_devMenu)

    #-----------------------------------------------------------------------------------------
    # callback methods
    #-----------------------------------------------------------------------------------------

    def _nyi(self):
        """Not yet implemented"""
        MessageDialog.showNYI()

    #-----------------------------------------------------------------------------------------
    # File --> callback methods
    #-----------------------------------------------------------------------------------------
    def _loadDataCallback(self):
        """Call loadData from the menu and trap errors.
        """
        self.ui.loadData()

    def _newProjectCallback(self):
        """Callback for creating new project
        """
        self.ui.newProject()

    def _openProjectCallback(self):
        """
        Opens a OpenProject dialog box if project directory is not specified.
        Loads the selected project.
        """
        self.ui.loadProject()

    def _importNefCallback(self):
        """menu callback; use ui.loadData to do the lifting
        """
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader

        self.ui.loadData(formatFilter=(NefDataLoader.dataFormat,))

    def _exportNEFCallback(self):
        """
        Export the current project as a Nef file
        Temporary routine because I don't know how else to do it yet
        """
        from ccpn.ui.gui.popups.ExportNefPopup import ExportNefPopup
        from ccpn.framework.lib.ccpnNef.CcpnNefIo import NEFEXTENSION

        _path = aPath(self.application.preferences.general.userWorkingPath or '~').filepath / (
                    self.project.name + NEFEXTENSION)
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
        includeOrphans = flags['includeOrphans']

        self.project.exportNef(nefPath,
                               overwriteExisting=True,
                               skipPrefixes=skipPrefixes,
                               expandSelection=expandSelection,
                               includeOrphans=includeOrphans,
                               pidList=pidList)

    def _loadNMRStarFileCallback(self):
        """menu callback; use ui.loadData to do the lifting
        """
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader

        self.ui.loadData(formatFilter=(StarDataLoader.dataFormat,))

    def _saveCallback(self):
        """The project save callback"""
        if self.project.isTemporary:
            # if temporary then use the saveAs dialog
            self.ui.saveProjectAs()

        else:
            self.application.saveProject()

    def _saveAsCallback(self):
        """Opens save Project as dialog box and saves project to path specified
        in the file dialog.
        """
        self.ui.saveProjectAs()

    def _archiveProjectCallback(self):

        if (path := self.application.saveToArchive()) is None:
            MessageDialog.showInfo('Archive Project',
                                   'Unable to archive Project')

        else:
            MessageDialog.showInfo('Archive Project',
                                   'Project archived to %s' % path)
            self.ui.mainWindow._updateRestoreArchiveMenu()

    def _restoreFromArchiveCallback(self):
        """Restore a project from archive
        """
        archivesDirectory = aPath(self.project.path) / CCPN_ARCHIVES_DIRECTORY
        _filter = '*.tgz'
        dialog = ArchivesFileDialog(parent=self.ui.mainWindow,
                                    acceptMode='select',
                                    directory=archivesDirectory,
                                    fileFilter=_filter)
        dialog._show()
        archivePath = dialog.selectedFile()

        if archivePath and \
                (newProject := self.application.restoreFromArchive(archivePath)) is not None:
            MessageDialog.showInfo('Restore from Archive',
                                   'Project restored as %s' % newProject.path)

    def _saveLayoutCallback(self):
        Layout.updateSavedLayout(self.ui.mainWindow)
        getLogger().info('Layout saved')

    def _saveLayoutAsCallback(self):
        path = _getSaveLayoutPath(self.mainWindow)
        try:
            Layout.saveLayoutToJson(self.mainWindow, jsonFilePath=path)
            getLogger().info('Layout saved to %s' % path)
        except Exception as es:
            getLogger().warning('Impossible to save layout. %s' % es)

    def _restoreLastSavedLayoutCallback(self):
        self.ui.mainWindow.moduleArea._closeAll()
        Layout.restoreLayout(self.ui.mainWindow, self.application.layout, restoreSpectrumDisplay=True)

    def _restoreLayoutFromFileCallback(self):
        if (path := _getOpenLayoutPath(self.mainWindow)) is None:
            return
        self.application._restoreLayoutFromFile(path)

    def _showProjectSummaryPopup(self):
        """Show the Project summary popup.
        """
        from ccpn.ui.gui.popups.ProjectSummaryPopup import ProjectSummaryPopup

        popup = ProjectSummaryPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, modal=True)
        # popup.show()
        # popup.raise_()
        popup.exec_()

    def _showApplicationPreferences(self):
        """
        Displays Application Preferences Popup.
        """
        from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup

        popup = PreferencesPopup(parent=self.ui.mainWindow._widget, mainWindow=self.ui.mainWindow,
                                 preferences=self.application.preferences)
        popup.exec_()

    def _quitCallback(self, event=None):
        """
        Saves application preferences. Displays message box asking user to save project or not.
        Closes Application.
        """
        self.ui.mainWindow._closeEvent(event=event)

    #-----------------------------------------------------------------------------------------
    # Edit --> callback methods
    #-----------------------------------------------------------------------------------------

    def _undoCallback(self):
        """Callback for Edit --> Undo
        """
        self.application.undo()

    def _redoCallback(self):
        """Callback for Edit --> Redo
        """
        self.application.redo()

    #-----------------------------------------------------------------------------------------
    # Spectra --> callback methods
    #-----------------------------------------------------------------------------------------

    def _loadSpectraCallback(self):
        """Load all the spectra callback
        """
        self.ui.loadSpectra()

    def _experimentTypesCallback(self):
        """
        Displays experiment type popup.
        """
        if not self.project.spectra:
            getLogger().warning('Experiment Type Selection: Project has no Spectra.')
            MessageDialog.showWarning('Experiment Type Selection', 'Project has no Spectra.')
        else:
            from ccpn.ui.gui.popups.ExperimentTypePopup import ExperimentTypePopup

            popup = ExperimentTypePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _validatePathsCallback(self, spectra=None, defaultSelected=None):
        """
        Displays validate spectra popup.
        """
        if not self.project.spectra:
            getLogger().warning('Validate Spectrum Paths Selection: Project has no Spectra.')
            MessageDialog.showWarning('Validate Spectrum Paths Selection', 'Project has no Spectra.')
        else:
            from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraPopup

            popup = ValidateSpectraPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, spectra=spectra,
                                         defaultSelected=defaultSelected)
            popup.exec_()

    def _convertSpectrumCallback(self):
        """Show the convertToHdf5 popup
        """
        if not self.project.spectra:
            getLogger().warning('Convert spectra: Project has no Spectra.')
            MessageDialog.showWarning('Convert spectra', 'Project has no Spectra.')
        else:
            from ccpn.ui.gui.popups.ConvertToHdf5Popup import ConvertToHdf5Popup

            popup = ConvertToHdf5Popup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _copyToProjectCallback(self):
        """Callback for Spectrum -> Copy into Project
        """
        title = 'Copy Spectra into Project'
        if len(self.project.spectra) == 0:
            MessageDialog.showWarning(title, 'No spectra in project', parent=self.mainWindow)
            return

        _spectra = [sp for sp in self.project.spectra if
                    sp.hasValidPath() and not sp._isInside and not sp.isEmptySpectrum()]
        if len(_spectra) == 0:
            MessageDialog.showWarning(title, 'There are no spectra to be copied', parent=self.mainWindow)
            return

        _size = '%.1f' % (sum([sp.dataSource.expectedFileSizeInBytes for sp in _spectra]) / (1024 * 1024))
        if len(_spectra) == 1:
            _msg = f'1 spectrum ({_size} MB) to be copied'
        else:
            _msg = f'{len(_spectra)} spectra ({_size} MB) to be copied'
        ok = MessageDialog.showOkCancel(title, _msg, parent=self.mainWindow)
        if ok:
            self.project.copySpectraToProject()

    def _reorderPeakListAxesCallback(self):
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

    def _peakPick1DCallback(self):
        """
        Callback to display Peak Picking 1D Popup.
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
                getLogger().warning('Peak Picking: Project has no 1d Spectra.')
                MessageDialog.showWarning('Peak Picking', 'Project has no 1d Spectra.')

    def _peakPickNDCallback(self):
        """
        Callback to display Peak Picking ND Popup.
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
                getLogger().warning('Peak Picking: Project has no Nd Spectra.')
                MessageDialog.showWarning('Peak Picking', 'Project has no Nd Spectra.')

    def _copyPeakListCallback(self):
        """Callback to display CopyPeakList popup
        """
        if not self.project.peakLists:
            txt = 'Project has no PeakList\'s. Peak Lists cannot be copied'
            getLogger().warning(txt)
            MessageDialog.showWarning('Cannot perform a copy', txt)
            return
        else:
            from ccpn.ui.gui.popups.CopyPeakListPopup import CopyPeakListPopup

            popup = CopyPeakListPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _copyPeaksCallback(self):
        """Callback to display CopyPeaks popup
        """
        if not self.project.peaks:
            getLogger().warning('Project has no Peaks: Peaks cannot be copied')
            MessageDialog.showWarning('Project has no Peaks', 'Peaks cannot be copied')
            return
        else:
            from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

            popup = CopyPeaks(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            peaks = self.current.peaks
            popup._selectPeaks(peaks)
            popup.exec_()

    def _peakCollectionsCallback(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Spectrum groups cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Spectrum groups cannot be displayed')
        else:
            from ccpn.ui.gui.popups.SeriesPeakCollectionPopup import SeriesPeakCollectionPopup

            popup = SeriesPeakCollectionPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()
            # return popup

    def _estimateVolumesCallback(self):
        """
        Displays Estimate Volumes Popup.
        """
        self.mainWindow._showEstimateVolumesPopup()

    def _estimateCurrentVolumesCallback(self):
        """
        Calculate volumes for the currently selected peaks
        """
        self.mainWindow._showEstimateCurrentVolumesPopup()

    def _spectrumGroupsCallback(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Spectrum groups cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Spectrum groups cannot be displayed')

        else:
            from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor

            if not self.project.spectrumGroups:
                #GST This seems to have problems MessageDialog wraps it which looks bad...
                # MessageDialog.showWarning('Project has no Spectrum Groups.',
                #                           'Create them using:\nSidebar → SpectrumGroups → <New SpectrumGroup>\n ')
                SpectrumGroupEditor(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, editMode=False).exec_()

            else:
                SpectrumGroupEditor(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, editMode=True,
                                    obj=self.project.spectrumGroups[0]).exec_()

    def _pseudoSpectrumCallback(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Pseudo Spectrum to SpectrumGroup Popup cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.',
                                      'Pseudo Spectrum to SpectrumGroup Popup cannot be displayed')
        else:
            from ccpn.ui.gui.popups.PseudoToSpectrumGroupPopup import PseudoToSpectrumGroupPopup

            popup = PseudoToSpectrumGroupPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _makeProjectionCallback(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Make Projection Popup cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Make Projection Popup cannot be displayed')
        else:
            from ccpn.ui.gui.popups.SpectrumProjectionPopup import SpectrumProjectionPopup

            popup = SpectrumProjectionPopup(parent=self.mainWindow._widget, mainWindow=self.mainWindow)
            popup.exec_()

    def _printToFileCallback(self):
        """Show the print spectrumDisplay dialog
        """
        from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup

        if len(self.mainWindow.spectrumDisplays) == 0:
            MessageDialog.showWarning('', 'No SpectrumDisplay found')
        else:
            exportDialog = ExportStripToFilePopup(parent=self.mainWindow._widget,
                                                  mainWindow=self.mainWindow,
                                                  strips=self.project.strips,
                                                  selectedStrip=self.current.strip
                                                  )
            exportDialog.exec_()

    #-----------------------------------------------------------------------------------------
    # View -->
    #-----------------------------------------------------------------------------------------
    def _showChemicalShiftTableCallback(self):
        """Callback for showing ChemicalShiftTable module
        """
        self.ui.showChemicalShiftTable()

    def _showNmrResidueTableCallback(self):
        """Callback for showing NmrResidueTable module
        """
        self.ui.showNmrResidueTable()

    def _showResidueTableCallback(self):
        """Callback for showing ResidueTable module
        """
        self.ui.showResidueTable()

    def _showPeakTableCallback(self):
        """Callback for showing PeakTable module
        """
        self.ui.showPeakTable()

    def _showIntegralTableCallback(self):
        """Callback for showing IntegralTable module
        """
        self.ui.showIntegralTable()

    def _showMultipletTableCallback(self):
        """Callback for showing MultipletTable module
        """
        self.ui.showMultipletTable()

    def _showDataTableCallback(self):
        """Callback for showing DataTable module
        """
        self.ui.showDataTable()

    def _toggleToolbarCallback(self):
        if self.current.strip is not None:
            self.current.strip.spectrumDisplay.toggleToolbar()
        else:
            getLogger().warning('Toggle toolbar: No strip selected')
            MessageDialog.showWarning('Toggle toolbar', 'No strip selected')

    def _toggleSpectrumToolbarCallback(self):
        if self.current.strip is not None:
            self.current.strip.spectrumDisplay.toggleSpectrumToolbar()
        else:
            getLogger().warning('Toggle spectrum toolbar: No strip selected')
            MessageDialog.showWarning('Toggle spectrum toolbar', 'No strip selected')

    def _togglePhaseConsoleCallback(self):
        if self.current.strip is not None:
            self.current.strip.spectrumDisplay.togglePhaseConsole()
        else:
            getLogger().warning('Toggle pahsing console: No strip selected')
            MessageDialog.showWarning('Toggle phasing console', 'No strip selected')

    def _setZoomCallback(self):
        if self.current.strip is not None:
            self.current.strip._setZoomPopup()
        else:
            getLogger().warning('Zoom: No strip selected')
            MessageDialog.showWarning('Zoom', 'No strip selected')

    def _resetZoomCallback(self):
        if self.current.strip is not None:
            self.current.strip.resetZoom()
        else:
            getLogger().warning('Reset zoom: No strip selected')
            MessageDialog.showWarning('Reset zoom', 'No strip selected')

    def _copyStripCallback(self):
        if self.current.strip is not None:
            self.current.strip.copyStrip()
        else:
            getLogger().warning('Copy strip: No strip selected')
            MessageDialog.showWarning('Copy strip', 'No strip selected')

    def _arrangeLabelsCallback(self):
        """Auto-arrange the peak/multiplet labels to minimise any overlaps.
        """
        if (strp := self.current.strip) is None:
            getLogger().warning('Arrange labels: No strip selected')
            MessageDialog.showWarning('Arrange Labels', 'No strip selected')
        else:
            strp.spectrumDisplay.arrangeLabels()

    def _resetLabelsCallback(self):
        """Reset arrangement of peak/multiplet labels.
        """
        if (strp := self.current.strip) is None:
            getLogger().warning('Reset labels: No strip selected')
            MessageDialog.showWarning('reset Labels', 'No strip selected')
        else:
            strp.spectrumDisplay.resetLabels()

    def _flipXYAxisCallback(self):
        """Callback to flip XY axes
        """
        if self.current.strip is not None:
            self.current.strip.flipXYAxis()
        else:
            getLogger().warning('Flip XY axes: No strip selected')
            MessageDialog.showWarning('Flip XY axes', 'No strip selected')

    def _flipXZAxisCallback(self):
        """Callback to flip XZ axes
        """
        if self.current.strip is not None:
            self.current.strip.flipXZAxis()
        else:
            getLogger().warning('Flip XZ axes: No strip selected')
            MessageDialog.showWarning('Flip XZ axes', 'No strip selected')

    def _flipYZAxisCallback(self):
        """Callback to flip YZ axes
        """
        if self.current.strip is not None:
            self.current.strip.flipYZAxis()
        else:
            getLogger().warning('Flip YZ axes: No strip selected')
            MessageDialog.showWarning('Flip YZ axes', 'No strip selected')

    def _flipArbitraryAxesCallback(self):
        """Callback to flip arbitrary axes
        """
        if self.current.strip is not None:
            self.ui._flipArbitraryAxes(strip=self.current.strip, usePosition=False)
        else:
            getLogger().warning('Flip arbitrary axes: No strip selected')
            MessageDialog.showWarning('Flip arbitrary axes', 'No strip selected')

    def _toggleSidebarCallback(self):
        """Toggles whether the sidebar is displayed.
        """
        self.mainWindow._toggleSidebar()

    def _toggleConsoleCallback(self):
        """Toggles whether python console is displayed.
        """
        self.mainWindow._toggleConsole()

    def _toggleCrosshairCallback(self):
        """Toggles whether crosshairs are displayed in all SpectrumDisplays.
        """
        self.mainWindow.toggleCrosshair()

    def _showRestraintAnalysisInspectorCallback(self):
        """Callback for showing the RestrainAnalysis inspector
        """
        self.ui.showRestraintAnalysisInspector()

    def _showChemicalShiftMappingCallback(self):
        """Callback to show Chemical shift mapping module
        """
        self.ui.showChemicalShiftMapping()

    #-----------------------------------------------------------------------------------------
    # Molecules -->
    #-----------------------------------------------------------------------------------------

    def _createChainCallback(self):
        """
        Displays sequence creation popup.
        """
        from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup

        popup = CreateChainPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
        popup.exec_()

    # def inspectMolecule(self):
    #     pass

    def _editMolecularBondsCallback(self):
        """Callback to display the molecular-bonds popup.
        """
        from ccpn.ui.gui.popups.MolecularBondsPopup import MolecularBondsPopup

        popup = MolecularBondsPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()

    def _showResidueInformationCallback(self):
        """Callback for showing residue information Module
        """
        self.ui.showResidueInformation()

    def _showReferenceChemicalShiftsCallback(self):
        """Callback to show reference chemical shifts
        """
        self.ui.showReferenceChemicalShifts()

    #-----------------------------------------------------------------------------------------
    # Macro -->
    #-----------------------------------------------------------------------------------------

    def _showMacroEditorCallback(self):
        """Displays macro editor. Just handing down to ui for now
        """
        self.ui.newMacroEditor()

    def _openMacroCallback(self, directory=None):
        """ Select macro file and on MacroEditor.
        """
        from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog

        mainWindow = self.ui.mainWindow
        dialog = MacrosFileDialog(parent=mainWindow, acceptMode='open', fileFilter='*.py', directory=directory)
        dialog._show()
        path = dialog.selectedFile()
        if path is not None:
            self.ui.newMacroEditor(path=path)

    def _runMacroCallback(self):
        """Callback for running macro
        """
        self.ui.runMacro()

    def _defineUserShortcutsCallback(self):
        from ccpn.ui.gui.popups.ShortcutsPopup import ShortcutsPopup

        ShortcutsPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()

    #-----------------------------------------------------------------------------------------
    # Help -->
    #-----------------------------------------------------------------------------------------

    def _showVersion3Documentation(self):
        """Displays CCPN wrapper documentation in a module.
        """
        from ccpn.framework.PathsAndUrls import ccpnDocumentationUrl, documentationPath

        if self.application.preferences.appearance.useOnlineDocumentation:
            self.ui._showHtmlFile("Analysis Version-3 Documentation", ccpnDocumentationUrl)
        else:
            self.ui._showHtmlFile("Analysis Version-3 Documentation", documentationPath)

    def _showForum(self):
        """Displays Forum in a module.
        """
        from ccpn.framework.PathsAndUrls import ccpnForum

        self.ui._showHtmlFile("Analysis Version-3 Forum", ccpnForum)

    def _showShortcuts(self):
        from ccpn.framework.PathsAndUrls import shortcutsPath

        self.ui._systemOpen(shortcutsPath)

    def _showAboutPopup(self):
        from ccpn.ui.gui.popups.AboutPopup import AboutPopup

        popup = AboutPopup(parent=self.ui.mainWindow)
        popup.exec_()

    def _showAboutCcpn(self):
        from ccpn.framework.PathsAndUrls import ccpnUrl

        self.ui._showHtmlFile("About CCPN", ccpnUrl)

    def _showRegisterPopup(self):
        """Open the registration popup
        """
        self.ui._registerDetails()

    def _showCcpnLicense(self):
        from ccpn.framework.PathsAndUrls import ccpnLicenceUrl

        self.ui._showHtmlFile("CCPN Licence", ccpnLicenceUrl)

    #-----------------------------------------------------------------------------------------
    # Inactive
    #-----------------------------------------------------------------------------------------

    def _showIssuesList(self):
        from ccpn.framework.PathsAndUrls import ccpnIssuesUrl

        self.ui._showHtmlFile("CCPN Issues", ccpnIssuesUrl)

    def _showLicense(self):
        from ccpn.framework.PathsAndUrls import licensePath

        self.ui._showHtmlFile("CCPN Licence", licensePath)

    def _showSubmitMacroPopup(self):
        """Open the submit macro popup
        """
        from ccpn.ui.gui.popups.SubmitMacroPopup import SubmitMacroPopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            submitMacroPopup = SubmitMacroPopup(parent=self.ui.mainWindow)
            submitMacroPopup.show()
            submitMacroPopup.raise_()

        else:
            MessageDialog.showWarning('Submit Macro',
                                      'Could not connect to the server, please check your internet connection.')

    def _showFeedbackPopup(self):
        """Open the submit feedback popup
        """
        from ccpn.ui.gui.popups.FeedbackPopup import FeedbackPopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():

            # this is non-modal so you can copy/paste from the project as required
            feedbackPopup = FeedbackPopup(parent=self.ui.mainWindow)
            feedbackPopup.show()
            feedbackPopup.raise_()

        else:
            MessageDialog.showWarning('Submit Feedback',
                                      'Could not connect to the server, please check your internet connection.')

    #-----------------------------------------------------------------------------------------
    # Implementation methods
    #-----------------------------------------------------------------------------------------

    def insertAfter(self, menuKeys: list, menuDef: tuple):
        """Insert menuDef after the menu/action/section defined by menuKeys, i.e. a list
        of names or indices that recursively define the menu;
        e.g. ['File', 'New']

        NB. to get something at the end, use -1; e.g. at the end of 'File' menu:
            insertAfter(['File', -1], ....)

        :param menuKeys: a list of names or position-indices defining the menu/action/section
        :param menuDef: a list define the menu/action/separator/section to be inserted
        """
        _indx, currentMenu = self._findMenu(menuKeys=menuKeys)
        if _indx < 0:
            # Correct the _indx to positive numbers, i.e. -1 is last item
            _indx += len(currentMenu)
        currentMenu.insert(_indx + 1, menuDef)

    def insertBefore(self, menuKeys: list, menuDef: tuple):
        """Insert menuDef before the menu/action/section defined by menuKeys, i.e. a list
        of names or indices that recursively define the menu;
        e.g. ['File', 'New']

        NB. to get something as the first menu/action, use 0; e.g. at the start of 'File' menu:
            insertBefore(['File', 0], ....)

        :param menuKeys: a list of names or position-indices defining the menu/action/section
        :param menuDef: a list define the menu/action/separator/section to be inserted
        """
        _indx, currentMenu = self._findMenu(menuKeys=menuKeys)
        if _indx < 0:
            # Correct the _indx to positive numbers, i.e. -1 is last item
            _indx += len(currentMenu)
        currentMenu.insert(_indx, menuDef)

    def _findMenu(self, menuKeys: list, currentMenu=None) -> tuple[int, list]:
        """(Recursively) find menu/action/section defined by menuKeys, i.e. a list
        of names or indices (0-based) that recursively define the menu;
        e.g. ['File', 'New'] or ['File', 3]

        :param menuKeys: a list of names or position-indices defining the menu/action
        :param currentMenu: a list to be used for the recursion; defaults to None at initialisation

        :return (indx, currentMenu) tuple: the index and the menu for which menu[indx] was defined
                                           by the menuKeys list
                                           
        :raise ValueError for invalid arguments, or RuntimeError if menus defines a non
               existing menu/action.
        """
        if not isinstance(menuKeys, list) or len(menuKeys) == 0:
            raise ValueError(f'_findMenu: invalid menus {menuKeys}')

        if currentMenu is None:
            currentMenu = self

        # find the index of first key of menuKeys
        key = menuKeys[0]

        if isinstance(key, str):
            # key is a string:
            _indx = -1
            for _ii, item in enumerate(currentMenu):
                if isinstance(item, Menu):
                    if item.name == key:
                        _indx = _ii
                        break
                elif isinstance(item, tuple):
                    # old tuple-based definition
                    _name = item[0] if len(item) > 0 else None
                    if _name == key:
                        _indx = _ii
                        break
                else:
                    raise RuntimeError(f'_findMenu: invalid menu-item {item!r}')

        elif isinstance(key, int):
            # key is an int, ie. an index
            _indx = key if key < len(currentMenu) else -1

        else:
            raise RuntimeError(f'_findMenu: invalid menu-key {key!r}')

        # check the index; -1 indicates it was not found
        if _indx == -1:
            raise RuntimeError(f'_findMenu: menu-key {key!r} not found')

        # recurse if we are not done
        if len(menuKeys) > 1:
            _menu = currentMenu[_indx]
            if isinstance(_menu, tuple):
                # old definitions
                _menu = _menu[1]
            return self._findMenu(menuKeys=menuKeys[1:], currentMenu=_menu)

        return _indx, currentMenu

    def __str__(self):
        return f'<MenuDef of {self.application}>'

    __repr__ = __str__


# end class #-----------------------------------------------------------------------------


from ccpn.util.DataEnum import DataEnum


class NodeType(DataEnum):
    UNDEFINED = 0, 'Undefined'
    SEPARATOR = 1, 'Separator'
    SECTION = 2, 'Section'
    MENU = 3, 'Menu'
    ACTION = 4, 'Action'


class MenuNode(Tree):
    """Just a class to define the MenuNode tree structure to store the MenuWidget and
    ActionWidget objects
    Has dict like behavior to facilitate lookup,
    e.g. assume a myMenus (nested) object from a MenuDefs instance:

       myMenus['File']['New'] would yield the corresponding MenuNode for that Menu

    """

    def __init__(self, parent,
                 name: str, nodeType: NodeType, isDynamic: bool = False,
                 callback: CallableOrNone = None, options: dict = {}):
        """
        Initialise the node
        :param parent: parent node; None denotes root
        :param name: name of the node
        :param nodeType: type of the node
        :param isDynamic: flag to indicate a dynamic node
        :param callback: callback function (for an Action-node)
        :param options: (keyword,value) options to the Action
        """

        # Make node initially as stand-alone,
        # to be added after all init's are completed
        Tree.__init__(self, parent=None)

        self.name = name
        self.nodeType = nodeType
        self.callback = callback
        self.options = options

        # Menu nodes can be dynamically filled
        self.isDynamic = isDynamic
        self.dynamicCallback = None

        # Action's can be checked for needing enabling
        self.checkEnable = False
        self.checkEnableCallback = None

        # The widget associated with this node
        self.widget = None

        # Add to tree, if parent is not None, i.e. this node is not the root
        if parent is not None:
            parent._addChild(self)

    #-----------------------------------------------------------------------------------------

    @property
    def parent(self):
        return self._parent

    @property
    def level(self) -> int:
        """
        :return the level of the MenuNode in the nested structure (root has level 0)
        """
        return len(self.anchestors())

    @property
    def isSeparator(self) -> bool:
        """:return True if node is a separator
        """
        return self.nodeType == NodeType.SEPARATOR

    @property
    def isSection(self) -> bool:
        """:return True if node is a section
        """
        return self.nodeType == NodeType.SECTION

    @property
    def isMenu(self) -> bool:
        """:return True if node is a menu
        """
        return self.nodeType == NodeType.MENU

    @property
    def isAction(self) -> bool:
        """:return True if node is a action
        """
        return self.nodeType == NodeType.ACTION

    #-----------------------------------------------------------------------------------------

    def setDynamicNode(self, callback: Callable):
        """Make MenuNode a dynamically updated one, defining callback when it is about to show
        :param callback: a function with signature callback(node:MenuNode) -> list
        """
        if not self.isMenu:
            raise RuntimeError(f'setDynamicNode: invalid for {self}')
        self.isDynamic = True
        self.dynamicCallback = callback

    def clearNode(self):
        """For a dynamic Menu node only:
        clear self; clear and remove all descendant nodes
        """
        if not (self.isMenu and self.isDynamic):
            raise RuntimeError(f'clearNode: Cannot clear {self}')

        if self.widget:
            self.widget.clear()
        # remove the descendant nodes;
        self._removeAllChildren()

    def setCheckedNode(self, callback):
        """Make node a checked one, defining callback for checking by parent
        param callback: a function with signature callback(node:MenuNode) -> bool
        """
        self.checkEnable = True
        self.checkEnableCallback = callback

    def setEnabled(self, flag):
        """Set the enabled status of widget to flag
        """
        if self.widget:
            self.widget.setEnabled(flag)

    # def _aboutToShow(self, callback):
    #     """Connect the aboutToShow signal of widget of self to callback.
    #     Use partial to add self to callback
    #     """
    #     if not self.isMenu or self.widget is None:
    #         raise RuntimeError(f'_aboutToShow: Cannot connect to signal')
    #     self.widget.aboutToShow.connect(partial(callback, self))

    #-----------------------------------------------------------------------------------------

    def addNode(self, name, **kwds):
        """Syntactically sugar to add a node to self.
        Node is defined by name and **kwds (see __init__)
        :return The newly created MenuNode instance
        """
        _node = MenuNode(parent=self, name=name, **kwds)
        return _node

    @classmethod
    def newFromList(cls, theList, parent=None, name='menuRoot'):
        """Create new Menu node, (Recursively) traverse theList with Menu definitions,
        adding items in theList as child-nodes.

        :param thelist: a list of Menu definitions
        :param parent: the parent Node; None indicates the result to be root
        :param name: name of the resulting node

        :return a the newly created MenuNode instance
        """
        if not isinstance(theList, list):
            raise ValueError(f'newFromList: expected list; got {type(theList)}')

        isDynamic = (len(theList) == 0)
        node = cls(parent=parent, name=name, nodeType=NodeType.MENU, isDynamic=isDynamic)
        node.addNodesFromList(theList)
        return node

    def addNodesFromList(self, theList) -> list:
        """(Recursively) Traverse theList with Menu definitions,
        adding items in theList as child-nodes.
        The method effectively parses the menu-definitions list, as defined by the
        MenuDefs class above

        :param theList: a list of Menu tuple definitions (see also MenuDefs class)

        :return A list of nodes added
        """

        def _str120(val):
            """truncate str(val) to 120 chars
            """
            _tmp = str(val)
            if len(_tmp) > 120:
                _tmp = f'{_tmp[0:54]}    ....    {_tmp[-54:]}'
            return _tmp

        if not isinstance(theList, list):
            raise ValueError(f'addNodesFromList to {self}: expected list; got {type(theList)}')

        result = []
        separatorIndex = 0  # This gives each separator a unique name
        for item in theList:
            if not isinstance(item, (tuple, Menu)):
                raise RuntimeError(f'addNodesFromList to {self}: Invalid menu definition: \n>>> {_str120(item)}')

            if isinstance(item, Menu):
                node = self.newFromList(theList=item, parent=self, name=item.name)
                result.extend(node.allObjects())
                if item.checkEnabled is not None:
                    node.setCheckedNode(item.checkEnabled)

            elif len(item) == 0:
                # A separator
                name = f'Separator_{separatorIndex}'
                node = self.addNode(name=name, nodeType=NodeType.SEPARATOR)
                result.append(node)
                separatorIndex += 1

            elif len(item) == 1:
                # A section
                name = item[0]
                node = self.addNode(name=name, nodeType=NodeType.SECTION)
                result.append(node)

            # elif len(item) in (2, 4) and isinstance(item[1], list):
            #     # a (sub-)Menu
            #     name = item[0]
            #     val = item[1]
            #     node = self.newFromList(theList=val, parent=self, name=name)
            #
            #     checkCallback = item[3] if len(item) >= 4 else None
            #     if checkCallback is not None:
            #         node.setCheckedNode(checkCallback)
            #
            #     result.extend(node.allObjects())

            elif len(item) in (2, 3, 4) and callable(item[1]):
                # An action
                name = item[0]
                callback = item[1]
                options = item[2] if len(item) >= 3 else {}
                # Convert any list,tuple of key,value pairs to dict
                if isinstance(options, (list, tuple)):
                    options = dict(options)

                node = self.addNode(name=name, nodeType=NodeType.ACTION, callback=callback, options=options)

                checkCallback = item[3] if len(item) >= 4 else None
                if checkCallback is not None:
                    node.setCheckedNode(checkCallback)

                result.append(node)

            else:
                # this should not happen
                raise RuntimeError(
                    f'addNodesFromList to {self}: We should not be here! Invalid menu definition: \n>>> {_str120(item)}')

        return result

    #-----------------------------------------------------------------------------------------
    # implement some dict-like behaviour
    #-----------------------------------------------------------------------------------------

    @property
    def _childrenAsDict(self):
        """:return self._children as a dict of (name, child) key, value pairs
        """
        return dict([(child.name, child) for child in self._children])

    def keys(self) -> list:
        return list(self._childrenAsDict.keys())

    def items(self) -> list:
        return list(self._childrenAsDict.items())

    def values(self) -> list:
        return list(self._childrenAsDict.values())

    def __getitem__(self, key):
        _vals = self._childrenAsDict
        if key not in _vals:
            raise KeyError(f'key {key!r} not in {self}')
        return _vals[key]

    #-----------------------------------------------------------------------------------------

    def print(self):
        """
        print Tree of self with indentation
        """
        for node in self.allObjects():
            level = node.level
            tabs = '\t' * (level - 1) if level > 1 else ''
            if level == 1:
                tabs = '\n' + tabs
            print(
                f'{tabs}{node.name!r:25}  (level={node.level}, type={node.nodeType}, dynamic={node.isDynamic}) {node.options}')
            if node.isMenu and node.isDynamic and len(node._children) == 0:
                print(f'{tabs}\t>>> dynamically filled')

    def __str__(self):
        return f'<MenuNode: {self.name!r} (level={self.level}, type={self.nodeType}, dynamic={self.isDynamic}, checked={self.checkEnable})>'

    __repr__ = __str__


# end class #-----------------------------------------------------------------------------


class MenuManager(object):
    """A class to manage the Menus
    Works of a MenuNode Tree structure
    """

    def __init__(self, mainWindow, menuDefs):

        self.mainWindow = mainWindow
        self.menuBar = mainWindow._getMenuBarWidget()
        self.useNativeMenus = False

        # define self.application; project, current and ui are derived via properties
        self.application = mainWindow.application

        # define the MenuNode's tree
        self.menuNodes = MenuNode.newFromList(menuDefs)

        #-------------------------------------------------------------------------------------
        # define dynamic nodes
        #-------------------------------------------------------------------------------------

        # File->Open Recent
        _node = self.menuNodes[FILE_MENU][FILE_OPEN_RECENT]
        _node.setDynamicNode(callback=self._fillFileOpenRecentCallback)
        # File->Layout->Open pre-defined
        _node = self.menuNodes[FILE_MENU][FILE_LAYOUT][FILE_LAYOUT_OPEN_PREDEFINED]
        _node.setDynamicNode(callback=self._fillFilePredefinedLayoutsCallback)

        # View->Show Modules
        _node = self.menuNodes[VIEW_MENU][VIEW_SHOW_MODULES]
        _node.setDynamicNode(callback=self._fillViewShowModulesCallback)

        # Macro->Run Recent
        _node = self.menuNodes[MACRO_MENU][MACRO_RUN_RECENT]
        _node.setDynamicNode(callback=self._fillMacroRunRecentCallback)
        # Macro->Run CCPN
        _node = self.menuNodes[MACRO_MENU][MACRO_RUN_CCPN]
        _node.setDynamicNode(callback=self._fillMacroRunCCPNCallback)

        # Plugins->User plugins
        _node = self.menuNodes[PLUGINS_MENU][USER_PLUGINS]
        _node.setDynamicNode(callback=self._fillUserPluginsCallback)
        # Plugins->CCPN plugins
        _node = self.menuNodes[PLUGINS_MENU][CCPN_PLUGINS]
        _node.setDynamicNode(callback=self._fillCCPNPluginsCallback)

        # Help->Tutorials
        _node = self.menuNodes[HELP_MENU][HELP_TUTORIALS]
        _node.setDynamicNode(callback=self._fillHelpTutorialsCallback)
        # Help->Howto's
        _node = self.menuNodes[HELP_MENU][HELP_HOWTOS]
        _node.setDynamicNode(callback=self._fillHelpHowtosCallback)

        # Development->Debug
        if self.application._isInDebugMode:
            _node = self.menuNodes[DEVELOPMENT_MENU][DEVELOPMENT_DEBUG]
            _node.setDynamicNode(callback=self._fillDevelopmentDebugCallback)

    @property
    def project(self):
        """:return The Project instance
        """
        return self.application.project

    @property
    def current(self):
        """:return The Current instance
        """
        return self.application.current

    @property
    def ui(self):
        """:return The Ui instance
        """
        return self.application.ui

    #-----------------------------------------------------------------------------------------

    def makeMenus(self, node: MenuNode = None, useNativeMenus=False):
        """Use node to make its menu's; i.e. adding Menu/Action to node
        Recursively decent into its children
        :param node: a MenuNode starting point; default to self.menuNodes
        :param useNativeMenus: flag to use native menu's
        """
        if node is None:
            node = self.menuNodes

        if node.isRoot:
            # MenuNode root's widget is the MenuBar instance
            self.menuBar.clear()
            self.menuBar.setNativeMenuBar(useNativeMenus)
            self.useNativeMenus = useNativeMenus
            node.widget = self.menuBar

        else:
            # We are not root, so should have a parent with a widget
            if (_parent := node.parent) is None:
                raise RuntimeError(f'makeMenu: {node} has no parent')

            if _parent.widget is None:
                raise ValueError(f'makeMenu: {_parent} has no widget')

            if node.isAction:
                node.widget = ActionWidget(parent=_parent.widget, text=node.name,
                                           callback=node.callback, **node.options
                                          )
                _parent.widget.addAction(node.widget)

            elif node.isMenu:
                if node.level == 0:
                    raise RuntimeError(f'makeMenu: invalid {node} for level=0 ')

                elif node.level == 1:
                    # Adding to menuBar
                    node.widget = MenuWidget(parent=_parent.widget, title=node.name)
                    _parent.widget.addMenu(node.widget)

                # GWV: not quite sure why is needs this way, (i.e. different from addMenu
                # for menuBar, but it works)
                elif node.level > 1:
                    node.widget = _parent.widget.addMenu(node.name)

                # Always set callback for Menu nodes;
                node.widget.aboutToShow.connect(partial(self._updateMenuNodeCallback, node))

            elif node.isSeparator:
                node.widget = _parent.widget.addSeparator()

            elif node.isSection:
                # We do not use _parent.widget.addSection as it does not show with native settings
                # _parent.widget.addSeparator()
                node.widget = _parent.widget.addItem(text=f'⎯⎯⎯⎯⎯ {node.name} ⎯⎯⎯⎯⎯', enabled=False)

            else:
                raise RuntimeError(f'Invalid: {node} is ill-defined')

            # if node.checkEnable and node.checkEnableCallback is not None:
            #     # This node needs checking for enabling;
            #     # set callback on parent which will check all its children
            #     if node.parent is None or \
            #         node.parent.widget is None or not node.parent.isMenu:
            #         raise RuntimeError(f'Unable to activate checkEnable for {node}')
            #     node.parent.widget.aboutToShow.connect(partial(self._updateMenuNode, node.parent))

        # recurse into children
        for _child in node._children:
            self.makeMenus(_child)

    #-----------------------------------------------------------------------------------------
    # Callback's from dynamic nodes
    #-----------------------------------------------------------------------------------------

    def _updateMenuNodeCallback(self, node: MenuNode):
        """Callback to update Menu node:
        - optionally adding dynamic nodes
        - checking self for checkEnable
        - checking child-nodes for checkEnable and enabling/disabling corresponding widgets.
        """
        if node.isDynamic and node.dynamicCallback:
            node.dynamicCallback(node)

        if node.checkEnable:
            node.checkEnableCallback(node)

        for child in [_c for _c in node._children if _c.checkEnable]:
            enabled = child.checkEnableCallback(child)
            child.setEnabled(enabled)

    def _updateDynamicNode(self, node: MenuNode, defs: list):
        """Update dynamic node using defs to generate child-nodes and corresponding
        Menu widgets.
        """
        if not node.isDynamic:
            raise RuntimeError(f'_updateDynamicNode: not allowed for {node}')

        # clear this node and its decendants
        node.clearNode()
        # construct the new decendant nodes from the defs
        node.addNodesFromList(defs)
        # make the menu's
        for _child in node._children:
            self.makeMenus(_child)

    def _fillFileOpenRecentCallback(self, node: MenuNode):
        """callback to fill File->Open recent menu
        """
        _defs = _fillFileOpenRecentCallback(node)
        self._updateDynamicNode(node=node, defs=_defs)

    def _fillFilePredefinedLayoutsCallback(self, node):
        """Callback to fill File->Layouts->Open pre-defined
        """
        from ccpn.ui.gui import Layout

        _files = Layout._getPredefinedLayouts()
        _defs = [(f.basename, partial(self.application._restoreLayoutFromFile, f))
                 for f in _files
                 ]
        self._updateDynamicNode(node=node, defs=_defs)

    def _fillViewShowModulesCallback(self, node) -> bool:
        """Callback to fill View->Show/hide Modules Menu
        """
        _modules = [m for m in self.mainWindow.modules if not m._isPythonConsoleModule]
        _defs = []
        count = 1
        for module in _modules:
            # create a shortcut command/cntr 1-9,0 for first 10 modules
            if count <= 10:
                shortcut = f'⌃{count % 10}'  # Unicode U+2303, NOT the carrot on your keyboard.
            else:
                shortcut = None

            _defs.append(
                    (module.moduleName, partial(self.mainWindow._toggleModule, module=module),
                     dict(checkable=True, checked=module._showState, shortcut=shortcut)
                     )
                    )
            count += 1

        self._updateDynamicNode(node=node, defs=_defs)

    def _fillMacroRunRecentCallback(self, node):
        """Callback to fill Macro->Run Recent Menu
        """
        from ccpn.framework.Preferences import RECENT_MACROS

        _files = reversed(self.application.preferences.get(RECENT_MACROS))
        _defs = [(f, partial(self.application.runMacro, f))
                 for f in _files
                 ]
        _defs.extend([
            Separator(),
            ('Clear', self.application.preferences.clearRecentMacros)
            ])
        self._updateDynamicNode(node=node, defs=_defs)

    def _fillMacroRunCCPNCallback(self, node):
        """Callback to fill Macro->Run CCPN Menu
        """
        from ccpn.framework.PathsAndUrls import macroPaths

        _defs = []
        # loop over directories to find macro's, skip any that start with underscore,
        # i.e. '_'
        for path in macroPaths:
            _defs.append(
                    (path.basename,)
                    )
            _files = sorted(f for f in path.glob('*.py') if not f.basename.startswith('_'))
            _defs.extend(
                    [(f.basename, partial(self.application.runMacro, f)) for f in _files]
                    )
        # update the node
        self._updateDynamicNode(node=node, defs=_defs)

    def _fillUserPluginsCallback(self, node):
        """Callback to fill Plugins->User Plugins
        """
        from ccpn.framework.PathsAndUrls import pluginPath
        from ccpn.plugins import loadedPlugins, loadedUserPlugins
        from ccpn.util.Common import camelCaseToString

        _defs = []
        _defs.extend([
            (f.PLUGINNAME, partial(self.mainWindow.startPlugin, f)) for f in loadedUserPlugins
            ])

        self._updateDynamicNode(node=node, defs=_defs)

    def _fillCCPNPluginsCallback(self, node):
        """Callback to fill Plugins->CCPN Plugins
        """
        from ccpn.framework.PathsAndUrls import pluginPath
        from ccpn.plugins import loadedPlugins, loadedUserPlugins
        from ccpn.util.Common import camelCaseToString

        _defs = []
        _defs.extend([
            (f.PLUGINNAME, partial(self.mainWindow.startPlugin, f)) for f in loadedPlugins
            ])

        self._updateDynamicNode(node=node, defs=_defs)

    def _fillHelpTutorialsCallback(self, node):
        """Callback to fill Help->Tutorials Menu
        """
        from ccpn.framework.PathsAndUrls import tutorialsPath, definedTutorialPaths
        from ccpn.util.Common import camelCaseToString

        _defs = [
            ('Video Tutorials && Manual', self.ui._showCCPNVideos),
            ('Tutorial Data', self.ui._showTutorialData),
            Separator(),
            ]

        # Add the defined tutorials
        _defs.extend([
            (camelCaseToString(f.basename), partial(self.ui._showPath, f)) for f in definedTutorialPaths
            ])
        _defs.append(Separator())

        # loop over tutorialsPath for pdf's,
        # skip any that start with underscore, i.e. '_' or we already processed
        for path in [tutorialsPath]:
            _files = sorted(f for f in path.glob('*.pdf')
                            if not f.basename.startswith('_') and f not in definedTutorialPaths
                            )
            _defs.extend([
                (camelCaseToString(f.basename), partial(self.ui._showPath, f)) for f in _files
                ])

        self._updateDynamicNode(node=node, defs=_defs)

    def _fillHelpHowtosCallback(self, node):
        """Callback to fill Help->How-to's
        """
        from ccpn.framework.PathsAndUrls import howTosPath
        from ccpn.util.Common import camelCaseToString

        _defs = []

        # loop over tutorialsPath for pdf's,
        # skip any that start with underscore, i.e. '_' or we already processed
        for path in [howTosPath]:
            _files = sorted(f for f in path.glob('*.pdf')
                            if not f.basename.startswith('_')
                            )
            _defs.extend([
                (camelCaseToString(f.basename), partial(self.ui._showPath, f)) for f in _files
                ])

        self._updateDynamicNode(node=node, defs=_defs)

    def _fillDevelopmentDebugCallback(self, node):
        """Callback to fill Development->Debug Menu
        """
        _defs = []
        for _level in range(4):
            name = 'off' if _level == 0 else f'set level {_level}'
            _defs.append(
                    (name, partial(self.application.setDebug, _level),
                     dict(checkable=True, checked=self.application.debugLevel == _level)
                     )
                    )

        self._updateDynamicNode(node=node, defs=_defs)

    #-----------------------------------------------------------------------------------------

    def __str__(self):
        return f'<MenuManager>'


# end class #-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Helper code
#-----------------------------------------------------------------------------------------

def _getOpenLayoutPath(mainWindow):
    """Opens a saved Layout as dialog box and gets directory specified in the
    file dialog.
    :return selected path or None
    """

    fType = 'JSON (*.json)'
    dialog = LayoutsFileDialog(parent=mainWindow, acceptMode='open', fileFilter=fType)
    dialog._show()
    path = dialog.selectedFile()
    return path or None


def _getSaveLayoutPath(mainWindow):
    """Opens save Layout as dialog box and gets directory specified in the
    file dialog.
    :return selected path or None
    """

    jsonType = '.json'
    fType = 'JSON (*.json)'
    dialog = LayoutsFileDialog(parent=mainWindow, acceptMode='save', fileFilter=fType)
    dialog._show()
    newPath = dialog.selectedFile()
    if not newPath:
        return None

    newPath = aPath(newPath)
    if newPath.exists():
        # should not really need to check the second and third condition above, only
        # the Qt dialog stupidly insists a directory exists before you can select it
        # so if it exists but is empty then don't bother asking the question
        title = 'Overwrite path'
        msg = 'Path "%s" already exists, continue?' % newPath
        if not MessageDialog.showYesNo(title, msg):
            return None

    newPath.assureSuffix(jsonType)
    return newPath


#-----------------------------------------------------------------------------------------
# Various small helper functions for menu actions dynamic settings;
# i.e. checking if node is active or for filling dynamic nodes.
# Pass-in node for all functions.
#-----------------------------------------------------------------------------------------

def _fillFileOpenRecentCallback(node) -> list:
    """callback to yield the list of Actions for File->Open Recent
    """
    from ccpn.framework.Preferences import RECENT_FILES
    _app = getApplication()

    _files = _app.preferences.get(RECENT_FILES)
    _defs = [Action(f, partial(_app.loadProject, f)) for f in _files]
    _defs.extend([
        Separator(),
        Action('Clear', _app.preferences.clearRecentFiles)
        ])
    return _defs


def _projectCanBeSaved(node) -> bool:
    """callback to test if project can be saved; ie. not temporary and not readOnly
    """
    project = getProject()
    return project and not project.isTemporary and not project.isReadOnly


def _projectIsNotTemporary(node) -> bool:
    """callback to test if project is temporary
    """
    project = getProject()
    return project and not project.isTemporary


def _projectIsNotReadOnly(node) -> bool:
    """callback to test if project is temporary
    """
    project = getProject()
    return project and not project.isReadOnly


def _projectHasArchives(node) -> bool:
    """callback to test if project has archives
    """
    project = getProject()
    return bool(project and project._getArchivePaths())


def _projectHasPeaks(node) -> bool:
    """callback to test if project has peaks
    """
    project = getProject()
    return bool(project and project.peaks)


def _projectHasSpectra(node) -> bool:
    """callback to test if project has spectra
    """
    project = getProject()
    return bool(project and project.spectra)


def _projectHasChains(node) -> bool:
    """callback to test if project has chains
    """
    project = getProject()
    return bool(project and project.chains)


def _hasSpectrumDisplays(node) -> bool:
    """callback to test if MainWindow has SpectrumDisplays
    """
    app = getApplication()
    return len(app.mainWindow.spectrumDisplays) > 0


def _hasActiveDisplay(node) -> bool:
    """callback to test if project has spectra
    """
    current = getCurrent()
    if current and current.strip is not None:
        _sd = current.strip.spectrumDisplay
        node.widget.setTitle(f'In SpectrumDisplay {_sd.id}')
        return True
    else:
        node.widget.setTitle('Select Strip in SpectrumDisplay')
        return False


def _updatePythonConsole(node) -> bool:
    """callback to check and update the Show/hide Python Console action
    """
    app = getApplication()
    if (widget := app.ui.mainWindow._getPythonConsoleWidget()) is not None:
        hidden = widget.isHidden()
        checked = not hidden
    else:
        checked = False
    node.widget.setChecked(checked)
    return True


def _updateShowHideModules(node) -> bool:
    """callback to check and update the Show/hide Modules menu;
    :return True if there are modules other then the PythonConsoleModule
    """
    app = getApplication()
    modules = [m for m in app.ui.mainWindow.modules
               if not m._isPythonConsoleModule
               ]
    return len(modules) > 0
