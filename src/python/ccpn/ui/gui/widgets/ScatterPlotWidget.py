"""
Module Documentation Here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import shutil
import numpy as np
import pandas as pd
import pyqtgraph as pg
import ccpn.ui.gui.widgets as Widgets
from functools import partial
from collections import OrderedDict as od
import ccpn.ui.gui.guiSettings as gs
import ccpn.ui.gui.lib.mouseEvents as me
import ccpn.ui.gui.lib.GuiStripContextMenus as cm
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.util.Colour import hexToRgb, hexToRgba, rgbaRatioToHex, darkDefaultSpectrumColours, hexToRgbaArray
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.lib.MenuActions import _openItemObject
from ccpn.ui.gui.widgets.CustomExportDialog import CustomExportDialog
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Frame import Frame
# from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.util.Logging import getLogger
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.Font import setWidgetFont, getWidgetFontHeight
from ccpn.ui.gui.widgets.Font import Font, DEFAULTFONTNAME, DEFAULTFONTSIZE, getFontHeight, getFont
from ccpn.util.Common import _getObjectsByPids, splitDataFrameWithinRange
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.widgets.Icon import Icon, ICON_DIR

# colours
BackgroundColour = gs.getColours()[gs.CCPNGLWIDGET_HEXBACKGROUND]
OriginAxes = pg.functions.mkPen(hexToRgb(gs.getColours()[gs.GUISTRIP_PIVOT]), width=1, style=QtCore.Qt.DashLine)
SelectedPointPen = pg.functions.mkPen(rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_HIGHLIGHT]), width=4)
ROIline = rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_SELECTAREA])
ROIPen = pg.functions.mkPen(ROIline, width=3, style=QtCore.Qt.SolidLine)
HandlePen = pg.functions.mkPen(hexToRgb(gs.getColours()[gs.GUISTRIP_PIVOT]), width=5, style=QtCore.Qt.SolidLine)
DefaultRoiLimits = [[0, 0], [0, 0]]  #

SelectedLabel = pg.functions.mkBrush(rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_HIGHLIGHT]), width=4)
c =rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_LABELLING])
GridPen = pg.functions.mkPen(c, width=1, style=QtCore.Qt.SolidLine)
GridFont = getFont()
DefaultPointSize = 10
DefaultPointColour = '#000000' # black
DefaultInnerPointColour = '#7080EE'
DefaultSymbol = 'o'
AllowedSymbols = ['o', 's', 't', 'd', '+']

_SELECTORNAME = 'selectorName'
_VALUEHEADER = 'headerValueName'
_PIDHEADER = 'headerPidName'
_TOOLTIP = 'tooltip'
_HEXCOLOURHEADER = 'headerHexColour'
_OBJCOLOURPROPERTY = 'objColourProperty'
_SYMBOL = 'symbol'
_CALLBACK = 'callback'
_POINTSIZE = 'pointSize'
_HEXCOLOUR = 'hexColour'
_INNERHEXCOLOUR = 'innerHexColour'

ScatterSymbolsDict = od([
                        ['circle',   {'symbol':'o', 'icon': 'icons/scatter_o'}],
                        ['square',   {'symbol':'s', 'icon': 'icons/scatter_s'}],
                        ['triangle', {'symbol':'t', 'icon': 'icons/scatter_t'}],
                        ['diamond',  {'symbol':'d', 'icon': 'icons/scatter_d'}],
                        ['plus',     {'symbol':'+', 'icon': 'icons/scatter_+'}],
                        ])

def _getPointsWithinLimits(points, limits):
    xMin, xMax, yMin, yMax = limits
    ptsPos = list(map(lambda s: (s.pos().x(), s.pos().y()), points))
    if len(ptsPos) > 0:
        x, y = zip(*ptsPos)
        x, y = np.array(x), np.array(y)
        i = np.where((x >= xMin) & (x <= xMax) & (y >= yMin) & (y <= yMax))
        innerPoints = points[i]
        return innerPoints
    return []

class _ItemBC(object):
    ''' '''

    def __init__(self, headerValueName, **kwargs):
        '''
        Used to set the points/axis in the plot
        :param kwargs:

        '''
        self.kwargs = {
                       _SELECTORNAME      : headerValueName,
                       _VALUEHEADER       : headerValueName,
                       _PIDHEADER         : None,
                       _HEXCOLOURHEADER   : None,
                       _OBJCOLOURPROPERTY : None, # the obj property where to grab the colour. E.g for spectrum: sliceColour
                       }
        self.kwargs.update(kwargs)
        for k, v in self.kwargs.items():
            setattr(self, k, v)

class ScatterROI(pg.ROI):
    """
    Re-implemetation of pg.ROI to allow customised functionalities
    """
    def __init__(self, parentWidget,  *args, **kwargs):

        pg.ROI.__init__(self,  *args, **kwargs)
        self.parentWidget = parentWidget
        self.handleSize = 8
        self.translatable = False # keep False otherwise it doesn't allow normal pan/selection of the plotItems within the ROI region.
        self._setROIhandles()
        # self._isEnabled = True

    def _setROIhandles(self):
        """ sets the handles,"""
        ## TranslateHandle -> moves the ROI without changing the shape
        self.xMinHandle = self.addTranslateHandle((0, 0.5), name='xMinHandle')
        self.xMaxHandle = self.addTranslateHandle((1, 0.5), name='xMaxHandle')
        self.yMinHandle = self.addTranslateHandle((0.5, 0), name='yMinHandle')
        self.yMaxHandle = self.addTranslateHandle((0.5, 1), name='yMaxHandle')
        ## ScaleHandle -> reshape the ROI without translating it
        self.topRightHandle = self.addScaleHandle([1, 1], [0.5, 0.5], name='topRight')
        self.topLeft = self.addScaleHandle([0, 1], [1, 0], name='topLeft')
        self.bottomLeft = self.addScaleHandle([0, 0], [0.5, 0.5], name='bottomLeft')
        self.bottomRight = self.addScaleHandle([1, 0], [0, 1], name='bottomRight'),

    def getLimits(self):
        """
        the values for the ROI
        (getState returns a dict ['pos']  left bottom corner, ['size'] the size of RO1 and ['angle'] for this RectROI is 0)
        :return: a list of rectangle coordinates in the format minX, maxX, minY, maxY
        """
        state = self.getState()
        pos = state['pos']
        size = state['size']
        xMin = pos[0]
        xMax = pos[0] + size[0]
        yMin = pos[1]
        yMax = pos[1] + size[1]
        return [xMin, xMax, yMin, yMax]

    def setLimits(self, xMin, xMax, yMin, yMax):
        """
        a conversion mechanism to the internal roiItem setState
        :return:  set the ROI box
        """
        state = {'pos': [], 'size': [], 'angle': 0}
        xSize = abs(xMax) - abs(xMin)
        ySize = abs(yMax) - abs(yMin)
        state['pos'] = [xMin, yMin]
        state['size'] = [xSize, ySize]
        self.setState(state)

    def getInnerPoints(self):
        """
        :return: the pointItems within the ROI limits (included extremes)
        """
        return _getPointsWithinLimits(self.parentWidget.scatterPlot.points(), self.getLimits())


    def getInnerData(self):
        """
        :return: List of Pandas series. The linked data for points within the ROI limits.
        """
        return list(map(lambda s: s.data(), self.getInnerPoints()))

    def _getInnerIxNames(self):
        """
        :return: List of Pandas series. The linked data for points within the ROI limits.
        """
        return list(map(lambda s: s.data().name(), self.getInnerPoints()))

    def getInnerDataFrame(self):
        """
        :return: the inner data objs as a single Pandas dataframe
        """
        innerSeries = self.getInnerData()
        return pd.DataFrame(innerSeries)

class ScatterPlot(Widget):

    dataSelectedSignal = QtCore.Signal(object)

    def __init__(self,
                 application,
                 dataFrame,
                 axesDefinitions = None,
                 roiVisible = True,
                 roiEnabled = True,
                 mouseSelectionRegion = True,
                 pointSelectionCallback = None,
                 pointActionCallback = None,
                 pointSymbol = DefaultSymbol,
                 pointSize = DefaultPointSize,
                 hexPointColour = DefaultPointColour,
                 innerRoiPointColour = DefaultInnerPointColour,
                 **kwds):
        super().__init__(setLayout=True, **kwds)

        self.application = application
        self.project = None
        if self.application:
            self.project = self.application.project
        self._dataFrame = dataFrame
        self._roiLimits = DefaultRoiLimits
        self._roiDataFrame = None
        self.axesDefinitions = axesDefinitions
        self.setAxesDefinitions(self.axesDefinitions, updateWidgets=False)
        self.pointSymbol = pointSymbol
        self.pointSize = pointSize
        self.hexPointColour = hexPointColour
        self.innerRoiPointColour = innerRoiPointColour
        self._scatterView = pg.GraphicsLayoutWidget()
        self._scatterView.setBackground(BackgroundColour)
        self._plotItem = self._scatterView.addPlot()
        self._scatterViewbox = self._plotItem.vb
        self._addScatterSelectionBox()
        self._scatterViewbox.mouseClickEvent = self._scatterViewboxMouseClickEvent # click on the background canvas
        self._scatterViewbox.mouseDragEvent = self._scatterMouseDragEvent
        # self._scatterViewbox.hoverEvent = self._scatterHoverEvent
        self._scatterViewbox.scene().sigMouseMoved.connect(self.mouseMoved) #use this if you need the mouse Posit
        # self._scatterViewbox.setLimits(**{'xMin':0, 'xMax':1, 'yMin':0, 'yMax':1})
        self._plotItem.setMenuEnabled(False)
        self._exportDialog = None
        self.scatterPlot = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0))
        # self.scatterPlot.sigClicked.connect(self._plotClicked)
        self.scatterPlot.mouseClickEvent = self._scatterMouseClickEvent
        self.scatterPlot.mouseDoubleClickEvent = self._scatterMouseDoubleClickEvent
        setWidgetFont(self)
        ## adjustable ROI box
        self.roiItem = ScatterROI(self, *DefaultRoiLimits, pen=ROIPen)
        self.roiItem.sigRegionChangeFinished.connect(self._roiChangedCallback)
        self._plotItem.addItem(self.roiItem)
        self.showROI(roiVisible)
        self.tipText = pg.TextItem(anchor=(-0.1, -0.6), angle=0, border='w', fill=(0, 0, 255, 100))
        # self.tipText.hide()
        self.tipText.setFont(GridFont)
        self._plotItem.addItem(self.tipText)
        self._plotItem.autoRange()
        self.xOriginLine = pg.InfiniteLine(angle=90, pos=0, pen=OriginAxes)
        self.yOriginLine = pg.InfiniteLine(angle=0, pos=0, pen=OriginAxes)
        self.pointSelectionCallback = pointSelectionCallback # single click
        self.pointActionCallback = pointActionCallback # double click
        self._plotItem.addItem(self.scatterPlot)
        self._plotItem.addItem(self.xOriginLine)
        self._plotItem.addItem(self.yOriginLine)
        autoBtnFile = os.path.join(ICON_DIR, 'icons/zoom-full.png')
        self.autoBtn = self._plotItem.autoBtn = pg.ButtonItem(imageFile=autoBtnFile, width=30, parentItem=self._plotItem)
        self._plotItem.updateButtons = lambda : None # just to remove the odd PyQtGraph default behaviour
        self.autoBtn.clicked.connect(self._setZoomFull)
        self.getLayout().addWidget(self._scatterView)
        self.axisSelectionFrame = Frame(self, setLayout=True, grid=(1, 0))
        self._xSelCW = PulldownListCompoundWidget(self.axisSelectionFrame, labelText='Select X-axis',
                                        callback=self._axisSelectionCallback, grid=(0, 0))#,  hAlign='l',)
        self._ySelCW = PulldownListCompoundWidget(self.axisSelectionFrame, labelText='Select Y-axis',
                                                  callback=self._axisSelectionCallback, grid=(0, 1))#,  hAlign='l',)
        self.xAxisSelector = self._xSelCW.pulldownList
        self.yAxisSelector = self._ySelCW.pulldownList

        # coordinates
        self.coordinatesLabel = Label(self.axisSelectionFrame, text='', grid=(0,2))
        # context menu
        self.contextMenu = Menu('', None, isFloatWidget=True)
        self._setPlotItemFonts()
        self.setAxesWidgets()
        self._selectedData = []
        self._tipTextIsEnabled = True


    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame

    @property
    def roiLimits(self) -> list:
        """
        :return: a list of 4 elements: [xMin, xMax, yMin, yMax]
        """
        self._roiLimits = self.roiItem.getLimits()
        return self._roiLimits

    @roiLimits.setter
    def roiLimits(self, data):
        """
        :param data: list of 4 elements: [xMin, xMax, yMin, yMax]
        :return: None, set the roiLimits and update its plotItem.
        """
        if len(data) != 4:
            getLogger().warn('ROI Data must be a list of 4 elements: [xMin, xMax, yMin, yMax]')
            return
        self._roiLimits = data
        self.roiItem.setLimits(*data)

    @property
    def roiDataFrame(self) -> list:
        """
        :return: dataframe from data within the ROI
        """
        self._roiDataFrame = self.roiItem.getInnerDataFrame()
        return self._roiDataFrame

    @property
    def selectedData(self):
        return self._selectedData

    @selectedData.setter
    def selectedData(self, data):
        """
        :param data: list of series (retrieved from spotItem.data())
        set the data as selected and draws the pattern around the spotItem
        NB. it use selectedData rather item because an Item can get deleted while redrawing/changing axis.
        By adding data, it fires a signal (dataSelectedSignal) that can be used for external callbacks.
        """
        self._selectedData = data
        # self._selectedData = list(OrderedSet(data))
        self._setPointPens(self._getPointPens())
        self.dataSelectedSignal.emit(data)

    def setAxesDefinitions(self, defs:od, updateWidgets=True):
        '''
        :param defs: orderedDict key: visible label to appear in the pulldown, value: the dataframe column header name.
        if None, they will be used the  header names as they appear in the original dataframe.
        '''
        if isinstance(defs, dict):
            self.axesDefinitions = defs
        if defs is None:
            self.axesDefinitions = od([k, _ItemBC(k)] for k in self.dataFrame.columns)
        if updateWidgets:
            self.setAxesWidgets()

    def setAxesWidgets(self):
        '''
        Set from the axesDefinitions. If None, uses the dataFrame column names.
        '''
        pulldownTexts = list(self.axesDefinitions.keys())
        self.xAxisSelector.setData(list(pulldownTexts))
        self.yAxisSelector.setData(list(pulldownTexts))

    def selectAxes(self, xHeader=None, yHeader=None):
        '''
        :param x: str, header as appears in the selection Pulldown
        :param y: str, header as appears in the selection Pulldown
        if None is given, it keeps the current value.
        '''
        if xHeader:
            self.xAxisSelector.select(xHeader)
        if yHeader:
            self.yAxisSelector.select(yHeader)

    def updatePlot(self):
        self.scatterPlot.updatePoints()

    def _setZoomFull(self, *args):
        self._plotItem.autoRange()

    def setEnabledROI(self, enable=True):
        return
        #todo
        if not enable:
            self.roiItem.hide()
            self.roiItem.setLimits(0,0,0,0)
            self.roiItem.sigRegionChangeFinished.disconnect(self._roiChangedCallback)
            self.roiItem._isEnabled = False
        else:
            self.roiItem.show()
            self.roiItem.sigRegionChangeFinished.connect(self._roiChangedCallback)
            self.roiItem._isEnabled = True

    def setPointColour(self, hex, updatePlot=True, overrideItemDef=False):
        self.hexPointColour = hex
        if updatePlot:
            brushes = self.getPointBrushes(overrideItemDef=overrideItemDef)
            if len(brushes) == len(self.scatterPlot.points()):
                self.scatterPlot.setBrush(brushes)

    def setInnerPointColour(self, hex, updatePlot=True):
        self.innerRoiPointColour = hex
        if updatePlot:
            brushes = self.getPointBrushes()
            self.scatterPlot.setBrush(brushes)

    def setPointSymbol(self, symbol=DefaultSymbol, updatePlot=True):
        if symbol in AllowedSymbols:
            self.pointSymbol = symbol
            if updatePlot:
                self.scatterPlot.setSymbol(self.pointSymbol)

    def setPointSize(self, size=10, updatePlot=True):
        self.pointSize = size
        if updatePlot:
            self.scatterPlot.setSize(self.pointSize)

    def _setPointPens(self, pens):
        if len(pens) == len(self.scatterPlot.points()):
            self.scatterPlot.setPen(pens)

    def addPoints(self, x=None, y=None, points=None, **kwargs):

        """
        used to add points to the scatterPlot.
        If only x,y is given, all the other parameters are set as default.
        To set each property use points or define the kwargs (see below).
        X,Y can also be define in points or kwargs constructs as "pos" (see below);
        in that case is not necessary to set x,y as individual args, and can be left as None.

        :param x:  1D arrays of x,y values
        :param y:  1D arrays of x,y values
        :param points:  Optional list of dicts. Each dict specifies parameters for a single point:
                        {'pos': (x,y), 'size', 'pen', 'brush', 'symbol'}. This is just an alternative method
        :param kwargs:
                x,y                    1D arrays of x,y values.
                pos                    2D structure of x,y pairs (such as Nx2 array or list of tuples)
                symbol                 can be one (or a list) of:
                                       * 'o'  circle (default)
                                       * 's'  square
                                       * 't'  triangle
                                       * 'd'  diamond
                                       * '+'  plus
                pen                    The pen (or list of pens) to use for drawing point outlines.
                brush                  The brush (or list of brushes) to use for filling points.
                size                   The size (or list of sizes) of points.
                data                   a list of python objects used to uniquely identify each point.
                name                   The name of this item. Names are used for automatically
                                       generating LegendItem entries and by some exporters.
        """
        self.scatterPlot.clear()
        args = []
        if points is not None:
            args = [points]
        if x is not None and y is not None:
            args = [x, y]
        if not kwargs.get(_SYMBOL) in AllowedSymbols:
            getLogger().warning('Symbol not available. Used the default instead')
            kwargs.update({_SYMBOL:'o'})
        self.scatterPlot.addPoints(*args, **kwargs)
        self.setPlotLimits()

    def setupContextMenu(self):
        """
        :return: list of items for creating the context Menu.
        Subclass this to insert/remove items in bespoke plots.
        """
        items = []
        items += self._getDefaultMenuItems()
        items += self._getExportMenuItems()
        return items

    def _getValuesFromDefition(self, definitionName, definitionValueHeader):
        """
        :param definitionName: the _ItemBC name
        :param definitionValueHeader: the _ItemBC header values name.
        :return:
        """
        values = []
        _item = self.axesDefinitions.get(definitionName)
        dfColumnHeader = getattr(_item, definitionValueHeader)
        filteredDf = self.dataFrame.get(dfColumnHeader)
        if filteredDf is not None:
            values = filteredDf.values
        return values

    def setPlotLimits(self, **kwargs):
        from ccpn.util.Common import percentage
        addPercent = 200
        xValues, yValues = self.scatterPlot.getData()
        xMin, xMax = np.min(xValues), np.max(xValues)
        yMin, yMax = np.min(yValues), np.max(yValues)
        deltaX = xMax - xMin
        deltaY = yMax - yMin
        deltaX += percentage(addPercent, deltaX)
        deltaY += percentage(addPercent, deltaY)
        self._scatterViewbox.setLimits(
                                    xMin = xMin - deltaX,
                                    xMax = xMax + deltaX,
                                    yMin = yMin - deltaY,
                                    yMax = yMax + deltaY,
                                    minXRange = 0.01,
                                    maxXRange = max(xValues)*10,
                                    minYRange = 0.01,
                                    maxYRange = max(yValues)*10,
                                    )

    def getPointBrushes(self, itemDef=None, overrideItemDef=False):
        """
        Two way of defining the point colours:
        - Global: a unique colour for all point.
                global colours are set on init or using the setters.
        - Single: one colour for each point.
                this option can to be defined in two ways:
                *   from defining the HEX colours in the input dataframe and
                    stating the coloumName in the _ItemBC definitions
                        _HEXCOLOURHEADER   : 'theHeaderName',

                *   from the ccpnObjects property, e.g 'sliceColour'
                    in this case it is necessary to have a dataframe containing a column with pids,
                    and objs needs to exist in the project.
                    also define the object Property  and the pidHeader name to use in the _ItemBC definitions:
                       _PIDHEADER         : 'SpectraColumn',
                       _OBJCOLOURPROPERTY : 'sliceColour',
        If points are outside the ROI, then they are a more transparent shade of colour.

        :return: list of brushes for painting the scatterPlot points
        """
        if itemDef is None:
            if len(self.axesDefinitions.values())>0:
                itemDef = list(self.axesDefinitions.values())[0]

        innerData = self.roiItem.getInnerData()
        if len(self.dataFrame) == 0: return []
        ixs, series = zip(*self.dataFrame.iterrows())
        hexs = [self.hexPointColour for i in ixs]

        if not overrideItemDef:
            if isinstance(itemDef, _ItemBC):
                pidHeader = getattr(itemDef, _PIDHEADER)
                objColourProperty = getattr(itemDef, _OBJCOLOURPROPERTY)
                hexHeader = getattr(itemDef, _HEXCOLOURHEADER)
                if objColourProperty is not None: # use the obj for getting the colour info (if defined)
                    pidDf = self.dataFrame.get(pidHeader)
                    if pidDf is not None and self.project:
                        ccpnObjs = _getObjectsByPids(self.project, pidDf.values)
                        hexs = [getattr(o, objColourProperty) for o in ccpnObjs]

                if hexHeader is not None: # use the dedicated colour Header for getting the colour info (if defined)
                    hexDf = self.dataFrame.get(hexHeader)
                    if hexDf is not None:
                        hexDf.fillna(self.hexPointColour, inplace=True)
                        hexs = hexDf.values

        innerNames = np.array([x.name for x in innerData])
        _tempColours = hexToRgbaArray(hexs, 100)
        innerIndices = np.where(np.in1d(ixs, innerNames))[0]
        brushes = []
        for i, colour in enumerate(list(_tempColours)):
            if i in innerIndices:
                colour = colour[:-1]
            brushes.append(pg.functions.mkBrush(list(colour)))
        return brushes

    def _getPointPens(self):
        """
        :return: list of pens. Used to draw a selection pattern. [Pen, None] None if no Pen.
        """
        if len(self.dataFrame) == 0: return []
        indices, series = zip(*self.dataFrame.iterrows())
        pens = [SelectedPointPen if i in [j.name for j in self._selectedData] else None for i in indices]
        return pens

    def _axisSelectionCallback(self, *args):
        """
        Callback from pulldown selectors. Adds Points to the plot based on the dataframe columns.
        Objects are set from pids if defined in the dataframe and definitions
        Colours are set from objs if they have the in their class property or if specified in the
        :param args:
        :return:
        """
        if len(self.dataFrame) == 0: return
        self.scatterPlot.clear()
        self._setPlotItemLabels()
        # brushes = self.getPointBrushes(self.axesDefinitions.get(self.xAxisSelector.getText()))
        pens = self._getPointPens()
        indices, series = zip(*self.dataFrame.iterrows())
        xValues = self._getValuesFromDefition(self.xAxisSelector.getText(), _VALUEHEADER)
        yValues = self._getValuesFromDefition(self.yAxisSelector.getText(), _VALUEHEADER)
        if len(xValues) == len(yValues):
            self.addPoints(x=xValues, y=yValues,  size=self.pointSize, symbol=self.pointSymbol,
                            data=series, pen=pens)
            self._updateBrushes() #update colours
            self._plotItem.autoRange()
        else:
            Widgets.MessageDialog.showWarning('Error displaying data', 'Values lenght mismatch')

    def _setPlotItemLabels(self):
        self._plotItem.setLabel('bottom', self.xAxisSelector.getText())
        self._plotItem.setLabel('left', self.yAxisSelector.getText())
    
    def _setPlotItemFonts(self):
        if self.application:
            self._plotItem.getAxis('bottom').setPen(GridPen)
            self._plotItem.getAxis('left').setPen(GridPen)
            self._plotItem.getAxis('bottom').tickFont = GridFont
            self._plotItem.getAxis('left').tickFont = GridFont

    ###### Context menu setups ######

    def _getDefaultMenuItems(self):
        """
        Creates default context menu items.
        """
        items = [
                cm._SCMitem(name='Reset Zoom',
                         typeItem=cm.ItemTypes.get(cm.ITEM), icon='icons/zoom-full',
                         toolTip='Reset the plot to default limits',
                         callback=self._plotItem.autoRange),
                cm._SCMitem(name='ROI',
                        typeItem=cm.ItemTypes.get(cm.ITEM), icon='icons/roi',
                        toolTip='Toggle ROI',
                        checkable = True,
                        callback=self.toggleROI),
                cm._SCMitem(name='Select within ROI',
                            typeItem=cm.ItemTypes.get(cm.ITEM), icon='icons/roi_selection',
                            toolTip='Select items locatate inside the ROI limits',
                            callback=self.selectFromROI),
                cm._SCMitem(name='Toggle Mouse Text',
                        typeItem=cm.ItemTypes.get(cm.ITEM), icon=None,
                        toolTip='Show/hide the mouse coordinates from plot',
                        callback=self.toggleTipText),
                cm._separator(),
                ]
        items = [itm for itm in items if itm is not None]
        return items

    def _getExportMenuItems(self):
        """
        Creates default Export context menu items.
        """
        items = [
                cm._SCMitem(name='Export image...',
                        typeItem=cm.ItemTypes.get(cm.ITEM), icon=None,
                        toolTip='Export image to file.',
                        callback=partial(self._showExportDialog, self._scatterViewbox)),
                ]
        items = [itm for itm in items if itm is not None]
        return items

    def _addSubMenus(self, mainMenu):
        """
        subclass this to add subMenus
        """
        pass

    def _raiseScatterContextMenu(self, ev):
        """ Creates all the menu items for the scatter context menu. """
        mainMenu = cm._createMenu(self, self.setupContextMenu())
        self._addSubMenus(mainMenu)
        self.contextMenu.exec_(ev.screenPos().toPoint())

    def _showExportDialog(self, viewBox):
        """
        :param viewBox: the viewBox obj for the selected plot
        :return:
        """
        if self._exportDialog is None:
            self._exportDialog = CustomExportDialog(viewBox.scene(), titleName='Exporting')
        self._exportDialog.show(viewBox)

    ###########  scatter Mouse Events ############

    def _scatterViewboxMouseClickEvent(self, event):
        """ click on scatter viewBox (the background canvas).
        The parent of scatterPlot. Opens the context menu at any point. """
        if event.button() == QtCore.Qt.RightButton:
            event.accept()
            self._raiseScatterContextMenu(event)

    def _setCallbackData(self, items, trigger=None):
        """
        :param items:  list of pg.PointItem type
        :param trigger: Any of CallBack _callbackwords:(CLICK, DOUBLECLICK, CURRENT)
        :return: CallBack instance (ordered dict type)
        """
        data = []
        for item in items:
            if item is not None:
                data.append(CallBack(value=[item.pos().x(), item.pos().y()],
                                theObject=item,
                                object=item.data(),
                                targetName=None,
                                trigger=trigger,
                                ))
        return data

    def _scatterMouseDoubleClickEvent(self, ev):
        """
        re-implementation of scatter double click even
        """
        plot = self.scatterPlot
        pts = plot.pointsAt(ev.pos())
        if len(pts) > 0:
            callbackData = self._setCallbackData(pts, trigger=CallBack.DOUBLECLICK)
            if self.pointActionCallback is not None:
                self.pointActionCallback(callbackData)
            ev.accept()
        else:
            # "no points, needs to clear selection"
            ev.accept()

    def _scatterMouseClickEvent(self, ev):
        """
          Re-implementation of scatter mouse event to allow selections of a single point
        """
        plot = self.scatterPlot
        pts = plot.pointsAt(ev.pos())
        _data = [pt.data() for pt in pts]
        if len(pts) > 0:
            callbackData = self._setCallbackData(pts, trigger=CallBack.CLICK)
            if me.leftMouse(ev):
                if self.pointSelectionCallback is not None:
                    self.pointSelectionCallback(callbackData)
                self._clearScatterSelection()
                self.selectedData = _data
                # self._setPointPens(self._getPointPens())

                # setPens = [pt.setPen(SelectedPointPen) for pt in pts]
                ev.accept()
            elif me.controlLeftMouse(ev):
                # Control-left-click;  add to selection
                if self.pointSelectionCallback is not None:
                    self.pointSelectionCallback(callbackData)
                self.selectedData += _data
                # setPens = [pt.setPen(SelectedPointPen) for pt in pts]
                ev.accept()
            else:
                ev.ignore()
        else:
            #need to clear selection
            self.selectedData = []
            # self.scatterPlot.setPen([None]*len(self.dataFrame.index))
            ev.accept()

    def mouseMoved(self, event):
        """
        use this if you need for example display the mouse coords on display
        :param event:
        :return:
        """
        position = event
        if self._tipTextIsEnabled:
            if self._scatterViewbox.sceneBoundingRect().contains(position):
                mousePoint = self._scatterViewbox.mapSceneToView(position)
                x = mousePoint.x()
                y =  mousePoint.y()
                self._showTipTextForPosition(x,y)
            else:
                self.tipText.hide()

    # def _scatterHoverEvent(self, event):
    #     position = event.pos()
    #     if self._tipTextIsEnabled:
    #         if self._scatterViewbox.sceneBoundingRect().contains(position):
    #             mousePoint = self._scatterViewbox.mapToView(event.pos())
    #             x = mousePoint.x()
    #             y =  mousePoint.y()
    #             print(x, y, 'Mouse moved')
    #             self._showTipTextForPosition(x,y)
    #         else:
    #             self.tipText.hide()

    def _showTipTextForPosition(self, x, y):
        labelPos = "x=%0.2f, y=%0.2f" % (x, y)
        pts = self.scatterPlot.pointsAt(pg.Point(x, y))
        if len(pts)>0:
            pids = self.getPidsFromPoints(pts)
            if any(pids):
                pidsLabels = '\n'.join(map(str, pids))
                labelPos += '\n'
                labelPos += pidsLabels
        self.tipText.setText(labelPos)
        self.tipText.setPos(x, y)
        self.tipText.show()

    # def hoverEvent(self, event):
    #     pass #not needed

    def _getDataForPoints(self, points):
        return list(map(lambda s: s.data(), points))

    def _scatterMouseDragEvent(self, event, *args):
        """
        Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
        drag events. Same as spectrum Display. Check Spectrum Display View Box for more documentation.
        Known bug: left drag on the axis, raises a pyqtgraph exception
        """
        if me.leftMouse(event):
            pg.ViewBox.mouseDragEvent(self._scatterViewbox, event)
        elif me.controlLeftMouse(event):
            self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
            event.accept()
            if not event.isFinish():
                self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
            else:  ## the event is finished.
                limits = self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
                selectedData = self._getDataForPoints(_getPointsWithinLimits(self.scatterPlot.points(), limits))
                self.selectedData += selectedData
                # self._setPointPens(self._getPointPens())
                self._resetSelectionBox()
        else:
            self._resetSelectionBox()
            event.ignore()

    def toggleTipText(self):
        self._tipTextIsEnabled = not self.tipText.isVisible()
        self.tipText.setVisible(not self.tipText.isVisible())

    def toggleROI(self):
        """
        show/hide ROI from the plot
        """
        self.roiItem.setVisible(not self.roiItem.isVisible())

    def showROI(self, value):
        """
        show/hide ROI from the plot
        """
        self.roiItem.setVisible(value)

    def selectFromROI(self):
        self.selectedData = self.roiItem.getInnerData()

    def _addScatterSelectionBox(self):
        self._scatterSelectionBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self._scatterSelectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
        self._scatterSelectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
        self._scatterSelectionBox.setZValue(1e9)
        self._scatterViewbox.addItem(self._scatterSelectionBox, ignoreBounds=True)
        self._scatterSelectionBox.hide()

    def _roiChangedCallback(self):
        self._updateBrushes()

    def _updateBrushes(self):
        brushes = self.getPointBrushes()
        if len(brushes) == len(self.scatterPlot.points()):
            self.scatterPlot.setBrush(brushes)

    def presetROI(self, func=np.std, factor=3):
        """
        Apply the function (default np.mean) to the currently displayed plot data
        to get the x,y values for setting the ROI box.
        :param func: a function applicable to the x,y data
        :return: set the ROI on the scatter plot
        """

        return
        #todo
        x, y = self.scatterPlot.getData()
        if not len(x) > 0 and not len(y) > 0:
            return
        xR = func(x)
        yR = func(y)
        xRange = np.max(x) - np.min(x)
        yRange = np.max(y) - np.min(y)
        xMin = xR - xperc
        yMin = yR - yperc
        xMax = xR + xperc
        yMax = yR + yperc
        self.setROI(xMin, xMax, yMin, yMax)

    def _updateScatterSelectionBox(self, p1: float, p2: float):
        """
        Updates drawing of selection box as mouse is moved.
        """
        vb = self._scatterViewbox
        r = QtCore.QRectF(p1, p2)
        r = vb.childGroup.mapRectFromParent(r)
        self._scatterSelectionBox.setPos(r.topLeft())
        self._scatterSelectionBox.resetTransform()
        self._scatterSelectionBox.scale(r.width(), r.height())
        self._scatterSelectionBox.show()
        minX = r.topLeft().x()
        minY = r.topLeft().y()
        maxX = minX + r.width()
        maxY = minY + r.height()
        return [minX, maxX, minY, maxY]

    def _resetSelectionBox(self):
        "Reset/Hide the boxes "
        self._successiveClicks = None
        self._scatterSelectionBox.hide()
        self._scatterViewbox.rbScaleBox.hide()

    def _clearScatterSelection(self):
        self._selectedData = []
        # self._setPointPens(self._getPointPens())

    def _selectScatterPointsFromCurrent(self):
       pass
        #todo

    def _invertScatterSelection(self):
        pass
        #todo

    def selectByPids(self, pids):

        if len(self.axesDefinitions)>0:
            dataToSelect = []
            itemDef = list(self.axesDefinitions.values())[0]
            pidHeader = getattr(itemDef, _PIDHEADER)
            for pid in pids:
                for point in self.scatterPlot.points():
                    pidPoint = point.data().get(pidHeader)
                    if pid == pidPoint:
                        dataToSelect.append(point.data())
            self.blockSignals(True)
            self.selectedData = dataToSelect
            self.blockSignals(False)

    def getPidsFromPoints(self, points):
        pids = []
        if len(self.axesDefinitions)>0:
            itemDef = list(self.axesDefinitions.values())[0]
            pidHeader = getattr(itemDef, _PIDHEADER)
            for point in points:
                pid = point.data().get(pidHeader)
                pids.append(pid)
        return pids

    def constrainPlot(self, abool):
        if not abool:
            self._scatterViewbox.setLimits(
                                        xMin = None,
                                        xMax = None,
                                        yMin = None,
                                        yMax = None,
                                        minXRange = None,
                                        maxXRange = None,
                                        minYRange = None,
                                        maxYRange = None,
                                        )
        else:
            self.setPlotLimits()

if __name__ == '__main__':
    from PyQt5 import QtGui, QtWidgets
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule
    n = 50

    data = pd.DataFrame({
        'entryValues': np.arange(1, n+1),
        'lengthValues': np.random.rand(n)*33,
        'diameterValues': np.random.rand(n)/10,
        'heightValues': np.random.rand(n)*7.5,
        'buggingScoreValues': np.random.rand(n),
        # 'SpectraPidsValues': np.array(['SP:LadyBug', 'SP:Lice', 'SP:BedBug', 'SP:Flea', 'SP:Mite']),
        # 'HexColoursValues': np.array([list(darkDefaultSpectrumColours.keys())[10]]*n),
    })

    defs = od([
                ( '#', _ItemBC(
                        selectorName = '#',
                        headerValueName = 'entryValues',
                        headerPidName = 'SpectraPidsValues',
                        headerHexColour = 'HexColoursValues',
                        )),
                ('Length', _ItemBC(
                    selectorName='Length',
                    headerValueName='lengthValues',
                    headerPidName='SpectraPidsValues',
                    headerHexColour='HexColoursValues',
                    )),
                ('Score', _ItemBC(
                    selectorName='Score',
                    headerValueName='buggingScoreValues',
                    headerPidName='SpectraPidsValues',
                    headerHexColour='HexColoursValues',
                    )),
                ])


    app = TestApplication()
    win = QtWidgets.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None)
    module = CcpnModule(mainWindow=None, name='Testing Module')
    moduleArea.addModule(module)
    scatterPlot = ScatterPlot(parent=module.mainWidget, application=None,
                              dataFrame=data, axesDefinitions=defs, roiEnabled=True, grid=(0,0))
    # scatterPlot.setAxesDefinitions(defs)
    scatterPlot.selectAxes(xHeader='#', yHeader='Length')
    scatterPlot.roiLimits = [0, 1, 0, 1]
    scatterPlot.setInnerPointColour('#008000') # green
    scatterPlot.setPointSymbol(AllowedSymbols[4])

    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
    win.close()

false = False
if false: # this should never be called from here ###  only run on ipythonConsole
    from collections import OrderedDict as od
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule
    from ccpn.ui.gui.widgets.ScatterPlotWidget import ScatterPlot, _ItemBC
    import numpy as np
    import pandas as pd
    n = 5

    data = pd.DataFrame({
                        'Values0': np.arange(1, n + 1),
                        'Values1': np.random.rand(n),
                        'Values2': np.random.rand(n),
                        'SpectraPids': [sp.pid for sp in project.spectra[:5]]
                        })

    defs = od([
                ('#', _ItemBC(
                    selectorName='#',
                    headerValueName='Values0',
                    headerPidName='SpectraPids',
                    objColourProperty='positiveContourColour',
                )),
                ('Length', _ItemBC(
                    selectorName='Length',
                    headerValueName='Values1',
                    headerPidName='SpectraPids',
                    objColourProperty='positiveContourColour',
                )),
                ('Score', _ItemBC(
                    selectorName='Score',
                    headerValueName='Values2',
                    headerPidName='SpectraPids',
                    objColourProperty='positiveContourColour',
                )),
                ])

    module = CcpnModule(mainWindow=mainWindow, name='Testing Module')
    scatterPlot = ScatterPlot(parent=module.mainWidget, application=application, dataFrame=data, grid=(0,0))
    scatterPlot.setAxesDefinitions(defs)
    scatterPlot.selectAxes(xHeader='#', yHeader='Length')
    mainWindow.moduleArea.addModule(module)
