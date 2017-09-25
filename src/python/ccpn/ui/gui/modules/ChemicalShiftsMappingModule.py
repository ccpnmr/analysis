from functools import partial

import pyqtgraph as pg
from PyQt4 import QtCore, QtGui

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
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

  def __init__(self, mainWindow, name='Chemical Shifts Mapping', nmrChain= None, **kw):
    # super(ChemicalShiftsMapping, self)
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name, settingButton=True)
    self.mainWindow = mainWindow
    if mainWindow is not None:
      self.project = self.mainWindow.project
      self.application = self.mainWindow.application




  def setNmrChain(self, nmrChain):
    if nmrChain:
      shifts = []
      sequenceCode = []
      nmrResidues = []
      for nmrResidue in nmrChain.nmrResidues:
        shifts += [self._getMeanNmrResiduePeaksShifts(nmrResidue), ]
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

    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects
    self.colour = colour
    self.addBarItems()


    self._addExtraItems()

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
    self.addLegend()
    self.addThresholdLine()


  def setValue(self, xValues, yValues, objects):
    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects

  def setViewBoxLimits(self, xMin, xMax, yMin, yMax):
    self.customViewBox.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

  def updateViewBoxLimits(self):
    '''Updates with default paarameters. Minimum values to show the data only'''
    if self.xValues and self.yValues:
      self.customViewBox.setLimits(xMin=min(self.xValues)/2, xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                   yMin=min(self.yValues)/2 ,yMax=max(self.yValues) + (max(self.yValues) * 0.5))

  def addBarItems(self):
    bg = BarGraph(viewBox=self.customViewBox, xValues=self.xValues, yValues=self.yValues, objects=self.objects, brush = self.colour)
    self.customViewBox.addItem(bg)
    # self.updateViewBoxLimits()

  def _clearAll(self):
    self.customViewBox.clear()

  def addThresholdLine(self):

    self.xLine = pg.InfiniteLine(angle=0, movable=True, pen='b')
    self.customViewBox.addItem(self.xLine)
    if self.yValues is not None:
      if len(self.yValues)>0:
        self.xLine.setPos(min(self.yValues))
    self.showThresholdLine(True)
    self.xLine.sigPositionChangeFinished.connect(self._lineMoved)
  def showThresholdLine(self, value=True):
    if value:
      self.xLine.show()
    else:
      self.xLine.hide()

  def _lineMoved(self):
    self._clearAll()

    aboveX = []
    aboveY = []
    belowX = []
    belowY = []

    pos = self.xLine.pos().y()
    for x,y, in zip(self.xValues, self.yValues):
      if y > pos:
        aboveY.append(y)
        aboveX.append(x)
      else:
        belowX.append(x)
        belowY.append(y)


    aboveThreshold = BarGraph(viewBox=self.customViewBox, xValues=aboveX, yValues=aboveY, objects=None,
                  brush='g')
    belowTrheshold = BarGraph(viewBox=self.customViewBox, xValues=belowX, yValues=belowY, objects=None,
                  brush='r')
    self.customViewBox.addItem(aboveThreshold)
    self.customViewBox.addItem(belowTrheshold)
    # self.updateViewBoxLimits()


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




#################################### _________ RUN GUI TESTING ____________ ####################################




if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea

  app = TestApplication()
  win = QtGui.QMainWindow()

  moduleArea = CcpnModuleArea(mainWindow=None, )
  chemicalShiftsMapping = ChemicalShiftsMapping(mainWindow=None, xValues=[21,25,23], yValues=[0.555, 0.566, 0.588])
  moduleArea.addModule(chemicalShiftsMapping)
  # pipeline._openAllPipes()

  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % chemicalShiftsMapping.moduleName)
  win.show()

  app.start()