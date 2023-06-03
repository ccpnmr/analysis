#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-05-30 14:27:58 +0100 (Tue, May 30, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
import pyqtgraph as pg
import decorator
from PyQt5 import QtWidgets, QtGui, QtCore
from ccpn.ui.gui.widgets._NewBarGraph import BarGraph
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_HIGHLIGHT
from ccpn.ui.gui.guiSettings import getColours
from ccpn.util.Colour import hexToRgb, rgbaRatioToHex
from ccpn.ui.gui.widgets.Font import getFont
from ccpn.util.DataEnum import DataEnum
from typing import Optional, List, Tuple, Any, Sequence, Union
from ccpn.util.Logging import getLogger
from collections import defaultdict
from functools import partial

AllTicks  = 'All Ticks'
MinimalTicks = 'Minimal Ticks'
TICKOPTIONS = [MinimalTicks, AllTicks]

# must preserve the case exactly as it is defined here
_SCATTER = 'scatter'
_LINE = 'line'
_BAR = 'bar'
ERR = 'Err'
X = 'x'
Y = 'y'
COLUMNNAME = 'ColumnName'
XCOLUMNNAME = f'{X}{COLUMNNAME}'
YCOLUMNNAME =  f'{Y}{COLUMNNAME}'
XERRCOLUMNNAME =  f'{X}{ERR}{COLUMNNAME}'
YERRCOLUMNNAME =  f'{Y}{ERR}{COLUMNNAME}'
COLOURCOLUMNNAME = f'colour{COLUMNNAME}'
OBJECTCOLUMNNAME = f'object{COLUMNNAME}'
THRESHOLDCOLUMNNAME = f'threshold{COLUMNNAME}'

class PlotType(DataEnum):
    """
    Definitions for Allowed Plot types
    """
    SCATTER = 0, _SCATTER
    BAR = 1, _BAR
    LINE = 2, _LINE

