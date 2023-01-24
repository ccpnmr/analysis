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
__dateModified__ = "$dateModified: 2023-01-24 15:00:38 +0000 (Tue, January 24, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui, QtCore
from ccpn.ui.gui.widgets.BarGraph import BarGraph, CustomViewBox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import getColours
from ccpn.util.Colour import hexToRgb, rgbaRatioToHex

AboveX = 'aboveX'
AboveY = 'aboveY'
BelowX = 'belowX'
BelowY = 'belowY'
DisappearedX = 'disappearedX'
DisappearedY = 'disappearedY'
ErrorHeight = 'errorHeight'
AboveObjects = 'aboveObjects'
AllAboveObjects = 'allAboveObjects'
AllBelowObjects = 'allBelowObjects'
BelowObjects = 'belowObjects'
DisappearedObjects = 'disappearedObjects'
AboveBrush = 'aboveBrush'
AboveBrushes = 'aboveBrushes'
BelowBrush = 'belowBrush'
DisappearedBrush = 'disappearedBrush'
DrawLabels = 'drawLabels'
AllTicks  = 'All Ticks'
MinimalTicks = 'Minimal Ticks'
TICKOPTIONS = [MinimalTicks, AllTicks]


class XBarAxisItem(pg.AxisItem):
    def __init__(self, labelRotation=-90, outward=True, *args, **kwargs):
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

class YBarAxisItem(pg.AxisItem):
    def __init__(self,  outward=False, *args, **kwargs):
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


