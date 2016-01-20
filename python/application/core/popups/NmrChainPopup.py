from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit

class NmrChainPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, nmrChain=None, **kw):
    super(NmrChainPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.nmrChain = nmrChain
    self.nmrChainLabel = Label(self, "NmrChain Name ", grid=(0, 0))
    self.nmrChainText = LineEdit(self, nmrChain.shortName, grid=(0, 1))
    buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self.setNmrChainName], grid=(1, 1))

  def setNmrChainName(self):
    newName = self.nmrChainText.text()
    self.nmrChain.rename(newName)
    self.accept()


