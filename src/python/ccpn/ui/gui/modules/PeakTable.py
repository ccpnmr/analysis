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
__dateModified__ = "$dateModified: 2022-04-26 13:40:35 +0100 (Tue, April 26, 2022) $"
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
from collections import OrderedDict
from PyQt5 import QtWidgets

from ccpn.core.PeakList import PeakList
from ccpn.core.Peak import Peak
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.peakUtils import getPeakPosition, getPeakAnnotation, getPeakLinewidth
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.lib.GuiStripContextMenus import _selectedPeaksMenuItem, _addMenuItems, \
    _getNdPeakMenuItems, _setEnabledAllItems
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableViewProjectSpecific, _updateSimplePandasTable
from ccpn.util.Common import makeIterableList
from ccpn.util.Logging import getLogger


logger = getLogger()

UNITS = ['ppm', 'Hz', 'point']


class PeakTableModule(CcpnModule):
    """
    This class implements the module by wrapping a PeakListTable instance
    """

    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'

    activePulldownClass = None  # PeakList

    className = 'PeakTableModule'
    _allowRename = True

    def __init__(self, mainWindow=None, name='Peak Table',
                 peakList=None, selectFirstItem=False):
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

        if peakList is not None:
            self.selectTable(peakList)
        elif selectFirstItem:
            self._modulePulldown.selectFirstItem()

        # self.installMaximiseEventHandler(self._maximise, self._closeModule)

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
        self._modulePulldown = PeakListPulldown(parent=_topWidget,
                                                mainWindow=self.mainWindow,
                                                grid=(row, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                showSelectName=True,
                                                sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                callback=self._selectionPulldownCallback)

        # create widgets for selection of position units
        gridHPos += 1
        self.posUnitPulldownLabel = Label(parent=_topWidget, text=' Position Unit', grid=(row, gridHPos))
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

        # main window
        _hidden = ['Pid', 'Spectrum', 'PeakList', 'Id', 'HeightError', 'VolumeError']

        row += 1
        self._tableWidget = _NewPeakListTableWidget(parent=_topWidget,
                                                    mainWindow=self.mainWindow,
                                                    moduleParent=self,
                                                    # setLayout=True,
                                                    grid=(row, 0), gridSpan=(1, 6),
                                                    hiddenColumns=_hidden,
                                                    )

        # may not be needed for new table
        self._tableWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

    @property
    def _dataFrame(self):
        if self.peakListTable._dataFrameObject:
            return self.peakListTable._dataFrameObject.dataFrame

    def _maximise(self):
        """Maximise the attached table
        """
        self._selectionPulldownCallback(None)

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

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self._modulePulldown.unRegister()
        self._tableWidget._close()
        super()._closeModule()

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting peakList from the pull down menu
        """
        self._table = self._modulePulldown.getSelectedObject()
        self._tableWidget._table = self._table

        if self._table is not None:
            self._tableWidget.populateTable(rowObjects=self._table.peaks,
                                            columnDefs=self._tableWidget._getTableColumns(self._table),
                                            selectedObjects=self.current.peaks)
        else:
            self._tableWidget.populateEmptyTable()

    def _pulldownUnitsCallback(self, unit):
        # update the table with new units
        self._tableWidget._setPositionUnit(unit)
        self._tableWidget._updateAllModule()


#=========================================================================================
# PeakListTableWidget
#=========================================================================================

class PeakListTableWidget(GuiTable):
    """
    Class to present a peakList Table
    """
    className = 'PeakListTable'
    attributeName = 'peakLists'

    defaultHidden = ['Pid', 'Spectrum', 'PeakList', 'Id', 'HeightError', 'VolumeError']

    # define self._columns here
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = PeakList
    rowClass = Peak
    cellClass = None
    tableName = tableClass.className
    rowName = tableClass.className
    cellName = NmrAtom.className
    cellClassNames = (NmrAtom, 'assignedPeaks')

    selectCurrent = True
    callBackClass = Peak
    search = False

    positionsUnit = UNITS[0]  #default

    @staticmethod
    def _setFigureOfMerit(obj, value):
        """
        CCPN-INTERNAL: Set figureOfMerit from table
        Must be a floatRatio in range [0.0, 1.0]
        """
        # clip and set the figure of merit
        obj.figureOfMerit = min(max(float(value), 0.0), 1.0) if value else None

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 hiddenColumns=None, **kwds):
        """Initialise the widgets for the module.
        """
        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None
        self._table = None
        PeakListTableWidget.project = self.project

        self.settingWidgets = None
        self._selectedPeakList = None
        kwds['setLayout'] = True  # Assure we have a layout with the widget

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        self._hiddenColumns = [self.columnHeaders.get(col) or col for col in hiddenColumns] if hiddenColumns else \
            [self.columnHeaders.get(col) or col for col in self.defaultHidden]
        self.dataFrameObject = None

        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         # dataFrameObject=None,
                         # setLayout=True,
                         # autoResize=True,
                         multiSelect=True,
                         actionCallback=actionCallback,
                         selectionCallback=selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        self.setTableNotifiers(tableClass=PeakList,
                               rowClass=Peak,
                               cellClassNames=(NmrAtom, 'assignedPeaks'),
                               tableName='peakList', rowName='peak',
                               changeFunc=self._updateAllModule,
                               className=self.attributeName,
                               updateFunc=self._updateAllModule,
                               tableSelection='_table',
                               # pullDownWidget=self.pLwidget,
                               callBackClass=Peak,
                               selectCurrentCallBack=self._selectOnTableCurrentPeaksNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to add new items to context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        _actions = self.tableMenu.actions()
        if _actions:
            # _topMenuItem = _actions[0]
            # _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            # self._copyPeakMenuAction = self.tableMenu.addAction('Copy Peaks...', self._copyPeaks)
            # # move new actions to the top of the list
            # self.tableMenu.insertAction(_topSeparator, self._copyPeakMenuAction)

            # add the selected peaks menu to the bottom
            self.tableMenu.addSeparator()
            _peakItem = _selectedPeaksMenuItem(None)

            _addMenuItems(self, self.tableMenu, [_peakItem])

            # _selectedPeaksMenu submenu - add to Strip._selectedPeaksMenu
            items = _getNdPeakMenuItems(menuId='Main')
            # attach to the _selectedPeaksMenu submenu
            _addMenuItems(self, self._selectedPeaksMenu, items)

    def _raiseTableContextMenu(self, pos):
        """Raise the right-mouse menu
        """
        # Enable/disable menu items as required
        self._navigateToPeakMenuMain.setEnabled(False)
        _setEnabledAllItems(self._selectedPeaksMenu, True if self.current.peaks else False)

        super(PeakListTableWidget, self)._raiseTableContextMenu(pos)

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, PeakList, self.moduleParent._modulePulldown)

    def _getTableColumns(self, peakList):
        """Add default columns plus the ones according to peakList.spectrum dimension
        format of column = ( Header Name, value, tipText, editOption)
        editOption allows the user to modify the value content by doubleclick
        """

        columnDefs = []

        # Serial column
        columnDefs.append(('#', 'serial', 'Peak serial number', None, None))
        columnDefs.append(('Pid', lambda pk: pk.pid, 'Pid of the Peak', None, None))
        columnDefs.append(('_object', lambda pk: pk, 'Object', None, None))

        columnDefs.append(('Spectrum', lambda pk: pk.peakList.spectrum.id, 'Spectrum containing the Peak', None, None))
        columnDefs.append(('PeakList', lambda pk: pk.peakList.serial, 'PeakList containing the Peak', None, None))
        columnDefs.append(('Id', lambda pk: pk.serial, 'Peak serial', None, None))

        # Assignment column
        for i in range(peakList.spectrum.dimensionCount):
            assignTipText = 'NmrAtom assignments of peak in dimension %s' % str(i + 1)
            columnDefs.append(
                    ('Assign F%s' % str(i + 1), lambda pk, dim=i: getPeakAnnotation(pk, dim), assignTipText, None, None)
                    )

        # # Expanded Assignment columns
        # for i in range(peakList.spectrum.dimensionCount):
        #     assignTipText = 'NmrAtom assignments of peak in dimension %s' % str(i + 1)
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getNmrChain(pk, dim), assignTipText, None, None))
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getSequenceCode(pk, dim), assignTipText, None, None))
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getResidueType(pk, dim), assignTipText, None, None))
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getAtomType(pk, dim), assignTipText, None, None))

        # Peak positions column
        for i in range(peakList.spectrum.dimensionCount):
            positionTipText = 'Peak position in dimension %s' % str(i + 1)
            columnDefs.append(
                    ('Pos F%s' % str(i + 1),
                     lambda pk, dim=i, unit=self.positionsUnit: getPeakPosition(pk, dim, unit),
                     positionTipText, None, '%0.3f')
                    )

        # linewidth column TODO remove hardcoded Hz unit
        for i in range(peakList.spectrum.dimensionCount):
            linewidthTipTexts = 'Peak line width %s' % str(i + 1)
            columnDefs.append(
                    ('LW F%s (Hz)' % str(i + 1), lambda pk, dim=i: getPeakLinewidth(pk, dim), linewidthTipTexts,
                     None, '%0.3f')
                    )

        # height column
        heightTipText = 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited'
        columnDefs.append(('Height', lambda pk: pk.height if pk.height else 'None', heightTipText, None, None))
        columnDefs.append(('HeightError', lambda pk: pk.heightError, 'Error of the height', None, None))
        columnDefs.append(('S/N', lambda pk: pk.signalToNoiseRatio, 'Signal to Noise Ratio', None, None))

        # volume column
        volumeTipText = 'Integral of spectrum intensity around peak location, according to chosen volume method'
        columnDefs.append(('Volume', lambda pk: pk.volume if pk.volume else 'None', volumeTipText, None, None))
        columnDefs.append(('VolumeError', lambda pk: pk.volumeError, 'Error of the volume', None, None))

        # ClusterId column
        clusterIdTipText = 'The peak clusterId. ClusterIds are used for grouping peaks in fitting routines.'
        columnDefs.append(('ClusterId', lambda pk: pk.clusterId if pk.clusterId else 'None', clusterIdTipText,
                           lambda pk, value: self._setClusterId(pk, value), None))

        # figureOfMerit column
        figureOfMeritTipText = 'Figure of merit'
        columnDefs.append(('Merit', lambda pk: pk.figureOfMerit, figureOfMeritTipText,
                           lambda pk, value: self._setFigureOfMerit(pk, value), None)
                          )
        # annotation column
        annotationTipText = 'Any other peak label (excluded assignments)'
        columnDefs.append(('Annotation', lambda pk: self._getAnnotation(pk), annotationTipText,
                           lambda pk, value: self._setAnnotation(pk, value), None))

        # comment column
        commentsTipText = 'Textual notes about the peak'
        columnDefs.append(('Comment', lambda pk: self._getCommentText(pk), commentsTipText,
                           lambda pk, value: self._setComment(pk, value), None)
                          )

        return ColumnClass(columnDefs)

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _maximise(self):
        """Refresh the table on a maximise event
        """
        self._updateTable()

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets
        """
        self._updateTable()

    def _updateTable(self, useSelectedPeakList=True, peaks=None, peakList=None):
        """Display the peaks on the table for the selected PeakList.
        Obviously, If the peak has not been previously deleted and flagged isDeleted
        """
        self._selectedPeakList = self.project.getByPid(self.moduleParent._modulePulldown.getText())

        if useSelectedPeakList:
            if self._selectedPeakList:
                self.populateTable(rowObjects=self._selectedPeakList.peaks,
                                   columnDefs=self._getTableColumns(self._selectedPeakList),
                                   selectedObjects=self.current.peaks)
            else:
                self.clear()

        else:
            if peaks:
                if peakList:
                    self.populateTable(rowObjects=peaks,
                                       columnDefs=self._getTableColumns(peakList),
                                       selectedObjects=self.current.peaks)
            else:
                self.clear()

    def _selectPeakList(self, peakList=None):
        """Manually select a PeakList from the pullDown
        """
        if peakList is None:
            # logger.warning('select: No PeakList selected')
            # raise ValueError('select: No PeakList selected')
            self.pLwidget.selectFirstItem()
        else:
            if not isinstance(peakList, PeakList):
                logger.warning('select: Object is not of type PeakList')
                raise TypeError('select: Object is not of type PeakList')
            else:
                for widgetObj in self.pLwidget.textList:
                    if peakList.pid == widgetObj:
                        self._selectedPeakList = peakList
                        self.pLwidget.select(self._selectedPeakList.pid)

    #=========================================================================================
    # Widget callbacks
    #=========================================================================================

    def _getPullDownSelection(self):
        return self.pLwidget.getText()

    def _actionCallback(self, data, *args):
        """If current strip contains the double clicked peak will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio

        # multiselection table will return a list of objects
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            peak = objs[0]
        else:
            peak = objs

        if self.current.strip is not None:
            validPeakListViews = [pp.peakList for pp in self.current.strip.peakListViews if isinstance(pp.peakList, PeakList)]

            if peak and peak.peakList in validPeakListViews:
                widths = None

                if peak.peakList.spectrum.dimensionCount <= 2:
                    widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                navigateToPositionInStrip(strip=self.current.strip,
                                          positions=peak.position,
                                          axisCodes=peak.axisCodes,
                                          widths=widths)
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    def _selectionCallback(self, data, *args):
        """
        set as current the selected peaks on the table
        """
        peaks = data[CallBack.OBJECT]
        if peaks is None:
            self.current.clearPeaks()
        else:
            self.current.peaks = peaks

    def _pulldownUnitsCallback(self, unit):
        # update the table with new units
        self._setPositionUnit(unit)
        self._updateAllModule()

    def _pulldownPLcallback(self, data):
        self._updateAllModule()

    def _copyPeaks(self):
        from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

        popup = CopyPeaks(parent=self.mainWindow, mainWindow=self.mainWindow)
        self._selectedPeakList = self.project.getByPid(self.pLwidget.getText())
        if self._selectedPeakList is not None:
            spectrum = self._selectedPeakList.spectrum
            popup._selectSpectrum(spectrum)
            popup._selectPeaks(self.current.peaks)
        popup.exec_()

    def _selectOnTableCurrentPeaksNotifierCallback(self, data):
        """
        Callback from a notifier to highlight the peaks on the peak table
        :param data:
        """
        currentPeaks = data['value']
        self._selectOnTableCurrentPeaks(currentPeaks)

    def _selectOnTableCurrentPeaks(self, currentPeaks):
        """
        Highlight the list of peaks on the table
        :param currentPeaks:
        """
        self.highlightObjects(currentPeaks)

    def _setPositionUnit(self, value):
        if value in UNITS:
            self.positionsUnit = value


#=========================================================================================
# _NewPeakListTableWidget
#=========================================================================================

class _NewPeakListTableWidget(_SimplePandasTableViewProjectSpecific):
    """Class to present a peakList Table
    """
    className = 'PeakListTable'
    attributeName = 'peakLists'

    defaultHidden = ['Pid', 'Spectrum', 'PeakList', 'Id', 'HeightError', 'VolumeError']
    _internalColumns = ['isDeleted', '_object']  # columns that are always hidden

    # define self._columns here
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = PeakList
    rowClass = Peak
    cellClass = None
    tableName = tableClass.className
    rowName = tableClass.className
    cellClassNames = {NmrAtom: 'assignedPeaks'}
    selectCurrent = True
    callBackClass = Peak
    search = False

    # set the queue handling parameters
    _maximumQueueLength = 25

    positionsUnit = UNITS[0]  # default

    @staticmethod
    def _setFigureOfMerit(obj, value):
        """
        CCPN-INTERNAL: Set figureOfMerit from table
        Must be a floatRatio in range [0.0, 1.0]
        """
        # clip and set the figure of merit
        obj.figureOfMerit = min(max(float(value), 0.0), 1.0) if value else None

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
        """If current strip contains the double-clicked peak will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio

        # multi-selection table will return a list of objects
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            peak = objs[0]
        else:
            peak = objs

        if self.current.strip is not None:
            validPeakListViews = [pp.peakList for pp in self.current.strip.peakListViews if isinstance(pp.peakList, PeakList)]

            if peak and peak.peakList in validPeakListViews:
                widths = None

                if peak.peakList.spectrum.dimensionCount <= 2:
                    widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                navigateToPositionInStrip(strip=self.current.strip,
                                          positions=peak.position,
                                          axisCodes=peak.axisCodes,
                                          widths=widths)
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    def selectionCallback(self, data):
        """
        set as current the selected peaks on the table
        """
        peaks = data[CallBack.OBJECT]
        if peaks is None:
            self.current.clearPeaks()
        else:
            self.current.peaks = peaks

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

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

            for col, obj in enumerate(self._table.peaks):
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

        # use the object as the index, object always exists even if isDeleted
        df.set_index(df[self.OBJECTCOLUMN], inplace=True, )

        _dfObject = DataFrameObject(dataFrame=df,  # pd.DataFrame(allItems, columns=colDefs.headings),
                                    columnDefs=self._columnDefs,
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

    @staticmethod
    def getCellToRows(cellItem, attribute=None):
        """Get the list of objects which cellItem maps to for this table
        To be subclassed as required
        """
        # this is a step towards making guiTableABC and subclass for each table
        # return makeIterableList(getattr(cellItem, attribute, [])), Notifier.CHANGE

        return makeIterableList(cellItem._oldAssignedPeaks) if cellItem.isDeleted \
                   else makeIterableList(cellItem.assignedPeaks), \
               Notifier.CHANGE

    def _updateCellCallback(self, data):
        """Notifier callback for updating the table
        :param data:
        """
        with self._blockTableSignals('_updateCellCallback'):
            cellData = data[Notifier.OBJECT]

            rowObjs = []
            _triggerType = Notifier.CHANGE

            if (attr := self.cellClassNames.get(type(cellData))):
                rowObjs, _triggerType = self.getCellToRows(cellData, attr)

            # update the correct row by calling row handler
            for rowObj in rowObjs:
                rowData = {Notifier.OBJECT : rowObj,
                           Notifier.TRIGGER: _triggerType or data[Notifier.TRIGGER],  # Notifier.CHANGE
                           }

                self._updateRowCallback(rowData)

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
                objSet = set(self._table.peaks)  # objects in the list
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

        # add extra items to the menu
        _actions = self.tableMenu.actions()
        if _actions:
            # _topMenuItem = _actions[0]
            # _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            # self._copyPeakMenuAction = self.tableMenu.addAction('Copy Peaks...', self._copyPeaks)
            # # move new actions to the top of the list
            # self.tableMenu.insertAction(_topSeparator, self._copyPeakMenuAction)

            # add the selected peaks menu to the bottom
            self.tableMenu.addSeparator()
            _peakItem = _selectedPeaksMenuItem(None)

            _addMenuItems(self, self.tableMenu, [_peakItem])

            # _selectedPeaksMenu submenu - add to Strip._selectedPeaksMenu
            items = _getNdPeakMenuItems(menuId='Main')
            # attach to the _selectedPeaksMenu submenu
            _addMenuItems(self, self._selectedPeaksMenu, items)

    def _raiseTableContextMenu(self, pos):
        """Raise the right-mouse menu
        """
        # Enable/disable menu items as required
        self._navigateToPeakMenuMain.setEnabled(False)
        _setEnabledAllItems(self._selectedPeaksMenu, True if self.current.peaks else False)

        # raise the menu
        super()._raiseTableContextMenu(pos)

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, PeakList, self.moduleParent._modulePulldown)

    def _getTableColumns(self, peakList):
        """Add default columns plus the ones according to peakList.spectrum dimension
        format of column = ( Header Name, value, tipText, editOption)
        editOption allows the user to modify the value content by doubleclick
        """

        columnDefs = []

        # Serial column
        columnDefs.append(('#', 'serial', 'Peak serial number', None, None))
        columnDefs.append(('Pid', lambda pk: pk.pid, 'Pid of the Peak', None, None))
        columnDefs.append(('_object', lambda pk: pk, 'Object', None, None))

        columnDefs.append(('Spectrum', lambda pk: pk.peakList.spectrum.id, 'Spectrum containing the Peak', None, None))
        columnDefs.append(('PeakList', lambda pk: pk.peakList.serial, 'PeakList containing the Peak', None, None))
        columnDefs.append(('Id', lambda pk: pk.serial, 'Peak serial', None, None))

        # Assignment column
        for i in range(peakList.spectrum.dimensionCount):
            assignTipText = 'NmrAtom assignments of peak in dimension %s' % str(i + 1)
            columnDefs.append(
                    ('Assign F%s' % str(i + 1), lambda pk, dim=i: getPeakAnnotation(pk, dim), assignTipText, None, None)
                    )

        # # Expanded Assignment columns
        # for i in range(peakList.spectrum.dimensionCount):
        #     assignTipText = 'NmrAtom assignments of peak in dimension %s' % str(i + 1)
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getNmrChain(pk, dim), assignTipText, None, None))
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getSequenceCode(pk, dim), assignTipText, None, None))
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getResidueType(pk, dim), assignTipText, None, None))
        #     columnDefs.append(('Assign F%s' % str(i + 1), lambda pk, dim=i: self._getAtomType(pk, dim), assignTipText, None, None))

        # Peak positions column
        for i in range(peakList.spectrum.dimensionCount):
            positionTipText = 'Peak position in dimension %s' % str(i + 1)
            columnDefs.append(
                    ('Pos F%s' % str(i + 1),
                     lambda pk, dim=i, unit=self.positionsUnit: getPeakPosition(pk, dim, unit),
                     positionTipText, None, '%0.3f')
                    )

        # linewidth column TODO remove hardcoded Hz unit
        for i in range(peakList.spectrum.dimensionCount):
            linewidthTipTexts = 'Peak line width %s' % str(i + 1)
            columnDefs.append(
                    ('LW F%s (Hz)' % str(i + 1), lambda pk, dim=i: getPeakLinewidth(pk, dim), linewidthTipTexts,
                     None, '%0.3f')
                    )

        # height column
        heightTipText = 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited'
        columnDefs.append(('Height', lambda pk: pk.height if pk.height else 'None', heightTipText, None, None))
        columnDefs.append(('HeightError', lambda pk: pk.heightError, 'Error of the height', None, None))
        columnDefs.append(('S/N', lambda pk: pk.signalToNoiseRatio, 'Signal to Noise Ratio', None, None))

        # volume column
        volumeTipText = 'Integral of spectrum intensity around peak location, according to chosen volume method'
        columnDefs.append(('Volume', lambda pk: pk.volume if pk.volume else 'None', volumeTipText, None, None))
        columnDefs.append(('VolumeError', lambda pk: pk.volumeError, 'Error of the volume', None, None))

        # ClusterId column
        clusterIdTipText = 'The peak clusterId. ClusterIds are used for grouping peaks in fitting routines.'
        columnDefs.append(('ClusterId', lambda pk: pk.clusterId if pk.clusterId else 'None', clusterIdTipText,
                           lambda pk, value: self._setClusterId(pk, value), None))

        # figureOfMerit column
        figureOfMeritTipText = 'Figure of merit'
        columnDefs.append(('Merit', lambda pk: pk.figureOfMerit, figureOfMeritTipText,
                           lambda pk, value: self._setFigureOfMerit(pk, value), None)
                          )
        # annotation column
        annotationTipText = 'Any other peak label (excluded assignments)'
        columnDefs.append(('Annotation', lambda pk: self._getAnnotation(pk), annotationTipText,
                           lambda pk, value: self._setAnnotation(pk, value), None))

        # comment column
        commentsTipText = 'Textual notes about the peak'
        columnDefs.append(('Comment', lambda pk: self._getCommentText(pk), commentsTipText,
                           lambda pk, value: self._setComment(pk, value), None)
                          )

        return ColumnClass(columnDefs)

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _maximise(self):
        """Refresh the table on a maximise event
        """
        self._updateTable()

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets
        """
        self._updateTable()

    def _updateTable(self, useSelectedPeakList=True, peaks=None, peakList=None):
        """Display the peaks on the table for the selected PeakList.
        Obviously, If the peak has not been previously deleted and flagged isDeleted
        """
        self._selectedPeakList = self.project.getByPid(self.moduleParent._modulePulldown.getText())

        if useSelectedPeakList:
            if self._selectedPeakList:
                self.populateTable(rowObjects=self._selectedPeakList.peaks,
                                   selectedObjects=self.current.peaks)
            else:
                self.populateEmptyTable()

        else:
            if peaks:
                if peakList:
                    self.populateTable(rowObjects=peaks,
                                       selectedObjects=self.current.peaks)
            else:
                self.populateEmptyTable()

    def _selectPeakList(self, peakList=None):
        """Manually select a PeakList from the pullDown
        """
        if peakList is None:
            # logger.warning('select: No PeakList selected')
            # raise ValueError('select: No PeakList selected')
            self.pLwidget.selectFirstItem()
        else:
            if not isinstance(peakList, PeakList):
                logger.warning('select: Object is not of type PeakList')
                raise TypeError('select: Object is not of type PeakList')
            else:
                for widgetObj in self.pLwidget.textList:
                    if peakList.pid == widgetObj:
                        self._selectedPeakList = peakList
                        self.pLwidget.select(self._selectedPeakList.pid)

    def queueFull(self):
        """Method that is called when the queue is deemed to be too big.
        Apply overall operation instead of all individual notifiers.
        """
        self._updateTable()

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    def _getPullDownSelection(self):
        return self.pLwidget.getText()

    def _pulldownUnitsCallback(self, unit):
        # update the table with new units
        self._setPositionUnit(unit)
        self._updateAllModule()

    def _pulldownPLcallback(self, data):
        self._updateAllModule()

    def _copyPeaks(self):
        from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

        popup = CopyPeaks(parent=self.mainWindow, mainWindow=self.mainWindow)
        self._selectedPeakList = self.project.getByPid(self.pLwidget.getText())
        if self._selectedPeakList is not None:
            spectrum = self._selectedPeakList.spectrum
            popup._selectSpectrum(spectrum)
            popup._selectPeaks(self.current.peaks)
        popup.exec_()

    def _selectOnTableCurrentPeaksNotifierCallback(self, data):
        """
        Callback from a notifier to highlight the peaks on the peak table
        :param data:
        """
        currentPeaks = data['value']
        self._selectOnTableCurrentPeaks(currentPeaks)

    def _selectOnTableCurrentPeaks(self, currentPeaks):
        """
        Highlight the list of peaks on the table
        :param currentPeaks:
        """
        self.highlightObjects(currentPeaks)

    def _setPositionUnit(self, value):
        if value in UNITS:
            self.positionsUnit = value

    #=========================================================================================
    # object properties
    #=========================================================================================

    @staticmethod
    def _getCommentText(obj):
        """
        CCPN-INTERNAL: Get a comment from GuiTable
        """
        try:
            if obj.comment == '' or not obj.comment:
                return ''
            else:
                return obj.comment
        except:
            return ''

    @staticmethod
    def _setComment(obj, value):
        """
        CCPN-INTERNAL: Insert a comment into object
        """
        obj.comment = value if value else None

    @staticmethod
    def _getAnnotation(obj):
        """
        CCPN-INTERNAL: Get an annotation from GuiTable
        """
        try:
            if obj.annotation == '' or not obj.annotation:
                return ''
            else:
                return obj.annotation
        except:
            return ''

    @staticmethod
    def _setAnnotation(obj, value):
        """
        CCPN-INTERNAL: Insert an annotation into object
        """
        obj.annotation = value if value else None


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
    _module = PeakTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
