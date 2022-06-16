"""This file contains ChemicalShiftTable class

modified by Geerten 1-7/12/2016
tertiary version by Ejb 9/5/17
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
__dateModified__ = "$dateModified: 2022-06-16 12:26:54 +0100 (Thu, June 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore
from functools import partial
from types import SimpleNamespace
import pandas as pd

from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.core.ChemicalShiftList import CS_UNIQUEID, CS_ISDELETED, CS_PID, \
    CS_STATIC, CS_STATE, CS_ORPHAN, CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT, CS_ATOMNAME, \
    CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, \
    CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT, \
    CS_COMMENT, CS_OBJECT, \
    CS_TABLECOLUMNS, ChemicalShiftState
from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.util.Logging import getLogger
from ccpn.util.Common import makeIterableList
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChemicalShiftListPulldown
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.MessageDialog import showYesNo, showWarning
from ccpn.ui.gui.widgets.SettingsWidgets import ALL
from ccpn.ui.gui.widgets.Column import COLUMN_COLDEFS, COLUMN_SETEDITVALUE, COLUMN_FORMAT
from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableViewProjectSpecific, _updateSimplePandasTable


logger = getLogger()

LINKTOPULLDOWNCLASS = 'linkToPulldownClass'


#=========================================================================================
# ChemicalShiftTableModule
#=========================================================================================

class ChemicalShiftTableModule(CcpnModule):
    """This class implements the module by wrapping a NmrResidueTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    className = 'ChemicalShiftTableModule'
    _allowRename = True

    activePulldownClass = None  # e.g., can make the table respond to current peakList

    def __init__(self, mainWindow=None, name='Chemical Shift Table',
                 chemicalShiftList=None, selectFirstItem=False):
        """Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        self._table = None

        # add the widgets
        self._setWidgets()

        if chemicalShiftList is not None:
            self._selectTable(chemicalShiftList)
        elif selectFirstItem:
            self._modulePulldown.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _setWidgets(self):
        """Set up the widgets for the module
        """
        # Put all the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
        # backBoneAssignment modules
        if self.includeSettingsWidget:
            self._CSTwidget = Widget(self.settingsWidget, setLayout=True,
                                     grid=(0, 0), vAlign='top', hAlign='left')

            # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
            # underpinning the addNotifier call do not allow for it either
            colwidth = 140

            self.autoClearMarksWidget = CheckBoxCompoundWidget(
                    self._CSTwidget,
                    grid=(3, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                    fixedWidths=(colwidth, 30),
                    orientation='left',
                    labelText='Auto clear marks:',
                    checked=True
                    )

        _topWidget = self.mainWidget

        # main widgets at the top
        row = 0
        Spacer(_topWidget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(0, 0), gridSpan=(1, 1))
        row += 1

        self._modulePulldown = ChemicalShiftListPulldown(parent=_topWidget,
                                                         mainWindow=self.mainWindow, default=None,
                                                         grid=(row, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                         showSelectName=True,
                                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                         callback=self._selectionPulldownCallback,
                                                         )
        # fixed height
        self._modulePulldown.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        self.spacer = Spacer(_topWidget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 1), gridSpan=(1, 1))
        _topWidget.getLayout().setColumnStretch(1, 2)

        # main window
        _hidden = [CS_UNIQUEID, CS_ISDELETED, CS_FIGUREOFMERIT, CS_ALLPEAKS, CS_CHAINCODE,
                   CS_SEQUENCECODE, CS_STATE, CS_ORPHAN]

        row += 1
        self._tableWidget = _NewChemicalShiftTable(parent=_topWidget,
                                                   mainWindow=self.mainWindow,
                                                   moduleParent=self,
                                                   grid=(row, 0), gridSpan=(1, 6),
                                                   hiddenColumns=_hidden)

    def _maximise(self):
        """Maximise the attached table
        """
        self._selectionPulldownCallback(None)

    def _selectTable(self, chemicalShiftList=None):
        """Manually select a ChemicalShiftList from the pullDown
        """
        if chemicalShiftList is None:
            self._modulePulldown.selectFirstItem()
        else:
            if not isinstance(chemicalShiftList, ChemicalShiftList):
                logger.warning('select: Object is not of type ChemicalShiftList')
                raise TypeError('select: Object is not of type ChemicalShiftList')
            else:
                self._modulePulldown.select(chemicalShiftList.pid)

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self._modulePulldown.unRegister()
        self._tableWidget._close()
        super()._closeModule()

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting ChemicalShiftList from the pull down menu
        """
        self._table = self._modulePulldown.getSelectedObject()
        self._tableWidget._table = self._table

        if self._table is not None:
            self._tableWidget.populateTable(rowObjects=self._table.chemicalShifts,
                                            selectedObjects=self.current.chemicalShifts)
        else:
            self._tableWidget.populateEmptyTable()


#=========================================================================================
# ChemicalShiftTable
#=========================================================================================

