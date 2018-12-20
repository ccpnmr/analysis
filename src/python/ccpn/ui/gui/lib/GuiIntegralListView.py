"""
Get the regions between two peak Limits and fill the area under the curve.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import pyqtgraph as pg
# from ccpn.ui.gui.widgets.PlotWidget import PlotWidget
from ccpn.ui.gui.lib.GuiListView import GuiListViewABC


class GuiIntegralListView(GuiListViewABC):
    """integralList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()

# def _getSpectrumPlotItem(spectrum, plotWidget):
#     for i in plotWidget.items():
#         if isinstance(i, pg.PlotDataItem):
#             if i.objectName() == spectrum.pid:
#                 return i
#
#
# def _test_getIntegralFilledItems(plotWidget, integralList, intersectingThreshold=None):
#     import numpy as np
#     import pyqtgraph as pg
#
#     spectrum = integralList.spectrum
#     intersectingThreshold = intersectingThreshold or spectrum.noiseLevel
#     brush = spectrum.sliceColour
#     spectrumItem = _getSpectrumPlotItem(spectrum, plotWidget)
#
#     limitsPairs = [integral.limits for integral in integralList.integrals]
#     x, y = np.array(spectrum.positions), np.array(spectrum.intensities)
#
#     fills = []
#     for pair in limitsPairs:
#         index = np.where((x <= max(pair[0])) & (x >= min(pair[0])))
#
#         y_region = y[index]
#         x_region = x[index]
#
#         yBaselineCurve = [intersectingThreshold] * len(y_region)
#         baselineCurve = pg.PlotCurveItem(x_region, yBaselineCurve)
#         integralCurve = pg.PlotCurveItem(x_region, y_region)
#
#         baselineCurve.setParentItem(spectrumItem)
#         integralCurve.setParentItem(spectrumItem)
#
#         fill = pg.FillBetweenItem(integralCurve, baselineCurve, brush=brush)
#         fills.append(fill)
#
#     return fills
#
#
# def _addIntegralRegionsToPlot(plotWidget, fillRegions):
#     for fillRegion in fillRegions:
#         if isinstance(plotWidget, PlotWidget):
#             plotWidget.addItem(fillRegion)
#
#
# def _removeIntegralRegionsFromPlot(plotWidget, fillRegions):
#     for fillRegion in fillRegions:
#         if isinstance(plotWidget, PlotWidget):
#             plotWidget.removeItem(fillRegion)
