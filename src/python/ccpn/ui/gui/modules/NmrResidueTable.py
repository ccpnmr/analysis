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
__dateModified__ = "$dateModified: 2020-01-28 09:52:40 +0000 (Tue, January 28, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.lib.Strip import navigateToNmrResidueInDisplay, navigateToNmrAtomsInStrip
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot
from ccpnc.clibrary import Clibrary
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QShowEvent, QHideEvent
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget
logger = getLogger()
ALL = '<all>'
_getNmrIndex = Clibrary.getNmrResidueIndex


LINKTOPULLDOWNCLASS = 'linkToPulldownClass'


class NmrResidueTableModule(CcpnModule):
    """
    This class implements the module by wrapping a NmrResidueTable instance
    """
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includeDisplaySettings = False
    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False
    activePulldownClass = NmrChain

    className = 'NmrResidueTableModule'

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='NmrResidue Table',
                 nmrChain=None, selectFirstItem=False):
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

        self.nmrResidueTableSettings = StripPlot(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                                 includeDisplaySettings=self.includeDisplaySettings,
                                                 includePeakLists=self.includePeakLists,
                                                 includeNmrChains=self.includeNmrChains,
                                                 includeSpectrumTable=self.includeSpectrumTable,
                                                 activePulldownClass=self.activePulldownClass,
                                                 grid=(0, 0))

        # initialise the table
        self.nmrResidueTable = NmrResidueTable(parent=self.mainWidget,
                                               mainWindow=self.mainWindow,
                                               moduleParent=self,
                                               setLayout=True,
                                               actionCallback=self.navigateToNmrResidueCallBack,
                                               multiSelect=True,
                                               grid=(0, 0))





        # install the event filter to handle maximising from floated dock
        self.installMaximiseEventHandler(self._maximise, self._closeModule)

        if self.activePulldownClass:
            self._setCurrentPulldown = Notifier(self.current,
                                                [Notifier.CURRENT],
                                                targetName=self.activePulldownClass._pluralLinkName,
                                                callback=self._selectCurrentPulldownClass)

        # put these in a smaller additional class
        if self.activePulldownClass:
            self.nmrResidueTable._activePulldownClass = self.activePulldownClass
            self.nmrResidueTable._activeCheckbox = getattr(self.nmrResidueTableSettings, LINKTOPULLDOWNCLASS, None)

        if nmrChain is not None:
            self.selectNmrChain(nmrChain)
        elif selectFirstItem:
            self.nmrResidueTable.ncWidget.selectFirstItem()
            chain = self.nmrResidueTable.ncWidget.getCurrentObject()
            self.nmrResidueTable._update(chain)


    def _maximise(self):
        """
        Maximise the attached table
        """
        self.nmrResidueTable._maximise()

    def _selectCurrentPulldownClass(self, data):
        """Respond to change in current activePulldownClass
        """
        if self.activePulldownClass and self.nmrResidueTable._activeCheckbox and self.nmrResidueTable._activeCheckbox.isChecked():
            self.selectNmrChain(self.current.nmrChain)

    def selectNmrChain(self, nmrChain=None):
        """
        Manually select an NmrChain from the pullDown
        """
        self.nmrResidueTable._selectNmrChain(nmrChain)

    def _getDisplays(self):
        """Return list of displays to navigate - if needed
        """
        displays = []
        # check for valid displays
        if self.nmrResidueTableSettings.displaysWidget:
            gids = self.nmrResidueTableSettings.displaysWidget.getTexts()
            if len(gids) == 0:
                return displays

            if self.includeDisplaySettings:
                if ALL in gids:
                    displays = self.application.ui.mainWindow.spectrumDisplays
                else:
                    displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        else:
            if self.current.strip:
                displays.append(self.current.strip.spectrumDisplay)

        return displays

    # def navigateToNmrResidue(self, nmrResidue, row=None, col=None):
    def navigateToNmrResidueCallBack(self, data):
        """Navigate in selected displays to nmrResidue; skip if none defined
        """
        from ccpn.core.lib.CallBack import CallBack

        # handle a single nmrResidue - should always contain an object
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            nmrResidue = objs[0]
        else:
            nmrResidue = objs

        logger.debug('nmrResidue=%s' % str(nmrResidue.id if nmrResidue else None))

        displays = self._getDisplays()
        if len(displays) == 0 and self.nmrResidueTableSettings.displaysWidget:
            logger.warning('Undefined display module(s); select in settings first')
            showWarning('startAssignment', 'Undefined display module(s);\nselect in settings first')
            return

        from ccpn.core.lib.ContextManagers import undoBlock

        with undoBlock():
            # optionally clear the marks
            if self.nmrResidueTableSettings.autoClearMarksWidget.checkBox.isChecked():
                self.application.ui.mainWindow.clearMarks()

            newWidths = []

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

            # # navigate the displays
            # for display in displays:
            #     if len(display.strips) > 0:
            #         newWidths = []  #_getCurrentZoomRatio(display.strips[0].viewBox.viewRange())
            #         navigateToNmrResidueInDisplay(nmrResidue, display, stripIndex=0,
            #                                       widths=newWidths,  #['full'] * len(display.strips[0].axisCodes),
            #                                       showSequentialResidues=(len(display.axisCodes) > 2) and
            #                                                              self.nmrResidueTableSettings.sequentialStripsWidget.checkBox.isChecked(),
            #                                       markPositions=self.nmrResidueTableSettings.markPositionsWidget.checkBox.isChecked()
            #                                       )

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self.nmrResidueTable._close()
        self.nmrResidueTableSettings._cleanupWidget()
        super()._closeModule()

    def close(self):
        """Close the table from the commandline
        """
        self._closeModule()

    @staticmethod  # has to be a static method
    def onDestroyed(widget):
        # print("DEBUG on destroyed:", widget)
        widget.self.nmrResidueTable._close()
        widget.nmrResidueTableSettings._cleanupWidget()

    def paintEvent(self, event):
        event.ignore()


