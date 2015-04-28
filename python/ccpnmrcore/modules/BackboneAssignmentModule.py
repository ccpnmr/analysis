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

from functools import partial

from ccpncore.gui.Button import Button
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Widget import Widget

from ccpnmrcore.modules.PeakTable import PeakListSimple

class BackboneAssignmentModule(PeakListSimple):

  def __init__(self, project=None, name=None, peakLists=None, assigner=None, hsqcDisplay=None):
    PeakListSimple.__init__(self, name='Backbone Assignment', peakLists=project.peakLists, grid=(1, 0), gridSpan=(2, 4))
    self.hsqcDisplay = hsqcDisplay
    self.project = project
    self.current = project._appBase.current
    # self.assigner = assigner
    self.peakTable.callback = self.findMatchingPeaks
    self.layout.setContentsMargins(4, 4, 4, 4)
    spectra = [spectrum.pid for spectrum in project.spectra]
    displays = [display.pid for display in project.spectrumDisplays if len(display.orderedAxes) > 2]
    # self.querySpectrumPulldown = PulldownList(self, grid=(5, 1), callback=self.selectQuerySpectrum)
    # self.matchSpectrumPulldown = PulldownList(self, grid=(5, 3), callback=self.selectMatchSpectrum)
    self.queryDisplayPulldown = PulldownList(self, grid=(4, 0), callback=self.selectQuerySpectrum)
    self.matchDisplayPulldown = PulldownList(self, grid=(4, 2), callback=self.selectMatchSpectrum)
    # self.querySpectrumPulldown.setData([peakList.pid for peakList in project.peakLists])
    # self.matchSpectrumPulldown.setData([peakList.pid for peakList in project.peakLists])
    self.queryDisplayPulldown.setData(displays)
    self.matchDisplayPulldown.setData(displays)
    # self.queryLabel = Label(self, text='Query Spectra', grid=(5, 0))
    # self.matchLabel = Label(self, text='Match Spectra', grid=(5, 2))
    self.queryList = ListWidget(self, grid=(6, 0), gridSpan=(1, 1))
    self.matchList = ListWidget(self, grid=(6, 2), gridSpan=(1, 1))
    # QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self, self.queryList.removeItem)
    self.layout.addWidget(self.queryList, 6, 0, 1, 2)
    self.layout.addWidget(self.matchList, 6, 2, 1, 2)
    # self.numberOfMatches = 7
    self.lines = []

    pickAndAssignWidget = Widget(self, grid=(0, 4), gridSpan=(6, 1))
    headerLabel = Label(self, text='i-1', grid=(0, 0), )
    pickAndAssignWidget.layout().addWidget(headerLabel, 0, 0)
    headerLabel = Label(pickAndAssignWidget, text='i', grid=(0, 1))
    headerLabel = Label(pickAndAssignWidget, text='i+1', grid=(0, 2))
    self.hButton1 = Button(pickAndAssignWidget, text='H', grid=(1, 0), callback=partial(self.pickAndAssign, '-1', 'H'))
    self.hButton2 = Button(pickAndAssignWidget, text='H', grid=(1, 1), callback=partial(self.pickAndAssign, '', 'H'))
    self.hButton3 = Button(pickAndAssignWidget, text='H', grid=(1, 2), callback=partial(self.pickAndAssign, '+1', 'H'))
    self.nButton1 = Button(pickAndAssignWidget, text='N', grid=(2, 0), callback=partial(self.pickAndAssign, '-1', 'N'))
    self.nButton2 = Button(pickAndAssignWidget, text='N', grid=(2, 1), callback=partial(self.pickAndAssign, '', 'N'))
    self.nButton3 = Button(pickAndAssignWidget, text='N', grid=(2, 2), callback=partial(self.pickAndAssign, '+1', 'N'))
    self.caButton1 = Button(pickAndAssignWidget, text='CA', grid=(3, 0), callback=partial(self.pickAndAssign, '-1', 'CA'))
    self.caButton2 = Button(pickAndAssignWidget, text='CA', grid=(3, 1), callback=partial(self.pickAndAssign, '', 'CA'))
    self.caButton3 = Button(pickAndAssignWidget, text='CA', grid=(3, 2), callback=partial(self.pickAndAssign, '+1', 'CA'))
    self.cbButton1 = Button(pickAndAssignWidget, text='CB', grid=(4, 0), callback=partial(self.pickAndAssign, '-1', 'CB'))
    self.cbButton2 = Button(pickAndAssignWidget, text='CB', grid=(4, 1), callback=partial(self.pickAndAssign, '', 'CB'))
    self.cbButton3 = Button(pickAndAssignWidget, text='CB', grid=(4, 2), callback=partial(self.pickAndAssign, '+1', 'CB'))
    self.buttons = [self.hButton1, self.hButton2, self.hButton3, self.nButton1, self.nButton2,
                    self.nButton3, self.caButton1, self.caButton2, self.caButton3, self.cbButton1,
                    self.cbButton2, self.cbButton3]
    for button in self.buttons:
      button.clicked.connect(self.returnButtonToNormal)


  def pickAndAssign(self, position, atomType):

    r = self.current.nmrResidue
    name = atomType+position
    newNmrAtom = r.fetchNmrAtom(name=name)
    for peak in self.current.peaks:
      print(newNmrAtom)
      # if len(peak.dimensionNmrAtoms[1]) > 0:
      peak.dimensionNmrAtoms[1].append(newNmrAtom)
      # else:
      #   peak.dimensionNmrAtoms[1] = [newNmrAtom]


  def returnButtonToNormal(self):
    for button in self.buttons:
    # print(self.sender())
     button.setStyleSheet('background-color: None')



  def predictAssignments(self, peaks):
    values = []
    experiments = []
    self.current.nmrResidue = peaks[0].dimensionNmrAtoms[0][0]._parent
    print(self.current.nmrResidue.atoms)
    for peak in peaks:
      values.append(peak.apiPeak.findFirstPeakIntensity().value)
      experiments.append(peak.peakList.spectrum.experimentName)

    for value in values:
      if value < 0:
        if 'HNcoCA/CB' in experiments:
          self.cbButton1.setStyleSheet('background-color: green')
          self.cbButton2.setStyleSheet('background-color: orange')
        else:
          self.cbButton2.setStyleSheet('background-color: green')
      if value > 0:
        if 'HNcoCA/CB' in experiments or 'HNcoCA' in experiments:
          self.caButton1.setStyleSheet('background-color: green')
          self.caButton2.setStyleSheet('background-color: orange')
        else:
          self.caButton2.setStyleSheet('background-color: green')

        # palette.setColor(QtGui.QColor('orange'))
        # self.cbButton1.setPalette(palette)

  def findMatchingPeaks(self, peak, row, col):


    # self.assigner.clearAllItems()
    ### determine query and match windows
    queryWindows = []
    for index in range(self.queryList.count()):
      queryWindows.append(self.project.getById(self.queryList.item(index).text()))
    matchWindows = []
    for index in range(self.matchList.count()):
      matchWindows.append(self.project.getById(self.matchList.item(index).text()))

    positions = peak.position
    self.hsqcDisplay.strips[-1].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))

    for queryWindow in queryWindows:
      queryWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[1][0].id))
      queryWindow.orderedStrips[0].changeZPlane(position=positions[1])
      queryWindow.orderedStrips[0].orderedAxes[0].position=positions[0]

    # for matchWindow in matchWindows:
    #   matchWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[1][0].id))
    #   matchWindow.orderedStrips[0].changeZPlane(position=positions[1])
    #   matchWindow.orderedStrips[0].orderedAxes[0].position=positions[0]

    if len(self.lines) == 0:

      line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', style=QtCore.Qt.DashLine))
      line.setPos(QtCore.QPointF( positions[0], 0))
      queryWindow.orderedStrips[0].plotWidget.addItem(line)
      # line2 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', style=QtCore.Qt.DashLine))
      # line2.setPos(QtCore.QPointF( positions[1], 0))
      # matchWindow.orderedStrips[0].plotWidget.addItem(line2)
      # self.lines.append(line)
      # self.lines.append(line2)
    else:
      self.lines[0].setPos(QtCore.QPointF(positions[0], 0))
      # self.lines[1].setPos(QtCore.QPointF( positions[1], 0))

    self.current.nmrResidue = self.project.getById(peak.dimensionNmrAtoms[0][0]._parent.pid)

    self.assigner.addResidue(name=peak.dimensionNmrAtoms[0][0]._parent.id)

    intraShifts = {}
    interShifts = {}

    for nmrResidue in self.project.nmrResidues:
     intraShifts[nmrResidue] = []
     interShifts[nmrResidue] = []
     for atom in nmrResidue.atoms:
       if atom.name == 'CA':
        intraShifts[nmrResidue].append(atom)

       if atom.name == 'CB':
        intraShifts[nmrResidue].append(atom)

       if atom.name == 'CA-1':
        interShifts[nmrResidue].append(atom)

       if atom.name == 'CB-1':
        interShifts[nmrResidue].append(atom)

    print(interShifts)
    print(intraShifts)
    for atom in self.current.nmrResidue.atoms:
      if atom.apiResonance.isotopeCode == '13C':
        print(atom.name)
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




  def setAssigner(self, assigner):
    self.assigner = assigner
    self.project._appBase.current.assigner = assigner
    # print(self.assigner)


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




