__author__ = 'luca'


from pyqtgraph.dockarea import Dock

from ccpncore.gui.Button import Button

from application.core.modules.PeakTable import PeakListSimple

class ScreeningComparisonModule(Dock):

  def __init__(self, project):

    Dock.__init__(self, name='Screening Comparison')

    compareButton = Button(self, text='Compare Peaks...', callback=self.comparePeakLists)
    self.layout.addWidget(compareButton, 0, 2, 1, 1)
    self.peakListA = PeakListSimple(self, peakLists=project.peakLists)
    self.layout.addWidget(self.peakListA, 1, 0)
    self.peakListB = PeakListSimple(self, peakLists=project.peakLists)
    self.layout.addWidget(self.peakListB, 1, 2)

  def comparePeakLists(self):
    print(self.peakListA.peakListPulldown.currentObject())
    print(self.peakListB.peakListPulldown.currentObject())
    for peak in self.peakListA.peakListPulldown.currentObject().peaks:
      print(peak.position)