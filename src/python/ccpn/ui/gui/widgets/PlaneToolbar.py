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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
import json
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.guiSettings import textFont, getColours, STRIPHEADER_BACKGROUND, \
    STRIPHEADER_FOREGROUND, GUINMRRESIDUE
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.core.Peak import Peak
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.Menu import Menu


STRIPLABEL_CONNECTDIR = '_connectDir'
STRIPLABEL_CONNECTNONE = 'none'
SINGLECLICK = 'click'
DOUBLECLICK = 'doubleClick'


class _StripLabel(Label):
    """
    Specific Label to be used in Strip displays
    """

    # ED: This class contains the best current method for handling single and double click events
    # without any clashes between events, and creating a dragged item
    DOUBLECLICKENABLED = False

    def __init__(self, parent, mainWindow, strip, text, dragKey=DropBase.PIDS, **kwds):

        super().__init__(parent, text, **kwds)
        # The text of the label can be dragged; it will be passed on in the dict under key dragKey

        self._parent = parent
        self.strip = strip
        self.spectrumDisplay = self.strip.spectrumDisplay
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.project

        self._dragKey = dragKey
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)           # not possible for Label

        self._lastClick = None
        self._mousePressed = False

        # disable any drop event callback's until explicitly defined later
        self.setDropEventCallback(None)

    def _createDragEvent(self, mouseDict):  # event: QtGui.QMouseEvent):
        """
        Re-implementation of the mouse press event to enable a NmrResidue label to be dragged as a json object
        containing its id and a modifier key to encode the direction to drop the strip.
        """
        if not self.project.getByPid(self.text()):
            # label does not point to an object
            return

        mimeData = QtCore.QMimeData()
        # create the dataDict
        dataDict = {self._dragKey: [self.text()],
                    DropBase.TEXT: self.text()
                    }
        connectDir = self._connectDir if hasattr(self, STRIPLABEL_CONNECTDIR) else STRIPLABEL_CONNECTNONE
        dataDict[STRIPLABEL_CONNECTDIR] = connectDir

        # update the dataDict with all mouseEvents﻿{"controlRightMouse": false, "text": "NR:@-.@27.", "leftMouse": true, "controlShiftMiddleMouse": false, "middleMouse": false, "controlMiddleMouse": false, "controlShiftLeftMouse": false, "controlShiftRightMouse": false, "shiftMiddleMouse": false, "_connectDir": "isRight", "controlLeftMouse": false, "rightMouse": false, "shiftLeftMouse": false, "shiftRightMouse": false}
        dataDict.update(mouseDict)
        # convert to json
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
        drag.setHotSpot(QtCore.QPoint(dragLabel.width() // 2, dragLabel.height() // 2))

        # drag.targetChanged.connect(self._targetChanged)
        drag.exec_(QtCore.Qt.CopyAction)

    def event(self, event):
        """
        Process all events in the event handler
        Not sure if this is the best solution, but doesn't interfere with _processDroppedItems
        and allows changing of the cursor (cursor not always changing properly in pyqt5) - ejb
        """
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # process the single click event
            self._mousePressEvent(event)
            return True

        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            # process the doubleClick event
            self._mouseButtonDblClick(event)
            return True

        if event.type() == QtCore.QEvent.MouseButtonRelease:
            # process the mouse release event
            self._mouseReleaseEvent(event)
            return True

        return super().event(event)

    def _mousePressEvent(self, event):
        """Handle mouse press event for single click and beginning of mouse drag event
        """
        self._mousePressed = True
        if not self._lastClick:
            self._lastClick = SINGLECLICK

        if self._lastClick == SINGLECLICK:
            mouseDict = getMouseEventDict(event)

            # set up a singleshot event, but a bit quicker than the normal interval (which seems a little long)
            QtCore.QTimer.singleShot(QtWidgets.QApplication.instance().doubleClickInterval() // 2,
                                     partial(self._handleMouseClicked, mouseDict))

        elif self._lastClick == DOUBLECLICK:
            self._lastClick = None

    def _mouseButtonDblClick(self, event):
        """Handle mouse doubleCLick
        """
        self._lastClick = DOUBLECLICK
        if self.DOUBLECLICKENABLED:
            self._processDoubleClick(self.text())

    def _mouseReleaseEvent(self, event):
        """Handle mouse release
        """
        self._mousePressed = False
        if event.button() == QtCore.Qt.RightButton:
            self._rightButtonPressed(event)

    def _handleMouseClicked(self, mouseDict):
        """handle a single mouse event, but ignore double click events
        """
        if self._lastClick == SINGLECLICK and self._mousePressed:
            self._createDragEvent(mouseDict)
        self._lastClick = None

    def _processDoubleClick(self, obj):
        """Process the doubleClick event, action the clicked stripHeader in the selected strip
        """
        from ccpn.ui.gui.lib.SpectrumDisplay import navigateToPeakInStrip, navigateToNmrResidueInStrip

        obj = self.project.getByPid(obj) if isinstance(obj, str) else obj
        if obj:
            spectrumDisplays = self.spectrumDisplay._spectrumDisplaySettings.displaysWidget._getDisplays()
            for specDisplay in spectrumDisplays:

                if specDisplay.strips:
                    if isinstance(obj, Peak):
                        navigateToPeakInStrip(specDisplay, specDisplay.strips[0], obj)

                    elif isinstance(obj, NmrResidue):
                        navigateToNmrResidueInStrip(specDisplay, specDisplay.strips[0], obj)

    def _rightButtonPressed(self, event):
        """Handle pressing the right mouse button
        """
        menu = self._createContextMenu(self)
        if menu:
            menu.move(event.globalPos().x(), event.globalPos().y() + 10)
            menu.exec()

    def _createContextMenu(self, button: QtWidgets.QToolButton):
        """Creates a context menu to close headers.
        """
        contextMenu = Menu('', self, isFloatWidget=True)

        contextMenu.addSeparator()
        contextMenu.addAction('Close Strip Header', self._closeStrip)
        contextMenu.addAction('Close All Strip Headers in SpectrumDisplay', self._closeSpectrumDisplay)
        contextMenu.addAction('Close All', self._closeAll)
        return contextMenu

    def _closeStrip(self):
        """Close header in this strip
        """
        self.strip.header.reset()

    def _closeSpectrumDisplay(self):
        """Close all headers in this spectrumDisplay
        """
        for strip in self.spectrumDisplay.strips:
            strip.header.reset()

    def _closeAll(self):
        """Close all headers in all spectrumDisplays
        """
        displays = self.mainWindow.spectrumDisplays
        for display in displays:
            for strip in display.strips:
                strip.header.reset()


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

        width = 20
        height = 20

        self.previousPlaneButton = Button(parent=self, text='<', grid=(0, 0),
                                          callback=self._previousPlane)
        self.previousPlaneButton.setFixedWidth(width)
        self.previousPlaneButton.setFixedHeight(height)

        self.spinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0, 1),
                                     callback=self._spinBoxChanged, objectName='PlaneSelectorWidget_planeDepth')
        self.spinBox.setFixedHeight(height)

        self.nextPlaneButton = Button(parent=self, text='<', grid=(0, 2),
                                      callback=self._nextPlane)
        self.nextPlaneButton.setFixedWidth(width)
        self.nextPlaneButton.setFixedHeight(height)

        self.planeCountSpinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0, 3),
                                               callback=self._planeCountChanged, objectName='PlaneSelectorWidget_planeCount'
                                               )
        self.planeCountSpinBox.setFixedHeight(height)


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
            planeLabel = DoubleSpinbox(self, showButtons=False, objectName="PlaneToolbar_planeLabel" + str(i),
                                       )
            planeLabel.setToolTip(str(strip.axisCodes[i+2]))

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
            planeCount.setMaximum(1000)
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
STRIPCONNECT_NONE = 'noneConnect'
STRIPCONNECT_DIRS = (STRIPCONNECT_NONE, STRIPCONNECT_LEFT, STRIPCONNECT_RIGHT)

