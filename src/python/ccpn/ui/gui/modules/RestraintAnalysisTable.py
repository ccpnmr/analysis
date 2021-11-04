"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2021-11-04 20:14:38 +0000 (Thu, November 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-04-26 11:53:10 +0100 (Mon, April 26, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
import random

from functools import partial
from PyQt5 import QtWidgets
from collections import OrderedDict
from itertools import zip_longest

from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.Restraint import Restraint
from ccpn.core.RestraintTable import RestraintTable
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CompoundWidgets import DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.TableSorting import MultiColumnTableWidgetItem
from ccpn.ui.gui.widgets.SettingsWidgets import ModuleSettingsWidget, \
    RestraintTableSelectionWidget, SpectrumDisplaySelectionWidget
from ccpn.util.Logging import getLogger
from ccpn.util.Common import makeIterableList
import ccpn.ui.gui.modules.PyMolUtil as pyMolUtil
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.util.Common import flattenLists
from ccpn.util.Path import joinPath


logger = getLogger()

UNITS = ['ppm', 'Hz', 'point']

LINKTOPULLDOWNCLASS = 'linkToPulldownClass'
HeaderIndex = '#'
HeaderPeak = 'Peak Serial'
HeaderObject = '_object'
HeaderExpand = 'Expand'
HeaderRestraint = 'RestraintPid'
HeaderAtoms = 'Atoms'
HeaderMin = 'Min'
HeaderMax = 'Max'
HeaderMean = 'Mean'
HeaderStd = 'STD'
HeaderCount1 = 'Count>0.3'
HeaderCount2 = 'Count>0.5'
nefHeaders = ['restraintpid', 'atoms', 'min', 'max', 'mean', 'std', 'count_0_3', 'count_0_5']
Headers = [HeaderRestraint, HeaderAtoms, HeaderMin, HeaderMax, HeaderMean, HeaderStd, HeaderCount1, HeaderCount2]

ALL = '<Use all>'
PymolScriptName = 'Restraint_Pymol_Template.py'


