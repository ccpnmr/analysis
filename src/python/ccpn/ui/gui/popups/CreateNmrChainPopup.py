"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2018-02-07 15:28:41 +0000 (Wed, February 02, 2018) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2018-02-07 15:28:41 +0000 (Wed, February 02, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown, ChainPulldown, SELECT, SubstancePulldown, ComplexesPulldown
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Chain import Chain
from ccpn.core.Substance import Substance
from ccpn.core.Complex import Complex
from ccpn.util.Logging import getLogger

CHAIN     = 'Chain'
NMRCHAIN  = 'NmrChain'
SUBSTANCE = 'Substance'
COMPLEX   = 'Complex'

Cancel = 'Cancel'
Create =  'Create'
COPYNMRCHAIN = '-Copy'
CloneOptions = [CHAIN, NMRCHAIN, SUBSTANCE, COMPLEX]


class CreateNmrChainPopup(CcpnDialog):
  def __init__(self, parent=None, mainWindow=None
               , title='Create NmrChain', **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title,size=(200,300),  **kw)

    self.parent = parent
    self.mainWindow = mainWindow
    self.project = None
    if self.mainWindow:
      self.project = self.mainWindow.project


    # GUI
    self.getLayout().setContentsMargins(15, 20, 25, 10)  # L,T,R,B
    vGrid = 0
    self.createNewLabel = Label(self, text="Create New", grid=(vGrid, 0))
    self.createNewWidget = RadioButton(self,
                                           callback=self._selectCreateEmpty,
                                           grid=(vGrid, 1),
                                           )
    vGrid += 1
    self.cloneFromLabel = Label(self, text="Clone from", grid=(vGrid,0))
    self.cloneOptionsWidget = RadioButtons(self, texts=CloneOptions,
                                           callback=self._cloneOptionCallback,
                                           direction='v',
                                           tipTexts=None,
                                           grid=(vGrid, 1),
                                           vAlign='c'
                                           )
    vGrid += 1

    self.availableChainsPD = ChainPulldown(self, self.project,showSelectName=True, callback=self._populateWidgets, labelText='', grid=(vGrid, 1),)
    self.availableChainsPD.label.hide()
    self.availableChainsPD.hide()
    vGrid += 1
    self.availableNmrChainsPD = NmrChainPulldown(self, self.project,showSelectName=True, callback=self._populateWidgets, labelText='', grid=(vGrid, 1))
    self.availableNmrChainsPD.label.hide()
    self.availableNmrChainsPD.hide()
    vGrid += 1
    self.availableComplexesPD = ComplexesPulldown(self, self.project, showSelectName=True,
                                                  callback=self._populateWidgets, labelText='', grid=(vGrid, 1))
    self.availableComplexesPD.label.hide()
    self.availableComplexesPD.hide()
    vGrid += 1
    self.availableSubstancesPD = SubstancePulldown(self, self.project, showSelectName=True,
                                                 callback=self._populateWidgets, labelText='', grid=(vGrid, 1))
    self.availableSubstancesPD.label.hide()
    self.availableSubstancesPD.hide()

    self.pulldownsOptions = {NMRCHAIN:self.availableNmrChainsPD, CHAIN:self.availableChainsPD,
                             SUBSTANCE: self.availableSubstancesPD, COMPLEX:self.availableComplexesPD}

    vGrid += 1
    self.labelName = Label(self, text="Name", grid=(vGrid, 0),  )
    self.nameLineEdit = LineEdit(self, grid=(vGrid, 1), )


    vGrid += 1

    self.spacerLabel = Label(self, text="", grid=(vGrid, 0))
    self.buttonBox = ButtonList(self, texts=[Cancel, Create], callbacks=[self.reject, self._createNmrChain], grid=(vGrid, 1))

    self._resetObjectSelections()
    self._setCreateButtonEnabled(False)
    # self._activateCloneOptions()

  def _resetObjectSelections(self):
    # used to create a new nmrChain from a selected object.
    self._createEmpty = False
    self._chain = None
    self._nmrChain = None
    self._substance = None
    self._complex = None

  def _selectCreateEmpty(self):
    # Gui bit
    self.cloneOptionsWidget.deselectAll()
    if not self.createNewWidget.isChecked():
      self.buttonBox.setButtonEnabled(Create, False)
    else:
      self._setCreateButtonEnabled(True)
    for h in self.pulldownsOptions:
      self.pulldownsOptions[h].hide()

    # FIXME Not an elegant solution
    self._resetObjectSelections()
    self._createEmpty = True

  def _createEmptyNmrChain(self, name):
    if not self.project.getByPid(NmrChain.shortClassName + ':' + name):
      return self.project.newNmrChain(name)
    else:
      showWarning('Existing NmrChain name.', 'Change name')
      return

  def _setCreateButtonEnabled(self, value:bool=True):
    self.buttonBox.setButtonEnabled(Create, value)

  def _cloneFromChain(self, name):
    newNmrChain = self._createEmptyNmrChain(name)
    if newNmrChain:
      try:
        self.project._startCommandEchoBlock('_createNmrChain')
        if len(self._chain.residues) > 0:
          self.project.blankNotification()  # For speed issue: Blank the notifications until the penultimate residue
          for residue in self._chain.residues[:-1]:
            nmrResidue = newNmrChain.newNmrResidue(sequenceCode=residue.sequenceCode, residueType=residue.residueType)
            for atom in residue.atoms:
              nmrResidue.fetchNmrAtom(atom.name)
          self.project.unblankNotification()
          lastResidue = self._chain.residues[-1]
          lastNmrResidue = newNmrChain.newNmrResidue(sequenceCode=lastResidue.sequenceCode,
                                                     residueType=lastResidue.residueType)
          # lastNmrResidue.residue = lastResidue
          for atom in lastResidue.atoms:
            lastNmrResidue.fetchNmrAtom(atom.name)
      finally:
        self.project._endCommandEchoBlock()
      return newNmrChain


  def _cloneFromNmrChain(self, name):
    newNmrChain = self._createEmptyNmrChain(name)
    if newNmrChain:
      try:
        self.project._startCommandEchoBlock('_createNmrChain')
        if len(self._nmrChain.nmrResidues) > 0:
          self.project.blankNotification()  # For speed issue: Blank the notifications until the penultimate residue
          for nmrResidue in self._nmrChain.nmrResidues[:-1]:
            newNmrResidue = newNmrChain.newNmrResidue(sequenceCode=nmrResidue.sequenceCode, residueType=nmrResidue.residueType)
            for nmrAtom in nmrResidue.nmrAtoms:
              newNmrResidue.fetchNmrAtom(nmrAtom.name)
          self.project.unblankNotification()
          lastNmrResidue = self._nmrChain.nmrResidues[-1]
          lastTargetNmrResidue = newNmrChain.newNmrResidue(sequenceCode=lastNmrResidue.sequenceCode,
                                                     residueType=lastNmrResidue.residueType)
          # lastNmrResidue.residue = lastResidue
          for nmrAtom in lastNmrResidue.nmrAtoms:
            lastTargetNmrResidue.fetchNmrAtom(nmrAtom.name)
      finally:
        self.project._endCommandEchoBlock()
      return newNmrChain


  def _createNmrChain(self):
    name = self.nameLineEdit.get()

    if self.project:
      # self.project.blankNotification()
      if self._createEmpty:
        newNmrChain = self._createEmptyNmrChain(name)
        if newNmrChain:
          self.accept()
        else:
          return

      if self._chain:
        newNmrChain = self._cloneFromChain(name)
        if newNmrChain:
          self.accept()
        else:
          return

      if self._nmrChain:
        newNmrChain = self._cloneFromNmrChain(name)
        if newNmrChain:
          self.accept()
        else:
          return

      self.accept()


  def _populateWidgets(self, selected):
    self._resetObjectSelections()
    obj = self.project.getByPid(selected)
    if isinstance(obj, NmrChain):
      self.nameLineEdit.clear()
      self.nameLineEdit.setText(obj.shortName+COPYNMRCHAIN)
      self._nmrChain = obj

    if isinstance(obj, Chain):
      self.nameLineEdit.clear()
      self.nameLineEdit.setText(obj.shortName)
      self._chain = obj

    if isinstance(obj, Substance):
      self.nameLineEdit.clear()
      self.nameLineEdit.setText(obj.name)
      self._substance = obj

    if isinstance(obj, Complex):
      self.nameLineEdit.clear()
      self.nameLineEdit.setText(obj.shortName)
      self._complex = obj


  def _activateCloneOptions(self):
    # if self.availableNmrChainsPD.textList is None:

    # self.newNChainOptionsRButtons.radioButtons[2].setEnabled(False)
    if self.availableChainsPD.textList is None:
      self.cloneOptionsWidget.radioButtons[1].setEnabled(False)

  def _cloneOptionCallback(self):
    self.createNewWidget.setChecked(False)
    self._setCreateButtonEnabled(True)

    selected = self.cloneOptionsWidget.getSelectedText()
    # # needs to clear the previous selection otherwise has an odd behaviour from pulldownNofiers which remember the previous selection
    self._createEmpty = False
    for pd in self.pulldownsOptions:
      self.pulldownsOptions[pd].select(SELECT)
      self._chain = None
    if selected in self.pulldownsOptions:
      self.pulldownsOptions[selected].show()
    hs = [x for x in self.pulldownsOptions if x != selected]
    for h in hs:
      self.pulldownsOptions[h].hide()



if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.ui.gui.widgets.Widget import Widget


    app = TestApplication()
    popup = CreateNmrChainPopup()
    widget = Widget(parent=popup, grid=(0,0))

    popup.show()
    popup.raise_()
    app.start()