STRIPPOSITION_LEFT = 'l'
STRIPPOSITION_CENTRE = 'c'
STRIPPOSITION_RIGHT = 'r'
STRIPPOSITIONS = (STRIPPOSITION_LEFT, STRIPPOSITION_CENTRE, STRIPPOSITION_RIGHT)

STRIPDICT = 'stripHeaderDict'
STRIPTEXT = 'stripText'
STRIPOBJECT = 'stripObject'
STRIPCONNECT = 'stripConnect'
STRIPVISIBLE = 'stripVisible'
STRIPENABLED = 'stripEnabled'
STRIPTRUE = 1
STRIPFALSE = 0
STRIPSTOREINDEX = [STRIPTEXT, STRIPOBJECT, STRIPCONNECT, STRIPVISIBLE, STRIPENABLED]
STRIPHEADERVISIBLE = 'stripHeaderVisible'
STRIPHANDLE = 'stripHandle'


class StripHeader(Widget):
    def __init__(self, parent, mainWindow, strip, **kwds):
        super().__init__(parent=parent, **kwds)

        self._parent = parent
        self.mainWindow = mainWindow
        self.strip = strip

        self._labels = {}

        labelsVisible = False
        for stripPos in STRIPPOSITIONS:
            # read the current strip header values
            headerText = self._getPositionParameter(stripPos, STRIPTEXT, '')
            # not sure this is required
            headerObject = self.strip.project.getByPid(self._getPositionParameter(stripPos, STRIPOBJECT, None))
            headerConnect = self._getPositionParameter(stripPos, STRIPCONNECT, STRIPCONNECT_NONE)
            headerVisible = self._getPositionParameter(stripPos, STRIPVISIBLE, False)
            headerEnabled = self._getPositionParameter(stripPos, STRIPENABLED, True)

            self._labels[stripPos] = _StripLabel(parent=self, mainWindow=mainWindow, strip=strip,
                                                 text=headerText, spacing=(0, 0),
                                                 grid=(0, STRIPPOSITIONS.index(stripPos)))

            # ED: the only way I could find to cure the mis-aligned header
            self._labels[stripPos].setStyleSheet('QLabel {'
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

            self._labels[stripPos].obj = headerObject
            self._labels[stripPos]._connectDir = headerConnect
            self._labels[stripPos].setFixedHeight(16)
            self._labels[stripPos].setAlignment(QtCore.Qt.AlignAbsolute)

            self._labels[stripPos].setVisible(headerVisible)
            labelsVisible = labelsVisible or headerVisible
            self._labels[stripPos].setEnabled(headerEnabled)

        # get the visible state of the header
        headerVisible = self.strip.getParameter(STRIPDICT, STRIPHEADERVISIBLE)
        self.setVisible(headerVisible if headerVisible is not None else labelsVisible)

        # guiNotifiers are attached to the backboneAssignment module, not active on loading of project
        # currently needs a doubleClick in the backboneAssignment table to start

        self._labels[STRIPPOSITION_LEFT].setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self._labels[STRIPPOSITION_CENTRE].setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self._labels[STRIPPOSITION_RIGHT].setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.setFixedHeight(16)
        # self.eventFilter = self._eventFilter
        # self.installEventFilter(self)

        # self.reset()          # reset if backboneAssignment controls all headers

    def _setPositionParameter(self, stripPos, subParameterName, value):
        """Set the item in the position dict
        """
        params = self.strip.getParameter(STRIPDICT, stripPos)
        if not params:
            params = {}

        # fix for bad characters in the XML
        if isinstance(value, str):
            if '<<<' in value:
                value = 'MINUS'
            elif '>>>' in value:
                value = 'PLUS'

        # currently writes directly into _ccpnInternal
        params.update({subParameterName: value})
        self.strip.setParameter(STRIPDICT, stripPos, params)

    def _getPositionParameter(self, stripPos, subParameterName, default):
        """Return the item from the position dict
        """
        params = self.strip.getParameter(STRIPDICT, stripPos)
        if params:
            if subParameterName in params:
                value = params.get(subParameterName)

                # fix for bad characters in the XML
                # Could ignore here, so that needs doubleClick in backboneAssignment to restart
                if isinstance(value, str):
                    if 'MINUS' in value:
                        value = '<<<'
                    elif 'PLUS' in value:
                        value = '>>>'

                return value

        return default

    def reset(self):
        """Clear all header labels
        """
        self.hide()
        for stripPos in STRIPPOSITIONS:
            self._labels[stripPos].setText('')
            self._labels[stripPos].obj = None
            self._labels[stripPos]._connectDir = STRIPCONNECT_NONE
            self._labels[stripPos].setVisible(True)
            self._labels[stripPos].setEnabled(True)

            # clear the header store
            params = {STRIPTEXT   : '',
                      STRIPOBJECT : None,
                      STRIPCONNECT: STRIPCONNECT_NONE,
                      STRIPVISIBLE: True,
                      STRIPENABLED: True
                      }
            self.strip.setParameter(STRIPDICT, stripPos, params)
        self.strip.setParameter(STRIPDICT, STRIPHANDLE, None)
        self.strip.setParameter(STRIPDICT, STRIPHEADERVISIBLE, False)

    def setLabelObject(self, obj=None, position=STRIPPOSITION_CENTRE):
        """Set the object attached to the header label at the given position and store its pid
        """
        self.show()
        if position in STRIPPOSITIONS:
            self._labels[position].obj = obj

            # SHOULD have a pid if an object
            if obj and hasattr(obj, 'pid'):
                self._setPositionParameter(position, STRIPOBJECT, str(obj.pid))
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def getLabelObject(self, position=STRIPPOSITION_CENTRE):
        """Return the object attached to the header label at the given position
        """
        if position in STRIPPOSITIONS:
            return self._labels[position].obj
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def setLabelText(self, text=None, position=STRIPPOSITION_CENTRE):
        """Set the text for header label at the given position
        """
        self.show()
        if position in STRIPPOSITIONS:
            self._labels[position].setText(str(text))
            self._setPositionParameter(position, STRIPTEXT, str(text))
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def getLabelText(self, position=STRIPPOSITION_CENTRE):
        """Return the text for header label at the given position
        """
        if position in STRIPPOSITIONS:
            return self._labels[position].text()
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def getLabel(self, position=STRIPPOSITION_CENTRE):
        """Return the header label widget at the given position
        """
        if position in STRIPPOSITIONS:
            return self._labels[position]
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def setLabelVisible(self, position=STRIPPOSITION_CENTRE, visible: bool = True):
        """show/hide the header label at the given position
        """
        if position in STRIPPOSITIONS:
            if visible:
                self.show()
            else:
                self.hide()
            self._labels[position].setVisible(visible)
            self._setPositionParameter(position, STRIPVISIBLE, visible)
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def getLabelVisible(self, position=STRIPPOSITION_CENTRE):
        """Return if the widget at the given position is visible
        """
        if position in STRIPPOSITIONS:
            return self._labels[position].isVisible()
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def setLabelEnabled(self, position=STRIPPOSITION_CENTRE, enable: bool = True):
        """Enable/disable the header label at the given position
        """
        if position in STRIPPOSITIONS:
            self._labels[position].setEnabled(enable)
            self._setPositionParameter(position, STRIPENABLED, enable)
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def getLabelEnabled(self, position=STRIPPOSITION_CENTRE):
        """Return if the widget at the given position is enabled
        """
        if position in STRIPPOSITIONS:
            return self._labels[position].isEnabled()
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def setLabelConnectDir(self, position=STRIPPOSITION_CENTRE, connectDir: str = STRIPCONNECT_NONE):
        """set the connectDir attribute of the header label at the given position
        """
        if position in STRIPPOSITIONS:
            self._labels[position]._connectDir = connectDir
            self._setPositionParameter(position, STRIPCONNECT, connectDir)
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def getLabelConnectDir(self, position=STRIPPOSITION_CENTRE):
        """Return the connectDir attribute of the header label at the given position
        """
        if position in STRIPPOSITIONS:
            return self._labels[position]._connectDir
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def processNotifier(self, data):
        """Process the notifiers for the strip header
        """
        trigger = data[Notifier.TRIGGER]
        obj = data[Notifier.OBJECT]

        if trigger == 'rename':
            oldPid = data[Notifier.OLDPID]

            for stripPos in STRIPPOSITIONS:
                # change the label text
                if oldPid in self.getLabelText(stripPos):
                    self.setLabelText(position=stripPos, text=str(obj.pid))

                # change the object text
                if self.getLabelObject(stripPos) is obj:
                    self.setLabelObject(position=stripPos, obj=obj)

    @property
    def headerVisible(self):
        return self.strip.getParameter(STRIPDICT, STRIPHEADERVISIBLE)

    @headerVisible.setter
    def headerVisible(self, visible):
        self.setVisible(visible)
        self.strip.setParameter(STRIPDICT, STRIPHEADERVISIBLE, visible)

    @property
    def handle(self):
        return self.strip.getParameter(STRIPDICT, STRIPHANDLE)

    @handle.setter
    def handle(self, handle):
        self.strip.setParameter(STRIPDICT, STRIPHANDLE, handle)