class RestraintAnalysisTableModule(CcpnModule):
    """
    This class implements the module by wrapping a RestraintAnalysisTable instance
    """

    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'left'
    settingsMinimumSizes = (500, 200)

    includeDisplaySettings = True
    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'RestraintAnalysisTableModule'
    _allowRename = True

    activePulldownClass = None  # e.g., can make the table respond to current peakList

    def __init__(self, mainWindow=None, name='Restraint Analysis Table',
                 peakList=None, selectFirstItem=False):
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        # add the settings widgets defined from the following orderedDict - test for refactored
        settingsDict = OrderedDict((('SpectrumDisplays', {'label'   : '',
                                                          'tipText' : '',
                                                          'callBack': None,  #self.restraintTablePulldown,
                                                          'enabled' : True,
                                                          '_init'   : None,
                                                          'type'    : SpectrumDisplaySelectionWidget,
                                                          'kwds'    : {'texts'      : [],
                                                                       'displayText': [],
                                                                       'defaults'   : [],
                                                                       'objectName' : 'SpectrumDisplaysSelection'},
                                                          }),
                                    ('RestraintTables', {'label'   : '',
                                                        'tipText' : '',
                                                        'callBack': None,  #self.restraintTablePulldown,
                                                        'enabled' : True,
                                                        '_init'   : None,
                                                        'type'    : RestraintTableSelectionWidget,
                                                        'kwds'    : {'texts'      : [],
                                                                     'displayText': [],
                                                                     'defaults'   : [],
                                                                     'objectName' : 'RestraintTablesSelection'},
                                                        }),
                                    # ('autoExpand', {'label'   : '',
                                    #                 'tipText' : '',
                                    #                 'callBack': self._updateAutoExpand,
                                    #                 'enabled' : True,
                                    #                 'checked' : False,
                                    #                 '_init'   : None,
                                    #                 'type'    : RadioButtonsCompoundWidget,
                                    #                 'kwds'    : {'labelText'   : 'Auto-Expand Groups',
                                    #                              'compoundKwds': {'direction': 'h',
                                    #                                               'hAlign'   : 'l',
                                    #                                               'texts'    : ['Collapse', 'Expand', 'Ignore'], }
                                    #                              }
                                    #                 }),
                                    ('meanLowerLimit', {'label'   : 'Mean Value Lower Limit',
                                                        'callBack': self._updateMeanLowerLimit,
                                                        'enabled' : True,
                                                        '_init'   : None,
                                                        'type'    : DoubleSpinBoxCompoundWidget,
                                                        'kwds'    : {'labelText': 'Mean Value Lower Limit',
                                                                     'tipText'  : 'Lower threshold for mean value of restraints',
                                                                     'range'    : (0.0, 1.0),
                                                                     'decimals' : 2,
                                                                     'step'     : 0.05,
                                                                     'value'    : 0.3},
                                                        }),
                                    ('autoExpand', {'label'   : 'Auto-expand Groups',
                                                    'tipText' : 'Automatically expand/collapse groups on\nadding new restraintTable, or sorting.',
                                                    'callBack': self._updateAutoExpand,
                                                    'enabled' : True,
                                                    'checked' : False,
                                                    '_init'   : None,
                                                    }),
                                    ('sequentialStrips', {'label'   : 'Show sequential strips',
                                                          'tipText' : 'Show nmrResidue in all strips.',
                                                          'callBack': None,  #self.showNmrChainFromPulldown,
                                                          'enabled' : True,
                                                          'checked' : False,
                                                          '_init'   : None,
                                                          }),
                                    ('markPositions', {'label'   : 'Mark positions',
                                                       'tipText' : 'Mark positions in all strips.',
                                                       'callBack': None,  #self.showNmrChainFromPulldown,
                                                       'enabled' : True,
                                                       'checked' : True,
                                                       '_init'   : None,
                                                       }),
                                    ('autoClearMarks', {'label'   : 'Auto clear marks',
                                                        'tipText' : 'Auto clear all previous marks',
                                                        'callBack': None,
                                                        'enabled' : True,
                                                        'checked' : True,
                                                        '_init'   : None,
                                                        }),
                                    ))
        if self.activePulldownClass:
            settingsDict.update(OrderedDict(((LINKTOPULLDOWNCLASS, {'label'   : 'Link to current %s:' % self.activePulldownClass.className,
                                                                    'tipText' : 'Set/update current %s when selecting from pulldown' % self.activePulldownClass.className,
                                                                    'callBack': None,
                                                                    'enabled' : True,
                                                                    'checked' : True,
                                                                    '_init'   : None,
                                                                    }),
                                             )))

        self._RATwidget = ModuleSettingsWidget(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                               settingsDict=settingsDict,
                                               grid=(0, 0))
        # self._displayListWidget = self._RATwidget.checkBoxes['SpectrumDisplays']['widget']
        # self._restraintTable = self._RATwidget.checkBoxes['RestraintTables']['widget']
        self._displayListWidget = self._RATwidget.getWidget('SpectrumDisplays')
        self._restraintTable = self._RATwidget.getWidget('RestraintTables')
        self._restraintTable.listWidget.changed.connect(self._updateRestraintTables)
        # self._expandSelector = self._RATwidget.checkBoxes['autoExpand']['widget']

        self._meanLowerLimitSpinBox = self._RATwidget.checkBoxes['meanLowerLimit']['widget']
        self._autoExpandCheckBox = self._RATwidget.checkBoxes['autoExpand']['widget']

        # mainWidget
        self.restraintAnalysisTable = RestraintAnalysisTableWidget(parent=self.mainWidget,
                                                                   mainWindow=self.mainWindow,
                                                                   moduleParent=self,
                                                                   setLayout=True,
                                                                   grid=(0, 0))

        if peakList is not None:
            self.selectPeakList(peakList)
        elif selectFirstItem:
            self.restraintAnalysisTable.pLwidget.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    @property
    def _dataFrame(self):
        if self.restraintAnalysisTable._dataFrameObject:
            return self.restraintAnalysisTable._dataFrameObject.dataFrame

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.restraintAnalysisTable._maximise()

    def selectPeakList(self, peakList=None):
        """
        Manually select a peakList from the pullDown
        """
        self.restraintAnalysisTable._selectPeakList(peakList)

    def _closeModule(self):
        """Re-implementation of closeModule function from CcpnModule to unregister notification """
        self.restraintAnalysisTable._close()
        super()._closeModule()

    def restoreWidgetsState(self, **widgetsState):
        super().restoreWidgetsState(**widgetsState)
        getLogger().debug(f'RestraintTableModule {self} - restoreWidgetsState')

        # need to set the values from the restored state
        self.restraintAnalysisTable._updateSettings(self._meanLowerLimitSpinBox.getValue(),
                                                    self._autoExpandCheckBox.get())

    @property
    def dataFrame(self):
        return self.restraintAnalysisTable.dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self.restraintAnalysisTable.dataFrame = dataFrame

    def _updateRestraintTables(self, *args):
        """Update the selected restraintTables
        """
        restraintTables = self._restraintTable.getTexts()
        if ALL in restraintTables:
            restraintTables = self.project.restraintTables
        else:
            restraintTables = [self.project.getByPid(rList) for rList in restraintTables]
            restraintTables = [rList for rList in restraintTables if rList is not None and isinstance(rList, RestraintTable)]

        self.restraintAnalysisTable.updateRestraintTables(restraintTables)

    def _updateAutoExpand(self, expand):
        # index = self._expandSelector.getIndex()
        self.restraintAnalysisTable.updateAutoExpand(expand)

    def _updateMeanLowerLimit(self, value):
        self.restraintAnalysisTable.updateMeanLowerLimit(value)


