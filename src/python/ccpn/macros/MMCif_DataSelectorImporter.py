
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import numpy
import re
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.FileDialog import OtherFileDialog
from ccpn.ui.gui.widgets import ButtonList
from ccpn.ui.gui.widgets.HLine import LabeledHLine
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Path import aPath
from ccpn.core.DataTable import TableFrame



class MMCif_DataSelectorImporter(CcpnDialogMainWidget):
    """
    Basic setup principals of GUI based macros
    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    _GREY = '#888888'

    title = 'MMCif_DataSelectorImporter'

    def __init__(self, parent=None, mainWindow=None, title=title,  **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(500, 500), minimumSize=None, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project

        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()

        # enable the buttons

        self.setOkButton(callback=self._okCallback, tipText ='Okay', text='OK', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

        # initialise the buttons and dialog size
        self._postInit()

    def _getPathFromDialog(self):
        """Select a new path from using a dialog
        """
        _path = self.project.application.dataPath
        dialog = FileDialog(parent=self.mainWindow, directory=str(_path))
        dialog._show()

        if (path := dialog.selectedFile()) is not None:
            self.pathData.setText(str(path))
            self._loadRunData()

    def _createWidgets(self):
        """Make the widgets
        """

        row = 0


        pathFrame = Frame(parent=self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 5))
        self.pathLabel = Label(pathFrame, text="Path to MMCif/PDBx File", grid=(row, 0), hAlign='left')
        self.pathData = PathEdit(pathFrame, grid=(row, 1), gridSpan=(1, 1), vAlign='t')
        self.pathData.setMinimumWidth(400)

        row += 1
        self.pathDataButton = Button(pathFrame, grid=(row, 2), callback=self._getPathFromDialog,
                                     icon='icons/directory', hPolicy='fixed')
        self.pathData.set('/Users/Eliza/Downloads/2af8.cif')

        row += 1
        self.listWidgetPair = ListWidgetPair(self, grid=(row, 0), gridSpan=(1, 2))

        row += 1


    def _okCallback(self):
        """Clicked 'OK':
        """
        print(self.listWidgetPair.rightList.getTexts())
        loopNames = self.listWidgetPair.rightList.getTexts()
        pathToMMCif = self.pathData.get()
        for loopName in loopNames:
            print(loopName)

            df = self.getLoopData(pathToMMCif, loopName)
            print(df.head())
            if loopName == '_struct_conf':
                    
                    for residue in chain.residues:
                        residue.sequenceCode
                        residue.shortName,
                        residue.residueType


            self.project.newDataTable(name=loopName, data=df, comment='MMCif Data '+loopName)



        #if not self.project:
        #    raise RuntimeError('Project is not defined')



    def _getPathFromDialog(self):

        _currentPath = self.pathData.get()
        if len(_currentPath) > 0:
            _directory = aPath(_currentPath).parent.asString()
        else:
            _directory = self.project.application.dataPath.asString()

        dialog = OtherFileDialog(parent=self.mainWindow, _useDirectoryOnly=False, directory=_directory)
        dialog._show()
        if (path := dialog.selectedFile()) is not None:
            self.pathData.setText(str(path))
        self._updateCallback()

    def _updateCallback(self):
        pathToMMCif = self.pathData.get()
        loopNames = self.getLoopNames(pathToMMCif)
        print(loopNames)
        for x in loopNames: self.listWidgetPair.leftList.addItem(x)


    def getLoopData(self, filename, loopName) -> pd.DataFrame:
        """
        Create a Pandas DataFrame from an mmCIF file.
        """
        columns = []
        atomData = []
        loop_ = False
        _atom_siteLoop = False
        print(filename)
        with open(filename) as f:
            for l in f:
                l = l.strip()
                if len(l) == 0:
                    continue  # Ignore blank lines
                if l.startswith('#'):
                    loop_ = False
                    _atom_siteLoop = False
                    continue
                if l.startswith('loop_'):
                    loop_ = True
                    _atom_siteLoop = False
                    continue
                if loop_ and l.startswith(loopName+'.'):
                    _atom_siteLoop = True
                    columns.append(l.replace(loopName+'.', "").strip())
                if _atom_siteLoop and l.startswith('#'):
                    loop_ = False
                    _atom_siteLoop = False
                if _atom_siteLoop and not l.startswith(loopName+'.'):
                    split_data = re.findall(r"'[^']*'|\S+", l)
                    split_data = [item.strip("'") for item in split_data]
                    atomData.append(split_data)


        print(atomData, columns)
        df = pd.DataFrame(atomData, columns=columns)
        # df = df.infer_objects()  # This method returns the DataFrame with inferred data types
        df['idx'] = numpy.arange(1, df.shape[0] + 1)  # Create an 'idx' column
        df.set_index('idx', inplace=True)  # Set 'idx' as the index

        return df

    def getLoopNames(self, filename):
        print(filename)
        loopNames = []
        loop_ = False
        with open(filename) as f:
            for l in f:
                l = l.strip()
                if len(l) == 0:
                    continue  # Ignore blank lines
                if l.startswith('#'):
                    loop_ = False
                    continue
                if l.startswith('loop_'):
                    loop_ = True
                    continue
                if (loop_ == True) and (l.startswith('_')):
                    loopNames.append(l.split('.')[0])

        return list(set(loopNames))

if __name__ == '__main__':

    popup = MMCif_DataSelectorImporter(mainWindow=mainWindow)
    popup.show()
    popup.raise_()

