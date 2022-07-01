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


import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel

class FmtAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [f'{v:.3f}' for v in values]


class FitPlotPanel(GuiPanel):

    position = 2
    panelName = 'FitPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)


    def initWidgets(self):
        colour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self.backgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self.gridPen = pg.functions.mkPen(colour, width=1, style=QtCore.Qt.SolidLine)
        self.gridFont = getFont()
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
        self.bindingPlot = self._bindingPlotView.addPlot(axisItems={'left': FmtAxisItem(orientation='left')})
        self.bindingPlot.setMenuEnabled(False)
        self.bindingPlot.getAxis('bottom').setPen(self.gridPen)
        self.bindingPlot.getAxis('left').setPen(self.gridPen)
        self.bindingPlot.getAxis('bottom').tickFont = self.gridFont
        self.bindingPlot.getAxis('left').tickFont = self.gridFont
        self.getLayout().addWidget(self._bindingPlotView)
