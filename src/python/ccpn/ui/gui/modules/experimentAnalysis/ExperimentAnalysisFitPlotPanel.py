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
__dateModified__ = "$dateModified: 2022-08-15 16:47:20 +0100 (Mon, August 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ROI import MouseDragHandler, Handle
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.widgets.Font import Font, getFont,getFontHeight
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Label import Label
from collections import OrderedDict as od
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Action import Action
from ccpn.core.Peak import Peak
from ccpn.ui.gui.widgets.ViewBox import CrossHair
from ccpn.util.Common import percentage
from ccpn.core.lib.Notifiers import Notifier

class ExperimentAnalysisPlotToolBar(ToolBar):

    def __init__(self, parent, plotItem, **kwds):
        super().__init__(parent=parent, **kwds)
        self.plotItem = plotItem
        self.plotItem.toolbar = self
        self.setToolActions(self._defaultToolBarDefs())
        self.setMaximumHeight(30)

    def setToolActions(self, actionDefinitions):
        for v in actionDefinitions:
            if len(v) == 2:
                if isinstance(v[1], od):
                    action = Action(self, **v[1])
                    action.setObjectName(v[0])
                    self.addAction(action)
            else:
                self.addSeparator()

    def _defaultToolBarDefs(self):
        toolBarDefs = (
            ('Zoom-All', od((
                ('text', 'Zoom-All'),
                ('toolTip', 'Zoom All Axes'),
                ('icon', Icon('icons/zoom-full')),
                ('callback', self.plotItem.zoomFull),
                ('enabled', True)
                ))),
            ('Zoom-X', od((
                ('text', 'Zoom-X-axis'),
                ('toolTip', 'Reset X-axis to fit view'),
                ('icon', Icon('icons/zoom-full-1d')),
                ('callback', self.plotItem.fitXZoom),
                ('enabled', True)
            ))),
            ('Zoom-Y', od((
                ('text', 'Zoom-Y-axis'),
                ('toolTip', 'Reset Y-axis to fit view'),
                ('icon', Icon('icons/zoom-best-fit-1d')),
                ('callback', self.plotItem.fitYZoom),
                ('enabled', True)
            ))),
            (),
            )
        return toolBarDefs


