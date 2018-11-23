from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb

from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import PROTEIN_ATOM_NAMES
from ccpn.util.Common import isotopeCode2Nucleus
from ccpn.util.Logging import getLogger


###from ccpn.framework.Framework import createFramework  # see note below

class NmrAtomPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, nmrAtom=None, title='Nmr Atom', **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        # WARNING: above says nmrAtom can be None but code below assumes it is not None
        # super(NmrAtomPopup, self).__init__(parent)

        self.nmrAtom = nmrAtom
        # self.project = nmrAtom.project
        ###application = createFramework() # this does not work, it creates a new Framework

        self.colourScheme = self.application.colourScheme
        self.nmrAtomLabel = Label(self, "NmrAtom: %s " % self.nmrAtom.id, grid=(0, 0))
        self.nmrAtomNameLabel = Label(self, "NmrAtom name", grid=(1, 0))
        self.nmrAtomNamePulldown = FilteringPulldownList(self, grid=(1, 1))
        mergeLabel = Label(self, grid=(1, 2), hAlign='r', text='Merge to Existing?')
        self.mergeBox = CheckBox(self, grid=(1, 3), hAlign='l')
        self.nmrResidue = self.nmrAtom.nmrResidue
        self.nmrResidueLabel = Label(self, text='NmrResidue', grid=(2, 0))
        self.nmrResiduePulldown = PulldownList(self, grid=(2, 1))
        self.nmrResiduePulldown.setData([x.id for x in self.nmrAtom.project.nmrResidues])
        self.nmrResiduePulldown.select(self.nmrAtom.nmrResidue.id)
        leftOverLabel = Label(self, grid=(5, 0))
        closeButton = Button(self, grid=(6, 1), text='Close', callback=self.reject)
        applyButton = Button(self, grid=(6, 2), text='Apply', callback=self._applyChanges)
        okButton = Button(self, grid=(6, 3), text='Ok', callback=self._okButton)
        isotopeCode = nmrAtom.isotopeCode
        nucleus = isotopeCode2Nucleus(isotopeCode)
        if nucleus:
            atomNames = sorted(set([x for y in PROTEIN_ATOM_NAMES.values() for x in y if x.startswith(nucleus)]))
        else:
            atomNames = sorted(set([x for y in PROTEIN_ATOM_NAMES.values() for x in y]))

        self.nmrAtomNamePulldown.setData(texts=atomNames)

        if nmrAtom.name:
            self.nmrAtomNamePulldown.select(self.nmrAtom.name)

    def _repopulate(self):
        self.nmrAtomLabel.setText("NmrAtom: %s " % self.nmrAtom.id)
        self.nmrResiduePulldown.setData([x.id for x in self.nmrAtom.project.nmrResidues])
        self.nmrResiduePulldown.select(self.nmrAtom.nmrResidue.id)
        isotopeCode = self.nmrAtom.isotopeCode
        nucleus = isotopeCode2Nucleus(isotopeCode)
        if nucleus:
            atomNames = sorted(set([x for y in PROTEIN_ATOM_NAMES.values() for x in y if x.startswith(nucleus)]))
        else:
            atomNames = sorted(set([x for y in PROTEIN_ATOM_NAMES.values() for x in y]))

        self.nmrAtomNamePulldown.setData(texts=atomNames)

        if self.nmrAtom.name:
            self.nmrAtomNamePulldown.select(self.nmrAtom.name)

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        applyAccept = False
        oldUndo = self.project._undo.numItems()

        self.project._startCommandEchoBlock('_applyChanges', quiet=True)
        try:
            if self.nmrAtom.name != self.nmrAtomNamePulldown.currentText():
                self.nmrAtom.rename(self.nmrAtomNamePulldown.currentText())

            if self.nmrAtom.nmrResidue.id != self.nmrResiduePulldown.currentText():
                nmrResidue = self.project.getByPid('NR:%s' % self.nmrResiduePulldown.currentText())

                if not self.mergeBox.isChecked() and self.project.getByPid('NA:%s.%s' %
                                                                           (nmrResidue.id, self.nmrAtomNamePulldown.currentText())):
                    showWarning('Merge must be selected', 'Cannot re-assign NmrAtom to an existing '
                                                          'NmrAtom of another NmrResidue without merging')

                else:
                    self.nmrAtom.assignTo(chainCode=nmrResidue.nmrChain.shortName,
                                          sequenceCode=nmrResidue.sequenceCode,
                                          residueType=nmrResidue.residueType,
                                          mergeToExisting=self.mergeBox.isChecked())
                    # self.nmrResidue._finaliseAction('change')

                self.nmrAtomLabel.setText("NmrAtom: %s" % self.nmrAtom.id)

            applyAccept = True
        except Exception as es:
            showWarning(str(self.windowTitle()), str(es))
        finally:
            self.project._endCommandEchoBlock()

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)
            if oldUndo != self.project._undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

            # repopulate popup
            self._repopulate()
            return False
        else:
            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
