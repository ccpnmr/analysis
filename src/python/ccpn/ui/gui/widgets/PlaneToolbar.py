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
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import json
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label, VerticalLabel, ActiveLabel
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame, OpenGLOverlayFrame
from ccpn.ui.gui.guiSettings import textFont, getColours, STRIPHEADER_BACKGROUND, \
    STRIPHEADER_FOREGROUND, GUINMRRESIDUE, CCPNGLWIDGET_BACKGROUND, textFontLarge, \
    CCPNGLWIDGET_HEXHIGHLIGHT, CCPNGLWIDGET_HEXFOREGROUND
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.core.Peak import Peak
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.util.Logging import getLogger


STRIPLABEL_CONNECTDIR = '_connectDir'
STRIPLABEL_CONNECTNONE = 'none'
SINGLECLICK = 'click'
DOUBLECLICK = 'doubleClick'


class _StripLabel(ActiveLabel):  #  VerticalLabel): could use Vertical label so that the strips can flip
    """
    Specific Label to be used in Strip displays
    """

    # ED: This class contains the best current method for handling single and double click events
    # without any clashes between events, and creating a dragged item
    DOUBLECLICKENABLED = False

    def __init__(self, parent, mainWindow, strip=None, text=None, dragKey=DropBase.PIDS, stripArrangement=None, **kwds):

        super().__init__(parent, text, **kwds)
        # The text of the label can be dragged; it will be passed on in the dict under key dragKey

        self._parent = parent
        self.strip = strip
        self.spectrumDisplay = self.strip.spectrumDisplay if strip else None
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.project

        self._dragKey = dragKey
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)           # not possible for Label

        self._lastClick = None
        self._mousePressed = False
        self.stripArrangement = stripArrangement
        # self.setOrientation('vertical' if stripArrangement == 'X' else 'horizontal')

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
        contextMenu.addAction('Close All Headers in All SpectrumDisplays', self._closeAll)
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
class PlaneSelectorWidget(Frame):
    """
    This widget contains the buttons and entry boxes for selection of the plane
    """

    def __init__(self, qtParent, mainWindow=None, strip=None, axis=None, **kwds):
        "Setup the buttons and callbacks for axis"

        super().__init__(parent=qtParent, setLayout=True, **kwds)

        self.mainWindow = mainWindow
        self.project = mainWindow.project
        self.strip = strip
        self.axis = axis

        self._linkedSpinBox = None
        self._linkedPlaneCount = None

        width = 20
        height = 20

        self.previousPlaneButton = Button(parent=self, text='<', grid=(0, 0),
                                          callback=self._previousPlane)
        self.previousPlaneButton.setFixedWidth(width)
        self.previousPlaneButton.setFixedHeight(height)

        self.spinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0, 1),
                                     callback=self._spinBoxChanged, objectName='PlaneSelectorWidget_planeDepth')
        self.spinBox.setFixedWidth(60)
        self.spinBox.setFixedHeight(height)
        self.spinBox.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.nextPlaneButton = Button(parent=self, text='>', grid=(0, 2),
                                      callback=self._nextPlane)
        self.nextPlaneButton.setFixedWidth(width)
        self.nextPlaneButton.setFixedHeight(height)

        self.planeCountSpinBox = Spinbox(parent=self, showButtons=False, grid=(0, 3), min=1, max=1000,
                                         objectName='PlaneSelectorWidget_planeCount'
                                         )
        self.planeCountSpinBox.setFixedWidth(32)
        self.planeCountSpinBox.setFixedHeight(height)
        self.planeCountSpinBox.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.planeCountSpinBox.returnPressed.connect(self._planeCountChanged)
        self.planeCountSpinBox.wheelChanged.connect(self._planeCountChanged)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    def _initialise(self, strip=None, axis=None):
        """Set the initial values for the plane selector
        """
        from ccpn.ui.gui.lib.Strip import GuiStrip

        strip = self.project.getByPid(strip) if isinstance(strip, str) else strip
        if not isinstance(strip, GuiStrip):
            raise TypeError("%s is not of type Strip" % str(strip))
        if not isinstance(axis, int):
            raise TypeError("%s is not of type int" % str(axis))
        if not (0 <= axis < len(strip.axisCodes)):
            raise ValueError("axis %s is out of range (0, %i)" % (str(axis), len(self.axisCodes) - 1))

        self.strip = strip
        self.axis = axis

        self.spinBox.setToolTip(str(self.strip.axisCodes[self.axis]))

    def setCallbacks(self, callbacks):
        self._callbacks = callbacks

    def _planeCountChanged(self, value: int = 1):
        """
        Changes the number of planes displayed simultaneously.
        """
        if self.strip:
            self._callbacks[3](value)

    def _nextPlane(self, *args):
        """
        Increases axis ppm position by one plane
        """
        if self.strip:
            self._callbacks[2](*args)

    def _previousPlane(self, *args):
        """
        Decreases axis ppm position by one plane
        """
        if self.strip:
            self._callbacks[0](*args)

    def _spinBoxChanged(self, value: float):
        """
        Sets the value of the axis plane position box if the specified value is within the displayable limits.
        """
        if self.strip:
            self._callbacks[1](value)

    def _wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            if self.strip.prevPlaneCallback:
                self.strip.prevPlaneCallback(self.axis)
        else:
            if self.strip.nextPlaneCallback:
                self.strip.nextPlaneCallback(self.axis)

        self.strip._rebuildStripContours()

    def updatePosition(self):
        """Set new axis position
        """
        axis = self.strip.orderedAxes[self.axis]

        ppmPosition = axis.position
        ppmWidth = axis.width

        self.setPosition(ppmPosition, ppmWidth)

    def setPosition(self, ppmPosition, ppmWidth):
        """Set the new ppmPosition/ppmWidth
        """
        with self.blockWidgetSignals():
            self.spinBox.setValue(ppmPosition)

    def setPlaneValues(self, minZPlaneSize=None, minAliasedFrequency=None, maxAliasedFrequency=None, ppmPosition=None):
        """Set new values for the plane selector
        """
        with self.blockWidgetSignals():

            self.spinBox.setSingleStep(minZPlaneSize)
            if maxAliasedFrequency is not None:
                self.spinBox.setMaximum(maxAliasedFrequency)
            if minAliasedFrequency is not None:
                self.spinBox.setMinimum(minAliasedFrequency)

            self.spinBox.setValue(ppmPosition)

    def getPlaneValues(self):
        """Return the current settings for this axis
        :returns: ppmValue, maximum ppmValue, ppmStepSize, ppmPosition, planeCount
        """
        return self.spinBox.minimum(), self.spinBox.maximum(), self.spinBox.singleStep(), self.spinBox.value(), self.planeCount

    @property
    def planeCount(self):
        """Return the plane count for this axis
        """
        return self.planeCountSpinBox.value()


