"""
This Module defines a ABC for popups that need to query for an output path, e.g.
ConvertSpectrumPopup, SpectrumProjectionPopup, PseudoToSpectrumGroup
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
__date__ = "$Date: 2023-07-10 11:28:58 +0100 (Mon, July 10, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
from ccpn.core.lib.DataStore import DataStore

from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit, LineEdit2
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FileDialog import ExportFileDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showOkCancelWarning, showInfo
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.util.Path import Path, aPath


class CcpnDialogWithOutputPathPopupABC(CcpnDialogMainWidget):
    """
    A dialog popup ABC that implements Widgets for selecting/querying an output path.
    Requires a spectrum; creates/maintains a dataStore instance defining the outputPath

    """

    minimumWidth = 400
    minimumHeight = 25
    _alignLabel = dict(vAlign='c', hAlign='r', minimumHeight=minimumHeight) # Keyword labels
    _align1 = dict(vAlign='c', hAlign='l', textColour='black', minimumHeight=minimumHeight)  # Data Labels
    _align2 = dict(vAlign='c', minimumWidth=minimumWidth)  # Dimensional Pulldowns / LineEdits

    _options = ['Derive from input path', 'Inside project', 'Alongside project', 'User defined']
    _OPTION_FROMPATH = 0
    _OPTION_INSIDE = 1
    _OPTION_ALONGSIDE = 2
    _OPTION_USERDEFINED = 3
    _DEFAULT_OPTION = _OPTION_FROMPATH

    _defaultDataSourceClass = Hdf5SpectrumDataSource

    def __init__(self, parent=None, mainWindow=None, title='', **kwds):

        # for CcpnDialogMainWidget:
        super().__init__(parent=parent, setLayout=True, windowTitle=title, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.project = self.mainWindow.project
            self.application = self.mainWindow.application
        else:
            self.mainWindow = self.project = self.application = None

        self.spectrum = None  # Spectrum instance
        self.validSpectra = []  # The list of valid spectra for input selection
        self.dataStore = None # DataStore instance; used to generate the output path

        # we can later add provisions for more data formats
        self.dataFormat = self._defaultDataSourceClass.dataFormat
        self.suffix = self._defaultDataSourceClass.suffixes[0]

    def initialiseSpectrumWidgets(self, userFrame, rowIndex) -> int:
        """Create the widgets for the Spectrum selection widgets
        :return next rowIndex
        """

        if self.spectrum is None:
            raise RuntimeError(f'A Spectrum instance is required for initialisation of {self.__class__.__name__}')

        # spectrum selection
        Label(userFrame, 'Input', grid=(rowIndex, 0), bold=True, **self._alignLabel)
        self.spectrumPulldown = PulldownList(userFrame, grid=(rowIndex, 1), **self._align2, callback=self._setSpectrumCallback)
        self.spectrumPulldown.setData([s.pid for s in self.validSpectra])
        rowIndex += 1

        self.inPathLabel = Label(userFrame, 'Path', grid=(rowIndex, 0), **self._alignLabel)
        self.inPathWidget = LineEdit2(userFrame, textAlignment='l', grid=(rowIndex, 1), gridSpan=(1, 1),
                                       editable=False, **self._align2)
        rowIndex += 1

        self.infoWidget = Label(userFrame, textAlignment='l', grid=(rowIndex, 1), gridSpan=(1, 1), **self._align1)
        rowIndex += 1

        return rowIndex

    def initialiseOutputPathWidgets(self, userFrame, rowIndex) -> int:
        """Create the widgets for the OutputPath selection widgets
        :return next rowIndex
        """

        if self.spectrum is None:
            raise RuntimeError(f'A Spectrum instance is required for initialisation of {self.__class__.__name__}')

        # output radio buttons; align label at top
        _align = {}
        _align.update(self._alignLabel)
        _align['vAlign'] = 't'
        Label(userFrame, 'Output', grid=(rowIndex, 0), bold=True, **_align)
        self.optionsRadioButtons = RadioButtons(userFrame, texts=self._options,
                                                direction='v', minimumHeight=self.minimumHeight*len(self._options),
                                                grid=(rowIndex, 1),
                                                callback=self._optionsCallback)
        rowIndex += 1

        # outpath
        Label(userFrame, 'Path', grid=(rowIndex, 0), **self._alignLabel)
        self.outPathWidget = LineEdit2(userFrame, textAlignment='l', grid=(rowIndex, 1), gridSpan=(1, 1), editable=True,
                                        **self._align2, callback=self._outPathCallback)
        self.fileButton = Button(userFrame,  hPolicy='fixed', icon='icons/directory', grid=(rowIndex,3), callback=self._fileButtonCallback)
        self.fileButton.setEnabled(False)
        rowIndex += 1

        return rowIndex

    def getName(self) -> str:
        """Return a string for the name of the file
        Can be subclassed
        """
        return self.spectrum.name

    def getInfoString(self) -> str:
        """Return a string for the info widget field
        Should be subclassed
        """
        return ''

    def populate(self, userFrame):
        """populate the widgets
        """
        with self.blockWidgetSignals(userFrame):
            if self.spectrum:
                # update all widgets to correct settings
                self._setSpectrumCallback(self.spectrum.pid)

    def _setDataStore(self, option=None, path=None):
        """Set the dataStore to path based on option (retrieved from radioButtons if None)
        """
        if self.spectrum is None:
            raise RuntimeError(f'Undefined spectrum, cannot set DataStore instance')

        if option is None:
            option = self.optionsRadioButtons.getIndex()

        # Using the DataStore object will preserve any redirections and assures versioning (i.e. no overwriting)
        if option == self._OPTION_USERDEFINED:
            if path is None:
                path = Path(self.spectrum.filePath).with_name(self.getName())
            self.dataStore = DataStore.newFromPath(path=path,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.dataFormat)

        elif option == self._OPTION_INSIDE:
            self.dataStore = DataStore.newFromPath(path=self.project.spectraPath / self.getName(),
                                                   autoRedirect=True,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.dataFormat)

        elif option == self._OPTION_ALONGSIDE:
            self.dataStore = DataStore.newFromPath(path=self.project.projectPath.parent / self.getName(),
                                                   autoRedirect=True,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.dataFormat)

        elif option == self._OPTION_FROMPATH:
            _path = Path(self.spectrum.filePath).with_name(self.getName())
            self.dataStore = DataStore.newFromPath(path=_path,
                                                   autoVersioning=True,
                                                   withSuffix=self.suffix,
                                                   dataFormat=self.dataFormat)

    def _setSpectrumCallback(self, spectrumPid):
        """Callback for selecting spectrum; only show infoWidget if there is an infoString to display
        """
        self.spectrum = self.project.getByPid(spectrumPid)
        self.inPathWidget.setText(self.spectrum.filePath)
        # info
        _txt = self.getInfoString()
        if len(_txt) > 0:
            self.infoWidget.setText(_txt)
            self.infoWidget.setVisible(True)
        else:
            self.infoWidget.setVisible(False)

        # Set the initial option of the radio buttons depending on spectrum path settings
        if self.spectrum._isInside:
            self.optionsRadioButtons.setIndex(self._OPTION_INSIDE)
        elif self.spectrum._isAlongside:
            self.optionsRadioButtons.setIndex(self._OPTION_ALONGSIDE)
        else:
            self.optionsRadioButtons.setIndex(self._DEFAULT_OPTION)
        self._optionsCallback()

    def _optionsCallback(self):
        """Callback for options radio buttons
        """
        option = self.optionsRadioButtons.getIndex()
        # print(f'Index = {option}; {self._options[option]}')

        self._setDataStore(option)
        if option == self._OPTION_FROMPATH:
            self.outPathWidget.setEditable(False)
            self.fileButton.setEnabled(False)

        elif option == self._OPTION_INSIDE:
            self.outPathWidget.setEditable(False)
            self.fileButton.setEnabled(False)

        elif option == self._OPTION_ALONGSIDE:
            self.outPathWidget.setEditable(False)
            self.fileButton.setEnabled(False)

        elif option == self._OPTION_USERDEFINED:
            self.outPathWidget.setEditable(True)
            self.fileButton.setEnabled(True)

        else:
            raise RuntimeError(f'Invalid choice returned; This should not happen')

        with self.blockWidgetSignals(self.outPathWidget):
            self.outPathWidget.set(self.dataStore.path.asString())

    def _outPathCallback(self):
        """Callback upon completion of entering text to the outpath widget
        """
        newPath = self.outPathWidget.get()
        self._setDataStore(self._OPTION_USERDEFINED, path=newPath)
        with self.blockWidgetSignals(self.outPathWidget):
            self.outPathWidget.set(self.dataStore.path.asString())

    def _fileButtonCallback(self):
        """Callback when pressing file button
        """
        _dialog = ExportFileDialog(parent=self, acceptMode='open',
                                   directory=self.dataStore.aPath().parent.asString(),
                                   selectFile=self.dataStore.aPath().name
                                  )
        _dialog.exec_()
        if (newPath := _dialog.selectedFile()) is None:
            # cancel was pressed
            return
        self._setDataStore(self._OPTION_USERDEFINED, path=newPath)
        with self.blockWidgetSignals(self.outPathWidget):
            self.outPathWidget.set(self.dataStore.path.asString())
