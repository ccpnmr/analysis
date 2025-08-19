from typing import Any, Optional
from functools import partial
import pandas as pd
from ccpn.api import PluginBase, PluginGUIModule, aPath, undo
from collections import OrderedDict as od
import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget

SettingsWidgetFixedWidths = (200, 350, 350)
SOURCE_PEAKLIST = 'SOURCE_PEAKLIST'
WORKING_DIR = 'WORKING_DIR'
OUTPUT_FILE = 'OUTPUT_FILE'
RUN_BUTTON = 'RUN_BUTTON'

class DemoGuiModule(PluginGUIModule):

    def getWidgetDefinitions(self) :
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
        super().__init__(descriptor, application)
        self.ui = DemoGuiModule
        self._workDirName = 'ThePeakPickerProgram'
        self._exeRelPath = aPath('DemoPeakPicker.sh')
        self._workDirPath = self.rootDir / aPath(self._workDirName)

        self.execPath = self._workDirPath / self._exeRelPath
        self.inputPath = self._workDirPath / aPath('GB1_HSQC.ucsf')
        self.outputPath = self._workDirPath / aPath('GB1_peaks.csv')


    def run(self, **kwargs: Any):
        selectedPeakListPid = kwargs.get(SOURCE_PEAKLIST)
        outputPath = kwargs.get(OUTPUT_FILE)
        workDirPath = kwargs.get(WORKING_DIR)
        pl = self.application.project.getByPid(selectedPeakListPid)
        if not pl:
            # show warning
            return
        sp = pl.spectrum
        inputPath = sp.filePath
        self.runCommandOnBackground(self.execPath, args=[inputPath, outputPath])
        self.startFileWatcher([workDirPath],
                              callbackFunc=partial(self._onFileChanged, pl, outputPath),
                              includeSuffixes={'.csv'})

    def _onFileChanged(self, peakList, outputPath, infoD):
        print('INFO', infoD)

        # Map coords -> peak object
        existing = {tuple(map(float, (*p.ppmPositions, p.height))): p
                    for p in peakList.peaks}

        # Read CSV
        df = pd.read_csv(outputPath).dropna(subset=['x', 'y', 'height'])
        file_coords = {tuple(map(float, (x, y, h))) for x, y, h in zip(df['x'], df['y'], df['height'])}

        # Delete peaks missing in CSV
        for coord in set(existing) - file_coords:
            existing[coord].delete()

        # Add peaks missing in current list
        for coord in file_coords - set(existing):
            x, y, h = coord
            peakList.newPeak(ppmPositions=(x, y), height=h)