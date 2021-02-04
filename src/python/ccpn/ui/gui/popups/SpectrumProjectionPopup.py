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
__dateModified__ = "$dateModified: 2021-02-04 12:07:36 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.FileDialog import SpectrumFileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import progressManager

from ccpn.core.lib.SpectrumLib import PROJECTION_METHODS

import os


class SpectrumProjectionPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, title='Make Spectrum Projection', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application

        # spectrum selection
        self.spectrumLabel = Label(self, 'Spectrum', grid=(0, 0))
        self.spectrumPulldown = PulldownList(self, grid=(0, 1), callback=self._setSpectrum, gridSpan=(1, 2))
        # Only select 3D's for now
        validSpectra = [s for s in self.project.spectra if s.dimensionCount ==3]
        self.spectrumPulldown.setData([s.pid for s in validSpectra])

        # projection axis
        self.axisLabel = Label(self, 'Projection axis', grid=(2, 0))
        self.projectionAxisPulldown = PulldownList(self, grid=(2, 1), gridSpan=(1, 2))

        # method
        self.methodLabel = Label(self, 'Projection method', grid=(4, 0))
        self.methodPulldown = PulldownList(self, grid=(4, 1), gridSpan=(1, 2), callback=self._setMethod)
        self.methodPulldown.setData(PROJECTION_METHODS)

        # threshold
        self.thresholdLabel = Label(self, 'Threshold', grid=(5, 0))
        self.thresholdData = ScientificDoubleSpinBox(self, grid=(5, 1), gridSpan=(1, 2), vAlign='t', min=0.1, max=1e12)

        # Contour colours checkbox
        self.contourLabel = Label(self, 'Preserve contour colours', grid=(6, 0))
        self.contourCheckBox = CheckBox(self, checked=True, grid=(6, 1))

        self.addSpacer(0, 10, grid=(7,0))
        # action buttons
        self.buttonBox = ButtonList(self, grid=(8, 0), gridSpan=(1, 3),
                                          callbacks=[self.reject, self.makeProjection],
                                          texts=['Close', 'Make Projection'])

        if len(validSpectra) == 0:
            from ccpn.ui.gui.widgets.MessageDialog import showWarning
            showWarning('No valid spectra', 'No 3D spectra in current dataset')
            self.reject()

        # select a spectrum from current or validSpectra
        if self.application.current.strip is not None and \
            not self.application.current.strip.isDeleted and \
            len(self.application.current.strip.spectra) > 0 and \
            self.application.current.strip.spectra[0].dimensionCount == 3:
            spectrum = self.application.current.strip.spectra[0]
        else:
            spectrum = validSpectra[0]

        # update all widgets to correct settings
        self.spectrumPulldown.set(spectrum.pid)
        self._setSpectrum(spectrum.pid)
        self._setMethod(self.methodPulldown.currentText())

    def _setSpectrum(self, spectrumPid):
        """Callback for selecting spectrum"""
        spectrum = self.project.getByPid(spectrumPid)
        self.projectionAxisPulldown.setData(spectrum.axisCodes)
        self.thresholdData.set(spectrum.positiveContourBase)

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
        spectrum = self.project.getByPid(self.spectrumPulldown.currentText())
        axisCodes = self.axisCodes
        method = self.methodPulldown.currentText()
        threshold = self.thresholdData.get()

        with progressManager(self, 'Making %s projection from %s' % ('-'.join(axisCodes), spectrum.name)):
            projectedSpectrum = spectrum.extractProjectionToFile(axisCodes, method=method, threshold=threshold)
            if not self.contourCheckBox.get():
                # settings are copied by default from the originating spectrum
                projectedSpectrum._setDefaultContourColours()
        self.accept()  # close the popup

    def _getSpectrumFile(self):
        if os.path.exists('/'.join(self.filePathLineEdit.text().split('/')[:-1])):
            currentSpectrumDirectory = '/'.join(self.filePathLineEdit.text().split('/')[:-1])
        elif self.application.preferences.general.dataPath:
            currentSpectrumDirectory = self.application.preferences.general.dataPath
        else:
            currentSpectrumDirectory = os.path.expanduser('~')
        dialog = SpectrumFileDialog(parent=self, acceptMode='select', directory=currentSpectrumDirectory)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.filePathLineEdit.setText(directory[0])
