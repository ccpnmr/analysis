"""This file contains ChemicalShiftTable class

modified by Geerten 1-7/12/2016
tertiary version by Ejb 9/5/17
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
__dateModified__ = "$dateModified: 2021-11-04 13:25:04 +0000 (Thu, November 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from functools import partial
import pandas as pd
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.ChemicalShiftList import CS_UNIQUEID, CS_ISDELETED, CS_PID, \
    CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT, CS_ATOMNAME, \
    CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT, \
    CS_COMMENT, CS_OBJECT, \
    CS_TABLECOLUMNS
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
from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip
from ccpn.ui.gui.widgets.Column import COLUMN_COLDEFS, COLUMN_SETEDITVALUE, COLUMN_FORMAT


logger = getLogger()

LINKTOPULLDOWNCLASS = 'linkToPulldownClass'


class ChemicalShiftTableModule(CcpnModule):
    """
    This class implements the module by wrapping a NmrResidueTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    className = 'ChemicalShiftTableModule'
    _allowRename = True

    activePulldownClass = None  # e.g., can make the table respond to current peakList

    def __init__(self, mainWindow=None, name='Chemical Shift Table',
                 chemicalShiftList=None, selectFirstItem=False):
        """
        Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
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
                    #minimumWidths=(colwidth, 0),
                    fixedWidths=(colwidth, 30),
                    orientation='left',
                    labelText='Auto clear marks:',
                    checked=True
                    )

        # main window
        self.chemicalShiftTable = ChemicalShiftTable(parent=self.mainWidget,
                                                     mainWindow=self.mainWindow,
                                                     moduleParent=self,
                                                     setLayout=True,
                                                     grid=(0, 0),
                                                     hiddenColumns=['isDeleted', 'allPeaks', 'chainCode', 'sequenceCode', 'residueType'])

        if chemicalShiftList is not None:
            self.selectChemicalShiftList(chemicalShiftList)
        elif selectFirstItem:
            self.chemicalShiftTable._chemicalShiftListPulldown.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.chemicalShiftTable._maximise()

    def selectChemicalShiftList(self, chemicalShiftList=None):
        """
        Manually select a ChemicalShiftList from the pullDown
        """
        self.chemicalShiftTable._selectChemicalShiftList(chemicalShiftList)

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.chemicalShiftTable._close()
        super()._closeModule()


class ChemicalShiftTable(GuiTable):
    """
    Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
    """

    className = 'ChemicalShiftListTable'
    attributeName = 'chemicalShiftLists'

    PRIMARYCOLUMN = CS_OBJECT  # column holding active objects (uniqueId/ChemicalShift for this table?)

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 chemicalShiftList=None, hiddenColumns=None, **kwds):
        """
        Initialise the widgets for the module.
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

        # self._widget = Widget(parent=parent, **kwds)
        self._selectedChemicalShiftList = None

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        # self.chemicalShiftList = None

        # initialise the currently attached dataFrame
        self._hiddenColumns = hiddenColumns or []
        self.dataFrameObject = None
        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        # create the table; objects are added later via the displayTableForNmrChain method
        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True, multiSelect=True,
                         actionCallback=actionCallback,
                         selectionCallback=selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6),
                         )
        self.moduleParent = moduleParent

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self._chemicalShiftListPulldown = ChemicalShiftListPulldown(parent=self._widget,
                                                                    mainWindow=self.mainWindow, default=None,
                                                                    # first NmrChain in project (if present)
                                                                    grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                                    showSelectName=True,
                                                                    sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                                    callback=self._selectionPulldownCallback,
                                                                    )

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 1), gridSpan=(1, 1))
        self._widget.getLayout().setColumnStretch(1, 2)

        if chemicalShiftList is not None:
            self._selectChemicalShiftList(chemicalShiftList)

        self.setTableNotifiers(tableClass=ChemicalShiftList,
                               rowClass=ChemicalShift,
                               # cellClassNames=(NmrAtom, '_chemicalShifts'), # not required
                               tableName='chemicalShiftList', rowName='chemicalShift',
                               changeFunc=self.displayTableForChemicalShift,
                               className=self.attributeName,
                               # updateFunc=self._update,
                               tableSelection='_selectedChemicalShiftList',
                               pullDownWidget=self._chemicalShiftListPulldown,
                               callBackClass=ChemicalShift,
                               selectCurrentCallBack=self._selectOnTableCurrentChemicalShiftNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, ChemicalShiftList, self._chemicalShiftListPulldown)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

    def _selectChemicalShiftList(self, chemicalShiftList=None):
        """
        Manually select a ChemicalShiftList from the pullDown
        """
        if chemicalShiftList is None:
            # logger.warning('select: No ChemicalShiftList selected')
            # raise ValueError('select: No ChemicalShiftList selected')
            self._chemicalShiftListPulldown.selectFirstItem()
        else:
            if not isinstance(chemicalShiftList, ChemicalShiftList):
                logger.warning('select: Object is not of type ChemicalShiftList')
                raise TypeError('select: Object is not of type ChemicalShiftList')
            else:
                for widgetObj in self._chemicalShiftListPulldown.textList:
                    if chemicalShiftList.pid == widgetObj:
                        self.chemicalShiftList = chemicalShiftList
                        self._chemicalShiftListPulldown.select(self.chemicalShiftList.pid)

    def displayTableForChemicalShift(self, chemicalShiftList):
        """
        Display the table for all chemicalShift
        """
        self._chemicalShiftListPulldown.select(chemicalShiftList.pid)
        self._update(chemicalShiftList)

    def _updateCallback(self, data):
        """
        Notifier callback for updating the table
        """
        thisChemicalShiftList = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the restraintList
        if self.chemicalShiftList in thisChemicalShiftList:
            self.displayTableForChemicalShift(self.chemicalShiftList)
        else:
            self.clearTable()

    def _maximise(self):
        """
        Refresh the table on a maximise event
        """
        if self.chemicalShiftList:
            self.displayTableForChemicalShift(self.chemicalShiftList)
        else:
            self.clear()

    def _update(self, chemicalShiftList):
        """
        Update the table
        """
        self._selectedChemicalShiftList = self.project.getByPid(self._chemicalShiftListPulldown.getText())

        if self._selectedChemicalShiftList == chemicalShiftList:
            self.populateTable(rowObjects=chemicalShiftList.chemicalShifts,
                               # columnDefs=self.CScolumns,
                               selectedObjects=self.current.chemicalShifts)

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
        # if not cShift.nmrAtom:
        #     showWarning('Cannot perform action', 'No NmrAtom found for ChemicalShift')
        #     return
        return cShift

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Widgets callbacks
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _actionCallback(self, data):
        """
        Notifier DoubleClick action on item in table. Mark a chemicalShift based on attached nmrAtom
        """
        from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import markNmrAtoms

        cShift = self._getValidChemicalShift4Callback(data.get(CallBack.OBJECT, []))
        if len(self.mainWindow.marks):
            if self.moduleParent.autoClearMarksWidget.checkBox.isChecked():
                self.mainWindow.clearMarks()
        if cShift and cShift.nmrAtom:
            markNmrAtoms(self.mainWindow, [cShift.nmrAtom])

    def _selectionCallback(self, data):
        """
        Notifier Callback for selecting a row in the table
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

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting ChemicalShiftList from the pull down menu
        """
        self.chemicalShiftList = self._chemicalShiftListPulldown.getSelectedObject()
        logger.debug('>selectionPulldownCallback>', item, type(item), self.chemicalShiftList)
        if self.chemicalShiftList is not None:
            self._update(self.chemicalShiftList)
        else:
            self.clearTable()

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
            _check = (currentNmrAtom and (1 < len(selection) < 5) and currentNmrAtom in selection) or False
            _option = ' into {}'.format(currentNmrAtom.id if currentNmrAtom else '') if _check else ''
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
        """
        Callback from a notifier to highlight the chemical shifts
        :param data:
        """
        currentShifts = data['value']
        self._selectOnTableCurrentChemicalShifts(currentShifts)

    def _selectOnTableCurrentChemicalShifts(self, currentShifts):
        """
        Highlight the list of currentShifts on the table
        :param currentShifts:
        """
        self.highlightObjects(currentShifts)

    @staticmethod
    def _getShiftPeakCount(chemicalShift):
        """
        CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
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
        """
        CCPN-INTERNAL: used to display Table
        """
        try:
            return float(getattr(row, name))
        except:
            return None

    @staticmethod
    def _getNmrChain(chemicalShift):
        """
        CCPN-INTERNAL: get the nmrChain for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue.nmrChain.id
        except:
            return None

    @staticmethod
    def _getSequenceCode(chemicalShift):
        """
        CCPN-INTERNAL: get the sequenceCode for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue.sequenceCode
        except:
            return None

    @staticmethod
    def _getResidueType(chemicalShift):
        """
        CCPN-INTERNAL: get the residueType for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue.residueType
        except:
            return None

    @staticmethod
    def _getNmrResidue(chemicalShift):
        """
        CCPN-INTERNAL: get the nmrResidue for the nmrResidue associated with this chemicalShift
        """
        try:
            return chemicalShift.nmrAtom.nmrResidue
        except:
            return None

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        self._chemicalShiftListPulldown.unRegister()
        super()._close()

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
            # raise es

        finally:
            self._highLightObjs(objs)
            self.project.unblankNotification()

    # def setTableFromDataFrameObject(self, dataFrameObject, columnDefs=None):
    #     """Populate the table from a Pandas dataFrame
    #     """
    #
    #     with self._tableBlockSignals('setTableFromDataFrameObject'):
    #
    #         # get the currently selected objects
    #         objs = self.getSelectedObjects()
    #
    #         self._dataFrameObject = dataFrameObject
    #
    #         with self._guiTableUpdate(dataFrameObject):
    #             if not dataFrameObject.dataFrame.empty:
    #                 self.setData(dataFrameObject.dataFrame.values)
    #                 # self._updateGroups(dataFrameObject.dataFrame)
    #
    #             else:
    #                 # set a dummy row of the correct length
    #                 self.setData([list(range(len(dataFrameObject.headings)))])
    #                 self._groups = None
    #
    #             # store the current headings, in case table is cleared, to stop table jumping
    #             # self._defaultHeadings = dataFrameObject.headings
    #             # self._defaultHiddenColumns = dataFrameObject.hiddenColumns
    #
    #             if columnDefs:
    #                 for col, colFormat in enumerate(columnDefs.formats):
    #                     if colFormat is not None:
    #                         self.setFormat(colFormat, column=col)
    #
    #         # highlight them back again
    #         self._highLightObjs(objs)
    #
    #     # # outside of the with to spawn a repaint
    #     # self.show()

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
        _peaks = obj.allAssignedPeaks or []
        allPeaks = str([pp.pid for pp in _peaks])
        try:
            shiftPeakCount = len([pp for pp in _peaks if pp.spectrum.chemicalShiftList == obj._chemicalShiftList])
        except Exception as es:
            shiftPeakCount = 0
        peakCount = len(_peaks) if _peaks else 0

        return (allPeaks, shiftPeakCount, peakCount)

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

        # define self._columns here
        _tipTexts = ('Unique identifier for the chemicalShift',
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
                     'List of assigned peaks associated with this chemicalShift',
                     'Number of assigned peaks attached to a chemicalShift\nbelonging to spectra associated with parent chemicalShiftList',
                     'Total number of assigned peaks attached to a chemicalShift\nbelonging to any spectra',
                     'Optional comment for each chemicalShift',
                     '1',
                     )
        # create the column objects
        _cols = [
            (col, lambda row: _getValueByHeader(row, col), _tipTexts[ii], None, None)
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

        if self.chemicalShiftList._wrappedData.data is not None:
            # is of type _ChemicalShiftListFrame - should move functionality to there
            _table = self.chemicalShiftList._wrappedData.data.copy()
            _table = _table[_table[CS_ISDELETED] == False]
            _table.set_index(_table[CS_UNIQUEID], inplace=True, )  # drop=False)

            _table.insert(CS_TABLECOLUMNS.index(CS_PID), CS_PID, None)
            _table.insert(CS_TABLECOLUMNS.index(CS_ALLPEAKS), CS_ALLPEAKS, None)
            _table.insert(CS_TABLECOLUMNS.index(CS_SHIFTLISTPEAKSCOUNT), CS_SHIFTLISTPEAKSCOUNT, None)
            _table.insert(CS_TABLECOLUMNS.index(CS_ALLPEAKSCOUNT), CS_ALLPEAKSCOUNT, None)

            _objs = [self.chemicalShiftList.getChemicalShift(uniqueId=unq) for unq in _table[CS_UNIQUEID]]
            if _objs:
                # append the actual objects as the last column - not sure whether this is required - check _highlightObjs
                _table[CS_OBJECT] = _objs
                _table[CS_PID] = [_shift.pid for _shift in _objs]

                _stats = [self._derivedFromObject(obj) for obj in _objs]
                _table[[CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT]] = _stats

                # replace the visible nans with '' for comment column and string 'None' elsewhere
                _table[CS_COMMENT].fillna('', inplace=True)
                _table.fillna('None', inplace=True)
        else:
            _table = pd.DataFrame(columns=CS_TABLECOLUMNS)

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

    def _updateRowCallback(self, data):
        """
        Notifier callback for updating the table for change in nmrRows
        :param data:
        """

        def _newRowFromUniqueId(data, obj, uniqueId):
            # NOTE:ED - this needs to go elsewhere
            #   need to define a row handler rather than a column handler
            _row = data.loc[uniqueId]
            # make the new row - put into method
            newRow = _row[:CS_ISDELETED].copy()
            _midRow = _row[CS_VALUE:CS_ATOMNAME]
            _comment = _row[CS_COMMENT:]
            _pidCol = pd.Series(obj.pid, index=[CS_PID, ])
            _extraCols = pd.Series(self._derivedFromObject(obj), index=[CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT])

            newRow = newRow.append([_pidCol, _midRow, _extraCols, _comment])

            # append the actual object to the end - not sure whether this is required - check _highlightObjs
            newRow[CS_OBJECT] = obj

            # replace the visible nans with '' for comment column and string 'None' elsewhere
            newRow[CS_COMMENT:CS_COMMENT].fillna('', inplace=True)
            newRow.fillna('None', inplace=True)
            return newRow

        with self._tableBlockSignals('_updateRowCallback'):
            obj = data[Notifier.OBJECT]
            uniqueId = obj.uniqueId

            # check that the object belongs to the list that is being displayed
            if not self._dataFrameObject or obj is None:
                return
            if obj.chemicalShiftList != self.chemicalShiftList:
                return

            _update = False  # from original row update - need to check

            trigger = data[Notifier.TRIGGER]
            try:
                _df = self.chemicalShiftList._data
                _df = _df[_df[CS_ISDELETED] == False]  # not deleted - should be the only visible ones
                # the column containing the uniqueId
                col = CS_TABLECOLUMNS.index(CS_UNIQUEID)
                tableIds = tuple(self.item(rr, col).value for rr in range(self.rowCount()))

                if trigger == Notifier.DELETE:
                    # uniqueIds in the visible table
                    # tableIds = [(rr, self.item(rr, col).value) for rr in range(self.rowCount())]
                    if uniqueId in (set(tableIds) - set(_df[CS_UNIQUEID])):
                        # remove from the table
                        self._dataFrameObject._dataFrame.drop([uniqueId], inplace=True)
                        self.removeRow(tableIds.index(uniqueId))

                elif trigger == Notifier.CREATE:
                    # uniqueIds in the visible table
                    if uniqueId in (set(_df[CS_UNIQUEID]) - set(tableIds)):
                        newRow = _newRowFromUniqueId(_df, obj, uniqueId)
                        # visible table dataframe update
                        self._dataFrameObject._dataFrame.loc[uniqueId] = newRow
                        # update the table widgets - really need to change to QTableView (think it was actually this before)
                        self.addRow(newRow)

                elif trigger == Notifier.CHANGE:
                    # uniqueIds in the visible table
                    if uniqueId in (set(_df[CS_UNIQUEID]) & set(tableIds)):
                        newRow = _newRowFromUniqueId(_df, obj, uniqueId)
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
