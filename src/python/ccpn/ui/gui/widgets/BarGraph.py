"""
Module Documentation Here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-18 18:08:36 +0100 (Thu, August 18, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
from ccpn.util.Common import percentage,groupIntoChunks



current = []

class BarGraph(pg.BarGraphItem):
    def __init__(self, application=None, viewBox=None, xValues=None ,x0Values=None,x1Values=None, yValues=None,
                 objects=None, brush=None, brushes = None, useGradient=False, drawLabels=True, labelDistanceRatio=0.1, **kwds):
        super().__init__(**kwds)
        self.viewBox = viewBox
        self.callback = None
        self.trigger = QtCore.pyqtSignal()
        self.useGradient = useGradient
        self.xValues = xValues if xValues is not None else []
        self.x0Values = x0Values if x0Values is not None else self.xValues
        self.x1Values = x1Values if x1Values is not None else self.xValues
        self.yValues = yValues if yValues is not None else []
        self.brush = brush
        self.brushes = brushes
        self.clicked = None
        self.objects = objects or []
        self.application = application
        self.barColoursDict = {}

        self.opts = dict(  # setting for BarGraphItem
                x=self.xValues,
                x0=self.x0Values,
                x1=self.x1Values,
                height=self.yValues,
                width=1,
                pen=None,
                brush=self.brush,
                pens=None,
                brushes=self.brushes
                )

        self.opts.update(self.opts)
        self.allValues = {}
        self.getValueDict()
        self.labels = []
        if drawLabels:
            self.drawLabels(labelDistanceRatio)
        if self.objects:
            self.setObjects(self.objects)

    def setValues(self, xValues, yValues):
        opts = dict(  # setting for BarGraphItem
                x=xValues,
                x0=self.x0Values,
                x1=self.x1Values,
                height=yValues,
                width=1,
                pen=self.brush,
                brush=self.brush,
                pens=None,
                brushes=self.brushes,
                )
        self.opts.update(opts)

    def setObjects(self, objects, objAttr='pid'):

        if len(self.labels) == len(objects):
            for label, obj in zip(self.labels, objects):
                if isinstance(obj, NmrResidue):
                    nmrResidue = obj
                    if hasattr(nmrResidue, 'sequenceCode'):
                        if nmrResidue.residue:
                            if nmrResidue.sequenceCode is not None:
                                if str(nmrResidue.sequenceCode) == label.text():
                                    label.setData(int(nmrResidue.sequenceCode), obj)
                else:
                    label.setData(0, obj)
                    if objAttr == 'pid':
                        label.setText(obj.pid)
                    else:
                        label.setText(getattr(obj, objAttr, ''))

        # for label in self.labels:
        #     for object in objects:
        #         if isinstance(object, NmrResidue):
        #             nmrResidue = object
        #             if hasattr(nmrResidue, 'sequenceCode'):
        #
        #                 if nmrResidue.residue:
        #                     if nmrResidue.sequenceCode is not None:
        #                         if str(nmrResidue.sequenceCode) == label.text():
        #                             label.setData(int(nmrResidue.sequenceCode), object)
        #         if isinstance(object, Spectrum):
        #             label.setData(str(object.name), object)
        #
        #
        #                 # if nmrResidue.sequenceCode is not None:
        #                 #   ind = nmrResidue.nmrChain.nmrResidues.index(nmrResidue)
        #                 #   lbl = label.text()
        #                 #   if str(ind) == lbl:
        #                 #     label.setData(ind, object)
        #
        #         # else:
        #         # pass
        #         # print('Impossible to set this object to its label. Function implemented only for NmrResidue')

    def getValueDict(self):
        for x, y in zip(self.xValues, self.yValues):
            self.allValues.update({x: y})

    def mouseClickEvent(self, event):

        position = event.pos().x()

        self.clicked = int(position)
        if event.button() == QtCore.Qt.LeftButton:
            for label in self.labels:
                if label.text() == str(self.clicked):
                    label.setSelected(True)

            event.accept()

    def mouseDoubleClickEvent(self, event):

        position = event.pos().x()

        self.doubleclicked = int(position)
        if event.button() == QtCore.Qt.LeftButton:
            for label in self.labels:
                if label.text() == str(self.doubleclicked):
                    print(label.text(), label.data(self.doubleclicked))

        event.accept()

    def drawLabels(self, ratio=0.5):
        """

        The label Text is the str of the x values and is used to find and set an object to it.
        NB, changing the text to any other str may not set the objects correctly!

        """
        self.allLabelsShown = True
        for key, value in self.allValues.items():
            label = CustomLabel(text=str(key))
            self.viewBox.addItem(label)
            label.setPos(int(key), value + ratio)
            self.labels.append(label)
            label.setBrush(QtGui.QColor(self.brush))

    def drawPicture(self):
        self.picture = QtGui.QPicture()
        self._shape = QtGui.QPainterPath()
        p = QtGui.QPainter(self.picture)

        pen = self.opts['pen']
        pens = self.opts['pens']

        if pen is None and pens is None:
            pen = getConfigOption('foreground')

        brush = self.opts['brush']
        brushes = self.opts['brushes']
        if brush is None and brushes is None:
            brush = (128, 128, 128)

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

        p.setPen(fn.mkPen(pen))
        p.setBrush(fn.mkBrush(brush))

        heightGroups = [[height]]
        if brushes and self.useGradient:
            count = len(brushes)
            heightGroups = np.array_split(np.sort(height), count)
        for i in range(len(x0 if not np.isscalar(x0) else y0)):
            if pens is not None:
                p.setPen(fn.mkPen(pens[i]))
            if brushes and not self.useGradient:
                try:
                    p.setBrush(fn.mkBrush(brushes[i]))
                    self.barColoursDict[x] = brushes[i]
                except:
                    getLogger().warn(f'BarGraph error. Cannot find a brush for at position {i}')

            if np.isscalar(x0):
                x = x0
            else:
                x = x0[i]
            self.barColoursDict[x] = brush
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
                if self.useGradient:
                    for heightGroup, brush in zip(heightGroups, brushes):
                        if h in heightGroup:
                            p.setBrush(fn.mkBrush(brush))
                            self.barColoursDict[x]=brush
                            break

            rect = QtCore.QRectF(x, y, w, h)
            p.drawRect(rect)
            self._shape.addRect(rect)

        p.end()
        self.prepareGeometryChange()


class CustomLabel(QtWidgets.QGraphicsSimpleTextItem):
    """ A text annotation of a bar.
        """

    def __init__(self, text, application=None):

        QtWidgets.QGraphicsSimpleTextItem.__init__(self)

        self.setText(text)

        font = self.font()
        font.setPointSize(15)
        self.setRotation(-75)
        self.setFont(font)
        self.setFlag(self.ItemIgnoresTransformations + self.ItemIsSelectable)
        self.setToolTip(text)
        self.isBelowThreshold = False


        self.customObject = self.data(int(self.text()))

        self.application = application

    def setCustomObject(self, obj):
        self.customObject = obj
        self.customObject.customLabel = self

    def getCustomObject(self):
        return self.customObject

    def paint(self, painter, option, widget):
        self._selectCurrent()
        QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, option, widget)

    def _selectCurrent(self):
        if self.text().isdigit():
            if self.data(int(self.text())) is not None:
                if self.application is not None:
                    if self.data(int(self.text())) in self.application.current.nmrResidues:
                        self.setSelected(True)
        #  add other option to use pids/


class CustomViewBox(pg.ViewBox):
    itemsSelected = QtCore.pyqtSignal(object)

    def __init__(self, application=None, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.exportDialog = None
        self.addSelectionBox()
        self.application = application
        self.allLabelsShown = True
        self.showAboveThresholdOnly = False
        self.lastRange = self.viewRange()

        self.__xLine = pg.InfiniteLine(angle=0, movable=True, pen='b')
        self.addItem(self.xLine)
        self.contextMenu = None

    @property
    def xLine(self):
        return self.__xLine

    @xLine.getter
    def xLine(self):
        return self.__xLine

    def addSelectionBox(self):
        self.selectionBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self.selectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
        self.selectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
        self.selectionBox.setZValue(1e9)
        self.addItem(self.selectionBox, ignoreBounds=True)
        self.selectionBox.hide()

    def wheelEvent(self, ev, axis=None):
        if (self.viewRange()[0][1] - self.viewRange()[0][0]) >= 10.001:
            self.lastRange = self.viewRange()
            super(CustomViewBox, self).wheelEvent(ev, axis)
        if (self.viewRange()[0][1] - self.viewRange()[0][0]) < 10:
            self.setRange(xRange=self.lastRange[0])

    def _getLimits(self, p1: float, p2: float):
        r = QtCore.QRectF(p1, p2)
        r = self.childGroup.mapRectFromParent(r)
        self.selectionBox.setPos(r.topLeft())
        self.selectionBox.resetTransform()
        self.selectionBox.scale(r.width(), r.height())
        minX = r.topLeft().x()
        minY = r.topLeft().y()
        maxX = minX + r.width()
        maxY = minY + r.height()
        return minX, maxX, minY, maxY

    def _updateSelectionBox(self, ev, p1: float, p2: float):
        """
        Updates drawing of selection box as mouse is moved.
        """
        r = QtCore.QRectF(p1, p2)
        # print('PPP',dir(self.mapToParent(ev.buttonDownPos())))

        r = self.mapRectFromParent(r)
        self.selectionBox.setPos(self.mapToParent(ev.buttonDownPos()))

        self.selectionBox.resetTransform()
        self.selectionBox.scale(r.width(), r.height())
        self.selectionBox.show()

    def mouseClickEvent(self, event):

        if event.button() == QtCore.Qt.RightButton:
            event.accept()
            self._raiseContextMenu(event)

        elif event.button() == QtCore.Qt.LeftButton:

            event.accept()

    def mouseDragEvent(self, event):
        """
        Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
        drag events. Same as spectrum Display. Check SpectrumDisplay View Box for more documentation.

        """

        selected = []
        if leftMouse(event):
            # Left-drag: Panning of the view
            pg.ViewBox.mouseDragEvent(self, event)
        elif controlLeftMouse(event):
            self._updateSelectionBox(event, event.buttonDownPos(), event.pos())
            event.accept()
            if not event.isFinish():
                self._updateSelectionBox(event, event.buttonDownPos(), event.pos())

            else:  ## the event is finished.
                self._updateSelectionBox(event, event.buttonDownPos(), event.pos())
                minX, maxX, minY, maxY = self._getLimits(event.buttonDownPos(), event.pos())
                labels = [label for label in self.childGroup.childItems() if isinstance(label, CustomLabel)]
                # Control(Cmd)+left drag: selects label
                for label in labels:
                    if int(label.pos().x()) in range(int(minX), int(maxX)):
                        if self.inYRange(label.pos().y(), minY, maxY, ):
                            if self.application is not None:
                                obj = label.data(int(label.pos().x()))
                                if obj is None:
                                    # new mode of setting object.
                                    obj = label.data(0)
                                selected.append(obj)

                self._resetBoxes()

        else:
            self._resetBoxes()
            event.ignore()

        if len(selected) > 0:
            try:
                self.itemsSelected.emit(selected)
                if self.application.current:  # replace this bit
                    currentSelected = getattr(self.application.current, selected[0]._pluralLinkName)
                    selected.extend(currentSelected)
                    currentObjs = setattr(self.application.current, selected[0]._pluralLinkName, selected)
                    self.updateSelectionFromCurrent()
            except Exception as e:
                getLogger().debug('Error in setting current objects. TODO: Replace with itemsSelected Notifier ' + str(e))

    def inYRange(self, yValue, y1, y2):
        if round(y1, 3) <= round(yValue, 3) <= round(y2, 3):
            return True
        return False

    def getLabels(self):
        return [label for label in self.childGroup.childItems() if isinstance(label, CustomLabel)]

    def _selectLabelsByTexts(self, texts):
        if self.getLabels():
            for label in self.getLabels():
                for text in texts:
                    if text == label.text():
                        label.setSelected(True)

    def clearSelection(self):
        for label in self.getLabels():
            label.setSelected(False)

    def updateSelectionFromCurrent(self):
        if self.getLabels():
            for label in self.getLabels():
                for nmrResidue in self.application.current.nmrResidues:
                    if nmrResidue.sequenceCode is not None:
                        if label.data(int(nmrResidue.sequenceCode)):
                            label.setSelected(True)

    def upDateSelections(self, positions):
        if self.getLabels():
            for label in self.getLabels():
                for position in positions:
                    print('Not impl')

    def _resetBoxes(self):
        "Reset/Hide the boxes "
        self._successiveClicks = None
        self.selectionBox.hide()
        self.rbScaleBox.hide()

    def _getContextMenu(self):
        self.contextMenu = Menu('', None, isFloatWidget=True)
        self.contextMenu.addAction('Reset View', self.autoRange)

        ## ThresholdLine
        self.thresholdLineAction = QtGui.QAction("Threshold Line", self, triggered=self._toggleThresholdLine,
                                                 checkable=True, )
        self._checkThresholdAction()
        self.contextMenu.addAction(self.thresholdLineAction)

        ## Labels: Show All
        self.labelsAction = QtGui.QAction("Show Labels", self, triggered=self._toggleLabels, checkable=True, )
        self.labelsAction.setChecked(self.allLabelsShown)
        self.contextMenu.addAction(self.labelsAction)

        ## Labels: Show Above Threshold
        self.showAboveThresholdAction = QtGui.QAction("Show Labels Above Threshold", self,
                                                      triggered=self.showAboveThreshold)
        self.contextMenu.addAction(self.showAboveThresholdAction)

        ## Selection: Select Above Threshold
        self.selectAboveThresholdAction = QtGui.QAction("Select Items Above Threshold", self,
                                                        triggered=self.selectAboveThreshold)
        self.contextMenu.addAction(self.selectAboveThresholdAction)

        self.contextMenu.addSeparator()
        self.contextMenu.addAction('Export', self.showExportDialog)
        return self.contextMenu

    def _raiseContextMenu(self, ev):

        self.contextMenu = self._getContextMenu()
        self.contextMenu.exec_(ev.screenPos().toPoint())

    def _checkThresholdAction(self):
        tl = self.xLine
        if tl:
            if tl.isVisible():
                self.thresholdLineAction.setChecked(True)
            else:
                self.thresholdLineAction.setChecked(False)

    def addLabelMenu(self):
        self.labelMenu = Menu(parent=self.contextMenu, title='Label Menu')
        self.labelMenu.addItem('Show All', callback=self.showAllLabels,
                               checked=False, checkable=True, )
        self.labelMenu.addItem('Hide All', callback=self.hideAllLabels,
                               checked=False, checkable=True, )
        self.labelMenu.addItem('Show Above Threshold', callback=self.showAboveThreshold,
                               checked=False, checkable=True, )

        self.contextMenu._addQMenu(self.labelMenu)

    def _toggleThresholdLine(self):
        tl = self.xLine
        if tl:
            tl.setVisible(not tl.isVisible())

    def _toggleLabels(self):

        if self.allLabelsShown:
            self.hideAllLabels()
        else:
            self.showAllLabels()

    def getThreshouldLine(self):
        if hasattr(self, 'xLine'):
            return self.xLine

    def hideAllLabels(self):
        self.allLabelsShown = False
        self.showAboveThresholdOnly = False
        if self.getLabels():
            for label in self.getLabels():
                label.hide()

    def showAllLabels(self):
        self.allLabelsShown = True
        self.showAboveThresholdOnly = False
        if self.getLabels():
            for label in self.getLabels():
                label.show()

    def showAboveThreshold(self):
        self.allLabelsShown = False
        self.showAboveThresholdOnly = True
        if self.xLine:
            yTlPos = self.xLine.pos().y()
            if self.getLabels():
                for label in self.getLabels():
                    if label.pos().y() >= yTlPos:
                        label.show()
                    else:
                        label.hide()
                        label.isBelowThreshold = True
        else:
            print('NOT FOUND')

    def selectAboveThreshold(self):
        """Reimplement this in the module subclass"""

        pass

    def showExportDialog(self):
        if self.exportDialog is None:
            ### parent() is the graphicsScene
            self.exportDialog = CustomExportDialog(self.scene(), titleName='Exporting')
        self.exportDialog.show(self)

######################################################################################################
###################################      Mock DATA    ################################################
######################################################################################################

from collections import namedtuple
import random

nmrResidues = []
for i in range(30):
  nmrResidue = namedtuple('nmrResidue', ['sequenceCode'])
  nmrResidue.__new__.__defaults__ = (0,)
  nmrResidue.sequenceCode = int(random.randint(1,300))
  nmrResidues.append(nmrResidue)

x1 = [nmrResidue.sequenceCode for nmrResidue in nmrResidues]
y1 = [(i**random.random())/10 for i in range(len(x1))]


xLows = []
yLows = []

xMids = []
yMids = []

xHighs = []
yHighs = []


for x, y in zip(x1,y1):
    if y <= 0.5:
        xLows.append(x)
        yLows.append(y)
    if y > 0.5 and y <= 1:
        xMids.append(x)
        yMids.append(y)
    if y > 1:
        xHighs.append(x)
        yHighs.append(y)

######################################################################################################

app = pg.mkQApp()

customViewBox = CustomViewBox()
#
plotWidget = pg.PlotWidget(viewBox=customViewBox, background='w')
customViewBox.setParent(plotWidget)

x=[
    6,
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    24,
    26,
    28,
    30,
    36,
    48,
    60
   ]

y = [
    1.731,
    20.809,
    10.658,
    400.831,
    11.406,
    5.287,
    2.971,
    400.412,
    10.731,
    20.809,
    100.658,
    400.831,
    110.406,
    50.287,
    20.971,
    400.412,
    ]


L = 'abcdefghilmnopqrstuvz'
x = np.arange(1,len(L))
ticks = [list(zip(x, L))]
y = np.random.normal(1,100,len(L))
y = np.absolute(y)
gradientName = 'gray-black'
from ccpn.util.Colour import colorSchemeTable
brushes = colorSchemeTable[gradientName]



if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    app = TestApplication()
    window = QtWidgets.QWidget()
    window.setLayout(QtWidgets.QGridLayout())


    xax = plotWidget.getAxis('bottom')
    xticks = list(x)+list(xMids)+list(xHighs)
    xLabelTicks = [f'{str(i)}_abcd' for i in xticks]
    xLabelTicksNumb = [int(i)+1 for i in range(len(xLabelTicks))]

    # ticks = [list(zip(xLabelTicksNumb, xLabelTicks))]

    # xax.setTicks(ticks)
    xLow = BarGraph(window,
                    viewBox=customViewBox, xValues=x-0.5,
                    yValues=y, objects=[], brushes=brushes, useGradient=True,
                    drawLabels=False,
                    widht=1)
    # xMid = BarGraph(viewBox=customViewBox, xValues=xMids, yValues=yMids, objects=[nmrResidues], brush='b', widht=1)
    # xHigh = BarGraph(viewBox=customViewBox, xValues=xHighs, yValues=yHighs, objects=[nmrResidues], brush='g', widht=1)

    customViewBox.addItem(xLow)
    # customViewBox.addItem(xMid)
    # customViewBox.addItem(xHigh)

    # xLine = pg.InfiniteLine(pos=max(yLows), angle=0, movable=True, pen='b')
    # customViewBox.addItem(xLine)

    l = pg.LegendItem((100,60), offset=(70,30))  # args are (size, offset)
    l.setParentItem(customViewBox.graphicsItem())

    c1 = plotWidget.plot(pen='r', name='low')
    # c2 = plotWidget.plot(pen='b', name='mid')
    # c3 = plotWidget.plot(pen='g', name='high')

    l.addItem(c1, 'low')
    # l.addItem(c2, 'mid')
    # l.addItem(c3, 'high')

    # customViewBox.setLimits(xMin=0, xMax=max(x1) + (max(x1) * 0.5), yMin=0, yMax=max(y1) + (max(y1) * 0.5))
    customViewBox.setRange(xRange=[10,200], yRange=[0.01,1000],)
    customViewBox.setMenuEnabled(enableMenu=False)

    plotWidget.show()

    window.show()
    window.raise_()

    app.start()


#
# # Start Qt event
# if __name__ == '__main__':
#   import sys
#   if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#     QtWidgets.QApplication.instance().exec_()


