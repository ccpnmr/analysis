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
__dateModified__ = "$dateModified: 2022-08-09 18:58:05 +0100 (Tue, August 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from collections import OrderedDict as od
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Action import Action

class FmtAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        """ Overridden method to show minimal decimals.
        """
        return [f'{v:.4f}' for v in values]

class FittingPlot(pg.PlotItem):
    def __init__(self, parentWidget, toolbar, *args, **kwargs):
        pg.PlotItem.__init__(self, axisItems={'left': FmtAxisItem(orientation='left')}, **kwargs)
        self.parentWidget = parentWidget

        colour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self.gridPen = pg.functions.mkPen(colour, width=1, style=QtCore.Qt.SolidLine)
        self.gridFont = getFont()
        self.toolbar = toolbar
        self.toolbar.setMaximumHeight(30)
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
        self._setToolBar()

    def _setToolBar(self):
        for v in self._getToolBarDefs():
            if len(v) == 2:
                if isinstance(v[1], od):
                    action = Action(self, **v[1])
                    action.setObjectName(v[0])
                    self.toolbar.addAction(action)
            else:
                self.toolbar.addSeparator()

    def _getToolBarDefs(self):
        toolBarDefs = (
            ('Zoom-All', od((
                ('text', 'Zoom-All'),
                ('toolTip', 'Zoom All Axes'),
                ('icon', Icon('icons/zoom-full')),
                ('callback', self.zoomFull),
                ('enabled', True)
                ))),
            ('Zoom-X', od((
                ('text', 'Zoom-X-axis'),
                ('toolTip', 'Reset X-axis to fit view'),
                ('icon', Icon('icons/zoom-full-1d')),
                ('callback', self.fitXZoom),
                ('enabled', True)
            ))),
            ('Zoom-Y', od((
                ('text', 'Zoom-Y-axis'),
                ('toolTip', 'Reset Y-axis to fit view'),
                ('icon', Icon('icons/zoom-best-fit-1d')),
                ('callback', self.fitYZoom),
                ('enabled', True)
            ))),
            (),

            )
        return toolBarDefs

    def _getPlotData(self):
        xs = []
        ys = []
        for item in self.dataItems:
            if hasattr(item, 'getData'):
                x,y = item.getData()
                xs.append(x)
                ys.append(y)
        return xs,ys

    def zoomFull(self):
        self.autoRange()

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

    def mouseDoubleClickEvent(self, *args):
        print('Under implementation. _mouseDoubleClickEvent on bindingPlot ', args)

    def mouseClickEvent(self, *args):
        print('Under implementation. _mouseClickEvent on bindingPlot ', args)

    def _viewboxMouseClickEvent(self, *args):
        print('Under implementation. _viewboxMouseClickEvent on bindingPlot ', args)

class FitPlotPanel(GuiPanel):

    position = 2
    panelName = 'FitPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, showBorder=True, *args , **Framekwargs)


    def initWidgets(self):

        self.backgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self.originAxesPen = pg.functions.mkPen(hexToRgb(getColours()[GUISTRIP_PIVOT]), width=1,
                                                style=QtCore.Qt.DashLine)
        self.fittingLinePen = pg.functions.mkPen(hexToRgb(getColours()[DIVIDER]), width=0.5, style=QtCore.Qt.DashLine)
        self.selectedPointPen = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
        self.selectedLabelPen = pg.functions.mkBrush(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
        self._setBindingPlot()

    def setXLabel(self, label=''):
        self.bindingPlot.setLabel('bottom', label)

    def setYLabel(self, label=''):
        self.bindingPlot.setLabel('left', label)

    def _setBindingPlot(self):
        ###  Plot setup
        self._bindingPlotView = pg.GraphicsLayoutWidget()
        self._bindingPlotView.setBackground(self.backgroundColour)
        self.toolbar = ToolBar(self, grid=(0, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')
        self.bindingPlot = FittingPlot(parentWidget=self, toolbar=self.toolbar)
        self._bindingPlotView.addItem(self.bindingPlot)
        self.getLayout().addWidget(self._bindingPlotView)


    def plotCurve(self, xs, ys):
        self.clearData()
        self.bindingPlot.plot(xs, ys)

    def clearData(self):
        self.bindingPlot.clear()
