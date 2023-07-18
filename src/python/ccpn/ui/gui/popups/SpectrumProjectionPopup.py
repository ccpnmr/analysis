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
__dateModified__ = "$dateModified: 2023-07-18 17:54:23 +0100 (Tue, July 18, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
from ccpn.core.lib.DataStore import DataStore

from ccpn.core.lib.SpectrumLib import PROJECTION_METHODS
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FileDialog import ExportFileDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showWarning
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.util.Path import aPath, Path

_alignLabel = dict(vAlign='c', hAlign='r', minimumHeight=25) # Keyword labels
_align1 = dict(vAlign='c', hAlign='l', textColour='black')  # Data Labels
_align2 = dict(vAlign='c')  # Dimensional Pulldowns / LineEdits

minWidth = 400


class SpectrumProjectionPopup(CcpnDialogMainWidget):  # ExportDialogABC):
    FIXEDHEIGHT = True
    FIXEDWIDTH = False

    saveDataFormat = Hdf5SpectrumDataSource.dataFormat
    suffix = Hdf5SpectrumDataSource.suffixes[0]

    def __init__(self, parent=None, mainWindow=None, title='Spectrum Projection', **kwds):

        # for CcpnDialogMainWidget:
        super().__init__(parent=parent, setLayout=True, windowTitle=title,
                         **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.project = self.mainWindow.project
            self.application = self.mainWindow.application
        else:
            self.mainWindow = self.project = self.application = None

        self.dataStore = None # DataStore instance

        self.validSpectra = None # list of valid spectra
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
        return self.projectionAxisPulldown.currentText()

    @property
    def axisCodes(self):
        """Return axisCodes of projected spectra (as defined by self.projectionAxisCode)"""
        ac = list(self.spectrum.axisCodes)
        ac.remove(self.projectionAxisCode)
        return ac

    def actionButtons(self):
        self.setOkButton(callback=self.makeProjection, text='Make Projection', tipText='Export the projection to file and close dialog')
        self.setCloseButton(callback=self._rejectDialog, text='Close', tipText='Close')
        self.setDefaultButton(ExportDialogABC.CLOSEBUTTON)

    def _rejectDialog(self):
        # NOTE:ED - not required for exportDialogABC
        self.reject()

    def initialise(self, userFrame):
        """Create the widgets for the userFrame
        """
        row = -1

        # spectrum selection
        row += 1
        Label(userFrame, 'Spectrum', grid=(row, 0), **_alignLabel)
        self.spectrumPulldown = PulldownList(userFrame, grid=(row, 1), callback=self._setSpectrumCallback, gridSpan=(1, 2))
        self.spectrumPulldown.setData([s.pid for s in self.validSpectra])

        row += 1
        self.infoWidget = Label(userFrame, textAlignment='l', grid=(row, 1), gridSpan=(1, 1), **_align1)

        # projection axis
        row += 1
        Label(userFrame, 'Projection', grid=(row, 0), bold=True, **_alignLabel)

        row += 1
        Label(userFrame, 'Axis', grid=(row, 0), **_alignLabel)
        self.projectionAxisPulldown = PulldownList(userFrame, grid=(row, 1), gridSpan=(1, 2),
                                                   callback=self._setAxisCallback)

        # method
        row += 1
        Label(userFrame, 'Method', grid=(row, 0), **_alignLabel)
        self.methodPulldown = PulldownList(userFrame, grid=(row, 1), gridSpan=(1, 2),
                                           callback=self._setMethodCallback)
        self.methodPulldown.setData(PROJECTION_METHODS)

        # threshold
        row += 1
        Label(userFrame, 'Threshold', grid=(row, 0), **_alignLabel)
        self.thresholdData = ScientificDoubleSpinBox(userFrame, grid=(row, 1), gridSpan=(1, 2), vAlign='t', min=0.1, max=1e12)

        row += 1
        userFrame.addSpacer(10, 20, grid=(row, 1), expandX=True, expandY=True)

        row += 1
        Label(userFrame, 'Output', grid=(row, 0), bold=True, **_alignLabel)
        self.autoPathCheckBox = CheckBox(userFrame, text='Auto generate',
                                         checked=True, grid=(row, 1), callback=self._checkboxCallback)

        # Save inside project checkbox; only enabled if project is not temporary
        row += 1
        self.saveInProjectCheckBox = CheckBox(userFrame, text='Save inside project',
                                              checked=False, grid=(row, 1), callback=self._saveInProjectCallback)
        self.saveInProjectCheckBox.setEnabled(not self.project.isTemporary)

        # outpath
        row += 1
        Label(userFrame, 'Path', grid=(row, 0), **_alignLabel)
        self.outPathWidget = LineEdit(userFrame, textAlignment='l', grid=(row, 1), gridSpan=(1, 1), editable=True,
                                      minimumWidth=minWidth)
        self.fileButton = Button(userFrame,  hPolicy='fixed', icon='icons/directory', grid=(row,3), callback=self._fileButtonCallback)
        self.fileButton.setEnabled(False)

        # Contour colours checkbox
        row += 1
        # Label(userFrame, 'Preserve contour colours', grid=(row, 0), **_alignLabel)
        self.contourCheckBox = CheckBox(userFrame, text='Preserve contour colours', checked=True, grid=(row, 1))

        row += 1
        userFrame.addSpacer(5, 5, grid=(row, 1), expandX=True, expandY=True)

    def populate(self, userFrame):
        """populate the widgets
        """
        with self.blockWidgetSignals(userFrame):
            if self.spectrum:
                # update all widgets to correct settings
                self.spectrumPulldown.set(self.spectrum.pid)
                self._setSpectrumCallback(self.spectrum.pid)
                self._setMethodCallback(self.methodPulldown.currentText())
                self._checkboxCallback()

    def _setDataStore(self, path=None):
        """Set the dataStore to path or autogenerate based on the various settings when None
        """
        if self.spectrum is None:
            raise RuntimeError(f'Undefined spectrum, cannot set DataStore instance')

        _saveInside = self.saveInProjectCheckBox.get()
        _projectionAxis = self.projectionAxisPulldown.get()
        _name = f'{self.spectrum.name}_{_projectionAxis}_projection'
        if path is not None:
            # Using the DataStore object will preserve any redirections and assures versioning (i.e. no overwriting)
            self.dataStore = DataStore.newFromPath(path=path,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.saveDataFormat)
        elif _saveInside:
            # Using the DataStore object sets the $INSIDE redirection and assures versioning (i.e. no overwriting)
            self.dataStore = DataStore.newFromPath(path=self.project.spectraPath / _name,
                                                   autoRedirect=True,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.saveDataFormat)
        else:
            # Using the DataStore object will preserve any redirections and assures versioning (i.e. no overwriting)
            _path = Path(self.spectrum.filePath).parent / _name
            self.dataStore = DataStore.newFromPath(path=_path,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.saveDataFormat)

    def _setSpectrumCallback(self, spectrumPid):
        """Callback for selecting spectrum
        """
        self.spectrum = self.project.getByPid(spectrumPid)
        self.infoWidget.set(f'{self.spectrum.dataSource._fileInfoString2}')
        self.projectionAxisPulldown.setData(self.spectrum.axisCodes)
        self.projectionAxisPulldown.set(self.spectrum.axisCodes[0])
        self.thresholdData.set(self.spectrum.positiveContourBase)
        self._setDataStore()
        self.outPathWidget.setText(self.dataStore.path.asString())

    def _checkboxCallback(self):
        """Callback for checkbox"""
        checked = self.autoPathCheckBox.get()
        if checked:
            self._setDataStore()
            self.outPathWidget.set(self.dataStore.path.asString())
        self.outPathWidget.setEditable(not checked)
        self.fileButton.setEnabled(not checked)

    def _saveInProjectCallback(self):
        """Callback for saveInProject checkbox
        """
        self._setDataStore()
        self.outPathWidget.set(self.dataStore.path.asString())

    def _fileButtonCallback(self):
        """Callback when pressing file button"""
        _dialog = ExportFileDialog(parent=self, acceptMode='open',
                                   directory=self.dataStore.aPath().parent.asString(),
                                   selectFile=self.dataStore.aPath().name
                                  )
        _dialog.exec_()
        newPath = _dialog.selectedFile()
        # if not iterable then ignore - dialog may return string or tuple(<path>, <fileOptions>)
        if isinstance(newPath, tuple) and len(newPath) > 0:
            newPath = newPath[0]
        self._setDataStore(newPath)
        self.outPathWidget.set(self.dataStore.path.asString())

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
        """Make projection from the specified spectrum.
        """
        # get options
        # Update the dataStore, as the widget might have been edited
        newPath = self.outPathWidget.get()
        self.dataStore.path = newPath

        if self.spectrum is not None:
            axisCodes = self.axisCodes
            method = self.methodPulldown.currentText()
            threshold = self.thresholdData.get()

            with progressManager(self, 'Making %s projection from %s' % ('-'.join(axisCodes), self.spectrum.name)):
                projectedSpectrum = self.spectrum.extractProjectionToFile(axisCodes, method=method, threshold=threshold,
                                                                          dataFormat=self.dataStore.dataFormat,
                                                                          path=self.dataStore.path
                                                                          )
                if not self.contourCheckBox.get():
                    # settings are copied by default from the originating spectrum
                    projectedSpectrum._setDefaultContourColours()

        else:
            raise RuntimeError(f'Spectrum is undefined')

        self.accept()


def main():
    from ccpn.ui.gui.widgets.Application import newTestApplication

    app = newTestApplication()
    dialog = SpectrumProjectionPopup()
    dialog.exec_()


if __name__ == '__main__':
    main()
