"""
Module Documentation Here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
from pyqtgraph.Point import Point

from ccpn.ui.gui.lib.mouseEvents import \
    leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, \
    middleMouse, shiftMiddleMouse, controlMiddleMouse, controlShiftMiddleMouse, \
    rightMouse, shiftRightMouse, controlRightMouse, controlShiftRightMouse
from ccpn.core.NmrResidue import NmrResidue
from ccpn.ui.gui.widgets.CustomExportDialog import CustomExportDialog
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Logging import getLogger


current = []


#TODO:LUCA: this is most likely yours; update with documentation and check for ViewBox __init__ as it has changed

class BarGraph(pg.BarGraphItem):
    def __init__(self, application=None, viewBox=None, xValues=None, yValues=None,
                 objects=None, brush=None, **kwds):
        super().__init__(**kwds)
        '''
        This class allows top draw bars with or without objects.It Needs only xValues and yValues.
        The bar width is by default set to 1.
        The objects are linked to the bars through the label annotations (with setData).
        '''
        # TODO:
        # setObjects in a more general way. Initially implemented only for NmrResidues objects.

        self.viewBox = viewBox
        self.callback = None
        self.trigger = QtCore.pyqtSignal()
        self.xValues = xValues or []
        self.yValues = yValues or []
        self.brush = brush
        self.clicked = None
        self.objects = objects or []
        self.application = application
        # self.application = QtCore.QCoreApplication.instance()._ccpnApplication

        self.opts = dict(  # setting for BarGraphItem
                x=self.xValues,
                x0=self.xValues,
                x1=self.xValues,
                height=self.yValues,
                width=1,
                pen=self.brush,
                brush=self.brush,
                pens=None,
                brushes=None,
                )

        self.opts.update(self.opts)
        self.allValues = {}
        self.getValueDict()
        self.labels = []
        self.drawLabels()
        if self.objects:
            self.setObjects(self.objects)

    def setValues(self, xValues, yValues):
        opts = dict(  # setting for BarGraphItem
                x=xValues,
                x0=xValues,
                x1=xValues,
                height=yValues,
                width=1,
                pen=self.brush,
                brush=self.brush,
                pens=None,
                brushes=None,
                )
        self.opts.update(opts)

    def setObjects(self, objects):

        for label in self.labels:
            for object in objects:
                if isinstance(object, NmrResidue):
                    nmrResidue = object
                    if hasattr(nmrResidue, 'sequenceCode'):

                        if nmrResidue.residue:
                            if nmrResidue.sequenceCode is not None:
                                if str(nmrResidue.sequenceCode) == label.text():
                                    label.setData(int(nmrResidue.sequenceCode), object)

                        # if nmrResidue.sequenceCode is not None:
                        #   ind = nmrResidue.nmrChain.nmrResidues.index(nmrResidue)
                        #   lbl = label.text()
                        #   if str(ind) == lbl:
                        #     label.setData(ind, object)

                # else:
                # pass
                # print('Impossible to set this object to its label. Function implemented only for NmrResidue')

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

    def drawLabels(self):
        '''

        The label Text is the str of the x values and is used to find and set an object to it.
        NB, changing the text to any other str may not set the objects correctly!

        '''
        self.allLabelsShown = True
        for key, value in self.allValues.items():
            label = CustomLabel(text=str(key))
            self.viewBox.addItem(label)
            label.setPos(int(key), value)
            self.labels.append(label)
            label.setBrush(QtGui.QColor(self.brush))


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
        # self.application = QtCore.QCoreApplication.instance()._ccpnApplication

        self.application = application

    def setCustomObject(self, obj):
        self.customObject = obj
        self.customObject.customLabel = self

    def getCustomObject(self):
        return self.customObject

    def paint(self, painter, option, widget):
        self._selectCurrentNmrResidue()
        QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, option, widget)

    def _selectCurrentNmrResidue(self):

        if self.data(int(self.text())) is not None:

            if self.application is not None:

                if self.data(int(self.text())) in self.application.current.nmrResidues:
                    self.setSelected(True)


class CustomViewBox(pg.ViewBox):
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


    def _getLimits(self,p1:float, p2:float):
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

    def _updateSelectionBox(self,ev, p1:float, p2:float):
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
        drag events. Same as spectrum Display. Check Spectrum Display View Box for more documentation.

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
                                selected.append(obj)

                self._resetBoxes()

        else:
            self._resetBoxes()
            event.ignore()

        if len(selected) > 0:
            try:
                currentObjs = setattr(self.application.current, selected[0]._pluralLinkName, selected)
                self.updateSelectionFromCurrent()
            except Exception as e:
                getLogger().warning('Error in setting current objects. ' + str(e))


    def inYRange(self, yValue, y1, y2):
        if round(y1, 3) <= round(yValue, 3) <= round(y2, 3):
            return True
        return False

    def getLabels(self):
        return [label for label in self.childGroup.childItems() if isinstance(label, CustomLabel)]

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

    def _raiseContextMenu(self, ev):

        self.contextMenu = Menu('', None, isFloatWidget=True)
        self.contextMenu.addAction('Reset View', self.autoRange)

        ## ThresholdLine
        self.thresholdLineAction = QtGui.QAction("Threshold Line", self, triggered=self._toggleThresholdLine, checkable=True, )
        self._checkThresholdAction()
        self.contextMenu.addAction(self.thresholdLineAction)

        ## Labels: Show All
        self.labelsAction = QtGui.QAction("Show Labels", self, triggered=self._toggleLabels, checkable=True, )
        self.labelsAction.setChecked(self.allLabelsShown)
        self.contextMenu.addAction(self.labelsAction)

        ## Labels: Show Above Threshold
        self.showAboveThresholdAction = QtGui.QAction("Show Labels Above Threshold", self, triggered=self.showAboveThreshold)
        self.contextMenu.addAction(self.showAboveThresholdAction)

        ## Selection: Select Above Threshold
        self.selectAboveThresholdAction = QtGui.QAction("Select Items Above Threshold", self,
                                                        triggered=self.selectAboveThreshold)
        self.contextMenu.addAction(self.selectAboveThresholdAction)

        self.contextMenu.addSeparator()
        self.contextMenu.addAction('Export', self.showExportDialog)
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
        '''Reimplement this in the module subclass'''

        pass

    def showExportDialog(self):
        if self.exportDialog is None:
            ### parent() is the graphicsScene
            self.exportDialog = CustomExportDialog(self.scene(), titleName='Exporting')
        self.exportDialog.show(self)

######################################################################################################
###################################      Mock DATA    ################################################
######################################################################################################

# from collections import namedtuple
# import random
#
# nmrResidues = []
# for i in range(30):
#   nmrResidue = namedtuple('nmrResidue', ['sequenceCode'])
#   nmrResidue.__new__.__defaults__ = (0,)
#   nmrResidue.sequenceCode = int(random.randint(1,300))
#   nmrResidues.append(nmrResidue)
#
# x1 = [nmrResidue.sequenceCode for nmrResidue in nmrResidues]
# y1 = [(i**random.random())/10 for i in range(len(x1))]
#
#
# xLows = []
# yLows = []
#
# xMids = []
# yMids = []
#
# xHighs = []
# yHighs = []
#
#
# for x, y in zip(x1,y1):
#     if y <= 0.5:
#         xLows.append(x)
#         yLows.append(y)
#     if y > 0.5 and y <= 1:
#         xMids.append(x)
#         yMids.append(y)
#     if y > 1:
#         xHighs.append(x)
#         yHighs.append(y)
#
# ######################################################################################################
#
# app = pg.mkQApp()
#
# customViewBox = CustomViewBox()
# #
# plotWidget = pg.PlotWidget(viewBox=customViewBox, background='w')
# customViewBox.setParent(plotWidget)
#
# x=[6,
#     8,
#     10,
#     12,
#     14,
#     16,
#     18,
#     20]
# y = [
# 1.731,
# 10.809,
# 10.658,
# 4.831,
# 11.406,
# 5.287,
# 2.971,
# 4.412,
# ]
#
# xLow = BarGraph(viewBox=customViewBox, xValues=x, yValues=y, objects=[], brush='r', widht=1)
# # xMid = BarGraph(viewBox=customViewBox, xValues=xMids, yValues=yMids, objects=[nmrResidues], brush='b',widht=1)
# # xHigh = BarGraph(viewBox=customViewBox, xValues=xHighs, yValues=yHighs,objects=[nmrResidues],  brush='g',widht=1)
#
#
# customViewBox.addItem(xLow)
# # customViewBox.addItem(xMid)
# # customViewBox.addItem(xHigh)
#
# # xLine = pg.InfiniteLine(pos=max(yLows), angle=0, movable=True, pen='b')
# # customViewBox.addItem(xLine)
#
# l = pg.LegendItem((100,60), offset=(70,30))  # args are (size, offset)
# l.setParentItem(customViewBox.graphicsItem())
#
# c1 = plotWidget.plot(pen='r', name='low')
# # c2 = plotWidget.plot(pen='b', name='mid')
# # c3 = plotWidget.plot(pen='g', name='high')
#
# l.addItem(c1, 'low')
# # l.addItem(c2, 'mid')
# # l.addItem(c3, 'high')
#
# # customViewBox.setLimits(xMin=0, xMax=max(x1) + (max(x1) * 0.5), yMin=0, yMax=max(y1) + (max(y1) * 0.5))
# customViewBox.setRange(xRange=[10,200], yRange=[0.01,1000],)
# customViewBox.setMenuEnabled(enableMenu=False)
# print(customViewBox.xLine._viewBox)
# plotWidget.show()
#
#
#
#
#
#
# # Start Qt event
# if __name__ == '__main__':
#   import sys
#   if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#     QtWidgets.QApplication.instance().exec_()
#
#
