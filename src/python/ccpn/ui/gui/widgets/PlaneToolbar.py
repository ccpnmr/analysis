"""
This module defines a specific Toolbar class for the strip display 
The NmrResidueLabel allows drag and drop of the ids displayed in them

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.guiSettings import textFont, getColours, STRIPHEADER_BACKGROUND, \
    STRIPHEADER_FOREGROUND, GUINMRRESIDUE

import json
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict

from PyQt5 import QtGui, QtWidgets, QtCore


STRIPLABEL_CONNECTDIR = '_connectDir'
STRIPLABEL_CONNECTNONE = 'none'


class _StripLabel(Label):
    """
    Specific Label to be used in Strip displays
    """

    def __init__(self, parent, text, dragKey=DropBase.TEXT, **kwds):

        super().__init__(parent, text, **kwds)
        # The text of the label can be dragged; it will be passed on in the dict under key dragKey

        self._parent = parent
        self._dragKey = dragKey
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)           # not possible for Label

        self._source = None
        self.eventFilter = self._eventFilter
        self.installEventFilter(self)

        # disable any drop event callback's until explicitly defined later
        self.setDropEventCallback(None)

    def _mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        Re-implementation of the mouse press event to enable a NmrResidue label to be dragged as a json object
        containing its id and a modifier key to encode the direction to drop the strip.
        """
        event.accept()
        mimeData = QtCore.QMimeData()
        # create the dataDict
        dataDict = {self._dragKey: self.text()}
        connectDir = self._connectDir if hasattr(self, STRIPLABEL_CONNECTDIR) else STRIPLABEL_CONNECTNONE
        dataDict[STRIPLABEL_CONNECTDIR] = connectDir

        # update the dataDict with all mouseEvents﻿{"controlRightMouse": false, "text": "NR:@-.@27.", "leftMouse": true, "controlShiftMiddleMouse": false, "middleMouse": false, "controlMiddleMouse": false, "controlShiftLeftMouse": false, "controlShiftRightMouse": false, "shiftMiddleMouse": false, "_connectDir": "isRight", "controlLeftMouse": false, "rightMouse": false, "shiftLeftMouse": false, "shiftRightMouse": false}
        dataDict.update(getMouseEventDict(event))
        # convert into json
        itemData = json.dumps(dataDict)

        # ejb - added so that itemData works with PyQt5
        tempData = QtCore.QByteArray()
        stream = QtCore.QDataStream(tempData, QtCore.QIODevice.WriteOnly)
        stream.writeQString(self.text())
        mimeData.setData(DropBase.JSONDATA, tempData)

        # mimeData.setData(DropBase.JSONDATA, self.text())
        mimeData.setText(itemData)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        # create a new temporary label the the dragged pixmap
        # fixes labels that are very big with small text
        dragLabel = QtWidgets.QLabel()
        dragLabel.setText(self.text())
        dragLabel.setFont(textFont)
        dragLabel.setStyleSheet('color : %s' % (getColours()[GUINMRRESIDUE]))

        # set the pixmap
        pixmap = dragLabel.grab()

        # make the label slightly transparent
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(painter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QtGui.QColor(0, 0, 0, 240))
        painter.end()
        drag.setPixmap(pixmap)

        # drag.setHotSpot(event.pos())
        drag.setHotSpot(QtCore.QPoint(dragLabel.width() / 2, dragLabel.height() / 2))

        # drag.targetChanged.connect(self._targetChanged)
        drag.exec_(QtCore.Qt.CopyAction)

    def _targetChanged(self, widget):
        pass

    def _eventFilter(self, obj, event):
        """
        Replace all the events with a single filter process
        Not sure if this is the best solution, but doesn't interfere with _processDroppedItems
        and allows changing of the cursor (cursor not changing properly in pyqt5) - ejb
        """
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self._mousePressEvent(event)  # call the standard mouse event
            return True

        # if event.type() == QtCore.QEvent.DragEnter:
        #     self._source = event.source()
        #     if isinstance(obj, _StripLabel) and self._source != self:
        #         mime = event.mimeData().text()
        #         dataItem = json.loads(mime)
        #         if 'text' in dataItem and dataItem['text'].startswith('NR'):
        #             # only test NmrResidues
        #             #   print('>>>DragEnterFilter %s' % dataItem['text'])
        #             #   QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.DragCopyCursor)
        #             #   event.setDropAction(QtCore.Qt.CopyAction)
        #             QtWidgets.QApplication.processEvents()
        #             event.accept()
        #             return True
        #
        #     event.ignore()
        #     return False

        # if event.type() == QtCore.QEvent.DragLeave:
        #     # QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.ClosedHandCursor)
        #     # QtWidgets.QApplication.restoreOverrideCursor()
        #     # QtWidgets.QApplication.processEvents()
        #     # print('>>>DragLeaveFilter')
        #     # event.setDropAction(QtCore.Qt.MoveAction)
        #     event.ignore()
        #     return True
        #
        # if event.type() == QtCore.QEvent.Leave:
        #     # QtWidgets.QApplication.restoreOverrideCursor()
        #     # QtWidgets.QApplication.processEvents()
        #     # print('>>>DragLeaveFilter')
        #     # event.setDropAction(QtCore.Qt.MoveAction)
        #     event.accept()
        #     return True
        #
        # if event.type() == QtCore.QEvent.MouseMove:
        #     if not isinstance(obj, _StripLabel):
        #         # QtWidgets.QApplication.restoreOverrideCursor()
        #         # QtWidgets.QApplication.processEvents()
        #         # print(">>>MoveFilter")
        #         event.accept()
        #         return True

        if event.type() == QtCore.QEvent.Drop:
            # QtWidgets.QApplication.restoreOverrideCursor()
            # QtWidgets.QApplication.processEvents()
            # print(">>>DropFilter")
            # event.setDropAction(QtCore.Qt.MoveAction)
            event.ignore()
            # no return True needed, so BackboneAssignment._processDroppedItem still fires

        return super(_StripLabel, self).eventFilter(obj, event)  # do the rest


