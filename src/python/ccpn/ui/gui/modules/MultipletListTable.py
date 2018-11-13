"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
# from ccpn.ui.gui.widgets.Table import ObjectTable, Column , ColumnViewSettings,  ObjectTableFilter
from ccpn.ui.gui.widgets.QuickTable import QuickTable
from ccpn.ui.gui.widgets.Column import ColumnClass, Column
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Multiplet import Multiplet
from ccpn.core.Multiplet import Multiplet
from ccpn.core.NmrAtom import NmrAtom
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.PeakTable import PeakListTableWidget
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.core.lib.peakUtils import getPeakPosition, getPeakAnnotation, getPeakLinewidth, getMultipletPosition
from ccpn.ui.gui.widgets.Splitter import Splitter


logger = getLogger()

MultipletPosUnits = ['ppm', 'Hz']


class MultipletTableModule(CcpnModule):
    '''
    This class implements the module by wrapping a MultipletListTable instance
    '''

    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'MultipletTableModule'

    def __init__(self, mainWindow=None, name='Multiplet Table', multipletList=None):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.project
        self.current = mainWindow.application.current
        self.splitter = Splitter(QtCore.Qt.Horizontal)
        # mainWidget
        self.peaksFrame = Frame(self.mainWidget, setLayout=True, grid=(0, 1))
        self.peakListTableLabel = Label(self.peaksFrame, 'Peaks:', grid=(0, 0), )
        self.peakListTableLabel.setFixedHeight(15)

        self.peakListTable = PeakListTableWidget(parent=self.peaksFrame,
                                                 mainWindow=self.mainWindow,
                                                 moduleParent=self,
                                                 setLayout=False,
                                                 grid=(1, 0))

        self.multipletListTable = MultipletListTableWidget(parent=self.mainWidget, mainWindow=self.mainWindow,
                                                           moduleParent=self, setLayout=True,
                                                           grid=(0, 0))

        if multipletList is not None:
            self.selectMultipletList(multipletList)

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

        self.peakListTable._widget.hide()
        self.splitter.addWidget(self.multipletListTable)
        self.splitter.addWidget(self.peaksFrame)
        self.mainWidget.getLayout().addWidget(self.splitter)

        # it is beyond explanation how stretchFactor works :)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(0, 5)

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
        self.multipletListTable.destroy()
        super(MultipletTableModule, self)._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class MultipletListTableWidget(QuickTable):
    """
    Class to present a multipletList Table
    """
    className = 'MultipletListTable'
    attributeName = 'multipletLists'

    positionsUnit = MultipletPosUnits[0]  #default

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, multipletList=None, actionCallback=None, selectionCallback=None, **kwds):
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.moduleParent = moduleParent
        self.peakListTable = self.moduleParent.peakListTable
        MultipletListTableWidget.project = self.project

        self.settingWidgets = None
        self._selectedMultipletList = None
        kwds['setLayout'] = True  ## Assure we have a layout with the widget
        self._widget = Widget(parent=parent, **kwds)

        ## create multipletList table widget
        # ObjectTable.__init__(self, parent=self._widget, setLayout=True, columns=[], objects=[]
        #                      , autoResize=True, multiSelect=True
        #                      , actionCallback=self._actionCallback, selectionCallback=self._setCurrentSpectrumHit
        #                      , grid=(1, 0), gridSpan=(1, 6))

        ## create Pulldown for selection of multipletList
        gridHPos = 0
        self.mLwidget = MultipletListPulldown(parent=self._widget,
                                              project=self.project,
                                              grid=(0, gridHPos), gridSpan=(1, 1),
                                              showSelectName=True,
                                              minimumWidths=(0, 100),
                                              sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                              callback=self._pulldownPLcallback)

        ## create widgets for selection of position units
        gridHPos += 1
        self.posUnitPulldownLabel = Label(parent=self._widget, text=' Position Unit', grid=(0, gridHPos))
        gridHPos += 1
        self.posUnitPulldown = PulldownList(parent=self._widget, texts=MultipletPosUnits, callback=self._pulldownUnitsCallback, grid=(0, gridHPos))

        self._widget.setFixedHeight(30)  # needed for the correct sizing of the table

        self._hiddenColumns = ['Pid']
        self.dataFrameObject = None
        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
        actionCallback = self._actionCallback if actionCallback is None else actionCallback

        QuickTable.__init__(self, parent=parent,
                            mainWindow=self.mainWindow,
                            dataFrameObject=None,
                            setLayout=True,
                            autoResize=True, multiSelect=True,
                            actionCallback=actionCallback,
                            selectionCallback=selectionCallback,
                            grid=(3, 0), gridSpan=(1, 6))

        # self._selectOnTableCurrentMultipletsNotifier = None
        # self._multipletListDeleteNotifier = None
        # self._multipletNotifier = None
        # self._setNotifiers()

        # self.tableMenu.addAction('Copy Multiplets...', self._copyMultiplets)
        self.tableMenu.insertSeparator(self.tableMenu.actions()[0])
        a = self.tableMenu.addAction('Edit Multiplet...', self._editMultiplets)
        self.tableMenu.insertAction(self.tableMenu.actions()[0], a)
        ## populate the table if there are multipletlists in the project
        if multipletList is not None:
            self._selectMultipletList(multipletList)

        self.setTableNotifiers(tableClass=MultipletList,
                               rowClass=Multiplet,
                               cellClassNames=(NmrAtom, 'assignedMultiplets'),
                               tableName='multipletList', rowName='multiplet',
                               changeFunc=self._updateAllModule,
                               className=self.attributeName,
                               updateFunc=self._updateAllModule,
                               tableSelection='_selectedMultipletList',
                               pullDownWidget=self.mLwidget,
                               callBackClass=Multiplet,
                               selectCurrentCallBack=self._selectOnTableCurrentMultipletsNotifierCallback)

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, MultipletList, self.mLwidget)

    def _getTableColumns(self, multipletList):
        '''Add default columns  plus the ones according with multipletList.spectrum dimension
         format of column = ( Header Name, value, tipText, editOption)
         editOption allows the user to modify the value content by doubleclick
         '''

        columnDefs = []

        # Serial column
        columnDefs.append(('#', 'serial', 'Multiplet serial number', None))
        columnDefs.append(('Pid', lambda ml: ml.pid, 'Pid of the Multiplet', None))
        columnDefs.append(('_object', lambda ml: ml, 'Object', None))

        # # Assignment column
        # for i in range(multipletList.spectrum.dimensionCount):
        #     assignTipText = 'NmrAtom assignments of multiplet in dimension %s' % str(i + 1)
        #     columnDefs.append(
        #             ('Assign F%s' % str(i + 1), lambda ml, dim=i: getPeakAnnotation(ml, dim), assignTipText, None))

        # Multiplet positions column
        for i in range(multipletList.spectrum.dimensionCount):
            positionTipText = 'Multiplet position in dimension %s' % str(i + 1)
            columnDefs.append(('Pos F%s' % str(i + 1),
                               lambda ml, dim=i, unit=MultipletListTableWidget.positionsUnit: getMultipletPosition(ml, dim, unit),
                               positionTipText, None))

        # linewidth column
        for i in range(multipletList.spectrum.dimensionCount):
            linewidthTipTexts = 'Multiplet line width %s' % str(i + 1)
            columnDefs.append(
                    ('LW F%s' % str(i + 1), lambda ml, dim=i: getPeakLinewidth(ml, dim), linewidthTipTexts, None))

        # height column
        heightTipText = 'Magnitude of spectrum intensity at multiplet center (interpolated), unless user edited'
        columnDefs.append(('Height', lambda ml: ml.height, heightTipText, None))

        # volume column
        volumeTipText = 'Integral of spectrum intensity around multiplet location, according to chosen volume method'
        columnDefs.append(('Volume', lambda ml: ml.volume, volumeTipText, None))

        # numPeaks column
        numPeaksTipText = 'Peaks count'
        columnDefs.append(('Peaks count', lambda ml: ml.numPeaks, numPeaksTipText, None))

        # figureOfMerit column
        figureOfMeritTipText = 'Figure of merit'
        columnDefs.append(('Merit', lambda ml: ml.figureOfMerit, figureOfMeritTipText, None))

        # comment column
        commentsTipText = 'Textual notes about the multiplet'
        columnDefs.append(('Comment', lambda ml: MultipletListTableWidget._getCommentText(ml), commentsTipText,
                           lambda ml, value: MultipletListTableWidget._setComment(ml, value)))

        return ColumnClass(columnDefs)

    ##################   Updates   ##################

    def _maximise(self):
        """
        refresh the table on a maximise event
        """
        self._updateTable()

    def _updateAllModule(self):
        '''Updates the table and the settings widgets'''
        # self.peakListTable.clear()
        self._updateTable()

    def _updateTable(self, ):
        '''Display the multiplets on the table for the selected MultipletList.
        Obviously, If the multiplet has not been previously deleted and flagged isDeleted'''

        # self.setObjectsAndColumns(objects=[], columns=[]) #clear current table first
        self._selectedMultipletList = self.project.getByPid(self.mLwidget.getText())

        if self._selectedMultipletList:

            self.project.blankNotification()
            self._dataFrameObject = self.getDataFrameFromList(table=self,
                                                              buildList=self._selectedMultipletList.multiplets,
                                                              colDefs=self._getTableColumns(self._selectedMultipletList),
                                                              hiddenColumns=self._hiddenColumns)

            # populate from the Pandas dataFrame inside the dataFrameObject
            self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
            self._highLightObjs(self.current.multiplets)
            multiplet = self.current.multiplet
            #
            self._updateMultipletPeaksOnTable()
            self.project.unblankNotification()
        else:
            self.clear()
            self.peakListTable.clear()

    def _selectMultipletList(self, multipletList=None):
        """
        Manually select a MultipletList from the pullDown
        """
        if multipletList is None:
            logger.warning('select: No MultipletList selected')
            raise ValueError('select: No MultipletList selected')
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

    def displayTableForMultipletList(self, multipletList):
        """
        Display the table for all NmrResidue's of nmrChain
        """
        self.mLwidget.select(multipletList.pid)
        self._updateTable(multiplets=multipletList.multiplets)

    def _actionCallback(self, data, *args):
        ''' If current strip contains the double clicked multiplet will navigateToPositionInStrip '''
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
        else:
            self.current.multiplets = multiplets
            #  show only the current multiplet peaks
            self._populateMultipletPeaksOnTable()
            self._updateMultipletPeaksOnTable()

    def _updateMultipletPeaksOnTable(self):
        if self.current.multiplet:
            peaks = self.current.multiplet.peaks
            if len(peaks) > 0:
                peakList = peaks[-1].peakList  # needed to create the columns in the peak table
                self.peakListTable._updateTable(useSelectedPeakList=False, peaks=peaks, peakList=peakList)

    def _populateMultipletPeaksOnTable(self):
        '''populates a dedicate peak table containing peaks of the current multiplet '''

        multiplet = self.current.multiplet
        if multiplet:
            if len(multiplet.peaks) > 0:
                self.peakListTable._dataFrameObject = self.getDataFrameFromList(table=self,
                                                                                buildList=multiplet.peaks,

                                                                                colDefs=self.peakListTable._getTableColumns(
                                                                                        multiplet.peaks[-1].peakList),

                                                                                hiddenColumns=self.peakListTable._hiddenColumns)
                # populate from the Pandas dataFrame inside the dataFrameObject
                self.peakListTable.setTableFromDataFrameObject(dataFrameObject=self.peakListTable._dataFrameObject)

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
        if len(currentMultiplets) > 0:
            self._highLightObjs(currentMultiplets)
            self._populateMultipletPeaksOnTable()
        else:
            self.clearSelection()
            self.peakListTable.clear()

    # @staticmethod
    # def _getCommentText(multiplet):
    #   if multiplet.comment == '' or not multiplet.comment:
    #     return ' '
    #   else:
    #     return multiplet.comment
    #
    # @staticmethod
    # def _setComment(multiplet, value):
    #   MultipletListTableWidget.project.blankNotification()
    #   multiplet.comment = value
    #   MultipletListTableWidget.project.unblankNotification()

    def _setPositionUnit(self, value):
        if value in MultipletPosUnits:
            MultipletListTableWidget.positionsUnit = value

    def destroy(self):
        "Cleanup of self"
        self.clearTableNotifiers()

    # def _setNotifiers(self):
    #   """
    #   Set a Notifier to call when an object is created/deleted/renamed/changed
    #   rename calls on name
    #   change calls on any other attribute
    #   """
    #   self._selectOnTableCurrentMultipletsNotifier = Notifier(self.current
    #                                                      , [Notifier.CURRENT]
    #                                                      , targetName='multiplets'
    #                                                      , callback=self._selectOnTableCurrentMultipletsNotifierCallback)
    #   # TODO set notifier to trigger only for the selected multipletList.
    #
    #   self._multipletListDeleteNotifier = Notifier(self.project
    #                                           , [Notifier.CREATE, Notifier.DELETE]
    #                                           , 'MultipletList'
    #                                           , self._multipletListNotifierCallback)
    #   self._multipletNotifier =  Notifier(self.project
    #                                  , [Notifier.DELETE, Notifier.CREATE, Notifier.CHANGE]
    #                                  , 'Multiplet', self._multipletNotifierNotifierCallback
    #                                  , onceOnly=True)
    #
    # def _clearNotifiers(self):
    #   """
    #   clean up the notifiers
    #   """
    #   if self._multipletListDeleteNotifier is not None:
    #     self._multipletListDeleteNotifier.unRegister()
    #   if self._multipletNotifier is not None:
    #     self._multipletNotifier.unRegister()
    #   if self._selectOnTableCurrentMultipletsNotifier is not None:
    #     self._selectOnTableCurrentMultipletsNotifier.unRegister()
