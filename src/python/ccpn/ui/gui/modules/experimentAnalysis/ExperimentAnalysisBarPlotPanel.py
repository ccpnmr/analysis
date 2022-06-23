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
__dateModified__ = "$dateModified: 2022-06-23 16:37:36 +0100 (Thu, June 23, 2022) $"
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

# colours NEED to go in common place
BackgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
OriginAxes = pg.functions.mkPen(hexToRgb(getColours()[GUISTRIP_PIVOT]), width=1, style=QtCore.Qt.DashLine)
FittingLine = pg.functions.mkPen(hexToRgb(getColours()[DIVIDER]), width=0.5, style=QtCore.Qt.DashLine)
SelectedPoint = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
SelectedLabel = pg.functions.mkBrush(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
c = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
GridPen = pg.functions.mkPen(c, width=1, style=QtCore.Qt.SolidLine)
GridFont = getFont()


class BarPlotPanel(GuiPanel):

    position = 3
    panelName = 'BarPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)

    def initWidgets(self):
        row = 0
        application = self.guiModule.application
        xValues = [1,2,3,4]
        yValues = [10,20,30,40]
        self.barGraphWidget = BarGraphWidget(self, application=application,
                                             xValues=xValues,
                                             yValues=yValues,
                                             backgroundColour=BackgroundColour, grid=(0,0))
        self._setBarGraphWidget()

    def _setBarGraphWidget(self):
        # MOCK
        self.barGraphWidget.setViewBoxLimits(0, None, 0, None)
        self.barGraphWidget.xLine.hide()
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').setPen(GridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').setPen(GridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').tickFont = GridFont
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').tickFont = GridFont
        self.barGraphWidget.plotWidget.setLabel('bottom', 'MOCK')
        self.barGraphWidget.plotWidget.setLabel('left', 'MOCK')
