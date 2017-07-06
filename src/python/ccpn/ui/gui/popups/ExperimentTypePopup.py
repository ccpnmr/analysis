#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:41 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog

from functools import partial

class ExperimentTypePopup(CcpnDialog):
  def __init__(self, parent=None, project=None, title:str='Experiment Type Selection', **kw):

    from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.parent = parent
    spectra = project.spectra
    self.experimentTypes = project._experimentTypeMap
    self.spPulldowns = []
    self.scrollArea = ScrollArea(self, setLayout=True, grid=(0, 0))
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = Frame(self, setLayout=True)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)

    for spectrumIndex, spectrum in enumerate(spectra):
      axisCodes = []
      for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([char for char in isotopeCode if not char.isdigit()]))

      atomCodes = tuple(sorted(axisCodes))
      self.pulldownItems = list(self.experimentTypes[spectrum.dimensionCount].get(atomCodes).keys())
      spLabel = Label(self.scrollAreaWidgetContents, text=spectrum.pid, grid=(spectrumIndex, 0))
      self.spPulldown = FilteringPulldownList(self.scrollAreaWidgetContents, grid=(spectrumIndex, 1),
                                callback=partial(self._setExperimentType, spectrum, atomCodes),
                                texts=self.pulldownItems)
      self.spPulldown.lineEdit().editingFinished.connect(partial(self.editedExpTypeChecker, self.spPulldown, self.pulldownItems))
      # self.spPulldown._completer.setCompletionMode(QtGui.QCompleter.InlineCompletion &~  QtGui.QCompleter.UnfilteredPopupCompletion)
      self.spPulldowns.append(self.spPulldown)
      spButton = Button(self.scrollAreaWidgetContents, grid=(spectrumIndex, 2),
                        callback=partial(self.raiseExperimentFilterPopup,
                                         spectrum, spectrumIndex, atomCodes),
                        hPolicy='fixed', icon='icons/applications-system')

      # Get the text that was used in the pulldown from the refExperiment
      # NBNB This could possibly give unpredictable results
      # if there is an experiment with experimentName (user settable!)
      # that happens to match the synonym for a differnet experiment type.
      # But if people will ignore our defined vocabulary, on their head be it!
      # Anyway, tha alternative (discarded) is to look into the ExpPrototype
      # to compare RefExperiment names and synonyums
      # or (too ugly for words) to have a third attribute in parallel with
      # spectrum.experimentName and spectrum.experimentType
      text = spectrum.experimentName
      if text not in self.pulldownItems:
        text = spectrum.experimentType
      # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
      # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
      text = priorityNameRemapping.get(text, text)
      self.spPulldown.setCurrentIndex(self.spPulldown.findText(text))

    self.buttonBox = Button(self, grid=(1, 0), text='Close',
                           callback=self.accept, hAlign='r', vAlign='b')

    self.setWindowTitle(title)


  def _setExperimentType(self, spectrum, atomCodes, item):
    expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(item)
    spectrum.experimentType = expType

  def raiseExperimentFilterPopup(self, spectrum, spectrumIndex, atomCodes):

    popup = ExperimentFilterPopup(spectrum=spectrum, application=spectrum.project._appBase)
    popup.exec_()
    if popup.expType:
      self.spPulldowns[spectrumIndex].select(popup.expType)
      expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(popup.expType)

      if expType is not None:
        spectrum.experimentType = expType

  def editedExpTypeChecker(self, pulldown, items):
    if not pulldown.currentText() in items:
      if pulldown.currentText():
        msg = ' (ExpTypeNotFound!)'
        if not msg in pulldown.currentText():
          pulldown.lineEdit().setText(pulldown.currentText() + msg)
          pulldown.lineEdit().selectAll()

  def keyPressEvent(self, KeyEvent):
    if KeyEvent.key() == QtCore.Qt.Key_Return:
      return
