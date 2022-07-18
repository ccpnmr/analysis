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
__dateModified__ = "$dateModified: 2022-07-18 11:29:58 +0100 (Mon, July 18, 2022) $"
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
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.util.Common import percentage

class XBarAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self.style = {
            'tickTextOffset': [5, 1],  ## (horizontal, vertical) spacing between text and axis
            'tickTextWidth': 15,  ## space reserved for tick text
            'tickTextHeight': 9,
            'autoExpandTextSpace': True,  ## automatically expand text space if needed
            'tickFont': None,
            'stopAxisAtTick': (False, False),  ## whether axis is drawn to edge of box or to last tick
            'textFillLimits': [  ## how much of the axis to fill up with tick text, maximally.
                (0, 0.8),  ## never fill more than 80% of the axis
                (2, 0.6),  ## If we already have 2 ticks with text, fill no more than 60% of the axis
                (4, 0.4),  ## If we already have 4 ticks with text, fill no more than 40% of the axis
                (6, 0.2),  ## If we already have 6 ticks with text, fill no more than 20% of the axis
            ],
            'showValues': True,
            'tickLength': 5,
            'maxTickLevel': 1,
            'maxTextLevel': 1,
        }
        self.textWidth = 15  ## Keeps track of maximum width / height of tick text
        self.textHeight = 9

    def mouseDragEvent(self, event):
        pass

    # def tickStrings(self, values, scale, spacing):
    #     strings = []
    #     for v in values:
    #         # vs is the original tick value
    #         vs = v * scale
    #         # if we have vs in our values, show the string
    #         # otherwise show nothing
    #         if vs in self.x_values:
    #             # Find the string with x_values closest to vs
    #             vstr = self.x_strings[np.abs(self.x_values - vs).argmin()]
    #         else:
    #             vstr = ""
    #         strings.append(vstr)
    #     return strings

    # def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
    #     p.setRenderHint(p.Antialiasing, False)
    #     p.setRenderHint(p.TextAntialiasing, True)
    #
    #     ## draw long line along axis
    #     pen, p1, p2 = axisSpec
    #     p.setPen(pen)
    #     p.drawLine(p1, p2)
    #     p.translate(0.5,0)  ## resolves some damn pixel ambiguity
    #
    #     ## draw ticks
    #     for pen, p1, p2 in tickSpecs:
    #         extra = 0# px.  percentage(10, p1.x()) #make the tick at
    #         p1.setX(p1.x() + extra)
    #         p2.setX(p2.x() + extra)
    #         p.setPen(pen)
    #         p.drawLine(p1, p2)
    #
    #     ## Draw all text
    #     if self.tickFont is not None:
    #         p.setFont(self.tickFont)
    #     p.setPen(self.pen())
    #     font = QtGui.QFont()
    #     font.setPixelSize(8)
    #     p.setFont(font)
    #     for rect, flags, text in textSpecs:
    #         # this is the important part
    #         p.save()
    #         p.translate(rect.x(), rect.y())
    #         p.rotate(-75)
    #         x1,y1,x2,y2 = -rect.width(), rect.height(), rect.width(), rect.height()
    #         p.drawText(x1,y1,x2,y2, flags, text)
    #         # restoring the painter is *required*!!!
    #         p.restore()

class BarPlotPanel(GuiPanel):

    position = 3
    panelName = 'BarPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self._appearancePanel = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        self._toolbarPanel = self.guiModule.panelHandler.getToolBarPanel()


    def initWidgets(self):
        ## this colour def could go in an higher position as they are same for all possible plots
        colour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self.backgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self.gridPen = pg.functions.mkPen(colour, width=1, style=QtCore.Qt.SolidLine)
        self.gridFont = getFont()
        self.originAxesPen = pg.functions.mkPen(hexToRgb(getColours()[GUISTRIP_PIVOT]), width=1,
                                                style=QtCore.Qt.DashLine)
        self.fittingLinePen = pg.functions.mkPen(hexToRgb(getColours()[DIVIDER]), width=0.5, style=QtCore.Qt.DashLine)
        self.selectedPointPen = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
        self.selectedLabelPen = pg.functions.mkBrush(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
        self.barGraphWidget = BarGraphWidget(self, application=self.application, backgroundColour=self.backgroundColour,
                                             threshouldLine=0.1, grid=(0,0))
        self.barGraphWidget.showThresholdLine(True)
        self.barGraphWidget.plotWidget.setAxisItems({'bottom': XBarAxisItem(orientation='bottom')})
        self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._thresholdLineMoved)
        self._setBarGraphWidget()

    def setXLabel(self, label=''):
        self.barGraphWidget.plotWidget.setLabel('bottom', label)

    def setYLabel(self, label=''):
        self.barGraphWidget.plotWidget.setLabel('left', label)

    def _getAxis(self, axisName):
        return self.barGraphWidget.plotWidget.plotItem.getAxis(axisName)

    def _setBarGraphWidget(self):
        self.barGraphWidget.setViewBoxLimits(0, None, 0, None)
        self.barGraphWidget.xLine.hide()
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').setPen(self.gridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').setPen(self.gridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').tickFont = self.gridFont
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').tickFont = self.gridFont

    def _thresholdLineMoved(self):
        pos = self.barGraphWidget.xLine.pos().y()
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThreshValue)
            if w:
                with w.blockWidgetSignals():
                    w.setValue(pos)
        self.updatePanel()

    @property
    def thresholdValue(self):
        return self.barGraphWidget.xLine.pos().y()

    @thresholdValue.setter
    def thresholdValue(self, value):
        self.barGraphWidget.xLine.setPos(value)

    @property
    def aboveThresholdBrushColour(self):
        """Returns selected colour name """
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_AboveThrColour)
            if w:
                value = w.getText()
        return value

    @aboveThresholdBrushColour.setter
    def aboveThresholdBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_AboveThrColour)
            if w:
                w.select(colourName)

    @property
    def belowThresholdBrushColour(self):
        """Returns selected colour name"""
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BelowThrColour)
            if w:
                value = w.getText()
        return value

    @belowThresholdBrushColour.setter
    def belowThresholdBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BelowThrColour)
            if w:
                w.select(colourName)
    @property
    def untraceableBrushColour(self):
        """Returns selected colour name"""
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_UntraceableColour)
            if w:
                value = w.getText()
        return value

    @untraceableBrushColour.setter
    def untraceableBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_UntraceableColour)
            if w:
                w.select(colourName)
    @property
    def thresholdBrushColour(self):
        """Returns selected colour name"""
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThrColour)
            if w:
                value = w.getText()
        return value

    @thresholdBrushColour.setter
    def thresholdBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThrColour)
            if w:
                w.select(colourName)

    def _updateThresholdValueFromSettings(self, value, *args):
        self.thresholdValue = value

    def plotDataFrame(self, dataFrame):
        pass
