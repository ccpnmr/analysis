"""
various mouse event functions. See ViewBox.py for the full mouse commands description.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-02 17:47:53 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph.Point import Point
from ccpn.util import Common as commonUtil

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.widgets.Menu import Menu

from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Font import setWidgetFont


# mouse modes for single click:
PICK = 'pick'
SELECT = 'select'
MOUSEMODEDICT_CURRENT = 'Mode'
MouseModes = [PICK, SELECT]
mouseModeDict = {MOUSEMODEDICT_CURRENT: SELECT}


def setCurrentMouseMode(mode):
    mouseModeDict[MOUSEMODEDICT_CURRENT] = mode


def getCurrentMouseMode():
    return mouseModeDict[MOUSEMODEDICT_CURRENT]


def doDebug(msg):
    if False:  #cannot get the regular debugger to work and likely do not want this on during production anyway
        sys.stderr.write(msg + '\n')


def controlShiftLeftMouse(event: QtGui.QMouseEvent):
    # Return True for control(cmd)-shift-left-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.LeftButton) \
             and (control) \
             and (shift)

    if result:
        doDebug('DEBUG mouse: Control-shift-left-Mouse event at %s' % event.pos())
    return result


def controlLeftMouse(event: QtGui.QMouseEvent):
    # Return True for control(cmd)-left-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.LeftButton) \
             and (control) \
             and not (shift)
    if result:
        doDebug('Control-left-Mouse event at %s' % event.pos())
    return result


def shiftLeftMouse(event: QtGui.QMouseEvent):
    # Return True for shift-left-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)

    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)
    result = (event.button() == QtCore.Qt.LeftButton) \
             and not (control) \
             and (shift)
    if result:
        doDebug('Shift-left-Mouse event at %s' % event.pos())
    return result


def leftMouse(event: QtGui.QMouseEvent):
    # Return True for left-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.LeftButton) \
             and not (control) \
             and not (shift)
    if result:
        doDebug('Left-Mouse event at %s' % event.pos())
    return result


def controlShiftRightMouse(event: QtGui.QMouseEvent):
    # Return True for control(cmd)-shift-right-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.RightButton) \
             and (control) \
             and (shift)
    if result:
        doDebug('Control-shift-right-Mouse event at %s' % event.pos())
    return result


def controlRightMouse(event: QtGui.QMouseEvent):
    # Return True for control(cmd)-right-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.RightButton) \
             and (control) \
             and not (shift)
    if result:
        doDebug('Control-right-Mouse event at %s' % event.pos())
    return result


def shiftRightMouse(event: QtGui.QMouseEvent):
    # Return True for shift-right-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.RightButton) \
             and not (control) \
             and (shift)
    if result:
        doDebug('Shift-right-Mouse event at %s' % event.pos())
    return result


def rightMouse(event: QtGui.QMouseEvent):
    # Return True for right-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.RightButton) \
             and not (control) \
             and not (shift)

    if result:
        doDebug('Right-Mouse event at %s' % event.pos())
    return result


def controlShiftMiddleMouse(event: QtGui.QMouseEvent):
    # Return True for control(cmd)-shift-middle-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.MiddleButton) \
             and (control) \
             and (shift)
    if result:
        doDebug('Control-shift-middle-Mouse event at %s' % event.pos())
    return result


def controlMiddleMouse(event: QtGui.QMouseEvent):
    # Return True for control(cmd)-middle-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.MiddleButton) \
             and (control) \
             and not (shift)
    if result:
        doDebug('Control-middle-Mouse event at %s' % event.pos())
    return result


def shiftMiddleMouse(event: QtGui.QMouseEvent):
    # Return True for shift-middle-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.MiddleButton) \
             and not (control) \
             and (shift)
    if result:
        doDebug('Shift-middle-Mouse event at %s' % event.pos())
    return result


def middleMouse(event: QtGui.QMouseEvent):
    # Return True for middle-Mouse event
    control = bool(event.modifiers() & QtCore.Qt.ControlModifier)
    shift = bool(event.modifiers() & QtCore.Qt.ShiftModifier)

    result = (event.button() == QtCore.Qt.MiddleButton) \
             and not (control) \
             and not (shift)
    if result:
        doDebug('Middle-Mouse event at %s' % event.pos())
    return result


def getMouseEventDict(event: QtGui.QMouseEvent):
    """
    Return a dict with the status of each mouseEvent as boolean
    """
    mouseModeDict = {}

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
        mouseModeDict[key] = func(event)
    return mouseModeDict


import json
from ccpn.ui.gui.widgets.DropBase import DropBase
# from ccpn.ui.gui.guiSettings import textFontLarge
from ccpn.ui.gui.guiSettings import getColours, DRAG_BACKGROUND, DRAG_FOREGROUND


# small border to make the drag items look cleaner
DRAGBORDER = 2


def _setMimeQString(value):
    """Convert a string to a stream
    """
    result = QtCore.QByteArray()
    stream = QtCore.QDataStream(result, QtCore.QIODevice.WriteOnly)
    stream.writeQString(value)
    return result


def _setMimeQVariant(value):
    """Convert a python object into a stream
    """
    result = QtCore.QByteArray()
    stream = QtCore.QDataStream(result, QtCore.QIODevice.WriteOnly)
    stream.writeQVariant(value)
    return result


def _getMimeQVariant(value):
    """Convert a stream QVariant back into a python object
    """
    stream = QtCore.QDataStream(value, QtCore.QIODevice.ReadOnly)
    result = stream.readQVariant()
    return result


def makeDragEvent(self, dataDict, texts, label=None, action=QtCore.Qt.CopyAction, alignCentre=True):
    """Create a new drag event with 'self' as the source

    :param self: source of the new drag event
    :param dataDict: data to add as mimeData
    :param texts: list of strings to copy/move to list widget types (if required)
    :param label: string required to create the drag icon
    :param action: QtCore.Qt.CopyAction or Move action - may be used by dropEvent
    :return:
    """
    itemData = json.dumps(dataDict)

    mimeData = QtCore.QMimeData()
    mimeData.setData(DropBase.JSONDATA, _setMimeQString(itemData))
    mimeData.setData(DropBase.MODELDATALIST, _setMimeQVariant(texts))
    mimeData.setText(itemData)

    # create the new event with the mimeData - this does not contain internal application/x-qabstractitemmodeldatalist (INTERNALQTDATA)
    drag = QtGui.QDrag(self)
    drag.setMimeData(mimeData)

    # create a new temporary label the the dragged pixmap
    # fixes labels that are very big with small text
    dragLabel = QtWidgets.QLabel()
    dragLabel.setText(str(label))

    if label is not None:
        setWidgetFont(dragLabel, size='MEDIUM')

        # set the colours and margin for the drag icon
        dragLabel.setStyleSheet('color: {}; background: {}'.format(getColours()[DRAG_FOREGROUND], getColours()[DRAG_BACKGROUND]))
        dragLabel.setContentsMargins(DRAGBORDER, DRAGBORDER, DRAGBORDER - 1, DRAGBORDER - 1)

        # set the pixmap
        pixmap = dragLabel.grab()

        # make the label slightly transparent - not strictly necessary
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(painter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QtGui.QColor(0, 0, 0, 240))
        painter.end()

        # set pixmap if label is defined other defaults to mimeData.text
        drag.setPixmap(pixmap)

    if alignCentre:
        # set the hotspot as the centre
        drag.setHotSpot(QtCore.QPoint(dragLabel.width() // 2, dragLabel.height() // 2))

    # invoke the drag event
    drag.exec_(action)
