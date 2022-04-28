#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-04-28 20:33:15 +0100 (Thu, April 28, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import pandas as pd
from collections import OrderedDict
from PyQt5 import QtWidgets

from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.CallBack import CallBack
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.PulldownListsForObjects import IntegralListPulldown
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableViewProjectSpecific, _updateSimplePandasTable
from ccpn.util.Logging import getLogger


logger = getLogger()
ALL = '<all>'


class IntegralTableModule(CcpnModule):
    """This class implements the module by wrapping a integralTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'top'

    className = 'IntegralTableModule'
    _allowRename = True

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='Integral Table',
                 integralList=None, selectFirstItem=False):
        """Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None
        self._table = None

        # add the widgets
        self._setWidgets()

        if integralList is not None:
            self.selectTable(integralList)
        elif selectFirstItem:
            self._modulePulldown.selectFirstItem()

    def _setWidgets(self):
        """Set up the widgets for the module
        """
        _topWidget = self.mainWidget

        # main widgets at the top
        row = 0
        Spacer(_topWidget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self._modulePulldown = IntegralListPulldown(parent=_topWidget,
                                                    mainWindow=self.mainWindow,
                                                    grid=(row, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                    showSelectName=True,
                                                    sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                    callback=self._selectionPulldownCallback)

        # fixed height
        self._modulePulldown.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        self.spacer = Spacer(_topWidget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 1), gridSpan=(1, 1))
        _topWidget.getLayout().setColumnStretch(gridHPos + 1, 2)

        # main window
        _hidden = ['Pid', 'Spectrum', 'IntegralList', 'Id']

        row += 1
        self._tableWidget = _NewIntegralTableWidget(parent=_topWidget,
                                                    mainWindow=self.mainWindow,
                                                    moduleParent=self,
                                                    grid=(row, 0), gridSpan=(1, 6),
                                                    hiddenColumns=_hidden,
                                                    )

        # make the table expand to fill the frame
        self._tableWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

    def selectTable(self, table=None):
        """Manually select a table from the pullDown
        """
        if table is None:
            self._modulePulldown.selectFirstItem()
        else:
            if not isinstance(table, self._tableWidget.tableClass):
                logger.warning(f'select: Object is not of type {self._tableWidget.tableName}')
                raise TypeError(f'select: Object is not of type {self._tableWidget.tableName}')
            else:
                self._modulePulldown.select(table.pid)

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting peakList from the pull down menu
        """
        self._table = self._modulePulldown.getSelectedObject()
        self._tableWidget._table = self._table

        if self._table is not None:
            self._tableWidget.populateTable(selectedObjects=self.current.integrals)
        else:
            self._tableWidget.populateEmptyTable()

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self._modulePulldown.unRegister()
        self._tableWidget._close()
        super()._closeModule()


#=========================================================================================
# _NewIntegralTableWidget
#=========================================================================================

class _NewIntegralTableWidget(_SimplePandasTableViewProjectSpecific):
    """Class to present an integralList Table
    """
    className = 'IntegralTable'
    attributeName = 'integralLists'

    defaultHidden = ['Pid', 'Spectrum', 'IntegralList', 'Id']
    _internalColumns = ['isDeleted', '_object']  # columns that are always hidden

    # define self._columns here
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = IntegralList
    rowClass = Integral
    cellClass = None
    tableName = tableClass.className
    rowName = rowClass.className
    cellClassNames = None
    selectCurrent = True
    callBackClass = Integral
    search = False

    # set the queue handling parameters
    _maximumQueueLength = 25

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 hiddenColumns=None,
                 enableExport=True, enableDelete=True, enableSearch=False,
                 **kwds):
        """Initialise the widgets for the module.
        """

        self._hiddenColumns = [self.columnHeaders.get(col) or col for col in hiddenColumns] if hiddenColumns else \
            [self.columnHeaders.get(col) or col for col in self.defaultHidden]
        self.dataFrameObject = None

        super().__init__(parent=parent,
                         mainWindow=mainWindow,
                         moduleParent=moduleParent,
                         multiSelect=True,
                         showVerticalHeader=False,
                         setLayout=True,
                         **kwds)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    #=========================================================================================
    # Widget callbacks
    #=========================================================================================

    def actionCallback(self, data):
        """Notifier DoubleClick action on item in table
        """
        # NOTE:ED - need to clean this up
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            integral = objs[0]
        else:
            integral = objs

        # self._showRegions()
        self._navigateToPosition()

    def selectionCallback(self, data):
        """set as current the selected peaks on the table
        """
        objs = data[CallBack.OBJECT]
        if objs is None:
            self.current.clearIntegrals()
        else:
            self.current.integrals = objs

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

    @property
    def _sourceObjects(self):
        """Return the list of source objects
        """
        return self._table.integrals

    def _newRowFromUniqueId(self, df, obj, uniqueId):
        """Create a new row to insert into the dataFrame or replace row
        """
        # generate a new row
        listItem = OrderedDict()
        for header in self._columnDefs.columns:
            try:
                listItem[header.headerText] = header.getValue(obj)
            except Exception as es:
                # NOTE:ED - catch any nasty surprises in tables
                listItem[header.headerText] = None

        return list(listItem.values())

    def _derivedFromObject(self, obj):
        """Get a tuple of derived values from obj
        Not very generic yet - column class now seems redundant
        """
        pass

    def buildTableDataFrame(self):
        """Return a Pandas dataFrame from an internal list of objects.
        The columns are based on the 'func' functions in the columnDefinitions.
        :return pandas dataFrame
        """
        allItems = []
        objects = []

        if self._table:
            self._columnDefs = self._getTableColumns(self._table)

            for col, obj in enumerate(self._sourceObjects):
                listItem = OrderedDict()
                for header in self._columnDefs.columns:
                    try:
                        listItem[header.headerText] = header.getValue(obj)
                    except Exception as es:
                        # NOTE:ED - catch any nasty surprises in tables
                        getLogger().debug(f'Error creating table information {es}')
                        listItem[header.headerText] = None

                allItems.append(listItem)
                objects.append(obj)

            df = pd.DataFrame(allItems, columns=self._columnDefs.headings)

        else:
            self._columnDefs = self._getTableColumns()
            df = pd.DataFrame(columns=self._columnDefs.headings)

        # use the object as the index, object always exists even if isDeleted
        df.set_index(df[self.OBJECTCOLUMN], inplace=True, )

        _dfObject = DataFrameObject(dataFrame=df,
                                    columnDefs=self._columnDefs or [],
                                    table=self)

        return _dfObject

    def refreshTable(self):
        # subclass to refresh the groups
        _updateSimplePandasTable(self, self._df)
        # self.updateTableExpanders()

    def setDataFromSearchWidget(self, dataFrame):
        """Set the data for the table from the search widget
        """
        _updateSimplePandasTable(self, dataFrame)
        # self._updateGroups(dataFrame)
        # self.updateTableExpanders()

    def _updateTableCallback(self, data):
        # print(f'>>> _updateTableCallback')
        pass

    def getCellToRows(self, cellItem, attribute=None):
        """Get the list of objects which cellItem maps to for this table
        To be subclassed as required
        """
        raise RuntimeError(f'{self.__class__.__name__}.getCellToRows not callable')

    def _updateRowCallback(self, data):
        """Notifier callback for updating the table for change in chemicalShifts
        :param data: notifier content
        """
        # print(f'>>> _updateRowCallback')

        with self._blockTableSignals('_updateRowCallback'):
            obj = data[Notifier.OBJECT]

            # check that the dataframe and object are valid
            if self._df is None:
                getLogger().debug(f'{self.__class__.__name__}._updateRowCallback: dataFrame is None')
                return
            if obj is None:
                getLogger().debug(f'{self.__class__.__name__}._updateRowCallback: callback object is undefined')
                return

            trigger = data[Notifier.TRIGGER]
            try:
                df = self._df
                objSet = set(self._sourceObjects)  # objects in the list
                tableSet = set(df[self.OBJECTCOLUMN])  # objects currently in the table

                if trigger == Notifier.DELETE:
                    # uniqueIds in the visible table
                    if obj in (tableSet - objSet):
                        # remove from the table
                        self.model()._deleteRow(obj)

                elif trigger == Notifier.CREATE:
                    # uniqueIds in the visible table
                    if obj in (objSet - tableSet):
                        # insert into the table
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._insertRow(obj, newRow)

                elif trigger == Notifier.CHANGE:
                    # uniqueIds in the visible table
                    if obj in (objSet & tableSet):
                        # visible table dataframe update - object MUST be in the table
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._updateRow(obj, newRow)

                elif trigger == Notifier.RENAME:
                    if obj in (objSet & tableSet):
                        # visible table dataframe update
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._updateRow(obj, newRow)

                    elif obj in (objSet - tableSet):
                        # insert renamed object INTO the table
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._insertRow(obj, newRow)

                    elif obj in (tableSet - objSet):
                        # remove renamed object OUT of the table
                        self.model()._deleteRow(obj)

            except Exception as es:
                getLogger().debug2(f'Error updating row in table {es}')

    def _searchCallBack(self, data):
        # print(f'>>> _searchCallBack')
        pass

    def _selectCurrentCallBack(self, data):
        """Callback from a notifier to highlight the current objects
        :param data:
        """
        if self._tableBlockingLevel:
            return

        objs = data['value']
        self._selectOnTableCurrent(objs)

    def _selectionChangedCallback(self, selected, deselected):
        """Handle item selection as changed in table - call user callback
        Includes checking for clicking below last row
        """
        self._changeTableSelection(None)

    def _selectOnTableCurrent(self, objs):
        """Highlight the list of objects on the table
        :param objs:
        """
        self.highlightObjects(objs)

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _getTableColumns(self, integralList=None):
        """Define the columns for the table
        """
        figureOfMeritTipText = 'Figure of merit'
        commentsTipText = 'Textual notes about the integral'

        columnDefs = ColumnClass([
            ('#', lambda il: il.serial, '', None, None),
            ('Pid', lambda il: il.pid, 'Pid of integral', None, None),
            ('_object', lambda il: il, 'Object', None, None),

            ('Spectrum', lambda il: il.integralList.spectrum.id, 'Spectrum containing the Integral', None, None),
            ('IntegralList', lambda il: il.integralList.serial, 'IntegralList containing the Integral', None, None),
            ('Id', lambda il: il.serial, 'Integral serial', None, None),

            ('Value', lambda il: il.value, '', None, None),
            ('Lower Limit', lambda il: self._getLowerLimit(il), '', None, None),
            ('Higher Limit', lambda il: self._getHigherLimit(il), '', None, None),
            ('ValueError', lambda il: il.valueError, '', None, None),
            ('Bias', lambda il: il.bias, '', None, None),
            ('FigureOfMerit', lambda il: il.figureOfMerit, figureOfMeritTipText,
             lambda il, value: self._setFigureOfMerit(il, value), None),
            ('Baseline', lambda il: il.baseline, 'Baseline for the integral area', lambda il, value: self._setBaseline(il, value), None),
            ('Slopes', lambda il: il.slopes, '', None, None),
            # ('Annotation', lambda il: il.annotation, '', None, None),
            ('Comment', lambda il: self._getCommentText(il), commentsTipText,
             lambda il, value: self._setComment(il, value), None), ]
                )  #      [Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)

        return columnDefs

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets
        """
        self._updateTable()

    def _updateTable(self):
        """Display the objects on the table for the selected list.
        """
        if self._table and self._table.integrals:
            self.populateTable(selectedObjects=self.current.integrals)
        else:
            self.populateEmptyTable()

    def queueFull(self):
        """Method that is called when the queue is deemed to be too big.
        Apply overall operation instead of all individual notifiers.
        """
        self._updateTable()

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    def _navigateToPosition(self):
        """If current strip contains the double-clicked peak will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio

        integral = self.current.integral
        if self.current.strip is not None:
            try:
                widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                if len(integral.limits) == 1:
                    positions = integral.limits[0]
                    navigateToPositionInStrip(strip=self.current.strip, positions=positions, widths=widths)
            except Exception as es:
                logger.warning('Impossible to navigate to peak position.', es)
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    #=========================================================================================
    # object properties
    #=========================================================================================

    @staticmethod
    def _setFigureOfMerit(obj, value):
        """CCPN-INTERNAL: Set figureOfMerit from table
        Must be a floatRatio in range [0.0, 1.0]
        """
        # clip and set the figure of merit
        obj.figureOfMerit = min(max(float(value), 0.0), 1.0) if value is not None else None

    @staticmethod
    def _setBaseline(obj, value):
        """CCPN-INTERNAL: Edit baseline of integral
        """
        obj.baseline = float(value) if value is not None else None

    @staticmethod
    def _getHigherLimit(integral):
        """Returns HigherLimit
        """
        if integral is not None:
            if len(integral.limits) > 0:
                limits = integral.limits[0]
                if limits is not None:
                    return float(max(limits))

    @staticmethod
    def _getLowerLimit(integral):
        """Returns Lower Limit
        """
        if integral is not None:
            if len(integral.limits) > 0:
                limits = integral.limits[0]
                if limits:
                    return float(min(limits))


#=========================================================================================
# main
#=========================================================================================

def main():
    """Show the PeakTable module
    """
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = IntegralTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
