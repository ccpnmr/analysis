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
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.FillBetweenRegions import FillBetweenRegions
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
import pyqtgraph as pg
import  numpy as np
from pyqtgraph.graphicsItems.LinearRegionItem import LinearRegionItem
from ccpn.ui.gui.widgets.Icon import Icon






class LinearRegionsPlot(LinearRegionItem):
  """

  Used for marking a horizontal or vertical region in plots.
  The region can be dragged and is bounded by lines which can be dragged individually.
  """

  def __init__(self, values=None, orientation='v', brush = None, colour = None, movable=True, bounds=None, **kwds):
    if orientation == 'v':
      orientation = LinearRegionItem.Vertical
    else:
      orientation = LinearRegionItem.Horizontal

    colours = {
                'green': (0, 111, 20, 50),
                'yellow': (0, 111, 20, 50),
                'blue': None,  # Default,
                'transparent': (0, 111, 20, 50),
                'grey': (255, 255, 255, 50),
                'red': (255, 0, 0, 50),
                'purple': (178, 102, 255, 50)
              }
    if colour in  colours.keys():
      brush = colours[colour]

    LinearRegionItem.__init__(self, values=values, orientation=orientation, brush=brush, movable=movable, bounds=bounds)

  def setLines(self, values):
    self.lines[0].setPos(min(values))
    self.lines[1].setPos(max(values))


class TargetButtonSpinBoxes(Widget):
  def __init__(self, parent, application=None, orientation = 'v', plotWidget=None, values=None, step=None,
               colour = None, brush = None, movable=True, bounds=None, **kwds):
    super().__init__(parent, setLayout=True, **kwds)
    self.parent = parent
    self.plotWidget = plotWidget
    self.application = application

    self.movable = movable
    self.brush = brush
    self.colour = colour
    self.orientation = orientation

    self.toggleOnIcon = Icon('icons/target3+')
    self.toggleOffIcon =  Icon('icons/target3a-')

    tipText = "Select a strip and Toggle to activate the lines"
    self.pickOnSpectrumButton = Button(self, toggle=True,
                                       tipText=tipText, grid=(0, 0),  hAlign='l', vAlign='l' )
    self.pickOnSpectrumButton.setChecked(False)
    if self.pickOnSpectrumButton.isChecked():
      self.pickOnSpectrumButton.setIcon(self.toggleOnIcon)
    elif not self.pickOnSpectrumButton.isChecked():
      self.pickOnSpectrumButton.setIcon(self.toggleOffIcon)
    self.pickOnSpectrumButton.toggled.connect(self._togglePicking)

    self.spinBoxes = []
    self.values = values or [0,0]
    self.bounds = bounds or [-1e10, 1e10]
    self.pointBox1 = DoubleSpinbox(self, value=self.values[0], step=step, max=self.bounds[1], min=self.bounds[0],
                                   grid=(0, 1), hAlign='l', vAlign='l' )
    self.pointBox2 = DoubleSpinbox(self, value=self.values[1], step=step, max=self.bounds[1], min=self.bounds[0],
                                   grid=(0, 2), hAlign='l', vAlign='l' )
    self.spinBoxes.append(self.pointBox1)
    self.spinBoxes.append(self.pointBox2)

    self.pickOnSpectrumButton.setMaximumHeight(self.pointBox1.size().height()*1.2)
    self.pickOnSpectrumButton.setMaximumWidth(50)

    self.linearRegions = LinearRegionsPlot(values=self.values, orientation=self.orientation, bounds=self.bounds,
                                           brush=self.brush, colour = self.colour, movable=self.movable)

    for line in self.linearRegions.lines:
      line.sigPositionChanged.connect(self._lineMoved)

    for sb in self.spinBoxes:
      sb.valueChanged.connect(self._setLinePosition)

    # if self.plotWidget is None:
    #   self.pickOnSpectrumButton.setEnabled(False)

  def setPlotWidget(self, plotWidget):
    self.plotWidget = plotWidget

  def _togglePicking(self):

    if self.application is not None:
      self.current = self.application.current
      self.strip = self.current.strip
      if self.strip is not None:
        self.plotWidget = self.strip.plotWidget

    if self.plotWidget is not None:
        if self.pickOnSpectrumButton.isChecked():
          self.pickOnSpectrumButton.setIcon(self.toggleOnIcon)
          self._turnOnPositionPicking()
        elif not self.pickOnSpectrumButton.isChecked():
          self.pickOnSpectrumButton.setIcon(self.toggleOffIcon)
          self._turnOffPositionPicking()

  def _turnOnPositionPicking(self):
    if self.plotWidget is not None:
      self.plotWidget.addItem(self.linearRegions)

  def _turnOffPositionPicking(self):
    if self.plotWidget is not None:
      self.plotWidget.removeItem(self.linearRegions)

  def _lineMoved(self):
      values = []
      for line in self.linearRegions.lines:
        if self.orientation == 'h':
          values.append(line.pos().y())
        elif self.orientation == 'v':
          values.append(line.pos().x())
      self.pointBox1.setValue(min(values))
      self.pointBox2.setValue(max(values))

  def _setLinePosition(self):
    values = []
    for sb in self.spinBoxes:
      values.append(sb.value())

    self.pointBox1.setValue(min(values))
    self.pointBox2.setValue(max(values))

    self.linearRegions.lines[0].setPos(min(values))
    self.linearRegions.lines[1].setPos(max(values))

  def get(self):
    '''
    :return: positions displayed on the boxes
    '''
    if len(self.spinBoxes)>0:
      return [sb.value() for sb in self.spinBoxes]
    else:
      return [0,0]

  def setValues(self, values):

    self.linearRegions.lines[0].setPos(min(values))
    self.linearRegions.lines[1].setPos(max(values))

  def destroy(self, bool_destroyWindow=True, bool_destroySubWindows=True):
    self._turnOffPositionPicking()
    self.destroy( bool_destroyWindow=bool_destroyWindow, bool_destroySubWindows=bool_destroySubWindows)


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  app = TestApplication()

  popup = CcpnDialog(windowTitle='Test ',)

  cw = Widget(parent=popup, setLayout=True, grid=(0, 0))
  pw3 = pg.PlotWidget()
  cw.getLayout().addWidget(pw3)


  curve = pw3.plot(np.random.normal(size=100) * 1e0, clickable=True)
  y1 = [1]*100
  # curve1 = pw3.plot(-np.random.normal(size=100) * 1e0, clickable=True)
  # curve1 = pw3.plot(y1, clickable=True)
  # d = curve.yData - y1
  curveD = pw3.plot(y1, clickable=True)
  brush = (100, 100, 255)


  fills = [FillBetweenRegions(curveD,curve, brush=brush) ]
  for f in fills:
    pw3.addItem(f)
  curve.curve.setClickable(True)
  curve.setPen('w')  ## white pen


  w = TargetButtonSpinBoxes(parent=popup, plotWidget=pw3, values= [1, 30], colour = 'yellow', step=0.02, orientation='h', grid=(1,0) )


  popup.show()
  popup.raise_()
  popup.resize(500,500)
  app.start()
