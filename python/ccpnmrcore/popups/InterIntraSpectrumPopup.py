from PyQt4 import QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList

from ccpn.lib.assignment import isInterOnlyExpt


class InterIntraSpectrumPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(InterIntraSpectrumPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.project = project
    label2a = Label(self, text="Inter-residue spectra", grid=(0, 0))
    self.interList = ListWidget(self, grid=(2, 0))
    self.interSpectrumPulldown = PulldownList(self, grid=(1, 0), callback=self.selectInterSpectrum)
    self.interSpectrumPulldown.setData(self.getInterExpts()[0])


    label2b = Label(self, text="Intra-residue spectra", grid=(0, 1))
    self.intraList = ListWidget(self, grid=(2, 1))
    self.intraSpectrumPulldown = PulldownList(self, grid=(1, 1), callback=self.selectIntraSpectrum)

    self.intraSpectrumPulldown.setData(self.getInterExpts()[1])
    self.buttonBox = ButtonList(self, grid=(3, 1), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.setInterIntraSpectra])

  def selectInterSpectrum(self, item):
    self.interList.addItem(item)

  def selectIntraSpectrum(self, item):
    self.intraList.addItem(item)

  def getInterExpts(self):
    interExpts = []
    intraExpts = []
    for spectrum in self.project.spectra:
      if spectrum.dimensionCount > 2:
        if isInterOnlyExpt(spectrum.experimentType):
          interExpts.append(spectrum.pid)
        else:
          intraExpts.append(spectrum.pid)
    return intraExpts, interExpts

  def setInterIntraSpectra(self):
    self.parent().intraSpectra = [self.interList.item(i).text() for i in range(self.interList.count())]
    self.parent().interSpectra = [self.intraList.item(i).text() for i in range(self.intraList.count())]
    self.accept()