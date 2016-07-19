"""

Zoom and pan:
    Left-drag: pans the spectrum.
    Middle-drag, shift-left-drag, shift-middle-drag, shift-right-drag: draws a zooming box and zooms the viewbox.
    Two successive shift-right-clicks: define zoombox
    control-right click: reset the zoom

Peaks:
    Left-click: select peak near cursor in a spectrum display.
    Control(Cmd)-left-drag: selects peaks in an area specified by the cursor.

    Control(Cmd)-Shift-Left-click: picks a peak at the cursor position.
    Control(Cmd)-shift-left-drag: picks peaks in an area specified by the cursor.

Others:
    Right-click raises the context menu.



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
import sys
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from pyqtgraph.Point import Point

from ccpn.ui.gui.widgets.Menu import Menu
from ccpnmodel.ccpncore.lib.spectrum import Spectrum as spectrumLib

from ccpn.util.Logging import getLogger
logger = getLogger()


def doDebug(msg):
  if False: #cannot get the regular debugger to work and likely do not want this on during production anyway
    sys.stderr.write(msg)

def controlShiftLeftMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-shift-left-Mouse event
  result = event.button() == QtCore.Qt.LeftButton \
    and (event.modifiers() & QtCore.Qt.ControlModifier)\
    and (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('DEBUG mouse: Control-shift-left-Mouse event at %s' % event.pos())
  return result

def controlLeftMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-left-Mouse event
  result = event.button() == QtCore.Qt.LeftButton \
    and (event.modifiers() & QtCore.Qt.ControlModifier)\
    and not (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Control-left-Mouse event at %s' % event.pos())
  return result

def shiftLeftMouse(event:QtGui.QMouseEvent):
  # Return True for shift-left-Mouse event
  result = event.button() == QtCore.Qt.LeftButton \
    and not (event.modifiers() & QtCore.Qt.ControlModifier)\
    and     (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Shift-left-Mouse event at %s' % event.pos())
  return result

def leftMouse(event:QtGui.QMouseEvent):
  # Return True for left-Mouse event
  result = event.button() == QtCore.Qt.LeftButton \
    and not event.modifiers()
  if result:
    doDebug('Left-Mouse event at %s' % event.pos())
  return result

def controlShiftRightMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-shift-right-Mouse event
  result = event.button() == QtCore.Qt.RightButton \
    and (event.modifiers() & QtCore.Qt.ControlModifier)\
    and (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Control-shift-right-Mouse event at %s' % event.pos())
  return result

def controlRightMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-right-Mouse event
  result = event.button() == QtCore.Qt.RightButton \
    and (event.modifiers() & QtCore.Qt.ControlModifier)\
    and not (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Control-right-Mouse event at %s' % event.pos())
  return result

def shiftRightMouse(event:QtGui.QMouseEvent):
  # Return True for shift-right-Mouse event
  result = event.button() == QtCore.Qt.RightButton \
    and not (event.modifiers() & QtCore.Qt.ControlModifier)\
    and     (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Shift-right-Mouse event at %s' % event.pos())
  return result

def rightMouse(event:QtGui.QMouseEvent):
  # Return True for right-Mouse event
  result = event.button() == QtCore.Qt.RightButton \
    and not event.modifiers()
  if result:
    doDebug('Right-Mouse event at %s' % event.pos())
  return result

def controlShiftMiddleMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-shift-middle-Mouse event
  result = event.button() == QtCore.Qt.MiddleButton \
    and (event.modifiers() & QtCore.Qt.ControlModifier)\
    and (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Control-shift-middle-Mouse event at %s' % event.pos())
  return result

def controlMiddleMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-middle-Mouse event
  result = event.button() == QtCore.Qt.MiddleButton \
    and (event.modifiers() & QtCore.Qt.ControlModifier)\
    and not (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Control-middle-Mouse event at %s' % event.pos())
  return result

def shiftMiddleMouse(event:QtGui.QMouseEvent):
  # Return True for shift-middle-Mouse event
  result = event.button() == QtCore.Qt.MiddleButton \
    and not (event.modifiers() & QtCore.Qt.ControlModifier)\
    and     (event.modifiers() & QtCore.Qt.ShiftModifier)
  if result:
    doDebug('Shift-middle-Mouse event at %s' % event.pos())
  return result

def middleMouse(event:QtGui.QMouseEvent):
  # Return True for middle-Mouse event
  result = event.button() == QtCore.Qt.MiddleButton \
    and not event.modifiers()
  if result:
    doDebug('Middle-Mouse event at %s' % event.pos())
  return result


class ViewBox(pg.ViewBox):
  """
  Base-class to implement mouse and drag events in spectral canvas, axes
  """
  sigClicked = QtCore.Signal(object)

  def __init__(self, current=None, parent=None, *args, **kwds):
    pg.ViewBox.__init__(self, *args, **kwds)
    self.current = current
    self.menu = None # Override pyqtgraph ViewBoxMenu
    self.menu = self._getMenu()
    self.current = current
    self.parent = parent
    self.selectionBox = QtGui.QGraphicsRectItem(0, 0, 1, 1)
    self.selectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
    self.selectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
    self.selectionBox.setZValue(1e9)
    self.selectionBox.hide()
    self.addItem(self.selectionBox, ignoreBounds=True)
    self.pickBox = QtGui.QGraphicsRectItem(0, 0, 1, 1)
    self.pickBox.setPen(pg.functions.mkPen((0, 255, 255), width=1))
    self.pickBox.setBrush(pg.functions.mkBrush(100, 255, 255, 100))
    self.pickBox.setZValue(1e9)
    self.pickBox.hide()
    self.addItem(self.pickBox, ignoreBounds=True)
    self.project = current._project
    self.mouseClickEvent = self._mouseClickEvent
    self.mouseDragEvent = self._mouseDragEvent
    self.hoverEvent = self._hoverEvent
    self._successiveClicks = None  # GWV: Store successive click events for zooming; None means first click not set
    # self.getMenu = self._getMenu

    self.peakWidthPixels = 20  # for ND peaks

  def _raiseContextMenu(self, event:QtGui.QMouseEvent):
    """
    Raise the context menu
    """
    from functools import partial
    from ccpn.ui.gui.lib.Window import navigateToPeakPosition, navigateToPosition
    position = event.screenPos()
    self.menu.navigateToMenu.clear()
    if self.current.peak:
      for spectrumDisplay in self.current.project.spectrumDisplays:
        if len(list(set(spectrumDisplay.strips[0].axisCodes) & set(self.current.peak.peakList.spectrum.axisCodes))) <= 2:
          self.menu.navigateToMenu.addAction(spectrumDisplay.pid, partial(navigateToPeakPosition, self.current.project,
                                                                        self.current.peak, [spectrumDisplay.pid]))
    else:
      for spectrumDisplay in self.current.project.spectrumDisplays:
        axisCodes = self.current.strip.axisCodes
        if len(list(set(spectrumDisplay.strips[0].axisCodes) & set(self.current.strip.axisCodes))) <= 2:
          self.menu.navigateToMenu.addAction(spectrumDisplay.pid, partial(navigateToPosition, self.current.project, self.current.cursorPosition,
                                                                        axisCodes, [spectrumDisplay.pid]))
    self.menu.popup(QtCore.QPoint(position.x(), position.y()))

  def _getMenu(self):
    if self.menu is None:
      self.menu = Menu('', self.parent(), isFloatWidget=True)
      return self.menu

  def _mouseClickEvent(self, event:QtGui.QMouseEvent, axis=None):
    """
    Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
    click events.
    """
    self.current.strip = self.parentObject().parent
    xPosition = self.mapSceneToView(event.pos()).x()
    yPosition = self.mapSceneToView(event.pos()).y()
    self.current.positions = [xPosition, yPosition]

    # This is the correct future style for cursorPosition handling
    self.current.cursorPosition = (xPosition, yPosition)

    if controlShiftLeftMouse(event):
      # Control-Shift-left-click: pick peak
      mousePosition=self.mapSceneToView(event.pos())
      position = [mousePosition.x(), mousePosition.y()]
      for spectrumView in self.current.strip.spectrumViews:
        peakList = spectrumView.spectrum.peakLists[0]
        orderedAxes = self.current.strip.orderedAxes
        if len(orderedAxes) > 2:
          for n in orderedAxes[2:]:
            position.append(n.position)
        peak = peakList.newPeak(position=position)
        self.current.addPeak(peak)
        peak.isSelected = True
        self.current.strip.showPeaks(peakList)

    elif controlLeftMouse(event):
      # Control-left-click; select peak and add to selection
      event.accept()
      self._selectPeak(xPosition, yPosition)

    elif leftMouse(event):
      # Left-click; select peak, deselecting others
      event.accept()
      self._deselectPeaks()
      self._selectPeak(xPosition, yPosition)

    elif shiftRightMouse(event):
      # Two successive shift-right-clicks: define zoombox
      event.accept()
      if self._successiveClicks is None:
        self._resetBoxes()
        self._successiveClicks = Point(event.pos())
      else:
        self._setView(Point(self._successiveClicks), Point(event.pos()))
        self._successiveClicks = None
        self._resetBoxes()

    elif rightMouse(event) and axis is None:
      # right click on canvas, not the axes
      event.accept()
      self._raiseContextMenu(event)

    elif controlRightMouse(event) and axis is None:
      # control-right-mouse click: reset the zoom
      event.accept()
      self.current.strip.resetZoom()

    else:
      # reset and hide all for all other clicks an drags
      self._resetBoxes()
      event.accept()

  def _deselectPeaks(self):
    "Deselected all current peaks"
    # NBNB TBD FIXME. We need to deselect ALL peaks
    for spectrumView in self.current.strip.spectrumViews:
      for peakList in spectrumView.spectrum.peakLists:
        for peak in peakList.peaks:
          peak.isSelected = False

    # NBNB TBD FIXME this isSelected stuff is a dogs breakfast and needs refactoring.
    # Probably we should replace 'peak.isSelected' with 'peak in current.peaks'
    # Meanwhile at least deselect current peaks
    for peak in self.current.peaks:
      peak.isSelected = False

    self.current.clearPeaks()

  def _selectPeak(self, xPosition, yPosition):
    "Select first peak near cursor xPosition, yPosition"
    xPeakWidth = abs(self.mapSceneToView(QtCore.QPoint(self.peakWidthPixels, 0)).x() - self.mapSceneToView(QtCore.QPoint(0, 0)).x())
    yPeakWidth = abs(self.mapSceneToView(QtCore.QPoint(0, self.peakWidthPixels)).y() - self.mapSceneToView(QtCore.QPoint(0, 0)).y())
    xPositions = [xPosition - 0.5*xPeakWidth, xPosition + 0.5*xPeakWidth]
    yPositions = [yPosition - 0.5*yPeakWidth, yPosition + 0.5*yPeakWidth]
    if len(self.current.strip.orderedAxes) > 2:
      # NBNB TBD FIXME what about 4D peaks?
      zPositions = self.current.strip.orderedAxes[2].region
    else:
      zPositions = None

    # now select (take first one within range)
    for spectrumView in self.current.strip.spectrumViews:
      if spectrumView.spectrum.dimensionCount == 1:
        continue
      for peakListView in spectrumView.peakListViews:
        if peakListView.isVisible():
          for peak in peakListView.peakList.peaks:
            if (xPositions[0] < float(peak.position[0]) < xPositions[1]
              and yPositions[0] < float(peak.position[1]) < yPositions[1]):
              if zPositions is None or (zPositions[0] < float(peak.position[2]) < zPositions[1]):
                peak.isSelected = True
                # Bug fix - Rasmus 14/3/2016
                # self.current.peak = peak
                self.current.addPeak(peak)
                break

  def _resetBoxes(self):
    "Reset/Hide the boxes "
    self._succesiveClicks = None
    self.selectionBox.hide()
    self.pickBox.hide()
    self.rbScaleBox.hide()

  def _hoverEvent(self, event):
    self.current.viewBox = self
    if hasattr(event, '_scenePos'):
      self.position = self.mapSceneToView(event.pos())

  def _updateSelectionBox(self, p1:float, p2:float):
    """
    Updates drawing of selection box as mouse is moved.
    """
    r = QtCore.QRectF(p1, p2)
    r = self.childGroup.mapRectFromParent(r)
    self.selectionBox.setPos(r.topLeft())
    self.selectionBox.resetTransform()
    self.selectionBox.scale(r.width(), r.height())
    self.selectionBox.show()

  def _updatePickBox(self, p1:float, p2:float):
    """
    Updates drawing of selection box as mouse is moved.
    """
    r = QtCore.QRectF(p1, p2)
    r = self.childGroup.mapRectFromParent(r)
    self.pickBox.setPos(r.topLeft())
    self.pickBox.resetTransform()
    self.pickBox.scale(r.width(), r.height())
    self.pickBox.show()

  def _mouseDragEvent(self, event:QtGui.QMouseEvent, axis=None):
    """
    Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
    drag events.
    """

    self.current.strip = self.parentObject().parent
    if leftMouse(event):
      # Left-drag: Panning of the spectrum
      pg.ViewBox.mouseDragEvent(self, event)

    elif controlShiftLeftMouse(event):
      # Control(Cmd)+shift+left drag: Peak-picking
      event.accept()
      if not event.isFinish():
        # not isFinish() is not the same as isStart() in behavior; The latter will fire for every move, the former only
        # at the end of the move
        self._resetBoxes()
        self._updatePickBox(event.buttonDownPos(), event.pos())
      else:
        self._resetBoxes()
        startPosition = self.mapSceneToView(event.buttonDownPos())
        endPosition = self.mapSceneToView(event.pos())
        orderedAxes = self.current.strip.orderedAxes
        selectedRegion = [[round(startPosition.x(), 3), round(startPosition.y(), 3)],
                          [round(endPosition.x(), 3), round(endPosition.y(), 3)]]
        if len(orderedAxes) > 2:
          for n in orderedAxes[2:]:
            selectedRegion[0].append(n.region[0])
            selectedRegion[1].append(n.region[1])
        for spectrumView in self.current.strip.spectrumViews:
          if not spectrumView.isVisible():
            continue
          peakList = spectrumView.spectrum.peakLists[0]
          if self.current.project._appBase.ui.mainWindow is not None:
            mainWindow = self.current.project._appBase.ui.mainWindow
          else:
            mainWindow = self.current.project._appBase._mainWindow
          console = mainWindow.pythonConsole

          if spectrumView.spectrum.dimensionCount > 1:
            # nD's
            a = sorted(map(list, zip(*selectedRegion)))
            selectedRegion = [tuple(sorted(x)) for x in (list(a))]
            # TODO: remove/alter api-involvement
            apiSpectrumView = spectrumView._wrappedData
            newPeaks = peakList.pickPeaksNd(selectedRegion,
                                            doPos=apiSpectrumView.spectrumView.displayPositiveContours,
                                            doNeg=apiSpectrumView.spectrumView.displayNegativeContours,
                                            fitMethod='gaussian')
          else:
            # 1D's
            y0 = startPosition.y()
            y1 = endPosition.y()
            y0, y1 = min(y0, y1), max(y0, y1)
            newPeaks = peakList.pickPeaks1d(spectrumView,  [startPosition.x(), endPosition.x()], [y0, y1])

          # Add the new peaks to selection
          for peak in newPeaks:
            peak.isSelected = True
            self.current.addPeak(peak)

          for window in self.current.project.windows:
            for spectrumDisplay in window.spectrumDisplays:
              for strip in spectrumDisplay.strips:
                spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews]
                if peakList.spectrum in spectra:
                  strip.showPeaks(peakList)

    elif controlLeftMouse(event):
      # Control(Cmd)+left drag: selects peaks
      event.accept()
      if not event.isFinish():
        # not isFinish() is not the same as isStart() in behavior; The latter will fire for every move, the former only
        # at the end of the move
        self._resetBoxes()
        self._updateSelectionBox(event.buttonDownPos(), event.pos())
      else:
        self._resetBoxes()
        endPosition = self.mapSceneToView(event.pos())
        startPosition = self.mapSceneToView(event.buttonDownPos())
        xPositions = sorted(list([startPosition.x(), endPosition.x()]))
        yPositions = sorted(list([startPosition.y(), endPosition.y()]))
        if len(self.current.strip.orderedAxes) > 2:
          zPositions = self.current.strip.orderedAxes[2].region
        else:
          zPositions = None
        # selectedPeaks = []
        #self.current.clearPeaks()
        for spectrumView in self.current.strip.spectrumViews:
          for peakListView in spectrumView.peakListViews:
            if not peakListView.isVisible():
              continue
            peakList = peakListView.peakList
            stripAxisCodes = self.current.strip.axisOrder
            # TODO: Special casing 1D here, seems like a hack.
            if len(spectrumView.spectrum.axisCodes) == 1:
              y0 = startPosition.y()
              y1 = endPosition.y()
              y0, y1 = min(y0, y1), max(y0, y1)
              xAxis = 0
              scale = peakList.spectrum.scale
              for peak in peakList.peaks:
                height = peak.height * scale # TBD: is the scale already taken into account in peak.height???
                if xPositions[0] < float(peak.position[xAxis]) < xPositions[1] and y0 < height < y1:
                  peak.isSelected = True
                  self.current.addPeak(peak)
            else:
              # print('***', stripAxisCodes, spectrumView.spectrum.axisCodes)
              # Fixed 13/3/2016 Rasmus Fogh
              # Avoid comparing spectrum AxisCodes to display axisCodes - they are not identical
              spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
              xAxis = spectrumIndices[0]
              yAxis = spectrumIndices[1]
              # axisMapping = axisCodeMapping(stripAxisCodes, spectrumView.spectrum.axisCodes)
              # xAxis = spectrumView.spectrum.axisCodes.index(axisMapping[self.current.strip.orderedAxes[0].code])
              # yAxis = spectrumView.spectrum.axisCodes.index(axisMapping[self.current.strip.orderedAxes[1].code])
              for peak in peakList.peaks:
                if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                  and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):
                  if zPositions is not None:
                    zAxis = spectrumIndices[2]
                    # zAxis = spectrumView.spectrum.axisCodes.index(axisMapping[self.current.strip.orderedAxes[2].code])
                    if zPositions[0] < float(peak.position[zAxis]) < zPositions[1]:
                      peak.isSelected = True
                      self.current.addPeak(peak)
                  else:
                    peak.isSelected = True
                    self.current.addPeak(peak)

    elif middleMouse(event) or \
         shiftLeftMouse(event)or shiftMiddleMouse(event) or shiftRightMouse(event):
      # Middle-drag, shift-left-drag, shift-middle-drag, shift-right-drag: draws a zooming box and zooms the viewbox.
      event.accept()
      if not event.isFinish():
        # not isFinish() is not the same as isStart() in behavior; The latter will fire for every move, the former only
        # at the end of the move
        self._resetBoxes()
        self.updateScaleBox(event.buttonDownPos(), event.pos())
      else: ## This is the final move in the drag; change the view scale now
        self._resetBoxes()
        self._setView(Point(event.buttonDownPos(event.button())), Point(event.pos()))

    ## above events remove pan abilities from plot window,
    ## need to re-implement them without changing mouseMode
    else:
      event.ignore()

  def _setView(self, point1, point2):
      ax = QtCore.QRectF(point1, point2)
      ax = self.childGroup.mapRectFromParent(ax)
      self.showAxRect(ax)
      self.axHistoryPointer += 1
      self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
