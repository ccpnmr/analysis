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
from ccpn.util.Colour import hexToRgb, rgbaRatioToHex, darkDefaultSpectrumColours
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
from ccpn.util.Common import _getObjectsByPids

# colours
BackgroundColour = gs.getColours()[gs.CCPNGLWIDGET_HEXBACKGROUND]
OriginAxes = pg.functions.mkPen(hexToRgb(gs.getColours()[gs.GUISTRIP_PIVOT]), width=1, style=QtCore.Qt.DashLine)
SelectedPoint = pg.functions.mkPen(rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_HIGHLIGHT]), width=4)
ROIline = rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_SELECTAREA])
DefaultRoi = [[0, 0], [10, 10]]  #

SelectedLabel = pg.functions.mkBrush(rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_HIGHLIGHT]), width=4)
c =rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_LABELLING])
GridPen = pg.functions.mkPen(c, width=1, style=QtCore.Qt.SolidLine)
GridFont = getFont()
DefaultSpotSize = 15
DefaultSpotColour = '#FF0000' # red
DefaultSymbol = 's'

_SELECTORNAME = 'selectorName'
_VALUEHEADER = 'headerValueName'
_PIDHEADER = 'headerPidName'
_TOOLTIP = 'tooltip'
_HEXCOLOURHEADER = 'headerHexColour'
_OBJCOLOURPROPERTY = 'objColourProperty'
_SYMBOL = 'symbol'
_CALLBACK = 'callback'
_SPOTSIZE = 'spotSize'
_HEXCOLOUR = 'hexColour'

class _ItemBC(object):
    ''' '''

    def __init__(self, headerValueName, **kwargs):
        '''
        Used to set the spots/axis in the plot
        :param kwargs:

        '''
        self.kwargs = {
                       _SELECTORNAME      : headerValueName,
                       _VALUEHEADER       : headerValueName,
                       _PIDHEADER         : None,
                       _HEXCOLOURHEADER   : None,
                       _OBJCOLOURPROPERTY : None, # the obj property where to grab the colour. E.g for spectrum: sliceColour
                       _SYMBOL            : DefaultSymbol,
                       _SPOTSIZE          : DefaultSpotSize,
                       _HEXCOLOUR         : DefaultSpotColour,
                       }
        self.kwargs.update(kwargs)
        for k, v in self.kwargs.items():
            setattr(self, k, v)

