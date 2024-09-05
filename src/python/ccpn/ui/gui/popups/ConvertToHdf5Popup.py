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
__dateModified__ = "$dateModified: 2024-09-05 14:47:53 +0200 (Thu, September 05, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-07-10 11:28:58 +0100 (Mon, July 10, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showOkCancelWarning, showInfo, showWarning
from ccpn.ui.gui.popups._CcpnDialogWithOutputPathPopupABC import CcpnDialogWithOutputPathPopupABC
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC


class ConvertToHdf5Popup(CcpnDialogWithOutputPathPopupABC):
    FIXEDHEIGHT = True
    FIXEDWIDTH = False

    def __init__(self, parent=None, mainWindow=None, title='Convert spectrum (binary) data to Hdf5', **kwds):

        # for CcpnDialogMainWidget:
        super().__init__(parent=parent, mainWindow=mainWindow, title=title, **kwds)

        if self.project:
            # Only select 3D's for now
            self.validSpectra = [sp for sp in self.project.spectra if not sp.isEmptySpectrum()]

            if not self.validSpectra:
                from ccpn.ui.gui.widgets.MessageDialog import showWarning

                showWarning('No valid spectra', 'No non-Hdf5 spectra in current project')
                self.errorFlag = True
                return

        self.spectrum = self.validSpectra[0]

        # for CcpnDialogMainWidget:
        self.initialise(self.mainWidget)
        self.populate(self.mainWidget)
        self.actionButtons()

        # initialise the buttons and dialog size
        self._postInit()

    def initialise(self, userFrame):
        """Create the widgets for the userFrame
        """
        # spectrum selection
        rowIndex = 0
        rowIndex += self.initialiseSpectrumWidgets(userFrame, rowIndex=rowIndex)

        self.removeInPathCheckBox = CheckBox(userFrame, text='Remove on completion',
                                             checked=False, grid=(rowIndex, 1), callback=self._removeInPathCallback)
        rowIndex += 1

        userFrame.addSpacer(10, 20, grid=(rowIndex, 1), expandX=True, expandY=True)
        rowIndex += 1

        rowIndex += self.initialiseOutputPathWidgets(userFrame, rowIndex=rowIndex)

        userFrame.addSpacer(5, 5, grid=(rowIndex, 1), expandX=True, expandY=True)

    def actionButtons(self):
        self.setOkButton(callback=self.convertSpectrum, text='Convert to Hdf5', tipText='Convert spectrum to Hdf5 and close dialog')
        self.setCloseButton(callback=self.reject, text='Close', tipText='Close')
        self.setDefaultButton(ExportDialogABC.CLOSEBUTTON)

    def getInfoString(self) -> str:
        """Return a string for the info widget field
        Should be subclassed
        """
        return self.spectrum.dataSource._fileInfoString1

    def _removeInPathCallback(self):
        """Callback for removeInPath checkbox"""
        checked = self.removeInPathCheckBox.get()

    def convertSpectrum(self):
        """Convert the selected spectrum.
        """
        if self.spectrum is not None:
            removeInPath = self.removeInPathCheckBox.get()
            inDataSource = self.spectrum.dataSource  # Originating dataStore instance; keep a handle to optionally delete original spectrum data

            with progressManager(self, f'Converting "{self.spectrum.name}" to {self.dataFormat}'):
                outDataSource = self.spectrum.convertToHdf5(self.dataStore.path)

            title = f'Spectrum "{self.spectrum.name}"'
            message = f'Successfully converted the "{inDataSource.dataFormat}" spectral data to "{outDataSource.dataFormat}"\n'
            if removeInPath:
                files = inDataSource.getAllFilePaths()
                message += f'\nDo you want to delete the original {len(files)} {inDataSource.dataFormat}-file(s)? (Can not undo!)'
                ok = showOkCancelWarning(title, message, parent=self)
                if ok:
                    for _f in files:
                        _f.remove()
            else:
                showInfo(title, message, parent=self)

        self.accept()


# popup = ConvertToHdf5Popup(parent=mainWindow, mainWindow=mainWindow)
# popup.show()
