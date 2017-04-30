"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan",
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-04-11 15:15:27 +0100 (Tue, April 11, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

import pyqtgraph as pg
from PyQt4 import QtGui, QtCore, QtOpenGL

from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import Notifier

from ccpn.ui.gui.guiSettings import textFontSmall
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.PlotWidget import PlotWidget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import FloatLineEdit
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.PlaneToolbar import _StripLabel
from ccpn.ui.gui.widgets.Frame import Frame



from ccpn.util import Ticks
from ccpn.util.Colour import Colour
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Ruler as ApiRuler

from ccpn.util.Logging import getLogger
logger = getLogger()


class GuiStrip(Frame):

  # GWV: used for!?
  sigClicked = QtCore.Signal(object, object)

  def __init__(self, qtParent, spectrumDisplay, application, useOpenGL=False):
    """
    Basic strip class; used in StripNd and Strip1d

    :param qtParent: QT parent to place widgets
    :param spectrumDisplay: spectrumDisplay instance
    :param application: application instance

    This module inherits attributes from the Strip wrapper class
    """

    self.qtParent = qtParent
    # For now, cannot set spectrumDisplay attribute as it is owned by the wrapper class
    # self.spectrumDisplay = spectrumDisplay
    self.application = application
    self.current = application.current
    self.stripIndex = self.spectrumDisplay.orderedStrips.index(self)

    #print('GuiStrip>>>', qtParent, self.spectrumDisplay, application)

    # GWV:passing qtParent to the widget stops the PlotWidget filling all available space
    #TODO:GEERTEN: find cause and fix this

    Frame.__init__(self, parent=self.qtParent, setLayout=True, showBorder=True,
                           acceptDrops=True, hPolicy='expanding', vPolicy='minimal'
                  )

    # it appears to be required to explicitly set these, otherwise
    # the Widget will not fill all available space
    self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    # The strip is responsive on restore to the contentMargins set here
    self.setContentsMargins(30, 5, 30, 5)

    layout = self.getLayout()
    if layout is not None:
      layout.setContentsMargins(0, 0, 0, 0)

    self.setMinimumWidth(250)
    self.setMinimumHeight(200)

    self.plotWidget = PlotWidget(parent=self, application=self.application,
                                 useOpenGL=useOpenGL, strip=self,
                                 showDoubleCrosshair=application.preferences.general.doubleCrossHair)
    self.plotWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    self.plotWidget.setContentsMargins(0, 0, 0, 0)
    self.layout().addWidget(self.plotWidget, 0, 0)

    # placeholder for toolbar and a stripIdLabel; more items will be added by GuiStripNd and GuiStrip1d
    # TODO: oddly: left-alignment goes wrong when using Widget's
    self.stripToolBarWidget = ToolBar(parent=self,
                                      hPolicy='expanding', vAlign='top',
                                      grid=(1, 0)
                                     )
    self.stripToolBarWidget.setFixedHeight(20)

    #TODO: correct once pid has been reviewed
    self.stripIdLabel = Label(parent=self.stripToolBarWidget,
                              text='.'.join(self.id.split('.')[2:]))
#                              grid=(0,0), hAlign='left', vAlign='center', hPolicy='minimum')
    self.stripIdLabel.setFont(textFontSmall)
    #self.stripIdLabel.setMaximumWidth(100)
    #self.stripIdLabel.setMinimumWidth(100)
    self.stripToolBarWidget.addWidget(self.stripIdLabel)

    self.stripLabel = _StripLabel(parent=self.stripToolBarWidget, text='')
    self.stripLabel.setFont(textFontSmall)
    self.stripToolBarWidget.addWidget(self.stripLabel)
    self.showStripLabel(False)

    # Strip needs access to plotWidget's items and info #TODO: get rid of this
    self.plotItem = self.plotWidget.plotItem
    self.viewBox = self.plotItem.vb

    self.xAxisAtomLabels = []
    self.yAxisAtomLabels = []

    self.showDoubleCrossHair = self.application.preferences.general.doubleCrossHair
    self._showCrossHair()
    # callbacks
    self.plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self._showMousePosition)
    self.storedZooms = []
    
    self.beingUpdated = False
    self.xPreviousRegion, self.yPreviousRegion = self.viewBox.viewRange()

    # need to keep track of mouse position because Qt shortcuts don't provide
    # the widget or the position of where the cursor is
    self.axisPositionDict = {}  # axisCode --> position

    self.vRulerLineDict = {}  # ruler --> vertical line for that ruler
    self.hRulerLineDict = {}  # ruler --> horizontal line for that ruler
    self.rulerLabelDict = {}  # ruler --> label for that ruler
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

    self._stripNotifier = Notifier(self.current, [Notifier.CURRENT], 'strip', self._highlightCurrentStrip)
    self._peakNotifier = Notifier(self.project, [Notifier.CREATE], 'Peak', self._updateDisplayedPeaks)
    #self._stripNotifier.setDebug(True)
    #self._peakNotifier.setDebug(True)

  @property
  def gridIsVisible(self):
    "True if grid is visible"
    return self.plotWidget.grid.isVisible()

  @property
  def crossHairIsVisible(self):
    "True if crosshair is visible"
    return self.plotWidget.crossHair1.isVisible()

  def setStripLabelText(self, text: str):
    """set the text of the stripLabel"""
    if text is not None:
      self.stripLabel.setText(text)

  def getStripLabelText(self) -> str:
    """return the text of the stripLabel"""
    return self.stripLabel.text()

  #TODO:GEERTEN: the hide does not work!?
  def showStripLabel(self, doShow: bool):
    """show / hide the stripLabel"""
    if doShow:
      self.stripLabel.show()
    else:
      self.stripLabel.hide()

  # def hideStripLabelText(self):
  #   "Hide the stripLabel"
  #   self.stripLabel.hide()

  def _unregisterStrip(self):
    self._stripNotifier.unRegister()
    self._peakNotifier.unRegister()

  def _updateDisplayedPeaks(self, data):
    "Callback when peaks have changed"
    self.showPeaks(data['object'].peakList)

  def _highlightCurrentStrip(self, data):
    "Callback to highlight the axes of current strip"
    self.plotWidget.highlightAxes(self is self.current.strip)

  def _printToFile(self, printer):
    # CCPN INTERNAL - called in printToFile method of GuiMainWindow

    for spectrumView in self.spectrumViews:
      spectrumView._printToFile(printer)

    # print box

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
      if self.plotWidget.grid.isVisible():
        printer.writeLine(tick, printer.y0, tick, printer.y1, colour='#888888')
      printer.writeLine(tick, printer.y0, tick, printer.y0+xTickHeight)
      text = xMajorText[n]
      printer.writeText(text, tick-0.5*len(text)*fontsize*0.7, printer.y0+xTickHeight+1.5*fontsize)

    # output backwards for y
    for tick in yMinorTicks:
      printer.writeLine(printer.x0, printer.y1-tick, printer.x0+0.5*yTickHeight, printer.y1-tick)

    for n, tick in enumerate(yMajorTicks):
      if self.plotWidget.grid.isVisible():
        printer.writeLine(printer.x0, printer.y1-tick, printer.x1, printer.y1-tick, colour='#888888')
      printer.writeLine(printer.x0, printer.y1-tick, printer.x0+yTickHeight, printer.y1-tick)
      text = yMajorText[n]
      printer.writeText(text, printer.x0+yTickHeight+0.5*fontsize*0.7, printer.y1-tick+0.5*fontsize)

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
    #
    # TODO:GEERTEN: Fix with proper stylesheet
    colour = '#e4e15b' if self.application.colourScheme == 'dark' else '#000000'
    self.hPhasingPivot.setPen({'color': colour})
    self.vPhasingPivot.setPen({'color': colour})
    for spectrumView in self.spectrumViews:
      spectrumView._updatePhasing()
      
  def _updateRegion(self, viewBox):
    # this is called when the viewBox is changed on the screen via the mouse
    # this code is complicated because need to keep viewBox region and axis region in sync
    # and there can be different viewBoxes with the same axis

    if not self._finaliseDone: return

    assert viewBox is self.viewBox, 'viewBox = %s, self.viewBox = %s' % (viewBox, self.viewBox)

    self._updateY()
    self._updatePhasing()

  def _updateY(self):

    def _widthsChangedEnough(r1, r2, tol=1e-5):
      r1 = sorted(r1)
      r2 = sorted(r2)
      minDiff = abs(r1[0] - r2[0])
      maxDiff = abs(r1[1] - r2[1])
      return (minDiff > tol) or (maxDiff > tol)

    if not self._finaliseDone: return

    yRange = list(self.viewBox.viewRange()[1])
    for strip in self.spectrumDisplay.strips:
      stripYRange = list(self.viewBox.viewRange()[1])
      if _widthsChangedEnough(stripYRange, yRange):
        strip.viewBox.setYRange(*yRange, padding=0)

  #TODO:WAYNE: Make this part of PlotWidget, pass axes label strings on init (
  def _moveAxisCodeLabels(self):
    """
    Puts axis code labels in the correct place on the PlotWidget
    """
    if not self._finaliseDone: return
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

  def _toggleCrossHair(self):
    " Toggles whether crosshair is visible"
    self.plotWidget.crossHair1.toggle()
    if self.showDoubleCrossHair:
      self.plotWidget.crossHair2.toggle()

  def _showCrossHair(self):
    "Displays crosshair in strip"
    self.plotWidget.crossHair1.show()
    if self.showDoubleCrossHair:
      self.plotWidget.crossHair2.show()

  def _hideCrossHair(self):
    "Hides crosshair in strip."
    self.plotWidget.crossHair1.hide()
    if self.showDoubleCrossHair:
      self.plotWidget.crossHair2.hide()

  def toggleGrid(self):
    "Toggles whether grid is visible in the strip."
    self.plotWidget.toggleGrid()

  def _crosshairCode(self, axisCode):
    # determines what axisCodes are compatible as far as drawing crosshair is concerned
    # TBD: the naive approach below should be improved
    return axisCode #if axisCode[0].isupper() else axisCode
      
  def _setCrossHairPosition(self, axisPositionDict):
    """
    # CCPN INTERNAL
    Called in _setCrossHairPosition method of GuiSpectrumDisplay
    """
    if not self._finaliseDone: return

    axes = self.orderedAxes
    xPos = axisPositionDict.get(self._crosshairCode(axes[0].code))
    yPos = axisPositionDict.get(self._crosshairCode(axes[1].code))
    # print('>>', xPos, yPos)
    self.plotWidget.crossHair1.setPosition(xPos,yPos)

    #TODO:SOLIDS This is clearly not correct; it should take the offset as defined for spectrum
    if self.showDoubleCrossHair:
      xPos = axisPositionDict.get(self._crosshairCode(axes[1].code))
      yPos = axisPositionDict.get(self._crosshairCode(axes[0].code))
      self.plotWidget.crossHair2.setPosition(xPos, yPos)

  def _createMarkAtCursorPosition(self, task):
    # TBD: this creates a mark in all dims, is that what we want??

    if not self._finaliseDone: return

    axisPositionDict = self.axisPositionDict
    axisCodes = [axis.code for axis in self.orderedAxes]
    positions = [axisPositionDict[axisCode] for axisCode in axisCodes]
    mark = task.newMark('white', positions, axisCodes)

  #
  #TODO:API: remove
  def _rulerCreated(self, apiRuler):

    if not self._finaliseDone: return

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
    
    for mark in self.spectrumDisplay.mainWindow.task.marks:
      apiMark = mark._wrappedData
      for apiRuler in apiMark.rulers:
        self._rulerCreated(apiRuler)

  #TODO:WAYNE: this should move to PlotWidget
  def _mouseMoved(self, positionPixel):
    """
    Updates the position of the crosshair when the mouse is moved.
    """
    if not self._finaliseDone: return

    if self.isDeleted:
      return

    #TODO:WAYNE: PlotObject has lastMousePos, but it has the same 'Scene' coordinates, i.e. not world (ppm) coordinates)
    # We need a property lastMousePosition which gets the mouse position in world coordinates
    # and calls self.plotWidget.something to get this
    #print('>_mouseMoved>', self, self.plotWidget.lastMousePos, positionPixel)

    # position is in pixels
    if self.plotWidget.sceneBoundingRect().contains(positionPixel):
      self.mousePixel = (positionPixel.x(), positionPixel.y())
      mousePoint = self.viewBox.mapSceneToView(positionPixel) # mouse point is in ppm
      axisPositionDict = self.axisPositionDict
      position = []
      for n, axis in enumerate(self.orderedAxes):
        #TODO:WAYNE: what if x and y have the same (or related) axis codes?
        if n == 0:
          pos = mousePoint.x()
        elif n == 1:
          pos = mousePoint.y()
        else:
          pos = axis.position
        axisPositionDict[self._crosshairCode(axis.code)] = pos
        position.append(pos)
      self.mousePosition = tuple(position) # position is in ppm
      #TODO:WAYNE: replace with appropriate object
      for window in self.application.project.windows:
        window._setCrossHairPosition(axisPositionDict)

  def _showMousePosition(self, pos:QtCore.QPointF):
    """
    Displays mouse position for both axes by axis code.
    """
    if not self._finaliseDone: return

    if self.isDeleted:
      return

    position = self.viewBox.mapSceneToView(pos)
    if self.orderedAxes[1].code == 'intensity':
      format = "%s: %.3f  %s: %.4g"
    else:
      format = "%s: %.2f  %s: %.2f"
    self.spectrumDisplay.positionBox.setText(format %
      (self.axisOrder[0], position.x(), self.axisOrder[1], position.y())
    )

  def zoomToRegion(self, xRegion:typing.Tuple[float, float], yRegion:typing.Tuple[float, float]):
    """
    Zooms strip to the specified region
    """
    if not self._finaliseDone: return
    padding = self.application.preferences.general.stripRegionPadding
    self.viewBox.setXRange(*xRegion, padding=padding)
    self.viewBox.setYRange(*yRegion, padding=padding)

  def zoomX(self, x1:float, x2:float):
    """
    Zooms x axis of strip to the specified region
    """
    if not self._finaliseDone: return

    padding = self.application.preferences.general.stripRegionPadding
    self.viewBox.setXRange(x1, x2, padding=padding)

  def zoomY(self, y1:float, y2:float):
    """
    Zooms y axis of strip to the specified region
    """
    if not self._finaliseDone: return
    padding = self.application.preferences.general.stripRegionPadding
    self.viewBox.setYRange(y1, y2, padding=padding)

  def resetZoom(self):
    """
    Zooms both axis of strip to the specified region
    """
    if not self._finaliseDone: return
    padding = self.application.preferences.general.stripRegionPadding
    self.viewBox.autoRange(padding=padding)

  def showZoomPopup(self):
    """
    Creates and displays a popup for zooming to a region in the strip.
    """
    zoomPopup = QtGui.QDialog()

    Label(zoomPopup, text='x1', grid=(0, 0))
    x1LineEdit = FloatLineEdit(zoomPopup, grid=(0, 1))
    Label(zoomPopup, text='x2', grid=(0, 2))
    x2LineEdit = FloatLineEdit(zoomPopup, grid=(0, 3))
    Label(zoomPopup, text='y1', grid=(1, 0))
    y1LineEdit = FloatLineEdit(zoomPopup, grid=(1, 1))
    Label(zoomPopup, text='y2', grid=(1, 2))
    y2LineEdit = FloatLineEdit(zoomPopup, grid=(1, 3))

    def _zoomTo():
      x1 = x1LineEdit.get()
      y1 = y1LineEdit.get()
      x2 = x2LineEdit.get()
      y2 = y2LineEdit.get()
      if None in (x1, y1, x2, y2):
        logger.warning('Zoom: must specify region completely')
        return
      self.zoomToRegion(xRegion=(x1, x2), yRegion=(y1, y2))
      zoomPopup.close()

    Button(zoomPopup, text='OK', callback=_zoomTo, grid=(2, 0), gridSpan=(1, 2))
    Button(zoomPopup, text='Cancel', callback=zoomPopup.close, grid=(2, 2), gridSpan=(1, 2))

    zoomPopup.exec_()

  def _storeZoom(self):
    """
    Adds current region to the zoom stack for the strip.
    """
    if not self._finaliseDone: return
    self.storedZooms.append(self.viewBox.viewRange())

  def _restoreZoom(self):
    """
    Restores last saved region to the zoom stack for the strip.
    """
    if not self._finaliseDone: return
    if len(self.storedZooms) != 0:
      restoredZoom = self.storedZooms.pop()
      padding = self.application.preferences.general.stripRegionPadding
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

    if not self._finaliseDone: return
    if not peaks:
      peaks = peakList.peaks

    peakListView = self._findPeakListView(peakList)
    if not peakListView:
      return

    peaks = [peak for peak in peaks if self.peakIsInPlane(peak) or self.peakIsInFlankingPlane(peak)]
    self.spectrumDisplay.showPeaks(peakListView, peaks)

  def _resetRemoveStripAction(self):
    """Update interface when a strip is created or deleted.

      NB notifier is executed after deletion is final but before the wrapper is updated.
      len() > 1 check is correct also for delete
    """
    self.spectrumDisplay._resetRemoveStripAction()


