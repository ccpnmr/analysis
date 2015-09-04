__author__ = 'simon1'


from PyQt4 import QtGui

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Widget import Widget

from ccpnmrcore.gui.Assigner import CCP_CODES
from ccpnmrcore.gui.Frame import Frame



class ResidueInformation(CcpnDock):

  def __init__(self, parent=None, project=None):
    CcpnDock.__init__(self, name='Residue Information')

    chainLabel = Label(self, text='Chain')
    chainPulldown = PulldownList(self, callback=self.setChain)
    chainPulldown.setData([chain.pid for chain in project.chains])
    self.selectedChain = project.getById(chainPulldown.currentText())
    residueLabel = Label(self, text='Residue')
    residuePulldown = PulldownList(self, callback=self.setCurrentResidue)
    residuePulldown.setData(CCP_CODES)
    self.selectedResidueType = residuePulldown.currentText()
    print(self.selectedResidueType, self.selectedChain)
    self.residueWidget= QtGui.QWidget(self)
    self.residueWidget.setLayout(QtGui.QGridLayout())
    self.project = project
    self.layout.addWidget(chainLabel, 0, 0, 1, 1)
    self.layout.addWidget(chainPulldown, 0, 1, 1, 1)
    self.layout.addWidget(residueLabel, 0, 2, 1, 1)
    self.layout.addWidget(residuePulldown, 0, 3, 1, 1)

    self.layout.addWidget(self.residueWidget, 1, 0, 1, 4)
    self.getResidues()



  def setChain(self, value):
    self.selectedChain = self.project.getById(value)
    self.getResidues()


  def setCurrentResidue(self, value):
    print(value)
    self.selectedResidueType = value

    self.getResidues()

  def getResidues(self):

    foundResidues = []
    for residue in self.selectedChain.residues:
      if residue.residueType == self.selectedResidueType.upper():
        foundResidues.append([residue.previousResidue, residue, residue.nextResidue])
    print(foundResidues)
    layout = self.residueWidget.layout()
    for r in range(layout.rowCount()):
      for n in range(3):
        item = layout.itemAtPosition(r, n)
        if item is not None:
          item.widget().deleteLater()

    j = 0
    for i  in range(len(foundResidues)):

      if foundResidues[j+i][0] is not None:
        label1 = Label(self, text=foundResidues[j+i][0].sequenceCode+' '+foundResidues[j+i][0].residueType,
                     hAlign='c')
        label1.setMaximumHeight(20)
        if foundResidues[j+i][0].nmrResidue is not None:
          label1.setStyleSheet('Label {background-color: #f7ffff; color: #2a3358;}')

        self.residueWidget.layout().addWidget(label1, j+i, 0)
      if len(foundResidues[j+1]) > 1:
        label2 = Label(self, text=foundResidues[j+i][1].sequenceCode+' '+foundResidues[j+i][1].residueType,
                       hAlign='c')
        if foundResidues[j+i][1].nmrResidue is not None:
          label2.setStyleSheet('Label {background-color: #f7ffff; color:#2a3358; }')
        label2.setMaximumHeight(30)
        self.residueWidget.layout().addWidget(label2, j+i, 1)
      if len(foundResidues[j+1]) > 2:
        label3 = Label(self, text=foundResidues[j+i][2].sequenceCode+' '+foundResidues[j+i][2].residueType,
                       hAlign='c')
        if foundResidues[j+i][2].nmrResidue is not None:
          label3.setStyleSheet('Label {background-color: #f7ffff; color: #2a3358;}')
        self.residueWidget.layout().addWidget(label3, j+i, 2)
        label3.setMaximumHeight(30)