def _setAxisCode(self, *args):
    pass


def _setAxisPosition(self, *args):
    pass


def _setPlaneCount(self, *args):
    pass


def _setPlaneSelection(self, *args):
    pass


def _initAxisCode(self, widget, strip, axis):
    pass


def _initAxisPosition(self, widget, strip, axis):
    pass


def _initPlaneCount(self, widget, strip, axis):
    pass


def _initPlaneSelection(self, widget, strip, axis):
    self.__postInit__(widget, strip, axis)


class _OpenGLFrameABC(OpenGLOverlayFrame):
    """
    OpenGL ABC for items to overlay the GL frame (until a nicer way can by found)

    BUTTONS is a tuple of tuples of the form:

        ((attributeName, widgetType, init function, set attrib function)
         ...
         )

        attributeName is a string defining the attribute in the container
        widgetType is the type of widget, e.g. see PlaneAxisWidget
        init functions are called after instantiation of widgets
            - typically static functions of the form <name>(self, widget, ...)
                self is the container class, widget is the widget object
        attrib functions are called from _populate to populate the widgets after changes
            (or possibly revert - not fully implemented yet)

    """
    BUTTONS = tuple()

    def __init__(self, qtParent, mainWindow, *args, **kwds):

        super().__init__(parent=qtParent, setLayout=True, **kwds)

        self.mainWindow = mainWindow
        self.project = mainWindow.project
        self._initFuncList = ()
        self._setFuncList = ()

        if not self.BUTTONS:
            # MUST BE SUBCLASSED
            raise NotImplementedError("Code error: BUTTONS not implemented")

        # build the list of widgets in frame
        row = col = 0
        for buttonDef in self.BUTTONS:

            if buttonDef:
                widgetName, widgetType, initFunc, setFunc, grid, gridSpan = buttonDef

                if not widgetType:
                    raise TypeError('Error: button widget not defined')

                # if widget is given then add to the container
                widget = widgetType(self, mainWindow=mainWindow, grid=grid, gridSpan=gridSpan)  #grid=(row, col), gridSpan=(1, 1))
                self._setStyle(widget)
                if initFunc:
                    self._initFuncList += ((initFunc, self, widget),)
                if setFunc:
                    self._setFuncList += ((setFunc, self, widget),)

                # add the widget here
                setattr(self, widgetName, widget)
                col += 1
            else:

                # else, move to the next row (simple newLine)
                row += 1
                col = 0

        # add an expanding widget to the end of the row
        Spacer(self, 2, 2, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum,
               grid=(0, col + 1), gridSpan=(1, 1))

        # initialise the widgets
        for func, klass, widget in self._initFuncList:
            func(klass, widget, *args)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    def _populate(self):
        for pp, klass, widget in self._setFuncList:
            pp(self, klass, widget)


