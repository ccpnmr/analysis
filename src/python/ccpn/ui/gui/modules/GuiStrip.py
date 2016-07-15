"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList
from ccpn.core.Peak import Peak

from ccpn.ui.gui.widgets.CcpnGridItem import CcpnGridItem
from ccpn.ui.gui.widgets.Widget import Widget

from ccpn.util.Colour import Colour
from ccpn.util import Ticks
import typing

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Ruler as ApiRuler
from ccpn.ui.gui.widgets.AxisTextItem import AxisTextItem
from ccpn.ui.gui.widgets.PlotWidget import PlotWidget

# def _sufficientlyDifferentWidth(region1, region2):
#
#   w1 = abs(region1[1] - region1[0])
#   w2 = abs(region2[1] - region2[0])
#   d = abs(w1 - w2)
#
#   return d > 1.0e-5 * max(w1, w2)
#
# def _scaleRegion(otherPreviousRegion, region, previousRegion):
#
#   otherPreviousRegionWidth = abs(otherPreviousRegion[1] - otherPreviousRegion[0])
#   regionWidth = abs(region[1] - region[0])
#   previousRegionWidth = abs(previousRegion[1] - previousRegion[0])
#
#   otherRegionWidth = otherPreviousRegionWidth * regionWidth / previousRegionWidth
#   otherRegionPosition = 0.5 * (otherPreviousRegion[1] + otherPreviousRegion[0])
#
#   return (otherRegionPosition - 0.5*otherRegionWidth, otherRegionPosition + 0.5*otherRegionWidth)
  
