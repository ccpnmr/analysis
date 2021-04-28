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
__dateModified__ = "$dateModified: 2021-04-28 19:59:02 +0100 (Wed, April 28, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-04-26 11:53:10 +0100 (Mon, April 26, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
import random
from functools import partial
from PyQt5 import QtWidgets, QtCore
from collections import OrderedDict
from itertools import zip_longest
from pyqtgraph.widgets.TableWidget import TableWidgetItem
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.core.PeakList import PeakList
from ccpn.core.RestraintList import RestraintList
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.SettingsWidgets import ModuleSettingsWidget, \
    RestraintListSelectionWidget, SpectrumDisplaySelectionWidget
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.ui.gui.widgets.Icon import Icon


logger = getLogger()

UNITS = ['ppm', 'Hz', 'point']

LINKTOPULLDOWNCLASS = 'linkToPulldownClass'
Header1 = '#'
Header2 = 'Peak'
Header3 = '_object'
Header4 = 'Expand'
Header5 = 'Restraint'
Header6 = 'Atoms'
Header7 = 'Violation'

MERGECOLUMN = 1
PIDCOLUMN = 1
EXPANDERCOLUMN = 3
SPANCOLUMNS = (0, 1, 2, 3)
AUTOEXPANDSETTINGS = (True, False, None)
MINSORTCOLUMN = 3


def __ltForTableWidgetItem__(self, other):
    # new routine to overload TableWidgetItem that crashes when sorting None
    if self.sortMode == 'index' and hasattr(other, 'index'):
        return self.index < other.index
    if self.sortMode == 'value' and hasattr(other, 'value'):

        # need to compare the values of they are in the same group (i.e. same name)
        # need to compare the head of the group if different groups

        col = self.column()

        # NOTE:ED - these should be defined as constants in the table header at some point
        #           _groups needs to be defined when the tables are updated to link the required groups
        # if col in [3, 6]:
        if col > MINSORTCOLUMN:
            table = self.tableWidget()
            if getattr(table, '_groups', None):
                # get the names which should be column 0
                dataSelf = table.indexFromItem(table.item(self.row(), PIDCOLUMN)).data()
                dataOther = table.indexFromItem(table.item(other.row(), PIDCOLUMN)).data()

                try:
                    # # if need ascending/descending - group and subgroup
                    # if dataSelf != dataOther:  # different name -> sort by min/max of each group
                    #     if table.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
                    #         return table._groups[dataSelf]['min'][col] < table._groups[dataOther]['min'][col]
                    #     else:
                    #         return table._groups[dataSelf]['max'][col] < table._groups[dataOther]['max'][col]

                    # if need groups ascending/descending - subgroup always max->min
                    if dataSelf != dataOther:  # different name -> sort by min/max of each group
                        return table._groups[dataSelf]['max'][col] < table._groups[dataOther]['max'][col]

                    else:
                        if table.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
                            return (universalSortKey(self.value) > universalSortKey(other.value))
                        else:
                            return (universalSortKey(self.value) < universalSortKey(other.value))
                except Exception as es:
                    getLogger().warning(f'error sorting table on {dataSelf}({dataSelf in table._groups}):{dataOther}({dataOther in table._groups})')

        return (universalSortKey(self.value) < universalSortKey(other.value))

    else:
        if self.text() and other.text():
            return (universalSortKey(self.text()) < universalSortKey(other.text()))
        else:
            return False


