"""
This module defines a specific Toolbar class for the strip display 
The NmrResidueLabel allows drag and drop of the ids displayed in them

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
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

import json
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict
from ccpn.core.NmrResidue import NmrResidue


from PyQt4 import QtGui, QtCore


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
    self.mousePressEvent = self._mousePressEvent
    self.dragMoveEvent= self._dragMoveEvent
    self.setAcceptDrops(True)
    #self.setDragEnabled(True) # not possile for Label

    # disable any drop event callback's until explicitly defined later
    self.setDropEventCallback(None)

  def _dragMoveEvent(self, event:QtGui.QMouseEvent):
    """
    Required function to enable dragging and dropping within the sidebar.
    """
    event.accept()

  def _mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the mouse press event to enable a NmrResidue label to be dragged as a json object
    containing its id and a modifier key to encode the direction to drop the strip.
    """
    event.accept()
    mimeData = QtCore.QMimeData()
    # create the dataDict
    dataDict = {self._dragKey:self.text()}
    # update the dataDict with all mouseEvents
    dataDict.update(getMouseEventDict(event))
    # convert into json
    itemData = json.dumps(dataDict)
    mimeData.setData(DropBase.JSONDATA, self.text())
    mimeData.setText(itemData)
    drag = QtGui.QDrag(self)
    drag.setMimeData(mimeData)
    drag.start(QtCore.Qt.MoveAction)
    # if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
    #     pass
    # else:
    #   self.show()


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
    if event.delta() > 0: # note that in Qt5 this becomes angleDelta()
      if self.prevPlaneCallback:
        self.prevPlaneCallback(n)
    else:
      if self.nextPlaneCallback:
        self.nextPlaneCallback(n)