class RestraintAnalysisTableWidget(GuiTable):
    """
    Class to present a Restraint Analysis Table
    """
    className = 'RestraintAnalysisTable'
    attributeName = 'peakLists'

    positionsUnit = UNITS[0]  #default

    # define _columns for multi-column sorting
    ITEMKLASS = MultiColumnTableWidgetItem
    MERGECOLUMN = 1
    PIDCOLUMN = 1
    EXPANDERCOLUMN = 3
    SPANCOLUMNS = (0, 1, 2, 3)
    MINSORTCOLUMN = 3

    enableMultiColumnSort = True
    # groups are always max->min
    applySortToGroups = False

    PRIMARYCOLUMN = '_object'  # column holding active objects (pids for this table)

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, peakList=None, multiSelect=True,
                 actionCallback=None, selectionCallback=None, **kwds):
        """
        Initialise the table
        """
        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        RestraintAnalysisTableWidget.project = self.project

        self.settingWidgets = None
        self._selectedPeakList = None
        kwds['setLayout'] = True  # Assure we have a layout with the widget
        self._restraintTables = []
        self._autoExpand = False
        self._meanLowerLimit = 0.0

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        row = 0
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self.pLwidget = PeakListPulldown(parent=self._widget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, gridHPos), gridSpan=(1, 1),
                                         showSelectName=True,
                                         minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=self._pulldownPLcallback,
                                         )

        gridHPos += 1
        self.expandButtons = ButtonList(parent=self._widget, texts=[' Expand all', ' Collapse all'], grid=(row, gridHPos),
                                        callbacks=[partial(self._expandAll, True), partial(self._expandAll, False), ])

        gridHPos += 1
        self.showOnViewerButton = Button(self._widget, tipText='Show on Molecular Viewer',
                                         icon=Icon('icons/showStructure'),
                                         callback=self._showOnMolecularViewer,
                                         grid=(row, gridHPos), hAlign='l')

        row += 1
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, gridHPos + 1), gridSpan=(1, 1))
        self._widget.getLayout().setColumnStretch(gridHPos + 1, 2)

        # not the cleanest way for the minute
        self._hiddenColumns = ['Restraint_1', 'Restraint_2', 'Restraint_3', 'Restraint_4', 'Restraint_5',
                               'Restraint_6', 'Restraint_7', 'Restraint_8', 'Restraint_9']

        self.dataFrameObject = None
        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True, multiSelect=multiSelect,
                         actionCallback=actionCallback,
                         selectionCallback=selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        # populate the table if there are peakLists in the project
        if peakList is not None:
            self._selectPeakList(peakList)

        self.setTableNotifiers(tableClass=PeakList,
                               rowClass=Peak,
                               # cellClassNames=(Restraint, 'restraints'),
                               # tableName='peakList', rowName='peak',
                               # changeFunc=self._updateTable,
                               className=self.attributeName,
                               # updateFunc=self._updateTable,
                               tableSelection='_selectedPeakList',
                               pullDownWidget=self.pLwidget,
                               callBackClass=Peak,
                               selectCurrentCallBack=self._selectOnTableCurrentPeaksNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

        # update method for ccpn sorting with groups
        # TableWidgetItem.__lt__ = __ltForTableWidgetItem__

        self.horizontalHeader().sectionClicked.connect(self.onSectionClicked)
        self.horizontalHeader().setMinimumSectionSize(32)

        self._downIcon = Icon('icons/caret-grey-down')
        self._rightIcon = Icon('icons/caret-grey-right')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Updates
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _maximise(self):
        """Refresh the table on a maximise event
        """
        self._updateTable()

    def updateRestraintTables(self, restraintTables):
        """Update the selected restraint lists from the parent module
        """
        self._restraintTables = restraintTables
        self._updateTable()

    def _updateTable(self, useSelectedPeakList=True, peaks=None, peakList=None):
        """Display the restraints on the table for the selected PeakList.
        Obviously, If the restraint has not been previously deleted and flagged isDeleted
        """
        self._selectedPeakList = self.project.getByPid(self.pLwidget.getText())
        self._groups = None
        self.hide()

        if useSelectedPeakList:
            if self._selectedPeakList:
                self.populateTable(rowObjects=self._selectedPeakList.peaks,
                                   # columnDefs=self._columns,
                                   selectedObjects=self.current.peaks)
            else:
                self.clear()

        else:
            if peaks:
                if peakList:
                    self.populateTable(rowObjects=peaks,
                                       # columnDefs=self._columns,
                                       selectedObjects=self.current.peaks)
            else:
                self.clear()

        self.updateTableExpanders()
        self.show()

    def _selectPeakList(self, peakList=None):
        """Manually select a PeakList from the pullDown
        """
        if peakList is None:
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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Widgets callbacks
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _getPullDownSelection(self):
        return self.pLwidget.getText()

    def _actionCallback(self, data, *args):
        """If current strip contains the double clicked peak will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

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
            self.current.clearRestraints()
        else:
            self.current.peaks = peaks
            self.current.restraints = list(set(res for pk in peaks
                                               for res in pk.restraints if res and res.restraintTable in self._restraintTables))

    def _pulldownPLcallback(self, data):
        self._updateTable()

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        return

    def _expandAll(self, expand):
        """Expand/collapse all groups
        """
        self.updateTableExpanders(expand)

    def updateAutoExpand(self, expand):
        """Set the auto-expand/collapsed state for adding new restraintTables, or sorting table
        """
        self._autoExpand = expand

    def updateMeanLowerLimit(self, value):
        """Set the lower limit for visible restraints
        """
        self._meanLowerLimit = value
        self._updateTable()

    def _updateSettings(self, meanLowerLimit, expand):
        self._meanLowerLimit = meanLowerLimit
        self._autoExpand = expand

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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Subclass GuiTable
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def populateTable(self, rowObjects=None, columnDefs=None,
                      selectedObjects=None):
        """Populate the table with a set of objects to highlight, or keep current selection highlighted
        with the first item visible.

        Use selectedObjects = [] to clear the selected items

        :param rowObjects: list of objects to set each row
        """
        self.project.blankNotification()

        # if nothing passed in then keep the current highlighted objects
        objs = selectedObjects if selectedObjects is not None else self.getSelectedObjects()

        try:
            _dataFrameObject = self.getDataFrameFromExpandedList(table=self,
                                                                 buildList=rowObjects,
                                                                 expandColumn='Restraint')

            # populate from the Pandas dataFrame inside the dataFrameObject
            self.setTableFromDataFrameObject(dataFrameObject=_dataFrameObject, columnDefs=self._columns)

        except Exception as es:
            getLogger().warning('Error populating table', str(es))
            raise es

        finally:
            self._highLightObjs(objs)
            self.project.unblankNotification()

    def setTableFromDataFrameObject(self, dataFrameObject, columnDefs=None):
        """Populate the table from a Pandas dataFrame
        """

        with self._tableBlockSignals('setTableFromDataFrameObject'):

            # get the currently selected objects
            objs = self.getSelectedObjects()

            self._dataFrameObject = dataFrameObject

            with self._guiTableUpdate(dataFrameObject):
                if not dataFrameObject.dataFrame.empty:
                    self.setData(dataFrameObject.dataFrame.values)
                    self._updateGroups(dataFrameObject.dataFrame)

                else:
                    # set a dummy row of the correct length
                    self.setData([list(range(len(dataFrameObject.headings)))])
                    self._groups = None

                if columnDefs:
                    for col, colFormat in enumerate(columnDefs.formats):
                        if colFormat is not None:
                            self.setFormat(colFormat, column=col)

            # highlight them back again
            self._highLightObjs(objs)

    def _highLightObjs(self, selection, scrollToSelection=True):

        # skip if the table is empty
        if not self._dataFrameObject:
            return

        with self._tableBlockSignals('_highLightObjs'):

            selectionModel = self.selectionModel()
            model = self.model()

            itm = self.currentItem()

            selectionModel.clearSelection()
            if selection:
                if len(selection) > 0:
                    if isinstance(selection[0], pd.Series):
                        # not sure how to handle this
                        return
                uniqObjs = set(selection)

                _peakObjects = tuple(_getValueByHeader(row, 3) for row in self._dataFrameObject.objects)
                rows = [self._dataFrameObject.find(self, str(obj.pid), column='_object', multiRow=True) for obj in uniqObjs]
                # if obj in _peakObjects and obj.peakList == self._selectedPeakList]
                rows = [row for row in set(makeIterableList(rows)) if row is not None]
                if rows:
                    rows.sort(key=lambda c: int(c))

                    # remember the current cell so that cursor work correctly
                    if itm and itm.row() in rows:
                        self.setCurrentItem(itm)
                        _row = itm.row()
                    else:
                        _row = rows[0]
                        rowIndex = model.index(_row, 0)
                        self.setCurrentIndex(rowIndex)

                    for row in rows:
                        if row != _row:
                            rowIndex = model.index(row, 0)
                            selectionModel.select(rowIndex, selectionModel.Select | selectionModel.Rows)

                    if scrollToSelection and not self._scrollOverride:
                        self.scrollToSelectedIndex()

    def getDataFrameFromExpandedList(self, table=None,
                                     buildList=None,
                                     colDefs=None,
                                     expandColumn=None):
        """
        Return a Pandas dataFrame from an internal list of objects
        The columns are based on the 'func' functions in the columnDefinitions

        :param buildList:
        :param colDefs:
        :return pandas dataFrameObject:
        """
        allItems = []

        # building...
        _buildColumns = [(HeaderIndex, lambda pk, rt: pk.serial),
                         (HeaderPeak, lambda pk, rt: pk.pid),
                         (HeaderObject, lambda pk, rt: (pk, rt)),
                         ]
        _restraintColumns = [(HeaderRestraint, lambda rt: ''),
                             (HeaderAtoms, lambda rt: ''),
                             (HeaderMin, lambda rt: 0.0),
                             (HeaderMax, lambda rt: 0.0),
                             (HeaderMean, lambda rt: 0.0),
                             (HeaderStd, lambda rt: 0.0),
                             (HeaderCount1, lambda rt: 0.0),
                             (HeaderCount2, lambda rt: 0.0),
                             ]

        # define self._columns here
        # create the column objects
        _cols = [
            (HeaderIndex, lambda row: _getValueByHeader(row, HeaderIndex), 'TipTex1', None, None),
            (HeaderPeak, lambda row: _getValueByHeader(row, HeaderPeak), 'TipTex2', None, None),
            (HeaderObject, lambda row: _getValueByHeader(row, HeaderObject), 'TipTex3', None, None),
            ]

        if len(self._restraintTables) > 0:
            _buildColumns.append((HeaderExpand, lambda pk, rt: self._downIcon))
            _cols.append((HeaderExpand, lambda row: None, 'TipTex4', None, None))

        # for col in range(len(self._restraintTables)):
        #     for _colID in (HeaderRestraint, HeaderAtoms, HeaderMin, HeaderMax, HeaderMean, HeaderStd, HeaderCount1, HeaderCount2):
        #         _cols.append((f'{_colID}_{col + 1}', lambda row: _getValueByHeader(row, f'{_colID}_{col + 1}'), f'{_colID}_Tip{col + 1}', None, None))
        #
        #     # _cols.append((f'Restraint{col + 1}', lambda row: _getValueByHeader(row, f'Restraint{col + 1}'), f'RTipTex{col + 1}', None, None))
        #     # _cols.append((f'Atoms{col + 1}', lambda row: _getValueByHeader(row, f'Atoms{col + 1}'), f'ATipTex{col + 1}', None, None))
        #     # _cols.append((f'Violation{col + 1}', lambda row: _getValueByHeader(row, f'Violation{col + 1}'), f'VTipTex{col + 1}', None, None))
        #
        # self._columns = ColumnClass(_cols)

        # if buildList:
        #     for col, obj in enumerate(buildList):
        #
        #         # ids = pd.DataFrame({'#': [pk.serial for pk in buildList], 'Peak': [pk.pid for pk in buildList], '_object': [pk for pk in buildList], 'Expand': [None for pk in buildList]})
        #         # df1 = pd.DataFrame([(pk, res) for pk in buildList for res in pk.restraints if res.restraintTable == rl], columns=['Peak', 'Pid_1'])
        #         # rl1 = pd.merge(ids['Peak'], df1, how='right')
        #
        #         if not obj.restraints or len(self._restraintTables) < 1:
        #             listItem = OrderedDict()
        #             for headerText, func in _buildColumns:
        #                 listItem[headerText] = func(obj, None)
        #             allItems.append(listItem)
        #
        #         else:
        #             _restraints = obj.restraints
        #             listItem = OrderedDict()
        #             for headerText, func in _buildColumns:
        #                 listItem[headerText] = func(obj, None)
        #
        #             _resLists = OrderedDict([(res, []) for res in self._restraintTables])
        #
        #             # get the result from the dataSet.data
        #             # rl = self._restraintTables[0]; rl.structureData.data[0].parameters.get('results')
        #             #
        #             # rename the columns to match
        #             # viols.columns = [col+'_{ii+1}' for col in viols.columns]
        #             #
        #             # pd.merge(blank, viols, on=['Pid_1', 'Atoms_1'], how='left').fillna(0.0)
        #
        #             for _res in _restraints:
        #                 if _res and _res.restraintTable in _resLists:
        #                     _atoms = self._getContributions(_res)
        #                     for _atom in _atoms:
        #                         _resLists[_res.restraintTable].append((_res, _atom, 0.0))
        #
        #             for val in zip_longest(*_resLists.values()):
        #                 copyItem = listItem.copy()
        #                 for cc, rr in enumerate(val):
        #                     copyItem[f'{HeaderRestraint}_{cc + 1}'] = rr[0].pid if rr else ''
        #                     copyItem[f'{HeaderAtoms}_{cc + 1}'] = rr[1] if rr else ''
        #                     # for _colID in (HeaderMin, HeaderMax, HeaderMean, HeaderStd, HeaderCount1, HeaderCount2):
        #                     #     copyItem[f'{_colID}_{cc + 1}'] = rr[2] if rr else 0
        #
        #                 allItems.append(copyItem)
        #
        #     pass
        #
        # _dataFrame = DataFrameObject(dataFrame=pd.DataFrame(allItems, _columns=self._columns.headings),
        #                              # objectList=objects or [],
        #                              # indexList=indexList,
        #                              columnDefs=self._columns or [],
        #                              table=table,
        #                              )
        # _objects = [row for row in _dataFrame.dataFrame.itertuples()]
        # _dataFrame._objects = _objects
        #
        # return _dataFrame

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

        # print('Create violation dataFrames')

        def _getContributions(restraint):
            return [' - '.join(sorted(ri)) for rc in restraint.restraintContributions
                    for ri in rc.restraintItems]

        # get the target peakLists
        pks = buildList
        resLists = self._restraintTables

        if resLists:
            # make references for quicker access later
            contribs = {res: _getContributions(res) for rList in resLists for res in rList.restraints}

            # make a dict of peak.restraints as this is reverse generated by the api every call to peak.restraints
            # pkRes = {}
            pkRestraints = {}
            for resList in resLists:
                for res in resList.restraints:
                    for pk in res.peaks:
                        pkRestraints.setdefault(pk.serial, set()).add(res)
                        # pkRes.setdefault(pk, {})
                        # pkRes[pk].setdefault(resList, set()).add(res)

            # get the maximum number of restraintItems from each restraint list
            counts = [np.array([sum([
                len(contribs[res]) for res in (pkRestraints.get(pk.serial) or ()) if res and res.restraintTable == rList
                ])
                for pk in pks])
                for rList in resLists]
            maxCount = np.max(counts, axis=0)
            # print(f' max counts {list(maxCount)}')
            # maxCount += 1

            # allPks = pd.DataFrame([(pk.serial, pk, None)  for pk, count in zip(pks, maxCount) for rr in range(count)], columns=['Peak', '_object', 'Expand'])
            allPkSerials = pd.DataFrame([pk.serial for pk, count in zip(pks, maxCount) for rr in range(count)], columns=['PeakSerial', ])
            index = pd.DataFrame([ii for ii in range(1, len(allPkSerials) + 1)], columns=['index', ])
            allPks = pd.DataFrame([(pk.serial, pk.pid, self._downIcon) for pk, count in zip(pks, maxCount) for rr in range(count)], columns=['PeakSerial', '_object', 'Expand'])

            # make matching length tables for each of the restraintTables for each peak so the rows match up in the table
            dfs = {}
            ll = [(None, None)] * sum(maxCount)
            for lCount, rl in enumerate(resLists):
                head = 0
                for pk, cc, maxcc in zip(pks, counts[lCount], maxCount):
                    _res = [(res.pid, _atom) for res in (pkRestraints.get(pk.serial) or ()) if res.restraintTable == rl
                            for _atom in contribs[res]]
                    if _res:
                        ll[head:head + len(_res)] = _res

                    head += maxcc

                # put the serial and atoms into another table to be concatenated to the right, lCount = index in resLists
                dfs[rl] = pd.concat([allPkSerials,
                                     pd.DataFrame(ll, columns=[f'{HeaderRestraint}_{lCount + 1}',
                                                               f'Atoms_{lCount + 1}'])], axis=1)

            # get the dataSets that contain data with a matching 'result' name - should be violations
            violationResults = {resList: viols.copy() if viols is not None else None
                                for resList in resLists
                                for data in resList.structureData.data if resList.name == data.name
                                for k, viols in data.parameters.items() if k == 'results'}

            # rename the columns to match the order in visible list - number must match the position in the selected restraintTables
            for ii, (k, resViol) in enumerate(violationResults.items()):
                ind = resLists.index(k)
                resViol.columns = [vv + f'_{ind + 1}' for vv in resViol.columns]

            # merge all the tables for each restraintTable
            _out = {}
            zeroCols = []
            for ii, resList in enumerate(resLists):
                if resList in violationResults:

                    _left = dfs[resList]
                    _right = violationResults[resList]
                    if (f'{HeaderRestraint}_{ii + 1}' in _left.columns and f'Atoms_{ii + 1}' in _left.columns) and \
                            (f'{HeaderRestraint}_{ii + 1}' in _right.columns and f'Atoms_{ii + 1}' in _right.columns):
                        _out[resList] = pd.merge(_left, _right, on=[f'{HeaderRestraint}_{ii + 1}', f'Atoms_{ii + 1}'], how='left').drop(columns=['PeakSerial']).fillna(0.0)
                        zeroCols.append(f'{HeaderMean}_{ii + 1}')

                    for _colID in (HeaderRestraint, HeaderAtoms, HeaderMin, HeaderMax, HeaderMean, HeaderStd, HeaderCount1, HeaderCount2):
                        _cols.append((f'{_colID}_{ii + 1}', lambda row: _getValueByHeader(row, f'{_colID}_{ii + 1}'), f'{_colID}_Tip{ii + 1}', None, None))

            # concatenate the final dataFrame
            _table = pd.concat([index, allPks, *_out.values()], axis=1)
            # # purge all rows that contain all means == 0, fastest method
            # _table = _table[np.count_nonzero(_table[zeroCols].values, axis=1) > 0]
            # process all row that have means > 0.3, keep only rows that contain at least one valid mean
            _table = _table[(_table[zeroCols] >= self._meanLowerLimit).sum(axis=1) > 0]

        else:
            # make a table that only has peaks
            index = pd.DataFrame([ii for ii in range(1, len(pks) + 1)], columns=['index'])
            allPks = pd.DataFrame([(pk.serial, pk.pid, self._downIcon) for pk in pks], columns=['PeakSerial', '_object', 'Expand'])

            _table = pd.concat([index, allPks], axis=1)

        # set the table _columns
        self._columns = ColumnClass(_cols)

        # set the table from the dataFrame
        _dataFrame = DataFrameObject(dataFrame=_table,
                                     columnDefs=self._columns or [],
                                     table=table,
                                     )
        # extract the row objects from the dataFrame
        _objects = [row for row in _dataFrame.dataFrame.itertuples()]
        _dataFrame._objects = _objects

        return _dataFrame

    def refreshTable(self):
        # subclass to refresh the groups
        self.setTableFromDataFrameObject(self._dataFrameObject)
        self.updateTableExpanders()

    def setDataFromSearchWidget(self, dataFrame):
        """Set the data for the table from the search widget
        """
        self.setData(dataFrame.values)
        self._updateGroups(dataFrame)
        self.updateTableExpanders()

    @staticmethod
    def _getContributions(restraint):
        """
        CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
        using ChemicalShiftList
        """
        return [' - '.join(ri) for rc in restraint.restraintContributions for ri in rc.restraintItems]

        # if len(restraint.restraintContributions) > 0:
        #     if restraint.restraintContributions[0].restraintItems:
        #         # return restraint.restraintContributions[0].restraintItems[0]
        #         return [' - '.join(rr) for rr in restraint.restraintContributions[0].restraintItems]
        # else:
        #     return ''

    @staticmethod
    def _getSortedContributions(restraint):
        """
        CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
        using ChemicalShiftList
        """
        return [sorted(ri) for rc in restraint.restraintContributions for ri in rc.restraintItems if ri]

    def _updateGroups(self, df):
        self._groups = {}
        # collate max/min information
        for row in df.itertuples(index=False):
            name = str(row[self.PIDCOLUMN])
            if name not in self._groups:
                _row = tuple(universalSortKey(x) for x in row)
                self._groups[name] = {'min': _row, 'max': _row}
            else:
                self._groups[name]['min'] = tuple(map(lambda x, y: min(universalSortKey(x), y), row, self._groups[name]['min']))
                self._groups[name]['max'] = tuple(map(lambda x, y: max(universalSortKey(x), y), row, self._groups[name]['max']))

    def onSectionClicked(self, *args):
        """Respond to reordering the table
        """
        self.updateTableExpanders()

    def updateTableExpanders(self, expandState=None):
        """Update the state of the expander buttons
        """
        if not isinstance(expandState, (bool, type(None))):
            raise TypeError('expandState must be bool or None')

        if self.EXPANDERCOLUMN >= self.columnCount():
            return

        rows = self.rowCount()
        _order = [self.indexFromItem(self.item(ii, self.MERGECOLUMN)).data() for ii in range(rows)]
        if not _order:
            return

        self.clearSpans()

        row = rowCount = 0
        lastRow = _order[row]
        _expand = self._autoExpand if expandState is None else expandState

        for i in range(0, rows):

            nextRow = _order[i + 1] if i < (rows - 1) else None  # catch the last group, otherwise need try/except

            if lastRow == nextRow:
                rowCount += 1

            elif rowCount > 0:

                for col in self.SPANCOLUMNS:
                    self.setSpan(row, col, rowCount + 1, 1)
                self.setRowHidden(row, False)

                _widg = self.cellWidget(row, self.EXPANDERCOLUMN)
                _widg.updateCellWidget(row, True, setPixMapState=_expand)

                for rr in range(row + 1, row + rowCount):
                    self.setRowHidden(rr, not _expand)
                    _widg = self.cellWidget(rr, self.EXPANDERCOLUMN)
                    _widg.updateCellWidget(rr, False)

                self.setRowHidden(row + rowCount, not _expand)
                _widg = self.cellWidget(row + rowCount, self.EXPANDERCOLUMN)
                _widg.updateCellWidget(row + rowCount, False)

                rowCount = 0
                row = i + 1

            else:
                self.setRowHidden(i, False)
                _widg = self.cellWidget(i, self.EXPANDERCOLUMN)
                _widg.updateCellWidget(i, False)
                row = i + 1

            lastRow = nextRow

        self.resizeRowsToContents()

    def _showOnMolecularViewer(self):

        pdbPath = None
        selectedPeaks = self.getSelectedObjects() or []
        ## get the restraints to display
        restraints = flattenLists([pk.restraints for pk in selectedPeaks])
        ## get the PDB file from the parent restraintTable.
        for rs in restraints:
            if rs.restraintTable.moleculeFilePath:
                pdbPath = rs.restraintTable.moleculeFilePath
                getLogger().info('Using pdb file %s for displaying violation on Molecular viewer.' % pdbPath)
                break
        ## run Pymol
        pymolScriptPath = joinPath(self.application.pymolScriptsPath, PymolScriptName)
        if pdbPath is None:
            MessageDialog.showWarning('No Molecule File found',
                                      '''To add a molecule file path to the RestraintTable: Find the restraintTable on sideBar, 
                                      open the properties popup, add a full PDB file path in the entry widget.''')
            return
        pymolScriptPath = pyMolUtil._restraintsSelection2PyMolFile(pymolScriptPath, pdbPath, restraints)
        pyMolUtil.runPymolWithScript(self.application, pymolScriptPath)


if __name__ == '__main__':
    # show the empty module
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication


    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add the module to mainWindow
    _module = RestraintAnalysisTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()
