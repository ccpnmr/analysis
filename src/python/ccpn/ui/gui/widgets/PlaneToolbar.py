__author__ = 'simon1'

from functools import partial

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.SpinSystemLabel import SpinSystemLabel
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.ToolBar import ToolBar


from PyQt4 import QtGui, QtCore

class PlaneToolbar(ToolBar):

  def __init__(self, strip, callbacks, **kw):

    ToolBar.__init__(self, strip.stripFrame, **kw)

    self.stripLabel = SpinSystemLabel(self, text='.'.join(strip.pid.id.split('.')[2:]),
                                      appBase=strip._parent._appBase,
                                      hAlign='center', vAlign='top', strip=strip)
    self.stripLabel.setFixedHeight(15)
    self.stripLabel.setFont(QtGui.QFont('Lucida Grande', 10))
    self.spinSystemLabel = Label(self, text='',
                                 hAlign='center', vAlign='top')
    # self.spinSystemLabel.dropEvent = self.dropCallback
    # self.spinSystemLabel.setText("Spin systems shown here")
    self.spinSystemLabel.setFixedHeight(15)
    self.spinSystemLabel.setFont(QtGui.QFont('Lucida Grande', 10))
    self.addWidget(self.stripLabel)
    self.addWidget(self.spinSystemLabel)
    # self.spinSystemLabel.pid = self.pid
    # print(self.pid)lo
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