class MainPlotWidget(Widget):
    """
    MainPlotWidget to plot experimentAnalysis resulting DataTables.
    It contains three main plot kinds: scatters - bars - lines. Either one at the time or together.
    To plot  is necessary a dataframe and define the columns to be plotted.
    To add an extra element call again the plotData method and use the argument clearPlot = False.
    Bars and lines can also plot in the Xaxis strings as values.

    Core hierarchy: viewBox -> plotItem -> axes -> plotWidget -> children items (bar, line... Handlers )
        Viewbox: is the canvas. Is the box that allows internal scaling/panning of children by mouse drag. It also contains signals fired on viewChanges
                       Common built-in methods:
        PlotItem: is the actual plotter.
                      Common built-in methods: plot
        Axes (xAxis, yAxis): the items containing the ticks
                        Common built-in methods: plot
        PlotWidget:
    """
    name = 'MainPlotWidget'
    allowedPlotTypes = PlotType.descriptions()

    def __init__(self, parent, application=None, name=None, title=None, actionCallback=None,
                 selectionCallback=None, hoverCallback=None, lineMovedCallback = None,
                 **kwds):

        super().__init__(parent, setLayout=True, acceptDrops=False, **kwds)
        self.parent = parent
        self.application = application
        self.name = name
        self.title = title
        self.actionCallback = actionCallback
        self._selectionCallback = selectionCallback
        self._hoverCallback = hoverCallback
        self._actionCallback = actionCallback
        self._lineMovedCallback = lineMovedCallback
        self._plottedDataFrames = None


        # Background/canvas items.
        self.viewBox = ViewBox(self)
        self.plotItem = PlotItem(self, name=self.name, labels=None, title=self.title, viewBox=self.viewBox,
                                 axisItems= {'bottom': XAxisItem(self, orientation='bottom'),'left': YAxisItem(self, orientation='left')},
                                 enableMenu=False)
        self.plotWidget = PlotWidget(self, viewBox=self.viewBox, plotItem=self.plotItem)

        layout = self.getLayout()
        layout.addWidget(self.plotWidget, 0, 0, 1, 1)
        layout.setContentsMargins(1, 1, 1, 1)

        # children items and handlers
        self._plottingHandlers = set() # automatically registered (if the registerToParent flag is set to True)
        self.barsHandler = BarsHandler(self, selectionCallback=self._selectionCallback, hoverCallback=self._hoverCallback)
        self.scattersHandler = ScattersHandler(self, selectionCallback=self._selectionCallback, hoverCallback=self._hoverCallback)
        self.thresholdsLineHandler = ThresholdLinesHandler(self, lineMovedCallback=self._lineMovedCallback)
        self.linesHandler = LinesHandler(self, selectionCallback=self._selectionCallback)
        self.errorBarsHandler = ErrorBarsHandler(self)
        self.legendHandler = LegendHandler(self)
        self.selectionBoxHandler = SelectionBoxHandler(self)
        self._postInitOptions()


    ###################################################################
    #########################     Public methods     #########################
    ###################################################################


    def plotData(self,
                 dataFrame,
                 plotName: str,
                 plotType: Union[str, int],
                 xColumnName: str,
                 yColumnName: str,
                 xErrColumnName: str = None,
                 yErrColumnName: str = None,
                 colourColumnName: str = None,
                 errColourColumnName: str = None,
                 thresholdColumnName: str = None,
                 objectColumnName: str = None,
                 clearPlot=True,
                 resetAxes=True,
                 **kwargs):
        """
        Plot data on the main widget.
        :param dataFrame: the source of data as Pandas DataFrame
        :param plotName: name to the plot to be identified.
        :param plotType: one of  'scatter, bar, line'
        :param xColumnName: str. column name in the dataframe. Get the values to be plotted in the xAxis.
        :param yColumnName:  str. column name in the dataframe. Get the values to be plotted in the yAxis.
        :param xErr: str. column name in the dataframe. Column containing the errors for the xAxis. (only scatter)
        :param yErr: str. column name in the dataframe. Column containing the errors for the yAxis.
        :param objectColumnName:  str. column name in the dataframe. Expected a column containing the Pids for V3 core objects. If Given they are used in selection/actions.

        :param clearPlot: bool. True to clean the plot  from previous data before adding any new data.
        :return: Bool. True if successful

        String values are allowed only on Bars/Lines.
        If Strings are given in the xValues, then the dataframe index is used as numeric and the xValues will be the ticks.

        """

        columnNameDict = {k:v for k,v in locals().items() if COLUMNNAME in k}

        ### Check columns are in dataFrame
        if not self._isColumnNamesValid(dataFrame, xColumnName, yColumnName, columnNameDict):
            return False

        ### Check Columns dType are plottable for the plotType
        if not self._isPlotTypeValid(plotType):
            return False

        ###
        if clearPlot:
            self.clearPlot()
        ###  Dispatch data to the relative handler to do the actual plotting
        self._dispatchDataToHandler(dataFrame, plotType=plotType, columnNameDict=columnNameDict )

    def getPlottedDataFrames(self):
        """
        The dataframes currently plotted. Contains only the columns and index as plotted
        :return:
        """
        _plottedDataFrames = self._plottedDataFrames
        return _plottedDataFrames

    @property
    def plottingHandlers(self):
        return list(self._plottingHandlers)

    ############  Graphics behaviours. Zoom and panning  ############

    @property
    def xAxis(self):
        return self.plotItem.getAxis('bottom')

    @property
    def yAxis(self):
        return self.plotItem.getAxis('left')

    def setZoomLimits(self, xMin, xMax, yMin, yMax):
        """
        These arguments prevent the view being zoomed in or
        out too far. This is not a zoom to a region.
        :param xMin: float or int
        :param xMax: float or int
        :param yMin: float or int
        :param yMax: float or int
        :return: None
        """
        self.plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def setPanLimits(self, xMin, xMax, yMin, yMax):
        """
        Set limits that constrain the possible view ranges. This is not a zoom to a region.
        :param xMin: float or int
        :param xMax: float or int
        :param yMin: float or int
        :param yMax: float or int
        :return: None
        """
        self.plotWidget.setLimits(minXRange=xMin, maxXRange=xMax, minYRange=yMin, maxYRange=yMax)

    def setXZoom(self, xMin, xMax, padding=None, update=True):
        """ Set the visible x region of the plot.
        Does not constrain the view. Use setZoomLimits/setPanLimits to restrict the zooming/viewing level"""
        pass

    def setYZoom(self, yMin, yMax, padding=None, update=True):
        """ Set the visible y region of the plot.
        Does not constrain the view. Use setZoomLimits/setPanLimits to restrict the zooming/viewing level"""
        pass

    def setBestPlotLimits(self):
        pass

    def setBestFitXYZoom(self):
        self.plotWidget.autoRange()

    def zoomFull(self):
        """ back-compatibility"""
        self.setBestFitXYZoom()

    def fitYZoom(self):
        """ back-compatibility"""
        self.setBestFitYZoom()

    def fitXZoom(self):
        """ back-compatibility"""
        self.setBestFitXZoom()

    def setBestFitXZoom(self):
        """
        :return:
        """
        pass

    def setBestFitYZoom(self):
        """
        :return:
        """
        pass

    ############  Graphics behaviours. Colours ############

    def setBackgroundColour(self, hexColour):
        """ Set the backgroundColour for the canvas"""
        self.plotWidget.setBackground(hexColour)

    def setAxesColour(self, hexColour, width=1, style=QtCore.Qt.SolidLine):
        """ Set the pen colour for the axes"""
        pen = pg.functions.mkPen(hexColour, width=width, style=style)
        self.xAxis.setPen(pen)
        self.yAxis.setPen(pen)

    def setAxisFonts(self, font):
        """ Set the fonts for the axes"""
        self.xAxis.tickFont = font
        self.yAxis.tickFont = font

    ############  Graphics behaviours. Toggle views ############

    def toggle(self, itemName, setVisible:bool):
        pass

    ############  Closing ############

    def clearPlot(self, excludedItems:list=None):
        self.viewBox.clear()

    def closePlot(self):
        pass


    ####################################################################
    #########################     Private methods     #########################
    ####################################################################

    def _postInitOptions(self):

        self._tickOption = MinimalTicks
        self._setColoursFromPreferences()

    def _registerHandler(self, handler):
        self._plottingHandlers.add(handler)

    def _isColumnNamesValid(self, dataFrame, xColumnName, yColumnName,  otherColumnNames):
        """
        Check if the columnName is present in dataFrame.
        :return: True if all ok.
        """
        if xColumnName not in dataFrame:
            getLogger().warning(f'{self}: Cannot plot {xColumnName}. Mandatory column {xColumnName} not found in data')
            return False
        if yColumnName not in dataFrame:
            getLogger().warning(f'{self}: Cannot plot {yColumnName}. Mandatory column {yColumnName} not found in data')
            return False
        for arg, columnName in otherColumnNames.items():
            if columnName is not None and columnName not in dataFrame:
                getLogger().warning(f'{self}: Cannot plot  by {columnName}. Columns {columnName} not found in data')
        return True

    def _isPlotTypeValid(self, plotType):
        """
        Check if the Plot Type is supported.
        :return: True if ok.
        """
        if not plotType in PlotType.descriptions() or plotType in PlotType.values():
            getLogger().warning(f'{self}: Cannot plot {plotType}. Plot type not supported. Use one of {PlotType.descriptions()}')
            return False
        return True

    def _dispatchDataToHandler(self, dataFrame, plotType, columnNameDict):

        for handler in list(self._plottingHandlers):
            if handler.plotType == plotType or handler.plotType is None:
                handler.items = []
                handler.plotData(dataFrame, columnNameDict)


    def _setColoursFromPreferences(self, *args, **kwargs):
        """ Reset the colour. Called from notifiers when the general preferences get changed"""
        axisColour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        axisFont = getFont()
        backgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        selectionColour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT])
        self.setAxesColour(axisColour)
        self.setAxisFonts(axisFont)
        self.setBackgroundColour(backgroundColour)
        # self._refreshSelectionColour() or something similar.

    def _setTickOption(self, value):
        if value in TICKOPTIONS:
            self._tickOption = value

    def getSelectionPen(self):
        return pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=2)

    def _mouseDoubleClickCallback(self, x, y):
        pass

    def _mouseSingleClickCallback(self, x, y):
        pass

    def _mouseHoverCallback(self, barIndex, x, y):
        pass

    def selectByPids(self, pids):
        for handler in self._plottingHandlers:
            handler.selectData(pids)

    def __repr__(self):
        return f'<{self.__class__.__name__}_{self.name}>'



