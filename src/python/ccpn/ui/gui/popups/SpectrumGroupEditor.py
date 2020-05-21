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
__dateModified__ = "$dateModified: 2020-05-21 14:00:18 +0100 (Thu, May 21, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5 import QtWidgets, QtGui, QtCore
from ast import literal_eval
from typing import Tuple, Any
from collections import OrderedDict, Iterable
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.popups.Dialog import handleDialogApply, _verifyPopupApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.core.lib.ContextManagers import queueStateChange
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup, SeriesTypes
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumGroupPulldown
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.TextEditor import PlainTextEditor
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import ColourTab, ContoursTab
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Constants import ALL_UNITS, ERRORSTRING

DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 1, 5)  # l, t, r, b
INVALIDROWCOLOUR = QtGui.QColor('lightpink')
SPECTRATABNUM = 0
GENERAL1DTABNUM = 1
GENERALNDTABNUM = 2
SERIESTABNUM = 3
NUMTABS = 4
SPECTRA_LABEL = 'Spectra'
GENERALTAB1D_LABEL = 'General 1d'
GENERALTABND_LABEL = 'General Nd'
SERIES_LABEL = 'Series'


class SpectrumGroupEditor(_GroupEditorPopupABC):
    """
    A popup to create and manage SpectrumGroups

    Used in 'New' or 'Edit' mode:
    - For creating new SpectrumGroup (editMode==False); optionally uses passed in spectra list
      i.e. NewSpectrumGroup of SideBar and Context menu of SideBar

    - For editing existing SpectrumGroup (editMode==True); requires spectrumGroup argument
      i.e. Edit of SpectrumGroup of SideBar
    or
      For selecting and editing SpectrumGroup (editMode==True)
      i.e. Menu Spectrum->Edit SpectrumGroup...

    """
    KLASS = SpectrumGroup
    KLASS_ITEM_ATTRIBUTE = 'spectra'  # Attribute in KLASS containing items
    KLASS_PULLDOWN = SpectrumGroupPulldown

    PROJECT_NEW_METHOD = 'newSpectrumGroup'  # Method of Project to create new KLASS instance
    PROJECT_ITEM_ATTRIBUTE = 'spectra'  # Attribute of Project containing items
    PLURAL_GROUPED_NAME = 'Spectrum Groups'
    SINGULAR_GROUP_NAME = 'Spectrum Group'

    GROUP_PID_KEY = 'SG'
    ITEM_PID_KEY = 'SP'

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

        _colourTabs1d = [self._colourTabs1d.widget(tt) for tt in range(self._colourTabs1d.count())]
        _colourTabsNd = [self._colourTabsNd.widget(tt) for tt in range(self._colourTabsNd.count())]
        if not (_colourTabs1d or _colourTabsNd):
            raise RuntimeError("Code error: tabs not implemented")

        _allTabs = self.getActiveTabList()

        # get the list of widgets that have been changed - exit if all empty
        allChanges = any(t._changes for t in _allTabs if t is not None) or (True if self._currentEditorState() else False)
        if not allChanges:
            return True

        # handle clicking of the Apply/OK button
        with handleDialogApply(self) as error:

            # get the list of spectra that have changed - for refreshing the displays
            spectrumList = []
            for t in (_colourTabs1d + _colourTabsNd):
                if t is not None:
                    changes = t._changes
                    if changes:
                        spectrumList.append(t.spectrum)

            # add an undo item to redraw these spectra
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._updateGl, spectrumList))

            # call the _groupEditor _applyChanges method which sets the group items
            if not super()._applyChanges():
                error.errorValue = True

            # add a redo item to redraw these spectra
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._updateGl, spectrumList))

            # rebuild the contours as required
            for spec in spectrumList:
                for specViews in spec.spectrumViews:
                    specViews.buildContours = True
            self._updateGl(spectrumList)

        # everything has happened - disable the apply button
        self._applyButton.setEnabled(False)

        # check for any errors
        if error.errorValue:
            # repopulate popup on an error
            self._populate()
            return False

        # remove all changes
        for tab in (_colourTabs1d + _colourTabsNd):
            tab._changes = {}

        # self._currentNumApplies += 1
        # self._revertButton.setEnabled(True)
        return True

    def _groupInit(self):
        # apply the changes to the listed spectra spectraTab._changes
        if self.spectraTab._changes:
            self._applyAllChanges(self.spectraTab._changes)

        for tt in range(self._colourTabs1d.count()):
            _changes = self._colourTabs1d.widget(tt)._changes
            if _changes:
                self._applyAllChanges(_changes)

        for tt in range(self._colourTabsNd.count()):
            _changes = self._colourTabsNd.widget(tt)._changes
            if _changes:
                self._applyAllChanges(_changes)

        self._spectrumGroupSeriesEdited = OrderedDict()
        self._spectrumGroupSeriesValues = list(self.obj.series)
        self._spectrumGroupSeriesUnitsEdited = None
        self._spectrumGroupSeriesTypeEdited = None

        # set the series values - this may crash
        if self.seriesTab._changes:
            self._applyAllChanges(self.seriesTab._changes)

        if self._spectrumGroupSeriesUnitsEdited is not None:
            self.obj.seriesUnits = self._spectrumGroupSeriesUnitsEdited

        if self._spectrumGroupSeriesTypeEdited is not None:
            self.obj.seriesType = self._spectrumGroupSeriesTypeEdited

        specList = self._currentEditorState()[self.obj.id]
        for dim, specPid in enumerate(specList):
            spec = self.project.getByPid(specPid)

            # read the value from the edits dict - bit of a hack from _changeSpectrumSeriesValues
            if spec and dim in self._spectrumGroupSeriesEdited:
                self._spectrumGroupSeriesValues[dim] = self._spectrumGroupSeriesEdited[dim]
        if self._spectrumGroupSeriesEdited:
            try:

                for ii, val in enumerate(self._spectrumGroupSeriesValues):
                    try:
                        tp = self.seriesTab.seriesType.getIndex()
                        if tp == SeriesTypes.FLOAT.value:
                            val = float(val)
                        elif tp == SeriesTypes.INTEGER.value:
                            val = int(val)
                        elif tp == SeriesTypes.STRING.value:
                            val = str(val)
                        else:
                            val = repr(val)
                    except Exception as es:
                        break
                    else:
                        self._spectrumGroupSeriesValues[ii] = val
                else:
                    self.obj.series = tuple(self._spectrumGroupSeriesValues)

            except Exception as es:
                raise es

    GROUPEDITOR_INIT_METHOD = _groupInit

    # make this a tabbed dialog, with the default widget going into tab 0
    USE_TAB = 0
    NUMBER_TABS = 4  # create the first tab

    def __init__(self, parent=None, mainWindow=None, editMode=True, obj=None, defaultItems=None, **kwds):
        """
        Initialise the widget, note defaultItems is only used for create
        """
        super().__init__(parent=parent, mainWindow=mainWindow, editMode=editMode, obj=obj, defaultItems=defaultItems, **kwds)

        self.TAB_NAMES = ((SPECTRA_LABEL, self._initSpectraTab),
                          (GENERALTAB1D_LABEL, self._initGeneralTab1d),
                          (GENERALTABND_LABEL, self._initGeneralTabNd),
                          (SERIES_LABEL, self._initSeriesTab))

        if obj and editMode:
            defaultItems = obj.spectra
        # replace the tab widget with a new seriesWidget
        seriesTabContents = SeriesFrame(parent=self, mainWindow=self.mainWindow, spectrumGroup=obj, editMode=editMode,
                                        showCopyOptions=True if defaultItems and len(defaultItems) > 1 else False,
                                        defaultItems=defaultItems or ())
        self._tabWidget.widget(SERIESTABNUM).setWidget(seriesTabContents)

        # get pointers to the tabs
        self.spectraTab = self._tabWidget.widget(SPECTRATABNUM)._scrollContents
        self.generalTab1d = self._tabWidget.widget(GENERAL1DTABNUM)._scrollContents
        self.generalTabNd = self._tabWidget.widget(GENERALNDTABNUM)._scrollContents
        self.seriesTab = self._tabWidget.widget(SERIESTABNUM)._scrollContents

        self._generalTabWidget1d = self._tabWidget.widget(GENERAL1DTABNUM)
        self._generalTabWidgetNd = self._tabWidget.widget(GENERALNDTABNUM)

        self.currentSpectra = self._getSpectraFromList()

        # this should be the list when the popup is opened
        self._defaultSpectra = self.currentSpectra
        self._defaultName = self._editedObject.name if self._editedObject else ''

        # set the labels in the first pass
        for tNum, (tabName, tabFunc) in enumerate(self.TAB_NAMES):
            self._tabWidget.setTabText(tNum, tabName)

        # call the tab initialise functions (may show/hide tabs)
        for tNum, (tabName, tabFunc) in enumerate(self.TAB_NAMES):
            if tabFunc:
                tabFunc()

        self._populate()
        self.setDefaultButton(None)
        self.setMinimumSize(600, 550)  # change to a calculation rather than a guess

        self.connectSignals()
        self.setSizeGripEnabled(False)

    def connectSignals(self):
        # connect to changes in the spectrumGroup
        self.nameEdit.textChanged.connect(self.seriesTab._queueChangeName)
        self.leftListWidget.model().dataChanged.connect(self._spectraChanged)
        self.leftListWidget.model().rowsRemoved.connect(self._spectraChanged)
        self.leftListWidget.model().rowsInserted.connect(self._spectraChanged)
        self.leftListWidget.model().rowsMoved.connect(self._spectraChanged)

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        # test the colour tabs for the moment
        tabs = tuple(self._colourTabs1d.widget(ii) for ii in range(self._colourTabs1d.count())) + \
               tuple(self._colourTabsNd.widget(ii) for ii in range(self._colourTabsNd.count())) + \
               (self.spectraTab, self.seriesTab)
        return tabs

    def _initSpectraTab(self):
        thisTab = self.spectraTab
        thisTab._changes = OrderedDict()

    def _initGeneralTab1d(self):
        thisTab = self.generalTab1d
        self._colourTabs1d = Tabs(thisTab, grid=(0, 0))

        # remember the state when switching tabs
        self.copyCheckBoxState = []

        spectra1d = [spec for spec in (self.currentSpectra or []) if spec.dimensionCount == 1]
        for specNum, thisSpec in enumerate(spectra1d):

            if thisSpec.dimensionCount == 1:
                contoursTab = ColourTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec,
                                        showCopyOptions=True if len(spectra1d) > 1 else False,
                                        copyToSpectra=spectra1d)

                self._colourTabs1d.addTab(contoursTab, thisSpec.name)
                contoursTab.setContentsMargins(*TABMARGINS)

        self._colourTabs1d.setTabClickCallback(self._tabClicked1d)
        self._colourTabs1d.tabCloseRequested.connect(self._closeColourTab1d)
        self._oldTabs = OrderedDict()

        index = self._tabWidget.indexOf(self._generalTabWidget1d)
        if self._colourTabs1d.count() == 0:
            if (0 <= index < NUMTABS):
                self._tabWidget.removeTab(index)

    def _initGeneralTabNd(self):
        thisTab = self.generalTabNd
        self._colourTabsNd = Tabs(thisTab, grid=(0, 0))

        # remember the state when switching tabs
        self.copyCheckBoxState = []

        spectraNd = [spec for spec in (self.currentSpectra or []) if spec.dimensionCount > 1]
        for specNum, thisSpec in enumerate(spectraNd):

            if thisSpec.dimensionCount > 1:
                contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec,
                                          showCopyOptions=True if len(spectraNd) > 1 else False,
                                          copyToSpectra=spectraNd)

                self._colourTabsNd.addTab(contoursTab, thisSpec.name)
                contoursTab.setContentsMargins(*TABMARGINS)

        self._colourTabsNd.setTabClickCallback(self._tabClickedNd)
        self._colourTabsNd.tabCloseRequested.connect(self._closeColourTabNd)
        self._oldTabs = OrderedDict()

        index = self._tabWidget.indexOf(self._generalTabWidgetNd)
        if self._colourTabsNd.count() == 0:
            if (0 <= index < NUMTABS):
                self._tabWidget.removeTab(index)

    def _initSeriesTab(self):
        thisTab = self.seriesTab
        thisTab._changes = OrderedDict()
        thisTab._populate()

    def _populate(self):
        """Populate the widgets in the tabs
        """
        with self.blockWidgetSignals():
            for colourTab in (self._colourTabs1d, self._colourTabsNd):
                for aTab in tuple(colourTab.widget(ii) for ii in range(colourTab.count())):
                    aTab._populateColour()

        self.seriesTab._fillSeriesFrame(self._defaultSpectra)
        self.seriesTab._populate()

        # NOTE:ED - check that the list widgets are populated correctly - may be called twice
        super()._populate()

    def _getChangeState(self):
        """Define the required widgets with storing changes
        returns Popup containing the apply/close buttons
                dict containing current changes
        """
        try:
            editName = self.nameEdit.text()
            defaultName = self._defaultName
            pidState = self._groupedObjects
            pidList = [str(spec.pid) for spec in self._defaultSpectra]

            revertState = (pidState != pidList) or (editName != defaultName)
            applyState = (True if pidState else False) and (True if editName else False) # and revertState

            tabs = self.getActiveTabList()
            allChanges = any(t._changes for t in tabs if t is not None)

        except Exception as es:
            return [None] * 7

        return self, allChanges, applyState, revertState, \
               self._applyButton, self._revertButton, 0

    def _tabClicked1d(self, index):
        """Callback for clicking a tab - needed for refilling the checkboxes and populating the pulldown
        """
        for colourTab in (self._colourTabs1d,):
            aTabs = tuple(colourTab.widget(ii) for ii in range(colourTab.count()))
            if aTabs and hasattr(aTabs[index], '_populateCheckBoxes'):
                aTabs[index]._populateCheckBoxes()

    def _tabClickedNd(self, index):
        """Callback for clicking a tab - needed for refilling the checkboxes and populating the pulldown
        """
        for colourTab in (self._colourTabsNd,):
            aTabs = tuple(colourTab.widget(ii) for ii in range(colourTab.count()))
            if aTabs and hasattr(aTabs[index], '_populateCheckBoxes'):
                aTabs[index]._populateCheckBoxes()

    def _getSpectraFromList(self):
        """Get the list of spectra from the list
        """
        return [spec for spec in [self.project.getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in self._groupedObjects] if spec]

    def _cleanColourTab(self, spectrum):
        """Remove the unwanted queue items from spectra reomved from the spectrumQueue
        """
        with self.blockWidgetSignals():
            for colourTab in (self._colourTabs1d, self._colourTabsNd):
                for aTab in tuple(colourTab.widget(ii) for ii in range(colourTab.count())):
                    if aTab.spectrum == spectrum:
                        aTab._cleanWidgetQueue()

    def _removeTab(self, spectrum):
        """Remove the unwanted queue items from spectra reomved from the spectrumQueue
        """
        for colourTab in (self._colourTabs1d, self._colourTabsNd):
            for aTab in tuple(colourTab.widget(ii) for ii in range(colourTab.count())):
                if aTab.spectrum == spectrum:
                    pass

    def _closeColourTab1d(self, index):
        self._colourTabs1d.removeTab(index)

    def _closeColourTabNd(self, index):
        self._colourTabsNd.removeTab(index)

    def _spectraChanged(self, *args):
        """Respond to a change in the list of spectra to add the spectrumGroup
        """
        self._spectraChanged1d()
        self._spectraChangedNd()

    def _spectraChanged1d(self):
        self._newSpectra = self._getSpectraFromList()

        deleteSet = (set(self.currentSpectra) - set(self._newSpectra))
        newSet = (set(self.currentSpectra) - set(self._newSpectra))

        # only select the 1d spectra
        deleteSet = [spec for spec in deleteSet if spec.dimensionCount == 1]
        spectra1d = [spec for spec in self._newSpectra if spec.dimensionCount == 1]

        for spec in deleteSet:
            # remove tab widget
            self._cleanColourTab(spec)
            if spec in self.seriesTab._currentSeriesValues:
                del self.seriesTab._currentSeriesValues[spec]

        # remove all in reverse order, keep old ones
        for ii in range(self._colourTabs1d.count() - 1, -1, -1):
            tab = self._colourTabs1d.widget(ii)
            self._oldTabs[tab.spectrum] = tab
            self._colourTabs1d.removeTab(ii)

        for spec in spectra1d:
            # add new tab widget here
            if spec in self._oldTabs:
                self._colourTabs1d.addTab(self._oldTabs[spec], spec.name)
                self._oldTabs[spec].setCopyOptionsVisible(True if len(spectra1d) > 1 else False)

                # make sure the new spectrum lists are up-to-date
                self._oldTabs[spec]._updateSpectra(spec, spectra1d)
                self._oldTabs[spec]._populateColour()
            else:
                if spec.dimensionCount == 1:
                    contoursTab = ColourTab(parent=self, mainWindow=self.mainWindow, spectrum=spec,
                                            showCopyOptions=True if len(spectra1d) > 1 else False,
                                            copyToSpectra=spectra1d)

                self._colourTabs1d.addTab(contoursTab, spec.name)
                contoursTab.setContentsMargins(*TABMARGINS)
                contoursTab._populateColour()

        # set the visibility of the general 1d tab
        index = self._tabWidget.indexOf(self._generalTabWidget1d)
        if self._colourTabs1d.count() == 0:
            if (0 <= index < NUMTABS):
                self._tabWidget.removeTab(index)
        else:
            if not (0 <= index < NUMTABS):
                self._tabWidget.insertTab(1, self._generalTabWidget1d, GENERALTAB1D_LABEL)

        self.seriesTab._fillSeriesFrame(self._newSpectra)

        # update the current list
        self.currentSpectra = self._newSpectra

    def _spectraChangedNd(self):
        self._newSpectra = self._getSpectraFromList()

        deleteSet = (set(self.currentSpectra) - set(self._newSpectra))
        newSet = (set(self.currentSpectra) - set(self._newSpectra))

        # only select the 1d spectra
        deleteSet = [spec for spec in deleteSet if spec.dimensionCount > 1]
        spectraNd = [spec for spec in self._newSpectra if spec.dimensionCount > 1]

        for spec in deleteSet:
            # remove tab widget
            self._cleanColourTab(spec)
            if spec in self.seriesTab._currentSeriesValues:
                del self.seriesTab._currentSeriesValues[spec]

        # remove all in reverse order, keep old ones
        for ii in range(self._colourTabsNd.count() - 1, -1, -1):
            tab = self._colourTabsNd.widget(ii)
            self._oldTabs[tab.spectrum] = tab
            self._colourTabsNd.removeTab(ii)

        for spec in spectraNd:
            # add new tab widget here
            if spec in self._oldTabs:
                self._colourTabsNd.addTab(self._oldTabs[spec], spec.name)
                self._oldTabs[spec].setCopyOptionsVisible(True if len(spectraNd) > 1 else False)

                # make sure the new spectrum lists are up-to-date
                self._oldTabs[spec]._updateSpectra(spec, spectraNd)
                self._oldTabs[spec]._populateColour()
            else:
                if spec.dimensionCount > 1:
                    contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=spec,
                                              showCopyOptions=True if len(spectraNd) > 1 else False,
                                              copyToSpectra=spectraNd)

                self._colourTabsNd.addTab(contoursTab, spec.name)
                contoursTab.setContentsMargins(*TABMARGINS)
                contoursTab._populateColour()

        # set the visibility of the general 1d tab
        index = self._tabWidget.indexOf(self._generalTabWidgetNd)
        if self._colourTabsNd.count() == 0:
            if (0 <= index < NUMTABS):
                self._tabWidget.removeTab(index)
        else:
            if not (0 <= index < NUMTABS):
                self._tabWidget.insertTab(self._tabWidget.count() - 1, self._generalTabWidgetNd, GENERALTABND_LABEL)

        self.seriesTab._fillSeriesFrame(self._newSpectra)

        # update the current list
        self.currentSpectra = self._newSpectra

    def copySpectra(self, fromSpectrum, toSpectra):
        """Copy the contents of tabs to other spectra
        """
        colourTabs = [self._colourTabs1d.widget(ii) for ii in range(self._colourTabs1d.count())] + \
                     [self._colourTabsNd.widget(ii) for ii in range(self._colourTabsNd.count())]
        for aTab in colourTabs:
            if aTab.spectrum == fromSpectrum:
                fromSpectrumTab = aTab
                for aTab in [tab for tab in colourTabs if tab != fromSpectrumTab and tab.spectrum in toSpectra]:
                    aTab._copySpectrumAttributes(fromSpectrumTab)


