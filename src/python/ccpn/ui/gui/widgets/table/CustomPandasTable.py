"""
A custom Table using Columns and a standard DataFrame
"""

import pandas as pd
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Column import Column
from ccpn.ui.gui.widgets.table.Table import Table
from ccpn.ui.gui.widgets.table._TableModel import  INDEX_ROLE
from ccpn.util.OrderedSet import OrderedSet

class CustomDataFrameTable(Table):
    _defaultEditable = False
    def __init__(self, parent, dataFrame=None, columns=None, **kwds):
        super().__init__(parent, **kwds)
        self._columnDefs = self.getColumnDefs(columns)
        if dataFrame is None:
            dataFrame = pd.DataFrame()
        self.setDataFrame(dataFrame)

    def getColumnDefs(self, columns=None):
        """ Overide in subclass """
        self._columnDefs = ColumnClass([])
        columns = columns or []
        self._columnDefs._columns = columns
        return self._columnDefs

    def setDataFrame(self, dataFrame):
        self._buildColumnsFromDataFrame(dataFrame)

    # def selectionCallback(self, selected, deselected, selection, lastItem):
    #     """Handle item selection has changed in table - call user callback
    #     :param selected: table indexes selected
    #     :param deselected: table indexes deselected
    #     """
    #     # print('Selected', selected, 'DESE', deselected, 'sel', selection)
    #     print(self.getSelectedObjects(), 'OBJ')


    def getSelectedObjects(self):
        """
        :return: list of Pandas series object corresponding to the selected row(s).
        """
        sRows = OrderedSet((dd := idx.data(INDEX_ROLE)) is not None and dd[0] for idx in self.selectedIndexes())
        return [self._objects[row] for row in sRows]

    def getCurrentObject(self):
        """ Deprecated, backcompatibility only"""
        return self.getSelectedObjects()

    @staticmethod
    def _checkColumns(columnDefs, dataframeToBeSet):
        """
        Ensure columns  are compatible between ColumnDefs and setting DataFrame
        Cases:
        1) columnDefs have more definitions than the given DataFrame to be set
        2) columnDefs have fewer definitions than the given DataFrame to be set

        """

        headingFromDefs = [col.rawDataHeading for col in columnDefs._columns]
        columnFromDf = dataframeToBeSet.columns

        missingColumnsInDf = [h for h in headingFromDefs if h not in columnFromDf]
        missingHeadings = [c for c in columnFromDf if c not in headingFromDefs]

        ## case: Heading are more than the columns in the DataFrame.
        ## Update the dataframe with none values
        if len(missingColumnsInDf):
            dataframeToBeSet[missingColumnsInDf] =  [None] * len(missingColumnsInDf)

        ## case: Heading defs are fewer than the columns in the DataFrame.
        ##  add definitions to show all data on table.
        if len(missingHeadings)>0:
            oldHeadings = columnDefs._columns
            newHeadings = []
            for missingHeading in missingHeadings:
                c = Column(headerText=missingHeading,
                           getValue=missingHeading,
                           rawDataHeading=missingHeading,
                           isHidden=True)
                newHeadings.append(c)
            columnDefs.setColumns(oldHeadings+newHeadings)


    def _buildColumnsFromDataFrame(self, dataFrame):
        hidden = []
        data={}
        self._checkColumns(self._columnDefs, dataFrame)
        for col in self._columnDefs._columns:
            values = dataFrame[col.rawDataHeading].values
            data[col.headerText] = values
            if col.isHidden:
                hidden.append(col.headerText)
        df = pd.DataFrame(data)
        frames = [s for h, s in dataFrame.iterrows()]
        self._objects = frames
        self.updateDf(df)
        self.setHiddenColumns(hidden)

    def getObjects(self):
        return self._objects

