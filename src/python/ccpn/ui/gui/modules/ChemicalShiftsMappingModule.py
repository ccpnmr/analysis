from functools import partial

import pyqtgraph as pg
from PyQt4 import QtCore, QtGui

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTable
from ccpn.ui.gui.widgets.BarGraph import BarGraph, CustomViewBox
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Base import Base


class ChemicalShiftsMapping(CcpnModule):

  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'top'
  className = 'ChemicalShiftsMapping'

  def __init__(self, mainWindow, name='Chemical Shift Mapping', nmrChain= None, **kw):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name, settingButton=True)
    self.mainWindow = mainWindow
    self.application = None
    if self.mainWindow is not None:
      self.project = self.mainWindow.project
      self.application = self.mainWindow.application

    if nmrChain is not None:
      self.setNmrChain(nmrChain)

    self._setWidgets()

  def _setWidgets(self):
    self.barGraphWidget = BarGraphWidget(self.mainWidget, xValues=None, yValues=None, objects=None, grid=(0, 0))
    if self.application:
      self.nmrResidueTable = NmrResidueTable(parent=self.mainWidget, application=self.application,  setLayout=True, grid=(1, 0))



  def setNmrChain(self, nmrChain):
    if nmrChain:
      shifts = []
      sequenceCode = []
      nmrResidues = []
      for nmrResidue in nmrChain.nmrResidues:
        if not nmrResidue.peaksShifts:
          shifts += [self._getMeanNmrResiduePeaksShifts(nmrResidue),]
        else:
          shifts += [nmrResidue.peaksShifts]
        sequenceCode += [int(nmrResidue.sequenceCode), ]
        nmrResidues += [nmrResidue, ]

      self.barGraphWidget = BarGraphWidget(self.mainWidget, xValues=sequenceCode, yValues=shifts, objects=nmrResidues, grid=(0, 0))


  def _getMeanNmrResiduePeaksShifts(self, nmrResidue):
    import numpy as np
    deltas = []
    peaks = nmrResidue.nmrAtoms[0].assignedPeaks
    for i, peak in enumerate(peaks):
      deltas += [
        (((peak.position[0] - peaks[0].position[0]) * 7) ** 2 + (peak.position[1] - peaks[0].position[1]) ** 2) ** 0.5,]
    if not None in deltas and deltas:
      return round(float(np.mean(deltas)),3)
    return

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification on current
    """
    # FIXME __deregisterNotifiers
    # self.settingWidget.__deregisterNotifiers()
    super(ChemicalShiftsMapping, self)._closeModule()



class BarGraphWidget(Widget, Base):

  def __init__(self, parent, xValues=None, yValues=None, colour='r', objects=None, **kw):
    Widget.__init__(self, parent)
    Base.__init__(self, **kw)
    self._setViewBox()
    self._setLayout()

    self.xLine = None
    self.barGraphs = []

    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects
    self.colour = colour
    self.setData(xValues=xValues,yValues=yValues, objects=objects,colour=colour,replace=True)


    self._addExtraItems()
    self.updateViewBoxLimits()

  def _setViewBox(self):
    self.customViewBox = CustomViewBox()
    self.customViewBox.setMenuEnabled(enableMenu=False)  # override pg default context menu
    self.plotWidget = pg.PlotWidget(viewBox=self.customViewBox, background='w')
    self.customViewBox.setParent(self.plotWidget)

  def _setLayout(self):
    hbox = QtGui.QHBoxLayout()
    self.setLayout(hbox)
    hbox.addWidget(self.plotWidget)

  def _addExtraItems(self):
    # self.addLegend()
    self.addThresholdLine()


  def setData(self, xValues, yValues, objects, colour, replace=True):
    if replace:
      self.barGraphs = []
      self.customViewBox.clear()

    self.barGraph = BarGraph(viewBox=self.customViewBox, xValues=xValues, yValues=yValues, objects=objects,
                  brush=colour)
    self.barGraphs.append(self.barGraph)
    self.customViewBox.addItem(self.barGraph)
    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects

    # self._lineMoved()

  def setViewBoxLimits(self, xMin, xMax, yMin, yMax):
    self.customViewBox.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

  def updateViewBoxLimits(self):
    '''Updates with default paarameters. Minimum values to show the data only'''
    if self.xValues and self.yValues:
      self.customViewBox.setLimits(xMin=min(self.xValues)/2, xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                   yMin=min(self.yValues)/2 ,yMax=max(self.yValues) + (max(self.yValues) * 0.5))



  def clearBars(self):
    self.barGraphs = []
    for item in self.customViewBox.addedItems:
      if not isinstance(item, pg.InfiniteLine):
        self.customViewBox.removeItem(item)

  def addThresholdLine(self):

    self.xLine = pg.InfiniteLine(angle=0, movable=True, pen='b')
    self.customViewBox.addItem(self.xLine)
    if self.yValues is not None:
      if len(self.yValues)>0:
        self.xLine.setPos(min(self.yValues))
    self.showThresholdLine(False)
    self._lineMoved()
    self.xLine.sigPositionChangeFinished.connect(self._lineMoved)

  def showThresholdLine(self, value=True):
    if value:
      self.xLine.show()
    else:
      self.xLine.hide()

  def _lineMoved(self):
    self.clearBars()

    aboveX = []
    aboveY = []
    aboveObjects = []
    belowX = []
    belowY = []
    belowObjects = []

    pos = self.xLine.pos().y()
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



      self.aboveThreshold = BarGraph(viewBox=self.customViewBox, xValues=aboveX, yValues=aboveY, objects=aboveObjects,
                    brush='g')
      self.belowTrheshold = BarGraph(viewBox=self.customViewBox, xValues=belowX, yValues=belowY, objects=belowObjects,
                    brush='r')
      self.customViewBox.addItem(self.aboveThreshold)
      self.customViewBox.addItem(self.belowTrheshold)
      self.barGraphs.append(self.aboveThreshold)
      self.barGraphs.append(self.belowTrheshold)
      self.updateViewBoxLimits()

    for bar in self.barGraphs:
      bar.viewBox.showAboveThreshold()

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

  def _updateGraph(self):
    self.customViewBox.clear()





#######################################################################################################
####################################      Mock DATA TESTING    ########################################
#######################################################################################################

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
