"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-25 18:02:31 +0100 (Fri, October 25, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-11-14 11:28:58 +0100 (Mon, November 14, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import ccpn.core.lib.SpectrumLib as specLib
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
# from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showWarning
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.popups._CcpnDialogWithOutputPathPopupABC import CcpnDialogWithOutputPathPopupABC
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
# from ccpn.util.Path import aPath


class PseudoToSpectrumGroupPopup(CcpnDialogWithOutputPathPopupABC):  # ExportDialogABC):
    FIXEDHEIGHT = True
    FIXEDWIDTH = False

    def __init__(self, parent=None, mainWindow=None, spectrum=None, **kwds):

        # for CcpnDialogMainWidget:
        super().__init__(parent=parent, mainWindow=mainWindow, title='Pseudo-nD Spectrum to SpectrumGroup', **kwds)

        if self.project:
            self.validSpectra = [sp for sp in self.project.spectra if sp._getPseudoDimension() != 0]

        if not self.validSpectra:  # not None or len==0
            showWarning('No valid spectra', 'No pseudo-spectra in current dataset')
            self.errorFlag = True
            return

        if spectrum is not None and spectrum not in self.validSpectra:
            showWarning('No valid spectrum', f'{spectrum} is not a valid pseudo-spectrum')
            self.errorFlag = True
            return

        self.pseudoDimension = None
        self.spectrum = spectrum or self.validSpectra[0]

        # for CcpnDialogMainWidget:
        self.initialise(self.mainWidget)
        self.populate(self.mainWidget)

    def initialise(self, userFrame):
        """Create the widgets for the userFrame
        """
        # spectrum selection
        rowIndex = 0
        rowIndex += self.initialiseSpectrumWidgets(userFrame, rowIndex=rowIndex)
        # Hide in inPath info as it is not really needed
        self.inPathLabel.setVisible(False)
        self.inPathWidget.setVisible(False)

        userFrame.addSpacer(10, 20, grid=(rowIndex, 1), expandX=True, expandY=True)
        rowIndex += 1

        rowIndex += self.initialiseOutputPathWidgets(userFrame, rowIndex=rowIndex)

        # Contour  checkbox
        Label(userFrame, 'Contours', grid=(rowIndex, 0), **self._alignLabel)
        self.contourCheckBox = CheckBox(userFrame, text='keep settings', checked=True, grid=(rowIndex, 1))
        rowIndex += 1

        userFrame.addSpacer(5, 5, grid=(rowIndex, 1), expandX=True, expandY=True)

        self.setOkButton(callback=self.makeSpectrumGroup, text='Make SpectrumGroup', tipText='Extract spectra along pseudo dimensions and close dialog')
        self.setCloseButton(callback=self.reject, text='Cancel', tipText='Cancel')
        self.setDefaultButton(ExportDialogABC.CLOSEBUTTON)

    def getInfoString(self) -> str:
        """Return a string for the info widget field
        Should be subclassed
        """
        return self.spectrum.dataSource._fileInfoString2

    def getName(self) -> str:
        """Return a string for the name of the file
        Can be subclassed
        """
        return f'{self.spectrum.name}_%03d'

    def _setSpectrumCallback(self, spectrumPid):
        """Callback for selecting spectrum
        """
        self.spectrum = self.project.getByPid(spectrumPid)
        self.pseudoDimension = self.spectrum._getPseudoDimension()
        super()._setSpectrumCallback(spectrumPid)

    def makeSpectrumGroup(self):
        """Make SpectrumGroup from the specified spectrum.

        Spectrum is saved alongside the original spectrum, if this folder is not available then
        the spectrum is saved in the project/data/spectra folder.
        """
        if self.spectrum is not None:
            with progressManager(self, f'Making SpectrumGroup from "{self.spectrum.name}"'):
                spectrumGroup = self.spectrum.pseudoToSpectrumGroup(pathTemplate=self.dataStore.path.asString())

                if not self.contourCheckBox.isChecked():
                    # values are copied by default
                    for sp in spectrumGroup.spectra:
                        sp._setDefaultContourValues()
                        sp._setDefaultContourColours()

            self.accept()
