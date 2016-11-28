from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import PROTEIN_ATOM_NAMES
from ccpn.util.Common import isotopeCode2Nucleus

###from ccpn.framework.Framework import getFramework  # see note below

class NmrAtomPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, nmrAtom=None, **kw):
    # WARNING: above says nmrAtom can be None but code below assumes it is not None
    super(NmrAtomPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.nmrAtom = nmrAtom
    self.project = nmrAtom.project
    ###application = getFramework() # this does not work, it creates a new Framework
    application = self.project._appBase
    self.colourScheme = application.preferences.general.colourScheme
    self.nmrAtomLabel = Label(self, "NmrAtom: %s " % self.nmrAtom.id, grid=(0, 0))
    self.nmrAtomNameLabel = Label(self, "NmrAtom name", grid=(1, 0))
    self.nmrAtomNamePulldown = PulldownList(self, grid=(1, 1))
    mergeLabel = Label(self, grid=(1, 2), hAlign='r', text='Merge to Existing?')
    self.mergeBox = CheckBox(self, grid=(1, 3), hAlign='l')
    self.nmrResidue = self.nmrAtom.nmrResidue
    self.nmrResidueLabel = Label(self, text='NmrResidue', grid=(2, 0))
    self.nmrResiduePulldown = PulldownList(self, grid=(2, 1))
    self.nmrResiduePulldown.setData([x.id for x in self.nmrAtom.project.nmrResidues])
    self.nmrResiduePulldown.select(self.nmrAtom.nmrResidue.id)
    leftOverLabel = Label(self, grid=(5, 0))
    applyButton = Button(self, grid=(6, 1), text='Apply', callback=self.applyChanges)
    applyButton = Button(self, grid=(6, 2), text='Close', callback=self.reject)
    isotopeCode = nmrAtom.isotopeCode
    nucleus = isotopeCode2Nucleus(isotopeCode)
    if nucleus:
      atomNames = sorted(set([y for x in PROTEIN_ATOM_NAMES.values() for y in x if y.startswith(nucleus)]))
    else:
      atomNames = sorted(set([y for x in PROTEIN_ATOM_NAMES.values() for y in x]))

    self.nmrAtomNamePulldown.setData(texts=atomNames)

    if nmrAtom.name:
      self.nmrAtomNamePulldown.select(self.nmrAtom.name)


  def applyChanges(self):
    if self.nmrAtom.name != self.nmrAtomNamePulldown.currentText():
      self.nmrAtom.rename(self.nmrAtomNamePulldown.currentText())

    if self.nmrAtom.nmrResidue.id != self.nmrResiduePulldown.currentText():
      nmrResidue = self.project.getByPid('NR:%s' % self.nmrResiduePulldown.currentText())
      if not self.mergeBox.isChecked() and self.project.getByPid('NA:%s.%s' %
                                           (nmrResidue.id, self.nmrAtomNamePulldown.currentText())):
        showWarning('Merge must be selected', 'Cannot re-assign NmrAtom to an existing '
                    'NmrAtom of another NmrResidue without merging', colourScheme=self.colourScheme)

      else:
        self.nmrAtom.assignTo(chainCode=nmrResidue.nmrChain.shortName,
                              sequenceCode=nmrResidue.sequenceCode,
                              residueType=nmrResidue.residueType,
                              mergeToExisting=self.mergeBox.isChecked())

      self.nmrAtomLabel.setText("NmrAtom: %s" % self.nmrAtom.id)