class PlaneAxisWidget(_OpenGLFrameABC):
    """
    Need Frame:
        AxisCode label

        AxisValue

            Frame

                Change arrow
                value box
                Change arrow

                planes box

    """
    BUTTONS = (('_axisLabel', ActiveLabel, _initAxisCode, _setAxisCode, (0, 0), (1, 1)),
               ('_axisPpmPosition', ActiveLabel, _initAxisPosition, _setAxisPosition, (0, 1), (1, 1)),
               ('_axisPlaneCount', ActiveLabel, _initPlaneCount, _setPlaneCount, (0, 2), (1, 1)),
               ('_axisSelector', PlaneSelectorWidget, _initPlaneSelection, _setPlaneSelection, (0, 3), (1, 1))
               )

    def __init__(self, qtParent, mainWindow, strip, axis, **kwds):
        super().__init__(qtParent, mainWindow, strip, axis, **kwds)

        self.strip = strip
        self.axis = axis

        axisButtons = (self._axisLabel, self._axisPpmPosition, self._axisPlaneCount, self._axisSelector)

        axisButtons[0].setSelectionCallback(partial(self._selectAxisCallback, axisButtons))
        for button in axisButtons[1:3]:
            button.setSelectionCallback(partial(self._selectPositionCallback, axisButtons))

        self._axisLabel.setVisible(True)
        self._axisPpmPosition.setVisible(True)
        self._axisPlaneCount.setVisible(True)
        self._axisSelector.setVisible(False)

        # connect strip changed events to here
        self.strip.optionsChanged.connect(self._optionsChanged)

    def __postInit__(self, widget, strip, axis):
        """Seems an awkward way of getting a generic post init function but can't think of anything else yet
        """
        # assume that nothing has been set yet
        self._axisSelector._initialise(strip, axis)
        self._axisLabel.setText(strip.axisCodes[axis] + ':')
        self._axisLabel.setToolTip(strip.axisCodes[axis])
        self._axisSelector.setCallbacks((self._previousPlane,
                                         self._spinBoxChanged,
                                         self._nextPlane,
                                         self._planeCountChanged,
                                         self._wheelEvent
                                         ))
        self._resize()

    @pyqtSlot(dict)
    def _optionsChanged(self, aDict):
        """Respond to signals from other frames in the strip
        """
        # may be required to select/de-select rows
        source = aDict.get('source')
        if source and source != self:
            # change settings here
            self._setLabelBorder(False)

            # set the axis in the strip for modifying with the wheelMouse event - not implemented yet
            self.strip.activePlaneAxis = self.axis

    def _setLabelBorder(self, value):
        for label in (self._axisLabel, self._axisPpmPosition, self._axisPlaneCount):
            if value:
                self._setStyle(label, foregroundColour=CCPNGLWIDGET_HEXHIGHLIGHT)
            else:
                self._setStyle(label, foregroundColour=CCPNGLWIDGET_HEXFOREGROUND)

    def _selectAxisCallback(self, widgets):
        # if the first widget is clicked then change the selected axis
        if widgets[3].isVisible():
            widgets[3].hide()
            widgets[2].show()
            widgets[1].show()

        self._setLabelBorder(True)
        self.strip.optionsChanged.emit({'source' : self,
                                        'clicked': True})
        self._resize()

    def _selectPositionCallback(self, widgets):
        # if the other widgets are clicked then toggle the planeToolbar buttons
        if widgets[3].isVisible():
            widgets[3].hide()
            widgets[2].show()
            widgets[1].show()
        else:
            widgets[1].hide()
            widgets[2].hide()
            widgets[3].show()

        self._setLabelBorder(True)
        self.strip.optionsChanged.emit({'source' : self,
                                        'clicked': True})
        self._resize()

    def updatePosition(self):
        """Set new axis position
        """
        axis = self.strip.orderedAxes[self.axis]
        ppmPosition = axis.position
        ppmWidth = axis.width

        self.setPosition(ppmPosition, ppmWidth)

    def setPosition(self, ppmPosition, ppmWidth):
        """Set the new ppmPosition/ppmWidth
        """
        self._axisSelector.setPosition(ppmPosition, ppmWidth)
        self._axisPpmPosition.setText('%.3f' % ppmPosition)

    def getPlaneValues(self):
        """Return the current settings for this axis
        :returns: ppmValue, maximum ppmValue, ppmStepSize, ppmPosition, planeCount
        """
        return self._axisSelector.getPlaneValues()

    def setPlaneValues(self, minZPlaneSize=None, minAliasedFrequency=None, maxAliasedFrequency=None, ppmPosition=None):
        """Set new values for the plane selector
        """
        planeBox = self._axisSelector
        planeBox.setPlaneValues(minZPlaneSize, minAliasedFrequency, maxAliasedFrequency, ppmPosition)

        self._axisPpmPosition.setText('%.3f' % ppmPosition)
        self._axisPlaneCount.setText('[' + str(planeBox.planeCount) + ']')

    @property
    def planeCount(self) -> int:
        return self._axisSelector.planeCount

    def _planeCountChanged(self, value: int = 1):
        """
        Changes the number of planes displayed simultaneously.
        """
        if self.strip:
            zAxis = self.strip.orderedAxes[self.axis]
            zAxis.width = value * self._axisSelector.spinBox.singleStep()
            self._axisPlaneCount.setText('[' + str(value) + ']')
            self.strip._rebuildStripContours()

    def _nextPlane(self, *args):
        """
        Increases axis ppm position by one plane
        """
        if self.strip:
            self.strip.changeZPlane(self.axis, planeCount=-1)  # -1 because ppm units are backwards
            self.strip._rebuildStripContours()

            self.strip.pythonConsole.writeConsoleCommand("strip.nextZPlane()", strip=self.strip)
            getLogger().info("application.getByGid(%r).nextZPlane()" % self.strip.pid)

    def _previousPlane(self, *args):
        """
        Decreases axis ppm position by one plane
        """
        if self.strip:
            self.strip.changeZPlane(self.axis, planeCount=1)
            self.strip._rebuildStripContours()

            self.strip.pythonConsole.writeConsoleCommand("strip.prevZPlane()", strip=self.strip)
            getLogger().info("application.getByGid(%r).prevZPlane()" % self.strip.pid)

    def _spinBoxChanged(self, *args):
        """
        Sets the value of the axis plane position box if the specified value is within the displayable limits.
        """
        if self.strip:
            planeLabel = self._axisSelector.spinBox
            value = planeLabel.value()

            if planeLabel.minimum() <= value <= planeLabel.maximum():
                self.strip.changeZPlane(self.axis, position=value)
                self.strip._rebuildStripContours()

    def _wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            if self.strip.prevPlaneCallback:
                self.strip.prevPlaneCallback(self.axis)
        else:
            if self.strip.nextPlaneCallback:
                self.strip.nextPlaneCallback(self.axis)

        self.strip._rebuildStripContours()


