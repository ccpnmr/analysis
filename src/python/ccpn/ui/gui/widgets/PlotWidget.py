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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence

import pyqtgraph as pg
from PyQt4 import QtCore, QtGui, QtOpenGL

from ccpn.ui.gui.widgets.ViewBox import ViewBox
from ccpn.ui.gui.widgets.ViewBox import CrossHair
from ccpn.ui.gui.widgets.CcpnGridItem import CcpnGridItem
from ccpn.ui.gui.lib.mouseEvents import rightMouse

from ccpn.util.Colour import Colour

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Ruler as ApiRuler

#TODO:WAYNE: This class should contain all the nitty gritty of the displaying; including the axis labels and the like
# as it is only there and is just a small wrapper arount a pyqtgraph class
# goes together with AxisTextItem (probably can be reduced to a function and included here.
#TODO:WAYNE: should this inherit from Base??
class PlotWidget(pg.PlotWidget):

  def __init__(self, strip, useOpenGL=False, showDoubleCrosshair=False):

    # Be sure to use explicit arguments to ViewBox as the call order is different in the __init__
    self.viewBox = ViewBox(strip)
    pg.PlotWidget.__init__(self, parent=strip,
                                 viewBox=self.viewBox,
                                 axes=None, enableMenu=True)

    self.strip = strip

    self.plotItem.setAcceptHoverEvents(True)
    self.setInteractive(True)
    self.plotItem.setAcceptDrops(True)
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)

    self.rulerLineDict = {}  # ruler --> line for that ruler
    self.rulerLabelDict = {}  # ruler --> label for that ruler

    self.xAxisAtomLabels = []
    self.yAxisAtomLabels = []

    self.xAxisTextItem = None
    self.yAxisTextItem = None

    self.hideButtons()

    if useOpenGL:
      self.setViewport(QtOpenGL.QGLWidget())
      # need FullViewportUpdate below, otherwise ND windows do not update when you pan/zoom
      # (BoundingRectViewportUpdate might work if you can implement boundingRect suitably)
      # (NoViewportUpdate might work if you could explicitly get the view to repaint when needed)
      self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)

    strip.spectrumDisplay.mainWindow._mouseMovedSignal.connect(self._mousePositionChanged)

    #TODO:GEERTEN: Fix with proper stylesheet
    # Also used in AxisTextItem
    # NOTE: self.highlightColour is also being used in GuiPeakListView for selected peaks
    if strip.spectrumDisplay.mainWindow.application.colourScheme == 'light':
      self.background = '#f7ffff'
      self.foreground = '#080000'
      self.gridColour = '#080000'
      self.highlightColour = '#3333ff'
    else:
      self.background = '#080000'
      self.foreground = '#f7ffff'
      self.gridColour = '#f7ffff'
      self.highlightColour = '#00ff00'
    self.setBackground(self.background)
    #self.setForeground(self.foreground) # does not seem to have this (or typo?)

    # axes
    self.plotItem.axes['left']['item'].hide()
    self.plotItem.axes['right']['item'].show()
    for orientation in ('left', 'top'):
      axisItem = self.plotItem.axes[orientation]['item']
      axisItem.hide()
    for orientation in ('right', 'bottom'):
      axisItem = self.plotItem.axes[orientation]['item']
      axisItem.setPen(color=self.foreground)

    # add grid
    self.grid = CcpnGridItem(gridColour=self.gridColour)
    self.addItem(self.grid, ignoreBounds=False)

    # Add two crosshairs
    self.crossHair1 = CrossHair(self, show=True, colour=self.foreground)
    self.crossHair2 = CrossHair(self, show=showDoubleCrosshair, colour=self.foreground)

  def highlightAxes(self, state=False):
    "Highlight the axes on/of"
    if state:
      for orientation in ('right', 'bottom'):
        axisItem = self.plotItem.axes[orientation]['item']
        axisItem.setPen(color=self.highlightColour)
    else:
      for orientation in ('right', 'bottom'):
        axisItem = self.plotItem.axes[orientation]['item']
        axisItem.setPen(color=self.foreground)

  def toggleGrid(self):
    "Toggle grid state"
    self.grid.setVisible(not self.grid.isVisible())

  def __getattr__(self, attr):
    """
    Wrap pyqtgraph PlotWidget __getattr__, which raises wrong error and so makes hasattr fail.
    """
    try:
      return super().__getattr__(attr)
    except NameError:
      raise AttributeError(attr)

  def addItem(self, item:QtGui.QGraphicsObject):
    """
    Adds specified graphics object to the Graphics Scene of the PlotWidget.
    """
    self.scene().addItem(item)

  # copied from GuiStripNd!
  def _mouseDragEvent(self, event):
    """
    Re-implemented mouse event to enable smooth panning.
    """
    if rightMouse(event):
      pass
    else:
      self.viewBox.mouseDragEvent(self, event)

  def _crosshairCode(self, axisCode):
    # determines what axisCodes are compatible as far as drawing crosshair is concerned
    # TBD: the naive approach below should be improved
    return axisCode  # if axisCode[0].isupper() else axisCode

  @QtCore.pyqtSlot(dict)
  def _mousePositionChanged(self, mouseMovedDict):
    """
      This is called when the mouse position is changed in some strip
      It means the crosshair(s) position should be updated
    :param mouseMovedDict: 'strip'->strip and axisCode->position for each axisCode in strip
    :return:  None
    """
    strip = self.strip
    if strip.isDeleted: return
    if not strip._finaliseDone: return

    axes = strip.orderedAxes

    # TODO:ED sometimes set to None
    xPos = mouseMovedDict.get(self._crosshairCode(axes[0].code))
    yPos = mouseMovedDict.get(self._crosshairCode(axes[1].code))
    #print('>>', strip, xPos, yPos)
    self.crossHair1.setPosition(xPos, yPos)

    strip.axisPositionDict[axes[0].code] = xPos
    strip.axisPositionDict[axes[1].code] = yPos

    #TODO:SOLIDS This is clearly not correct; it should take the offset as defined for spectrum
    xPos = mouseMovedDict.get(self._crosshairCode(axes[1].code))
    yPos = mouseMovedDict.get(self._crosshairCode(axes[0].code))
    self.crossHair2.setPosition(xPos, yPos)

  # NBNB TODO code uses API object. REFACTOR

  def _addRulerLine(self, apiRuler:ApiRuler):
    """CCPN internal
       Called from GuiStrip when a ruler is created
       This adds a line into the PlotWidget"""

    axisCode = apiRuler.axisCode # TODO: use label and unit
    position = apiRuler.position
    label = apiRuler.label
    if apiRuler.mark.colour[0] == '#':  # TODO: why this restriction???
      colour = Colour(apiRuler.mark.colour)  # TODO: this is a CCPN object, does it work to set pen=colour below
    else:
      colour = self.foreground
    strip = self.strip
    axisOrder = strip.axisOrder

    # TODO: is the below correct (so the correct axes)?
    if axisCode == axisOrder[0]:
      angle = 90
      y = self.plotItem.vb.mapSceneToView(strip.viewBox.boundingRect().bottomLeft()).y()
      textPosition = (position, y)
      textAnchor = 1
      labels = self.xAxisAtomLabels
    elif axisCode == axisOrder[1]:
      angle = 0
      x = strip.plotWidget.plotItem.vb.mapSceneToView(strip.viewBox.boundingRect().bottomLeft()).x()
      textPosition = (x, position)
      textAnchor = 0
      labels = self.yAxisAtomLabels
    else:
      return

    line = pg.InfiniteLine(angle=angle, movable=False, pen=colour)
    line.setPos(position)
    self.addItem(line, ignoreBounds=True)
    self.rulerLineDict[apiRuler] = line
    if label:
      textItem = pg.TextItem(label, color=colour)
      textItem.anchor = pg.Point(0, textAnchor)
      textItem.setPos(*textPosition)
      self.addItem(textItem)
      labels.append(textItem)
      self.rulerLabelDict[apiRuler] = textItem

  def _removeRulerLine(self, apiRuler:ApiRuler):
    """CCPN internal
       Called from GuiStrip when a ruler is deleted
       This removes a line into the PlotWidget"""

    if apiRuler in self.rulerLineDict:
      line = self.rulerLineDict.pop(apiRuler)
      self.removeItem(line)
    if apiRuler in self.rulerLabelDict:
      label = self.rulerLabelDict.pop(apiRuler)
      self.removeItem(label)


  # TODO:WAYNE: Make this part of PlotWidget [done], pass axes label strings on init [??]
  def _moveAxisCodeLabels(self):
    """CCPN internal
       Called from a notifier in GuiStrip
       Puts axis code labels in the correct place on the PlotWidget
    """
    if not self.strip._finaliseDone: return
    self.xAxisTextItem.setPos(self.viewBox.boundingRect().bottomLeft())
    self.yAxisTextItem.setPos(self.viewBox.boundingRect().topRight())
    for item in self.xAxisAtomLabels:
      y = self.plotItem.vb.mapSceneToView(self.strip.viewBox.boundingRect().bottomLeft()).y()
      x = item.pos().x()
      item.setPos(x, y)
    for item in self.yAxisAtomLabels:
      x = self.plotItem.vb.mapSceneToView(self.strip.viewBox.boundingRect().bottomLeft()).x()
      y = item.pos().y()
      item.setPos(x, y)

  def _initTextItems(self):
    """CCPN internal
       Called from GuiStrip when axes are ready
    """
    axisOrder = self.strip.axisOrder
    self.xAxisTextItem = AxisTextItem(self, orientation='top', axisCode=axisOrder[0])
    self.yAxisTextItem = AxisTextItem(self, orientation='left', axisCode=axisOrder[1])

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
