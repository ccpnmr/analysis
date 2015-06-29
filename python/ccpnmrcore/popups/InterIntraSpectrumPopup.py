from PyQt4 import QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Spinbox import Spinbox

from ccpn.lib.assignment import isInterOnlyExpt


class InterIntraSpectrumPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(InterIntraSpectrumPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.project = project
    label2a = Label(self, text="Inter-residue spectra", grid=(0, 0))
    self.interSpectrumPulldown = PulldownList(self, grid=(1, 0), callback=self.selectInterSpectrum)
    self.interSpectrumPulldown.setData(self.getInterExpts()[0])
    self.interSpectrumPulldown.setCurrentIndex(1)
    self.interList = ListWidget(self, grid=(2, 0))

    label2b = Label(self, text="Intra-residue spectra", grid=(0, 1))
    self.intraSpectrumPulldown = PulldownList(self, grid=(1, 1), callback=self.selectIntraSpectrum)
    self.intraList = ListWidget(self, grid=(2, 1))
    self.intraSpectrumPulldown.setData(self.getInterExpts()[1])
    self.intraSpectrumPulldown.setCurrentIndex(1)

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