class PlaneToolbar(Frame):
    #TODO: undocumented and needs refactoring ;
    # GWV: Does not work as a Widget!?
    def __init__(self, qtParent, strip, callbacks, stripArrangement=None,
                 containers=None, **kwds):

        super().__init__(parent=qtParent, setLayout=True, **kwds)

        self.strip = strip
        self.planeLabels = []
        self.planeCounts = []
        row = 0
        for i in range(len(strip.orderedAxes) - 2):
            if not containers:
                _toolbar = ToolBar(self, grid=(0, row))
            else:
                cFrame, cWidgets = list(containers.items())[i]
                _toolbar = ToolBar(cFrame, grid=(0, 3))

                # add the new toolbar to the popup display
                cWidgets += (_toolbar,)
                cWidgets[2].setVisible(False)
                cWidgets[3].setVisible(False)

                # set the axisCode
                cWidgets[0].setText(str(strip.axisCodes[i + 2]) + ":")

            self.prevPlaneButton = Button(_toolbar, '<', callback=partial(callbacks[0], i))
            self.prevPlaneButton.setFixedWidth(19)
            self.prevPlaneButton.setFixedHeight(19)
            planeLabel = DoubleSpinbox(_toolbar, showButtons=False, objectName="PlaneToolbar_planeLabel" + str(i),
                                       )
            planeLabel.setToolTip(str(strip.axisCodes[i + 2]))

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
            self.nextPlaneButton = Button(_toolbar, '>', callback=partial(callbacks[1], i))
            self.nextPlaneButton.setFixedWidth(19)
            self.nextPlaneButton.setFixedHeight(19)
            planeCount = Spinbox(_toolbar, showButtons=False, hAlign='c')
            planeCount.setMinimum(1)
            planeCount.setMaximum(1000)
            planeCount.setValue(1)
            planeCount.oldValue = 1
            planeCount.returnPressed.connect(partial(callbacks[3], i))
            planeCount.wheelChanged.connect(partial(callbacks[3], i))

            _toolbar.addWidget(self.prevPlaneButton)
            _toolbar.addWidget(planeLabel)
            _toolbar.addWidget(self.nextPlaneButton)
            _toolbar.addWidget(planeCount)
            self.planeLabels.append(planeLabel)
            self.planeCounts.append(planeCount)
            row += 1

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

