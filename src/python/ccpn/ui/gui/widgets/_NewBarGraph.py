"""
Module Documentation Here
"""
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
__dateModified__ = "$dateModified: 2023-05-28 11:06:25 +0100 (Sun, May 28, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import getConfigOption
from pyqtgraph import functions as fn
import numpy as np
from ccpn.ui.gui.lib.mouseEvents import \
    leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, \
    middleMouse, shiftMiddleMouse, controlMiddleMouse, controlShiftMiddleMouse, \
    rightMouse, shiftRightMouse, controlRightMouse, controlShiftRightMouse
from ccpn.core.NmrResidue import NmrResidue
from ccpn.ui.gui.widgets.CustomExportDialog import CustomExportDialog
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Logging import getLogger
from ccpn.util.Colour import hexToRgb, rgbaRatioToHex
from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND, \
    GUISTRIP_PIVOT, DIVIDER, CCPNGLWIDGET_SELECTAREA, CCPNGLWIDGET_HIGHLIGHT



class BarItem(object):
    """
    Class referring to individual bar in a BarGraph plot.
    These can be retrieved by calling BarGraph.bars()
    """

    def __init__(self, data, index):

        """

        :param data:
                            dict([
                                ('index', ), bar positional value
                                ('height', ), bar height
                                (xRange ), min, max
                                (yRange ), min, max
                                ('pen', currentPen),
                                ('brush', brush),
                                ('pid', str),  pid for a core object
                                ('item', parent ),
                                ('sourceRect', rect), the qt rect
                                ('width', width)]) the bar width default 1
        :param index:
        """


        self._data = data
        self._index = index

    @property
    def data(self):
        """Return the user data associated with this spot."""
        return self._data['data']

    @property
    def index(self):
        """Return the index of this point as given in the scatter plot data."""
        return self._index

    @property
    def xRange(self):
        """Return the  start and end of x bar."""
        return self._data['xRange']

    @property
    def yRange(self):
        """Return the  start and end of y bar."""
        return self._data['yRange']

    @property
    def height(self):
        """Return the bar height ."""
        return self._data['height']

    @property
    def pid(self):
        """Return the pid for a core object ."""
        return self._data['pid']

    @property
    def width(self):
        """Return the bar width ."""
        return self._data['width']

    def pos(self):
        return pg.Point(self._data['index'], self._data['height'])

