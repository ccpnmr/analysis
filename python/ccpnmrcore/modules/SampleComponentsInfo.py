__author__ = 'luca'


from PyQt4 import QtGui, QtCore
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea

class SampleComponentInfo(QtGui.QWidget):
  def __init__(self, parent=None, project=None):
    super(SampleComponentInfo, self).__init__(parent)

    self.project = project

    labelSelectSample = Label(self, ' Select Sample:', grid=(0, 0), hAlign='r')
    self.SamplePulldown = PulldownList(self, grid=(0, 1), callback=self.pulldownSample)
    self.SamplePulldown.setData([sample.pid for sample in project.samples if len(sample.spectra) > 1])

    labelSelectComponent = Label(self, 'Select Component:', grid=(0, 2), hAlign='r')
    self.componentsPulldown = PulldownList(self, grid=(0, 3))




  def pulldownSample(self, selection):
    for sample in self.project.samples:
      if sample.pid  == selection:
        pLsamples = [sample.pid for sample in sample.spectra]
        self.componentsPulldown.setData(pLsamples)

