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
__dateModified__ = "$dateModified: 2021-11-10 12:56:37 +0000 (Wed, November 10, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5 import QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import RestraintTablePulldown
from ccpn.core.RestraintTable import RestraintTable
from ccpn.core.Restraint import Restraint
from ccpn.core.lib.CallBack import CallBack
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Button import Button
import ccpn.ui.gui.modules.PyMolUtil as pyMolUtil
from ccpn.ui.gui.widgets import MessageDialog


logger = getLogger()
ALL = '<all>'
PymolScriptName = 'Restraint_Pymol_Template.py'


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
    _allowRename = True

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='Restraint Table',
                 restraintTable=None, selectFirstItem=False):
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
                                   includeSequentialStrips=False,
                                   grid=(0, 0))

        # main window
        self.restraintTable = GuiRestraintTable(parent=self.mainWidget,
                                                mainWindow=self.mainWindow,
                                                moduleParent=self,
                                                setLayout=True,
                                                grid=(0, 0))

        if restraintTable is not None:
            self.selectRestraintTable(restraintTable)
        elif selectFirstItem:
            self.restraintTable.rtWidget.selectFirstItem()

        # install the event filter to handle maximising from floated dock
        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.restraintTable._maximise()

    def selectRestraintTable(self, restraintTable=None):
        """
        Manually select a restraintTable from the pullDown
        """
        self.restraintTable._selectRestraintTable(restraintTable)

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.restraintTable._close()
        super()._closeModule()