STRIPPOSITION_MINUS = 'minus'
STRIPPOSITION_PLUS = 'plus'
STRIPPOSITION_LEFT = 'l'
STRIPPOSITION_CENTRE = 'c'
STRIPPOSITION_RIGHT = 'r'
STRIPPOSITIONS = (STRIPPOSITION_MINUS, STRIPPOSITION_PLUS, STRIPPOSITION_LEFT, STRIPPOSITION_CENTRE, STRIPPOSITION_RIGHT)

STRIPDICT = 'stripHeaderDict'
STRIPTEXT = 'stripText'
STRIPICONNAME = 'stripIconName'
STRIPICONSIZE = 'stripIconSize'
STRIPOBJECT = 'stripObject'
STRIPCONNECT = 'stripConnect'
STRIPVISIBLE = 'stripVisible'
STRIPENABLED = 'stripEnabled'
STRIPTRUE = 1
STRIPFALSE = 0
STRIPSTOREINDEX = [STRIPTEXT, STRIPOBJECT, STRIPCONNECT, STRIPVISIBLE, STRIPENABLED]
STRIPHEADERVISIBLE = 'stripHeaderVisible'
STRIPHANDLE = 'stripHandle'


def _initIcon(self, widget, strip):
    self.__postIconInit__(widget, strip)


def _initStripHeader(self, widget, strip):
    self.__postHeaderInit__(widget, strip)


