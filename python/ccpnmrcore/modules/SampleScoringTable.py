__author__ = 'luca'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Label import Label
from ccpncore.gui.Table import ObjectTable, Column
from pyqtgraph.dockarea import Dock
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock



class SampleTableSimple(QtGui.QWidget):
  pass
#
  def __init__(self, parent=None, samples=None):
    QtGui.QWidget.__init__(self, parent)


    if not samples:
      samples = []


    print(samples, 'TableSimple')

    columns = [Column('Sample Name', lambda sample: str(sample.pid)),
               Column('Number of components', lambda sample: str(len(sample.peakCollections))),
               Column('Minimum Score', lambda sample: str(sample.minScore)),
               Column('Average Score', lambda sample: str(sample.averageScore))]


    sampleTable = ObjectTable(self, columns, callback=None, objects=[])
    sampleTable.setObjects(samples)


    self.layout().addWidget(sampleTable, 3, 0, 1, 4)

  def callback(self):
    pass