class GuiRestraintTable(GuiTable):
    """
    Class to present a RestraintTable pulldown list, wrapped in a Widget
    """
    className = 'RestraintTable'
    attributeName = 'restraintTables'

    OBJECT = 'object'
    TABLE = 'table'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, restraintTable=None, **kwds):
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

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        # GuiRestraintTable.project = self.project  # why? ancient...

        kwds['setLayout'] = True  ## Assure we have a layout with the widget
        self.restraintTable = None

        # create the column objects
        self.RLcolumns = ColumnClass([('#', '_key', 'Restraint Id', None, None),
                                      ('Pid', lambda restraint: restraint.pid, 'Pid of integral', None, None),
                                      ('_object', lambda restraint: restraint, 'Object', None, None),
                                      ('Atoms', lambda restraint: GuiRestraintTable._getContributions(restraint),
                                       'Atoms involved in the restraint', None, None),
                                      ('Target Value.', 'targetValue', 'Target value for the restraint', None, None),
                                      ('Upper Limit', 'upperLimit', 'Upper limit for the restraint', None, None),
                                      ('Lower Limit', 'lowerLimit', 'Lower limit or the restraint', None, None),
                                      ('Error', 'error', 'Error on the restraint', None, None),
                                      ('Peaks', lambda restraint: '%3d ' % GuiRestraintTable._getRestraintPeakCount(restraint),
                                       'Number of peaks used to derive this restraint', None, None),
                                      # ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift), None, None)
                                      ('Comment', lambda restraint: GuiRestraintTable._getCommentText(restraint), 'Notes',
                                       lambda restraint, value: GuiRestraintTable._setComment(restraint, value), None)
                                      ])  # [Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)

        row = 0
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self.rtWidget = RestraintTablePulldown(parent=self._widget,
                                               mainWindow=self.mainWindow, default=None,
                                               grid=(row, gridHPos), minimumWidths=(0, 100),
                                               showSelectName=True,
                                               sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                               callback=self._selectionPulldownCallback)
        gridHPos += 1
        self.showOnViewerButton = Button(self._widget, tipText='Show on Molecular Viewer',
                                         icon=Icon('icons/showStructure'),
                                         callback=self._showOnMolecularViewer,
                                         grid=(row, gridHPos), hAlign='l')
        row += 1
        gridHPos += 1
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, gridHPos), gridSpan=(1, 2))
        self._widget.getLayout().setColumnStretch(gridHPos, 2)

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
                         multiSelect=True,
                         actionCallback=self._actionCallback,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        ## populate the table if there are restraintTables in the project
        if restraintTable is not None:
            self._selectRestraintTable(restraintTable)

        self.setTableNotifiers(tableClass=GuiRestraintTable,
                               rowClass=Restraint,
                               cellClassNames=None,
                               tableName='restraintTable', rowName='restraint',
                               changeFunc=self.displayTableForRestraint,
                               className=self.attributeName,
                               updateFunc=self._update,
                               tableSelection='restraintTable',
                               pullDownWidget=self.RLcolumns,
                               callBackClass=Restraint,
                               selectCurrentCallBack=self._selectOnTableCurrentRestraintNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _getPullDownSelection(self):
        return self.rtWidget.getText()

    def _selectPullDown(self, value):
        self.rtWidget.select(value)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, GuiRestraintTable, self.rtWidget)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

    def _selectRestraintTable(self, restraintTable=None):
        """
        Manually select a restraintTable from the pullDown
        """
        if restraintTable is None:
            # logger.debug('select: No RestraintTable selected')
            # raise ValueError('select: No RestraintTable selected')
            self.rtWidget.selectFirstItem()
        else:
            if not isinstance(restraintTable, GuiRestraintTable):
                getLogger().warning(f'select: Object {restraintTable} is not of type RestraintTable')
                return
            else:
                for widgetObj in self.rtWidget.textList:
                    if restraintTable.pid == widgetObj:
                        self.restraintTable = restraintTable
                        self.rtWidget.select(self.restraintTable.pid)

    def displayTableForRestraint(self, restraintTable):
        """
        Display the table for all Restraints"
        """
        self.rtWidget.select(restraintTable.pid)
        self._update(restraintTable)

    def _selectOnTableCurrentRestraintNotifierCallback(self, data):
        """
        callback from a notifier to select the current Restraints
        :param data:
        """
        currentRestraints = data['value']
        self._selectOnTableCurrentRestraints(currentRestraints)

    def _selectOnTableCurrentRestraints(self, currentRestraints):
        """
        highlight  current Restraints on the opened table
        """
        self.highlightObjects(currentRestraints)

    def _showOnMolecularViewer(self):

        restraintTable = self.rtWidget.getSelectedObject()
        restraints = self.getSelectedObjects() or []

        if restraintTable is not None:
            pymolScriptPath = os.path.join(self.application.pymolScriptsPath, PymolScriptName)
            pdbPath = restraintTable.moleculeFilePath
            if pdbPath is None:
                MessageDialog.showWarning('No Molecule File found', 'Add a molecule file path to the RestraintTable from SideBar.')
                return
            pymolScriptPath = pyMolUtil._restraintsSelection2PyMolFile(pymolScriptPath, pdbPath, restraints)
            pyMolUtil.runPymolWithScript(self.application, pymolScriptPath)

        if not restraintTable:
            MessageDialog.showWarning('Nothing to show', 'Select a RestraintTable first')

    def _updateCallback(self, data):
        """
        Notifier callback for updating the table
        """
        thisRestraintTable = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the restraintTable
        if self.restraintTable in thisRestraintTable:
            self.displayTableForRestraint(self.restraintTable)
        else:
            self.clear()

    def _maximise(self):
        """
        Redraw the table on a maximise event
        """
        if self.restraintTable:
            self.displayTableForRestraint(self.restraintTable)
        else:
            self.clear()

    def _update(self, restraintTable):
        """
        Update the table
        """
        self.populateTable(rowObjects=restraintTable.restraints,
                           columnDefs=self.RLcolumns
                           )
        self._highLightObjs(self.current.restraints)

    def _selectionCallback(self, data, *args):
        """
        Notifier Callback for selecting a row in the table
        """
        restraints = self.getSelectedObjects()
        self.current.restraints = restraints
        RestraintTableModule.currentCallback = {'object': self.restraintTable, 'table': self}

    def _actionCallback(self, data, *args):
        """
        Notifier DoubleClick action on item in table
        """
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            restraint = objs[0]
        else:
            restraint = objs

        from ccpn.ui.gui.widgets.MessageDialog import showWarning
        from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
        from ccpn.ui.gui.lib.Strip import _getCurrentZoomRatio, navigateToPositionInStrip

        if restraint and restraint.peaks:
            self.current.peaks = restraint.peaks
            pk = restraint.peaks[0]
            displays = self.moduleParent._RTwidget.displaysWidget.getDisplays()
            autoClear = self.moduleParent._RTwidget.autoClearMarksWidget.isChecked()
            markPositions = self.moduleParent._RTwidget.markPositionsWidget.isChecked()

            with undoBlockWithoutSideBar():
                # optionally clear the marks
                if autoClear:
                    self.mainWindow.clearMarks()

                # navigate the displays
                for display in displays:
                    if display and len(display.strips) > 0 and display.strips[0].spectrumViews:
                        widths = None
                        if pk.peakList.spectrum.dimensionCount <= 2:
                            widths = _getCurrentZoomRatio(display.strips[0].viewRange())
                        navigateToPositionInStrip(strip=display.strips[0],
                                                  positions=pk.position,
                                                  axisCodes=pk.axisCodes,
                                                  widths=widths)
                        if markPositions:
                            display.strips[0]._markSelectedPeaks()

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting restraint from the pull down menu
        """
        self.restraintTable = self.project.getByPid(item)
        logger.debug('>selectionPulldownCallback>', item, type(item), self.restraintTable)
        if self.restraintTable is not None:
            # self.thisDataSet = self._getAttachedDataSet(item)
            self.displayTableForRestraint(self.restraintTable)
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
        CCPN-INTERNAL:  Get the first pair of atoms Ids from the first restraintContribution of a restraint.
        Empty str if not atoms.
        """
        atomPair = GuiRestraintTable.getFirstRestraintAtomsPair(restraint)
        if atomPair and None not in atomPair:
            return ' - '.join([a.id for a in atomPair])
        else:
            return ''

    @staticmethod
    def getFirstRestraintAtomsPair(restraint):
        """ Get the first pair of atoms from the first restraintContribution of a restraint."""
        atomPair = []
        if len(restraint.restraintContributions) > 0:
            if len(restraint.restraintContributions[0].restraintItems) > 0:
                atomPair = [restraint.project.getAtom(x) for x in restraint.restraintContributions[0].restraintItems[0]]
                if all(atomPair):
                    return atomPair
        return atomPair

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