class PlotItemHandlerABC(object):

    plotType = None
    registerToParent = True

    callbackData = {
                    'pids':[],
                    'xs': [],
                    'ys': [],
                    'items': [],
                    'mousePos': []
                    }

    def __init__(self, parent, actionCallback=None,
                 selectionCallback=None, hoverCallback=None, *args, **kwds):

        self.parent = parent
        self.plotWidget = parent.plotWidget
        self.plotItem = parent.plotItem
        self.viewBox = parent.viewBox
        self.items = []
        self._actionCallback = actionCallback
        self._selectionCallback = selectionCallback
        self._hoverCallback = hoverCallback
        self.penColour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self._selectedPenColour =  rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT])
        self._selectedPen =  pg.functions.mkPen(self._selectedPenColour, width=2, style=QtCore.Qt.SolidLine)
        self._unselectedPen = None
        if self.registerToParent:
            self.parent._registerHandler(self)

    def plotData(self, dataFrame, columnsDict, **kwargs):
        "Override in subclasses"
        pass

    def _getValuesForColumn(self, dataFrame, columnArgName, columnsDict):
        """ Given a column Name, return the values as an array.
        If the column is not available, and for some reason has not been trapped beforehand, then is returned a nan array."""

        columnName = columnsDict.get(columnArgName)
        if columnName is None or columnName not in dataFrame:
            emptyArray = np.full(len(dataFrame), np.nan)
            dataFrame = pd.DataFrame({columnName: emptyArray})
            getLogger().warning(f'Plotting Warning. Could not find any values for {columnArgName}')
        filtered = dataFrame[columnName]
        values = filtered.values
        return values

    def setItemsVisible(self, value):
        for item in self.items:
            if item is not None:
                item.setVisible(value)

    def _getPlotData(self):
        xs = []
        ys = []
        plotItems = self.plotWidget.items()
        for item in plotItems:
            if hasattr(item, 'getData'):
                x,y = item.getData()
                xs.append(x)
                if isinstance(y, pd.Series):
                    ys.append(y.values)
                else:
                    ys.append(y)
        return xs,ys

    def getPlotData(self):
        """ Return X and Y data as tuple"""
        xs, ys = self._getPlotData()
        if len(xs) == len(ys) and len(xs)>0:
            yAll = [a for j in ys for a in j]
            yAll = np.array(yAll)
            xAll = [a for j in xs for a in j]
            xAll = np.array(xAll)
            return xAll, yAll
        return np.array([]), np.array([])

    def defaultSelectionCallback(self, *args, **kwargs):
        """This has to be subclassed to handle the various signals depending on the item and fire a common callback dictionary of values"""
        pass

    def defaultActionCallback(self, *args, **kwargs):
        """This has to be subclassed to handle the various signals depending on the item and fire a common callback dictionary of values"""
        pass

    def defaultHoverCallback(self, *args, **kwargs):
        """This has to be subclassed to handle the various signals depending on the item and fire a common callback dictionary of values"""
        pass

    def selectData(self, objs):
        """
        Each Plotitem (qtwidget) contains natively a property called objects.
         if any item can be linked to a V3 core object we save/link it with the pids (rather than storing the V3 object)
         If the pid(object) is found in the graphical item, then is selected by setting a pen colour around its shape.
        :param objs: pids
        :return: None
        """
        pass