#TODO:GEERTEN: complete this and replace
class PlaneSelectorWidget(Widget):
    """
    This widget contains the buttons and entry boxes for selection of the plane
    """

    def __init__(self, qtParent, strip, axis, **kwds):
        "Setup the buttons and callbacks for axis"

        Widget.__init__(self, parent=qtParent, **kwds)

        self.strip = strip
        self.axis = axis

        width = 20;
        height = 20

        self.previousPlaneButton = Button(parent=self, text='<', grid=(0, 0),
                                          callback=self._previousPlane)
        self.previousPlaneButton.setFixedWidth(width)
        self.previousPlaneButton.setFixedHeight(height)

        self.spinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0, 1),
                                     callback=self._spinBoxChanged)
        self.spinBox.setFixedHeight(height)

        self.nextPlaneButton = Button(parent=self, text='<', grid=(0, 2),
                                      callback=self._nextPlane)
        self.nextPlaneButton.setFixedWidth(width)
        self.nextPlaneButton.setFixedHeight(height)

        self.planeCountSpinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0, 3),
                                               callback=self._planeCountChanged
                                               )
        self.planeCountSpinBox.setFixedHeight(height)

    def _previousPlane(self):
        print('clicked previous')

    def _nextPlane(self):
        print('clicked previous')

    def _spinBoxChanged(self, value):
        print('spinBox chnaged to:', value)

    def _planeCountChanged(self, value):
        print('planeCount changed to:', value)


class PlaneToolbar(ToolBar):
    #TODO: undocumented and needs refactoring ;
    # GWV: Does not work as a Widget!?
    def __init__(self, qtParent, strip, callbacks, **kwds):

        ToolBar.__init__(self, parent=qtParent, **kwds)

        self.strip = strip
        self.planeLabels = []
        self.planeCounts = []
        for i in range(len(strip.orderedAxes) - 2):
            self.prevPlaneButton = Button(self, '<', callback=partial(callbacks[0], i))
            self.prevPlaneButton.setFixedWidth(19)
            self.prevPlaneButton.setFixedHeight(19)
            planeLabel = DoubleSpinbox(self, showButtons=False)
            # planeLabel.setFixedHeight(19)

            # force the minimum width of the planeLabel
            planeLabel.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                     QtWidgets.QSizePolicy.MinimumExpanding)
            planeLabel.setMinimumWidth(55)

            # below does not work because it allows wheel events to behave but not manual text entry (some Qt stupidity)
            # so instead use a wheelEvent to deal with the wheel events and editingFinished (in GuiStripNd) to do text
            #planeLabel.valueChanged.connect(partial(callbacks[2], i))
            if callbacks[2]:
                planeLabel.wheelEvent = partial(self._wheelEvent, i)
                self.prevPlaneCallback = callbacks[0]
                self.nextPlaneCallback = callbacks[1]
            self.nextPlaneButton = Button(self, '>', callback=partial(callbacks[1], i))
            self.nextPlaneButton.setFixedWidth(19)
            self.nextPlaneButton.setFixedHeight(19)
            planeCount = Spinbox(self, showButtons=False, hAlign='c')
            planeCount.setMinimum(1)
            planeCount.setValue(1)
            planeCount.oldValue = 1
            planeCount.valueChanged.connect(partial(callbacks[3], i))
            self.addWidget(self.prevPlaneButton)
            self.addWidget(planeLabel)
            self.addWidget(self.nextPlaneButton)
            self.addWidget(planeCount)
            self.planeLabels.append(planeLabel)
            self.planeCounts.append(planeCount)

    def _wheelEvent(self, n, event):
        if event.angleDelta().y() > 0:  # note that in Qt5 this becomes angleDelta().y()
            if self.prevPlaneCallback:
                self.prevPlaneCallback(n)
        else:
            if self.nextPlaneCallback:
                self.nextPlaneCallback(n)

        self.strip._rebuildStripContours()


