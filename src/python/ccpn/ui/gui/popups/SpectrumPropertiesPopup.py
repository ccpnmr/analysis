"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-08-20 19:26:48 +0100 (Fri, August 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
from itertools import permutations
from collections import Iterable
from ccpn.core.Spectrum import MAXALIASINGRANGE, Spectrum
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
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
from ccpn.util.Constants import DEFAULT_ISOTOPE_DICT
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply, _verifyPopupApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.core.lib.SpectrumLib import getContourLevelsFromNoise
from ccpn.core.lib.ContextManagers import queueStateChange
from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraForSpectrumPopup
from ccpn.ui.gui.lib.ChangeStateHandler import changeState, ChangeDict
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.popups.AttributeEditorPopupABC import getAttributeTipText


SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 1, 5)  # l, t, r, b
SELECTALL = '<All>'
SELECT1D = '<All 1d Spectra>'
SELECTND = '<All Nd Spectra>'


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

        self._okButton = self.getButton(self.OKBUTTON)
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

    def _getChangeState(self):
        """Get the change state of the contained widgets
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _revertClicked(self):
        """Revert button signal comes here
        Revert (roll-back) the state of the project to before the popup was opened
        """
        if self.project and self.project._undo:
            for undos in range(self._currentNumApplies):
                self.project._undo.undo()

        self._populate()
        self._okButton.setEnabled(False)
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
            tab._changes = ChangeDict()

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
            self.tabWidget.setCurrentIndex(2)

        # don't forget to call postInit to finish initialise
        self.__postInit__()

    def _fillPullDowns(self):
        if self.spectrum.dimensionCount == 1:
            self._generalTab._fillPullDowns()
        else:
            self._contoursTab._fillPullDowns()

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

    def _revertClicked(self):
        """Revert button signal comes here
        Revert (roll-back) the state of the project to before the popup was opened
        """
        # reset the references so that the pulldowns return to correct state
        self._dimensionsTab._referenceExperiment = None
        self._dimensionsTab._referenceDimensions = None
        super()._revertClicked()

    def _getChangeState(self):
        """Get the change state from the popup tabs
        """
        if not self._changes.enabled:
            return None

        applyState = True
        revertState = False
        tabs = self.getActiveTabList()
        allChanges = any(t._changes for t in tabs if t is not None)

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton, self._revertButton, self._currentNumApplies)

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

        for specNum, thisSpec in enumerate(self.orderedSpectra):
            contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec,
                                      showCopyOptions=True if len(self.orderedSpectra) > 1 else False,
                                      copyToSpectra=self.orderedSpectra)
            self.tabWidget.addTab(contoursTab, thisSpec.name)
            contoursTab.setContentsMargins(*TABMARGINS)

        self.tabWidget.setTabClickCallback(self._tabClicked)

        # don't forget to call postInit to finish initialise
        self.__postInit__()

    def _fillPullDowns(self):
        for aTab in self.tabs:
            aTab._fillPullDowns()

    def _populate(self):
        """Populate the widgets in the tabs
        """
        for aTab in self.tabs:
            aTab._populateColour()

    def _getChangeState(self):
        """Get the change state from the colour tabs
        """
        applyState = True
        revertState = False
        tabs = self.getActiveTabList()
        allChanges = any(t._changes for t in tabs if t is not None)

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton, self._revertButton, self._currentNumApplies)

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
                    try:
                        aTab._copySpectrumAttributes(fromSpectrumTab)
                    except Exception as es:
                        pass

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

        self.tabWidget.setTabClickCallback(self._tabClicked)

        # don't forget to call postInit to finish initialise
        self.__postInit__()

    def _fillPullDowns(self):
        for aTab in self.tabs:
            aTab._fillPullDowns()

    def _populate(self):
        """Populate the widgets in the tabs
        """
        for aTab in self.tabs:
            aTab._populateColour()

    def _getChangeState(self):
        """Get the change state from the colour tabs
        """
        applyState = True
        revertState = False
        tabs = self.getActiveTabList()
        allChanges = any(t._changes for t in tabs if t is not None)

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton, self._revertButton, self._currentNumApplies)

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
                    try:
                        aTab._copySpectrumAttributes(fromSpectrumTab)
                    except Exception as es:
                        pass

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
        self._changes = ChangeDict()
        self.atomCodes = ()

        self.experimentTypes = spectrum._project._experimentTypeMap

        row = 0
        self.layout().addItem(QtWidgets.QSpacerItem(row, 5), 0, 0)
        Spacer(self, 5, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum,
               grid=(row, 3))
        row += 1

        Label(self, text="Pid ", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'pid'))
        self.spectrumPidLabel = Label(self, vAlign='t', grid=(row, 1))
        row += 1

        Label(self, text="Name ", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'name'))
        self.nameData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1), backgroundText='> Enter name <')
        self.nameData.textChanged.connect(partial(self._queueSpectrumNameChange, spectrum))  # ejb - was editingFinished
        row += 1

        Label(self, text="Comment ", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'comment'))
        self.commentData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1), backgroundText='> Optional <')
        self.commentData.textChanged.connect(partial(self._queueSpectrumCommentChange, spectrum))  # ejb - was editingFinished
        row += 1

        # add validate frame
        self._validateFrame = ValidateSpectraForSpectrumPopup(self, mainWindow=self.mainWindow, spectra=(spectrum,),
                                                              setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 3))

        self._validateFrame._filePathCallback = self._queueSetValidateFilePath
        self._validateFrame._dataUrlCallback = self._queueSetValidateDataUrl
        self._validateFrame._matchFilePathWidths = None
        row += 1

        Label(self, text="Chemical Shift List ", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'chemicalShiftList'))
        self.chemicalShiftListPulldown = PulldownList(self, vAlign='t', grid=(row, 1),
                                                      callback=partial(self._queueChemicalShiftListChange, spectrum))
        row += 1

        Label(self, text="Sample", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'sample'))
        self.samplesPulldownList = PulldownList(self, vAlign='t', grid=(row, 1))
        self.samplesPulldownList.currentIndexChanged.connect(partial(self._queueSampleChange, spectrum))
        row += 1

        if spectrum.dimensionCount == 1:
            Label(self, text="Colour", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'sliceColour'))
            self.colourBox = PulldownList(self, vAlign='t', grid=(row, 1))

            # populate initial pulldown
            fillColourPulldown(self.colourBox, allowAuto=False, includeGradients=False)

            self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))
            colourButton = Button(self, vAlign='t', hAlign='l', grid=(row, 2), hPolicy='fixed',
                                  callback=partial(self._queueSetSpectrumColour, spectrum), icon='icons/colours')
            row += 1

            Label(self, text="Reference Experiment Type ", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'experimentType'))
            self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(row, 1))
            spButton = Button(self, grid=(row, 2),
                              callback=partial(self._raiseExperimentFilterPopup, spectrum),
                              hPolicy='fixed', icon='icons/applications-system')

            # Added to account for renaming of experiments
            self.spectrumType.currentIndexChanged.connect(partial(self._queueSetSpectrumType, spectrum))
            row += 1

            Label(self, text="Spinning Rate (Hz)", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'spinningRate'))
            self.spinningRateData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=100000.0)
            self.spinningRateData.valueChanged.connect(partial(self._queueSpinningRateChange, spectrum, self.spinningRateData.textFromValue))
            row += 1

            Label(self, text="Temperature", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'temperature'))
            self.temperatureData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=1000.0)
            self.temperatureData.valueChanged.connect(partial(self._queueTemperatureChange, spectrum, self.temperatureData.textFromValue))
            row += 1

            Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'scale'))
            self.spectrumScalingData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0.1, max=100.0)
            self.spectrumScalingData.valueChanged.connect(partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))
            row += 1

            Label(self, text="Date Recorded ", vAlign='t', hAlign='l', grid=(row, 0))
            Label(self, text='n/a', vAlign='t', hAlign='l', grid=(row, 1))
            row += 1

            Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'noiseLevel'))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', hAlign='l', grid=(row, 1))

            self.noiseLevelData.valueChanged.connect(partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))
            row += 1

        else:
            _specLabel = Label(self, text="Reference Experiment Type ", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'experimentType'))
            self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(row, 1))
            _specButton = Button(self, grid=(row, 2),
                              callback=partial(self._raiseExperimentFilterPopup, spectrum),
                              hPolicy='fixed', icon='icons/applications-system')

            self.spectrumType.currentIndexChanged.connect(partial(self._queueSetSpectrumType, spectrum))
            _specLabel.setVisible(False)
            self.spectrumType.setVisible(False)
            _specButton.setVisible(False)
            row += 1

            Label(self, text="Spinning rate (Hz)", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'spinningRate'))
            self.spinningRateData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=100000.0)
            self.spinningRateData.valueChanged.connect(partial(self._queueSpinningRateChange, spectrum, self.spinningRateData.textFromValue))
            row += 1

            Label(self, text="Temperature", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'temperature'))
            self.temperatureData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0, max=1000.0)
            self.temperatureData.valueChanged.connect(partial(self._queueTemperatureChange, spectrum, self.temperatureData.textFromValue))
            row += 1

            spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'scale'))
            self.spectrumScalingData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1), min=0.1, max=100.0)
            self.spectrumScalingData.valueChanged.connect(partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))
            row += 1

            noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'noiseLevel'))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', grid=(row, 1))
            row += 1

            self.noiseLevelData.valueChanged.connect(partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))

            self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    def _fillPullDowns(self):
        if self.spectrum.dimensionCount == 1:
            fillColourPulldown(self.colourBox, allowAuto=False, includeGradients=False)

    def _populateGeneral(self):
        """Populate general tab from self.spectrum
        Blocking to be performed by tab container
        """
        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():
            self._validateFrame._populate()

            self.spectrumPidLabel.setText(self.spectrum.pid)
            self.nameData.setText(self.spectrum.name)
            self.commentData.setText(self.spectrum.comment)

            try:
                index = self.spectrum.project.chemicalShiftLists.index(self.spectrum.chemicalShiftList)
            except:
                index = 0
            self.chemicalShiftListPulldown.setData([csList.pid for csList in self.spectrum.project.chemicalShiftLists] + ['<New>'])
            self.chemicalShiftListPulldown.setIndex(index)

            self.samplesPulldownList.clear()
            # add a blank item
            self.samplesPulldownList.addItem('', None)
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
            self.spectrumType.setData(texts=texts, objects=objects)

            text = self.spectrum.experimentName
            if experimentTypes and text not in experimentTypes:
                text = self.spectrum.experimentType
            # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
            # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
            # Added to account for renaming of experiments
            text = priorityNameRemapping.get(text, text)
            self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

            value = self.spectrum.spinningRate
            self.spinningRateData.setValue(value if value is not None else 0)

            value = self.spectrum.temperature
            self.temperatureData.setValue(value if value is not None else 0)

            value = self.spectrum.scale
            self.spectrumScalingData.setValue(value if value is not None else 0)

            value = self.spectrum.noiseLevel
            self.noiseLevelData.setValue(value if value is not None else 0)

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._parent._getChangeState()

    @queueStateChange(_verifyPopupApply)
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
        self._validateFrame.dataUrlFunc(dataUrl, newUrl)

    @queueStateChange(_verifyPopupApply)
    def _queueSetValidateFilePath(self, spectrum, filePath, dim):
        """Set the new filePath for the spectrum
        dim is required by the decorator to give a unique id for filePath row
        """
        if filePath != spectrum.filePath:
            return partial(self._validateFrame.filePathFunc, spectrum, filePath)

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumNameChange(self, spectrum, value):
        if value != spectrum.name:
            return partial(self._changeSpectrumName, spectrum, value)

    def _changeSpectrumName(self, spectrum, name):
        spectrum.rename(name)

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumCommentChange(self, spectrum, value):
        if value != spectrum.comment:
            return partial(self._changeSpectrumComment, spectrum, value)

    def _changeSpectrumComment(self, spectrum, comment):
        spectrum.comment = comment

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumScaleChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.scale)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setSpectrumScale, spectrum, value)

    def _setSpectrumScale(self, spectrum, scale):
        spectrum.scale = float(scale)

    @queueStateChange(_verifyPopupApply)
    def _queueNoiseLevelDataChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.noiseLevel) if spectrum.noiseLevel else None
        if textFromValue(value) != specValue:
            return partial(self._setNoiseLevelData, spectrum, value)

    def _setNoiseLevelData(self, spectrum, noise):
        spectrum.noiseLevel = float(noise)

    @queueStateChange(_verifyPopupApply)
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

    def _setChemicalShiftList(self, spectrum, item):
        self.spectrum.chemicalShiftList = spectrum.project.getByPid(item)

    @queueStateChange(_verifyPopupApply)
    def _queueSampleChange(self, spectrum, value):
        _text, sample = self.samplesPulldownList.getSelected()
        return partial(self._changeSampleSpectrum, spectrum, sample)

    def _changeSampleSpectrum(self, spectrum, sample):
        spectrum.sample = sample

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectrumType(self, spectrum, value):
        if self.spectrumType.getObject():
            expType = self.spectrumType.objects[value]
            if expType != spectrum.experimentType:
                return partial(self._setSpectrumType, spectrum, expType)

    def _setSpectrumType(self, spectrum, expType):
        spectrum.experimentType = expType

    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangeSliceComboIndex(self, spectrum, value):
        if value >= 0:
            colName = colourNameNoSpace(self.colourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrum.sliceColour:
                # and list(spectrumColours.keys())[value] != spectrum.sliceColour:
                return partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        colName = colourNameNoSpace(self.colourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        if newColour:
            spectrum.sliceColour = newColour

    @queueStateChange(_verifyPopupApply)
    def _queueSpinningRateChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.spinningRate or 0.0)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setSpinningRate, spectrum, value)

    def _setSpinningRate(self, spectrum, value):
        spectrum.spinningRate = float(value)

    @queueStateChange(_verifyPopupApply)
    def _queueTemperatureChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.temperature or 0.0)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setTemperature, spectrum, value)

    def _setTemperature(self, spectrum, value):
        spectrum.temperature = float(value)


class DimensionsTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, dimensions=None):
        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self.mainWindow = mainWindow
        self.spectrum = spectrum
        self.dimensions = dimensions
        self._changes = ChangeDict()
        self._referenceExperiment = None
        self._referenceDimensions = None

        Label(self, text="Dimension ", grid=(1, 0), hAlign='l', vAlign='t', )

        self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)
        for i in range(dimensions):
            dimLabel = Label(self, text='%s' % str(i + 1), grid=(1, i + 1), vAlign='t', hAlign='l')

        self.axisCodeEdits = [i for i in range(dimensions)]
        self.isotopeCodePullDowns = [i for i in range(dimensions)]
        self.referenceDimensionPullDowns = [i for i in range(dimensions)]

        self._pointCountsLabels = [i for i in range(dimensions)]
        self._dimensionTypesLabels = [i for i in range(dimensions)]
        self.spectralWidthsData = [i for i in range(dimensions)]
        self.spectralWidthsHzData = [i for i in range(dimensions)]
        self.spectrometerFrequenciesData = [i for i in range(dimensions)]

        self.spectralReferencingData = [i for i in range(dimensions)]
        self.spectralReferencingDataPoints = [i for i in range(dimensions)]
        self.spectralAssignmentToleranceData = [i for i in range(dimensions)]
        self.spectralDoubleCursorOffset = [i for i in range(dimensions)]

        self.foldingModesCheckBox = [i for i in range(dimensions)]
        self.minAliasingPullDowns = [i for i in range(dimensions)]
        self.maxAliasingPullDowns = [i for i in range(dimensions)]

        row = 2
        Label(self, text="Axis Code ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'axisCodes'))

        row += 1
        Label(self, text="Isotope Code ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'isotopeCodes'))

        row += 1
        _specLabel = Label(self, text="Reference Experiment Type ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'experimentType'))

        row += 1
        _refLabel = Label(self, text="Reference Experiment Dimensions ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'referenceExperimentDimensions'))

        row += 2
        # spacer for extra button
        hLine = HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)
        hLine.setContentsMargins(5, 0, 0, 0)

        row += 1
        Label(self, text="Point Counts ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'pointCounts'))

        row += 1
        Label(self, text="Dimension Type ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'dimensionTypes'))

        row += 1
        Label(self, text="Spectrum Width (ppm) ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'spectralWidths'))

        row += 1
        Label(self, text="Spectral Width (Hz) ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'spectralWidthsHz'))

        row += 1
        Label(self, text="Spectrometer Frequency (MHz) ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'spectrometerFrequencies'))

        row += 1
        Label(self, text="Referencing (ppm) ", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'referenceValues'))

        row += 1
        Label(self, text="Referencing (points)", grid=(row, 0), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'referencePoints'))

        row += 1
        Label(self, text="Assignment Tolerance ", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'assignmentTolerances'))

        row += 1
        Label(self, text="Second Cursor Offset (Hz) ", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'doubleCrosshairOffsets'))

        row += 1
        hLine = HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)
        hLine.setContentsMargins(5, 0, 0, 0)

        row += 1
        Label(self, text="Show Aliased Regions", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Dimension is Circular", grid=(row, 0), hAlign='l', tipText=getAttributeTipText(Spectrum, 'foldingModes'))

        row += 1
        Label(self, text="Aliasing Limits         Upperbound", grid=(row, 0), hAlign='r', tipText=getAttributeTipText(Spectrum, 'aliasingLimits'))

        row += 1
        Label(self, text="Lowerbound", grid=(row, 0), hAlign='r')

        self._isotopeList = [code for code in DEFAULT_ISOTOPE_DICT.values() if code]

        # add set of widgets for each dimension
        for i in range(dimensions):
            row = 2
            self.axisCodeEdits[i] = LineEdit(self, grid=(row, i + 1), vAlign='t', hAlign='l')
            self.axisCodeEdits[i].textChanged.connect(partial(self._queueSetAxisCodes, spectrum, ))
                                                              # self.axisCodeEdits[i].text, i))

            row += 1
            self.isotopeCodePullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t')
            self.isotopeCodePullDowns[i].setData(self._isotopeList)
            self.isotopeCodePullDowns[i].currentIndexChanged.connect(partial(self._queueSetIsotopeCodes, spectrum, self.isotopeCodePullDowns[i].getText, i))

            row += 1
            if i == 0:
                # reference experiment type
                self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(row, i + 1), gridSpan=(1, dimensions))
                _specButton = Button(self, grid=(row, i + 1 + dimensions),
                                  callback=partial(self._raiseExperimentFilterPopup, spectrum),
                                  hPolicy='fixed', icon='icons/applications-system')
                # Added to account for renaming of experiments
                self.spectrumType.currentIndexChanged.connect(partial(self._queueSetSpectrumType, spectrum))

                if self.dimensions < 2:
                    # hide as not required for 1d
                    _specLabel.setVisible(False)
                    self.spectrumType.setVisible(False)
                    _specButton.setVisible(False)
                    _refLabel.setVisible(False)

            row += 1
            # reference axis codes
            _refPullDown = self.referenceDimensionPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t')
            self.referenceDimensionPullDowns[i].currentIndexChanged.connect(partial(self._queueSetReferenceDimensions, spectrum, )) #self.referenceDimensionPullDowns[i].getText, i))
            if self.dimensions < 2:
                # hide as not required for 1d
                _refPullDown.setVisible(False)

            row += 1
            if i == 0:
                # button to copy to axis Codes
                _copyBox = Frame(self, setLayout=True, grid=(row, i + 1), gridSpan=(1, dimensions))
                _copyButton = Button(_copyBox, text='Copy to Axis Codes', grid=(0, 0), hAlign='r',
                                     callback=self._copyReferenceExperiments,
                                     tipText='Copy all non-empty reference experiment dimensions to axis codes')
                if self.dimensions < 2:
                    # hide as not required for 1d
                    _copyBox.setVisible(False)

            row += 1
            # line spacer
            
            row += 1
            self._pointCountsLabels[i] = Label(self, grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            self._dimensionTypesLabels[i] = Label(self, grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            self.spectralWidthsData[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectralWidthsData[i].valueChanged.connect(partial(self._queueSetSpectralWidths, spectrum, i,
                                                                    self.spectralWidthsData[i].textFromValue))

            row += 1
            self.spectralWidthsHzData[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectralWidthsHzData[i].valueChanged.connect(partial(self._queueSetSpectralWidthsHz, spectrum, i,
                                                                      self.spectralWidthsHzData[i].textFromValue))

            row += 1
            self.spectrometerFrequenciesData[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectrometerFrequenciesData[i].valueChanged.connect(partial(self._queueSetSpectrometerFrequencies, spectrum, i,
                                                                             self.spectrometerFrequenciesData[i].textFromValue))

            row += 1
            self.spectralReferencingData[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectralReferencingData[i].valueChanged.connect(partial(self._queueSetDimensionReferencing, spectrum, i,
                                                                         self.spectralReferencingData[i].textFromValue))

            row += 1
            self.spectralReferencingDataPoints[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectralReferencingDataPoints[i].valueChanged.connect(partial(self._queueSetPointDimensionReferencing, spectrum, i,
                                                                               self.spectralReferencingDataPoints[i].textFromValue))

            row += 1
            self.spectralAssignmentToleranceData[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), hAlign='l', decimals=3, step=0.1)
            self.spectralAssignmentToleranceData[i].valueChanged.connect(partial(self._queueSetAssignmentTolerances, spectrum, i,
                                                                                 self.spectralAssignmentToleranceData[i].textFromValue))

            row += 1
            self.spectralDoubleCursorOffset[i] = ScientificDoubleSpinBox(self, grid=(row, i + 1), hAlign='l', decimals=3, step=0.1)
            self.spectralDoubleCursorOffset[i].valueChanged.connect(partial(self._queueSetDoubleCursorOffset, spectrum, i,
                                                                            self.spectralDoubleCursorOffset[i].textFromValue))

            # space
            row += 2
            if i == 0:
                # only need 1 checkbox in the first column
                spectrum.displayFoldedContours
                self.displayedFoldedContours = CheckBox(self, grid=(row, i + 1), vAlign='t')
                self.displayedFoldedContours.clicked.connect(partial(self._queueSetDisplayFoldedContours, spectrum, self.displayedFoldedContours.isChecked))

            row += 1
            self.foldingModesCheckBox[i] = CheckBox(self, grid=(row, i + 1), vAlign='t')
            self.foldingModesCheckBox[i].clicked.connect(partial(self._queueSetFoldingModes, spectrum, self.foldingModesCheckBox[i].isChecked, i))

            # max aliasing
            row += 1
            self.maxAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t', )
            self.maxAliasingPullDowns[i].activated.connect(partial(self._queueSetMaxAliasing, spectrum, self.maxAliasingPullDowns[i].getText, i))

            # min aliasing
            row += 1
            self.minAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t', )
            self.minAliasingPullDowns[i].activated.connect(partial(self._queueSetMinAliasing, spectrum, self.minAliasingPullDowns[i].getText, i))

        # add preferred order widgets for Nd and
        if spectrum.dimensionCount > 1:
            row += 1
            hLine = HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)
            hLine.setContentsMargins(5, 0, 0, 0)

            row += 1
            self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self, labelText="Preferred Axis Order",
                                                                         grid=(row, 0), gridSpan=(1, dimensions + 1), vAlign='t', tipText=getAttributeTipText(Spectrum, 'preferredAxisOrdering'))
            self.preferredAxisOrderPulldown.pulldownList.setCallback(partial(self._queueSetSpectrumOrderingComboIndex, spectrum))

        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, dimensions + 1), gridSpan=(1, 1))

    def _fillPreferredWidgetFromAxisTexts(self):
        """Fill the pullDown during preSelect
        """
        with self.blockWidgetSignals(self.preferredAxisOrderPulldown):
            self._populatePreferredOrder()

    def _populatePreferredOrder(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(self.spectrum.preferredAxisOrdering) if self.spectrum.preferredAxisOrdering is not None else None

        axisCodeTexts = tuple([ss.text() for ss in self.axisCodeEdits])
        ll = ['<None>']

        # add permutations for the axes
        axisPerms = permutations([axisCode for axisCode in axisCodeTexts])
        axisOrder = tuple(permutations(list(range(len(axisCodeTexts)))))
        ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        if specOrder is not None:
            specIndex = axisOrder.index(specOrder) + 1
            self.preferredAxisOrderPulldown.setIndex(specIndex)
        else:
            self.preferredAxisOrderPulldown.setIndex(0)

    @queueStateChange(_verifyPopupApply)
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

    def _fillPullDowns(self):
        pass

    def _populateReferenceDimensions(self):
        """Populate the references dimensions from the current experiment and the current value
        """
        # get the nucleus codes from the current isotope codes
        refDimensions = self._referenceDimensions or self.spectrum.referenceExperimentDimensions

        if (self._referenceExperiment or self.spectrum.experimentType) is None:
            _referenceLists = [['', val] if val else ['',] for val in refDimensions]
            _refDimensions = [val if val else '' for val in refDimensions]

            for ii, (refList, ref) in enumerate(zip(_referenceLists, _refDimensions)):
                self.referenceDimensionPullDowns[ii].setData(refList)
                self.referenceDimensionPullDowns[ii].setIndex(refList.index(ref))

        else:
            _referenceLists = [['',] for val in refDimensions]
            _refDimensions = [val if val else '' for val in refDimensions]

            # get the permutations of the available experiment dimensions
            matches = self.spectrum.getAvailableReferenceExperimentDimensions(_experimentType=self._referenceExperiment)
            if matches:
                for ac in matches:
                    for ii in range(self.dimensions):
                        if ac[ii] not in _referenceLists[ii]:
                            _referenceLists[ii].append(ac[ii])

            for ii, (refList, ref, combo) in enumerate(zip(_referenceLists, _refDimensions, self.referenceDimensionPullDowns)):
                if ref not in refList:
                    model = combo.model()

                    refList.append(ref)
                    combo.setData(list(refList))

                    self.referenceDimensionPullDowns[ii].set(ref)
                    color = QtGui.QColor('red')
                    model.item(len(refList) - 1).setForeground(color)

                else:
                    combo.setData(list(refList))
                    combo.set(ref)

                index = combo.currentIndex()
                model = combo.model()
                item = model.item(index)
                if item is not None:
                    color = item.foreground().color()
                    # use the palette to change the colour of the selection text - may not match for other themes
                    palette = combo.palette()
                    palette.setColor(QtGui.QPalette.Text, color)
                    combo.setPalette(palette)
                    # combo.setStyleSheet('PulldownList { padding: 3px 3px 3px 3px; combobox-popup: 0; color: red; }')

    def _populateExperimentType(self):
        """Populate the experimentType pulldown
        """
        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        experimentTypes = _getExperimentTypes(self.spectrum.project, self.spectrum)
        texts = ('',) + tuple(experimentTypes.keys()) if experimentTypes else ()
        objects = ('',) + tuple(experimentTypes.values()) if experimentTypes else ()
        self.spectrumType.setData(texts=texts, objects=objects)

        text = self.spectrum.experimentName
        if experimentTypes and text not in experimentTypes:
            text = self.spectrum.experimentType
        text = priorityNameRemapping.get(text, text)
        self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

        self._referenceExperiment = text

    def _populateDimension(self):
        """Populate dimensions tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():

            self.aliasLim = self.spectrum.aliasingLimits
            self.axesReversed = self.spectrum.axesReversed
            self.specLim = tuple(sorted(spLim) for spLim in self.spectrum.spectrumLimits)
            self.deltaLim = tuple(max(spLim) - min(spLim) for spLim in self.specLim)

            for i in range(self.dimensions):
                value = self.spectrum.axisCodes[i]
                self.axisCodeEdits[i].setText('<None>' if value is None else str(value))

                if self.spectrum.isotopeCodes[i] in self._isotopeList:
                    self.isotopeCodePullDowns[i].setIndex(self._isotopeList.index(self.spectrum.isotopeCodes[i]))

                self._pointCountsLabels[i].setText(str(self.spectrum.pointCounts[i]))
                self._dimensionTypesLabels[i].setText(self.spectrum.dimensionTypes[i])

                value = self.spectrum.spectralWidths[i]
                self.spectralWidthsData[i].setValue(value or 0.0)

                value = self.spectrum.spectralWidthsHz[i]
                self.spectralWidthsHzData[i].setValue(value or 0.0)

                value = self.spectrum.spectrometerFrequencies[i]
                self.spectrometerFrequenciesData[i].setValue(value or 0.0)

                value = self.spectrum.referenceValues[i]
                self.spectralReferencingData[i].setValue(value or 0.0)

                value = self.spectrum.referencePoints[i]
                self.spectralReferencingDataPoints[i].setValue(value or 0.0)

                value = self.spectrum.assignmentTolerances[i]
                self.spectralAssignmentToleranceData[i].setValue(value or 0.0)

                value = self.spectrum.doubleCrosshairOffsets[i]
                self.spectralDoubleCursorOffset[i].setValue(value or 0.0)

                if i == 0:
                    # hack just to show one
                    value = self.spectrum.displayFoldedContours
                    self.displayedFoldedContours.setChecked(value)

                fModes = self.spectrum.foldingModes
                dd = {'circular': True, 'mirror': False, None: True}  # swapped because inverted checkbox
                self.foldingModesCheckBox[i].setChecked(dd[fModes[i]])

                # pullDown for min/max aliasing
                aliasMaxRange = list(max(self.specLim[i]) + rr * self.deltaLim[i] for rr in range(MAXALIASINGRANGE, -1, -1))
                aliasMinRange = list(min(self.specLim[i]) + rr * self.deltaLim[i] for rr in range(0, -MAXALIASINGRANGE - 1, -1))
                aliasMaxText = [f'{MAXALIASINGRANGE - ii}   ({aa:.3f} ppm)' for ii, aa in enumerate(aliasMaxRange)]
                aliasMinText = [f'{-ii}   ({aa:.3f} ppm)' for ii, aa in enumerate(aliasMinRange)]

                self.maxAliasingPullDowns[i].setData(aliasMaxText)
                _close = (max(self.aliasLim[i]) - max(self.specLim[i]) + self.deltaLim[i] / 2) // self.deltaLim[i]
                self.maxAliasingPullDowns[i].setIndex(MAXALIASINGRANGE - int(_close))

                self.minAliasingPullDowns[i].setData(aliasMinText)
                _close = (min(self.specLim[i]) - min(self.aliasLim[i]) + self.deltaLim[i] / 2) // self.deltaLim[i]
                self.minAliasingPullDowns[i].setIndex(int(_close))

            if self.spectrum.dimensionCount > 1:
                self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidgetFromAxisTexts)
                self._populatePreferredOrder()

            self._populateExperimentType()
            self._populateReferenceDimensions()

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._parent._getChangeState()

    @queueStateChange(_verifyPopupApply)
    def _queueSetAssignmentTolerances(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.assignmentTolerances[dim] or 0.0)  # this means they are not being set
        if textFromValue(value) != specValue:
            return partial(self._setAssignmentTolerances, spectrum, dim, value)

    def _setAssignmentTolerances(self, spectrum, dim, value):
        assignmentTolerances = list(spectrum.assignmentTolerances)
        assignmentTolerances[dim] = float(value)
        spectrum.assignmentTolerances = assignmentTolerances

    @queueStateChange(_verifyPopupApply)
    def _queueSetDoubleCursorOffset(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.doubleCrosshairOffsets[dim] or 0.0)
        if textFromValue(value) != specValue:
            return partial(self._setDoubleCursorOffset, spectrum, dim, value)

    def _setDoubleCursorOffset(self, spectrum, dim, value):
        doubleCrosshairOffsets = list(spectrum.doubleCrosshairOffsets)
        doubleCrosshairOffsets[dim] = float(value)
        spectrum.doubleCrosshairOffsets = doubleCrosshairOffsets

    @queueStateChange(_verifyPopupApply)
    def _queueSetAxisCodes(self, spectrum, ): #valueGetter, dim): # dim required to make the changeState unique per dim
        # set the axisCodes in single operation
        value = tuple(val.text() for val in self.axisCodeEdits)
        if value != spectrum.axisCodes:
            return partial(self._setAxisCodes, spectrum ,value) #, dim, value)

        # repopulate the preferred axis order pulldown
        self._fillPreferredWidgetFromAxisTexts()

    def _setAxisCodes(self, spectrum, value):
        showWarning('Change Axis Code', 'Caution is advised when changing axis codes\n'
                                        'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')
        spectrum.axisCodes = value

    @queueStateChange(_verifyPopupApply)
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

    def _raiseExperimentFilterPopup(self, spectrum):
        from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup

        popup = ExperimentFilterPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=spectrum)
        popup.exec_()
        self.spectrumType.select(popup.expType)

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectrumType(self, spectrum, value):
        if self.spectrumType.getObject():
            expType = self.spectrumType.objects[value]
            if expType != spectrum.experimentType:
                self._referenceExperiment = expType
                with self.blockWidgetSignals():
                    self._populateReferenceDimensions()
                return partial(self._setSpectrumType, spectrum, expType)

    def _setSpectrumType(self, spectrum, expType):
        spectrum.experimentType = expType

    @queueStateChange(_verifyPopupApply)
    def _queueSetReferenceDimensions(self, spectrum, ): #valueGetter, dim):
        # set the referenceDimensions in single operation
        value = tuple(val.getText() or None for val in self.referenceDimensionPullDowns)

        _refDims = []
        # set colour depending on selection
        for ii, combo in enumerate(self.referenceDimensionPullDowns):
            _text = combo.getText() or None
            _refDims.append(_text)

            index = combo.currentIndex()
            model = combo.model()
            item = model.item(index)
            if item is not None:
                color = item.foreground().color()
                if len([True for _combo in self.referenceDimensionPullDowns if _text and _text == _combo.getText()]) > 1:
                    color = QtGui.QColor('red')
                # use the palette to change the colour of the selection text - may not work for other themes
                palette = combo.palette()
                palette.setColor(QtGui.QPalette.Text, color)
                combo.setPalette(palette)

        self._referenceDimensions = tuple(_refDims)

        if value != spectrum.referenceExperimentDimensions:
            return partial(self._setReferenceDimensions, spectrum, value) #, dim, value)

    def _setReferenceDimensions(self, spectrum, value): #, dim, value):
        """Set the value for a single referenceDimension
        - this can lead to non-unique values"""
        spectrum.referenceExperimentDimensions = value

    def _copyReferenceExperiments(self):
        """Copy the reference experiment dimensions to the axisCode lineEdits
        """
        # get list of all non-empty reference experiments
        _texts = [_combo.getText() for _combo in self.referenceDimensionPullDowns if _combo.getText()]
        if len(_texts) != len(set(_texts)):
            showWarning('Copy to Axis Codes', 'Reference experiment dimensions contains duplicates')

        else:
            for axisEdit, refPulldown in zip(self.axisCodeEdits, self.referenceDimensionPullDowns):
                _text = refPulldown.getText() or None
                if _text:
                    axisEdit.set(_text)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectralWidths(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.spectralWidths[dim])
        if textFromValue(value) != specValue:
            return partial(self._setSpectralWidths, spectrum, dim, value)

    def _setSpectralWidths(self, spectrum, dim, value):
        spectralWidths = list(spectrum.spectralWidths)
        spectralWidths[dim] = float(value)
        spectrum.spectralWidths = spectralWidths

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectralWidthsHz(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.spectralWidthsHz[dim])
        if textFromValue(value) != specValue:
            return partial(self._setSpectralWidthsHz, spectrum, dim, value)

    def _setSpectralWidthsHz(self, spectrum, dim, value):
        spectralWidthsHz = list(spectrum.spectralWidthsHz)
        spectralWidthsHz[dim] = float(value)
        spectrum.spectralWidthsHz = spectralWidthsHz

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectrometerFrequencies(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.spectrometerFrequencies[dim])
        if textFromValue(value) != specValue:
            return partial(self._setSpectrometerFrequencies, spectrum, dim, value)

    def _setSpectrometerFrequencies(self, spectrum, dim, value):
        spectrometerFrequencies = list(spectrum.spectrometerFrequencies)
        spectrometerFrequencies[dim] = float(value)
        spectrum.spectrometerFrequencies = spectrometerFrequencies

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyPopupApply)
    def _queueSetDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referenceValues[dim])
        if textFromValue(value) != specValue:
            return partial(self._setDimensionReferencing, spectrum, dim, value)

    def _setDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referenceValues)
        spectrumReferencing[dim] = float(value)
        spectrum.referenceValues = spectrumReferencing

    @queueStateChange(_verifyPopupApply)
    def _queueSetPointDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referencePoints[dim] or 0.0)
        if textFromValue(value) != specValue:
            return partial(self._setPointDimensionReferencing, spectrum, dim, value)

    def _setPointDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referencePoints)
        spectrumReferencing[dim] = float(value)
        spectrum.referencePoints = spectrumReferencing

    @queueStateChange(_verifyPopupApply)
    def _queueSetMinAliasing(self, spectrum, valueGetter, dim):
        _index = self.minAliasingPullDowns[dim].getSelectedIndex()
        minValue = min(self.specLim[dim]) - _index * self.deltaLim[dim]
        if abs(minValue - min(spectrum.aliasingLimits[dim])) > 1e-8:  # for rounding errors
            returnVal = partial(self._setMinAliasing, self.spectrum, dim, minValue)
            return returnVal

    def _setMinAliasing(self, spectrum, dim, value):
        alias = list(spectrum.aliasingLimits)
        value = float(value)
        alias[dim] = (value, max(alias[dim][1], value))
        spectrum.aliasingLimits = tuple(alias)

    @queueStateChange(_verifyPopupApply)
    def _queueSetMaxAliasing(self, spectrum, valueGetter, dim):
        _index = MAXALIASINGRANGE - self.maxAliasingPullDowns[dim].getSelectedIndex()
        maxValue = max(self.specLim[dim]) + _index * self.deltaLim[dim]
        if abs(maxValue - max(spectrum.aliasingLimits[dim])) > 1e-8:  # for rounding errors
            returnVal = partial(self._setMaxAliasing, spectrum, dim, maxValue)
            return returnVal

    def _setMaxAliasing(self, spectrum, dim, value):
        alias = list(spectrum.aliasingLimits)
        value = float(value)
        alias[dim] = (min(alias[dim][0], value), value)
        spectrum.aliasingLimits = tuple(alias)

    @queueStateChange(_verifyPopupApply)
    def _queueSetFoldingModes(self, spectrum, valueGetter, dim):
        dd = {False: 'mirror', True: 'circular', None: None}  # swapped because inverted checkbox
        value = dd[valueGetter()]
        if value != spectrum.foldingModes[dim]:
            return partial(self._setFoldingModes, spectrum, dim, value)

    def _setFoldingModes(self, spectrum, dim, value):
        folding = list(spectrum.foldingModes)
        folding[dim] = value
        spectrum.foldingModes = tuple(folding)

    @queueStateChange(_verifyPopupApply)
    def _queueSetDisplayFoldedContours(self, spectrum, valueGetter):
        value = valueGetter()
        if value != spectrum.displayFoldedContours:
            return partial(self._setDisplayFoldedContours, spectrum, value)

    def _setDisplayFoldedContours(self, spectrum, value):
        spectrum.displayFoldedContours = bool(value)


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

        self._changes = ChangeDict()
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
        positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(row, col), vAlign='t', hAlign='l', tipText=getAttributeTipText(Spectrum, 'includePositiveContours'))
        self.positiveContoursCheckBox = CheckBox(self, grid=(row, col + 1), vAlign='t', hAlign='l')
        self.positiveContoursCheckBox.stateChanged.connect(partial(self._queueChangePositiveContourDisplay, spectrum))

        row += 1
        positiveContourBaseLabel = Label(self, text="Positive Base Level", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'positiveContourBase'))
        self.positiveContourBaseData = ScientificDoubleSpinBox(self, grid=(row, col + 1), vAlign='t', min=0.1, max=1e12)
        self.positiveContourBaseData.valueChanged.connect(partial(self._queueChangePositiveContourBase, spectrum, self.positiveContourBaseData.textFromValue))

        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.positiveContourBaseData.setSingleStep(self.positiveContourBaseData.value() * 0.1)

        row += 1
        positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'positiveContourFactor'))
        self.positiveMultiplierData = ScientificDoubleSpinBox(self, grid=(row, col + 1), vAlign='t', min=0.0, decimals=3, step=0.01)
        self.positiveMultiplierData.valueChanged.connect(partial(self._queueChangePositiveContourFactor, spectrum, self.positiveMultiplierData.textFromValue))

        row += 1
        positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'positiveContourCount'))
        self.positiveContourCountData = Spinbox(self, grid=(row, col + 1), vAlign='t', min=1)
        self.positiveContourCountData.valueChanged.connect(partial(self._queueChangePositiveContourCount, spectrum))

        row += 1
        positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'positiveContourColour'))
        self.positiveColourBox = PulldownList(self, grid=(row, col + 1), vAlign='t')
        self.negativeColourBox = PulldownList(self, grid=(row, col + 1), vAlign='t')

        # populate initial pulldown
        spectrumColourKeys = list(spectrumColours.keys())
        fillColourPulldown(self.positiveColourBox, allowAuto=False, includeGradients=True)
        fillColourPulldown(self.negativeColourBox, allowAuto=False, includeGradients=True)

        self.positiveColourButton = Button(self, grid=(row, col + 2), vAlign='t', hAlign='l',
                                           icon='icons/colours', hPolicy='fixed')
        self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, spectrum))

        row += 1
        negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'includeNegativeContours'))
        self.negativeContoursCheckBox = CheckBox(self, grid=(row, col + 1), vAlign='t', hAlign='l')
        # self.negativeContoursCheckBox.setChecked(self.spectrum.includeNegativeContours)
        self.negativeContoursCheckBox.stateChanged.connect(partial(self._queueChangeNegativeContourDisplay, spectrum))

        row += 1
        negativeContourBaseLabel = Label(self, text="Negative Base Level", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'negativeContourBase'))
        self.negativeContourBaseData = ScientificDoubleSpinBox(self, grid=(row, col + 1), vAlign='t', min=-1e12, max=-0.1)

        self.negativeContourBaseData.valueChanged.connect(partial(self._queueChangeNegativeContourBase, spectrum, self.negativeContourBaseData.textFromValue))

        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.negativeContourBaseData.setSingleStep((self.negativeContourBaseData.value() * -1) * 0.1)

        row += 1
        negativeMultiplierLabel = Label(self, text="Negative Multiplier", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'negativeContourFactor'))
        self.negativeMultiplierData = ScientificDoubleSpinBox(self, grid=(row, col + 1), vAlign='t', min=0.0, decimals=3, step=0.01)
        self.negativeMultiplierData.valueChanged.connect(partial(self._queueChangeNegativeContourFactor, spectrum, self.negativeMultiplierData.textFromValue))

        row += 1
        negativeContourCountLabel = Label(self, text="Number of negative contours", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'negativeContourCount'))
        self.negativeContourCountData = Spinbox(self, grid=(row, col + 1), vAlign='t', min=1)
        self.negativeContourCountData.valueChanged.connect(partial(self._queueChangeNegativeContourCount, spectrum))

        row += 1
        negativeContourColourLabel = Label(self, text="Negative Contour Colour", grid=(row, col), vAlign='c', hAlign='l', tipText=getAttributeTipText(Spectrum, 'negativeContourColour'))

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
        if self.preferences.general._copySpectraSettingsNd and len(self.preferences.general._copySpectraSettingsNd) == len(self._copyList):
            # read existing settings
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=self.preferences.general._copySpectraSettingsNd[rr], hAlign='c')
                self._copyCheckBoxes.append(thisCheckBox)
                thisCheckBox.setCallback(partial(self._copyButtonClicked, thisCheckBox, rr))

                self._addToCopyWidgetSet(thisCheckBox)
        else:
            # create a new list in preferences
            self.preferences.general._copySpectraSettingsNd = [True] * len(self._copyList)
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

        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row + 3, col + 1), gridSpan=(1, 1))

    def _updateSpectra(self, spectrum, copyToSpectra):
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
        posBase, negBase, posMult, negMult, posLevels, negLevels = getContourLevelsFromNoise(self.spectrum,
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

    def _fillPullDowns(self):
        fillColourPulldown(self.positiveColourBox, allowAuto=False, includeGradients=True)
        fillColourPulldown(self.negativeColourBox, allowAuto=False, includeGradients=True)

    def _populateColour(self):
        """Populate colour tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():
            self.positiveContoursCheckBox.setChecked(self.spectrum.includePositiveContours)
            self.positiveContourBaseData.setValue(self.spectrum.positiveContourBase)
            self.positiveMultiplierData.setValue(float(self.spectrum.positiveContourFactor))
            self.positiveContourCountData.setValue(int(self.spectrum.positiveContourCount))
            _setColourPulldown(self.positiveColourBox, self.spectrum.positiveContourColour)

            self.negativeContoursCheckBox.setChecked(self.spectrum.includeNegativeContours)
            self.negativeContourBaseData.setValue(-abs(self.spectrum.negativeContourBase))
            self.negativeMultiplierData.setValue(self.spectrum.negativeContourFactor)
            self.negativeContourCountData.setValue(self.spectrum.negativeContourCount)
            _setColourPulldown(self.negativeColourBox, self.spectrum.negativeContourColour)

        self._populateCheckBoxes()

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._parent._getChangeState()

    def _populateCheckBoxes(self):
        """Populate the checkbox from preferences and fill the pullDown from the list of spectra
        """
        if not hasattr(self, '_copyCheckBoxes'):
            return

        with self._changes.blockChanges():
            checkBoxList = self.preferences.general._copySpectraSettingsNd
            if checkBoxList:
                for cc, checkBox in enumerate(checkBoxList):
                    state = checkBoxList[cc]
                    self._copyCheckBoxes[cc].setChecked(state)

            if self._copyToSpectra:
                texts = [SELECTND] + [spectrum.pid for spectrum in self._copyToSpectra if spectrum != self.spectrum]
                self._copyToSpectraPullDown.modifyTexts(texts)

    def _cleanWidgetQueue(self):
        """Clean the items from the stateChange queue
        """
        self._changes.clear()

    @queueStateChange(_verifyPopupApply)
    def _queueChangePositiveContourDisplay(self, spectrum, state):
        if (state == QtCore.Qt.Checked) != spectrum.includePositiveContours:
            return partial(self._changePositiveContourDisplay, spectrum, state)

    def _changePositiveContourDisplay(self, spectrum, state):
        if state == QtCore.Qt.Checked:
            spectrum.includePositiveContours = True
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayPositiveContours = True
        else:
            self.spectrum.includePositiveContours = False
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayPositiveContours = False

    @queueStateChange(_verifyPopupApply)
    def _queueChangeNegativeContourDisplay(self, spectrum, state):
        if (state == QtCore.Qt.Checked) != spectrum.includeNegativeContours:
            return partial(self._changeNegativeContourDisplay, spectrum, state)

    def _changeNegativeContourDisplay(self, spectrum, state):
        if state == QtCore.Qt.Checked:
            spectrum.includeNegativeContours = True
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayNegativeContours = True
        else:
            spectrum.includeNegativeContours = False
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayNegativeContours = False

    @queueStateChange(_verifyPopupApply)
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

    @queueStateChange(_verifyPopupApply)
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

    @queueStateChange(_verifyPopupApply)
    def _queueChangePositiveContourCount(self, spectrum, value):
        if value > 0 and value != spectrum.positiveContourCount:
            returnVal = partial(self._changePositiveContourCount, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeContourCountData.set(value)
        return returnVal

    def _changePositiveContourCount(self, spectrum, value):
        spectrum.positiveContourCount = int(value)

    @queueStateChange(_verifyPopupApply)
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

    @queueStateChange(_verifyPopupApply)
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

    @queueStateChange(_verifyPopupApply)
    def _queueChangeNegativeContourCount(self, spectrum, value):
        if value > 0 and value != spectrum.negativeContourCount:
            returnVal = partial(self._changeNegativeContourCount, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveContourCountData.set(value)
        return returnVal

    def _changeNegativeContourCount(self, spectrum, value):
        spectrum.negativeContourCount = int(value)

    # spectrum positiveContourColour button and pulldown
    def _queueChangePosSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.positiveColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangePosColourComboIndex(self, spectrum, value):
        if value >= 0:
            colName = colourNameNoSpace(self.positiveColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrum.positiveContourColour:
                # and list(spectrumColours.keys())[value] != spectrum.positiveContourColour:
                return partial(self._changePosColourComboIndex, spectrum, value)

    def _changePosColourComboIndex(self, spectrum, value):
        colName = colourNameNoSpace(self.positiveColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        if newColour:
            spectrum.positiveContourColour = newColour

    # spectrum negativeContourColour button and pulldown
    def _queueChangeNegSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.negativeColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangeNegColourComboIndex(self, spectrum, value):
        if value >= 0:
            colName = colourNameNoSpace(self.negativeColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrum.negativeContourColour:
                # and list(spectrumColours.keys())[value] != spectrum.negativeContourColour:
                return partial(self._changeNegColourComboIndex, spectrum, value)

    def _changeNegColourComboIndex(self, spectrum, value):
        colName = colourNameNoSpace(self.negativeColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        if newColour:
            spectrum.negativeContourColour = newColour

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
        checkBoxList = self.preferences.general._copySpectraSettingsNd
        if checkBoxList and checkBoxIndex < len(checkBoxList):
            checkBoxList[checkBoxIndex] = state

    def _copyActionClicked(self):
        """Copy action clicked - call the copy method from the parent Tab widget
        """
        if self._showCopyOptions:
            toSpectraPids = self._copyToSpectraPullDown.getText()
            if toSpectraPids == SELECTND:
                toSpectra = [spectrum for spectrum in self._copyToSpectra if spectrum != self.spectrum]
            else:
                toSpectra = [self.application.project.getByPid(toSpectraPids)]

            # call the parent tab copy action
            self._parent.copySpectra(self.spectrum, toSpectra)

    def _copySpectrumAttributes(self, fromSpectrumTab):
        """Copy the attributes to the other spectra
        """
        if self._showCopyOptions:
            checkBoxList = self.preferences.general._copySpectraSettingsNd
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
        self._changes = ChangeDict()
        self.atomCodes = ()

        self._showCopyOptions = showCopyOptions

        self._copyWidgetSet = set()
        self._topRow = 7
        self._checkBoxCol = 4

        # if showCopyOptions:
        copyLabel = Label(self, text="Copy Selected\nAttribute", grid=(self._topRow - 1, self._checkBoxCol), vAlign='t', hAlign='l')
        self._addToCopyWidgetSet(copyLabel)

        Label(self, text="Colour", vAlign='t', hAlign='l', grid=(7, 0), tipText=getAttributeTipText(Spectrum, 'sliceColour'))
        self.positiveColourBox = PulldownList(self, vAlign='t', grid=(7, 1))

        # populate initial pulldown
        fillColourPulldown(self.positiveColourBox, allowAuto=False, includeGradients=True)
        self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))

        # add a colour dialog button
        self.colourButton = Button(self, vAlign='t', hAlign='l', grid=(7, 2),
                                   icon='icons/colours', hPolicy='fixed')
        self.colourButton.clicked.connect(partial(self._queueSetSpectrumColour, spectrum))

        self._copyList = (self._copyPositiveContourColour,
                          )

        self._copyCheckBoxes = []

        # add the checkboxes and keep a list of selected in the preferences (so it will be saved)
        if self.preferences.general._copySpectraSettings1d and len(self.preferences.general._copySpectraSettings1d) == len(self._copyList):
            # read existing settings
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=self.preferences.general._copySpectraSettings1d[rr], hAlign='c')
                self._copyCheckBoxes.append(thisCheckBox)
                thisCheckBox.setCallback(partial(self._copyButtonClicked, thisCheckBox, rr))

                self._addToCopyWidgetSet(thisCheckBox)
        else:
            # create a new list in preferences
            self.preferences.general._copySpectraSettings1d = [True] * len(self._copyList)
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

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding,
               grid=(len(self._copyList) + self._topRow + 2, 1), gridSpan=(1, 1))

        self._addToCopyWidgetSet(self._copyToSpectraPullDown)
        self._addToCopyWidgetSet(self._copyButton)

    def _updateSpectra(self, spectrum, copyToSpectra):
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

    def _fillPullDowns(self):
        fillColourPulldown(self.positiveColourBox, allowAuto=False, includeGradients=True)

    def _populateColour(self):
        """Populate dimensions tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():
            _setColourPulldown(self.positiveColourBox, self.spectrum.sliceColour)

        self._populateCheckBoxes()

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._parent._getChangeState()

    def _populateCheckBoxes(self):
        """Populate the checkbox from preferences and fill the pullDown from the list of spectra
        """
        if not hasattr(self, '_copyCheckBoxes'):
            return

        with self._changes.blockChanges():
            checkBoxList = self.preferences.general._copySpectraSettings1d
            if checkBoxList:
                for cc, checkBox in enumerate(checkBoxList):
                    state = checkBoxList[cc]
                    try:
                        self._copyCheckBoxes[cc].setChecked(state)
                    except Exception as es:
                        pass

            if self._copyToSpectra:
                texts = [SELECT1D] + [spectrum.pid for spectrum in self._copyToSpectra if spectrum != self.spectrum]
                self._copyToSpectraPullDown.modifyTexts(texts)

    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.positiveColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangeSliceComboIndex(self, spectrum, value):
        if value >= 0:
            colName = colourNameNoSpace(self.positiveColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrum.sliceColour:
                # and list(spectrumColours.keys())[value] != spectrum.sliceColour:
                return partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        colName = colourNameNoSpace(self.positiveColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        if newColour:
            spectrum.sliceColour = newColour

    def _copyPositiveContourColour(self, fromSpectrumTab):
        name = fromSpectrumTab.positiveColourBox.currentText()
        colour = getSpectrumColour(name, defaultReturn='#')
        _setColourPulldown(self.positiveColourBox, colour)

    def _copyButtonClicked(self, checkBox, checkBoxIndex, state):
        """Set the state of the checkBox in preferences
        """
        checkBoxList = self.preferences.general._copySpectraSettings1d
        if checkBoxList and checkBoxIndex < len(checkBoxList):
            checkBoxList[checkBoxIndex] = state

    def _copyActionClicked(self):
        """Copy action clicked - call the copy method from the parent Tab widget
        """
        if self._showCopyOptions:
            toSpectraPids = self._copyToSpectraPullDown.getText()
            if toSpectraPids == SELECT1D:
                toSpectra = [spectrum for spectrum in self._copyToSpectra if spectrum != self.spectrum]
            else:
                toSpectra = [self.application.project.getByPid(toSpectraPids)]

            # call the parent tab copy action
            self._parent.copySpectra(self.spectrum, toSpectra)

    def _copySpectrumAttributes(self, fromSpectrumTab):
        """Copy the attributes to the other spectra
        """
        if self._showCopyOptions:
            checkBoxList = self.preferences.general._copySpectraSettings1d
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
        self._changes.clear()


class ColourFrameABC(Frame):
    POSITIVECOLOUR = False
    NEGATIVECOLOUR = False
    SLICECOLOUR = False
    EDITMODE = True

    def __init__(self, parent=None, mainWindow=None, container=None, editMode=False, spectrumGroup=None, item=None, **kwds):

        super().__init__(parent, **kwds)

        self._parent = parent
        self._container = container  # master widget, that this is attached to
        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project
        self.preferences = self.application.preferences

        # check that the spectrum and the copyToSpectra list are correctly defined
        getByPid = self.application.project.getByPid
        if editMode:
            self.spectrumGroup = getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
            if not isinstance(self.spectrumGroup, SpectrumGroup):
                raise TypeError('spectrumGroup must be of type SpectrumGroup or None')
        else:
            # create a dummy container to hold the colours
            self.spectrumGroup = AttrDict()
            self.spectrumGroup.positiveContourColour = None
            self.spectrumGroup.negativeContourColour = None
            self.spectrumGroup.sliceColour = None

        self.EDITMODE = editMode

        self.item = item
        self._changes = ChangeDict()

        row = 0
        if self.POSITIVECOLOUR:
            Label(self, text="Group Positive Contour Colour", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(SpectrumGroup, 'positiveContourColour'))
            self.positiveColourBox = PulldownList(self, vAlign='t', grid=(row, 1))
            self.positiveColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                               icon='icons/colours', hPolicy='fixed')
            self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, self.spectrumGroup))
            row += 1

        if self.NEGATIVECOLOUR:
            Label(self, text="Group Negative Contour Colour", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(SpectrumGroup, 'negativeContourColour'))
            self.negativeColourBox = PulldownList(self, vAlign='t', grid=(row, 1))
            self.negativeColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                               icon='icons/colours', hPolicy='fixed')
            self.negativeColourButton.clicked.connect(partial(self._queueChangeNegSpectrumColour, self.spectrumGroup))
            row += 1

        if self.SLICECOLOUR:
            Label(self, text="Group Slice Colour", vAlign='t', hAlign='l', grid=(row, 0), tipText=getAttributeTipText(SpectrumGroup, 'sliceColour'))
            self.sliceColourBox = PulldownList(self, vAlign='t', grid=(row, 1))
            self.sliceColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                            icon='icons/colours', hPolicy='fixed')
            self.sliceColourButton.clicked.connect(partial(self._queueChangeSliceColour, self.spectrumGroup))
            row += 1

        self._fillPullDowns()

        if self.POSITIVECOLOUR:
            self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, self.spectrumGroup))
        if self.NEGATIVECOLOUR:
            self.negativeColourBox.currentIndexChanged.connect(partial(self._queueChangeNegColourComboIndex, self.spectrumGroup))
        if self.SLICECOLOUR:
            self.sliceColourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, self.spectrumGroup))

    def _updateSpectrumGroup(self, spectrumGroup):
        # check that the spectrum and the copyToSpectra list are correctly defined
        getByPid = self.application.project.getByPid
        self.spectrumGroup = getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(self.spectrumGroup, (SpectrumGroup, type(None))):
            raise TypeError('spectrumGroup must be of type SpectrumGroup or None')

    def _fillPullDowns(self):
        if self.POSITIVECOLOUR:
            fillColourPulldown(self.positiveColourBox, allowAuto=False, includeGradients=True, allowNone=True)
        if self.NEGATIVECOLOUR:
            fillColourPulldown(self.negativeColourBox, allowAuto=False, includeGradients=True, allowNone=True)
        if self.SLICECOLOUR:
            fillColourPulldown(self.sliceColourBox, allowAuto=False, includeGradients=True, allowNone=True)

    def _populateColour(self):
        """Populate dimensions tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():
            if self.POSITIVECOLOUR:
                _setColourPulldown(self.positiveColourBox, self.spectrumGroup.positiveContourColour, allowAuto=False, includeGradients=True, allowNone=True)
            if self.NEGATIVECOLOUR:
                _setColourPulldown(self.negativeColourBox, self.spectrumGroup.negativeContourColour, allowAuto=False, includeGradients=True, allowNone=True)
            if self.SLICECOLOUR:
                _setColourPulldown(self.sliceColourBox, self.spectrumGroup.sliceColour, allowAuto=False, includeGradients=True, allowNone=True)

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._container._getChangeState()

    # spectrum positiveContourColour button and pulldown
    def _queueChangePosSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._container._fillPullDowns()
            self.positiveColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangePosColourComboIndex(self, spectrumGroup, value):
        if value >= 0:
            colName = colourNameNoSpace(self.positiveColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrumGroup.positiveContourColour:
                # and list(spectrumColours.keys())[value] != spectrumGroup.positiveContourColour:
                return partial(self._changePosColourComboIndex, spectrumGroup, value)

    def _changePosColourComboIndex(self, spectrumGroup, value):
        colName = colourNameNoSpace(self.positiveColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        _value = newColour or None
        spectrumGroup.positiveContourColour = _value

    # spectrum negativeContourColour button and pulldown
    def _queueChangeNegSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._container._fillPullDowns()
            self.negativeColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangeNegColourComboIndex(self, spectrumGroup, value):
        if value >= 0:
            colName = colourNameNoSpace(self.negativeColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrumGroup.negativeContourColour:
                # and list(spectrumColours.keys())[value] != spectrumGroup.negativeContourColour:
                return partial(self._changeNegColourComboIndex, spectrumGroup, value)

    def _changeNegColourComboIndex(self, spectrumGroup, value):
        colName = colourNameNoSpace(self.negativeColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        _value = newColour or None
        spectrumGroup.negativeContourColour = _value

    # spectrum sliceColour button and pulldown
    def _queueChangeSliceColour(self, spectrumGroup):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._container._fillPullDowns()
            self.sliceColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueChangeSliceComboIndex(self, spectrumGroup, value):
        if value >= 0:
            colName = colourNameNoSpace(self.sliceColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != spectrumGroup.sliceColour:
                # and list(spectrumColours.keys())[value] != spectrumGroup.sliceColour:
                return partial(self._changedSliceComboIndex, spectrumGroup, value)

    def _changedSliceComboIndex(self, spectrumGroup, value):
        colName = colourNameNoSpace(self.sliceColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        _value = newColour or None
        spectrumGroup.sliceColour = _value

    def _cleanWidgetQueue(self):
        """Clean the items from the stateChange queue
        """
        self._changes.clear()


class Colour1dFrame(ColourFrameABC):
    POSITIVECOLOUR = False
    NEGATIVECOLOUR = False
    SLICECOLOUR = True


class ColourNdFrame(ColourFrameABC):
    POSITIVECOLOUR = True
    NEGATIVECOLOUR = True
    SLICECOLOUR = False