class StripHeaderWidget(_OpenGLFrameABC):
    BUTTONS = (('_nmrChainLeft', _StripLabel, None, None, (0, 0), (2, 1)),
               ('_nmrChainRight', _StripLabel, _initIcon, None, (0, 4), (2, 1)),
               ('_stripDirection', _StripLabel, None, None, (0, 2), (1, 2)),
               ('_stripLabel', _StripLabel, None, None, (1, 2), (1, 1)),
               ('_stripPercent', _StripLabel, _initStripHeader, None, (1, 3), (1, 1)),
               )

    def __postIconInit__(self, widget, strip):
        """Seems an awkward way of getting a generic post init function but can't think of anything else yet
        """
        # assume that nothing has been set yet
        # self._nmrChainLeft.setPixmap(Icon('icons/down-left').pixmap(18, 18))
        # self._nmrChainRight.setPixmap(Icon('icons/down-right').pixmap(18, 18))
        # self._nmrChainLeft.setVisible(False)
        # self._nmrChainRight.setVisible(False)

        # self.setLabelIcon('icons/down-left', (18, 18), STRIPPOSITION_MINUS)
        # self.setLabelIcon('icons/down-right', (18, 18), STRIPPOSITION_PLUS)
        # self.setEnabledLeftDrop(False)
        # self.setEnabledRightDrop(False)
        pass

    def __postHeaderInit__(self, widget, strip):
        """Seems an awkward way of getting a generic post init function but can't think of anything else yet
        """
        # assume that nothing has been set yet

        # add gui notifiers here instead of in backboneAssignment?
        GuiNotifier(self._nmrChainLeft,
                    [GuiNotifier.DROPEVENT], [DropBase.TEXT],
                    self._processDroppedLabel,
                    toLabel=self._stripDirection,
                    plusChain=False)

        GuiNotifier(self._nmrChainRight,
                    [GuiNotifier.DROPEVENT], [DropBase.TEXT],
                    self._processDroppedLabel,
                    toLabel=self._stripDirection,
                    plusChain=True)

        self._resize()

    def _processDroppedLabel(self, data, toLabel=None, plusChain=None):
        """Not a very elegant way of running backboneAssignment code from the strip headers

        Should be de-coupled from the backboneAssignment module
        """
        if toLabel and toLabel.text():
            dest = toLabel.text()
            nmrResidue = self.project.getByPid(dest)

            if nmrResidue:

                guiModules = self.mainWindow.modules
                for guiModule in guiModules:
                    if guiModule.className == 'BackboneAssignmentModule':
                        guiModule._processDroppedNmrResidue(data, nmrResidue=nmrResidue, plusChain=plusChain)

    def __init__(self, qtParent, mainWindow, strip, stripArrangement=None, **kwds):
        super().__init__(qtParent, mainWindow, strip, **kwds)

        self._parent = qtParent
        self.mainWindow = mainWindow
        self.strip = strip
        self.setAutoFillBackground(False)

        self._labels = dict((strip, widget) for strip, widget in
                            zip(STRIPPOSITIONS,
                                (self._nmrChainLeft, self._nmrChainRight, self._stripLabel, self._stripDirection, self._stripPercent)))

        labelsVisible = False
        for stripPos in STRIPPOSITIONS:
            # read the current strip header values
            headerText = self._getPositionParameter(stripPos, STRIPTEXT, '')

            headerIconName = self._getPositionParameter(stripPos, STRIPICONNAME, '')
            headerIconSize = self._getPositionParameter(stripPos, STRIPICONSIZE, (18, 18))

            # not sure this is required
            headerObject = self.strip.project.getByPid(self._getPositionParameter(stripPos, STRIPOBJECT, None))
            headerConnect = self._getPositionParameter(stripPos, STRIPCONNECT, STRIPCONNECT_NONE)
            headerVisible = self._getPositionParameter(stripPos, STRIPVISIBLE, False)
            headerEnabled = self._getPositionParameter(stripPos, STRIPENABLED, True)

            self._labels[stripPos].obj = headerObject
            self._labels[stripPos]._connectDir = headerConnect

            self._labels[stripPos].setVisible(True if headerText else False)

            self._labels[stripPos].setVisible(headerVisible)
            labelsVisible = labelsVisible or headerVisible
            self._labels[stripPos].setEnabled(headerEnabled)

            if headerIconName:
                self.setLabelIcon(headerIconName, headerIconSize, stripPos)
            elif headerText:
                self.setLabelText(headerText, stripPos)

        # get the visible state of the header
        headerVisible = self.strip.getParameter(STRIPDICT, STRIPHEADERVISIBLE)
        self.setVisible(True)  # headerVisible if headerVisible is not None else labelsVisible)
        self._resize()

    def setEnabledLeftDrop(self, value):

        # set the icon the first time if not loaded
        iconLeft = self._getPositionParameter(STRIPPOSITION_MINUS, STRIPICONNAME, '')
        if value and not iconLeft:
            self.setLabelIcon('icons/down-left', (18, 18), STRIPPOSITION_MINUS)

        self.setLabelVisible(STRIPPOSITION_MINUS, value)
        self._resize()

    def setEnabledRightDrop(self, value):

        # set the icon the first time if not loaded
        iconRight = self._getPositionParameter(STRIPPOSITION_PLUS, STRIPICONNAME, '')
        if value and not iconRight:
            self.setLabelIcon('icons/down-right', (18, 18), STRIPPOSITION_PLUS)

        self.setLabelVisible(STRIPPOSITION_PLUS, value)
        self._resize()

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
                        # value = '<<<'
                        value = ''
                    elif 'PLUS' in value:
                        # value = '>>>'
                        value = ''

                return value

        return default

    def reset(self):
        """Clear all header labels
        """
        self.setVisible(False)
        for stripPos in STRIPPOSITIONS:
            self._labels[stripPos].obj = None
            self._labels[stripPos]._connectDir = STRIPCONNECT_NONE
            self._labels[stripPos].setVisible(False)
            self._labels[stripPos].setEnabled(True)

            # clear the header store
            params = {STRIPTEXT    : '',
                      STRIPICONNAME: '',
                      STRIPOBJECT  : None,
                      STRIPCONNECT : STRIPCONNECT_NONE,
                      STRIPVISIBLE : False,
                      STRIPENABLED : True
                      }
            self.strip.setParameter(STRIPDICT, stripPos, params)
        self.strip.setParameter(STRIPDICT, STRIPHANDLE, None)
        self.strip.setParameter(STRIPDICT, STRIPHEADERVISIBLE, False)
        self._resize()

    def setLabelObject(self, obj=None, position=STRIPPOSITION_CENTRE):
        """Set the object attached to the header label at the given position and store its pid
        """
        # NOTE:ED not sure I need this now - cbheck rename nmrResidue, etc.
        self.show()
        if position in STRIPPOSITIONS:
            self._labels[position].obj = obj

            # SHOULD have a pid if an object
            if obj and hasattr(obj, 'pid'):
                self._setPositionParameter(position, STRIPOBJECT, str(obj.pid))
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

        self._resize()

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

            self._labels[position].setVisible(True if text else False)
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

        self._resize()

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

        self._resize()

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

        self._resize()

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

        self._resize()

    def getLabelConnectDir(self, position=STRIPPOSITION_CENTRE):
        """Return the connectDir attribute of the header label at the given position
        """
        if position in STRIPPOSITIONS:
            return self._labels[position]._connectDir
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

    def setLabelIcon(self, iconName=None, iconSize=(18, 18), position=STRIPPOSITION_CENTRE):
        """Set the text for header label at the given position
        """
        self.show()
        if position in STRIPPOSITIONS:
            self._labels[position].setPixmap(Icon(iconName).pixmap(*iconSize))
            self._setPositionParameter(position, STRIPICONNAME, str(iconName))

            self._labels[position].setVisible(True if iconName else False)
        else:
            raise ValueError('Error: %s is not a valid position' % str(position))

        self._resize()

    # def getLabelIcon(self, position=STRIPPOSITION_CENTRE):
    #     """Return the text for header label at the given position
    #     """
    #     if position in STRIPPOSITIONS:
    #         return self._labels[position].text()
    #     else:
    #         raise ValueError('Error: %s is not a valid position' % str(position))

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
        self._resize()

    @property
    def handle(self):
        return self.strip.getParameter(STRIPDICT, STRIPHANDLE)

    @handle.setter
    def handle(self, handle):
        self.strip.setParameter(STRIPDICT, STRIPHANDLE, handle)
        self._resize()


class TestPopup(Frame):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        self.setLayout(QtWidgets.QHBoxLayout())
        Button_close = QtWidgets.QPushButton('close')
        self.layout().addWidget(QtWidgets.QLabel("HI"))
        self.layout().addWidget(Button_close)
        Button_close.clicked.connect(self.close)
        self.exec_()
        print("clicked")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPos() - self.oldPos)
        #print(delta)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()
