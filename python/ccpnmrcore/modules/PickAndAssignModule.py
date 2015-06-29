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

from ccpn.lib.assignment import isInterOnlyExpt

from ccpncore.gui.Button import Button
from ccpncore.gui.DockLabel import DockLabel
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Widget import Widget

from ccpnmrcore.modules.PeakTable import PeakListSimple

from pyqtgraph.dockarea import Dock

class PickAndAssignModule(Dock):

  def __init__(self, parent, project=None):
    Dock.__init__(self, name='Atom Selector')
    self.label.hide()

    self.label = DockLabel('Atom Selector', self)
    self.label.show()
    self.orientation = 'vertical'
    self.moveLabel=False
    pickAndAssignWidget = Widget(self)
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
    self.buttons = [self.hButton1, self.hButton2, self.hButton3, self.nButton1, self.nButton2,
                    self.nButton3, self.caButton1, self.caButton2, self.caButton3, self.cbButton1,
                    self.cbButton2, self.cbButton3]
    for button in self.buttons:
      button.clicked.connect(self.returnButtonToNormal)

    self.addWidget(pickAndAssignWidget)

  def pickAndAssign(self, position, atomType):

    r = self.current.nmrResidue
    name = atomType+position
    newNmrAtom = r.fetchNmrAtom(name=name)
    for peak in self.current.peaks:
      print(newNmrAtom)
      peak.assignDimension(axisCode='C', value=[newNmrAtom])

  def returnButtonToNormal(self):
    for button in self.buttons:
     button.setStyleSheet('background-color: None')


  def predictAssignments(self, peaks):
    experiments = []
    self.current.nmrResidue = peaks[0].dimensionNmrAtoms[0][0]._parent
    values = [peak.height for peak in peaks]
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





