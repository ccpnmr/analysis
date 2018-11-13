
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from functools import partial
import weakref
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
from ccpn.ui.gui.widgets.BarGraph import BarGraph, CustomViewBox , CustomLabel
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Base import Base


class BarGraphWidget(Widget):

  def __init__(self, parent, application=None, xValues=None, yValues=None, colour='r',
               objects=None, threshouldLine=0.01, **kwds):
    super().__init__(parent, **kwds)

    self.application = application
    self.backgroundColour = 'w'
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
    self.setData(viewBox=self.customViewBox, xValues=xValues,yValues=yValues, objects=objects,colour=colour,replace=True)
    self.xLine = self.customViewBox.xLine
    self.customViewBox.addItem(self.xLine)
    self.setThresholdLine()

  def _setViewBox(self):
    self.customViewBox = CustomViewBox(application = self.application)
    self.customViewBox.setMenuEnabled(enableMenu=False)  # override pg default context menu
    self.plotWidget = pg.PlotWidget(viewBox=self.customViewBox, background=self.backgroundColour)
    self.customViewBox.setParent(self.plotWidget)

  def _setLayout(self):
    hbox = QtGui.QHBoxLayout()
    self.setLayout(hbox)
    hbox.addWidget(self.plotWidget)
    hbox.setContentsMargins(1, 1, 1, 1)

  def _addExtraItems(self):
    # self.addLegend()
    self.setThresholdLine()

  def setData(self,viewBox, xValues, yValues, objects, colour, replace=True):
    if replace:
      self.barGraphs = []
      self.customViewBox.clear()

    self.barGraph = BarGraph(viewBox=viewBox, application = self.application,
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
    '''Updates with default paarameters. Minimum values to show the data only'''
    if self.xValues and self.yValues:
      self.customViewBox.setLimits(xMin=min(self.xValues)/2, xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                   yMin=min(self.yValues)/2 ,yMax=max(self.yValues) + (max(self.yValues) * 0.5),
                                   )

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
      if len(self.yValues)>0:
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
    if len(args)>0:
        aboveX = args['aboveX']
        aboveY =  args['aboveY']
        disappearedX = args['disappearedX']
        disappearedY = args['disappearedY']
        aboveObjects = args['aboveObjects']
        belowX =  args['belowX']
        belowY =  args['belowY']
        belowObjects =  args['belowObjects']
        disappearedObjects =  args['disappearedObjects']
        self.aboveBrush = args['aboveBrush']
        self.belowBrush = args['belowBrush']
        self.disappearedBrush = args['disappearedBrush']

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

      pos = self.xLine.pos().y()
      self.xLine.show()
      if self.xValues:
        for x,y,obj in zip(self.xValues, self.yValues, self.objects):
          if y > pos:
            aboveY.append(y)
            aboveX.append(x)
            aboveObjects.append(obj)
          else:
            belowX.append(x)
            belowY.append(y)
            belowObjects.append(obj)

    self.aboveThreshold = BarGraph(viewBox=self.customViewBox, application = self.application,
                                   xValues=aboveX, yValues=aboveY, objects=aboveObjects, brush=self.aboveBrush)
    self.belowThreshold = BarGraph(viewBox=self.customViewBox, application = self.application,
                                   xValues=belowX, yValues=belowY, objects=belowObjects, brush=self.belowBrush)
    self.disappearedPeaks = BarGraph(viewBox=self.customViewBox, application=self.application,
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

  def showLegend(self, value:False):
    if value:
      self.legendItem.show()
    else:
     self.legendItem.hide()


#######################################################################################################
####################################      Mock DATA TESTING    ########################################
#######################################################################################################
#
# from collections import namedtuple
# import random
#
# nmrResidues = []
# for i in range(30):
#   nmrResidue = namedtuple('nmrResidue', ['sequenceCode','peaksShifts'])
#   nmrResidue.__new__.__defaults__ = (0,)
#   nmrResidue.sequenceCode = i
#   nmrResidue.peaksShifts = random.uniform(1.5, 3.9)
#   nmrResidues.append(nmrResidue)
#
# nmrChain = namedtuple('nmrChain', ['nmrResidues'])
# nmrChain.nmrResidues = nmrResidues



#
# if __name__ == '__main__':
#   from ccpn.ui.gui.widgets.Application import TestApplication
#   from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
#   from ccpn.ui.gui.modules.ChemicalShiftsMappingModule import ChemicalShiftsMapping
#
#   app = TestApplication()
#   win = QtGui.QMainWindow()
#
#   moduleArea = CcpnModuleArea(mainWindow=None, )
#   chemicalShiftsMapping = ChemicalShiftsMapping(mainWindow=None, nmrChain=nmrChain)
#   moduleArea.addModule(chemicalShiftsMapping)
#
#
#
#
#   win.setCentralWidget(moduleArea)
#   win.resize(1000, 500)
#   win.setWindowTitle('Testing %s' % chemicalShiftsMapping.moduleName)
#   win.show()
#
#   app.start()
