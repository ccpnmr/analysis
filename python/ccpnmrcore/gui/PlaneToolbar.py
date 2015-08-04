__author__ = 'simon1'

from ccpncore.gui.Button import Button
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.gui.SpinSystemLabel import SpinSystemLabel

from PyQt4 import QtGui, QtCore

class PlaneToolbar(ToolBar):

  def __init__(self, parent, callbacks, **kw):


    ToolBar.__init__(self, parent.stripFrame, **kw)

    self.stripLabel = SpinSystemLabel(self, text='.'.join(parent.pid.id.split('.')[2:]), appBase=parent._parent._appBase,
                                 hAlign='center', vAlign='top', strip=parent)
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
    if len(parent.orderedAxes) > 2:
      for i in range(len(parent.orderedAxes)-2):
        self.prevPlaneButton = Button(self,'<', callback=callbacks[0])
        self.prevPlaneButton.setFixedWidth(19)
        self.prevPlaneButton.setFixedHeight(19)
        self.planeLabel = DoubleSpinbox(self, showButtons=False)
        self.planeLabel.setFixedHeight(19)
        self.planeLabel.setValue(parent.positions[2])
        self.planeLabel.valueChanged.connect(callbacks[2])
        self.nextPlaneButton = Button(self,'>', callback=callbacks[1])
        self.nextPlaneButton.setFixedWidth(19)
        self.nextPlaneButton.setFixedHeight(19)
        self.addWidget(self.prevPlaneButton)
        self.addWidget(self.planeLabel)
        self.addWidget(self.nextPlaneButton)
        self.planeThickness = Spinbox(self, showButtons=False, hAlign='c')
        self.planeThickness.setMinimum(1)
        self.planeThicknessValue = 1
        self.planeThickness.valueChanged.connect(callbacks[3])
        self.addWidget(self.planeThickness)

