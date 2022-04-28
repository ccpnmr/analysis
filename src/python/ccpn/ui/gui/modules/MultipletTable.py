"""Module Documentation here

"""
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
__dateModified__ = "$dateModified: 2022-04-28 20:35:37 +0100 (Thu, April 28, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from PyQt5 import QtWidgets
from collections import OrderedDict
from dataclasses import dataclass

from ccpn.core.MultipletList import MultipletList
from ccpn.core.Multiplet import Multiplet
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.PulldownListsForObjects import MultipletListPulldown
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.modules.MultipletPeakTable import MultipletPeakTableWidget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Font import getFontHeight
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.peakUtils import getPeakLinewidth, getMultipletPosition
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableViewProjectSpecific, _updateSimplePandasTable
from ccpn.util.Logging import getLogger


logger = getLogger()

UNITS = ['ppm', 'Hz', 'point']


#=========================================================================================
# MultipletTableModule
#=========================================================================================

class MultipletTableModule(CcpnModule):
    """This class implements the module by wrapping a MultipletTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'MultipletTableModule'
    _allowRename = True

    def __init__(self, mainWindow=None, name='Multiplet Table',
                 multipletList=None, selectFirstItem=False):
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

        if multipletList is not None:
            self.selectTable(multipletList)
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
        self._modulePulldown = MultipletListPulldown(parent=_topWidget,
                                                     mainWindow=self.mainWindow,
                                                     grid=(row, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                     showSelectName=True,
                                                     sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                     callback=self._selectionPulldownCallback)

        # create widgets for selection of position units
        gridHPos += 1
        _posUnitPulldownLabel = Label(parent=_topWidget, text=' Position Unit', grid=(row, gridHPos))
        gridHPos += 1
        self.posUnitPulldown = PulldownList(parent=_topWidget, texts=UNITS, callback=self._pulldownUnitsCallback, grid=(row, gridHPos),
                                            objectName='posUnits_PT')

        # fixed height
        self._modulePulldown.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        self.spacer = Spacer(_topWidget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 1), gridSpan=(1, 1))
        _topWidget.getLayout().setColumnStretch(gridHPos + 1, 2)

        # add the splitter between multiplets and peaks
        row += 1
        outerFrame = Frame(_topWidget, setLayout=True, grid=(row, 0), gridSpan=(1, gridHPos + 2))
        splitter = Splitter(horizontal=True, collapsible=False)

        outerFrame.getLayout().addWidget(splitter)

        # main window
        _hidden = ['Pid', 'Spectrum', 'MultipletList', 'Id']

        row += 1
        self._tableWidget = _NewMultipletTableWidget(parent=_topWidget,
                                                     mainWindow=self.mainWindow,
                                                     moduleParent=self,
                                                     grid=(row, 0), gridSpan=(1, 6),
                                                     hiddenColumns=_hidden,
                                                     )

        # make the table expand to fill the frame
        self._tableWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        # add the peak-table to the right
        self.peaksFrame = Frame(self.mainWidget, setLayout=True, grid=(0, 1))
        self.peakListTableLabel = Label(self.peaksFrame, 'Peaks:', grid=(0, 0))
        self.peakListTableLabel.setFixedHeight(getFontHeight())

        self.peakListTable = MultipletPeakTableWidget(parent=self.peaksFrame,
                                                      mainWindow=self.mainWindow,
                                                      moduleParent=None,
                                                      grid=(1, 0))

        # make the table expand to fill the frame
        self.peakListTable.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        # put the frames into the splitter
        splitter.addWidget(self._tableWidget)
        splitter.addWidget(self.peaksFrame)

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
        """Notifier Callback for selecting table from the pull down menu
        """
        self._table = self._modulePulldown.getSelectedObject()
        self._tableWidget._table = self._table

        if self._table is not None:
            self._tableWidget.populateTable(selectedObjects=self.current.multiplets)
        else:
            self._tableWidget.populateEmptyTable()

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self._modulePulldown.unRegister()
        self._tableWidget._close()
        self.peakListTable._close()
        super()._closeModule()

    def _pulldownUnitsCallback(self, unit):
        """Update both tables with the new units
        """
        self._tableWidget._setPositionUnit(unit)
        self._tableWidget._updateAllModule()
        self.peakListTable._setPositionUnit(unit)
        self.peakListTable._updateAllModule()


#=========================================================================================
# _NewMultipletTableWidget
#=========================================================================================

# simple class to show items on the multipletPeakTable
@dataclass
class _PeakList:
    peaks = []
    spectrum = None


class _NewMultipletTableWidget(_SimplePandasTableViewProjectSpecific):
    """Class to present an multipletList Table
    """
    className = 'MultipletTable'
    attributeName = 'multipletLists'

    defaultHidden = ['Pid', 'Spectrum', 'MultipletList', 'Id']
    _internalColumns = ['isDeleted', '_object']  # columns that are always hidden

    # define self._columns here
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = MultipletList
    rowClass = Multiplet
    cellClass = None
    tableName = tableClass.className
    rowName = rowClass.className
    cellClassNames = None
    selectCurrent = True
    callBackClass = Multiplet
    search = False

    # set the queue handling parameters
    _maximumQueueLength = 25

    positionsUnit = UNITS[0]  #default

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
        If current strip contains the double-clicked multiplet will navigateToPositionInStrip
        """
        from ccpn.core.PeakList import PeakList
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio

        # TODO hack until we have multiplet views
        multiplet = self.current.multiplet
        if multiplet:
            if len(multiplet.peaks) > 0:
                peak = multiplet.peaks[-1]

                if self.current.strip is not None:
                    validPeakListViews = [pp.peakList for pp in self.current.strip.peakListViews if
                                          isinstance(pp.peakList, PeakList)]

                    if peak.peakList in validPeakListViews:
                        widths = None

                        if peak.peakList.spectrum.dimensionCount <= 2:
                            widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                        navigateToPositionInStrip(strip=self.current.strip, positions=multiplet.position, widths=widths)
            else:
                logger.warning('Impossible to navigate to peak position. No peaks in multiplet')
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    def selectionCallback(self, data):
        """set as current the selected peaks on the table
        """
        multiplets = data[Notifier.OBJECT]
        if multiplets is None:
            self.current.clearMultiplets()
        else:
            self.current.multiplets = multiplets

        self._updateMultipletPeaksOnTable()

    def _updateMultipletPeaksOnTable(self):
        """Populate the multiplet-peak-table with the multiplet-peaks
        """
        newTable = _PeakList()

        if self.current.multiplets:
            peaks = tuple(OrderedSet(peak for mt in self.current.multiplets for peak in mt.peaks))
            if len(peaks) > 0:
                # create a dummy structure to hold the list of peaks
                newTable.peaks = peaks
                newTable.spectrum = peaks[0].spectrum

        # populate the table - wrong direction, should use a signal
        self.moduleParent.peakListTable._table = newTable
        self.moduleParent.peakListTable._updateTable()

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

    @property
    def _sourceObjects(self):
        """Return the list of source objects
        """
        return self._table.multiplets

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

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to add new items to context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)

        self.tableMenu.insertSeparator(self.tableMenu.actions()[0])
        a = self.tableMenu.addAction('Edit Multiplet...', self._editMultiplets)
        self.tableMenu.insertAction(self.tableMenu.actions()[0], a)

    def _raiseTableContextMenu(self, pos):
        """Raise the right-mouse menu
        """
        super()._raiseTableContextMenu(pos)

    def _editMultiplets(self):
        """Raise the edit multiplet popup
        """
        from ccpn.ui.gui.popups.EditMultipletPopup import EditMultipletPopup

        multiplets = self.current.multiplets
        if len(multiplets) > 0:
            multiplet = multiplets[-1]
            popup = EditMultipletPopup(parent=self.mainWindow, mainWindow=self.mainWindow, multiplet=multiplet)
        else:
            popup = EditMultipletPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _getTableColumns(self, multipletList=None):
        """Add default columns plus the ones according to multipletList.spectrum dimension
         format of column = ( Header Name, value, tipText, editOption)
         editOption allows the user to modify the value content by doubleclick
         """

        columnDefs = [('#', 'serial', 'Multiplet serial number', None, None),
                      ('Pid', lambda ml: ml.pid, 'Pid of the Multiplet', None, None),
                      ('_object', lambda ml: ml, 'Object', None, None),
                      ('Spectrum', lambda multiplet: multiplet.multipletList.spectrum.id, 'Spectrum containing the Multiplet', None, None),
                      ('MultipletList', lambda multiplet: multiplet.multipletList.serial, 'MultipletList containing the Multiplet', None, None),
                      ('Id', lambda multiplet: multiplet.serial, 'Multiplet serial', None, None)]

        # Serial column

        # # Assignment column
        # for i in range(multipletList.spectrum.dimensionCount):
        #     assignTipText = 'NmrAtom assignments of multiplet in dimension %s' % str(i + 1)
        #     columnDefs.append(
        #             ('Assign F%s' % str(i + 1), lambda ml, dim=i: getPeakAnnotation(ml, dim), assignTipText, None, None))

        if multipletList:
            # Multiplet positions column
            for i in range(multipletList.spectrum.dimensionCount):
                positionTipText = 'Multiplet position in dimension %s' % str(i + 1)
                columnDefs.append(('Pos F%s' % str(i + 1),
                                   lambda ml, dim=i, unit=self.positionsUnit: getMultipletPosition(ml, dim, unit),
                                   positionTipText, None, '%0.3f'))

            # line-width column
            for i in range(multipletList.spectrum.dimensionCount):
                linewidthTipTexts = 'Multiplet line width %s' % str(i + 1)
                columnDefs.append(
                        ('LW F%s' % str(i + 1), lambda ml, dim=i: getPeakLinewidth(ml, dim), linewidthTipTexts, None, '%0.3f'))

        # height column
        heightTipText = 'Magnitude of spectrum intensity at multiplet center (interpolated), unless user edited'
        columnDefs.append(('Height', lambda ml: ml.height, heightTipText, None, None))

        # volume column
        volumeTipText = 'Integral of spectrum intensity around multiplet location, according to chosen volume method'
        columnDefs.append(('Volume', lambda ml: ml.volume, volumeTipText, None, None))

        # numPeaks column
        numPeaksTipText = 'Peaks count'
        columnDefs.append(('Peaks count', lambda ml: ml.numPeaks, numPeaksTipText, None, None))

        # figureOfMerit column
        figureOfMeritTipText = 'Figure of merit'
        columnDefs.append(('Merit', lambda ml: ml.figureOfMerit, figureOfMeritTipText,
                           lambda ml, value: self._setFigureOfMerit(ml, value), None))

        # comment column
        commentsTipText = 'Optional user comment'
        columnDefs.append(('Comment', lambda ml: self._getCommentText(ml), commentsTipText,
                           lambda ml, value: self._setComment(ml, value), None))

        return ColumnClass(columnDefs)

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets
        """
        self._updateTable()

    def _updateTable(self):
        """Display the objects on the table for the selected list.
        Obviously, If the object has not been previously deleted and flagged isDeleted
        """
        if self._table and self._table.multiplets:
            self.populateTable(selectedObjects=self.current.multiplets)
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

        multiplet = self.current.multiplet
        if self.current.strip is not None:
            # widths = None
            try:
                widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                if len(multiplet.limits) == 1:
                    positions = multiplet.limits[0]
                    navigateToPositionInStrip(strip=self.current.strip, positions=positions, widths=widths)
            except Exception as es:
                logger.warning('Impossible to navigate to peak position.', es)
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    def _setPositionUnit(self, value):
        if value in UNITS:
            self.positionsUnit = value

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
        """CCPN-INTERNAL: Edit baseline of multiplet
        """
        obj.baseline = float(value) if value is not None else None

    @staticmethod
    def _getHigherLimit(multiplet):
        """Returns HigherLimit
        """
        if multiplet is not None:
            if len(multiplet.limits) > 0:
                limits = multiplet.limits[0]
                if limits is not None:
                    return float(max(limits))

    @staticmethod
    def _getLowerLimit(multiplet):
        """Returns Lower Limit
        """
        if multiplet is not None:
            if len(multiplet.limits) > 0:
                limits = multiplet.limits[0]
                if limits:
                    return float(min(limits))


#=========================================================================================
# main
#=========================================================================================

def main():
    """Show the MultipletTableModule
    """
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = MultipletTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
