__author__ = 'simon1'

from PyQt4 import QtGui, QtCore

# from ccpn.lib.Experiment import EXPERIMENT_TYPES

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from functools import partial

class ExperimentTypePopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(ExperimentTypePopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    spectra = project.spectra
    self.experimentTypes = project._experimentTypeMap
    for spectrum in spectra:
      spectrumIndex = spectra.index(spectrum)
      axisCodes = []
      for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([code for code in isotopeCode if not code.isdigit()]))

      atomCodes = tuple(sorted(axisCodes))
      pulldownItems = list(self.experimentTypes[spectrum.dimensionCount].get(atomCodes).keys())
      spLabel = Label(self, text=spectrum.pid, grid=(spectrumIndex, 0))
      spPulldown = PulldownList(self, grid=(spectrumIndex, 1), callback=partial(self.setExperimentType, spectrum, atomCodes), texts=pulldownItems)
      spPulldown.setCurrentIndex(spPulldown.findText(spectrum.experimentName))
    self.buttonBox = ButtonList(self, grid=(len(project.spectra)+1, 1), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.accept])


  def setExperimentType(self, spectrum, atomCodes, item):
    expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(item)
    spectrum.experimentType = expType