class GuiStrip(Widget): # DropBase needs to be first, else the drop events are not processed

  sigClicked = QtCore.Signal(object, object)

  def __init__(self, useOpenGL=False):
    
    self.stripFrame = self._parent.stripFrame
    self.guiSpectrumDisplay = self._parent  # NBNB TBD is it worth keeping both?

    Widget.__init__(self)
    # DropBase.__init__(self, self._parent._appBase)
    # DropBase.__init__(self, self._parent._appBase, self.dropCallback)
    self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    self.plotWidget = PlotWidget(self.stripFrame, appBase=self._parent._appBase,
                                 useOpenGL=useOpenGL, strip=self)
              # dropCallback=self.dropCallback, useOpenGL=useOpenGL)#, gridSpan=(1, 1))
    # newSplitter = QtGui.QSplitter   # NBNB FIXME - is this correct?
    self.stripFrame.layout().addWidget(self.plotWidget, 0,
                                       self.guiSpectrumDisplay.orderedStrips.index(self))
    self.colourScheme = self._parent._appBase.preferences.general.colourScheme
    if self.colourScheme == 'light':
      self.background = '#f7ffff'
      self.foreground = '#080000'
      self.gridColour = '#080000'
    else:
      self.background = '#080000'
      self.foreground = '#f7ffff'
      self.gridColour = '#f7ffff'
    self.plotWidget.setBackground(self.background)
    self._appBase = self._parent._appBase
    self.current = self._appBase.current
    self.current.registerNotify(self._highlightCurrentStrip, 'strips')
    self.plotItem = self.plotWidget.plotItem
    self.plotItem.parent = self
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.viewBox = self.plotItem.vb
    self.xAxisAtomLabels = []
    self.yAxisAtomLabels = []

    self._appBase.project.registerNotifier('Peak', 'create', self._updateDisplayedPeaks)


    #self.xAxis = Axis(self.plotWidget, orientation='top', #pen=self.foreground,
    #                  viewBox=self.viewBox, axisCode=self.orderedAxes[0].code)
    #self.yAxis = Axis(self.plotWidget, orientation='left', #pen=self.foreground,
    #                  viewBox=self.viewBox, axisCode=self.orderedAxes[1].code)

    for orientation in ('left', 'top'):
      axisItem = self.plotItem.axes[orientation]['item']
      axisItem.hide()
    for orientation in ('right', 'bottom'):
      axisItem = self.plotItem.axes[orientation]['item']
      axisItem.setPen(color=self.foreground)
    self.gridShown = True


    # self.viewBox.sigClicked.connect(self._mouseClicked)
    self.grid = CcpnGridItem(self.gridColour)
    self.plotWidget.addItem(self.grid)
    self.setMinimumWidth(200)
    self._createCrossHair()
    self.plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self._showMousePosition)
    self.storedZooms = []
    
    self.beingUpdated = False
    self.xPreviousRegion, self.yPreviousRegion = self.viewBox.viewRange()
    
    self.axisPositionDict = {}  # axisCode --> position
    # need to keep track of mouse position because Qt shortcuts don't provide the widget or the position of where the cursor is
    
    self.vRulerLineDict = {}  # ruler --> vertical line for that ruler
    self.hRulerLineDict = {}  # ruler --> horizontal line for that ruler
    self._initRulers()
    
    self.mousePixel = None
    self.mousePosition = None
    
    self.hPhasingPivot = pg.InfiniteLine(angle=90, movable=True)
    self.hPhasingPivot.setVisible(False)
    self.plotWidget.addItem(self.hPhasingPivot)
    self.hPhasingPivot.sigPositionChanged.connect(lambda phasingPivot: self._movedPivot())
    self.haveSetHPhasingPivot = False

    self.vPhasingPivot = pg.InfiniteLine(angle=0, movable=True)
    self.vPhasingPivot.setVisible(False)
    self.plotWidget.addItem(self.vPhasingPivot)
    self.vPhasingPivot.sigPositionChanged.connect(lambda phasingPivot: self._movedPivot())
    self.haveSetVPhasingPivot = False

    # Notifiers.registerNotify(self._axisRegionUpdated, 'ccpnmr.gui.Task.Axis', 'setPosition')
    # Notifiers.registerNotify(self._axisRegionUpdated, 'ccpnmr.gui.Task.Axis', 'setWidth')
    # Notifiers.registerNotify(self.rulerCreated, 'ccpnmr.gui.Task.Ruler', '__init__')
    # Notifiers.registerNotify(self.rulerDeleted, 'ccpnmr.gui.Task.Ruler', 'delete')


  def _updateDisplayedPeaks(self, peak):
    self.showPeaks(peak.peakList)

  def _unregisterStrip(self):
    self.current.unRegisterNotify(self._highlightCurrentStrip, 'strips')
    self._appBase.project.unRegisterNotifier('Peak', 'create', self._updateDisplayedPeaks)

  def _highlightCurrentStrip(self, strips=None):

    if self._appBase.preferences.general.colourScheme == 'light':
      axisColour = '#3333ff'
    elif self._appBase.preferences.general.colourScheme == 'dark':
      axisColour = '#00ff00'
    else:
      return

    if self is self.current.strips[0]:
      for orientation in ('right', 'bottom'):
        axisItem = self.plotItem.axes[orientation]['item']
        axisItem.setPen(color=axisColour)
    else:
      for orientation in ('right', 'bottom'):
        axisItem = self.plotItem.axes[orientation]['item']
        axisItem.setPen(color=self.foreground)

  def printToFile(self, printer):

    for spectrumView in self.spectrumViews:
      spectrumView._printToFile(printer)

    # print ticks and grid line
    viewRegion = self.plotWidget.viewRange()
    v1, v0 = viewRegion[0]  # TBD: relies on axes being backwards
    w1, w0 = viewRegion[1]  # TBD: relies on axes being backwards, which is not true in 1D
    xMajorTicks, xMinorTicks, xMajorFormat = Ticks.findTicks((v0, v1))
    yMajorTicks, yMinorTicks, yMajorFormat = Ticks.findTicks((w0, w1))

    xScale = (printer.x1-printer.x0)/(v1-v0)
    xOffset = printer.x0 - xScale*v0
    yScale = (printer.y1-printer.y0)/(w1-w0)
    yOffset = printer.y0 - yScale*w0
    xMajorText = [xMajorFormat % tick for tick in xMajorTicks]
    xMajorTicks = [tick*xScale+xOffset for tick in xMajorTicks]
    xMinorTicks = [tick*xScale+xOffset for tick in xMinorTicks]
    yMajorText = [xMajorFormat % tick for tick in yMajorTicks]
    yMajorTicks = [tick*yScale+yOffset for tick in yMajorTicks]
    yMinorTicks = [tick*yScale+yOffset for tick in yMinorTicks]

    xTickHeight = yTickHeight = max(printer.y1-printer.y0, printer.x1-printer.x0)*0.01

    for tick in xMinorTicks:
      printer.writeLine(tick, printer.y0, tick, printer.y0+0.5*xTickHeight)

    fontsize = 10
    for n, tick in enumerate(xMajorTicks):
      if self.grid.isVisible():
        printer.writeLine(tick, printer.y0, tick, printer.y1, colour='#888888')
      printer.writeLine(tick, printer.y0, tick, printer.y0+xTickHeight)
      text = xMajorText[n]
      printer.writeText(text, tick-0.5*len(text)*fontsize*0.7, printer.y0+xTickHeight+1.5*fontsize)

    # output backwards for y
    for tick in yMinorTicks:
      printer.writeLine(printer.x0, printer.y1-tick, printer.x0+0.5*yTickHeight, printer.y1-tick)

    for n, tick in enumerate(yMajorTicks):
      if self.grid.isVisible():
        printer.writeLine(printer.x0, printer.y1-tick, printer.x1, printer.y1-tick, colour='#888888')
      printer.writeLine(printer.x0, printer.y1-tick, printer.x0+yTickHeight, printer.y1-tick)
      text = yMajorText[n]
      printer.writeText(text, printer.x0+yTickHeight+0.5*fontsize*0.7, printer.y1-tick+0.5*fontsize)

  # def addStrip(self):
  #
  #   newStrip = self.strips[0].clone()
  #   print('spectrumViews', newStrip.spectrumViews)
  #   for spectrumView in newStrip.spectrumViews:
  #     spectrumView.connectStrip(newStrip)


  #
  #
  # def setupAxes(self):
  #
  #   # this is called from GuiSpectrumView because the axes are not ready when the strip is created
  #   # TBD: but that means this is called for every spectrum in the strip, which is not what we want
  #   self.viewBox.setXRange(*self.orderedAxes[0].region)
  #   self.viewBox.setYRange(*self.orderedAxes[1].region)
  #   self.xAxisTextItem = AxisTextItem(self.plotWidget, orientation='top',
  #                                 axisCode=self.orderedAxes[0].code)
  #   self.yAxisTextItem = AxisTextItem(self.plotWidget, orientation='left',
  #                                 axisCode=self.orderedAxes[1].code)
  #   self.viewBox.sigStateChanged.connect(self.moveAxisCodeLabels)
  #   self.viewBox.sigRangeChanged.connect(self.updateRegion)

  def _newPhasingTrace(self):
    for spectrumView in self.spectrumViews:
      spectrumView._newPhasingTrace()
      
  """
  def newHPhasingTrace(self):
    
    for spectrumView in self.spectrumViews:
      spectrumView.newHPhasingTrace(self.mousePosition[1])
      
  def newVPhasingTrace(self):
    
    for spectrumView in self.spectrumViews:
      spectrumView.newVPhasingTrace(self.mousePosition[0])
  """
   
  def _setPhasingPivot(self):
    
    phasingFrame = self.spectrumDisplay.phasingFrame
    direction = phasingFrame.getDirection()
    position = self.mousePosition[0] if direction == 0 else self.mousePosition[1]
    phasingFrame.pivotEntry.set(position)
    self._updatePivot()
      
  def removePhasingTraces(self):
    
    for spectrumView in self.spectrumViews:
      spectrumView.removePhasingTraces()

  """
  def togglePhasingPivot(self):
    
    self.hPhasingPivot.setPos(self.mousePosition[0])
    self.hPhasingPivot.setVisible(not self.hPhasingPivot.isVisible())
  """
  
  def _updatePivot(self): # this is called if pivot entry at bottom of display is updated and then "return" key used
  
    phasingFrame = self.spectrumDisplay.phasingFrame
    position = phasingFrame.pivotEntry.get()
    direction = phasingFrame.getDirection()
    if direction == 0:
      self.hPhasingPivot.setPos(position)
    else:
      self.vPhasingPivot.setPos(position)
    self._updatePhasing()
  
  def _movedPivot(self): # this is called if pivot on screen is dragged
    
    phasingFrame = self.spectrumDisplay.phasingFrame
    direction = phasingFrame.getDirection()
    if direction == 0:
      position = self.hPhasingPivot.getXPos()
    else:
      position = self.vPhasingPivot.getYPos()
      
    phasingFrame.pivotEntry.set(position)
    self._updatePhasing()
    
  def turnOnPhasing(self):
    
    self.hPhasingPivot.setVisible(True)
    self.vPhasingPivot.setVisible(True)
      
    for spectrumView in self.spectrumViews:
      spectrumView._turnOnPhasing()
      
  def turnOffPhasing(self):
    
    self.hPhasingPivot.setVisible(False)
    self.vPhasingPivot.setVisible(False)
      
    for spectrumView in self.spectrumViews:
      spectrumView._turnOffPhasing()
      
  def _changedPhasingDirection(self):
    
    phasingFrame = self.spectrumDisplay.phasingFrame
    direction = phasingFrame.getDirection()
    if direction == 0:
      self.hPhasingPivot.setVisible(True)
      self.vPhasingPivot.setVisible(False)
    else:
      self.hPhasingPivot.setVisible(False)
      self.vPhasingPivot.setVisible(True)
      
    for spectrumView in self.spectrumViews:
      spectrumView._changedPhasingDirection()
      
  def _updatePhasing(self):
    #colour = '#ffffff' if self.background == 'k' else '#000000'
    colour = '#e4e15b' if self._appBase.preferences.general.colourScheme == 'dark' else '#000000'
    self.hPhasingPivot.setPen({'color': colour})
    self.vPhasingPivot.setPen({'color': colour})
    for spectrumView in self.spectrumViews:
      spectrumView._updatePhasing()
      
  def _updateRegion(self, viewBox):
    # this is called when the viewBox is changed on the screen via the mouse
    
    # this code is complicated because need to keep viewBox region and axis region in sync
    # and there can be different viewBoxes with the same axis

    assert viewBox is self.viewBox, 'viewBox = %s, self.viewBox = %s' % (viewBox, self.viewBox)
    #
    # print('*', viewBox)
    # if self.beingUpdated:
    #   return
    # self.beingUpdated = True
    #
    # try:
    #   print('**', viewBox)
    #   xPreviousRegion = self.xPreviousRegion
    #   yPreviousRegion = self.yPreviousRegion
    #   xRegion, yRegion = viewBox.viewRange()
    #   print('***', xPreviousRegion, xRegion, yPreviousRegion, yRegion)
    #   xIsChanged = _sufficientlyDifferentWidth(xRegion, xPreviousRegion) if xPreviousRegion else True
    #   yIsChanged = _sufficientlyDifferentWidth(yRegion, yPreviousRegion) if yPreviousRegion else True
    #
    #   spectrumDisplay = self.guiSpectrumDisplay
    #   if xIsChanged and yIsChanged and spectrumDisplay.stripDirection is not None:
    #     for otherStrip in spectrumDisplay.strips:
    #       if otherStrip is self:
    #         continue
    #       otherStrip.beingUpdated = True
    #       if spectrumDisplay.stripDirection == 'Y':
    #         # x axis needs updating, y axis happens automatically below
    #         xOtherRegion = _scaleRegion(otherStrip.xPreviousRegion, yRegion, yPreviousRegion)
    #         otherStrip.viewBox.setXRange(*xOtherRegion)
    #         otherStrip.viewBox.setYRange(*yRegion)
    #         otherStrip.orderedAxes[0].region = otherStrip.xPreviousRegion = xOtherRegion
    #         otherStrip.yPreviousRegion = yRegion
    #       else: # spectrumDisplay.stripDirection == 'X'
    #         # y axis needs updating, x axis happens automatically below
    #         yOtherRegion = _scaleRegion(otherStrip.yPreviousRegion, xRegion, xPreviousRegion)
    #         otherStrip.viewBox.setYRange(*yOtherRegion)
    #         otherStrip.viewBox.setXRange(*xRegion)
    #         otherStrip.orderedAxes[1].region = otherStrip.yPreviousRegion = yOtherRegion
    #         otherStrip.xPreviousRegion = xRegion
    #
    #   self.orderedAxes[0].region = self.xPreviousRegion = xRegion
    #   self.orderedAxes[1].region = self.yPreviousRegion = yRegion
    #
    # finally:
    #
    #   self.beingUpdated = False
    #   if xIsChanged and yIsChanged and spectrumDisplay.stripDirection is not None:
    #     for otherStrip in self.guiSpectrumDisplay.strips:
    #       if otherStrip is self:
    #         continue
    #       otherStrip.beingUpdated = False
    self._parent.stripFrame.updateY(self)
    self._updatePhasing()


  #
  # def _axisRegionUpdated(self, apiAxis):
  #   # this is called when the api region (position and/or width) is changed
  #
  #   xAxis, yAxis = self.orderedAxes[:2]
  #   if not xAxis or not yAxis:
  #     return
  #
  #   if apiAxis not in (xAxis._wrappedData, yAxis._wrappedData):
  #     return
  #
  #   if self.beingUpdated:
  #     return
  #
  #   self.beingUpdated = True
  #
  #   try:
  #     xRegion = xAxis.region
  #     yRegion = yAxis.region
  #     self.viewBox.setXRange(*xRegion)
  #     self.viewBox.setYRange(*yRegion)
  #   finally:
  #     self.beingUpdated = False

  # def addSpinSystemLabel(self):
  #   self.planeToolbar = ToolBar(self.stripFrame, grid=(1, self.guiSpectrumDisplay.orderedStrips.index(self)), hAlign='center', vAlign='c')
  #   self.stripLabel = Label(self, text='.'.join(self.pid.id.split('.')[2:]),
  #                                hAlign='center', vAlign='top',dragDrop=True, pid=self.pid)
  #   # self.spinSystemLabel.dropEvent = self.dropCallback
  #   # self.spinSystemLabel.setText("Spin systems shown here")
  #   self.stripLabel.setFixedHeight(15)
  #   self.stripLabel.setFont(QtGui.QFont('Lucida Grande', 10))
  #   self.spinSystemLabel = Label(self, text='',
  #                                hAlign='center', vAlign='top',dragDrop=True, pid=self.pid)
  #   # self.spinSystemLabel.dropEvent = self.dropCallback
  #   # self.spinSystemLabel.setText("Spin systems shown here")
  #   self.spinSystemLabel.setFixedHeight(15)
  #   self.spinSystemLabel.setFont(QtGui.QFont('Lucida Grande', 10))
  #   self.planeToolbar.addWidget(self.stripLabel)
  #   self.planeToolbar.addWidget(self.spinSystemLabel)
  #   # self.spinSystemLabel.pid = self.pid
    # print(self.pid)lo



  def _moveAxisCodeLabels(self):
    """
    Puts axis code labels in the correct place on the PlotWidget
    """
    ###self.xAxis.textItem.setPos(self.viewBox.boundingRect().bottomLeft())
    ###self.yAxis.textItem.setPos(self.viewBox.boundingRect().topRight())
    self.xAxisTextItem.setPos(self.viewBox.boundingRect().bottomLeft())
    self.yAxisTextItem.setPos(self.viewBox.boundingRect().topRight())
    for item in self.xAxisAtomLabels:
      y = self.plotWidget.plotItem.vb.mapSceneToView(self.viewBox.boundingRect().bottomLeft()).y()
      x = item.pos().x()
      item.setPos(x, y)
    for item in self.yAxisAtomLabels:
      x = self.plotWidget.plotItem.vb.mapSceneToView(self.viewBox.boundingRect().bottomLeft()).x()
      y = item.pos().y()
      item.setPos(x, y)
    # self.textItem.setPos(self.viewBox.boundingRect().topLeft())

  # def hideCrossHairs(self):
  #   """
  #   Hides all crosshairs in all strips in parent spectrum display.
  #   """
  #   for strip in self.guiSpectrumDisplay.guiStrips:
  #     strip.hideCrossHair()

  def _createCrossHair(self):
    """
    Creates a single or double cross hair depending on specification in application preferences.
    """
    self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=self.foreground)
    self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=self.foreground)
    self.plotWidget.addItem(self.vLine, ignoreBounds=True)
    self.plotWidget.addItem(self.hLine, ignoreBounds=True)
    self.vLine2 = pg.InfiniteLine(angle=90, movable=False, pen=self.foreground)
    self.hLine2 = pg.InfiniteLine(angle=0, movable=False, pen=self.foreground)
    if self._appBase.preferences.general.doubleCrossHair is True:
      self.plotWidget.addItem(self.vLine2, ignoreBounds=True)
      self.plotWidget.addItem(self.hLine2, ignoreBounds=True)

  def _toggleCrossHair(self):
    """
    Toggles whether crosshair is visible.
    """
    self.vLine.setVisible(not self.vLine.isVisible())
    self.hLine.setVisible(not self.hLine.isVisible())
    self.vLine2.setVisible(not self.vLine2.isVisible())
    self.hLine2.setVisible(not self.hLine2.isVisible())

  def _showCrossHair(self):
    """
    Displays cross hair in strip.
    """
    self.vLine.show()
    self.hLine.show()
    self.vLine2.show()
    self.hLine2.show()

  def _hideCrossHair(self):
    """
    Hides cross hair in strip.
    """
    self.vLine.hide()
    self.hLine.hide()
    self.vLine2.hide()
    self.hLine2.hide()

  def toggleGrid(self):
    """
    Toggles whether grid is visible in the strip.
    """
    self.grid.setVisible(not self.grid.isVisible())

  def _crosshairCode(self, axisCode):
    # determines what axisCodes are compatible as far as drawing crosshair is concerned
    # TBD: the naive approach below should be improved
    return axisCode #if axisCode[0].isupper() else axisCode
      
  def _setCrossHairPosition(self, axisPositionDict):
    """
    # CCPN INTERNAL
    Called in _setCrossHairPosition method of GuiSpectrumDisplay
    """
    axes = self.orderedAxes
    position = axisPositionDict.get(self._crosshairCode(axes[0].code))
    position2 = axisPositionDict.get(self._crosshairCode(axes[1].code))
    if position is not None:
      self.vLine.setPos(position)
    if position2 is not None:
      self.vLine2.setPos(position2)


    position = axisPositionDict.get(self._crosshairCode(axes[1].code))
    position2 = axisPositionDict.get(self._crosshairCode(axes[0].code))
    if position is not None:
      self.hLine.setPos(position)
    if position2 is not None:
      self.hLine2.setPos(position2)

  def _createMarkAtCursorPosition(self, task):
    # TBD: this creates a mark in all dims, is that what we want??
    axisPositionDict = self.axisPositionDict
    axisCodes = [axis.code for axis in self.orderedAxes]
    positions = [axisPositionDict[axisCode] for axisCode in axisCodes]
    mark = task.newMark('white', positions, axisCodes)

  #
  def _rulerCreated(self, apiRuler):
    axisCode = apiRuler.axisCode # TBD: use label and unit
    position = apiRuler.position
    if apiRuler.mark.colour[0] == '#':
      colour = Colour(apiRuler.mark.colour)
    else:
      colour = self.foreground
    # TBD: is the below correct (so the correct axes)?
    if axisCode == self.axisOrder[0]:
      line = pg.InfiniteLine(angle=90, movable=False, pen=colour)
      line.setPos(position)
      self.plotWidget.addItem(line, ignoreBounds=True)
      self.vRulerLineDict[apiRuler] = line

    if axisCode == self.axisOrder[1]:
      line = pg.InfiniteLine(angle=0, movable=False, pen=colour)
      line.setPos(position)
      self.plotWidget.addItem(line, ignoreBounds=True)
      self.hRulerLineDict[apiRuler] = line

  def _rulerDeleted(self, apiRuler):
    for dd in self.vRulerLineDict, self.hRulerLineDict:
      if apiRuler in dd:
        line = dd[apiRuler]
        del dd[apiRuler]
        self.plotWidget.removeItem(line)
            
  def _initRulers(self):
    
    for mark in self.spectrumDisplay.window.task.marks:
      apiMark = mark._wrappedData
      for apiRuler in apiMark.rulers:
        self._rulerCreated(apiRuler)
        
  # def _mouseClicked(self, event):
  #   print(event)


  # def setStripToCurrent(self):
  #   position = self.viewBox.mapSceneToView(pos)


  # def mousePressEvent(self, event):
  #
  #   print('event')

  def _mouseMoved(self, positionPixel):
    """
    Updates the position of the crosshair when the mouse is moved.
    """

    # position is in pixels

    if self.plotWidget.sceneBoundingRect().contains(positionPixel):
      self.mousePixel = (positionPixel.x(), positionPixel.y())
      mousePoint = self.viewBox.mapSceneToView(positionPixel) # mouse point is in ppm
      axisPositionDict = self.axisPositionDict
      position = []
      for n, axis in enumerate(self.orderedAxes):
        # TBD: what if x and y have the same (or related) axis codes?
        if n == 0:
          pos = mousePoint.x()
        elif n == 1:
          pos = mousePoint.y()
        else:
          pos = axis.position
        axisPositionDict[self._crosshairCode(axis.code)] = pos
        position.append(pos)
      self.mousePosition = tuple(position) # position is in ppm
      for window in self._project.windows:
        window._setCrossHairPosition(axisPositionDict)
      ###self.vLine.setPos(mousePoint.x())
      ###self.hLine.setPos(mousePoint.y())
      ###for vLine in self.guiSpectrumDisplay._appBase.vLines:
      ###  vLine.setPos(self.mousePoint.x())
      ###for hLine in self.guiSpectrumDisplay._appBase.hLines:
      ###  hLine.setPos(self.mousePoint.y())
    ###return self.mousePoint

  def _showMousePosition(self, pos:QtCore.QPointF):
    """
    Displays mouse position for both axes by axis code.
    """
    position = self.viewBox.mapSceneToView(pos)
    self.guiSpectrumDisplay.positionBox.setText("%s: %.3f  %s: %.3f" %
      (self.axisOrder[0], position.x(), self.axisOrder[1], position.y())
    )

  def zoomToRegion(self, xRegion:typing.Tuple[float, float], yRegion:typing.Tuple[float, float]):
    """
    Zooms strip to the specified region
    """
    padding = self._appBase.preferences.general.stripRegionPadding
    self.viewBox.setXRange(*xRegion, padding=padding)
    self.viewBox.setYRange(*yRegion, padding=padding)

  def zoomX(self, x1:float, x2:float):
    """
    Zooms x axis of strip to the specified region
    """
    padding = self._appBase.preferences.general.stripRegionPadding
    self.viewBox.setXRange(x1, x2, padding=padding)

  def zoomY(self, y1:float, y2:float):
    """
    Zooms y axis of strip to the specified region
    """
    padding = self._appBase.preferences.general.stripRegionPadding
    self.viewBox.setYRange(y1, y2, padding=padding)

  def resetZoom(self):
    """
    Zooms both axis of strip to the specified region
    """
    self.viewBox.autoRange()

  def _zoomTo(self, x1:float, x2:float, y1:float, y2:float):
    self.zoomToRegion(xRegion=(x1, x2), yRegion=(y1, y2))
    self.zoomPopup.close()

  def showZoomPopup(self):
    """
    Creates and displays a popup for zooming to a region in the strip.
    """
    self.zoomPopup = QtGui.QDialog()
    layout = QtGui.QGridLayout()
    layout.addWidget(QtGui.QLabel(text='x1'), 0, 0)
    x1 = QtGui.QLineEdit()
    layout.addWidget(x1, 0, 1, 1, 1)
    layout.addWidget(QtGui.QLabel(text='x2'), 0, 2)
    x2 = QtGui.QLineEdit()
    layout.addWidget(x2, 0, 3, 1, 1)
    layout.addWidget(QtGui.QLabel(text='y1'), 1, 0,)
    y1 = QtGui.QLineEdit()
    layout.addWidget(y1, 1, 1, 1, 1)
    layout.addWidget(QtGui.QLabel(text='y2'), 1, 2)
    y2 = QtGui.QLineEdit()
    layout.addWidget(y2, 1, 3, 1, 1)
    okButton = QtGui.QPushButton(text="OK")
    okButton.clicked.connect(partial(self._zoomTo, float(x1.text()), float(x2.text()),
                                                   float(y1.text()), float(y2.text())
                                     )
                             )
    cancelButton = QtGui.QPushButton(text='Cancel')
    layout.addWidget(okButton,2, 1)
    layout.addWidget(cancelButton, 2, 3)
    cancelButton.clicked.connect(self.zoomPopup.close)
    self.zoomPopup.setLayout(layout)
    self.zoomPopup.exec_()

  def _storeZoom(self):
    """
    Adds current region to the zoom stack for the strip.
    """
    self.storedZooms.append(self.viewBox.viewRange())

  def _restoreZoom(self):
    """
    Restores last saved region to the zoom stack for the strip.
    """
    if len(self.storedZooms) != 0:
      restoredZoom = self.storedZooms.pop()
      padding = self._appBase.preferences.general.stripRegionPadding
      self.plotWidget.setXRange(restoredZoom[0][0], restoredZoom[0][1], padding=padding)
      self.plotWidget.setYRange(restoredZoom[1][0], restoredZoom[1][1], padding=padding)
    else:
      self.resetZoom()

  def showSpectrum(self, guiSpectrumView):
    raise Exception('should be implemented in subclass')

  def showPeaks(self, peakList:PeakList, peaks:typing.List[Peak]=None):
    ###from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView
    # NBNB TBD 1) we should not always display all peak lists together
    # NBNB TBD 2) This should not be called for each strip

    if not peaks:
      peaks = peakList.peaks

    peakListView = self._findPeakListView(peakList)
    if not peakListView:
      return

    peaks = [peak for peak in peaks if self.peakIsInPlane(peak)]
    self.stripFrame.guiSpectrumDisplay.showPeaks(peakListView, peaks)

  def _resetRemoveStripAction(self):
    """Update interface when a strip is created or deleted.

      NB notifier is executed after deletion is final but before the wrapper is updated.
      len() > 1 check is correct also for delete
    """
    self.spectrumDisplay._resetRemoveStripAction()


