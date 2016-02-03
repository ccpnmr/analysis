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

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from application.core.gui.PlotWidget import PlotWidget

class PcaModule(CcpnDock, Base):

  def __init__(self, project, **kw):

    super(PcaModule, self)
    CcpnDock.__init__(self, name='PCA')
    Base.__init__(self, **kw)
    self.project = project

    self.decomposeLabel = Label(self, 'Decompose Method ')

    self.layout.addWidget(self.decomposeLabel, 0, 0, 1, 1)
    self.decomposePulldown = PulldownList(self, grid=(0, 1), gridSpan=(1, 1))
    self.decomposePulldown.setData(['PCA'])
    self.sourceLabel = Label(self, 'Source', grid=(0, 2), gridSpan=(1, 1))
    self.sourcePulldown = PulldownList(self, grid=(0, 3), gridSpan=(1, 1))
    self.sourcePulldown.setData([group.pid for group in project.spectrumGroups])
    self.goButton = Button(self, 'GO', grid=(0, 5), gridSpan=(1, 1))

    self.plottingWidget = QtGui.QWidget()
    self.plottingWidgetLayout = QtGui.QGridLayout()
    self.plottingWidget.setLayout(self.plottingWidgetLayout)

    self.layout.addWidget(self.plottingWidget, 1, 0, 4, 6)

    self.loadingPlot = PlotWidget(self, appBase=project._appBase)
    self.loadingPlot.plotItem.axes['left']['item'].show()
    self.loadingPlot.plotItem.axes['right']['item'].hide()
    self.loadingWidget = QtGui.QWidget(self)
    self.loadingWidgetLayout = QtGui.QGridLayout()
    self.loadingWidgetLayout.addWidget(self.loadingPlot, 0, 0, 1, 7)
    self.loadingXLabel = Label(self, 'x ')
    self.loadingXBox = DoubleSpinbox(self)
    self.loadingYLabel = Label(self, 'y ')
    self.loadingYBox = DoubleSpinbox(self)
    self.loadingColourLabel = Label(self, 'Colour')
    self.loadingColourPulldown = PulldownList(self)
    self.loadingWidgetLayout.addWidget(self.loadingXLabel, 1, 0, 1, 1)
    self.loadingWidgetLayout.addWidget(self.loadingXBox, 1, 2, 1, 1)
    self.loadingWidgetLayout.addWidget(self.loadingYLabel, 1, 3, 1, 1)
    self.loadingWidgetLayout.addWidget(self.loadingYBox, 1, 4, 1, 1)
    self.loadingWidgetLayout.addWidget(self.loadingColourLabel, 1, 5, 1, 1)
    self.loadingWidgetLayout.addWidget(self.loadingColourPulldown, 1, 6, 1, 1)
    self.loadingWidget.setLayout(self.loadingWidgetLayout)
    self.plottingWidget.layout().addWidget(self.loadingWidget, 1, 0, 2, 2)

    self.plot2 = PlotWidget(self, appBase=project._appBase)
    self.plot2.plotItem.axes['left']['item'].show()
    self.plot2.plotItem.axes['right']['item'].hide()
    self.plot2WidgetLayout = QtGui.QGridLayout()
    self.plot2Widget = QtGui.QWidget(self)
    self.plot2XLabel = Label(self, 'x ')
    self.plot2XBox = DoubleSpinbox(self)
    self.plot2YLabel = Label(self, 'y ')
    self.plot2YBox = DoubleSpinbox(self)
    self.plot2ColourLabel = Label(self, 'Colour')
    self.plot2ColourPulldown = PulldownList(self)
    self.plot2WidgetLayout.addWidget(self.plot2, 0, 0, 1, 7)
    self.plot2WidgetLayout.addWidget(self.plot2XLabel, 1, 0, 1, 1)
    self.plot2WidgetLayout.addWidget(self.plot2XBox, 1, 2, 1, 1)
    self.plot2WidgetLayout.addWidget(self.plot2YLabel, 1, 3, 1, 1)
    self.plot2WidgetLayout.addWidget(self.plot2YBox, 1, 4, 1, 1)
    self.plot2WidgetLayout.addWidget(self.plot2ColourLabel, 1, 5, 1, 1)
    self.plot2WidgetLayout.addWidget(self.plot2ColourPulldown, 1, 6, 1, 1)
    self.plot2Widget.setLayout(self.plot2WidgetLayout)
    self.plottingWidget.layout().addWidget(self.plot2Widget, 1, 2, 2, 2)

  def setSpectrumDisplay(self, spectrumDisplay):
    self.spectrumDisplay = spectrumDisplay

  def runPca(self):
    params = {'method': self.decomposePulldown.currentText(),
              'source': self.sourcePulldown.currentText()}


