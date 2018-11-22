"""This file contains ChemicalShiftTable class

modified by Geerten 1-7/12/2016
tertiary version by Ejb 9/5/17
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:43 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.QuickTable import QuickTable
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.NmrResidue import NmrResidue
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
    def __init__(self, mainWindow=None, name='Chemical Shift Table', chemicalShiftList=None):
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
        # settingsWidget

        if chemicalShiftList is not None:
            self.selectChemicalShiftList(chemicalShiftList)

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _fillDisplayWidget(self):
        list = ['> select-to-add <'] + [ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
        self.displaysWidget.pulldownList.setData(texts=list)

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


class ChemicalShiftTable(QuickTable):
    """
    Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
    """

    className = 'ChemicalShiftListTable'
    attributeName = 'chemicalShiftLists'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None,
                 chemicalShiftList=None, hiddenColumns=['Pid'], **kwds):
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
        self._widget = Widget(parent=parent, **kwds)
        self.chemicalShiftList = None

        # create the column objects
        self.CScolumns = ColumnClass(
                [('#', lambda cs: cs.nmrAtom.serial, 'NmrAtom serial number', None),
                 ('Pid', lambda cs: cs.pid, 'Pid of chemicalShift', None),
                 ('_object', lambda cs: cs, 'Object', None),
                 ('NmrResidue', lambda cs: cs._key.rsplit('.', 1)[0], 'NmrResidue Id', None),
                 ('Name', lambda cs: cs._key.rsplit('.', 1)[-1], 'NmrAtom name', None),
                 ('Shift', lambda cs: '%8.3f' % ChemicalShiftTable._stLamFloat(cs, 'value'), 'Value of chemical shift, in selected ChemicalShiftList', None),
                 ('Std. Dev.', lambda cs: '%6.3f' % ChemicalShiftTable._stLamFloat(cs, 'valueError'),
                  'Standard deviation of chemical shift, in selected ChemicalShiftList', None),
                 ('Shift list peaks',
                  lambda cs: '%3d ' % ChemicalShiftTable._getShiftPeakCount(cs), 'Number of peaks assigned to this NmrAtom in PeakLists associated with this'
                                                                                 'ChemicalShiftList', None),
                 ('All peaks',
                  lambda cs: '%3d ' % len(set(x for x in cs.nmrAtom.assignedPeaks)), 'Number of peaks assigned to this NmrAtom across all PeakLists', None),
                 ('Comment', lambda cs: ChemicalShiftTable._getCommentText(cs), 'Notes',
                  lambda cs, value: ChemicalShiftTable._setComment(cs, value))
                 ])
        #[Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

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
                         )
        self.moduleParent = moduleParent

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self._chemicalShiftListPulldown = ChemicalShiftListPulldown(parent=self._widget,
                                                                    project=self.project, default=0,
                                                                    # first NmrChain in project (if present)
                                                                    grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                                                    showSelectName=True,
                                                                    sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                                    callback=self._selectionPulldownCallback
                                                                    )

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 0), gridSpan=(1, 1))

        self._widget.setFixedHeight(30)

        # initialise the currently attached dataFrame
        self._hiddenColumns = hiddenColumns
        self.dataFrameObject = None

        # TODO: see how to handle peaks as this is too costly at present
        # Notifier object to update the table if the peaks change
        self._peaksNotifier = None
        self._updateSilence = False  # flag to silence updating of the table
        # self._setNotifiers()

        # self.setColumns(self.CScolumns)   # ejb - moved here but doesn't allow changing of the columns

        if chemicalShiftList is not None:
            self._selectChemicalShiftList(chemicalShiftList)

        self.setTableNotifiers(tableClass=ChemicalShiftList,
                               className=self.attributeName,
                               tableSelection='chemicalShiftList',
                               rowClass=ChemicalShift,
                               cellClassNames=None,
                               tableName='chemicalShiftList', rowName='chemicalShift',
                               changeFunc=self.displayTableForChemicalShift,
                               updateFunc=self._update,
                               pullDownWidget=self.CScolumns,
                               callBackClass=ChemicalShift,
                               selectCurrentCallBack=None,
                               searchCallBack=NmrResidue,
                               moduleParent=moduleParent)

        self._droppedNotifier = GuiNotifier(self,
                                            [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                            self._processDroppedItems)

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
            logger.warning('select: No ChemicalShiftList selected')
            raise ValueError('select: No ChemicalShiftList selected')
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
        if not self._updateSilence:
            self.project.blankNotification()
            objs = self.getSelectedObjects()

            self._dataFrameObject = self.getDataFrameFromList(table=self,
                                                              buildList=chemicalShiftList.chemicalShifts,
                                                              colDefs=self.CScolumns,
                                                              hiddenColumns=self._hiddenColumns)

            # populate from the Pandas dataFrame inside the dataFrameObject
            self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
            self._highLightObjs(objs)
            self.project.unblankNotification()

    def setUpdateSilence(self, silence):
        """
        Silences/unsilences the update of the table until switched again
        """
        self._updateSilence = silence

    def _actionCallback(self, data):
        """
        Notifier DoubleClick action on item in table
        """
        obj = data[CallBack.OBJECT]

        getLogger().debug('ChemicalShiftTable>>> action', obj)

    def _selectionCallback(self, data):
        """
        Notifier Callback for selecting a row in the table
        """
        obj = data[CallBack.OBJECT]

        getLogger().debug('ChemicalShiftTable>>> selection', obj)
        return

        selected = data[CallBack.OBJECT]

        if selected:
            if self.multiSelect:  #In this case selected is a List!!
                if isinstance(selected, list):
                    obj = selected
            else:
                obj = selected[0]
        else:
            obj = None

        self.current.chemicalShift = obj
        ChemicalShiftTableModule.currentCallback = {'object': self.chemicalShiftList, 'table': self}

        if obj:  # should presumably always be the case
            chemicalShift = obj
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

    @staticmethod
    def _stLamFloat(row, name):
        """
        CCPN-INTERNAL: used to display Table
        """
        try:
            return float(getattr(row, name))
        except:
            return None

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        # self.clearTableNotifiers()
        self._chemicalShiftListPulldown.unRegister()
        super()._close()
