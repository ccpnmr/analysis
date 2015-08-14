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
    self.parent = parent

    label2a = Label(self, text="Reference spectra", grid=(0, 0))

    self.refSpectrumPulldown = PulldownList(self, grid=(1, 0), callback=self.selectRefSpectrum)
    self.refSpectrumPulldown.addItem('')
    spectra = [spectrum.pid for spectrum in project.spectra]
    spectra.insert(0, '')
    self.refSpectrumPulldown.setData(spectra)
    self.refList = ListWidget(self, grid=(2, 0))


    label2a = Label(self, text="Intra-residue spectra", grid=(0, 1))

    self.intraSpectrumPulldown = PulldownList(self, grid=(1, 1), callback=self.selectIntraSpectrum)
    threeDspectra = self.getIntraExpts()
    threeDspectra.insert(0, '')
    self.intraSpectrumPulldown.setData(threeDspectra)
    self.intraList = ListWidget(self, grid=(2, 1))


    label2b = Label(self, text="Inter-residue spectra", grid=(0, 2))
    self.interSpectrumPulldown = PulldownList(self, grid=(1, 2), callback=self.selectInterSpectrum)
    self.interList = ListWidget(self, grid=(2, 2))
    interSpectra = [spectrum.pid for spectrum in project.spectra if spectrum.dimensionCount > 2]
    interSpectra.insert(0, '')
    self.interSpectrumPulldown.setData(interSpectra)
    self.buttonBox = ButtonList(self, grid=(3, 2), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.setInterIntraSpectra])

  def selectInterSpectrum(self, item):
    self.interList.addItem(item)

  def selectRefSpectrum(self, item):
    self.refList.addItem(item)

  def selectIntraSpectrum(self, item):
    self.intraList.addItem(item)

  def getIntraExpts(self):
    interExpts = []
    for spectrum in self.project.spectra:
      if spectrum.dimensionCount > 2:
        # if not isInterOnlyExpt(spectrum.experimentType):
          interExpts.append(spectrum.pid)
    return interExpts

  def setInterIntraSpectra(self):
    self.parent.refSpectra = [self.refList.item(i).text() for i in range(self.refList.count())]
    self.parent.intraSpectra = [self.interList.item(i).text() for i in range(self.interList.count())]
    self.parent.interSpectra = [self.intraList.item(i).text() for i in range(self.intraList.count())]
    self.accept()