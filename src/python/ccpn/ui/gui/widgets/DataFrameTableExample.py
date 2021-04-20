#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-04-20 11:00:56 +0100 (Tue, April 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-04-2=13 15:19:37 +0000 (Tue, April 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

######## core imports ########
import pandas as pd
from ccpn.util.Common import makeIterableList, _getObjectsByPids, _getPidsFromObjects

######## gui/ui imports ########
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader, _selectRowsOnTable, _colourTableByValue, _setValueByHeader
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets import MessageDialog


Header1 = '#'
Header2 = 'Name'
Header3 = 'Value1'
Header4 = 'Value2'
Header5 = 'Comment'



class PandasDataFrameGuiTable(GuiTable):
    """
    A GUI table for a flat Pandas DataFrame type (not a ccpn dataFrameObject).

    Usage:
    dataFrame = pd.DataFrame()
    myTable = PandasDataFrameGuiTable()
    myTable.dataFrame = dataFrame

    To update the table:
    myTable.dataFrame = dataFrame

    """
    className = '_PandasDataFrameGuiTable'
    OBJECT = 'object'
    TABLE = 'table'

    def __init__(self, parent, mainWindow,  **kwds):
        self.mainWindow = mainWindow
        self.dataFrameObject = None
        super().__init__(parent=parent, mainWindow=self.mainWindow, dataFrameObject=None,
                            setLayout=True, autoResize=True, multiSelect=True,
                            enableMouseMoveEvent=False,
                            selectionCallback=self.selection,
                            actionCallback=self.action, checkBoxCallback=self.actionCheckBox,  grid=(0, 0))

        # Set the column definitions:
        # ColumnClass defs are:
        # 1) header name as it will appear on the Gui Table
        # 2) Get Function, to get the cell value from the original dataFrame: e.g.:
        #   lambda row: _getValueByHeader(row, HeaderNameAsInDataFrame)
        # 3) TipText
        # 4) Edit Function, to set the cell value to the original dataFrame after a doubleclick.
        #   e.g.: lambda row, value: PandasDataFrameGuiTable._setFreeText(self, row, Header5, value)
        # 5) Value Formatting for the cell


        self.columns = ColumnClass([
            (Header1, lambda row: _getValueByHeader(row, Header1),  'TipTex1', None, None),
            (Header2, lambda row: _getValueByHeader(row, Header2),  'TipTex2', None, None),
            (Header3, lambda row: _getValueByHeader(row, Header3),  'TipTex3', None, '%0.4f'),
            (Header4, lambda row: _getValueByHeader(row, Header4),  'TipTex4', None, '%0.4f'),
            (Header5, lambda row: _getValueByHeader(row, Header5),  'TipTex5',
             lambda row, value: PandasDataFrameGuiTable._setFreeText(self, row, Header5, value), None)
        ])

        self._hiddenColumns = [Header4]
        # self._dataFrame = dataFrame
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.setMinimumHeight(100)
        self._selectOverride = True # otherwise very odd behaviour

    @property
    def dataFrame(self):
        return self._dataFrame

    def clean(self):
        self.dataFrame = pd.DataFrame()

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame
        self.build(dataFrame)

    def build(self, dataFrame):
        self.clear()
        self.dfo = self.getDataFromFrame(table=self, df=dataFrame, colDefs=self.columns, hiddenColumns=self._hiddenColumns)
        self.setTableFromDataFrameObject(dataFrameObject=self.dfo, columnDefs=self.columns)

    @staticmethod
    def _setFreeText(table, row, header, value):
        print('setting new value: %s for header: %s' %(value, header))
        row = _setValueByHeader(row, header, value)
        return row

    def action(self, *args):
        MessageDialog.showNotImplementedMessage()

    def selection(self, *args):
        selected = self.getSelectedObjects()
        print('Selected Series:', selected)

    def actionCheckBox(self, data):
        state = data.get('checked')
        row = data.get('object')
        # do some action and re-set the dataFrame
        # df = the updated dataFrame
        # self.dataFrame = df

    def deleteObjFromTable(self):
        selected = self.getSelectedObjects()
        # remove row from dataframe and reset the amended DataFrame on the table.


class PandasTableModuleExample(CcpnModule):
    """
    This is example of CCPN module showing a Pandas DataFrame table.
    """
    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'MyModule'

    def __init__(self, mainWindow, name):
        super().__init__(mainWindow=mainWindow, name=name)
        self.pandasTable = PandasDataFrameGuiTable(parent=self.mainWidget, mainWindow=mainWindow, grid=(0, 0))

    @property
    def dataFrame(self):
        return self.pandasTable.dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self.pandasTable.dataFrame = dataFrame


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    moduleArea = CcpnModuleArea(mainWindow=None, )
    module = PandasTableModuleExample(mainWindow=None, name='PandasTableModuleExample')

    dataFrame = pd.DataFrame({
                              Header1:[1,2,3],
                              Header2: ['A', 'B', 'C'],
                              Header3:[1,2,3],
                              Header4:[1,2,3],
                              Header5:['comment1', 'comment2', 'comment3']
                            })

    module.dataFrame = dataFrame
    moduleArea.addModule(module)
    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.show()
    app.start()