class LeftAxisItem(pg.AxisItem):
    """ Overridden class for the left axis to show minimal decimals and stop resizing to massive space.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(orientation='left', *args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        """ Overridden method to show minimal decimals.
        """
        return [f'{v:.4f}' for v in values]

class FittingHandle(Handle):
    """Experimental.  A class to allow manual refitting of a curve based.  """

    sigMoved = QtCore.Signal(object)  # pos
    sigHovered = QtCore.Signal(object)  # ev

    def __init__(self, parentPlot=None, radius=8, typ='s', pen=(200, 200, 220),  deletable=False):
        super().__init__(radius, typ, pen=pen, parent=parentPlot, deletable=deletable)
        self.parentPlot = parentPlot
        self.pen.setWidth(2)
        self.hoverPen = pg.functions.mkPen((255, 255, 0), width=2, style=QtCore.Qt.SolidLine)

    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.LeftButton:
            return
        ev.accept()
        if ev.isFinish():
            if self.isMoving:
                pos = self.mapToParent(ev.pos())
                self.setPos(pos)
                self.sigMoved.emit([pos.x(), pos.y()])
            self.isMoving = False
        elif ev.isStart():
            self.isMoving = True
            pos = self.mapToParent(ev.pos())
            self.setPos(pos)
            self.sigMoved.emit([pos.x(), pos.y()])
        if self.isMoving:  ## note: isMoving may become False in mid-drag due to right-click.
            pos = self.mapToParent(ev.pos())
            self.setPos(pos)
            self.sigMoved.emit([pos.x(), pos.y()])

    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            if ev.acceptDrags(QtCore.Qt.LeftButton):
                hover = True
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MidButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover = True
        if hover:
            self.currentPen = self.hoverPen
            self.sigHovered.emit(ev)
        else:
            self.currentPen = self.pen
        self.update()

    def mouseClickEvent(self, ev):
        print('Testing HANDLE CLICKED', ev)
        self.sigClicked.emit(self, ev)


class FittingPlot(pg.PlotItem):
    def __init__(self, parentWidget, *args, **kwargs):
        pg.PlotItem.__init__(self, axisItems={'left': LeftAxisItem()}, **kwargs)
        self.parentWidget = parentWidget

        colour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self.gridPen = pg.functions.mkPen(colour, width=1, style=QtCore.Qt.SolidLine)
        self.gridFont = getFont()
        self.toolbar = None
        self.setMenuEnabled(False)
        self.getAxis('bottom').setPen(self.gridPen)
        self.getAxis('left').setPen(self.gridPen)
        self.getAxis('bottom').tickFont = self.gridFont
        self.getAxis('left').tickFont = self.gridFont
        self._bindingPlotViewbox = self.vb
        self._bindingPlotViewbox.mouseClickEvent = self._viewboxMouseClickEvent
        self.autoBtn.mode = None
        self.buttonsHidden = True
        self.autoBtn.hide()
        self.crossHair = CrossHair(plotWidget=self)
        self.fittingHandle = FittingHandle(pen=self.gridPen)
        self.fittingHandle.sigMoved.connect(self._handleMoved)
        self.fittingHandle.sigHovered.connect(self._handleHovered)
        self.fittingHandle.sigClicked.connect(self._handleClicked)
        self.addItem(self.fittingHandle)

    def _handleMoved(self, pos, *args):
        self.parentWidget._replot(**{'pos':pos})

    def _handleHovered(self, *args):
        # Action to be decided: maybe a tooltip of what it can do.
        pass

    def _handleClicked(self, *args):
        # Action to be decided. maybe open a context menu gor right-click?
        pass

    def clear(self):
        """
        Remove all items from the ViewBox.
        """
        for i in self.items[:]:
            if not isinstance(i, (pg.InfiniteLine,Handle)):
                self.removeItem(i)
        self.avgCurves = {}

    def setToolbar(self, toolbar):
        self.toolbar = toolbar

    def zoomFull(self):
        self.fitXZoom()
        self.fitYZoom()

    def fitXZoom(self):
        xs,ys = self._getPlotData()
        if len(xs)>0:
            x,y = xs[-1], ys[-1]
            xMin, xMax = min(x), max(x)
            self.setXRange(xMin, xMax, padding=None, update=True)

    def fitYZoom(self):
        xs, ys = self._getPlotData()
        if len(xs) > 0:
            x, y = xs[-1], ys[-1]
            yMin, yMax = min(y), max(y)
            self.setYRange(yMin, yMax, padding=None, update=True)

    def _getPlotData(self):
        xs = []
        ys = []
        for item in self.dataItems:
            if hasattr(item, 'getData'):
                x,y = item.getData()
                xs.append(x)
                ys.append(y)
        return xs,ys

    def mouseDoubleClickEvent(self, *args):
        print('Under implementation. _mouseDoubleClickEvent on bindingPlot ', args)

    def mouseClickEvent(self, *args):
        print('Under implementation. _mouseClickEvent on bindingPlot ', args)

    def _viewboxMouseClickEvent(self, *args):
        print('Under implementation. _viewboxMouseClickEvent on bindingPlot ', args)

    def mouseMoved(self, event):
        position = event
        mousePoint = self._bindingPlotViewbox.mapSceneToView(position)
        x = mousePoint.x()
        y = mousePoint.y()
        self.crossHair.setPosition(x, y)
        label = f'x:{round(x,3)} \ny:{round(y,3)}'
        self.crossHair.hLine.label.setText(label)


class _CustomLabel(QtWidgets.QGraphicsSimpleTextItem):
    """ A text annotation of a scatterPlot.
        """
    def __init__(self, obj, textProperty='pid', labelRotation = 0, application=None):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self)
        self.textProperty = textProperty
        self.obj = obj
        self.displayProperty(self.textProperty)
        self.setRotation(labelRotation)
        # self.setDefaultFont() #this oddly set the font to everything in the program!
        self.setBrushByObject()
        self.setFlag(self.ItemIgnoresTransformations + self.ItemIsSelectable)
        self.application = application

    def setDefaultFont(self):
        font = getFont()
        # height = getFontHeight(size='SMALL') #SMALL is still to large
        font.setPointSize(10)
        self.setFont(font) #this oddly set the font to everything in the program!

    def setBrushByObject(self):
        brush = None
        if isinstance(self.obj, Peak):
            brush = pg.functions.mkBrush(hexToRgb(self.obj.peakList.textColour))
        if brush:
            self.setBrush(brush)

    def displayProperty(self, theProperty):
        text = getattr(self.obj, theProperty)
        self.setText(str(text))
        self.setToolTip(f'Displaying {theProperty} for {self.obj}')

    def setObject(self, obj):
        self.obj = obj

    def getCustomObject(self):
        return self.customObject

    def paint(self, painter, option, widget):
        # self._selectCurrent()
        QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, option, widget)

class FitPlotPanel(GuiPanel):

    position = 2
    panelName = 'FitPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, showBorder=True, *args , **Framekwargs)
        self.fittedCurve = None #not sure if this var should Exist


    def initWidgets(self):

        self.backgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self._setExtraWidgets()
        self._selectCurrentCONotifier = Notifier(self.current, [Notifier.CURRENT], targetName='collections',
                                                 callback=self._currentCollectionCallback, onceOnly=True)

    def setXLabel(self, label=''):
        self.bindingPlot.setLabel('bottom', label)

    def setYLabel(self, label=''):
        self.bindingPlot.setLabel('left', label)

    def _setExtraWidgets(self):
        ###  Plot setup
        self._bindingPlotView = pg.GraphicsLayoutWidget()
        self._bindingPlotView.setBackground(self.backgroundColour)
        self.bindingPlot = FittingPlot(parentWidget=self)
        self.toolbar = ExperimentAnalysisPlotToolBar(parent=self, plotItem=self.bindingPlot,
                                                     grid=(0, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')
        self.currentCollectionLabel = Label(self, text='', grid=(0, 2), hAlign='r',)
        self._bindingPlotView.addItem(self.bindingPlot)
        self.getLayout().addWidget(self._bindingPlotView, 1,0,1,3)

    def _replot(self,  *args, **kwargs):
        pass

    def _currentCollectionCallback(self, *args):
        self.plotCurrentData()

    def plotCurve(self, xs, ys):
        self.clearData()
        self.bindingPlot.plot(xs, ys)

    def clearData(self):
        self.bindingPlot.clear()

    def close(self):
        self._selectCurrentCONotifier.unRegister()