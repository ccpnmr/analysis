"""
various mouse event functions
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
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================
import sys
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from pyqtgraph.Point import Point
from ccpn.util import Common as commonUtil

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.widgets.Menu import Menu

from ccpn.util.Logging import getLogger
logger = getLogger()


def doDebug(msg):
  if False: #cannot get the regular debugger to work and likely do not want this on during production anyway
    sys.stderr.write(msg +'\n')


def controlShiftLeftMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-shift-left-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =     (event.button() == QtCore.Qt.LeftButton) \
           and (control) \
           and (shift)

  if result:
    doDebug('DEBUG mouse: Control-shift-left-Mouse event at %s' % event.pos())
  return result


def controlLeftMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-left-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.LeftButton) \
           and     (control) \
           and not (shift)
  if result:
    doDebug('Control-left-Mouse event at %s' % event.pos())
  return result


def shiftLeftMouse(event:QtGui.QMouseEvent):
  # Return True for shift-left-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)

  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)
  result =         (event.button() == QtCore.Qt.LeftButton) \
           and not (control) \
           and     (shift)
  if result:
    doDebug('Shift-left-Mouse event at %s' % event.pos())
  return result


def leftMouse(event:QtGui.QMouseEvent):
  # Return True for left-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.LeftButton) \
            and not (control) \
            and not (shift)
  if result:
    doDebug('Left-Mouse event at %s' % event.pos())
  return result


def controlShiftRightMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-shift-right-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =     (event.button() == QtCore.Qt.RightButton) \
           and (control) \
           and (shift)
  if result:
    doDebug('Control-shift-right-Mouse event at %s' % event.pos())
  return result


def controlRightMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-right-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.RightButton) \
           and     (control) \
           and not (shift)
  if result:
    doDebug('Control-right-Mouse event at %s' % event.pos())
  return result


def shiftRightMouse(event:QtGui.QMouseEvent):
  # Return True for shift-right-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.RightButton) \
           and not (control) \
           and     (shift)
  if result:
    doDebug('Shift-right-Mouse event at %s' % event.pos())
  return result


def rightMouse(event:QtGui.QMouseEvent):
  # Return True for right-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.RightButton) \
           and not (control) \
           and not (shift)

  if result:
    doDebug('Right-Mouse event at %s' % event.pos())
  return result


def controlShiftMiddleMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-shift-middle-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =      (event.button() == QtCore.Qt.MiddleButton) \
            and (control)\
            and (shift)
  if result:
    doDebug('Control-shift-middle-Mouse event at %s' % event.pos())
  return result


def controlMiddleMouse(event:QtGui.QMouseEvent):
  # Return True for control(cmd)-middle-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.MiddleButton) \
           and     (control)\
           and not (shift)
  if result:
    doDebug('Control-middle-Mouse event at %s' % event.pos())
  return result


def shiftMiddleMouse(event:QtGui.QMouseEvent):
  # Return True for shift-middle-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.MiddleButton) \
           and not (control)\
           and     (shift)
  if result:
    doDebug('Shift-middle-Mouse event at %s' % event.pos())
  return result


def middleMouse(event:QtGui.QMouseEvent):
  # Return True for middle-Mouse event
  control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
  shift   = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

  result =         (event.button() == QtCore.Qt.MiddleButton) \
           and not (control) \
           and not (shift)
  if result:
    doDebug('Middle-Mouse event at %s' % event.pos())
  return result


def getMouseEventDict(event:QtGui.QMouseEvent):
  """
  Return a dict with the status of each mouseEvent as boolean
  """
  mouseDict = {}

  for key, func in [
    ('leftMouse', leftMouse),
    ('shiftLeftMouse', shiftLeftMouse),
    ('controlLeftMouse', controlLeftMouse),
    ('controlShiftLeftMouse', controlShiftLeftMouse),

    ('middleMouse', middleMouse),
    ('shiftMiddleMouse', shiftMiddleMouse),
    ('controlMiddleMouse', controlMiddleMouse),
    ('controlShiftMiddleMouse', controlShiftMiddleMouse),

    ('rightMouse', rightMouse),
    ('shiftRightMouse', shiftRightMouse),
    ('controlRightMouse', controlRightMouse),
    ('controlShiftRightMouse', controlShiftRightMouse),
  ]:
    mouseDict[key] = func(event)
  return mouseDict

