"""
This file contains NmrResidueTableModule and NmrResidueTable classes

The NmrResidueModule allows for selection of displays, after which double-clicking a row 
navigates the displays to the relevant positions and marks the NmrAtoms of the selected 
NmrResidue.

Geerten 1-7/12/2016; 11/04/2017
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
__dateModified__ = "$dateModified: 2022-05-19 11:39:58 +0100 (Thu, May 19, 2022) $"
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

from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core._OldChemicalShift import _OldChemicalShift
from ccpn.core.lib import CcpnSorting
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT, DataFrameObject
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showYesNo
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.lib.StripLib import navigateToNmrResidueInDisplay, navigateToNmrAtomsInStrip
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableViewProjectSpecific, _updateSimplePandasTable
from ccpn.util.Logging import getLogger


logger = getLogger()
ALL = '<all>'

LINKTOPULLDOWNCLASS = 'linkToPulldownClass'


#=========================================================================================
# NmrResidueTableModule
#=========================================================================================

class NmrResidueTableModule(CcpnModule):
    """This class implements the module by wrapping a NmrResidueTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'left'

    includeDisplaySettings = False
    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False
    activePulldownClass = NmrChain

    className = 'NmrResidueTableModule'
    _allowRename = True

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='NmrResidue Table',
                 nmrChain=None, selectFirstItem=False):
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

        # set the widgets and callbacks
        self._setWidgets(self.settingsWidget, self.mainWidget, nmrChain, selectFirstItem)
        self._setCallbacks()

    def _setWidgets(self, settingsWidget, mainWidget, nmrChain, selectFirstItem):
        """Set up the widgets for the module
        """
        # add to settings widget
        self.nmrResidueTableSettings = StripPlot(parent=settingsWidget, mainWindow=self.mainWindow,
                                                 includeDisplaySettings=self.includeDisplaySettings,
                                                 includePeakLists=self.includePeakLists,
                                                 includeNmrChains=self.includeNmrChains,
                                                 includeSpectrumTable=self.includeSpectrumTable,
                                                 activePulldownClass=self.activePulldownClass,
                                                 activePulldownInitialState=False,
                                                 grid=(0, 0))

        # add the frame containing the pulldown and table
        self._mainFrame = NmrResidueTableFrame(parent=mainWidget,
                                               mainWindow=self.mainWindow,
                                               moduleParent=self,
                                               nmrChain=nmrChain, selectFirstItem=selectFirstItem,
                                               grid=(0, 0))

        # link the table to the mainWidget - needs refactoring
        self._mainFrame._tableWidget._autoClearMarksCheckBox = self.nmrResidueTableSettings.autoClearMarksWidget.checkBox
        self._mainFrame.nmrResidueTableSettings = self.nmrResidueTableSettings

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
                                                   checkBox=getattr(self.nmrResidueTableSettings, LINKTOPULLDOWNCLASS, None))

        # set the dropped callback through mainWidget
        self.mainWidget._dropEventCallback = self._mainFrame._processDroppedItems

    def selectTable(self, table):
        """Select the object in the table
        """
        self._mainFrame.selectTable(table)


#=========================================================================================
# NmrResidueTableWidget
#=========================================================================================

