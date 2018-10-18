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
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.QuickTable import QuickTable, QuickTableFrame
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Blank import Blank
from ccpn.ui.gui.lib.Strip import navigateToNmrResidueInDisplay, _getCurrentZoomRatio
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from PyQt5 import QtGui, QtWidgets, QtCore
from pyqtgraph import dockarea
from pyqtgraph.dockarea import DockArea
from pyqtgraph.dockarea.DockArea import TempAreaWindow
from ccpn.util.Logging import getLogger
import numpy as np
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame

logger = getLogger()
ALL = '<all>'


class NmrResidueTableModule(CcpnModule):
    """
    This class implements the module by wrapping a NmrResidueTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    className = 'NmrResidueTableModule'

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='NmrResidue Table', nmrChain=None):
        """
        Initialise the Module widgets
        """
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            displayText = [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
        else:
            self.application = None
            self.project = None
            self.current = None
            displayText = []

        # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
        # backBoneAssignment modules
        self._NTSwidget = Widget(self.settingsWidget, setLayout=True,
                                 grid=(0, 0), vAlign='top', hAlign='left')
        #self._NTSwidget = self.settingsWidget

        # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
        # underpinning the addNotifier call do not allow for it either
        colwidth = 140
        self.displaysWidget = ListCompoundWidget(self._NTSwidget,
                                                 grid=(0, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                 vPolicy='minimal',
                                                 #minimumWidths=(colwidth, 0, 0),
                                                 fixedWidths=(colwidth, colwidth, colwidth),
                                                 orientation='left',
                                                 labelText='Display(s):',
                                                 tipText='SpectrumDisplay modules to respond to double-click',
                                                 texts=[ALL] + displayText)
        self.displaysWidget.setFixedHeights((None, None, 40))
        self.displaysWidget.pulldownList.set(ALL)
        self.displaysWidget.setPreSelect(self._fillDisplayWidget)

        self.sequentialStripsWidget = CheckBoxCompoundWidget(
                self._NTSwidget,
                grid=(1, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Show sequential strips:',
                checked=False
                )

        self.markPositionsWidget = CheckBoxCompoundWidget(
                self._NTSwidget,
                grid=(2, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Mark positions:',
                checked=True
                )
        self.autoClearMarksWidget = CheckBoxCompoundWidget(
                self._NTSwidget,
                grid=(3, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Auto clear marks:',
                checked=True
                )

        # initialise the table
        self.nmrResidueTable = NmrResidueTable(parent=self.mainWidget,
                                               mainWindow=self.mainWindow,
                                               moduleParent=self,
                                               setLayout=True,
                                               actionCallback=self.navigateToNmrResidueCallBack,
                                               grid=(0, 0))

        if nmrChain is not None:
            self.selectNmrChain(nmrChain)

        # install the event filter to handle maximising from floated dock
        self.installMaximiseEventHandler(self._maximise, self._closeModule)
        # self.mainWidget.layout().setVerticalSpacing(0)

    def _fillDisplayWidget(self):
        list = ['> select-to-add <'] + [ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
        self.displaysWidget.pulldownList.setData(texts=list)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.nmrResidueTable._maximise()

    def selectNmrChain(self, nmrChain=None):
        """
        Manually select an NmrChain from the pullDown
        """
        self.nmrResidueTable._selectNmrChain(nmrChain)

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

    # def navigateToNmrResidue(self, nmrResidue, row=None, col=None):
    def navigateToNmrResidueCallBack(self, data):
        """
        Navigate in selected displays to nmrResidue; skip if none defined
        """
        from ccpn.core.lib.CallBack import CallBack

        nmrResidue = data[CallBack.OBJECT]

        logger.debug('nmrResidue=%s' % (nmrResidue.id))

        displays = self._getDisplays()
        if len(displays) == 0:
            logger.warning('Undefined display module(s); select in settings first')
            showWarning('startAssignment', 'Undefined display module(s);\nselect in settings first')
            return

        self.application._startCommandBlock('%s.navigateToNmrResidue(project.getByPid(%r))' %
                                            (self.className, nmrResidue.pid))
        try:
            # optionally clear the marks
            if self.autoClearMarksWidget.checkBox.isChecked():
                self.application.ui.mainWindow.clearMarks()

            # navigate the displays
            for display in displays:
                if len(display.strips) > 0:
                    newWidths = []  #_getCurrentZoomRatio(display.strips[0].viewBox.viewRange())
                    navigateToNmrResidueInDisplay(nmrResidue, display, stripIndex=0,
                                                  widths=newWidths,  #['full'] * len(display.strips[0].axisCodes),
                                                  showSequentialResidues=(len(display.axisCodes) > 2) and
                                                                         self.sequentialStripsWidget.checkBox.isChecked(),
                                                  markPositions=self.markPositionsWidget.checkBox.isChecked()
                                                  )
        finally:
            self.application._endCommandBlock()

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.nmrResidueTable._close()
        super(NmrResidueTableModule, self)._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()

    def paintEvent(self, event):
        event.ignore()


class NmrResidueTable(QuickTable):
    """
    Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
    """
    className = 'NmrResidueTable'
    attributeName = 'nmrChains'

    OBJECT = 'object'
    TABLE = 'table'

    @staticmethod
    def _nmrIndex(nmrRes):
        """
        CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            return nmrRes.nmrChain.nmrResidues.index(nmrRes)
        except:
            return None

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
                 checkBoxCallback=None, nmrChain=None, multiSelect=False,
                 **kwds):
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

        self.moduleParent = moduleParent
        # self._widget = Widget(parent=parent, **kwds)

        # parent.getLayout().setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)

        self._widgetScrollArea = ScrollArea(parent, setLayout=True, grid=(0, 0), gridSpan=(1, 1))
        self._widgetScrollArea.setWidgetResizable(True)
        # self._widgetScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self._widgetScrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self._widget = Frame(setLayout=True, showBorder=False)
        self._widgetScrollArea.setWidget(self._widget)

        self._widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # # self._widget.setStyleSheet("""ScrollArea { border: 0px; }""")
        # self._widget.getLayout().setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        # self._widgetFrame.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)

        # parent.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.MinimumExpanding)


        self._nmrChain = None
        if actionCallback is None:
            actionCallback = self.defaultActionCallback

        NmrResidueTable.project = self.project

        # create the column objects
        self.NMRcolumns = ColumnClass([
            ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None),
            ('Index', lambda nmrResidue: NmrResidueTable._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None),
            # ('Index',      lambda nmrResidue: nmrResidue.nmrChain.nmrResidues.index(nmrResidue), 'Index of NmrResidue in the NmrChain', None),
            # ('NmrChain',   lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain id', None),
            ('Pid', lambda nmrResidue: nmrResidue.pid, 'Pid of NmrResidue', None),
            ('_object', lambda nmrResidue: nmrResidue, 'Object', None),
            ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None),
            ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None),
            ('NmrAtoms', lambda nmrResidue: NmrResidueTable._getNmrAtomNames(nmrResidue), 'NmrAtoms in NmrResidue', None),
            ('Peak count', lambda nmrResidue: '%3d ' % NmrResidueTable._getNmrResiduePeakCount(nmrResidue)
             , 'Number of peaks assigned to NmrResidue', None),
            ('Comment', lambda nmr: NmrResidueTable._getCommentText(nmr), 'Notes',
             lambda nmr, value: NmrResidueTable._setComment(nmr, value))
            ])

        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback

        # GWV: Not sure why spaces are needed, as _setWidgetHeight will do fine
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self.ncWidget = NmrChainPulldown(parent=self._widget,
                                         project=self.project, default=0,  #first NmrChain in project (if present)
                                         grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                         showSelectName=True,
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=self._selectionPulldownCallback
                                         )
        # self.spacer = Spacer(self._widget, 5, 5,
        #                      QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
        #                      grid=(2, 50), gridSpan=(1, 1))
        self._setWidgetHeight(30)
        self.ncWidget.setFixedSize(self.ncWidget.sizeHint())
        # self.ncWidget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        # self._widget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

        # initialise the currently attached dataFrame
        self._hiddenColumns = ['Pid']
        self.dataFrameObject = None

        # initialise the table
        QuickTable.__init__(self, parent=parent,
                            mainWindow=self.mainWindow,
                            dataFrameObject=None,
                            setLayout=True,
                            autoResize=True, multiSelect=multiSelect,
                            actionCallback=actionCallback,
                            selectionCallback=selectionCallback,
                            checkBoxCallback=checkBoxCallback,
                            grid=(3, 0), gridSpan=(1, 6),
                            enableDelete=True
                            )

        # Notifier object to update the table if the nmrChain changes
        # self._chainNotifier = None
        # self._residueNotifier = None
        # self._atomNotifier = None
        # self._selectOnTableCurrentNmrResiduesNotifier = None

        # TODO: see how to handle peaks as this is too costly at present
        # Notifier object to update the table if the peaks change
        self._peakNotifier = None
        # self._updateSilence = False  # flag to silence updating of the table
        # self._setNotifiers()

        if nmrChain is not None:
            self._selectNmrChain(nmrChain)

        self.setTableNotifiers(tableClass=NmrChain,
                               className=self.attributeName,
                               tableSelection='_nmrChain',  # _nmrChain.nmrResidues
                               rowClass=NmrResidue,
                               cellClassNames=[(NmrAtom, 'nmrResidue')],  # doesn't change anything
                               tableName='nmrChain', rowName='nmrResidue',
                               changeFunc=self.displayTableForNmrChain,
                               updateFunc=self._update,
                               pullDownWidget=self.ncWidget,
                               callBackClass=NmrResidue,
                               selectCurrentCallBack=self._selectOnTableCurrentNmrResiduesNotifierCallback)

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, NmrChain, self.ncWidget)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)
        widget.setFixedSize(widget.sizeHint())
        self._widget.setFixedSize(self._widget.sizeHint())

    def addWidgetToPos(self, widget, row=0, col=2, rowSpan=1, colSpan=1, overrideMinimum=False):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2 and not overrideMinimum:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, row, col, rowSpan, colSpan)
        widget.setFixedSize(widget.sizeHint())
        self._widget.setFixedSize(self._widget.sizeHint())

    def _setWidgetHeight(self, height):
        self._widget.setFixedHeight(height)

    def _selectNmrChain(self, nmrChain=None):
        """
        Manually select a NmrChain from the pullDown
        """
        if nmrChain is None:
            logger.warning('select: No NmrChain selected')
            raise ValueError('select: No NmrChain selected')
        else:
            if not isinstance(nmrChain, NmrChain):
                logger.warning('select: Object is not of type NmrChain')
                raise TypeError('select: Object is not of type NmrChain')
            else:
                for widgetObj in self.ncWidget.textList:
                    if nmrChain.pid == widgetObj:
                        self._nmrChain = nmrChain
                        self.ncWidget.select(self._nmrChain.pid)

    def defaultActionCallback(self, nmrResidue, *args):
        """
        default Action Callback if not defined in the parent Module
        If current strip contains the double clicked nmrResidue will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

        self.application.ui.mainWindow.clearMarks()
        if self.current.strip is not None:
            strip = self.current.strip
            newWidths = _getCurrentZoomRatio(strip.viewBox.viewRange())
            navigateToNmrResidueInDisplay(nmrResidue, strip.spectrumDisplay, stripIndex=0,
                                          widths=None)
            # widths=['default'] * len(strip.axisCodes))

        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    def displayTableForNmrChain(self, nmrChain):
        """
        Display the table for all NmrResidue's of nmrChain
        """
        self.ncWidget.select(nmrChain.pid)
        self._update(nmrChain)

    # def _updateChainCallback(self, data):
    #   """
    #   Notifier callback for updating the table
    #   """
    #   thisChainList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the chainList
    #   nmrChain = data[Notifier.OBJECT]
    #
    #   if self._nmrChain in thisChainList:
    #     trigger = data[Notifier.TRIGGER]
    #     if nmrChain.pid == self.ncWidget.getText() and trigger == Notifier.DELETE:
    #
    #       self.clear()
    #
    #     elif nmrChain.pid == self.ncWidget.getText() and trigger == Notifier.CHANGE:
    #
    #       self.displayTableForNmrChain(nmrChain)
    #
    #     elif trigger == Notifier.RENAME:
    #       if nmrChain == self._nmrChain:
    #         self.displayTableForNmrChain(nmrChain)
    #
    #   else:
    #     self.clear()
    #
    #   logger.debug('>updateCallback>', data['notifier'], self._nmrChain, data['trigger'], data['object'], self._updateSilence)
    #
    # def _updateResidueCallback(self, data):
    #   """
    #   Notifier callback for updating the table for change in nmrResidues
    #   """
    #   thisChainList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the chainList
    #   nmrResidue = data[Notifier.OBJECT]
    #   trigger = data[Notifier.TRIGGER]
    #
    #   if self._nmrChain in thisChainList and nmrResidue.nmrChain.pid == self.ncWidget.getText():
    #     # is the nmrResidue in the visible list
    #     # TODO:ED move these into the table class
    #
    #     if trigger == Notifier.DELETE:
    #
    #         # remove item from self._dataFrameObject
    #
    #       self._dataFrameObject.removeObject(nmrResidue)
    #
    #     elif trigger == Notifier.CREATE:
    #
    #       # insert item into self._dataFrameObject
    #
    #       if self._nmrChain.nmrResidues and len(self._nmrChain.nmrResidues) > 1:
    #         self._dataFrameObject.appendObject(nmrResidue)
    #       else:
    #         self._update(self._nmrChain)
    #
    #     elif trigger == Notifier.CHANGE:
    #
    #       # modify the line in the table
    #       self._dataFrameObject.changeObject(nmrResidue)
    #
    #     elif trigger == Notifier.RENAME:
    #       # get the old pid before the rename
    #       oldPid = data[Notifier.OLDPID]
    #
    #       # modify the oldPid in the objectList, change to newPid
    #       self._dataFrameObject.renameObject(nmrResidue, oldPid)
    #
    #   logger.debug('>updateResidueCallback>', data['notifier'], self._nmrChain, data['trigger'], data['object'], self._updateSilence)
    #
    # def _updateAtomCallback(self, data):
    #   """
    #   Notifier callback for updating the table
    #   """
    #   thisChainList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the chainList
    #   nmrAtom = data[Notifier.OBJECT]
    #   nmrResidue = nmrAtom.nmrResidue
    #
    #   if self._nmrChain in thisChainList and nmrResidue.nmrChain.pid == self.ncWidget.getText():
    #     # change the dataFrame for the updated nmrAtom
    #     self._dataFrameObject.changeObject(nmrResidue)
    #
    #   logger.debug('>updateCallback>', data['notifier'], self._nmrChain, data['trigger'], data['object'], self._updateSilence)

    def _maximise(self):
        """
        refresh the table on a maximise event
        """
        if self._nmrChain:
            self.displayTableForNmrChain(self._nmrChain)
        else:
            self.clear()

    def _update(self, nmrChain):
        """
        Update the table with NmrResidues of nmrChain
        """
        # if not self._updateSilence:
        # # objs = self.getSelectedObjects()
        # self.setObjectsAndColumns(nmrChain.nmrResidues,self.NMRcolumns)
        # # self.setColumns(self.NMRcolumns)
        # # self.setObjects(nmrChain.nmrResidues)
        # # self._highLightObjs(objs)
        # self._selectOnTableCurrentNmrResidues(self.current.nmrResidues)
        # # self.show()

        self.project.blankNotification()
        objs = self.getSelectedObjects()

        self._dataFrameObject = self.getDataFrameFromList(table=self,
                                                          buildList=nmrChain.nmrResidues,
                                                          colDefs=self.NMRcolumns,
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

    def _selectionCallback(self, data):
        """
        Notifier Callback for selecting a row in the table
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

        NmrResidueTableModule.currentCallback = {'object': self._nmrChain, 'table': self}

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting NmrChain
        """
        self._nmrChain = self.project.getByPid(item)
        logger.debug('>selectionPulldownCallback>', item, type(item), self._nmrChain)
        if self._nmrChain is not None:
            self.displayTableForNmrChain(self._nmrChain)
        else:
            self.clearTable()

    def _selectOnTableCurrentNmrResiduesNotifierCallback(self, data):
        """
        callback from a notifier to select the current NmrResidue
        """
        currentNmrResidues = data['value']
        self._selectOnTableCurrentNmrResidues(currentNmrResidues)

    def _selectOnTableCurrentNmrResidues(self, currentNmrResidues):
        """
        highlight  current NmrResidues on the opened table
        """
        if len(currentNmrResidues) > 0:
            self._highLightObjs(currentNmrResidues)
        else:
            self.clearSelection()

    # @staticmethod
    # def _getCommentText(nmrResidue):
    #   """
    #   CCPN-INTERNAL: Get a comment from ObjectTable
    #   """
    #   try:
    #     if nmrResidue.comment == '' or not nmrResidue.comment:
    #       return ''
    #     else:
    #       return nmrResidue.comment
    #   except:
    #     return ''

    # @staticmethod
    # def _setComment(nmrResidue, value):
    #   """
    #   CCPN-INTERNAL: Insert a comment into ObjectTable
    #   """
    #
    #   # why is it blanking a notification here?
    #   # NmrResidueTable.project.blankNotification()
    #   nmrResidue.comment = value
    #   # NmrResidueTable.project.unblankNotification()

    @staticmethod
    def _getNmrAtomNames(nmrResidue):
        """
        Returns a sorted list of NmrAtom names
        """
        return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms]),
                                key=CcpnSorting.stringSortKey))

    @staticmethod
    def _getNmrResiduePeakCount(nmrResidue):
        """
        Returns peak list count
        """
        l1 = [peak for atom in nmrResidue.nmrAtoms for peak in atom.assignedPeaks]
        return len(set(l1))

    # @staticmethod
    # def _getMeanNmrResiduePeaksShifts(nmrResidue):
    #   deltas = []
    #   peaks = nmrResidue.nmrAtoms[0].assignedPeaks
    #   for i, peak in enumerate(peaks):
    #     deltas += [
    #       (((peak.position[0] - peaks[0].position[0]) * 7) ** 2 + (peak.position[1] - peaks[0].position[1]) ** 2) ** 0.5,]
    #   if not None in deltas and deltas:
    #     return round(float(np.mean(deltas)),3)
    #   return

    # def _setNotifiers(self):
    #   """
    #   Set a Notifier to call when an object is created/deleted/renamed/changed
    #   rename calls on name
    #   change calls on any other attribute
    #   """
    #   self._clearNotifiers()
    #   self._chainNotifier = Notifier(self.project
    #                                     , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
    #                                     , NmrChain.__name__
    #                                     , self._updateChainCallback)
    #   self._residueNotifier = Notifier(self.project
    #                                     , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
    #                                     , NmrResidue.__name__
    #                                     , self._updateResidueCallback
    #                                     , onceOnly=True)
    #   self._atomNotifier = Notifier(self.project
    #                                     , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
    #                                     , NmrAtom.__name__
    #                                     , self._updateAtomCallback
    #                                     , onceOnly=True)
    #   # very slow
    #   # self._peakNotifier = Notifier(self.project
    #   #                               , [Notifier.DELETE, Notifier.CREATE, Notifier.CHANGE]
    #   #                               , 'Peak'
    #   #                               , self._updateCallback
    #   #                               , onceOnly = True
    #   #                               )
    #
    #   self._selectOnTableCurrentNmrResiduesNotifier = Notifier(self.current
    #                                                      , [Notifier.CURRENT]
    #                                                      , targetName='nmrResidues'
    #                                                      , callback=self._selectOnTableCurrentNmrResiduesNotifierCallback)
    #
    # def _clearNotifiers(self):
    #   """
    #   clean up the notifiers
    #   """
    #   if self._chainNotifier is not None:
    #     self._chainNotifier.unRegister()
    #   if self._residueNotifier is not None:
    #     self._residueNotifier.unRegister()
    #   if self._atomNotifier is not None:
    #     self._atomNotifier.unRegister()
    #   if self._peakNotifier is not None:
    #     self._peakNotifier.unRegister()
    #   if self._selectOnTableCurrentNmrResiduesNotifier is not None:
    #     self._selectOnTableCurrentNmrResiduesNotifier.unRegister()

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        self.clearTableNotifiers()

    def _getPullDownSelection(self):
        return self.ncWidget.getText()

    def _selectPullDown(self, value):
        self.ncWidget.select(value)