class BarsHandler(PlotItemHandlerABC):

    plotType = PlotType.BAR.description
    registerToParent = True

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, **kwds)

    def plotData(self, dataFrame, columnsDict, clear=False, **kwargs):
        if clear:
            self.viewBox.clear()
            self.items = []
        xValues = self._getValuesForColumn(dataFrame, XCOLUMNNAME, columnsDict)
        yValues = self._getValuesForColumn(dataFrame, YCOLUMNNAME, columnsDict)
        coloursValues = self._getValuesForColumn(dataFrame, COLOURCOLUMNNAME, columnsDict)
        objectValues = self._getValuesForColumn(dataFrame, OBJECTCOLUMNNAME, columnsDict)

        if not xValues.dtype in [int]:
            xValues = np.arange(1, len(yValues)+1)

        bars = BarGraph(
                                       xValues=xValues, yValues=yValues,
                                       selectionCallback=self.defaultSelectionCallback,
                                       actionCallback=self.defaultActionCallback,
                                       #hoverCallback=self.defaultHoverCallback,
                                        brushes=coloursValues,
                                        pids=objectValues,
                                      )
        self.viewBox.addItem(bars)
        self.items.append(bars)

    def _getDataForCallback(self, data):
        return {
                        'pids': [data.get('pid')],
                        'xs': [data.get('index')],
                        'ys': [data.get('height')],
                        'items': [data.get('item')],
                        'mousePos': [data.get('mousePos')]
                    }

    def defaultSelectionCallback(self, data, *args, **kwargs):
        if self._selectionCallback:
            callbackData = self._getDataForCallback(data)
            self._selectionCallback(callbackData)

    def defaultHoverCallback(self, data, *args, **kwargs):
        if self._hoverCallback:
            callbackData = self._getDataForCallback(data)
            self._hoverCallback(callbackData)

    def selectData(self, pids):
        for item in self.items:
            selected = []
            for bar in item.bars:
                if bar.pid in pids:
                    selected.append(bar.index)
            item.drawPicture(selected=selected)

