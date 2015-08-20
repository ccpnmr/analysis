from PyQt4 import QtCore, QtGui
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.Button import Button
from ccpncore.gui.Label import Label
from ccpncore.gui.Table import ObjectTable, Column
from pyqtgraph.dockarea import Dock
from ccpncore.gui.Table import ObjectTable, Column

from ccpncore.gui.Dock import CcpnDock
from ccpnmrcore.modules.SamplesComponentsTable import PeakListSampleComponent
from ccpnmrcore.modules.SamplesComponentsView import SamplesComponentsView



class SampleAnalysis(CcpnDock):
  ### this class creates a module to analyse the samples. It is composed by four tabs.

  def __init__(self, project, samples=None,):
    super(SampleAnalysis, self)
    CcpnDock.__init__(self, name='Sample Analysis')
    self.project = project

    ######## ========   Set Layout  ====== ########
    self.tabWidget = QtGui.QTabWidget()
    self.moduleLayout = QtGui.QGridLayout()
    self.layout.addLayout(self.moduleLayout, 0, 0)
    self.moduleLayout.addWidget(self.tabWidget, 1, 1, 1, 1)
    self.setLayout(self.moduleLayout)


    ######## ======== On The Fly Sample Table  ====== ########
    if not samples:
      samples = []
    self.samples = samples
    columns = [Column('Sample Name', lambda sample: str(sample.pid)),
               Column('Number of components', lambda sample: str(len(sample.peakCollections))),
               Column('Minimum Score', lambda sample: str(sample.minScore)),
               Column('Average Score', lambda sample: str(sample.averageScore))]
    self.sampleTable = ObjectTable(self, columns, callback=None, objects=[])
    self.sampleTable.setObjects(samples)

    ######## ========   Set Tabs  ====== ########
    self.componentPL = PeakListSampleComponent(self, project=project)
    self.componentView = SamplesComponentsView(self, project=project)
    self.componentInfo = componentInfo()

    self.tabWidget.addTab(self.sampleTable, 'Sample Scoring')
    self.tabWidget.addTab(self.componentPL, 'Component Peak List')
    self.tabWidget.addTab(self.componentView, 'Component View')
    self.tabWidget.addTab(self.componentInfo, 'Component info')





class componentInfo(QtGui.QWidget):
  def __init__(self, parent=None):
    super(componentInfo, self).__init__(parent)
    pass