import pyqtgraph as pg
from PySide import QtCore
from pyqtgraph.Point import Point

class ViewBox(pg.ViewBox):

  def __init__(self, current  = None,  *args, **kwds):
    pg.ViewBox.__init__(self, *args, **kwds)
    self.setMenuDisabled()
    self.current = current


  def setMenuDisabled(self, enableMenu=False):
    self.state['enableMenu'] = enableMenu
    self.sigStateChanged.emit(self)

  def menuDisabled(self):
    return self.state.get('enableMenu', False)

  def mouseClickEvent(self, event):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      event.accept()
      self.current.pane = self.parent

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

    elif event.button() == QtCore.Qt.RightButton and not event.modifiers():
      event.accept()
      print('Context Menu to be activated here')

    elif event.button() == QtCore.Qt.RightButton and (event.modifiers() & QtCore.Qt.ShiftModifier):
      event.accept()
      self.autoRange()

      print('Context Menu to be activated here')

    if event.double():
      event.accept()
      print("Double Click event")


  def mouseDragEvent(self, event, axis=None):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      pg.ViewBox.mouseDragEvent(self, event)


    elif (event.button() == QtCore.Qt.RightButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier) or event.button() == QtCore.Qt.MidButton:
      print("Zoom into area")
      if event.isFinish():  ## This is the final move in the drag; change the view scale now
        print("finish")
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
