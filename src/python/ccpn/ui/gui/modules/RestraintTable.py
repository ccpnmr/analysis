"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.QuickTable import QuickTable
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import RestraintPulldown
from ccpn.core.RestraintList import RestraintList
from ccpn.core.Restraint import Restraint
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier

from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot


logger = getLogger()
ALL = '<all>'


class RestraintTableModule(CcpnModule):
    """
    This class implements the module by wrapping a restaintsTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'RestraintTableModule'

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='Restraint Table', restraintList=None):
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

        # settings
        self._RTwidget = StripPlot(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                   includePeakLists=self.includePeakLists,
                                   includeNmrChains=self.includeNmrChains,
                                   includeSpectrumTable=self.includeSpectrumTable,
                                   grid=(0, 0))

        # main window
        self.restraintTable = RestraintTable(parent=self.mainWidget,
                                             mainWindow=self.mainWindow,
                                             moduleParent=self,
                                             setLayout=True,
                                             grid=(0, 0))

        if restraintList is not None:
            self.selectRestraintList(restraintList)

        # install the event filter to handle maximising from floated dock
        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.restraintTable._maximise()

    def selectRestraintList(self, restraintList=None):
        """
        Manually select a StructureEnsemble from the pullDown
        """
        self.restraintTable._selectRestraintList(restraintList)

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
        self.restraintTable._close()
        super()._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class RestraintTable(QuickTable):
    """
    Class to present a RestraintTable pulldown list, wrapped in a Widget
    """
    className = 'RestraintTable'
    attributeName = 'restraintLists'

    OBJECT = 'object'
    TABLE = 'table'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, restraintList=None, **kwds):
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

        parent.getLayout().setHorizontalSpacing(0)
        self._widgetScrollArea = ScrollArea(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self._widgetScrollArea.setWidgetResizable(True)
        self._widget = Widget(parent=self._widgetScrollArea, setLayout=True)
        self._widgetScrollArea.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        RestraintTable.project = self.project

        kwds['setLayout'] = True  ## Assure we have a layout with the widget
        self.restraintList = None

        # create the column objects
        self.RLcolumns = ColumnClass([('#', '_key', 'Restraint Id', None),
                                      ('Pid', lambda restraint: restraint.pid, 'Pid of integral', None),
                                      ('_object', lambda restraint: restraint, 'Object', None),
                                      ('Atoms', lambda restraint: RestraintTable._getContributions(restraint),
                                       'Atoms involved in the restraint', None),
                                      ('Target Value.', 'targetValue', 'Target value for the restraint', None),
                                      ('Upper Limit', 'upperLimit', 'Upper limit for the restraint', None),
                                      ('Lower Limit', 'lowerLimit', 'Lower limit or the restraint', None),
                                      ('Error', 'error', 'Error on the restraint', None),
                                      ('Peaks', lambda restraint: '%3d ' % RestraintTable._getRestraintPeakCount(restraint),
                                       'Number of peaks used to derive this restraint', None),
                                      # ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
                                      ('Comment', lambda restraint: RestraintTable._getCommentText(restraint), 'Notes',
                                       lambda restraint, value: RestraintTable._setComment(restraint, value))
                                      ])  # [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

        row = 0
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self.rtWidget = RestraintPulldown(parent=self._widget,
                                          project=self.project, default=0,
                                          grid=(row, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                          showSelectName=True,
                                          sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                          callback=self._selectionPulldownCallback)
        row += 1
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, gridHPos + 1), gridSpan=(1, 1))
        self._widgetScrollArea.setFixedHeight(35)  # needed for the correct sizing of the table

        # initialise the currently attached dataFrame
        self._hiddenColumns = ['Pid']
        self.dataFrameObject = None

        # initialise the table
        super().__init__(parent=parent,
                            mainWindow=self.mainWindow,
                            dataFrameObject=None,
                            setLayout=True,
                            autoResize=True,
                            selectionCallback=self._selectionCallback,
                            actionCallback=self._actionCallback,
                            grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        ## populate the table if there are restraintLists in the project
        if restraintList is not None:
            self._selectRestraintList(restraintList)

        self.setTableNotifiers(tableClass=RestraintList,
                               rowClass=Restraint,
                               cellClassNames=None,
                               tableName='restraintList', rowName='restraint',
                               changeFunc=self.displayTableForRestraint,
                               className=self.attributeName,
                               updateFunc=self._update,
                               tableSelection='restraintList',
                               pullDownWidget=self.RLcolumns,
                               callBackClass=Restraint,
                               selectCurrentCallBack=None,
                               moduleParent=moduleParent)

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

    def _getPullDownSelection(self):
        return self.rtWidget.getText()

    def _selectPullDown(self, value):
        self.rtWidget.select(value)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, RestraintList, self.rtWidget)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

    def _selectRestraintList(self, restraintList=None):
        """
        Manually select a restraintList from the pullDown
        """
        if restraintList is None:
            logger.debug('select: No RestraintList selected')
            raise ValueError('select: No RestraintList selected')
        else:
            if not isinstance(restraintList, RestraintList):
                logger.debug('select: Object is not of type RestraintList')
                raise TypeError('select: Object is not of type RestraintList')
            else:
                for widgetObj in self.rtWidget.textList:
                    if restraintList.pid == widgetObj:
                        self.restraintList = restraintList
                        self.rtWidget.select(self.restraintList.pid)

    def displayTableForRestraint(self, restraintList):
        """
        Display the table for all Restraints"
        """
        self.rtWidget.select(restraintList.pid)
        self._update(restraintList)

    def _updateCallback(self, data):
        """
        Notifier callback for updating the table
        """
        thisRestraintList = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the restraintList
        if self.restraintList in thisRestraintList:
            self.displayTableForRestraint(self.restraintList)
        else:
            self.clear()

    def _maximise(self):
        """
        Redraw the table on a maximise event
        """
        if self.restraintList:
            self.displayTableForRestraint(self.restraintList)
        else:
            self.clear()

    def _update(self, restraintList):
        """
        Update the table
        """
        self.project.blankNotification()
        objs = self.getSelectedObjects()

        self._dataFrameObject = self.getDataFrameFromList(table=self,
                                                          buildList=restraintList.restraints,
                                                          colDefs=self.RLcolumns,
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

    def _selectionCallback(self, data, *args):
        """
        Notifier Callback for selecting a row in the table
        """
        restraint = data[Notifier.OBJECT]

        self.current.restraint = restraint
        RestraintTableModule.currentCallback = {'object': self.restraintList, 'table': self}

    def _actionCallback(self, data, *args):
        """
        Notifier DoubleClick action on item in table
        """
        restraint = data[Notifier.OBJECT]

        logger.debug(str(NotImplemented))

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting restraint from the pull down menu
        """
        self.restraintList = self.project.getByPid(item)
        logger.debug('>selectionPulldownCallback>', item, type(item), self.restraintList)
        if self.restraintList is not None:
            # self.thisDataSet = self._getAttachedDataSet(item)
            self.displayTableForRestraint(self.restraintList)
        else:
            self.clearTable()

    def navigateToRestraintInDisplay(restraint, display, stripIndex=0, widths=None,
                                     showSequentialStructures=False, markPositions=True):
        """
        Notifier Callback for selecting Object from item in the table
        """
        logger.debug('display=%r, nmrResidue=%r, showSequentialResidues=%s, markPositions=%s' %
                     (display.id, restraint.id, showSequentialStructures, markPositions)
                     )
        return None

    @staticmethod
    def _getContributions(restraint):
        """
        CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
        using ChemicalShiftList
        """
        if restraint.restraintContributions[0].restraintItems:
            return ' - '.join(restraint.restraintContributions[0].restraintItems[0])

    @staticmethod
    def _getRestraintPeakCount(restraint):
        """
        CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
        using ChemicalShiftList
        """
        peaks = restraint.peaks
        if peaks:
            return len(peaks)
        else:
            return 0

    def _callback(self):
        """
        CCPN-INTERNAL: Notifier callback inactive
        """
        pass

    # def _close(self):
    #     """
    #     Cleanup the notifiers when the window is closed
    #     """
    #     self.clearTableNotifiers()
