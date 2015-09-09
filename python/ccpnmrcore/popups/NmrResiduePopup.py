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
    self.residueTypePulldown = PulldownList(self, grid=(4, 1))
    self.residueTypePulldown.setData(CCP_CODES)
    atomTypePulldownLabel = Label(self, "Atom Type", grid=(5, 0))
    atomTypePulldown = PulldownList(self, grid=(5, 1))
    leftoverLabel = Label(self, "Leftover possibilities: ", grid=(6, 0))
    # self.leftoverPoss = Label(self, grid=(6, 1))

    self.update()


  def getResidueTypeProb(self, currentNmrResidue):
    predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0]._wrappedData)
    preds0 = ', '.join([x[0] for x in predictions])
    preds1 = ', '.join([' '.join([x[0], x[1]]) for x in predictions])
    residueCodes = CCP_CODES
    print(preds1)
    for pred in predictions:
      residueCodes.remove(pred[0])

    print(residueCodes)
    # self.typePred.setText(preds1)
    # getNmrAtomPrediction([x[0] for x in predictions], self.project.chemicalShiftLists[0].findChemicalShift(self.project._appBase.current.nmrAtom).value)


  def update(self):
    if self.project._appBase.current.nmrResidue is not None:
      currentNmrResidue = self.project._appBase.current.nmrResidue
      if currentNmrResidue is not None:
        self.nmrResidueLabel.setText("NMR Residue: %s" % currentNmrResidue.id)
        self.chainPulldown.setCurrentIndex(self.chainPulldown.findText(currentNmrResidue.nmrChain.pid))
        sequenceCode = "%s (%s)" % (currentNmrResidue.sequenceCode, currentNmrResidue.residueType)
        self.seqCodePulldown.setCurrentIndex(self.seqCodePulldown.findText(sequenceCode))
        self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.findText(self.getCcpCodeFromNmrResidueName(currentNmrResidue)))
        # self.leftoverPoss.setText(self.getLeftOverResidues(currentNmrResidue))
        self.getResidueTypeProb(currentNmrResidue)

  def selectNmrChain(self, item):
    self.project._appBase.current.nmrChain = self.project.getByPid(item)
    print(self.project._appBase.current.nmrChain)


  def getCcpCodeFromNmrResidueName(self, currentNmrResidue):
    if currentNmrResidue.residue is not None:
      # print(currentNmrResidue.residue)
      return currentNmrResidue.residueType.capitalize()

  def getLeftOverResidues(self, currentNmrResidue):
    leftovers = []
    for residue in self.project.residues:
      if currentNmrResidue.residueType == self.residueTypePulldown.currentText().upper()\
              and residue.id != currentNmrResidue.id:
        leftovers.append(residue.id)
    return ", ".join(leftovers)