# Notifiers:
def _axisRegionChanged(axis:'Axis'):
  """Notifier function: Update strips etc. for when axis position or width changes"""

  strip = axis.strip
  if not strip._finaliseDone: return

  position = axis.position
  width = axis.width
  region = (position - width/2., position + width/2.)

  index = strip.axisOrder.index(axis.code)
  if not strip.beingUpdated:

    strip.beingUpdated = True

    try:
      if index == 0:
        # X axis
        padding = strip.application.preferences.general.stripRegionPadding
        strip.viewBox.setXRange(*region, padding=padding)
      elif index == 1:
        # Y axis
        padding = strip.application.preferences.general.stripRegionPadding
        strip.viewBox.setYRange(*region, padding=padding)
      else:
        # One of the Z axes
        for spectrumView in strip.spectrumViews:
          if spectrumView.isVisible():
            for peakListView in spectrumView.peakListViews:
              if peakListView.isVisible():
                peakList = peakListView.peakList
                peaks = [peak for peak in peakList.peaks if strip.peakIsInPlane(peak) or strip.peakIsInFlankingPlane(peak)]
                strip.spectrumDisplay.showPeaks(peakListView, peaks)

        if len(strip.axisOrder) > 2:
          n = index - 2
          if n >= 0:
            planeLabel = strip.planeToolbar.planeLabels[n]
            planeSize = planeLabel.singleStep()
            planeLabel.setValue(position)
            strip.planeToolbar.planeCounts[n].setValue(width/planeSize)

      if index >= 2:
        spectrumDisplay = strip.spectrumDisplay
        if hasattr(spectrumDisplay, 'activePeakItemDict'):  # ND display
          activePeakItemDict = spectrumDisplay.activePeakItemDict
          for spectrumView in strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:
              peakItemDict = activePeakItemDict.get(peakListView, {})
              for peakItem in peakItemDict.values():
                peakItem._stripRegionUpdated()

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
  label = apiRuler.label
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
      if label:
        textItem = pg.TextItem(label, color=colour)
        y = strip.plotWidget.plotItem.vb.mapSceneToView(strip.viewBox.boundingRect().bottomLeft()).y()
        textItem.anchor = pg.Point(0, 1)
        textItem.setPos(position, y)
        strip.plotWidget.addItem(textItem)
        strip.xAxisAtomLabels.append(textItem)
        strip.rulerLabelDict[apiRuler] = textItem


    elif axisCode == axisOrder[1]:
      if colour:
        line = pg.InfiniteLine(angle=0, movable=False, pen=colour)
      else:
        line = pg.InfiniteLine(angle=0, movable=False, pen=strip.foreground)
      line.setPos(position)
      strip.plotWidget.addItem(line, ignoreBounds=True)
      strip.hRulerLineDict[apiRuler] = line
      if label:
        textItem = pg.TextItem(label, color=colour)
        x = strip.plotWidget.plotItem.vb.mapSceneToView(strip.viewBox.boundingRect().bottomLeft()).x()
        textItem.anchor = pg.Point(0, 0)
        textItem.setPos(x, position)
        strip.plotWidget.addItem(textItem)
        strip.yAxisAtomLabels.append(textItem)
        strip.rulerLabelDict[apiRuler] = textItem