class SeriesFrame(Frame):
    EDITMODE = False

    def __init__(self, parent=None, mainWindow=None, spectrumGroup=None, editMode=False,
                 showCopyOptions=False, defaultItems=None):

        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING)

        self._parent = parent
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.preferences = self.application.preferences
        self.EDITMODE = editMode

        # check that the spectrum and the copyToSpectra list are correctly defined
        getByPid = self.application.project.getByPid
        self.spectrumGroup = getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(self.spectrumGroup, (SpectrumGroup, type(None))):
            raise TypeError('spectrumGroup must be of type spectrumGroup or None')

        if not isinstance(defaultItems, (Iterable, type(None))):
            raise TypeError('copyToSpectra must be of type Iterable/None')
        if defaultItems:
            self._copyToSpectra = [getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in defaultItems]
            for spec in self._copyToSpectra:
                if not isinstance(spec, (Spectrum, type(None))):
                    raise TypeError('copyToSpectra is not defined correctly.')
        else:
            self._copyToSpectra = None

        self._changes = OrderedDict()
        self._editors = OrderedDict()
        self._currentSeriesValues = OrderedDict()

        if self.EDITMODE:
            self.defaultObject = spectrumGroup
        else:
            # create a dummy object that SHOULD contain the required attributes
            self.defaultObject = _SpectrumGroupContainer()
            self.defaultObject.spectra = defaultItems

        row = 0
        col = 0
        # seriesLabel = Label(self, text="Spectrum SeriesValues", grid=(row, col), gridSpan=(1, 3), hAlign='l')
        # seriesLabel.setFixedHeight(30)
        # seriesLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        Spacer(self, 10, 10, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(row, col))

        row += 1
        seriesTypeLabel = Label(self, text='Series Type', grid=(row, col), hAlign='l')
        self.seriesType = RadioButtons(self, texts=[str(val.description) for val in SeriesTypes],
                                       grid=(row, col + 1), gridSpan=(1, 2), hAlign='l',
                                       callback=partial(self._queueChangeSeriesType, self.defaultObject))

        row += 1
        self._seriesFrameRow = row
        self._seriesFrameCol = col

        # self._seriesFrame = Frame(self, setLayout=True, showBorder=False, grid=(self._seriesFrameRow, self._seriesFrameCol), gridSpan=(1, 3))
        self._seriesFrame = None
        self._fillSeriesFrame(defaultItems=defaultItems)

        row += 1
        # unitsLabel = Label(self, text='Series Units', grid=(row, col), hAlign='l')
        # self.unitsEditor = LineEdit(self, grid=(row, col + 1))
        # unitsLabel.setFixedHeight(30)
        self.unitsEditor = PulldownListCompoundWidget(self, labelText='Series Units', grid=(row, col), gridSpan=(1, 3), hAlign='l',
                                                      editable=True, sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents)
        self.unitsEditor.pulldownList.pulldownTextEdited.connect(partial(self._queueChangeSeriesUnits, self.unitsEditor, self.defaultObject))
        self.unitsEditor.pulldownList.pulldownTextReady.connect(partial(self._updateSeriesUnitsPulldown, self.unitsEditor, self.defaultObject))
        self._pulldownData = ALL_UNITS

        row += 1
        self._errorFrameSeriesValues = Frame(self, setLayout=True, grid=(row, col), gridSpan=(1, 3), hAlign='l')

        # add a frame containing an error message if the series values are not all the same type
        self.errorIcon = Icon('icons/exclamation_small')
        # self._errorFrameSeriesValues.layout().setColumnStretch(0, 1)
        # self._errorFrameSeriesValues.layout().setColumnStretch(1, 1000)
        self._errors = ['seriesValues must be of the same type']
        for i, error in enumerate(self._errors):
            iconLabel = Label(self._errorFrameSeriesValues, grid=(i, 0))
            iconLabel.setPixmap(self.errorIcon.pixmap(16, 16))
            label = Label(self._errorFrameSeriesValues, error, grid=(i, 1))
        self._errorFrameSeriesValues.hide()

        row += 1
        self._errorFrameDict = Frame(self, setLayout=True, grid=(row, col), gridSpan=(1, 3), hAlign='l')

        # add a frame containing an error message if the dicts do not contain the same keys
        self.errorIcon = Icon('icons/exclamation_small')
        # self._errorFrameDict.layout().setColumnStretch(0, 1)
        # self._errorFrameDict.layout().setColumnStretch(1, 1000)
        self._errors = ['seriesValue dicts do not contain the same keys']
        for i, error in enumerate(self._errors):
            iconLabel = Label(self._errorFrameDict, grid=(i, 0))
            iconLabel.setPixmap(self.errorIcon.pixmap(16, 16))
            label = Label(self._errorFrameDict, error, grid=(i, 1))
        self._errorFrameDict.hide()

        row += 1
        Spacer(self, 1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(row, col + 2))
        self.getLayout().setRowStretch(row, 10)

        # set the background to transparent so matches the colour of the tab
        self.setAutoFillBackground(False)
        self.setStyleSheet('Frame { background: transparent; }')

        # get colours from the lineEdit and copy to the plainTextEdit
        # yourWidget.palette().highlight().color().name()?

    def _fillSeriesFrame(self, defaultItems):
        """Reset the contents of the series frame for changed spectrum list
        """
        # remove previous editor values
        for spec, editor in self._editors.items():
            editor.textChanged.disconnect()
            self._currentSeriesValues[spec] = editor.get()

        self._changes = OrderedDict()
        self._editors = OrderedDict()

        # empty the frame
        if self._seriesFrame:
            self._seriesFrame.hide()
            self._seriesFrame.deleteLater()

        self._seriesFrame = Frame(self, setLayout=True, showBorder=False,
                                  grid=(self._seriesFrameRow, self._seriesFrameCol), gridSpan=(1, 3),
                                  vAlign='t')

        # add new editors with the new values
        for sRow, spec in enumerate(defaultItems):
            seriesLabel = Label(self._seriesFrame, text=spec.pid, grid=(sRow, 0), vAlign='t')
            seriesLabel.setFixedHeight(30)

            editorFrame = Frame(self._seriesFrame, setLayout=True, grid=(sRow, 1), vAlign='t')
            seriesEditor = PlainTextEditor(editorFrame, grid=(0, 0), fitToContents=True)
            seriesEditor.textChanged.connect(partial(self._queueChangeSpectrumSeriesValues,
                                                     seriesEditor, self.defaultObject,
                                                     spec, sRow))

            seriesEditor.setMinimumSize(50, 25)
            # attributes for setting size when using resize-grip
            seriesEditor._minimumWidth = 50
            seriesEditor._minimumHeight = 25
            seriesEditor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

            if spec in self._currentSeriesValues and self._currentSeriesValues[spec] is not None:
                seriesEditor.set(self._currentSeriesValues[spec])

            self._editors[spec] = seriesEditor

        self._seriesFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    def _populate(self):
        """Populate the texteditors - seriesValues and seriesUnits for the spectrumGroup
        """
        self.seriesType.setIndex(int(self.defaultObject.seriesType or 0))
        series = self.defaultObject.series
        if series:
            for spec, textEditor in self._editors.items():
                ii = self.defaultObject.spectra.index(spec)

                try:
                    if self.seriesType.getIndex() == SeriesTypes.FLOAT.value:
                        seriesValue = float(series[ii])
                    if self.seriesType.getIndex() == SeriesTypes.INTEGER.value:
                        seriesValue = int(series[ii])
                    elif self.seriesType.getIndex() == SeriesTypes.STRING.value:
                        seriesValue = str(series[ii])
                    else:
                        seriesValue = repr(series[ii])
                except Exception as es:
                    textEditor.set('')
                else:
                    textEditor.set(str(seriesValue))

        if self.defaultObject.seriesUnits is not None and self.defaultObject.seriesUnits not in self._pulldownData:
            self._pulldownData += (self.defaultObject.seriesUnits,)
        self.unitsEditor.modifyTexts(texts=self._pulldownData)
        self.unitsEditor.select(self.defaultObject.seriesUnits)
        self._validateEditors()

    def _getValuesFromTextEdit(self):
        # read the values from the textEditors and put in dict for later
        for spec, editor in self._editors.items():
            self._currentSeriesValues[spec] = editor.get()

    def _cleanSpacers(self, widget):
        # remove unneeded spacers
        layout = widget.getLayout()
        spacers = [layout.itemAt(itmNum) for itmNum in range(layout.count()) if isinstance(layout.itemAt(itmNum), Spacer)]
        for sp in spacers:
            layout.removeItem(sp)

    @queueStateChange(_verifyPopupApply)
    def _queueChangeSpectrumSeriesValues(self, editor, spectrumGroup, spectrum, dim):
        # queue the value if has changed from the original
        value = editor.get()
        try:
            if self.seriesType.getIndex() == SeriesTypes.FLOAT.value:
                seriesValue = float(value)
            elif self.seriesType.getIndex() == SeriesTypes.INTEGER.value:
                seriesValue = int(value)
            elif self.seriesType.getIndex() == SeriesTypes.STRING.value:
                seriesValue = str(value)
            else:
                seriesValue = literal_eval(value)

        except Exception as es:
            # return partial(self._changeSpectrumSeriesValues, spectrumGroup, spectrum, dim, ERRORSTRING)
            pass

        else:
            specValue = spectrum._getSeriesItemsById(spectrumGroup.pid)
            if seriesValue != specValue:
                return partial(self._changeSpectrumSeriesValues, spectrumGroup, spectrum, dim, seriesValue)

        finally:
            self._validateEditors()

    def _compareDict(self, d1, d2):
        """Compare the keys in two dictionaries
        Routine is recursive, empty dicts are ignored
        """
        for k in d1:
            if k not in d2:
                return False
            if type(d1[k]) == dict and d1[k]:
                if type(d2[k]) == dict and d2[k]:
                    compare = self._compareDict(d1[k], d2[k])
                    if not compare:
                        return False
                else:
                    return False
        for k in d2:
            if k not in d1:
                return False
            if type(d2[k]) == dict and d2[k]:
                if type(d1[k]) == dict and d1[k]:
                    compare = self._compareDict(d1[k], d2[k])
                    if not compare:
                        return False
                else:
                    return False

        return True

    def _validateEditors(self):
        """Check that all the editors contain the same type of seriesValues
        """
        errorState = False
        errorDict = False
        heightSum = 0.0
        literalTypes = set()
        literalDictCompare = None
        for editor in self._editors.values():
            value = editor.get()
            palette = editor.viewport().palette()
            colour = editor._background
            try:
                seriesValue = None
                if self.seriesType.getIndex() == SeriesTypes.FLOAT.value:
                    seriesValue = float(value)
                elif self.seriesType.getIndex() == SeriesTypes.INTEGER.value:
                    seriesValue = int(value)
                elif self.seriesType.getIndex() == SeriesTypes.STRING.value:
                    seriesValue = str(value)
                else:
                    seriesValue = literal_eval(value)
                    literalTypes.add(type(seriesValue))

                    # compare whether the dicts contain the same keys - not essential
                    if not literalDictCompare:
                        literalDictCompare = seriesValue
                    else:
                        if isinstance(literalDictCompare, dict) and isinstance(seriesValue, dict):
                            cmp = self._compareDict(literalDictCompare, seriesValue)
                            if not cmp:
                                colour = INVALIDROWCOLOUR
                                errorDict = True

            except Exception as es:
                # catch exception raised by bad literals
                colour = INVALIDROWCOLOUR
                errorState = True

            finally:
                if literalTypes and len(literalTypes) > 1:
                    colour = INVALIDROWCOLOUR
                    errorState = True

                palette.setColor(editor.viewport().backgroundRole(), colour)
                editor.viewport().setPalette(palette)

            # rowHeight = QtGui.QFontMetrics(editor.document().defaultFont()).height()
            # lineCount = editor.document().lineCount()
            #
            # minHeight = (rowHeight + 1) * (lineCount + 1)
            # height = max(editor._minimumHeight, minHeight)
            # heightSum += height
            # editor.setMaximumHeight(height)
            # editor.updateGeometry()

        self._errorFrameSeriesValues.setVisible(errorState)
        self._errorFrameDict.setVisible(errorDict)

    def _changeSpectrumSeriesValues(self, spectrumGroup, spectrum, dim, value):
        # set the spectrum series value from here
        # spectrum.seriesValue = value

        # bit of a hack here - called by _groupInit which builds the spectrumGroup series
        self._parent._spectrumGroupSeriesEdited[dim] = value

    @queueStateChange(_verifyPopupApply)
    def _queueChangeSeriesUnits(self, editor, spectrumGroup):
        """callback from editing the seriesUnits - respond to every keypress
        """
        value = editor.getText()
        specValue = spectrumGroup.seriesUnits
        if value != specValue:
            return partial(self._changeSeriesUnits, spectrumGroup, value)

    def _changeSeriesUnits(self, spectrumGroup, value):
        """set the spectrumGroup seriesUnits
        """
        self._parent._spectrumGroupSeriesUnitsEdited = value

    def _updateSeriesUnitsPulldown(self, editor, spectrumGroup, newText):
        """callback from editing the seriesUnits pulldown
         - respond to index changed/focus changed to capture new text and add to pulldown list
        """
        # NOTE:ED - could put this into the pullDown widget as an 'autoUpdateContents' setting
        value = newText
        if value and value not in self._pulldownData:
            self._pulldownData += (value,)
            editor.modifyTexts(self._pulldownData)

        self._queueChangeSeriesUnits(editor, spectrumGroup)

    def _getChangeState(self):
        """Get the change state from the parent widget
        """
        return self._parent._getChangeState()

    @queueStateChange(_verifyPopupApply)
    def _queueChangeSeriesType(self, spectrumGroup):
        """callback from editing the seriesType
        """
        self._validateEditors()

        index = self.seriesType.getIndex()
        specType = spectrumGroup.seriesType
        if index != specType:
            return partial(self._changeSeriesType, spectrumGroup, index)

    def _changeSeriesType(self, spectrumGroup, value):
        """set the spectrumGroup seriesType
        """
        self._parent._spectrumGroupSeriesTypeEdited = value

    @queueStateChange(_verifyPopupApply)
    def _queueChangeName(self):
        """callback from editing the name
        """
        editName = self._parent.nameEdit.text()
        defaultName = self._parent._defaultName

        if editName != defaultName:
            return partial(self._changeName, editName)

    def _changeName(self, value):
        """set the spectrumGroup seriesType
        """
        # doesn't need to do anything, just insert an item into the revert _changes dict
        pass


