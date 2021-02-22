"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-22 16:19:38 +0000 (Mon, February 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.SpectrumLib import PROJECTION_METHODS
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.util.Path import aPath


class SpectrumProjectionPopup(ExportDialogABC):

    FIXEDHEIGHT = True

    def __init__(self, parent=None, mainWindow=None, title='Make Spectrum Projection', **kwds):

        super().__init__(parent=parent, mainWindow=mainWindow, title=title,
                         fileMode='anyFile',
                         acceptMode='export',
                         selectFile=None,
                         **kwds)

        if self.project:
            # Only select 3D's for now
            validSpectra = [s for s in self.project.spectra if s.dimensionCount == 3]

            if len(validSpectra) == 0:
                from ccpn.ui.gui.widgets.MessageDialog import showWarning

                showWarning('No valid spectra', 'No 3D spectra in current dataset')
                self.reject()

        if self.mainWindow:
            self.mainWindow = mainWindow
            self.project = self.mainWindow.project
            self.application = self.mainWindow.application
        else:
            self.mainWindow = None
            self.project = None
            self.application = None

    def actionButtons(self):
        self.setOkButton(callback=self.makeProjection, text='Make Projection', tipText='Export the projection to file and close dialog')
        self.setCloseButton(callback=self._rejectDialog, text='Close', tipText='Close')
        self.setDefaultButton(ExportDialogABC.CLOSEBUTTON)

    def initialise(self, userFrame):
        """Create the widgets for the userFrame
        """
        spectrumLabel = Label(userFrame, 'Spectrum to project', grid=(0, 0))
        self.spectrumPulldown = PulldownList(userFrame, grid=(0, 1), callback=self._setSpectrum, gridSpan=(1, 2))

        # projection axis
        axisLabel = Label(userFrame, 'Projection axis', grid=(2, 0))
        self.projectionAxisPulldown = PulldownList(userFrame, grid=(2, 1), gridSpan=(1, 2), callback=self._setProjectionAxis)
        # method
        methodLabel = Label(userFrame, 'Projection Method', grid=(4, 0))
        self.methodPulldown = PulldownList(userFrame, grid=(4, 1), gridSpan=(1, 2), callback=self._setMethod)
        self.methodPulldown.setData(PROJECTION_METHODS)
        # threshold
        thresholdLabel = Label(userFrame, 'Threshold', grid=(5, 0))
        self.thresholdData = ScientificDoubleSpinBox(userFrame, grid=(5, 1), gridSpan=(1, 2), vAlign='t', min=0.1, max=1e12)
        # self.thresholdData.setMinimumHeight(25)
        # Contour colours checkbox
        contourLabel = Label(userFrame, 'Preserve contour colours', grid=(6, 0))
        self.contourCheckBox = CheckBox(userFrame, checked=True, grid=(6, 1))

        userFrame.addSpacer(5, 5, grid=(7, 1), expandX=True, expandY=True)

        if self.project:
            validSpectra = [s for s in self.project.spectra if s.dimensionCount == 3]
            self.spectrumPulldown.setData([s.pid for s in validSpectra])

            # select a spectrum from current or validSpectra
            if self.application.current.strip is not None and \
                    not self.application.current.strip.isDeleted and \
                    len(self.application.current.strip.spectra) > 0 and \
                    self.application.current.strip.spectra[0].dimensionCount == 3:
                self.spectrum = self.application.current.strip.spectra[0]
            else:
                self.spectrum = validSpectra[0]

        else:
            self.spectrum = None

    def populate(self, userFrame):
        """populate the widgets
        """
        with self.blockWidgetSignals(userFrame):
            if self.spectrum:
                # update all widgets to correct settings
                self.spectrumPulldown.set(self.spectrum.pid)
                self._setSpectrum(self.spectrum.pid)
                self._setMethod(self.methodPulldown.currentText())

    def _setSpectrum(self, spectrumPid):
        """Callback for selecting spectrum"""
        spectrum = self.project.getByPid(spectrumPid)
        self.projectionAxisPulldown.setData(spectrum.axisCodes)
        self._setProjectionAxis(self.projectionAxisPulldown.currentText())
        self.thresholdData.set(spectrum.positiveContourBase)

    def _setProjectionAxis(self, projectionAxis):
        """Callback when setting projection axis
        """
        spectrum = self.project.getByPid(self.spectrumPulldown.currentText())
        path = aPath(spectrum._getDefaultProjectionPath(self.axisCodes))
        self.updateFilename(path)

    def _setMethod(self, method):
        """Callback when setting method"""
        if method.endswith('threshold'):
            self.thresholdData.setEnabled(True)
        else:
            self.thresholdData.setEnabled(False)

    @property
    def projectionAxisCode(self):
        return self.projectionAxisPulldown.currentText()

    @property
    def axisCodes(self):
        """Return axisCodes of projected spectra (as defined by self.projectionAxisCode)"""
        spectrum = self.project.getByPid(self.spectrumPulldown.currentText())
        ac = list(spectrum.axisCodes)
        ac.remove(self.projectionAxisCode)
        return ac

    def makeProjection(self):
        self._acceptDialog()

        if self.accepted:
            spectrum = self.project.getByPid(self.spectrumPulldown.currentText())
            axisCodes = self.axisCodes
            filePath = aPath(self.saveText.text())
            method = self.methodPulldown.currentText()
            threshold = self.thresholdData.get()

            with progressManager(self, 'Making %s projection from %s' % ('-'.join(axisCodes), spectrum.name)):
                # spectrum.getProjection(axisCodes, method=method, threshold=threshold, path=filePath)
                # objs = self.project.loadData(filePath)
                # #print('>>> obj', objs)
                # if len(objs) == 0:
                #     raise RuntimeError('Error loading "%s"' % filePath)
                projectedSpectrum = spectrum.extractProjectionToFile(axisCodes, method=method, threshold=threshold, path=filePath)
                if self.contourCheckBox.get():
                    # projectedSpectrum = objs[0]
                    projectedSpectrum.positiveContourColour = spectrum.positiveContourColour
                    projectedSpectrum.negativeContourColour = spectrum.negativeContourColour

    # def _getSpectrumFile(self):
    #     if os.path.exists('/'.join(self.saveText.text().split('/')[:-1])):
    #         currentSpectrumDirectory = '/'.join(self.saveText.text().split('/')[:-1])
    #     elif self.application.preferences.general.dataPath:
    #         currentSpectrumDirectory = self.application.preferences.general.dataPath
    #     else:
    #         currentSpectrumDirectory = os.path.expanduser('~')
    #     dialog = SpectrumFileDialog(parent=self, acceptMode='select', directory=currentSpectrumDirectory)
    #     dialog._show()
    #     directory = dialog.selectedFiles()
    #     if directory and len(directory) > 0:
    #         self.saveText.setText(directory[0])


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import newTestApplication


    app = newTestApplication()
    dialog = SpectrumProjectionPopup()
    dialog.exec_()