# Notifiers:
def _axisRegionChanged(axis:'Axis'):
  """Notifier function: Update strips etc. for when axis position or width changes"""

  position = axis.position
  width = axis.width
  region = (position - width/2., position + width/2.)

  strip = axis.strip

  index = strip.axisOrder.index(axis.code)
  if not strip.beingUpdated:

    strip.beingUpdated = True

    try:
      if index == 0:
        # X axis
        padding = strip._appBase.preferences.general.stripRegionPadding
        strip.viewBox.setXRange(*region, padding=padding)
      elif index == 1:
        # Y axis
        padding = strip._appBase.preferences.general.stripRegionPadding
        strip.viewBox.setYRange(*region, padding=padding)
      else:
        # One of the Z axes
        for spectrumView in strip.spectrumViews:
          if spectrumView.isVisible():
            for peakListView in spectrumView.peakListViews:
              if peakListView.isVisible():
                peakList = peakListView.peakList
                peaks = [peak for peak in peakList.peaks if strip.peakIsInPlane(peak)]
                strip.stripFrame.guiSpectrumDisplay.showPeaks(peakListView, peaks)

        if len(strip.axisOrder) > 2:
          n = index - 2
          if n >= 0:
            planeLabel = strip.planeToolbar.planeLabels[n]
            planeSize = planeLabel.singleStep()
            planeLabel.setValue(position)
            strip.planeToolbar.planeCounts[n].setValue(width/planeSize)

    finally:
      strip.beingUpdated = False

  if index == 1:  # ASSUMES that only do H phasing
    strip._updatePhasing()