class ScattersHandler(PlotItemHandlerABC):
    registerToParent = True
    plotType = PlotType.SCATTER.description

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, **kwds)

    def plotData(self, dataFrame, columnsDict, clearPlot=True, **kwargs):
        if clearPlot:
            self.viewBox.clear()
            self.items.clear()
        xValues = self._getValuesForColumn(dataFrame, XCOLUMNNAME, columnsDict)
        yValues = self._getValuesForColumn(dataFrame, YCOLUMNNAME, columnsDict)
        coloursValues = self._getValuesForColumn(dataFrame, COLOURCOLUMNNAME, columnsDict)
        objectValues = self._getValuesForColumn(dataFrame, OBJECTCOLUMNNAME, columnsDict)

        noPen = None  # pen defined as None will not plot a line connecting scatters
        self.penColour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        scatterPen = pg.functions.mkPen(self.penColour, width=0.5, style=QtCore.Qt.SolidLine)
        brushes = [pg.fn.mkBrush(c) for c in coloursValues]

        if not yValues.dtype in [int, float]:
            yValues = np.arange(1, len(yValues)+1)
            getLogger().warning('Impossible to plot Y values. dType not allowed. Used array index instead.')

        if not xValues.dtype in [int, float]:
            xValues = np.arange(1, len(yValues)+1)
            getLogger().warning('Impossible to plot X values. dType not allowed. Used array index instead.')

        curve = self.plotItem.plot(xValues, yValues,
                                                         symbol='o', pen=noPen,
                                                         symbolPen=scatterPen,
                                                         symbolBrush=brushes,
                                                         data=objectValues)
        scattersItem = curve.scatter
        self.items.append(scattersItem)
        curve.sigPointsClicked.connect(self.defaultSelectionCallback)

    def selectData(self, pids):
        """Highlight the item by changing the pen colour """
        for i in self.items: #loop over the scatter curves
            individualScatterPoints = i.points()
            for scatterPoint in individualScatterPoints:
                scatterObject =  scatterPoint.data()
                if str(scatterObject) in pids:
                    scatterPoint.setPen(self._selectedPen)
                else:
                    scatterPoint.setPen(self._unselectedPen)

    def defaultSelectionCallback(self, item, points, *args, **kwargs):
        """ Parse the callback and get the selected objects"""
        callbackData = defaultdict(list)
        for i in points:
            pid = i.data()
            callbackData['pids'].append(pid)
            x = i.pos().x()
            y = i.pos().y()
            callbackData['xs'].append(x)
            callbackData['ys'].append(y)
            callbackData['items'].append(i)
        if self._selectionCallback:
            self._selectionCallback(callbackData)


