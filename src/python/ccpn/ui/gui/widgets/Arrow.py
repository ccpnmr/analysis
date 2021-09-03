"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-07-30 20:44:25 +0100 (Fri, July 30, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from pyqtgraph import ArrowItem
from PyQt5 import QtCore, QtWidgets
import pyqtgraph.functions as fn


class Arrow(ArrowItem):
    sigDragged = QtCore.pyqtSignal(object)
    sigPositionChangeFinished = QtCore.pyqtSignal(object)
    sigPositionChanged = QtCore.pyqtSignal(object)

    def __init__(self, pos=None, angle=90, pen=None, movable=False, bounds=None):
        # GraphicsObject.__init__(self)
        super().__init__(pos=pos, angle=angle)
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
