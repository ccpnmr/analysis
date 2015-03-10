__author__ = 'simon'

from PyQt4 import QtGui, QtCore

import pyqtgraph as pg

from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.PeakTable import PeakListSimple

class BackboneAssignmentModule(PeakListSimple):

  def __init__(self, project=None, name=None, peakLists=None, assigner=None):
    PeakListSimple.__init__(self, name='Backbone Assignment', peakLists=project.peakLists)
    self.project = project
    self.assigner = assigner
    print(self.assigner)
    self.peakTable.callback = self.findMatchingPeaks
    self.layout.setContentsMargins(4, 4, 4, 4)
    spectra = [spectrum.pid for spectrum in project.spectra]
    displays = [display.pid for display in project.spectrumDisplays if len(display.orderedAxes) > 2]
    self.querySpectrumPulldown = PulldownList(self, grid=(5, 1), callback=self.selectQuerySpectrum)
    self.matchSpectrumPulldown = PulldownList(self, grid=(5, 3), callback=self.selectMatchSpectrum)
    self.queryDisplayPulldown = PulldownList(self, grid=(4, 0))
    self.matchDisplayPulldown = PulldownList(self, grid=(4, 2))
    self.querySpectrumPulldown.setData(spectra)
    self.matchSpectrumPulldown.setData(spectra)
    self.queryDisplayPulldown.setData(displays)
    self.matchDisplayPulldown.setData(displays)
    self.queryLabel = Label(self, text='Query Spectra', grid=(5, 0))
    self.matchLabel = Label(self, text='Match Spectra', grid=(5, 2))
    self.queryList = QtGui.QListWidget(self)
    self.matchList = QtGui.QListWidget(self)
    self.layout.addWidget(self.queryList, 6, 0, 1, 2)
    self.layout.addWidget(self.matchList, 6, 2, 1, 2)


  def findMatchingPeaks(self, peak, row, col):
    self.assigner.addResidue()
    queryWindow = self.project.getById(self.queryDisplayPulldown.currentText())
    matchWindow = self.project.getById(self.matchDisplayPulldown.currentText())
    position = peak.sortedPeakDims()[1].value
    print(position)
    position1 = peak.sortedPeakDims()[0].value
    queryWindow.strips[-1].changeZPlane(position=position)
    line = pg.InfiniteLine(angle=90, movable=False, pen='w')
    line.setPos(QtCore.QPointF( position1, 0))
    queryWindow.strips[-1].plotWidget.addItem(line)
    queryPeakLists = []
    matchPeakLists = []
    for index in range(self.queryList.count()):
      queryPeakLists.append(self.project.getById(self.queryList.item(index).text()).peakLists[0])
      # ).text()).peakLists[0])
    for index in range(self.matchList.count()):
      matchPeakLists.append(self.project.getById(self.matchList.item(index).text()).peakLists[0])
      # ).text()).peakLists[0])
    queryPeaks = {}


    for peakList in queryPeakLists:

      for peak in peakList.peaks:
        if abs(peak.position[0] - position1) <= 0.02 and abs(peak.position[2] - position) < 0.02:
          queryPeaks.append(peak)
    print(queryPeaks)
    # for peak1, peak2 in zip(queryPeaks, queryPeaks[1:]):
    #   print(abs(peak1.position[1] - peak2.position[1]))
    #     # print(peak1)

    # matchingNHs = []
    # for peakList in matchPeakLists:
    #   for peak2 in peakList.peaks:
    #     for peak in queryPeaks:
    #       if abs(peak2.position[1] - peak.position[1]) < 0.02:
    #         list1 = [peak2.position, peakList]
    #         matchingNHs.append(peak2.position[2])
    #
    # nPositions = set()
    # for x, y in zip(sorted(matchingNHs), sorted(matchingNHs)[1:]):
    #   if abs(x - y) < 0.02:
    #     nPositions.add(x)
    # for position in nPositions:
    #     newStrip = matchWindow.strips[-1].clone()
    #     newStrip.changeZPlane(position=position)








  def selectQuerySpectrum(self, item):
    self.queryList.addItem(item)

  def selectMatchSpectrum(self, item):
    self.matchList.addItem(item)




