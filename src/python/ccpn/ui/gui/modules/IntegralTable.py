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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtGui, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.LinearRegionsPlot import LinearRegionsPlot
# from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.ui.gui.widgets.QuickTable import QuickTable
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import IntegralListPulldown
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral

from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea


logger = getLogger()
ALL = '<all>'


class IntegralTableModule(CcpnModule):
    """
    This class implements the module by wrapping a integralTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'top'

    className = 'IntegralTableModule'

    # we are subclassing this Module, hence some more arguments to the init
    def __init__(self, mainWindow=None, name='Integral Table', integralList=None):
        """
        Initialise the Module widgets
        """
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.integralTable = IntegralTable(parent=self.mainWidget,
                                           mainWindow=self.mainWindow,
                                           moduleParent=self,
                                           setLayout=True,
                                           grid=(0, 0))

        if integralList is not None:
            self.selectIntegralList(integralList)

        # install the event filter to handle maximising from floated dock
        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.integralTable._maximise()

    def selectIntegralList(self, integralList=None):
        """
        Manually select a IL from the pullDown
        """
        self.integralTable._selectIntegralList(integralList)

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.integralTable._close()
        super(IntegralTableModule, self)._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class IntegralTable(QuickTable):
    """
    Class to present a IntegralTable pulldown list, wrapped in a Widget
    """
    className = 'IntegralTable'
    attributeName = 'integralLists'

    OBJECT = 'object'
    TABLE = 'table'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, integralList=None, **kwds):
        """
        Initialise the widgets for the module.
        """
        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.moduleParent = moduleParent
        IntegralTable.project = self.project

        kwds['setLayout'] = True  ## Assure we have a layout with the widget
        self.integralList = None

        # strange, need to do this when using scrollArea, but not a Widget
        parent.getLayout().setHorizontalSpacing(0)
        self._widgetScrollArea = ScrollArea(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self._widgetScrollArea.setWidgetResizable(True)
        self._widget = Widget(parent=self._widgetScrollArea, setLayout=True)
        self._widgetScrollArea.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        # create the column objects
        self.ITcolumns = ColumnClass([
            ('#', lambda integral: integral.serial, '', None),
            ('Pid', lambda integral: integral.pid, 'Pid of integral', None),
            ('_object', lambda integral: integral, 'Object', None),
            ('Value', lambda integral: integral.value, '', None),
            ('Lower Limit', lambda integral: IntegralTable._getLowerLimit(integral), '', None),
            ('Higher Limit', lambda integral: IntegralTable._getHigherLimit(integral), '', None),
            ('ValueError', lambda integral: integral.valueError, '', None),
            ('Bias', lambda integral: integral.bias, '', None),
            ('FigureOfMerit', lambda integral: integral.figureOfMerit, '', None),
            ('Slopes', lambda integral: integral.slopes, '', None),
            ('Annotation', lambda integral: integral.annotation, '', None),
            ('Comment', lambda integral: integral.annotation, '', None), ]
                )  #      [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

        # create the table; objects are added later via the displayTableForIntegrals method
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self.itWidget = IntegralListPulldown(parent=self._widget,
                                             project=self.project, default=0,
                                             grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                             showSelectName=True,
                                             sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                             callback=self._selectionPulldownCallback)
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 1), gridSpan=(1, 1))
        self._widgetScrollArea.setFixedHeight(35)

        # initialise the currently attached dataFrame
        self._hiddenColumns = ['Pid']
        self.dataFrameObject = None

        # initialise the table
        QuickTable.__init__(self, parent=parent,
                            mainWindow=self.mainWindow,
                            dataFrameObject=None,
                            setLayout=True,
                            autoResize=True,
                            selectionCallback=self._selectionCallback,
                            actionCallback=self._actionCallback,
                            multiSelect=True,
                            grid=(3, 0), gridSpan=(1, 6))

        if integralList is not None:
            self._selectIntegralList(integralList)

        self.setTableNotifiers(tableClass=IntegralList,
                               rowClass=Integral,
                               cellClassNames=None,
                               tableName='integralList', rowName='integral',
                               changeFunc=self.displayTableForIntegralList,
                               className=self.attributeName,
                               updateFunc=self._update,
                               tableSelection='integralList',
                               pullDownWidget=self.ITcolumns,
                               callBackClass=Integral,
                               selectCurrentCallBack=self._selectOnTableCurrentIntegralsNotifierCallback,
                               moduleParent=self.moduleParent)

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, IntegralList, self.itWidget)

    def _selectIntegralList(self, integralList=None):
        """
        Manually select a IntegralList from the pullDown
        """
        if integralList is None:
            logger.debug('select: No IntegralList selected')
            raise ValueError('select: No IntegralList selected')
        else:
            if not isinstance(integralList, IntegralList):
                logger.debug('select: Object is not of type IntegralList')
                raise TypeError('select: Object is not of type IntegralList')
            else:
                for widgetObj in self.itWidget.textList:
                    if integralList.pid == widgetObj:
                        self.integralList = integralList
                        self.itWidget.select(self.integralList.pid)

    def _getPullDownSelection(self):
        return self.itWidget.getText()

    def _selectPullDown(self, value):
        self.itWidget.select(value)

    def displayTableForIntegralList(self, integralList):
        """
        Display the table for the IntegralList"
        """
        self.itWidget.select(integralList.pid)
        self._update(integralList)

    def _updateCallback(self, data):
        """
        Notifier callback for updating the table
        """
        thisIntegralList = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the integralList
        if self.integralList in thisIntegralList:
            self.displayTableForIntegralList(self.integralList)
        else:
            self.clearTable()

    def _maximise(self):
        """
        Redraw the table on a maximise event
        """
        if self.integralList:
            self.displayTableForIntegralList(self.integralList)
        else:
            self.clear()

    def _update(self, integralList):
        """
        Update the table
        """
        self.project.blankNotification()
        objs = self.getSelectedObjects()

        self._dataFrameObject = self.getDataFrameFromList(table=self,
                                                          buildList=integralList.integrals,
                                                          colDefs=self.ITcolumns,
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

    def _clearRegions(self):
        strip = self.current.strip
        if strip:
            strip.plotWidget.viewBox._clearIntegralRegions()

    def _showRegions(self):
        strip = self.current.strip
        if strip:
            strip.plotWidget.viewBox._showIntegralLines()

    def _selectionCallback(self, data, *args):
        """
        Set as current the selected integrals on the table
        """
        integrals = data[Notifier.OBJECT]

        # self._clearRegions()
        if integrals is None:
            self.current.clearIntegrals()
        else:
            self.current.integrals = integrals

    def _actionCallback(self, data):
        """
        Notifier DoubleClick action on item in table
        """
        integral = data[Notifier.OBJECT]

        # self._showRegions()
        self._navigateToPosition()

        # logger.debug(str(NotImplemented))

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting integral from the pull down menu
        """
        if item is not None:
            self.integralList = self.project.getByPid(item)
            if self.integralList is not None:
                self.displayTableForIntegralList(self.integralList)
            else:
                self.clearTable()

    def _selectOnTableCurrentIntegralsNotifierCallback(self, data):
        """callback from a notifier to select the current Integrals  """
        currentIntegrals = data['value']
        self._selectOnTableCurrentIntegrals(currentIntegrals)

    def _selectOnTableCurrentIntegrals(self, currentIntegrals):
        """ highlight current integrals on the opened integral table """

        # print(currentIntegrals)
        if len(currentIntegrals) > 0:
            self._highLightObjs(currentIntegrals)
        else:
            self.clearSelection()

    ##### Action callback: Lines on plot

    # def _showLines(self, integral):
    #
    #   if self.application is not None:
    #     self.strip = self.current.strip
    #     if self.strip is not None:
    #       self.plotWidget = self.strip.plotWidget
    #       if len(integral.limits) == 1:
    #         self.linearRegions.setLines(integral.limits[0])
    #       self.plotWidget.addItem(self.linearRegions)

    # def _clearLines(self):
    #   if self.application is not None:
    #     self.strip = self.current.strip
    #     if self.strip is not None:
    #       self.plotWidget = self.strip.plotWidget
    #       self.plotWidget.removeItem(self.linearRegions)
    #
    # def _lineMoved(self):
    #   integral = self.current.integral
    #   values = []
    #   for line in self.linearRegions.lines:
    #       values.append(line.pos().x())
    #   if integral is not None:
    #     integral.limits = [[min(values),max(values)],]

    def _navigateToPosition(self):
        ''' If current strip contains the double clicked peak will navigateToPositionInStrip '''
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

        integral = self.current.integral
        if self.current.strip is not None:
            widths = None
            try:
                widths = _getCurrentZoomRatio(self.current.strip.viewBox.viewRange())
                if len(integral.limits) == 1:
                    positions = integral.limits[0]
                    navigateToPositionInStrip(strip=self.current.strip, positions=positions, widths=widths)
            except Exception as e:
                logger.warning('Impossible to navigate to peak position.', e)
        else:
            logger.warning('Impossible to navigate to peak position. Set a current strip first')

    @staticmethod
    def _getHigherLimit(integral):
        """
        Returns HigherLimit
        """
        # FIXME Wrapper? BUG if limits is None
        if integral is not None:
            if len(integral.limits) > 0:
                limits = integral.limits[0]
                if limits is not None:
                    return float(max(limits))

    @staticmethod
    def _getLowerLimit(integral):
        """
        Returns Lower Limit
        """
        if integral is not None:
            if len(integral.limits) > 0:
                limits = integral.limits[0]
                if limits:
                    return float(min(limits))

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        # self.clearTableNotifiers()
        self._clearRegions()
