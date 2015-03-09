"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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

class ViewBox(pg.ViewBox):

  def __init__(self, current  = None,  *args, **kwds):
    pg.ViewBox.__init__(self, *args, **kwds)
    self.current = current
    self.menu = None # Override pyqtgraph ViewBoxMenu
    self.menu = self.getMenu()


  def raiseContextMenu(self, event):
    """
    Raise the context menu
    """
    position  = event.screenPos()
    self.menu.popup(QtCore.QPoint(position.x(), position.y()))

  def getMenu(self):
    if self.menu is None:
      self.menu = Menu(self.parent(), isFloatWidget=True)
      return self.menu


  def mouseClickEvent(self, event, axis=None):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      event.accept()
      print('Left Click Event')
      # self.current.pane = self.parent

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and not (
    event.modifiers() & QtCore.Qt.ShiftModifier):
      position = event.scenePos()
      mousePoint = self.mapSceneToView(position)
      print(mousePoint)

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
    event.modifiers() & QtCore.Qt.ControlModifier):
      print('Add Select')

    elif event.button() == QtCore.Qt.MiddleButton and not event.modifiers():
      event.accept()
      print('Pick and Assign')

    elif event.button() == QtCore.Qt.RightButton and not event.modifiers() and axis is None:
      event.accept()
      self.raiseContextMenu(event)

    elif event.button() == QtCore.Qt.RightButton and not event.modifiers():
      event.accept()
      print('axis Context Menu')

    elif event.button() == QtCore.Qt.RightButton and (event.modifiers() & QtCore.Qt.ShiftModifier):
      event.accept()
      self.autoRange()

    if event.double():
      event.accept()
      print("Double Click event")

  def mouseDragEvent(self, event, axis=None):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      pg.ViewBox.mouseDragEvent(self, event)


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
        # Pick in area
      print('LeftDrag + Control + Shift')

      if event.isFinish():

        startPosition = event.buttonDownPos()
        endPosition = event.pos()
        print(startPosition,endPosition)

      event.accept()



    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier):
       # Add select area
      print('LeftDrag + Shift')
      if event.isStart():
        startPosition = event.buttonDownPos()
        print("start ",startPosition)
      elif event.isFinish():
        endPosition = event.pos()
        print("end ",endPosition)

      event.accept()
    ## above events remove pan abilities from plot window,
    ## need to re-implement them without changing mouseMode
    else:
      event.ignore()
