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

import os

from functools import partial

from ccpn.lib.Assignment import isInterOnlyExpt

from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.Widget import Widget

from ccpncore.util import Path

from ccpnmrcore.gui.assignmentModuleLogic import getAxisCodeForPeakDimension, getIsotopeCodeForPeakDimension

class AtomSelector(CcpnDock):

  def __init__(self, parent, project=None):
    CcpnDock.__init__(self, name='Atom Selector')
    self.orientation = 'vertical'
    self.moveLabel=False
    pickAndAssignWidget = Widget(self)#
    pickAndAssignWidget.setMaximumSize(500, 300)

    headerLabel = Label(self, text='i-1')
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
    self.coButton1 = Button(pickAndAssignWidget, text='CO', grid=(5, 0), callback=partial(self.pickAndAssign, '-1', 'CO'))
    self.coButton2 = Button(pickAndAssignWidget, text='CO', grid=(5, 1), callback=partial(self.pickAndAssign, '', 'CO'))
    self.coButton3 = Button(pickAndAssignWidget, text='CO', grid=(5, 2), callback=partial(self.pickAndAssign, '+1', 'CO'))
    self.buttons = [self.hButton1, self.hButton2, self.hButton3, self.nButton1, self.nButton2,
                    self.nButton3, self.caButton1, self.caButton2, self.caButton3, self.cbButton1,
                    self.cbButton2, self.cbButton3, self.coButton1, self.coButton2, self.coButton3]
    self.parent = parent
    self.current = self.parent._appBase.current
    self.project = project
    self.project._appBase.current.registerNotify(self.predictAssignments, 'peaks')
    for button in self.buttons:
      button.clicked.connect(self.returnButtonToNormal)

    self.addWidget(pickAndAssignWidget)

  def pickAndAssign(self, position, atomType):

    name = atomType
    if position == '-1' and '-1' not in self.current.nmrResidue.sequenceCode:
      r = self.current.nmrResidue.nmrChain.fetchNmrResidue(sequenceCode=self.current.nmrResidue.sequenceCode+'-1')
    else:
      r = self.current.nmrResidue

    if self.current.nmrResidue is None:
      r = self.current.peaks[0].dimensionNmrAtoms[0][0].nmrResidue

    newNmrAtom = r.fetchNmrAtom(name=name)
    for peak in self.current.peaks:
      for dim in range(len(peak.dimensionNmrAtoms)):
        isotopeCode = getIsotopeCodeForPeakDimension(peak, dim)
        if newNmrAtom._apiResonance.isotopeCode == isotopeCode:
          axisCode = getAxisCodeForPeakDimension(peak, dim)
          self.assignPeakDimension(peak, dim, axisCode, newNmrAtom)
      else:
          pass
    self.returnButtonToNormal()


  def returnButtonToNormal(self):
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


  def predictAssignments(self, current):

    print(current.peaks)

    if len(current.peaks) == 0:
      print(len(current.peaks))
      for button in self.buttons:
        button.clicked.connect(self.returnButtonToNormal)

    else:
      peaks = current.peaks

      experiments = []
      try:
        self.current.nmrResidue = peaks[0].dimensionNmrAtoms[0][0]._parent

      except IndexError:
        self.current.nmrResidue = self.project.nmrChains[0].newNmrResidue()
      values = [peak.height for peak in peaks]
      print(values)
      experiments = [peak.peakList.spectrum.experimentName for peak in peaks]
      for value in values:
        if value < 0:
          if(any(isInterOnlyExpt(experiment) for experiment in experiments)):
            self.cbButton1.setStyleSheet('background-color: green')
            self.cbButton2.setStyleSheet('background-color: orange')
          else:
            self.cbButton2.setStyleSheet('background-color: green')
        if value > 0:
          if(any(isInterOnlyExpt(experiment) for experiment in experiments)):
            self.caButton1.setStyleSheet('background-color: green')
            self.caButton2.setStyleSheet('background-color: orange')
          else:
            self.caButton2.setStyleSheet('background-color: green')




  def assignPeakDimension(self, peak, dim, axisCode, nmrAtom):
    axisCode = getAxisCodeForPeakDimension(peak, dim)
    peak.assignDimension(axisCode=axisCode, value=[nmrAtom])
    shiftList = peak.peakList.spectrum.chemicalShiftList
    shiftList.newChemicalShift(value=peak.position[dim], nmrAtom=nmrAtom)



