"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from pyqtgraph.Point import Point

from ccpncore.gui.Menu import Menu

from ccpncore.lib.spectrum.Spectrum import axisCodeMapping

class ViewBox(pg.ViewBox):

  sigClicked = QtCore.Signal(object)

  def __init__(self, current=None, parent=None, *args, **kwds):
    pg.ViewBox.__init__(self, *args, **kwds)
    self.current = current
    self.menu = None # Override pyqtgraph ViewBoxMenu
    self.menu = self.getMenu()
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


  def raiseContextMenu(self, event:QtGui.QMouseEvent):
    """
    Raise the context menu
    """
    position  = event.screenPos()
    self.menu.popup(QtCore.QPoint(position.x(), position.y()))

  def getMenu(self):
    if self.menu is None:
      self.menu = Menu('', self.parent(), isFloatWidget=True)
      return self.menu



  def mouseClickEvent(self, event:QtGui.QMouseEvent, axis=None):
    """
    Re-implementation of PyQtGraph mouse drag event to allow custom actions off of  different mouse
    click events.

    Left click selects peaks in a spectrum display.
    Shift+Left click picks a peak at the cursor position.
    Right click raises the context menu.


    """
    self.current.strip = self.parentObject().parent

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():

      selectedPeaks = []
      event.accept()
      # print('Left Click Event')
      xPosition = self.mapSceneToView(event.pos()).x()
      yPosition = self.mapSceneToView(event.pos()).y()
      # print('position',xPosition, yPosition)
      # for spectrumView in self.current.strip.spectrumViews:
      #   for peakList in spectrumView.spectrum.peakLists:
      #     for peak in peakList.peaks:
      #       # print('x',xPosition-0.05, peak.position[0], xPosition+0.05)
      #       # print('y',yPosition-0.05, peak.position[1], yPosition+0.05)
      #       if (xPosition-0.05 < float(peak.position[0]) < xPosition+0.05
      #       and yPosition-0.05 < float(peak.position[1]) <
      #           yPosition+0.05):
      #         msg = 'self.current.peak = ' + peak.pid + '\n'
      #         selectedPeaks.append(peak)
      #         self.parent._appBase.mainWindow.pythonConsole.write(msg)
      #
      # msg = 'self.current.peaks = ' + [peak.pid for peak in selectedPeaks]+ '\n'
      # self.parent._appBase.mainWindow.pythonConsole.write(msg)




    #
    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():

      selectedPeaks = []
      event.accept()
      # print('Left Click Event')
      xPositions = [self.mapSceneToView(event.pos()).x()-0.05, self.mapSceneToView(event.pos()).x()+0.05]
      yPositions = [self.mapSceneToView(event.pos()).y()-0.05, self.mapSceneToView(event.pos()).y()+0.05]
      if len(self.current.strip.orderedAxes) > 2:
          zPositions = self.current.strip.orderedAxes[2].region
      else:
        zPositions = None
      for spectrumView in self.current.strip.spectrumViews:
        for peakList in spectrumView.spectrum.peakLists:
          for peak in peakList.peaks:
            if (xPositions[0] < float(peak.position[0]) < xPositions[1]
              and yPositions[0] < float(peak.position[1]) < yPositions[1]):
              if zPositions is not None:
                if zPositions[0] < float(peak.position[2]) < zPositions[1]:
                  peak.isSelected = True
    #   position = event.scenePos()
    #   mousePoint = self.mapSceneToView(position)
    #   print(mousePoint)
      # for spectrumView in self.current.strip.spectrumViews:
      #   peakList = spectrumView.spectrum.peakLists[0]
      #   newPeak = peakList.newPeak(position=[mousePoint.x(), mousePoint.y()])
      #   # print(newPeak.position)
      #   self.current.strip.showPeaks(peakList)

    # elif (event.button() == QtCore.Qt.LeftButton) and (
    #           event.modifiers() & QtCore.Qt.ShiftModifier) and not (
    # event.modifiers() & QtCore.Qt.ControlModifier):
    #   print('Add Select')
    #
    # elif event.button() == QtCore.Qt.MiddleButton and not event.modifiers():
    #   event.accept()
    #   print('Pick and Assign')

    if event.button() == QtCore.Qt.RightButton and not event.modifiers() and axis is None:
      event.accept()
      self.raiseContextMenu(event)

    elif event.button() == QtCore.Qt.RightButton and not event.modifiers():
      event.accept()
    #
    elif event.button() == QtCore.Qt.LeftButton and (event.modifiers() & QtCore.Qt.ShiftModifier):
      mousePosition=self.mapSceneToView(event.pos())
      position = [mousePosition.x(), mousePosition.y()]
      for spectrumView in self.current.strip.spectrumViews:
        peakList = spectrumView.spectrum.peakLists[0]
        orderedAxes = self.current.strip.orderedAxes
        if len(orderedAxes) > 2:
          for n in orderedAxes[2:]:
            position.append(n.position)
        peakList.newPeak(position=position)
        self.current.strip.showPeaks(peakList)


    elif event.button() == QtCore.Qt.RightButton and (event.modifiers() & QtCore.Qt.ShiftModifier):
      event.accept()
      # self.autoRange()
    #
    # if event.double():
    #   event.accept()
    #   print("Double Click event")

  # def hoverEvent(self, event):
  #
  #   self.current.strip = self.parentObject().parent


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

  def mouseDragEvent(self, event:QtGui.QMouseEvent, axis=None):
    """
    Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
    drag events.

    Left drag pans the spectrum.
    Control+left drag picks peaks in an area specified by the mouse.
    Shift+left drag selects peaks in an area specified by the mouse.
    Shift+right drag/middle drag draws a zooming box and zooms the viewbox.
    """

    self.current.strip = self.parentObject().parent
    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      pg.ViewBox.mouseDragEvent(self, event)

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and not (
              event.modifiers() & QtCore.Qt.ShiftModifier):
      if event.isFinish():

        self.pickBox.hide()
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
          peakList = spectrumView.spectrum.peakLists[0]
          console = self.current.project._appBase.mainWindow.pythonConsole


          if spectrumView.spectrum.dimensionCount > 1:

            apiSpectrumView = spectrumView._wrappedData
            newPeaks = peakList.pickPeaksNd(selectedRegion, apiSpectrumView.spectrumView.orderedDataDims,
                                            doPos=apiSpectrumView.spectrumView.displayPositiveContours,
                                            doNeg=apiSpectrumView.spectrumView.displayNegativeContours,
                                            fitMethod='gaussian')
            # console.writeCommand('peakList', 'peakList.pickPeaksNd',
            #                      'selectedRegion={0}, doPos={1}, doNeg={2}'.format(
            #                      selectedRegion, apiSpectrumView.spectrumView.displayPositiveContours,
            #                      apiSpectrumView.spectrumView.displayNegativeContours),
            #                      obj=peakList)
            console.writeConsoleCommand(
              "peakList.pickPeaksNd('selectedRegion={0}, doPos={1}, doNeg={2})".format(
                selectedRegion, apiSpectrumView.spectrumView.displayPositiveContours,
                apiSpectrumView.spectrumView.displayNegativeContours
              ), peakList=peakList
            )
          else:
            newPeaks = peakList.pickPeaks1dFiltered(spectrumView)

          for window in self.current.project.windows:
            for spectrumDisplay in window.spectrumDisplays:
              for strip in spectrumDisplay.strips:
                spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews]
                if peakList.spectrum in spectra:
                  strip.showPeaks(peakList)


      else:
          self._updatePickBox(event.buttonDownPos(), event.pos())
      event.accept()



    elif (event.button() == QtCore.Qt.RightButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier) or event.button() == QtCore.Qt.MidButton:
      if event.isFinish():  ## This is the final move in the drag; change the view scale now
        self.rbScaleBox.hide()
        ax = QtCore.QRectF(Point(event.buttonDownPos(event.button())), Point(event.pos()))
        ax = self.childGroup.mapRectFromParent(ax)
        self.showAxRect(ax)
        self.axHistoryPointer += 1
        self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
      else:
        self.updateScaleBox(event.buttonDownPos(), event.pos())

      event.accept()

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and (
              event.modifiers() & QtCore.Qt.ShiftModifier):


      event.accept()




    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier):
       # Add select area
      if event.isStart():
        startPosition = event.buttonDownPos()
      elif event.isFinish():
        endPosition = self.mapSceneToView(event.pos())
        self.selectionBox.hide()
        startPosition = self.mapSceneToView(event.buttonDownPos())
        xPositions = sorted(list([startPosition.x(), endPosition.x()]))
        yPositions = sorted(list([startPosition.y(), endPosition.y()]))
        if len(self.current.strip.orderedAxes) > 2:
          zPositions = self.current.strip.orderedAxes[2].region
        else:
          zPositions = None
        # selectedPeaks = []
        for spectrumView in self.current.strip.spectrumViews:
          for peakList in spectrumView.spectrum.peakLists:
            stripAxisCodes = [axis.code for axis in self.current.strip.orderedAxes]
            axisMapping = axisCodeMapping(stripAxisCodes, spectrumView.spectrum.axisCodes)
            xAxis = spectrumView.spectrum.axisCodes.index(axisMapping[self.current.strip.orderedAxes[0].code])
            yAxis = spectrumView.spectrum.axisCodes.index(axisMapping[self.current.strip.orderedAxes[1].code])
            for peak in peakList.peaks:
              if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):
                if zPositions is not None:
                  zAxis = spectrumView.spectrum.axisCodes.index(axisMapping[self.current.strip.orderedAxes[2].code])
                  if zPositions[0] < float(peak.position[zAxis]) < zPositions[1]:
                    peak.isSelected = True
                else:
                  peak.isSelected = True
      else:
        self._updateSelectionBox(event.buttonDownPos(), event.pos())
      event.accept()



    ## above events remove pan abilities from plot window,
    ## need to re-implement them without changing mouseMode
    else:
      event.ignore()
