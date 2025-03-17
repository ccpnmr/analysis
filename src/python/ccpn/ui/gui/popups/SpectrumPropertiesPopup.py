"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-03-17 11:01:18 +0000 (Mon, March 17, 2025) $"
__version__ = "$Revision: 3.3.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# NOTE:ED - do not remove occurrences of `  # type: ignore`
#   for the minute, they are suppressing the pyqtSignal warning in pycharm
import re
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
from itertools import permutations
from collections.abc import Iterable
import pandas as pd
from contextlib import contextmanager

from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.core.lib.SpectrumLib import (MAXALIASINGRANGE, CoherenceOrder,
                                       MagnetisationTransferParameters, _getApiExpTransfers)
from ccpn.core.lib.ContextManagers import queueStateChange

from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox, VariableScientificSpinBox, fexp
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.MagnetisationTransferTable import MagnetisationTransferTable
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.popups.ExperimentTypePopup import _getExperimentTypes
from ccpn.ui.gui.popups.ValidateSpectraPopup import SpectrumPathRow
from ccpn.ui.gui.popups.PreferencesPopup import PEAKFITTINGDEFAULTS
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply, _verifyPopupApply
from ccpn.ui.gui.lib.ChangeStateHandler import changeState, ChangeDict
from ccpn.ui.gui.lib.DynamicSizeAdjust import dynamicSizeAdjust

from ccpn.util.AttrDict import AttrDict
from ccpn.util.Colour import (spectrumColours, addNewColour, fillColourPulldown,
                              colourNameNoSpace, _setColourPulldown, getSpectrumColour)
from ccpn.util.isotopes import isotopeRecords
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.popups.AttributeEditorPopupABC import getAttributeTipText


SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 1, 5)  # l, t, r, b
SELECTALL = '<All>'
SELECT1D = '<All 1D Spectra>'
SELECTND = '<All nD Spectra>'

ORIENTATIONS = {'h'                 : QtCore.Qt.Horizontal,
                'horizontal'        : QtCore.Qt.Horizontal,
                'v'                 : QtCore.Qt.Vertical,
                'vertical'          : QtCore.Qt.Vertical,
                QtCore.Qt.Horizontal: QtCore.Qt.Horizontal,
                QtCore.Qt.Vertical  : QtCore.Qt.Vertical,
                }

_alignLabel = dict(vAlign='c', hAlign='r', minimumHeight=25)  # Keyword labels
_align1 = dict(vAlign='c', hAlign='l', textColour='black')  # Data Labels
_align2 = dict(vAlign='c')  # Dimensional Pulldowns / LineEdits

LIGHTGREY = QtGui.QColor('lightgrey')

_overrideClassCheck = False


def _updateGl(self, spectrumList):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    # # spawn a redraw of the contours
    # for spec in spectrumList:
    #     for specViews in spec.spectrumViews:
    #         specViews.buildContours = True

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


#=========================================================================================
# SpectrumPropertiesPopupABC - Base-class for dialogs
#=========================================================================================

class SpectrumPropertiesPopupABC(CcpnDialogMainWidget):
    # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
    # The apply button then steps through each tab, and calls each function in the _changes dictionary
    # in order to set the parameters.

    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    MINIMUM_WIDTH_PER_TAB = 120
    MINIMUM_WIDTH = 500
    BORDER_OFFSET = 20
    _revertState = 0

    def __init__(self, parent=None, mainWindow=None, spectrum=None,
                 title='Spectrum Properties', **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.spectrum = spectrum
        self.tabWidget = Tabs(self.mainWidget, setLayout=True, grid=(0, 0), focusPolicy='strong')

        # dynamically change the width of the popup when the tab is changed
        self.tabWidget.currentChanged.connect(self._resizeWidthToTab)

        # enable the buttons
        self.setOkButton(callback=self._okClicked)
        self.setApplyButton(callback=self._applyClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

    def _postInit(self):
        """post-initialise functions
        CCPN-Internal to be called at the end of __init__
        """
        super()._postInit()

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

    @staticmethod
    def _keyPressEvent(event):
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

    @contextmanager
    def _inRevertState(self):
        self._revertState += 1
        try:
            yield
        finally:
            self._revertState -= 1
            if self._revertState < 0:
                raise RuntimeError('revertState below 0')

    def _revertClicked(self):
        """Revert button signal comes here
        Revert (roll-back) the state of the project to before the popup was opened
        """
        if (_undo := self.application._getUndo()) is not None:
            for undos in range(self._currentNumApplies):
                _undo.undo()

        with self._inRevertState():
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

        _tabs = self.getActiveTabList()

        # get the list of widgets that have been changed - exit if all empty
        allChanges = any(t._changes for t in _tabs if t is not None)
        if not allChanges:
            return True

        # handle clicking of the Apply/OK button
        with handleDialogApply(self) as error:
            # get the list of spectra that have changed - for refreshing the displays
            spectrumList = []
            for t in _tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        spectrumList.append(t.spectrum)

            # add an undo item to redraw these spectra
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateGl, self, spectrumList))

            # apply all functions to the spectra
            for t in _tabs:
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
        for tab in _tabs:
            tab._changes = ChangeDict()

        self._currentNumApplies += 1
        self._revertButton.setEnabled(True)
        return True

    def copySpectra(self, fromSpectrum, toSpectra):
        """Copy the contents of tabs to other spectra
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _resizeWidthToTab(self, tab):
        """change the width to the selected tab
        """
        # create a single-shot - waits until gui is up-to-date before firing first iteration of size adjust
        QtCore.QTimer.singleShot(0, partial(dynamicSizeAdjust, self, sizeFunction=self._targetSize,
                                            adjustWidth=True, adjustHeight=False))

    def _targetSize(self) -> tuple | None:
        """Get the size of the widget to match the popup to.

        Returns the size of the clicked tab, or None if there is an error.
        None will terminate the iteration.

        :return: size of target widget, or None.
        """
        try:
            # get the widths of the tabWidget and the current tab to match against
            tab = self.tabWidget.currentWidget()
            targetSize = tab._scrollContents.sizeHint() + QtCore.QSize(self.BORDER_OFFSET, 2 * self.BORDER_OFFSET)

            # match against the tab-container
            sourceSize = self.tabWidget.size()

            return targetSize, sourceSize

        except Exception:
            return None


#=========================================================================================
# _SpectrumPropertiesFrame
#=========================================================================================

class _SpectrumPropertiesFrame(ScrollableFrame):

    def __init__(self, *args, **kwds):
        super(_SpectrumPropertiesFrame, self).__init__(*args, **kwds)
        self._widget = None

    # def _revertClicked(self):
    #     """Revert button signal comes here
    #     Revert (roll-back) the state of the project to before the popup was opened
    #     """
    #     if self._widget:
    #         return self._thisparent.parent()._revertClicked()
    #
    # def _getChangeState(self):
    #     """Get the change state from the popup tabs
    #     """
    #     if self._widget:
    #         return self._thisparent.parent()._getChangeState()

    def addWidget(self, widget, *args):
        """Add a widget to the frame
        """
        self.getLayout().addWidget(widget, *args)
        self._widget = widget


#=========================================================================================
# SpectrumPropertiesPopup
#=========================================================================================

class SpectrumPropertiesPopup(SpectrumPropertiesPopupABC):
    # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
    # The apply button then steps through each tab, and calls each function in the _changes dictionary
    # in order to set the parameters.

    def __init__(self, parent=None, mainWindow=None, spectrum=None,
                 title='Spectrum Properties', **kwds):

        super().__init__(parent=parent, mainWindow=mainWindow,
                         spectrum=spectrum, title=title, **kwds)

        # define first, as calling routines are dependent on existence of attributes
        self._generalTab = None
        self._dimensionsTab = None
        self._contoursTab = None

        self._generalTab = self._dimensionsTab = self._contoursTab = None
        self.setWindowTitle(f'Spectrum Properties: {spectrum.name}')
        if spectrum.dimensionCount == 1:
            for (tabName, attrName, tabFunc) in (('General', '_generalTab',
                                                  partial(GeneralTab, container=self, mainWindow=self.mainWindow,
                                                          spectrum=spectrum)),
                                                 ('Dimensions', '_dimensionsTab',
                                                  partial(DimensionsTab, container=self, mainWindow=self.mainWindow,
                                                          spectrum=spectrum, dimensions=spectrum.dimensionCount)),
                                                 ):
                fr = _SpectrumPropertiesFrame(self.mainWidget, setLayout=True, spacing=DEFAULTSPACING,
                                              scrollBarPolicies=('never', 'asNeeded'), margins=TABMARGINS)

                self.tabWidget.addTab(fr.scrollArea, tabName)
                _tab = tabFunc(parent=fr)
                fr.addWidget(_tab, 0, 0)  # add to the gridlayout
                setattr(self, attrName, _tab)

            self.tabWidget.setCurrentIndex(1)

        else:
            for (tabName, attrName, tabFunc) in (('General', '_generalTab',
                                                  partial(GeneralTab, container=self, mainWindow=self.mainWindow,
                                                          spectrum=spectrum)),
                                                 ('Dimensions', '_dimensionsTab',
                                                  partial(DimensionsTab, container=self, mainWindow=self.mainWindow,
                                                          spectrum=spectrum, dimensions=spectrum.dimensionCount)),
                                                 ('Contours', '_contoursTab',
                                                  partial(ContoursTab, container=self, mainWindow=self.mainWindow,
                                                          spectrum=spectrum, showCopyOptions=False)),
                                                 ):
                fr = _SpectrumPropertiesFrame(self.mainWidget, setLayout=True, spacing=DEFAULTSPACING,
                                              scrollBarPolicies=('never', 'asNeeded'), margins=TABMARGINS)

                self.tabWidget.addTab(fr.scrollArea, tabName)
                _tab = tabFunc(parent=fr)
                fr.addWidget(_tab, 0, 0)  # add to the gridlayout
                setattr(self, attrName, _tab)

            self.tabWidget.setCurrentIndex(2)

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
                self._dimensionsTab._populateDimension(revert=self._revertState)
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

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton,
                           self._revertButton, self._currentNumApplies)

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return tuple(tab for tab in (self._generalTab, self._dimensionsTab, self._contoursTab) if tab is not None)


#=========================================================================================
# SpectrumDisplayPropertiesPopupNd
#=========================================================================================

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
            contoursTab = ContoursTab(parent=self, container=self, mainWindow=self.mainWindow,
                                      spectrum=thisSpec,
                                      showCopyOptions=True if len(self.orderedSpectra) > 1 else False,
                                      copyToSpectra=self.orderedSpectra)
            self.tabWidget.addTab(contoursTab, thisSpec.name)
            contoursTab.setContentsMargins(*TABMARGINS)

        self.tabWidget.setTabClickCallback(self._tabClicked)

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

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton,
                           self._revertButton, self._currentNumApplies)

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
                for inTab in [tab for tab in self.tabs if tab != fromSpectrumTab and tab.spectrum in toSpectra]:
                    try:
                        inTab._copySpectrumAttributes(fromSpectrumTab)
                    except Exception:
                        pass

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))


#=========================================================================================
# SpectrumDisplayPropertiesPopup1d
#=========================================================================================

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
            colourTab = ColourTab(parent=self, container=self, mainWindow=self.mainWindow,
                                  spectrum=thisSpec,
                                  showCopyOptions=True if len(self.orderedSpectra) > 1 else False,
                                  copyToSpectra=self.orderedSpectra
                                  )
            self.tabWidget.addTab(colourTab, thisSpec.name)
            colourTab.setContentsMargins(*TABMARGINS)

        self.tabWidget.setTabClickCallback(self._tabClicked)

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

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton,
                           self._revertButton, self._currentNumApplies)

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
                    except Exception:
                        pass

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))


#=========================================================================================
# GeneralTab
#=========================================================================================

class _SpectrumPathRow(SpectrumPathRow):
    """Just a class to re-jig the columns"""
    SELECT_COLLUMN = 4  # Not used
    LABEL_COLLUMN = 0
    DATAFORMAT_COLLUMN = 5  # Not used
    DATA_COLLUMN = 1
    BUTTON_COLLUMN = 2
    RELOAD_COLLUMN = 3  # Not used