class _SpectrumGroupContainer(AttrDict):
    """
    Class to simulate a spectrumGroup in popup.
    """

    def __init__(self):
        super(_SpectrumGroupContainer, self).__init__()
        self.pid = id(self)
        self.spectra = []
        self._modifiedSpectra = set()
        self._setDefaultSeriesValues()
        self._seriesUnits = None
        self._seriesType = 0

    @property
    def series(self) -> Tuple[Any, ...]:
        """Returns a tuple of series items for the attached spectra

        series = (val1, val2, ..., valN)

        where val1-valN correspond to the series items in the attached spectra associated with this group
        For a spectrum with no values, returns None in place of Item

        Duplicated from spectrumGroup.series
        """
        series = ()
        for spectrum in self.spectra:
            series += (spectrum._getSeriesItemsById(self.pid),)

        return series

    @property
    def seriesUnits(self):
        """Return the seriesUnits for the simulated spectrumGroup
        """
        return self._seriesUnits

    @property
    def seriesType(self):
        """Return the type for seriesValues widget entry
        """
        return self._seriesType

    def _setDefaultSeriesValues(self):
        for spec in self.spectra:
            spec._setSeriesItemsById(self.pid, None)

    def _removeDefaultSeriesValues(self):
        for spec in self.spectra:
            spec._removeSeriesItemsById(self.pid)

    def __del__(self):
        """destructor required to cleanup ids in altered spectra
        """
        self._removeDefaultSeriesValues()
