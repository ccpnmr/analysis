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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-18 13:29:08 +0000 (Thu, March 18, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import IntegralListPulldown
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral
from ccpn.util.Logging import getLogger
from ccpn.core.lib.CallBack import CallBack


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
    def __init__(self, mainWindow=None, name='Integral Table',
                 integralList=None, selectFirstItem=False):
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
        elif selectFirstItem:
            self.integralTable.itWidget.selectFirstItem()

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
        super()._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


class IntegralTable(GuiTable):
    """
    Class to present a IntegralTable pulldown list, wrapped in a Widget
    """
    className = 'IntegralTable'
    attributeName = 'integralLists'

    OBJECT = 'object'
    TABLE = 'table'

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

    @staticmethod
    def _setBaseline(obj, value):
        """
        CCPN-INTERNAL: Edit baseline of integral
        """
        obj.baseline = float(value) if value else None

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, integralList=None, **kwds):
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
        IntegralTable.project = self.project

        kwds['setLayout'] = True  ## Assure we have a layout with the widget
        self.integralList = None

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        figureOfMeritTipText = 'Figure of merit'
        commentsTipText = 'Textual notes about the integral'

        # create the column objects
        self.ITcolumns = ColumnClass([
            ('#', lambda il: il.serial, '', None, None),
            ('Pid', lambda il: il.pid, 'Pid of integral', None, None),
            ('_object', lambda il: il, 'Object', None, None),

            ('Spectrum', lambda il: il.integralList.spectrum.id, 'Spectrum containing the Integral', None, None),
            ('IntegralList', lambda il: il.integralList.serial, 'IntegralList containing the Integral', None, None),
            ('Id', lambda il: il.serial, 'Integral serial', None, None),

            ('Value', lambda il: il.value, '', None, None),
            ('Lower Limit', lambda il: IntegralTable._getLowerLimit(il), '', None, None),
            ('Higher Limit', lambda il: IntegralTable._getHigherLimit(il), '', None, None),
            ('ValueError', lambda il: il.valueError, '', None, None),
            ('Bias', lambda il: il.bias, '', None, None),
            ('FigureOfMerit', lambda il: il.figureOfMerit, figureOfMeritTipText,
             lambda il, value: self._setFigureOfMerit(il, value), None),
            ('Baseline', lambda il: il.baseline, 'Baseline for the integral area', lambda il, value: self._setBaseline(il, value), None),
            ('Slopes', lambda il: il.slopes, '', None, None),
            # ('Annotation', lambda il: il.annotation, '', None, None),
            ('Comment', lambda il: self._getCommentText(il), commentsTipText,
             lambda il, value: self._setComment(il, value), None), ]
                )  #      [Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat)

        # create the table; objects are added later via the displayTableForIntegrals method
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))
        self.itWidget = IntegralListPulldown(parent=self._widget,
                                             mainWindow=self.mainWindow, default=None,
                                             grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                             showSelectName=True,
                                             sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                             callback=self._selectionPulldownCallback)
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 1), gridSpan=(1, 1))

        # initialise the currently attached dataFrame
        self._hiddenColumns = ['Pid', 'Spectrum', 'IntegralList', 'Id']
        self.dataFrameObject = None

        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         multiSelect=True,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

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
                               moduleParent=moduleParent)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

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
            # logger.debug('select: No IntegralList selected')
            # raise ValueError('select: No IntegralList selected')
            self.itWidget.selectFirstItem()
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
        self.populateTable(rowObjects=integralList.integrals,
                           columnDefs=self.ITcolumns
                           )

    def _selectionCallback(self, data, *args):
        """
        Set as current the selected integrals on the table
        """
        integrals = data[CallBack.OBJECT]

        # self._clearRegions()
        if integrals is None:
            self.current.clearIntegrals()
        else:
            self.current.integrals = integrals

    def _actionCallback(self, data):
        """
        Notifier DoubleClick action on item in table
        """
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            integral = objs[0]
        else:
            integral = objs

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
        """
        Callback from a notifier to select the current Integrals
        """
        currentIntegrals = data['value']
        self._selectOnTableCurrentIntegrals(currentIntegrals)

    def _selectOnTableCurrentIntegrals(self, currentIntegrals):
        """
        Highlight current integrals on the opened integral table
        """
        self.highlightObjects(currentIntegrals)

    def _navigateToPosition(self):
        """
        If current strip contains the double clicked peak will navigateToPositionInStrip
        """
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

        integral = self.current.integral
        if self.current.strip is not None:
            widths = None
            try:
                widths = _getCurrentZoomRatio(self.current.strip.viewRange())
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
        super()._close()