class NmrResidueTable(GuiTable):
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
            return _getNmrIndex(nmrRes)
            # return nmrRes.nmrChain.nmrResidues.index(nmrRes)                # ED: THIS IS VERY SLOW
        except Exception as es:
            return None

    @staticmethod
    def _nmrLamInt(row, name):
        """
        CCPN-INTERNAL: Insert an int into ObjectTable
        """
        try:
            return int(getattr(row, name))
        except:
            return None


    class ScrollBarVisibilityWatcher(QObject):

        def __init__(self,table,corner):
            super().__init__()
            self._corner = corner
            self._table = table
            horizontalScrollBar = self._getHorizontalScrollBar(table)
            verticalScrollBar = self._getVerticalScrollBar(table)

            horizontalScrollBar.installEventFilter(self)
            verticalScrollBar.installEventFilter(self)

            self.scrollBarChanged( horizontalScrollBar, horizontalScrollBar.isVisible(),
                                   verticalScrollBar, verticalScrollBar.isVisible(), self._table)





        def eventFilter(self, watched, event):

            show = None
            if isinstance(event,QShowEvent):
                show = True
            elif isinstance(event, QHideEvent):
                show = False

            if show is not None:

                self._doScrollBarChange(show, watched)

            return super().eventFilter(watched,event)

        def _doScrollBarChange(self, show, watched):
            horizontalScrollBar = self._getHorizontalScrollBar(self._table)
            verticalScrollBar = self._getVerticalScrollBar(self._table)
            if watched == horizontalScrollBar:
                horizontalVisible = show
                verticalVisible = verticalScrollBar is not None and verticalScrollBar.isVisible()
            elif watched == verticalScrollBar:
                horizontalVisible = horizontalScrollBar is not None and horizontalScrollBar.isVisible()
                verticalVisible = show
            else:
                raise Exception("scroll bar watcher recieved a object that wasn't watched %s" % repr(watched))
            self.scrollBarChanged(horizontalScrollBar, horizontalVisible, verticalScrollBar, verticalVisible, self._table)

        def _getHorizontalScrollBar(self, watched):
            return watched.horizontalScrollBar()

        def _getVerticalScrollBar(self, watched):
            return watched.verticalScrollBar()

        def scrollBarChanged(self, horizontal, horizontalVisible, vertical, verticalVisible, parent):
            if horizontalVisible and verticalVisible:
                self._table.setCornerWidget(self._corner)
            else:
                self._table.setCornerWidget(None)

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
                 checkBoxCallback=None, _pulldownKwds=None, nmrChain=None, multiSelect=False,
                 **kwds):
        """
        Initialise the widgets for the module. kwds passed to the scrollArea widget
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

        # strange, need to do this when using scrollArea, but not a Widget
        parent.getLayout().setHorizontalSpacing(0)
        self._widgetScrollArea = ScrollArea(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self._widgetScrollArea.setWidgetResizable(True)
        self._widgetScrollArea.setStyleSheet('''
                                    margin-left : 2px;
                                    margin-right : 2px;
                                    padding : 2px''')
        self._widget = Widget(parent=self._widgetScrollArea, setLayout=True)
        self._widgetScrollArea.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        self._nmrChain = None
        if actionCallback is None:
            actionCallback = self.defaultActionCallback

        NmrResidueTable.project = self.project

        # create the column objects
        self.NMRcolumns = ColumnClass([
            ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None, None),
            ('Index', lambda nmrResidue: NmrResidueTable._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            # ('Index', lambda nmrResidue: NmrResidueTable._nmrLamInt(nmrResidue, 'Index'), 'Index of NmrResidue in the NmrChain', None, None),

            # ('Index',      lambda nmrResidue: nmrResidue.nmrChain.nmrResidues.index(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
            # ('NmrChain',   lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain id', None, None),
            ('Pid', lambda nmrResidue: nmrResidue.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda nmrResidue: nmrResidue, 'Object', None, None),
            ('NmrChain', lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain containing the nmrResidue', None, None),        # just add the nmrChain for clarity
            ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None, None),
            ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None, None),
            ('NmrAtoms', lambda nmrResidue: NmrResidueTable._getNmrAtomNames(nmrResidue), 'NmrAtoms in NmrResidue', None, None),
            ('Peak count', lambda nmrResidue: '%3d ' % NmrResidueTable._getNmrResiduePeakCount(nmrResidue),
             'Number of peaks assigned to NmrResidue', None, None),
            ('Comment', lambda nmr: NmrResidueTable._getCommentText(nmr), 'Notes',
             lambda nmr, value: NmrResidueTable._setComment(nmr, value), None)
            ])

        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self.ncWidget = NmrChainPulldown(parent=self._widget,
                                         mainWindow=self.mainWindow, default=None,  #first NmrChain in project (if present)
                                         grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=self._selectionPulldownCallback,
                                         showSelectName=False, selectNoneText='none',
                                         )
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 1), gridSpan=(1, 1))
        self._setWidgetHeight(35)

        # initialise the currently attached dataFrame
        self._hiddenColumns = ['Pid', 'NmrChain']
        self.dataFrameObject = None

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

        # Notifier object to update the table if the peaks change
        self._peakNotifier = None

        if nmrChain is not None:
            self._selectNmrChain(nmrChain)

        self.setTableNotifiers(tableClass=NmrChain,
                               className=self.attributeName,
                               tableSelection='_nmrChain',
                               rowClass=NmrResidue,
                               cellClassNames=[(NmrAtom, 'nmrResidue')],            #, (Peak, 'assignments')],
                               tableName='nmrChain', rowName='nmrResidue',
                               changeFunc=self.displayTableForNmrChain,
                               updateFunc=self._update,
                               pullDownWidget=self.ncWidget,
                               callBackClass=NmrResidue,
                               selectCurrentCallBack=self._selectOnTableCurrentNmrResiduesNotifierCallback,
                               moduleParent=moduleParent)

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

        # put into subclass
        self._activePulldownClass = None
        self._activeCheckbox = None

        self.setStyleSheet('''
                    NmrResidueTable {border: 1px solid  #a9a9a9;
                    border-bottom-right-radius: 2px;
                    border-bottom-left-radius: 2px;}
                    ''')

        self._corner = QWidget()
        self._corner.setStyleSheet('''
            border-top: 1px solid #a9a9a9;
            border-left: 1px solid #a9a9a9;
        ''')
        self._cornerDisplay = NmrResidueTable.ScrollBarVisibilityWatcher(self, self._corner)

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

    def addWidgetToPos(self, widget, row=0, col=2, rowSpan=1, colSpan=1, overrideMinimum=False, alignment=None):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2 and not overrideMinimum:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, row, col, rowSpan, colSpan)
        if alignment is not None:
            self._widget.getLayout().setAlignment(widget,alignment)
        widget.setFixedSize(widget.sizeHint())
        self._widget.setFixedSize(self._widget.sizeHint())

    def _setWidgetHeight(self, height):
        self._widgetScrollArea.setFixedHeight(height)

    def _selectNmrChain(self, nmrChain=None):
        """
        Manually select a NmrChain from the pullDown
        """
        if nmrChain is None:
            # logger.warning('select: No NmrChain selected')
            # raise ValueError('select: No NmrChain selected')
            self.ncWidget.selectFirstItem()
        else:
            if not isinstance(nmrChain, NmrChain):
                logger.warning('select: Object is not of type NmrChain')
                raise TypeError('select: Object is not of type NmrChain')
            else:
                for widgetObj in self.ncWidget.textList:
                    if nmrChain.pid == widgetObj and self._nmrChain != nmrChain:
                        self._nmrChain = nmrChain
                        self.ncWidget.select(self._nmrChain.pid)

    def defaultActionCallback(self, data):
        """
        default Action Callback if not defined in the parent Module
        If current strip contains the double clicked nmrResidue will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

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

        self.populateTable(rowObjects=nmrChain.nmrResidues,
                           columnDefs=self.NMRcolumns,
                           selectedObjects=self.current.nmrResidues
                           )

        # self.project.blankNotification()
        # objs = self.getSelectedObjects()
        #
        # self._dataFrameObject = self.getDataFrameFromList(table=self,
        #                                                   buildList=nmrChain.nmrResidues,
        #                                                   colDefs=self.NMRcolumns,
        #                                                   hiddenColumns=self._hiddenColumns)
        #
        # # populate from the Pandas dataFrame inside the dataFrameObject
        # self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
        # self._highLightObjs(objs)
        # self.project.unblankNotification()

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
        print('item', item)
        self._nmrChain = self.project.getByPid(item)
        logger.debug('>selectionPulldownCallback>', item, type(item), self._nmrChain)
        if self._nmrChain is not None:
            self.displayTableForNmrChain(self._nmrChain)

            if self._activePulldownClass and self._activeCheckbox and \
                    self._nmrChain != self.current.nmrChain and self._activeCheckbox.isChecked():
                self.current.nmrChain = self._nmrChain
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
        self.highlightObjects(currentNmrResidues)
        # if len(currentNmrResidues) > 0:
        #     self._highLightObjs(currentNmrResidues)
        # else:
        #     self.clearSelection()

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
        return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms if not atom._flaggedForDelete]),
                                key=CcpnSorting.stringSortKey))

    @staticmethod
    def _getNmrResiduePeakCount(nmrResidue):
        """
        Returns peak list count
        """
        l1 = [peak for atom in nmrResidue.nmrAtoms if not atom._flaggedForDelete for peak in atom.assignedPeaks if not peak._flaggedForDelete]
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
    #   self._chainNotifier = Notifier(self.project,
    #                                      [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
    #                                      NmrChain.__name__,
    #                                      self._updateChainCallback)
    #   self._residueNotifier = Notifier(self.project,
    #                                      [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE],
    #                                      NmrResidue.__name__,
    #                                      self._updateResidueCallback,
    #                                      onceOnly=True)
    #   self._atomNotifier = Notifier(self.project,
    #                                      [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
    #                                      NmrAtom.__name__,
    #                                      self._updateAtomCallback,
    #                                      onceOnly=True)
    #   # very slow
    #   # self._peakNotifier = Notifier(self.project,
    #   #                                [Notifier.DELETE, Notifier.CREATE, Notifier.CHANGE],
    #   #                                'Peak',
    #   #                                self._updateCallback,
    #   #                                onceOnly = True
    #   #                               )
    #
    #   self._selectOnTableCurrentNmrResiduesNotifier = Notifier(self.current,
    #                                                       [Notifier.CURRENT],
    #                                                       targetName='nmrResidues',
    #                                                       callback=self._selectOnTableCurrentNmrResiduesNotifierCallback)
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

    # def _close(self):
    #     """
    #     Cleanup the notifiers when the window is closed
    #     """
    #     self.clearTableNotifiers()

    def _getPullDownSelection(self):
        return self.ncWidget.getText()

    def _selectPullDown(self, value):
        self.ncWidget.select(value)