STRIPCONNECT_LEFT = 'isLeft'
STRIPCONNECT_RIGHT = 'isRight'
STRIPCONNECT_NONE = 'none'
STRIPCONNECT_DIRS = (STRIPCONNECT_NONE, STRIPCONNECT_LEFT, STRIPCONNECT_RIGHT)
STRIPPOSITION_LEFT = 'l'
STRIPPOSITION_CENTRE = 'c'
STRIPPOSITION_RIGHT = 'r'
STRIPPOSITIONS = (STRIPPOSITION_LEFT, STRIPPOSITION_CENTRE, STRIPPOSITION_RIGHT)


class StripHeader(Widget):
    def __init__(self, parent, mainWindow, **kwds):
        super().__init__(parent=parent, **kwds)

        self._parent = parent
        self.mainWindow = mainWindow

        self._labels = {}

        for lab in STRIPPOSITIONS:
            self._labels[lab] = _StripLabel(parent=self,
                                            text='', spacing=(0, 0),
                                            grid=(0, STRIPPOSITIONS.index(lab)))

            # ED: the only way I could find to cure the mis-aligned header
            self._labels[lab].setStyleSheet('QLabel {'
                                            'padding: 0; '
                                            'margin: 0px 0px 0px 0px;'
                                            'color:  %s;'
                                            'background-color: %s;'
                                            'border: 0 px;'
                                            'font-family: %s;'
                                            'font-size: %dpx;'
                                            'qproperty-alignment: AlignCenter;'
                                            '}' % (getColours()[STRIPHEADER_FOREGROUND],
                                                   getColours()[STRIPHEADER_BACKGROUND],
                                                   textFont.fontName,
                                                   textFont.pointSize()))

            self._labels[lab].obj = None
            self._labels[lab]._connectDir = STRIPCONNECT_NONE
            self._labels[lab].setFixedHeight(16)
            self._labels[lab].setAlignment(QtCore.Qt.AlignAbsolute)

        self._labels[STRIPPOSITION_LEFT].setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self._labels[STRIPPOSITION_CENTRE].setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self._labels[STRIPPOSITION_RIGHT].setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.setFixedHeight(16)

    def reset(self):
        for lab in STRIPPOSITIONS:
            self._labels[lab].setText('')
            self._labels[lab].obj = None
            self._labels[lab]._connectDir = STRIPCONNECT_NONE

    def setLabelObject(self, obj=None, position=STRIPPOSITION_CENTRE):
        if position in STRIPPOSITIONS:
            self._labels[position].obj = obj

    def getLabelObject(self, position=STRIPPOSITION_CENTRE):
        if position in STRIPPOSITIONS:
            return self._labels[position].obj

    def setLabelText(self, text=None, position=STRIPPOSITION_CENTRE):
        if position in STRIPPOSITIONS:
            self._labels[position].setText(text)

    def getLabelText(self, position=STRIPPOSITION_CENTRE):
        if position in STRIPPOSITIONS:
            return self._labels[position].text()

    def getLabel(self, position=STRIPPOSITION_CENTRE):
        """Return the header label widget"""
        if position in STRIPPOSITIONS:
            return self._labels[position]

    def showLabel(self, position=STRIPPOSITION_CENTRE, doShow: bool = True):
        """show / hide the header label"""
        position = position[0]
        if position in STRIPPOSITIONS:
            self._labels[position].setVisible(doShow)

    def hideLabel(self, position=STRIPPOSITION_CENTRE):
        "Hide the header label; convienience"
        if position in STRIPPOSITIONS:
            self._labels[position].setVisible(False)

    def setLabelEnabled(self, position=STRIPPOSITION_CENTRE, enable: bool = True):
        """show / hide the header label"""
        if position in STRIPPOSITIONS:
            self._labels[position].setEnabled(enable)

    def setLabelConnectDir(self, position=STRIPPOSITION_CENTRE, connectDir: str = STRIPCONNECT_NONE):
        """set the connectDir attribute of the header label"""
        if position in STRIPPOSITIONS:
            self._labels[position]._connectDir = connectDir

    def getLabelConnectDir(self, position=STRIPPOSITION_CENTRE):
        """set the connectDir attribute of the header label"""
        if position in STRIPPOSITIONS:
            return self._labels[position]._connectDir
