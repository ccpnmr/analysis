"""
This file contains Framework-related Gui methods;
A first step towards separating them from the Framework class
"""
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-01-24 17:30:31 +0000 (Mon, January 24, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from tqdm import tqdm
from functools import partial
from typing import Union, Optional, List, Tuple, Sequence

from PyQt5 import QtWidgets

from ccpn.framework.PathsAndUrls import \
    userPreferencesPath,  \
    userPreferencesDirectory,  \
    macroPath, \
    CCPN_EXTENSION, \
    CCPN_ARCHIVES_DIRECTORY

from ccpn.core.IntegralList import IntegralList
from ccpn.core.PeakList import PeakList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import NotifierBase, Notifier
from ccpn.core.lib.Pid import Pid, PREFIXSEP
from ccpn.core.lib.ContextManagers import \
    catchExceptions, \
    undoBlockWithoutSideBar, \
    undoBlock, \
    notificationEchoBlocking, \
    logCommandManager
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
from ccpn.util.Path import Path, aPath

from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FileDialog import \
    ProjectFileDialog, \
    DataFileDialog, \
    NefFileDialog, \
    ArchivesFileDialog, \
    MacrosFileDialog, \
    CcpnMacrosFileDialog, \
    LayoutsFileDialog, \
    NMRStarFileDialog, \
    SpectrumFileDialog, \
    ProjectSaveFileDialog

from ccpn.ui.gui.widgets.Menu import \
    SHOWMODULESMENU, \
    CCPNMACROSMENU, \
    TUTORIALSMENU, \
    CCPNPLUGINSMENU, \
    PLUGINSMENU

class GuiBase(object):
    """Just methods taken from Framework for now
    """

    def __init__(self):
        pass

    def _setupMenus(self):
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
            ("Save", self._saveCallback, [('shortcut', '⌃s')]),  # Unicode U+2303, NOT the carrot on your keyboard.
            ("Save As...", self._saveAsCallback, [('shortcut', 'sa')]),
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
            ("Summary", self.showProjectSummaryPopup),
            ("Archive", self._archiveProjectCallback, [('enabled', False)]),
            ("Restore From Archive...", self._restoreFromArchiveCallback, [('enabled', False)]),
            (),
            ("Preferences...", self.showApplicationPreferences, [('shortcut', '⌃,')]),
            (),
            ("Quit", self._quitCallback, [('shortcut', '⌃q')]),  # Unicode U+2303, NOT the carrot on your keyboard.
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
            ("Show License", self._showCcpnLicense),
            (),
            ("CcpNmr Homepage", self.showAboutCcpn),
            ("CcpNmr V3 Forum", self.showForum),
            (),
            # ("Inspect Code...", self.showCodeInspectionPopup, [('shortcut', 'gv'),
            #                                                    ('enabled', False)]),
            # ("Show Issues...", self.showIssuesList),
            ("Check for Updates...", self._showUpdatePopup),
            ("Register...", self.showRegisterPopup),
            (),
            ("About CcpNmr V3...", self.showAboutPopup),
            ]
        ))

    #-----------------------------------------------------------------------------------------
    # callback methods
    #-----------------------------------------------------------------------------------------

    def _nyi(self):
        """Not yet implemented"""
        pass

    #-----------------------------------------------------------------------------------------
    # File --> callback methods
    #-----------------------------------------------------------------------------------------
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

    def _openProjectMenuCallback(self):
        """Just a stub for the menu setup to pass on to mainWindow, to be moved later
        """
        return self.ui.mainWindow._openProjectCallback()

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

    def _saveCallback(self):
        """The project callback"""
        succes = self._saveProject(newPath=None, createFallback=True, overwriteExisting=True)

    def _saveAsCallback(self):
        """Opens save Project as dialog box and saves project to path specified in the file dialog."""
        oldPath = self.project.path
        newPath = getSaveDirectory(self.ui.mainWindow, self.preferences)

        with catchExceptions(application=self, errorStringTemplate='Error saving project: %s', printTraceBack=True):
            if newPath:
                # Next line unnecessary, but does not hurt
                successful = self._saveProject(newPath=newPath, createFallback=False)

                if not successful:
                    getLogger().warning("Saving project to %s aborted" % newPath)
            else:
                successful = False
                getLogger().info("Project not saved - no valid destination selected")

            self._getRecentProjectFiles(oldPath=oldPath)  # this will also update the list
            self.ui.mainWindow._fillRecentProjectsMenu()  # Update the menu

            return successful

    def _archiveProjectCallback(self):

        if (path := self.project.makeArchive()) is None:
            MessageDialog.showInfo('Archive Project',
                                   'Unable to archive Projec' )

        else:
            MessageDialog.showInfo('Archive Project',
                                   'Project archived to %s' % path )

            self.ui.mainWindow._updateRestoreArchiveMenu()

    def _restoreFromArchiveCallback(self):
        """Restore a project from archive
        """
        archivesDirectory = aPath(self.project.path) / CCPN_ARCHIVES_DIRECTORY
        _filter = '*.tgz'
        dialog = ArchivesFileDialog(parent=self.ui.mainWindow,
                                    acceptMode='select',
                                    directory=self._archiveDirectory,
                                    fileFilter=_filter)
        dialog._show()
        archivePath = dialog.selectedFile()

        if archivePath and \
           (newProject := self.restoreFromArchive(archivePath)) is not None:
            MessageDialog.showInfo('Restore from Archive',
                                   'Project restored as %s' % newProject.path )

    def showProjectSummaryPopup(self):
        """Show the Project summary popup.
        """
        from ccpn.ui.gui.popups.ProjectSummaryPopup import ProjectSummaryPopup

        if self.ui:
            popup = ProjectSummaryPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, modal=True)
            popup.show()
            popup.raise_()
            popup.exec_()

    def _quitCallback(self, event=None):
        """
        Saves application preferences. Displays message box asking user to save project or not.
        Closes Application.
        """
        self.ui.mainWindow._closeEvent(event=event)

    #-----------------------------------------------------------------------------------------
    # Spectra --> callback methods
    #-----------------------------------------------------------------------------------------
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
            _path = aPath(path)
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

    #-----------------------------------------------------------------------------------------
    # Help -->
    #-----------------------------------------------------------------------------------------

    def _showCcpnLicense(self):
        from ccpn.framework.PathsAndUrls import ccpnLicenceUrl
        self._showHtmlFile("CCPN Licence", ccpnLicenceUrl)

    def _showUpdatePopup(self):
        """Open the update popup
        CCPNINTERNAL: Also called from.Gui._executeUpdates
        """
        from ccpn.framework.update.UpdatePopup import UpdatePopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            updatePopup = UpdatePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
            updatePopup.exec_()

            # if updates have been installed then popup the quit dialog with no cancel button
            if updatePopup._numUpdatesInstalled > 0:
                self.ui.mainWindow._closeWindowFromUpdate(disableCancel=True)

        else:
            MessageDialog.showWarning('Check For Updates',
                                      'Could not connect to the update server, please check your internet connection.')

    #-----------------------------------------------------------------------------------------
    # Inactive
    #-----------------------------------------------------------------------------------------

    def _showLicense(self):
        from ccpn.framework.PathsAndUrls import licensePath
        self._showHtmlFile("CCPN Licence", licensePath)

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
    # Menu Implementation methods
    #-----------------------------------------------------------------------------------------

    def _addApplicationMenuSpec(self, spec, position=-3):
        """Add an entirely new menu at specified position"""
        self._menuSpec.insert(position, spec)

    def _addApplicationMenuItem(self, menuName, menuItem, position):
        """Add a new item to an existing menu at specified position"""
        for spec in self._menuSpec:
            if spec[0] == menuName:
                spec[1].insert(position, menuItem)
                return

        raise Exception('No menu with name %s' % menuName)

    def _addApplicationMenuItems(self, menuName, menuItems, position):
        """Add a new items to an existing menu starting at specified position"""
        for n, menuItem in enumerate(menuItems):
            self._addApplicationMenuItem(menuName, menuItem, position + n)

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

    def _testShortcuts0(self):
        print('>>> Testing shortcuts0')

    def _testShortcuts1(self):
        print('>>> Testing shortcuts1')

#end class

#-----------------------------------------------------------------------------------------
# Helper code
#-----------------------------------------------------------------------------------------

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

        newPath = aPath(newPath).assureSuffix(CCPN_EXTENSION)
        if ( newPath.exists() and
             newPath.is_file() or (newPath.is_dir() and newPath.listDirFiles() > 0)
           ):
            # should not really need to check the second and third condition above, only
            # the Qt dialog stupidly insists a directory exists before you can select it
            # so if it exists but is empty then don't bother asking the question
            title = 'Overwrite path'
            msg = 'Path "%s" already exists, continue?' % newPath
            if not MessageDialog.showYesNo(title, msg):
                newPath = ''

        return newPath
