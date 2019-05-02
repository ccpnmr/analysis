"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog, dialogErrorReport
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.lib.ContextManagers import undoBlock, undoStackBlocking

from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import PROTEIN_ATOM_NAMES
from ccpn.util.Common import isotopeCode2Nucleus
from ccpn.util.Logging import getLogger


###from ccpn.framework.Framework import createFramework  # see note below

class NmrAtomPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, nmrAtom=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Edit NmrAtom', **kwds)

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

        if self.nmrAtom.name not in atomNames:
            atomNames.insert(0, self.nmrAtom.name)

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

        if self.nmrAtom.name not in atomNames:
            atomNames.insert(0, self.nmrAtom.name)

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
        undo = self.project._undo

        try:
            with undoBlock():

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

                    self.nmrAtomLabel.setText("NmrAtom: %s" % self.nmrAtom.id)

        except Exception as es:
            dialogErrorReport(self, undo, es)

            # repopulate popup
            self._repopulate()
            return False

        return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
