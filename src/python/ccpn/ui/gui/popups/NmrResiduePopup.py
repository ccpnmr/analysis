#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:41 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

from ccpn.core.Chain import Chain
from ccpn.core.lib.AssignmentLib import CCP_CODES,  getNmrResiduePrediction
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger


import sys


class NmrResiduePopup(CcpnDialog):
  def __init__(self, parent=None, mainWindow=None, nmrResidue=None, nmrAtom=None, title='Nmr Residues', **kw):
    """
    Initialise the widget
    """
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.setStyleSheet("border: 0px solid")
    self.parent = parent
    self.nmrAtom = nmrAtom
    self.nmrResidueLabel = Label(self, grid=(0, 0), gridSpan=(1, 1))
    chainLabel = Label(self, "Chain ", grid=(1, 0))
    self.chainPulldown = PulldownList(self, grid=(1, 1), callback=self._selectNmrChain)
    nmrChains = [nmrChain.pid for nmrChain in self.project.nmrChains] + [chain.pid for chain in self.project.chains]
    self.chainPulldown.setData(nmrChains)
    self.seqCodeLabel = Label(self, "Sequence Code ", grid=(1, 2))
    self.seqCodePulldown = PulldownList(self, grid=(1, 3), callback=self._getResidueType)

    residueTypeLabel = Label(self, "Residue Type ", grid=(2, 0))
    self.residueTypePulldown = PulldownList(self, grid=(2, 1))
    self.residueTypePulldown.setData(('',)+CCP_CODES)              # ejb
    self.residueTypePulldown.setFixedWidth(100)

    leftOverLabel = Label(self, "Leftover Possibilities ", grid=(5, 0))
    leftOvers = Label(self, grid=(5, 1))
    closeButton = Button(self, grid=(6, 1), text='Close', callback=self.reject)
    applyButton = Button(self, grid=(6, 2), text='Apply', callback=self._applyChanges)
    okButton = Button(self, grid=(6, 3), text='Ok', callback=self._okButton)

    self._updatePopup(nmrResidue)


  def _getResidueTypeProb(self, currentNmrResidue):
    try:
      self.project.chemicalShiftLists[0]
    except Exception:
      getLogger().warning('No chemicalShiftLists in project.')
      return

    if len(self.project.chemicalShiftLists) > 0:
      predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0])
      preds1 = [' '.join([x[0], x[1]]) for x in predictions if not currentNmrResidue.residueType]
      predictedTypes = [x[0] for x in predictions]
      remainingResidues = [x for x in CCP_CODES if x not in predictedTypes and not currentNmrResidue.residueType]
      possibilities = [currentNmrResidue.residueType]+preds1+remainingResidues
      self.residueTypePulldown.setData(possibilities)

  def _updatePopup(self, nmrResidue):
    if nmrResidue is not None:

      self.nmrResidueLabel.setText("NMR Residue: %s" % nmrResidue.id)
      self.chainPulldown.setCurrentIndex(self.chainPulldown.findText(nmrResidue.nmrChain.pid))
      chain = self.project.getByPid(self.chainPulldown.currentText())
      sequenceCodes = ["%s %s" % (nmrResidue.sequenceCode, nmrResidue.residueType)
                   for nmrResidue in chain.nmrResidues]
      self.seqCodePulldown.setData(sequenceCodes)
      sequenceCode = "%s %s" % (nmrResidue.sequenceCode, nmrResidue.residueType)
      self.seqCodePulldown.setCurrentIndex(self.seqCodePulldown.findText(sequenceCode))
      self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.findText(self._getCcpCodeFromNmrResidueName(nmrResidue)))
      self._getResidueTypeProb(nmrResidue)
      self.nmrResidue = nmrResidue

  def _selectNmrChain(self, item):
    chain = self.project.getByPid(self.chainPulldown.currentText())
    if isinstance(chain, Chain):
      self.seqCodePulldown.setData(["%s %s" % (residue.sequenceCode, residue.residueType)
                     for residue in chain.residues])
    else:
      self.seqCodePulldown.setData(["%s %s" % (nmrResidue.sequenceCode, nmrResidue.residueType)
                     for nmrResidue in chain.nmrResidues])
    self._getResidueType(self.seqCodePulldown.currentText())

  def _getResidueType(self, item):
    try:
      residueType = item.split(' ')[1].capitalize()       # ejb - crash when empty
    except:
      residueType = ''
    for type in self.residueTypePulldown.texts:
      if type.split(' ')[0] == residueType:
        self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.texts.index(type))

  def _getCcpCodeFromNmrResidueName(self, currentNmrResidue):
    if currentNmrResidue.residue is not None:
      return currentNmrResidue.residueType.capitalize()

  def _getLeftOverResidues(self):
    leftovers = []
    for residue in self.project.residues:
      if residue.residueType == self.residueTypePulldown.currentText().upper():
        leftovers.append(residue)
    leftovers.remove(self.nmrResidue.residue)
    return [residue.id for residue in leftovers]

  def _repopulate(self):
    #TODO:ED make sure that this popup is repopulated correctly
    pass

  def _applyChanges(self):
    """
    The apply button has been clicked
    Define an undo block for setting the properties of the object
    If there is an error setting any values then generate an error message
      If anything has been added to the undo queue then remove it with application.undo()
      repopulate the popup widgets
    """
    chain = self.project.getByPid(self.chainPulldown.currentText())

    applyAccept = False
    oldUndo = self.project._undo.numItems()

    self.project._startCommandEchoBlock('_applyChanges')
    try:
      if isinstance(chain, Chain):
        residueItem = self.seqCodePulldown.currentText().split(' ')
        residue = self.project.getByPid('MR:%s.%s.%s' % (chain.shortName, residueItem[0], residueItem[1]))
        self.nmrResidue.residue = residue
      else:
        seqCode = self.seqCodePulldown.currentText().split(' ')[0]
        residueType = self.residueTypePulldown.currentText().split(' ')[0].upper()
        newSeqCode = '.'.join([seqCode, residueType])
        self.nmrResidue.rename(newSeqCode)

      self.nmrResidueLabel.setText("NMR Residue: %s" % self.nmrResidue.id)
      if self.parent:
        if self.parent.name() == 'PEAK ASSIGNER':
          self.parent.emptyAllTablesAndLists()
          self.parent.updateTables()
          self.parent.updateAssignedNmrAtomsListwidgets()
          self.parent.updateWidgetLabels()

      applyAccept = True
    except Exception as es:
      showWarning(str(self.windowTitle()), str(es))
    finally:
      self.project._endCommandEchoBlock()

    if applyAccept is False:
      # should only undo if something new has been added to the undo deque
      # may cause a problem as some things may be set with the same values
      # and still be added to the change list, so only undo if length has changed
      errorName = str(self.__class__.__name__)
      if oldUndo != self.project._undo.numItems():
        self.application.undo()
        getLogger().debug('>>>Undo.%s._applychanges' % errorName)
      else:
        getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

      # repopulate popup
      self._repopulate()
      return False
    else:
      return True

  def _okButton(self):
    if self._applyChanges() is True:
      self.accept()
