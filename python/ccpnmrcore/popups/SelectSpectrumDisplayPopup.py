from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList



class SelectSpectrumDisplayPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(SelectSpectrumDisplayPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    displays = [display.pid for display in project.spectrumDisplays]
    self.project = project
    displays.insert(0, '  ')
    label1a = Label(self, text="Reference modules", grid=(0, 0))
    self.refModulePulldown = PulldownList(self, grid=(1, 0), callback=self.selectRefModule)
    self.refModulePulldown.setData(displays)
    self.refList = ListWidget(self, grid=(2, 0))
    label2a = Label(self, text="Query modules", grid=(0, 1))
    self.queryModulePulldown = PulldownList(self, grid=(1, 1), callback=self.selectQueryModule)
    self.queryModulePulldown.setData(displays)
    self.queryList = ListWidget(self, grid=(2, 1))
    if hasattr(self.parent, 'queryDisplays'):
      self.queryList.addItems(self.parent.queryDisplays)



    label2b = Label(self, text="Match modules", grid=(0, 2))
    self.matchModulePulldown = PulldownList(self, grid=(1, 2), callback=self.selectMatchModule)
    self.matchModulePulldown.addItem('')
    self.matchList = ListWidget(self, grid=(2, 2))
    self.matchModulePulldown.setData(displays)

    if hasattr(self.parent, 'matchDisplays'):
      self.matchList.addItems(self.parent.matchDisplays)

    self.buttonBox = ButtonList(self, grid=(3, 2), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.setSpectrumDisplays])


  def selectRefModule(self, item):
    self.refList.addItem(item)

  def selectQueryModule(self, item):
    self.queryList.addItem(item)

  def selectMatchModule(self, item):
    self.matchList.addItem(item)

  def setSpectrumDisplays(self):
    self.parent.referenceDisplays = [self.refList.item(i).text() for i in range(self.refList.count())]
    self.parent.queryDisplays = [self.queryList.item(i).text() for i in range(self.queryList.count())]
    self.parent.matchDisplays = [self.matchList.item(i).text() for i in range(self.matchList.count())]
    self.accept()