class NmrResidueTableWidget(GuiTable):
    """Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
    """
    className = 'NmrResidueTable'
    attributeName = 'nmrChains'

    OBJECT = 'object'
    TABLE = 'table'

    tableClass = NmrChain
    tableName = tableClass.className

    @staticmethod
    def _nmrIndex(nmrRes):
        """CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            from ccpnc.clibrary import Clibrary

            _getNmrIndex = Clibrary.getNmrResidueIndex

            return _getNmrIndex(nmrRes)
            # return nmrRes.nmrChain.nmrResidues.index(nmrRes)                # ED: THIS IS VERY SLOW
        except Exception as es:
            return None

    @staticmethod
    def _nmrLamInt(row, name):
        """CCPN-INTERNAL: Insert an int into ObjectTable
        """
        try:
            return int(getattr(row, name))
        except:
            return None

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
                 checkBoxCallback=None, _pulldownKwds=None, nmrChain=None, multiSelect=False,
                 **kwds):
        """Initialise the widgets for the module. kwds passed to the scrollArea widget
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

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        self._table = None
        if actionCallback is None:
            actionCallback = self.defaultActionCallback

        NmrResidueTableWidget.project = self.project

        # create the column objects
        self.NMRcolumns = ColumnClass([
            ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None, None),
            ('Index', lambda nmrResidue: NmrResidueTableWidget._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            # ('Index', lambda nmrResidue: NmrResidueTable._nmrLamInt(nmrResidue, 'Index'), 'Index of NmrResidue in the NmrChain', None, None),

            # ('Index',      lambda nmrResidue: nmrResidue.nmrChain.nmrResidues.index(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            # ('NmrChain',   lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain id', None, None),
            ('Pid', lambda nmrResidue: nmrResidue.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda nmrResidue: nmrResidue, 'Object', None, None),
            ('NmrChain', lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain containing the nmrResidue', None, None),  # just add the nmrChain for clarity
            ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None, None),
            ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None, None),
            ('NmrAtoms', lambda nmrResidue: NmrResidueTableWidget._getNmrAtomNames(nmrResidue), 'NmrAtoms in NmrResidue', None, None),
            ('Peak count', lambda nmrResidue: '%3d ' % NmrResidueTableWidget._getNmrResiduePeakCount(nmrResidue),
             'Number of peaks assigned to NmrResidue', None, None),
            ('Comment', lambda nmr: NmrResidueTableWidget._getCommentText(nmr), 'Notes',
             lambda nmr, value: NmrResidueTableWidget._setComment(nmr, value), None)
            ])

        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True, multiSelect=multiSelect,
                         actionCallback=actionCallback,
                         selectionCallback=selectionCallback,
                         checkBoxCallback=checkBoxCallback,
                         _pulldownKwds=_pulldownKwds,
                         grid=(3, 0), gridSpan=(1, 6),
                         enableDelete=True
                         )
        self.moduleParent = moduleParent

        self.setTableNotifiers(tableClass=NmrChain,
                               className=self.attributeName,
                               tableSelection='_table',
                               rowClass=NmrResidue,
                               cellClassNames=[(NmrAtom, 'nmrResidue'), (_OldChemicalShift, 'nmrAtom')],
                               tableName='nmrChain', rowName='nmrResidue',
                               # changeFunc=self.displayTableForNmrChain, # might be renamed|deleted
                               # updateFunc=self._update,
                               # pullDownWidget=self.moduleParent._modulePulldown,
                               callBackClass=NmrResidue,
                               selectCurrentCallBack=self._selectOnTableCurrentNmrResiduesNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    @property
    def table(self):
        """Return the current table
        """
        return self._table

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pass

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)
        # widget.setFixedSize(widget.sizeHint())
        # self._widget.setFixedSize(self._widget.sizeHint())

    def addWidgetToPos(self, widget, row=0, col=2, rowSpan=1, colSpan=1, overrideMinimum=False, alignment=None):
        """Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2 and not overrideMinimum:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, row, col, rowSpan, colSpan)

        # if alignment is not None:
        #     self._widget.getLayout().setAlignment(widget, alignment)
        # widget.setFixedSize(widget.sizeHint())
        # self._widget.setFixedSize(self._widget.sizeHint())

    def _setWidgetHeight(self, height):
        self._widgetScrollArea.setFixedHeight(height)

    def defaultActionCallback(self, data):
        """default Action Callback if not defined in the parent Module
        If current strip contains the double-clicked nmrResidue will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.StripLib import _getCurrentZoomRatio

        nmrResidue = data[Notifier.OBJECT]

        if self.current.strip is not None:
            self.application.ui.mainWindow.clearMarks()
            strip = self.current.strip
            newWidths = _getCurrentZoomRatio(strip.viewRange())
            navigateToNmrResidueInDisplay(nmrResidue, strip.spectrumDisplay, stripIndex=0,
                                          widths=None)
            # widths=['default'] * len(strip.axisCodes))

        else:
            logger.warning('Impossible to navigate to position. Set a current strip first')

    #=========================================================================================
    # Updates
    #=========================================================================================

    def _update(self):
        """Update the table with NmrResidues of nmrChain
        """
        if self._table:
            self.populateTable(rowObjects=self._table.nmrResidues,
                               columnDefs=self.NMRcolumns,
                               selectedObjects=self.current.nmrResidues
                               )
        else:
            self.clear()

    #=========================================================================================
    # Widget callbacks
    #=========================================================================================

    def _selectionCallback(self, data):
        """Notifier Callback for selecting a row in the table
        """
        selected = data[Notifier.OBJECT]

        if selected:
            if self.multiSelect:  #In this case selected is a List!!
                if isinstance(selected, list):
                    self.current.nmrResidues = selected
            else:
                self.current.nmrResidue = selected[0]
        else:
            # TODO:ED this should never be called, and where is it?
            self.current.clearNmrResidues()

        NmrResidueTableModule.currentCallback = {'object': self._table, 'table': self}

    def _selectOnTableCurrentNmrResiduesNotifierCallback(self, data):
        """callback from a notifier to select the current NmrResidue
        :param data:
        """
        currentNmrResidues = data['value']
        self._selectOnTableCurrentNmrResidues(currentNmrResidues)

    def _selectOnTableCurrentNmrResidues(self, currentNmrResidues):
        """highlight  current NmrResidues on the opened table
        """
        self.highlightObjects(currentNmrResidues)

    @staticmethod
    def _getNmrAtomNames(nmrResidue):
        """Returns a sorted list of NmrAtom names
        """
        return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms if not atom.isDeleted]),
                                key=CcpnSorting.stringSortKey))

    @staticmethod
    def _getNmrResiduePeakCount(nmrResidue):
        """Returns peak list count
        """
        l1 = [peak for atom in nmrResidue.nmrAtoms if not atom.isDeleted for peak in atom.assignedPeaks if not peak.isDeleted]
        return len(set(l1))

    # def _getPullDownSelection(self):
    #     return self.moduleParent._modulePulldown.getText()
    #
    # def _selectPullDown(self, value):
    #     self.moduleParent._modulePulldown.select(value)

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to insert new merge items to top of context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        _actions = self.tableMenu.actions()

        if _actions:
            _topMenuItem = _actions[0]
            _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            self._mergeMenuAction = self.tableMenu.addAction('Merge NmrResidues', self._mergeNmrResidues)
            self._editMenuAction = self.tableMenu.addAction('Edit NmrResidue', self._editNmrResidue)
            self._markMenuAction = self.tableMenu.addAction('Mark Position', self._markNmrResidue)
            # move new actions to the top of the list
            self.tableMenu.insertAction(_topSeparator, self._markMenuAction)
            self.tableMenu.insertAction(self._markMenuAction, self._mergeMenuAction)
            self.tableMenu.insertAction(self._mergeMenuAction, self._editMenuAction)

    def _raiseTableContextMenu(self, pos):
        """Create a new menu and popup at cursor position
        Add merge item
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if data:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)

            selection = selection or []
            _check = (currentNmrResidue and (1 < len(selection) < 5) and currentNmrResidue in selection)
            _option = ' into {}'.format(currentNmrResidue.id if currentNmrResidue else '') if _check else ''
            self._mergeMenuAction.setText('Merge NmrResidues {}'.format(_option))
            self._mergeMenuAction.setEnabled(_check)

            self._editMenuAction.setText('Edit NmrResidue {}'.format(currentNmrResidue.id if currentNmrResidue else ''))
            self._editMenuAction.setEnabled(True if currentNmrResidue else False)

        else:
            # disabled but visible lets user know that menu items exist
            self._mergeMenuAction.setText('Merge NmrResidues')
            self._mergeMenuAction.setEnabled(False)
            self._editMenuAction.setText('Edit NmrResidue')
            self._editMenuAction.setEnabled(False)

        super()._raiseTableContextMenu(pos)

    def _mergeNmrResidues(self):
        """Merge the nmrResidues in the selection into the nmrResidue that has been right-clicked
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if data and selection:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)
            matching = [ch for ch in selection if ch and ch != currentNmrResidue]

            if len(matching):
                yesNo = showYesNo('Merge NmrResidues', "Do you want to merge\n\n"
                                                       "{}   into   {}".format('\n'.join([ss.id for ss in matching]),
                                                                               currentNmrResidue.id))
                if yesNo:
                    currentNmrResidue.mergeNmrResidues(matching)

    def _editNmrResidue(self):
        """Show the edit nmrResidue popup for the clicked nmrResidue
        """
        data = self.getRightMouseItem()
        if data:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)

            if currentNmrResidue:
                from ccpn.ui.gui.popups.NmrResiduePopup import NmrResidueEditPopup

                popup = NmrResidueEditPopup(parent=self.mainWindow, mainWindow=self.mainWindow, obj=currentNmrResidue)
                popup.exec_()

    def _markNmrResidue(self):
        """Mark the position of the nmrResidue
        """
        data = self.getRightMouseItem()
        if data:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)

            if currentNmrResidue:
                from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import markNmrAtoms

                # optionally clear the marks
                # if self.moduleParent.nmrResidueTableSettings.autoClearMarksWidget.checkBox.isChecked():
                if self._autoClearMarksCheckBox.isChecked():
                    self.mainWindow.clearMarks()

                markNmrAtoms(self.mainWindow, currentNmrResidue.nmrAtoms)


