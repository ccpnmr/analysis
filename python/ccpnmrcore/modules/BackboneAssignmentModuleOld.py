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

import math

from ccpnmrcore.lib.Window import navigateToNmrResidue, navigateToPeakPosition

from ccpncore.gui.Button import Button
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.popups.InterIntraSpectrumPopup import InterIntraSpectrumPopup
from ccpnmrcore.popups.SelectSpectrumDisplayPopup import SelectSpectrumDisplayPopup

class BackboneAssignmentModule(CcpnDock):

  def __init__(self, project):

    # # CcpnDock.__init__(self, parent=None, name='Backbone Assignment')
    super(BackboneAssignmentModule, self).__init__(parent=None, name='Backbone Assignment')
    spacingLabel = Label(self)
    spacingLabel.setFixedHeight(15)
    self.displayButton = Button(self, text='Select Modules', callback=self.showDisplayPopup)
    self.spectrumButton = Button(self, text='Select Inter/Intra Spectra', callback=self.showInterIntraPopup)

    self.directionPullDown = PulldownList(self, callback=self.selectAssignmentDirection)
    self.layout.addWidget(self.directionPullDown, 1, 4, 1, 1)
    self.directionPullDown.setData(['', 'i-1', 'i+1'])
    # hsqcDisplay = hsqcDisplay
    self.layout.addWidget(spacingLabel, 0, 1, 1, 1)
    self.project = project
    self.current = project._appBase.current

    self.layout.addWidget(spacingLabel, 2, 1, 1, 1)
    self.layout.addWidget(self.displayButton, 1, 0, 1, 1)
    self.layout.addWidget(self.spectrumButton, 1, 2, 1, 1)
    self.peakTable = PeakListSimple(self, project=project, callback=self.navigateTo)
    self.layout.addWidget(self.peakTable, 4, 0, 1, 6)

    self.lines = []
    self.numberOfMatches = 5


  def navigateTo(self, peak=None, row=None, col=None, nmrResidue=None):

    # if selectedDisplays is not None:

    for display in self.referenceDisplays:
      hsqcDisplay = self.project.getByPid(display)
      if peak:
        self.assigner.clearAllItems()
        self.current.nmrResidue = self.project.getByPid(peak.dimensionNmrAtoms[0][0]._parent.pid)
        navigateToPeakPosition(self.project, peak=peak, selectedDisplays=[hsqcDisplay.pid], markPositions=True)


      elif nmrResidue:
        navigateToNmrResidue(self.project, nmrResidue=self.current.nmrResidue,
                           selectedDisplays=[hsqcDisplay.pid], markPositions=True)



      navigateToNmrResidue(self.project, nmrResidue=self.current.nmrResidue,
                           selectedDisplays=self.queryDisplays, markPositions=True)

    self.assigner.addResidue(self.current.nmrResidue)
    assignMatrix = self.getQueryShifts(self.current.nmrResidue)
    self.findMatches(assignMatrix)


  def getQueryShifts(self, currentNmrResidue):
    intraShifts = {}
    interShifts = {}

    for nmrResidue in self.project.nmrResidues:
      intraShifts[nmrResidue] = []
      interShifts[nmrResidue] = []

      if '-1' in nmrResidue.sequenceCode:
        # get inter residue chemical shifts for each -1 nmrResidue
        interCa = nmrResidue.fetchNmrAtom(name='CA')
        interShifts[nmrResidue].append(self.project.chemicalShiftLists[0].getChemicalShift(interCa.id))
        interCb = nmrResidue.fetchNmrAtom(name='CB')
        interShifts[nmrResidue].append(self.project.chemicalShiftLists[0].getChemicalShift(interCb.id))

      if '-1' not in nmrResidue.sequenceCode:
        # get intra residue chemical shifts for each nmrResidue
        intraCa = nmrResidue.fetchNmrAtom(name='CA')
        intraShifts[nmrResidue].append(self.project.chemicalShiftLists[0].getChemicalShift(intraCa.id))
        intraCb = nmrResidue.fetchNmrAtom(name='CB')
        intraShifts[nmrResidue].append(self.project.chemicalShiftLists[0].getChemicalShift(intraCb.id))


    if self.direction == 'i-1':
      seqCode = currentNmrResidue.sequenceCode+'-1'
      queryNmrResidue = currentNmrResidue.nmrChain.fetchNmrResidue(sequenceCode=seqCode)
      queryShifts = interShifts[queryNmrResidue]
      matchShifts=intraShifts

    elif self.direction == 'i+1':
      print(currentNmrResidue)
      queryShifts = intraShifts[currentNmrResidue]
      matchShifts=interShifts


    assignMatrix = self.buildAssignmentMatrix(queryShifts, matchShifts=matchShifts)

    return assignMatrix

  def findMatches(self, assignMatrix):

    assignmentScores = sorted(assignMatrix[1])[0:self.numberOfMatches]
    for assignmentScore in assignmentScores[1:]:
      matchResidue = assignMatrix[0][assignmentScore]
      if self.direction == 'i+1':
        seqCode = matchResidue.sequenceCode.replace('-1', '')
        parentMatchResidue = matchResidue.nmrChain.fetchNmrResidue(sequenceCode=seqCode)
        matchResidue = parentMatchResidue
      else:
        matchResidue = matchResidue
      zAtom = [atom for atom in matchResidue.nmrAtoms if atom._apiResonance.isotopeCode == '15N']
      xAtom = [atom for atom in matchResidue.nmrAtoms if atom._apiResonance.isotopeCode == '1H']

      zShift = self.project.chemicalShiftLists[0].getChemicalShift(zAtom[0].id).value
      xShift = self.project.chemicalShiftLists[0].getChemicalShift(xAtom[0].id).value

      for matchDisplay in self.matchDisplays:
        matchWindow = self.project.getByPid(matchDisplay)
        newStrip = matchWindow.addStrip()
        newStrip.changeZPlane(position=zShift)
        newStrip.planeToolbar.spinSystemLabel.setText(matchResidue.sequenceCode)


    firstMatchResidue = assignMatrix[0][assignmentScores[0]]
    if self.direction == 'i+1':
      seqCode = firstMatchResidue.sequenceCode.replace('-1', '')
      parentMatchResidue = firstMatchResidue.nmrChain.fetchNmrResidue(sequenceCode=seqCode)
      firstMatchResidue = parentMatchResidue

    zAtom = [atom for atom in firstMatchResidue.nmrAtoms if atom._apiResonance.isotopeCode == '15N']
    xAtom = [atom for atom in firstMatchResidue.nmrAtoms if atom._apiResonance.isotopeCode == '1H']
    zShift = self.project.chemicalShiftLists[0].getChemicalShift(zAtom[0].id).value
    xShift = self.project.chemicalShiftLists[0].getChemicalShift(xAtom[0].id).value


    for matchDisplay in self.matchDisplays:
      matchWindow = self.project.getByPid(matchDisplay)
      matchWindow.orderedStrips[0].changeZPlane(position=zShift)
      matchWindow.orderedStrips[0].planeToolbar.spinSystemLabel.setText(firstMatchResidue.sequenceCode)


  def setAssigner(self, assigner):
    self.assigner = assigner
    self.project._appBase.current.assigner = assigner

  def qScore(self, query, match):
    if query is not None and match is not None:
      return math.sqrt(((query.value-match.value)**2)/((query.value+match.value)**2))
    else:
      return None

  def selectAssignmentDirection(self, value):
    if value == 'i-1':
      self.assigner.direction = 'left'
      self.direction = 'i-1'

    elif value == 'i+1':
      self.assigner.direction = 'right'
      self.direction = 'i+1'


  def buildAssignmentMatrix(self, queryShifts, matchShifts):

    scores = []
    matrix = {}
    for res, shift in matchShifts.items():
      if len(shift) > 1:
        if self.qScore(queryShifts[0], shift[0]) is not None and self.qScore(queryShifts[1], shift[1]) is not None:

          score = (self.qScore(queryShifts[0], shift[0])+self.qScore(queryShifts[1], shift[1]))/2
          scores.append(score)
          matrix[score] = res
      elif len(shift) == 1:
        if self.qScore(queryShifts[0], shift[0]) is not None:

          score = self.qScore(queryShifts[0], shift[0])
          scores.append(score)
          matrix[score] = res

    return matrix, scores
  #
  def showInterIntraPopup(self):
    popup = InterIntraSpectrumPopup(self, project=self.project)
    popup.exec_()

  def showDisplayPopup(self):
    popup = SelectSpectrumDisplayPopup(self, project=self.project)
    popup.exec_()




