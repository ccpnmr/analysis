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
import munkres

from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.PeakTable import PeakListSimple

class BackboneAssignmentModule(PeakListSimple):

  def __init__(self, project=None, name=None, peakLists=None, assigner=None, hsqcDisplay=None):
    PeakListSimple.__init__(self, name='Backbone Assignment', peakLists=project.peakLists)
    self.hsqcDisplay = hsqcDisplay
    self.project = project
    # self.assigner = assigner
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
    self.queryList = ListWidget(self, grid=(6, 0), gridSpan=(1, 2))
    self.matchList = ListWidget(self, grid=(6, 2), gridSpan=(1, 2))
    # QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self, self.queryList.removeItem)
    self.layout.addWidget(self.queryList, 6, 0, 1, 2)
    self.layout.addWidget(self.matchList, 6, 2, 1, 2)
    # self.numberOfMatches = 7
    self.lines = []


  # def setAssigner(self, assigner):
  #   self.assigner = assigner
  #   self.project._appBase.current.assigner = assigner
  #   # print(self.assigner)

  def findMatchingPeaks(self, peak, row, col):


    # self.assigner.clearAllItems()
    ### determine query and match windows
    queryWindow = self.project.getById(self.queryDisplayPulldown.currentText())
    matchWindow = self.project.getById(self.matchDisplayPulldown.currentText())
    positions = peak.position
    self.hsqcDisplay.strips[-1].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))

    queryWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[1][0].id))
    queryWindow.orderedStrips[0].changeZPlane(position=positions[1])
    queryWindow.orderedStrips[0].orderedAxes[0].position=positions[0]

    matchWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0].id))
    matchWindow.orderedStrips[0].changeZPlane(position=positions[0])
    matchWindow.orderedStrips[0].orderedAxes[0].position=positions[1]

    if len(self.lines) == 0:

      line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line.setPos(QtCore.QPointF( positions[0], 0))
      queryWindow.orderedStrips[0].plotWidget.addItem(line)
      line2 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line2.setPos(QtCore.QPointF( positions[1], 0))
      matchWindow.orderedStrips[0].plotWidget.addItem(line2)
      self.lines.append(line)
      self.lines.append(line2)
    else:
      self.lines[0].setPos(QtCore.QPointF( positions[0], 0))
      self.lines[1].setPos(QtCore.QPointF( positions[1], 0))




    # self.assigner.addResidue(name=peak.dimensionNmrAtoms[0][0]._parent.id)
    # if self.assigner.direction == 'left':
    #   queryWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))
    #   queryWindow.orderedStrips[0].changeZPlane(position=positions[1])
    #   line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    #   line.setPos(QtCore.QPointF( positions[0], 0))
    #   queryWindow.orderedStrips[0].plotWidget.addItem(line)
    # currentStrip = self.project._appBase.current.strip
    # if currentStrip is None:
    #   currentStrip = queryWindow.orderedStrips[0]
    # queryWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))

    # line2 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    # line2.setPos(QtCore.QPointF(positions[0], 0))
    # line3 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    # line3.setPos(QtCore.QPointF(0, positions[1]))
    # self.hsqcDisplay.strips[0].plotWidget.addItem(line2)
    # self.hsqcDisplay.strips[0].plotWidget.addItem(line3)
    # queryAtom = self.project.getById(peak.dimensionNmrAtoms[0][0].pid)
    #
    #
    # assignedPeaks = queryAtom.assignedPeaks
    #
    # queryPeaks = []
    #
    # for i in range(self.queryList.count()):
    #
    #   for peak in assignedPeaks[0]:
    #     if peak._parent.pid == self.queryList.item(i).text():
    #       queryPeaks.append(peak)
    #       line2 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    #       line2.setPos(QtCore.QPointF(0, peak.position[1]))
    #       currentStrip.plotWidget.addItem(line2)
    #
    #
    # matchPeakLists = [self.project.getById(self.matchList.item(i).text()) for i in range(self.matchList.count())]
    #
    # assignMatrix = self.buildAssignmentMatrix(queryPeaks, matchPeakLists)
    #
    # indices = self.hungarian(assignMatrix)
    #
    # assignedSet = set()
    # peaksSet = set()
    #
    #
    # for index in indices:
    #   assignedSet.add(matchPeakLists[0].peaks[index[1]].dimensionNmrAtoms[0][0]._parent)
    #   peaksSet.add(matchPeakLists[0].peaks[index[1]].position)
    #
    # assignmentList = list(assignedSet)
    # peaksList = list(peaksSet)
    #
    # matchWindow.strips[0].changeZPlane(position=peaksList[0][2])
    # matchWindow.strips[0].spinSystemLabel.setText(assignmentList[0].id)
    # line4 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    # line5 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    # line6 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    # line4.setPos(pg.Point(QtCore.QPointF(peaksList[0][0], 0)))
    # line5.setPos(pg.Point(QtCore.QPointF(0, peaksList[0][1])))
    # line6.setPos(pg.Point(QtCore.QPointF(0, peaksList[1][1])))
    # matchWindow.strips[0].plotWidget.addItem(line4)
    # matchWindow.strips[0].plotWidget.addItem(line5)
    # matchWindow.strips[0].plotWidget.addItem(line6)





  def qScore(self, query, match):

    return math.sqrt(((query-match)**2)/((query+match)**2))



  def hungarian(self, matrix):
    m = munkres.Munkres()
    indices = m.compute(matrix)
    return indices

  def buildAssignmentMatrix(self, queryPeaks, matchPeakLists):

    matrix = []

    for qPeak in queryPeaks:
      matrix.append([])
      for peakList in matchPeakLists:
        for mPeak in peakList.peaks:
          score = self.qScore(qPeak.position[1], mPeak.position[1])
          matrix[-1].append(score)

    return matrix


  def selectQuerySpectrum(self, item):
    self.queryList.addItem(item)

  def selectMatchSpectrum(self, item):
    self.matchList.addItem(item)