class ViolationTableModule(CcpnModule):
    """
    This class implements the module by wrapping a ViolationTable instance
    """

    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'left'
    settingsMinimumSizes = (500, 200)

    includeDisplaySettings = True
    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'ViolationTableModule'

    activePulldownClass = None  # e.g., can make the table respond to current peakList

    def __init__(self, mainWindow=None, name='Violation Table',
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
                                                          'callBack': None,  #self.restraintListPulldown,
                                                          'enabled' : True,
                                                          '_init'   : None,
                                                          'type'    : SpectrumDisplaySelectionWidget,
                                                          'kwds'    : {'texts'      : [],
                                                                       'displayText': [],
                                                                       'defaults'   : []},
                                                          }),
                                    ('RestraintLists', {'label'   : '',
                                                        'tipText' : '',
                                                        'callBack': None,  #self.restraintListPulldown,
                                                        'enabled' : True,
                                                        '_init'   : None,
                                                        'type'    : RestraintListSelectionWidget,
                                                        'kwds'    : {'texts'      : [],
                                                                     'displayText': [],
                                                                     'defaults'   : []},
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
                                    ('autoExpand', {'label'   : 'Auto-expand Groups',
                                                    'tipText' : 'Autotomatically expand/collapse groups on\nadding new restraintList, or sorting.',
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

        self._VTwidget = ModuleSettingsWidget(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                              settingsDict=settingsDict,
                                              grid=(0, 0))
        self._restraintList = self._VTwidget.checkBoxes['RestraintLists']['pulldownList']
        self._restraintList.listWidget.changed.connect(self._updateRestraintLists)
        # self._expandSelector = self._VTwidget.checkBoxes['autoExpand']['pulldownList']

        # mainWidget
        self.violationTable = ViolationTableWidget(parent=self.mainWidget,
                                                   mainWindow=self.mainWindow,
                                                   moduleParent=self,
                                                   setLayout=True,
                                                   grid=(0, 0))

        if peakList is not None:
            self.selectPeakList(peakList)
        elif selectFirstItem:
            self.violationTable.pLwidget.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    @property
    def _dataFrame(self):
        if self.violationTable._dataFrameObject:
            return self.violationTable._dataFrameObject.dataFrame

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.violationTable._maximise()

    def selectPeakList(self, peakList=None):
        """
        Manually select a peakList from the pullDown
        """
        self.violationTable._selectPeakList(peakList)

    def _closeModule(self):
        """Re-implementation of closeModule function from CcpnModule to unregister notification """
        self.violationTable._close()
        super()._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()

    @property
    def dataFrame(self):
        return self.violationTable.dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self.violationTable.dataFrame = dataFrame

    def _updateRestraintLists(self, *args):
        """Update the selected restraintLists
        """
        restraintLists = self._restraintList.getTexts()
        if '<all>' in restraintLists:
            restraintLists = self.project.restraintLists
        else:
            restraintLists = [self.project.getByPid(rList) for rList in restraintLists]
            restraintLists = [rList for rList in restraintLists if rList is not None and isinstance(rList, RestraintList)]

        self.violationTable.updateRestraintLists(restraintLists)

    def _updateAutoExpand(self, expand):
        # index = self._expandSelector.getIndex()
        self.violationTable.updateAutoExpand(expand)


class ViolationTableWidget(GuiTable):
    """
    Class to present a violation Table
    """
    className = 'ViolationTable'
    attributeName = 'peakLists'

    positionsUnit = UNITS[0]  #default

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

        ViolationTableWidget.project = self.project

        self.settingWidgets = None
        self._selectedPeakList = None
        kwds['setLayout'] = True  # Assure we have a layout with the widget
        self._restraintLists = []
        self._autoExpand = False

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

        row += 1
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, gridHPos + 1), gridSpan=(1, 1))

        # not the cleanest way for the minute
        self._hiddenColumns = ['Restraint1', 'Restraint2', 'Restraint3', 'Restraint4', 'Restraint5',
                               'Restraint6', 'Restraint7', 'Restraint8', 'Restraint9']

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
                               className=self.attributeName,
                               pullDownWidget=self.pLwidget,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

        # update method for ccpn sorting with groups
        TableWidgetItem.__lt__ = __ltForTableWidgetItem__
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

    def updateRestraintLists(self, restraintLists):
        """Update the selected restraint lists from the parent module
        """
        self._restraintLists = restraintLists
        self._updateTable()

    def _updateTable(self, useSelectedPeakList=True, peaks=None, peakList=None):
        """Display the restraints on the table for the selected PeakList.
        Obviously, If the restraint has not been previously deleted and flagged isDeleted
        """
        self._selectedPeakList = self.project.getByPid(self.pLwidget.getText())
        self._groups = None

        if useSelectedPeakList:
            if self._selectedPeakList:
                self.populateTable(rowObjects=self._selectedPeakList.peaks,
                                   # columnDefs=self.columns,
                                   selectedObjects=self.current.peaks)
            else:
                self.clear()

        else:
            if peaks:
                if peakList:
                    self.populateTable(rowObjects=peaks,
                                       # columnDefs=self.columns,
                                       selectedObjects=self.current.peaks)
            else:
                self.clear()

        self.updateTableExpanders()

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
        return

    def _selectionCallback(self, data, *args):
        """
        set as current the selected restraints on the table
        """
        return

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
        """Set the auto-expand/collapsd state for adding new restraintLists, or sorting table
        """
        self._autoExpand = expand

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
                                                                 # colDefs=columnDefs,
                                                                 hiddenColumns=self._hiddenColumns,
                                                                 expandColumn='Restraint')

            # populate from the Pandas dataFrame inside the dataFrameObject
            self.setTableFromDataFrameObject(dataFrameObject=_dataFrameObject, columnDefs=self.columns)

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

                # store the current headings, in case table is cleared, to stop table jumping
                self._defaultHeadings = dataFrameObject.headings
                self._defaultHiddenColumns = dataFrameObject.hiddenColumns

                if columnDefs:
                    for col, colFormat in enumerate(columnDefs.formats):
                        if colFormat is not None:
                            self.setFormat(colFormat, column=col)

            # highlight them back again
            self._highLightObjs(objs)

        # outside of the with to spawn a repaint
        self.show()

    def getDataFrameFromExpandedList(self, table=None,
                                     buildList=None,
                                     colDefs=None,
                                     hiddenColumns=None,
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
        _buildColumns = [('#', lambda pk, rt: pk.serial),
                         ('Peak', lambda pk, rt: pk.pid),
                         ('_object', lambda pk, rt: (pk, rt)),
                         ]
        _restraintColumns = [('Restraint', lambda rt: ''),
                             ('Atoms', lambda rt: ''),
                             ('Violation', lambda rt: 0.0),
                             ]

        # define self.columns here
        # create the column objects
        _cols = [
            (Header1, lambda row: _getValueByHeader(row, Header1), 'TipTex1', None, None),
            (Header2, lambda row: _getValueByHeader(row, Header2), 'TipTex2', None, None),
            (Header3, lambda row: _getValueByHeader(row, Header3), 'TipTex3', None, None),
            ]

        if len(self._restraintLists) > 0:
            _buildColumns.append(('Expand', lambda pk, rt: self._downIcon))
            _cols.append((Header4, lambda row: None, 'TipTex4', None, None))

        for col in range(len(self._restraintLists)):
            _cols.append((f'Restraint{col + 1}', lambda row: _getValueByHeader(row, f'Restraint{col + 1}'), f'RTipTex{col + 1}', None, None))
            _cols.append((f'Atoms{col + 1}', lambda row: _getValueByHeader(row, f'Atoms{col + 1}'), f'ATipTex{col + 1}', None, None))
            _cols.append((f'Violation{col + 1}', lambda row: _getValueByHeader(row, f'Violation{col + 1}'), f'VTipTex{col + 1}', None, None))

        self.columns = ColumnClass(_cols)

        if buildList:
            for col, obj in enumerate(buildList):

                if not obj.restraints or len(self._restraintLists) < 1:
                    listItem = OrderedDict()
                    for headerText, func in _buildColumns:
                        listItem[headerText] = func(obj, None)
                    allItems.append(listItem)

                else:
                    _restraints = obj.restraints
                    listItem = OrderedDict()
                    for headerText, func in _buildColumns:
                        listItem[headerText] = func(obj, None)

                    _resLists = OrderedDict([(res, []) for res in self._restraintLists])
                    for _res in _restraints:
                        if _res and _res.restraintList in _resLists:
                            _atoms = self._getContributions(_res)
                            for _atom in _atoms:
                                _resLists[_res.restraintList].append((_res, _atom, random.random()))

                    for val in zip_longest(*_resLists.values()):
                        copyItem = listItem.copy()
                        for cc, rr in enumerate(val):
                            copyItem[f'Restraint{cc + 1}'] = rr[0].pid if rr else ''
                            copyItem[f'Atoms{cc + 1}'] = rr[1] if rr else ''
                            copyItem[f'Violation{cc + 1}'] = rr[2] if rr else 0

                        allItems.append(copyItem)

        _dataFrame = DataFrameObject(dataFrame=pd.DataFrame(allItems, columns=self.columns.headings),
                                     # objectList=objects or [],
                                     # indexList=indexList,
                                     columnDefs=self.columns or [],
                                     hiddenColumns=hiddenColumns or [],
                                     table=table,
                                     )
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
            name = row[PIDCOLUMN]
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

        if EXPANDERCOLUMN >= self.columnCount():
            return

        rows = self.rowCount()
        _order = [self.indexFromItem(self.item(ii, MERGECOLUMN)).data() for ii in range(rows)]
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

                for col in SPANCOLUMNS:
                    self.setSpan(row, col, rowCount + 1, 1)
                self.setRowHidden(row, False)

                _widg = self.cellWidget(row, EXPANDERCOLUMN)
                _widg.updateCellWidget(row, True, setPixMapState=_expand)

                for rr in range(row + 1, row + rowCount):
                    self.setRowHidden(rr, not _expand)
                    _widg = self.cellWidget(rr, EXPANDERCOLUMN)
                    _widg.updateCellWidget(rr, False)

                self.setRowHidden(row + rowCount, not _expand)
                _widg = self.cellWidget(row + rowCount, EXPANDERCOLUMN)
                _widg.updateCellWidget(row + rowCount, False)

                rowCount = 0
                row = i + 1

            else:
                self.setRowHidden(i, False)
                _widg = self.cellWidget(i, EXPANDERCOLUMN)
                _widg.updateCellWidget(i, False)
                row = i + 1

            lastRow = nextRow

        self.resizeRowsToContents()


if __name__ == '__main__':
    # show the empty module
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication


    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add the module to mainWindow
    _module = ViolationTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()