class ChemicalShiftTable(GuiTable):
    """Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
    """

    className = 'ChemicalShiftListTable'
    attributeName = 'chemicalShiftLists'

    PRIMARYCOLUMN = CS_OBJECT  # column holding active objects (uniqueId/ChemicalShift for this table?)
    defaultHidden = [CS_UNIQUEID, CS_ISDELETED, CS_FIGUREOFMERIT, CS_ALLPEAKS, CS_CHAINCODE,
                     CS_SEQUENCECODE, CS_STATE, CS_ORPHAN]

    # define self._columns here
    columnHeaders = {CS_UNIQUEID           : 'Unique ID',
                     CS_ISDELETED          : 'isDeleted',  # should never be visible
                     CS_PID                : 'ChemicalShift',
                     CS_VALUE              : 'ChemicalShift Value (ppm)',
                     CS_VALUEERROR         : 'Value Error',
                     CS_FIGUREOFMERIT      : 'Figure of Merit',
                     CS_NMRATOM            : 'NmrAtom',
                     CS_CHAINCODE          : 'ChainCode',
                     CS_SEQUENCECODE       : 'SequenceCode',
                     CS_RESIDUETYPE        : 'ResidueType',
                     CS_ATOMNAME           : 'AtomName',
                     CS_STATE              : 'State',
                     CS_ORPHAN             : 'Orphaned',
                     CS_ALLPEAKS           : 'Assigned Peaks',
                     CS_SHIFTLISTPEAKSCOUNT: 'Peak Count',
                     CS_ALLPEAKSCOUNT      : 'Total Peak Count',
                     CS_COMMENT            : 'Comment',
                     CS_OBJECT             : '_object'
                     }

    tipTexts = ('Unique identifier for the chemicalShift',
                'isDeleted',  # should never be visible
                'ChemicalShift.pid',
                'ChemicalShift value in ppm',
                'Error in the chemicalShift value in ppm',
                'Figure of merit, between 0 and 1',
                'Pid of nmrAtom if attached, or None',
                'ChainCode of attached nmrAtom, or None',
                'SequenceCode of attached nmrAtom, or None',
                'ResidueType of attached nmrAtom, or None',
                'AtomName of attached nmrAtom, or None',
                'Active state of chemicalShift',
                'Orphaned state of chemicalShift',
                'List of assigned peaks associated with this chemicalShift',
                'Number of assigned peaks attached to a chemicalShift\nbelonging to spectra associated with parent chemicalShiftList',
                'Total number of assigned peaks attached to a chemicalShift\nbelonging to any spectra',
                'Optional comment for each chemicalShift',
                'None',
                )

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 chemicalShiftList=None, hiddenColumns=None, **kwds):
        """Initialise the widgets for the module.
        """
        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        self._table = None

        # self._widget = Widget(parent=parent, **kwds)
        # self._selectedChemicalShiftList = None

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        # initialise the currently attached dataFrame
        self._hiddenColumns = [self.columnHeaders[col] for col in hiddenColumns] if hiddenColumns else \
            [self.columnHeaders[col] for col in self.defaultHidden]
        self.dataFrameObject = None

        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        # create the table; objects are added later via the displayTableForNmrChain method
        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         setLayout=True,
                         multiSelect=True,
                         actionCallback=actionCallback,
                         selectionCallback=selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6),
                         )
        self.moduleParent = moduleParent

        self.setTableNotifiers(tableClass=ChemicalShiftList,
                               rowClass=ChemicalShift,
                               # cellClassNames=(NmrAtom, '_chemicalShifts'), # not required
                               tableName='chemicalShiftList', rowName='chemicalShift',
                               changeFunc=self._tableChangeNotifierCallback,
                               className=self.attributeName,
                               # updateFunc=self._update,
                               tableSelection='_table',
                               callBackClass=ChemicalShift,
                               selectCurrentCallBack=self._selectOnTableCurrentChemicalShiftNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, ChemicalShiftList, self.moduleParent._modulePulldown)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

    def _getValidChemicalShift4Callback(self, objs):
        if not objs or not all(objs):
            return
        if isinstance(objs, (tuple, list)):
            cShift = objs[-1]
        else:
            cShift = objs
        if not cShift:
            showWarning('Cannot perform action', 'No selected ChemicalShift')
            return

        return cShift

    def _tableChangeNotifierCallback(self, table):
        """Respond to table has been changed, e.g. renamed
        """
        if self._table is not None:
            self.populateTable(rowObjects=self._table.chemicalShifts,
                               selectedObjects=self.current.chemicalShifts)
        else:
            self.clearTable()

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    def _actionCallback(self, data):
        """Notifier DoubleClick action on item in table. Mark a chemicalShift based on attached nmrAtom
        """
        from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import markNmrAtoms

        cShift = self._getValidChemicalShift4Callback(data.get(CallBack.OBJECT, []))
        if len(self.mainWindow.marks):
            if self.moduleParent.autoClearMarksWidget.checkBox.isChecked():
                self.mainWindow.clearMarks()
        if cShift and cShift.nmrAtom:
            markNmrAtoms(self.mainWindow, [cShift.nmrAtom])

    def _selectionCallback(self, data):
        """Notifier Callback for selecting rows in the table
        """
        objs = data[CallBack.OBJECT]
        self.current.chemicalShifts = objs or []

        if objs:
            nmrResidues = tuple(set(cs.nmrAtom.nmrResidue for cs in objs if cs.nmrAtom))
        else:
            nmrResidues = []

        if nmrResidues:
            # set the associated nmrResidue and nmrAtoms
            nmrAtoms = tuple(set(nmrAtom for nmrRes in nmrResidues for nmrAtom in nmrRes.nmrAtoms))
            self.current.nmrAtoms = nmrAtoms
            self.current.nmrResidues = nmrResidues

        else:
            self.current.nmrAtoms = []
            self.current.nmrResidues = []

    #=========================================================================================
    # Menus
    #=========================================================================================

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to insert new merge items to top of context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        _actions = self.tableMenu.actions()
        if _actions:
            _topMenuItem = _actions[0]
            _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            self._navigateMenu = self.tableMenu.addMenu('Navigate to:')
            self._mergeMenuAction = self.tableMenu.addAction('Merge NmrAtoms', self._mergeNmrAtoms)
            self._editMenuAction = self.tableMenu.addAction('Edit NmrAtom', self._editNmrAtom)
            # move new actions to the top of the list
            self.tableMenu.insertAction(_topSeparator, self._mergeMenuAction)
            self.tableMenu.insertAction(self._mergeMenuAction, self._editMenuAction)

    def _addNavigationStripsToContextMenu(self):
        cShift = self._getValidChemicalShift4Callback(self.getSelectedObjects())
        self._navigateMenu.clear()
        if cShift and cShift.nmrAtom:
            name = cShift.nmrAtom.name
            if cShift.value is None:
                return
            value = round(cShift.value, 3)
            if self._navigateMenu is not None:
                self._navigateMenu.addItem(f'All ({name}:{value})',
                                           callback=partial(self._navigateToChemicalShift,
                                                            chemicalShift=cShift,
                                                            stripPid=ALL))
                self._navigateMenu.addSeparator()
                for spectrumDisplay in self.mainWindow.spectrumDisplays:
                    for strip in spectrumDisplay.strips:
                        self._navigateMenu.addItem(f'{strip.pid} ({name}:{value})',
                                                   callback=partial(self._navigateToChemicalShift,
                                                                    chemicalShift=cShift,
                                                                    stripPid=strip.pid))
                    self._navigateMenu.addSeparator()

    def _navigateToChemicalShift(self, chemicalShift, stripPid):
        # TODO add check if chemicalShift.spectra are in the strip.
        strips = []
        if stripPid == ALL:
            strips = self.mainWindow.strips
        else:
            strip = self.application.getByGid(stripPid)
            if strip:
                strips.append(strip)
        if strips:
            failedStripPids = []
            for strip in strips:

                try:
                    navigateToPositionInStrip(strip,
                                              positions=[chemicalShift.value],
                                              axisCodes=[chemicalShift.nmrAtom.name],
                                              widths=[])
                except:
                    failedStripPids.append(strip.pid)
            if len(failedStripPids) > 0:
                stripStr = 'strip' if len(failedStripPids) == 1 else 'strips'
                strips = ', '.join(failedStripPids)
                getLogger().warn(
                        f'Cannot navigate to position {round(chemicalShift.value, 3)} '
                        f'in {stripStr}: {strips} '
                        f'for nmrAtom {chemicalShift.nmrAtom.name}.')

    def _raiseTableContextMenu(self, pos):
        """Create a new menu and popup at cursor position
        Add merge item
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if data:
            cShift = data.get(DATAFRAME_OBJECT)
            currentNmrAtom = cShift.nmrAtom if cShift else None

            selection = [ch.nmrAtom for ch in selection or [] if ch.nmrAtom]
            _check = (currentNmrAtom and 1 < len(selection) and currentNmrAtom in selection) or False
            _option = 'into {}'.format(currentNmrAtom.id if currentNmrAtom else '') if _check else ''
            self._mergeMenuAction.setText('Merge NmrAtoms {}'.format(_option))
            self._mergeMenuAction.setEnabled(_check)

            self._editMenuAction.setText('Edit NmrAtom {}'.format(currentNmrAtom.id if currentNmrAtom else ''))
            self._editMenuAction.setEnabled(True if currentNmrAtom else False)
            self._addNavigationStripsToContextMenu()

        else:
            # disabled but visible lets user know that menu items exist
            self._mergeMenuAction.setText('Merge NmrAtoms')
            self._mergeMenuAction.setEnabled(False)
            self._editMenuAction.setText('Edit NmrAtom')
            self._editMenuAction.setEnabled(False)

        super()._raiseTableContextMenu(pos)

    def _mergeNmrAtoms(self):
        """Merge the nmrAtoms in the selection into the nmrAtom that has ben right-clicked
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if data and selection:
            cShift = data.get(DATAFRAME_OBJECT)
            currentNmrAtom = cShift.nmrAtom if cShift else None
            matching = [ch.nmrAtom for ch in selection if ch and ch.nmrAtom and ch.nmrAtom != currentNmrAtom and
                        ch.nmrAtom.isotopeCode == currentNmrAtom.isotopeCode]
            nonMatching = [ch.nmrAtom for ch in selection if ch and ch.nmrAtom and ch.nmrAtom != currentNmrAtom and
                           ch.nmrAtom.isotopeCode != currentNmrAtom.isotopeCode]

            if len(matching) < 1:
                showWarning('Merge NmrAtoms', 'No matching isotope codes')
            else:
                ss = 's' if (len(nonMatching) > 1) else ''
                nonMatchingList = '\n\n\n({} nmrAtom{} with non-matching isotopeCode{})'.format(len(nonMatching), ss, ss) if nonMatching else ''
                yesNo = showYesNo('Merge NmrAtoms', "Do you want to merge\n\n"
                                                    "{}   into   {}{}".format('\n'.join([ss.id for ss in matching]),
                                                                              currentNmrAtom.id,
                                                                              nonMatchingList))
                if yesNo:
                    currentNmrAtom.mergeNmrAtoms(matching)

    def _editNmrAtom(self):
        """Show the edit nmrAtom popup for the clicked nmrAtom
        """
        data = self.getRightMouseItem()
        if data:
            cShift = data.get(DATAFRAME_OBJECT)
            currentNmrAtom = cShift.nmrAtom if cShift else None

            if currentNmrAtom:
                from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomEditPopup

                popup = NmrAtomEditPopup(parent=self.mainWindow, mainWindow=self.mainWindow, obj=currentNmrAtom)
                popup.exec_()

    def _selectOnTableCurrentChemicalShiftNotifierCallback(self, data):
        """Callback from a notifier to highlight the chemical shifts
        :param data:
        """
        currentShifts = data['value']
        self._selectOnTableCurrentChemicalShifts(currentShifts)

    def _selectOnTableCurrentChemicalShifts(self, currentShifts):
        """Highlight the list of currentShifts on the table
        :param currentShifts:
        """
        self.highlightObjects(currentShifts)

    @staticmethod
    def _getShiftPeakCount(chemicalShift):
        """CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
        using ChemicalShiftList
        """
        chemicalShiftList = chemicalShift.chemicalShiftList
        peaks = chemicalShift.nmrAtom.assignedPeaks
        return (len(set(x for x in peaks
                        if x.peakList.chemicalShiftList is chemicalShiftList)))

    # def getCellToRows(self, cellItem, attribute):
    #     """Get the list of objects which cellItem maps to for this table
    #     To be subclassed as required
    #     """
    #     # classItem is usually a type such as PeakList, MultipletList
    #     # with an attribute such as peaks/peaks
    #
    #     # this is a step towards making guiTableABC and subclass for each table
    #     return getattr(cellItem, attribute, []), None

    @staticmethod
    def _stLamFloat(row, name):
        """CCPN-INTERNAL: used to display Table
        """
        try:
            return float(getattr(row, name))
        except:
            return None

    @staticmethod
    def _getNmrChain(chemicalShift):
        """CCPN-INTERNAL: get the nmrChain for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue.nmrChain.id
        except:
            return None

    @staticmethod
    def _getSequenceCode(chemicalShift):
        """CCPN-INTERNAL: get the sequenceCode for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue.sequenceCode
        except:
            return None

    @staticmethod
    def _getResidueType(chemicalShift):
        """CCPN-INTERNAL: get the residueType for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue.residueType
        except:
            return None

    @staticmethod
    def _getNmrResidue(chemicalShift):
        """CCPN-INTERNAL: get the nmrResidue for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue
        except:
            return None

    #=========================================================================================
    # Subclass GuiTable
    #=========================================================================================

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
            # raise es

        finally:
            self._highLightObjs(objs)
            self.project.unblankNotification()

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

                # NOTE:ED - fix this?
                # _shiftObjects = tuple(_getValueByHeader(row, CS_OBJECT) for row in self._dataFrameObject.objects)

                rows = [self._dataFrameObject.find(self, str(obj), column=CS_OBJECT, multiRow=True) for obj in uniqObjs]
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

    def _derivedFromObject(self, obj):
        """Get a tuple of derived values from obj
        Not very generic yet - column class now seems redundant
        """
        _peaks = obj.assignedPeaks or []
        allPeaks = str([pp.pid for pp in _peaks])
        try:
            shiftPeakCount = len([pp for pp in _peaks if pp.spectrum.chemicalShiftList == obj.chemicalShiftList])
        except Exception as es:
            shiftPeakCount = 0
        peakCount = len(_peaks) if _peaks else 0

        state = obj.state
        if state == ChemicalShiftState.ORPHAN:
            state = ChemicalShiftState.DYNAMIC
        state = state.description  # if state needed
        orphan = u'\u2713' if obj.orphan else ''  # unicode tick character

        return (state, orphan, allPeaks, shiftPeakCount, peakCount)

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
        # create the column objects
        _cols = [
            # (col, lambda row: _getValueByHeader(row, col), _tipTexts[ii], None, None)
            (self.columnHeaders[col], lambda row: _getValueByHeader(row, col), self.tipTexts[ii], None, None)
            for ii, col in enumerate(CS_TABLECOLUMNS)
            ]
        # NOTE:ED - hack to add the comment editor to the comment column, decimal places to value/valueError/figureOfMerit
        _temp = list(_cols[CS_TABLECOLUMNS.index(CS_COMMENT)])
        _temp[COLUMN_COLDEFS.index(COLUMN_SETEDITVALUE)] = lambda obj, value: self._setComment(obj, value)
        _cols[CS_TABLECOLUMNS.index(CS_COMMENT)] = tuple(_temp)
        for col in [CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT]:
            _temp = list(_cols[CS_TABLECOLUMNS.index(col)])
            _temp[COLUMN_COLDEFS.index(COLUMN_FORMAT)] = '%0.3f'
            _cols[CS_TABLECOLUMNS.index(col)] = tuple(_temp)

        # set the table _columns
        self._columns = ColumnClass(_cols)

        _csl = self._table

        if _csl._data is not None:
            # is of type _ChemicalShiftListFrame - should move functionality to there
            _table = _csl._data.copy()
            _table = _table[_table[CS_ISDELETED] == False]
            _table.drop(columns=[CS_STATIC], inplace=True)  # static not required

            _table.set_index(_table[CS_UNIQUEID], inplace=True, )  # drop=False)

            _table.insert(CS_TABLECOLUMNS.index(CS_PID), CS_PID, None)
            _table.insert(CS_TABLECOLUMNS.index(CS_STATE), CS_STATE, None)  # if state require
            _table.insert(CS_TABLECOLUMNS.index(CS_ORPHAN), CS_ORPHAN, None)  # if state require
            _table.insert(CS_TABLECOLUMNS.index(CS_ALLPEAKS), CS_ALLPEAKS, None)
            _table.insert(CS_TABLECOLUMNS.index(CS_SHIFTLISTPEAKSCOUNT), CS_SHIFTLISTPEAKSCOUNT, None)
            _table.insert(CS_TABLECOLUMNS.index(CS_ALLPEAKSCOUNT), CS_ALLPEAKSCOUNT, None)

            _objs = [_csl.getChemicalShift(uniqueId=unq) for unq in _table[CS_UNIQUEID]]
            if _objs:
                # append the actual objects as the last column - not sure whether this is required - check _highlightObjs
                _table[CS_OBJECT] = _objs
                _table[CS_PID] = [_shift.pid for _shift in _objs]

                _stats = [self._derivedFromObject(obj) for obj in _objs]
                # _table[[CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT]] = _stats
                _table[[CS_STATE, CS_ORPHAN, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT]] = _stats

                # replace the visible nans with '' for comment column and string 'None' elsewhere
                _table[CS_COMMENT].fillna('', inplace=True)
                _table.fillna('None', inplace=True)
        else:
            # _table = pd.DataFrame(columns=CS_TABLECOLUMNS)
            _table = pd.DataFrame(columns=[self.columnHeaders[val] for val in CS_TABLECOLUMNS])

        # set the table from the dataFrame
        _dataFrame = DataFrameObject(dataFrame=_table,
                                     columnDefs=self._columns or [],
                                     table=table,
                                     )
        # extract the row objects from the dataFrame
        _objects = [row for row in _table.itertuples()]
        _dataFrame._objects = _objects

        return _dataFrame

    def refreshTable(self):
        # subclass to refresh the groups
        self.setTableFromDataFrameObject(self._dataFrameObject)
        # self.updateTableExpanders()

    def setDataFromSearchWidget(self, dataFrame):
        """Set the data for the table from the search widget
        """
        self.setData(dataFrame.values)
        # self._updateGroups(dataFrame)
        # self.updateTableExpanders()

    def _newRowFromUniqueId(self, df, obj, uniqueId):
        # NOTE:ED - this needs to go elsewhere?
        #   need to define a row handler rather than a column handler
        _row = df.loc[uniqueId]
        # make the new row
        newRow = _row[:CS_ISDELETED].copy()
        _midRow = _row[CS_VALUE:CS_ATOMNAME]  # CS_STATIC
        _comment = _row[CS_COMMENT:]
        _pidCol = pd.Series(obj.pid, index=[CS_PID, ])
        _extraCols = pd.Series(self._derivedFromObject(obj), index=[CS_STATE, CS_ORPHAN, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT])  # if state required

        newRow = newRow.append([_pidCol, _midRow, _extraCols, _comment])

        # append the actual object to the end - not sure whether this is required - check _highlightObjs
        newRow[CS_OBJECT] = obj

        # replace the visible nans with '' for comment column and string 'None' elsewhere
        newRow[CS_COMMENT:CS_COMMENT].fillna('', inplace=True)
        newRow.fillna('None', inplace=True)

        return list(newRow)

    def _updateRowCallback(self, data):
        """
        Notifier callback for updating the table for change in nmrRows
        :param data:
        """

        with self._tableBlockSignals('_updateRowCallback'):
            obj = data[Notifier.OBJECT]
            uniqueId = obj.uniqueId

            # check that the object belongs to the list that is being displayed
            if not self._dataFrameObject or obj is None:
                return
            if obj.chemicalShiftList != self._table:
                return

            _update = False  # from original row update - need to check

            trigger = data[Notifier.TRIGGER]
            try:
                _df = self._table._data
                _df = _df[_df[CS_ISDELETED] == False]  # not deleted - should be the only visible ones

                # the column containing the uniqueId
                col = CS_TABLECOLUMNS.index(CS_UNIQUEID)
                tableIds = tuple(self.item(rr, col).value for rr in range(self.rowCount()))

                if trigger == Notifier.DELETE:
                    # uniqueIds in the visible table
                    if uniqueId in (set(tableIds) - set(_df[CS_UNIQUEID])):
                        # remove from the table
                        self._dataFrameObject._dataFrame.drop([uniqueId], inplace=True)
                        self.removeRow(tableIds.index(uniqueId))

                elif trigger == Notifier.CREATE:
                    # uniqueIds in the visible table
                    if uniqueId in (set(_df[CS_UNIQUEID]) - set(tableIds)):
                        newRow = self._newRowFromUniqueId(_df, obj, uniqueId)
                        # visible table dataframe update
                        self._dataFrameObject._dataFrame.loc[uniqueId] = newRow
                        # update the table widgets - really need to change to QTableView (think it was actually this before)
                        self.addRow(newRow)

                elif trigger == Notifier.CHANGE:
                    # uniqueIds in the visible table
                    if uniqueId in (set(_df[CS_UNIQUEID]) & set(tableIds)):
                        newRow = self._newRowFromUniqueId(_df, obj, uniqueId)
                        # visible table dataframe update
                        self._dataFrameObject._dataFrame.loc[uniqueId] = newRow
                        # update the table widgets - really need to change to QTableView (think it was actually this before)
                        self.setRow(tableIds.index(uniqueId), newRow)

                elif trigger == Notifier.RENAME:
                    # not sure that I need this yet
                    pass

            except Exception as es:
                getLogger().debug2(f'Error updating row in table {es}')

        if _update:
            getLogger().debug2('<updateRowCallback>', data['notifier'],
                               self._tableData['tableSelection'],
                               data['trigger'], data['object'])
            _val = self.getSelectedObjects() or []
            self._tableSelectionChanged.emit(_val)

        return _update

    def clearSelection(self):
        """Clear the current selection in the table
        and remove objects from the current list
        """
        with self._tableBlockSignals('clearSelection'):
            # get the selected objects from the table
            objList = self.getSelectedObjects()
            self.selectionModel().clearSelection()

            # remove from the current list
            multiple = self._tableData['classCallBack']
            if self._dataFrameObject and multiple:
                multipleAttr = getattr(self.current, multiple, [])
                if len(multipleAttr) > 0:
                    # need to remove objList from multipleAttr - fires only one current change
                    setattr(self.current, multiple, tuple(set(multipleAttr) - set(objList)))

            self._lastSelection = [None]
        self._tableSelectionChanged.emit([])


