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

from PyQt4 import QtGui

from collections import OrderedDict

import math

from ccpn import ChemicalShift, NmrResidue

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Button import Button
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.lib.spectrum import Spectrum as spectrumLib
from ccpncore.util import Types

from application.core.modules.NmrResidueTable import NmrResidueTable
from application.core.modules.GuiStrip import GuiStrip

from application.core.lib.Window import navigateToNmrResidue, markPositionsInStrips

class BackboneAssignmentModule(CcpnDock):

  def __init__(self, project):

    super(BackboneAssignmentModule, self).__init__(parent=None, name='Backbone Assignment')

    self.project = project
    self.current = project._appBase.current
    self.numberOfMatches = 5
    self.nmrChains = project.nmrChains
    self.matchModules = []
    self.nmrResidueTable = NmrResidueTable(self, project, callback=self.startAssignment)
    self.displayButton = Button(self.nmrResidueTable, text='Select Match Modules',
                                callback=self._showMatchDisplayPopup, grid=(0, 3))

    self.layout.addWidget(self.nmrResidueTable, 0, 0, 1, 3)


  def startAssignment(self, nmrResidue:NmrResidue, row:int=None, col:int=None):
    """
    Initiates assignment procedure when triggered by selection of an NmrResidue from the nmrResidueTable
    inside the module.
    """
    self._setupShiftDicts()
    if hasattr(self, 'assigner'):
      self.assigner.clearAllItems()
    # self.navigateTo(nmrResidue, row, col)
    self.current.nmrChain = nmrResidue.nmrChain
    if self.current.nmrChain.isConnected:
      nmrResidues = [nmrResidue for nmrResidue in self.current.nmrChain.nmrResidues if not '-1' in nmrResidue.sequenceCode]
      for nmrResidue in nmrResidues:
        self.assigner.addResidue(nmrResidue, '+1')
    self.navigateTo(nmrResidue, row, col)


  def navigateTo(self, nmrResidue:NmrResidue, row:int=None, col:int=None, strip:GuiStrip=None):
    """
    Takes an NmrResidue and an optional GuiStrip and changes z position(s) of all available displays
    to chemical shift value NmrAtoms in the NmrResidue. Creates assignMatrix for strip matching and
    add strips to matchModule(s) corresponding to assignment matches.
    """
    self.project._appBase.mainWindow.clearMarks()

    self.nmrResidueTable.nmrResidueTable.updateTable()
    selectedDisplays = [display for display in self.project.spectrumDisplays if display.pid not in self.matchModules]

    if '-1' in nmrResidue.sequenceCode:
      direction = '-1'
      seqCode = nmrResidue.sequenceCode
      newSeqCode = seqCode.replace('-1', '')
      iNmrResidue = nmrResidue.nmrChain.fetchNmrResidue(sequenceCode=newSeqCode)
      self.current.nmrResidue = iNmrResidue
      # navigateToNmrResidue(self.project, nmrResidue, selectedDisplays=selectedDisplays,
      #                      markPositions=True, strip=strip)
      navigateToNmrResidue(self.project, iNmrResidue, selectedDisplays=selectedDisplays,
                           strip=strip, markPositions=False)

      queryShifts = self.interShifts[nmrResidue]
      matchShifts = self.intraShifts
      for display in selectedDisplays:
        if not strip:
          strip = display.strips[0]
        strip.planeToolbar.spinSystemLabel.setText(iNmrResidue._id)
        shiftDict = {}
        for axis in strip.orderedAxes:
          shiftDict[axis.code] = []
          for atom in nmrResidue.nmrAtoms:
            if atom._apiResonance.isotopeCode == spectrumLib.name2IsotopeCode(axis.code):
              shift = self.project.chemicalShiftLists[0].getChemicalShift(atom.id)
              if shift is not None:
                shiftDict[axis.code].append(shift)
          for atom in iNmrResidue.nmrAtoms:
            if (atom._apiResonance.isotopeCode == spectrumLib.name2IsotopeCode(axis.code) and atom._apiResonance.isotopeCode != '13C'):
              shift = self.project.chemicalShiftLists[0].getChemicalShift(atom.id)
              if shift is not None:
                shiftDict[axis.code].append(shift)
        atomPositions = [shiftDict[axis.code] for axis in strip.orderedAxes]
        markPositionsInStrips(self.project, strip, strip.orderedAxes[:2], atomPositions)

    else:
      direction = '+1'
      iNmrResidue = nmrResidue
      self.current.nmrResidue = iNmrResidue
      navigateToNmrResidue(self.project, iNmrResidue, selectedDisplays=selectedDisplays, markPositions=True, strip=strip)
      queryShifts = self.intraShifts[nmrResidue]
      matchShifts = self.interShifts
      for display in selectedDisplays:
        if not strip:
          display.strips[0].planeToolbar.spinSystemLabel.setText(nmrResidue._id)
        else:
          strip.planeToolbar.spinSystemLabel.setText(nmrResidue._id)


    assignMatrix = self._buildAssignmentMatrix(queryShifts, matchShifts=matchShifts)
    self._createMatchStrips(assignMatrix)
    if hasattr(self, 'assigner'):
      self.assigner.addResidue(iNmrResidue, direction)




  def _setupShiftDicts(self):
    """
    Creates two ordered dictionaries for the inter residue and intra residue CA and CB shifts for
    all NmrResidues in the project.
    """
    self.intraShifts = OrderedDict()
    self.interShifts = OrderedDict()

    for nmrResidue in self.project.nmrResidues:
      nmrAtoms = [nmrAtom.name for nmrAtom in nmrResidue.nmrAtoms]
      shifts = []

        # get inter residue chemical shifts for each -1 nmrResidue

      if 'CA' in nmrAtoms:
        interCa = nmrResidue.fetchNmrAtom(name='CA')
        shift1 = self.project.chemicalShiftLists[0].getChemicalShift(interCa.id)
        shifts.append(shift1)
      if 'CB' in nmrAtoms:
        interCb = nmrResidue.fetchNmrAtom(name='CB')
        shift2 = self.project.chemicalShiftLists[0].getChemicalShift(interCb.id)
        shifts.append(shift2)
      if '-1' in nmrResidue.sequenceCode:
        self.interShifts[nmrResidue] = shifts
      else:
        self.intraShifts[nmrResidue] = shifts



  def _createMatchStrips(self, assignMatrix:Types.Tuple[Types.Dict[NmrResidue, Types.List[ChemicalShift]], Types.List[float]]):
    """
    Creates strips in match module corresponding to the best assignment possibilities in the assignMatrix.
    """
    assignmentScores = sorted(assignMatrix[1])[0:self.numberOfMatches]
    for assignmentScore in assignmentScores[1:]:
      matchResidue = assignMatrix[0][assignmentScore]
      if '-1' in matchResidue.sequenceCode:
        seqCode = matchResidue.sequenceCode
        newSeqCode = seqCode.replace('-1', '')
        iNmrResidue = matchResidue.nmrChain.fetchNmrResidue(sequenceCode=newSeqCode)

      else:
        iNmrResidue = matchResidue

      for matchModule in self.matchModules:
        if len(self.project.getByPid(matchModule).strips) < self.numberOfMatches:
          newStrip = self.project.getByPid(matchModule).addStrip()
          newStrip.planeToolbar.spinSystemLabel.setText(iNmrResidue.sequenceCode)
          navigateToNmrResidue(self.project, iNmrResidue, strip=newStrip)
        else:
          strip = self.project.getByPid(matchModule).orderedStrips[assignmentScores.index(assignmentScore)]
          strip.planeToolbar.spinSystemLabel.setText(iNmrResidue.sequenceCode)
          navigateToNmrResidue(self.project, iNmrResidue, strip=strip)

    firstMatchResidue = assignMatrix[0][assignmentScores[0]]
    if '-1' in firstMatchResidue.sequenceCode:
      seqCode = firstMatchResidue.sequenceCode
      newSeqCode = seqCode.replace('-1', '')
      iNmrResidue = matchResidue.nmrChain.fetchNmrResidue(sequenceCode=newSeqCode)

    else:
      iNmrResidue = firstMatchResidue

    for matchModule in self.matchModules:
      module = self.project.getByPid(matchModule)
      navigateToNmrResidue(self.project, iNmrResidue, strip=module.orderedStrips[0])
      module.orderedStrips[0].planeToolbar.spinSystemLabel.setText(iNmrResidue._id)


  def connectAssigner(self, assigner:CcpnDock):
    """
    Connects Assigner Widget to this module.
    """
    self.assigner = assigner
    self.project._appBase.current.assigner = assigner

  def qScore(self, query, match):
    if query is not None and match is not None:
      return math.sqrt(((query.value-match.value)**2)/((query.value+match.value)**2))
    else:
      return None


  def _buildAssignmentMatrix(self, queryShifts:Types.List[ChemicalShift],
                             matchShifts:Types.Dict[NmrResidue, ChemicalShift]) -> Types.Tuple[Types.Dict[NmrResidue, Types.List[ChemicalShift]], Types.List[float]]:
    """
    Creates a dictionary of NmrResidues and qScores between queryShifts and matching shifts.
    Returns dictionary and a list of the qScores.
    """
    scores = []
    matrix = OrderedDict()
    for res, shift in matchShifts.items():

      if len(queryShifts) > 1 and len(shift) > 1:
        if self.qScore(queryShifts[0], shift[0]) is not None and self.qScore(queryShifts[1], shift[1]) is not None:

          score = (self.qScore(queryShifts[0], shift[0])+self.qScore(queryShifts[1], shift[1]))/2
          scores.append(score)
          matrix[score] = res
      elif len(queryShifts) == 1:
        if self.qScore(queryShifts[0], shift[0]) is not None:

          score = self.qScore(queryShifts[0], shift[0])
          scores.append(score)
          matrix[score] = res

    return matrix, scores

  def _showMatchDisplayPopup(self):
    self.popup = SelectMatchDisplaysPopup(self, project=self.project)
    self.popup.exec_()



class SelectMatchDisplaysPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(SelectMatchDisplaysPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    modules = [display.pid for display in project.spectrumDisplays]
    self.project = project
    modules.insert(0, '  ')
    label1a = Label(self, text="Selected Modules", grid=(0, 0))
    self.modulePulldown = PulldownList(self, grid=(1, 0), callback=self._selectMatchModule)
    self.modulePulldown.setData(modules)
    self.moduleList = ListWidget(self, grid=(2, 0))

    self.buttonBox = ButtonList(self, grid=(3, 0), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self._setMatchModules])

  def _selectMatchModule(self, item):
    self.moduleList.addItem(item)

  def _setMatchModules(self):
    self.parent.matchModules = [self.moduleList.item(i).text() for i in range(self.moduleList.count())]
    self.accept()