__author__ = 'simon1'

from PyQt4 import QtGui

from ccpn.lib.Assignment import CCP_CODES, getNmrResiduePrediction

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea

from ccpn.lib.Assignment import getNmrResiduePrediction, getNmrAtomPrediction



class NmrResiduePopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(NmrResiduePopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.setStyleSheet("border: 0px solid")
    self.parent = parent
    self.project = project
    self.nmrResidueLabel = Label(self, grid=(0, 0), gridSpan=(1, 2))
    chainLabel = Label(self, "Chain", grid=(1, 0))
    self.chainPulldown = PulldownList(self, grid=(1, 1), callback=self.selectNmrChain)
    nmrChains = [nmrChain.pid for nmrChain in project.nmrChains]
    self.chainPulldown.setData(nmrChains)
    self.seqCodeLabel = Label(self, "Sequence Code: ", grid=(2, 0))
    self.seqCodePulldown = PulldownList(self, grid=(2, 1))
    sequenceCodes = ["%s (%s)" % (nmrResidue.sequenceCode, nmrResidue.residueType)
                     for nmrResidue in project.nmrResidues]
    self.seqCodePulldown.setData(sequenceCodes)


    tentativeLabel = Label(self, "Tentative: ", grid=(3, 0))
    tentativeAssignments = Label(self, grid=(3, 1))
    residueTypeLabel = Label(self, "Residue Type: ", grid=(4, 0))
    self.residueTypePulldown = PulldownList(self, grid=(4, 1), callback=self.setResidueType)
    self.residueTypePulldown.setData(CCP_CODES)
    self.residueTypePulldown.setFixedWidth(100)
    atomTypePulldownLabel = Label(self, "Atom Type", grid=(5, 0))
    self.atomTypePulldown = PulldownList(self, grid=(5, 1), callback=self.setAtomType)
    leftoverLabel = Label(self, "Leftover possibilities: ", grid=(6, 0), vAlign='c')
    self.leftoverPoss = ListWidget(self, grid=(6, 1))
    self.leftoverPoss.setFixedHeight(100)

    self.updatePopup()


  def getResidueTypeProb(self, currentNmrResidue):
    predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0]._wrappedData)
    preds1 = [' '.join([x[0], x[1]]) for x in predictions]
    remainingResidues = [x for x in CCP_CODES if x not in predictions]

    possibilities = preds1+remainingResidues

    self.residueTypePulldown.setData(possibilities)
    selectedResidue = self.residueTypePulldown.currentText().split(' ')[0]
    atomPredictions = getNmrAtomPrediction(selectedResidue, self.project.chemicalShiftLists[0],
                                           self.project._appBase.current.nmrAtom)
    atomPossibilites = [' '.join([x[0][1], x[1]]) for x in atomPredictions]
    self.atomTypePulldown.setData(atomPossibilites)

  def updatePopup(self):
    if self.project._appBase.current.nmrResidue is not None:
      currentNmrResidue = self.project._appBase.current.nmrResidue
      if currentNmrResidue is not None:
        self.nmrResidueLabel.setText("NMR Residue: %s" % currentNmrResidue.id)
        self.chainPulldown.setCurrentIndex(self.chainPulldown.findText(currentNmrResidue.nmrChain.pid))
        sequenceCode = "%s (%s)" % (currentNmrResidue.sequenceCode, currentNmrResidue.residueType)
        self.seqCodePulldown.setCurrentIndex(self.seqCodePulldown.findText(sequenceCode))
        self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.findText(self.getCcpCodeFromNmrResidueName(currentNmrResidue)))
        self.leftoverPoss.clear()
        self.leftoverPoss.addItems(self.getLeftOverResidues(currentNmrResidue))
        self.getResidueTypeProb(currentNmrResidue)

  def selectNmrChain(self, item):
    self.project._appBase.current.nmrChain = self.project.getByPid(item)


  def getCcpCodeFromNmrResidueName(self, currentNmrResidue):
    if currentNmrResidue.residue is not None:
      # print(currentNmrResidue.residue)
      return currentNmrResidue.residueType.capitalize()

  def getLeftOverResidues(self, currentNmrResidue):
    leftovers = []
    for residue in self.project.residues:
      if residue.residueType == self.residueTypePulldown.currentText().upper():
        leftovers.append(residue)
    leftovers.remove(currentNmrResidue.residue)
    return [residue.id for residue in leftovers]

  def setResidueType(self, item):
    currentNmrResidue = self.project._appBase.current.nmrResidue
    # print(item.text().split(' ')[0])
    currentNmrResidue.residueType = item.split(' ')[0].upper()

  def setAtomType(self, item):
    pass
    currentNmrAtom = self.project._appBase.current.nmrAtom
    currentNmrAtom.name = item.split(' ')[0]

