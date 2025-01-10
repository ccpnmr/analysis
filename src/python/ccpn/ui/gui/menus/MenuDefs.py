"""
The menus are specified by a (recursive) Menu's (i.e. lists) composed of either
Action, Separator, Section, Menu or DynamicMenu instances (see _MenuItems for
their definitions).

Note for Actions:
      Use a callback function defined as a method of MenuDefs and pass on
      the action from there.
      This avoids the (V3) situation in that the MainWindow has not yet been defined,
      when initialising the MenuDefs; i.e. ui.mainWindow is None on initialisation of
      the MenuDefs instance, but is defined the moment the callback is executed.

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
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
__dateModified__ = "$dateModified: 2025-01-10 16:38:47 +0000 (Fri, January 10, 2025) $"
__version__ = "$Revision: 3.3.0.develop $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"

#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from typing import Optional, Callable

CallableOrNone = Optional[Callable]

from ccpn.framework.PathsAndUrls import macroPath
from ccpn.framework.Application import getApplication, getProject, getCurrent
from ccpn.framework.lib.FrameWorkProperties import FrameworkProperties

from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath
from ccpn.util.decorators import singleton

from ccpn.ui.gui.widgets import MessageDialog


from ccpn.ui.gui.menus._MenuItems import Menu, Action, Section, Separator, DynamicMenu


FILE_MENU = 'File'
EDIT_MENU = 'Edit'
VIEW_MENU = 'View'
VIEW_CHEMICAL_SHIFT_PERTURBATION = 'Chemical Shift Perturbation (Beta)'  # used in AnalysisAssign
SPECTRUM_MENU = 'Spectrum'
MOLECULES_MENU = 'Molecules'
MACRO_MENU = 'Macro'
PLUGINS_MENU = 'Plugins'
HELP_MENU = 'Help'
DEVELOPMENT_MENU = 'Development'


def getMenuDefs():
    """:return The MenuDefs (singleton) instance
    """
    return MenusDefs()

#-----------------------------------------------------------------------------------------
# Define the actual Menu of the MenuBar
#-----------------------------------------------------------------------------------------

@singleton
class MenusDefs(Menu, FrameworkProperties):
    """A Menu class (list) to define the menu definitions and callback routines
    Used by MainWindow to initialise the menuBar

    Use insertAfter() or insertBefore() methods to dynamically add to the MenuDefs
    instance.

    NB __init__ at end of code!
    """

    def _defineMenus(self):
        """Set up the menu specification; called from __init__
        """
        app = self.application
        ui = self.application.ui

        # Populate self
        self.clear()
        self.extend([

    #-----------------------------------------------------------------------------------------

    Menu(FILE_MENU,

         # Unicode U+2303, NOT the carrot on your keyboard.
         Action("New", self._newProjectCallback, shortcut='⌃n'),

         Separator(),
         Action("Open...", self._openProjectCallback, shortcut='⌃o'),  # Unicode U+2303
         DynamicMenu('Open Recent', callback=_fillFileOpenRecentCallback),
         Action("Load Data...", self._loadDataCallback, shortcut='ld'),

         Separator(),
         Action("Save", self._saveCallback, shortcut='⌃s', checkEnabled=_projectCanBeSaved),  # Unicode U+2303
         Action("Save As...", self._saveAsCallback, shortcut='sa'),

         Separator(),
         Menu("Import from",
            Action("NEF File", self._importNefCallback, shortcut='in'),
            Action("NmrStar File", self._loadNMRStarFileCallback, shortcut='bi'),
         ),
         Menu("Export to",
            Action("NEF File", self._exportToNEFCallback, shortcut='ex'),
         ),

         Separator(),
         Menu('Layout',
              Action("Save", self._saveLayoutCallback, checkEnabled=_projectCanBeSaved),
              Action("Save as...", self._saveLayoutAsCallback, checkEnabled=_projectCanBeSaved),

              Separator(),
              Action("Restore last", self._restoreLastSavedLayoutCallback),
              Action("Restore from file...", self._restoreLayoutFromFileCallback),

              Separator(),
              DynamicMenu('Open pre-defined', callback=_fillFilePredefinedLayoutsCallback),
         ),
         Action("Summary", self._showSummaryCallback),

         Separator(),
         Action('Archive', self._saveToArchiveCallback, checkEnabled=_projectCanBeSaved),
         Action('Restore From Archive...', self._restoreFromArchiveCallback, checkEnabled=_projectHasArchives),

         Separator(),
         Action("Preferences...", self._showPreferencesCallback, shortcut='⌃,'),

         Separator(),
         Action("Quit", self._quitCallback, shortcut='⌃q'),  # Unicode U+2303,

    ), # end Menu File

    Menu(EDIT_MENU,

        Action("Undo", self._undoCallback, shortcut='⌃z'),  # Unicode U+2303,
        Action("Redo", self._redoCallback, shortcut='⌃y'),  # Unicode U+2303,

        Separator(),
        Action("Cut", self._nyi, shortcut='⌃x', enabled=False),
        Action("Copy", self._nyi, shortcut='⌃c', enabled=False),
        Action("Paste", self._nyi, shortcut='⌃v', enabled=False),
        Action("Select all", self._nyi, shortcut='⌃a', enabled=False),

    ), # end Menu Edit

    Menu(VIEW_MENU,

         Action("Chemical Shift Table", self._showChemicalShiftTableCallback, shortcut='ct'),
         Action("NmrResidue Table", self._showNmrResidueTableCallback, shortcut='nt'),
         Action("Residue Table", self._showResidueTableCallback, checkEnabled=_projectHasChains),
         Action("Peak Table", self._showPeakTableCallback, shortcut='pt', checkEnabled=_projectHasSpectra),
         Action("Integral Table", self._showIntegralTableCallback, shortcut='it', checkEnabled=_projectHasSpectra),
         Action("Multiplet Table", self._showMultipletTableCallback, shortcut='mt', checkEnabled=_projectHasSpectra),
         Action("Data Table", self._showDataTableCallback, shortcut='dt', checkEnabled=_projectHasDataTables),

         Separator(),
         Action("Restraint Table", self._showRestraintTableCallback, shortcut='rt', checkEnabled=_projectHasRestraintTables),
         Action("Violation Table", self._showViolationTableCallback, shortcut='vt', checkEnabled=_projectHasViolationTables),
         Action("Structure Ensemble Table", self._showStructureEnsembleTableCallback, shortcut='st', checkEnabled=_projectHasStructureEnsembles),

         Separator(),
         Action(VIEW_CHEMICAL_SHIFT_PERTURBATION, self._showChemicalShiftMappingCallback, shortcut='cm'),
         Action("Relaxation Analysis (Beta)", self._showRelaxationModuleCallback, shortcut='ra'),
         Action("Notes Editor", self._showNotesEditorCallback, shortcut='no'),

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
         DynamicMenu('Show/hide Modules', callback=_fillViewShowModulesCallback, checkEnabled=_updateShowHideModules),
         Action("Show/hide Sidebar", self._toggleSidebarCallback, shortcut=' s', checkable=True, checked=True),
         Action("Show/hide Python Console", self._toggleConsoleCallback, shortcut='  ', checkable=True, checked=True,
                                            checkEnabled=_updatePythonConsoleModule
         ),

         ), # end Menu View

    Menu(SPECTRUM_MENU,

        Action('Load Spectra...', self._loadSpectraCallback, shortcut='ls'),
        Action("Validate Paths...", self._validatePathsCallback, shortcut='vp', checkEnabled=_projectHasSpectra),

        Separator(),
        Action("Copy Spectra into Project...", self._copyToProjectCallback, checkEnabled=_projectHasSpectra),
        Action("Convert...", self._convertSpectrumCallback, checkEnabled=_projectHasSpectra),
        Action("Make Projection...", self._makeProjectionCallback, shortcut='pj', checkEnabled=_projectHasSpectra),

        Separator(),
        Action("New Spectrum Group...", self._newSpectrumGroupCallback, checkEnabled=_projectHasSpectra),
        Action("Edit Spectrum Group...", self._editSpectrumGroupCallback, shortcut ='ss', checkEnabled=_projectHasSpectrumGroups),
        Action("Pseudo-Spectrum to SpectrumGroup...", self._pseudoSpectrumCallback, checkEnabled=_projectHasPseudoSpectra),

        Separator(),
        Action("Set Experiment Types...", self._experimentTypesCallback, shortcut='et', checkEnabled=_projectHasSpectra),

        Separator(),
        Menu("Pick Peaks",
             Action("Pick 1D Peaks...", self._pick1DPeaksCallback, shortcut='p1', checkEnabled=_projectHas1DSpectra),
             Action("Pick nD Peaks...", self._pickNDPeaksCallback, shortcut='pp', checkEnabled=_projectHasNDSpectra),
             checkEnabled=_projectHasSpectra
             ),
        Action("Copy PeakList...", self._copyPeakListCallback, shortcut='cl', checkEnabled=_projectHasSpectra),
        Action("Copy Peaks...", self._copyPeaksCallback, shortcut='cp', checkEnabled=_projectHasPeaks),
        Action("Peak Collections...", self._peakCollectionsCallback, shortcut='sc', checkEnabled=_projectHasPeaks),
        Action("Estimate Peak Volumes...", self._estimateVolumesCallback, shortcut='ev', checkEnabled=_projectHasPeaks),
        Action("Estimate Currently Selected Peak Volumes", self._estimateCurrentVolumesCallback, shortcut='ec', checkEnabled=_projectHasCurrentPeaks),
        Action("Reorder PeakList Axes...", self._reorderPeakListAxesCallback, shortcut='rl', checkEnabled=_projectHasSpectra),

        Separator(),
        Action("Make Strip Plot...", self._makeStripPlotCallback, shortcut='sp', checkEnabled=_projectHasSpectra),
        Action("Print to File...", self._printToFileCallback, shortcut='⌃p', checkEnabled=_projectHasSpectra),

    ), # end Menu Spectrum

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

    ), # end Menu Molecules

    Menu(MACRO_MENU,

        Action("New Macro Editor", self._showMacroEditorCallback, shortcut='nm'),

        Separator(),
        Action("Open User Macro...", self._openMacroCallback, shortcut='om'),
        Action("Open CCPN Macro...", partial(self._openMacroCallback, directory=macroPath)),

        Separator(),
        Action("Run...", self._runMacroCallback, shortcut='rm'),
        DynamicMenu('Run Recent', callback=_fillMacroRunRecentCallback),
        DynamicMenu('Run CCPN Macros', callback=_fillMacroRunCCPNCallback),

        Separator(),
        Action("Define Macro Shortcuts...", self._defineUserShortcutsCallback, shortcut='du'),

    ),  # end Menu Macro

    Menu(PLUGINS_MENU,

        DynamicMenu('CCPN Plugins', callback=_fillCCPNPluginsCallback),
        DynamicMenu('User Plugins', callback=_fillUserPluginsCallback),

        Separator(),
        Action("Reload", app._reloadPlugins),

    ),  # end Menu Plugins

    Menu(HELP_MENU,

        DynamicMenu('Tutorials', callback=_fillHelpTutorialsCallback),
        DynamicMenu('How-Tos', callback=_fillHelpHowtosCallback),

        Section('Handies'),
        Action("Tip of the Day", self._showTipOfTheDayCallback),
        Action("Key Concepts", self._showKeyConceptsCallback),
        Action("Show Shortcuts", self._showShortcutsCallback),

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

    ), # end Menu Help

    #-----------------------------------------------------------------------------------------
    ])  # end extend

    #-----------------------------------------------------------------------------------------
    # Development Menu
    #-----------------------------------------------------------------------------------------
        _devMenu = Menu( DEVELOPMENT_MENU,
            DynamicMenu('Debug', callback=_fillDevelopmentDebugCallback),
            Action('Print Undo Stack', callback=self._printUndoStackCallback),
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
        self.ui._loadDataIgnoreExtension(NefDataLoader)

    def _exportToNEFCallback(self):
        """Export the current project as a Nef file
        """
        self.ui.exportToNef()

    def _loadNMRStarFileCallback(self):
        """menu callback; use ui.loadData to do the lifting
        """
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        self.ui._loadDataIgnoreExtension(StarDataLoader)

    def _saveCallback(self):
        """The project save callback
        """
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

    def _saveToArchiveCallback(self):
        """Archive the project
        """
        self.ui.saveToArchive()

    def _restoreFromArchiveCallback(self):
        """Restore a project from archive
        """
        self.ui.restoreFromArchive()

    def _saveLayoutCallback(self):
        """Save layout without query for path
        """
        self.mainWindow._saveLayoutToFile()

    def _restoreLastSavedLayoutCallback(self):
        """Restore layout without query for path
        """
        self.mainWindow._loadLayoutFromFile()
        self.mainWindow._restoreLayout()

    def _saveLayoutAsCallback(self):
        """Save layout with query for path
        """
        self.ui.saveLayoutToFile()

    def _restoreLayoutFromFileCallback(self):
        """Restore layout with query for path
        """
        self.ui.restoreLayoutFromFile()

    def _showSummaryCallback(self):
        """Show the Project summary popup.
        """
        from ccpn.ui.gui.popups.ProjectSummaryPopup import ProjectSummaryPopup
        popup = ProjectSummaryPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, modal=True)
        popup.exec_()

    def _showPreferencesCallback(self):
        """
        Displays Application Preferences Popup.
        """
        self.ui.showPreferences()

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
        self.ui.setExperimentTypes()

    def _validatePathsCallback(self, spectra=None, defaultSelected=None):
        """validate the spectrum paths.
        """
        self.ui.validatePaths()
        # if not self.project.spectra:
        #     getLogger().warning('Validate Spectrum Paths Selection: Project has no Spectra.')
        #     MessageDialog.showWarning('Validate Spectrum Paths Selection', 'Project has no Spectra.')
        # else:
        #     from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraPopup
        #
        #     popup = ValidateSpectraPopup(mainWindow=self.ui.mainWindow, spectra=spectra,
        #                                  defaultSelected=defaultSelected)
        #     popup.exec_()

    def _convertSpectrumCallback(self):
        """Show the convertToHdf5 popup
        """
        if not self.project.spectra:
            getLogger().warning('Convert spectra: Project has no Spectra.')
            MessageDialog.showWarning('Convert spectra', 'Project has no Spectra.')
        else:
            from ccpn.ui.gui.popups.ConvertToNdf5Popup import ConvertToNdf5Popup

            popup = ConvertToNdf5Popup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _makeStripPlotCallback(self):
        """Callback for Spectrum->Make Strip Plot
        """
        self.ui.makeStripPlot()

    def _copyToProjectCallback(self):
        """Callback for Spectrum->Copy into Project
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

    def _pick1DPeaksCallback(self):
        """
        Callback to display Peak Picking 1D Popup.
        """
        self.ui.pick1DPeaks()

    def _pickNDPeaksCallback(self):
        """ Callback to display Peak Picking nD Popup.
        """
        self.ui.pickNDPeaks()

    def _copyPeakListCallback(self):
        """Callback to display CopyPeakList popup
        """
        self.ui.copyPeakList()

    def _copyPeaksCallback(self):
        """Callback to display CopyPeaks popup
        """
        self.ui.copyPeaks(useCurrent=True)

    def _peakCollectionsCallback(self):
        """Callback to display the series peak collections popup
        """
        from ccpn.ui.gui.popups.SeriesPeakCollectionPopup import SeriesPeakCollectionPopup

        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Spectrum groups cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Spectrum groups cannot be displayed')
            return

        popup = SeriesPeakCollectionPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
        popup.exec_()

    def _estimateVolumesCallback(self):
        """
        Displays Estimate Volumes Popup.
        """
        self.ui.estimateVolumes()

    def _estimateCurrentVolumesCallback(self):
        """Calculate volumes for the currently selected peaks
        """
        self.mainWindow._showEstimateCurrentVolumesPopup()

    def _editSpectrumGroupCallback(self):
        """Callback to edit SpectrumGroup
        """
        self.ui.editSpectrumGroup(editMode=True)

    def _newSpectrumGroupCallback(self):
        """Callback to edit SpectrumGroup
        """
        self.ui.editSpectrumGroup(editMode=False)

    def _pseudoSpectrumCallback(self):
        """Pseudo-spectrum to spectrumGroup popup
        """
        self.ui.newSpectrumGroupFromPseudoSpectrum()

    def _makeProjectionCallback(self):
        """Make projection pupup callback
        """
        self.ui.makeProjection()

    def _printToFileCallback(self):
        """Show the print spectrumDisplay dialog
        """
        from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup

        if len(self.mainWindow.spectrumDisplays) == 0:
            MessageDialog.showWarning('', 'No SpectrumDisplay found')
            return

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

    def _showRestraintTableCallback(self):
        """Callback for showing RestraintTable module
        """
        self.ui.showRestraintTable()

    def _showViolationTableCallback(self):
        """Callback for showing ViolationTable module
        """
        self.ui.showViolationTable()

    def _showStructureEnsembleTableCallback(self):
        """Callback for showing StructureEnsembleTable module
        """
        self.ui.showStructureEnsembleTable()

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

    def _showChemicalShiftMappingCallback(self):
        """Callback to show Chemical Shift Perturbation module
        """
        self.ui.showChemicalShiftMapping()

    def _showRelaxationModuleCallback(self):
        """Callback to show relaxation module
        """
        self.ui.showRelaxationModule()

    def _showNotesEditorCallback(self):
        """Callback to show Notes editor module
        """
        self.ui.showNotesEditor()

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
        self.ui.showMacroEditor()

    def _openMacroCallback(self, directory=None):
        """ Select macro file and on MacroEditor.
        """
        from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog

        mainWindow = self.ui.mainWindow
        dialog = MacrosFileDialog(parent=mainWindow, acceptMode='open', fileFilter='*.py', directory=directory)
        dialog._show()
        path = dialog.selectedFile()
        if path is not None:
            self.ui.showMacroEditor(path=path)

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

    def _showTipOfTheDayCallback(self):
        self.ui._showTipOfTheDay()

    def _showKeyConceptsCallback(self):
        self.ui._showKeyConcepts()

    def _showShortcutsCallback(self):
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
    # development
    #-----------------------------------------------------------------------------------------

    def _printUndoStackCallback(self):
        """Callback for Development-->Print Undo Stack
        """
        self.application._getUndo().print()

    #-----------------------------------------------------------------------------------------
    # Implementation methods
    #-----------------------------------------------------------------------------------------

    def __init__(self):
        super().__init__(name='root')
        FrameworkProperties.__init__(self)
        self._defineMenus()

    def insertAfter(self, menuKeys: list, menuDef: list):
        """Insert menuDef after the menu/action/section defined by menuKeys, i.e. a list
        of names or indices that recursively define the menu;
        e.g. ['File', 'New']

        NB. to get something at the end, use -1; e.g. at the end of 'File' menu:
            insertAfter(['File', -1], ....)

        :param menuKeys: a list of names or position-indices defining the menu/action/section
        :param menuDef: a list defining the menu/action/separator/section items to be inserted
        """
        _indx, currentMenu = self._findMenu(menuKeys=menuKeys)
        if _indx < 0:
            # Correct the _indx to positive numbers, i.e. -1 is last item
            _indx += len(currentMenu)
        currentMenu.insert(_indx + 1, menuDef)

    def insertBefore(self, menuKeys: list, menuDef: list):
        """Insert menuDef before the menu/action/section defined by menuKeys, i.e. a list
        of names or indices that recursively define the menu;
        e.g. ['File', 'New']

        NB. to get something as the first menu/action, use 0; e.g. at the start of 'File' menu:
            insertBefore(['File', 0], ....)

        :param menuKeys: a list of names or position-indices defining the menu/action/section
        :param menuDef: a list defining the menu/action/separator/section items to be inserted
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
                if isinstance(item, (Menu, Action, Section, Separator)):
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


#-----------------------------------------------------------------------------------------
# Various small helper functions for menu actions dynamic settings;
# i.e. checking if node is active (e.g. _projectXYZ or _hasXYZ)
#      or for filling dynamic nodes (e.g. _fillXYZ).
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


def _fillFilePredefinedLayoutsCallback(node) -> list:
    """Callback to fill File->Layouts->Open pre-defined
    """
    from ccpn.ui.gui import Layout
    _app = getApplication()

    _files = Layout._getPredefinedLayouts()
    _defs = [Action(f.basename, partial(_app.mainWindow._restoreLayoutFromFile, f)) for f in _files]
    return _defs


def _fillViewShowModulesCallback(node) -> list:
    """Callback to fill View->Show/hide Modules Menu
    """
    _app = getApplication()
    _mainWindow = _app.ui.mainWindow

    _modules = [m for m in _mainWindow.modules if not m._isPythonConsoleModule]
    _defs = []
    count = 1
    for module in _modules:
        # create a shortcut command/cntr 1-9,0 for first 10 modules
        if count <= 10:
            shortcut = f'⌃{count % 10}'  # Unicode U+2303, NOT the carrot on your keyboard.
        else:
            shortcut = None

        _defs.append(
                Action(module.moduleName, partial(_mainWindow._toggleModule, module=module),
                       checkable=True, checked=module._showState, shortcut=shortcut
                )
        )
        count += 1
    return _defs


def _fillMacroRunRecentCallback(node) -> list:
    """Callback to fill Macro->Run Recent Menu
    """
    from ccpn.framework.Preferences import RECENT_MACROS
    _app = getApplication()

    _files = reversed(_app.preferences.get(RECENT_MACROS))
    _defs = [Action(f, partial(_app.runMacro, f)) for f in _files]
    _defs.extend([
        Separator(),
        Action('Clear', _app.preferences.clearRecentMacros)
    ])
    return _defs


def _fillMacroRunCCPNCallback(node) -> list:
    """Callback to fill Macro->Run CCPN Menu
    """
    from ccpn.framework.PathsAndUrls import macroPaths
    _app = getApplication()

    _defs = []
    # loop over directories to find macro's, skip any that start with underscore,
    # i.e. '_'
    for path in macroPaths:
        _defs.append(Section(path.basename))
        _files = sorted(f for f in path.glob('*.py') if not f.basename.startswith('_'))
        _defs.extend(
                [Action(f.basename, partial(_app.runMacro, f)) for f in _files]
                )
    return _defs


def _fillUserPluginsCallback(node) -> list:
    """Callback to fill Plugins->User Plugins
    """
    from ccpn.plugins import loadedUserPlugins

    _app = getApplication()
    _mainWindow = _app.ui.mainWindow
    _defs = [Action(f.PLUGINNAME, partial(_mainWindow.startPlugin, f)) for f in loadedUserPlugins]
    return _defs


def _fillCCPNPluginsCallback(node) -> list:
    """Callback to fill Plugins->CCPN Plugins
    """
    from ccpn.plugins import loadedPlugins

    _app = getApplication()
    _mainWindow = _app.ui.mainWindow
    _defs = [Action(f.PLUGINNAME, partial(_mainWindow.startPlugin, f)) for f in loadedPlugins]
    return _defs


def _fillHelpTutorialsCallback(node) -> list:
    """Callback to fill Help->Tutorials Menu
    """
    from ccpn.framework.PathsAndUrls import tutorialsPath, definedTutorialPaths
    from ccpn.util.Common import camelCaseToString

    _app = getApplication()

    _defs = [
        Action('Video Tutorials && Manual', _app.ui._showCCPNVideos),
        Action('Tutorial Data', _app.ui._showTutorialData),
        Separator(),
        ]

    # Add the defined tutorials
    _defs.extend([
        Action(camelCaseToString(f.basename), partial(_app.ui._showPath, f)) for f in definedTutorialPaths
        ])
    _defs.append(Separator())

    # loop over tutorialsPath for pdf's,
    # skip any that start with underscore, i.e. '_' or we already processed
    for path in [tutorialsPath]:
        _files = sorted(f for f in path.glob('*.pdf')
                        if not f.basename.startswith('_') and f not in definedTutorialPaths
                        )
        _defs.extend([
            Action(camelCaseToString(f.basename), partial(_app.ui._showPath, f)) for f in _files
            ])

    return _defs


def _fillHelpHowtosCallback(node) -> list:
    """Callback to fill Help->How-to's
    """
    from ccpn.framework.PathsAndUrls import howTosPath
    from ccpn.util.Common import camelCaseToString

    _app = getApplication()

    _defs = []
    # loop over tutorialsPath for pdf's,
    # skip any that start with underscore, i.e. '_' or we already processed
    for path in [howTosPath]:
        _files = sorted(f for f in path.glob('*.pdf')
                        if not f.basename.startswith('_')
                        )
        _defs.extend([
            Action(camelCaseToString(f.basename), partial(_app.ui._showPath, f)) for f in _files
            ])

    return _defs


def _fillDevelopmentDebugCallback(node) -> list:
    """Callback to fill Development->Debug Menu
    """
    _app = getApplication()

    _defs = []
    for _level in range(4):
        name = 'off' if _level == 0 else f'set level {_level}'
        _defs.append(Action(name, partial(_app.setDebug, _level),
                            checkable=True, checked=(_app.debugLevel==_level)
                            )
        )
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


def _projectHasCurrentPeaks(node) -> bool:
    """callback to test if project has peaks selected
    """
    app = getApplication()
    return bool(app.current.peaks)


def _projectHasSpectra(node) -> bool:
    """callback to test if project has spectra
    """
    project = getProject()
    return bool(project and project.spectra)


def _projectHasNDSpectra(node) -> bool:
    """callback to test if project has nD-spectra
    """
    project = getProject()
    spectra = [spec for spec in project.spectra if spec.dimensionCount > 1]
    return len(spectra) > 0


def _projectHas1DSpectra(node) -> bool:
    """callback to test if project has 1D-spectra
    """
    project = getProject()
    spectra = [spec for spec in project.spectra if spec.dimensionCount == 1]
    return len(spectra) > 0


def _projectHasPseudoSpectra(node) -> bool:
    """callback to test if project has pseudo nD spectra
    """
    project = getProject()
    if not project:
        return False
    _validSpectra = [sp for sp in project.spectra if sp._getPseudoDimension() != 0]
    return bool(_validSpectra)


def _projectHasSpectrumGroups(node) -> bool:
    """callback to test if project has spectrumGroups
    """
    project = getProject()
    return bool(project and project.spectrumGroups)


def _projectHasChains(node) -> bool:
    """callback to test if project has chains
    """
    project = getProject()
    return bool(project and project.chains)


def _projectHasDataTables(node) -> bool:
    """callback to test if project has dataTables
    """
    project = getProject()
    return bool(project and project.dataTables)


def _projectHasRestraintTables(node) -> bool:
    """callback to test if project has restraintTables
    """
    project = getProject()
    return bool(project and project.restraintTables)


def _projectHasViolationTables(node) -> bool:
    """callback to test if project has violationTables
    """
    project = getProject()
    return bool(project and project.violationTables)


def _projectHasStructureEnsembles(node) -> bool:
    """callback to test if project has StructureEnsembles
    """
    project = getProject()
    return bool(project and project.structureEnsembles)


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


def _updatePythonConsoleModule(node) -> bool:
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