class ErrorBarsHandler(PlotItemHandlerABC):

    plotType = None
    registerToParent = True

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, **kwds)

    def plotData(self, dataFrame, columnsDict, clearPlot=False, **kwargs):
        if clearPlot:
            self.viewBox.clear()
            self.items.clear()
        xValues = self._getValuesForColumn(dataFrame, XCOLUMNNAME, columnsDict)
        yValues = self._getValuesForColumn(dataFrame, YCOLUMNNAME, columnsDict)
        yErrorValues = self._getValuesForColumn(dataFrame, YERRCOLUMNNAME, columnsDict)
        penColour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])

        if not xValues.dtype in [int, float]:
            xValues = np.arange(1, len(yValues) + 1)
            getLogger().warning('Impossible to plot X values. dType not allowed. Used array index instead.')

        errorsItem = pg.ErrorBarItem(x=xValues, y=yValues, top=yErrorValues, beam=0.5, pen=penColour)

        self.viewBox.addItem(errorsItem)
        self.items.append(errorsItem)
        #

class LinesHandler(PlotItemHandlerABC):

    plotType = PlotType.LINE.description
    registerToParent = True

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, **kwds)

    def plotData(self, dataFrame, columnsDict, clear=False, **kwargs):
        return
        xValues = np.arange(1, len(dataFrame) + 1)
        yValues = self._getValuesForColumn(dataFrame, YCOLUMNNAME, columnsDict)
        item = self.plotItem.plot(xValues, yValues)
        self.items.append(item)


class ThresholdLinesHandler(PlotItemHandlerABC):
    registerToParent = True

    def __init__(self, parent, lineMovedCallback=None, *args, **kwds):
        """ For now is implemented for one H line. """
        super().__init__(parent, **kwds)
        self._lineMovedCallback = lineMovedCallback

    def plotData(self, dataFrame, columnsDict, **kwargs):
        yValues = self._getValuesForColumn(dataFrame, THRESHOLDCOLUMNNAME, columnsDict)
        item = pg.InfiniteLine(angle=0, movable=True, pen='b')
        item.sigPositionChangeFinished.connect(partial(self._moved, item))
        if len(yValues)>0:
            pos = yValues[-1]
        else:
            pos = 0
        item.setPos(pos)
        self.viewBox.addItem(item)
        self.items.append(item)

    def _moved(self, item, *args, **kwargs):
        if self._lineMovedCallback is not None:
            self._lineMovedCallback(position=item.getYPos(), name=item._name)

class LegendHandler(PlotItemHandlerABC):
    # NOT sure if we are implementing this
    registerToParent = False

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, **kwds)

class SelectionBoxHandler(PlotItemHandlerABC):
    # NOT sure bout this yet
    registerToParent = False

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, **kwds)