class ScatterPlot(Widget):
    def __init__(self,
                 application,
                 dataFrame,
                 axesDefinitions = None,
                 roiVisible = True,
                 mouseSelectionRegion = True,
                 spotSelectionCallback = None,
                 spotActionCallback = None,
                 **kwds):
        super().__init__(setLayout=True, **kwds)

        self.application = application
        self.project = None
        if self.application:
            self.project = self.application.project
        self._dataFrame = dataFrame
        self._roiData = DefaultRoi
        self.axesDefinitions = axesDefinitions
        self.setAxesDefinitions(self.axesDefinitions, updateWidgets=False)
        self._scatterView = pg.GraphicsLayoutWidget()
        self._scatterView.setBackground(BackgroundColour)
        self._plotItem = self._scatterView.addPlot()
        self._scatterViewbox = self._plotItem.vb
        self._addScatterSelectionBox()
        self._scatterViewbox.mouseClickEvent = self._scatterViewboxMouseClickEvent # click on the background canvas
        self._scatterViewbox.mouseDragEvent = self._scatterMouseDragEvent
        self._scatterViewbox.scene().sigMouseMoved.connect(self.mouseMoved) #use this if you need the mouse Posit
        self._plotItem.setMenuEnabled(False)
        self._exportDialog = None
        self.scatterPlot = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0))
        # self.scatterPlot.sigClicked.connect(self._plotClicked)
        self.scatterPlot.mouseClickEvent = self._scatterMouseClickEvent
        self.scatterPlot.mouseDoubleClickEvent = self._scatterMouseDoubleClickEvent
        setWidgetFont(self)
        ## adjustable ROI box
        self.roiItem = pg.ROI(*DefaultRoi, pen=ROIline)
        self._setROIhandles()
        self.roiItem.sigRegionChangeFinished.connect(self.getROIdata)
        self._plotItem.addItem(self.roiItem)
        self.xLine = pg.InfiniteLine(angle=90, pos=0, pen=OriginAxes)
        self.yLine = pg.InfiniteLine(angle=0, pos=0, pen=OriginAxes)
        self.spotSelectionCallback = spotSelectionCallback # single click
        self.spotActionCallback = spotActionCallback # double click
        self._plotItem.addItem(self.scatterPlot)
        self._plotItem.addItem(self.xLine)
        self._plotItem.addItem(self.yLine)
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

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self.dataFrame = dataFrame

    @property
    def roiData(self) -> list:
        """
        :return: a list of 4 elements: [xMin, xMax, yMin, yMax]
        """
        self._roiData = self.getROIdata()
        return self._roiData

    @roiData.setter
    def roiData(self, data):
        """
        :param data: list of 4 elements: [xMin, xMax, yMin, yMax]
        :return: None, set the roiData and update its plotItem.
        """
        if len(data) != 4:
            getLogger().warn('ROI Data must be a list of 4 elements: [xMin, xMax, yMin, yMax]')
            return
        self._roiData = data
        self._setROI(*data)

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
        self.scatterPlot.updateSpots()

    def addPoints(self, x=None, y=None, spots=None, **kwargs):

        """
        used to add points to the scatterPlot.
        If only x,y is given, all the other parameters are set as default.
        To set each property use spots or define the kwargs.
        X,Y can also be define in spots or kwargs constructs as "pos", see below.
        In that case is not necessary to set x,y as individual args, and can be left as None.

        :param x:  1D arrays of x,y values
        :param y:  1D arrays of x,y values
        :param spots:  Optional list of dicts. Each dict specifies parameters for a single spot:
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
                pen                    The pen (or list of pens) to use for drawing spot outlines.
                brush                  The brush (or list of brushes) to use for filling spots.
                size                   The size (or list of sizes) of spots.
                data                   a list of python objects used to uniquely identify each spot.
                name                   The name of this item. Names are used for automatically
                                       generating LegendItem entries and by some exporters.
        """
        self.scatterPlot.clear()
        args = []
        if spots is not None:
            args = [spots]
        if x is not None and y is not None:
            args = [x, y]
        if not kwargs.get(_SYMBOL) in ['o', 's', 't', 'd', '+']:
            getLogger().warning('Symbol not available. Used the default instead')
            kwargs.update({_SYMBOL:'o'})
        self.scatterPlot.addPoints(*args, **kwargs)

    def setupContextMenu(self):
        """
        :return: Subclass this to insert/remove items in bespoke plots.
        """
        items = []
        items += self._getDefaultMenuItems()
        items += self._getExportMenuItems()
        menu = cm._createMenu(self, items)

    def _axisSelectionCallback(self, *args):
        """
        Callback from pulldown selectors. Adds Points to the plot based on the dataframe columns.
        Objects are set from pids if defined in the dataframe and definitions
        Colours are set from objs if they have the in their class property or if specified in the
        :param args:
        :return:
        """
        self.scatterPlot.clear()
        self._setPlotItemLabels()

        _xItem = self.axesDefinitions.get(self.yAxisSelector.getText())
        _yItem = self.axesDefinitions.get(self.yAxisSelector.getText())
        if not all([_xItem, _yItem]): return

        x_ValueHeader = getattr(_xItem, _VALUEHEADER)
        y_ValueHeader = getattr(_yItem, _VALUEHEADER)
        pidHeader = getattr(_xItem, _PIDHEADER)
        objColourProperty = getattr(_xItem, _OBJCOLOURPROPERTY)
        hexHeader = getattr(_xItem, _HEXCOLOURHEADER)
        symbol = getattr(_xItem, _SYMBOL)
        size = getattr(_xItem, _SPOTSIZE)
        defaultHex = getattr(_xItem, _HEXCOLOUR)
        hexs = [defaultHex] * len(self.dataFrame.index)

        if objColourProperty is not None: # use the obj for getting the colour info (if defined)
            pidDf = self.dataFrame.get(pidHeader)
            if pidDf is not None and self.project:
                ccpnObjs = _getObjectsByPids(self.project, pidDf.values)
                hexs = [getattr(o, objColourProperty)  for o in ccpnObjs]
        else:
            if hexHeader is not None: # use the dedicated colour Header for getting the colour info (if defined)
                hexDf = self.dataFrame.get(hexHeader)
                if hexDf is not None:
                    hexs = hexDf.values
        brushes = [pg.functions.mkBrush(hexToRgb(hx)) for hx in hexs]
        indices, series = map(list,zip(*self.dataFrame.iterrows()))
        # this is used for creating a selection pattern around the scatter item
        pens = [SelectedPoint if i in [j.name for j in self._selectedData] else None for i in indices]

        xDf = self.dataFrame.get(x_ValueHeader)
        yDf = self.dataFrame.get(y_ValueHeader)
        if xDf is not None and yDf is not None:
            xValues = xDf.values
            yValues = yDf.values
            if len(xValues) == len(yValues):
                self.addPoints(x=xValues, y=yValues, size=size, symbol=symbol, brush=brushes, data=series, pen=pens)
            else:
                Widgets.MessageDialog.showWarning('Error displaying data',
                                        'Values lenght mismatch')

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

    def _raiseScatterContextMenu(self, ev):
        """ Creates all the menu items for the scatter context menu. """
        self.setupContextMenu()
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
        :param items:  list of pg.SpotItem type
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
            if self.spotActionCallback is not None:
                self.spotActionCallback(callbackData)
            ev.accept()
        else:
            # "no spots, needs to clear selection"
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
                if self.spotSelectionCallback is not None:
                    self.spotSelectionCallback(callbackData)
                self._selectedData = _data
                self.scatterPlot.setPen([None] * len(self.dataFrame.index)) # clear first
                setPens = [pt.setPen(SelectedPoint) for pt in pts]
                ev.accept()
            elif me.controlLeftMouse(ev):
                # Control-left-click;  add to selection
                if self.spotSelectionCallback is not None:
                    self.spotSelectionCallback(callbackData)
                self._selectedData += _data
                setPens = [pt.setPen(SelectedPoint) for pt in pts]
                ev.accept()
            else:
                ev.ignore()
        else:
            #need to clear selection
            self._selectedData = []
            self.scatterPlot.setPen([None]*len(self.dataFrame.index))
            ev.accept()

    def mouseMoved(self, event):
        """
        use this if you need for example display the mouse coords on display
        :param event:
        :return:
        """
        position = event
        if self._scatterViewbox.sceneBoundingRect().contains(position):
            mousePoint = self._scatterViewbox.mapSceneToView(position)
            x = mousePoint.x()
            y =  mousePoint.y()
            self.coordinatesLabel.setText("x=%0.2f, y=%0.2f" % (x, y))

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
                pts = self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
                df = self.dataFrame
                print(pts)
                #todo add the data
                # if self.decomposition:
                #     i, o = self.decomposition.splitDataWithinRange(self.getPcaResults(),
                #                                                    *self._getSelectedAxesLabels(), *pts)
                #     self._selectedObjs.extend(i.index)
                #     self._selectScatterPoints()
                self._resetSelectionBox()
        else:
            self._resetSelectionBox()
            event.ignore()

    def toggleROI(self):
        """
        show/hide ROI from the plot
        """
        self.roiItem.setVisible(not self.roiItem.isVisible())

    def _addScatterSelectionBox(self):
        self._scatterSelectionBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self._scatterSelectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
        self._scatterSelectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
        self._scatterSelectionBox.setZValue(1e9)
        self._scatterViewbox.addItem(self._scatterSelectionBox, ignoreBounds=True)
        self._scatterSelectionBox.hide()


    ########### ROI box for scatter Plot ############

    def _roiPresetCallBack(self, *args):
        v = self.roiMethodPulldown.getObject()
        perc = self.roiPercValue.get()
        self.presetROI(v, perc)

    def _roiMouseActionCallBack(self, *args):
        """ called by the context menu. Sets the settings checkbox, The settings CB will do the actual work"""
        self.roiCheckbox.set(not self.roiCheckbox.get())
        self._toggleROI()

    def _toggleROI(self, *args):
        """ Toggle the ROI from the scatter plot"""
        v = self.roiCheckbox.get()
        if v:
            self.roiItem.show()
        else:
            self.roiItem.hide()

    def _setROIhandles(self):
        """ sets the handle in each corners, no matter the roiItem sizes """
        self.roiItem.addScaleHandle([1, 1], [0.5, 0.5], name='topRight')
        self.roiItem.addScaleHandle([0, 1], [1, 0], name='topLeft')
        self.roiItem.addScaleHandle([0, 0], [0.5, 0.5], name='bottomLeft')
        self.roiItem.addScaleHandle([1, 0], [0, 1], name='bottomRight'),

    def getROIdata(self):
        """
        the values for the ROI
        (getState returns a dict ['pos']  left bottom corner, ['size'] the size of RO1 and ['angle'] for this RectROI is 0)
        :return: a list of rectangle coordinates in the format minX, maxX, minY, maxY
        """
        state = self.roiItem.getState()
        pos = state['pos']
        size = state['size']
        xMin = pos[0]
        xMax = pos[0] + size[0]
        yMin = pos[1]
        yMax = pos[1] + size[1]
        return [xMin, xMax, yMin, yMax]

    def presetROI(self, func=np.median, percent=20):
        """
        Apply the function (default np.mean) to the currently displayed plot data
        to get the x,y values for setting the ROI box.
        :param func: a function applicable to the x,y data
        :return: set the ROI on the scatter plot
        """

        x, y = self.scatterPlot.getData()
        if not len(x) > 0 and not len(y) > 0:
            return

        xR = func(x)
        yR = func(y)
        xRange = np.max(x) - np.min(x)
        yRange = np.max(y) - np.min(y)

        xperc = percentage(percent, xRange)
        yperc = percentage(percent, yRange)

        xMin = xR - xperc
        yMin = yR - yperc
        xMax = xR + xperc
        yMax = yR + yperc

        self.setROI(xMin, xMax, yMin, yMax)

    def _setROI(self, xMin, xMax, yMin, yMax):
        """
        a conversion mechanism to the internal roiItem setState
        :return:  set the ROI box
        """
        state = {'pos': [], 'size': [], 'angle': 0}
        xSize = abs(xMin) + xMax
        ySize = abs(yMin) + yMax
        state['pos'] = [xMin, yMin]
        state['size'] = [xSize, ySize]
        self.roiItem.setState(state)

    def _selectFromROI(self):

        scores = self.getPcaResults()
        if scores is not None:
            roi = self.getROIdata()
            i, o = self.decomposition.splitDataWithinRange(scores, *self._getSelectedAxesLabels(), *roi)
            if i is not None:
                self._selectedObjs = i.index
                self._selectScatterPoints()

    def _createGroupFromROI(self, inside=True):
        pass
        # TODO

        # xsel = self.xAxisSelector.get()
        # ysel = self.yAxisSelector.get()
        # xl = PC + str(xsel)
        # yl = PC + str(ysel)
        # scores = self.getPcaResults()
        # if scores is not None:
        #     roiItem = self.getROIdata()
        #     i, o = self.decomposition.splitDataWithinRange(scores, xl, yl, *roiItem)
        #     if inside:
        #         self.decomposition.createSpectrumGroupFromScores(list(i.index))
        #     else:
        #         self.decomposition.createSpectrumGroupFromScores(list(i.index))

    def _axisChanged(self, *args):
        """callback from axis pulldowns which will replot the scatter"""
        pass
        #TODO
        # self.plotPCAscatterResults(self.getPcaResults(), *self._getSelectedAxesLabels(), selectedObjs=self._selectedObjs)

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
        self._selectedObjs = []
        self._selectScatterPoints()

    def _selectScatterPoints(self):
        self.scatterPlot.clear()
        if self.current:
            self.current.pcaComponents = self._selectedObjs  # does selection through notifier
        else:  # does still selection. E.g. if used as stand alone module
            self.plotPCAscatterResults(self.getPcaResults(), *self._getSelectedAxesLabels(), selectedObjs=self._selectedObjs)

    def _invertScatterSelection(self):
        invs = [point.data() for point in self.scatterPlot.points() if point.data() not in self._selectedObjs]
        self._selectedObjs = invs
        self._selectScatterPoints()

    def _getObjFromPoints(self, points=None):
        if points is None:
            points = self.scatterPlot.points()
        df = pd.DataFrame(points, index=[point.data() for point in points], columns=['item'])
        return df

