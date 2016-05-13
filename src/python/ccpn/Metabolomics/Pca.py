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


from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Dock import CcpnDock
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpn.ui.gui.base.PlotWidget import PlotWidget

from ccpn.Metabolomics.lib.persistence import MetabolomicsPersistenceDict
from ccpn.Metabolomics.lib.decomposition import PCA

import pyqtgraph as pg


class PcaModule(CcpnDock, Base):

  def __init__(self, project, **kw):

    super(PcaModule, self)
    CcpnDock.__init__(self, name='PCA')
    Base.__init__(self, **kw)
    self.project = project
    self.mDict = MetabolomicsPersistenceDict()

    self.decomposeLabel = Label(self, 'Decompose Method ')

    self.layout.addWidget(self.decomposeLabel, 0, 0, 1, 1)
    self.decomposePulldown = PulldownList(self, grid=(0, 1), gridSpan=(1, 1))
    self.decomposePulldown.setData(['PCA'])
    self.sourceLabel = Label(self, 'Source', grid=(0, 2), gridSpan=(1, 1))
    self.sourcePulldown = PulldownList(self, grid=(0, 3), gridSpan=(1, 1))
    # self.sourcePulldown.setData([group.pid for group in project.spectrumGroups])
    self.sourcePulldown.setData(list(self.mDict['Pipelines'].keys()))

    self.goButton = Button(self, 'GO', grid=(0, 5), gridSpan=(1, 1))
    self.goButton.clicked.connect(self.runPca)

    self.plottingWidget = QtGui.QWidget()
    self.plottingWidgetLayout = QtGui.QGridLayout()
    self.plottingWidget.setLayout(self.plottingWidgetLayout)

    self.layout.addWidget(self.plottingWidget, 1, 0, 4, 6)

    self.scoresPlot = PlotWidget(self, appBase=project._appBase)
    self.scoresPlot.plotItem.axes['left']['item'].show()
    self.scoresPlot.plotItem.axes['right']['item'].hide()
    self.scoresWidget = QtGui.QWidget(self)
    self.scoresWidgetLayout = QtGui.QGridLayout()
    self.scoresWidgetLayout.addWidget(self.scoresPlot, 0, 0, 1, 7)
    self.scoresXLabel = Label(self, 'x ')
    self.scoresXBox = PulldownList(self)
    self.scoresYLabel = Label(self, 'y ')
    self.scoresYBox = PulldownList(self)
    self.scoresColourLabel = Label(self, 'Colour')
    self.scoresColourPulldown = PulldownList(self)
    self.scoresWidgetLayout.addWidget(self.scoresXLabel, 1, 0, 1, 1)
    self.scoresWidgetLayout.addWidget(self.scoresXBox, 1, 2, 1, 1)
    self.scoresWidgetLayout.addWidget(self.scoresYLabel, 1, 3, 1, 1)
    self.scoresWidgetLayout.addWidget(self.scoresYBox, 1, 4, 1, 1)
    self.scoresWidgetLayout.addWidget(self.scoresColourLabel, 1, 5, 1, 1)
    self.scoresWidgetLayout.addWidget(self.scoresColourPulldown, 1, 6, 1, 1)
    self.scoresWidget.setLayout(self.scoresWidgetLayout)
    self.plottingWidget.layout().addWidget(self.scoresWidget, 1, 0, 2, 2)

    self.evPlot = PlotWidget(self, appBase=project._appBase)
    self.evPlot.plotItem.axes['left']['item'].show()
    self.evPlot.plotItem.axes['right']['item'].hide()
    self.evPlotWidgetLayout = QtGui.QGridLayout()
    self.evPlotWidget = QtGui.QWidget(self)
    self.evPlotXLabel = Label(self, 'x ')
    self.evPlotXBox = PulldownList(self)
    self.evPlotXBox.setData([]) # list of text that can be used to call stuff.
    self.evPlotYLabel = Label(self, 'y ')
    self.evPlotYBox = PulldownList(self)
    self.evPlotColourLabel = Label(self, 'Colour')
    self.evPlotColourPulldown = PulldownList(self)
    self.evPlotWidgetLayout.addWidget(self.evPlot, 0, 0, 1, 7)
    self.evPlotWidgetLayout.addWidget(self.evPlotXLabel, 1, 0, 1, 1)
    self.evPlotWidgetLayout.addWidget(self.evPlotXBox, 1, 2, 1, 1)
    self.evPlotWidgetLayout.addWidget(self.evPlotYLabel, 1, 3, 1, 1)
    self.evPlotWidgetLayout.addWidget(self.evPlotYBox, 1, 4, 1, 1)
    self.evPlotWidgetLayout.addWidget(self.evPlotColourLabel, 1, 5, 1, 1)
    self.evPlotWidgetLayout.addWidget(self.evPlotColourPulldown, 1, 6, 1, 1)
    self.evPlotWidget.setLayout(self.evPlotWidgetLayout)
    self.plottingWidget.layout().addWidget(self.evPlotWidget, 1, 2, 2, 2)

  def setSpectrumDisplay(self, spectrumDisplay):
    self.spectrumDisplay = spectrumDisplay

  def runPca(self):
    params = {'method': self.decomposePulldown.currentText(),
              'source': self.sourcePulldown.currentText()}
    preProcessedData = self.mDict['Pipelines'][self.sourcePulldown.currentText()]['output']

    self.pca = PCA(preProcessedData)

    scores = self.pca.scores
    xValues, yValues = 'PC1', 'PC2'
    x = scores[xValues].values
    y = scores[yValues].values
    self.scoresPlot.plot(x, y, pen=None, symbol='o')
    self.scoresYLabel = yValues

    ev = self.pca.explainedVariance
    xValues = list(range(1, 1+len(ev)))
    self.evPlot.plot(xValues, ev, symbol='o')

    if self.spectrum:
      spectrumDisplay = self.createSpectrumDisplay(spectrum=None)
      self.setSpectrumDisplay(spectrumDisplay)
      self.project._appBase.mainWindow.dockArea.moveDock(spectrumDisplay.dock, position='bottom', neighbor=self)