KD = 'Kd'
Deltas = 'Ddelta'


#=========================================================================================
# _NewNmrResidueTableWidget
#=========================================================================================

class _NewNmrResidueTableWidget(_SimplePandasTableViewProjectSpecific):
    """Class to present a nmrResidue Table
    """
    className = 'NmrResidueTable'
    attributeName = 'nmrChains'

    defaultHidden = ['Pid', 'NmrChain']
    _internalColumns = ['isDeleted', '_object']  # columns that are always hidden
    _INDEX = 'Index'

    # define self._columns here
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = NmrChain
    rowClass = NmrResidue
    cellClass = None
    tableName = tableClass.className
    rowName = tableClass.className
    cellClassNames = {NmrAtom: 'nmrResidue'}  # , _OldChemicalShift: 'nmrAtom'}
    selectCurrent = True
    callBackClass = NmrResidue
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

        self.chemicalShiftsMappingModule = None

    #=========================================================================================
    # Action callbacks
    #=========================================================================================

    def actionCallback(self, data):
        """If current strip contains the double-clicked peak will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.StripLib import _getCurrentZoomRatio

        nmrResidue = data[Notifier.OBJECT]
        if isinstance(nmrResidue, list) and nmrResidue:
            nmrResidue = nmrResidue[0]  # select the first in the list
        if not nmrResidue:
            return

        if self.current.strip is not None:
            self.application.ui.mainWindow.clearMarks()
            strip = self.current.strip
            newWidths = _getCurrentZoomRatio(strip.viewRange())
            navigateToNmrResidueInDisplay(nmrResidue, strip.spectrumDisplay, stripIndex=0,
                                          widths=None)
            # widths=['default'] * len(strip.axisCodes))

        else:
            logger.warning('Impossible to navigate to position. Set a current strip first')

    def selectionCallback(self, data):
        """set as current the selected core objects on the table
        """
        itms = data[CallBack.OBJECT]
        if itms is None:
            self.current.nmrResidues = ()
        else:
            self.current.nmrResidues = itms

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

            for col, obj in enumerate(self._table.nmrResidues):
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
        # classItem is usually a type such as PeakList, MultipletList
        # with an attribute such as peaks/peaks
        return [cellItem._oldNmrResidue] if cellItem.isDeleted else [cellItem.nmrResidue], Notifier.CHANGE

    def _updateCellCallback(self, data):
        """Notifier callback for updating the table
        :param data:
        """
        # print(f'>>> _updateCellCallback')

        with self._blockTableSignals('_updateCellCallback'):
            cellData = data[Notifier.OBJECT]

            rowObjs = []
            _triggerType = Notifier.CHANGE

            if (attr := self.cellClassNames.get(type(cellData))):
                rowObjs, _triggerType = self.getCellToRows(cellData, attr)

            # update the correct row by calling row handler
            for rowObj in rowObjs:
                rowData = {Notifier.OBJECT : rowObj,
                           Notifier.TRIGGER: _triggerType or data[Notifier.TRIGGER],
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

            # check that the object belongs to the list that is being displayed

            trigger = data[Notifier.TRIGGER]
            try:
                df = self._df
                objSet = set(self._table.nmrResidues)  # objects in the list
                tableSet = set(df[self.OBJECTCOLUMN])  # objects currently in the table

                if trigger == Notifier.DELETE:
                    # uniqueIds in the visible table
                    if obj in (tableSet - objSet):
                        # remove from the table
                        self.model()._deleteRow(obj)
                        self._reindexTable()

                elif trigger == Notifier.CREATE:
                    # uniqueIds in the visible table
                    if obj in (objSet - tableSet):
                        # insert into the table
                        newRow = self._newRowFromUniqueId(df, obj, None)
                        self.model()._insertRow(obj, newRow)
                        self._reindexTable()

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
                        self._reindexTable()

                    elif obj in (tableSet - objSet):
                        # remove renamed object OUT of the table
                        self.model()._deleteRow(obj)
                        self._reindexTable()

            except Exception as es:
                getLogger().debug2(f'Error updating row in table {es}')

    def _reindexTable(self):
        """Reset the index column for the table
        Not required for most core-object tables, but nmrResidues and Residues have an order
        """
        # must be done after the insert/delete as the object-column will have changed
        df = self._df
        objs = tuple(self._table.nmrResidues)  # objects in the list
        tableObjs = tuple(df[self.OBJECTCOLUMN])  # objects currently in the table

        # table will automatically replace this on the update
        df[self._INDEX] = [objs.index(obj) if obj in objs else 0 for obj in tableObjs]

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
            _topMenuItem = _actions[0]
            _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            self._mergeMenuAction = self.tableMenu.addAction('Merge NmrResidues', self._mergeNmrResidues)
            self._editMenuAction = self.tableMenu.addAction('Edit NmrResidue', self._editNmrResidue)
            self._markMenuAction = self.tableMenu.addAction('Mark Position', self._markNmrResidue)
            # move new actions to the top of the list
            self.tableMenu.insertAction(_topSeparator, self._markMenuAction)
            self.tableMenu.insertAction(self._markMenuAction, self._mergeMenuAction)
            self.tableMenu.insertAction(self._mergeMenuAction, self._editMenuAction)

    def _raiseTableContextMenu(self, pos):
        """Raise the right-mouse menu
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if data is not None and not data.empty:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)

            selection = selection or []
            _check = (currentNmrResidue and (1 < len(selection) < 5) and currentNmrResidue in selection)
            _option = ' into {}'.format(currentNmrResidue.id if currentNmrResidue else '') if _check else ''
            self._mergeMenuAction.setText('Merge NmrResidues {}'.format(_option))
            self._mergeMenuAction.setEnabled(_check)

            self._editMenuAction.setText('Edit NmrResidue {}'.format(currentNmrResidue.id if currentNmrResidue else ''))
            self._editMenuAction.setEnabled(True if currentNmrResidue else False)

        else:
            # disabled but visible lets user know that menu items exist
            self._mergeMenuAction.setText('Merge NmrResidues')
            self._mergeMenuAction.setEnabled(False)
            self._editMenuAction.setText('Edit NmrResidue')
            self._editMenuAction.setEnabled(False)

        # raise the menu
        super()._raiseTableContextMenu(pos)

    def _mergeNmrResidues(self):
        """Merge the nmrResidues in the selection into the nmrResidue that has been right-clicked
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if data is not None and not data.empty and selection:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)
            matching = [ch for ch in selection if ch and ch != currentNmrResidue]

            if len(matching):
                yesNo = showYesNo('Merge NmrResidues', "Do you want to merge\n\n"
                                                       "{}   into   {}".format('\n'.join([ss.id for ss in matching]),
                                                                               currentNmrResidue.id))
                if yesNo:
                    currentNmrResidue.mergeNmrResidues(matching)

    def _editNmrResidue(self):
        """Show the edit nmrResidue popup for the clicked nmrResidue
        """
        data = self.getRightMouseItem()
        if data is not None and not data.empty:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)

            if currentNmrResidue:
                from ccpn.ui.gui.popups.NmrResiduePopup import NmrResidueEditPopup

                popup = NmrResidueEditPopup(parent=self.mainWindow, mainWindow=self.mainWindow, obj=currentNmrResidue)
                popup.exec_()

    def _markNmrResidue(self):
        """Mark the position of the nmrResidue
        """
        data = self.getRightMouseItem()
        if data is not None and not data.empty:
            currentNmrResidue = data.get(DATAFRAME_OBJECT)

            if currentNmrResidue:
                from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import markNmrAtoms

                # optionally clear the marks
                # if self.moduleParent.nmrResidueTableSettings.autoClearMarksWidget.checkBox.isChecked():
                if self._autoClearMarksCheckBox.isChecked():
                    self.mainWindow.clearMarks()

                markNmrAtoms(self.mainWindow, currentNmrResidue.nmrAtoms)

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _getTableColumns(self, objs):
        """format of column = ( Header Name, value, tipText, editOption)
        editOption allows the user to modify the value content by doubleclick
        """
        cols = ColumnClass([
            ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None, None),
            ('Index', lambda nmrResidue: self._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            # ('Index', lambda nmrResidue: NmrResidueTable._nmrLamInt(nmrResidue, 'Index'), 'Index of NmrResidue in the NmrChain', None, None),

            # ('Index',      lambda nmrResidue: nmrResidue.nmrChain.nmrResidues.index(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            # ('NmrChain',   lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain id', None, None),
            ('Pid', lambda nmrResidue: nmrResidue.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda nmrResidue: nmrResidue, 'Object', None, None),
            ('NmrChain', lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain containing the nmrResidue', None, None),  # just add the nmrChain for clarity
            ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None, None),
            ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None, None),
            ('NmrAtoms', lambda nmrResidue: self._getNmrAtomNames(nmrResidue), 'NmrAtoms in NmrResidue', None, None),
            ('Peak count', lambda nmrResidue: '%3d ' % self._getNmrResiduePeakCount(nmrResidue),
             'Number of peaks assigned to NmrResidue', None, None),
            ('Comment', lambda nmr: self._getCommentText(nmr), 'Notes',
             lambda nmr, value: self._setComment(nmr, value), None)
            ])

        return cols

    #=========================================================================================
    # Updates
    #=========================================================================================

    def displayTableForNmrChain(self, nmrChain):
        """
        Display the table for all NmrResidue's of nmrChain
        """
        # NOTE:ED - should be an emitter
        self.moduleParent._modulePulldown.select(nmrChain.pid)
        self._update()

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets
        """
        self._update()

    def _update(self, useSelected=True, nmrResidues=None, nmrChain=None):
        """Display the nmrResidues on the table for the selected nmrChain.
        Obviously, If the nmrResidue has not been previously deleted and flagged isDeleted
        """
        # self._selectedNmrChain = self.project.getByPid(nmrChain) if isinstance(nmrChain, str) else nmrChain

        if useSelected:
            if self._table:
                self.populateTable(rowObjects=self._table.nmrResidues,
                                   selectedObjects=self.current.nmrResidues)
            else:
                self.populateEmptyTable()

        else:
            if nmrResidues:  # and nmrChain:
                self.populateTable(rowObjects=nmrResidues,
                                   selectedObjects=self.current.nmrResidues)
            else:
                self.populateEmptyTable()

    def queueFull(self):
        """Method that is called when the queue is deemed to be too big.
        Apply overall operation instead of all individual notifiers.
        """
        self._update()

    #=========================================================================================
    # object properties
    #=========================================================================================

    @staticmethod
    def _nmrIndex(nmrRes):
        """CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            from ccpnc.clibrary import Clibrary

            _getNmrIndex = Clibrary.getNmrResidueIndex

            return _getNmrIndex(nmrRes)
            # return nmrRes.nmrChain.nmrResidues.index(nmrRes)                # ED: THIS IS VERY SLOW
        except Exception as es:
            return None

    @staticmethod
    def _nmrLamInt(row, name):
        """CCPN-INTERNAL: Insert an int into ObjectTable
        """
        try:
            return int(getattr(row, name))
        except:
            return None

    @staticmethod
    def _getNmrAtomNames(nmrResidue):
        """Returns a sorted list of NmrAtom names
        """
        return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms if not atom._flaggedForDelete]),
                                key=CcpnSorting.stringSortKey))

    @staticmethod
    def _getNmrResiduePeakCount(nmrResidue):
        """Returns peak list count
        """
        l1 = [peak for atom in nmrResidue.nmrAtoms if not atom._flaggedForDelete for peak in atom.assignedPeaks if not peak._flaggedForDelete]
        return len(set(l1))


#=========================================================================================
# NmrResidueTableFrame
#=========================================================================================

class NmrResidueTableFrame(Frame):
    """Frame containing the pulldown and the table widget
    """
    _TableWidget = _NewNmrResidueTableWidget  # NmrResidueTableWidget
    _activePulldownClass = None
    _activeCheckbox = None

    def __init__(self, parent, mainWindow=None, moduleParent=None,
                 nmrChain=None, selectFirstItem=False, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None
        self._table = None
        self.moduleParent = moduleParent

        # add the widgets
        self._setWidgets(mainWidget=self)

        if nmrChain is not None:
            self.selectTable(nmrChain)
        elif selectFirstItem:
            self._modulePulldown.selectFirstItem()

    def _setWidgets(self, mainWidget=None):
        """Set up the widgets for the module
        """
        # add to main widget area
        _topWidget = mainWidget

        # main widgets at the top
        row = 0
        Spacer(_topWidget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self._modulePulldown = NmrChainPulldown(parent=_topWidget,
                                                mainWindow=self.mainWindow,
                                                grid=(row, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                showSelectName=True,
                                                sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                callback=self._selectionPulldownCallback)

        # fixed height for the pulldown
        self._modulePulldown.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        self.spacer = Spacer(_topWidget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 1), gridSpan=(1, 1))

        # main window
        _hidden = ['Pid', 'NmrChain']

        row += 1
        self._tableWidget = self._TableWidget(parent=_topWidget,
                                              mainWindow=self.mainWindow,
                                              # moduleParent=self.moduleParent,
                                              # setLayout=True,
                                              actionCallback=self.navigateToNmrResidueCallBack,
                                              # multiSelect=True,
                                              grid=(row, 0), gridSpan=(1, 6),
                                              # hiddenColumns=_hidden,
                                              )
        _topWidget.getLayout().setColumnStretch(5, 2)

        # set policy to fill the frame - still required?
        # self._tableWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

    def setActivePulldownClass(self, coreClass, checkBox):
        """Set up the callback properties for changing the current object from the pulldown
        """
        self._activePulldownClass = coreClass
        self._activeCheckbox = checkBox

    @property
    def table(self):
        """Return the current table
        """
        return self._table

    @property
    def guiTable(self):
        """Return the current table widget
        """
        return self._tableWidget

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

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, NmrChain, self._modulePulldown)

    def _handleDroppedItems(self, pids, objType, pulldown):
        """handle dropping pids onto the table
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle. Eg. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        from ccpn.ui.gui.lib.MenuActions import _openItemObject

        objs = [self.project.getByPid(pid) for pid in pids]

        selectableObjects = [obj for obj in objs if isinstance(obj, objType)]
        others = [obj for obj in objs if not isinstance(obj, objType)]
        if len(selectableObjects) > 0:
            _openItemObject(self.mainWindow, selectableObjects[1:])
            pulldown.select(selectableObjects[0].pid)

        else:
            from ccpn.ui.gui.widgets.MessageDialog import showYesNo

            othersClassNames = list(set([obj.className for obj in others if hasattr(obj, 'className')]))
            if len(othersClassNames) > 0:
                if len(othersClassNames) == 1:
                    title, msg = 'Dropped wrong item.', 'Do you want to open the %s in a new module?' % ''.join(othersClassNames)
                else:
                    title, msg = 'Dropped wrong items.', 'Do you want to open items in new modules?'
                openNew = showYesNo(title, msg)
                if openNew:
                    _openItemObject(self.mainWindow, others)

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting nmrChain from the pull down menu
        """
        self._table = self._modulePulldown.getSelectedObject()
        self._tableWidget._table = self._table

        # self._tableWidget._selectionPulldownCallback(self._table)
        self._tableWidget._update()

        # if self._table is not None:
        #     self._tableWidget.populateTable(rowObjects=self._table.nmrResidues,
        #                                     columnDefs=self._tableWidget._getTableColumns(self._table),
        #                                     selectedObjects=self.current.nmrResidues)
        # else:
        #     self._tableWidget.populateEmptyTable()

        # update the current object from the pulldown
        if self._activePulldownClass and self._activeCheckbox and self._table != self.current.nmrChain and self._activeCheckbox.isChecked():
            self.current.nmrChain = self._table

    def _selectCurrentPulldownClass(self, data):
        """Respond to change in current activePulldownClass
        """
        if self._activePulldownClass and self._activeCheckbox and self._activeCheckbox.isChecked():
            self._tableWidget._table = self._table = self.current.nmrChain
            self._tableWidget._update()

            if self._table:
                self._modulePulldown.select(self._table.pid, blockSignals=True)
            else:
                self._modulePulldown.setIndex(0, blockSignals=True)

    def navigateToNmrResidueCallBack(self, data):
        """Navigate in selected displays to nmrResidue; skip if none defined
        """
        from ccpn.core.lib.CallBack import CallBack

        # handle a single nmrResidue - should always contain an object
        objs = data[CallBack.OBJECT]
        if not objs or not all(objs):
            return
        if isinstance(objs, (tuple, list)):
            nmrResidue = objs[0]
        else:
            nmrResidue = objs

        logger.debug('nmrResidue=%s' % str(nmrResidue.id if nmrResidue else None))
        displays = []
        if self.nmrResidueTableSettings.displaysWidget:
            displays = self.nmrResidueTableSettings.displaysWidget.getDisplays()
        else:
            if self.current.strip:
                displays = [self.current.strip.spectrumDisplay]
        if len(displays) == 0 and self.nmrResidueTableSettings.displaysWidget:
            logger.warning('Undefined display module(s); select in settings first')
            showWarning('startAssignment', 'Undefined display module(s);\nselect in settings first')
            return

        from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

        with undoBlockWithoutSideBar():
            # optionally clear the marks
            if self.nmrResidueTableSettings.autoClearMarksWidget.checkBox.isChecked():
                self.application.ui.mainWindow.clearMarks()

            newWidths = []

            # follow the previous/next nmrResidues to navigate to the correct position
            offset = nmrResidue.relativeOffset
            nmrResidue = nmrResidue.mainNmrResidue
            if offset is not None:
                if offset < 0:
                    for _next in range(-offset):
                        _adjacent = nmrResidue.previousNmrResidue
                        if not (_adjacent and _adjacent.mainNmrResidue):
                            break
                        nmrResidue = _adjacent.mainNmrResidue

                elif offset > 0:
                    for _next in range(offset):
                        _adjacent = nmrResidue.nextNmrResidue
                        if not (_adjacent and _adjacent.mainNmrResidue):
                            break
                        nmrResidue = _adjacent.mainNmrResidue

            for specDisplay in displays:
                if self.current.strip in specDisplay.strips:

                    # just navigate to this strip
                    navigateToNmrAtomsInStrip(self.current.strip,
                                              nmrResidue.nmrAtoms,
                                              widths=newWidths,
                                              markPositions=self.nmrResidueTableSettings.markPositionsWidget.checkBox.isChecked(),
                                              setNmrResidueLabel=True)

                else:
                    #navigate to the specDisplay (and remove excess strips)
                    if len(specDisplay.strips) > 0:
                        newWidths = []
                        navigateToNmrResidueInDisplay(nmrResidue, specDisplay, stripIndex=0,
                                                      widths=newWidths,  #['full'] * len(display.strips[0].axisCodes),
                                                      showSequentialResidues=(len(specDisplay.axisCodes) > 2) and
                                                                             self.nmrResidueTableSettings.sequentialStripsWidget.checkBox.isChecked(),
                                                      markPositions=self.nmrResidueTableSettings.markPositionsWidget.checkBox.isChecked()
                                                      )

                # open the other headers to match
                for strip in specDisplay.strips:
                    if strip != self.current.strip and not strip.header.headerVisible:
                        strip.header.reset()
                        strip.header.headerVisible = True


#=========================================================================================
# _CSMNmrResidueTable
#=========================================================================================

class _CSMNmrResidueTableWidget(NmrResidueTableWidget):
    """Custom nmrResidue Table with extra columns used in the ChemicalShiftsMapping Module
    """

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
                 checkBoxCallback=None, nmrChain=None, **kwds):

        NmrResidueTableWidget.__init__(self, parent=parent, mainWindow=mainWindow,
                                       moduleParent=moduleParent,
                                       actionCallback=actionCallback,
                                       selectionCallback=selectionCallback,
                                       checkBoxCallback=checkBoxCallback,
                                       nmrChain=nmrChain,
                                       # multiSelect=True,
                                       **kwds)

        self.NMRcolumns = ColumnClass([
            ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None, None),
            ('Pid', lambda nmrResidue: nmrResidue.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda nmrResidue: nmrResidue, 'Object', None, None),
            ('Index', lambda nmrResidue: NmrResidueTableWidget._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None, None),
            ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None, None),
            ('Selected', lambda nmrResidue: _CSMNmrResidueTableWidget._getSelectedNmrAtomNames(nmrResidue), 'NmrAtoms selected in NmrResidue', None, None),
            ('Spectra', lambda nmrResidue: _CSMNmrResidueTableWidget._getNmrResidueSpectraCount(nmrResidue)
             , 'Number of spectra selected for calculating the deltas', None, None),
            (Deltas, lambda nmrResidue: nmrResidue._delta, '', None, None),
            (KD, lambda nmrResidue: nmrResidue._estimatedKd, '', None, None),
            ('Include', lambda nmrResidue: nmrResidue._includeInDeltaShift, 'Include this residue in the Mapping calculation', lambda nmr, value: _CSMNmrResidueTableWidget._setChecked(nmr, value), None),
            # ('Flag', lambda nmrResidue: nmrResidue._flag,  '',  None, None),
            ('Comment', lambda nmr: NmrResidueTableWidget._getCommentText(nmr), 'Notes', lambda nmr, value: NmrResidueTableWidget._setComment(nmr, value), None)
            ])  #[Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)

        self._widget.setFixedHeight(45)
        self.chemicalShiftsMappingModule = None

    @staticmethod
    def _setChecked(obj, value):
        """CCPN-INTERNAL: Insert a comment into GuiTable
        """
        obj._includeInDeltaShift = value
        obj._finaliseAction('change')

    @staticmethod
    def _getNmrResidueSpectraCount(nmrResidue):
        """CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            return nmrResidue.spectraCount
        except:
            return None

    @staticmethod
    def _getSelectedNmrAtomNames(nmrResidue):
        """CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            return ', '.join(nmrResidue.selectedNmrAtomNames)
        except:
            return None

    def _selectPullDown(self, value):
        """Used for automatic restoring of widgets
        """
        self.moduleParent._modulePulldown.select(value)
        try:
            if self.chemicalShiftsMappingModule is not None:
                self.chemicalShiftsMappingModule._updateModule()
        except Exception as e:
            getLogger().warning('Impossible update chemicalShiftsMappingModule from restoring %s' % e)


#=========================================================================================
# _NewCSMNmrResidueTable
#=========================================================================================

class _NewCSMNmrResidueTableWidget(_NewNmrResidueTableWidget):
    """Custom nmrResidue Table with extra columns used in the ChemicalShiftsMapping Module
    """

    def setActionCallback(self, actionCallback=None):
        # enable callbacks
        self.actionCallback = actionCallback

        for act in [self._doubleClickCallback]:
            try:
                self.doubleClicked.disconnect(act)
            except Exception:
                getLogger().debug2('nothing to disconnect')

        if self.actionCallback:
            self.doubleClicked.connect(self._doubleClickCallback)

    def setCheckBoxCallback(self, checkBoxCallback):
        # enable callback on the checkboxes
        self._checkBoxCallback = checkBoxCallback

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _getTableColumns(self, objs):
        """format of column = ( Header Name, value, tipText, editOption)
        editOption allows the user to modify the value content by doubleclick
        """
        cols = ColumnClass([
            ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None, None),
            ('Pid', lambda nmrResidue: nmrResidue.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda nmrResidue: nmrResidue, 'Object', None, None),
            ('Index', lambda nmrResidue: self._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None, None),
            ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None, None),
            ('Selected', lambda nmrResidue: self._getSelectedNmrAtomNames(nmrResidue), 'NmrAtoms selected in NmrResidue', None, None),
            ('Spectra', lambda nmrResidue: self._getNmrResidueSpectraCount(nmrResidue)
             , 'Number of spectra selected for calculating the deltas', None, None),
            (Deltas, lambda nmrResidue: nmrResidue._delta, '', None, None),
            (KD, lambda nmrResidue: nmrResidue._estimatedKd, '', None, None),
            ('Include', lambda nmrResidue: nmrResidue._includeInDeltaShift, 'Include this residue in the Mapping calculation', lambda nmr, value: self._setChecked(nmr, value), None),
            # ('Flag', lambda nmrResidue: nmrResidue._flag,  '',  None, None),
            ('Comment', lambda nmr: self._getCommentText(nmr), 'Notes', lambda nmr, value: self._setComment(nmr, value), None)
            ])  #[Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)

        return cols

    #=========================================================================================
    # object properties
    #=========================================================================================

    @staticmethod
    def _setChecked(obj, value):
        """CCPN-INTERNAL: Insert a comment into GuiTable
        """
        obj._includeInDeltaShift = value
        obj._finaliseAction('change')

    @staticmethod
    def _getNmrResidueSpectraCount(nmrResidue):
        """CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            return nmrResidue.spectraCount
        except:
            return None

    @staticmethod
    def _getSelectedNmrAtomNames(nmrResidue):
        """CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            return ', '.join(nmrResidue.selectedNmrAtomNames)
        except:
            return None

    def _selectPullDown(self, value):
        """Used for automatic restoring of widgets
        """
        self.moduleParent._modulePulldown.select(value)
        try:
            if self.chemicalShiftsMappingModule is not None:
                self.chemicalShiftsMappingModule._updateModule()
        except Exception as e:
            getLogger().warning('Impossible update chemicalShiftsMappingModule from restoring %s' % e)


#=========================================================================================
# NmrResidueTableFrame
#=========================================================================================

class _CSMNmrResidueTableFrame(NmrResidueTableFrame):
    """Frame containing the pulldown and the table widget
    """
    _TableWidget = _NewCSMNmrResidueTableWidget


#=========================================================================================
# main
#=========================================================================================

def main():
    """Show the NmrResidueTable module
    """
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = NmrResidueTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
