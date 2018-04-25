"""
This module defines a specific Toolbar class for the strip display 
The NmrResidueLabel allows drag and drop of the ids displayed in them

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.guiSettings import textFontSmall

import json
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict

from PyQt5 import QtGui, QtWidgets, QtCore

STRIPLABEL_ISPLUS = '_isPlus'


class _StripLabel(Label):
  """
  Specific Label to be used in Strip displays
  """
  def __init__(self, parent, text, dragKey=DropBase.TEXT, **kwds):

    Label.__init__(self, parent, text, **kwds)
    """
    The text of the label can be dragged; it will be passed on in the dict under key dragKey
    """
    self.parent = parent
    self._dragKey = dragKey
    # self.mousePressEvent = self._mousePressEvent
    # self.dragMoveEvent = self._dragMoveEvent
    self.eventFilter = self._eventFilter        # ejb - only need this one now
    self.setAcceptDrops(True)
    #self.setDragEnabled(True) # not possible for Label

    self._source = None             # ejb
    self.installEventFilter(self)   # ejb

    # disable any drop event callback's until explicitly defined later
    self.setDropEventCallback(None)

  # def _dragMoveEvent(self, event:QtGui.QMouseEvent):
  #   """
  #   Required function to enable dragging and dropping within the sidebar.
  #   """
  #   event.accept()

  def _mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the mouse press event to enable a NmrResidue label to be dragged as a json object
    containing its id and a modifier key to encode the direction to drop the strip.
    """
    event.accept()
    mimeData = QtCore.QMimeData()
    # create the dataDict
    dataDict = {self._dragKey:self.text()}
    isPlus = self._isPlus if hasattr(self, STRIPLABEL_ISPLUS) else True
    dataDict[STRIPLABEL_ISPLUS] = isPlus
    # print ('>>>isPlus', isPlus)

    # update the dataDict with all mouseEvents
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

    # pixmap = QtGui.QPixmap.grabWidget(self)     # ejb - set the pixmap to the image of the label
    pixmap = self.grab()     # ejb - set the pixmap to the image of the label
    painter = QtGui.QPainter(pixmap)            #       replaces the block text
    painter.setCompositionMode(painter.CompositionMode_DestinationIn)

    # change background to selected?
    painter.fillRect(pixmap.rect(), QtGui.QColor(0, 0, 0, 240))
    painter.end()
    drag.setPixmap(pixmap)
    drag.setHotSpot(event.pos())

    # drag.start(QtCore.Qt.MoveAction)
    drag.exec_(QtCore.Qt.MoveAction)      # ejb - PytQ5

    # if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
    #     pass
    # else:
    #   self.show()

  def _eventFilter(self, obj, event):
    """
    Replace all the events with a single filter process
    Not sure if this is the best solution, but doesn't interfere with _processDroppedItems
    and allows changing of the cursor - ejb
    """
    if event.type() == QtCore.QEvent.MouseButtonPress:
      self._mousePressEvent(event)                      # call the standard mouse event
      return True

    if event.type() == QtCore.QEvent.DragEnter:
      self._source = event.source()
      try:
        if isinstance(obj,_StripLabel) and self._source != self:
          mime = event.mimeData().text()
          dataItem = json.loads(mime)
          if 'text' in dataItem and dataItem['text'].startswith('NR'):
          # only test NmrResidues
          # print('>>>DragEnterFilter %s' % dataItem['text'])
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.DragCopyCursor)
      finally:
        event.accept()
        return True

    if event.type() == QtCore.QEvent.DragLeave:
      QtWidgets.QApplication.restoreOverrideCursor()
      # print('>>>DragLeaveFilter')
      event.accept()
      return True

    if event.type() == QtCore.QEvent.Leave:
      QtWidgets.QApplication.restoreOverrideCursor()
      # print('>>>DragLeaveFilter')
      event.accept()
      return True

    if event.type() == QtCore.QEvent.MouseMove:
      if not isinstance(obj,_StripLabel):
        QtWidgets.QApplication.restoreOverrideCursor()
        event.accept()
        return True

    if event.type() == QtCore.QEvent.Drop:
      QtWidgets.QApplication.restoreOverrideCursor()
      # print(">>>DropFilter")
      event.ignore()
      # no return True needed, so BackboneAssignment._processDroppedItem still fires

    return super(_StripLabel, self).eventFilter(obj,event)    # do the rest


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

    width=20; height=20

    self.previousPlaneButton = Button(parent=self, text='<', grid=(0,0),
                                      callback=self._previousPlane)
    self.previousPlaneButton.setFixedWidth(width)
    self.previousPlaneButton.setFixedHeight(height)

    self.spinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0,1),
                                 callback=self._spinBoxChanged)
    self.spinBox.setFixedHeight(height)

    self.nextPlaneButton = Button(parent=self, text='<', grid=(0,2),
                                  callback=self._nextPlane)
    self.nextPlaneButton.setFixedWidth(width)
    self.nextPlaneButton.setFixedHeight(height)

    self.planeCountSpinBox = DoubleSpinbox(parent=self, showButtons=False, grid=(0,3),
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
  def __init__(self, qtParent, strip, callbacks, **kw):

    ToolBar.__init__(self, parent=qtParent, **kw)

    self.strip = strip
    self.planeLabels = []
    self.planeCounts = []
    for i in range(len(strip.orderedAxes)-2):
      self.prevPlaneButton = Button(self, '<', callback=partial(callbacks[0], i))
      self.prevPlaneButton.setFixedWidth(19)
      self.prevPlaneButton.setFixedHeight(19)
      planeLabel = DoubleSpinbox(self, showButtons=False)
      planeLabel.setFixedHeight(19)
      # below does not work because it allows wheel events to behave but not manual text entry (some Qt stupidity)
      # so instead use a wheelEvent to deal with the wheel events and editingFinished (in GuiStripNd) to do text
      #planeLabel.valueChanged.connect(partial(callbacks[2], i))
      if callbacks[2]:
        planeLabel.wheelEvent = partial(self._wheelEvent, i)
        self.prevPlaneCallback = callbacks[0]
        self.nextPlaneCallback = callbacks[1]
      self.nextPlaneButton = Button(self,'>', callback=partial(callbacks[1], i))
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
    if event.angleDelta().y() > 0: # note that in Qt5 this becomes angleDelta().y()
      if self.prevPlaneCallback:
        self.prevPlaneCallback(n)
    else:
      if self.nextPlaneCallback:
        self.nextPlaneCallback(n)

    self.strip._rebuildStripContours()

STRIPCONNECT_ISMINUS = 'isMinus'
STRIPCONNECT_ISPLUS = 'isPlus'
STRIPCONNECT_DIRS = (STRIPCONNECT_ISMINUS, None, STRIPCONNECT_ISPLUS)
STRIPPOSITION_LEFT = 'left'
STRIPPOSITION_CENTRE = 'centre'
STRIPPOSITION_RIGHT = 'right'
STRIPPOSITIONS = (STRIPPOSITION_LEFT[0], STRIPPOSITION_CENTRE[0], STRIPPOSITION_RIGHT[0])


class stripHeader(Frame):
  def __init__(self, parent, mainWindow, **kw):
    super(stripHeader, self).__init__(parent=parent, **kw)

    self.parent = parent
    self.mainWindow = mainWindow

    self._labels = {}

    for lab in STRIPPOSITIONS:
      self._labels[lab] = _StripLabel(parent=self,
                                     text='', spacing=(0,0),
                                     grid=(0,STRIPPOSITIONS.index(lab)))

      self._labels[lab].setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
      self._labels[lab].setFont(textFontSmall)
      self._labels[lab].dropEnabled = False

    self.setFixedHeight(16)

  def setLabelText(self, text=None, position=STRIPPOSITION_CENTRE):
    pos = position[0]
    if pos in STRIPPOSITIONS:
      self._labels[pos].setText(text)

  def getLabelText(self, position=STRIPPOSITION_CENTRE):
    pos = position[0]
    if pos in STRIPPOSITIONS:
      return self._labels[pos].text()

    return None

  def geLabel(self, position=STRIPPOSITION_CENTRE):
    """Return the stripLabel widget"""
    pos = position[0]
    if pos in STRIPPOSITIONS:
      return self._Labels[pos]

    return None

  def showLabel(self, position=STRIPPOSITION_CENTRE, doShow: bool=True):
    """show / hide the _stripLabel"""
    pos = position[0]
    if pos in STRIPPOSITIONS:
      self._labels[pos].setVisible(doShow)

  def hideLabel(self, position=STRIPPOSITION_CENTRE):
    "Hide the _stripLabel; convienience"
    pos = position[0]
    if pos in STRIPPOSITIONS:
      self._labels[pos].setVisible(False)






  def setStripLabelisPlus(self, isPlus: bool):
    """set the isPlus attribute of the _stripResidueId"""
    self._stripLabel._isPlus = isPlus