class GeneralTab(Widget):
    def __init__(self, parent=None, container=None, mainWindow=None, spectrum=None, item=None, colourOnly=False):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)
        self.setWindowTitle("Spectrum Properties")
        self.setMinimumHeight(600)
        self.setMinimumWidth(400)

        self._parent = parent
        self._container = container  # master widget that this is attached to
        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project

        self.item = item
        self.spectrum = spectrum
        self._changes = ChangeDict()
        self.atomCodes = ()

        self.experimentTypes = self.project._experimentTypeMap
        self._setWidgets(spectrum)

    def _setWidgets(self, spectrum):
        row = 0
        Label(self, text="Pid", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'pid'),
              bold=True, **_alignLabel)
        self.spectrumPidLabel = Label(self, grid=(row, 1), **_align1)
        row += 1
        Label(self, text="Name", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'name'), **_alignLabel)
        self.nameData = LineEdit(self, textAlignment='left', grid=(row, 1), backgroundText='> Enter name <', **_align2)
        self.nameData.textChanged.connect(partial(self._queueSpectrumNameChange, spectrum))  # ejb - was editingFinished

        row += 1
        Label(self, text="Comment", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'comment'), **_alignLabel)
        self.commentData = LineEdit(self, textAlignment='left', grid=(row, 1), backgroundText='> Optional <', **_align2)
        self.commentData.textChanged.connect(
                partial(self._queueSpectrumCommentChange, spectrum))  # ejb - was editingFinished

        #======= HLine ======
        row += 1
        hLine = HLine(self, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15, divisor=2)

        row += 1
        Label(self, text="Path", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'filePath'), **_alignLabel)
        self.spectrumRow = _SpectrumPathRow(parentWidget=self, rowIndex=row,
                                            labelText=None,  # This skips the creation of the Label
                                            spectrum=self.spectrum,
                                            enabled=(not self.spectrum.isEmptySpectrum()),
                                            callback=self._queueSpectrumPathChange,
                                            )

        row += 1
        # Label(self, text="Data Format", grid=(row, 0),
        #       tipText=getAttributeTipText(Spectrum, 'Format of the binary data defined by path'), **_alignLabel)
        self.dataInfoWidget = Label(parent=self, grid=(row, 1), text=self.spectrum.dataSource._fileInfoString1,
                                    **_align1)

        # Date; not yet operational
        row += 1
        Label(self, text="Date Recorded", grid=(row, 0), **_alignLabel)
        self.dateRecordedWidget = LineEdit(self, text='> Unknown <', textAlignment='left', grid=(row, 1),
                                           editable=False, **_align2)

        row += 1
        Label(self, text="Temperature", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'temperature'),
              **_alignLabel)
        self.temperatureData = ScientificDoubleSpinBox(self, grid=(row, 1), min=0, max=1000.0, decimals=1, **_align2)
        self.temperatureData.valueChanged.connect(
            partial(self._queueTemperatureChange, spectrum, self.temperatureData.textFromValue))

        row += 1
        Label(self, text="Noise Level", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'noiseLevel'),
              **_alignLabel)
        self.noiseLevelData = ContourBaseSpinBox(self, grid=(row, 1), decimals=1, **_align2)
        self.noiseLevelData.valueChanged.connect(
            partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))

        row += 1
        Label(self, text="MAS Spinning Rate (Hz)", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'spinningRate'),
              **_alignLabel)
        self.spinningRateData = ScientificDoubleSpinBox(self, grid=(row, 1), min=0, max=100000.0, decimals=1, **_align2)
        self.spinningRateData.valueChanged.connect(
            partial(self._queueSpinningRateChange, spectrum, self.spinningRateData.textFromValue))

        #======= HLine ======
        row += 1
        hLine = HLine(self, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15, divisor=2)

        row += 1
        Label(self, text='Scaling', grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'scale'), **_alignLabel)
        self.spectrumScalingData = ScientificDoubleSpinBox(self, grid=(row, 1), min=-1e12, max=1e12, decimals=3,
                                                           **_align2)
        self.spectrumScalingData.valueChanged.connect(
            partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))

        # 1D specific Colour widget
        if spectrum.dimensionCount == 1:
            row += 1
            Label(self, text="Colour", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'sliceColour'),
                  **_alignLabel)
            self.colourBox = PulldownList(self, grid=(row, 1), **_align2)
            self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))
            colourButton = Button(self, hAlign='l', grid=(row, 2), hPolicy='fixed',
                                  callback=partial(self._queueSetSpectrumColour, spectrum), icon='icons/colours')

        row += 1
        Label(self, text="Chemical Shift List", grid=(row, 0),
              tipText=getAttributeTipText(Spectrum, 'chemicalShiftList'), **_alignLabel)
        self.chemicalShiftListPulldown = PulldownList(self, grid=(row, 1),
                                                      callback=partial(self._queueChemicalShiftListChange, spectrum),
                                                      **_align2
                                                      )

        #====== Peak Picking ======
        if spectrum.dimensionCount == 1:
            row += 1
            Label(self, text="Default 1d peak picker", vAlign='t', hAlign='l', grid=(row, 0))
            self.peakPicker1dData = PulldownList(self, vAlign='t', grid=(row, 1), headerText='< default >')
            self.peakPicker1dData.currentIndexChanged.connect(partial(self._queueChangePeakPicker1dIndex, spectrum))
            row += 1
            self.peakFittingMethodLabel = Label(self, text="Peak interpolation method", grid=(row, 0))
            self.peakFittingMethod = RadioButtons(self, texts=PEAKFITTINGDEFAULTS,
                                                  callback=self._queueSetPeakFittingMethod,
                                                  direction='h',
                                                  grid=(row, 1), hAlign='l',  #gridSpan=(1, 2),
                                                  tipTexts=None,
                                                  )
            self.peakFittingMethodLabel.setEnabled(False)
            self.peakFittingMethodLabel.setVisible(False)
            self.peakFittingMethod.setEnabled(False)
            self.peakFittingMethod.setVisible(False)
            # row += 1
            # self.dropFactorLabel = Label(self, text="1D Peak picking drop (%)",
            #                                   tipText='Increase to filter out more', grid=(row, 0))
            # self.peakFactor1D = DoubleSpinbox(self, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=-100,
            #                                   max=100)
            # # self.peakFactor1D.valueChanged.connect(self._queueSetDropFactor1D)
        else:
            row += 1
            Label(self, text="Default nD peak picker", vAlign='t', hAlign='l', grid=(row, 0))
            self.peakPickerNdData = PulldownList(self, vAlign='t', grid=(row, 1), headerText='< default >')
            self.peakPickerNdData.currentIndexChanged.connect(partial(self._queueChangePeakPickerNdIndex, spectrum))
            row += 1
            self.peakFittingMethodLabel = Label(self, text="Peak interpolation method", grid=(row, 0))
            self.peakFittingMethod = RadioButtons(self, texts=PEAKFITTINGDEFAULTS,
                                                  callback=self._queueSetPeakFittingMethod,
                                                  direction='h',
                                                  grid=(row, 1), hAlign='l',  #gridSpan=(1, 2),
                                                  tipTexts=None,
                                                  )
            self.peakFittingMethodLabel.setEnabled(False)
            self.peakFittingMethodLabel.setVisible(False)
            self.peakFittingMethod.setEnabled(False)
            self.peakFittingMethod.setVisible(False)
            # row += 1
            # self.dropFactorLabel = Label(self, text="nD Peak picking drop (%)",
            #                                   tipText='Increase to filter out more', grid=(row, 0))
            # self.peakFactorNd = DoubleSpinbox(self, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=-100,
            #                                   max=100)
            # # self.peakFactorNd.valueChanged.connect(self._queueSetDropFactor1D)

        row += 1
        Label(self, text="Sample", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'sample'), **_alignLabel)
        self.samplesPulldownList = PulldownList(self, grid=(row, 1), **_align2)
        self.samplesPulldownList.currentIndexChanged.connect(partial(self._queueSampleChange, spectrum))

        row += 1
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

            self.spectrumRow.revert()
            self.spectrumPidLabel.setText(self.spectrum.pid)
            self.nameData.setText(self.spectrum.name)
            self.commentData.setText(self.spectrum.comment)

            try:
                idx = self.spectrum.project.chemicalShiftLists.index(self.spectrum.chemicalShiftList)
            except Exception:
                idx = 0
            self.chemicalShiftListPulldown.setData(
                [csList.pid for csList in self.project.chemicalShiftLists] + ['<New>'])
            self.chemicalShiftListPulldown.setIndex(idx)

            self.samplesPulldownList.clear()
            # add a blank item
            self.samplesPulldownList.addItem('', None)
            for sample in self.project.samples:
                self.samplesPulldownList.addItem(sample.name, sample)
            if self.spectrum.sample is not None:
                self.samplesPulldownList.select(self.spectrum.sample.name)

            # add the colour button just for 1d spectra
            if self.spectrum.dimensionCount == 1:
                # populate initial pulldown
                fillColourPulldown(self.colourBox, allowAuto=False, includeGradients=False)
                _setColourPulldown(self.colourBox, self.spectrum.sliceColour)

            # experimentTypes = _getExperimentTypes(self.spectrum.project, self.spectrum)
            # texts = ('',) + tuple(experimentTypes.keys()) if experimentTypes else ()
            # objects = ('',) + tuple(experimentTypes.values()) if experimentTypes else ()
            # self.spectrumType.setData(texts=texts, objects=objects)
            #
            # if (text := self.spectrum.experimentType):
            #     # reference-experiment is set
            #     key = self.spectrum.synonym or text
            #     # Added to account for renaming of experiments
            #     key = priorityNameRemapping.get(key, key)
            #
            #     if (idx := self.spectrumType.findText(key)) > 0:
            #         self.spectrumType.setCurrentIndex(idx)

            # add the peakPicker list
            from ccpn.core.lib.PeakPickers.PeakPickerABC import getPeakPickerTypes

            _peakPickers = getPeakPickerTypes()
            if self.spectrum.dimensionCount == 1:
                self.peakPicker1dData.setData(texts=sorted([name for name, pp in _peakPickers.items()]))
                if pp := self.spectrum.peakPicker:
                    self.peakPicker1dData.set(pp.peakPickerType)
            else:
                self.peakPickerNdData.setData(texts=sorted([name for name, pp in _peakPickers.items()
                                                            if not pp.onlyFor1D]))
                if pp := self.spectrum.peakPicker:
                    self.peakPickerNdData.set(pp.peakPickerType)
            # this is still a global value here :|
            self.peakFittingMethod.setIndex(PEAKFITTINGDEFAULTS.index(
                    self.application.preferences.general.peakFittingMethod))

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
        return self._container._getChangeState()

    # @queueStateChange(_verifyPopupApply)
    # def _queueSetValidateDataUrl(self, dataUrl, newUrl, urlValid, dim):
    #     """Set the new url in the dataUrl
    #     dim is required by the decorator to give a unique id for dataUrl row
    #     """
    #     if newUrl != dataUrl.url.path:
    #         return partial(self._validatePreferencesDataUrl, dataUrl, newUrl, urlValid, dim)
    #
    # def _validatePreferencesDataUrl(self, dataUrl, newUrl, urlValid, dim):
    #     """Put the new dataUrl into the dataUrl and the preferences.general.dataPath
    #     Extra step incase urlValid needs to be checked
    #     """
    #     self._validateFrame.dataUrlFunc(dataUrl, newUrl)
    #
    # @queueStateChange(_verifyPopupApply)
    # def _queueSetValidateFilePath(self, spectrum, filePath, dim):
    #     """Set the new filePath for the spectrum
    #     dim is required by the decorator to give a unique id for filePath row
    #     """
    #     if filePath != spectrum.filePath:
    #         return partial(self._validateFrame.filePathFunc, spectrum, filePath)

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumNameChange(self, spectrum, value):
        if value != spectrum.name:
            return partial(self._changeSpectrumName, spectrum, value)

    @staticmethod
    def _changeSpectrumName(spectrum, name):
        spectrum.rename(name)

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumPathChange(self, value):
        """Callback when validating text of the spectrumRow instance
        """
        if self.spectrumRow.hasChanged:
            return self._changeSpectrumPath

    def _changeSpectrumPath(self):
        """Method queued to update the spectrum row on apply
        """
        self.spectrumRow.update()

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumCommentChange(self, spectrum, value):
        if value != spectrum.comment:
            return partial(self._changeSpectrumComment, spectrum, value)

    @staticmethod
    def _changeSpectrumComment(spectrum, comment):
        spectrum.comment = comment

    @queueStateChange(_verifyPopupApply)
    def _queueSpectrumScaleChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.scale)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setSpectrumScale, spectrum, value)

    @staticmethod
    def _setSpectrumScale(spectrum, scale):
        spectrum.scale = float(scale)

    @queueStateChange(_verifyPopupApply)
    def _queueNoiseLevelDataChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.noiseLevel) if spectrum.noiseLevel else None
        if textFromValue(value) != specValue:
            return partial(self._setNoiseLevelData, spectrum, value)

    @staticmethod
    def _setNoiseLevelData(spectrum, noise):
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
    def _queueSampleChange(self, spectrum, _value):
        _text, sample = self.samplesPulldownList.getSelected()
        return partial(self._changeSampleSpectrum, spectrum, sample)

    @staticmethod
    def _changeSampleSpectrum(spectrum, sample):
        spectrum.sample = sample

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectrumType(self, spectrum, value):
        if self.spectrumType.getObject() is not None:
            expType = self.spectrumType.objects[value] if 0 <= value < len(self.spectrumType.objects) else None
            if expType != spectrum.experimentType:
                return partial(self._setSpectrumType, spectrum, expType)

    @staticmethod
    def _setSpectrumType(spectrum, expType):
        spectrum.experimentType = expType or None

    @queueStateChange(_verifyPopupApply)
    def _queueChangePeakPicker1dIndex(self, spectrum, _value):
        value = self.peakPicker1dData.get() or None
        if value != spectrum.peakPicker:
            return partial(self._updatePeakPickerOnSpectra, [spectrum], value)

    # def _setPeakPicker1d(self, spectrum, value):
    #     """Set the default peak picker for 1d spectra
    #     """
    #     self._updatePeakPickerOnSpectra([spectrum], value)

    @queueStateChange(_verifyPopupApply)
    def _queueChangePeakPickerNdIndex(self, spectrum, _value):
        value = self.peakPickerNdData.get() or None
        if value != spectrum.peakPicker:
            return partial(self._updatePeakPickerOnSpectra, [spectrum], value)

    # def _setPeakPickerNd(self, spectrum, value):
    #     """Set the default peak picker for Nd spectra
    #     """
    #     self._updatePeakPickerOnSpectra([spectrum], value)

    @staticmethod
    def _updatePeakPickerOnSpectra(spectra, value):
        from ccpn.core.lib.ContextManagers import undoBlock
        from ccpn.core.lib.PeakPickers.PeakPickerABC import getPeakPickerTypes

        PeakPicker = getPeakPickerTypes().get(value)
        if PeakPicker is None:  # Don't use a fetch or fallback to default. User should select one.
            raise RuntimeError(f'Cannot find a PeakPicker called {value}.')
        # getLogger().info(f'Setting the {value} PeakPicker to Spectra')
        with undoBlock():
            for sp in spectra:
                if sp.peakPicker and sp.peakPicker.peakPickerType == value:
                    continue  # is the same. no need to reset.
                sp.peakPicker = None
                thePeakPicker = PeakPicker(spectrum=sp)
                sp.peakPicker = thePeakPicker

    @queueStateChange(_verifyPopupApply)
    def _queueSetPeakFittingMethod(self):
        value = PEAKFITTINGDEFAULTS[self.peakFittingMethod.getIndex()]
        if value != self.application.preferences.general.peakFittingMethod:
            return partial(self._setPeakFittingMethod, value)

    def _setPeakFittingMethod(self, value):
        """Set the matching of the axis codes across different strips
        """
        self.application.preferences.general.peakFittingMethod = value

    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            self._container._fillPullDowns()
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

    @staticmethod
    def _setSpinningRate(spectrum, value):
        spectrum.spinningRate = float(value)

    @queueStateChange(_verifyPopupApply)
    def _queueTemperatureChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.temperature or 0.0)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setTemperature, spectrum, value)

    @staticmethod
    def _setTemperature(spectrum, value):
        spectrum.temperature = float(value)


