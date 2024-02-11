"""
    The menus are specified by a (recursive) list of lists of lists
    (actually, an iterable of iterables of iterables, but the term ‘list’ will be used here to mean any iterable).

    Menu specification lists are composed of:
    - A (name, callable) tuple or (name, callable, options) tuple that specifies a menu action with the callable
      that is triggered when the menu item is selected. Options is a list or dict of (keyword, value) pairs.
      Valid options (from Action widget):
        :param shortcut: optional two letter shortcut
        :param checked: optional checked flag (if checkable, default: True)
        :param checkable: optional checkable flag (default: False)
        :param icon: optional icon
        :param enabled: optional enable flag (default: True)
        :param toolTip: optional tooltip

    - A (name, list) tuple where the list defines the sub-menu items. A zero-length list denotes a
      dynamically filled menu

    - A zero-length () tuple, indicating a separator.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-02-11 15:47:52 +0000 (Sun, February 11, 2024) $"
__version__ = "$Revision: 3.2.2 $"
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
from typing import Optional

from PyQt5 import QtWidgets

from ccpn.framework.PathsAndUrls import \
    macroPath, \
    widgetsPath, \
    CCPN_ARCHIVES_DIRECTORY
from ccpn.framework.Application import getApplication

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


FILE_MENU = 'File'
FILE_OPEN_RECENT = 'Open Recent'
FILE_ARCHIVE = 'Archive'
FILE_RESTORE_FROM_ARCHIVE = 'Restore From Archive...'
FILE_LAYOUT = 'Layout'
FILE_LAYOUT_OPEN_PREDEFINED = 'Open pre-defined'


VIEW_MENU = 'View'
VIEW_SHOW_MODULES = 'Show/hide Modules'

MACRO_MENU = 'Macro'
MACRO_RUN_CCPN = 'Run CCPN Macros'
MACRO_RUN_RECENT = 'Run Recent'

PLUGINS_MENU = 'Plugins'
USER_PLUGINS_MENU = 'User Plugins'
CCPN_PLUGINS_MENU = 'CCPN Plugins'

HELP_MENU = 'Help'
TUTORIALS_MENU = 'Tutorials'
HOWTOS_MENU = 'How-Tos'

SEPARATOR = ()
DYNAMIC_FILL = []


def getMenuDefs():
    """:return The MenuDefs (singleton) instance
    """
    app = getApplication()
    return MenusDefs(application=app)


@singleton
class MenusDefs(list):
    """A class to implement the menu definitions and callback rountines
    Used by MainWindow to initialiase the menuBar
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

        (FILE_MENU, [
            ("New", self._newProjectCallback, [('shortcut', '⌃n')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (),
            ("Open...", self._openProjectCallback, [('shortcut', '⌃o')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (FILE_OPEN_RECENT, DYNAMIC_FILL),
            ("Load Data...", self._loadDataCallback, [('shortcut', 'ld')]),
            (),
            ("Save", self._saveCallback, [('shortcut', '⌃s')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Save As...", self._saveAsCallback, [('shortcut', 'sa')]),
            (),
            ("Import", [
                ("Nef File", self._importNefCallback, [('shortcut', 'in'), ('enabled', True)]),
                ("NmrStar File", self._loadNMRStarFileCallback, [('shortcut', 'bi')]),
                ]
            ),
            ("Export", [
                ("Nef File", self._exportNEFCallback, [('shortcut', 'ex'), ('enabled', True)]),
                ]
            ),
            (),
            (FILE_LAYOUT, [
                ("Save", self._saveLayoutCallback, [('enabled', True)]),
                ("Save as...", self._saveLayoutAsCallback, [('enabled', True)]),
                (),
                ("Restore last", self._restoreLastSavedLayoutCallback, [('enabled', True)]),
                ("Restore from file...", self._restoreLayoutFromFileCallback, [('enabled', True)]),
                (),
                (FILE_LAYOUT_OPEN_PREDEFINED, DYNAMIC_FILL),
                ]
            ),
            ("Summary", self._showProjectSummaryPopup),
            (FILE_ARCHIVE, self._archiveProjectCallback, [('enabled', False)]),
            (FILE_RESTORE_FROM_ARCHIVE, self._restoreFromArchiveCallback, [('enabled', False)]),
            (),
            ("Preferences...", self._showApplicationPreferences, [('shortcut', '⌃,')]),
            (),
            ("Quit", self._quitCallback, [('shortcut', '⌃q')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ]
        ),

        ('Edit', [
            ("Undo", self._undoCallback, [('shortcut', '⌃z')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Redo", self._redoCallback, [('shortcut', '⌃y')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            (),
            ("Cut", self._nyi, [('shortcut', '⌃x'), ('enabled', False)]),
            ("Copy", self._nyi, [('shortcut', '⌃c'), ('enabled', False)]),
            ("Paste", self._nyi, [('shortcut', '⌃v'), ('enabled', False)]),
            ("Select all", self._nyi, [('shortcut', '⌃a'), ('enabled', False)]),
            ]
        ),

        (VIEW_MENU, [
            ("Chemical Shift Table", partial(app.showChemicalShiftTable, selectFirstItem=True), [('shortcut', 'ct')]),
            ("NmrResidue Table", partial(app.showNmrResidueTable, selectFirstItem=True), [('shortcut', 'nt')]),
            ("Residue Table", partial(app.showResidueTable, selectFirstItem=True)),
            ("Peak Table", partial(app.showPeakTable, selectFirstItem=True), [('shortcut', 'pt')]),
            ("Integral Table", partial(app.showIntegralTable, selectFirstItem=True), [('shortcut', 'it')]),
            ("Multiplet Table", partial(app.showMultipletTable, selectFirstItem=True), [('shortcut', 'mt')]),
            ("Data Table", partial(app.showDataTable, selectFirstItem=True), [('shortcut', 'dt')]),
            ("Restraint Table", partial(app.showRestraintTable, selectFirstItem=True), [('shortcut', 'rt')]),
            ("Violation Table", partial(app.showViolationTable, selectFirstItem=True), [('shortcut', 'vt')]),
            ("Structure Table", partial(app.showStructureTable, selectFirstItem=True), [('shortcut', 'st')]),
            (),
            ("Restraint Analysis Inspector", partial(app.showRestraintAnalysisTable, selectFirstItem=True), [('shortcut', 'at')]),
            ("Chemical Shift Mapping (Beta)", app.showChemicalShiftMappingModule, [('shortcut', 'cm')]),
            ("Relaxation Analysis (Beta)", app.showRelaxationModule, [('shortcut', 'ra')]),
            ("Notes Editor", partial(app.showNotesEditor, selectFirstItem=True), [('shortcut', 'no')]),
            (),
            ("In Active Spectrum Display", [
                ("Show/Hide Toolbar", self._toggleToolbarCallback, [('shortcut', 'tb')]),
                ("Show/Hide Spectrum Toolbar", self._toggleSpectrumToolbarCallback, [('shortcut', 'sb')]),
                ("Show/Hide Phasing Console", self._togglePhaseConsoleCallback, [('shortcut', 'pc')]),
                (),
                ("Set Zoom...", self._setZoomCallback, [('shortcut', 'sz')]),
                # ("Reset Zoom", self._resetZoomCallback, [('shortcut', 'rz')]),
                (),
                ("New SpectrumDisplay with New Strip, Same Axes", self._copyStripCallback, []),
                (" .. with X-Y Axes Flipped", self._flipXYAxisCallback, [('shortcut', 'xy')]),
                (" .. with X-Z Axes Flipped", self._flipXZAxisCallback, [('shortcut', 'xz')]),
                (" .. with Y-Z Axes Flipped", self._flipYZAxisCallback, [('shortcut', 'yz')]),
                (" .. with Axes Flipped...", self._flipArbitraryAxesCallback, [('shortcut', 'fa')]),
                (),
                ("Auto-arrange Labels", self._arrangeLabelsCallback, [('shortcut', 'av')]),
                ("Reset Labels", self._resetLabelsCallback, [('shortcut', 'rv')]),
                ]
            ),
            ("Show/Hide Crosshairs", self._toggleCrosshairCallback, [('shortcut', 'ch')]),
            (),
            (VIEW_SHOW_MODULES, DYNAMIC_FILL),
            ("Python Console", self._toggleConsoleCallback, [('shortcut', '  ')]),
            ]
        ),

        ('Spectrum', [
            ("Load Spectra...", self._loadSpectraCallback, [('shortcut', 'ls')]),
            # ("Spectrum Groups...", self._spectrumGroupsCallback, [('shortcut', 'ss')]), # multiple edit temporarly disabled
            # (),
            ("Validate Paths...", self._validatePathsCallback, [('shortcut', 'vp')]),
            ("Set Experiment Types...", self._experimentTypesCallback, [('shortcut', 'et')]),
            ("Copy into Project...", self._copyToProjectCallback, []),
            (),
            ("Pick Peaks", [
                ("Pick 1D Peaks...", self._peakPick1DCallback, [('shortcut', 'p1')]),
                ("Pick nD Peaks...", self._peakPickNDCallback, [('shortcut', 'pp')]),
                ]
            ),
            ("Copy PeakList...", self._copyPeakListCallback, [('shortcut', 'cl')]),
            ("Copy Peaks...", self._copyPeaksCallback, [('shortcut', 'cp')]),
            ("Peak Collections...", self._peakCollectionsCallback, [('shortcut', 'sc')]),
            ("Estimate Peak Volumes...", self._estimateVolumesCallback, [('shortcut', 'ev')]),
            ("Estimate Current Peak Volumes", self._estimateCurrentVolumesCallback, [('shortcut', 'ec')]),
            ("Reorder PeakList Axes...", self._reorderPeakListAxesCallback, [('shortcut', 'rl')]),
            (),
            ("Pseudo-Spectrum to SpectrumGroup...", self._pseudoSpectrumCallback),
            ("Make Projection...", self._makeProjectionCallback, [('shortcut', 'pj')]),
            ("Convert...", self._convertSpectrumCallback, []),
            (),
            ("Make Strip Plot...", app.makeStripPlot, [('shortcut', 'sp')]),
            ("Print to File...", self._printToFileCallback, [('shortcut', '⌃p')]),
            ]
        ),

        ('Molecules', [
            ("New Chain...", self._createChainCallback),
            ("New Chain from FASTA...", self._loadDataCallback),
            (),
            ("Load ChemComp from Xml...", self._loadDataCallback),
            ("Edit Molecular Bonds...", self._editMolecularBondsCallback, ),
            # ("Inspect...", self.inspectMolecule, [('enabled', False)]),
            (),
            ("Residue Information", app.showResidueInformation, [('shortcut', 'ri')]),
            ("Reference Chemical Shifts", app.showReferenceChemicalShifts, [('shortcut', 'rc')]),
            ]
        ),

        (MACRO_MENU, [
            ("New Macro Editor", self._showMacroEditorCallback, [('shortcut', 'nm')]),
            (),
            ("Open User Macro...", self._openMacroCallback, [('shortcut', 'om')]),
            ("Open CCPN Macro...", partial(self._openMacroCallback, directory=macroPath)),
            (),
            ("Run...", app.runMacro, [('shortcut', 'rm')]),
            (MACRO_RUN_RECENT, DYNAMIC_FILL),
            (MACRO_RUN_CCPN, DYNAMIC_FILL),
            (),
            ("Define Macro Shortcuts...", self._defineUserShortcutsCallback, [('shortcut', 'du')]),
            ]
        ),

        (PLUGINS_MENU, [
            (CCPN_PLUGINS_MENU, DYNAMIC_FILL),
            (USER_PLUGINS_MENU, DYNAMIC_FILL),
            ]
        ),

        (HELP_MENU, [
            (TUTORIALS_MENU, DYNAMIC_FILL),
            ("Show Tip of the Day", partial(app._displayTipOfTheDay, standalone=True)),
            ("Key Concepts", app._displayKeyConcepts),
            ("Show Shortcuts", self._showShortcuts),
            ("Show API Documentation", self._showVersion3Documentation),
            (),
            ("CcpNmr Homepage", self._showAboutCcpn),
            ("CcpNmr V3 Forum", self._showForum),
            (),
            # ("Inspect Code...", self.showCodeInspectionPopup, [('shortcut', 'gv'), ('enabled', False)]),
            # ("Show Issues...", self.showIssuesList),
            ("Check for Updates...", ui._checkForUpdates),
            (),
            ("Register...", self._showRegisterPopup),
            ("Show License...", self._showCcpnLicense),
            ("About CcpNmr V3...", self._showAboutPopup),
            ]
        ),

        ])  # end extend

        # optionally add debug menu
        if app._isInDebugMode:
            self._addMenuDef(
        ('Development', [
            ("Set debug off", partial(app.setDebug, 0)),
            ("Set debug level 1", partial(app.setDebug, 1)),
            ("Set debug level 2", partial(app.setDebug, 2)),
            ("Set debug level 3", partial(app.setDebug, 3)),
            ]
        ), position = -1

        )  # end insert

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

        _path = aPath(self.application.preferences.general.userWorkingPath or '~').filepath / (self.project.name + NEFEXTENSION)
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
        popup = PreferencesPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, preferences=self.application.preferences)
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
            popup = ValidateSpectraPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, spectra=spectra, defaultSelected=defaultSelected)
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

        _spectra = [sp for sp in self.project.spectra if sp.hasValidPath() and not sp._isInside and not sp.isEmptySpectrum()]
        if len(_spectra) == 0:
            MessageDialog.showWarning(title, 'There are no spectra to be copied', parent=self.mainWindow)
            return

        _size = '%.1f' % (sum([sp.dataSource.expectedFileSizeInBytes for sp in _spectra]) / (1024*1024))
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
                SpectrumGroupEditor(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, editMode=True, obj=self.project.spectrumGroups[0]).exec_()

    def _pseudoSpectrumCallback(self):
        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Pseudo Spectrum to SpectrumGroup Popup cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.', 'Pseudo Spectrum to SpectrumGroup Popup cannot be displayed')
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
            popup = SpectrumProjectionPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            popup.exec_()

    def _printToFileCallback(self):
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

    #-----------------------------------------------------------------------------------------
    # View -->
    #-----------------------------------------------------------------------------------------

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
        self.ui._flipArbitraryAxes(strip=self.current.strip, usePosition=False)

    def _toggleConsoleCallback(self):
        """Toggles whether python console is displayed at bottom of the main window.
        """
        self.mainWindow.toggleConsole()

    def _toggleCrosshairCallback(self):
        """Toggles whether crosshairs are displayed in all SpectrumDisplays.
        """
        self.mainWindow.toggleCrosshair()

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
        """Displays the molecular-bonds popup.
        """
        from ccpn.ui.gui.popups.MolecularBondsPopup import MolecularBondsPopup
        popup = MolecularBondsPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()

    #-----------------------------------------------------------------------------------------
    # Macro -->
    #-----------------------------------------------------------------------------------------

    def _showMacroEditorCallback(self):
        """Displays macro editor. Just handing down to MainWindow for now
        """
        self.mainWindow.newMacroEditor()

    def _openMacroCallback(self, directory=None):
        """ Select macro file and on MacroEditor.
        """
        from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog

        mainWindow = self.ui.mainWindow
        dialog = MacrosFileDialog(parent=mainWindow, acceptMode='open', fileFilter='*.py', directory=directory)
        dialog._show()
        path = dialog.selectedFile()
        if path is not None:
            mainWindow.newMacroEditor(path=path)

    def _defineUserShortcutsCallback(self):
        from ccpn.ui.gui.popups.ShortcutsPopup import ShortcutsPopup
        ShortcutsPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()

    #-----------------------------------------------------------------------------------------
    # Help -->
    #-----------------------------------------------------------------------------------------

    def _showBeginnersTutorial(self):
        from ccpn.framework.PathsAndUrls import beginnersTutorialPath
        self.application._systemOpen(beginnersTutorialPath)

    def _showBackboneTutorial(self):
        from ccpn.framework.PathsAndUrls import backboneAssignmentTutorialPath
        self.application._systemOpen(backboneAssignmentTutorialPath)

    def _showCSPtutorial(self):
        from ccpn.framework.PathsAndUrls import cspTutorialPath
        self.application._systemOpen(cspTutorialPath)

    def _showScreenTutorial(self):
        from ccpn.framework.PathsAndUrls import screenTutorialPath
        self.application._systemOpen(screenTutorialPath)

    def _showVersion3Documentation(self):
        """Displays CCPN wrapper documentation in a module.
        """
        from ccpn.framework.PathsAndUrls import ccpnDocumentationUrl, documentationPath

        if self.application.preferences.appearance.useOnlineDocumentation:
            self.application._showHtmlFile("Analysis Version-3 Documentation", ccpnDocumentationUrl)
        else:
            self.application._showHtmlFile("Analysis Version-3 Documentation", documentationPath)

    def _showForum(self):
        """Displays Forum in a module.
        """
        from ccpn.framework.PathsAndUrls import ccpnForum
        self.application._showHtmlFile("Analysis Version-3 Forum", ccpnForum)

    def _showShortcuts(self):
        from ccpn.framework.PathsAndUrls import shortcutsPath
        self.application._systemOpen(shortcutsPath)

    def _showAboutPopup(self):
        from ccpn.ui.gui.popups.AboutPopup import AboutPopup
        popup = AboutPopup(parent=self.ui.mainWindow)
        popup.exec_()

    def _showAboutCcpn(self):
        from ccpn.framework.PathsAndUrls import ccpnUrl
        self.application._showHtmlFile("About CCPN", ccpnUrl)

    def _showIssuesList(self):
        from ccpn.framework.PathsAndUrls import ccpnIssuesUrl
        self.application._showHtmlFile("CCPN Issues", ccpnIssuesUrl)

    def _showTutorials(self):
        from ccpn.framework.PathsAndUrls import ccpnTutorials
        self.application._showHtmlFile("CCPN Tutorials", ccpnTutorials)

    def _showRegisterPopup(self):
        """Open the registration popup
        """
        self.ui._registerDetails()

    def _showCcpnLicense(self):
        from ccpn.framework.PathsAndUrls import ccpnLicenceUrl
        self.application._showHtmlFile("CCPN Licence", ccpnLicenceUrl)

    #-----------------------------------------------------------------------------------------
    # Inactive
    #-----------------------------------------------------------------------------------------

    def _showLicense(self):
        from ccpn.framework.PathsAndUrls import licensePath
        self.application._showHtmlFile("CCPN Licence", licensePath)

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

    def _getAsDict(self) -> dict:
        """:return self as a dict-of-dict-of-ActionDict"""
    #-----------------------------------------------------------------------------------------
    # Implementation methods
    #-----------------------------------------------------------------------------------------

    def _showHtmlFile(self, title, urlPath):
        """Display html files
        Optional program QT viewer or native webbrowser (currently disabled)
        depending on useNativeWebbrowser option in preferences
        """
        useNative = self.application.preferences.general.useNativeWebbrowser
        if not useNative:
            getLogger().debug('non-native HtmlModule has been disabled due to PyQT bugs')

        if True:
            import webbrowser
            import posixpath

            # may be a Path object
            urlPath = str(urlPath)

            urlPath = urlPath or ''
            if (urlPath.startswith('http://') or urlPath.startswith('https://')):
                pass
            elif urlPath.startswith('file://'):
                urlPath = urlPath[len('file://'):]
                urlPath = urlPath.replace(os.sep, posixpath.sep) if isWindowsOS() else f'file://{urlPath}'

            elif isWindowsOS():
                urlPath = urlPath.replace(os.sep, posixpath.sep)
            else:
                urlPath = f'file://{urlPath}'

            webbrowser.open(urlPath)

    def _addMenuDef(self, menuDef, position):
        """Add an new menuDef tuple at specified position
        """
        self.insert(position, menuDef)

    def _addMenuItem(self, menuName, menuItem, position):
        """Add a new menuItem to the existing menuName at specified position
        """
        if (indx := self._getMenuIndex(menuName)) == -1:
            raise ValueError(f'No menu with name {menuName}')
        self[indx][1].insert(position, menuItem)

    def _addMenuItems(self, menuName, menuItems, position):
        """Add a new menuItems to the existing menuName starting at specified position
        """
        for n, menuItem in enumerate(menuItems):
            self._addMenuItem(menuName, menuItem, position + n)

    def _getMenuIndex(self, menuName) -> int:
        """:return index for menuName or -1 when not found
        """
        for indx, mDef in enumerate(self):
            if mDef[0] == menuName:
                return indx

        #  no matches found; return -1
        return -1

    @staticmethod
    def _testShortcuts0():
        print('>>> Testing shortcuts0')

    @staticmethod
    def _testShortcuts1():
        print('>>> Testing shortcuts1')

#end class

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


class MenuNode(dict, Tree):
    """Just a class to define the MenuNode and store the Menu and Action objects
    """
    def __init__(self, parent, name, callback=None, isSeparator=False, isAction=False, options={}):

        super().__init__()
        Tree.__init__(self, parent=None)

        # self.parent = parent
        self.name = name
        self.callback = callback
        self.isSeparator = isSeparator
        self.isAction = isAction
        self.options = options

        self.isDynamic = False
        self.dynamicCallback = None

        self.widget = None

        if parent is not None:
            parent._addChild(self)

    @property
    def level(self) -> int:
        """
        :return the level of the MenuNode in the nested structure (root has level 0)
        """
        return len(self.anchestors())
        # _result = 0
        # _node = self
        # while _node.parent is not None:
        #     _result += 1
        #     _node = _node.parent
        # return _result

    def makeDynamic(self, callback):
        """Make MenuNode a dynamically updated one, calling callback when it is about to show
        """
        self.isDynamic = True
        self.dynamicCallback = callback
        if self.widget is None:
            raise RuntimeError('Cannot make MenuNode dynamic without a widget')
        self.widget.aboutToShow.connect(callback)

    def print(self):
        """
        print Tree of self with indentation
        """
        level = self.level
        tabs = '\t'*level if level else ''
        print(f'{tabs}{self}  {self.options}')
        for key, val in self.items():
            val.print()

    def __str__(self):
        return f'<MenuNode: {self.name}, level={self.level}>'

    __repr__ = __str__


def traverse(theList, parent=None, name='root') -> MenuNode:
    """Traverse the menuDefs list, converting it to a nested MenuNode data structure.
    """
    result = MenuNode(parent=parent, name=name)
    separatorIndex = 0  # This gives each separator a unique name

    for item in theList:
        if len(item) == 0:
            name = f'separator_{separatorIndex}'
            result[name] = MenuNode(parent=result, name=name, isSeparator=True)
            separatorIndex += 1

        elif len(item) == 1:
            # this should not happen
            raise RuntimeError('Invalid menu definitions')

        elif len(item) == 2:
            name = item[0]
            if isinstance(item[1], (tuple, list)):
                result[name]=traverse(item[1], parent=result, name=name)
            elif callable(item[1]):
                callback=item[1]
                result[name]=MenuNode(parent=result, name=name, callback=callback, isAction=True)
            else:
                raise RuntimeError('Invalid menu definitions')

        elif len(item) == 3:
            name = item[0]
            callback=item[1]
            options = dict(item[2])
            result[name] = MenuNode(parent=result, name=name, callback=callback, options=options)

    return result




"""
gui. -->
    _updateCheckableMenuItems
    
mainWindow.  -->
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
    _updateRestoreArchiveMenu
    getMenuAction
    searchMenuAction
    _clearRecentProjects
    _clearRecentMacros
    
GuiMainWindow.  -->
    _attacheTutorialsMenuAction
    _fillTutorialsMenu
        --> How-to's menu

FrameWork.  -->
    _getProjectFiles
    
    
dynamic menus:; uses aboutToShow PyQt signal
_fill ....

"""