class BarGraphWidget(Widget):

    def __init__(self, parent, application=None, xValues=None, yValues=None, colour='r', actionCallback=None,
                 selectionCallback=None, hoverCallback=None, objects=None, threshouldLine=0, backgroundColour='w',
                 selectionBoxEnabled=True, **kwds):
        super().__init__(parent, **kwds)

        self.application = application
        self.backgroundColour = backgroundColour
        self.thresholdLineColour = 'b'
        self._selectionBoxEnabled = selectionBoxEnabled
        self._setViewBox()
        self._setLayout()
        self.setContentsMargins(1, 1, 1, 1)
        self.barGraphs = []
        self.xValues = xValues
        self.yValues = yValues
        self.objects = objects
        self.colour = colour
        self.aboveBrush = 'g'
        self.belowBrush = 'r'
        self.disappearedBrush = 'b'
        self.threshouldLine = threshouldLine
        self._hoverBox = pg.TextItem(text='', anchor=(-0.1,0.1), angle=0, border='w', fill=(0, 0, 255, 100))
        self._hoverBox.hide()
        self._hoverBoxEnabled = False
        self.setData(viewBox=self.customViewBox, xValues=xValues, yValues=yValues, objects=objects, colour=colour, replace=True)
        self.xLine = self.customViewBox.xLine
        self.customViewBox.addItem(self.xLine)
        self.setThresholdLine()
        self._actionCallback = actionCallback
        self._selectionCallback = selectionCallback
        self._hoverCallback = hoverCallback
        self._tickOption = MinimalTicks # one of AllTicks or MinimalTicks
        # plot.addItem(text)
        self.errorBars = None
        colour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self.errorBarsPen = pg.functions.mkPen(colour, width=1, style=QtCore.Qt.SolidLine)

        self._dataDict = {
            AboveX            : [],
            AboveY            : [],
            AboveBrush        : 'g',
            AboveObjects      : [],
            AllAboveObjects   : [],
            BelowX            : [],
            BelowY            : [],
            BelowBrush        : 'r',
            BelowObjects      : [],
            DisappearedX      : [],
            DisappearedY      : [],
            DisappearedBrush  : 'b',
            DisappearedObjects: [],
            DrawLabels        : True
            }

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

    def _getDefaultPlotLimits(self):
        """ Get the limits for x and y axes to best fit the data as tuple of tuple
         (xMin, xMax), (yMin, yMax)"""
        import numpy as np
        xs, ys = self.getPlotData()
        if len(xs) == 0:
            return
        xMin, xMax = int(np.min(xs)), int(np.max(xs))
        yMin, yMax = np.min(ys), np.max(ys)
        if yMin > 0:
            yMin = 0
        else:
            yMin += yMin / 2
        xMax += xMax / 2
        yMax += yMax / 2
        return (xMin, xMax), (yMin, yMax)

    def setDefaultPlotLimits(self):
        limits = self._getDefaultPlotLimits()
        if limits is None:
            return
        xLims, yLims = limits
        self.setLimits(xMin=xLims[0], xMax=xLims[1], yMin=yLims[0], yMax=yLims[1])

    def zoomFull(self):
        self.plotWidget.autoRange()

    def setLimits(self, **kwargs):
        """
       Set limits that constrain the possible view ranges.

        **Panning limits**. The following arguments define the region within the
        viewbox coordinate system that may be accessed by panning the view.

        =========== ============================================================
        xMin        Minimum allowed x-axis value
        xMax        Maximum allowed x-axis value
        yMin        Minimum allowed y-axis value
        yMax        Maximum allowed y-axis value
        =========== ============================================================

        **Scaling limits**. These arguments prevent the view being zoomed in or
        out too far.

        =========== ============================================================
        minXRange   Minimum allowed left-to-right span across the view.
        maxXRange   Maximum allowed left-to-right span across the view.
        minYRange   Minimum allowed top-to-bottom span across the view.
        maxYRange   Maximum allowed top-to-bottom span across the view.
        =========== ============================================================

        :return:
        """
        self.plotWidget.setLimits(**kwargs)

    def fitXZoom(self):
        xs, ys = self._getPlotData()
        xRange, yRange = self.customViewBox.viewRange()
        xm, xM = xRange
        if len(xs) > 0:
            xAll = [a for j in xs for a in j]
            xAll = np.array(xAll)
            xAll.sort()
            masked = np.ma.masked_inside(xAll, xm, xM)
            filtered = xAll[masked.mask]
            # filter for only the visible range.
            if len(filtered)>0:
                _max = np.max(filtered)
                _min = np.min(filtered)
                self.plotWidget.setXRange(_min, _max)
            else:
                self.zoomFull()

    def fitYZoom(self):
        """"""
        xs, ys = self._getPlotData()
        xRange, yRange = self.customViewBox.viewRange()
        xm, xM = xRange
        if len(ys) > 0:
            yAll = [a for j in ys for a in j]
            yAll = np.array(yAll)
            xAll = [a for j in xs for a in j]
            xAll = np.array(xAll)
            # filter for only the visible range.
            masked = np.ma.masked_inside(xAll, xm, xM)
            filtered = yAll[masked.mask]
            yMin = np.min(filtered)
            if yMin > 0:
                yMin = 0
            else:
                yMin += yMin / 2
            if len(filtered) > 0:
                self.plotWidget.setYRange(yMin,  np.max(filtered))
            else:
                self.zoomFull()

    def setTickOption(self, value):
        if value in TICKOPTIONS:
            self._tickOption = value

    def _setViewBox(self):
        self.customViewBox = CustomViewBox(application=self.application)
        self.customViewBox.setMenuEnabled(enableMenu=False)  # override pg default context menu
        self.plotWidget = pg.PlotWidget(viewBox=self.customViewBox, background=self.backgroundColour)
        self.plotWidget.setAxisItems({'bottom': XBarAxisItem(orientation='bottom'), 'left': YBarAxisItem(orientation='left')})
        self.customViewBox.setParent(self.plotWidget)

    def _setLayout(self):
        hbox = QtWidgets.QHBoxLayout()
        self.setLayout(hbox)
        hbox.addWidget(self.plotWidget)
        hbox.setContentsMargins(1, 1, 1, 1)

    def _addExtraItems(self):
        # self.addLegend()
        self.setThresholdLine()

    def getPlottedColoursDict(self):
        """ A dict for each tick return index as key and colour as value"""
        dd = {}
        for i in self.plotWidget.items():
            if isinstance(i, BarGraph):
               dd.update(i.barColoursDict)
        return dict(sorted(dd.items()))

    def setData(self, viewBox, xValues, yValues, objects, colour, replace=True):
        if replace:
            self.barGraphs = []
            self.customViewBox.clear()

        self.barGraph = BarGraph(viewBox=viewBox, actionCallback = self._mouseDoubleClickCallback,
                                 selectionCallback=self._mouseSingleClickCallback, application=self.application,
                                 xValues=xValues, yValues=yValues, objects=objects, brush=colour)
        self.barGraphs.append(self.barGraph)
        self.customViewBox.addItem(self.barGraph)
        self.customViewBox.addItem(self._hoverBox)
        self.customViewBox._selectionBoxEnabled = self._selectionBoxEnabled
        self.xValues = xValues
        self.yValues = yValues
        self.objects = objects
        self.updateViewBoxLimits()

    def _mouseDoubleClickCallback(self, x, y):
        self._selectBarNumbers(selected=[x])
        if self._actionCallback:
            self._actionCallback(x,y)

    def _mouseSingleClickCallback(self, x, y):
        self._selectBarNumbers(selected=[x])
        if self._selectionCallback:
            self._selectionCallback(x,y)

    def _selectBarNumbers(self, selected=[]):
        """ Redraw with selected items """
        for bar in self.barGraphs:
            bar.drawPicture(selected)

    def _mouseHoverCallback(self, barIndex, x, y):
        if self._hoverCallback:
            self._hoverCallback(barIndex, x, y)
            if self._hoverBoxEnabled:
                self._hoverBox.show()
                self._hoverBox.setPos(x,y)
            else:
                self._hoverBox.hide()


    def setViewBoxLimits(self, xMin, xMax, yMin, yMax):
        self.customViewBox.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def updateViewBoxLimits(self):
        """Updates with default parameters. Minimum values to show the data only
        """
        if self.xValues and self.yValues:
            self.customViewBox.setLimits(xMin=min(self.xValues) / 2, xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                         yMin=min(self.yValues) / 2, yMax=max(self.yValues) + (max(self.yValues) * 0.5),
                                         )
        else:
            xValues = []
            yValues = []
            for bar in self.barGraphs:
                xValues.extend(bar.xValues)
                yValues.extend(bar.yValues)

            if xValues and yValues:
                self.customViewBox.setLimits(xMin=0, xMax=max(xValues)*2, yMin=min(yValues), yMax=max(yValues)*2)


    def setXRange(self, xMin, xMax, padding=None, update=True):
        self.customViewBox.setXRange(xMin, xMax, padding=padding, update=update)

    def setYRange(self, yMin, yMax, padding=None, update=True):
        self.customViewBox.setYRange(yMin, yMax, padding=padding, update=update)


    def clear(self):

        for item in self.customViewBox.addedItems:
            if not isinstance(item, pg.InfiniteLine):
                self.customViewBox.removeItem(item)
        for ch in self.customViewBox.childGroup.childItems():
            if not isinstance(ch, pg.InfiniteLine):
                self.customViewBox.removeItem(ch)

    def clearBars(self):
        self.barGraphs = []
        for item in self.customViewBox.addedItems:
            if not isinstance(item, pg.InfiniteLine):
                self.customViewBox.removeItem(item)

    def setThresholdLine(self):

        # self.thresholdValueTextItem = pg.TextItem(str(self.xLine.pos().y()), anchor=(self.customViewBox.viewRange()[0][0], 1.0),)
        # self.thresholdValueTextItem.setParentItem(self.xLine)
        # self.thresholdValueTextItem.setBrush(QtGui.QColor(self.thresholdLineColour))
        if self.yValues is not None:
            if len(self.yValues) > 0:
                self.xLine.setPos(self.threshouldLine)
        self.showThresholdLine(True)
        self.xLine.sigPositionChangeFinished.connect(self._lineMoved)
        # self.xLine.setToolTip(str(round(self.xLine.pos().y(), 4)))
        self.xLine.sigPositionChanged.connect(self._updateTextLabel)

    def _updateTextLabel(self):
        # self.thresholdValueTextItem.setText(str(round(self.xLine.pos().y(),3)))#, color=self.thresholdLineColour)
        self.xLine.setToolTip(str(round(self.xLine.pos().y(), 4)))

    def showThresholdLine(self, value=True):
        if value:
            self.xLine.show()
        else:
            self.xLine.hide()

    def _lineMoved(self, **args):
        self.clear()
        drawLabels = True
        if len(args) > 0:
            aboveX = args[AboveX]
            aboveY = args[AboveY]
            disappearedX = args[DisappearedX]
            disappearedY = args[DisappearedY]
            aboveObjects = args[AboveObjects]
            belowX = args[BelowX]
            belowY = args[BelowY]
            errorHeights = args.get(ErrorHeight, {})
            belowObjects = args[BelowObjects]
            disappearedObjects = args[DisappearedObjects]
            self.aboveBrush = args[AboveBrush]
            aboveBrushes = args.get(AboveBrushes, [])
            self.belowBrush = args[BelowBrush]
            self.disappearedBrush = args[DisappearedBrush]
            drawLabels = args.get(DrawLabels)

        else:
            aboveX = []
            aboveY = []
            aboveObjects = []
            belowX = []
            belowY = []
            belowObjects = []
            disappearedX = []
            disappearedY = []
            disappearedObjects = []
            aboveBrushes = []
            errorHeights = {}
            pos = self.xLine.pos().y()
            self.xLine.show()
            if self.xValues:
                for x, y, obj in zip(self.xValues, self.yValues, self.objects):
                    if y > pos:
                        aboveY.append(y)
                        aboveX.append(x)
                        aboveObjects.append(obj)
                    else:
                        belowX.append(x)
                        belowY.append(y)
                        belowObjects.append(obj)
        aboveX = np.array(aboveX) - 0.5 #need -0.5 to center the bar to the tick on axis
        belowX = np.array(belowX) - 0.5
        disappearedX = np.array(disappearedX) - 0.5
        if len(aboveBrushes)>0:
            self.aboveThreshold = BarGraph(viewBox=self.customViewBox, application=self.application,
                                           drawLabels=drawLabels, actionCallback=self._mouseDoubleClickCallback,
                                           selectionCallback=self._mouseSingleClickCallback,
                                           hoverCallback = self._mouseHoverCallback,
                                           xValues=aboveX, yValues=aboveY,
                                           objects=aboveObjects, useGradient=True, brushes=aboveBrushes)
        else:
            self.aboveThreshold = BarGraph(viewBox=self.customViewBox, application=self.application,
                                           drawLabels=drawLabels,
                                           actionCallback=self._mouseDoubleClickCallback,
                                           selectionCallback=self._mouseSingleClickCallback,
                                           hoverCallback=self._mouseHoverCallback,
                                           xValues=aboveX, yValues=aboveY, objects=aboveObjects, brush=self.aboveBrush)
        self.belowThreshold = BarGraph(viewBox=self.customViewBox, application=self.application,
                                       actionCallback=self._mouseDoubleClickCallback, drawLabels=drawLabels,
                                       selectionCallback=self._mouseSingleClickCallback,
                                       hoverCallback=self._mouseHoverCallback,
                                       xValues=belowX, yValues=belowY, objects=belowObjects, brush=self.belowBrush)
        self.disappearedPeaks = BarGraph(viewBox=self.customViewBox, application=self.application, drawLabels=drawLabels,
                                         actionCallback=self._mouseDoubleClickCallback,
                                         selectionCallback=self._mouseSingleClickCallback,
                                         hoverCallback=self._mouseHoverCallback,
                                         xValues=disappearedX, yValues=disappearedY, objects=disappearedObjects,
                                         brush=self.disappearedBrush)
        xErr = errorHeights.get('xError', np.array([]))
        yErr = errorHeights.get('yError', np.array([]))
        topErr = errorHeights.get('topError', np.array([]))
        topErr = topErr.astype(float)
        top = np.nan_to_num(topErr)
        self.errorBars = pg.ErrorBarItem(x=xErr, y=yErr, top=top, beam=0.5, pen=self.errorBarsPen)
        self.customViewBox.addItem(self.errorBars)
        self.customViewBox.addItem(self.aboveThreshold)
        self.customViewBox.addItem(self.belowThreshold)
        self.customViewBox.addItem(self.disappearedPeaks)

        self.customViewBox.addItem(self._hoverBox)
        self.customViewBox._selectionBoxEnabled = self._selectionBoxEnabled
        self.barGraphs.append(self.aboveThreshold)
        self.barGraphs.append(self.belowThreshold)
        self.barGraphs.append(self.disappearedPeaks)
        self.updateViewBoxLimits()
        if self.customViewBox.allLabelsShown:
            self.customViewBox.showAllLabels()
        if self.customViewBox.showAboveThresholdOnly:
            self.customViewBox.showAboveThreshold()
        self.setDefaultPlotLimits()

    def addLegend(self):
        self.legendItem = pg.LegendItem((100, 60), offset=(70, 30))  # args are (size, offset)
        self.legendItem.setParentItem(self.customViewBox.graphicsItem())

    def addLegendItem(self, pen='r', name=''):
        c = self.plotWidget.plot(pen=pen, name=name)
        self.legendItem.addItem(c, name)

    def showLegend(self, value: False):
        if value:
            self.legendItem.show()
        else:
            self.legendItem.hide()

#######################################################################################################
####################################      Mock DATA TESTING    ########################################
#######################################################################################################
#
from collections import namedtuple
import random

nmrResidues = []
for i in range(30):
  nmrResidue = namedtuple('nmrResidue', ['sequenceCode','peaksShifts'])
  nmrResidue.__new__.__defaults__ = (0,)
  nmrResidue.sequenceCode = i
  nmrResidue.peaksShifts = random.uniform(1.5, 3.9)
  nmrResidues.append(nmrResidue)

nmrChain = namedtuple('nmrChain', ['nmrResidues'])
nmrChain.nmrResidues = nmrResidues



if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
  from ccpn.ui.gui.modules.ChemicalShiftsMappingModule import ChemicalShiftsMapping

  app = TestApplication()
  win = QtGui.QMainWindow()

  moduleArea = CcpnModuleArea(mainWindow=None, )
  chemicalShiftsMapping = ChemicalShiftsMapping(mainWindow=None, nmrChain=nmrChain)
  moduleArea.addModule(chemicalShiftsMapping)




  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % chemicalShiftsMapping.moduleName)
  win.show()

  app.start()
