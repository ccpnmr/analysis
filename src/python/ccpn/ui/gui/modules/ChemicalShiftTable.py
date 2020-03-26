"""This file contains ChemicalShiftTable class

modified by Geerten 1-7/12/2016
tertiary version by Ejb 9/5/17
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-03-26 12:02:35 +0000 (Thu, March 26, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChemicalShiftListPulldown
# from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from ccpn.core.lib.CallBack import CallBack
from PyQt5 import QtGui, QtWidgets
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier


logger = getLogger()
ALL = '<all>'


class ChemicalShiftTableModule(CcpnModule):
    """
    This class implements the module by wrapping a NmrResidueTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    className = 'ChemicalShiftTableModule'

    # we are subclassing this Module, hence some more arguments to the init
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
            self.displaysWidget = ListCompoundWidget(self._CSTwidget,
                                                     grid=(0, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                     vPolicy='minimal',
                                                     #minimumWidths=(colwidth, 0, 0),
                                                     fixedWidths=(colwidth, 2 * colwidth, None),
                                                     orientation='left',
                                                     labelText='Display(s):',
                                                     tipText='SpectrumDisplay modules to respond to double-click',
                                                     texts=[ALL] + [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
                                                     )
            self.displaysWidget.setPreSelect(self._fillDisplayWidget)
            self.displaysWidget.setFixedHeights((None, None, 40))

            self.sequentialStripsWidget = CheckBoxCompoundWidget(
                    self._CSTwidget,
                    grid=(1, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                    #minimumWidths=(colwidth, 0),
                    fixedWidths=(colwidth, 30),
                    orientation='left',
                    labelText='Show sequential strips:',
                    checked=False
                    )

            self.markPositionsWidget = CheckBoxCompoundWidget(
                    self._CSTwidget,
                    grid=(2, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                    #minimumWidths=(colwidth, 0),
                    fixedWidths=(colwidth, 30),
                    orientation='left',
                    labelText='Mark positions:',
                    checked=True
                    )
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
                                                     grid=(0, 0))

        if chemicalShiftList is not None:
            self.selectChemicalShiftList(chemicalShiftList)
        elif selectFirstItem:
            self.chemicalShiftTable._chemicalShiftListPulldown.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _fillDisplayWidget(self):
        ll = ['> select-to-add <'] + [ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
        self.displaysWidget.pulldownList.setData(texts=ll)

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

    def _getDisplays(self):
        """
        Return list of displays to navigate - if needed
        """
        displays = []
        # check for valid displays
        gids = self.displaysWidget.getTexts()
        if len(gids) == 0: return displays
        if ALL in gids:
            displays = self.application.ui.mainWindow.spectrumDisplays
        else:
            displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        return displays

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.chemicalShiftTable._close()
        super()._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class ChemicalShiftTable(GuiTable):
    """
    Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
    """

    className = 'ChemicalShiftListTable'
    attributeName = 'chemicalShiftLists'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 chemicalShiftList=None, hiddenColumns=['Pid', 'NmrChain', 'Sequence', 'Type'], **kwds):
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

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        self.chemicalShiftList = None

        # create the column objects
        self.CScolumns = ColumnClass(
                [('#', lambda cs: cs.nmrAtom.serial, 'NmrAtom serial number', None, None),
                 ('Pid', lambda cs: cs.pid, 'Pid of chemicalShift', None, None),
                 ('_object', lambda cs: cs, 'Object', None, None),
                 ('NmrResidue', lambda cs: cs._key.rsplit('.', 1)[0], 'NmrResidue Id', None, None),

                 # ('testResidue', lambda cs: ChemicalShiftTable._getNmrResidue(cs), 'NmrResidue: nmrChain', None, None),  # should be the same as above
                 ('NmrChain', lambda cs: ChemicalShiftTable._getNmrChain(cs), 'NmrChain containing the nmrResidue linked to this chemicalShift', None, None),
                 ('Sequence', lambda cs: ChemicalShiftTable._getSequenceCode(cs), 'NmrResidue sequence code', None, None),
                 ('Type', lambda cs: ChemicalShiftTable._getResidueType(cs), 'NmrResidue residue type', None, None),

                 ('Name', lambda cs: cs._key.rsplit('.', 1)[-1], 'NmrAtom name', None, None),
                 ('Shift', lambda cs: ChemicalShiftTable._stLamFloat(cs, 'value'), 'Value of chemical shift, in selected ChemicalShiftList', None, '%8.3f'),
                 ('Std. Dev.', lambda cs: ChemicalShiftTable._stLamFloat(cs, 'valueError'),
                  'Standard deviation of chemical shift, in selected ChemicalShiftList', None, '%6.3f'),
                 ('Shift list peaks',
                  lambda cs: ChemicalShiftTable._getShiftPeakCount(cs), 'Number of peaks assigned to this NmrAtom in PeakLists associated with this'
                                                                                 'ChemicalShiftList', None, '%3d'),
                 ('All peaks',
                  lambda cs: len(set(x for x in cs.nmrAtom.assignedPeaks)), 'Number of peaks assigned to this NmrAtom across all PeakLists', None, '%3d'),
                 ('Comment', lambda cs: ChemicalShiftTable._getCommentText(cs), 'Notes',
                  lambda cs, value: ChemicalShiftTable._setComment(cs, value), None)
                 ])
        #[Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)
        # for colName, func, tipText, editValue, columnFormat in self.columnDefs]

        # create the table; objects are added later via the displayTableForNmrChain method
        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True,
                         actionCallback=actionCallback if actionCallback else self._actionCallback,
                         selectionCallback=selectionCallback if selectionCallback else self._selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6),
                         multiSelect=True
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

        # initialise the currently attached dataFrame
        self._hiddenColumns = hiddenColumns
        self.dataFrameObject = None

        # TODO: see how to handle peaks as this is too costly at present
        # Notifier object to update the table if the peaks change
        self._peaksNotifier = None
        # self._setNotifiers()

        # self.setColumns(self.CScolumns)   # ejb - moved here but doesn't allow changing of the columns

        if chemicalShiftList is not None:
            self._selectChemicalShiftList(chemicalShiftList)

        self.setTableNotifiers(tableClass=ChemicalShiftList,
                               className=self.attributeName,
                               tableSelection='chemicalShiftList',
                               rowClass=ChemicalShift,
                               cellClassNames=None,     # handled by the _finaliseAction notifier system
                               tableName='chemicalShiftList', rowName='chemicalShift',
                               changeFunc=self.displayTableForChemicalShift,
                               updateFunc=self._update,
                               pullDownWidget=self.CScolumns,
                               callBackClass=ChemicalShift,
                               selectCurrentCallBack=None,
                               searchCallBack=None,
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
        self.populateTable(rowObjects=chemicalShiftList.chemicalShifts,
                           columnDefs=self.CScolumns
                           )

    def _actionCallback(self, data):
        """
        Notifier DoubleClick action on item in table
        """
        # multiselection table will return a list of objects
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            obj = objs[0]
        else:
            obj = objs

        getLogger().debug('ChemicalShiftTable>>> action', obj)

    def _selectionCallback(self, data):
        """
        Notifier Callback for selecting a row in the table
        """
        # obj = data[CallBack.OBJECT]
        #
        # getLogger().debug('ChemicalShiftTable>>> selection', obj)
        # return

        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            chemicalShift = objs[0]
        else:
            chemicalShift = objs

        if chemicalShift:
            self.current.chemicalShift = chemicalShift
            ChemicalShiftTableModule.currentCallback = {'object': self.chemicalShiftList, 'table': self}

            self.current.nmrAtom = chemicalShift.nmrAtom
            self.current.nmrResidue = chemicalShift.nmrAtom.nmrResidue

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

    # this is now deprecated and replaced by notifers in _finaliseAction - may do this for all tables
    # def getCellToRows(self, cellItem, attribute):
    #     """Get the list of objects which cellItem maps to for this table
    #     """
    #     # this is a step towards making guiTableABC and subclass for each table
    #     chemicalShifts = ()
    #     if self.chemicalShiftList:
    #         # chemicalShifts = tuple(set([cs for cs in self.chemicalShiftList.chemicalShifts if cs.nmrAtom and cellItem in cs.nmrAtom.assignedPeaks]))
    #         chemicalShifts = tuple(set([cs for cs in self.chemicalShiftList.chemicalShifts if cs.nmrAtom is cellItem]))
    #
    #     print('>>>>>>chemicalShift on nmrAtom', cellItem, chemicalShifts)
    #     return chemicalShifts

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
        # self.clearTableNotifiers()
        self._chemicalShiftListPulldown.unRegister()
        super()._close()

