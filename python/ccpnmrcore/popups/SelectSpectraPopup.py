__author__ = 'simon1'



from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList



class SelectSpectraPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, dim=None, **kw):
    super(SelectSpectraPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    spectra = [spectrum.pid for spectrum in project.spectra if len(spectrum.axisCodes) >= dim]
    self.project = project
    spectra.insert(0, '  ')
    label1a = Label(self, text="Selected Spectra", grid=(0, 0))
    self.spectrumPulldown = PulldownList(self, grid=(1, 0), callback=self.selectRefModule)
    self.spectrumPulldown.setData(spectra)
    self.spectrumList = ListWidget(self, grid=(2, 0))

    self.buttonBox = ButtonList(self, grid=(3, 0), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.setSpectra])

  def selectRefModule(self, item):
    self.spectrumList.addItem(item)

  def setSpectra(self):
    self.parent.spectra = [self.spectrumList.item(i).text() for i in range(self.spectrumList.count())]
    self.accept()