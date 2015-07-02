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


import pyqtgraph as pg

from pyqtgraph.dockarea import Dock

from PyQt4 import QtCore

import math

from ccpncore.gui.Button import Button
from ccpncore.gui.Base import Base
from ccpncore.gui.Label import Label
from ccpncore.gui.Dock import CcpnDockLabel, CcpnDock
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.popups.InterIntraSpectrumPopup import InterIntraSpectrumPopup
from ccpnmrcore.popups.SelectSpectrumDisplayPopup import SelectSpectrumDisplayPopup

class BackboneAssignmentModule(CcpnDock, Base):

  def __init__(self, project=None, name=None, peakLists=None, assigner=None, hsqcDisplay=None, **kw):

    CcpnDock.__init__(self, name='Backbone Assignment')
    # self.label.hide()
    # self.label = DockLabel('Backbone Assignment', self)
    # self.label.show()
    self.displayButton = Button(self, text='Select Modules', callback=self.showDisplayPopup)
    self.spectrumButton = Button(self, text='Select Inter/Intra Spectra', callback=self.showInterIntraPopup)
    self.layout.addWidget(self.displayButton, 0, 0, 1, 1)
    self.layout.addWidget(self.spectrumButton, 0, 2, 1, 1)
    self.hsqcDisplay = hsqcDisplay
    self.project = project
    self.current = project._appBase.current
    self.peakTable = PeakListSimple(self, peakLists=project.peakLists, callback=self.findMatchingPeaks)
    self.layout.addWidget(self.peakTable, 2, 0, 1, 6)

    self.lines = []
    self.numberOfMatches = 5


  def findMatchingPeaks(self, peak=None, row=None, col=None, nmrResidue=None):


    # self.assigner.clearAllItems()
    ### determine query and match windows
    print(self.queryDisplays, self.matchDisplays)
    if peak:
      positions = peak.position
      self.hsqcDisplay.strips[-1].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[0][0]._parent.id))
      self.hsqcDisplay.strips[-1].zoomToRegion([peak.position[0]-0.2, peak.position[0]+0.2,
                                                peak.position[1]-2, peak.position[1]+2])
      line1 = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line2 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line1.setPos(QtCore.QPointF(0, peak.position[1]))
      line2.setPos(QtCore.QPointF(peak.position[0], 0))
      self.hsqcDisplay.strips[-1].viewBox.addItem(line1)
      self.hsqcDisplay.strips[-1].viewBox.addItem(line2)


      for queryDisplay in self.queryDisplays:
        queryWindow = self.project.getById(queryDisplay)
        queryWindow.orderedStrips[0].spinSystemLabel.setText(str(peak.dimensionNmrAtoms[1][0].id))
        queryWindow.orderedStrips[0].changeZPlane(position=positions[1])
        queryWindow.orderedStrips[0].orderedAxes[0].position=positions[0]




        if len(self.lines) == 0:

          line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
          line.setPos(QtCore.QPointF(positions[0], 0))
          queryWindow.orderedStrips[0].plotWidget.addItem(line)

        else:
          self.lines[0].setPos(QtCore.QPointF(positions[0], 0))

      self.current.nmrResidue = self.project.getById(peak.dimensionNmrAtoms[0][0]._parent.pid)

    elif nmrResidue is not None:
      self.current.nmrResidue = nmrResidue

    self.assigner.addResidue(self.current.nmrResidue)

    intraShifts = {}
    interShifts = {}

    for nmrResidue in self.project.nmrResidues:
     intraShifts[nmrResidue] = []
     interShifts[nmrResidue] = []
     for atom in nmrResidue.atoms:
       if atom.name == 'CA':
        intraShifts[nmrResidue].append(self.project.chemicalShiftLists[0].findChemicalShift(atom))

       if atom.name == 'CB':
        intraShifts[nmrResidue].append(self.project.chemicalShiftLists[0].findChemicalShift(atom))

       if atom.name == 'CA-1':
        interShifts[nmrResidue].append(self.project.chemicalShiftLists[0].findChemicalShift(atom))

       if atom.name == 'CB-1':
        interShifts[nmrResidue].append(self.project.chemicalShiftLists[0].findChemicalShift(atom))

    queryShifts = []
    for atom in self.current.nmrResidue.atoms:
      if atom.apiResonance.isotopeCode == '13C':
        if '-1' in atom.name:
          """ go through intra shifts and find matches for CB and CA shifts using hungarian
              output results as strips ordered by 'goodness of match'
          """
          queryShifts.append(self.project.chemicalShiftLists[0].findChemicalShift(atom))

    for queryShift in queryShifts:
      line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line.setPos(QtCore.QPointF(0, queryShift.value))
      for queryDisplay in self.queryDisplays:
        queryWindow = self.project.getById(queryDisplay)
        queryWindow.orderedStrips[0].plotWidget.addItem(line)

    assignMatrix = self.buildAssignmentMatrix(queryShifts, intraShifts)
    assignmentScores = sorted(assignMatrix[1])[0:self.numberOfMatches]
    for assignmentScore in assignmentScores[1:]:
      matchResidue = assignMatrix[0][assignmentScore]
      zAtom = [atom for atom in matchResidue.atoms if atom.apiResonance.isotopeCode == '15N']
      xAtom = [atom for atom in matchResidue.atoms if atom.apiResonance.isotopeCode == '1H']
      yAtoms = [atom for atom in matchResidue.atoms if atom.apiResonance.isotopeCode == '13C' and '-1' not in atom.name]

      zShift = self.project.chemicalShiftLists[0].findChemicalShift(zAtom[0]).value
      xShift = self.project.chemicalShiftLists[0].findChemicalShift(xAtom[0]).value
      yShifts = []
      for atom in yAtoms:
        if atom is not None:
          if self.project.chemicalShiftLists[0].findChemicalShift(atom) is not None:
            yShifts.append(self.project.chemicalShiftLists[0].findChemicalShift(atom).value)
      line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
      line.setPos(QtCore.QPointF(xShift, 0))
      for matchDisplay in self.matchDisplays:
        matchWindow = self.project.getById(matchDisplay)
        newStrip = matchWindow.addStrip()
        newStrip.changeZPlane(position=zShift)
        newStrip.spinSystemLabel.setText(matchResidue.sequenceCode)
        newStrip.plotWidget.addItem(line)
        for shift in yShifts:
          line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
          line.setPos(QtCore.QPointF(0, shift))
          newStrip.plotWidget.addItem(line)

    firstMatchResidue = assignMatrix[0][assignmentScores[0]]
    zAtom = [atom for atom in firstMatchResidue.atoms if atom.apiResonance.isotopeCode == '15N']
    xAtom = [atom for atom in firstMatchResidue.atoms if atom.apiResonance.isotopeCode == '1H']
    yAtoms = [atom for atom in firstMatchResidue.atoms if atom.apiResonance.isotopeCode == '13C' and '-1' not in atom.name]
    zShift = self.project.chemicalShiftLists[0].findChemicalShift(zAtom[0]).value
    xShift = self.project.chemicalShiftLists[0].findChemicalShift(xAtom[0]).value
    yShifts = []
    for atom in yAtoms:
      if self.project.chemicalShiftLists[0].findChemicalShift(atom) is not None:
        yShifts.append(self.project.chemicalShiftLists[0].findChemicalShift(atom).value)

    line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
    line.setPos(QtCore.QPointF(xShift, 0))
    for matchDisplay in self.matchDisplays:
      matchWindow = self.project.getById(matchDisplay)
      matchWindow.orderedStrips[0].changeZPlane(position=zShift)
      matchWindow.orderedStrips[0].spinSystemLabel.setText(firstMatchResidue.sequenceCode)
      matchWindow.orderedStrips[0].plotWidget.addItem(line)
      for shift in yShifts:
        line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', style=QtCore.Qt.DashLine))
        line.setPos(QtCore.QPointF(0, shift))
        matchWindow.orderedStrips[0].plotWidget.addItem(line)


  def setAssigner(self, assigner):
    self.assigner = assigner
    self.project._appBase.current.assigner = assigner

  def qScore(self, query, match):
    if query is not None and match is not None:
      return math.sqrt(((query.value-match.value)**2)/((query.value+match.value)**2))
    else:
      return None

  def buildAssignmentMatrix(self, queryShifts, matchShifts):

    scores = []
    matrix = {}
    for res, shift in matchShifts.items():
      if len(shift) > 1:
        if self.qScore(queryShifts[0], shift[0]) is not None and self.qScore(queryShifts[1], shift[1]) is not None:

          score = (self.qScore(queryShifts[0], shift[0])+self.qScore(queryShifts[1], shift[1]))/2
        # else:
        #   score = None
          scores.append(score)
          matrix[score] = res
      elif len(shift) == 1:
        if self.qScore(queryShifts[0], shift[0]) is not None:

          score = self.qScore(queryShifts[0], shift[0])
        # else:
        #   score = None
          scores.append(score)
          matrix[score] = res

    return matrix, scores

  def showInterIntraPopup(self):
    popup = InterIntraSpectrumPopup(self, project=self.project)
    popup.exec_()

  def showDisplayPopup(self):
    popup = SelectSpectrumDisplayPopup(self, project=self.project)
    popup.exec_()




