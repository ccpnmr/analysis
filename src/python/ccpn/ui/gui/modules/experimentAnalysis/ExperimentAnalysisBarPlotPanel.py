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
__dateModified__ = "$dateModified: 2022-07-01 09:41:43 +0100 (Fri, July 01, 2022) $"
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
                                             grid=(0,0))
        self.barGraphWidget.showThresholdLine(True)
        self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._thresholdLineMoved)
        self._setBarGraphWidget()

    def setXLabel(self, label=''):
        self.barGraphWidget.plotWidget.setLabel('bottom', label)

    def setYLabel(self, label=''):
        self.barGraphWidget.plotWidget.setLabel('left', label)

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

    def plotDataFrame(self, dataFrame):
        pass
