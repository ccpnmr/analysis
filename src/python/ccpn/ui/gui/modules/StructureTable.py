"""
This file contains StructureTableModule and StructureTable classes
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-18 13:10:48 +0000 (Thu, March 18, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from ccpn.core.lib.CallBack import CallBack
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import StructureEnsemblePulldown
from ccpn.ui.gui.widgets.Column import ColumnClass
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot


ALL = '<all>'


class StructureTableModule(CcpnModule):
    """
    This class implements the module by wrapping a StructureTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'StructureTableModule'

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='Structure Table',
                 structureEnsemble=None, selectFirstItem=False):
        """
        Initialise the Module widgets
        """
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

        # add test code here

        # settings
        self._STwidget = StripPlot(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                   includePeakLists=self.includePeakLists,
                                   includeNmrChains=self.includeNmrChains,
                                   includeSpectrumTable=self.includeSpectrumTable,
                                   grid=(0, 0))

        # main window
        self.structureTable = StructureTable(parent=self.mainWidget,
                                             mainWindow=self.mainWindow,
                                             moduleParent=self,
                                             setLayout=True,
                                             grid=(0, 0))

        if structureEnsemble is not None:
            self.selectStructureEnsemble(structureEnsemble)
        elif selectFirstItem:
            self.structureTable.stWidget.selectFirstItem()

    def selectStructureEnsemble(self, structureEnsemble=None):
        """
        Manually select a StructureEnsemble from the pullDown
        """
        self.structureTable._selectStructureEnsemble(structureEnsemble)

    def _getDisplays(self) -> list:
        """
        Return list of displays to navigate - if needed
        """
        displays = []
        # check for valid displays
        gids = self.displaysWidget.getTexts()
        if len(gids) == 0: return displays
        if ALL in gids:
            displays = self.mainWindow.spectrumDisplays
        else:
            displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        return displays

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.structureTable._close()
        super()._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class GuiTableStructure(GuiTable):
    """
    GuiTable specific to tables that only contain a single pid for the pandas dataframe
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
        self.stWidget = StructureEnsemblePulldown(parent=self._widget,
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

        # ejb - doesn't work, can't store in a DataSet
        if self.thisDataSet is not None:
            self._updateDataSet(self.thisDataSet)

    def _getAttachedDataSet(self, thisObj):
        """
        Get the DataSet object attached to this StructureEnsemble
        """
        if len(self.stButtons.radioButtons) > 0:
            self.stButtons.radioButtons[1].setEnabled(False)
        try:
            Found = False
            dd = dt = None
            self.thisDataSet = None
            if self._project.dataSets:
                for dd in self._project.dataSets:
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
            # ejb - does't work, can't store in a DataSet

            # for dd in self._project.dataSets:
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
        #   if self._project.dataSets:
        #     for dd in self._project.dataSets:
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
                                                          hiddenColumns=self._hiddenColumns)

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
                                                          hiddenColumns=self._hiddenColumns)

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
        if not objs:
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

    # def _clearNotifiers(self):
    #   """
    #   clean up the notifiers
    #   """
    #   if self._ensembleNotifier is not None:
    #     self._ensembleNotifier.unRegister()

    # def _close(self):
    #     """
    #     Cleanup the notifiers when the window is closed
    #     """
    #     self.clearTableNotifiers()

    # def resizeEvent(self, event):
    #   getLogger().info('table.resize '+str(self.resizeCount))
    #   self.resizeCount+=1
    #   return super(StructureTable, self).resizeEvent(event)
    #
    # def paintEvent(self, event):
    #   getLogger().info('table.paint '+str(self.paintCount))
    #   self.paintCount+=1
    #   return super(StructureTable, self).paintEvent(event)

    # #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # # add test structure Ensembles
    # try:
    #   StructureTableModule.defined
    # except:
    #   #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    #   self.ensemble = self.project.newStructureEnsemble()
    #   self.data = self.ensemble.data
    #
    #   self.testAtomName = ['CA', 'C', 'N', 'O', 'H',
    #      'CB', 'HB1', 'HB2', 'HB3',
    #      'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23',
    #      'CE', 'HE1', 'HE2', 'HE3',
    #      'CG', 'HG1', 'HG2', 'HG3',
    #      'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    #   self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + [
    #                                                                                                  'VAL'] * 8
    #   self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    #   self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #   self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #   self.comment = ['Test'] * 33
    #
    #   self.data['atomName'] = self.testAtomName
    #   self.data['residueName'] = self.testResidueName
    #   self.data['chainCode'] = self.testChainCode
    #   self.data['sequenceId'] = self.testSequenceId
    #   self.data['modelNumber'] = self.testModelNumber
    #   self.data['comment'] = self.comment
    #
    #   #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    #   self.ensemble = self.project.newStructureEnsemble()
    #   self.data = self.ensemble.data
    #
    #   self.testAtomName = ['CA', 'C', 'N', 'O', 'H',
    #      'CB', 'HB1', 'HB2', 'HB3',
    #      'CE', 'HE1', 'HE2', 'HE3',
    #      'CG', 'HG1', 'HG2', 'HG3',
    #      'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23',
    #      'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    #   self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + [
    #                                                                                                  'VAL'] * 8
    #   self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    #   self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #   self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #
    #   self.data['atomName'] = self.testAtomName
    #   self.data['residueName'] = self.testResidueName
    #   self.data['chainCode'] = self.testChainCode
    #   self.data['sequenceId'] = self.testSequenceId
    #   self.data['modelNumber'] = self.testModelNumber
    #   self.data['comment'] = self.comment
    #
    #   self.ensemble = self.project.newStructureEnsemble()
    #   self.ensemble.data = self.data.extract(index='1, 2, 6-7, 9')
    #
    #   # make a test dataset in here
    #
    #   self.dataSet = self.project.newDataSet(self.ensemble.longPid)    # title - should be ensemble name/title/longPid
    #
    #   self.dataItem = self.dataSet.newData('derivedConformers')
    #   self.dataSet.attachedObject = self.ensemble       # the newest object
    #   self.dataItem.setParameter(name='backboneSelector', value=self.ensemble.data.backboneSelector)
    #
    #   StructureTableModule.defined=True
    #   # should be a DataSet with the corresponding stuff in it
    #   #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # finally:
    #   pass

    # tuples = structureEnsemble.data.as_namedtuples()
    # self.setColumns(self.STcolumns)
    # self.setObjects(tuples)
    # self.show()

    # import inspect
    # attr = inspect.getmembers(StructureEnsemble, lambda a:not (inspect.isroutine(a)))
    # filteredAttr = [a for a in attr if
    #                 not (a[0].startswith('__') and a[0].endswith('__')) and not a[0].startswith(
    #                   '_')]
    # for i in filteredAttr:
    #   att, val = i
    #   try:
    #     setattr(structureEnsemble, att, val)
    #   except Exception as e:
    #     # print(e, att)
    #     del filteredAttr[att]       # remove the attribute
    #
    # data = np.array([
    #   (1, 1.6, 'x'),
    #   (3, 5.4, 'y'),
    #   (8, 12.5, 'z'),
    #   (443, 1e-12, 'w'),
    # ], dtype=[('Column 1', int), ('Column 2', float), ('Column 3', object)])

    # self.hide()
    # tuples = structureEnsemble.data.as_namedtuples()
    # headings = [head[0] for head in self.STcolumns]
    # data = []
    # for row in tuples:
    #   data.append(list(row))
    #
    # df = pd.DataFrame(data[0], columns=headings)

    # PandasData = np.dataFra([12,45,'help'], dtype=[('Index', int),
    #                                       ('modelNumber', int),
    #                                       ('chainCode', str)])

    # xdata = np.array({'x':10,'y':13.34}, dtype=[('x', np.uint8), ('y', np.float64)])
    # df = pd.DataFrame(xdata)

    # x = np.empty((10,), dtype=[('x', np.uint8), ('y', np.float64)])
    # df = pd.DataFrame(x)
    # t = df.dtypes

    # newArraydata = np.array( [(1, 1.6, 'x'),
    #       (3, 5.4, 'y'),
    #       (8, 12.5, 'z'),
    #       (443, 1e-12, 'w')],
    #                          dtype=[('Index', np.uint),
    #                                       ('modelNumber', np.float32),
    #                                       ('chainCode', np.str)])

    # temp = [(1, 1.6, 'x'),
    #         (3, 5.4, 'y'),
    #         (8, 12.5, 'z'),
    #         (443, 1e-12, 'w')]
    # newArraydata = np.array(temp, dtype=[('Index', int),
    #                                         ('modelNumber', float),
    #                                         ('chainCode', str)])

    # self._project.blankNotification()
    #
    # self.setData(structureEnsemble.data.values)
    # self.setHorizontalHeaderLabels([head[0] for head in NewStructureTable.columnHeadings])
    #
    # self._project.unblankNotification()
    # self.resizeColumnsToContents()
    # self.show()

    # add a comment field to the Pandas dataFrame?

    # dataFrameObject = self.getDataFrameFromRows(structureEnsemble.data, self.STcolumns)
