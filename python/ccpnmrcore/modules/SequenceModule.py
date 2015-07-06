__author__ = 'simon1'


from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from PyQt4 import QtCore, QtGui
import math

class SequenceModule(CcpnDock):

  def __init__(self, name=None, project=None):
    CcpnDock.__init__(self, name='Sequence')
    scrollArea = ScrollArea(None)
    self.addWidget(scrollArea, 0, 0)

    widget = QtGui.QWidget(self)
    for chain in project.chains:
      sequenceToShow = ''.join(self.getSpacedSequence(chain))
      chainLabel = Label(widget, chain.compoundName+': '+sequenceToShow, grid=(0, 0))
      chainLabel.chainCode = chain.compoundName
      chainLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

    scrollArea.setWidget(widget)
    self.hideTitleBar()
    # print(scrollArea.minimumSizeHint())
    self.setMinimumHeight(30)
    # scrollArea.setWidget(sequence1)

  def getSpacedSequence(self, chain):
    residues = [residue.shortName for residue in chain.residues]
    for i in range(len(residues)):
      if i % 10 == 0 and i !=0:
        residues.insert(int(i+i/10)-1, ' ')

    return residues


