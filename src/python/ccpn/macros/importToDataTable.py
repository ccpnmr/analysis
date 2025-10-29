import pandas as pd
from ccpn.ui.gui.widgets.FileDialog import TablesFileDialog
from pathlib import Path
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo


dialog = TablesFileDialog()
dialog.exec_()
path = Path(dialog.selectedFile())
stem = path.stem
dfs = {}
while dialog.selectedFile() is not None and path.suffix not in ['.csv', '.json', '.xlsx']:
    showWarning('Incompatible File',
                'Please choose a csv, json or xlsx file.')
    dialog.exec_()
    path = Path(dialog.selectedFile())
if path.suffix == '.csv':
    dfs = {stem: pd.read_csv(path)}
elif path.suffix == '.json':
    dfs = {stem: pd.read_json(path)}
elif path.suffix == '.xlsx':
    loadedDfs = pd.read_excel(path, sheet_name=None)
    dfs = {f'{stem}_{key}': value for key, value in loadedDfs.items()}

for key, value in dfs.items():
    key = key.replace(' ', '_')
    project.newDataTable(name=key, data=value)
