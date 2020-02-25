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
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.core.lib.ContextManagers import undoBlock


class SetupNmrResiduesPopup(CcpnDialogMainWidget):
    def __init__(self, parent=None, mainWindow=None,
                 title='Set up nmrResidues', **kwds):
        CcpnDialogMainWidget.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self._parent = parent
        self.mainWindow = mainWindow
        self.project = self.mainWindow.project

        label1a = Label(self.mainWidget, text="Source PeakList ", grid=(0, 0))
        self.peakListPulldown = PulldownList(self.mainWidget, grid=(0, 1))
        self.peakListPulldown.setData([peakList.pid for peakList in self.project.peakLists if len(peakList.peaks) > 0])
        label1a = Label(self.mainWidget, text="NmrChain ", grid=(0, 2))
        self.nmrChainPulldown = PulldownList(self.mainWidget, grid=(0, 3))
        self.nmrChainPulldown.setData([nmrChain.pid for nmrChain in self.project.nmrChains])
        self.assignmentCheckBox = CheckBox(self.mainWidget, text="Keep existing assignments", checked=True, grid=(1, 0), gridSpan=(1,3))

        self._acceptButtonText = 'Setup NMR Residues'
        self.BUTTON_CANCEL = 'Cancel'

        self.setApplyButton(callback=self._setupNmrResidues, text=self._acceptButtonText, tipText='Setup Nmr Residues and close')
        self.setCancelButton(callback=self.reject, text=self.BUTTON_CANCEL, tipText='Cancel and close')
        self.setDefaultButton(CcpnDialogMainWidget.APPLYBUTTON)


        self.__postInit__()
        self._applyButton = self.getButton(self.APPLYBUTTON)
        self._applyButton.setEnabled(True)
        self._cancelButton = self.getButton(self.CANCELBUTTON)
        # self.assignmentCheckBox.setEnabled(False) #This option is broken.
        # self.buttonBox = ButtonList(self, grid=(1, 3), texts=['Cancel', 'Ok'],
        #                             callbacks=[self.reject, ])

    def _setupNmrResidues(self):
        with undoBlock():
            peakList = self.project.getByPid(self.peakListPulldown.currentText())
            nmrChain = self.project.getByPid(self.nmrChainPulldown.currentText())
            keepAssignments = self.assignmentCheckBox.isChecked()  #This option is broken.

            # go through all the peaks in the peakList
            for peak in peakList.peaks:

                # only process those that are empty OR those not empty when checkbox cleared
                if not keepAssignments or all(not dimensionNmrAtoms for dimensionNmrAtoms in peak.dimensionNmrAtoms):

                    nmrResidue = nmrChain.newNmrResidue()
                    for i, axisCode in enumerate(peak.axisCodes):
                        nmrAtom = nmrResidue.fetchNmrAtom(name=str(axisCode))
                        peak.assignDimension(axisCode=axisCode, value=[nmrAtom])

        self.accept()