# NB The following two notifiers could be replaced by wrapper notifiers on
# Mark, 'change'. But it would be rather more clumsy, so leave it as it is.

# NBNB TODO code uses API object. REFACTOR

def _rulerCreated(project:Project, apiRuler:ApiRuler):
  """]Notifier function for creating rulers"""
  axisCode = apiRuler.axisCode # TBD: use label and unit
  position = apiRuler.position
  colour = None
  if apiRuler.mark.colour[0] == '#':
    colour = Colour(apiRuler.mark.colour)
  task = project._data2Obj[apiRuler.mark.guiTask]
  for strip in task.strips:
    axisOrder = strip.axisOrder
    # TBD: is the below correct (so the correct axes)?
    if axisCode == axisOrder[0]:
      if colour:
        line = pg.InfiniteLine(angle=90, movable=False, pen=colour)
      else:
        line = pg.InfiniteLine(angle=90, movable=False, pen=strip.foreground)
      line.setPos(position)
      strip.plotWidget.addItem(line, ignoreBounds=True)
      strip.vRulerLineDict[apiRuler] = line

    elif axisCode == axisOrder[1]:
      if colour:
        line = pg.InfiniteLine(angle=0, movable=False, pen=colour)
      else:
        line = pg.InfiniteLine(angle=0, movable=False, pen=strip.foreground)
      line.setPos(position)
      strip.plotWidget.addItem(line, ignoreBounds=True)
      strip.hRulerLineDict[apiRuler] = line

