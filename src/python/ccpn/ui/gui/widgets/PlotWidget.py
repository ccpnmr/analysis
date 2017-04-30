"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

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
from PyQt4 import QtGui, QtOpenGL

from ccpn.ui.gui.widgets.SpectrumGroupsToolBarWidget import SpectrumGroupsWidget
from ccpn.ui.gui.widgets.ViewBox import ViewBox
from ccpn.ui.gui.widgets.ViewBox import CrossHair
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.CcpnGridItem import CcpnGridItem


#TODO:WAYNE: This class should contain all the nitty gritty of the displaying; including the axis labels and the like
# as it is only there and is just a small wrapper arount a pyqtgraph class
# goes together with AxisTextItem (probably can be reduced to a function and included here.
#TODO:WAYNE: should this inherit from Base??
class PlotWidget(pg.PlotWidget, Base):

  def __init__(self, parent, application, useOpenGL=False, strip=None,
                     showDoubleCrosshair=False, **kw):

    # Be sure to use explicit arguments to ViewBox as the call order is different in the __init__
    self.viewBox = ViewBox(parent=parent, current=application.current, strip=strip)
    pg.PlotWidget.__init__(self, parent=parent,
                                 viewBox=self.viewBox,
                                 axes=None, enableMenu=True)
    Base.__init__(self, **kw)

    self.application = application
    self.strip = strip
    self.parent = parent

    self.plotItem.setAcceptHoverEvents(True)
    self.setInteractive(True)
    self.plotItem.setAcceptDrops(True)
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)

    self.hideButtons()

    if useOpenGL:
      self.setViewport(QtOpenGL.QGLWidget())
      self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)

    #TODO:GEERTEN: Fix with proper stylesheet
    # Also used in AxisTextItem
    if self.application.colourScheme == 'light':
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
    self.addItem(self.grid)

    # Add two crosshairs
    self.crossHair1 = CrossHair(parent=self, show=True, colour=self.foreground)
    self.crossHair2 = CrossHair(parent=self, show=showDoubleCrosshair, colour=self.foreground)

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
