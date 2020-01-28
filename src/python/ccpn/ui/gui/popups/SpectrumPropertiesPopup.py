"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-01-28 03:30:44 +0000 (Tue, January 28, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5 import QtWidgets, QtCore
from itertools import permutations
from collections import Iterable
from ccpn.core.Spectrum import MAXALIASINGRANGE, Spectrum
from collections import OrderedDict
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.popups.ExperimentTypePopup import _getExperimentTypes
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown, \
    colourNameNoSpace, _setColourPulldown, getSpectrumColour
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.util.Logging import getLogger
from ccpn.util.Constants import DEFAULT_ISOTOPE_DICT
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.DialogButtonBox import DialogButtonBox
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply, _verifyPopupTabApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.core.lib.SpectrumLib import getContourLevelsFromNoise
from ccpn.core.lib.ContextManagers import queueStateChange
from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraForSpectrumPopup


SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 1, 5)  # l, t, r, b
SELECTALL = '<All>'


def _updateGl(self, spectrumList):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    # # spawn a redraw of the contours
    # for spec in spectrumList:
    #     for specViews in spec.spectrumViews:
    #         specViews.buildContours = True

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


class SpectrumPropertiesPopupABC(CcpnDialogMainWidget):
    # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
    # The apply button then steps through each tab, and calls each function in the _changes dictionary
    # in order to set the parameters.

    MINIMUM_WIDTH_PER_TAB = 120
    MINIMUM_WIDTH = 500

    def __init__(self, parent=None, mainWindow=None, spectrum=None,
                 title='Spectrum Properties', **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.spectrum = spectrum

        self.tabWidget = Tabs(self.mainWidget, setLayout=True, grid=(0, 0), focusPolicy='strong')

        # enable the buttons
        self.setOkButton(callback=self._okClicked)
        self.setApplyButton(callback=self._applyClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

    def __postInit__(self):
        """post initialise functions
        """
        super().__postInit__()

        self.tabs = tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))
        self._populate()

        self._applyButton = self.getButton(self.APPLYBUTTON)
        self._revertButton = self.getButton(self.RESETBUTTON)

    def _fillPullDowns(self):
        """Set the primary classType for the child list attached to this container
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            pass

    def _populate(self):
        """Set the primary classType for the child list attached to this container
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _revertClicked(self):
        """Revert button signal comes here
        Revert (roll-back) the state of the project to before the popup was opened
        """
        if self.project and self.project._undo:
            # with undoStackBlocking():
            for undos in range(self._currentNumApplies):
                self.project._undo.undo()

        self._populate()
        self._applyButton.setEnabled(False)
        self._revertButton.setEnabled(False)

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets

        This is controlled by a series of dicts that contain change functions - operations that are scheduled
        by changing items in the popup. These functions are executed when the Apply or OK buttons are clicked

        Return True unless any errors occurred
        """

        if not self.tabs:
            raise RuntimeError("Code error: tabs not implemented")

        # get the list of widgets that have been changed - exit if all empty
        allChanges = any(t._changes for t in self.tabs if t is not None)
        if not allChanges:
            return True

        # handle clicking of the Apply/OK button
        with handleDialogApply(self) as error:

            # get the list of spectra that have changed - for refreshing the displays
            spectrumList = []
            for t in self.tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        spectrumList.append(t.spectrum)

            # add an undo item to redraw these spectra
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateGl, self, spectrumList))

            # apply all functions to the spectra
            for t in self.tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        self._applyAllChanges(changes)

            # add a redo item to redraw these spectra
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_updateGl, self, spectrumList))

            # rebuild the contours as required
            for spec in spectrumList:
                for specViews in spec.spectrumViews:
                    specViews.buildContours = True
            _updateGl(self, spectrumList)

        # everything has happened - disable the apply button
        self._applyButton.setEnabled(False)

        # check for any errors
        if error.errorValue:
            # repopulate popup on an error
            self._populate()
            return False

        # remove all changes
        for tab in self.tabs:
            tab._changes = {}

        self._currentNumApplies += 1
        self._revertButton.setEnabled(True)
        return True

    def copySpectra(self, fromSpectrum, toSpectra):
        """Copy the contents of tabs to other spectra
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")


class SpectrumPropertiesPopup(SpectrumPropertiesPopupABC):
    # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
    # The apply button then steps through each tab, and calls each function in the _changes dictionary
    # in order to set the parameters.

    def __init__(self, parent=None, mainWindow=None, spectrum=None,
                 title='Spectrum Properties', **kwds):

        super().__init__(parent=parent, mainWindow=mainWindow,
                         spectrum=spectrum, title=title, **kwds)

        if spectrum.dimensionCount == 1:
            self._generalTab = GeneralTab(parent=self, mainWindow=self.mainWindow, spectrum=spectrum)
            self._dimensionsTab = DimensionsTab(parent=self, mainWindow=self.mainWindow,
                                                spectrum=spectrum, dimensions=spectrum.dimensionCount)

            self.tabWidget.addTab(self._generalTab, "General")
            self.tabWidget.addTab(self._dimensionsTab, "Dimensions")
            self._contoursTab = None
        else:
            self._generalTab = GeneralTab(parent=self, mainWindow=self.mainWindow, spectrum=spectrum)
            self._dimensionsTab = DimensionsTab(parent=self, mainWindow=self.mainWindow,
                                                spectrum=spectrum, dimensions=spectrum.dimensionCount)
            self._contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=spectrum, showCopyOptions=False)

            self.tabWidget.addTab(self._generalTab, "General")
            self.tabWidget.addTab(self._dimensionsTab, "Dimensions")
            self.tabWidget.addTab(self._contoursTab, "Contours")

        # don't forget to call postInit to finish initialise
        self.__postInit__()

    def _fillPullDowns(self):
        if self.spectrum.dimensionCount == 1:
            fillColourPulldown(self._generalTab.colourBox, allowAuto=False)
        else:
            fillColourPulldown(self._contoursTab.positiveColourBox, allowAuto=False)
            fillColourPulldown(self._contoursTab.negativeColourBox, allowAuto=False)

    def _populate(self):
        """Populate the widgets in the tabs
        """
        with self.blockWidgetSignals():
            if self._generalTab:
                self._generalTab._populateGeneral()
            if self._dimensionsTab:
                self._dimensionsTab._populateDimension()
            if self._contoursTab:
                self._contoursTab._populateColour()

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return (self._generalTab, self._dimensionsTab, self._contoursTab)


class SpectrumDisplayPropertiesPopupNd(SpectrumPropertiesPopupABC):
    """All spectra in the current display are added as tabs
    The apply button then steps through each tab, and calls each function in the _changes dictionary
    in order to set the parameters.
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, orderedSpectrumViews=None,
                 title='SpectrumDisplay Properties', **kwds):
        super().__init__(parent=parent, mainWindow=mainWindow,
                         spectrum=spectrum, title=title, **kwds)

        self.orderedSpectrumViews = orderedSpectrumViews
        self.orderedSpectra = OrderedSet([spec.spectrum for spec in self.orderedSpectrumViews])

        self.tabWidget.setFixedWidth(self.MINIMUM_WIDTH)

        for specNum, thisSpec in enumerate(self.orderedSpectra):
            contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec,
                                      showCopyOptions=True if len(self.orderedSpectra) > 1 else False,
                                      copyToSpectra=self.orderedSpectra)
            self.tabWidget.addTab(contoursTab, thisSpec.name)
            contoursTab.setContentsMargins(*TABMARGINS)

        # self.tabWidget.setFixedWidth(self.MINIMUM_WIDTH)
        self.tabWidget.setTabClickCallback(self._tabClicked)

        # don't forget to call postInit to finish initialise
        self.__postInit__()

    def _fillPullDowns(self):
        # should be handled by _populate?
        for aTab in self.tabs:
            fillColourPulldown(aTab.positiveColourBox, allowAuto=False)
            fillColourPulldown(aTab.negativeColourBox, allowAuto=False)

    def _populate(self):
        """Populate the widgets in the tabs
        """
        with self.blockWidgetSignals():
            for aTab in self.tabs:
                aTab._populateColour()

    def _tabClicked(self, index):
        """Callback for clicking a tab - needed for refilling the checkboxes and populating the pulldown
        """
        if hasattr(self.tabs[index], '_populateCheckBoxes'):
            self.tabs[index]._populateCheckBoxes()

    def copySpectra(self, fromSpectrum, toSpectra):
        """Copy the contents of tabs to other spectra
        """
        for aTab in self.tabs:
            if aTab.spectrum == fromSpectrum:
                fromSpectrumTab = aTab
                for aTab in [tab for tab in self.tabs if tab != fromSpectrumTab and tab.spectrum in toSpectra]:
                    aTab._copySpectrumAttributes(fromSpectrumTab)

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))


class SpectrumDisplayPropertiesPopup1d(SpectrumPropertiesPopupABC):
    """All spectra in the current display are added as tabs
    The apply button then steps through each tab, and calls each function in the _changes dictionary
    in order to set the parameters.
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, orderedSpectrumViews=None,
                 title='SpectrumDisplay Properties', **kwds):

        super().__init__(parent=parent, mainWindow=mainWindow,
                         spectrum=spectrum, title=title, **kwds)

        self.orderedSpectrumViews = orderedSpectrumViews
        self.orderedSpectra = [spec.spectrum for spec in self.orderedSpectrumViews]

        for specNum, thisSpec in enumerate(self.orderedSpectra):
            colourTab = ColourTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec,
                                  showCopyOptions=True if len(self.orderedSpectra) > 1 else False,
                                  copyToSpectra=self.orderedSpectra
                                  )
            self.tabWidget.addTab(colourTab, thisSpec.name)
            colourTab.setContentsMargins(*TABMARGINS)

        self.tabWidget.setFixedWidth(self.MINIMUM_WIDTH)
        self.tabWidget.setTabClickCallback(self._tabClicked)

        # don't forget to call postInit to finish initialise
        self.__postInit__()

    def _fillPullDowns(self):
        # should be handled by _populate?
        for aTab in self.tabs:
            fillColourPulldown(aTab.colourBox, allowAuto=False)

    def _populate(self):
        """Populate the widgets in the tabs
        """
        with self.blockWidgetSignals():
            for aTab in self.tabs:
                aTab._populateColour()

    def _tabClicked(self, index):
        """Callback for clicking a tab - needed for refilling the checkboxes and populating the pulldown
        """
        if hasattr(self.tabs[index], '_populateCheckBoxes'):
            self.tabs[index]._populateCheckBoxes()

    def copySpectra(self, fromSpectrum, toSpectra):
        """Copy the contents of tabs to other spectra
        """
        for aTab in self.tabs:
            if aTab.spectrum == fromSpectrum:
                fromSpectrumTab = aTab
                for aTab in [tab for tab in self.tabs if tab != fromSpectrumTab and tab.spectrum in toSpectra]:
                    aTab._copySpectrumAttributes(fromSpectrumTab)

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))


class GeneralTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, item=None, colourOnly=False):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)  # ejb
        self.setWindowTitle("Spectrum Properties")

        self._parent = parent
        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project

        self.item = item
        self.spectrum = spectrum
        self._changes = OrderedDict()
        self.atomCodes = ()

        self.experimentTypes = spectrum._project._experimentTypeMap

        row = 0
        self.layout().addItem(QtWidgets.QSpacerItem(row, 5), 0, 0)
        #GST adds a correctly sized right margin
        Spacer(self, 5, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum,
               grid=(row, 3))
        row += 1

        Label(self, text="PID ", vAlign='t', hAlign='l', grid=(row, 0))
        # self.layout().addItem(QtWidgets.QSpacerItem(0, 5), 0, 0)
        self.spectrumPidLabel = Label(self, vAlign='t', grid=(row, 1))
        row += 1

        Label(self, text="Name ", grid=(row, 0))
        self.nameData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1))
        # self.nameData.setText(spectrum.name)
        self.nameData.textChanged.connect(partial(self._queueSpectrumNameChange, spectrum))  # ejb - was editingFinished
        row += 1

        # add validate frame
        self._validateFrame = ValidateSpectraForSpectrumPopup(self, mainWindow=self.mainWindow, spectra=(spectrum,),
                                                              setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 3))

        self._validateFrame._filePathCallback = self._queueSetValidateFilePath
        self._validateFrame._dataUrlCallback = self._queueSetValidateDataUrl
        self._validateFrame._matchFilePathWidths = self
        row += 1

        # self.pathLabel = Label(self, text="Path", vAlign='t', hAlign='l', grid=(row, 0))
        # self.pathData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1))
        # self.pathData.setValidator(SpectrumValidator(parent=self.pathData, spectrum=spectrum))
        # self.pathButton = Button(self, grid=(row, 2), callback=partial(self._getSpectrumFile, spectrum, option='_HELP_'), icon='icons/directory')
        # row += 1

        # self.pathLabel.setVisible(False)
        # self.pathData.setVisible(False)
        # self.pathButton.setVisible(False)

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()  # self.spectrum.project._logger

        # self.spectrumData = OrderedDict()
        # self.spectrumData[spectrum] = (self.pathData, self.pathButton, Label)
        # self._setPathData(spectrum)
        # self.pathData.textEdited.connect(partial(self._queueSetSpectrumPath, spectrum, option='_HELP_'))

        # try:
        #     index = spectrum.project.chemicalShiftLists.index(spectrum.chemicalShiftList)
        # except:
        #     index = 0
        Label(self, text="ChemicalShiftList ", vAlign='t', hAlign='l', grid=(row, 0))
        self.chemicalShiftListPulldown = PulldownList(self, vAlign='t', grid=(row, 1),
                                                      # texts=[csList.pid for csList in spectrum.project.chemicalShiftLists] + ['<New>'],
                                                      callback=partial(self._queueChemicalShiftListChange, spectrum))
        row += 1

        Label(self, text="Sample", vAlign='t', hAlign='l', grid=(row, 0))
        self.samplesPulldownList = PulldownList(self, texts=['None'], objects=[None], vAlign='t', grid=(row, 1))
        # for sample in spectrum.project.samples:
        #     self.samplesPulldownList.addItem(sample.name, sample)
        # if spectrum.sample is not None:
        #     self.samplesPulldownList.select(spectrum.sample.name)
        # self.samplesPulldownList.activated[str].connect(partial(self._queueSampleChange, spectrum))
        self.samplesPulldownList.currentIndexChanged.connect(partial(self._queueSampleChange, spectrum))
        row += 1

        if spectrum.dimensionCount == 1:
            Label(self, text="Colour", vAlign='t', hAlign='l', grid=(row, 0))
            self.colourBox = PulldownList(self, vAlign='t', grid=(row, 1))

            # populate initial pulldown
            # spectrumColourKeys = list(spectrumColours.keys())
            fillColourPulldown(self.colourBox, allowAuto=False)
            # c = spectrum.sliceColour
            # if c in spectrumColourKeys:
            #     self.colourBox.setCurrentText(spectrumColours[c])
            # else:
            #     addNewColourString(c)
            #     fillColourPulldown(self.colourBox, allowAuto=False)
            #     spectrumColourKeys = list(spectrumColours.keys())
            #     self.colourBox.setCurrentText(spectrumColours[c])

            self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))
            colourButton = Button(self, vAlign='t', hAlign='l', grid=(row, 2), hPolicy='fixed',
                                  callback=partial(self._queueSetSpectrumColour, spectrum), icon='icons/colours')
            row += 1

            Label(self, text="Experiment Type ", vAlign='t', hAlign='l', grid=(row, 0))
            self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(row, 1))
            spButton = Button(self, grid=(row, 2),
                              callback=partial(self._raiseExperimentFilterPopup, spectrum),
                              hPolicy='fixed', icon='icons/applications-system')

            # experimentTypes = _getExperimentTypes(spectrum.project, spectrum)
            # self.spectrumType.setData(texts=list(experimentTypes.keys()), objects=list(experimentTypes.values()))

            # Added to account for renaming of experiments
            self.spectrumType.activated.connect(partial(self._queueSetSpectrumType, spectrum))
            # if spectrum.experimentType is not None:
            #     self.spectrumType.select(spectrum.experimentType)
            row += 1

            Label(self, text="Spinning rate (Hz)", grid=(row, 0), hAlign='l')
            self.spinningRateData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=100000.0)
            self.spinningRateData.valueChanged.connect(partial(self._queueSpinningRateChange, spectrum, self.spinningRateData.textFromValue))
            row += 1

            Label(self, text="Temperature", grid=(row, 0), hAlign='l')
            self.temperatureData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=1000.0)
            self.temperatureData.valueChanged.connect(partial(self._queueTemperatureChange, spectrum, self.temperatureData.textFromValue))
            row += 1

            Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(row, 0))
            self.spectrumScalingData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0.1, max=100.0)
            # self.spectrumScalingData.setValue(spectrum.scale)
            self.spectrumScalingData.valueChanged.connect(partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))
            row += 1

            Label(self, text="Date Recorded ", vAlign='t', hAlign='l', grid=(row, 0))
            Label(self, text='n/a', vAlign='t', hAlign='l', grid=(row, 1))
            row += 1

            Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(row, 0))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', hAlign='l', grid=(row, 1))

            # if spectrum.noiseLevel is not None:
            #     self.noiseLevelData.setValue(spectrum.noiseLevel)
            # else:
            #     self.noiseLevelData.setValue(0)
            self.noiseLevelData.valueChanged.connect(partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))
            row += 1

        else:
            Label(self, text="Experiment Type ", vAlign='t', hAlign='l', grid=(row, 0))
            self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(row, 1))
            spButton = Button(self, grid=(row, 2),
                              callback=partial(self._raiseExperimentFilterPopup, spectrum),
                              hPolicy='fixed', icon='icons/applications-system')
            # experimentTypes = _getExperimentTypes(spectrum.project, spectrum)
            # if experimentTypes:
            #     self.spectrumType.setData(texts=list(experimentTypes.keys()), objects=list(experimentTypes.values()))

            # axisCodes = []
            # for isotopeCode in spectrum.isotopeCodes:
            #   axisCodes.append(''.join([code for code in isotopeCode if not code.isdigit()]))
            #
            # self.atomCodes = tuple(sorted(axisCodes))
            # itemsList = list(self.experimentTypes[spectrum.dimensionCount].get(self.atomCodes).keys())
            # self.spectrumType.addItems(itemsList)
            # Get the text that was used in the pulldown from the refExperiment
            # NBNB This could possibly give unpredictable results
            # if there is an experiment with experimentName (user settable!)
            # that happens to match the synonym for a different experiment type.
            # But if people will ignore our defined vocabulary, on their head be it!
            # Anyway, tha alternative (discarded) is to look into the ExpPrototype
            # to compare RefExperiment names and synonyms
            # or (too ugly for words) to have a third attribute in parallel with
            # spectrum.experimentName and spectrum.experimentType
            # text = spectrum.experimentName
            # if experimentTypes and text not in experimentTypes:
            #     text = spectrum.experimentType
            # # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
            # # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
            # # Added to account for renaming of experiments
            # text = priorityNameRemapping.get(text, text)
            # self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

            self.spectrumType.activated.connect(partial(self._queueSetSpectrumType, spectrum))
            # self.spectrumType.setMinimumWidth(self.pathData.width() * 1.95)
            # self.spectrumType.setFixedHeight(25)
            row += 1

            Label(self, text="Spinning rate (Hz)", grid=(row, 0), hAlign='l')
            self.spinningRateData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=100000.0)
            self.spinningRateData.valueChanged.connect(partial(self._queueSpinningRateChange, spectrum, self.spinningRateData.textFromValue))
            row += 1

            Label(self, text="Temperature", grid=(row, 0), hAlign='l')
            self.temperatureData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=1000.0)
            self.temperatureData.valueChanged.connect(partial(self._queueTemperatureChange, spectrum, self.temperatureData.textFromValue))
            row += 1

            spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', grid=(row, 0))
            self.spectrumScalingData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0.1, max=100.0)
            # self.spectrumScalingData.setValue(spectrum.scale)
            self.spectrumScalingData.valueChanged.connect(partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))
            row += 1

            noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(row, 0))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1))
            row += 1
            # if spectrum.noiseLevel is None:
            #     self.noiseLevelData.setValue(spectrum.estimateNoise())
            # else:
            #     self.noiseLevelData.setValue(spectrum.noiseLevel)
            self.noiseLevelData.valueChanged.connect(partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))

            self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    # def _setPathDataFromUrl(self, spectrum, newFilePath):
    #     """Set the pathData widgets from the filePath
    #     Creates a temporary dataUrl to get the required data location
    #     """
    #     # from ValidateSpectraPopup...
    #     if spectrum and spectrum in self.spectrumData:
    #         pathData, pathButton, pathLabel = self.spectrumData[spectrum]
    #
    #         dataUrl = spectrum.project._wrappedData.root.fetchDataUrl(newFilePath)
    #
    #         # apiDataStore = spectrum._apiDataSource.dataStore
    #
    #         # Different methods for accessing the apiUrls
    #         # standardStore = spectrum.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
    #         # stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls()
    #         #           for url in store.sortedDataStores() if url == dataUrl.url]
    #         # urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]
    #
    #         # get the list of dataUrls
    #         apiDataStores = [store for store in dataUrl.sortedDataStores() if store.fullPath == newFilePath]
    #         if not apiDataStores:
    #             return
    #
    #         apiDataStore = apiDataStores[0]
    #
    #         if not apiDataStore:
    #             pathData.setText('<None>')
    #         elif apiDataStore.dataLocationStore.name == 'standard':
    #
    #             # this fails on the first loading of V2 projects - ordering issue?
    #             dataUrlName = apiDataStore.dataUrl.name
    #             if dataUrlName == 'insideData':
    #                 pathData.setText('$INSIDE/%s' % apiDataStore.path)
    #             elif dataUrlName == 'alongsideData':
    #                 pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
    #             elif dataUrlName == 'remoteData':
    #                 pathData.setText('$DATA/%s' % apiDataStore.path)
    #         else:
    #             pathData.setText(apiDataStore.fullPath)
    #
    #         pathData.validator().resetCheck()

    # def _setPathData(self, spectrum):
    #     """Set the pathData widgets from the spectrum.
    #     """
    #     # from ValidateSpectraPopup...
    #     if spectrum and spectrum in self.spectrumData:
    #         pathData, pathButton, pathLabel = self.spectrumData[spectrum]
    #
    #         apiDataStore = spectrum._apiDataSource.dataStore
    #         if not apiDataStore:
    #             pathData.setText('<None>')
    #         elif apiDataStore.dataLocationStore.name == 'standard':
    #
    #             # this fails on the first loading of V2 projects - ordering issue?
    #             dataUrlName = apiDataStore.dataUrl.name
    #             if dataUrlName == 'insideData':
    #                 pathData.setText('$INSIDE/%s' % apiDataStore.path)
    #             elif dataUrlName == 'alongsideData':
    #                 pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
    #             elif dataUrlName == 'remoteData':
    #                 pathData.setText('$DATA/%s' % apiDataStore.path)
    #         else:
    #             pathData.setText(apiDataStore.fullPath)
    #
    #         pathData.validator().resetCheck()

    def _populateGeneral(self):
        """Populate general tab from self.spectrum
        Blocking to be performed by tab container
        """
        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        # clear all changes
        self._changes = OrderedDict()

        self._validateFrame._populate()

        self.spectrumPidLabel.setText(self.spectrum.pid)
        self.nameData.setText(self.spectrum.name)
        # self.pathData.setValidator(SpectrumValidator(parent=self.pathData, spectrum=self.spectrum))

        # self.spectrumData[self.spectrum] = (self.pathData, self.pathButton, Label)
        # self._setPathData(self.spectrum)

        try:
            index = self.spectrum.project.chemicalShiftLists.index(self.spectrum.chemicalShiftList)
        except:
            index = 0
        self.chemicalShiftListPulldown.setData([csList.pid for csList in self.spectrum.project.chemicalShiftLists] + ['<New>'])
        self.chemicalShiftListPulldown.setIndex(index)

        self.samplesPulldownList.clear()
        for sample in self.spectrum.project.samples:
            self.samplesPulldownList.addItem(sample.name, sample)
        if self.spectrum.sample is not None:
            self.samplesPulldownList.select(self.spectrum.sample.name)

        # add the colour button just for 1d spectra
        if self.spectrum.dimensionCount == 1:
            _setColourPulldown(self.colourBox, self.spectrum.sliceColour)

        experimentTypes = _getExperimentTypes(self.spectrum.project, self.spectrum)
        texts = ('',) + tuple(experimentTypes.keys()) if experimentTypes else ()
        objects = ('',) + tuple(experimentTypes.values()) if experimentTypes else ()
        # self.spectrumType.setData(texts=list(experimentTypes.keys()), objects=list(experimentTypes.values()))
        self.spectrumType.setData(texts=texts, objects=objects)

        # if self.spectrum.experimentType is not None:
        #     self.spectrumType.select(self.spectrum.experimentType)
        text = self.spectrum.experimentName
        if experimentTypes and text not in experimentTypes:
            text = self.spectrum.experimentType
        # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
        # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
        # Added to account for renaming of experiments
        text = priorityNameRemapping.get(text, text)
        self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

        value = self.spectrum.spinningRate
        if value:
            self.spinningRateData.setValue(value)
        value = self.spectrum.temperature
        if value:
            self.temperatureData.setValue(value)

        if self.spectrum.scale is not None:
            self.spectrumScalingData.setValue(self.spectrum.scale)

        if self.spectrum.noiseLevel is not None:
            self.noiseLevelData.setValue(self.spectrum.noiseLevel)
        else:
            self.noiseLevelData.setValue(0)

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetValidateDataUrl(self, dataUrl, newUrl, urlValid, dim):
        """Set the new url in the dataUrl
        dim is required by the decorator to give a unique id for dataUrl row
        """
        if newUrl != dataUrl.url.path:
            return partial(self._validatePreferencesDataUrl, dataUrl, newUrl, urlValid, dim)

    def _validatePreferencesDataUrl(self, dataUrl, newUrl, urlValid, dim):
        """Put the new dataUrl into the dataUrl and the preferences.general.dataPath
        Extra step incase urlValid needs to be checked
        """
        # if urlValid:
        self._validateFrame.dataUrlFunc(dataUrl, newUrl)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetValidateFilePath(self, spectrum, filePath, dim):
        """Set the new filePath for the spectrum
        dim is required by the decorator to give a unique id for filePath row
        """
        if filePath != spectrum.filePath:
            return partial(self._validateFrame.filePathFunc, spectrum, filePath)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSpectrumNameChange(self, spectrum, value):
        if value != spectrum.name:
            return partial(self._changeSpectrumName, spectrum, value)

    def _changeSpectrumName(self, spectrum, name):
        spectrum.rename(name)
        self._writeLoggingMessage("spectrum.rename('%s')" % str(name))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSpectrumScaleChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.scale)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setSpectrumScale, spectrum, value)

    def _setSpectrumScale(self, spectrum, scale):
        spectrum.scale = float(scale)
        self._writeLoggingMessage("spectrum.scale = %s" % str(scale))
        self.pythonConsole.writeConsoleCommand("spectrum.scale = %s" % scale, spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueNoiseLevelDataChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.noiseLevel) if spectrum.noiseLevel else None
        if textFromValue(value) != specValue:
            return partial(self._setNoiseLevelData, spectrum, value)

    def _setNoiseLevelData(self, spectrum, noise):
        spectrum.noiseLevel = float(noise)
        self._writeLoggingMessage("spectrum.noiseLevel = %s" % str(noise))

    @queueStateChange(_verifyPopupTabApply)
    def _queueChemicalShiftListChange(self, spectrum, item):
        if item == '<New>':
            listLen = len(self.chemicalShiftListPulldown.texts)
            return partial(self._setNewChemicalShiftList, spectrum, listLen)
        else:
            value = spectrum.project.getByPid(item)
            if value and value != spectrum.chemicalShiftList:
                return partial(self._setChemicalShiftList, spectrum, item)

    def _raiseExperimentFilterPopup(self, spectrum):
        from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup

        popup = ExperimentFilterPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=spectrum)
        popup.exec_()
        self.spectrumType.select(popup.expType)

    def _setNewChemicalShiftList(self, spectrum, listLen):
        newChemicalShiftList = spectrum.project.newChemicalShiftList()
        insertionIndex = listLen - 1
        self.chemicalShiftListPulldown.texts.insert(insertionIndex, newChemicalShiftList.pid)
        self.chemicalShiftListPulldown.setData(self.chemicalShiftListPulldown.texts)
        self.chemicalShiftListPulldown.setCurrentIndex(insertionIndex)
        self.spectrum.chemicalShiftList = newChemicalShiftList
        self._writeLoggingMessage("""newChemicalShiftList = project.newChemicalShiftList()
                                spectrum.chemicalShiftList = newChemicalShiftList""")
        self.pythonConsole.writeConsoleCommand('spectrum.chemicalShiftList = chemicalShiftList', chemicalShiftList=newChemicalShiftList, spectrum=spectrum)
        self.logger.info('spectrum.chemicalShiftList = chemicalShiftList')

    def _setChemicalShiftList(self, spectrum, item):
        self.spectrum.chemicalShiftList = spectrum.project.getByPid(item)
        self.pythonConsole.writeConsoleCommand('spectrum.newChemicalShiftList = chemicalShiftList', chemicalShiftList=spectrum.chemicalShiftList,
                                               spectrum=spectrum)
        self._writeLoggingMessage("""chemicalShiftList = project.getByPid('%s')
                                  spectrum.chemicalShiftList = chemicalShiftList""" % spectrum.chemicalShiftList.pid)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSampleChange(self, spectrum, value):
        return partial(self._changeSampleSpectrum, spectrum, self.samplesPulldownList.currentObject())

    def _changeSampleSpectrum(self, spectrum, sample):
        if sample is not None:
            sample.spectra += (spectrum,)
        else:
            if spectrum.sample is not None:
                spectrum.sample = None

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetSpectrumType(self, spectrum, value):
        if self.spectrumType.getObject():
            expType = self.spectrumType.objects[value]
            if expType != spectrum.experimentType:
                return partial(self._setSpectrumType, spectrum, expType)

    def _setSpectrumType(self, spectrum, expType):
        # expType = self.experimentTypes[self.spectrum.dimensionCount].get(self.atomCodes).get(self.spectrumType.currentText())
        # expType = self.spectrumType.getObject()
        spectrum.experimentType = expType
        self.pythonConsole.writeConsoleCommand('spectrum.experimentType = experimentType', experimentType=expType, spectrum=self.spectrum)
        self._writeLoggingMessage("spectrum.experimentType = '%s'" % expType)

    # @queueStateChange(_verifyApply)
    # def _getSpectrumFile(self, spectrum, option):
    #     """Get the path from the widget and call the open dialog.
    #     option is used by the decorator to give a unique function call id
    #     """
    #     if spectrum and spectrum in self.spectrumData:
    #         pathData, pathButton, pathLabel = self.spectrumData[spectrum]
    #         filePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())
    #
    #         dialog = FileDialog(self, text='Select Spectrum File', directory=filePath,
    #                             fileMode=1, acceptMode=0,
    #                             preferences=self.application.preferences.general)
    #         directory = dialog.selectedFiles()
    #         if directory:
    #             newFilePath = directory[0]
    #
    #             if spectrum.filePath != newFilePath:
    #
    #                 from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
    #
    #                 dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
    #                 if dataType == 'Spectrum':
    #                     with undoStackBlocking():
    #                         self._setPathDataFromUrl(spectrum, newFilePath)
    #
    #                     return partial(self._setSpectrumFilePath, spectrum, newFilePath)

    # @queueStateChange(_verifyApply)
    # def _queueSetSpectrumPath(self, spectrum, option):
    #     """Get the path from the lineEdit
    #     option is used by the decorator to give a unique function call id
    #     """
    #     if spectrum and spectrum in self.spectrumData:
    #         pathData, pathButton, pathLabel = self.spectrumData[spectrum]
    #         newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())
    #
    #         if spectrum.filePath != newFilePath:
    #
    #             from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
    #
    #             dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
    #             if dataType == 'Spectrum':
    #                 return partial(self._setSpectrumFilePath, spectrum, newFilePath)

    # def _setSpectrumFilePath(self, spectrum, filePath):
    #     spectrum.filePath = filePath
    #     self._writeLoggingMessage("spectrum.filePath = '%s'" % filePath)
    #     self.pythonConsole.writeConsoleCommand("spectrum.filePath('%s')" % filePath,
    #                                            spectrum=spectrum)
    #
    #     spectrum.filePath = filePath
    #     self._setPathData(spectrum)

    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeSliceComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.sliceColour:
            return partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.colourBox.currentText()))]
        if newColour:
            spectrum.sliceColour = newColour
            self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % newColour, spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSpinningRateChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.scale)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setSpinningRate, spectrum, value)

    def _setSpinningRate(self, spectrum, value):
        spectrum.spinningRate = float(value)
        self._writeLoggingMessage("spectrum.spinningRate = %s" % str(value))
        self.pythonConsole.writeConsoleCommand("spectrum.spinningRate = %s" % value, spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueTemperatureChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.scale)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setTemperature, spectrum, value)

    def _setTemperature(self, spectrum, value):
        spectrum.temperature = float(value)
        self._writeLoggingMessage("spectrum.temperature = %s" % str(value))
        self.pythonConsole.writeConsoleCommand("spectrum.temperature = %s" % value, spectrum=spectrum)


class DimensionsTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, dimensions=None):
        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self.mainWindow = mainWindow
        self.spectrum = spectrum
        self.dimensions = dimensions
        self._changes = OrderedDict()

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()

        Label(self, text="Dimension ", grid=(1, 0), hAlign='l', vAlign='t', )

        self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)
        for i in range(dimensions):
            dimLabel = Label(self, text='%s' % str(i + 1), grid=(1, i + 1), vAlign='t', hAlign='l')

        self.axisCodeEdits = [i for i in range(dimensions)]
        self.isotopeCodePullDowns = [i for i in range(dimensions)]

        self._pointCountsLabels = [i for i in range(dimensions)]
        self._dimensionTypesLabels = [i for i in range(dimensions)]
        self._spectralWidthsLabels = [i for i in range(dimensions)]
        self._spectralWidthsHzLabels = [i for i in range(dimensions)]
        self._spectrometerFrequenciesLabels = [i for i in range(dimensions)]

        self.spectralReferencingData = [i for i in range(dimensions)]
        self.spectralReferencingDataPoints = [i for i in range(dimensions)]
        self.spectralAssignmentToleranceData = [i for i in range(dimensions)]
        self.spectralDoubleCursorOffset = [i for i in range(dimensions)]

        self.foldingModesCheckBox = [i for i in range(dimensions)]
        self.minAliasingPullDowns = [i for i in range(dimensions)]
        self.maxAliasingPullDowns = [i for i in range(dimensions)]

        row = 2
        Label(self, text="Axis Code ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Isotope Code ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Point Counts ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Dimension Type ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Spectrum Width (ppm) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Spectral Width (Hz) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Spectrometer Frequency (MHz) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Referencing (ppm) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Referencing (points)", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Assignment Tolerance ", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Second cursor offset (Hz) ", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Show folded contours", grid=(row, 0), hAlign='l')

        row += 1
        label = Label(self, text="Dimension is inverted", grid=(row, 0), hAlign='l')
        label.setEnabled(False)

        row += 1
        Label(self, text="Maximum displayed aliasing ", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Minimum displayed aliasing ", grid=(row, 0), hAlign='l')

        self._isotopeList = [code for code in DEFAULT_ISOTOPE_DICT.values() if code]

        for i in range(dimensions):
            row = 2
            # Label(self, text=str(spectrum.axisCodes[i]), grid=(row, i+1),  hAlign='l', vAlign='t',)

            # value = spectrum.axisCodes[i]
            self.axisCodeEdits[i] = LineEdit(self,
                                             # text='<None>' if value is None else str(value),
                                             grid=(row, i + 1), vAlign='t', hAlign='l')
            self.axisCodeEdits[i].textChanged.connect(partial(self._queueSetAxisCodes, spectrum,
                                                              self.axisCodeEdits[i].text, i))

            row += 1

            self.isotopeCodePullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t')
            # isotopeList = [code for code in DEFAULT_ISOTOPE_DICT.values() if code]
            self.isotopeCodePullDowns[i].setData(self._isotopeList)

            # if spectrum.isotopeCodes[i] in self._isotopeList:
            #     index = self.isotopeList.index(spectrum.isotopeCodes[i])
            #     self.isotopeCodePullDowns[i].setIndex(index)

            self.isotopeCodePullDowns[i].currentIndexChanged.connect(partial(self._queueSetIsotopeCodes, spectrum, self.isotopeCodePullDowns[i].getText, i))

            row += 1
            self._pointCountsLabels[i] = Label(self,  #text=str(spectrum.pointCounts[i]),
                                               grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            self._dimensionTypesLabels[i] = Label(self,  #text=spectrum.dimensionTypes[i],
                                                  grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            self._spectralWidthsLabels[i] = Label(self,  #text=str("%.3f" % (spectrum.spectralWidths[i] or 0.0)),
                                                  grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            self._spectralWidthsHzLabels[i] = Label(self,  #text=str("%.3f" % (spectrum.spectralWidthsHz[i] or 0.0)),
                                                    grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            self._spectrometerFrequenciesLabels[i] = Label(self,  #text=str("%.3f" % (spectrum.spectrometerFrequencies[i] or 0.0)),
                                                           grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            # value = spectrum.referenceValues[i]
            self.spectralReferencingData[i] = DoubleSpinbox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            # self.spectralReferencingData[i].setValue(value)
            self.spectralReferencingData[i].valueChanged.connect(partial(self._queueSetDimensionReferencing, spectrum, i,
                                                                         self.spectralReferencingData[i].textFromValue))

            row += 1
            # value = spectrum.referencePoints[i]
            self.spectralReferencingDataPoints[i] = DoubleSpinbox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            # self.spectralReferencingDataPoints[i].setValue(value)
            self.spectralReferencingDataPoints[i].valueChanged.connect(partial(self._queueSetPointDimensionReferencing, spectrum, i,
                                                                               self.spectralReferencingDataPoints[i].textFromValue))

            row += 1
            # value = spectrum.assignmentTolerances[i]
            self.spectralAssignmentToleranceData[i] = DoubleSpinbox(self, grid=(row, i + 1), hAlign='l', decimals=3, step=0.1)
            # self.spectralAssignmentToleranceData[i].setValue(value)
            self.spectralAssignmentToleranceData[i].valueChanged.connect(partial(self._queueSetAssignmentTolerances, spectrum, i,
                                                                                 self.spectralAssignmentToleranceData[i].textFromValue))

            row += 1
            # value = spectrum.doubleCrosshairOffsets[i]
            self.spectralDoubleCursorOffset[i] = DoubleSpinbox(self, grid=(row, i + 1), hAlign='l', decimals=3, step=0.1)
            # self.spectralDoubleCursorOffset[i].setValue(value)
            self.spectralDoubleCursorOffset[i].valueChanged.connect(partial(self._queueSetDoubleCursorOffset, spectrum, i,
                                                                            self.spectralDoubleCursorOffset[i].textFromValue))

            row += 1
            if i == 0:
                # only need 1 checkbox in the first column
                showFolded = spectrum.displayFoldedContours
                self.displayedFoldedContours = CheckBox(self, grid=(row, i + 1), vAlign='t')
                self.displayedFoldedContours.clicked.connect(partial(self._queueSetDisplayFoldedContours, spectrum, self.displayedFoldedContours.isChecked))

            row += 1
            # fModes = spectrum.foldingModes
            # dd = {'circular': False, 'mirror': True, None: False}
            self.foldingModesCheckBox[i] = CheckBox(self, grid=(row, i + 1), vAlign='t')
            # self.foldingModesCheckBox[i].setChecked(dd[fModes[i]])
            self.foldingModesCheckBox[i].clicked.connect(partial(self._queueSetFoldingModes, spectrum, self.foldingModesCheckBox[i].isChecked, i))
            # self.foldingModesCheckBox[i].setEnabled(False)

            # pullDown for min/max aliasing
            # aliasLim = spectrum.visibleAliasingRange
            # aliasMaxRange = list(range(MAXALIASINGRANGE, -1, -1))
            # aliasMinRange = list(range(0, -MAXALIASINGRANGE - 1, -1))
            # aliasMaxText = [str(aa) for aa in aliasMaxRange]
            # aliasMinText = [str(aa) for aa in aliasMinRange]

            # max aliasing
            row += 1
            self.maxAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t', )
            # texts=aliasMaxText)
            # if aliasLim[i][1] in aliasMaxRange:
            #     index = aliasMaxRange.index(aliasLim[i][1])
            #     self.maxAliasingPullDowns[i].setIndex(index)

            self.maxAliasingPullDowns[i].activated.connect(partial(self._queueSetMaxAliasing, spectrum, self.maxAliasingPullDowns[i].getText, i))

            # min aliasing
            row += 1
            self.minAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t', )
            # texts=aliasMinText)
            # if aliasLim[i][0] in aliasMinRange:
            #     index = aliasMinRange.index(aliasLim[i][0])
            #     self.minAliasingPullDowns[i].setIndex(index)

            self.minAliasingPullDowns[i].activated.connect(partial(self._queueSetMinAliasing, spectrum, self.minAliasingPullDowns[i].getText, i))

        row += 1
        hLine = HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)
        hLine.setContentsMargins(5, 0, 0, 0)

        row += 1
        self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self, labelText="Preferred Axis Order",
                                                                     grid=(row, 0), gridSpan=(1, dimensions + 1), vAlign='t')
        # self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidgetFromAxisTexts)
        # self._fillPreferredWidget()
        self.preferredAxisOrderPulldown.pulldownList.setCallback(partial(self._queueSetSpectrumOrderingComboIndex, spectrum))

        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, dimensions + 1), gridSpan=(1, 1))

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(self.spectrum.preferredAxisOrdering) if self.spectrum.preferredAxisOrdering is not None else None

        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow:
            # add permutations for the axes
            axisPerms = permutations([axisCode for axisCode in self.spectrum.axisCodes])
            axisOrder = tuple(permutations(list(range(len(self.spectrum.axisCodes)))))
            ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        if specOrder is not None and self.mainWindow:
            specIndex = axisOrder.index(specOrder) + 1
            self.preferredAxisOrderPulldown.setIndex(specIndex)

    def _fillPreferredWidgetFromAxisTexts(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(self.spectrum.preferredAxisOrdering) if self.spectrum.preferredAxisOrdering is not None else None

        axisCodeTexts = tuple([ss.text() for ss in self.axisCodeEdits])
        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow:
            # add permutations for the axes
            axisPerms = permutations([axisCode for axisCode in axisCodeTexts])
            axisOrder = tuple(permutations(list(range(len(axisCodeTexts)))))
            ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        if specOrder is not None and self.mainWindow:
            specIndex = axisOrder.index(specOrder) + 1
            self.preferredAxisOrderPulldown.setIndex(specIndex)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetSpectrumOrderingComboIndex(self, spectrum, item):
        if item:
            index = self.preferredAxisOrderPulldown.getIndex()

            axisOrder = tuple(permutations(list(range(len(spectrum.axisCodes)))))
            value = tuple(axisOrder[index - 1])
            if value != spectrum.preferredAxisOrdering:
                return partial(self._setSpectrumOrdering, spectrum, value)

    def _setSpectrumOrdering(self, spectrum, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        spectrum.preferredAxisOrdering = value
        self.pythonConsole.writeConsoleCommand("spectrum.preferredAxisOrdering = {0}".format(str(value)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.preferredAxisOrdering = {0}".format(str(value)))

    def _populateDimension(self):
        """Populate dimensions tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes = OrderedDict()

        for i in range(self.dimensions):
            value = self.spectrum.axisCodes[i]
            self.axisCodeEdits[i].setText('<None>' if value is None else str(value))

            if self.spectrum.isotopeCodes[i] in self._isotopeList:
                self.isotopeCodePullDowns[i].setIndex(self._isotopeList.index(self.spectrum.isotopeCodes[i]))

            self._pointCountsLabels[i].setText(str(self.spectrum.pointCounts[i]))
            self._dimensionTypesLabels[i].setText(self.spectrum.dimensionTypes[i])
            self._spectralWidthsLabels[i].setText(str("%.3f" % (self.spectrum.spectralWidths[i] or 0.0)))
            self._spectralWidthsHzLabels[i].setText(str("%.3f" % (self.spectrum.spectralWidthsHz[i] or 0.0)))
            self._spectrometerFrequenciesLabels[i].setText(str("%.3f" % (self.spectrum.spectrometerFrequencies[i] or 0.0)))

            value = self.spectrum.referenceValues[i]
            if value:
                self.spectralReferencingData[i].setValue(value)

            value = self.spectrum.referencePoints[i]
            if value:
                self.spectralReferencingDataPoints[i].setValue(value)

            value = self.spectrum.assignmentTolerances[i]
            if value:
                self.spectralAssignmentToleranceData[i].setValue(value)

            value = self.spectrum.doubleCrosshairOffsets[i]
            if value:
                self.spectralDoubleCursorOffset[i].setValue(value)

            if i == 0:
                # hack just to show one
                value = self.spectrum.displayFoldedContours
                self.displayedFoldedContours.setChecked(value)

            fModes = self.spectrum.foldingModes
            dd = {'circular': False, 'mirror': True, None: False}
            self.foldingModesCheckBox[i].setChecked(dd[fModes[i]])

            # pullDown for min/max aliasing
            aliasLim = self.spectrum.visibleAliasingRange
            aliasMaxRange = list(range(MAXALIASINGRANGE, -1, -1))
            aliasMinRange = list(range(0, -MAXALIASINGRANGE - 1, -1))
            aliasMaxText = [str(aa) for aa in aliasMaxRange]
            aliasMinText = [str(aa) for aa in aliasMinRange]

            self.maxAliasingPullDowns[i].setData(aliasMaxText)

            if aliasLim[i][1] in aliasMaxRange:
                index = aliasMaxRange.index(aliasLim[i][1])
                self.maxAliasingPullDowns[i].setIndex(index)

            self.minAliasingPullDowns[i].setData(aliasMinText)

            if aliasLim[i][0] in aliasMinRange:
                index = aliasMinRange.index(aliasLim[i][0])
                self.minAliasingPullDowns[i].setIndex(index)

        self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidgetFromAxisTexts)

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetAssignmentTolerances(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.assignmentTolerances[dim] or 0.0)  # this means they are not being set
        if textFromValue(value) != specValue:
            return partial(self._setAssignmentTolerances, spectrum, dim, value)

    def _setAssignmentTolerances(self, spectrum, dim, value):
        assignmentTolerances = list(spectrum.assignmentTolerances)
        assignmentTolerances[dim] = float(value)
        spectrum.assignmentTolerances = assignmentTolerances
        self.pythonConsole.writeConsoleCommand("spectrum.assignmentTolerances = {0}".format(assignmentTolerances), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.assignmentTolerances = {0}".format(assignmentTolerances))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetDoubleCursorOffset(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.doubleCrosshairOffsets[dim])
        if textFromValue(value) != specValue:
            return partial(self._setDoubleCursorOffset, spectrum, dim, value)

    def _setDoubleCursorOffset(self, spectrum, dim, value):
        doubleCrosshairOffsets = list(spectrum.doubleCrosshairOffsets)
        doubleCrosshairOffsets[dim] = float(value)
        spectrum.doubleCrosshairOffsets = doubleCrosshairOffsets
        self.pythonConsole.writeConsoleCommand("spectrum.doubleCrosshairOffsets = {0}".format(doubleCrosshairOffsets), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.doubleCrosshairOffsets = {0}".format(doubleCrosshairOffsets))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetAxisCodes(self, spectrum, valueGetter, dim):
        value = valueGetter()
        if value != spectrum.axisCodes[dim]:
            return partial(self._setAxisCodes, spectrum, dim, value)

        # repopulate the preferred axis order pulldown
        self._fillPreferredWidgetFromAxisTexts()

    def _setAxisCodes(self, spectrum, dim, value):
        axisCodes = list(spectrum.axisCodes)
        axisCodes[dim] = str(value)
        spectrum.axisCodes = axisCodes
        showWarning('Change Axis Code', 'Caution is advised when changing axis codes\n'
                                        'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')

        self.pythonConsole.writeConsoleCommand("spectrum.axisCodes = {0}".format(axisCodes), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(axisCodes))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetIsotopeCodes(self, spectrum, valueGetter, dim):
        value = valueGetter()
        if value != spectrum.isotopeCodes[dim]:
            return partial(self._setIsotopeCodes, spectrum, dim, value)

    def _setIsotopeCodes(self, spectrum, dim, value):
        isotopeCodes = list(spectrum.isotopeCodes)
        isotopeCodes[dim] = str(value)
        spectrum.isotopeCodes = isotopeCodes
        showWarning('Change Isotope Code', 'Caution is advised when changing isotope codes\n'
                                           'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')

        self.pythonConsole.writeConsoleCommand("spectrum.isotopeCodes = {0}".format(isotopeCodes), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(isotopeCodes))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referenceValues[dim])
        if textFromValue(value) != specValue:
            return partial(self._setDimensionReferencing, spectrum, dim, value)

    def _setDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referenceValues)
        spectrumReferencing[dim] = float(value)
        spectrum.referenceValues = spectrumReferencing
        self.pythonConsole.writeConsoleCommand("spectrum.referenceValues = {0}".format(spectrumReferencing), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(spectrumReferencing))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetPointDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referencePoints[dim])
        if textFromValue(value) != specValue:
            return partial(self._setPointDimensionReferencing, spectrum, dim, value)

    def _setPointDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referencePoints)
        spectrumReferencing[dim] = float(value)
        spectrum.referencePoints = spectrumReferencing
        self.pythonConsole.writeConsoleCommand("spectrum.referencePoints = {0}".format(spectrumReferencing), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referencePoints = {0}".format(spectrumReferencing))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetMinAliasing(self, spectrum, valueGetter, dim):
        minValue = int(valueGetter())
        if minValue != spectrum.visibleAliasingRange[dim][1]:
            returnVal = partial(self._setMinAliasing, self.spectrum, dim, minValue)
            maxValue = self.maxAliasingPullDowns[dim].get()
            if isinstance(maxValue, int) and isinstance(minValue, int) and minValue > maxValue:
                self.maxAliasingPullDowns[dim].select(str(minValue))
            return returnVal

    def _setMinAliasing(self, spectrum, dim, value):
        alias = list(spectrum.visibleAliasingRange)
        value = int(value)

        alias[dim] = (value, max(alias[dim][1], value))
        spectrum.visibleAliasingRange = tuple(alias)

        self.pythonConsole.writeConsoleCommand("spectrum.visibleAliasingRange = {0}".format(tuple(alias)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.visibleAliasingRange = {0}".format(tuple(alias)))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetMaxAliasing(self, spectrum, valueGetter, dim):
        maxValue = int(valueGetter())
        if maxValue != spectrum.visibleAliasingRange[dim][0]:
            returnVal = partial(self._setMaxAliasing, spectrum, dim, maxValue)
            minValue = self.minAliasingPullDowns[dim].get()
            if isinstance(maxValue, int) and isinstance(minValue, int) and maxValue < minValue:
                self.minAliasingPullDowns[dim].select(str(maxValue))
            return returnVal

    def _setMaxAliasing(self, spectrum, dim, value):
        alias = list(spectrum.visibleAliasingRange)
        value = int(value)
        alias[dim] = (min(alias[dim][0], value), value)
        spectrum.visibleAliasingRange = tuple(alias)

        self.pythonConsole.writeConsoleCommand("spectrum.visibleAliasingRange = {0}".format(tuple(alias)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.aliasingLimits = {0}".format(tuple(alias)))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetFoldingModes(self, spectrum, valueGetter, dim):
        dd = {True: 'mirror', False: 'circular', None: None}
        value = dd[valueGetter()]
        if value != spectrum.foldingModes[dim]:
            return partial(self._setFoldingModes, spectrum, dim, value)

    def _setFoldingModes(self, spectrum, dim, value):
        folding = list(spectrum.foldingModes)
        folding[dim] = value
        spectrum.foldingModes = tuple(folding)

        self.pythonConsole.writeConsoleCommand("spectrum.foldingModes = {0}".format(tuple(folding)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.foldingModes = {0}".format(tuple(folding)))

    @queueStateChange(_verifyPopupTabApply)
    def _queueSetDisplayFoldedContours(self, spectrum, valueGetter):
        value = valueGetter()
        if value != spectrum.displayFoldedContours:
            return partial(self._setDisplayFoldedContours, spectrum, value)

    def _setDisplayFoldedContours(self, spectrum, value):
        spectrum.displayFoldedContours = bool(value)

        self.pythonConsole.writeConsoleCommand("spectrum.displayFoldedContours = {0}".format(spectrum.displayFoldedContours), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.displayFoldedContours = {0}".format(spectrum.displayFoldedContours))


class ContoursTab(Widget):

    def __init__(self, parent=None, mainWindow=None, spectrum=None, showCopyOptions=False, copyToSpectra=None):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.preferences = self.application.preferences

        # check that the spectrum and the copyToSpectra list are correctly defined
        getByPid = self.application.project.getByPid
        self.spectrum = getByPid(spectrum) if isinstance(spectrum, str) else spectrum
        if not isinstance(self.spectrum, (Spectrum, type(None))):
            raise TypeError('spectrum must be of type Spectrum or None')

        if not isinstance(copyToSpectra, (Iterable, type(None))):
            raise TypeError('copyToSpectra must be of type Iterable/None')
        if copyToSpectra:
            self._copyToSpectra = [getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in copyToSpectra]
            for spec in self._copyToSpectra:
                if not isinstance(spec, (Spectrum, type(None))):
                    raise TypeError('copyToSpectra is not defined correctly.')
        else:
            self._copyToSpectra = None

        # store the options for which spectra to copy to when clicking the copy button (if active)
        self._showCopyOptions = showCopyOptions

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()

        self._changes = OrderedDict()
        self._copyWidgetSet = set()

        row = 0
        col = 1
        self._checkBoxCol = 4

        #GST adds a correctly sized right margin
        Spacer(self, 5, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum,
               grid=(row, 3))
        self.layout().addItem(QtWidgets.QSpacerItem(0, 10), row, col)

        # if showCopyOptions:
        copyLabel = Label(self, text="Copy Selected\nAttribute", grid=(row, self._checkBoxCol), vAlign='t', hAlign='l')
        self._addToCopyWidgetSet(copyLabel)

        row += 1
        self._topRow = row
        linkContoursLabel = Label(self, text="Link Contours", grid=(row, col), vAlign='t', hAlign='l')
        self.linkContoursCheckBox = CheckBox(self, grid=(row, col + 1), checked=True, vAlign='t', hAlign='l')

        row += 1
        positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(row, col), vAlign='t', hAlign='l')
        self.positiveContoursCheckBox = CheckBox(self, grid=(row, col + 1), vAlign='t', hAlign='l')
        # self.positiveContoursCheckBox.setChecked(self.spectrum.includePositiveContours)
        self.positiveContoursCheckBox.stateChanged.connect(partial(self._queueChangePositiveContourDisplay, spectrum))

        row += 1
        positiveContourBaseLabel = Label(self, text="Positive Base Level", grid=(row, col), vAlign='c', hAlign='l')
        self.positiveContourBaseData = ScientificDoubleSpinBox(self, grid=(row, col + 1), vAlign='t', min=0.1, max=1e12)
        # self.positiveContourBaseData.setValue(self.spectrum.positiveContourBase)
        self.positiveContourBaseData.valueChanged.connect(partial(self._queueChangePositiveContourBase, spectrum, self.positiveContourBaseData.textFromValue))

        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.positiveContourBaseData.setSingleStep(self.positiveContourBaseData.value() * 0.1)

        row += 1
        positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(row, col), vAlign='c', hAlign='l')
        self.positiveMultiplierData = DoubleSpinbox(self, grid=(row, col + 1), vAlign='t', min=0.0, decimals=3, step=0.1)
        # self.positiveMultiplierData.setValue(float(self.spectrum.positiveContourFactor))
        self.positiveMultiplierData.valueChanged.connect(partial(self._queueChangePositiveContourFactor, spectrum, self.positiveMultiplierData.textFromValue))

        row += 1
        positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(row, col), vAlign='c', hAlign='l')
        self.positiveContourCountData = Spinbox(self, grid=(row, col + 1), vAlign='t')
        # self.positiveContourCountData.setValue(int(self.spectrum._apiDataSource.positiveContourCount))
        self.positiveContourCountData.valueChanged.connect(partial(self._queueChangePositiveContourCount, spectrum))

        row += 1
        positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(row, col), vAlign='c', hAlign='l')
        self.positiveColourBox = PulldownList(self, grid=(row, col + 1), vAlign='t')
        self.negativeColourBox = PulldownList(self, grid=(row, col + 1), vAlign='t')

        # populate initial pulldown
        spectrumColourKeys = list(spectrumColours.keys())
        fillColourPulldown(self.positiveColourBox, allowAuto=False)
        fillColourPulldown(self.negativeColourBox, allowAuto=False)

        # c = self.spectrum.positiveContourColour
        # if c in spectrumColourKeys:
        #     col = spectrumColours[c]
        #     self.positiveColourBox.setCurrentText(col)
        # else:
        #     addNewColourString(c)
        #     fillColourPulldown(self.positiveColourBox, allowAuto=False)
        #     fillColourPulldown(self.negativeColourBox, allowAuto=False)
        #     spectrumColourKeys = list(spectrumColours.keys())
        #     col = spectrumColours[c]
        #     self.positiveColourBox.setCurrentText(col)

        self.positiveColourButton = Button(self, grid=(row, col + 2), vAlign='t', hAlign='l',
                                           icon='icons/colours', hPolicy='fixed')
        self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, spectrum))

        row += 1
        negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(row, col), vAlign='c', hAlign='l')
        self.negativeContoursCheckBox = CheckBox(self, grid=(row, col + 1), vAlign='t', hAlign='l')
        # self.negativeContoursCheckBox.setChecked(self.spectrum.includeNegativeContours)
        self.negativeContoursCheckBox.stateChanged.connect(partial(self._queueChangeNegativeContourDisplay, spectrum))

        row += 1
        negativeContourBaseLabel = Label(self, text="Negative Base Level", grid=(row, col), vAlign='c', hAlign='l')
        self.negativeContourBaseData = ScientificDoubleSpinBox(self, grid=(row, col + 1), vAlign='t', min=-1e12, max=-0.1)
        # self.negativeContourBaseData.setValue(-abs(self.spectrum.negativeContourBase))

        self.negativeContourBaseData.valueChanged.connect(partial(self._queueChangeNegativeContourBase, spectrum, self.negativeContourBaseData.textFromValue))

        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.negativeContourBaseData.setSingleStep((self.negativeContourBaseData.value() * -1) * 0.1)

        row += 1
        negativeMultiplierLabel = Label(self, text="Negative Multiplier", grid=(row, col), vAlign='c', hAlign='l')
        self.negativeMultiplierData = DoubleSpinbox(self, grid=(row, col + 1), vAlign='t', min=0.0, decimals=3, step=0.1)
        # self.negativeMultiplierData.setValue(self.spectrum.negativeContourFactor)
        self.negativeMultiplierData.valueChanged.connect(partial(self._queueChangeNegativeContourFactor, spectrum, self.negativeMultiplierData.textFromValue))

        row += 1
        negativeContourCountLabel = Label(self, text="Number of negative contours", grid=(row, col), vAlign='c', hAlign='l')
        self.negativeContourCountData = Spinbox(self, grid=(row, col + 1), vAlign='t')
        # self.negativeContourCountData.setValue(self.spectrum.negativeContourCount)
        self.negativeContourCountData.valueChanged.connect(partial(self._queueChangeNegativeContourCount, spectrum))

        row += 1
        negativeContourColourLabel = Label(self, text="Negative Contour Colour", grid=(row, col), vAlign='c', hAlign='l')

        # c = self.spectrum.negativeContourColour
        # if c in spectrumColourKeys:
        #     self.negativeColourBox.setCurrentText(spectrumColours[c])
        # else:
        #     addNewColourString(c)
        #     fillColourPulldown(self.positiveColourBox, allowAuto=False)
        #     fillColourPulldown(self.negativeColourBox, allowAuto=False)
        #     spectrumColourKeys = list(spectrumColours.keys())
        #     self.negativeColourBox.setCurrentText(spectrumColours[c])

        self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, spectrum))
        self.negativeColourBox.currentIndexChanged.connect(partial(self._queueChangeNegColourComboIndex, spectrum))

        self.negativeColourButton = Button(self, grid=(row, col + 2), icon='icons/colours', hPolicy='fixed',
                                           vAlign='t', hAlign='l')
        self.negativeColourButton.clicked.connect(partial(self._queueChangeNegSpectrumColour, spectrum))

        # move to the correct row
        self.getLayout().addWidget(self.negativeColourBox, row, col + 1)

        # if showCopyOptions:
        # add a column of checkBoxes on the left for copying across spectra

        self._copyList = (self._copyLinkContours,
                          self._copyShowPositive,
                          self._copyPositiveBaseLevel,
                          self._copyPositiveMultiplier,
                          self._copyPositiveContours,
                          self._copyPositiveContourColour,
                          self._copyShowNegative,
                          self._copyNegativeBaseLevel,
                          self._copyNegativeMultiplier,
                          self._copyNegativeContours,
                          self._copyNegativeContourColour)

        self._copyCheckBoxes = []

        # add the checkboxes and keep a list of selected in the preferences (so it will be saved)
        if self.preferences.general._copySpectraSettings and len(self.preferences.general._copySpectraSettings) == len(self._copyList):
            # read existing settings
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=self.preferences.general._copySpectraSettings[rr], hAlign='c')
                self._copyCheckBoxes.append(thisCheckBox)
                thisCheckBox.setCallback(partial(self._copyButtonClicked, thisCheckBox, rr))

                self._addToCopyWidgetSet(thisCheckBox)
        else:
            # create a new list in preferences
            self.preferences.general._copySpectraSettings = [True] * len(self._copyList)
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=True, hAlign='c')
                self._copyCheckBoxes.append(thisCheckBox)
                thisCheckBox.setCallback(partial(self._copyButtonClicked, thisCheckBox, rr))

                self._addToCopyWidgetSet(thisCheckBox)

        # add the spectrum selection pulldown to the bottom and a copy action button
        self._copyToSpectraPullDown = PulldownListCompoundWidget(self, labelText="Copy to",
                                                                 grid=(len(self._copyList) + self._topRow, 0),
                                                                 gridSpan=(1, self._checkBoxCol + 1), vAlign='t', hAlign='r')
        self._copyButton = Button(self, text='Copy', grid=(len(self._copyList) + self._topRow + 1, self._checkBoxCol), hAlign='r',
                                  callback=self._copyActionClicked)

        self._addToCopyWidgetSet(self._copyToSpectraPullDown)
        self._addToCopyWidgetSet(self._copyButton)

        # end showCopyList widgets

        # TODO:ED populate _copyToSpectraPullDown here or __init__

        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row + 3, col + 1), gridSpan=(1, 1))

    def _addToCopyWidgetSet(self, widget):
        """Add widgets to a set so that we can set visible/invisible at any time
        """
        if not self._copyWidgetSet:
            self._copyWidgetSet = set()
        self._copyWidgetSet.add(widget)
        widget.setVisible(self._showCopyOptions)

    def _setContourLevels(self):
        """Estimate the contour levels for the current spectrum
        """
        posBase, negBase, posMult, negMult, posLevels, negLevels = getContourLevelsFromNoise(self.spectrum, setNoiseLevel=False,
                                                                                             setPositiveContours=self.setPositiveContours.isChecked(),
                                                                                             setNegativeContours=self.setNegativeContours.isChecked(),
                                                                                             useSameMultiplier=self.setUseSameMultiplier.isChecked(),
                                                                                             useDefaultLevels=self.setDefaults.isChecked(),
                                                                                             useDefaultMultiplier=self.setDefaults.isChecked())

        # put the new values into the widgets (will queue changes)
        if posBase:
            self.positiveContourBaseData.setValue(posBase)
        if negBase:
            self.negativeContourBaseData.setValue(negBase)
        if posMult:
            self.positiveMultiplierData.setValue(posMult)
        if negMult:
            self.negativeMultiplierData.setValue(negMult)
        if posLevels:
            self.positiveContourCountData.setValue(posLevels)
        if negLevels:
            self.negativeContourCountData.setValue(negLevels)

    def _populateColour(self):
        """Populate colour tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes = OrderedDict()

        self.positiveContoursCheckBox.setChecked(self.spectrum.includePositiveContours)
        self.positiveContourBaseData.setValue(self.spectrum.positiveContourBase)
        self.positiveMultiplierData.setValue(float(self.spectrum.positiveContourFactor))
        self.positiveContourCountData.setValue(int(self.spectrum._apiDataSource.positiveContourCount))
        _setColourPulldown(self.positiveColourBox, self.spectrum.positiveContourColour)

        self.negativeContoursCheckBox.setChecked(self.spectrum.includeNegativeContours)
        self.negativeContourBaseData.setValue(-abs(self.spectrum.negativeContourBase))
        self.negativeMultiplierData.setValue(self.spectrum.negativeContourFactor)
        self.negativeContourCountData.setValue(self.spectrum.negativeContourCount)
        _setColourPulldown(self.negativeColourBox, self.spectrum.negativeContourColour)

        # if self._showCopyOptions:
        self._populateCheckBoxes()

    def _populateCheckBoxes(self):
        """Populate the checkbox from preferences and fill the pullDown from the list of spectra
        """
        if not hasattr(self, '_copyCheckBoxes'):
            return

        checkBoxList = self.preferences.general._copySpectraSettings
        if checkBoxList:
            for cc, checkBox in enumerate(checkBoxList):
                state = checkBoxList[cc]
                self._copyCheckBoxes[cc].setChecked(state)
        if self._copyToSpectra:
            texts = ['<All>'] + [spectrum.pid for spectrum in self._copyToSpectra if spectrum != self.spectrum]
            self._copyToSpectraPullDown.modifyTexts(texts)

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)

    def _cleanWidgetQueue(self):
        """Clean the items from the stateChange queue
        """
        self._changes = OrderedDict()

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangePositiveContourDisplay(self, spectrum, state):
        if (state == QtCore.Qt.Checked) != spectrum.includePositiveContours:
            return partial(self._changePositiveContourDisplay, spectrum, state)

    def _changePositiveContourDisplay(self, spectrum, state):
        if state == QtCore.Qt.Checked:
            spectrum.includePositiveContours = True
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayPositiveContours = True
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayPositiveContours = True")
        else:
            self.spectrum.includePositiveContours = False
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayPositiveContours = False
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayPositiveContours = False")

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeNegativeContourDisplay(self, spectrum, state):
        if (state == QtCore.Qt.Checked) != spectrum.includeNegativeContours:
            return partial(self._changeNegativeContourDisplay, spectrum, state)

    def _changeNegativeContourDisplay(self, spectrum, state):
        if state == QtCore.Qt.Checked:
            spectrum.includeNegativeContours = True
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayNegativeContours = True
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayNegativeContours = True")
        else:
            spectrum.includeNegativeContours = False
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayNegativeContours = False
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayNegativeContours = False")

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangePositiveContourBase(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.positiveContourBase)
        if value >= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changePositiveContourBase, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeContourBaseData.set(-value)
        return returnVal

    def _changePositiveContourBase(self, spectrum, value):
        spectrum.positiveContourBase = float(value)
        self._writeLoggingMessage("spectrum.positiveContourBase = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourBase = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangePositiveContourFactor(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.positiveContourFactor)
        if value >= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changePositiveContourFactor, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeMultiplierData.set(value)
        return returnVal

    def _changePositiveContourFactor(self, spectrum, value):
        spectrum.positiveContourFactor = float(value)
        self._writeLoggingMessage("spectrum.positiveContourFactor = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourFactor = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangePositiveContourCount(self, spectrum, value):
        if value >= 0 and value != spectrum.positiveContourCount:
            returnVal = partial(self._changePositiveContourCount, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeContourCountData.set(value)
        return returnVal

    def _changePositiveContourCount(self, spectrum, value):
        spectrum.positiveContourCount = int(value)
        self._writeLoggingMessage("spectrum.positiveContourCount = %d" % int(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourCount = %d" % int(value), spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeNegativeContourBase(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.negativeContourBase)
        if value <= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changeNegativeContourBase, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveContourBaseData.set(-value)
        return returnVal

    def _changeNegativeContourBase(self, spectrum, value):
        # force to be negative
        value = -abs(value)
        spectrum.negativeContourBase = float(value)
        self._writeLoggingMessage("spectrum.negativeContourBase = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourBase = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeNegativeContourFactor(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.negativeContourFactor)
        if value >= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changeNegativeContourFactor, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveMultiplierData.set(value)
        return returnVal

    def _changeNegativeContourFactor(self, spectrum, value):
        spectrum.negativeContourFactor = float(value)
        self._writeLoggingMessage("spectrum.negativeContourFactor = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourFactor = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeNegativeContourCount(self, spectrum, value):
        if value >= 0 and value != spectrum.negativeContourCount:
            returnVal = partial(self._changeNegativeContourCount, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveContourCountData.set(value)
        return returnVal

    def _changeNegativeContourCount(self, spectrum, value):
        spectrum.negativeContourCount = int(value)
        self._writeLoggingMessage("spectrum.negativeContourCount = %d" % int(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourCount = %d" % int(value), spectrum=spectrum)

    # spectrum negativeContourColour button and pulldown
    def _queueChangePosSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.positiveColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangePosColourComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.positiveContourColour:
            return partial(self._changePosColourComboIndex, spectrum, value)

    def _changePosColourComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.positiveColourBox.currentText()))]
        if newColour:
            spectrum.positiveContourColour = newColour
            self._writeLoggingMessage("spectrum.positiveContourColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.positiveContourColour = '%s'" % newColour, spectrum=spectrum)

    # spectrum negativeContourColour button and pulldown
    def _queueChangeNegSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.negativeColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeNegColourComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.negativeContourColour:
            return partial(self._changeNegColourComboIndex, spectrum, value)

    def _changeNegColourComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.negativeColourBox.currentText()))]
        if newColour:
            spectrum.negativeContourColour = newColour
            self._writeLoggingMessage("spectrum.negativeContourColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.negativeContourColour = '%s'" % newColour, spectrum=spectrum)

    # methods for copying the spectrum attributes to the others in the pulldown
    # should be contained within the undo/revert mechanism

    def _copyLinkContours(self, fromSpectrumTab):
        state = fromSpectrumTab.linkContoursCheckBox.get()
        self.linkContoursCheckBox.set(state)

    def _copyShowPositive(self, fromSpectrumTab):
        state = fromSpectrumTab.positiveContoursCheckBox.get()
        self.positiveContoursCheckBox.set(state)

    def _copyPositiveBaseLevel(self, fromSpectrumTab):
        value = fromSpectrumTab.positiveContourBaseData.get()
        self.positiveContourBaseData.set(value)

    def _copyPositiveMultiplier(self, fromSpectrumTab):
        value = fromSpectrumTab.positiveMultiplierData.get()
        self.positiveMultiplierData.set(value)

    def _copyPositiveContours(self, fromSpectrumTab):
        value = fromSpectrumTab.positiveContourCountData.get()
        self.positiveContourCountData.set(value)

    def _copyPositiveContourColour(self, fromSpectrumTab):
        name = fromSpectrumTab.positiveColourBox.currentText()
        colour = getSpectrumColour(name, defaultReturn='#')
        _setColourPulldown(self.positiveColourBox, colour)

    def _copyShowNegative(self, fromSpectrumTab):
        state = fromSpectrumTab.negativeContoursCheckBox.get()
        self.negativeContoursCheckBox.set(state)

    def _copyNegativeBaseLevel(self, fromSpectrumTab):
        value = fromSpectrumTab.negativeContourBaseData.get()
        self.negativeContourBaseData.set(value)

    def _copyNegativeMultiplier(self, fromSpectrumTab):
        value = fromSpectrumTab.negativeMultiplierData.get()
        self.negativeMultiplierData.set(value)

    def _copyNegativeContours(self, fromSpectrumTab):
        value = fromSpectrumTab.negativeContourCountData.get()
        self.negativeContourCountData.set(value)

    def _copyNegativeContourColour(self, fromSpectrumTab):
        name = fromSpectrumTab.negativeColourBox.currentText()
        colour = getSpectrumColour(name, defaultReturn='#')
        _setColourPulldown(self.negativeColourBox, colour)

    def _copyButtonClicked(self, checkBox, checkBoxIndex, state):
        """Set the state of the checkBox in preferences
        """
        checkBoxList = self.preferences.general._copySpectraSettings
        if checkBoxList and checkBoxIndex < len(checkBoxList):
            checkBoxList[checkBoxIndex] = state

    def _copyActionClicked(self):
        """Copy action clicked - call the copy method from the parent Tab widget
        """
        if self._showCopyOptions:
            toSpectraPids = self._copyToSpectraPullDown.getText()
            if toSpectraPids == SELECTALL:
                toSpectra = [spectrum for spectrum in self._copyToSpectra if spectrum != self.spectrum]
            else:
                toSpectra = [self.application.project.getByPid(toSpectraPids)]

            # call the parent tab copy action
            self._parent.copySpectra(self.spectrum, toSpectra)

    def _copySpectrumAttributes(self, fromSpectrumTab):
        """Copy the attributes to the other spectra
        """
        if self._showCopyOptions:
            checkBoxList = self.preferences.general._copySpectraSettings
            if checkBoxList and len(checkBoxList) == len(self._copyList):
                for cc, copyFunc in enumerate(self._copyList):
                    # call the copy function if checked
                    if checkBoxList[cc] and self.spectrum and fromSpectrumTab.spectrum:
                        copyFunc(fromSpectrumTab)

                    # toSpectraPids = self._copyToSpectraPullDown.getText()
                    # if toSpectraPids == SELECTALL:
                    #     for toSpectrum in [spectrum for spectrum in self._copyToSpectra if spectrum != self.spectrum]:
                    #         copyFunc(self.spectrum, toSpectrum)
                    # else:
                    #     toSpectrum = self.application.project.getByPid(toSpectraPids)
                    #     if toSpectrum:
                    #         copyFunc(self.spectrum, toSpectrum)

    def setCopyOptionsVisible(self, value):
        """Show/hide the copyOptions widgets
        """
        if not isinstance(value, bool):
            raise TypeError('Error: value must be a boolean')

        self._showCopyOptions = value
        for widg in self._copyWidgetSet:
            widg.setVisible(value)


class ColourTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, item=None, colourOnly=False,
                 showCopyOptions=False, copyToSpectra=None):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project
        self.preferences = self.application.preferences

        # check that the spectrum and the copyToSpectra list are correctly defined
        getByPid = self.application.project.getByPid
        self.spectrum = getByPid(spectrum) if isinstance(spectrum, str) else spectrum
        if not isinstance(self.spectrum, (Spectrum, type(None))):
            raise TypeError('spectrum must be of type Spectrum or None')

        if not isinstance(copyToSpectra, (Iterable, type(None))):
            raise TypeError('copyToSpectra must be of type Iterable/None')
        if copyToSpectra:
            self._copyToSpectra = [getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in copyToSpectra]
            for spec in self._copyToSpectra:
                if not isinstance(spec, (Spectrum, type(None))):
                    raise TypeError('copyToSpectra is not defined correctly.')
        else:
            self._copyToSpectra = None

        self.item = item
        self.spectrum = spectrum
        self._changes = OrderedDict()
        self.atomCodes = ()

        self._showCopyOptions = showCopyOptions

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()

        self._copyWidgetSet = set()
        self._topRow = 7
        self._checkBoxCol = 4

        # if showCopyOptions:
        copyLabel = Label(self, text="Copy Selected\nAttribute", grid=(self._topRow-1, self._checkBoxCol), vAlign='t', hAlign='l')
        self._addToCopyWidgetSet(copyLabel)

        Label(self, text="Colour", vAlign='t', hAlign='l', grid=(7, 0))
        self.colourBox = PulldownList(self, vAlign='t', grid=(7, 1))

        # populate initial pulldown
        fillColourPulldown(self.colourBox, allowAuto=False)
        self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))

        # add a colour dialog button
        self.colourButton = Button(self, vAlign='t', hAlign='l', grid=(7, 2),
                                   icon='icons/colours', hPolicy='fixed')
        self.colourButton.clicked.connect(partial(self._queueSetSpectrumColour, spectrum))

        self._copyList = (self._copyPositiveContourColour,
                          )

        self._copyCheckBoxes = []

        # add the checkboxes and keep a list of selected in the preferences (so it will be saved)
        if self.preferences.general._copySpectraSettings and len(self.preferences.general._copySpectraSettings) == len(self._copyList):
            # read existing settings
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=self.preferences.general._copySpectraSettings[rr], hAlign='c')
                self._copyCheckBoxes.append(thisCheckBox)
                thisCheckBox.setCallback(partial(self._copyButtonClicked, thisCheckBox, rr))

                self._addToCopyWidgetSet(thisCheckBox)
        else:
            # create a new list in preferences
            self.preferences.general._copySpectraSettings = [True] * len(self._copyList)
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=True, hAlign='c')
                self._copyCheckBoxes.append(thisCheckBox)
                thisCheckBox.setCallback(partial(self._copyButtonClicked, thisCheckBox, rr))

                self._addToCopyWidgetSet(thisCheckBox)

        # add the spectrum selection pulldown to the bottom and a copy action button
        self._copyToSpectraPullDown = PulldownListCompoundWidget(self, labelText="Copy to",
                                                                 grid=(len(self._copyList) + self._topRow, 0),
                                                                 gridSpan=(1, self._checkBoxCol + 1), vAlign='t', hAlign='r')
        self._copyButton = Button(self, text='Copy', grid=(len(self._copyList) + self._topRow + 1, self._checkBoxCol), hAlign='r',
                                  callback=self._copyActionClicked)

        self._addToCopyWidgetSet(self._copyToSpectraPullDown)
        self._addToCopyWidgetSet(self._copyButton)

    def _populateColour(self):
        """Populate dimensions tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes = OrderedDict()

        _setColourPulldown(self.colourBox, self.spectrum.sliceColour)

        # if self._showCopyOptions:
        self._populateCheckBoxes()

    def _populateCheckBoxes(self):
        """Populate the checkbox from preferences and fill the pullDown from the list of spectra
        """
        if not hasattr(self, '_copyCheckBoxes'):
            return

        checkBoxList = self.preferences.general._copySpectraSettings
        if checkBoxList:
            for cc, checkBox in enumerate(checkBoxList):
                state = checkBoxList[cc]
                self._copyCheckBoxes[cc].setChecked(state)
        if self._copyToSpectra:
            texts = ['<All>'] + [spectrum.pid for spectrum in self._copyToSpectra if spectrum != self.spectrum]
            self._copyToSpectraPullDown.modifyTexts(texts)

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)

    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupTabApply)
    def _queueChangeSliceComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.sliceColour:
            return partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.colourBox.currentText()))]
        if newColour:
            spectrum.sliceColour = newColour
            self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % newColour, spectrum=spectrum)

    def _copyPositiveContourColour(self, fromSpectrumTab):
        name = fromSpectrumTab.colourBox.currentText()
        colour = getSpectrumColour(name, defaultReturn='#')
        _setColourPulldown(self.colourBox, colour)

    def _copyButtonClicked(self, checkBox, checkBoxIndex, state):
        """Set the state of the checkBox in preferences
        """
        checkBoxList = self.preferences.general._copySpectraSettings
        if checkBoxList and checkBoxIndex < len(checkBoxList):
            checkBoxList[checkBoxIndex] = state

    def _copyActionClicked(self):
        """Copy action clicked - call the copy method from the parent Tab widget
        """
        if self._showCopyOptions:
            toSpectraPids = self._copyToSpectraPullDown.getText()
            if toSpectraPids == SELECTALL:
                toSpectra = [spectrum for spectrum in self._copyToSpectra if spectrum != self.spectrum]
            else:
                toSpectra = [self.application.project.getByPid(toSpectraPids)]

            # call the parent tab copy action
            self._parent.copySpectra(self.spectrum, toSpectra)

    def _copySpectrumAttributes(self, fromSpectrumTab):
        """Copy the attributes to the other spectra
        """
        if self._showCopyOptions:
            checkBoxList = self.preferences.general._copySpectraSettings
            if checkBoxList and len(checkBoxList) == len(self._copyList):
                for cc, copyFunc in enumerate(self._copyList):
                    # call the copy function if checked
                    if checkBoxList[cc] and self.spectrum and fromSpectrumTab.spectrum:
                        copyFunc(fromSpectrumTab)

    def setCopyOptionsVisible(self, value):
        """Show/hide the copyOptions widgets
        """
        if not isinstance(value, bool):
            raise TypeError('Error: value must be a boolean')

        self._showCopyOptions = value
        for widg in self._copyWidgetSet:
            widg.setVisible(value)

    def _addToCopyWidgetSet(self, widget):
        """Add widgets to a set so that we can set visible/invisible at any time
        """
        if not self._copyWidgetSet:
            self._copyWidgetSet = set()
        self._copyWidgetSet.add(widget)
        widget.setVisible(self._showCopyOptions)

    def _cleanWidgetQueue(self):
        """Clean the items from the stateChange queue
        """
        self._changes = OrderedDict()
