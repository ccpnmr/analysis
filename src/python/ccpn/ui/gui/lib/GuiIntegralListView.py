"""
Get the regions between two peak Limits and fill the area under the curve.

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pyqtgraph as pg
from ccpn.ui.gui.widgets.PlotWidget import PlotWidget
from PyQt5 import QtCore, QtGui, QtWidgets

# import pyqtgraph as pg

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
# from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.util.Logging import getLogger
from ccpn.core.IntegralList import IntegralList

# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import AbstractPeakDimContrib as ApiAbstractPeakDimContrib
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Resonance as ApiResonance
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrChain as ApiNmrChain
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakDim as ApiPeakDim
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataDimRef as ApiDataDimRef
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FreqDataDim as ApiFreqDataDim

NULL_RECT = QtCore.QRectF()
IDENTITY = QtGui.QTransform()
IDENTITY.reset()


class GuiIntegralListView(QtWidgets.QGraphicsItem):

    def __init__(self):
        """ peakList is the CCPN wrapper object
        """
        #FIXME: apparently it gets passed an object which already has crucial attributes
        # A big NONO!!!
        strip = self.spectrumView.strip
        # scene = strip.plotWidget.scene()
        QtWidgets.QGraphicsItem.__init__(self)  # ejb - need to remove, scene=scene from here
        # self.scene = scene

        ###self.strip = strip
        ###self.peakList = peakList
        self.peakItems = {}  # CCPN peak -> Qt peakItem
        self.setFlag(QtWidgets.QGraphicsItem.ItemHasNoContents, True)
        self.application = self.spectrumView.application

        # strip.viewBox.addItem(self)
        ###self._parent = parent
        # self.displayed = True
        # self.symbolColour = None
        # self.symbolStyle = None
        # self.isSymbolDisplayed = True
        # self.textColour = None
        # self.isTextDisplayed = True
        # self.regionChanged()

        # ED - added to allow rebuilding of GLlists
        self.buildSymbols = True
        self.buildLabels = True
        # self.buildSymbols = True

        # if isinstance(self.peakList, IntegralList):
        #     self.setVisible(False)


    def boundingRect(self):

        return NULL_RECT

    def paint(self, painter, option, widget):

        return

    # For notifiers - moved from core IntegralListView
    # def _createdIntegralListView(self):
    #     spectrumView = self.spectrumView
    #     spectrum = spectrumView.spectrum
    #     # NBNB TBD FIXME we should get rid of this API-level access
    #     # But that requires refactoring the spectrumActionDict
    #     action = spectrumView.strip.spectrumDisplay.spectrumActionDict.get(spectrum._wrappedData)
    #     if action:
    #         action.toggled.connect(self.setVisible)  # TBD: need to undo this if integralListView removed
    #
    #     if not self.scene:  # this happens after an undo of a spectrum/integralList deletion
    #         spectrumView.strip.plotWidget.scene().addItem(self)
    #         spectrumView.strip.viewBox.addItem(self)
    #
    #     strip = spectrumView.strip
    #     for integralList in spectrum.integralLists:
    #         strip.showIntegrals(integralList)

    # For notifiers - moved from core IntegralListView
    # def _deletedStripIntegralListView(self):
    #     spectrumView = self.spectrumView
    #     strip = spectrumView.strip
    #     spectrumDisplay = strip.spectrumDisplay
    #
    #     try:
    #         integralItemDict = spectrumDisplay.activeIntegralItemDict[self]
    #         integralItems = set(spectrumDisplay.inactiveIntegralItemDict[self])
    #         for apiIntegral in integralItemDict:
    #             # NBNB TBD FIXME change to get rid of API integrals here
    #             integralItem = integralItemDict[apiIntegral]
    #             integralItems.add(integralItem)
    #
    #         # TODO:ED should really remove all references at some point
    #         # if strip.plotWidget:
    #         #   scene = strip.plotWidget.scene()
    #         #   for integralItem in integralItems:
    #         #     scene.removeItem(integralItem.annotation)
    #         #     if spectrumDisplay.is1D:
    #         #       scene.removeItem(integralItem.symbol)
    #         #     scene.removeItem(integralItem)
    #         #   self.scene.removeItem(self)
    #
    #         del spectrumDisplay.activeIntegralItemDict[self]
    #         del spectrumDisplay.inactiveIntegralItemDict[self]
    #     except Exception as es:
    #         getLogger().warning('Error: integralList does not exist in spectrum')

    # def _changedIntegralListView(self):
    #
    #     pass
    #     # for integralItem in self.integralItems.values():
    #     #     if isinstance(integralItem, IntegralNd):
    #     #         integralItem.update()  # ejb - force a repaint of the integralItem
    #     #         integralItem.annotation.setupIntegralAnnotationItem(integralItem)

    def setVisible(self, visible):
        super().setVisible(visible)

        # change visibility list for the strip
        self.spectrumView.strip._updateVisibility()

        # repaint all displays - this is called for each spectrumView in the spectrumDisplay
        # all are attached to the same click
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()


# WARNING:
# This  file is Under development.
# DO NOT USE !!

def _getSpectrumPlotItem(spectrum, plotWidget):
  for i in plotWidget.items():
    if isinstance(i, pg.PlotDataItem):
      if i.objectName() == spectrum.pid:
        return i

def _test_getIntegralFilledItems(plotWidget, integralList, intersectingThreshold= None):
  import numpy as np
  import pyqtgraph as pg

  spectrum = integralList.spectrum
  intersectingThreshold = intersectingThreshold or spectrum.noiseLevel
  brush = spectrum.sliceColour
  spectrumItem = _getSpectrumPlotItem(spectrum, plotWidget)

  limitsPairs = [integral.limits for integral in integralList.integrals]
  x, y = np.array(spectrum.positions), np.array(spectrum.intensities)

  fills = []
  for pair in limitsPairs:
    index = np.where((x <= max(pair[0])) & (x >= min(pair[0])))

    y_region = y[index]
    x_region = x[index]

    yBaselineCurve = [intersectingThreshold] * len(y_region)
    baselineCurve = pg.PlotCurveItem(x_region, yBaselineCurve)
    integralCurve = pg.PlotCurveItem(x_region, y_region)

    baselineCurve.setParentItem(spectrumItem)
    integralCurve.setParentItem(spectrumItem)

    fill = pg.FillBetweenItem(integralCurve, baselineCurve, brush=brush)
    fills.append(fill)

  return  fills

def _addIntegralRegionsToPlot(plotWidget, fillRegions):
  for fillRegion in fillRegions:
    if isinstance(plotWidget, PlotWidget):
      plotWidget.addItem(fillRegion)

def _removeIntegralRegionsFromPlot(plotWidget, fillRegions):
  for fillRegion in fillRegions:
    if isinstance(plotWidget, PlotWidget):
      plotWidget.removeItem(fillRegion)
