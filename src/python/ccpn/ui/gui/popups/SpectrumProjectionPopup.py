"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import progressManager

from ccpn.core.lib.SpectrumLib import PROJECTION_METHODS

import os


class SpectrumProjectionPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, title='Make Spectrum Projection', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application

        # spectrum selection
        spectrumLabel = Label(self, 'Spectrum to project', grid=(0, 0))
        self.spectrumPulldown = PulldownList(self, grid=(0, 1), callback=self._setSpectrum, gridSpan=(1, 2))
        # Only select 3D's for now
        self.spectrumPulldown.setData(
                [spectrum.pid for spectrum in self.project.spectra if spectrum.dimensionCount == 3])
        # filepath
        filePathLabel = Label(self, 'New Spectrum Path', grid=(1, 0))
        self.filePathLineEdit = LineEdit(self, grid=(1, 1))
        self.pathButton = Button(self, grid=(1, 2), callback=self._getSpectrumFile, icon='icons/applications-system')
        # projection axis
        axisLabel = Label(self, 'Projection axis', grid=(2, 0))
        self.projectionAxisPulldown = PulldownList(self, grid=(2, 1), gridSpan=(1, 2), callback=self._setProjectionAxis)
        # method
        methodLabel = Label(self, 'Projection Method', grid=(4, 0))
        self.methodPulldown = PulldownList(self, grid=(4, 1), gridSpan=(1, 2), callback=self._setMethod)
        self.methodPulldown.setData(PROJECTION_METHODS)
        # threshold
        thresholdLabel = Label(self, 'Threshold', grid=(5, 0))
        self.thresholdData = ScientificDoubleSpinBox(self, grid=(5, 1), gridSpan=(1, 2), vAlign='t', min=0.1, max=1e12)
        # Contour coulours checkbox
        contourLabel = Label(self, 'Preserve contour colours', grid=(6, 0))
        self.contourCheckBox = CheckBox(self, checked=True, grid=(6, 1))
        # action buttons
        self.buttonBox = ButtonList(self, grid=(7, 0), gridSpan=(1, 2), hAlign='r',
                                    callbacks=[self.reject, self.makeProjection],
                                    texts=['Close','Make Projection'])

        # update all widgets to correct settings
        if self.application.current.strip is not None:
            spectrum = self.application.current.strip.spectra[0]
            self.spectrumPulldown.set(spectrum.pid)
        self._setSpectrum(self.spectrumPulldown.currentText())
        self._setMethod(self.methodPulldown.currentText())

    def _setSpectrum(self, spectrumPid):
        """Callback for selecting spectrum"""
        spectrum = self.project.getByPid(spectrumPid)
        self.projectionAxisPulldown.setData(spectrum.axisCodes)
        self._setProjectionAxis(self.projectionAxisPulldown.currentText())
        self.thresholdData.set(spectrum.positiveContourBase)

    def _setProjectionAxis(self, projectionAxis):
        """Callback when setting projection axis"""
        spectrum = self.project.getByPid(self.spectrumPulldown.currentText())
        path = '/'.join(spectrum.filePath.split('/')[:-1]) + '/' + spectrum.name + '-' + '-'.join(
            self.axisCodes) + '.dat'
        self.filePathLineEdit.setText(path)

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
        filePath = self.filePathLineEdit.text()
        method = self.methodPulldown.currentText()
        threshold = self.thresholdData.get()

        with progressManager(self, 'Making %s projection from %s' % ('-'.join(axisCodes), spectrum.name)):
            spectrum.getProjection(axisCodes, method=method, threshold=threshold, path=filePath)
            objs = self.project.loadData(filePath)
            #print('>>> obj', objs)
            if len(objs) == 0:
                raise RuntimeError('Error loading "%s"' % filePath)
            if self.contourCheckBox.get():
                projectedSpectrum = objs[0]
                projectedSpectrum.positiveContourColour = spectrum.positiveContourColour
                projectedSpectrum.negativeContourColour = spectrum.negativeContourColour
        self.accept()  # close the popup

    def _getSpectrumFile(self):
        if os.path.exists('/'.join(self.filePathLineEdit.text().split('/')[:-1])):
            currentSpectrumDirectory = '/'.join(self.filePathLineEdit.text().split('/')[:-1])
        elif self.application.preferences.general.dataPath:
            currentSpectrumDirectory = self.application.preferences.general.dataPath
        else:
            currentSpectrumDirectory = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Projection File', directory=currentSpectrumDirectory,
                            fileMode=0, acceptMode=1,
                            preferences=self.application.preferences.general)
        directory = dialog.selectedFiles()
        if len(directory) > 0:
            self.filePathLineEdit.setText(directory[0])