#=========================================================================================
# New ChemicalShiftTable
#=========================================================================================

# define a simple class that can contains a simple id
blankId = SimpleNamespace(className='notDefined', serial=0)

OBJECT_CLASS = 0
OBJECT_PARENT = 1
MODULEIDS = {}


class _NewChemicalShiftTable(_SimplePandasTableViewProjectSpecific):
    """New chemicalShiftTable based on faster QTableView
    Actually more like the original table but with pandas dataFrame
    """
    className = 'ChemicalShiftListTable'
    attributeName = 'chemicalShiftLists'

    PRIMARYCOLUMN = CS_OBJECT  # column holding active objects (uniqueId/ChemicalShift for this table?)
    defaultHidden = [CS_UNIQUEID, CS_ISDELETED, CS_FIGUREOFMERIT, CS_ALLPEAKS, CS_CHAINCODE,
                     CS_SEQUENCECODE, CS_STATE, CS_ORPHAN]
    _internalColumns = [CS_ISDELETED, CS_OBJECT]  # columns that are always hidden

    # define self._columns here
    columnHeaders = {CS_UNIQUEID           : 'Unique ID',
                     CS_ISDELETED          : 'isDeleted',  # should never be visible
                     CS_PID                : 'ChemicalShift',
                     CS_VALUE              : 'ChemicalShift Value (ppm)',
                     CS_VALUEERROR         : 'Value Error',
                     CS_FIGUREOFMERIT      : 'Figure of Merit',
                     CS_NMRATOM            : 'NmrAtom',
                     CS_CHAINCODE          : 'ChainCode',
                     CS_SEQUENCECODE       : 'SequenceCode',
                     CS_RESIDUETYPE        : 'ResidueType',
                     CS_ATOMNAME           : 'AtomName',
                     CS_STATE              : 'State',
                     CS_ORPHAN             : 'Orphaned',
                     CS_ALLPEAKS           : 'Assigned Peaks',
                     CS_SHIFTLISTPEAKSCOUNT: 'Peak Count',
                     CS_ALLPEAKSCOUNT      : 'Total Peak Count',
                     CS_COMMENT            : 'Comment',
                     CS_OBJECT             : '_object'
                     }

    tipTexts = ('Unique identifier for the chemicalShift',
                'isDeleted',  # should never be visible
                'ChemicalShift.pid',
                'ChemicalShift value in ppm',
                'Error in the chemicalShift value in ppm',
                'Figure of merit, between 0 and 1',
                'Pid of nmrAtom if attached, or None',
                'ChainCode of attached nmrAtom, or None',
                'SequenceCode of attached nmrAtom, or None',
                'ResidueType of attached nmrAtom, or None',
                'AtomName of attached nmrAtom, or None',
                'Active state of chemicalShift',
                'Orphaned state of chemicalShift',
                'List of assigned peaks associated with this chemicalShift',
                'Number of assigned peaks attached to a chemicalShift\nbelonging to spectra associated with parent chemicalShiftList',
                'Total number of assigned peaks attached to a chemicalShift\nbelonging to any spectra',
                'Optional comment for each chemicalShift',
                'None',
                )

    # define the notifiers that are required for the specific table-type
    tableClass = ChemicalShiftList
    rowClass = ChemicalShift
    cellClass = None
    tableName = tableClass.className
    rowName = tableClass.className
    cellName = None
    cellClassNames = None

    selectCurrent = True
    callBackClass = ChemicalShift
    search = False

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 chemicalShiftList=None, hiddenColumns=None,
                 enableExport=True, enableDelete=True, enableSearch=False,
                 **kwds):
        """Initialise the widgets for the module.
        """

        # initialise the currently attached dataFrame
        self._hiddenColumns = [self.columnHeaders[col] for col in hiddenColumns] if hiddenColumns else \
            [self.columnHeaders[col] for col in self.defaultHidden]
        self._internalColumns = [self.columnHeaders[col] for col in self._internalColumns]

        # create the table; objects are added later via the displayTableForNmrChain method
        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=mainWindow,
                         moduleParent=moduleParent,
                         multiSelect=True,
                         showVerticalHeader=False,
                         setLayout=True,
                         **kwds
                         )

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

        # set the delegate for editing
        delegate = _CSLTableDelegate(self)
        self.setItemDelegate(delegate)

    def _postInitTableCommonWidgets(self):
        from ccpn.ui.gui.widgets.DropBase import DropBase
        from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
        from ccpn.ui.gui.widgets.ScrollBarVisibilityWatcher import ScrollBarVisibilityWatcher

        # add a dropped notifier to all tables
        if self.moduleParent is not None:
            # set the dropEvent to the mainWidget of the module, otherwise the event gets stolen by Frames
            self.moduleParent.mainWidget._dropEventCallback = self._processDroppedItems

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

        # add a widget handler to give a clean corner widget for the scroll area
        self._cornerDisplay = ScrollBarVisibilityWatcher(self)

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    def _getValidChemicalShift4Callback(self, objs):
        if not objs or not all(objs):
            return
        if isinstance(objs, (tuple, list)):
            cShift = objs[-1]
        else:
            cShift = objs
        if not cShift:
            showWarning('Cannot perform action', 'No selected ChemicalShift')
            return

        return cShift

    def actionCallback(self, data):
        """Notifier DoubleClick action on item in table. Mark a chemicalShift based on attached nmrAtom
        """
        from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import markNmrAtoms

        cShift = self._getValidChemicalShift4Callback(data.get(CallBack.OBJECT, []))
        if len(self.mainWindow.marks):
            if self.moduleParent.autoClearMarksWidget.checkBox.isChecked():
                self.mainWindow.clearMarks()
        if cShift and cShift.nmrAtom:
            markNmrAtoms(self.mainWindow, [cShift.nmrAtom])

    def selectionCallback(self, data):
        """Notifier Callback for selecting rows in the table
        """
        objs = data[CallBack.OBJECT]
        self.current.chemicalShifts = objs or []

        if objs:
            nmrResidues = tuple(set(cs.nmrAtom.nmrResidue for cs in objs if cs.nmrAtom))
        else:
            nmrResidues = []

        if nmrResidues:
            # set the associated nmrResidue and nmrAtoms
            nmrAtoms = tuple(set(nmrAtom for nmrRes in nmrResidues for nmrAtom in nmrRes.nmrAtoms))
            self.current.nmrAtoms = nmrAtoms
            self.current.nmrResidues = nmrResidues

        else:
            self.current.nmrAtoms = []
            self.current.nmrResidues = []

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

    def _newRowFromUniqueId(self, df, obj, uniqueId):
        """Create a new row to insert into the dataFrame or replace row
        """
        _row = df.loc[uniqueId]
        # make the new row
        newRow = _row[:CS_ISDELETED].copy()
        _midRow = _row[CS_VALUE:CS_ATOMNAME]  # CS_STATIC
        _comment = _row[CS_COMMENT:]
        _pidCol = pd.Series(obj.pid, index=[CS_PID, ])
        _extraCols = pd.Series(self._derivedFromObject(obj), index=[CS_STATE, CS_ORPHAN, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT])  # if state required

        # newRow = newRow.append([_pidCol, _midRow, _extraCols, _comment])  # deprecated
        newRow = pd.concat([newRow, _pidCol, _midRow, _extraCols, _comment])

        # append the actual object to the end - not sure whether this is required - check _highlightObjs
        newRow[CS_OBJECT] = obj

        # replace the visible nans with '' for comment column and string 'None' elsewhere
        newRow[CS_COMMENT:CS_COMMENT].fillna('', inplace=True)
        newRow.fillna('None', inplace=True)

        return list(newRow)

    def _derivedFromObject(self, obj):
        """Get a tuple of derived values from obj
        Not very generic yet - column class now seems redundant
        """
        _allPeaks = obj.allAssignedPeaks
        totalPeakCount = len(_allPeaks)
        peaks = [pp.pid for pp in _allPeaks if pp.spectrum.chemicalShiftList == obj.chemicalShiftList]
        peakCount = len(peaks)

        state = obj.state
        if state == ChemicalShiftState.ORPHAN:
            state = ChemicalShiftState.DYNAMIC
        state = state.description  # if state needed
        orphan = u'\u2713' if obj.orphan else ''  # unicode tick character

        return (state, orphan, str(peaks), peakCount, totalPeakCount)

    @staticmethod
    def _setComment(obj, value):
        """CCPN-INTERNAL: Insert a comment into object
        """
        obj.comment = value if value else None

    def buildTableDataFrame(self):
        """Return a Pandas dataFrame from an internal list of objects.
        The columns are based on the 'func' functions in the columnDefinitions.
        :return pandas dataFrame
        """
        # create the column objects
        _cols = [
            # (col, lambda row: _getValueByHeader(row, col), _tipTexts[ii], None, None)
            (self.columnHeaders[col], lambda row: _getValueByHeader(row, col), self.tipTexts[ii], None, None)
            for ii, col in enumerate(CS_TABLECOLUMNS)
            ]

        # NOTE:ED - hack to add the comment editor to the comment column, decimal places to value/valueError/figureOfMerit
        _temp = list(_cols[CS_TABLECOLUMNS.index(CS_COMMENT)])
        _temp[COLUMN_COLDEFS.index(COLUMN_SETEDITVALUE)] = lambda obj, value: self._setComment(obj, value)
        _cols[CS_TABLECOLUMNS.index(CS_COMMENT)] = tuple(_temp)
        for col in [CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT]:
            _temp = list(_cols[CS_TABLECOLUMNS.index(col)])
            _temp[COLUMN_COLDEFS.index(COLUMN_FORMAT)] = '%0.3f'
            _cols[CS_TABLECOLUMNS.index(col)] = tuple(_temp)

        # set the table _columns
        self._columns = ColumnClass(_cols)

        _csl = self._table

        if _csl._data is not None:
            # is of type _ChemicalShiftListFrame - should move functionality to there
            df = _csl._data.copy()
            df = df[df[CS_ISDELETED] == False]
            df.drop(columns=[CS_STATIC], inplace=True)  # static not required

            df.set_index(df[CS_UNIQUEID], inplace=True, )  # drop=False)

            df.insert(CS_TABLECOLUMNS.index(CS_PID), CS_PID, None)
            df.insert(CS_TABLECOLUMNS.index(CS_STATE), CS_STATE, None)  # if state require
            df.insert(CS_TABLECOLUMNS.index(CS_ORPHAN), CS_ORPHAN, None)  # if state require
            df.insert(CS_TABLECOLUMNS.index(CS_ALLPEAKS), CS_ALLPEAKS, None)
            df.insert(CS_TABLECOLUMNS.index(CS_SHIFTLISTPEAKSCOUNT), CS_SHIFTLISTPEAKSCOUNT, None)
            df.insert(CS_TABLECOLUMNS.index(CS_ALLPEAKSCOUNT), CS_ALLPEAKSCOUNT, None)

            _objs = _csl._shifts
            if _objs:
                # append the actual objects as the last column - not sure whether this is required - check _highlightObjs
                df[CS_OBJECT] = _objs
                df[CS_PID] = [_shift.pid for _shift in _objs]

                _stats = [self._derivedFromObject(obj) for obj in _objs]
                df[[CS_STATE, CS_ORPHAN, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT]] = _stats

                # replace the visible nans with '' for comment column and string 'None' elsewhere
                df[CS_COMMENT].fillna('', inplace=True)
                df.fillna('None', inplace=True)
            else:
                df[CS_OBJECT] = []

        else:
            df = pd.DataFrame(columns=[self.columnHeaders[val] for val in CS_TABLECOLUMNS])

        # extract the row objects from the dataFrame
        _objects = [row for row in df.itertuples()]
        self._objects = _objects

        # update the columns to the visible headings
        df.columns = [self.columnHeaders[val] for val in CS_TABLECOLUMNS]

        # set the table from the dataFrame
        _dfObject = DataFrameObject(dataFrame=df,
                                    columnDefs=self._columns or [],
                                    table=self,
                                    )
        _dfObject._objects = _objects

        return _dfObject

    def refreshTable(self):
        # subclass to refresh the groups
        # _updateSimplePandasTable(self, self._df)
        # # self.updateTableExpanders()

        # easier to re-populate from scratch
        self.populateTable(selectedObjects=self.current.chemicalShifts)

    def setDataFromSearchWidget(self, dataFrame):
        """Set the data for the table from the search widget
        """
        # update to the new sub-table
        _updateSimplePandasTable(self, dataFrame)
        self._df = dataFrame
        # self._updateGroups(dataFrame)
        # self.updateTableExpanders()

    def _updateTableCallback(self, data):
        # check the trigger and the current pulldown and update accordingly
        trigger = data[Notifier.TRIGGER]

        if trigger == Notifier.RENAME and data[Notifier.OBJECT] == self.moduleParent._modulePulldown.getSelectedObject():
            self.populateTable(selectedObjects=self.current.chemicalShifts)

    def _updateCellCallback(self, data):
        # print(f'>>> _updateCellCallback')
        pass

    def _searchCallBack(self, data):
        # print(f'>>> _searchCallBack')
        pass

    def _updateRowCallback(self, data):
        """Notifier callback for updating the table for change in chemicalShifts
        :param data: notifier content
        """
        with self._blockTableSignals('_updateRowCallback'):
            obj = data[Notifier.OBJECT]
            uniqueId = obj.uniqueId

            # check that the dataframe and object are valid
            if self._df is None:
                getLogger().debug(f'{self.__class__.__name__}._updateRowCallback: dataFrame is None')
                return
            if obj is None:
                getLogger().debug(f'{self.__class__.__name__}._updateRowCallback: callback object is undefined')
                return

            # check that the object belongs to the list that is being displayed
            if obj.chemicalShiftList != self._table:
                return

            _update = False  # from original row update - need to check

            trigger = data[Notifier.TRIGGER]
            try:
                _data = self._table._data
                _data = _data[_data[CS_ISDELETED] == False]  # not deleted - should be the only visible ones
                dataIds = set(_data[CS_UNIQUEID])
                tableIds = set(self._df['Unique ID'])  # must be table column name, not reference name

                if trigger == Notifier.DELETE:
                    # uniqueIds in the visible table
                    if uniqueId in (tableIds - dataIds):
                        # remove from the table
                        self.model()._deleteRow(uniqueId)

                        # NOTE:ED - remember which row was deleted for undo?

                elif trigger == Notifier.CREATE:
                    # uniqueIds in the visible table
                    if uniqueId in (dataIds - tableIds):
                        newRow = self._newRowFromUniqueId(_data, obj, uniqueId)

                        # insert into the table
                        self.model()._insertRow(uniqueId, newRow)

                elif trigger == Notifier.CHANGE:
                    # uniqueIds in the visible table
                    if uniqueId in (dataIds & tableIds):
                        newRow = self._newRowFromUniqueId(_data, obj, uniqueId)

                        # visible table dataframe update
                        self.model()._updateRow(uniqueId, newRow)

                elif trigger == Notifier.RENAME:
                    # not sure that I need this yet - should be the same as .CHANGE
                    pass

            except Exception as es:
                getLogger().debug2(f'Error updating row in table {es}')

        if _update:
            getLogger().debug2('<updateRowCallback>', data['notifier'],
                               self._tableData['tableSelection'],
                               data['trigger'], data['object'])
            _val = self.getSelectedObjects() or []
            self._tableSelectionChanged.emit(_val)

        return _update

    def _selectCurrentCallBack(self, data):
        """Callback from a notifier to highlight the chemical shifts
        :param data:
        """
        if self._tableBlockingLevel:
            return

        currentShifts = data['value']
        self._selectOnTableCurrentChemicalShifts(currentShifts)

    def _selectionChangedCallback(self, selected, deselected):
        """Handle item selection as changed in table - call user callback
        Includes checking for clicking below last row
        """
        self._changeTableSelection(None)

    def _selectOnTableCurrentChemicalShifts(self, currentShifts):
        """Highlight the list of currentShifts on the table
        :param currentShifts:
        """
        self.highlightObjects(currentShifts)

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to insert new merge items to top of context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)

        # add extra items to the menu
        _actions = self.tableMenu.actions()
        if _actions:
            _topMenuItem = _actions[0]
            _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            self._navigateMenu = self.tableMenu.addMenu('Navigate to:')
            self._mergeMenuAction = self.tableMenu.addAction('Merge NmrAtoms', self._mergeNmrAtoms)
            self._editMenuAction = self.tableMenu.addAction('Edit NmrAtom', self._editNmrAtom)
            self._removeAssignmentsMenuAction = self.tableMenu.addAction('Remove assignments', self._removeAssignments)

            # move new actions to the top of the list
            self.tableMenu.insertAction(_topSeparator, self._removeAssignmentsMenuAction)
            self.tableMenu.insertAction(self._removeAssignmentsMenuAction, self._mergeMenuAction)
            self.tableMenu.insertAction(self._mergeMenuAction, self._editMenuAction)

    def _raiseTableContextMenu(self, pos):
        """Create a new menu and popup at cursor position
        Add merge item
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if (data is not None and not data.empty):
            cShift = data.get(DATAFRAME_OBJECT)
            currentNmrAtom = cShift.nmrAtom if cShift else None

            selection = [ch.nmrAtom for ch in selection or [] if ch.nmrAtom]
            _check = (currentNmrAtom and 1 < len(selection) and currentNmrAtom in selection) or False
            _option = 'into {}'.format(currentNmrAtom.id if currentNmrAtom else '') if _check else ''
            self._mergeMenuAction.setText('Merge NmrAtoms {}'.format(_option))
            self._mergeMenuAction.setEnabled(_check)

            current = True if (currentNmrAtom and selection) else False
            self._editMenuAction.setText('Edit NmrAtom {}'.format(currentNmrAtom.id if current else ''))
            self._editMenuAction.setEnabled(True if current else False)
            self._addNavigationStripsToContextMenu()

            self._removeAssignmentsMenuAction.setEnabled(True if selection else False)

        else:
            # disabled but visible lets user know that menu items exist
            self._mergeMenuAction.setText('Merge NmrAtoms')
            self._mergeMenuAction.setEnabled(False)
            self._editMenuAction.setText('Edit NmrAtom')
            self._editMenuAction.setEnabled(False)
            self._removeAssignmentsMenuAction.setEnabled(False)

        # raise the menu
        super()._raiseTableContextMenu(pos)

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _mergeNmrAtoms(self):
        """Merge the nmrAtoms in the selection into the nmrAtom that has been right-clicked
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if (data is not None and not data.empty) and selection:
            cShift = data.get(DATAFRAME_OBJECT)
            currentNmrAtom = cShift.nmrAtom if cShift else None

            matching = [ch.nmrAtom for ch in selection if ch and ch.nmrAtom and ch.nmrAtom != currentNmrAtom and
                        ch.nmrAtom.isotopeCode == currentNmrAtom.isotopeCode]
            nonMatching = [ch.nmrAtom for ch in selection if ch and ch.nmrAtom and ch.nmrAtom != currentNmrAtom and
                           ch.nmrAtom.isotopeCode != currentNmrAtom.isotopeCode]

            if len(matching) < 1:
                showWarning('Merge NmrAtoms', 'No matching isotope codes')
            else:
                ss = 's' if (len(nonMatching) > 1) else ''
                nonMatchingList = '\n\n\n({} nmrAtom{} with non-matching isotopeCode{})'.format(len(nonMatching), ss, ss) if nonMatching else ''
                yesNo = showYesNo('Merge NmrAtoms', "Do you want to merge\n\n"
                                                    "{}   into   {}{}".format('\n'.join([ss.id for ss in matching]),
                                                                              currentNmrAtom.id,
                                                                              nonMatchingList))
                if yesNo:
                    currentNmrAtom.mergeNmrAtoms(matching)

    def _editNmrAtom(self):
        """Show the edit nmrAtom popup for the clicked nmrAtom
        """
        data = self.getRightMouseItem()
        if data is not None and not data.empty:
            cShift = data.get(DATAFRAME_OBJECT)
            currentNmrAtom = cShift.nmrAtom if cShift else None

            if currentNmrAtom:
                from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomEditPopup

                popup = NmrAtomEditPopup(parent=self.mainWindow, mainWindow=self.mainWindow, obj=currentNmrAtom)
                popup.exec_()

    def _addNavigationStripsToContextMenu(self):
        cShift = self._getValidChemicalShift4Callback(self.getSelectedObjects())
        self._navigateMenu.clear()
        if cShift and cShift.nmrAtom:
            name = cShift.nmrAtom.name
            if cShift.value is None:
                return
            value = round(cShift.value, 3)
            if self._navigateMenu is not None:
                self._navigateMenu.addItem(f'All ({name}:{value})',
                                           callback=partial(self._navigateToChemicalShift,
                                                            chemicalShift=cShift,
                                                            stripPid=ALL))
                self._navigateMenu.addSeparator()
                for spectrumDisplay in self.mainWindow.spectrumDisplays:
                    for strip in spectrumDisplay.strips:
                        self._navigateMenu.addItem(f'{strip.pid} ({name}:{value})',
                                                   callback=partial(self._navigateToChemicalShift,
                                                                    chemicalShift=cShift,
                                                                    stripPid=strip.pid))
                    self._navigateMenu.addSeparator()

    def _navigateToChemicalShift(self, chemicalShift, stripPid):
        strips = []
        if stripPid == ALL:
            strips = self.mainWindow.strips
        else:
            strip = self.application.getByGid(stripPid)
            if strip:
                strips.append(strip)
        if strips:
            failedStripPids = []
            for strip in strips:

                try:
                    navigateToPositionInStrip(strip,
                                              positions=[chemicalShift.value],
                                              axisCodes=[chemicalShift.nmrAtom.name],
                                              widths=[])
                except:
                    failedStripPids.append(strip.pid)
            if len(failedStripPids) > 0:
                stripStr = 'strip' if len(failedStripPids) == 1 else 'strips'
                strips = ', '.join(failedStripPids)
                getLogger().warn(
                        f'Cannot navigate to position {round(chemicalShift.value, 3)} '
                        f'in {stripStr}: {strips} '
                        f'for nmrAtom {chemicalShift.nmrAtom.name}.')

    def _removeAssignments(self):
        """Remove assignments from the selection
        """
        selection = self.getSelectedObjects()
        data = self.getRightMouseItem()
        if (data is not None and not data.empty) and selection:
            if (matching := [ch for ch in selection if ch and ch.nmrAtom]):

                # if there is a selection and the selection contains shift with nmrAtoms
                with undoBlockWithoutSideBar():
                    _peaks = list(pp for pp in self.project.peaks if pp.chemicalShiftList == self._table)

                    for cs in matching:
                        nmrAtom = cs.nmrAtom

                        for peak in _peaks:
                            peakDimNmrAtoms = list(list(pp) for pp in peak.dimensionNmrAtoms)
                            for peakDim in peakDimNmrAtoms:
                                if nmrAtom in peakDim:
                                    peakDim.remove(nmrAtom)

                            peak.dimensionNmrAtoms = peakDimNmrAtoms


