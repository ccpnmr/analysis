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
__dateModified__ = "$dateModified: 2022-07-19 12:09:50 +0100 (Tue, July 19, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui
from ccpn.ui.gui.widgets.BarGraph import BarGraph, CustomViewBox
from ccpn.ui.gui.widgets.Widget import Widget


AboveX = 'aboveX'
AboveY = 'aboveY'
BelowX = 'belowX'
BelowY = 'belowY'
DisappearedX = 'disappearedX'
DisappearedY = 'disappearedY'
AboveObjects = 'aboveObjects'
AllAboveObjects = 'allAboveObjects'
AllBelowObjects = 'allBelowObjects'
BelowObjects = 'belowObjects'
DisappearedObjects = 'disappearedObjects'
AboveBrush = 'aboveBrush'
AboveBrushes = 'aboveBrushes'
BelowBrush = 'belowBrush'
DisappearedBrush = 'disappearedBrush'
DrawLabels = 'drawLabels'


class BarGraphWidget(Widget):

    def __init__(self, parent, application=None, xValues=None, yValues=None, colour='r',
                 objects=None, threshouldLine=0, backgroundColour='w', **kwds):
        super().__init__(parent, **kwds)

        self.application = application
        self.backgroundColour = backgroundColour
        self.thresholdLineColour = 'b'

        self._setViewBox()
        self._setLayout()
        self.setContentsMargins(1, 1, 1, 1)
        self.barGraphs = []
        self.xValues = xValues
        self.yValues = yValues
        self.objects = objects
        self.colour = colour
        self.aboveBrush = 'g'
        self.belowBrush = 'r'
        self.disappearedBrush = 'b'
        self.threshouldLine = threshouldLine
        self.setData(viewBox=self.customViewBox, xValues=xValues, yValues=yValues, objects=objects, colour=colour, replace=True)
        self.xLine = self.customViewBox.xLine
        self.customViewBox.addItem(self.xLine)
        self.setThresholdLine()
        self._dataDict = {
            AboveX            : [],
            AboveY            : [],
            AboveBrush        : 'g',
            AboveObjects      : [],
            AllAboveObjects   : [],
            BelowX            : [],
            BelowY            : [],
            BelowBrush        : 'r',
            BelowObjects      : [],
            DisappearedX      : [],
            DisappearedY      : [],
            DisappearedBrush  : 'b',
            DisappearedObjects: [],
            DrawLabels        : True
            }

    def _setViewBox(self):
        self.customViewBox = CustomViewBox(application=self.application)
        self.customViewBox.setMenuEnabled(enableMenu=False)  # override pg default context menu
        self.plotWidget = pg.PlotWidget(viewBox=self.customViewBox, background=self.backgroundColour)
        self.customViewBox.setParent(self.plotWidget)

    def _setLayout(self):
        hbox = QtWidgets.QHBoxLayout()
        self.setLayout(hbox)
        hbox.addWidget(self.plotWidget)
        hbox.setContentsMargins(1, 1, 1, 1)

    def _addExtraItems(self):
        # self.addLegend()
        self.setThresholdLine()

    def getPlottedColoursDict(self):
        """ TODO> check assignment. x axis is now detached from sequenceCode"""
        dd = {}
        for i in self.plotWidget.items():
            if isinstance(i, BarGraph):
               dd.update(i.barColoursDict)
        return dict(sorted(dd.items()))

    def setData(self, viewBox, xValues, yValues, objects, colour, replace=True):
        if replace:
            self.barGraphs = []
            self.customViewBox.clear()

        self.barGraph = BarGraph(viewBox=viewBox, application=self.application,
                                 xValues=xValues, yValues=yValues, objects=objects, brush=colour)
        self.barGraphs.append(self.barGraph)
        self.customViewBox.addItem(self.barGraph)
        self.xValues = xValues
        self.yValues = yValues
        self.objects = objects
        self.updateViewBoxLimits()

    def setViewBoxLimits(self, xMin, xMax, yMin, yMax):
        self.customViewBox.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def updateViewBoxLimits(self):
        """Updates with default paarameters. Minimum values to show the data only
        """
        if self.xValues and self.yValues:
            self.customViewBox.setLimits(xMin=min(self.xValues) / 2, xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                         yMin=min(self.yValues) / 2, yMax=max(self.yValues) + (max(self.yValues) * 0.5),
                                         )

    def setXRange(self, xMin, xMax, padding=None, update=True):
        self.customViewBox.setXRange(xMin, xMax, padding=padding, update=update)

    def setYRange(self, yMin, yMax, padding=None, update=True):
        self.customViewBox.setYRange(yMin, yMax, padding=padding, update=update)


    def clear(self):

        for item in self.customViewBox.addedItems:
            if not isinstance(item, pg.InfiniteLine):
                self.customViewBox.removeItem(item)
        for ch in self.customViewBox.childGroup.childItems():
            if not isinstance(ch, pg.InfiniteLine):
                self.customViewBox.removeItem(ch)

    def clearBars(self):
        self.barGraphs = []
        for item in self.customViewBox.addedItems:
            if not isinstance(item, pg.InfiniteLine):
                self.customViewBox.removeItem(item)

    def setThresholdLine(self):

        # self.thresholdValueTextItem = pg.TextItem(str(self.xLine.pos().y()), anchor=(self.customViewBox.viewRange()[0][0], 1.0),)
        # self.thresholdValueTextItem.setParentItem(self.xLine)
        # self.thresholdValueTextItem.setBrush(QtGui.QColor(self.thresholdLineColour))
        if self.yValues is not None:
            if len(self.yValues) > 0:
                self.xLine.setPos(self.threshouldLine)
        self.showThresholdLine(True)
        self.xLine.sigPositionChangeFinished.connect(self._lineMoved)
        # self.xLine.setToolTip(str(round(self.xLine.pos().y(), 4)))
        self.xLine.sigPositionChanged.connect(self._updateTextLabel)

    def _updateTextLabel(self):
        # self.thresholdValueTextItem.setText(str(round(self.xLine.pos().y(),3)))#, color=self.thresholdLineColour)
        self.xLine.setToolTip(str(round(self.xLine.pos().y(), 4)))

    def showThresholdLine(self, value=True):
        if value:
            self.xLine.show()
        else:
            self.xLine.hide()

    def _lineMoved(self, **args):
        self.clear()
        drawLabels = True
        if len(args) > 0:
            aboveX = args[AboveX]
            aboveY = args[AboveY]
            disappearedX = args[DisappearedX]
            disappearedY = args[DisappearedY]
            aboveObjects = args[AboveObjects]
            belowX = args[BelowX]
            belowY = args[BelowY]
            belowObjects = args[BelowObjects]
            disappearedObjects = args[DisappearedObjects]
            self.aboveBrush = args[AboveBrush]
            aboveBrushes = args.get(AboveBrushes, [])
            self.belowBrush = args[BelowBrush]
            self.disappearedBrush = args[DisappearedBrush]
            drawLabels = args.get(DrawLabels)

        else:
            aboveX = []
            aboveY = []
            aboveObjects = []
            belowX = []
            belowY = []
            belowObjects = []
            disappearedX = []
            disappearedY = []
            disappearedObjects = []
            aboveBrushes = []

            pos = self.xLine.pos().y()
            self.xLine.show()
            if self.xValues:
                for x, y, obj in zip(self.xValues, self.yValues, self.objects):
                    if y > pos:
                        aboveY.append(y)
                        aboveX.append(x)
                        aboveObjects.append(obj)
                    else:
                        belowX.append(x)
                        belowY.append(y)
                        belowObjects.append(obj)
        if len(aboveBrushes)>0:
            self.aboveThreshold = BarGraph(viewBox=self.customViewBox, application=self.application,
                                           drawLabels=drawLabels,
                                           xValues=aboveX, yValues=aboveY, objects=aboveObjects, useGradient=True, brushes=aboveBrushes)
        else:
            self.aboveThreshold = BarGraph(viewBox=self.customViewBox, application=self.application, drawLabels=drawLabels,
                                       xValues=aboveX, yValues=aboveY, objects=aboveObjects, brush=self.aboveBrush)
        self.belowThreshold = BarGraph(viewBox=self.customViewBox, application=self.application, drawLabels=drawLabels,
                                       xValues=belowX, yValues=belowY, objects=belowObjects, brush=self.belowBrush)
        self.disappearedPeaks = BarGraph(viewBox=self.customViewBox, application=self.application, drawLabels=drawLabels,
                                         xValues=disappearedX, yValues=disappearedY, objects=disappearedObjects,
                                         brush=self.disappearedBrush)

        self.customViewBox.addItem(self.aboveThreshold)
        self.customViewBox.addItem(self.belowThreshold)
        self.customViewBox.addItem(self.disappearedPeaks)
        self.barGraphs.append(self.aboveThreshold)
        self.barGraphs.append(self.belowThreshold)
        self.barGraphs.append(self.disappearedPeaks)
        self.updateViewBoxLimits()
        if self.customViewBox.allLabelsShown:
            self.customViewBox.showAllLabels()
        if self.customViewBox.showAboveThresholdOnly:
            self.customViewBox.showAboveThreshold()

    def addLegend(self):
        self.legendItem = pg.LegendItem((100, 60), offset=(70, 30))  # args are (size, offset)
        self.legendItem.setParentItem(self.customViewBox.graphicsItem())

    def addLegendItem(self, pen='r', name=''):
        c = self.plotWidget.plot(pen=pen, name=name)
        self.legendItem.addItem(c, name)

    def showLegend(self, value: False):
        if value:
            self.legendItem.show()
        else:
            self.legendItem.hide()

#######################################################################################################
####################################      Mock DATA TESTING    ########################################
#######################################################################################################
#
from collections import namedtuple
import random

nmrResidues = []
for i in range(30):
  nmrResidue = namedtuple('nmrResidue', ['sequenceCode','peaksShifts'])
  nmrResidue.__new__.__defaults__ = (0,)
  nmrResidue.sequenceCode = i
  nmrResidue.peaksShifts = random.uniform(1.5, 3.9)
  nmrResidues.append(nmrResidue)

nmrChain = namedtuple('nmrChain', ['nmrResidues'])
nmrChain.nmrResidues = nmrResidues



if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
  from ccpn.ui.gui.modules.ChemicalShiftsMappingModule import ChemicalShiftsMapping

  app = TestApplication()
  win = QtGui.QMainWindow()

  moduleArea = CcpnModuleArea(mainWindow=None, )
  chemicalShiftsMapping = ChemicalShiftsMapping(mainWindow=None, nmrChain=nmrChain)
  moduleArea.addModule(chemicalShiftsMapping)




  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % chemicalShiftsMapping.moduleName)
  win.show()

  app.start()
