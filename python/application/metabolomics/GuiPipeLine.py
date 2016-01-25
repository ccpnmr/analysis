"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.Label import Label
import pyqtgraph as pg

from functools import partial

methodDict = {}

class PolyBaseline(QtGui.QWidget, Base):


  def __init__(self, parent=None, current=None, method:str=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.current = current
    self.orderLabel = Label(self, 'Order ', grid=(0, 0))
    self.orderBox = Spinbox(self, grid=(0, 1))
    self.orderBox.setMinimum(2)
    self.orderBox.setMaximum(5)
    # self.orderBox.setValue(2)
    self.orderBox.valueChanged.connect(self.updateLayout)
    self.controlPointsLabel = Label(self, 'Control Points ', grid=(0, 2))
    self.pickOnSpectrumButton = Button(self, 'pick', grid=(0, 9), toggle=True)
    self.pickOnSpectrumButton.setChecked(False)
    self.pickOnSpectrumButton.toggled.connect(self.togglePicking)
    # self.mySignal1.connect(self.setSpinBoxSelected)
    self.currentBox = None
    self.linePoints = []


    self.updateLayout(self.orderBox.value())



  def updateLayout(self, value=None):
    if value < 6:
      for j in range(self.layout().rowCount()):
        for k in range(3, self.layout().columnCount()-1):
          item = self.layout().itemAtPosition(j, k)
          if item:
            if item.widget():
              item.widget().hide()
            self.layout().removeItem(item)
      self.controlPointBoxList = []
      self.controlPointBox1 = DoubleSpinbox(self, grid=(0, 3), showButtons=False)
      self.controlPointBoxList.append(self.controlPointBox1)
      self.ppmLabel = Label(self, 'ppm', grid=(0, 4))
      self.controlPointBox2 = DoubleSpinbox(self, grid=(0, 5), showButtons=False)
      self.controlPointBoxList.append(self.controlPointBox2)
      self.ppmLabel = Label(self, 'ppm', grid=(0, 6))
      self.controlPointBox3 = DoubleSpinbox(self, grid=(0, 7), showButtons=False)
      self.controlPointBoxList.append(self.controlPointBox3)
      self.ppmLabel = Label(self, 'ppm', grid=(0, 8))
      if 2 < value <= 5:
        gridArray = [3+x for x in range(2*(value-2))]
        for i in range(0, len(gridArray), 2):
          self.controlPointBox = DoubleSpinbox(self, grid=(1, gridArray[i]), showButtons=False)
          self.controlPointBoxList.append(self.controlPointBox)
          self.ppmLabel = Label(self, 'ppm', grid=(1, gridArray[i+1]))
    else:
      pass


  def setValueInValueList(self):
    self.valueList = [controlPointBox.value() for controlPointBox in self.controlPointBoxList]


  def togglePicking(self):
    if self.pickOnSpectrumButton.isChecked():
      self.turnOnPositionPicking()
    elif not self.pickOnSpectrumButton.isChecked():
      self.turnOffPositionPicking()

  def turnOnPositionPicking(self):
    print('picking on')
    self.current.registerNotify(self.setPositions, 'positions')

  def turnOffPositionPicking(self):
    print('picking off')
    self.current.unRegisterNotify(self.setPositions, 'positions')

  def setPositions(self, positions):
    if len(self.linePoints) < len(self.controlPointBoxList):
      line = pg.InfiniteLine(angle=90, pos=self.current.positions[0], movable=True, pen=(0, 0, 100))
      line.sigPositionChanged.connect(self.lineMoved)
      self.current.strip.plotWidget.addItem(line)
      self.linePoints.append(line)
      for i, line in enumerate(self.linePoints):
        self.controlPointBoxList[i].setValue(line.pos().x())
    else:
      print('No more lines can be added')


  def lineMoved(self, line):
    lineIndex = self.linePoints.index(line)
    self.controlPointBoxList[lineIndex].setValue(line.pos().x())

