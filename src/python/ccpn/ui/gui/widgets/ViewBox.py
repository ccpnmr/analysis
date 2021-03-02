"""
By Functionality:

Zoom and pan:
    Left-drag:                          pans the spectrum.

    shift-left-drag:                    draws a zooming box and zooms the viewbox.
    shift-middle-drag:                  draws a zooming box and zooms the viewbox.
    shift-right-drag:                   draws a zooming box and zooms the viewbox.
    Two successive shift-right-clicks:  define zoombox
    control-right click:                reset the zoom

Peaks:
    Left-click:                         select peak near cursor in a spectrum display, deselecting others
    Control(Cmd)-left-click:            (de)select peak near cursor in a spectrum display, adding/removing to selection.
    Control(Cmd)-left-drag:             selects peaks in an area specified by the dragged region.
    Middle-drag:                        Moves a selected peak.
    Control(Cmd)-Shift-Left-click:      picks a peak at the cursor position, adding to selection
    Control(Cmd)-shift-left-drag:       picks peaks in an area specified by the dragged region.

Others:
    Right-click:                        raises the context menu.


By Mouse button:

    Left-click:                         select peak near cursor in a spectrum display, deselecting others
    Control(Cmd)-left-click:            (de)select peak near cursor in a spectrum display, adding/removing to selection.
    Control(Cmd)-Shift-Left-click:      picks a peak at the cursor position, adding to selection

    Left-drag:                          pans the spectrum.
    shift-left-drag:                    draws a zooming box and zooms the viewbox.
    Control(Cmd)-left-drag:             selects peaks in an area specified by the dragged region.
    Control(Cmd)-shift-left-drag:       picks peaks in an area specified by the dragged region.


    shift-middle-drag:                  draws a zooming box and zooms the viewbox.

    Right-click:                        raises the context menu.
    control-right click:                reset the zoom
    Two successive shift-right-clicks:  define zoombox

    shift-right-drag:                   draws a zooming box and zooms the viewbox.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-02 15:00:02 +0000 (Tue, March 02, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-22 15:13:45 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph.Point import Point
from ccpn.util import Common as commonUtil
import numpy as np

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.widgets.Menu import Menu

from ccpn.util.Logging import getLogger

# GWV: moved to ccpn.ui.gui.lib.mouseEvents on 17/04/2017
from ccpn.ui.gui.lib.mouseEvents import \
    leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, \
    middleMouse, shiftMiddleMouse, controlMiddleMouse, controlShiftMiddleMouse, \
    rightMouse, shiftRightMouse, controlRightMouse, controlShiftRightMouse, PICK, SELECT
from ccpn.ui.gui.widgets.LinearRegionsPlot import LinearRegionsPlot
from ccpn.ui.gui.lib.mouseEvents import MouseModes, getCurrentMouseMode
from ccpn.core.lib.ContextManagers import undoBlock


class CrossHair:
    "class to implement a cross-hair"

    def __init__(self, plotWidget, position=Point(0, 0), show=True, rgb=None, colour=None, moveable=False, **kwds):
        """CrossHair init,
           stetting color, using rgb or colour, which-ever is
                           not None (default to grey) + optional **kwds
           setting visibility
           it adds CrossHair hLine and vLine plot items to parent using addItem method
        """
        self.plotWidget = plotWidget

        if rgb:
            pen = pg.functions.mkPen(color=rgb, **kwds)
        elif colour:
            pen = pg.functions.mkPen(color=rgb, **kwds)
        else:
            pen = pg.functions.mkPen(color=(129, 129, 129), **kwds)

        self.vLine = pg.InfiniteLine(angle=90, movable=moveable, pen=pen)
        self.hLine = pg.InfiniteLine(angle=0, movable=moveable, pen=pen)
        plotWidget.addItem(self.vLine, ignoreBounds=True)
        plotWidget.addItem(self.hLine, ignoreBounds=True)

        # ejb - set the Z value to 1.0 to bring to the top
        self.vLine.setZValue(1.0)
        self.hLine.setZValue(1.0)

        self.setPointPosition(position)
        if show:
            self.show()
        else:
            self.hide()

    def setPosition(self, xPos: float, yPos: float):
        "Set position in world xPos, yPos coordinates"
        self.setVline(xPos)
        self.setHline(yPos)

    def setVline(self, xPos: float):
        "Set vertical line in world xPos coordinates"
        if xPos is not None:
            self.vLine.setPos(xPos)

    def setHline(self, yPos: float):
        "Set horizontal  in world xPos coordinates"
        if yPos is not None:
            self.hLine.setPos(yPos)

    def setPointPosition(self, position: QtCore.QPointF):
        "Set position in Point syntax"
        self.setPosition(position.x(), position.y())

    def show(self):
        #print(">> show")
        self.vLine.show()
        self.hLine.show()

    def hide(self):
        #print(">> hide")
        self.vLine.hide()
        self.hLine.hide()

    def isVisible(self):
        return self.vLine.isVisible()

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


class ViewBox(pg.ViewBox):
    """
    Base-class to implement mouse and drag events in PlotWidget.py;
    it will inherit the same parent as PlotWidget
    """

    def __init__(self, strip):
        pg.ViewBox.__init__(self)

        # Override pyqtgraph ViewBoxMenu
        self.menu = self._getMenu()  # built in GuiStrip, GuiStripNd, GuiStrip1D
        self.strip = strip
        self.application = self.current = strip.spectrumDisplay.mainWindow.application
        self.current = self.application.current
        self.preferences = self.application.preferences
        self.mainWindow = strip.spectrumDisplay.mainWindow

        self._setMouseCursor()

        # self.rbScaleBox: Native PyQtGraph; used for Zoom

        self.selectionBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self.selectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
        self.selectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
        self.selectionBox.setZValue(1e9)
        self.selectionBox.hide()
        self.addItem(self.selectionBox, ignoreBounds=True)

        self.pickBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self.pickBox.setPen(pg.functions.mkPen((0, 255, 255), width=1))
        self.pickBox.setBrush(pg.functions.mkBrush(100, 255, 255, 100))
        self.pickBox.setZValue(1e9)
        self.pickBox.hide()
        self.addItem(self.pickBox, ignoreBounds=True)

        self.mouseClickEvent = self._mouseClickEvent
        self.mouseDragEvent = self._mouseDragEvent
        self.hoverEvent = self._hoverEvent
        self.state['wheelScaleFactor'] = -1.0 / 20.0  #speed of the wheel event. the larger the denominator the slower the zoom

        self._successiveClicks = None  # GWV: Store successive click events for zooming; None means first click not set
        self.crossHair = CrossHair(self, show=False, rgb=(255, 255, 0), dash=[20.0, 7.0])  # dashes in pixels, [on, off]

        # not needed anymore
        # self.integralRegions = LinearRegionsPlot(values=[0, 0], orientation='v', bounds=None,
        #                                          brush=None, colour='purple', movable=True)
        # for line in self.integralRegions.lines:
        #   line.sigPositionChanged.connect(self._integralRegionsMoved)

        # TODO:ED smaller cross for now, need to scale for ppm
        self.peakWidthPixels = 16  # for ND peaks
        self.contextMenuPosition = None  #we need this because current.position is not always the best choice for everything!

    def _raiseContextMenu(self, event: QtGui.QMouseEvent):
        """
        Raise the context menu
        """

        position = event.screenPos()

        self.menu.popup(QtCore.QPoint(position.x(), position.y()))

        self.contextMenuPosition = self.current.cursorPosition

    def _getMenu(self):
        if self.menu is None:
            self.menu = Menu('', self.parent(), isFloatWidget=True)
            return self.menu

    def _setMouseCursor(self):

        # if self.application.ui.mainWindow.mouseMode == PICK:
        if getCurrentMouseMode() == PICK:
            cursor = QtGui.QCursor(QtCore.Qt.CrossCursor)
            self.setCursor(cursor)

        else:
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def _pickAtMousePosition(self, event):
        ''
        event.accept()
        self._resetBoxes()
        mousePosition = self.mapSceneToView(event.pos())
        position = [mousePosition.x(), mousePosition.y()]
        orderedAxes = self.current.strip.orderedAxes
        for orderedAxis in orderedAxes[2:]:
            position.append(orderedAxis.position)

        newPeaks = self.current.strip.peakPickPosition(position)
        self.current.peaks = newPeaks

    def _mouseClickEvent(self, event: QtGui.QMouseEvent, axis=None):
        """
        Re-implementation of PyQtGraph mouse click event to allow custom actions
        for different mouse click events.
        """
        self.current.strip = self.strip
        xPosition = self.mapSceneToView(event.pos()).x()
        yPosition = self.mapSceneToView(event.pos()).y()
        self.current.positions = [xPosition, yPosition]

        # This is the correct future style for cursorPosition handling
        self.current.cursorPosition = (xPosition, yPosition)

        # if self.application.ui.mainWindow.mouseMode == PICK:
        if getCurrentMouseMode() == PICK:
            self._pickAtMousePosition(event)

        if controlShiftLeftMouse(event):
            # Control-Shift-left-click: pick peak
            self._pickAtMousePosition(event)

            # peaks = list(self.current.peaks)
            # peakLists = []
            #
            # for spectrumView in self.current.strip.spectrumViews:
            #   if not spectrumView.peakListViews:
            #     continue
            #   peakListView = spectrumView.peakListViews[0]  # TODO: is there some way of specifying which peakListView
            #   if not peakListView.isVisible():
            #     continue
            #   peakList = peakListView.peakList
            #   peak = peakList.newPeak(ppmPositions=position)
            #   # note, the height below is not derived from any fitting
            #   # but is a weighted average of the values at the neighbouring grid points
            #   peak.height = spectrumView.spectrum.getPositionValue(peak.pointPositions)
            #   #self.current.addPeak(peak)
            #   # peak.isSelected = True
            #   peaks.append(peak)
            #   peakLists.append(peakList)
            #
            # self.current.peaks = peaks
            # for peakList in peakLists:
            #   self.current.strip.showPeaks(peakList)

        elif controlLeftMouse(event):
            # Control-left-click; (de-)select peak and add/remove to selection
            event.accept()
            self._resetBoxes()
            # self._deselectPeaks()
            #self.current.clearPeaks()
            self._selectPeak(xPosition, yPosition)

        elif leftMouse(event):
            # Left-click; select peak, deselecting others
            event.accept()
            self._resetBoxes()
            # self._deselectPeaks()
            self.current.clearPeaks()
            self.current.clearIntegrals()
            self._clearIntegralRegions()
            self._selectPeak(xPosition, yPosition)

        elif shiftRightMouse(event):
            # Two successive shift-right-clicks: define zoombox
            event.accept()
            if self._successiveClicks is None:
                self._resetBoxes()
                self._successiveClicks = Point(event.pos())
                position = self.mapSceneToView(event.pos())
                self.crossHair.setPointPosition(position)
                self.crossHair.show()
            else:
                self._setView(Point(self._successiveClicks), Point(event.pos()))
                self._resetBoxes()
                self._successiveClicks = None

        elif rightMouse(event) and axis is None:
            # right click on canvas, not the axes
            event.accept()
            self._resetBoxes()
            self._raiseContextMenu(event)

        elif controlRightMouse(event) and axis is None:
            # control-right-mouse click: reset the zoom
            event.accept()
            self._resetBoxes()
            self.current.strip.resetZoom()

        else:
            # reset and hide all for all other clicks
            self._resetBoxes()
            event.ignore()

    # def _deselectPeaks(self):
    #   "Deselected all current peaks"
    #   # NBNB TBD FIXME. We need to deselect ALL peaks
    #   for spectrumView in self.current.strip.spectrumViews:
    #     for peakList in spectrumView.spectrum.peakLists:
    #       for peak in peakList.peaks:
    #         peak.isSelected = False
    #
    #   # NBNB TBD FIXME this isSelected stuff is a dogs breakfast and needs refactoring.
    #   # Probably we should replace 'peak.isSelected' with 'peak in current.peaks'
    #   # Meanwhile at least deselect current peaks
    #   for peak in self.current.peaks:
    #     peak.isSelected = False
    #
    #   self.current.clearPeaks()

    def _selectPeak(self, xPosition, yPosition):
        """(de-)Select first peak near cursor xPosition, yPosition
           if peak already was selected, de-select it
        """
        xPeakWidth = abs(self.mapSceneToView(QtCore.QPoint(self.peakWidthPixels, 0)).x() - self.mapSceneToView(QtCore.QPoint(0, 0)).x())
        yPeakWidth = abs(self.mapSceneToView(QtCore.QPoint(0, self.peakWidthPixels)).y() - self.mapSceneToView(QtCore.QPoint(0, 0)).y())
        xPositions = [xPosition - 0.5 * xPeakWidth, xPosition + 0.5 * xPeakWidth]
        yPositions = [yPosition - 0.5 * yPeakWidth, yPosition + 0.5 * yPeakWidth]
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

                    # ejb - strange error AttributeError: 'IntegralList' object has no attribute 'peaks'
                    if peakListView.peakList and hasattr(peakListView.peakList, 'peaks'):
                        for peak in peakListView.peakList.peaks:
                            if (xPositions[0] < float(peak.position[0]) < xPositions[1]
                                    and yPositions[0] < float(peak.position[1]) < yPositions[1]):
                                if zPositions is None or (zPositions[0] < float(peak.position[2]) < zPositions[1]):
                                    #print(">>found peak", peak, peak.isSelected, peak in self.current.peaks)
                                    if peak in self.current.peaks:
                                        self.current._peaks.remove(peak)
                                    else:
                                        self.current.addPeak(peak)
                                    break

    def _resetBoxes(self):
        "Reset/Hide the boxes "
        self._successiveClicks = None
        self.selectionBox.hide()
        self.pickBox.hide()
        self.rbScaleBox.hide()
        self.crossHair.hide()

    def _hoverEvent(self, event):
        if hasattr(event, '_scenePos'):
            position = self.mapSceneToView(event.pos())

            if self.strip and hasattr(self.strip, 'spectrumDisplay'):
                self.mainWindow._mousePositionMoved(self.strip, position)

    def _updateSelectionBox(self, p1: float, p2: float):
        """
        Updates drawing of selection box as mouse is moved.
        """
        r = QtCore.QRectF(p1, p2)
        r = self.childGroup.mapRectFromParent(r)
        self.selectionBox.setPos(r.topLeft())
        self.selectionBox.resetTransform()
        self.selectionBox.scale(r.width(), r.height())
        self.selectionBox.show()

    def _updatePickBox(self, p1: float, p2: float):
        """
        Updates drawing of selection box as mouse is moved.
        """
        r = QtCore.QRectF(p1, p2)
        r = self.childGroup.mapRectFromParent(r)
        self.pickBox.setPos(r.topLeft())
        self.pickBox.resetTransform()
        self.pickBox.scale(r.width(), r.height())
        self.pickBox.show()

    def _mouseDragEvent(self, event: QtGui.QMouseEvent, axis=None):
        """
        Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
        drag events.
        """
        self.current.strip = self.strip

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

                selectedRegion = [[round(startPosition.x(), 3), round(endPosition.x(), 3)],
                                  [round(startPosition.y(), 3), round(endPosition.y(), 3)]]
                if len(orderedAxes) > 2:
                    for n in orderedAxes[2:]:
                        selectedRegion.append((n.region[0], n.region[1]))

                # TBD: Should be using onceOnly=True notifiers and suspend/resumeNotification but that is not working.
                # So instead turn off notifications (so that they all get ignored) with blankNotification, and then
                # at the end turn them back on again. This means have to update the relevant parts of the code which
                # needs to know about new peaks. This is not a good way to do it.

                project = self.current.strip.project
                project.blankNotification()

                try:
                    peaks = self.current.strip.peakPickRegion(selectedRegion)
                finally:
                    project.unblankNotification()

                # hide all the messages from the peak annotation generation
                # project._startCommandEchoBlock('mousePeakPicking')
                # update strips which have the above peaks in them
                # (could check for visibility...)

                with undoBlock():
                    peakLists = set([peak.peakList for peak in peaks])
                    for peakList in peakLists:
                        for peakListView in peakList.peakListViews:
                            peakListView.spectrumView.strip.showPeaks(peakList)

                # project._endCommandEchoBlock()
                # update peak table
                # limitation: this will only update the first peak table
                # if hasattr(self.current.strip.spectrumDisplay.mainWindow.application, 'peakTableModule'):
                #     self.current.strip.spectrumDisplay.mainWindow.application.peakTableModule.peakListTable._updateTable()

                self.current.peaks = peaks

        elif controlLeftMouse(event):
            # Control(Cmd)+left drag: selects peaks
            event.accept()
            if not event.isFinish():
                # not isFinish() is not the same as isStart() in behavior; The latter will fire for every move, the former only
                # at the end of the move
                self._resetBoxes()
                self._updateSelectionBox(event.buttonDownPos(), event.pos())
            else:
                self._deselectPeaksFromOtherDisplays()
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
                peaks = list(self.current.peaks)
                for spectrumView in self.current.strip.spectrumViews:
                    for peakListView in spectrumView.peakListViews:
                        if not peakListView.isVisible():
                            continue
                        peakList = peakListView.peakList
                        if not isinstance(peakList, PeakList):  # it could be an IntegralList
                            continue
                        stripAxisCodes = self.current.strip.axisOrder
                        # TODO: Special casing 1D here, seems like a hack.
                        if len(spectrumView.spectrum.axisCodes) == 1:
                            y0 = startPosition.y()
                            y1 = endPosition.y()
                            y0, y1 = min(y0, y1), max(y0, y1)
                            xAxis = 0
                            # scale = peakList.spectrum.scale  # peak height now contains scale in it (so no scaling below)
                            for peak in peakList.peaks:
                                height = peak.height  # * scale # TBD: is the scale already taken into account in peak.height???
                                if xPositions[0] < float(peak.position[xAxis]) < xPositions[1] and y0 < height < y1:
                                    # peak.isSelected = True
                                    #self.current.addPeak(peak)
                                    peaks.append(peak)
                        else:
                            # print('***', stripAxisCodes, spectrumView.spectrum.axisCodes)
                            # Fixed 13/3/2016 Rasmus Fogh
                            # Avoid comparing spectrum AxisCodes to display axisCodes - they are not identical
                            spectrumIndices = spectrumView.dimensionOrdering
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
                                            # peak.isSelected = True
                                            #self.current.addPeak(peak)
                                            peaks.append(peak)
                                    else:
                                        # peak.isSelected = True
                                        #self.current.addPeak(peak)
                                        peaks.append(peak)
                self.current.peaks = peaks

        elif middleMouse(event):
            # middle drag: moves a selected peak
            event.accept()
            self.setMouseEnabled(False, False)
            refPosition = (self.mapSceneToView(event.buttonDownPos()).x(), self.mapSceneToView(event.buttonDownPos()).y())

            peaks = self.current.peaks
            if not peaks:
                return

            deltaPosition = np.subtract(self.current.cursorPosition, refPosition)
            for peak in peaks:
                peak.startPosition = peak.position

            if event.isFinish():
                for peak in peaks:
                    oldPosition = peak.position
                    peak.position = oldPosition + deltaPosition
                    peak._finaliseAction('change')
                    self.setMouseEnabled(True, True)

                    app = self.strip.spectrumDisplay.mainWindow.application
                    app.ui.echoCommands(("project.getByPid(%s).position = %s" % (peak.pid, peak.position),))

                self.current.peaks = peaks
            else:  #this is when is being dragged
                pass
                # for peak in peaks:
                #   # print(peak.position, deltaPosition)
                #   peak.position =  (peak.position[0] + deltaPosition[0],peak.position[1] + deltaPosition[1] )

            # startPoint = Point(event.buttonDownPos())
            # endPoint = Point(event.pos())
            # startPosition = self.childGroup.mapFromParent(startPoint)
            # endPosition = self.childGroup.mapFromParent(endPoint)
            # deltaPosition = endPosition - startPosition
            # deltaPosition = deltaPosition.x(), deltaPosition.y()
            #
            # project = peak.project
            # undo = project._undo
            #
            # if not hasattr(peak, 'startPosition'):
            #   # start of move
            #   project.newUndoPoint()
            #   undo.increaseBlocking()
            #   project.blankNotification()
            #   self.setMouseEnabled(False,False)
            #
            # try:
            #   self.pointer.show()
            #   self.pointer.setPos(endPosition)
            #   if not hasattr(peak, 'startPosition'):
            #     peak.startPosition = peak.position
            #   indices = peakListToIndicesDict[peak.peakList]
            #   position = list(peak.startPosition)
            #   for n, index in enumerate(indices):
            #     position[index] += deltaPosition[n]
            #   peak.position = self.current.cursorPosition
            #   project.newUndoPoint()
            #
            # except:
            #     undo.decreaseBlocking()
            #     project.unblankNotification()
            #     self.setMouseEnabled(True, True)
            #     self.pointer.hide()

            # else:
            # if event.isFinish():
            #   self.pointer.hide()
            #   undo.decreaseBlocking()
            #   project.unblankNotification()
            #   self.setMouseEnabled(True, True)
            #   if hasattr(peak, 'startPosition'):
            #     undo.newItem(setattr, setattr, undoArgs=[peak, 'position', peak.startPosition],
            #                  redoArgs=[peak, 'position', peak.position])
            #     delattr(peak, 'startPosition')
            #   peak._finaliseAction('change')
            #   self.strip.spectrumDisplay.mainWindow.application.ui.echoCommands(
            #     ("project.getByPid(%s).position = %s" % (peak.pid, peak.position),)
            #     )

        elif shiftLeftMouse(event) or shiftMiddleMouse(event) or shiftRightMouse(event):
            # Middle-drag, shift-left-drag, shift-middle-drag, shift-right-drag: draws a zooming box and zooms the viewbox.
            event.accept()
            if not event.isFinish():
                # not isFinish() is not the same as isStart() in behavior; The latter will fire for every move, the former only
                # at the end of the move
                self._resetBoxes()
                self.updateScaleBox(event.buttonDownPos(), event.pos())
            else:
                # This is the final move in the drag; change the view scale now
                self._resetBoxes()
                #self._setView(Point(event.buttonDownPos(event.button())), Point(event.pos()))
                self._setView(Point(event.buttonDownPos()), Point(event.pos()))

        ## above events remove pan abilities from plot window,
        ## need to re-implement them without changing mouseMode
        else:
            self._resetBoxes()
            event.ignore()

    def _deselectPeaksFromOtherDisplays(self):
        if self.current.peak:
            if self.current.strip.spectrumViews:
                if self.current.peak.peakList.spectrum.spectrumViews:
                    if self.current.strip.spectrumViews[0].strip != self.current.peak.peakList.spectrum.spectrumViews[0].strip:
                        # self._deselectPeaks()
                        self.current.clearPeaks()
                        getLogger().warning('Can only multi select from current strip')

    def _setView(self, point1, point2):
        ax = QtCore.QRectF(point1, point2)
        ax = self.childGroup.mapRectFromParent(ax)
        self.showAxRect(ax)
        # GWV: This was copied from pyqtgraph viewbox, but appears a oddly
        # implemented zoom stack, which could amount to a memory leak
        #self.axHistoryPointer += 1
        #self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]

    ##### Action callback: Lines on plot

    def _showIntegralLines(self):
        integral = self.current.integral
        if integral is not None:
            self.integralRegions.setLines(integral.limits[0])
            self.addItem(self.integralRegions)

    def _clearIntegralRegions(self):
        try:
            if self.integralRegions in self.addedItems:
                self.removeItem(self.integralRegions)
        except:
            pass

    def _integralRegionsMoved(self):
        integrals = self.current.integrals
        values = []
        for line in self.integralRegions.lines:
            values.append(line.pos().x())
        for integral in integrals:
            if integral is not None:
                integral.limits = [[min(values), max(values)], ]


def _peaksVisibleInStrip(peaks, strip):
    peakListToIndicesDict = {}
    for spectrumView in strip.spectrumViews:
        if spectrumView.spectrum.dimensionCount == 1:  # skip 1D peakLists
            continue
        indices = spectrumView.dimensionOrdering[:2]
        peakLists = [peakListView.peakList for peakListView in spectrumView.peakListViews if peakListView.isVisible()]
        for peakList in peakLists:
            peakListToIndicesDict[peakList] = indices

    # TBD: strip.positions and strip.widths not kept up to sync with plotWidget,
    # so need to go via plotWidget for now in x, y
    positions = strip.positions
    widths = strip.widths
    viewRange = strip.plotWidget.viewRange()
    positions0 = [viewRange[0][0], viewRange[1][0]]
    positions1 = [viewRange[0][1], viewRange[1][1]]
    for n, position in enumerate(positions):
        if n >= 2:
            positions0.append(positions[n] - 0.5 * widths[n])
            positions1.append(positions[n] + 0.5 * widths[n])

    peaksVisible = []
    for peak in peaks:
        if peak.peakList in peakListToIndicesDict.keys():
            for n, index in enumerate(peakListToIndicesDict[peak.peakList]):
                if hasattr(peak, 'startPosition'):
                    startPosition = peak.startPosition
                else:
                    startPosition = peak.position
                peakPosition = startPosition[index]
                if peakPosition < positions0[n] or peakPosition > positions1[n]:
                    break
            else:
                peaksVisible.append(peak)

    return peaksVisible, peakListToIndicesDict
