"""Module Documentation here

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
__author__ = 'simon'


from pyqtgraph import ArrowItem
from PyQt4 import QtCore
import pyqtgraph.functions as fn

class Arrow(ArrowItem):

  sigDragged = QtCore.Signal(object)
  sigPositionChangeFinished = QtCore.Signal(object)
  sigPositionChanged = QtCore.Signal(object)

  def __init__(self, pos=None, angle=90, pen=None, movable=False, bounds=None):
    # GraphicsObject.__init__(self)
    ArrowItem.__init__(self, pos=pos, angle=angle)
    self.moving = False
    self.setMovable(movable)
    self.setZValue(1e-6)

    if pen is None:
      pen = (200, 200, 100)
      self.setPen(pen)
      self.currentPen = self.pen

  def setPen(self, pen):
        """Set the pen for drawing the line. Allowable arguments are any that are valid
        for :func:`mkPen <pyqtgraph.mkPen>`."""
        self.pen = fn.mkPen(pen)
        self.currentPen = self.pen
        self.update()

  def setMovable(self, m):
    """Set whether the line is movable by the user."""
    self.movable = m
    self.setAcceptHoverEvents(m)


  def mouseDragEvent(self, ev):
    if self.movable and ev.button() == QtCore.Qt.LeftButton:
      if ev.isStart():
        self.moving = True
        self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
        self.startPosition = self.pos()
      ev.accept()

      if not self.moving:
        return

      #pressDelta = self.mapToParent(ev.buttonDownPos()) - Point(self.p)
      self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))
      self.sigDragged.emit(self)
      if ev.isFinish():
        self.moving = False
        self.sigPositionChangeFinished.emit(self)
    #else:
        #print ev


  def mouseClickEvent(self, ev):
    if self.moving and ev.button() == QtCore.Qt.LeftButton:
      ev.accept()
      print('arrowclicked')
      self.setPos(self.startPosition)
      self.moving = False
      self.sigDragged.emit(self)
      self.sigPositionChangeFinished.emit(self)



