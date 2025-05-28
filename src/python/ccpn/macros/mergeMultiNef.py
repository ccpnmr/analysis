from PyQt5 import QtWidgets
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog, LineEdit
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.framework.Application import getApplication
import os
import re
from ccpn.ui.gui.widgets.FileDialog import OtherFileDialog
from ccpn.util.Path import aPath

class MergeNefPopup(CcpnDialogMainWidget):
    FIXEDWIDTH = True
    title = 'Macro to merge (and load) multiple NEF Files'

    def __init__(self, parent=None, mainWindow=None, title=title, **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, size=(500, 150), **kwds)
        self.mainWindow = mainWindow
        self.application = getApplication()
        self.project = self.application.project if self.application else None

        self._createWidgets()

    def _createWidgets(self):
        row = 0
        # Folder selection widgets
        Label(self.mainWidget, text="Input Folder:", grid=(row, 0))
        self.folderEdit = LineEdit.LineEdit(self.mainWidget, grid=(row, 1))
        self.browseButton = Button(self.mainWidget, text="Browse", callback=self._browseFolder, grid=(row, 2))

        row += 1
        # Output filename widgets
        Label(self.mainWidget, text="Output Filename:", grid=(row, 0))
        self.outputEdit = LineEdit.LineEdit(self.mainWidget, text="merged.nef", grid=(row, 1))

        row += 1
        # Action buttons
        self.buttonFrame = Frame(self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 3))
        self.mergeButton = Button(self.buttonFrame, text="Merge", callback=self._merge, grid=(0, 0))
        self.mergeLoadButton = Button(self.buttonFrame, text="Merge and Load", callback=self._mergeAndLoad, grid=(0, 1))
        self.closeButton = Button(self.buttonFrame, text="Close", callback=self.reject, grid=(0, 2))


    def _browseFolder(self):
        _currentPath = self.folderEdit.text()
        if _currentPath is not None:
            _directory = aPath(_currentPath).parent.asString()
        else:
            _directory = self.project.application.dataPath.asString()

        dialog = OtherFileDialog(parent=self.mainWindow, _useDirectoryOnly=True,
                                 directory=_directory)
        dialog._show()
        if (path := dialog.selectedFile()) is not None:
            self.folderEdit.setText(str(path))


    def _mergeNefFiles(self, input_folder, output_file):
        unique_saveframes = {}
        data_line = ""

        # Get list of NEF files in directory
        nef_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.nef')]
        if not nef_files:
            raise ValueError("No NEF files found in selected directory")

        for filename in nef_files:
            file_path = os.path.join(input_folder, filename)
            with open(file_path, 'r') as f:
                content = f.read()

            # Extract data line from first file that has one
            if not data_line:
                data_match = re.search(r'^data_\S+', content, re.MULTILINE)
                if data_match:
                    data_line = data_match.group(0)

            # Extract saveframes
            saveframe_pattern = re.compile(r'(save_\S+)(.*?)(?=save_|\Z)', re.DOTALL)
            for match in saveframe_pattern.finditer(content):
                identifier = match.group(1).strip()
                saveframe_content = match.group(0).strip()

                # Add terminating 'save_' if missing
                if not saveframe_content.endswith('\nsave_'):
                    saveframe_content += '\nsave_'

                if identifier not in unique_saveframes:
                    unique_saveframes[identifier] = saveframe_content

        # Write merged output
        with open(output_file, 'w') as f:
            if data_line:
                f.write(data_line + '\n\n')
            f.write('\n\n'.join(unique_saveframes.values()))

    def _performMerge(self, loadAfter=False):
        input_folder = self.folderEdit.text().strip()
        output_filename = self.outputEdit.text().strip() or "merged.nef"

        if not input_folder:
            MessageDialog.showWarning("Missing Input", "Please select an input folder")
            return

        output_path = os.path.join(input_folder, output_filename)

        try:
            with undoBlockWithoutSideBar():
                with notificationEchoBlocking():
                    self._mergeNefFiles(input_folder, output_path)
                    msg = f"Successfully merged NEF files to:\n{output_path}"

                    if loadAfter:
                        self.application.loadData(output_path)
                        msg += "\n\nMerged file loaded into project"

                    MessageDialog.showInfo("Merge Successful", msg)

        except Exception as e:
            MessageDialog.showWarning("Merge Error", f"Error during merge process:\n{str(e)}")

    def _merge(self):
        self._performMerge(loadAfter=False)

    def _mergeAndLoad(self):
        self._performMerge(loadAfter=True)


if __name__ == '__main__':
    popup = MergeNefPopup()
    popup.exec_()