

import pandas as pd
from ccpn.api import PluginBase, PluginGUIModule, aPath, undo

class DemoGuiModule(PluginGUIModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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

        self.runCommandOnBackground(self.execPath, args=[self.inputPath, self.outputPath])
        self.startFileWatcher([self._workDirPath], callbackFunc=self._onFileChanged, includeSuffixes={'.csv'})

    def _onFileChanged(self, info):
        print('INFO', info)
        project = self.application.project

        for spectrum in project.spectra:
            if str(spectrum.filePath) != str(self.inputPath):
                continue
            peakList = spectrum.peakLists[-1]
            # Map coords -> peak object
            existing = {tuple(map(float, (*p.ppmPositions, p.height))): p
                        for p in peakList.peaks}

            # Read CSV
            df = pd.read_csv(self.outputPath).dropna(subset=['x', 'y', 'height'])
            file_coords = {tuple(map(float, (x, y, h))) for x, y, h in zip(df['x'], df['y'], df['height'])}

            # Delete peaks missing in CSV
            for coord in set(existing) - file_coords:
                existing[coord].delete()

            # Add peaks missing in current list
            for coord in file_coords - set(existing):
                x, y, h = coord
                peakList.newPeak(ppmPositions=(x, y), height=h)