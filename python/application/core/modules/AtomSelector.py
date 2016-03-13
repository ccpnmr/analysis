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

from PyQt4 import QtCore

import os

from functools import partial

from ccpn import Peak

from ccpn.lib.Assignment import isInterOnlyExpt, getNmrAtomPrediction, CCP_CODES

from ccpncore.gui.Button import Button
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.RadioButton import RadioButton
from ccpncore.gui.Widget import Widget

from ccpncore.lib.assignment.ChemicalShift import PROTEIN_ATOM_NAMES, ALL_ATOMS_SORTED

from ccpncore.lib.spectrum import Spectrum as spectrumLib

from ccpncore.util import Types

from ccpncore.util import Path

from application.core.gui.assignmentModuleLogic import peaksAreOnLine

class AtomSelector(CcpnDock):
  """
  Module to be used with PickAndAssignModule for prediction of nmrAtom names and assignment of nmrAtoms
  to peak dimensions
  """
  def __init__(self, parent, project=None):
    CcpnDock.__init__(self, name='Atom Selector')
    self.orientation = 'vertical'
    self.moveLabel=False
    self.pickAndAssignWidget = Widget(self)
    # self.pickAndAssignWidget.setMaximumSize(500, 300)
    self.pythonConsole = project._appBase.mainWindow.pythonConsole
    self.parent = parent
    self.current = self.parent._appBase.current
    self.project = project
    self.current.registerNotify(self.predictAssignments, 'peaks')
    self.current.registerNotify(self.predictAssignments, 'peaks')
    nmrResidueLabel = Label(self, 'Current NmrResidue', grid=(0, 0))
    self.currentNmrResidueLabel = Label(self, grid=(0, 1))
    self.radioButton1 = RadioButton(self, grid=(0, 2), hAlign='r', callback=self.createBackBoneButtons)
    self.radioButton1.setChecked(True)
    self.label1 = Label(self, 'Backbone', grid=(0, 3), hAlign='l')
    self.radioButton2 = RadioButton(self, grid=(0, 4), hAlign='r', callback=self.createSideChainButtons)
    # self.radioButton2.setChecked(True)
    self.label2 = Label(self, 'Side chain', grid=(0, 5), hAlign='l')
    self.molTypeLabel = Label(self, 'Molecule Type', grid=(0, 6))
    self.molTypePulldown = PulldownList(self, grid=(0, 7))
    self.molTypePulldown.setData(['protein', 'DNA', 'RNA', 'carbohydrate', 'other'])
    self.layout.addWidget(self.pickAndAssignWidget, 1, 0, 3, 8)
    self.current.registerNotify(self.updateWidget, 'nmrResidues')
    # self.createBackBoneButtons()

    self.buttons = []
    
  def closeDock(self):
    self.current.unRegisterNotify(self.predictAssignments, 'peaks')
    self.current.unRegisterNotify(self.updateWidget, 'nmrResidues')
    self.close()

  def updateWidget(self, nmrResidues=None):
    self.currentNmrResidueLabel.setText(nmrResidues[0].id)
    if self.radioButton1.isChecked():
      self.createBackBoneButtons()
    elif self.radioButton2.isChecked():
      self.createSideChainButtons()
    else:
      return


  def createBackBoneButtons(self):
    self.cleanupPickAndAssignWidget()
    headerLabel = Label(self, text='i-1')
    self.pickAndAssignWidget.layout().addWidget(headerLabel, 0, 0)
    headerLabel2 = Label(self.pickAndAssignWidget, text='i', grid=(0, 1))
    headerLabel3 = Label(self.pickAndAssignWidget, text='i+1', grid=(0, 2))
    self.hButton1 = Button(self.pickAndAssignWidget, text='H', grid=(1, 0), callback=partial(self.pickAndAssign, '-1', 'H'))
    self.hButton2 = Button(self.pickAndAssignWidget, text='H', grid=(1, 1), callback=partial(self.pickAndAssign, '', 'H'))
    self.hButton3 = Button(self.pickAndAssignWidget, text='H', grid=(1, 2), callback=partial(self.pickAndAssign, '+1', 'H'))
    self.nButton1 = Button(self.pickAndAssignWidget, text='N', grid=(2, 0), callback=partial(self.pickAndAssign, '-1', 'N'))
    self.nButton2 = Button(self.pickAndAssignWidget, text='N', grid=(2, 1), callback=partial(self.pickAndAssign, '', 'N'))
    self.nButton3 = Button(self.pickAndAssignWidget, text='N', grid=(2, 2), callback=partial(self.pickAndAssign, '+1', 'N'))
    self.caButton1 = Button(self.pickAndAssignWidget, text='CA', grid=(3, 0), callback=partial(self.pickAndAssign, '-1', 'CA'))
    self.caButton2 = Button(self.pickAndAssignWidget, text='CA', grid=(3, 1), callback=partial(self.pickAndAssign, '', 'CA'))
    self.caButton3 = Button(self.pickAndAssignWidget, text='CA', grid=(3, 2), callback=partial(self.pickAndAssign, '+1', 'CA'))
    self.cbButton1 = Button(self.pickAndAssignWidget, text='CB', grid=(4, 0), callback=partial(self.pickAndAssign, '-1', 'CB'))
    self.cbButton2 = Button(self.pickAndAssignWidget, text='CB', grid=(4, 1), callback=partial(self.pickAndAssign, '', 'CB'))
    self.cbButton3 = Button(self.pickAndAssignWidget, text='CB', grid=(4, 2), callback=partial(self.pickAndAssign, '+1', 'CB'))
    self.coButton1 = Button(self.pickAndAssignWidget, text='CO', grid=(5, 0), callback=partial(self.pickAndAssign, '-1', 'CO'))
    self.coButton2 = Button(self.pickAndAssignWidget, text='CO', grid=(5, 1), callback=partial(self.pickAndAssign, '', 'CO'))
    self.coButton3 = Button(self.pickAndAssignWidget, text='CO', grid=(5, 2), callback=partial(self.pickAndAssign, '+1', 'CO'))
    self.haButton1 = Button(self.pickAndAssignWidget, text='HA', grid=(6, 0), callback=partial(self.pickAndAssign, '-1', 'HA'))
    self.haButton2 = Button(self.pickAndAssignWidget, text='HA', grid=(6, 1), callback=partial(self.pickAndAssign, '', 'HA'))
    self.haButton3 = Button(self.pickAndAssignWidget, text='HA', grid=(6, 2), callback=partial(self.pickAndAssign, '+1', 'HA'))
    self.hbButton1 = Button(self.pickAndAssignWidget, text='HB', grid=(7, 0), callback=partial(self.pickAndAssign, '-1', 'HB'))
    self.hbButton2 = Button(self.pickAndAssignWidget, text='HB', grid=(7, 1), callback=partial(self.pickAndAssign, '', 'HB'))
    self.hbButton3 = Button(self.pickAndAssignWidget, text='HB', grid=(7, 2), callback=partial(self.pickAndAssign, '+1', 'HB'))
    self.returnButton = Button(self.pickAndAssignWidget, text='Clear', grid=(8, 0), gridSpan=(1, 3), callback=self._returnButtonsToNormal)

    self.buttons = [self.hButton1, self.hButton2, self.hButton3, self.nButton1, self.nButton2,
                    self.nButton3, self.caButton1, self.caButton2, self.caButton3, self.cbButton1,
                    self.cbButton2, self.cbButton3, self.coButton1, self.coButton2, self.coButton3,
                    self.haButton1, self.haButton2, self.haButton3, self.hbButton1, self.haButton1,
                    self.hbButton2, self.hbButton3]

    for button in self.buttons:
      button.clicked.connect(self._returnButtonsToNormal)



  def createSideChainButtons(self):
    self.cleanupPickAndAssignWidget()
    self.hCheckBox = CheckBox(self.pickAndAssignWidget, hAlign='r', callback=self.toggleBox)
    self.hCheckBox.setChecked(True)
    self.pickAndAssignWidget.layout().addWidget(self.hCheckBox, 0, 0, QtCore.Qt.AlignRight)
    self.hLabel = Label(self.pickAndAssignWidget, 'H', grid=(0, 1), hAlign='l')
    self.cCheckBox = CheckBox(self.pickAndAssignWidget, grid=(0, 2), hAlign='r', callback=self.toggleBox)
    self.cCheckBox.setChecked(True)
    self.cLabel = Label(self.pickAndAssignWidget, 'C', grid=(0, 3), hAlign='l')
    self.nCheckBox = CheckBox(self.pickAndAssignWidget, grid=(0, 4), hAlign='r', callback=self.toggleBox)
    self.nLabel = Label(self.pickAndAssignWidget, 'N', grid=(0, 5), hAlign='l')
    self.nCheckBox.setChecked(True)
    self.otherCheckBox = CheckBox(self.pickAndAssignWidget, grid=(0, 6), hAlign='r', callback=self.toggleBox)
    self.otherLabel = Label(self.pickAndAssignWidget, 'Other', grid=(0, 7), hAlign='l')

    self.updateLayout()


  def toggleBox(self):
    if self.cCheckBox.isChecked():
      self.updateLayout()
    else:
      self.updateLayout()

  def getAtomsForButtons(self, atomList, atomName):
    [atomList.remove(atom) for atom in sorted(atomList) if atom[0] == atomName]
  def updateLayout(self):

    # group atoms in useful categories based on usage

    alphaAtoms = [x for x in ALL_ATOMS_SORTED['alphas']]
    betaAtoms = [x for x in ALL_ATOMS_SORTED['betas']]
    gammaAtoms = [x for x in ALL_ATOMS_SORTED['gammas']]
    moreGammaAtoms = [x for x in ALL_ATOMS_SORTED['moreGammas']]
    deltaAtoms = [x for x in ALL_ATOMS_SORTED['deltas']]
    moreDeltaAtoms = [x for x in ALL_ATOMS_SORTED['moreDeltas']]
    epsilonAtoms = [x for x in ALL_ATOMS_SORTED['epsilons']]
    moreEpsilonAtoms = [x for x in ALL_ATOMS_SORTED['moreEpsilons']]
    zetaAtoms = [x for x in ALL_ATOMS_SORTED['zetas']]
    etaAtoms = [x for x in ALL_ATOMS_SORTED['etas']]
    moreEtaAtoms = [x for x in ALL_ATOMS_SORTED['moreEtas']]
    atomButtonList = [alphaAtoms, betaAtoms, gammaAtoms, moreGammaAtoms, deltaAtoms, moreDeltaAtoms,
                      epsilonAtoms, moreEpsilonAtoms, zetaAtoms, etaAtoms, moreEtaAtoms]
    # Activate button for Carbons
    if not self.cCheckBox.isChecked():
      [self.getAtomsForButtons(atomList, 'C') for atomList in atomButtonList]

    if not self.hCheckBox.isChecked():
      [self.getAtomsForButtons(atomList, 'H') for atomList in atomButtonList]

    if not self.nCheckBox.isChecked():
      [self.getAtomsForButtons(atomList, 'N') for atomList in atomButtonList]

    rowCount = self.pickAndAssignWidget.layout().rowCount()
    colCount = self.pickAndAssignWidget.layout().columnCount()

    for r in range(1, rowCount):
      for m in range(colCount):
        item = self.pickAndAssignWidget.layout().itemAtPosition(r, m)
        if item:
          if item.widget():
            item.widget().hide()
        self.pickAndAssignWidget.layout().removeItem(item)

    if self.current.nmrResidue:
      self.currentNmrResidueLabel.setText(self.current.nmrResidue.id)
      if self.current.nmrResidue.residueType == '':
        alphaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(1, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(alphaAtoms)]
        betaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(2, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(betaAtoms)]
        [button.setMinimumSize(45, 20) for button in alphaButtons]
        [button.setMinimumSize(45, 20) for button in betaButtons]
        gammaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(3, ii),  hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(gammaAtoms)]
        if len(moreGammaAtoms) > 0:
          moreGammaAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(4, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(moreGammaAtoms)]
          [button.hide() for button in moreGammaAtomButtons]
          moreGammaButton = Button(self.pickAndAssignWidget, text='More...', grid=(3, len(gammaAtoms)), toggle=True)
          moreGammaButton.setChecked(False)
          moreGammaButton.setMinimumSize(45, 20)
          moreGammaButton.toggled.connect(lambda: self.showMoreAtomButtons(moreGammaAtomButtons, moreGammaButton))
          [button.setMinimumSize(45, 20) for button in moreGammaAtomButtons]
        [button.setMinimumSize(45, 20) for button in gammaButtons]

        deltaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(5, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(deltaAtoms)]
        if len(moreDeltaAtoms) > 0:
          moreDeltaAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(6, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(moreDeltaAtoms)]
          [button.hide() for button in moreDeltaAtomButtons]
          moreDeltaButton = Button(self.pickAndAssignWidget, text=' More... ', grid=(5, len(deltaAtoms)), toggle=True)
          moreDeltaButton.setChecked(False)
          moreDeltaButton.toggled.connect(lambda: self.showMoreAtomButtons(moreDeltaAtomButtons, moreDeltaButton))
          moreDeltaButton.setMinimumSize(45, 20)
          [button.setMinimumSize(45, 20) for button in moreDeltaAtomButtons]
        [button.setMinimumSize(45, 20) for button in deltaButtons]


        epsilonButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(7, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(epsilonAtoms)]
        if len(moreEpsilonAtoms) > 0:
          moreEpsilonAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(8, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(moreEpsilonAtoms)]
          [button.hide() for button in moreEpsilonAtomButtons]
          moreEpsilonButton = Button(self.pickAndAssignWidget, text=' More... ', grid=(7, len(epsilonAtoms)), toggle=True)
          moreEpsilonButton.setChecked(False)
          moreEpsilonButton.setMinimumSize(45, 20)
          moreEpsilonButton.toggled.connect(lambda: self.showMoreAtomButtons(moreEpsilonAtomButtons, moreEpsilonButton))
          [button.setMinimumSize(45, 20) for button in moreEpsilonAtomButtons]
        [button.setMinimumSize(45, 20) for button in epsilonButtons]


        zetaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(9, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(zetaAtoms)]
        [button.setMinimumSize(45, 20) for button in zetaButtons]

        etaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(10, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(etaAtoms)]
        if len(moreEtaAtoms) > 0:
          moreEtaAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(11, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(moreEtaAtoms)]
          [button.hide() for button in moreEtaAtomButtons]
          moreEtaButton = Button(self.pickAndAssignWidget, text=' More... ', grid=(10, len(etaAtoms)), toggle=True)
          moreEtaButton.setChecked(False)
          moreEtaButton.setMinimumSize(45, 20)
          moreEtaButton.toggled.connect(lambda: self.showMoreAtomButtons(moreEtaAtomButtons, moreEtaButton))
          [button.setMinimumSize(45, 20) for button in moreEtaAtomButtons]
        [button.setMinimumSize(45, 20) for button in etaButtons]

      else:
        residueType = self.current.nmrResidue.residueType.upper()
        residueAtoms = PROTEIN_ATOM_NAMES[residueType]
        residueAlphas = [atom for atom in alphaAtoms if atom in residueAtoms]
        residueBetas = [atom for atom in betaAtoms if atom in residueAtoms]
        residueGammas = [atom for atom in gammaAtoms if atom in residueAtoms]
        residueMoreGammas = [atom for atom in moreGammaAtoms if atom in residueAtoms]
        residueDeltas = [atom for atom in deltaAtoms if atom in residueAtoms]
        residueMoreDeltas = [atom for atom in moreDeltaAtoms if atom in residueAtoms]
        residueEpsilons = [atom for atom in epsilonAtoms if atom in residueAtoms]
        residueMoreEpsilons = [atom for atom in moreEpsilonAtoms if atom in residueAtoms]
        residueZetas = [atom for atom in zetaAtoms if atom in residueAtoms]
        residueEtas = [atom for atom in etaAtoms if atom in residueAtoms]
        residueMoreEtas = [atom for atom in moreEtaAtoms if atom in residueAtoms]

        alphaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(1, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueAlphas)]
        betaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(2, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueBetas)]
        [button.setMinimumSize(45, 20) for button in alphaButtons]
        [button.setMinimumSize(45, 20) for button in betaButtons]
        if len(residueGammas) + len(residueMoreGammas) < 12:
          combinedGammas = residueGammas+residueMoreGammas
          gammaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(3, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(combinedGammas)]
        else:
          gammaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(3, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueGammas)]
          if len(residueMoreGammas) > 0:
            moreGammaAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(4, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueMoreGammas)]
            [button.hide() for button in moreGammaAtomButtons]
            moreGammaButton = Button(self.pickAndAssignWidget, text='More...', grid=(3, len(residueGammas)), toggle=True)
            moreGammaButton.setChecked(False)
            moreGammaButton.setMinimumSize(45, 20)
            moreGammaButton.toggled.connect(lambda: self.showMoreAtomButtons(moreGammaAtomButtons, moreGammaButton))
            [button.setMinimumSize(45, 20) for button in moreGammaAtomButtons]
        [button.setMinimumSize(45, 20) for button in gammaButtons]
        if len(residueDeltas) + len(residueMoreDeltas) < 12:
          combinedDeltas = residueDeltas+residueMoreDeltas
          deltaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(5, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(combinedDeltas)]
        else:
          deltaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(5, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueDeltas)]
          if len(residueMoreDeltas) > 0:
            moreDeltaAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(6, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueMoreDeltas)]
            [button.hide() for button in moreDeltaAtomButtons]
            moreDeltaButton = Button(self.pickAndAssignWidget, text=' More... ', grid=(5, len(residueDeltas)), toggle=True)
            moreDeltaButton.setChecked(False)
            moreDeltaButton.toggled.connect(lambda: self.showMoreAtomButtons(moreDeltaAtomButtons, moreDeltaButton))
            moreDeltaButton.setMinimumSize(45, 20)
            [button.setMinimumSize(45, 20) for button in moreDeltaAtomButtons]
        [button.setMinimumSize(45, 20) for button in deltaButtons]

        if len(residueEpsilons) + len(residueMoreEpsilons) < 12:
          combinedEpsilons = residueEpsilons+residueMoreEpsilons
          epsilonButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(7, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(combinedEpsilons)]
        else:
          epsilonButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(7, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueEpsilons)]
          if len(residueMoreEpsilons) > 0:
            moreEpsilonAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(8, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueMoreEpsilons)]
            [button.hide() for button in moreEpsilonAtomButtons]
            moreEpsilonButton = Button(self.pickAndAssignWidget, text=' More... ', grid=(7, len(residueEpsilons)), toggle=True)
            moreEpsilonButton.setChecked(False)
            moreEpsilonButton.setMinimumSize(45, 20)
            moreEpsilonButton.toggled.connect(lambda: self.showMoreAtomButtons(moreEpsilonAtomButtons, moreEpsilonButton))
            [button.setMinimumSize(45, 20) for button in moreEpsilonAtomButtons]
        [button.setMinimumSize(45, 20) for button in epsilonButtons]


        zetaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(9, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueZetas)]
        [button.setMinimumSize(45, 20) for button in zetaButtons]


        if len(residueEtas) + len(residueMoreEtas) < 12:
          combinedEtas = residueEpsilons+residueMoreEpsilons
          etaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(10, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(combinedEtas)]
        else:
          etaButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(10, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueEtas)]
          if len(residueMoreEtas) > 0:
            moreEtaAtomButtons = [Button(self.pickAndAssignWidget, text=atom, grid=(11, ii), hAlign='t', callback=partial(self.pickAndAssign, '0', atom)) for ii, atom in enumerate(residueMoreEtas)]
            [button.hide() for button in moreEtaAtomButtons]
            moreEtaButton = Button(self.pickAndAssignWidget, text=' More... ', grid=(10, len(residueEtas)), toggle=True)
            moreEtaButton.setChecked(False)
            moreEtaButton.setMinimumSize(45, 20)
            moreEtaButton.toggled.connect(lambda: self.showMoreAtomButtons(moreEtaAtomButtons, moreEtaButton))
            [button.setMinimumSize(45, 20) for button in moreEtaAtomButtons]
        [button.setMinimumSize(45, 20) for button in etaButtons]


  def showMoreAtomButtons(self, buttons, moreButton):
    if moreButton.isChecked():
      [button.show() for button in buttons]
    else:
      [button.hide() for button in buttons]

  def cleanupPickAndAssignWidget(self):

    layout = self.pickAndAssignWidget.layout()
    for r in range(layout.rowCount()):
      for c in range(layout.columnCount()):
        item = layout.itemAtPosition(r, c)
        if item:
          if item.widget():
            item.widget().hide()
        layout.removeItem(item)


  def pickAndAssign(self, position:int, atomType:str):
    """
    Takes a position either -1, 0 or +1 and an atom type, fetches an NmrAtom with name corresponding
    to the atom type and the position and assigns it to correct dimension of current.peaks
    """
    if not self.current.nmrResidue:
      return
    name = atomType
    if position == '-1' and '-1' not in self.current.nmrResidue.sequenceCode:
      r = self.current.nmrResidue.previousNmrResidue
      if not r:
        r = self.current.nmrResidue.nmrChain.fetchNmrResidue(sequenceCode=self.current.nmrResidue.sequenceCode+'-1')
    else:
      r = self.current.nmrResidue

    newNmrAtom = r.fetchNmrAtom(name=name)
    self.pythonConsole.writeConsoleCommand(
      "nmrAtom = nmrResidue.fetchNmrAtom(name='%s')" % name, nmrResidue=r.pid
    )
    for peak in self.current.peaks:
      for strip in self.project.strips:
        for peakListView in strip.peakListViews:
          if peak in peakListView.peakItems.keys():
            # NBNB TBD FIXME consider using new _displayOrderSpectrumDimensionIndices
            # function to map display axes to spectrum axes
            axisCode = spectrumLib.axisCodeMatch(strip.axisCodes[1], peak.peakList.spectrum.axisCodes)
            index = peak.peakList.spectrum.axisCodes.index(axisCode)
            nmrAtoms = peak.dimensionNmrAtoms[index] + [newNmrAtom]
            peak.assignDimension(axisCode, nmrAtoms)
    self._returnButtonsToNormal()


  def _returnButtonsToNormal(self):
    """
    Returns all buttons in Atom Selector to original colours and style.
    """
    if self.parent._appBase.preferences.general.colourScheme == 'dark':
      styleSheet = open(os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', 'DarkStyleSheet.qss')).read()
      self.setStyleSheet('''DockLabel  {
                                        background-color: #BEC4F3;
                                        color: #122043;
                                        border: 1px solid #00092D;
                                       }''')
      for button in self.buttons:
        button.setStyleSheet(styleSheet)
      self.setStyleSheet(styleSheet)

    elif self.parent._appBase.preferences.general.colourScheme == 'light':
      styleSheet = open(os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', 'LightStyleSheet.qss')).read()
      for button in self.buttons:
        button.setStyleSheet(styleSheet)
      self.setStyleSheet(styleSheet)


  def predictAssignments(self, peaks:Types.List[Peak]):
    """
    Predicts atom type for selected peaks and highlights the relevant buttons with confidence of
    that assignment prediction, green is very confident, orange is less confident.
    """
    self._returnButtonsToNormal()
    if not self.current.nmrResidue or None in peaks:
      return

    else:

      if len(peaks) == 0:
        for button in self.buttons:
          button.clicked.connect(self._returnButtonsToNormal)

      else:

        if peaksAreOnLine(peaks, 1):
          # RHF 15/12/2015 bug fix. From usage elsewhere this ought to use types, not name.
          # NBNB TBD CHECK THIS
          # experiments = [peak.peakList.spectrum.experimentName for peak in peaks]
          types = set(peak.peakList.spectrum.experimentType for peak in peaks)
          anyInterOnlyExperiments = any(isInterOnlyExpt(x) for x in types)

          for peak in peaks:


            isotopeCode = peak.peakList.spectrum.isotopeCodes[1]
            predictedAtomTypes = [getNmrAtomPrediction(ccpCode, peak.position[1], isotopeCode, strict=True) for ccpCode in CCP_CODES]
            refinedPreds = [[type[0][0][1], type[0][1]] for type in predictedAtomTypes if len(type) > 0]
            atomPredictions = set()
            for pred in refinedPreds:
              if pred[1] > 90:
                atomPredictions.add(pred[0])
            for atomPred in atomPredictions:
              if atomPred == 'CB':
                # if(any(isInterOnlyExpt(experiment) for experiment in experiments)):
                if anyInterOnlyExperiments:
                  self.cbButton1.setStyleSheet('background-color: green')
                else:
                  self.cbButton1.setStyleSheet('background-color: orange')
                  self.cbButton2.setStyleSheet('background-color: green')
              if atomPred == 'CA':
                # if(any(isInterOnlyExpt(experiment) for experiment in experiments)):
                if anyInterOnlyExperiments:
                  self.caButton1.setStyleSheet('background-color: green')
                else:
                  self.caButton1.setStyleSheet('background-color: orange')
                  self.caButton2.setStyleSheet('background-color: green')


