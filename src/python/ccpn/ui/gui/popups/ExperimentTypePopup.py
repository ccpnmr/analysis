__author__ = 'simon1'

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList

from functools import partial

class ExperimentTypePopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):

    from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

    super(ExperimentTypePopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    spectra = project.spectra
    self.experimentTypes = project._experimentTypeMap
    for spectrumIndex, spectrum in enumerate(spectra):
      axisCodes = []
      for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([char for char in isotopeCode if not char.isdigit()]))

      atomCodes = tuple(sorted(axisCodes))
      pulldownItems = list(self.experimentTypes[spectrum.dimensionCount].get(atomCodes).keys())
      spLabel = Label(self, text=spectrum.pid, grid=(spectrumIndex, 0))
      spPulldown = FilteringPulldownList(self, grid=(spectrumIndex, 1),
                                callback=partial(self._setExperimentType, spectrum, atomCodes),
                                texts=pulldownItems)

      # Get the text that was used in the pulldown from the refExperiment
      apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
      text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
      text = priorityNameRemapping.get(text, text)
      spPulldown.setCurrentIndex(spPulldown.findText(text))

    self.buttonBox = Button(self, grid=(len(project.spectra)+1, 1), text='Close',
                           callback=self.accept)


  def _setExperimentType(self, spectrum, atomCodes, item):
    expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(item)
    spectrum.experimentType = expType