KD = 'Kd'
Deltas = 'Ddelta'

class _CSMNmrResidueTable(NmrResidueTable):
  """
  Custom nmrResidue Table with extra columns used in the ChemicalShiftsMapping Module
  """
  def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
               checkBoxCallback=None, nmrChain=None, **kwds):

    NmrResidueTable.__init__(self, parent=parent, mainWindow=mainWindow,
                             moduleParent=moduleParent,
                             actionCallback=actionCallback,
                             selectionCallback=selectionCallback,
                             checkBoxCallback = checkBoxCallback,
                             nmrChain=nmrChain,
                             multiSelect=True,
                             **kwds)

    self.NMRcolumns = ColumnClass([
        ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None, None),
        ('Pid', lambda nmrResidue:nmrResidue.pid, 'Pid of NmrResidue', None, None),
        ('_object', lambda nmrResidue:nmrResidue, 'Object', None, None),
        ('Index', lambda nmrResidue: NmrResidueTable._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None, None),
        ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None, None),
        ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None, None),
        ('Selected', lambda nmrResidue: _CSMNmrResidueTable._getSelectedNmrAtomNames(nmrResidue), 'NmrAtoms selected in NmrResidue', None, None),
        ('Spectra', lambda nmrResidue: _CSMNmrResidueTable._getNmrResidueSpectraCount(nmrResidue)
         , 'Number of spectra selected for calculating the deltas', None, None),
        (Deltas, lambda nmrResidue: nmrResidue._delta, '', None, None),
        (KD, lambda nmrResidue: nmrResidue._estimatedKd, '', None, None),
        ('Include', lambda nmrResidue: nmrResidue._includeInDeltaShift, 'Include this residue in the Mapping calculation', lambda nmr, value: _CSMNmrResidueTable._setChecked(nmr, value), None),
        # ('Flag', lambda nmrResidue: nmrResidue._flag,  '',  None, None),
        ('Comment', lambda nmr: NmrResidueTable._getCommentText(nmr), 'Notes', lambda nmr, value: NmrResidueTable._setComment(nmr, value), None)
      ])        #[Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)
                # for colName, func, tipText, editValue, columnFormat in self.columnDefs]

    self._widget.setFixedHeight(45)
    self.chemicalShiftsMappingModule = None


  @staticmethod
  def _setChecked(obj, value):
    """
    CCPN-INTERNAL: Insert a comment into GuiTable
    """

    obj._includeInDeltaShift = value
    obj._finaliseAction('change')

  @staticmethod
  def _getNmrResidueSpectraCount(nmrResidue):

    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return nmrResidue.spectraCount
    except:
      return None

  @staticmethod
  def _getSelectedNmrAtomNames(nmrResidue):

    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return ', '.join(nmrResidue.selectedNmrAtomNames)
    except:
      return None

  def _selectPullDown(self, value):
    ''' Used for automatic restoring of widgets '''
    self.ncWidget.select(value)
    try:
      if self.chemicalShiftsMappingModule is not None:
        self.chemicalShiftsMappingModule._updateModule()
    except Exception as e:
      getLogger().warn('Impossible update chemicalShiftsMappingModule from restoring %s' %e)


