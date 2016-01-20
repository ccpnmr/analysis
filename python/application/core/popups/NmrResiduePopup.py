__author__ = 'simon1'

from PyQt4 import QtGui

from ccpn.lib.Assignment import CCP_CODES, ATOM_NAMES
from ccpn import Chain
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea

from ccpn.lib.Assignment import getNmrResiduePrediction, getNmrAtomPrediction



class NmrResiduePopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, nmrResidue=None, nmrAtom=None, **kw):
    super(NmrResiduePopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.setStyleSheet("border: 0px solid")
    self.parent = parent
    self.project = nmrResidue.project
    self.current = self.project._appBase.current
    self.nmrAtom = nmrAtom
    self.nmrResidueLabel = Label(self, grid=(0, 0), gridSpan=(1, 1))
    chainLabel = Label(self, "Chain ", grid=(1, 0))
    self.chainPulldown = PulldownList(self, grid=(1, 1), callback=self.selectNmrChain)
    nmrChains = [nmrChain.pid for nmrChain in self.project.nmrChains] + [chain.pid for chain in self.project.chains]
    self.chainPulldown.setData(nmrChains)
    self.seqCodeLabel = Label(self, "Sequence Code ", grid=(1, 2))
    self.seqCodePulldown = PulldownList(self, grid=(1, 3), callback=self.getResidueType)

    residueTypeLabel = Label(self, "Residue Type ", grid=(2, 0))
    self.residueTypePulldown = PulldownList(self, grid=(2, 1))
    self.residueTypePulldown.setData(CCP_CODES)
    self.residueTypePulldown.setFixedWidth(100)

    # atomTypeLabel = Label(self, "Atom Type ", grid=(2, 2))
    # self.atomTypePulldown = PulldownList(self, grid=(2, 3))

    leftOverLabel = Label(self, "Leftover Possibilities ", grid=(5, 0))
    leftOvers = Label(self, grid=(5, 1))
    applyButton = Button(self, grid=(6, 1), text='Apply', callback=self.assignResidue)



    self.updatePopup(nmrResidue, nmrAtom)


  def getResidueTypeProb(self, currentNmrResidue):
    predictions = getNmrResiduePrediction(currentNmrResidue, self.project.chemicalShiftLists[0])
    preds1 = [' '.join([x[0], x[1]]) for x in predictions if not currentNmrResidue.residueType]
    predictedTypes = [x[0] for x in predictions]
    remainingResidues = [x for x in CCP_CODES if x not in predictedTypes and not currentNmrResidue.residueType]
    print(remainingResidues, predictedTypes)

    possibilities = [currentNmrResidue.residueType]+preds1+remainingResidues

    self.residueTypePulldown.setData(possibilities)


  def updatePopup(self, nmrResidue, nmrAtom):
      if nmrResidue is not None:

        self.nmrResidueLabel.setText("NMR Residue: %s" % nmrResidue.id)
        self.chainPulldown.setCurrentIndex(self.chainPulldown.findText(nmrResidue.nmrChain.pid))
        chain = self.project.getByPid(self.chainPulldown.currentText())
        sequenceCodes = ["%s %s" % (nmrResidue.sequenceCode, nmrResidue.residueType)
                     for nmrResidue in chain.nmrResidues]
        self.seqCodePulldown.setData(sequenceCodes)
        sequenceCode = "%s %s" % (nmrResidue.sequenceCode, nmrResidue.residueType)
        self.seqCodePulldown.setCurrentIndex(self.seqCodePulldown.findText(sequenceCode))
        self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.findText(self.getCcpCodeFromNmrResidueName(nmrResidue)))
        self.getResidueTypeProb(nmrResidue)
        self.nmrResidue = nmrResidue
        self.nmrAtom = nmrAtom

  def selectNmrChain(self, item):
    chain = self.project.getByPid(self.chainPulldown.currentText())
    if isinstance(chain, Chain):
      self.seqCodePulldown.setData(["%s %s" % (residue.sequenceCode, residue.residueType)
                     for residue in chain.residues])
    else:
      self.seqCodePulldown.setData(["%s %s" % (nmrResidue.sequenceCode, nmrResidue.residueType)
                     for nmrResidue in chain.nmrResidues])

    self.getResidueType(self.seqCodePulldown.currentText())

  def getResidueType(self, item):
    residueType = item.split(' ')[1].capitalize()
    for type in self.residueTypePulldown.texts:
      if type.split(' ')[0] == residueType:
        self.residueTypePulldown.setCurrentIndex(self.residueTypePulldown.texts.index(type))

  def getAtomType(self, item):
    if item != '':
      shiftValue = self.project.chemicalShiftLists[0].getChemicalShift(self.nmrAtom.id).value
      residueType =  self.residueTypePulldown.currentText().split(' ')[0]
      atomPredictions = getNmrAtomPrediction(residueType, shiftValue, self.nmrAtom.isotopeCode)
      atomPossibilites = [' '.join([x[0][1], str(x[1])+'%']) for x in atomPredictions]
      remainingAtoms = [x for x in ATOM_NAMES[self.nmrAtom.isotopeCode] if x not in atomPredictions or not self.nmrAtom.name]
      self.atomTypePulldown.setData(atomPossibilites)
      self.atomTypePulldown.addItems(remainingAtoms)


  def getCcpCodeFromNmrResidueName(self, currentNmrResidue):
    if currentNmrResidue.residue is not None:
      return currentNmrResidue.residueType.capitalize()

  def getLeftOverResidues(self):
    leftovers = []
    for residue in self.project.residues:
      if residue.residueType == self.residueTypePulldown.currentText().upper():
        leftovers.append(residue)
    leftovers.remove(self.nmrResidue.residue)
    return [residue.id for residue in leftovers]

  def assignResidue(self):
    chain = self.project.getByPid(self.chainPulldown.currentText())
    if isinstance(chain, Chain):
      residueItem = self.seqCodePulldown.currentText().split(' ')
      residue = self.project.getByPid('MR:%s.%s.%s' % (chain.shortName, residueItem[0], residueItem[1]))
      self.nmrResidue.residue = residue
    else:
      seqCode = self.seqCodePulldown.currentText().split(' ')[0]
      residueType = self.residueTypePulldown.currentText().split(' ')[0].upper()

      newSeqCode = [seqCode, residueType]
      self.nmrResidue.rename(newSeqCode)
    self.nmrResidueLabel.setText("NMR Residue: %s" % self.nmrResidue.id)
    if self.parent.name() == 'ASSIGNMENT MODULE':
      self.parent.emptyAllTablesAndLists()
      self.parent.updateTables()
      self.parent.updateAssignedNmrAtomsListwidgets()
      self.parent.updateWidgetLabels()


  def setAtomType(self, item):

    self.nmrResidue.fetchNmrAtom(name=item.split(' ')[0])

