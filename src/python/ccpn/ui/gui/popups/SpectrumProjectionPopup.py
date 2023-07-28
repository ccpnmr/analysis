"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-07-28 17:24:46 +0100 (Fri, July 28, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.SpectrumLib import PROJECTION_METHODS
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FileDialog import ExportFileDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showWarning
from ccpn.ui.gui.popups._CcpnDialogWithOutputPathPopupABC import CcpnDialogWithOutputPathPopupABC
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.util.Path import aPath, Path


class SpectrumProjectionPopup(CcpnDialogWithOutputPathPopupABC):  # ExportDialogABC):
    FIXEDHEIGHT = True
    FIXEDWIDTH = False

    def __init__(self, parent=None, mainWindow=None, title='Spectrum Projection', **kwds):

        # for CcpnDialogMainWidget:
        super().__init__(parent=parent, mainWindow=mainWindow, title=title, **kwds)

        if self.project:
            # Only select 3D's for now
            self.validSpectra = [s for s in self.project.spectra if s.dimensionCount == 3]

        if not self.validSpectra:  # not None or len==0
            showWarning('No valid spectra', 'No 3D spectra in current dataset')
            self.errorFlag = True
            return

        # select a spectrum from current or validSpectra
        if self.application.current.strip is not None and \
                not self.application.current.strip.isDeleted and \
                len(self.application.current.strip.spectra) > 0 and \
                self.application.current.strip.spectra[0].dimensionCount == 3:
            self.spectrum = self.application.current.strip.spectra[0]
        else:
            self.spectrum = self.validSpectra[0]

        # for CcpnDialogMainWidget:
        self.initialise(self.mainWidget)
        self.populate(self.mainWidget)
        self.actionButtons()

        # initialise the buttons and dialog size
        self._postInit()

    @property
    def projectionAxisCode(self):
        return self.projectionAxisPulldown.get()

    @property
    def otherAxisCodes(self) -> list:
        """Return axisCodes of projected spectra (as defined by self.projectionAxisCode)
        """
        ac = list(self.spectrum.axisCodes)
        ac.remove(self.projectionAxisCode)
        return ac

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

        # projection axis
        Label(userFrame, 'Projection', grid=(rowIndex, 0), bold=True, **self._alignLabel)
        rowIndex += 1

        Label(userFrame, 'Axis', grid=(rowIndex, 0), **self._alignLabel)
        self.projectionAxisPulldown = PulldownList(userFrame, grid=(rowIndex, 1),
                                                   callback=self._setAxisCallback)
        rowIndex += 1

        # method
        Label(userFrame, 'Method', grid=(rowIndex, 0), **self._alignLabel)
        self.methodPulldown = PulldownList(userFrame, grid=(rowIndex, 1),
                                           callback=self._setMethodCallback)
        self.methodPulldown.setData(PROJECTION_METHODS)
        rowIndex += 1

        # threshold
        Label(userFrame, 'Threshold', grid=(rowIndex, 0), **self._alignLabel)
        self.thresholdData = ScientificDoubleSpinBox(userFrame, grid=(rowIndex, 1), min=0.1, max=1e12)
        rowIndex += 1

        userFrame.addSpacer(10, 20, grid=(rowIndex, 1), expandX=True, expandY=True)
        rowIndex += 1

        rowIndex += self.initialiseOutputPathWidgets(userFrame, rowIndex=rowIndex)

        # Contour colours checkbox
        Label(userFrame, 'Contours', grid=(rowIndex, 0), **self._alignLabel)
        self.contourCheckBox = CheckBox(userFrame, text='keep colours', checked=True, grid=(rowIndex, 1))
        rowIndex += 1

        userFrame.addSpacer(5, 5, grid=(rowIndex, 1), expandX=True, expandY=True)

    def actionButtons(self):
        self.setOkButton(callback=self.makeProjection, text='Make Projection', tipText='Export the projection to file and close dialog')
        self.setCloseButton(callback=self.reject, text='Close', tipText='Close')
        self.setDefaultButton(ExportDialogABC.CLOSEBUTTON)

    def populate(self, userFrame):
        """populate the widgets
        """
        if self.spectrum:
            self._setMethodCallback(self.methodPulldown.currentText())
        super(SpectrumProjectionPopup, self).populate(userFrame)

    def getInfoString(self) -> str:
        """Return a string for the info widget field
        Should be subclassed
        """
        return self.spectrum.dataSource._fileInfoString2

    def getName(self) -> str:
        """Return a string for the name of the file
        Can be subclassed
        """
        return f'{self.spectrum.name}_{self.projectionAxisCode}_projection'

    def _setSpectrumCallback(self, spectrumPid):
        """Callback for selecting spectrum
        """
        self.spectrum = self.project.getByPid(spectrumPid)
        self.projectionAxisPulldown.setData(self.spectrum.axisCodes)
        self.projectionAxisPulldown.set(self.spectrum.axisCodes[0])
        self.thresholdData.set(self.spectrum.positiveContourBase)
        super()._setSpectrumCallback(spectrumPid)

    def _setAxisCallback(self, axis):
        """Callback when setting projection axis"""
        self._setDataStore()
        self.outPathWidget.setText(self.dataStore.path.asString())

    def _setMethodCallback(self, method):
        """Callback when setting method"""
        if method.endswith('threshold'):
            self.thresholdData.setEnabled(True)
        else:
            self.thresholdData.setEnabled(False)

    def makeProjection(self):
        """Make projection from the selected spectrum.
        """
        if self.spectrum is None:
            raise RuntimeError(f'Spectrum is undefined')

        axisCodes = self.otherAxisCodes
        method = self.methodPulldown.get()
        threshold = self.thresholdData.get()

        with progressManager(self, 'Making %s projection from %s' % ('-'.join(axisCodes), self.spectrum.name)):
            projectedSpectrum = self.spectrum.extractProjectionToFile(axisCodes,
                                                                      method=method,
                                                                      threshold=threshold,
                                                                      dataFormat=self.dataStore.dataFormat,
                                                                      path=self.dataStore.path
                                                                      )
            if not self.contourCheckBox.get():
                # settings were copied by default from the originating spectrum
                projectedSpectrum._setDefaultContourColours()

        self.accept()


def main():
    from ccpn.ui.gui.widgets.Application import newTestApplication

    app = newTestApplication()
    dialog = SpectrumProjectionPopup()
    dialog.exec_()


if __name__ == '__main__':
    main()
