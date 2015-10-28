from PyQt4 import QtCore, QtGui
from ccpncore.gui.Dock import CcpnDock
from application.core.modules.SampleComponentsTable import PeakListSampleComponent
from application.core.modules.SampleComponentsView import SampleComponentsView
from application.core.modules.SampleComponentsInfo import SampleComponentInfo
from application.core.modules.SampleScoringTable import SampleTableSimple

class SampleAnalysis(CcpnDock):
  ### this class creates a module to analyse the samples. It is composed by four tabs.

  def __init__(self, project, samples=None,):
    super(SampleAnalysis, self)
    CcpnDock.__init__(self, name='Mixtures Analysis')
    self.project = project

    ######## ========   Set Layout  ====== ########
    self.tabWidget = QtGui.QTabWidget()
    self.moduleLayout = QtGui.QGridLayout()
    self.layout.addLayout(self.moduleLayout, 0, 0)
    self.moduleLayout.addWidget(self.tabWidget, 1, 1, 1, 1)
    self.setLayout(self.moduleLayout)


    ######## ========   Set Tabs  ====== ########
    self.sampleTable = SampleTableSimple(self, project=project)
    self.componentPL = PeakListSampleComponent(self, project=project)
    self.componentView = SampleComponentsView(self, project=project)
    self.componentInfo = SampleComponentInfo(self, project=project)

    self.tabWidget.addTab(self.sampleTable, 'Mixtures Scoring')
    self.tabWidget.addTab(self.componentPL, 'Substances Peak List')
    self.tabWidget.addTab(self.componentView, 'Substances View')
    self.tabWidget.addTab(self.componentInfo, 'Mixtures info')



