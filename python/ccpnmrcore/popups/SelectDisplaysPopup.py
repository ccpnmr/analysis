__author__ = 'simon1'

from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList



class SelectDisplaysAndSpectraPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, dim=None, **kw):
    super(SelectDisplaysAndSpectraPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    print(self.parent)
    displays = [display.pid for display in project.spectrumDisplays if len(display.orderedAxes) >= dim]
    self.project = project
    displays.insert(0, '  ')
    label1a = Label(self, text="Selected Modules", grid=(0, 0))
    self.displayPulldown = PulldownList(self, grid=(1, 0), callback=self.selectDisplays)
    self.displayPulldown.setData(displays)
    self.displayList = ListWidget(self, grid=(2, 0))
    spectra = [spectrum.pid for spectrum in project.spectra if len(spectrum.axisCodes) >= dim]
    self.project = project
    spectra.insert(0, '  ')
    label1a = Label(self, text="Selected Spectra", grid=(0, 1))
    self.spectrumPulldown = PulldownList(self, grid=(1, 1), callback=self.selectSpectra)
    self.spectrumPulldown.setData(spectra)
    self.spectrumList = ListWidget(self, grid=(2, 1))


    self.buttonBox = ButtonList(self, grid=(3, 1), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.setSpectra])

  def selectDisplays(self, item):
    self.displayList.addItem(item)

  def selectSpectra(self, item):
    self.spectrumList.addItem(item)

  def setSpectra(self):
    self.parent.selectedDisplays = [self.project.getById(self.displayList.item(i).text()) for i in range(self.displayList.count())]
    self.parent.spectra = [self.project.getById(self.spectrumList.item(i).text()) for i in range(self.spectrumList.count())]
    self.accept()