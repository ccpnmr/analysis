
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2025-08-19 12:13:23 +0100 (Tue, August 19, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-18 10:10:29 +0100 (Mon, August 18, 2025) $"

#=========================================================================================
# Start of code
#=========================================================================================

from typing import Any, Optional
from functools import partial
import pandas as pd
from ccpn.api import PluginBase, PluginGUIModule, aPath, undo, getLogger
from collections import OrderedDict as od
import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget

SettingsWidgetFixedWidths = (200, 350, 350)
SOURCE_PEAKLIST = 'SOURCE_PEAKLIST'
WORKING_DIR = 'WORKING_DIR'
OUTPUT_FILE = 'OUTPUT_FILE'
RUN_BUTTON = 'RUN_BUTTON'

class DemoGuiModule(PluginGUIModule):
    """A class to create the GUI element of the plugin as a GuiModule """

    def getWidgetDefinitions(self) :
        """
        An OrderedDict describing the GUI widgets for this plugin.
        Each entry defines one widget, keyed by its variable name, with metadata
        such as label, type (class, not instance), and keyword arguments for
        initialisation. The order controls how widgets are displayed in the GUI.
        :return: OrderedDict of widgets defs
        """
        self.widgetDefinitions = od((
            (SOURCE_PEAKLIST,
             {'label': 'PeakList',
              'tipText': 'Select a PeakList',
              'callBack': None,
              'type': objectPulldowns.PeakListPulldown,
              'kwds': {'labelText': 'PeakList',
                       'tipText': 'Select a PeakList',
                       'filterFunction': None,
                       'showSelectName':True,
                       'objectName': SOURCE_PEAKLIST,
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (WORKING_DIR,
             {'label'  : 'Working Dir',
              'tipText': 'Select the working directory',
              'enabled': True,
              'type'   : compoundWidget.EntryPathCompoundWidget,
              '_init'  : None,
              'kwds'   : {
                  'labelText'   :  'Working Dir',
                  'tipText'     : 'Select the working directory',
                  'entryText'   : str(self.plugin._workDirPath),
                  'fixedWidths' : SettingsWidgetFixedWidths,
                  'compoundKwds': {'lineEditMinimumWidth': 300}
                  }}),
            (OUTPUT_FILE,
             {'label'  : 'Output File',
              'tipText': 'Select an output File',
              'enabled': True,
              'type'   : compoundWidget.EntryPathCompoundWidget,
              '_init'  : None,
              'kwds'   : {
                  'labelText'   : 'Output File',
                  'tipText'     : 'Select an output File',
                  'entryText'   : str(self.plugin.outputPath),
                  'fixedWidths' : SettingsWidgetFixedWidths,
                  'compoundKwds': {'lineEditMinimumWidth': 300}
                  }}),
            (RUN_BUTTON,
             {'label'   : 'Run The Plugin',
              'tipText' : 'Run The Plugin',
              'callBack': self._runCallback,
              'type'    : compoundWidget.ButtonCompoundWidget,
              '_init'   : None,
              'kwds'    : {'labelText'  : 'Run',
                           'text'       : 'Execute',  # this is the Button name
                           'hAlign'     : 'left',
                           'tipText'    : 'Run The Plugin',
                           'fixedWidths': SettingsWidgetFixedWidths}}),
            ))
        return self.widgetDefinitions


class MyPickerModule(PluginBase):
    def __init__(self,  descriptor, application):
        """
        Plugin initialisation. Called automatically by the PluginManager.

        Framework-provided arguments:
              :param descriptor: Metadata object describing the plugin (name, version, entry point, etc.).
              :param application: Reference to the main application instance, used to access
                                  shared services such as project data, managers, and configuration.
        Notes:
          - These parameters are injected by the plugin manager and are not intended to be supplied by end users.

        - Additional static attributes are defined here in the init to configure the external program.
            These values are fixed for this plugin and are not user-configurable from the GUI.
            _workDirName : The dedicated working directory where input/output files live.
            _exeRelPath  : Relative path to the external executable/script.
            _workDirPath : Absolute path to the working directory (under the plugin’s root).
            execPath     : Full path to the executable, resolved at startup.
            Since these are invariant for the demo, they are set globally at init time  rather than being exposed as GUI options.

        """
        super().__init__(descriptor, application)
        self.ui = DemoGuiModule # we need to attach the Gui element here. See class above

        # the various attr needed to run the external program. See docs in the init
        self._workDirName = 'ThePeakPickerProgram'
        self._exeRelPath = aPath('DemoPeakPicker.sh')
        self._workDirPath = self.rootDir / aPath(self._workDirName)
        self.execPath = self._workDirPath / self._exeRelPath

        # Placeholders to fill the gui, changed by the users
        self.inputPath = self._workDirPath / aPath('GB1_HSQC.ucsf')
        self.outputPath = self._workDirPath / aPath('GB1_peaks.csv')


    def run(self, **kwargs: Any):
        """
        Execute the external peak-picking program and set up monitoring of its output.

        This method is called automatically when the user clicks *Run* in the plugin’s GUI.
        The keyword arguments (`kwargs`) are not manually provided, but are auto-generated
        from the plugin’s GUI layer — specifically from the `getWidgetDefinitions()` method
        of the GUI class. Each widget contributes a value that is passed here under its
        symbolic name (e.g. SOURCE_PEAKLIST, OUTPUT_FILE).

        Workflow:
          1. Retrieve the selected PeakList PID, output file path, and working directory
             from `kwargs`.
          2. Resolve the PeakList object from the project and obtain the input spectrum path.
          3. Launch the external program asynchronously using the plugin manager’s
             `ExternalProcessRunner`.
          4. Start a file watcher on the working directory (restricted to `.csv` files),
             with `_onFileChanged` as callback to update peaks when the output changes.

        :param kwargs: Auto-generated keyword arguments derived from GUI selections
                       (see `getWidgetDefinitions()`):
                           - SOURCE_PEAKLIST → PID of selected PeakList
                           - OUTPUT_FILE     → Path to output CSV
                           - WORKING_DIR     → Working directory
        :return: None
        """

        # get the various arguments needed to execute the external program
        selectedPeakListPid = kwargs.get(SOURCE_PEAKLIST)
        outputPath = kwargs.get(OUTPUT_FILE)
        workDirPath = kwargs.get(WORKING_DIR)
        peakList = self.application.project.getByPid(selectedPeakListPid)
        if not peakList:  return
        spectrum = peakList.spectrum
        inputPath = spectrum.filePath

        # execute the command to run an external program using the pluginManager built-in tools.
        self.runCommandOnBackground(self.execPath, args=[inputPath, outputPath])

        # start the startFileWatcher and pass-in some additional arguments. The default arg is a mappingDictionary of changes.
        self.startFileWatcher([workDirPath],  callbackFunc=partial(self._onFileChanged, peakList, outputPath), includeSuffixes={'.csv'})

    def _onFileChanged(self, peakList, outputPath, changesDict):
        """
        Reacts to file system changes detected by the file watcher.

        This method is triggered whenever the watcher reports a change in the
        output directory (for example, when the external program writes a new
        peak list file). It compares the contents of the updated CSV file with
        the current peaks in the given `peakList`, and synchronises them:

          • Peaks present in the CSV but missing from the current list are added.
          • Peaks present in the current list but absent in the CSV are deleted.

        :param peakList: The CCPN peak list object to be updated.
        :param outputPath: Path to the CSV file written by the external program.
        :param changesDict: Dictionary of change events reported by the file watcher.
                            See the watcher class documentation for details.
        :return: None
        This is only one possible application of the file watcher: you could adapt
        the same pattern to update spectra, parameters, or any other Analysis
        objects when external data changes.
        """
        getLogger().info(f'Detected changes: {changesDict}. \n updating PeakList: {peakList}')

        # Map coords -> peak object
        existing = {tuple(map(float, (*p.ppmPositions, p.height))): p
                    for p in peakList.peaks}
        # Read CSV — using hard-coded column names for demonstration only,  as this is a simplified, toy-style example program
        df = pd.read_csv(outputPath).dropna(subset=['x', 'y', 'height'])
        file_coords = {tuple(map(float, (x, y, h))) for x, y, h in zip(df['x'], df['y'], df['height'])}

        # Delete peaks missing in CSV
        for coord in set(existing) - file_coords:
            existing[coord].delete()

        # Add peaks missing in current list
        for coord in file_coords - set(existing):
            x, y, h = coord
            peakList.newPeak(ppmPositions=(x, y), height=h)
