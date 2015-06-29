from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList



class SelectSpectrumDisplayPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(SelectSpectrumDisplayPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    displays = [display.pid for display in project.spectrumDisplays if len(display.orderedAxes) > 2]
    self.project = project
    label2a = Label(self, text="Query modules", grid=(0, 0))
    self.queryModulePulldown = PulldownList(self, grid=(1, 0), callback=self.selectQueryModule)
    self.queryModulePulldown.setData(displays)
    self.queryModulePulldown.setCurrentIndex(1)
    self.queryList = ListWidget(self, grid=(2, 0))

    label2b = Label(self, text="Match modules", grid=(0, 1))
    self.matchModulePulldown = PulldownList(self, grid=(1, 1), callback=self.selectMatchModule)
    self.matchList = ListWidget(self, grid=(2, 1))
    self.matchModulePulldown.setData(displays)
    self.matchModulePulldown.setCurrentIndex(1)

  def selectQueryModule(self, item):
    self.queryList.addItem(item)

  def selectMatchModule(self, item):
    self.matchList.addItem(item)