def _rulerDeleted(project:Project, apiRuler:ApiRuler):
  task = project._data2Obj[apiRuler.mark.guiTask]
  for strip in task.strips:
    for dd in strip.vRulerLineDict, strip.hRulerLineDict:
      if apiRuler in dd:
        line = dd.pop(apiRuler)
        strip.plotWidget.removeItem(line)

# Add notifier functions to Project


# NB This notifier must be implemented as an API postInit notifier,
# As it relies on Axs that are not yet created when 'created' notifiers are executed
def _setupGuiStrip(project:Project, apiStrip):
  """Set up graphical parameters for completed strips - for notifiers"""
  strip = project._data2Obj[apiStrip]

  orderedAxes = strip.orderedAxes
  axisOrder = strip.axisOrder
  padding = strip._appBase.preferences.general.stripRegionPadding

  strip.viewBox.setXRange(*orderedAxes[0].region, padding=padding)
  strip.viewBox.setYRange(*orderedAxes[1].region, padding=padding)
  strip.xAxisTextItem = AxisTextItem(strip.plotWidget, orientation='top',
                                    axisCode=axisOrder[0])
  strip.yAxisTextItem = AxisTextItem(strip.plotWidget, orientation='left',
                                    axisCode=axisOrder[1])
  strip.viewBox.sigStateChanged.connect(strip._moveAxisCodeLabels)
  strip.viewBox.sigRangeChanged.connect(strip._updateRegion)