class ViewBox(pg.ViewBox):

    itemsSelected = QtCore.pyqtSignal(object)

    def __init__(self, parentWidget, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMenuEnabled(enableMenu=False)  # override pg default context menu


class PlotWidget(pg.PlotWidget):

    itemsSelected = QtCore.pyqtSignal(object)

    def __init__(self, parentWidget, *args, **kwds):
        pg.PlotWidget.__init__(self, *args, **kwds)
        self.setMenuEnabled(enableMenu=False)  # override pg default context menu


class PlotItem(pg.PlotItem):

    def __init__(self, parentWidget, *args, **kwargs):
        pg.PlotItem.__init__(self, *args, **kwargs)
        self.parentWidget = parentWidget
        self.setMenuEnabled(False)
        self.exportDialog = None
        self.hideButtons()

class XAxisItem(pg.AxisItem):
    def __init__(self,  parentWidget, labelRotation=-90, outward=True, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self.style = {
            'tickTextOffset': [5, 2],  ## (horizontal, vertical) spacing between text and axis
            'tickTextWidth': 30,  ## space reserved for tick text
            'tickTextHeight': 18,
            'autoExpandTextSpace': True,  ## automatically expand text space if needed
            'tickFont': None,
            'stopAxisAtTick': (False, False),  ## whether axis is drawn to edge of box or to last tick
            'textFillLimits': [  ## how much of the axis to fill up with tick text, maximally.
                (0, 0.8),    ## never fill more than 80% of the axis
                (2, 0.6),    ## If we already have 2 ticks with text, fill no more than 60% of the axis
                (4, 0.4),    ## If we already have 4 ticks with text, fill no more than 40% of the axis
                (6, 0.2),    ## If we already have 6 ticks with text, fill no more than 20% of the axis
                ],
            'showValues': True,
            'tickLength': 5 if outward else -5,
            'maxTickLevel': 2,
            'maxTextLevel': 2,
        }
        self.orientation = 'bottom'
        self.labelRotation = labelRotation
        self.pixelTextSize = 8
        self.setHeight(40)

    def mouseDragEvent(self, event):
        """ Override this method to remove a native bug in PyQtGraph. """
        pass

class YAxisItem(pg.AxisItem):
    def __init__(self, parentWidget, outward=False, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self.style = {
            'tickTextOffset': [5, 2],  ## (horizontal, vertical) spacing between text and axis
            'tickTextWidth': 30,  ## space reserved for tick text
            'tickTextHeight': 18,
            'autoExpandTextSpace': True,  ## automatically expand text space if needed
            'tickFont': None,
            'stopAxisAtTick': (False, False),  ## whether axis is drawn to edge of box or to last tick
            'textFillLimits': [  ## how much of the axis to fill up with tick text, maximally.
                (0, 0.8),    ## never fill more than 80% of the axis
                (2, 0.6),    ## If we already have 2 ticks with text, fill no more than 60% of the axis
                (4, 0.4),    ## If we already have 4 ticks with text, fill no more than 40% of the axis
                (6, 0.2),    ## If we already have 6 ticks with text, fill no more than 20% of the axis
                ],
            'showValues': True,
            'tickLength': 5 if outward else -5,
            'maxTickLevel': 2,
            'maxTextLevel': 2,
        }
        self.orientation = 'left'
        self.setWidth(50)

    def mouseDragEvent(self, event):
        """ this method is to remove a native bug in PyQtGraph. """
        pass




#######################################################################################################
####################################      Mock DATA TESTING    ########################################
#######################################################################################################



if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule

    def  _selectionCallback(dataDict, *args, **kwargs):
        print('Selected:', dataDict)

    def  _hoverCallback(dataDict, *args, **kwargs):
        print('_hoverCallback:', dataDict)

    app = TestApplication()
    win = QtGui.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None, )

    module = CcpnModule(None, name='Test')
    widget = MainPlotWidget(module.mainWidget,  selectionCallback=_selectionCallback, hoverCallback=_hoverCallback,  grid=(0,0))

    df = pd.DataFrame({'a':[1,2,3,4], 'b':[0.1, 1.3, 4.4, 7.9]})
    # widget.plotData(dataFrame=df, plotName='name', plotType=PlotType.LINE.description, xColumnName='a', yColumnName='b')
    widget.plotData(dataFrame=df, plotName='name', plotType=PlotType.BAR.description, xColumnName='a', yColumnName='b')
    # widget.plotData(dataFrame=df, plotName='name', plotType=PlotType.SCATTER.description, xColumnName='a', yColumnName='b')
    print(widget.allowedPlotTypes)
    moduleArea.addModule(module)
    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