#=========================================================================================
# DimensionsTab
#=========================================================================================

class DimensionsTab(Widget):

    def __init__(self, parent=None, container=None, mainWindow=None, spectrum=None, dimensions=None):
        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self._container = container  # master widget that this is attached to
        self.mainWindow = mainWindow
        self.spectrum = spectrum
        self.dimensions = dimensions
        self._magTransfers = self.spectrum.magnetisationTransfers

        self._changes = ChangeDict()
        self._referenceExperiment = self.spectrum.experimentType
        self._referenceDimensions = self.spectrum.referenceExperimentDimensions
        self._warningShown = False

        # Some definitions
        self._isotopeList = [r.isotopeCode for r in isotopeRecords.values() if r.spin > 0]  # All isotopes with a spin
        self._coherenceOrderList = CoherenceOrder.names()
        numCohOrders = max(CoherenceOrder.dataValues())

        _dimIndices = list(range(dimensions))

        # Start filling the rows
        row = 0
        Label(self, text="Dimensions", grid=(row, 0), bold=True, **_alignLabel)
        for i in range(dimensions):
            Label(self, text='%s' % str(i + 1), grid=(row, i + 1), bold=True, **_align1)

        #======= HLine ======
        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)

        # row += 1
        # self.addSpacer(10, 10, grid=(row, 0), expandX=True, expandY=False)

        row += 1
        Label(self, text="Point Counts ", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'pointCounts'),
              **_alignLabel)
        self._pointCountsLabels = [Label(self, grid=(row, i + 1), **_align1) for i in _dimIndices]

        row += 1
        Label(self, text="Data Types", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'pointCounts'),
              **_alignLabel)
        self._dataTypeLabels = [Label(self, grid=(row, i + 1), **_align1) for i in _dimIndices]

        row += 1
        Label(self, text="Dimension Types", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'dimensionTypes'),
              **_alignLabel)
        self._dimensionTypesLabels = [Label(self, grid=(row, i + 1), **_align1) for i in _dimIndices]

        row += 1
        Label(self, text="Coherence Orders", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'coherenceOrders'),
              **_alignLabel)
        self.coherenceOrderPullDowns = [PulldownList(self, grid=(row, i + 1), **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.coherenceOrderPullDowns[i].setData(self._coherenceOrderList)
            self.coherenceOrderPullDowns[i].currentIndexChanged.connect(
                partial(self._queueSetCoherenceOrders, spectrum, self.coherenceOrderPullDowns[i].getText, i))

        row += 1
        Label(self, text="Isotope Codes", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'isotopeCodes'),
              **_alignLabel)
        self.isotopeCodePullDowns: list[list[PulldownList | None]] = [[None for _ in range(len(CoherenceOrder))]
                                                                      for _ in range(dimensions)]
        row -= 1  # Temporarily lower as it is increased again in the loop
        for dd in range(numCohOrders):
            row += 1
            for i in _dimIndices:
                self.isotopeCodePullDowns[i][dd] = PulldownList(self, grid=(row, i + 1), **_align2)
                self.isotopeCodePullDowns[i][dd].setData(self._isotopeList)
                self.isotopeCodePullDowns[i][dd].currentIndexChanged.connect(
                    partial(self._queueSetIsotopeCodes, spectrum, self.isotopeCodePullDowns[i][dd].getText, i, dd))
        row += 1
        Label(self, text="Spectrum Widths (ppm)", grid=(row, 0),

              tipText=getAttributeTipText(Spectrum, 'spectralWidths'), **_alignLabel)
        self.spectralWidthsData = [ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=3, step=0.1, **_align2) for
                                   i in _dimIndices]
        for i in _dimIndices:
            self.spectralWidthsData[i].valueChanged.connect(partial(self._queueSetSpectralWidths, spectrum, i,
                                                                    self.spectralWidthsData[i].textFromValue))

        row += 1
        Label(self, text="Spectral Widths (Hz)", grid=(row, 0),

              tipText=getAttributeTipText(Spectrum, 'spectralWidthsHz'), **_alignLabel)
        self.spectralWidthsHzData = [ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=1, step=0.1, **_align2)
                                     for i in _dimIndices]
        for i in _dimIndices:
            self.spectralWidthsHzData[i].valueChanged.connect(partial(self._queueSetSpectralWidthsHz, spectrum, i,
                                                                      self.spectralWidthsHzData[i].textFromValue))

        row += 1
        Label(self, text="Spectrometer Frequencies (MHz) ", grid=(row, 0),

              tipText=getAttributeTipText(Spectrum, 'spectrometerFrequencies'), **_alignLabel)
        self.spectrometerFrequenciesData = [
            ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=6, step=0.1, **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.spectrometerFrequenciesData[i].valueChanged.connect(
                partial(self._queueSetSpectrometerFrequencies, spectrum, i,
                        self.spectrometerFrequenciesData[i].textFromValue))

        row += 1
        Label(self, text="Referencing (ppm) ", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'referenceValues'),
              **_alignLabel)
        self.spectralReferencingData = [
            ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=3, step=0.1, **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.spectralReferencingData[i].valueChanged.connect(
                partial(self._queueSetDimensionReferencing, spectrum, i,
                        self.spectralReferencingData[i].textFromValue))

        row += 1
        Label(self, text="Referencing (points)", grid=(row, 0),

              tipText=getAttributeTipText(Spectrum, 'referencePoints'), **_alignLabel)
        self.spectralReferencingDataPoints = [
            ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=1, step=0.1, **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.spectralReferencingDataPoints[i].valueChanged.connect(
                partial(self._queueSetPointDimensionReferencing, spectrum, i,
                        self.spectralReferencingDataPoints[i].textFromValue))

        row += 1
        Label(self, text="Assignment Tolerances", grid=(row, 0),

              tipText=getAttributeTipText(Spectrum, 'assignmentTolerances'), **_alignLabel)
        self.spectralAssignmentToleranceData = [
            ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=2, step=0.1, **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.spectralAssignmentToleranceData[i].valueChanged.connect(
                partial(self._queueSetAssignmentTolerances, spectrum, i,
                        self.spectralAssignmentToleranceData[i].textFromValue))

        row += 1
        Label(self, text="Second Cursor Offsets (Hz)", grid=(row, 0),
              tipText=getAttributeTipText(Spectrum, 'doubleCrosshairOffsets'), **_alignLabel)
        self.spectralDoubleCursorOffset = [
            ScientificDoubleSpinBox(self, grid=(row, i + 1), decimals=1, step=0.1, **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.spectralDoubleCursorOffset[i].valueChanged.connect(
                partial(self._queueSetDoubleCursorOffset, spectrum, i,
                        self.spectralDoubleCursorOffset[i].textFromValue))

        row += 1
        Label(self, text="Aliasing", grid=(row, 0), bold=True, **_alignLabel)
        self.displayedFoldedContours = CheckBox(self, grid=(row, 1), **_align2)
        self.displayedFoldedContours.clicked.connect(
            partial(self._queueSetDisplayFoldedContours, spectrum, self.displayedFoldedContours.isChecked))

        row += 1
        # disabled until getRegion correctly fetches mirrored/inverted regions
        _visible = False
        _FoldingModeLabel = Label(self, text="Dimension is Circular", grid=(row, 0),

              tipText=getAttributeTipText(Spectrum, 'foldingModes'), **_alignLabel)
        _FoldingModeLabel.setVisible(_visible)
        self.foldingModesCheckBox = [CheckBox(self, grid=(row, i + 1), **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.foldingModesCheckBox[i].clicked.connect(
                partial(self._queueSetFoldingModes, spectrum, self.foldingModesCheckBox[i].isChecked, i))
            self.foldingModesCheckBox[i].setVisible(False)

        # # Not implemented yet
        # row += 1
        # Label(self, text="Dimension is Inverted", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'invertedModes'), **_alignLabel)

        row += 1
        Label(self, text="Upperbound Limits", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'aliasingLimits'),
              **_alignLabel)
        self.maxAliasingPullDowns = [PulldownList(self, grid=(row, i + 1), **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.maxAliasingPullDowns[i].activated.connect(
                partial(self._queueSetMaxAliasing, spectrum, self.maxAliasingPullDowns[i].getText, i))

        row += 1
        Label(self, text="Lowerbound Limits", grid=(row, 0), **_alignLabel)
        self.minAliasingPullDowns = [PulldownList(self, grid=(row, i + 1), **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.minAliasingPullDowns[i].activated.connect(
                partial(self._queueSetMinAliasing, spectrum, self.minAliasingPullDowns[i].getText, i))

        #======= HLine ======
        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)

        row += 1
        Label(self, text="Axis Codes", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'axisCodes'), **_alignLabel)
        self.axisCodeEdits = [LineEdit(self, grid=(row, i + 1), textAlignment='left', hPolicy='expanding', **_align2)
                              for i in _dimIndices]
        for i in _dimIndices:
            self.axisCodeEdits[i].textChanged.connect(partial(self._queueSetAxisCodes,  # type: ignore
                                                              spectrum, ))

        row += 1
        _dimOrderLabel = Label(self, text="Preferred Dimension Order", grid=(row, 0),
                               tipText=getAttributeTipText(Spectrum, 'setDimensionOrdering'), **_alignLabel)
        self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self, labelText=None, grid=(row, 1),
                                                                     gridSpan=(1, 1),
                                                                     callback=partial(
                                                                         self._queueSetSpectrumOrderingComboIndex,
                                                                         spectrum),
                                                                     **_align2)
        # Only for nD:
        _dimOrderLabel.setVisible(self.dimensions > 1)
        self.preferredAxisOrderPulldown.setVisible(self.dimensions > 1)

        #======= HLine ======
        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)

        row += 1
        Label(self, text="Reference Experiment", grid=(row, 0), bold=True,
              tipText=getAttributeTipText(Spectrum, 'experimentType'), **_alignLabel)

        row += 1
        _specLabel = Label(self, text="Type", grid=(row, 0), tipText=getAttributeTipText(Spectrum, 'experimentType'),
                           **_alignLabel)
        # reference experiment type - editable because has a search-completer
        self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(row, 1), gridSpan=(1, dimensions + 1))
        # Added to account for renaming of experiments
        self.spectrumType.currentIndexChanged.connect(partial(self._queueSetSpectrumType, spectrum))
        _specButton = Button(self, grid=(row, 1 + dimensions + 1),
                             callback=partial(self._raiseExperimentFilterPopup, spectrum),
                             hPolicy='fixed', icon='icons/applications-system')

        row += 1
        Label(self, text="Dimensions", grid=(row, 0),
              tipText=getAttributeTipText(Spectrum, 'referenceExperimentDimensions'), **_alignLabel)
        self.referenceDimensionPullDowns = [PulldownList(self, grid=(row, i + 1), **_align2) for i in _dimIndices]
        for i in _dimIndices:
            self.referenceDimensionPullDowns[i].currentIndexChanged.connect(  # type: ignore
                                                                            partial(self._queueSetReferenceDimensions,
                                                                            spectrum, ))  #self.referenceDimensionPullDowns[i].getText, i))
        row += 1
        # button to copy to axis Codes
        _copyBox = Frame(self, setLayout=True, grid=(row, 1), gridSpan=(1, dimensions))
        _copyButton = Button(_copyBox, text='Copy to Axis Codes' if dimensions > 1 else 'Copy to Axis Code',
                             hAlign='r',
                             # icon='icons/update.png',
                             grid=(0, 0),
                             callback=self._copyReferenceExperiments,
                             tipText='Copy all non-empty reference experiment dimensions to axis codes')

        # magnetisation transfer table
        row += 1
        _magTransferLabel = Label(self, text="Magnetisation Transfers", grid=(row, 0),
                                  tipText=getAttributeTipText(Spectrum, 'magnetisationTransfers'), **_alignLabel)
        _data = pd.DataFrame(columns=MagnetisationTransferParameters)
        _refMagTransfer = self.magnetisationTransferTable = MagnetisationTransferTable(self,
                                                                                       spectrum=self.spectrum,
                                                                                       df=_data,
                                                                                       showVerticalHeader=False,
                                                                                       borderWidth=1,
                                                                                       _resize=True,
                                                                                       setHeightToRows=True,
                                                                                       setWidthToColumns=True,
                                                                                       setOnHeaderOnly=True)
        _refMagTransfer.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.getLayout().addWidget(_refMagTransfer, row, 1, 1, dimensions + 2)
        self.magnetisationTransferTable.tableChanged.connect(partial(self._queueSetMagnetisationTransfers, spectrum))
        # Only visible for nD:
        _refMagTransfer.setVisible(self.dimensions > 1)
        _magTransferLabel.setVisible(self.dimensions > 1)

        # row += 1
        # hLine = HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15, divisor=2)
        # hLine.setContentsMargins(5, 0, 0, 0)

        # #======= HLine ======
        # row += 1
        # hLine = HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 2), colour=getColours()[DIVIDER], height=15)
        # hLine.setContentsMargins(5, 0, 0, 0)

        # End; add spacer to fill empty space
        row += 1
        self.addSpacer(10, 10, grid=(row, 1), expandX=True, expandY=True)

    def _fillPreferredWidgetFromAxisTexts(self):
        """Fill the pullDown during preSelect
        """
        with self.blockWidgetSignals(self.preferredAxisOrderPulldown):
            self._populatePreferredOrder()

    def _populatePreferredOrder(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(
                self.spectrum._preferredAxisOrdering[:self.spectrum.dimensionCount]) \
            if self.spectrum._preferredAxisOrdering is not None else None

        axisCodeTexts = tuple(ss.text() for ss in self.axisCodeEdits)
        ll = ['<None>']

        if self.spectrum.dimensionCount == 1:
            # a bit of a hack, but, for 1d the specOrder is saved as (0,) or (1,) which is potentially dangerous
            #   but is changed to (0, 1) or (1, 0) for the popup
            axisCodeTexts += ('intensity',)
            if len(specOrder) == 1:
                specOrder += (1 - specOrder[0],)

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

            axisCodes = spectrum.axisCodes
            if self.spectrum.dimensionCount > 1:
                axisOrder = tuple(permutations(list(range(len(axisCodes)))))
                value = tuple(axisOrder[index - 1])
                if value != spectrum._preferredAxisOrdering:
                    return partial(self._setSpectrumOrdering, spectrum, value)

            else:
                axisCodes += ['intensity']

                axisOrder = tuple(permutations(list(range(len(axisCodes)))))
                value = tuple(axisOrder[index - 1])
                if value != spectrum._preferredAxisOrdering:
                    return partial(self._setSpectrumOrdering, spectrum, value[:1])  # only store the first value

    @staticmethod
    def _setSpectrumOrdering(spectrum, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        spectrum._preferredAxisOrdering = value

    def _fillPullDowns(self):
        pass

    def _getOnlyAvailable(self, expType):
        """Set the reference dimensions for those that only have one option when changing experiment-type
        """
        if (self._referenceExperiment or self.spectrum.experimentType) is None:
            return

        # get the nucleus codes from the current isotope codes
        refDimensions = list(self._referenceDimensions or self.spectrum.referenceExperimentDimensions)

        _referenceLists = [['', ] for val in refDimensions]
        _refDimensions = [val if val else '' for val in refDimensions]

        # get the permutations of the available experiment dimensions
        matches = self.spectrum.getAvailableReferenceExperimentDimensions(_experimentType=expType)
        if matches:
            for ac in matches:
                for ii in range(self.dimensions):
                    if ac[ii] not in _referenceLists[ii]:
                        _referenceLists[ii].append(ac[ii])

        for ii, (refList, ref, combo) in enumerate(
                zip(_referenceLists, _refDimensions, self.referenceDimensionPullDowns)):
            if len(refList) == 2:
                refDimensions[ii] = refList[1]
                combo.setIndex(1)

        self._referenceDimensions = tuple(refDimensions)

    def _populateReferenceDimensions(self):
        """Populate the references dimensions from the current experiment and the current value
        """
        # get the nucleus codes from the current isotope codes
        refDimensions = self._referenceDimensions or self.spectrum.referenceExperimentDimensions

        if (self._referenceExperiment or self.spectrum.experimentType) is None:
            _referenceLists = [['', val] if val else ['', ] for val in refDimensions]
            _refDimensions = [val if val else '' for val in refDimensions]

            for ii, (refList, ref) in enumerate(zip(_referenceLists, _refDimensions)):
                self.referenceDimensionPullDowns[ii].setData(refList)
                self.referenceDimensionPullDowns[ii].setIndex(refList.index(ref))

        else:
            _referenceLists = [['', ] for val in refDimensions]
            _refDimensions = [val if val else '' for val in refDimensions]

            # get the permutations of the available experiment dimensions
            matches = self.spectrum.getAvailableReferenceExperimentDimensions(_experimentType=self._referenceExperiment)
            if matches:
                for ac in matches:
                    for ii in range(self.dimensions):
                        if ac[ii] not in _referenceLists[ii]:
                            _referenceLists[ii].append(ac[ii])

            for ii, (refList, ref, combo) in enumerate(
                    zip(_referenceLists, _refDimensions, self.referenceDimensionPullDowns)):
                model = combo.model()
                if ref not in refList:
                    refList.append(ref)
                    combo.setData(list(refList))
                    self.referenceDimensionPullDowns[ii].set(ref)
                    color = QtGui.QColor('red')
                    itm = model.item(len(refList) - 1)
                    itm.setData(color, QtCore.Qt.ForegroundRole)
                else:
                    # clears/resets the foreground colours
                    combo.setData(list(refList))
                    combo.set(ref)
                combo.update()

    def _populateExperimentType(self):
        """Populate the experimentType pulldown
        """
        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        experimentTypes = _getExperimentTypes(self.spectrum.project, self.spectrum)
        texts = ('',) + tuple(experimentTypes.keys()) if experimentTypes else ()
        objects = ('',) + tuple(experimentTypes.values()) if experimentTypes else ()
        self.spectrumType.setData(texts=texts, objects=objects)

        self._referenceExperiment = None
        if (text := self.spectrum.experimentType):
            # reference-experiment is set
            key = self.spectrum.synonym or text
            key = priorityNameRemapping.get(key, key)

            if (idx := self.spectrumType.findText(key)) > 0:
                self.spectrumType.setCurrentIndex(idx)
                self._referenceExperiment = key

    def _populateMagnetisationTransfers(self, revert=0):
        """Populate the magnetisation transfers table
        """
        # refDimensions = self._referenceDimensions or self.spectrum.referenceExperimentDimensions
        refDimensions = tuple(val.getText() or None for val in
                              self.referenceDimensionPullDowns) or self.spectrum.referenceExperimentDimensions
        refExperimentName = self.spectrumType.getText()

        if (self._referenceExperiment or self.spectrum.experimentType) is None:
            _referenceLists = [['', val] if val else ['', ] for val in refDimensions]
            _refDimensions = [val if val else '' for val in refDimensions]

            for ii, (refList, ref) in enumerate(zip(_referenceLists, _refDimensions)):
                self.referenceDimensionPullDowns[ii].setData(refList)
                self.referenceDimensionPullDowns[ii].setIndex(refList.index(ref))

        if self._referenceExperiment:
            # need the same behaviour as the api - defaults to axisCode if not defined
            magTransfers = _getApiExpTransfers(self.spectrum, refExperimentName,
                                               [(ref or ax) for ref, ax in zip(refDimensions, self.spectrum.axisCodes)])
            editable = False

        else:
            magTransfers = self.spectrum.magnetisationTransfers if revert else self._magTransfers
            editable = True

        self.magnetisationTransferTable.populateTable(magTransfers, editable=editable)

    def _populateDimension(self, revert=0):
        """Populate dimensions tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():

            self.aliasLim = self.spectrum.aliasingLimits
            self.aliasInds = self.spectrum.aliasingIndexes
            # self.axesReversed = self.spectrum.axesReversed
            self.foldLim = tuple(sorted(lim) for lim in self.spectrum.foldingLimits)
            self.deltaLim = self.spectrum.spectralWidths  # tuple(max(lim) - min(lim) for lim in self.foldLim)

            isoCodes = self.spectrum.mqIsotopeCodes
            cohOrders = self.spectrum.coherenceOrders
            for i in range(self.dimensions):
                value = self.spectrum.axisCodes[i]
                self.axisCodeEdits[i].setText('<None>' if value is None else str(value))

                cohCount = CoherenceOrder.get(cohOrders[i]).dataValue
                dimIsoCodes = isoCodes[i]
                for cc in range(cohCount):
                    icPulldown: PulldownList = self.isotopeCodePullDowns[i][cc]
                    icPulldown.setVisible(True)
                    if cc < len(dimIsoCodes) and dimIsoCodes[cc] in self._isotopeList:
                        icPulldown.setIndex(self._isotopeList.index(dimIsoCodes[cc]))
                    else:
                        # maybe too small
                        icPulldown.setIndex(0)
                for cc in range(cohCount, max(CoherenceOrder.dataValues())):
                    icPulldown: PulldownList = self.isotopeCodePullDowns[i][cc]
                    icPulldown.setVisible(False)

                if self.spectrum.coherenceOrders[i] in self._coherenceOrderList:
                    self.coherenceOrderPullDowns[i].setIndex(
                        self._coherenceOrderList.index(self.spectrum.coherenceOrders[i]))

                self._pointCountsLabels[i].setText(str(self.spectrum.pointCounts[i]))
                self._dataTypeLabels[i].setText(self.spectrum.dataTypes[i])
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
                # self.invertedCheckBox[i].setChecked(False)  # not implemented yet

                # pullDown for min/max aliasing
                aliasMaxRange = list(
                        max(self.foldLim[i]) + rr * self.deltaLim[i]
                                     for rr in range(MAXALIASINGRANGE, -1, -1))
                aliasMinRange = list(
                        min(self.foldLim[i]) + rr * self.deltaLim[i]
                                     for rr in range(0, -MAXALIASINGRANGE - 1, -1))
                aliasMaxText = [f'{MAXALIASINGRANGE - ii}   ({aa:.3f} ppm)' for ii, aa in enumerate(aliasMaxRange)]
                aliasMinText = [f'{-ii}   ({aa:.3f} ppm)' for ii, aa in enumerate(aliasMinRange)]

                self.maxAliasingPullDowns[i].setData(aliasMaxText)
                # _close = (max(self.aliasLim[i]) - max(self.foldLim[i]) + self.deltaLim[i] / 2) // self.deltaLim[i]
                # self.maxAliasingPullDowns[i].setIndex(MAXALIASINGRANGE - int(_close))
                # just use the aliasingIndexes
                self.maxAliasingPullDowns[i].setIndex(MAXALIASINGRANGE - self.aliasInds[i][1])

                self.minAliasingPullDowns[i].setData(aliasMinText)
                # _close = (min(self.foldLim[i]) - min(self.aliasLim[i]) + self.deltaLim[i] / 2) // self.deltaLim[i]
                # self.minAliasingPullDowns[i].setIndex(int(_close))
                self.minAliasingPullDowns[i].setIndex(-self.aliasInds[i][0])

            self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidgetFromAxisTexts)
            self._populatePreferredOrder()

            self._populateExperimentType()
            self._populateReferenceDimensions()
            self._populateMagnetisationTransfers(revert=revert)

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._container._getChangeState()

    @queueStateChange(_verifyPopupApply)
    def _queueSetAssignmentTolerances(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.assignmentTolerances[dim] or 0.0)  # this means they are not being set
        if textFromValue(value) != specValue:
            return partial(self._setAssignmentTolerances, spectrum, dim, value)

    @staticmethod
    def _setAssignmentTolerances(spectrum, dim, value):
        assignmentTolerances = list(spectrum.assignmentTolerances)
        assignmentTolerances[dim] = float(value)
        spectrum.assignmentTolerances = assignmentTolerances

    @queueStateChange(_verifyPopupApply)
    def _queueSetDoubleCursorOffset(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.doubleCrosshairOffsets[dim] or 0.0)
        if textFromValue(value) != specValue:
            return partial(self._setDoubleCursorOffset, spectrum, dim, value)

    @staticmethod
    def _setDoubleCursorOffset(spectrum, dim, value):
        doubleCrosshairOffsets = list(spectrum.doubleCrosshairOffsets)
        doubleCrosshairOffsets[dim] = float(value)
        spectrum.doubleCrosshairOffsets = doubleCrosshairOffsets

    @queueStateChange(_verifyPopupApply)
    def _queueSetAxisCodes(self, spectrum,
                           _value):  #valueGetter, dim): # dim required to make the changeState unique per dim
        # set the axisCodes in single operation
        value = tuple(val.text() for val in self.axisCodeEdits)
        if value != spectrum.axisCodes:
            return partial(self._setAxisCodes, spectrum, value)  #, dim, value)

        # repopulate the preferred axis order pulldown
        self._fillPreferredWidgetFromAxisTexts()

    def _setAxisCodes(self, spectrum, value):

        count = 0
        for sd in self.mainWindow.spectrumDisplays:
            if sd.strips and spectrum in sd.strips[0].spectra:
                # set the border to red
                sd.mainWidget.setStyleSheet('Frame { border: 3px solid #FF1234; }')
                sd.mainWidget.setEnabled(False)
                for strp in sd.strips:
                    strp.setEnabled(False)
                    count += 1

        if count:
            showWarning('Change Axis Code',
                        'Changing Axis Codes can result in incorrect handling of axes in open Spectrum Displays.\n'
                        'Please close and reopen any Spectrum Displays outlined in red.')

        spectrum.axisCodes = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetIsotopeCodes(self, spectrum, valueGetter, dim, coherenceOrder, _value):
        value = valueGetter()
        dimMqCode = spectrum.mqIsotopeCodes[dim]
        mqCode = dimMqCode[coherenceOrder] if coherenceOrder < len(dimMqCode) else 'SQ'  # may be shorter if not defined
        if value != mqCode:
            return partial(self._setIsotopeCodes, spectrum, dim, value)

    def _setIsotopeCodes(self, spectrum, dim, value=None):
        self._updateIsotopeCodes(spectrum, dim)
        if not self._warningShown:
            showWarning('Change Isotope Code', 'Caution is advised when changing isotope codes\n'
                                               'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')
            self._warningShown = True

    def _updateIsotopeCodes(self, spectrum, dim):
        mqIsotopeCodes = list(spectrum.mqIsotopeCodes)
        cohOrders = spectrum.coherenceOrders
        mqIsotopeCodes[dim] = [self.isotopeCodePullDowns[dim][cc].get()
                               for cc in
                               range(CoherenceOrder.get(cohOrders[dim]).dataValue)]
        spectrum.mqIsotopeCodes = mqIsotopeCodes

    @queueStateChange(_verifyPopupApply)
    def _queueSetCoherenceOrders(self, spectrum, valueGetter, dim, _value):
        value = valueGetter()

        # change visibility
        cohOrders = self.coherenceOrderPullDowns[dim].get()
        cohCount = CoherenceOrder.get(cohOrders).dataValue
        for cc in range(cohCount):
            self.isotopeCodePullDowns[dim][cc].setVisible(True)
        for cc in range(cohCount, max(CoherenceOrder.dataValues())):
            self.isotopeCodePullDowns[dim][cc].setVisible(False)

        if value != spectrum.coherenceOrders[dim]:
            return partial(self._setCoherenceOrders, spectrum, dim, value)

    def _setCoherenceOrders(self, spectrum, dim, value):
        coherenceOrders = list(spectrum.coherenceOrders)
        coherenceOrders[dim] = str(value)
        spectrum.coherenceOrders = coherenceOrders
        # fix the length of the mqIsotopeCodes if not updated
        self._setIsotopeCodes(spectrum, dim)

    def _raiseExperimentFilterPopup(self, spectrum):
        from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup

        popup = ExperimentFilterPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=spectrum)
        popup.exec_()
        self.spectrumType.select(popup.expType)

    @queueStateChange(_verifyPopupApply, last=False)
    def _queueSetSpectrumType(self, spectrum, value):
        result = None
        if self.spectrumType.getObject() is not None:
            expType = self.spectrumType.objects[value] if 0 <= value < len(self.spectrumType.objects) else None
            if expType != spectrum.experimentType:
                self._referenceExperiment = expType or None
                self._magTransfers = None if self._referenceExperiment else self.spectrum.magnetisationTransfers

                result = partial(self._setSpectrumType, spectrum, expType)

                # set the only options here if available
                self._getOnlyAvailable(expType)

                if not expType:
                    # flag magTransfers to change if setting to empty - keeps current list
                    self._queueSetMagnetisationTransfers(self.spectrum, keepMagTransfers=True)

        # update the reference-dimensions and the magnetisation-transfers
        with self.blockWidgetSignals(blockUpdates=False):
            self._populateReferenceDimensions()
            self._populateMagnetisationTransfers()

        # update the reference-dimensions from the new experiment-type
        self._queueSetReferenceDimensions(spectrum, None)

        return result

    @staticmethod
    def _setSpectrumType(spectrum, expType):
        spectrum.experimentType = expType or None

    @queueStateChange(_verifyPopupApply)
    def _queueSetReferenceDimensions(self, spectrum, _value):  #valueGetter, dim):
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
                if len([True for _combo in self.referenceDimensionPullDowns if
                        _text and _text == _combo.getText()]) > 1:
                    color = QtGui.QColor('red')
                # use the palette to change the colour of the selection text - may not work for other themes
                palette = combo.palette()
                palette.setColor(QtGui.QPalette.Text, color)
                combo.setPalette(palette)

        self._referenceDimensions = tuple(_refDims)

        result = None
        if value != spectrum.referenceExperimentDimensions:
            result = partial(self._setReferenceDimensions, spectrum, value)  #, dim, value)

        with self.blockWidgetSignals(blockUpdates=False):
            self._populateMagnetisationTransfers()

        return result

    @staticmethod
    def _setReferenceDimensions(spectrum, value):  #, dim, value):
        """Set the value for a single referenceDimension
        - this can lead to non-unique values
        """
        spectrum.referenceExperimentDimensions = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetMagnetisationTransfers(self, spectrum, keepMagTransfers=False):
        # get the magTransfers
        value = self.magnetisationTransferTable.getMagnetisationTransfers()
        self._magTransfers = value if (self.spectrumType.getObject() is not None or keepMagTransfers) else None

        if sorted(value) != sorted(self.spectrum.magnetisationTransfers):
            return partial(self._setMagnetisationTransfers, spectrum, value)

    @staticmethod
    def _setMagnetisationTransfers(spectrum, value):  #, dim, value):
        """Set the magnetisationTransfers for the spectrum
        """
        try:
            spectrum._magnetisationTransfers = value
        except Exception:
            raise ValueError('Magnetisation Transfer Table contains bad values')

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

    def _setAliasingPulldowns(self, dim, spectrum):
        """Update aliasing pulldowns to reflect changes to spectrum proeprties."""
        newSw = self.spectralWidthsData[dim].value()
        _refPoint = self.spectralReferencingDataPoints[dim].value()
        _refPpm = self.spectralReferencingData[dim].value()
        _pointCount = spectrum.pointCounts[dim]
        _rev = spectrum.axesReversed[dim]
        _vpp = abs(newSw / _pointCount) * (-1.0 if _rev else 1.0)
        # 0.5 -> pointCount + 0.5
        _foldLim = sorted([_refPpm + (0.5 - _refPoint) * _vpp,
                           _refPpm + ((_pointCount + 0.5) - _refPoint) * _vpp])
        _deltaLim = newSw
        # pullDown for min/max aliasing
        aliasMaxRange = list(max(_foldLim) + rr * _deltaLim
                             for rr in range(MAXALIASINGRANGE, -1, -1))
        aliasMinRange = list(min(_foldLim) + rr * _deltaLim
                             for rr in range(0, -MAXALIASINGRANGE - 1, -1))
        aliasMaxText = [f'{MAXALIASINGRANGE - ii}   ({aa:.3f} ppm)' for ii, aa in enumerate(aliasMaxRange)]
        aliasMinText = [f'{-ii}   ({aa:.3f} ppm)' for ii, aa in enumerate(aliasMinRange)]
        ind = self.maxAliasingPullDowns[dim].currentIndex()
        self.maxAliasingPullDowns[dim].setData(aliasMaxText)
        self.maxAliasingPullDowns[dim].setIndex(ind)
        ind = self.minAliasingPullDowns[dim].currentIndex()
        self.minAliasingPullDowns[dim].setData(aliasMinText)
        self.minAliasingPullDowns[dim].setIndex(ind)

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectralWidths(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.spectralWidths[dim])
        if textFromValue(value) != specValue:
            # CHECK:ED - change _queueSetSpectralWidthsHz - watch out for cycle!
            with self.blockWidgetSignals(root=self):
                newSw = (value or 0.0)
                swhz = newSw * self.spectrometerFrequenciesData[dim].value()
                # update hz spinbox
                self.spectralWidthsHzData[dim].setValue(swhz)
                # update aliasing pulldowns
                self._setAliasingPulldowns(dim, spectrum)
            return partial(self._setSpectralWidths, spectrum, dim, value)

    @staticmethod
    def _setSpectralWidths(spectrum, dim, value):
        spectralWidths = list(spectrum.spectralWidths)
        spectralWidths[dim] = float(value)
        spectrum.spectralWidths = spectralWidths

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectralWidthsHz(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.spectralWidthsHz[dim])
        if textFromValue(value) != specValue:
            # CHECK:ED - change _queueSetSpectralWidths - watch out for cycle!
            with self.blockWidgetSignals(root=self):
                newSw = (value or 0.0) / self.spectrometerFrequenciesData[dim].value()
                # update ppm spinbox
                self.spectralWidthsData[dim].setValue(newSw)
                # update aliasing pulldowns
                self._setAliasingPulldowns(dim, spectrum)
            return partial(self._setSpectralWidthsHz, spectrum, dim, value)

    @staticmethod
    def _setSpectralWidthsHz(spectrum, dim, value):
        spectralWidthsHz = list(spectrum.spectralWidthsHz)
        spectralWidthsHz[dim] = float(value)
        spectrum.spectralWidthsHz = spectralWidthsHz

    @queueStateChange(_verifyPopupApply)
    def _queueSetSpectrometerFrequencies(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.spectrometerFrequencies[dim])
        if textFromValue(value) != specValue:
            # CHECK:ED - change _queueSetSpectralWidths - watch out for cycle!
            with self.blockWidgetSignals(root=self):
                self.spectralWidthsHzData[dim].setValue((value or 0.0) * self.spectralWidthsData[dim].value())
            return partial(self._setSpectrometerFrequencies, spectrum, dim, value)

    @staticmethod
    def _setSpectrometerFrequencies(spectrum, dim, value):
        spectrometerFrequencies = list(spectrum.spectrometerFrequencies)
        spectrometerFrequencies[dim] = float(value)
        spectrum.spectrometerFrequencies = spectrometerFrequencies

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyPopupApply)
    def _queueSetDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referenceValues[dim])
        if textFromValue(value) != specValue:
            # update aliasing pulldowns
            self._setAliasingPulldowns(dim, spectrum)
            return partial(self._setDimensionReferencing, spectrum, dim, value)

    @staticmethod
    def _setDimensionReferencing(spectrum, dim, value):
        spectrumReferencing = list(spectrum.referenceValues)
        spectrumReferencing[dim] = float(value)
        spectrum.referenceValues = spectrumReferencing

    @queueStateChange(_verifyPopupApply)
    def _queueSetPointDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referencePoints[dim] or 0.0)
        if textFromValue(value) != specValue:
            # update aliasing pulldowns
            self._setAliasingPulldowns(dim, spectrum)
            return partial(self._setPointDimensionReferencing, spectrum, dim, value)

    @staticmethod
    def _setPointDimensionReferencing(spectrum, dim, value):
        spectrumReferencing = list(spectrum.referencePoints)
        spectrumReferencing[dim] = float(value)
        spectrum.referencePoints = spectrumReferencing

    @queueStateChange(_verifyPopupApply)
    def _queueSetMinAliasing(self, spectrum, valueGetter, dim, _value):
        _index = self.minAliasingPullDowns[dim].getSelectedIndex()
        minValue = min(self.foldLim[dim]) - _index * self.deltaLim[dim]
        if abs(minValue - min(spectrum.aliasingLimits[dim])) > 1e-8:  # for rounding errors
            returnVal = partial(self._setMinAliasing, self.spectrum, dim, minValue)
            return returnVal

    @staticmethod
    def _setMinAliasing(spectrum, dim, value):
        alias = list(spectrum.aliasingLimits)
        value = float(value)
        alias[dim] = (value, max(alias[dim][1], value))
        spectrum.aliasingLimits = tuple(alias)

    @queueStateChange(_verifyPopupApply)
    def _queueSetMaxAliasing(self, spectrum, valueGetter, dim, _value):
        _index = MAXALIASINGRANGE - self.maxAliasingPullDowns[dim].getSelectedIndex()
        maxValue = max(self.foldLim[dim]) + _index * self.deltaLim[dim]
        if abs(maxValue - max(spectrum.aliasingLimits[dim])) > 1e-8:  # for rounding errors
            returnVal = partial(self._setMaxAliasing, spectrum, dim, maxValue)
            return returnVal

    @staticmethod
    def _setMaxAliasing(spectrum, dim, value):
        alias = list(spectrum.aliasingLimits)
        value = float(value)
        alias[dim] = (min(alias[dim][0], value), value)
        spectrum.aliasingLimits = tuple(alias)

    @queueStateChange(_verifyPopupApply)
    def _queueSetFoldingModes(self, spectrum, valueGetter, dim, _value):
        dd = {False: 'mirror', True: 'circular', None: None}  # swapped because inverted checkbox
        value = dd[valueGetter()]
        if value != spectrum.foldingModes[dim]:
            return partial(self._setFoldingModes, spectrum, dim, value)

    @staticmethod
    def _setFoldingModes(spectrum, dim, value):
        folding = list(spectrum.foldingModes)
        folding[dim] = value
        spectrum.foldingModes = tuple(folding)

    # @queueStateChange(_verifyPopupApply)
    # def _queueSetInvertedModes(self, spectrum, valueGetter, dim, _value):
    #     # not implemented yet
    #     pass
    #
    # def _setInvertedModes(self, spectrum, dim, value):
    #     # not implemented yet
    #     pass

    @queueStateChange(_verifyPopupApply)
    def _queueSetDisplayFoldedContours(self, spectrum, valueGetter, _value):
        value = valueGetter()
        if value != spectrum.displayFoldedContours:
            return partial(self._setDisplayFoldedContours, spectrum, value)

    @staticmethod
    def _setDisplayFoldedContours(spectrum, value):
        spectrum.displayFoldedContours = bool(value)


#=========================================================================================
# ContoursTab
#=========================================================================================

class ContourBaseSpinBox(VariableScientificSpinBox):
    """Class to have a spinbox that gives exp notation for values >1000
    """
    _FORMATDECIMALS = 3
    _PREC = 1

    def formatFloat(self, value):
        """Modified form of the 'g' format specifier.
        """
        val = float(value)
        mag = fexp(abs(val))

        if mag >= self._FORMATDECIMALS:
            string = self._qLocale.toString(val, 'e', self._PREC)

        elif mag >= 0:
            string = self._qLocale.toString(val, 'g', self._PREC)

        else:
            string = self._qLocale.toString(val, 'g', self._PREC)

        # NOTE:ED - 'g' format handles this with correct locale
        # clean leading zeroes from the exponent
        return re.sub("e(-|\+?)0*(\d+)", r"e\1\2", string.replace("e+", "e"))

    # check for an exponent, removing leading/trailing zeroes
    # reg = r'^((?:\+?)|(\-?))(?:0*)(\d+)((((\.\d*[1-9])(?:0*)|(?:\.0+)|)((e)((?:\+?)|(\-?))((?:0*)([1-9]\d*)|(0)(?:0*))(?:$)|(?:$))|(?:$)))'
    # _string = re.sub(reg, r'\2\3\7\9\11\13\14', string)


# GWV: new "ContourTabRow" class
class ContourTabRow(object):
    """Class to hold info on a row
    """

    def __init__(self, contoursTab, rowIdx, text, attrName, bold=False, widget=None, **kwds):
        self.contoursTab = contoursTab  # The parent
        self.rowIdx = rowIdx
        self.text = text
        self.attrName = attrName

        col = contoursTab._labelCol
        tipText = getAttributeTipText(Spectrum, attrName)
        self.labelWidget = Label(parent=contoursTab, text=text, grid=(rowIdx, col), bold=bold,
                                 tipText=tipText, vAlign='c', hAlign='r', minimumHeight=25)

        kwds.update(_align2)
        self.widget = widget(parent=contoursTab, grid=(rowIdx, col + 1), **kwds)

        checked = contoursTab._copyCheckboxSettings.get(attrName, True)
        self.checkboxWidget = CheckBox(parent=contoursTab, checkable=True, checked=checked,
                                       grid=(rowIdx, contoursTab._checkBoxCol), hAlign='c')
        contoursTab._addToCopyWidgetSet(self.checkboxWidget)

        # retain the initial value
        self.initialValue = self.getValue()

    @property
    def spectrum(self) -> Spectrum:
        """:return The spectrum instance
        """
        return self.contoursTab.spectrum

    def get(self):
        """Get and return value from widget;
        allows for subclassing
        """
        return self.widget.get()

    def set(self, value):
        """Set value in widget;
        allows for subclassing
        """
        self.widget.set(value)

    def copyTo(self, targetRow, overRide=False):
        """Copy the value in widget from self to target row;
        Uses get() and set() methods
        :raise RuntimeError if attrName's do not match unless overRide is set
        """
        if self.attrName != targetRow.attrName and not overRide:
            raise RuntimeError(f'Cannot copy from {self} to {targetRow}')
        value = self.get()
        targetRow.set(value)

    def getValue(self):
        """Get the value from the spectrum; set in the widget
        :return value
        """
        value = getattr(self.spectrum, self.attrName)
        self.set(value)
        return value

    def setValue(self):
        """Get the value from the widget and set in the spectrum;
        """
        value = self.get()
        setattr(self.spectrum, self.attrName, value)

    def setCallback(self, callback):
        """Set the callback of widget
        """
        self.widget.setCallback(callback)

    def __str__(self):
        return f'<{self.__class__.__name__}: rowIdx {self.rowIdx} "{self.attrName}">'


class ContourTabColourRow(ContourTabRow):
    """Class to hold info on a colour setting row
    """

    def getValue(self):
        """Get the value from the spectrum; set the widget
        :return value
        """
        spectrum = self.contoursTab.spectrum
        value = getattr(spectrum, self.attrName)
        _setColourPulldown(self.widget, value)
        return value

    def copyTo(self, targetRow):
        """Copy the value from self to target row
        """
        name = self.widget.currentText()
        colour = getSpectrumColour(name, defaultReturn='#')
        _setColourPulldown(targetRow.widget, colour)


class ContourTabNegativeBaseRow(ContourTabRow):
    """Class to hold info on negativeBase setting row
    """

    def set(self, value):
        """Set value in widget;
        Assure negative value
        """
        self.widget.set(-abs(value))


class ContoursTab(Widget):

    def __init__(self, parent=None, container=None, mainWindow=None, spectrum=None, showCopyOptions=False,
                 copyToSpectra=None):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self._container = container  # master widget that this is attached to
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.preferences = self.application.preferences

        # check that the spectrum and the copyToSpectra list are correctly defined
        self._updateSpectra(spectrum, copyToSpectra)

        # store the options for which spectra to copy to when clicking the copy button (if active)
        self._showCopyOptions = showCopyOptions
        # self._showCopyOptions = True # For debugging
        self._copyWidgetSet = set()
        self._copyCheckboxSettings = self._getCopyCheckboxSettingsDict()

        self._changes = ChangeDict()

        row = -1
        col = 0
        self._labelCol = 0
        self._widgetCol = 1
        self._checkBoxCol = 3
        self._rows = []

        # Start populating the rows
        row += 1
        self._topRow = row  # For other older code
        copyLabel = Label(self, text="Copy", grid=(row, self._checkBoxCol), bold=True, **_align1)
        self._addToCopyWidgetSet(copyLabel)

        row += 1
        _row = ContourTabRow(self, row, text="Positive Contours", bold=True, attrName='includePositiveContours',
                             widget=CheckBox
                             )
        _row.setCallback(partial(self._queueChangeRow, _row))
        # retain old name (for now)
        self.positiveContoursCheckBox = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabRow(self, row, text="Base Level", attrName='positiveContourBase',
                             widget=ContourBaseSpinBox, min=0.1, max=1e12
                             )
        _row.setCallback(partial(self._queueChangePositiveContourBase, _row))

        # retain old name (for now)
        self.positiveContourBaseData = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabRow(self, row, text="Multiplier", attrName='positiveContourFactor',
                             widget=ScientificDoubleSpinBox, min=0.0, decimals=2, step=0.1
                             )
        _row.setCallback(
                partial(self._queueChangePositiveContourFactor, _row))
        # retain old name (for now)
        self.positiveMultiplierData = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabRow(self, row, text="Number of contours", attrName='positiveContourCount',
                             widget=Spinbox, min=1, max=32, step=1
                             )
        _row.setCallback(partial(self._queueChangePositiveContourCount, _row))
        # retain old name (for now)
        self.positiveContourCountData = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabColourRow(self, row, text="Colour", attrName='positiveContourColour',
                                   widget=PulldownList
                                   )
        # Can't use setCallback() as the PulldownList does something complicated
        # _row.setCallback(partial(self._queueChangePosColourComboIndex, spectrum))
        _row.widget.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, spectrum))
        # retain the row-widget as it is used elsewhere in the code
        self.positiveColourBox = _row.widget

        # colour selection button
        _button = Button(self, grid=(row, col + 2), vAlign='t', hAlign='l', icon='icons/colours', hPolicy='fixed')
        _button.setCallback(partial(self._queueChangePosSpectrumColour, spectrum))
        self._rows.append(_row)

        #======= HLine ======
        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15, divisor=2)

        # Negative contours
        row += 1
        _row = ContourTabRow(self, row, text="Negative Contours", bold=True, attrName='includeNegativeContours',
                             widget=CheckBox
                             )
        _row.setCallback(partial(self._queueChangeRow, _row))
        # retain old name (for now)
        self.negativeContoursCheckBox = _row.widget
        self._rows.append(_row)

        row += 1
        Label(self, text='Mirror Positive Settings', grid=(row, col), **_alignLabel)
        self.linkContoursCheckBox = CheckBox(self,
                                             grid=(row, col + 1), checked=True,
                                             tipText='Use identical base, multiplier and number settings for positive and negative contours',
                                             callback=self._linkContoursCheckBoxCallback,
                                             **_align2)

        row += 1
        _row = ContourTabNegativeBaseRow(self, row, text="Base Level", attrName='negativeContourBase',
                                         widget=ContourBaseSpinBox, min=-1e12,
                                                               max=-0.1,
                                         )
        _row.setCallback(
                partial(self._queueChangeRow, _row))
        # retain old name (for now)
        self.negativeContourBaseData = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabRow(self, row, text="Multiplier", attrName='negativeContourFactor',
                             widget=ScientificDoubleSpinBox, min=0.0,
                                                              decimals=2, step=0.1
                             )
        _row.setCallback(
                partial(self._queueChangeRow, _row))
        # retain old name (for now)
        self.negativeMultiplierData = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabRow(self, row, text="Number of contours", attrName='negativeContourCount',
                             widget=Spinbox, min=1, max=32, step=1
                             )
        _row.setCallback(partial(self._queueChangeRow, _row))
        # retain old name (for now)
        self.negativeContourCountData = _row.widget
        self._rows.append(_row)

        row += 1
        _row = ContourTabColourRow(self, row, text="Colour", attrName='negativeContourColour',
                                   widget=PulldownList
                                   )
        # retain old name (for now)
        self.negativeColourBox = _row.widget
        # Can't use the setCallback method as the pulldown does something complicated
        self.negativeColourBox.currentIndexChanged.connect(partial(self._queueChangeNegColourComboIndex, spectrum))
        # colour button
        _button = Button(self, grid=(row, col + 2), icon='icons/colours', hPolicy='fixed', vAlign='t', hAlign='l')
        _button.setCallback(partial(self._queueChangeNegSpectrumColour, spectrum))
        self._rows.append(_row)

        # we are done now; for conveniance, also create a dict of (attrName, row) key value pairs for easy lookup
        self._rowsDict = dict([(r.attrName, r) for r in self._rows])

        # Update some settings
        self._linkContoursCheckBoxCallback()
        # self._fillPullDowns(); can't do as _postInit has not been called

        # ==== Copy selection box and copy button
        row += 1
        _hline = HLine(self, grid=(row, 0), gridSpan=(1, 4), colour=getColours()[DIVIDER], height=15, divisor=2,
                       hPolicy='expanding')
        self._addToCopyWidgetSet(_hline)

        row += 1
        if self._copyToSpectra:
            texts = [SELECTND] + [spectrum.pid for spectrum in self._copyToSpectra if spectrum != self.spectrum]
        else:
            texts = []
        self._copyToSpectraPullDown = PulldownListCompoundWidget(self, labelText='Copy to', texts=texts,
                                                                 grid=(row, 0), gridSpan=(1, 2), **_align2)
        self._addToCopyWidgetSet(self._copyToSpectraPullDown)

        self._copyButton = Button(self, text='Copy', grid=(row, 2), gridSpan=(1, 2), **_align2, minimumWidth=100,
                                  callback=self._copyActionClicked)
        self._addToCopyWidgetSet(self._copyButton)

        # ==== Spacer
        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row + 3, col + 1), gridSpan=(1, 1))

    def _getCopyCheckboxSettingsDict(self) -> dict:
        """Create a dict with copy-checkbox settings from the preferences
        """
        # the copy Check boxes setting are stored as a list; GWV: should really be stored as a dict and not in preferences
        # but in the state directory
        # define the copy checkboxes attributes
        _copyAttrs = """
            linkContours
            includePositiveContours
            positiveContourBase
            positiveContourFactor
            positiveContourCount
            positiveContourColour
            includeNegativeContours
            negativeContourBase
            negativeContourFactor
            negativeContourCount
            negativeContourColour
        """.split()
        # get the list of settings; assure sufficient length
        _tmp = self.preferences.general._copySpectraSettingsNd if self.preferences.general._copySpectraSettingsNd else [
                                                                                                                           True] * len(
            _copyAttrs)
        if len(_tmp) < len(_copyAttrs):
            _tmp += [True] * (len(_copyAttrs) - len(_tmp))

        # create a dict of the settings for lookup by attribute name
        return dict(zip(_copyAttrs, _tmp))

    def _updateSpectra(self, spectrum, copyToSpectra):
        # check that the spectrum and the copyToSpectra list are correctly defined
        getByPid = self.application.project.getByPid
        self.spectrum = getByPid(spectrum) if isinstance(spectrum, str) else spectrum
        if not _overrideClassCheck and not isinstance(self.spectrum, (Spectrum, type(None))):
            raise TypeError('spectrum must be of type Spectrum or None')

        if not isinstance(copyToSpectra, (Iterable, type(None))):
            raise TypeError('copyToSpectra must be of type Iterable/None')
        if copyToSpectra:
            self._copyToSpectra = []
            for spec in copyToSpectra:
                if isinstance(spec, str):
                    spec = getByPid(spec)
                if not isinstance(spec, (Spectrum, type(None))):
                    raise TypeError('copyToSpectra is not defined correctly')
                self._copyToSpectra.append(spec)
        else:
            self._copyToSpectra = None

    def _addToCopyWidgetSet(self, widget):
        """Add widgets to a set so that we can set visible/invisible at any time
        """
        if not self._copyWidgetSet:
            self._copyWidgetSet = set()
        self._copyWidgetSet.add(widget)
        widget.setVisible(self._showCopyOptions)

    def setCopyOptionsVisible(self, value):
        """Show/hide the copyOptions widgets
        """
        if not isinstance(value, bool):
            raise TypeError('Error: value must be a boolean')

        self._showCopyOptions = value
        for widg in self._copyWidgetSet:
            widg.setVisible(value)

    # GWV 13/07/2023: Not used? (should not be here anyway)
    # def _setContourLevels(self):
    #     """Estimate the contour levels for the current spectrum
    #     """
    #     posBase, negBase, posMult, negMult, posLevels, negLevels = getContourLevelsFromNoise(self.spectrum,
    #                                                                                          setPositiveContours=self.setPositiveContours.isChecked(),
    #                                                                                          setNegativeContours=self.setNegativeContours.isChecked(),
    #                                                                                          useSameMultiplier=self.setUseSameMultiplier.isChecked(),
    #                                                                                          useDefaultLevels=self.setDefaults.isChecked(),
    #                                                                                          useDefaultMultiplier=self.setDefaults.isChecked())
    #
    #     # put the new values into the widgets (will queue changes)
    #     if posBase:
    #         self.positiveContourBaseData.setValue(posBase)
    #     if negBase:
    #         self.negativeContourBaseData.setValue(negBase)
    #     if posMult:
    #         self.positiveMultiplierData.setValue(posMult)
    #     if negMult:
    #         self.negativeMultiplierData.setValue(negMult)
    #     if posLevels:
    #         self.positiveContourCountData.setValue(posLevels)
    #     if negLevels:
    #         self.negativeContourCountData.setValue(negLevels)

    def _fillPullDowns(self):
        """CCPNMR_INTERNAL: also used in SpectrumGroupEditor
        """
        fillColourPulldown(self.positiveColourBox, allowAuto=False, includeGradients=True)
        fillColourPulldown(self.negativeColourBox, allowAuto=False, includeGradients=True)

    def _populateColour(self):
        """Populate colour tab from self.spectrum
        Blocking to be performed by tab container
        """
        # clear all changes
        self._cleanWidgetQueue()

        with self._changes.blockChanges():
            for row in self._rows:
                row.getValue()

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._container._getChangeState()

    def _cleanWidgetQueue(self):
        """Clean the items from the stateChange queue
        """
        self._changes.clear()

    @queueStateChange(_verifyPopupApply)
    def _queueChangeRow(self, row, value):
        """Push a change of the row value to the queue
        :param row: a ContourTabRow instance
        """
        # row.set(value)
        if value != row.initialValue:
            return row.setValue

    # @queueStateChange(_verifyPopupApply)
    # def _queueChangePositiveContourDisplay(self, spectrum, state):
    #     if (state == QtCore.Qt.Checked) != spectrum.includePositiveContours:
    #         return partial(self._changePositiveContourDisplay, spectrum, state)
    #
    # def _changePositiveContourDisplay(self, spectrum, state):
    #     if state == QtCore.Qt.Checked:
    #         spectrum.includePositiveContours = True
    #         for spectrumView in spectrum.spectrumViews:
    #             spectrumView.displayPositiveContours = True
    #     else:
    #         self.spectrum.includePositiveContours = False
    #         for spectrumView in spectrum.spectrumViews:
    #             spectrumView.displayPositiveContours = False
    #
    # @queueStateChange(_verifyPopupApply)
    # def _queueChangeNegativeContourDisplay(self, spectrum, state):
    #     if (state == QtCore.Qt.Checked) != spectrum.includeNegativeContours:
    #         return partial(self._changeNegativeContourDisplay, spectrum, state)
    #
    # def _changeNegativeContourDisplay(self, spectrum, state):
    #     if state == QtCore.Qt.Checked:
    #         spectrum.includeNegativeContours = True
    #         for spectrumView in spectrum.spectrumViews:
    #             spectrumView.displayNegativeContours = True
    #     else:
    #         spectrum.includeNegativeContours = False
    #         for spectrumView in spectrum.spectrumViews:
    #             spectrumView.displayNegativeContours = False

    @queueStateChange(_verifyPopupApply)
    def _queueChangePositiveContourBase(self, row, value):
        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            negRow = self._getRow('negativeContourBase')
            negRow.set(-value)
        return self._queueChangeRow(row, value)

    # @queueStateChange(_verifyPopupApply)
    # def _queueChangePositiveContourBase(self, spectrum, textFromValue, value):
    #     specValue = textFromValue(spectrum.positiveContourBase)
    #     if value >= 0 and textFromValue(value) != specValue:
    #         returnVal = partial(self._changePositiveContourBase, spectrum, value)
    #     else:
    #         returnVal = None
    #
    #     # check linked attribute
    #     if self.linkContoursCheckBox.isChecked():
    #         self.negativeContourBaseData.set(-value)
    #     return returnVal
    #
    # def _changePositiveContourBase(self, spectrum, value):
    #     spectrum.positiveContourBase = float(value)

    @queueStateChange(_verifyPopupApply)
    def _queueChangePositiveContourFactor(self, row, value):
        if self.linkContoursCheckBox.isChecked():
            negRow = self._getRow('negativeContourFactor')
            negRow.set(value)
        return self._queueChangeRow(row, value)

    # @queueStateChange(_verifyPopupApply)
    # def _queueChangePositiveContourFactor(self, spectrum, textFromValue, value):
    #     specValue = textFromValue(spectrum.positiveContourFactor)
    #     if value >= 0 and textFromValue(value) != specValue:
    #         returnVal = partial(self._changePositiveContourFactor, spectrum, value)
    #     else:
    #         returnVal = None
    #
    #     # check linked attribute
    #     if self.linkContoursCheckBox.isChecked():
    #         self.negativeMultiplierData.set(value)
    #     return returnVal
    #
    # def _changePositiveContourFactor(self, spectrum, value):
    #     spectrum.positiveContourFactor = float(value)

    @queueStateChange(_verifyPopupApply)
    def _queueChangePositiveContourCount(self, row, value):
        if self.linkContoursCheckBox.isChecked():
            negRow = self._getRow('negativeContourCount')
            negRow.set(value)
        return self._queueChangeRow(row, value)

    # @queueStateChange(_verifyPopupApply)
    # def _queueChangePositiveContourCount(self, spectrum, value):
    #     if value > 0 and value != spectrum.positiveContourCount:
    #         returnVal = partial(self._changePositiveContourCount, spectrum, value)
    #     else:
    #         returnVal = None
    #
    #     # check linked attribute
    #     if self.linkContoursCheckBox.isChecked():
    #         self.negativeContourCountData.set(value)
    #     return returnVal
    #
    # def _changePositiveContourCount(self, spectrum, value):
    #     spectrum.positiveContourCount = int(value)

    # @queueStateChange(_verifyPopupApply)
    # def _queueChangeNegativeContourBase(self, spectrum, textFromValue, value):
    #     specValue = textFromValue(spectrum.negativeContourBase)
    #     if value <= 0 and textFromValue(value) != specValue:
    #         returnVal = partial(self._changeNegativeContourBase, spectrum, value)
    #     else:
    #         returnVal = None
    #
    #     # check linked attribute
    #     if self.linkContoursCheckBox.isChecked():
    #         self.positiveContourBaseData.set(-value)
    #     return returnVal
    #
    # def _changeNegativeContourBase(self, spectrum, value):
    #     # force to be negative
    #     value = -abs(value)
    #     spectrum.negativeContourBase = float(value)
    #
    # @queueStateChange(_verifyPopupApply)
    # def _queueChangeNegativeContourFactor(self, spectrum, textFromValue, value):
    #     specValue = textFromValue(spectrum.negativeContourFactor)
    #     if value >= 0 and textFromValue(value) != specValue:
    #         returnVal = partial(self._changeNegativeContourFactor, spectrum, value)
    #     else:
    #         returnVal = None
    #
    #     # check linked attribute
    #     if self.linkContoursCheckBox.isChecked():
    #         self.positiveMultiplierData.set(value)
    #     return returnVal
    #
    # def _changeNegativeContourFactor(self, spectrum, value):
    #     spectrum.negativeContourFactor = float(value)
    #
    # @queueStateChange(_verifyPopupApply)
    # def _queueChangeNegativeContourCount(self, spectrum, value):
    #     if value > 0 and value != spectrum.negativeContourCount:
    #         returnVal = partial(self._changeNegativeContourCount, spectrum, value)
    #     else:
    #         returnVal = None
    #
    #     # check linked attribute
    #     if self.linkContoursCheckBox.isChecked():
    #         self.positiveContourCountData.set(value)
    #     return returnVal
    #
    # def _changeNegativeContourCount(self, spectrum, value):
    #     spectrum.negativeContourCount = int(value)

    # spectrum positiveContourColour button and pulldown
    def _queueChangePosSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._container._fillPullDowns()
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
            self._container._fillPullDowns()
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

    def _getRow(self, attrName):
        """
        Get a row defined by attrName; raise RuntimeError if not found
        :param attrName:
        :return: ContourTabRow instance
        """
        if (row := self._rowsDict.get(attrName)) is None:
            raise RuntimeError(f'No row defined for "{attrName}"')
        return row

    def _linkContoursCheckBoxCallback(self):
        """Callback when pressing the link contours checkbox
        when checked:
        - copy positive contour settings (Base, Factor, Count) to negative contour settings
        - disable all negative contour boxes
        """
        checked = self.linkContoursCheckBox.get()
        for attrName1, attrName2 in ["negativeContourBase positiveContourBase".split(),
                                     "negativeContourFactor positiveContourFactor".split(),
                                     "negativeContourCount positiveContourCount".split()
                                     ]:
            negRow = self._getRow(attrName1)
            posRow = self._getRow(attrName2)
            if checked:
                posRow.copyTo(negRow, overRide=True)
            negRow.widget.setEnabled(not checked)

    # methods for copying the spectrum attributes to the others in the pulldown
    # should be contained within the undo/revert mechanism

    # def _copyLinkContours(self, fromSpectrumTab):
    #     state = fromSpectrumTab.linkContoursCheckBox.get()
    #     self.linkContoursCheckBox.set(state)

    # def _copyShowPositive(self, fromSpectrumTab):
    #     state = fromSpectrumTab.positiveContoursCheckBox.get()
    #     self.positiveContoursCheckBox.set(state)
    #
    # def _copyPositiveBaseLevel(self, fromSpectrumTab):
    #     value = fromSpectrumTab.positiveContourBaseData.get()
    #     self.positiveContourBaseData.set(value)
    #
    # def _copyPositiveMultiplier(self, fromSpectrumTab):
    #     value = fromSpectrumTab.positiveMultiplierData.get()
    #     self.positiveMultiplierData.set(value)
    #
    # def _copyPositiveContours(self, fromSpectrumTab):
    #     value = fromSpectrumTab.positiveContourCountData.get()
    #     self.positiveContourCountData.set(value)
    #
    # def _copyPositiveContourColour(self, fromSpectrumTab):
    #     name = fromSpectrumTab.positiveColourBox.currentText()
    #     colour = getSpectrumColour(name, defaultReturn='#')
    #     _setColourPulldown(self.positiveColourBox, colour)
    #
    # def _copyShowNegative(self, fromSpectrumTab):
    #     state = fromSpectrumTab.negativeContoursCheckBox.get()
    #     self.negativeContoursCheckBox.set(state)
    #
    # def _copyNegativeBaseLevel(self, fromSpectrumTab):
    #     value = fromSpectrumTab.negativeContourBaseData.get()
    #     self.negativeContourBaseData.set(value)
    #
    # def _copyNegativeMultiplier(self, fromSpectrumTab):
    #     value = fromSpectrumTab.negativeMultiplierData.get()
    #     self.negativeMultiplierData.set(value)
    #
    # def _copyNegativeContours(self, fromSpectrumTab):
    #     value = fromSpectrumTab.negativeContourCountData.get()
    #     self.negativeContourCountData.set(value)
    #
    # def _copyNegativeContourColour(self, fromSpectrumTab):
    #     name = fromSpectrumTab.negativeColourBox.currentText()
    #     colour = getSpectrumColour(name, defaultReturn='#')
    #     _setColourPulldown(self.negativeColourBox, colour)

    # def _copyButtonClicked(self, checkBox, checkBoxIndex, state):
    #     """Set the state of the checkBox in preferences
    #     """
    #     checkBoxList = self.preferences.general._copySpectraSettingsNd
    #     if checkBoxList and checkBoxIndex < len(checkBoxList):
    #         checkBoxList[checkBoxIndex] = state

    def _copyActionClicked(self):
        """Copy action clicked - call the copy method from the parent Tab widget
        """
        toSpectraPids = self._copyToSpectraPullDown.getText()
        if toSpectraPids == SELECTND:
            toSpectra = [spectrum for spectrum in self._copyToSpectra if spectrum != self.spectrum]
        else:
            toSpectra = [self.application.project.getByPid(toSpectraPids)]

        # GWV: replaced with code below
        # # call the parent tab copy action
        # self._container.copySpectra(self.spectrum, toSpectra)

        # Find the tabs of toSpectra
        _dict = dict([(t.spectrum.pid, t) for t in self._container.tabs])
        toTabs = [_dict.get(spec.pid, None) for spec in toSpectra]
        if None in toTabs:
            raise RuntimeError(f'Error copying settings; no ContourTab found for one of {toSpectraPids}')

        for tab in toTabs:
            self._copyValuesTo(tab)

    def _copyValuesTo(self, target):
        """Copy the values from self to target, accounting for the copy checkboxes of self
        """
        for attrName, row in self._rowsDict.items():
            if row.checkboxWidget.get():
                if (targetRow := target._rowsDict.get(attrName, None)) is None:
                    raise RuntimeError(f'Copying setting from {self} to {target}: "{attrName}" not found in the latter')
                row.copyTo(targetRow)

    # def _copySpectrumAttributes(self, fromSpectrumTab):
    #     """Copy the attributes to the other spectra
    #     """
    #     if self._showCopyOptions:
    #         checkBoxList = self.preferences.general._copySpectraSettingsNd
    #         if checkBoxList and len(checkBoxList) == len(self._copyList):
    #             for cc, copyFunc in enumerate(self._copyList):
    #                 # call the copy function if checked
    #                 if checkBoxList[cc] and self.spectrum and fromSpectrumTab.spectrum:
    #                     copyFunc(fromSpectrumTab)

    # GWV moved up to be next to other relevant routine
    # def setCopyOptionsVisible(self, value):
    #     """Show/hide the copyOptions widgets
    #     """
    #     if not isinstance(value, bool):
    #         raise TypeError('Error: value must be a boolean')
    #
    #     self._showCopyOptions = value
    #     for widg in self._copyWidgetSet:
    #         widg.setVisible(value)


#=========================================================================================
# ColourTab
#=========================================================================================

class ColourTab(Widget):
    def __init__(self, parent=None, container=None, mainWindow=None, spectrum=None, item=None, colourOnly=False,
                 showCopyOptions=False, copyToSpectra=None):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self._container = container  # master widget that this is attached to
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
            self._copyToSpectra = [getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in
                                   copyToSpectra]
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
        copyLabel = Label(self, text="Copy Selected\nAttribute", grid=(self._topRow - 1, self._checkBoxCol), vAlign='t',
                          hAlign='l')
        self._addToCopyWidgetSet(copyLabel)

        Label(self, text="Colour", vAlign='t', hAlign='l', grid=(7, 0),
              tipText=getAttributeTipText(Spectrum, 'sliceColour'))
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
        if self.preferences.general._copySpectraSettings1d and len(
                self.preferences.general._copySpectraSettings1d) == len(self._copyList):
            # read existing settings
            for rr, opt in enumerate(self._copyList):
                thisCheckBox = CheckBox(self, grid=(rr + self._topRow, self._checkBoxCol),
                                        checkable=True, checked=self.preferences.general._copySpectraSettings1d[rr],
                                        hAlign='c')
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
                                                                 gridSpan=(1, self._checkBoxCol + 1), vAlign='t',
                                                                 hAlign='r')
        self._copyButton = Button(self, text='Copy', grid=(len(self._copyList) + self._topRow + 1, self._checkBoxCol),
                                  hAlign='r',
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
            self._copyToSpectra = [getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in
                                   copyToSpectra]
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
        return self._container._getChangeState()

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
                    except Exception:
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
            self._container._fillPullDowns()
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
            self._container.copySpectra(self.spectrum, toSpectra)

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


#=========================================================================================
# ColourFrameABC
#=========================================================================================

class ColourFrameABC(Frame):
    POSITIVECOLOUR = False
    NEGATIVECOLOUR = False
    SLICECOLOUR = False
    EDITMODE = True

    spectrumGroup: SpectrumGroup | AttrDict

    def __init__(self, parent=None, mainWindow=None, container=None, editMode=False, spectrumGroup=None, item=None,
                 **kwds):

        super().__init__(parent, **kwds)

        self._parent = parent
        self._container = container  # master widget that this is attached to
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
            Label(self, text="Group Positive Contour Colour", vAlign='t', hAlign='l', grid=(row, 0),
                  tipText=getAttributeTipText(SpectrumGroup, 'positiveContourColour'))
            self.positiveColourBox = PulldownList(self, vAlign='t', grid=(row, 1))
            self.positiveColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                               icon='icons/colours', hPolicy='fixed')
            self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, self.spectrumGroup))
            row += 1

        if self.NEGATIVECOLOUR:
            Label(self, text="Group Negative Contour Colour", vAlign='t', hAlign='l', grid=(row, 0),
                  tipText=getAttributeTipText(SpectrumGroup, 'negativeContourColour'))
            self.negativeColourBox = PulldownList(self, vAlign='t', grid=(row, 1))
            self.negativeColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                               icon='icons/colours', hPolicy='fixed')
            self.negativeColourButton.clicked.connect(partial(self._queueChangeNegSpectrumColour, self.spectrumGroup))
            row += 1

        if self.SLICECOLOUR:
            Label(self, text="Group Slice Colour", vAlign='t', hAlign='l', grid=(row, 0),
                  tipText=getAttributeTipText(SpectrumGroup, 'sliceColour'))
            self.sliceColourBox = PulldownList(self, vAlign='t', grid=(row, 1))
            self.sliceColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                            icon='icons/colours', hPolicy='fixed')
            self.sliceColourButton.clicked.connect(partial(self._queueChangeSliceColour, self.spectrumGroup))
            self.copySliceColourButton = Button(self, text='Copy to All Spectra', grid=(row, 3), vAlign='t', hAlign='l',
                                                hPolicy='fixed')
            self.copySliceColourButton.clicked.connect(partial(self._queueChangeSliceColourToAll, self.spectrumGroup))
            row += 1

        self._fillPullDowns()

        if self.POSITIVECOLOUR:
            self.positiveColourBox.currentIndexChanged.connect(
                partial(self._queueChangePosColourComboIndex, self.spectrumGroup))
        if self.NEGATIVECOLOUR:
            self.negativeColourBox.currentIndexChanged.connect(
                partial(self._queueChangeNegColourComboIndex, self.spectrumGroup))
        if self.SLICECOLOUR:
            self.sliceColourBox.currentIndexChanged.connect(
                partial(self._queueChangeSliceComboIndex, self.spectrumGroup))

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
                _setColourPulldown(self.positiveColourBox, self.spectrumGroup.positiveContourColour, allowAuto=False,
                                   includeGradients=True, allowNone=True)
            if self.NEGATIVECOLOUR:
                _setColourPulldown(self.negativeColourBox, self.spectrumGroup.negativeContourColour, allowAuto=False,
                                   includeGradients=True, allowNone=True)
            if self.SLICECOLOUR:
                _setColourPulldown(self.sliceColourBox, self.spectrumGroup.sliceColour, allowAuto=False,
                                   includeGradients=True, allowNone=True)

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

    def _queueChangeSliceColourToAll(self, spectrumGroup):
        for spectrum in spectrumGroup.spectra:
            self._changedSliceComboIndex(spectrum, value='')

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


#=========================================================================================
# Colour1dFrame
#=========================================================================================

class Colour1dFrame(ColourFrameABC):
    POSITIVECOLOUR = False
    NEGATIVECOLOUR = False
    SLICECOLOUR = True


#=========================================================================================
# ColourNdFrame
#=========================================================================================

class ColourNdFrame(ColourFrameABC):
    POSITIVECOLOUR = True
    NEGATIVECOLOUR = True
    SLICECOLOUR = False