#=========================================================================================
# _CSLTableDelegate - handle editing the table, needs moving
#=========================================================================================

EDIT_ROLE = QtCore.Qt.EditRole


class _CSLTableDelegate(QtWidgets.QStyledItemDelegate):
    """handle the setting of data when editing the table
    """

    def __init__(self, parent):
        """Initialise the delegate
        :param parent - link to the handling table:
        """
        QtWidgets.QStyledItemDelegate.__init__(self, parent)
        self.customWidget = False
        self._parent = parent

    def setEditorData(self, widget, index) -> None:
        """populate the editor widget when the cell is edited
        """
        model = index.model()
        value = model.data(index, EDIT_ROLE)

        if not isinstance(value, (list, tuple)):
            value = (value,)

        if hasattr(widget, 'setColor'):
            widget.setColor(*value)

        elif hasattr(widget, 'setData'):
            widget.setData(*value)

        elif hasattr(widget, 'set'):
            widget.set(*value)

        elif hasattr(widget, 'setValue'):
            widget.setValue(*value)

        elif hasattr(widget, 'setText'):
            widget.setText(*value)

        elif hasattr(widget, 'setFile'):
            widget.setFile(*value)

        else:
            msg = 'Widget %s does not expose "setData", "set" or "setValue" method; ' % widget
            msg += 'required for table proxy editing'
            raise Exception(msg)

    def setModelData(self, widget, mode, index):
        """Set the object to the new value
        :param widget - typically a lineedit handling the editing of the cell
        :param mode - editing mode:
        :param index - QModelIndex of the cell
        """
        if hasattr(widget, 'get'):
            value = widget.get()

        elif hasattr(widget, 'value'):
            value = widget.value()

        elif hasattr(widget, 'text'):
            value = widget.text()

        elif hasattr(widget, 'getFile'):
            files = widget.selectedFiles()
            if not files:
                return
            value = files[0]

        else:
            msg = f'Widget {widget} does not expose "get", "value" or "text" method; required for table editing'
            raise Exception(msg)

        row = index.row()
        col = index.column()

        try:
            # get the sorted element from the dataFrame
            df = self._parent._df
            _iRow = self._parent.model()._sortOrder[row]
            obj = df.iloc[_iRow]['_object']

            # set the data which will fire notifiers to populate all tables (including this)
            func = self._parent._dataFrameObject.setEditValues[col]
            if func and obj:
                func(obj, value)

        except Exception as es:
            getLogger().debug('Error handling cell editing: %i %i - %s    %s    %s' % (row, col, str(es), self._parent.model()._sortOrder, value))


#=========================================================================================
# main
#=========================================================================================

def main():
    """Show the chemicalShiftTable module
    """
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = ChemicalShiftTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