class BarGraph(pg.BarGraphItem):

    def __init__(self, xValues=None, yValues=None, pids=None, brushes=None, pens=None,
                 actionCallback=None, selectionCallback=None, hoverCallback=None,
                  **kwds):
        super().__init__(**kwds)

        self._selectionCallback = selectionCallback
        self._actionCallback =  actionCallback
        self._hoverCallback = hoverCallback
        self.trigger = QtCore.pyqtSignal()
        self.xValues = xValues if xValues is not None else []
        self.yValues = yValues if yValues is not None else []
        self.brushes = brushes
        self.pens = pens
        self.pids = pids
        self.itemXRanges = [] #list of tuples, X start stop for the bar each bar in the plot
        self.itemYRanges = [] # list of tuples, Y start stop for the bar each bar in the plot
        self._shapes = {}
        self._barsDict = {}
        self.width = 1
        self.halfWidth = self.width * 0.5

        self.opts = dict(  # setting for BarGraphItem
                x=self.xValues,
                height=self.yValues,
                width=self.width,
                pens=self.pens,
                brushes=self.brushes,
                pids = self.pids,
                )

        self.opts.update(self.opts)


    def _getBarByEvent(self, event):
        # Bar are drawn starting half width before the actual x value. Therefore, the x position has to be back calculated.
        position = event.pos().x()
        height = event.pos().y()
        for _xRange, _yRange in zip(self.itemXRanges, self.itemYRanges):
            startX, stopX = _xRange
            startY, stopY = _yRange
            if startX <= position < stopX and startY <= height <= stopY:
                position = np.mean([startX, stopX])
                bar = self._barsDict.get(position)
                if bar is not None:
                    return bar
        return

    def _getDataForCallback(self, bar, event):

        data = dict([

            ('mousePos', (event.pos().x(), event.pos().y())),
            ('index', bar.index),
            ('height', bar.height),
            ('xRange', bar.xRange),
            ('yRange', bar.yRange),
            ('pid', bar.pid),
            ('parentItem', self),
            ('item', bar),
            ('width', bar.width)])
        return data


    def mouseClickEvent(self, event):
        if bar := self._getBarByEvent(event):
            self.drawPicture(selected=[bar.index]) #highlight by setting the pen  (requires repaint)
            if self._selectionCallback:
                self._selectionCallback(self._getDataForCallback(bar, event))
        if event.button() == QtCore.Qt.LeftButton:
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if self._actionCallback:
            if bar := self._getBarByEvent(event):
                self._actionCallback(self._getDataForCallback(bar, event))
        event.accept()

    def hoverEvent(self, event):
        try:

            if self._hoverCallback:
                if bar := self._getBarByEvent(event):
                    self._hoverCallback(self._getDataForCallback(bar, event))
        except:
            getLogger().debug("Error getting position of a bar from mouse event")

    def drawSelectionBox(self, value):
        region = self._shapes.get(value, [])
        if len(region) == 4:
            brush = self.barColoursDict.get(value)
            x, y, w, h = region
            p = QtGui.QPainter(self.picture)
            self._shape = QtGui.QPainterPath()
            selectedBarPen = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=2)
            p.setPen(selectedBarPen)
            p.setBrush(fn.mkBrush(brush))
            rect = QtCore.QRectF(x, y, w, h)
            p.drawRect(rect)
            self._shape.addRect(rect)

    @property
    def bars(self):
        return list(self._barsDict.values())

    def drawPicture(self, selected=[]):
        self._barsDict.clear()
        self.itemXRanges = []
        self.itemYRanges = []
        self.xValues = []
        self.yValues = []
        self.picture = QtGui.QPicture()
        self._shape = QtGui.QPainterPath()
        p = QtGui.QPainter(self.picture)
        selectedBarPen = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=2)
        pens = self.opts['pens']
        pids = self.opts['pids']

        if pens is None:
            pen = getConfigOption('foreground')
            p.setPen(fn.mkPen(pen))

        def asarray(x):
            if x is None or np.isscalar(x) or isinstance(x, np.ndarray):
                return x
            return np.array(x)

        x = asarray(self.opts.get('x'))
        x0 = asarray(self.opts.get('x0'))
        x1 = asarray(self.opts.get('x1'))
        width = asarray(self.opts.get('width'))



        if x0 is None:
            if width is None:
                raise Exception('must specify either x0 or width')
            if x1 is not None:
                x0 = x1 - width
            elif x is not None:
                x0 = x - width / 2.
            else:
                raise Exception('must specify at least one of x, x0, or x1')
        if width is None:
            if x1 is None:
                raise Exception('must specify either x1 or width')
            width = x1 - x0

        y = asarray(self.opts.get('y'))
        y0 = asarray(self.opts.get('y0'))
        y1 = asarray(self.opts.get('y1'))
        height = asarray(self.opts.get('height'))

        if y0 is None:
            if height is None:
                y0 = 0
            elif y1 is not None:
                y0 = y1 - height
            elif y is not None:
                y0 = y - height / 2.
            else:
                y0 = 0
        if height is None:
            if y1 is None:
                raise Exception('must specify either y1 or height')
            height = y1 - y0

        brushes = self.opts['brushes']
        if brushes is None:
            brush = (128, 128, 128)
            brushes = [brush]*len(x)
        if pids is None:
            pids = [None]*len(x)

        for i in range(len(x0 if not np.isscalar(x0) else y0)):

            if pens is not None:
                pen = pens[i]
                p.setPen(fn.mkPen(pen))
            if brushes is not None:
                brush = brushes[i]
                try:
                    p.setBrush(fn.mkBrush(brush))
                except:
                    getLogger().warning(f'BarGraph error. Cannot find a brush for at position {i}')

            if np.isscalar(pids):
                pid = pids
            else:
                pid = pids[i]

            if np.isscalar(x0):
                x = x0
            else:
                x = x0[i]
            index = x + width/2
            if np.isscalar(y0):
                y = y0
            else:
                y = y0[i]
            if np.isscalar(width):
                w = width
            else:
                w = width[i]
            if np.isscalar(height):
                h = height
            else:
                h = height[i]

            if x+width/2 in selected:
                currentPen = selectedBarPen
            else:
                currentPen = fn.mkPen(pen)
            p.setPen(currentPen)

            rect = QtCore.QRectF(x, y, w, h)
            _xRange = (x, x+w)
            _yRange = (y, h)
            self.itemXRanges.append(_xRange)
            self.itemYRanges.append(_yRange)
            self.xValues.append(index)
            self.yValues.append(h)
            p.drawRect(rect)
            self._shapes[index] = (x, y, w, h)
            self._shape.addRect(rect)
            data = dict([
                ('index', index),
                ('height', h),
                ('xRange', _xRange),
                ('yRange', _yRange),
                ('pen', currentPen),
                ('brush', brush),
                ('pid', pid),
                ('item', self),
                ('sourceRect', rect),
                ('width', w)])
            barItem = BarItem(data, index=index)
            self._barsDict.update({int(index) : barItem})

        p.end()
        self.prepareGeometryChange()



#  Testing




if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    app = TestApplication()


    def _testSelection(data):
        print('SELe: ', data)

    def _testHover(data):
        print('_testHover: ', data)

    x = np.arange(1, 20)
    y = np.random.random(len(x))
    brushes = ['#CD5C5C']*len(x)
    pids = [f'#-{i}'  for i in range(len(x))]
    bars = BarGraph(xValues=x, yValues=y, pids=pids, brushes=brushes, selectionCallback=_testSelection, hoverCallback=_testHover)

    viewBox = pg.ViewBox()
    plotWidget = pg.PlotWidget(viewBox=viewBox)
    viewBox.addItem(bars)

    plotWidget.show()
    app.start()




