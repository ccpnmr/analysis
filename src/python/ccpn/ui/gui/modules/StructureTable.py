"""
This file contains StructureTableModule and StructureTable classes
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
__dateModified__ = "$dateModified: 2022-05-05 10:28:06 +0100 (Thu, May 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from collections import OrderedDict

from ccpn.core.StructureEnsemble import StructureEnsemble as KlassTable
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import StructureEnsemblePulldown as KlassPulldown
from ccpn.ui.gui.widgets.Column import ColumnClass
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.SettingsWidgets import ModuleSettingsWidget
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableView, _updateSimplePandasTable
from ccpn.ui.gui.lib._CoreTableFrame import _CoreTableWidgetABC, _CoreTableFrameABC
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot


ALL = '<all>'
LINKTOPULLDOWNCLASS = 'linkToPulldownClass'


class StructureTableModule(CcpnModule):
    """This class implements the module by wrapping a StructureTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'top'

    activePulldownClass = KlassTable

    className = 'StructureTableModule'
    _allowRename = True

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='Structure Table',
                 structureEnsemble=None, selectFirstItem=False):
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
        self._setWidgets(self.settingsWidget, self.mainWidget, structureEnsemble, selectFirstItem)
        self._setCallbacks()

    def _setWidgets(self, settingsWidget, mainWidget, structureEnsemble, selectFirstItem):
        """Set up the widgets for the module
        """
        self._settings = None
        if self.activePulldownClass:
            # add to settings widget - see sequenceGraph for more detailed example
            settingsDict = OrderedDict(((LINKTOPULLDOWNCLASS, {'label'   : 'Link to current %s' % self.activePulldownClass.className,
                                                               'tipText' : 'Set/update current %s when selecting from pulldown' % self.activePulldownClass.className,
                                                               'callBack': None,
                                                               'enabled' : True,
                                                               'checked' : False,
                                                               '_init'   : None,
                                                               }),
                                        ))
            self._settings = ModuleSettingsWidget(parent=settingsWidget, mainWindow=self.mainWindow,
                                                  settingsDict=settingsDict,
                                                  grid=(0, 0))

        # add the frame containing the pulldown and table
        self._mainFrame = StructureTableFrame(parent=mainWidget,
                                              mainWindow=self.mainWindow,
                                              moduleParent=self,
                                              structureEnsemble=structureEnsemble, selectFirstItem=selectFirstItem,
                                              grid=(0, 0))

    @property
    def tableFrame(self):
        """Return the table frame
        """
        return self._mainFrame

    @property
    def tableWidget(self):
        """Return the table widget in the table frame
        """
        return self._mainFrame._tableWidget

    def _setCallbacks(self):
        """Set the active callbacks for the module
        """
        if self.activePulldownClass:
            self._setCurrentPulldown = Notifier(self.current,
                                                [Notifier.CURRENT],
                                                targetName=self.activePulldownClass._pluralLinkName,
                                                callback=self._mainFrame._selectCurrentPulldownClass)

            # set the active callback from the pulldown
            self._mainFrame.setActivePulldownClass(coreClass=self.activePulldownClass,
                                                   # checkBox=getattr(self.nmrResidueTableSettings, LINKTOPULLDOWNCLASS, None)
                                                   checkBox=self._settings.checkBoxes[LINKTOPULLDOWNCLASS]['widget'])

        # set the dropped callback through mainWidget
        self.mainWidget._dropEventCallback = self._mainFrame._processDroppedItems

    def selectTable(self, table):
        """Select the object in the table
        """
        self._mainFrame.selectTable(table)

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self.tableFrame._closeFrame()
        super()._closeModule()


