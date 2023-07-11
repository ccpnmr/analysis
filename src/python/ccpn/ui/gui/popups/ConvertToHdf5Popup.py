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
__dateModified__ = "$dateModified: 2023-07-11 16:13:16 +0100 (Tue, July 11, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-07-10 11:28:58 +0100 (Mon, July 10, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
from ccpn.core.lib.DataStore import DataStore

from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FileDialog import ExportFileDialog
from ccpn.ui.gui.widgets.Button import Button
# from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showOkCancelWarning, showInfo
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.util.Path import Path, aPath


class ConvertToHdf5Popup(CcpnDialogMainWidget):
    FIXEDHEIGHT = True
    FIXEDWIDTH = False

    def __init__(self, parent=None, mainWindow=None, title='Convert spectrum (binary) data to Hdf5', **kwds):

        # for CcpnDialogMainWidget:
        super().__init__(parent=parent, setLayout=True, windowTitle=title, **kwds)

        # self.errorFlag = False  # moved to base-class

        if mainWindow:
            self.mainWindow = mainWindow
            self.project = self.mainWindow.project
            self.application = self.mainWindow.application
        else:
            self.mainWindow = self.project = self.application = None

        self.spectrum = None  # Spectrum instance
        self.inDataSource = None  # Originating dataStore instance; keep a handle to optionally delete original spectrum data
        self.validSpectra = None  # list of valid spectra
        self.dataStore = None # DataStore instance

        if self.project:
            # Only select 3D's for now
            self.validSpectra = [sp for sp in self.project.spectra if not sp.dataSource.isEmptySpectrum]

            if not self.validSpectra:
                from ccpn.ui.gui.widgets.MessageDialog import showWarning

                showWarning('No valid spectra', 'No non-Hdf5 spectra in current project')
                self.errorFlag = True
                return

        # for CcpnDialogMainWidget:
        self.initialise(self.mainWidget)
        self.populate(self.mainWidget)
        self.actionButtons()

        # initialise the buttons and dialog size
        self._postInit()

    def actionButtons(self):
        self.setOkButton(callback=self.convertToHdf5, text='Convert to Hdf5', tipText='Convert spectrum to Hdf5 and close dialog')
        self.setCloseButton(callback=self._rejectDialog, text='Close', tipText='Close')
        self.setDefaultButton(ExportDialogABC.CLOSEBUTTON)

    def _rejectDialog(self):
        # NOTE:ED - not required for exportDialogABC
        self.reject()

    def initialise(self, userFrame):
        """Create the widgets for the userFrame
        """
        minWidth = 400

        # spectrum selection
        row = 0
        Label(userFrame, 'Spectrum', grid=(row, 0), hAlign='r')
        self.spectrumPulldown = PulldownList(userFrame, grid=(row, 1), callback=self._setSpectrumCallback)
        self.spectrumPulldown.setMinimumWidth(minWidth)

        row += 1
        Label(userFrame, 'filePath', grid=(row, 0), hAlign='r')
        self.inPathWidget = LineEdit(userFrame, textAlignment='l', grid=(row, 1), gridSpan=(1, 1), editable=False)
                                      # minimumWidth=minWidth)
        self.inPathWidget.setMinimumWidth(minWidth)
        # row += 1
        self.infoWidget = Label(userFrame, textAlignment='l', grid=(row, 3), gridSpan=(1, 1), textColour='black')
        row += 1
        self.removeInPathCheckBox = CheckBox(userFrame, text='Remove on completion',
                                             checked=False, grid=(row, 1), callback=self._removeInPathCallback)

        row += 1
        userFrame.addSpacer(10, 20, grid=(row, 1), expandX=True, expandY=True)

        row += 1
        Label(userFrame, 'Output Hdf5 path', grid=(row, 0), hAlign='r')

        # Auto-path checkbox
        self.autoPathCheckBox = CheckBox(userFrame, text='Auto generate',
                                         checked=True, grid=(row, 1), callback=self._checkboxCallback)

        # Save inside project checkbox
        row += 1
        self.saveInProjectCheckBox = CheckBox(userFrame, text='Save inside project',
                                              checked=False, grid=(row, 1), callback=self._saveInProjectCallback)

        # outpath
        row += 1
        self.outPathWidget = LineEdit(userFrame, textAlignment='l', grid=(row, 1), gridSpan=(1, 1), editable=True)
        self.outPathWidget.setMinimumWidth(minWidth)
        # self.outPathWidget.enableWidget(False)
        self.fileButton = Button(userFrame,  hPolicy='fixed', icon='icons/directory', grid=(row,3), callback=self._fileButtonCallback)
        self.fileButton.setEnabled(False)

        row += 1
        userFrame.addSpacer(5, 5, grid=(row, 1), expandX=True, expandY=True)

        self.spectrum = None
        if self.project:
            self.spectrumPulldown.setData([s.pid for s in self.validSpectra])
            self.spectrum = self.validSpectra[0]

    def populate(self, userFrame):
        """populate the widgets
        """
        with self.blockWidgetSignals(userFrame):
            if self.spectrum:
                # update all widgets to correct settings
                self.spectrumPulldown.set(self.spectrum.pid)
                self._setSpectrumCallback(self.spectrum.pid)
                self._checkboxCallback()

    def _setSpectrumCallback(self, spectrumPid):
        """Callback for selecting spectrum
        """
        self.spectrum = self.project.getByPid(spectrumPid)
        self.inDataSource = self.spectrum.dataSource

        suffix = Hdf5SpectrumDataSource.suffixes[0]
        dataFormat = Hdf5SpectrumDataSource.dataFormat
        _saveInside = self.saveInProjectCheckBox.get()
        if _saveInside:
            # Using the DataStore object sets the $INSIDE redirection and assures versioning (i.e. no overwriting)
            self.dataStore = DataStore.newFromPath(path=self.project.spectraPath / self.spectrum.name,
                                                   autoRedirect=True,
                                                   autoVersioning=True,
                                                   withSuffix=suffix,
                                                   dataFormat=dataFormat)
        else:
            # Using the DataStore object will preserve any redirections and assures versioning (i.e. no overwriting)
            self.dataStore = DataStore.newFromPath(path=self.spectrum.filePath,
                                                   autoVersioning=True,
                                                   withSuffix=suffix,
                                                   dataFormat=dataFormat)
        self.outPathWidget.setText(self.dataStore.path.asString())
        txt = f'{self.spectrum.dimensionCount}D - {self.spectrum.dataFormat} ({self.spectrum.dataSource.expectedFileSizeInBytes/(1024*1024):.1f} MB)'
        self.infoWidget.setText(txt)
        self.inPathWidget.setText(self.spectrum.filePath)

    def _checkboxCallback(self):
        """Callback for checkbox"""
        checked = self.autoPathCheckBox.get()
        self.outPathWidget.enableWidget(not checked)
        self.fileButton.setEnabled(not checked)

    def _saveInProjectCallback(self):
        """Callback for saveInProject checkbox"""
        # checked = self.autoPathCheckBox.get()
        # self.outPathWidget.enableWidget(not checked)
        pid = self.spectrumPulldown.get()
        self._setSpectrumCallback(pid)

    def _fileButtonCallback(self):
        """Callback when pressing file button"""
        _dialog = ExportFileDialog(parent=self, acceptMode='open',
                                   directory=self.dataStore.aPath().parent.asString(),
                                   selectFile=self.dataStore.aPath().name
                                  )
        _dialog.show()

    def _removeInPathCallback(self):
        """Callback for removeInPath checkbox"""
        checked = self.removeInPathCheckBox.get()

    def convertToHdf5(self):
        """Convert the selected spectrum.
        """
        removeInPath = self.removeInPathCheckBox.get()
        if self.spectrum is not None:
            with progressManager(self, f'Converting "{self.spectrum.name}" to Hdf'):
                outDataSource = self.spectrum.convertToHdf5(self.dataStore.path)

            title = f'Spectrum "{self.spectrum.name}"'
            message = f'Successfully converted the "{self.inDataSource.dataFormat}" spectral data to "{outDataSource.dataFormat}"\n'
            if removeInPath:
                files = self.inDataSource.getAllFilePaths()
                message += f'\nDo you want to delete the original {len(files)} {self.inDataSource.dataFormat}-file(s)? (Can not undo!)'
                ok = showOkCancelWarning(title, message, parent=self)
                if ok:
                    for _f in files:
                        _f.remove()
            else:
                showInfo(title, message, parent=self)

        self.accept()


# popup = ConvertToHdf5Popup(parent=mainWindow, mainWindow=mainWindow)
# popup.show()
