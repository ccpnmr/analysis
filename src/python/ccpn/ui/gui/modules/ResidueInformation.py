__author__ = 'simon1'

from PyQt4 import QtGui

from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList


class ResidueInformation(CcpnModule, Base):

  def __init__(self, parent=None, project=None, **kw):
    CcpnModule.__init__(self, name='Residue Information')
    Base.__init__(self, **kw)

    chainLabel = Label(self, text='Chain')
    self.layout.addWidget(chainLabel, 0, 0)
    chainPulldown = PulldownList(self, callback=self._setChain, grid=(0, 1))
    chainPulldownData = [chain.pid for chain in project.chains]
    chainPulldownData.append('<All>')
    chainPulldown.setData(chainPulldownData)
    self.selectedChain = project.getByPid(chainPulldown.currentText())
    residueLabel = Label(self, text='Residue ', grid=(0, 3))
    self.colourScheme = project._appBase.colourScheme
    residuePulldown = PulldownList(self, callback=self._setCurrentResidue, grid=(0, 4))
    residuePulldown.setData(CCP_CODES)
    self.selectedResidueType = residuePulldown.currentText()
    self.residueWidget = QtGui.QWidget(self)
    self.residueWidget.setLayout(QtGui.QGridLayout())
    self.project = project
    self.layout.addWidget(self.residueWidget, 1, 0, 1, 5)
    self._getResidues()



  def _setChain(self, value:str):
    """
    Sets the selected chain to the specified value and updates the module.
    """
    if value == '<All>':
      self.selectedChain = 'All'
    else:
      self.selectedChain = self.project.getByPid(value)
    self._getResidues()


  def _setCurrentResidue(self, value:str):
    """
    Sets the selected residue to the specified value and updates the module.
    """
    self.selectedResidueType = value
    self._getResidues()

  def _getResidues(self):
    """
    Finds all residues of the selected type along with one flanking residue either side and displays
    this information in the module.
    """
    if self.colourScheme == 'dark':
      stylesheet = 'Label {background-color: #f7ffff; color: #2a3358;}'
    elif self.colourScheme == 'light':
      stylesheet = 'Label {background-color: #bd8413; color: #fdfdfc;}'
    foundResidues = []
    if self.selectedChain == 'All':
      residues = self.project.residues
    else:
      residues = self.selectedChain.residues
    for residue in residues:
      if residue.residueType == self.selectedResidueType.upper():
        foundResidues.append([residue.previousResidue, residue, residue.nextResidue])
    layout = self.residueWidget.layout()
    for r in range(layout.rowCount()):
      for n in range(3):
        item = layout.itemAtPosition(r, n)
        if item is not None:
          item.widget().deleteLater()

    j = 0  # why was this introduced (it's not altered below)?
    for i in range(len(foundResidues)):

      if foundResidues[j+i][0] is not None:
        label1 = Label(self, text=foundResidues[j+i][0].id,
                     hAlign='c')
        label1.setMaximumHeight(30)
        if foundResidues[j+i][0].nmrResidue is not None:
          label1.setStyleSheet(stylesheet)

        self.residueWidget.layout().addWidget(label1, j+i, 0)
      if len(foundResidues[j+i]) > 1:
        label2 = Label(self, text=foundResidues[j+i][1].id,
                       hAlign='c')
        if foundResidues[j+i][1].nmrResidue is not None:
          label2.setStyleSheet(stylesheet)
        label2.setMaximumHeight(30)
        self.residueWidget.layout().addWidget(label2, j+i, 1)
      if len(foundResidues[j+i]) > 2:
        label3 = Label(self, text=foundResidues[j+i][2].id,
                       hAlign='c')
        if foundResidues[j+i][2].nmrResidue is not None:
          label3.setStyleSheet(stylesheet)
        self.residueWidget.layout().addWidget(label3, j+i, 2)
        label3.setMaximumHeight(30)