class GuiTableStructure(GuiTable):
    """GuiTable specific to tables that only contain a single pid for the pandas dataframe
    """

    def __init__(self, *args, **kwargs):
        super(GuiTableStructure, self).__init__(*args, **kwargs)

    def _selectionTableCallback(self, itemSelection, mouseDrag=True):
        with self._tableBlockSignals('_selectionTableCallback'):

            rowList = self.getSelectedRows()
            dataTable = {}
            for col in range(self.columnCount()):
                colName = self.horizontalHeaderItem(col).text()
                dataTable[colName] = []
                for row in rowList:
                    dataTable[colName].append(self.item(row, col).text())
            newPd = pd.DataFrame.from_dict(dataTable)

            if rowList:
                data = CallBack(theObject=self._dataFrameObject,
                                object=newPd,
                                index=None,
                                targetName=self.className,
                                trigger=CallBack.DOUBLECLICK,
                                row=None,
                                col=None,
                                rowItem=None)

                self._selectionCallback(data)

    def _getPullDownSelection(self):
        return self.stWidget.getText()

    def _selectPullDown(self, value):
        self.stWidget.select(value)

    def _doubleClickCallback(self, itemSelection):
        model = self.selectionModel()

        # selects all the items in the row
        selection = model.selectedRows()

        if itemSelection:
            row = itemSelection.row()
            col = itemSelection.column()

            dataTable = {}
            for colFind in range(self.columnCount()):
                colName = self.horizontalHeaderItem(colFind).text()
                dataTable[colName] = []
                dataTable[colName].append(self.item(row, colFind).text())
            newPd = pd.DataFrame.from_dict(dataTable)

            data = CallBack(theObject=self._dataFrameObject,
                            object=newPd,
                            index=None,
                            targetName=self.className,
                            trigger=CallBack.DOUBLECLICK,
                            row=row,
                            col=col,
                            rowItem=dataTable)

            if self._actionCallback and not self._dataFrameObject.columnDefinitions.setEditValues[col]:  # ejb - editable fields don't actionCallback
                self._actionCallback(data)
            elif self._dataFrameObject.columnDefinitions.setEditValues[col]:  # ejb - editable fields don't actionCallback:
                item = self.item(row, col)
                item.setEditable(True)
                # self.itemDelegate().closeEditor.connect(partial(self._changeMe, row, col))
                # item.textChanged.connect(partial(self._changeMe, item))
                self.editItem(item)  # enter the editing mode