if __name__ == '__main__':
    from PyQt5 import QtGui, QtWidgets
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule
    n = 500

    data = pd.DataFrame({
        'entryValues': np.arange(1, n+1),
        'lengthValues': np.random.rand(n)*33,
        'diameterValues': np.random.rand(n)/10,
        'heightValues': np.random.rand(n)*7.5,
        'buggingScoreValues': np.random.rand(n),
        # 'SpectraPidsValues': np.array(['SP:LadyBug', 'SP:Lice', 'SP:BedBug', 'SP:Flea', 'SP:Mite']),
        # 'HexColoursValues': np.array(list(darkDefaultSpectrumColours.keys())[:n]),
    })

    defs = od([
                ( '#', _ItemBC(
                        selectorName = '#',
                        headerValueName = 'entryValues',
                        headerPidName = 'SpectraPids',
                        headerHexColour = 'HexColoursValues',
                        objColourProperty = None,
                        spotSize = DefaultSpotSize,
                        symbol = DefaultSymbol
                        )),
                ('Length', _ItemBC(
                    selectorName='Length',
                    headerValueName='lengthValues',
                    headerPidName='SpectraPids',
                    headerHexColour='HexColoursValues',
                    objColourProperty=None,
                    spotSize=DefaultSpotSize,
                    symbol=DefaultSymbol
                    )),
                ('Score', _ItemBC(
                    selectorName='Score',
                    headerValueName='buggingScoreValues',
                    headerPidName='SpectraPids',
                    headerHexColour='HexColoursValues',
                    objColourProperty = None,
                    spotSize=DefaultSpotSize,
                    symbol=DefaultSymbol
                    )),
                ])


    app = TestApplication()
    win = QtWidgets.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None)
    module = CcpnModule(mainWindow=None, name='Testing Module')
    moduleArea.addModule(module)
    scatterPlot = ScatterPlot(parent=module.mainWidget, application=None, dataFrame=data, axesDefinitions=defs, grid=(0,0))
    # scatterPlot.setAxesDefinitions(defs)
    scatterPlot.selectAxes(xHeader='#', yHeader='Length')
    scatterPlot.roiData = [0,1,0,10]


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