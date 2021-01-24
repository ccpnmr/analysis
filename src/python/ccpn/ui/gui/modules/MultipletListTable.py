"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-01-24 17:58:24 +0000 (Sun, January 24, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.PulldownListsForObjects import MultipletListPulldown
# from ccpn.ui.gui.widgets.Table import ObjectTable, Column, ColumnViewSettings,  ObjectTableFilter
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import ColumnClass, Column
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Multiplet import Multiplet
from ccpn.core.Multiplet import Multiplet
from ccpn.core.NmrAtom import NmrAtom
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.PeakTable import PeakListTableWidget
from ccpn.ui.gui.modules.MultipletPeakTable import MultipletPeakListTableWidget
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Font import getFontHeight
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.core.lib.peakUtils import getPeakPosition, getPeakAnnotation, getPeakLinewidth, getMultipletPosition
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.util.OrderedSet import OrderedSet


logger = getLogger()

MultipletPosUnits = ['ppm', 'Hz']


class MultipletTableModule(CcpnModule):
    """This class implements the module by wrapping a MultipletListTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'MultipletTableModule'

    def __init__(self, mainWindow=None, name='Multiplet Table',
                 multipletList=None, selectFirstItem=False):
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.project
        self.current = mainWindow.application.current
        self.splitter = Splitter(horizontal=True, collapsible=False)
        # mainWidget
        self.peaksFrame = Frame(self.mainWidget, setLayout=True, grid=(0, 1))
        self.peakListTableLabel = Label(self.peaksFrame, 'Peaks:', grid=(0, 0), )
        self.peakListTableLabel.setFixedHeight(getFontHeight())

        self.peakListTable = MultipletPeakListTableWidget(parent=self.peaksFrame,
                                                          mainWindow=self.mainWindow,
                                                          moduleParent=self.peaksFrame,  # just to give a unique id
                                                          setLayout=False,
                                                          multiSelect=True,
                                                          grid=(1, 0))

        self.peakListTable._widgetScrollArea.hide()

        self.multipletListTable = MultipletListTableWidget(parent=self.mainWidget, mainWindow=self.mainWindow,
                                                           moduleParent=self, setLayout=True, multiSelect=False,
                                                           grid=(0, 0))

        if multipletList is not None:
            self.selectMultipletList(multipletList)
        elif selectFirstItem:
            self.multipletListTable.mLwidget.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

        self.splitter.addWidget(self.multipletListTable)
        self.splitter.addWidget(self.peaksFrame)

        # it is beyond explanation how stretchFactor works :)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(0, 1)
        self.mainWidget.getLayout().addWidget(self.splitter)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.multipletListTable._maximise()

    def selectMultipletList(self, multipletList=None):
        """
        Manually select a multipletList from the pullDown
        """
        self.multipletListTable._selectMultipletList(multipletList)

    def _closeModule(self):
        """Re-implementation of closeModule function from CcpnModule to unregister notification """
        self.multipletListTable._close()
        self.peakListTable._close()
        super()._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class MultipletListTableWidget(GuiTable):
    """
    Class to present a multipletList Table
    """
    className = 'MultipletListTable'
    attributeName = 'multipletLists'

    positionsUnit = MultipletPosUnits[0]  #default

    @staticmethod
    def _setFigureOfMerit(obj, value):
        """
        CCPN-INTERNAL: Set figureOfMerit from table
        Must be a floatRatio in range [0.0, 1.0]
        """
        # ejb - why is it blanking a notification here?
        # NmrResidueTable._project.blankNotification()

        # clip and set the figure of merit
        obj.figureOfMerit = min(max(float(value), 0.0), 1.0) if value else None

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, multipletList=None, multiSelect=True,
                 actionCallback=None, selectionCallback=None, **kwds):
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

        if moduleParent:
            self.peakListTable = moduleParent.peakListTable
        MultipletListTableWidget.project = self.project

        self.settingWidgets = None
        self._selectedMultipletList = None
        kwds['setLayout'] = True  ## Assure we have a layout with the widget

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        row = 0
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, 0), gridSpan=(1, 1))

        row += 1
        gridHPos = 0
        self.mLwidget = MultipletListPulldown(parent=self._widget,
                                              mainWindow=self.mainWindow,
                                              grid=(row, gridHPos), gridSpan=(1, 1),
                                              showSelectName=True,
                                              minimumWidths=(0, 100),
                                              sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                              callback=self._pulldownPLcallback)

        ## create widgets for selection of position units
        gridHPos += 1
        self.posUnitPulldownLabel = Label(parent=self._widget, text=' Position Unit', grid=(row, gridHPos))
        gridHPos += 1
        self.posUnitPulldown = PulldownList(parent=self._widget, texts=MultipletPosUnits, callback=self._pulldownUnitsCallback, grid=(row, gridHPos))

        row += 1
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(row, gridHPos + 1), gridSpan=(1, 1))

        self._hiddenColumns = ['Pid', 'Spectrum', 'MultipletList', 'Id']
        self.dataFrameObject = None
        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True, multiSelect=True,
                         actionCallback=actionCallback,
                         selectionCallback=selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        # self.tableMenu.addAction('Copy Multiplets...', self._copyMultiplets)
        self.tableMenu.insertSeparator(self.tableMenu.actions()[0])
        a = self.tableMenu.addAction('Edit Multiplet...', self._editMultiplets)
        self.tableMenu.insertAction(self.tableMenu.actions()[0], a)

        ## populate the table if there are multipletlists in the project
        if multipletList is not None:
            self._selectMultipletList(multipletList)

        self.setTableNotifiers(tableClass=MultipletList,
                               rowClass=Multiplet,
                               cellClassNames=None,
                               tableName='multipletList', rowName='multiplet',
                               changeFunc=self._updateAllModule,
                               className=self.attributeName,
                               updateFunc=self._updateAllModule,
                               tableSelection='_selectedMultipletList',
                               pullDownWidget=self.mLwidget,
                               callBackClass=Multiplet,
                               selectCurrentCallBack=self._selectOnTableCurrentMultipletsNotifierCallback,
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, MultipletList, self.mLwidget)

    def _getTableColumns(self, multipletList):
        """Add default columns  plus the ones according with multipletList.spectrum dimension
         format of column = ( Header Name, value, tipText, editOption)
         editOption allows the user to modify the value content by doubleclick
         """

        columnDefs = []

        # Serial column
        columnDefs.append(('#', 'serial', 'Multiplet serial number', None, None))
        columnDefs.append(('Pid', lambda ml: ml.pid, 'Pid of the Multiplet', None, None))
        columnDefs.append(('_object', lambda ml: ml, 'Object', None, None))

        columnDefs.append(('Spectrum', lambda multiplet: multiplet.multipletList.spectrum.id, 'Spectrum containing the Multiplet', None, None))
        columnDefs.append(('MultipletList', lambda multiplet: multiplet.multipletList.serial, 'MultipletList containing the Multiplet', None, None))
        columnDefs.append(('Id', lambda multiplet: multiplet.serial, 'Multiplet serial', None, None))

        # # Assignment column
        # for i in range(multipletList.spectrum.dimensionCount):
        #     assignTipText = 'NmrAtom assignments of multiplet in dimension %s' % str(i + 1)
        #     columnDefs.append(
        #             ('Assign F%s' % str(i + 1), lambda ml, dim=i: getPeakAnnotation(ml, dim), assignTipText, None, None))

        # Multiplet positions column
        for i in range(multipletList.spectrum.dimensionCount):
            positionTipText = 'Multiplet position in dimension %s' % str(i + 1)
            columnDefs.append(('Pos F%s' % str(i + 1),
                               lambda ml, dim=i, unit=MultipletListTableWidget.positionsUnit: getMultipletPosition(ml, dim, unit),
                               positionTipText, None, '%0.3f'))

        # linewidth column
        for i in range(multipletList.spectrum.dimensionCount):
            linewidthTipTexts = 'Multiplet line width %s' % str(i + 1)
            columnDefs.append(
                    ('LW F%s' % str(i + 1), lambda ml, dim=i: getPeakLinewidth(ml, dim), linewidthTipTexts, None, '%0.3f'))

        # height column
        heightTipText = 'Magnitude of spectrum intensity at multiplet center (interpolated), unless user edited'
        columnDefs.append(('Height', lambda ml: ml.height, heightTipText, None, None))

        # volume column
        volumeTipText = 'Integral of spectrum intensity around multiplet location, according to chosen volume method'
        columnDefs.append(('Volume', lambda ml: ml.volume, volumeTipText, None, None))

        # numPeaks column
        numPeaksTipText = 'Peaks count'
        columnDefs.append(('Peaks count', lambda ml: ml.numPeaks, numPeaksTipText, None, None))

        # figureOfMerit column
        figureOfMeritTipText = 'Figure of merit'
        columnDefs.append(('Merit', lambda ml: ml.figureOfMerit, figureOfMeritTipText,
                           lambda ml, value: self._setFigureOfMerit(ml, value), None))

        # comment column
        commentsTipText = 'Textual notes about the multiplet'
        columnDefs.append(('Comment', lambda ml: self._getCommentText(ml), commentsTipText,
                           lambda ml, value: self._setComment(ml, value), None))

        return ColumnClass(columnDefs)

    ##################   Updates   ##################

    def _maximise(self):
        """
        refresh the table on a maximise event
        """
        self._updateTable()

    def _updateAllModule(self, data=None):
        """Updates the table and the settings widgets"""
        # self.peakListTable.clear()
        self._updateTable()

    def _updateTable(self, ):
        """Display the multiplets on the table for the selected MultipletList.
        Obviously, If the multiplet has not been previously deleted and flagged isDeleted"""

        # self.setObjectsAndColumns(objects=[], columns=[]) #clear current table first
        self._selectedMultipletList = self.project.getByPid(self.mLwidget.getText())

        if self._selectedMultipletList:

            self.populateTable(rowObjects=self._selectedMultipletList.multiplets,
                               columnDefs=self._getTableColumns(self._selectedMultipletList),
                               selectedObjects=self.current.multiplets
                               )
            self._updateMultipletPeaksOnTable()

            # self.project.blankNotification()
            # self._dataFrameObject = self.getDataFrameFromList(table=self,
            #                                                   buildList=self._selectedMultipletList.multiplets,
            #                                                   colDefs=self._getTableColumns(self._selectedMultipletList),
            #                                                   hiddenColumns=self._hiddenColumns)
            #
            # # populate from the Pandas dataFrame inside the dataFrameObject
            # self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
            # self._highLightObjs(self.current.multiplets)
            # multiplet = self.current.multiplet
            # #
            # self._updateMultipletPeaksOnTable()
            # self.project.unblankNotification()

        else:
            self.clear()
            self.peakListTable.clear()
            self.peakListTable._selectedMultipletPeakList = None

    def _selectMultipletList(self, multipletList=None):
        """
        Manually select a MultipletList from the pullDown
        """
        if multipletList is None:
            # logger.warning('select: No MultipletList selected')
            # raise ValueError('select: No MultipletList selected')
            self.mLwidget.selectFirstItem()
        else:
            if not isinstance(multipletList, MultipletList):
                logger.warning('select: Object is not of type MultipletList')
                raise TypeError('select: Object is not of type MultipletList')
            else:
                for widgetObj in self.mLwidget.textList:
                    if multipletList.pid == widgetObj:
                        self._selectedMultipletList = multipletList
                        self.mLwidget.select(self._selectedMultipletList.pid)

    ##################   Widgets callbacks  ##################

    def _getPullDownSelection(self):
        return self.mLwidget.getText()

    def _selectPullDown(self, value):
        self.mLwidget.select(value)
        self._updateTable()

    # def displayTableForMultipletList(self, multipletList):
    #     """
    #     Display the table for all NmrResidue's of nmrChain
    #     """
    #     self.mLwidget.select(multipletList.pid)
    #     self._updateTable(multiplets=multipletList.multiplets)

    def _actionCallback(self, data, *args):
        """ If current strip contains the double clicked multiplet will navigateToPositionInStrip """
        from ccpn.core.PeakList import PeakList
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

        # TODO hack until we have multiplet views
        multiplet = self.current.multiplet
        if multiplet:
            if len(multiplet.peaks) > 0:
                peak = multiplet.peaks[-1]

                if self.current.strip is not None:
                    validPeakListViews = [pp.peakList for pp in self.current.strip.peakListViews if
                                          isinstance(pp.peakList, PeakList)]

                    if peak.peakList in validPeakListViews:
                        widths = None

                        if peak.peakList.spectrum.dimensionCount <= 2:
                            widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                        navigateToPositionInStrip(strip=self.current.strip, positions=multiplet.position, widths=widths)
            else:
                logger.warning('Impossible to navigate to peak position. No peaks in multiplet')
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    def _selectionCallback(self, data, *args):
        """
        set as current the selected multiplets on the table
        """
        multiplets = data[Notifier.OBJECT]
        if multiplets is None:
            self.current.clearMultiplets()
            self.peakListTable.clear()
            self.peakListTable._selectedMultipletPeakList = None
            self.highlightObjects(None)
        else:
            self.current.multiplets = multiplets
            #  show only the current multiplet peaks
            self._populateMultipletPeaksOnTable()
            self._updateMultipletPeaksOnTable()

    def _updateMultipletPeaksOnTable(self):
        if self.current.multiplets:

            peaks = OrderedSet()
            [peaks.add(peak) for mt in self.current.multiplets for peak in mt.peaks]
            peaks = tuple(peaks)
            if len(peaks) > 0:
                peakList = peaks[0].peakList  # needed to create the columns in the peak table

                if peakList:
                    self.peakListTable._selectedMultipletPeakList = self.current.multiplets
                    self.peakListTable._updateTable(useSelectedPeakList=False, peaks=peaks, peakList=peakList)

    def _populateMultipletPeaksOnTable(self):
        """populates a dedicate peak table containing peaks of the current multiplet """

        peaks = OrderedSet()
        [peaks.add(peak) for mt in self.current.multiplets for peak in mt.peaks]
        peaks = tuple(peaks)

        if peaks:
            # peakList may not exist for deleted objects
            peakList = peaks[0].peakList
            if peakList:
                self.peakListTable.populateTable(rowObjects=peaks,
                                                 columnDefs=self.peakListTable._getTableColumns(peakList))

        else:
            self.peakListTable.clear()
            self.peakListTable._selectedMultipletPeakList = None

    def _pulldownUnitsCallback(self, unit):
        # update the table with new units
        self._setPositionUnit(unit)
        self._updateAllModule()
        self.peakListTable._setPositionUnit(unit)
        self._updateMultipletPeaksOnTable()

    def _pulldownPLcallback(self, data):
        self._updateAllModule()

    # def _copyMultiplets(self):
    #     pass

    def _editMultiplets(self):
        from ccpn.ui.gui.popups.EditMultipletPopup import EditMultipletPopup

        multiplets = self.current.multiplets
        if len(multiplets) > 0:
            multiplet = multiplets[-1]
            popup = EditMultipletPopup(parent=self.mainWindow, mainWindow=self.mainWindow, multiplet=multiplet)
        else:
            popup = EditMultipletPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec()
        popup.raise_()

    ##################   Notifiers callbacks  ##################

    def _selectOnTableCurrentMultipletsNotifierCallback(self, data):
        """
        Callback from a notifier to highlight the multiplets on the multiplet table
        :param data:
        """
        currentMultiplets = data['value']
        self._selectOnTableCurrentMultiplets(currentMultiplets)

    def _selectOnTableCurrentMultiplets(self, currentMultiplets):
        """
        Highlight the list of multiplets on the table
        :param currentMultiplets:
        """
        self.highlightObjects(currentMultiplets)

        if len(currentMultiplets) > 0:
            # self._highLightObjs(currentMultiplets)
            self._populateMultipletPeaksOnTable()
        else:
            # self.clearSelection()
            self.peakListTable.clear()
            self.peakListTable._selectedMultipletPeakList = None

    def _setPositionUnit(self, value):
        if value in MultipletPosUnits:
            MultipletListTableWidget.positionsUnit = value
