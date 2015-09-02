__author__ = 'simon1'

from PyQt4 import QtGui

from ccpn.lib.Assignment import CCP_CODES, ATOM_NAMES

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
    self.parent = parent
    self.project = project
    self.nmrResidueLabel = Label(self, grid=(0, 0))
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
    residueTypeProbLabel = Label(self, "Residue Type Probability", grid=(5, 0))
    self.residueTypeProbs = Label(self, grid=(5, 1))
    leftoverLabel = Label(self, "Leftover possibilities: ", grid=(6, 0))
    self.leftoverPoss = Label(self, grid=(6, 1))
    typePredLabel = Label(self, "Residue Type Predictions: ", grid=(7, 0))
    self.typePred = Label(self, grid=(7, 1))


    nmrAtomButton = Button(self, grid=(8, 1), text="Show Nmr Atoms", callback=self.showNmrAtomPopup)
    self.update()


  def getResidueTypeProb(self, currentNmrResidue):
    predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0]._wrappedData)
    preds0 = ', '.join([x[0] for x in predictions])
    preds1 = ', '.join([' '.join([x[0], x[1]]) for x in predictions])
    print(preds0, 'preds')
    self.residueTypeProbs.setText(preds0)
    self.typePred.setText(preds1)
    getNmrAtomPrediction([x[0] for x in predictions], self.project.chemicalShiftLists[0].findChemicalShift(self.project._appBase.current.nmrAtom).value)


  def update(self):
    if self.project._appBase.current.nmrResidue is not None:
      currentNmrResidue = self.project._appBase.current.nmrResidue
      self.nmrResidueLabel.setText("NMR Residue: %s" % currentNmrResidue.id)
      self.chainPulldown.setCurrentIndex(self.chainPulldown.findText(currentNmrResidue.nmrChain.pid))
      sequenceCode = "%s (%s)" % (currentNmrResidue.sequenceCode, currentNmrResidue.residueType)
      self.seqCodePulldown.setCurrentIndex(self.seqCodePulldown.findText(sequenceCode))
      self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.findText(self.getCcpCodeFromNmrResidueName(currentNmrResidue)))
      self.leftoverPoss.setText(self.getLeftOverResidues(currentNmrResidue))
      self.getResidueTypeProb(currentNmrResidue)

  def selectNmrChain(self, item):
    self.project._appBase.current.nmrChain = self.project.getById(item)
    print(self.project._appBase.current.nmrChain)


  def getCcpCodeFromNmrResidueName(self, currentNmrResidue):
    if currentNmrResidue.residue is not None:
      # print(currentNmrResidue.residue)
      return currentNmrResidue.residueType.capitalize()

  def showNmrAtomPopup(self):
    popup = NmrAtomPopup(self)
    popup.exec_()


  def getLeftOverResidues(self, currentNmrResidue):
    leftovers = []
    for residue in self.project.residues:
      if residue.residueType == self.residueTypePulldown.currentText().upper()\
              and residue.id != currentNmrResidue.id:
        leftovers.append(residue.id)
    return ", ".join(leftovers)


class NmrAtomPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, nmrAtom=None, **kw):
    super(NmrAtomPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    self.project = project
    self = ScrollArea(self, grid=(0, 0))
    nmrAtomLabel = Label(self, grid=(0, 0))
    chainLabel = Label(self, "Atom Name", grid=(1, 0))
    if nmrAtom is not None:
      nmrAtomLabel.setText("NMR Residue: %s" % nmrAtom.sequenceCode)
    self.nmrAtomPulldown = PulldownList(self, grid=(1, 1), callback=self.selectNmrAtom)
    self.nmrAtomPulldown.setData(ATOM_NAMES)
    typePredLabel = Label(self, "Atom Type Predictions: ", grid=(2, 0))
    typePred = Label(self, grid=(2, 1))


  def selectNmrAtom(self):
    pass