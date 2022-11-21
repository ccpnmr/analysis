"""
A custom Table using Columns and a standard DataFrame
"""

import pandas as pd
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Column import Column
from ccpn.ui.gui.widgets.table.Table import Table
from ccpn.ui.gui.widgets.table._TableModel import _TableModel, DISPLAY_ROLE, CHECK_ROLE, \
    BACKGROUND_ROLE, CHECKED, UNCHECKED, ENABLED, CHECKABLE, SELECTABLE, EDIT_ROLE, \
    INDEX_ROLE, ICON_ROLE, TOOLTIP_ROLE, ALIGNMENT_ROLE
from ccpn.util.OrderedSet import OrderedSet


def _getDisplayRole(colDef, obj):
    return None if isinstance((value := colDef.getFormatValue(obj)), bool) else value

def _getCheckRole(colDef, obj):
    if isinstance((value := colDef.getValue(obj)), bool):
        return CHECKED if value else UNCHECKED
    return None

class _DataFrameTableModel(_TableModel):
    " A DataFrame TableModel "
    defaultFlags = ENABLED | SELECTABLE | CHECKABLE

    getAttribRole = {
        DISPLAY_ROLE: _getDisplayRole,
        CHECK_ROLE: _getCheckRole,
        ICON_ROLE: lambda colDef, obj: colDef.getIcon(obj),
        EDIT_ROLE: lambda colDef, obj: colDef.getEditValue(obj),
        TOOLTIP_ROLE: lambda colDef, obj: colDef.tipText,
        BACKGROUND_ROLE: lambda colDef, obj: colDef.getColor(obj),
        ALIGNMENT_ROLE: lambda colDef, obj: colDef.alignment
    }

    setAttribRole = {EDIT_ROLE: lambda colDef, obj, value: colDef.setEditValue(obj, value),
                     CHECK_ROLE: lambda colDef, obj, value: colDef.setEditValue(obj,
                                                                                True if (value == CHECKED) else False)
                     }

    def data(self, index, role=DISPLAY_ROLE):
        result = None
        if index.isValid():
            # get the source cell
            row, col = self._sortIndex[index.row()], index.column()
            obj = self._view._objects[row]
            colDef = self._view._columnDefs._columns[col]
            if (func := self.getAttribRole.get(role)):
                return func(colDef, obj)
        return result

    def setData(self, index, value, role=EDIT_ROLE) -> bool:
        if index.isValid():
            row, col = self._sortIndex[index.row()], index.column()
            obj = self._view._objects[row]
            colDef = self._view._columnDefs._columns[col]
            if (func := self.setAttribRole.get(role)):
                func(colDef, obj, value)
                self.dataChanged.emit(index, index)
                self._view.viewport().update()  # repaint the view
                return True
        return False

class CustomDataFrameTable(Table):
    defaultTableModel = _DataFrameTableModel

    def __init__(self, parent, dataFrame, columns=None, **kwds):
        super().__init__(parent, **kwds)
        self._columnDefs = self.getColumnDefs(columns)
        self.setDataFrame(dataFrame)

    def getColumnDefs(self, columns=None):
        """ Overide in subclass """
        self._columnDefs = ColumnClass([])
        columns = columns or []
        self._columnDefs._columns = columns
        return self._columnDefs

    def setDataFrame(self, dataFrame):
        self._buildColumnsFromDataFrame(dataFrame)

    def getSelectedObjects(self):
        """
        :return: list of Pandas series object corresponding to the selected row(s).
        """
        sRows = OrderedSet((dd := idx.data(INDEX_ROLE)) is not None and dd[0] for idx in self.selectedIndexes())
        return [self._objects[row] for row in sRows]

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
                c = Column(headerText=missingHeading, getValue=missingHeading, rawDataHeading=missingHeading, )
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