def _rulerDeleted(project:Project, apiRuler:ApiRuler):
  task = project._data2Obj[apiRuler.mark.guiTask]
  for strip in task.strips:
    for dd in strip.vRulerLineDict, strip.hRulerLineDict:
      if apiRuler in dd:
        line = dd.pop(apiRuler)
        strip.plotWidget.removeItem(line)
      if apiRuler in strip.rulerLabelDict:
        label = strip.rulerLabelDict.pop(apiRuler)
        strip.plotWidget.removeItem(label)

# Add notifier functions to Project


# NB This notifier must be implemented as an API postInit notifier,
# As it relies on Axs that are not yet created when 'created' notifiers are executed
def _setupGuiStrip(project:Project, apiStrip):
  """Set up graphical parameters for completed strips - for notifiers"""
  strip = project._data2Obj[apiStrip]

  if not strip._finaliseDone: return

  orderedAxes = strip.orderedAxes
  axisOrder = strip.axisOrder
  padding = strip.application.preferences.general.stripRegionPadding

  strip.viewBox.setXRange(*orderedAxes[0].region, padding=padding)
  strip.viewBox.setYRange(*orderedAxes[1].region, padding=padding)
  strip.xAxisTextItem = AxisTextItem(strip.plotWidget, orientation='top', axisCode=axisOrder[0])
  strip.yAxisTextItem = AxisTextItem(strip.plotWidget, orientation='left', axisCode=axisOrder[1])
  strip.viewBox.sigStateChanged.connect(strip._moveAxisCodeLabels)
  strip.viewBox.sigRangeChanged.connect(strip._updateRegion)


class AxisTextItem(pg.TextItem):

  def __init__(self, plotWidget, orientation, axisCode=None, units=None, mappedDim=None):

    self.plotWidget = plotWidget
    self.orientation = orientation
    self.axisCode = axisCode
    self.units = units
    self.mappedDim = mappedDim
    pg.TextItem.__init__(self, text=axisCode, color=plotWidget.gridColour)
    if orientation == 'top':
      self.setPos(plotWidget.plotItem.vb.boundingRect().bottomLeft())
      self.anchor = pg.Point(0, 1)
    else:
      self.setPos(plotWidget.plotItem.vb.boundingRect().topRight())
      self.anchor = pg.Point(1, 0)
    plotWidget.scene().addItem(self)

  def _setUnits(self, units):
    self.units = units

  def _setAxisCode(self, axisCode):
    self.axisCode = str(axisCode)
