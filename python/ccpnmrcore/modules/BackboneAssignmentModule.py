"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from PyQt4 import QtGui, QtCore

import pyqtgraph as pg

import math

from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.PeakTable import PeakListSimple

class BackboneAssignmentModule(PeakListSimple):

  def __init__(self, project=None, name=None, peakLists=None, assigner=None, hsqcDisplay=None):
    PeakListSimple.__init__(self, name='Backbone Assignment', peakLists=project.peakLists)
    self.hsqcDisplay = hsqcDisplay
    self.project = project
    self.assigner = assigner
    self.peakTable.callback = self.findMatchingPeaks
    self.layout.setContentsMargins(4, 4, 4, 4)
    spectra = [spectrum.pid for spectrum in project.spectra]
    displays = [display.pid for display in project.spectrumDisplays if len(display.orderedAxes) > 2]
    self.querySpectrumPulldown = PulldownList(self, grid=(5, 1), callback=self.selectQuerySpectrum)
    self.matchSpectrumPulldown = PulldownList(self, grid=(5, 3), callback=self.selectMatchSpectrum)
    self.queryDisplayPulldown = PulldownList(self, grid=(4, 0))
    self.matchDisplayPulldown = PulldownList(self, grid=(4, 2))
    self.querySpectrumPulldown.setData([peakList.pid for peakList in project.peakLists])
    self.matchSpectrumPulldown.setData([peakList.pid for peakList in project.peakLists])
    self.queryDisplayPulldown.setData(displays)
    self.matchDisplayPulldown.setData(displays)
    self.queryLabel = Label(self, text='Query Spectra', grid=(5, 0))
    self.matchLabel = Label(self, text='Match Spectra', grid=(5, 2))
    self.queryList = QtGui.QListWidget(self)
    self.matchList = QtGui.QListWidget(self)
    self.layout.addWidget(self.queryList, 6, 0, 1, 2)
    self.layout.addWidget(self.matchList, 6, 2, 1, 2)


  def findMatchingPeaks(self, peak, row, col):

    ### add GuiNmrResidue to assigner


    ### determine query and match windows
    queryWindow = self.project.getById(self.queryDisplayPulldown.currentText())
    matchWindow = self.project.getById(self.matchDisplayPulldown.currentText())

    positions = peak.position
    self.hsqcDisplay.strips[-1].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))
    self.assigner.addResidue(name=peak.dimensionNmrAtoms[0][0]._parent.id)
    # print(queryWindow.strips[-1].spinSystemLabel.text())
    if self.assigner.direction == 'left':
      queryWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))
      queryWindow.orderedStrips[0].changeZPlane(position=positions[1])
      line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line.setPos(QtCore.QPointF( positions[0], 0))
      queryWindow.orderedStrips[0].plotWidget.addItem(line)
      # queryWindow.strips[-1].spinSystemLabel.update()
      # print(queryWindow.strips[-1].spinSystemLabel.text())
      # position = peak.sortedPeakDims()[1].value
      # position1 = peak.sortedPeakDims()[0].value
    else:
      queryWindow.orderedStrips[-1].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))
      queryWindow.orderedStrips[-1].changeZPlane(position=positions[1])
      line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line.setPos(QtCore.QPointF( positions[0], 0))
      queryWindow.orderedStrips[-1].plotWidget.addItem(line)
    line2 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    line2.setPos(QtCore.QPointF( positions[0], 0))
    line3 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    line3.setPos(QtCore.QPointF(0, positions[1]))
    self.hsqcDisplay.strips[0].plotWidget.addItem(line2)
    self.hsqcDisplay.strips[0].plotWidget.addItem(line3)
    # for index in range(self.queryList.count()):
    #   queryPeakLists.append(self.project.getById(self.queryList.item(index).text()).peakLists[0])
    #
    # for index in range(self.matchList.count()):
    #   matchPeakLists.append(self.project.getById(self.matchList.item(index).text()).peakLists[0])



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

  def qScore(self, query, match):

    math.sqrt(((query-match)**2)/((query+match)**2))


  def buildAssignmentMatrix(self, queryPeaks, matchPeakLists):
    pass







  def selectQuerySpectrum(self, item):
    self.queryList.addItem(item)

  def selectMatchSpectrum(self, item):
    self.matchList.addItem(item)