class StructureTable(GuiTableStructure):
    """
    Class to present a StructureTable and a StructureData pulldown list, wrapped in a Widget
    """
    className = 'StructureTable'
    objectClass = 'StructureEnsemble'
    attributeName = 'structureEnsembles'

    OBJECT = 'object'
    TABLE = 'table'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, structureEnsemble=None, **kwds):
        # Derive application, project, and current from mainWindow
        self._mainWindow = mainWindow
        if mainWindow:
            self._application = mainWindow.application
            self._project = mainWindow.application.project
            self._current = mainWindow.application.current
        else:
            self._application = None
            self._project = None
            self._current = None

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        self.thisObj = None
        self.thisDataSet = None

        StructureTable._project = self._project

        # create the column objects
        self.structureColumns = [
            ('#', lambda row: StructureTable._stLamInt(row, 'Index'), 'Index', None, None),
            ('modelNumber', lambda row: StructureTable._stLamInt(row, 'modelNumber'), 'modelNumber', None, None),
            ('chainCode', lambda row: StructureTable._stLamStr(row, 'chainCode'), 'chainCode', None, None),
            ('sequenceId', lambda row: StructureTable._stLamInt(row, 'sequenceId'), 'sequenceId', None, None),
            ('insertionCode', lambda row: StructureTable._stLamStr(row, 'insertionCode'), 'insertionCode',
             None, None),
            ('residueName', lambda row: StructureTable._stLamStr(row, 'residueName'), 'residueName', None, None),
            ('atomName', lambda row: StructureTable._stLamStr(row, 'atomName'), 'atomName', None, None),
            ('altLocationCode', lambda row: StructureTable._stLamStr(row, 'altLocationCode'),
             'altLocationCode', None, None),
            ('element', lambda row: StructureTable._stLamStr(row, 'element'), 'element', None, None),
            ('x', lambda row: StructureTable._stLamFloat(row, 'x'), 'x', None, '%0.3f'),
            ('y', lambda row: StructureTable._stLamFloat(row, 'y'), 'y', None, '%0.3f'),
            ('z', lambda row: StructureTable._stLamFloat(row, 'z'), 'z', None, '%0.3f'),
            ('occupancy', lambda row: StructureTable._stLamFloat(row, 'occupancy'), 'occupancy', None, None),
            ('bFactor', lambda row: StructureTable._stLamFloat(row, 'bFactor'), 'bFactor', None, None),
            ('nmrChainCode', lambda row: StructureTable._stLamStr(row, 'nmrChainCode'), 'nmrChainCode',
             None, None),
            ('nmrSequenceCode', lambda row: StructureTable._stLamStr(row, 'nmrSequenceCode'),
             'nmrSequenceCode', None, None),
            ('nmrResidueName', lambda row: StructureTable._stLamStr(row, 'nmrResidueName'),
             'nmrResidueName', None, None),
            ('nmrAtomName', lambda row: StructureTable._stLamStr(row, 'nmrAtomName'), 'nmrAtomName', None, None),
            ('Comment', lambda row: StructureTable._getCommentText(row), 'Notes',
             lambda row, value: StructureTable._setComment(row, 'comment', value), None)
            ]  # [Column(colName, func, tipText, editValue, columnFormat)

        self.STcolumns = ColumnClass(self.structureColumns)

        # create the table; objects are added later via the displayTableForStructure method
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self.stWidget = KlassPulldown(parent=self._widget,
                                      mainWindow=self._mainWindow, default=None,  # first Structure in project (if present),
                                      grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                      showSelectName=True,
                                      sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                      callback=self._selectionPulldownCallback)
        self.stButtons = RadioButtons(self._widget, texts=['Ensemble', 'average'],
                                      selectedInd=1,
                                      callback=self._selectionButtonCallback,
                                      direction='h',
                                      tipTexts=None,
                                      grid=(1, 2), gridSpan=(1, 3))
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 5), gridSpan=(1, 1))
        self._widget.getLayout().setColumnStretch(5, 2)

        self._widgetScrollArea.setFixedHeight(35)

        # self._columnNames = [header.headerText for header in self.STcolumns]
        self._hiddenColumns = ['altLocationCode', 'element', 'occupancy']
        self.dataFrameObject = None

        super().__init__(parent=parent,
                         mainWindow=self._mainWindow,
                         dataFrameObject=None,  # class collating table and objects and headings,
                         setLayout=True,
                         autoResize=True, multiSelect=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         grid=(3, 0), gridSpan=(1, 6)
                         )
        self.moduleParent = moduleParent

        self._ensembleNotifier = None
        self._setNotifiers()

        if len(self.stButtons.radioButtons) > 0:
            self.stButtons.radioButtons[1].setEnabled(False)

        if structureEnsemble is not None:
            self._selectStructureEnsemble(structureEnsemble)

        # data = np.array([
        #   (1, 1.6, 'x'),
        #   (3, 5.4, 'y'),
        #   (8, 12.5, 'z'),
        #   (443, 1e-12, 'w'),
        # ], dtype=[('Column 1', int), ('Column 2', float), ('Column 3', object)])
        #
        # # self.setData(data)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, StructureEnsemble, self.stWidget)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

    def _selectStructureEnsemble(self, structureEnsemble=None):
        """
        Manually select a StructureEnsemble from the pullDown
        """
        if structureEnsemble is None:
            # getLogger().warning('select: No StructureEnsemble selected')
            # raise ValueError('select: No StructureEnsemble selected')
            self.stWidget.selectFirstItem()
        else:
            if not isinstance(structureEnsemble, StructureEnsemble):
                getLogger().warning('select: Object is not of type StructureEnsemble')
                raise TypeError('select: Object is not of type StructureEnsemble')
            else:
                for widgetObj in self.stWidget.textList:
                    if structureEnsemble.pid == widgetObj:
                        self.thisObj = structureEnsemble
                        self.thisDataSet = None
                        if len(self.stButtons.radioButtons) > 0:
                            self.stButtons.radioButtons[1].setEnabled(False)
                        # find the matching dataset if exists

                        self.stWidget.select(self.thisObj.pid)

    def displayTableForStructure(self, structureEnsemble):
        """
        Display the table for all StructureEnsembles
        """
        self.stWidget.select(structureEnsemble.pid)
        self._update(structureEnsemble)

    def displayTableForDataSetStructure(self, structureEnsemble):
        """
        Display the table for all StructureDataSet
        """

        # self.stWidget.select(structureEnsemble.pid)
        #
        # if self.thisDataSet:
        #   for dt in self.thisDataSet.data:
        #     if dt.name is 'Derived':
        #       try:
        #         self.params = dt.parameters
        #         thisFunc = self.params['backboneSelector']
        #         thisSubset = self.thisObj.data.extract(thisFunc)
        #         self._updateDataSet(thisSubset)
        #       except:
        #         pass

        # from ccpn.util.StructureData import averageStructure        # ejb - from TJ
        # try:
        #   self._updateDataSet(averageStructure(structureEnsemble.data))
        # except:
        #   info = showWarning(self.thisObj.pid+' contains no average', '')
        #   getLogger().warning(self.thisObj.pid+' contains no average', '')
        #   self.stButtons.setIndex(0)

        # self.stWidget.select(structureEnsemble.pid)

        # ejb - doesn't work, can't store in a StructureData
        if self.thisDataSet is not None:
            self._updateDataSet(self.thisDataSet)

    def _getAttachedDataSet(self, thisObj):
        """
        Get the StructureData object attached to this StructureEnsemble
        """
        if len(self.stButtons.radioButtons) > 0:
            self.stButtons.radioButtons[1].setEnabled(False)
        try:
            Found = False
            dd = dt = None
            self.thisDataSet = None
            if self._project.structureData:
                for dd in self._project.structureData:
                    if dd.title == thisObj.name:
                        for dt in dd.data:
                            if dt.name == 'Derived':
                                Found = True

            # if not Found:
            #   dd = self._project.newDataSet(thisObj.longPid)  # title - should be ensemble name/title/longPid
            #   dt = dd.newData('Derived')
            # self.thisDataSet = dd

            if Found is True:
                if 'average' not in dt.parameters:
                    self.thisDataSet = None
                else:
                    self.thisDataSet = dt.parameters['average']

                    # set the new columns
                    AVheadings = list(self.thisDataSet)
                    self.AVcolumns = ColumnClass([col for col in self.structureColumns if col[0] in AVheadings or col[0] == '#'])

                    if len(self.stButtons.radioButtons) > 0:
                        self.stButtons.radioButtons[1].setEnabled(True)
            else:
                self.thisDataSet = None
        except:
            self.thisDataSet = None

            # from ccpn.util.StructureData import averageStructure
            # dt.parameters['average'] = averageStructure(item.data)
            # dt.setParameter(name='average', value=averageStructure(item.data))
            # dt.attachedObject = averageStructure(item.data)
            # ejb - does't work, can't store in a StructureData

            # for dd in self._project.structureData:
            #
            #   if dd.title == thisObj.longPid:
            #
            #     self.thisDataSet = dd
            #     for dt in self.thisDataSet.data:
            #       if dt.name is 'derivedConformers':
            #         self.params = dt.parameters
            #         # thisFunc = self.params['backboneSelector']
            #
            #         if 'average' not in self.params:
            #           from ccpn.util.StructureData import averageStructure
            #           self.params['average'] = averageStructure(item.data)
            #
            #         return self.params['average']

        # if item:
        #   thisObj = self._project.getByPid(item)
        #   if self._project.structureData:
        #     for dd in self._project.structureData:
        #       if dd.title == thisObj.longPid:
        #
        #         self.thisDataSet = dd
        #         for dt in self.thisDataSet.data:
        #           if dt.name is 'derivedConformers':
        #             self.params = dt.parameters
        #             # thisFunc = self.params['backboneSelector']
        #
        #             if 'average' not in self.params():
        #               from ccpn.util.StructureData import averageStructure
        #               self.params['average'] = averageStructure(item.data)
        #
        #             return self.params['average']
        # else:
        #   return None

    def _update(self, structureEnsemble):
        """
        Update the table from StructureEnsemble
        """
        self._dataFrameObject = self.getDataFrameFromRows(table=self,
                                                          dataFrame=structureEnsemble.data,
                                                          colDefs=self.STcolumns,
                                                          )

        # new populate from Pandas
        self._project.blankNotification()
        self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
        self._project.unblankNotification()

    def _updateDataSet(self, structureData):
        """
        Update the table from EnsembleData
        """
        # tuples = structureData.as_namedtuples()
        # self.setColumns(self.STcolumns)
        # self.setObjects(tuples)
        # self.show()

        self._dataFrameObject = self.getDataFrameFromRows(table=self,
                                                          dataFrame=structureData,
                                                          colDefs=self.AVcolumns,
                                                          )

        # new populate from Pandas
        self._project.blankNotification()
        self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
        self._project.unblankNotification()

    def _selectionCallback(self, data):  #structureData, row, col):
        """
        Notifier Callback for selecting a row in the table
        """
        obj = data[CallBack.OBJECT]

        # self._current.structureData = obj
        # StructureTable._currentCallback = {'object':self.thisObj, 'table':self}

    def _actionCallback(self, data):  # atomRecordTuple, row, column):
        """
        Notifier DoubleClick action on item in table
        """
        objs = data[CallBack.OBJECT]
        if objs is None or objs.empty:
            return
        if isinstance(objs, (tuple, list)):
            obj = objs[0]
        else:
            obj = objs

        # getLogger().debug('StructureTable>>>', atomRecordTuple, row, column)
        getLogger().debug('StructureTable>>>', obj)

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting Structure from the pull down menu
        """
        self.stButtons.setIndex(0)
        self.thisObj = self._project.getByPid(item)
        getLogger().debug('>selectionPulldownCallback>', item, type(item), self.thisObj)
        if self.thisObj is not None:
            self._getAttachedDataSet(self.thisObj)  # check for a matching dataset, DS.title=SE.label
            self.displayTableForStructure(self.thisObj)
        else:
            self.clear()

    def _selectionButtonCallback(self):
        """
        Notifier Callback for selecting Structure Ensemble or average
        """
        item = self.stButtons.get()
        getLogger().debug('>selectionPulldownCallback>', item, type(item), self.thisObj)
        if self.thisObj is not None:
            if item == 'Ensemble':
                self.displayTableForStructure(self.thisObj)
            elif item == 'average':
                self.displayTableForDataSetStructure(self.thisObj)
        else:
            self.clear()

    def _updateCallback(self, data):
        """
        Notifier Callback for updating the table
        """
        thisEnsembleList = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the object
        getLogger().debug('>updateCallback> %s %s %s %s' % (data['notifier'], self.thisObj, data['trigger'], data['object']))
        if self.thisObj in thisEnsembleList:
            item = self.stButtons.get()
            getLogger().debug('>selectionPulldownCallback> %s %s %s' % (item, type(item), self.thisObj))
            if item == 'Ensemble':
                self.displayTableForStructure(self.thisObj)
            elif item == 'average':
                self.displayTableForDataSetStructure(self.thisObj)
        else:
            # self.clearTable()
            self.clear()

    def navigateToStructureInDisplay(structureEnsemble, display, stripIndex=0, widths=None,
                                     showSequentialStructures=False, markPositions=True):
        """
        Notifier Callback for selecting Object from item in the table
        """
        getLogger().debug('display=%r, nmrResidue=%r, showSequentialResidues=%s, markPositions=%s' %
                          (display.id, structureEnsemble.id, showSequentialStructures, markPositions)
                          )
        return None

    @staticmethod
    def _getCommentText(structure):
        """
        CCPN-INTERNAL: Get a comment from ObjectTable
        """
        try:
            if structure.comment == '' or not structure.comment:
                return ' '
            else:
                return structure.comment
        except:
            return ' '  # .comment may not exist

    @staticmethod
    def _setComment(structure, column, value):
        """
        CCPN-INTERNAL: Insert a comment into ObjectTable
        """
        # structure.comment = value
        # ejb - need to use PandasMethod, value is an AtomRecordTuple
        StructureTable._project.blankNotification()

        index = structure.Index
        setKw = {column: value}
        thisObj = StructureTable._currentCallback[StructureTable.OBJECT]
        thisData = thisObj.data
        thisTable = StructureTable._currentCallback[StructureTable.TABLE]
        # thisTable.setUpdatesEnabled(False)
        # thisTable.blockSignals(True)

        thisDataItem = thisData.extract(index=[index])  # strange, needs to be a list
        try:
            thisData[column]  # check if the column exists
        except KeyError:
            numRows = len(thisData.index)
            thisData[column] = '' * numRows
            thisDataItem[column] = '' * numRows  # need to set in both dataframes
        except:
            showWarning(thisObj.pid + ' update table error', '')
            return

        finally:
            thisData.setValues(thisDataItem, **setKw)  # ejb - update the object
            # StructureTable._currentCallback[StructureTable.TABLE]._updateDataSet(thisObj)

            tuples = thisData.as_namedtuples()  # populate the table
            thisTable.setObjects(tuples)

        StructureTable._project.unblankNotification()

        #FIXME:ED need to spawn a change event on the other tables - forced with changing comment
        # thisTable._clearNotifiers()
        #
        # tempLabel = thisObj.comment
        # thisObj.comment = 'SetNameForChangeEvent'
        #
        # thisTable._setNotifiers()
        # thisObj.comment = tempLabel

        # thisTable.blockSignals(False)
        # thisTable.setUpdatesEnabled(True)

    @staticmethod
    def _stLamInt(row, name):
        """
        CCPN-INTERNAL: Insert an int into ObjectTable
        """
        try:
            return int(getattr(row, name))
        except:
            return None

    @staticmethod
    def _stLamFloat(row, name):
        """
        CCPN-INTERNAL: Insert a float into ObjectTable
        """
        try:
            return float(getattr(row, name))
        except:
            return None

    @staticmethod
    def _stLamStr(row, name):
        """
        CCPN-INTERNAL: Insert a str into ObjectTable
        """
        try:
            return str(getattr(row, name))
        except:
            return None

    def initialiseButtons(self, index):
        """
        Set index of radioButton
        """
        self.stButtons.setIndex(index)

    def _setNotifiers(self):
        """
        Set a Notifier to call when an object is created/deleted/renamed/changed
        rename calls on name
        change calls on any other attribute
        """
        # self._clearNotifiers()
        self._ensembleNotifier = Notifier(self._project,
                                          [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE],
                                          StructureEnsemble.__name__,
                                          self._updateCallback,
                                          onceOnly=True)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#=========================================================================================
# _NewStructureTableWidget
#=========================================================================================

class _NewStructureTableWidget(_CoreTableWidgetABC):
    """Class to present a StructureTable
    """
    className = '_NewStructureTableWidget'
    attributeName = KlassTable._pluralLinkName

    defaultHidden = ['Pid', 'altLocationCode', 'element', 'occupancy']
    _internalColumns = ['isDeleted', '_object']  # columns that are always hidden

    # define self._columns here
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = KlassTable
    rowClass = None
    cellClass = None
    tableName = tableClass.className
    rowName = None
    cellClassNames = None
    selectCurrent = False
    callBackClass = None
    search = False

    # set the queue handling parameters
    _maximumQueueLength = 25

    #=========================================================================================
    # Properties
    #=========================================================================================

    #=========================================================================================
    # Widget callbacks
    #=========================================================================================

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _getTableColumns(self, structureEnsemble=None):
        """Add default columns plus the ones according to structureEnsemble
         format of column = ( Header Name, value, tipText, editOption)
         editOption allows the user to modify the value content by doubleclick
         """
        # create the column objects
        columnDefs = [
            ('#', lambda row: self._stLamInt(row, 'Index'), 'Index', None, None),
            ('modelNumber', lambda row: self._stLamInt(row, 'modelNumber'), 'modelNumber', None, None),
            ('chainCode', lambda row: self._stLamStr(row, 'chainCode'), 'chainCode', None, None),
            ('sequenceId', lambda row: self._stLamInt(row, 'sequenceId'), 'sequenceId', None, None),
            ('insertionCode', lambda row: self._stLamStr(row, 'insertionCode'), 'insertionCode',
             None, None),
            ('residueName', lambda row: self._stLamStr(row, 'residueName'), 'residueName', None, None),
            ('atomName', lambda row: self._stLamStr(row, 'atomName'), 'atomName', None, None),
            ('altLocationCode', lambda row: self._stLamStr(row, 'altLocationCode'),
             'altLocationCode', None, None),
            ('element', lambda row: self._stLamStr(row, 'element'), 'element', None, None),
            ('x', lambda row: self._stLamFloat(row, 'x'), 'x', None, '%0.3f'),
            ('y', lambda row: self._stLamFloat(row, 'y'), 'y', None, '%0.3f'),
            ('z', lambda row: self._stLamFloat(row, 'z'), 'z', None, '%0.3f'),
            ('occupancy', lambda row: self._stLamFloat(row, 'occupancy'), 'occupancy', None, None),
            ('bFactor', lambda row: self._stLamFloat(row, 'bFactor'), 'bFactor', None, None),
            ('nmrChainCode', lambda row: self._stLamStr(row, 'nmrChainCode'), 'nmrChainCode',
             None, None),
            ('nmrSequenceCode', lambda row: self._stLamStr(row, 'nmrSequenceCode'),
             'nmrSequenceCode', None, None),
            ('nmrResidueName', lambda row: self._stLamStr(row, 'nmrResidueName'),
             'nmrResidueName', None, None),
            ('nmrAtomName', lambda row: self._stLamStr(row, 'nmrAtomName'), 'nmrAtomName', None, None),
            ('Comment', lambda row: self._getCommentText(row), 'Notes',
             lambda row, value: self._setComment(row, 'comment', value), None)
            ]  # [Column(colName, func, tipText, editValue, columnFormat)

        return ColumnClass(columnDefs)

    def buildTableDataFrame(self):
        """Return a Pandas dataFrame from an internal list of objects.
        The columns are based on the 'func' functions in the columnDefinitions.
        :return pandas dataFrame
        """
        if self._table:
            self._columnDefs = self._getTableColumns(self._table)

            # TODO:ED - columns are wrong
            #   build similar to chemicalShiftTable

            df = pd.DataFrame(self._table.data, columns=self._columnDefs.headings)

        else:
            self._columnDefs = self._getTableColumns()
            df = pd.DataFrame(columns=self._columnDefs.headings)

        # # use the object as the index, object always exists even if isDeleted
        # df.set_index(df[self.OBJECTCOLUMN], inplace=True, )

        _dfObject = DataFrameObject(dataFrame=df,
                                    columnDefs=self._columnDefs or [],
                                    table=self)

        return _dfObject

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _update(self):
        """Display the objects on the table for the selected list.
        """
        if self._table:
            self.populateTable()
        else:
            self.populateEmptyTable()

    #=========================================================================================
    # object properties
    #=========================================================================================

    @staticmethod
    def _stLamInt(row, name):
        """
        CCPN-INTERNAL: Insert an int into ObjectTable
        """
        try:
            return int(getattr(row, name))
        except:
            return None

    @staticmethod
    def _stLamFloat(row, name):
        """
        CCPN-INTERNAL: Insert a float into ObjectTable
        """
        try:
            return float(getattr(row, name))
        except:
            return None

    @staticmethod
    def _stLamStr(row, name):
        """
        CCPN-INTERNAL: Insert a str into ObjectTable
        """
        try:
            return str(getattr(row, name))
        except:
            return None


#=========================================================================================
# StructureTableFrame
#=========================================================================================

class StructureTableFrame(_CoreTableFrameABC):
    """Frame containing the pulldown and the table widget
    """
    _TableKlass = _NewStructureTableWidget
    _PulldownKlass = KlassPulldown

    def __init__(self, parent, mainWindow=None, moduleParent=None,
                 structureEnsemble=None, selectFirstItem=False, **kwds):
        super().__init__(parent, mainWindow=mainWindow, moduleParent=moduleParent,
                         obj=structureEnsemble, selectFirstItem=selectFirstItem, **kwds)

        # create widget for selection of ensemble-average
        self.stButtons = RadioButtons(self, texts=['Ensemble', 'average'],
                                      selectedInd=1,
                                      callback=self._selectionButtonCallback,
                                      direction='h',
                                      tipTexts=None,
                                      )

        self.addWidgetToTop(self.stButtons, 2)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def _tableCurrent(self):
        """Return the list of source objects, e.g., _table.peaks/_table.nmrResidues
        """
        return self.current.structureEnsemble

    @_tableCurrent.setter
    def _tableCurrent(self, value):
        self.current.structureEnsemble = value

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    def _selectionButtonCallback(self):
        """Pass units change to the table
        """
        item = self.stButtons.get()

        # signal parent to update the units of both tables
        self._tableWidget.update()


#=========================================================================================
# main
#=========================================================================================

def main():
    """Show the IntegralTableModule
    """
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = StructureTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
