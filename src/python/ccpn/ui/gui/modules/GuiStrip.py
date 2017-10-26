"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
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
from PyQt5 import QtGui, QtWidgets, QtCore

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
from ccpn.ui.gui.widgets.PlaneToolbar import _StripLabel
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase


from ccpn.util import Ticks
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Ruler as ApiRuler

from ccpn.util.Logging import getLogger


class GuiStrip(Frame):

  def __init__(self, spectrumDisplay, useOpenGL=False):
    """
    Basic strip class; used in StripNd and Strip1d

    :param spectrumDisplay: spectrumDisplay instance

    This module inherits attributes from the Strip wrapper class:
    Use clone() method to make a copy
    """

    # For now, cannot set spectrumDisplay attribute as it is owned by the wrapper class
    # self.spectrumDisplay = spectrumDisplay
    self.mainWindow = self.spectrumDisplay.mainWindow
    self.application = self.mainWindow.application
    self.current = self.application.current

    getLogger().debug('GuiStrip>>> spectrumDisplay: %s' % self.spectrumDisplay)
    Frame.__init__(self, parent=spectrumDisplay.stripFrame, setLayout=True, showBorder=False,
                         acceptDrops=True, hPolicy='expanding', vPolicy='expanding' ##'minimal'
                  )

    # it appears to be required to explicitly set these, otherwise
    # the Widget will not fill all available space
    ###self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    # The strip is responsive on restore to the contentMargins set here
    #self.setContentsMargins(5, 0, 5, 0)
    self.setContentsMargins(0, 0, 0, 0)
    #self.setMinimumWidth(250)
    self.setMinimumWidth(75)
    self.setMinimumHeight(200)

    self.plotWidget = PlotWidget(self, useOpenGL=useOpenGL)
                                 #showDoubleCrosshair = self.application.preferences.general.doubleCrossHair)
    self.plotWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    # GWV: plotWidget appears not to be responsive to contentsMargins
    self.plotWidget.setContentsMargins(10, 30, 10, 30)
    self.getLayout().addWidget(self.plotWidget, 1, 0)
    self.layout().setHorizontalSpacing(0)
    self.layout().setVerticalSpacing(0)
    # self.plotWidget.showGrid(x=True, y=True, alpha=None)


    # TODO: ED comment out the block below to return to normal
    # self.plotWidget.hide()
    from ccpn.util.CcpnOpenGL import CcpnOpenGLWidget, CcpnGLWidget
    # self._testCcpnOpenGLWidget = CcpnOpenGLWidget(self)
    # self.getLayout().addWidget(self._testCcpnOpenGLWidget, 1, 0)

    self._testCcpnOpenGLWidget = CcpnGLWidget(self)
    self.getLayout().addWidget(self._testCcpnOpenGLWidget, 3, 0)
    self._testCcpnOpenGLWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    # self.plotWidgetOverlay = pg.PlotWidget(self, useOpenGL=useOpenGL)  #    make a copy
    # self.plotWidgetOverlay.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    # self.plotWidgetOverlay.resize(200, 200)
    # self.plotWidgetOverlay.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    # self.plotWidgetOverlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    # self.plotWidgetOverlay.showGrid(x=True, y=True, alpha=None)







    # Widgets for toolbar; items will be added by GuiStripNd (eg. the Z/A-plane boxes)
    # and GuiStrip1d; will be hidden for 2D's by GuiSpectrumView
    self._stripToolBarWidget = Widget(parent=self, setLayout=True,
                                      hPolicy='expanding',
                                      grid=(2, 0), spacing=(5,5))
    # self._stripToolBarWidget.setFixedHeight(30)

    # Widgets for _stripIdLabel and _stripLabel
    self._labelWidget = Widget(parent=self, setLayout=True,
                                     hPolicy='expanding', vAlign='center',
                                     grid=(0, 0), spacing=(0,0))
    self._labelWidget.layout().setHorizontalSpacing(0)
    self._labelWidget.layout().setVerticalSpacing(0)

    # self._labelWidget.setFixedHeight(34)

    # display and pid
    #TODO:GEERTEN correct once pid has been reviewed
    self._stripIdLabel = Label(parent=self._labelWidget,
                               text='.'.join(self.id.split('.')), margins=[0,0,0,0], spacing=(0,0),
                               grid=(0,0), gridSpan=(1,1), hAlign='left', vAlign='top', hPolicy='minimum')
    self._stripIdLabel.setFont(textFontSmall)

    # Displays a draggable label for the strip
    #TODO:GEERTEN reinsert a notifier for update in case this displays a nmrResidue
    self._stripLabel = _StripLabel(parent=self._labelWidget,
                                   text='.', spacing=(0,0),
                                   grid=(2,0), gridSpan=(1,3), hAlign='left', vAlign='top', hPolicy='minimum')
    self._stripLabel.setFont(textFontSmall)
    self.hideStripLabel()

    # A label to display the cursor positions (updated by _showMousePosition)
    self._cursorLabel = Label(parent=self._labelWidget,
                               text='',
                               grid=(0,0), gridSpan=(2,4), margins=[0,0,0,0], spacing=(0,0),
                               # grid=(0,0), gridSpan=(1,3), margins=[0,0,0,0],
                               hAlign='right', vAlign='top', hPolicy='minimum')#, vPolicy='expanding')

    # self._cursorLabel.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    # self._cursorLabel.setAutoFillBackground(False)
    # self._stripIdLabel.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    # self._stripIdLabel.setAutoFillBackground(False)
    # self._stripLabel.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    # self._stripLabel.setAutoFillBackground(False)

    self._cursorLabel.setFont(textFontSmall)
    # self._labelWidget.layout().setSpacing(0)    # ejb - stop overlap hiding spectrum _stripIdLabel

    # Strip needs access to plotWidget's items and info #TODO: get rid of this
    self.plotItem = self.plotWidget.plotItem
    self.viewBox = self.plotItem.vb

    self._showCrossHair()
    # callbacks
    ###self.plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self._showMousePosition)
    self.storedZooms = []
    
    self.beingUpdated = False
    self.xPreviousRegion, self.yPreviousRegion = self.viewBox.viewRange()

    # need to keep track of mouse position because Qt shortcuts don't provide
    # the widget or the position of where the cursor is
    self.axisPositionDict = {}  # axisCode --> position

    self._initRulers()

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

    # notifier for highlighting the strip
    self._stripNotifier = Notifier(self.current, [Notifier.CURRENT], 'strip', self._highlightCurrentStrip)
    # Notifier for updating the peaks
    self._peakNotifier = Notifier(self.project, [Notifier.CREATE], 'Peak', self._updateDisplayedPeaks)
    # Notifier for change of stripLabel
    self._stripLabelNotifier = Notifier(self.project, [Notifier.RENAME], 'NmrResidue', self._updateStripLabel)
    #self._stripNotifier.setDebug(True)
    #self._peakNotifier.setDebug(True)

    # For now, all dropevents are not strip specific, use spectrumDisplay's
    # handling
    self._droppedNotifier = GuiNotifier(self,
                                       [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                                       self.spectrumDisplay._processDroppedItems)

    self.show()

  @property
  def gridIsVisible(self):
    "True if grid is visible"
    return self.plotWidget.grid.isVisible()

  @property
  def crossHairIsVisible(self):
    "True if crosshair is visible"
    return self.plotWidget.crossHair1.isVisible()

  @property
  def pythonConsole(self):
    return self.mainWindow.pythonConsole

  def getStripLabel(self):
    """Return the stripLabel widget"""
    return self._stripLabel

  def setStripLabelText(self, text: str):
    """set the text of the _stripLabel"""
    if text is not None:
      self._stripLabel.setText(text)

  def getStripLabelText(self) -> str:
    """return the text of the _stripLabel"""
    return self._stripLabel.text()

  def showStripLabel(self, doShow: bool=True):
    """show / hide the _stripLabel"""
    self._stripLabel.setVisible(doShow)

  def hideStripLabel(self):
    "Hide the _stripLabel; convienience"
    self._stripLabel.setVisible(False)

  def _updateStripLabel(self, callbackDict):
    "Update the striplabel if it represented a NmrResidue that has changed its id"
    text = self.getStripLabelText()
    if callbackDict['oldPid'] == text:
      self.setStripLabelText(callbackDict['object'].pid)

  def _unregisterStrip(self):
    self._stripNotifier.unRegister()
    self._peakNotifier.unRegister()
    self._stripLabelNotifier.unRegister()
    self._droppedNotifier.unRegister()

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
    position = self.current.cursorPosition[0] if direction == 0 else self.current.cursorPosition[1]
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

    # FIXME fails on newer OSX. It causes the displays to shrink
    # the below updates the wrapper model.
    # for ii, axis in enumerate(self.orderedAxes[:2]):
    #   viewRange = self.viewBox.viewRange()[ii]
    #   axis.position = 0.5*(viewRange[0] + viewRange[1])
    #   axis.width = viewRange[1] - viewRange[0]

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
      if strip is not self:
        stripYRange = list(strip.viewBox.viewRange()[1])
        if _widthsChangedEnough(stripYRange, yRange):
          strip.viewBox.setYRange(*yRange, padding=0)

  def _toggleCrossHair(self):
    " Toggles whether crosshair is visible"
    self.plotWidget.crossHair1.toggle()
    if self.spectrumViews and self.spectrumViews[0].spectrum.showDoubleCrosshair:
      self.plotWidget.crossHair2.toggle()

  def _showCrossHair(self):
    "Displays crosshair in strip"
    self.plotWidget.crossHair1.show()
    if self.spectrumViews and self.spectrumViews[0].spectrum.showDoubleCrosshair:
      self.plotWidget.crossHair2.show()

  def _hideCrossHair(self):
    "Hides crosshair in strip."
    self.plotWidget.crossHair1.hide()
    if self.spectrumViews and self.spectrumViews[0].spectrum.showDoubleCrosshair:
      self.plotWidget.crossHair2.hide()

  def toggleGrid(self):
    "Toggles whether grid is visible in the strip."
    self.plotWidget.toggleGrid()

  def _crosshairCode(self, axisCode):
    # determines what axisCodes are compatible as far as drawing crosshair is concerned
    # TBD: the naive approach below should be improved
    return axisCode #if axisCode[0].isupper() else axisCode

  def _createMarkAtCursorPosition(self):
    # TODO: this creates a mark in all dims, is that what we want??

    if not self._finaliseDone: return

    axisPositionDict = self.axisPositionDict
    axisCodes = [axis.code for axis in self.orderedAxes[:2]]
    positions = [axisPositionDict[axisCode] for axisCode in axisCodes]
    self._project.newMark('white', positions, axisCodes) # the 'white' is overridden in PlotWidget._addRulerLine()

  # TODO: remove apiRuler (when notifier at bottom of module gets rid of it)
  def _initRulers(self):
    
    for mark in self._project.marks:
      apiMark = mark._wrappedData
      for apiRuler in apiMark.rulers:
        self.plotWidget._addRulerLine(apiRuler)

  def _showMousePosition(self, pos:QtCore.QPointF):
    """
    Displays mouse position for both axes by axis code.
    """
    if not self._finaliseDone: return

    if self.isDeleted:
      return

    position = self.viewBox.mapSceneToView(pos)
    try:
      # this only calls a single _wrapper function
      if self.orderedAxes[1].code == 'intensity':
        format = "%s: %.3f  %s: %.4g"
      else:
        format = "%s: %.2f  %s: %.2f"
    except:
      format = "%s: %.3f  %s: %.4g"

    self._cursorLabel.setText(format %
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
    zoomPopup = QtWidgets.QDialog()

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
        getLogger().warning('Zoom: must specify region completely')
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
    pass  # GWV: poor soultion self.spectrumDisplay._resetRemoveStripAction()

  def _moveToNextSpectrumView(self):
    spectrumViews = self.spectrumViews
    countSpvs = len(spectrumViews)
    if countSpvs > 0:
      visibleSpectrumViews = [i for i in spectrumViews if i.isVisible()]
      if len(visibleSpectrumViews) == 1:
        currentIndex = spectrumViews.index(visibleSpectrumViews[0])
        if countSpvs > currentIndex + 1:
          visibleSpectrumViews[0].setVisible(False)
          spectrumViews[currentIndex + 1].setVisible(True)
        elif countSpvs == currentIndex + 1: #starts again from the first
          visibleSpectrumViews[0].setVisible(False)
          spectrumViews[0].setVisible(True)
      else:
        print('Option available if only one spectrum per time is toggled on')
    else:
      print('No spectra displayed')

  def _moveToPreviousSpectrumView(self):
    spectrumViews = self.spectrumViews
    countSpvs = len(spectrumViews)
    if countSpvs > 0:
      visibleSpectrumViews = [i for i in spectrumViews if i.isVisible()]
      if len(visibleSpectrumViews) == 1:
        currentIndex = spectrumViews.index(visibleSpectrumViews[0])
        # if countSpvs > currentIndex + 1:
        visibleSpectrumViews[0].setVisible(False)
        spectrumViews[currentIndex - 1].setVisible(True)
      else:
        print('Option available if only one spectrum per time is toggled on')
    else:
      print('No spectra displayed')


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
        strip._updateTraces()
        for spectrumView in strip.spectrumViews:
          spectrumView.update()
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
  """Notifier function for creating rulers"""
  for strip in project.strips:
    strip.plotWidget._addRulerLine(apiRuler)

def _rulerDeleted(project:Project, apiRuler:ApiRuler):
  """Notifier function for deleting rulers"""
  for strip in project.strips:
    strip.plotWidget._removeRulerLine(apiRuler)

# Add notifier functions to Project


# NB This notifier must be implemented as an API postInit notifier,
# As it relies on Axs that are not yet created when 'created' notifiers are executed
def _setupGuiStrip(project:Project, apiStrip):
  """Set up graphical parameters for completed strips - for notifiers"""
  strip = project._data2Obj[apiStrip]

  if not strip._finaliseDone: return

  orderedAxes = strip.orderedAxes
  padding = strip.application.preferences.general.stripRegionPadding

  strip.viewBox.setXRange(*orderedAxes[0].region, padding=padding)
  strip.viewBox.setYRange(*orderedAxes[1].region, padding=padding)
  strip.plotWidget._initTextItems()
  strip.viewBox.sigStateChanged.connect(strip.plotWidget._moveAxisCodeLabels)
  strip.viewBox.sigRangeChanged.connect(strip._updateRegion)

