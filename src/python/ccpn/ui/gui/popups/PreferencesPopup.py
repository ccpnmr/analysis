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
__dateModified__ = "$dateModified: 2021-06-29 09:34:32 +0100 (Tue, June 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5 import QtWidgets, QtCore, QtGui, Qt
from functools import partial
from copy import deepcopy, copy
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.LineEdit import LineEdit, PasswordEdit
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.MessageDialog import showYesNo
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER, setColourScheme, FONTLIST, ZPlaneNavigationModes
from ccpn.framework.Translation import languages
from ccpn.ui.gui.popups.Dialog import handleDialogApply, _verifyPopupApply
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.util.Logging import getLogger
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown, colourNameNoSpace, _setColourPulldown
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.PeakList import GAUSSIANMETHOD, PARABOLICMETHOD
from ccpn.core.MultipletList import MULTIPLETAVERAGINGTYPES
from ccpn.util.UserPreferences import UserPreferences
from ccpn.util.Common import camelCaseToString
from ccpn.util.Path import aPath
from ccpn.util.Constants import AXIS_UNITS
from ccpn.ui.gui.lib.GuiPath import PathEdit
# from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraForPreferences
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.core.lib.ContextManagers import queueStateChange, undoStackBlocking
from ccpn.ui.gui.widgets.FileDialog import SpectrumFileDialog, ProjectFileDialog, AuxiliaryFileDialog, \
    LayoutsFileDialog, MacrosFileDialog, PluginsFileDialog, PipelineFileDialog, ExecutablesFileDialog, \
    ProjectSaveFileDialog
from ccpn.framework.lib.pipeline.PipesLoader import _fetchUserPipesPath
from ccpn.ui.gui.lib.ChangeStateHandler import changeState
from ccpn.ui.gui.widgets.Font import DEFAULTFONTNAME, DEFAULTFONTSIZE, DEFAULTFONTREGULAR, getFontHeight
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLFONT_DEFAULTSIZE, _OLDGLFONT_SIZES


PEAKFITTINGDEFAULTS = [PARABOLICMETHOD, GAUSSIANMETHOD]

# FIXME separate pure GUI to project/preferences properties
# The code sets Gui Parameters assuming that  Preference is not None and has a bunch of attributes.


PulldownListsMinimumWidth = 200
LineEditsMinimumWidth = 195
NotImplementedTipText = 'This option has not been implemented yet'
DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 10, 1)  # l, t, r, b
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b

FONTLABELFORMAT = '_fontLabel{}'
FONTDATAFORMAT = '_fontData{}'
FONTSTRING = '_fontString'
FONTPREFS = 'font{}'


def _updateSettings(self, newPrefs, updateColourScheme, updateSpectrumDisplays, userWorkingPath=None):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    # update the preferences, but keep in place
    self.application.preferences.clear()
    self.application.preferences.update(newPrefs)

    # application preferences updated so re-save
    self.application._savePreferences()

    # update the current userWorkingPath in the active file dialogs
    if userWorkingPath:
        _dialog = ProjectFileDialog(parent=self.mainWindow)
        _dialog.initialPath = aPath(userWorkingPath).filepath
        _dialog = ProjectSaveFileDialog(parent=self.mainWindow)
        _dialog.initialPath = aPath(userWorkingPath).filepath

    self._updateDisplay(updateColourScheme, updateSpectrumDisplays)

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


def _refreshGLItems():
    pass


class PreferencesPopup(CcpnDialogMainWidget):
    FIXEDHEIGHT = False
    FIXEDWIDTH = False

    def __init__(self, parent=None, mainWindow=None, preferences=None, title='Preferences', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, size=None, **kwds)

        self.mainWindow = mainWindow
        if self.mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
        else:
            self.application = None
            self.project = None

        if not self.project:
            MessageDialog.showWarning(title, 'No project loaded')
            self.close()
            return

        # copy the current preferences
        self.preferences = deepcopy(preferences)

        # grab the class with the preferences methods
        self._userPreferences = UserPreferences(readPreferences=False)

        # store the original values - needs to be recursive
        self._lastPrefs = deepcopy(self.preferences)

        self._setTabs()

        # enable the buttons
        self.setOkButton(callback=self._okClicked)
        self.setApplyButton(callback=self._applyClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        self._populate()

        tabs = tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))
        w = max(tab.sizeHint().width() for tab in tabs) + 40
        h = max(tab.sizeHint().height() for tab in tabs)
        h = max((h, 700))
        self._size = QtCore.QSize(w, h)
        self.setMinimumWidth(w)
        self.setMaximumWidth(w * 1.5)

        # keep a backup of the working paths in the dialogs
        self._tempDialog = ProjectFileDialog()
        self._tempDialog._storePaths()

        self.__postInit__()
        self._okButton = self.getButton(self.OKBUTTON)
        self._applyButton = self.getButton(self.APPLYBUTTON)
        self._revertButton = self.getButton(self.RESETBUTTON)

    def _getChangeState(self):
        """Get the change state from the _changes dict
        """
        if not self._changes.enabled:
            return None

        applyState = True
        revertState = False
        allChanges = True if self._changes else False

        return changeState(self, allChanges, applyState, revertState, self._okButton, self._applyButton, self._revertButton, self._currentNumApplies)

    def getActiveTabList(self):
        """Return the list of active tabs
        """
        return tuple(self.tabWidget.widget(ii) for ii in range(self.tabWidget.count()))

    def _revertClicked(self):
        """Revert button signal comes here
        Revert (roll-back) the state of the project to before the popup was opened
        """
        # Reset preferences to previous state
        if self._currentNumApplies > 0:

            if self.project and self.project._undo:
                for undos in range(self._currentNumApplies):
                    self.project._undo.undo()

            self.application._savePreferences()

        # retrieve the original preferences
        self.preferences = deepcopy(self._lastPrefs)
        self._populate()
        self._okButton.setEnabled(False)
        self._applyButton.setEnabled(False)
        self._revertButton.setEnabled(False)

    def _updateSpectrumDisplays(self):

        for display in self.project.spectrumDisplays:

            for strip in display.strips:
                with strip.blockWidgetSignals():
                    # NOTE:ED - should only set those values that have changed

                    strip.symbolLabelling = self.application.preferences.general.annotationType
                    strip.symbolType = self.application.preferences.general.symbolType
                    strip.symbolSize = self.application.preferences.general.symbolSizePixel

                    strip.symbolThickness = self.application.preferences.general.symbolThickness
                    strip.gridVisible = self.application.preferences.general.showGrid
                    strip.contourThickness = self.application.preferences.general.contourThickness
                    strip.crosshairVisible = self.application.preferences.general.showCrosshair
                    strip.doubleCrosshairVisible = self.application.preferences.general.showDoubleCrosshair
                    strip.sideBandsVisible = self.application.preferences.general.showSideBands

                    strip.spectrumBordersVisible = self.application.preferences.general.showSpectrumBorder

                    strip.aliasEnabled = self.application.preferences.general.aliasEnabled
                    strip.aliasShade = self.application.preferences.general.aliasShade
                    strip.aliasLabelsEnabled = self.application.preferences.general.aliasLabelsEnabled

                strip._frameGuide.resetColourTheme()

    def _updateDisplay(self, updateColourScheme, updateSpectrumDisplays):
        if updateColourScheme:
            # change the colour theme
            setColourScheme(self.application.preferences.general.colourScheme)
            self.application.correctColours()

        if updateSpectrumDisplays:
            self._updateSpectrumDisplays()

        # colour theme has changed - flag displays to update
        self._updateGui(updateSpectrumDisplays)

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

        # this will apply the immediate guiChanges with an undo block
        # applyToSDs = self.preferences.general.applyToSpectrumDisplays

        # need to get from the checkBox, otherwise out-of-sync
        applyToSDs = self.useApplyToSpectrumDisplaysBox.isChecked()

        allChanges = True if self._changes else False
        if not allChanges:
            return True

        # handle clicking of the Apply/OK button
        with handleDialogApply(self) as error:

            # remember the last state before applying changes
            lastPrefs = deepcopy(self.preferences)

            # apply all changes - only to self.preferences
            self._applyAllChanges(self._changes)

            # check whether the colourScheme needs updating
            _changeColour = self.preferences.general.colourScheme != lastPrefs.general.colourScheme
            _changeUserWorkingPath = self.preferences.general.userWorkingPath != lastPrefs.general.userWorkingPath

            # read the last working path set in the file dialogs
            _dialog = ProjectFileDialog(parent=self.mainWindow)
            _lastUserWorkingPath = _dialog.initialPath.asString()  # an aPath

            _newUserWorkingPath = self.preferences.general.userWorkingPath

            # add an undo item to update settings
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateSettings, self, lastPrefs, _changeColour, applyToSDs,
                                         _lastUserWorkingPath if _changeUserWorkingPath else None))

            # remember the new state - between addUndoItems because it may append to the undo stack
            newPrefs = deepcopy(self.preferences)
            _updateSettings(self, newPrefs, _changeColour, applyToSDs,
                            _newUserWorkingPath if _changeUserWorkingPath else None)

            # add a redo item to update settings
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_updateSettings, self, newPrefs, _changeColour, applyToSDs,
                                         _newUserWorkingPath if _changeUserWorkingPath else None))

            # everything has happened - disable the apply button
            self._applyButton.setEnabled(False)

        # check for any errors
        if error.errorValue:
            # re-populate popup from self.preferences on error
            self._populate()

            # revert the dialog paths
            self._tempDialog._restorePaths()
            return False

        # remove all changes
        self._changes.clear()

        self._currentNumApplies += 1
        self._revertButton.setEnabled(True)
        return True

    def reject(self) -> None:
        # revert the dialog paths
        self._tempDialog._restorePaths()

        super().reject()

    def _updateGui(self, updateSpectrumDisplays):

        # prompt the GLwidgets to update
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitEvent(triggers=[GLNotifier.GLALLCONTOURS,
                                      GLNotifier.GLALLPEAKS,
                                      GLNotifier.GLALLMULTIPLETS,
                                      GLNotifier.GLPREFERENCES])

        for specDisplay in self.project.spectrumDisplays:
            # update the fixed/locked state
            if specDisplay.strips and updateSpectrumDisplays:

                if not specDisplay.is1D:
                    specDisplay.zPlaneNavigationMode = ZPlaneNavigationModes(self.application.preferences.general.zPlaneNavigationMode).label
                    specDisplay.attachZPlaneWidgets()
                specDisplay._stripDirectionChangedInSettings(self.application.preferences.general.stripArrangement)
                # specDisplay.setVisibleAxes()

                # update the ratios from preferences
                specDisplay.strips[0].updateAxisRatios()

    def _setTabs(self):
        """Creates the tabs as Frame Widget. All the children widgets will go in the Frame.
        Each frame will be the widgets parent.
        Tabs are displayed by the order how appear here.
        """
        self.tabWidget = Tabs(self.mainWidget, grid=(0, 0), gridSpan=(1, 3))
        self.tabWidget.setContentsMargins(*ZEROMARGINS)
        # self.tabWidget.getLayout().setSpacing(0)

        for (tabFunc, tabName) in ((self._setGeneralTabWidgets, 'General'),
                                   (self._setSpectrumTabWidgets, 'Spectrum'),
                                   (self._setExternalProgramsTabWidgets, 'External Programs'),
                                   (self._setAppearanceTabWidgets, 'Appearance'),
                                   ):
            fr = ScrollableFrame(self.mainWidget, setLayout=True, spacing=DEFAULTSPACING,
                                 scrollBarPolicies=('never', 'asNeeded'), margins=TABMARGINS)

            self.tabWidget.addTab(fr.scrollArea, tabName)
            tabFunc(parent=fr)

        self.useApplyToSpectrumDisplaysLabel = Label(self.mainWidget, text="Apply to All Spectrum Displays", grid=(1, 0))
        self.useApplyToSpectrumDisplaysBox = CheckBox(self.mainWidget, grid=(1, 1))
        self.useApplyToSpectrumDisplaysBox.toggled.connect(partial(self._queueApplyToSpectrumDisplays, 'applyToSpectrumDisplays'))

    def _setGeneralTabWidgets(self, parent):
        """Insert a widget in here to appear in the General Tab
        """
        row = 0

        self.languageLabel = Label(parent, text="Language", grid=(row, 0), enabled=False)
        self.languageBox = PulldownList(parent, grid=(row, 1), hAlign='l', enabled=False)
        self.languageBox.addItems(languages)
        self.languageBox.setMinimumWidth(PulldownListsMinimumWidth)
        self.languageBox.currentIndexChanged.connect(self._queueChangeLanguage)

        row += 1
        self.autoSaveLayoutOnQuitLabel = Label(parent, text="Auto Save Layout On Quit", grid=(row, 0))
        self.autoSaveLayoutOnQuitBox = CheckBox(parent, grid=(row, 1))  #,
        self.autoSaveLayoutOnQuitBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoSaveLayoutOnQuit'))

        row += 1
        self.restoreLayoutOnOpeningLabel = Label(parent, text="Restore Layout On Opening", grid=(row, 0))
        self.restoreLayoutOnOpeningBox = CheckBox(parent, grid=(row, 1))
        self.restoreLayoutOnOpeningBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'restoreLayoutOnOpening'))

        row += 1
        self.autoBackupEnabledLabel = Label(parent, text="Auto Backup On", grid=(row, 0))
        self.autoBackupEnabledBox = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.general.autoBackupEnabled)
        self.autoBackupEnabledBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoBackupEnabled'))

        row += 1
        self.autoBackupFrequencyLabel = Label(parent, text="Auto Backup Freq (mins)", grid=(row, 0))
        self.autoBackupFrequencyData = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', min=10, decimals=0, step=10)
        self.autoBackupFrequencyData.setMinimumWidth(LineEditsMinimumWidth)
        self.autoBackupFrequencyData.valueChanged.connect(self._queueSetAutoBackupFrequency)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.userWorkingPathLabel = Label(parent, "User Working Path ", grid=(row, 0), )
        self.userWorkingPathData = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.userWorkingPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.userWorkingPathButton = Button(parent, grid=(row, 2), callback=self._getUserWorkingPath,
                                            icon='icons/directory', hPolicy='fixed')
        self.userWorkingPathData.textChanged.connect(self._queueSetUserWorkingPath)

        row += 1
        userLayouts = Label(parent, text="User Predefined Layouts ", grid=(row, 0))
        self.userLayoutsPathData = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.userLayoutsPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.userLayoutsLeButton = Button(parent, grid=(row, 2), callback=self._getUserLayoutsPath,
                                          icon='icons/directory', hPolicy='fixed')
        self.userLayoutsPathData.textChanged.connect(self._queueSetuserLayoutsPath)

        row += 1
        self.auxiliaryFilesLabel = Label(parent, text="Auxiliary Files Path ", grid=(row, 0))
        self.auxiliaryFilesData = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.auxiliaryFilesData.setMinimumWidth(LineEditsMinimumWidth)
        self.auxiliaryFilesDataButton = Button(parent, grid=(row, 2), callback=self._getAuxiliaryFilesPath,
                                               icon='icons/directory', hPolicy='fixed')
        self.auxiliaryFilesData.textChanged.connect(self._queueSetAuxiliaryFilesPath)

        row += 1
        self.macroPathLabel = Label(parent, text="Macro Path", grid=(row, 0))
        self.macroPathData = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.macroPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.macroPathDataButton = Button(parent, grid=(row, 2), callback=self._getMacroFilesPath,
                                          icon='icons/directory', hPolicy='fixed')
        self.macroPathData.textChanged.connect(self._queueSetMacroFilesPath)

        row += 1
        self.pluginPathLabel = Label(parent, text="Plugin Path", grid=(row, 0))
        self.pluginPathData = PathEdit(parent, grid=(row, 1), vAlign='t', tipText=NotImplementedTipText)
        self.pluginPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.pluginPathDataButton = Button(parent, grid=(row, 2), callback=self._getPluginFilesPath,
                                           icon='icons/directory', hPolicy='fixed')
        self.pluginPathData.textChanged.connect(self._queueSetPluginFilesPath)

        row += 1
        self.pipesPathLabel = Label(parent, text="Pipes Path", grid=(row, 0), )
        self.userPipesPath = PathEdit(parent, grid=(row, 1), vAlign='t', tipText='')
        self.userPipesPath.setMinimumWidth(LineEditsMinimumWidth)
        self.pipesPathDataButton = Button(parent, grid=(row, 2), callback=self._getUserPipesPath,
                                          icon='icons/directory', hPolicy='fixed')
        self.userPipesPath.textChanged.connect(self._queueSetPipesFilesPath)

        row += 1
        self.useProjectPathLabel = Label(parent, text="Set Working Path to Project Path", grid=(row, 0))
        self.useProjectPathBox = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.general.useProjectPath)
        self.useProjectPathBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'useProjectPath'))
        self.useProjectPathLabel.setToolTip('Set the current user working path to the project folder on loading')
        self.useProjectPathBox.setToolTip('Set the current user working path to the project folder on loading')

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.verifySSLLabel = Label(parent, text="Verify SSL certificates", grid=(row, 0))
        self.verifySSLBox = CheckBox(parent, grid=(row, 1))
        self.verifySSLBox.toggled.connect(self._queueSetVerifySSL)
        row += 1
        self.useProxyLabel = Label(parent, text="Use Proxy Settings", grid=(row, 0))
        self.useProxyBox = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.proxySettings.useProxy)
        self.useProxyBox.toggled.connect(self._queueSetUseProxy)

        row += 1
        self.proxyAddressLabel = Label(parent, text="   Web Proxy Server", grid=(row, 0), hAlign='l')
        self.proxyAddressData = LineEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyAddressData.setMinimumWidth(LineEditsMinimumWidth)
        self.proxyAddressData.textEdited.connect(self._queueSetProxyAddress)

        row += 1
        self.proxyPortLabel = Label(parent, text="   Port", grid=(row, 0), hAlign='l')
        self.proxyPortData = LineEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyPortData.setMinimumWidth(LineEditsMinimumWidth)
        self.proxyPortData.textEdited.connect(self._queueSetProxyPort)

        row += 1
        self.useProxyPasswordLabel = Label(parent, text="   Proxy Server Requires Password", grid=(row, 0))
        self.useProxyPasswordBox = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.proxySettings.useProxyPassword)
        self.useProxyPasswordBox.toggled.connect(self._queueSetUseProxyPassword)

        row += 1
        self.proxyUsernameLabel = Label(parent, text="        Username", grid=(row, 0), hAlign='l')
        self.proxyUsernameData = LineEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyUsernameData.setMinimumWidth(LineEditsMinimumWidth)
        self.proxyUsernameData.textEdited.connect(self._queueSetProxyUsername)

        row += 1
        self.proxyPasswordLabel = Label(parent, text="        Password", grid=(row, 0), hAlign='l')
        self.proxyPasswordData = PasswordEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyPasswordData.setMinimumWidth(LineEditsMinimumWidth)
        self.proxyPasswordData.textEdited.connect(self._queueSetProxyPassword)

        row += 1
        Spacer(parent, 15, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    def _setAppearanceTabWidgets(self, parent):
        """Insert a widget in here to appear in the Appearance Tab
        """

        row = 0
        self.colourSchemeLabel = Label(parent, text="Colour Scheme ", grid=(row, 0))
        self.colourSchemeBox = PulldownList(parent, grid=(row, 1), hAlign='l')
        self.colourSchemeBox.setToolTip('SpectrumDisplay Background only')
        self.colourSchemeBox.setMinimumWidth(PulldownListsMinimumWidth)
        self.colourSchemeBox.addItems(COLOUR_SCHEMES)
        self._oldColourScheme = None
        self.colourSchemeBox.currentIndexChanged.connect(self._queueChangeColourScheme)

        row += 1
        self.useNativeFileLabel = Label(parent, text="Use Native File Dialogs", grid=(row, 0))
        self.useNativeFileBox = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.general.useNative)
        self.useNativeFileBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'useNative'))

        row += 1
        self.useNativeLabel = Label(parent, text="Use Native Menus (requires restart)", grid=(row, 0))
        self.useNativeMenus = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.general.useNativeMenus)
        self.useNativeMenus.toggled.connect(partial(self._queueToggleGeneralOptions, 'useNativeMenus'))

        row += 1
        self.useNativeWebLabel = Label(parent, text="Use Native Web Browser", grid=(row, 0))
        self.useNativeWebBox = CheckBox(parent, grid=(row, 1))  #, checked=self.preferences.general.useNativeWebbrowser)
        self.useNativeWebBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'useNativeWebbrowser'))

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.useImportNefPopupLabel = Label(parent, text="Show Import Popup\n    on dropped Nef Files", grid=(row, 0))
        self.useImportNefPopupBox = CheckBox(parent, grid=(row, 1))
        self.useImportNefPopupBox.toggled.connect(partial(self._queueToggleAppearanceOptions, 'openImportPopupOnDroppedNef'))

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        # NOTE:ED - testing new font loader
        row += 1
        self._fontsLabel = Label(parent, text="Fonts (requires restart)", grid=(row, 0))

        for num, fontName in enumerate(FONTLIST):
            row += 1
            _label = Label(parent, text="    {}".format(fontName), grid=(row, 0))
            _data = Button(parent, grid=(row, 1), callback=partial(self._getFont, num, fontName))

            setattr(self, FONTLABELFORMAT.format(num), _label)
            setattr(self, FONTDATAFORMAT.format(num), _data)

        row += 1
        self.glFontSizeLabel = Label(parent, text="Spectrum Display Font Size", grid=(row, 0))
        self.glFontSizeData = PulldownList(parent, grid=(row, 1), hAlign='l')
        self.glFontSizeData.setMinimumWidth(PulldownListsMinimumWidth)
        self.glFontSizeData.currentIndexChanged.connect(self._queueChangeGLFontSize)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.showTipsAtStartUplabel = Label(parent, text="Show tips of the day at startup", grid=(row, 0))
        self.showTipsAtStartUp = CheckBox(parent, grid=(row, 1))
        self.showTipsAtStartUp.toggled.connect(self._queueSetShowTipsAtStartUp)

        row += 1
        self.showAllTipsLabel = Label(parent, text="Clear tip history\n (show all tips on next restart)", grid=(row, 0))
        self.showAllTips = CheckBox(parent, grid=(row, 1))
        self.showAllTips.clicked.connect(self._queueShowAllTips)

        row += 1
        Spacer(parent, 15, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    @queueStateChange(_verifyPopupApply)
    def _queueShowAllTips(self):
        if self.showAllTips.isChecked() and (len(self.preferences.general.seenTipsOfTheDay) != 0):
            return partial(self._setShowAllTips, True)
        else:
            return partial(self._setShowAllTips, False)

    @queueStateChange(_verifyPopupApply)
    def _queueSetShowTipsAtStartUp(self):
        value = self.showTipsAtStartUp.isChecked()
        if value != self.preferences.general.showTipOfTheDay:
            return partial(self._setShowTipsAtStartup, value)

    def _setShowTipsAtStartup(self, state):
        self.preferences.general.showTipOfTheDay = state

    def _setShowAllTips(self, showAllTips):
        if showAllTips:
            self.preferences.general.seenTipsOfTheDay.clear()
            self.preferences.general.seenTipsOfTheDay.extend(self._shownTips)
        else:
            self.preferences.general.seenTipsOfTheDay.clear()

    # def _queueClearSeenTips(self):
    #     #GST in this case the default should be no, but we can't do this yet... as yesNo doesn't support it
    #     #    also yes now sould allow custom button names and have default and action button separated...
    #     result = showYesNo(parent=self, title="Reset Seen tips", message="Are you sure you want to clear the seen tips list")
    #     if result:
    #         self.preferences.general.seenTipsOfTheDay.clear()

    def _populateAppearanceTab(self):
        """Populate the widgets in the appearanceTab
        """
        self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(self.preferences.general.colourScheme))
        self.useNativeFileBox.setChecked(self.preferences.general.useNative)
        self.useNativeMenus.setChecked(self.preferences.general.useNativeMenus)
        self.useNativeWebBox.setChecked(self.preferences.general.useNativeWebbrowser)
        self.useImportNefPopupBox.setChecked(self.preferences.appearance.openImportPopupOnDroppedNef)

        for fontNum, fontName in enumerate(FONTLIST):
            value = self.preferences.appearance[FONTPREFS.format(fontNum)]
            _fontAttr = getattr(self, FONTDATAFORMAT.format(fontNum))
            self.setFontText(_fontAttr, value)

        self.glFontSizeData.addItems([str(val) for val in _OLDGLFONT_SIZES])
        self.glFontSizeData.setCurrentIndex(self.glFontSizeData.findText(str(self.preferences.appearance.spectrumDisplayFontSize)))

        self.showTipsAtStartUp.setChecked(self.preferences.general.showTipOfTheDay)

        if len(self.preferences.general.seenTipsOfTheDay) == 0:
            self.showAllTips.setEnabled(False)
        self.showAllTips.setChecked(False)
        self._shownTips = copy(self.preferences.general.seenTipsOfTheDay)

    def _populate(self):
        """Populate the widgets in the tabs
        """
        # clear all changes
        self._changes.clear()

        with self._changes.blockChanges():
            self.useApplyToSpectrumDisplaysBox.setChecked(self.preferences.general.applyToSpectrumDisplays)
            self._populateGeneralTab()
            self._populateSpectrumTab()
            self._populateExternalProgramsTab()
            self._populateAppearanceTab()

    def setFontText(self, widget, fontString):
        """Set the contents of the widget the details of the font
        """
        try:
            fontList = fontString.split(',')
            if len(fontList) == 10:
                name, size, _, _, _, _, _, _, _, _ = fontList
                type = None
            elif len(fontList) == 11:
                name, size, _, _, _, _, _, _, _, _, type = fontList
            else:
                name, size, type = DEFAULTFONTNAME, DEFAULTFONTSIZE, DEFAULTFONTREGULAR
        except:
            name, size, type = DEFAULTFONTNAME, DEFAULTFONTSIZE, DEFAULTFONTREGULAR

        fontName = '{}, {}pt, {}'.format(name, size, type) if type else '{}, {}pt'.format(name, size, )
        widget._fontString = fontString
        widget.setText(fontName)

    def _populateGeneralTab(self):
        """Populate the widgets in the generalTab
        """
        self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
        self.autoSaveLayoutOnQuitBox.setChecked(self.preferences.general.autoSaveLayoutOnQuit)
        self.restoreLayoutOnOpeningBox.setChecked(self.preferences.general.restoreLayoutOnOpening)
        self.autoBackupEnabledBox.setChecked(self.preferences.general.autoBackupEnabled)
        self.autoBackupFrequencyData.setValue(self.preferences.general.autoBackupFrequency)
        self.userLayoutsPathData.setText(self.preferences.general.userLayoutsPath)
        self.userWorkingPathData.setText(self.preferences.general.userWorkingPath)
        self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
        self.macroPathData.setText(self.preferences.general.userMacroPath)
        self.pluginPathData.setText(self.preferences.general.userPluginPath)

        userPipesPath = _fetchUserPipesPath(self.application)  # gets from preferences or creates the default dir
        self.userPipesPath.setText(str(userPipesPath))

        self.useProjectPathBox.setChecked(self.preferences.general.useProjectPath)
        self.verifySSLBox.setChecked(self.preferences.proxySettings.verifySSL)
        self.useProxyBox.setChecked(self.preferences.proxySettings.useProxy)
        self.proxyAddressData.setText(str(self.preferences.proxySettings.proxyAddress))
        self.proxyPortData.setText(str(self.preferences.proxySettings.proxyPort))
        self.useProxyPasswordBox.setChecked(self.preferences.proxySettings.useProxyPassword)
        self.proxyUsernameData.setText(str(self.preferences.proxySettings.proxyUsername))
        self.proxyPasswordData.setText(self._userPreferences.decodeValue(str(self.preferences.proxySettings.proxyPassword)))

        # set the enabled state of the proxy settings boxes
        self._setProxyButtons()

    def _populateSpectrumTab(self):
        """Populate the widgets in the spectrumTab
        """
        self.autoSetDataPathBox.setChecked(self.preferences.general.autoSetDataPath)
        self.userDataPathText.setText(self.preferences.general.dataPath)

        # populate ValidateFrame
        # self._validateFrame._populate()

        self.regionPaddingData.setValue(float('%.1f' % (100 * self.preferences.general.stripRegionPadding)))
        self.dropFactorData.setValue(float('%.1f' % (100 * self.preferences.general.peakDropFactor)))
        self.peakFactor1D.setValue(float(self.preferences.general.peakFactor1D))
        volumeIntegralLimit = self.preferences.general.volumeIntegralLimit
        self.volumeIntegralLimitData.setValue(int(volumeIntegralLimit))

        from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC

        _peakPickers = PeakPickerABC._peakPickers
        self.peakPicker1dData.setData(texts=[''] + sorted([pp for pp in _peakPickers.keys()]))
        self.peakPickerNdData.setData(texts=[''] + sorted([pp for pp in _peakPickers.keys()]))
        self.peakPicker1dData.set(self.preferences.general.peakPicker1d)
        self.peakPickerNdData.set(self.preferences.general.peakPickerNd)

        self.peakFittingMethod.setIndex(PEAKFITTINGDEFAULTS.index(self.preferences.general.peakFittingMethod))
        self.showToolbarBox.setChecked(self.preferences.general.showToolbar)
        self.spectrumBorderBox.setChecked(self.preferences.general.showSpectrumBorder)
        self.showGridBox.setChecked(self.preferences.general.showGrid)
        self.showCrosshairBox.setChecked(self.preferences.general.showCrosshair)
        self.showDoubleCrosshairBox.setChecked(self.preferences.general.showDoubleCrosshair)
        self.showSideBandsBox.setChecked(self.preferences.general.showSideBands)
        self.showLastAxisOnlyBox.setChecked(self.preferences.general.lastAxisOnly)
        self.matchAxisCode.setIndex(self.preferences.general.matchAxisCode)
        self.axisOrderingOptions.setIndex(self.preferences.general.axisOrderingOptions)
        self.zoomCentre.setIndex(self.preferences.general.zoomCentreType)
        self.zoomPercentData.setValue(int(self.preferences.general.zoomPercent))
        self.stripWidthZoomPercentData.setValue(int(self.preferences.general.stripWidthZoomPercent))
        self.aspectRatioModeData.setIndex(self.preferences.general.aspectRatioMode)
        self.stripArrangementButtons.setIndex(self.preferences.general.stripArrangement)
        self.zPlaneNavigationModeData.setIndex(self.preferences.general.zPlaneNavigationMode)

        self.xAxisUnitsData.setIndex(self.preferences.general.xAxisUnits)
        self.yAxisUnitsData.setIndex(self.preferences.general.yAxisUnits)

        self.showZoomXLimitApplyBox.setChecked(self.preferences.general.zoomXLimitApply)
        self.showZoomYLimitApplyBox.setChecked(self.preferences.general.zoomYLimitApply)
        self.showIntensityLimitBox.setValue(self.preferences.general.intensityLimit)
        self.annotationsData.setIndex(self.preferences.general.annotationType)
        self.symbol.setIndex(self.preferences.general.symbolType)
        self.symbolSizePixelData.setValue(int('%i' % self.preferences.general.symbolSizePixel))
        self.symbolThicknessData.setValue(int(self.preferences.general.symbolThickness))

        _enabled = self.preferences.general.aliasEnabled
        self.aliasEnabledData.setChecked(_enabled)
        self.aliasShadeData.setValue(self.preferences.general.aliasShade)
        self.aliasLabelsEnabledData.setChecked(self.preferences.general.aliasLabelsEnabled)
        self.aliasLabelsEnabledData.setEnabled(_enabled)
        self.aliasShadeData.setEnabled(_enabled)

        self.contourThicknessData.setValue(int(self.preferences.general.contourThickness))

        self.autoCorrectBox.setChecked(self.preferences.general.autoCorrectColours)
        _setColourPulldown(self.marksDefaultColourBox, self.preferences.general.defaultMarksColour)
        self.showSideBandsData.setValue(int(self.preferences.general.numSideBands))

        multipletAveraging = self.preferences.general.multipletAveraging
        self.multipletAveraging.setIndex(MULTIPLETAVERAGINGTYPES.index(multipletAveraging) if multipletAveraging in MULTIPLETAVERAGINGTYPES else 0)
        self.singleContoursBox.setChecked(self.preferences.general.generateSinglePlaneContours)
        self.negativeTraceColourBox.setChecked(self.preferences.general.traceIncludeNegative)

        # NOTE: ED this seems a little awkward
        self.aspectLabel = {}
        self.aspectData = {}
        self._removeWidget(self.aspectLabelFrame)
        self._removeWidget(self.aspectDataFrame)
        for ii, aspect in enumerate(sorted(self.preferences.general.aspectRatios.keys())):
            aspectValue = self.preferences.general.aspectRatios[aspect]
            self.aspectLabel[aspect] = Label(self.aspectLabelFrame, text=aspect, grid=(ii, 0), hAlign='r')
            self.aspectData[aspect] = ScientificDoubleSpinBox(self.aspectDataFrame, min=1, grid=(ii, 0), hAlign='l')
            self.aspectData[aspect].setValue(aspectValue)
            self.aspectData[aspect].setMinimumWidth(LineEditsMinimumWidth)
            if aspect == self.preferences.general._baseAspectRatioAxisCode:
                self.aspectData[aspect].setEnabled(False)
            else:
                self.aspectData[aspect].setEnabled(True)
                self.aspectData[aspect].valueChanged.connect(partial(self._queueSetAspect, aspect, ii))

        self.useSearchBoxModeBox.setChecked(self.preferences.general.searchBoxMode)
        self.useSearchBoxDoFitBox.setChecked(self.preferences.general.searchBoxDoFit)

        self.searchBox1dLabel = {}
        self.searchBox1dData = {}
        self._removeWidget(self.searchBox1dLabelFrame)
        self._removeWidget(self.searchBox1dDataFrame)
        for ii, searchBox1d in enumerate(sorted(self.preferences.general.searchBoxWidths1d.keys())):
            searchBox1dValue = self.preferences.general.searchBoxWidths1d[searchBox1d]
            self.searchBox1dLabel[searchBox1d] = Label(self.searchBox1dLabelFrame, text=searchBox1d, grid=(ii, 0), hAlign='r')
            self.searchBox1dData[searchBox1d] = ScientificDoubleSpinBox(self.searchBox1dDataFrame, min=0.0001, grid=(ii, 0), hAlign='l')
            self.searchBox1dData[searchBox1d].setValue(searchBox1dValue)
            self.searchBox1dData[searchBox1d].setMinimumWidth(LineEditsMinimumWidth)
            # if searchBox1d == self.preferences.general._basesearchBox1dRatioAxisCode:
            #     self.searchBox1dData[searchBox1d].setEnabled(False)
            # else:
            #     self.searchBox1dData[searchBox1d].setEnabled(True)
            self.searchBox1dData[searchBox1d].valueChanged.connect(partial(self._queueSetSearchBox1d, searchBox1d, ii))

        self.searchBoxNdLabel = {}
        self.searchBoxNdData = {}
        self._removeWidget(self.searchBoxNdLabelFrame)
        self._removeWidget(self.searchBoxNdDataFrame)
        for ii, searchBoxNd in enumerate(sorted(self.preferences.general.searchBoxWidthsNd.keys())):
            searchBoxNdValue = self.preferences.general.searchBoxWidthsNd[searchBoxNd]
            self.searchBoxNdLabel[searchBoxNd] = Label(self.searchBoxNdLabelFrame, text=searchBoxNd, grid=(ii, 0), hAlign='r')
            self.searchBoxNdData[searchBoxNd] = ScientificDoubleSpinBox(self.searchBoxNdDataFrame, min=0.0001, grid=(ii, 0), hAlign='l')
            self.searchBoxNdData[searchBoxNd].setValue(searchBoxNdValue)
            self.searchBoxNdData[searchBoxNd].setMinimumWidth(LineEditsMinimumWidth)
            # if searchBoxNd == self.preferences.general._basesearchBoxNdRatioAxisCode:
            #     self.searchBoxNdData[searchBoxNd].setEnabled(False)
            # else:
            #     self.searchBoxNdData[searchBoxNd].setEnabled(True)
            self.searchBoxNdData[searchBoxNd].valueChanged.connect(partial(self._queueSetSearchBoxNd, searchBoxNd, ii))

    def _populateExternalProgramsTab(self):
        """Populate the widgets in the externalProgramsTab
        """
        with self._changes.blockChanges():
            for external, (extPath, _, _) in self.externalPaths.items():
                value = self.preferences.externalPrograms[external]
                extPath.setText(value)

    def _setSpectrumTabWidgets(self, parent):
        """Insert a widget in here to appear in the Spectrum Tab. Parent = the Frame obj where the widget should live
        """

        row = 0
        self.autoSetDataPathLabel = Label(parent, text="Auto Set dataPath", grid=(row, 0))
        self.autoSetDataPathBox = CheckBox(parent, grid=(row, 1))
        self.autoSetDataPathBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoSetDataPath'))

        row += 1
        self.userDataPathLabel = Label(parent, "User Data Path", grid=(row, 0), )
        self.userDataPathText = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.userDataPathText.setMinimumWidth(LineEditsMinimumWidth)
        self.userDataPathText.textChanged.connect(self._queueSetUserDataPath)
        self.userDataPathButton = Button(parent, grid=(row, 2), callback=self._getUserDataPath, icon='icons/directory',
                                         hPolicy='fixed', hAlign='left')


        # # add validate frame
        # row += 1
        # self._validateFrame = ValidateSpectraForPreferences(parent, mainWindow=self.mainWindow, spectra=self.project.spectra,
        #                                                     setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 3))
        #
        # self._validateFrame._filePathCallback = self._queueSetValidateFilePath
        # self._validateFrame._dataUrlCallback = self._queueSetValidateDataUrl
        # self._validateFrame._matchDataUrlWidths = parent
        # self._validateFrame._matchFilePathWidths = parent
        #
        # self._validateFrame.setVisible(False)
        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.xAxisUnits = Label(parent, text="X Axis Units", grid=(row, 0))
        self.xAxisUnitsData = RadioButtons(parent, texts=AXIS_UNITS,
                                           # selectedInd=xAxisUnits,
                                           callback=self._queueSetXUnits,
                                           direction='h',
                                           grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                           tipTexts=None,
                                           )

        row += 1
        self.yAxisUnits = Label(parent, text="Y Axis Units", grid=(row, 0))
        self.yAxisUnitsData = RadioButtons(parent, texts=AXIS_UNITS,
                                           # selectedInd=yAxisUnits,
                                           callback=self._queueSetYUnits,
                                           direction='h',
                                           grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                           tipTexts=None)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.regionPaddingLabel = Label(parent, text="Spectral Padding (%)", grid=(row, 0))
        self.regionPaddingData = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=0, max=100)
        self.regionPaddingData.setMinimumWidth(LineEditsMinimumWidth)
        self.regionPaddingData.valueChanged.connect(self._queueSetRegionPadding)

        ### Not fully Tested, Had some issues with $Path routines in setting the path of the copied spectra.
        ###  Needs more testing for different spectra formats etc. Disabled until completion.
        # row += 1
        # self.keepSPWithinProjectTipText = 'Keep a copy of spectra inside the project directory. Useful when changing the original spectra location path'
        # self.keepSPWithinProject = Label(parent, text="Keep a Copy Inside Project", grid=(row, 0))
        # self.keepSPWithinProjectBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.keepSpectraInsideProject,
        #                                        tipText=self.keepSPWithinProjectTipText)
        # self.keepSPWithinProjectBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'keepSpectraInsideProject'))

        row += 1
        self.showToolbarLabel = Label(parent, text="Show ToolBar(s)", grid=(row, 0))
        self.showToolbarBox = CheckBox(parent, grid=(row, 1))
        self.showToolbarBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showToolbar'))

        row += 1
        self.spectrumBorderLabel = Label(parent, text="Show Spectrum Borders", grid=(row, 0))
        self.spectrumBorderBox = CheckBox(parent, grid=(row, 1))
        self.spectrumBorderBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showSpectrumBorder'))

        row += 1
        self.showGridLabel = Label(parent, text="Show Grids", grid=(row, 0))
        self.showGridBox = CheckBox(parent, grid=(row, 1))
        self.showGridBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showGrid'))

        row += 1
        self.showCrosshairLabel = Label(parent, text="Show Crosshairs", grid=(row, 0))
        self.showCrosshairBox = CheckBox(parent, grid=(row, 1))
        self.showCrosshairBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showCrosshair'))

        row += 1
        self.showDoubleCrosshairLabel = Label(parent, text="    and Double Crosshairs", grid=(row, 0))
        self.showDoubleCrosshairBox = CheckBox(parent, grid=(row, 1))
        self.showDoubleCrosshairBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showDoubleCrosshair'))

        row += 1
        self.showSideBandsLabel = Label(parent, text="Show MAS Side Bands", grid=(row, 0))
        self.showSideBandsBox = CheckBox(parent, grid=(row, 1))
        self.showSideBandsBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showSideBands'))

        row += 1
        self.showSideBands = Label(parent, text='    number of MAS side bands shown', grid=(row, 0), hAlign='l')
        self.showSideBandsData = DoubleSpinbox(parent, step=1, min=0, max=25, grid=(row, 1), hAlign='l', decimals=0)
        self.showSideBandsData.setMinimumWidth(LineEditsMinimumWidth)
        self.showSideBandsData.valueChanged.connect(self._queueSetNumSideBands)

        row += 1
        self.showLastAxisOnlyLabel = Label(parent, text="Share Y Axis", grid=(row, 0))
        self.showLastAxisOnlyBox = CheckBox(parent, grid=(row, 1))
        self.showLastAxisOnlyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'lastAxisOnly'))

        row += 1
        self.matchAxisCodeLabel = Label(parent, text="Match Axis Codes", grid=(row, 0))
        self.matchAxisCode = RadioButtons(parent, texts=['Atom Type', 'Full Axis Code'],
                                          callback=self._queueSetMatchAxisCode,
                                          direction='h',
                                          grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                          tipTexts=None,
                                          )

        row += 1
        self.axisOrderingOptionsLabel = Label(parent, text="Axis Ordering", grid=(row, 0))
        self.axisOrderingOptions = RadioButtons(parent, texts=['Use Spectrum Settings', 'Always Ask'],
                                                callback=self._queueSetAxisOrderingOptions,
                                                direction='h',
                                                grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                                tipTexts=None,
                                                )

        row += 1
        _frame =  Frame(parent, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1,3))
        _frame.setMinimumHeight(40)

        _frame1 = Frame(_frame, setLayout=True, showBorder=False, grid=(0, 0))
        _frame1.setMaximumWidth(30)
        HLine(_frame1, grid=(0, 0), colour=getColours()[DIVIDER], height=20)

        Label(_frame, grid=(0, 1), hAlign='centre', hPolicy='minimal', bold=True, text="Peak Picking")

        _frame2 = Frame(_frame, setLayout=True, showBorder=False, grid=(0, 2))
        HLine(_frame2, grid=(0, 0), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.peakPicker1dLabel = Label(parent, text="Default 1D Peak Picker", grid=(row, 0))
        self.peakPicker1dData = PulldownList(parent, grid=(row, 1))
        # self.peakPicker1dData.setMinimumWidth(LineEditsMinimumWidth)
        self.peakPicker1dData.currentIndexChanged.connect(self._queueChangePeakPicker1dIndex)

        row += 1
        self.dropFactorLabel = Label(parent, text="1D Peak Picking Drop (%)", tipText='Increase to filter out more', grid=(row, 0))
        self.peakFactor1D = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=-100, max=100)
        self.peakFactor1D.setMinimumWidth(LineEditsMinimumWidth)
        self.peakFactor1D.valueChanged.connect(self._queueSetDropFactor1D)

        row += 1
        self.peakPickerNdLabel = Label(parent, text="Default nD Peak Picker", grid=(row, 0))
        self.peakPickerNdData = PulldownList(parent, grid=(row, 1))
        # self.peakPickerNdData.setMinimumWidth(LineEditsMinimumWidth)
        self.peakPickerNdData.currentIndexChanged.connect(self._queueChangePeakPickerNdIndex)

        row += 1
        self.dropFactorLabel = Label(parent, text="nD Peak Picking Drop (%)", grid=(row, 0))
        self.dropFactorData = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=0, max=100)
        self.dropFactorData.setMinimumWidth(LineEditsMinimumWidth)
        self.dropFactorData.valueChanged.connect(self._queueSetDropFactor)

        row += 1
        self.peakFittingMethodLabel = Label(parent, text="Peak Interpolation Method", grid=(row, 0))
        self.peakFittingMethod = RadioButtons(parent, texts=PEAKFITTINGDEFAULTS,
                                              callback=self._queueSetPeakFittingMethod,
                                              direction='h',
                                              grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                              tipTexts=None,
                                              )

        row += 1
        self.volumeIntegralLimitLabel = Label(parent, text="Volume Integral Limit", grid=(row, 0))
        self.volumeIntegralLimitData = DoubleSpinbox(parent, step=0.05, decimals=2,
                                                     min=1.0, max=5.0, grid=(row, 1), hAlign='l')
        self.volumeIntegralLimitData.setMinimumWidth(LineEditsMinimumWidth)
        self.volumeIntegralLimitData.valueChanged.connect(self._queueSetVolumeIntegralLimit)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.zoomCentreLabel = Label(parent, text="Zoom Centre", grid=(row, 0))
        self.zoomCentre = RadioButtons(parent, texts=['Mouse', 'Screen'],
                                       callback=self._queueSetZoomCentre,
                                       direction='h',
                                       grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                       tipTexts=None,
                                       )
        row += 1
        self.zoomPercentLabel = Label(parent, text="Manual Zoom (%)", grid=(row, 0))
        self.zoomPercentData = DoubleSpinbox(parent, step=1,
                                             min=1, max=100, grid=(row, 1), hAlign='l')
        self.zoomPercentData.setMinimumWidth(LineEditsMinimumWidth)
        self.zoomPercentData.valueChanged.connect(self._queueSetZoomPercent)

        row += 1
        self.stripWidthZoomPercentLabel = Label(parent, text="Strip Width Zoom (%)", grid=(row, 0))
        self.stripWidthZoomPercentData = DoubleSpinbox(parent, step=1,
                                                       min=1, max=100, grid=(row, 1), hAlign='l')
        self.stripWidthZoomPercentData.setMinimumWidth(LineEditsMinimumWidth)
        self.stripWidthZoomPercentData.valueChanged.connect(self._queueSetStripWidthZoomPercent)

        row += 1
        self.showZoomXLimitApplyLabel = Label(parent, text="Apply Zoom limit to X axis", grid=(row, 0))
        self.showZoomXLimitApplyBox = CheckBox(parent, grid=(row, 1))
        self.showZoomXLimitApplyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'zoomXLimitApply'))

        row += 1
        self.showZoomYLimitApplyLabel = Label(parent, text="Apply Zoom limit to Y axis", grid=(row, 0))
        self.showZoomYLimitApplyBox = CheckBox(parent, grid=(row, 1))
        self.showZoomYLimitApplyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'zoomYLimitApply'))

        row += 1
        self.showIntensityLimitLabel = Label(parent, text='Minimum Intensity Limit', grid=(row, 0), hAlign='l')
        self.showIntensityLimitBox = ScientificDoubleSpinBox(parent, min=1e-6, grid=(row, 1), hAlign='l')
        self.showIntensityLimitBox.setMinimumWidth(LineEditsMinimumWidth)
        self.showIntensityLimitBox.valueChanged.connect(self._queueSetIntensityLimit)


        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.aspectRatioModeLabel = Label(parent, text="Aspect Ratio Mode", grid=(row, 0))
        self.aspectRatioModeData = RadioButtons(parent, texts=['Free', 'Locked', 'Fixed'],
                                                callback=self._queueSetAspectRatioMode,
                                                direction='h',
                                                grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                                tipTexts=None,
                                                )

        row += 1
        Label(parent, text='Fixed Aspects', grid=(row, 0), hAlign='r')

        row += 1
        self.aspectLabel = {}
        self.aspectData = {}
        self.aspectLabelFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 0))
        self.aspectDataFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 1))

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.annotationsLabel = Label(parent, text="Symbol Labelling", grid=(row, 0))
        self.annotationsData = RadioButtons(parent, texts=['Short', 'Full', 'Pid', 'Minimal', 'Id', 'Annotation'],
                                            callback=self._queueSetAnnotations,
                                            direction='h',
                                            grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                            tipTexts=None,
                                            )
        row += 1
        self.symbolsLabel = Label(parent, text="Symbol Type", grid=(row, 0))
        self.symbol = RadioButtons(parent, texts=['Cross', 'lineWidths', 'Filled lineWidths', 'Plus'],
                                   callback=self._queueSetSymbol,
                                   direction='h',
                                   grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                   tipTexts=None,
                                   )

        row += 1
        self.symbolSizePixelLabel = Label(parent, text="Symbol Size (pixel)", grid=(row, 0))
        self.symbolSizePixelData = Spinbox(parent, step=1,
                                           min=2, max=50, grid=(row, 1), hAlign='l')
        self.symbolSizePixelData.setMinimumWidth(LineEditsMinimumWidth)
        self.symbolSizePixelData.valueChanged.connect(self._queueSetSymbolSizePixel)

        row += 1
        self.symbolThicknessLabel = Label(parent, text="Symbol Thickness (pixel)", grid=(row, 0))
        self.symbolThicknessData = Spinbox(parent, step=1,
                                           min=1, max=20, grid=(row, 1), hAlign='l')
        self.symbolThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        self.symbolThicknessData.valueChanged.connect(self._queueSetSymbolThickness)

        row += 1
        self.aliasEnabledLabel = Label(parent, text="Show Aliased Peaks", grid=(row, 0))
        self.aliasEnabledData = CheckBox(parent, grid=(row, 1))
        self.aliasEnabledData.toggled.connect(partial(self._queueToggleGeneralOptions, 'aliasEnabled'))

        row += 1
        self.aliasLabelsEnabledLabel = Label(parent, text="    Show Aliased Labels", grid=(row, 0))
        self.aliasLabelsEnabledData = CheckBox(parent, grid=(row, 1))
        self.aliasLabelsEnabledData.toggled.connect(partial(self._queueToggleGeneralOptions, 'aliasLabelsEnabled'))

        row += 1
        self.aliasShadeLabel = Label(parent, text="    Opacity", grid=(row, 0))
        # self.aliasShadeData = DoubleSpinbox(parent, step=0.05,
        #                                     min=0.0, max=1.0, grid=(row, 1), hAlign='l')
        _sliderBox = Frame(parent, setLayout=True, grid=(row, 1), hAlign='l')
        # self.aliasShadeData = Slider(parent, grid=(row, 1), hAlign='l')
        self.aliasShadeData = Slider(_sliderBox, grid=(0, 1), hAlign='l')
        Label(_sliderBox, text="0", grid=(0, 0), hAlign='l')
        Label(_sliderBox, text="100%", grid=(0, 2), hAlign='l')
        self.aliasShadeData.setMinimumWidth(LineEditsMinimumWidth)
        self.aliasShadeData.valueChanged.connect(self._queueSetAliasShade)

        row += 1
        self.contourThicknessLabel = Label(parent, text="Contour Thickness (pixel)", grid=(row, 0))
        self.contourThicknessData = Spinbox(parent, step=1,
                                            min=1, max=20, grid=(row, 1), hAlign='l')
        self.contourThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        self.contourThicknessData.valueChanged.connect(self._queueSetContourThickness)

        row += 1
        _height = getFontHeight(size='VLARGE') or 24
        self.stripArrangementLabel = Label(parent, text="Strip Arrangement", grid=(row, 0))
        self.stripArrangementButtons = RadioButtons(parent, texts=['    ', '    ', '    '],
                                                    # selectedInd=stripArrangement,
                                                    direction='horizontal',
                                                    grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                                    tipTexts=None,
                                                    icons=[('icons/strip-row', (_height, _height)),
                                                           ('icons/strip-column', (_height, _height)),
                                                           ('icons/strip-tile', (_height, _height))
                                                           ],
                                                    )
        # NOTE:ED - temporarily disable/hide the Tile button
        self.stripArrangementButtons.radioButtons[2].setEnabled(False)
        self.stripArrangementButtons.radioButtons[2].setVisible(False)
        self.stripArrangementButtons.setCallback(self._queueSetStripArrangement)

        row += 1
        self.zPlaneNavigationModeLabel = Label(parent, text="zPlane Navigation Mode", grid=(row, 0))
        self.zPlaneNavigationModeData = RadioButtons(parent, texts=[val.description for val in ZPlaneNavigationModes],
                                                     callback=self._queueSetZPlaneNavigationMode,
                                                     direction='h',
                                                     grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                                     tipTexts=('Tools are located at the bottom of the spectrumDisplay,\nand will operate on the last strip selected in that spectrumDisplay',
                                                               'Tools are located at the bottom of each strip',
                                                               'Tools are displayed in the upper-left corner of each strip display'),
                                                     )
        self.zPlaneNavigationModeLabel.setToolTip('Select where the zPlane navigation tools are located')

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.useSearchBoxModeLabel = Label(parent, text="Use Search Box Widths", grid=(row, 0))
        self.useSearchBoxModeBox = CheckBox(parent, grid=(row, 1))
        self.useSearchBoxModeBox.toggled.connect(self._queueSetUseSearchBoxMode)
        self.useSearchBoxModeLabel.setToolTip(
                'Use defined search box widths (ppm)\nor default to ±4 index points.\nNote, default will depend on resolution of spectrum')
        self.useSearchBoxModeBox.setToolTip(
                'Use defined search box widths (ppm)\nor default to ±4 index points.\nNote, default will depend on resolution of spectrum')

        row += 1
        self.useSearchBoxDoFitLabel = Label(parent, text="Apply Peak Fitting Method\n after Snap To Extrema", grid=(row, 0))
        self.useSearchBoxDoFitBox = CheckBox(parent, grid=(row, 1))
        self.useSearchBoxDoFitBox.toggled.connect(self._queueSetUseSearchBoxDoFit)
        self.useSearchBoxDoFitLabel.setToolTip('Option to apply fitting method after initial snap to extrema')
        self.useSearchBoxDoFitBox.setToolTip('Option to apply fitting method after initial snap to extrema')

        row += 1
        self.defaultSearchBox1dRatioLabel = Label(parent, text="1d Search Box Widths (ppm)", grid=(row, 0), hAlign='r')

        row += 1
        self.searchBox1dLabel = {}
        self.searchBox1dData = {}
        self.searchBox1dLabelFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 0))
        self.searchBox1dDataFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 1))

        row += 1
        self.defaultSearchBoxNdRatioLabel = Label(parent, text="Nd Search Box Widths (ppm)", grid=(row, 0), hAlign='r')

        row += 1
        self.searchBoxNdLabel = {}
        self.searchBoxNdData = {}
        self.searchBoxNdLabelFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 0))
        self.searchBoxNdDataFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 1))

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.autoCorrectLabel = Label(parent, text="Autocorrect Colours", grid=(row, 0))
        self.autoCorrectBox = CheckBox(parent, grid=(row, 1))
        self.autoCorrectBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoCorrectColours'))

        row += 1
        self.marksDefaultColourLabel = Label(parent, text="Default Marks Colour", grid=(row, 0))
        _colourFrame = Frame(parent, setLayout=True, grid=(row, 1), hAlign='l', gridSpan=(1, 2))
        self.marksDefaultColourBox = PulldownList(_colourFrame, grid=(0, 0))
        self.marksDefaultColourBox.setMinimumWidth(LineEditsMinimumWidth)

        # populate colour pulldown and set to the current colour
        fillColourPulldown(self.marksDefaultColourBox, allowAuto=False, includeGradients=True)
        self.marksDefaultColourBox.currentIndexChanged.connect(self._queueChangeMarksColourIndex)

        # add a colour dialog button
        self.marksDefaultColourButton = Button(_colourFrame, grid=(0, 1), hAlign='l',
                                               icon='icons/colours', hPolicy='fixed')
        self.marksDefaultColourButton.clicked.connect(self._queueChangeMarksColourButton)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.multipletAveragingLabel = Label(parent, text="Multiplet Averaging", grid=(row, 0))
        self.multipletAveraging = RadioButtons(parent, texts=MULTIPLETAVERAGINGTYPES,
                                               callback=self._queueSetMultipletAveraging,
                                               direction='h',
                                               grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                               tipTexts=None,
                                               )

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=20)

        row += 1
        self.singleContoursLabel = Label(parent, text="Generate Single Contours\n   per Plane", grid=(row, 0))
        self.singleContoursBox = CheckBox(parent, grid=(row, 1))
        self.singleContoursBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'generateSinglePlaneContours'))

        row += 1
        self.negativeTraceColourLabel = Label(parent, text="Include Negative Colour\n    for Phasing Traces", grid=(row, 0))
        self.negativeTraceColourBox = CheckBox(parent, grid=(row, 1))
        self.negativeTraceColourBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'traceIncludeNegative'))

        # add spacer to stop columns changing width
        row += 1
        Spacer(parent, 15, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    @queueStateChange(_verifyPopupApply)
    def _queueChangeMarksColourIndex(self, value):
        if value >= 0:
            colName = colourNameNoSpace(self.marksDefaultColourBox.getText())
            if colName in spectrumColours.values():
                colName = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            if colName != self.preferences.general.defaultMarksColour:
                # and list(spectrumColours.keys())[value] != self.preferences.general.defaultMarksColour:
                return partial(self._changeMarksColourIndex, value)

    def _changeMarksColourIndex(self, value):
        """Change the default maerks colour in the preferences
        """
        colName = colourNameNoSpace(self.marksDefaultColourBox.currentText())
        if colName in spectrumColours.values():
            newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        else:
            newColour = colName

        if newColour:
            self.preferences.general.defaultMarksColour = newColour

    def _queueChangeMarksColourButton(self):
        """set the default marks colour from the colour dialog
        """
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            fillColourPulldown(self.marksDefaultColourBox, allowAuto=False, includeGradients=True)
            self.marksDefaultColourBox.setCurrentText(spectrumColours[newColour.name()])

    def _setExternalProgramsTabWidgets(self, parent):
        """Insert a widget in here to appear in the externalPrograms Tab
        """
        self.externalPaths = {}
        extPrograms = sorted((camelCaseToString(k), k) for k in self.preferences.externalPrograms.keys())

        row = 0
        for dim, (name, external) in enumerate(extPrograms):
            Label(parent, name, grid=(row, 0), )

            externalPath = PathEdit(parent, grid=(row, 1), hAlign='t')
            externalPath.setMinimumWidth(LineEditsMinimumWidth)
            externalPath.textChanged.connect(partial(self._queueSetExternalPath, external, dim))

            externalButton = Button(parent, grid=(row, 2), callback=partial(self._getExternalPath, external),
                                    icon='icons/directory', hPolicy='fixed')

            externalTestButton = Button(parent, grid=(row, 3), callback=partial(self._testExternalPath, external),
                                        text='test', hPolicy='fixed')

            self.externalPaths[external] = (externalPath, externalButton, externalTestButton)

            row += 1

        # add spacer to stop columns changing width
        row += 1
        Spacer(parent, 15, 2,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    def _testExternalPath(self, external):
        if external not in self.preferences.externalPrograms:
            raise RuntimeError(f'{external} not defined')
        if external not in self.externalPaths:
            raise RuntimeError(f'{external} not defined in preferences')

        widgetList = self.externalPaths[external]
        try:
            extPath, _, _ = widgetList

            program = extPath.get()
            if not self._testExternalProgram(program):
                self.sender().setText('Failed')
            else:
                self.sender().setText('Success')

        except Exception as es:
            raise RuntimeError(f'{external} does not contain the correct widgets')

    def _testExternalProgram(self, program):
        import subprocess

        try:
            # TODO:ED check whether relative or absolute path and test
            # import ccpn.framework.PathsAndUrls as PAU
            # pathCwd = PAU.ccpnCodePath
            # programPath = os.path.abspath(os.path.join(pathCwd, program))

            p = subprocess.Popen(program,
                                 shell=False,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            return True

        except Exception as e:
            getLogger().warning('Testing External program: Failed.' + str(e))
            return False

    @queueStateChange(_verifyPopupApply)
    def _queueSetUserDataPath(self):
        value = self.userDataPathText.get()
        if value != self.preferences.general.dataPath:
            return partial(self._setUserDataPath, value)

    def _setUserDataPath(self, value):
        self.preferences.general.dataPath = value
        dialog = SpectrumFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getUserDataPath(self):
        currentDataPath = aPath(self.userDataPathText.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = SpectrumFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.userDataPathText.setText(directory[0])

    @queueStateChange(_verifyPopupApply)
    def _queueSetUserWorkingPath(self):
        value = self.userWorkingPathData.get()
        if value != self.preferences.general.userWorkingPath:
            return partial(self._setUserWorkingPath, value)

    def _setUserWorkingPath(self, value):
        self.preferences.general.userWorkingPath = value
        dialog = ProjectFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getUserWorkingPath(self):
        currentDataPath = aPath(self.userWorkingPathData.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = ProjectFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.userWorkingPathData.setText(directory[0])

    @queueStateChange(_verifyPopupApply)
    def _queueSetAuxiliaryFilesPath(self):
        value = self.auxiliaryFilesData.get()
        if value != self.preferences.general.auxiliaryFilesPath:
            return partial(self._setAuxiliaryFilesPath, value)

    def _setAuxiliaryFilesPath(self, value):
        self.preferences.general.auxiliaryFilesPath = value
        dialog = AuxiliaryFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getAuxiliaryFilesPath(self):
        currentDataPath = aPath(self.auxiliaryFilesData.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = AuxiliaryFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.auxiliaryFilesData.setText(directory[0])

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
    #     if dim == 0:
    #         # must be the first dataUrl for the preferences
    #         # self.preferences.general.dataPath = newUrl
    #         pass
    #
    #     # if urlValid:
    #     # self._validateFrame.dataUrlFunc(dataUrl, newUrl)

    # @queueStateChange(_verifyPopupApply)
    # def _queueSetValidateFilePath(self, spectrum, filePath, dim):
    #     """Set the new filePath for the spectrum
    #     dim is required by the decorator to give a unique id for filePath row
    #     """
    #     if filePath != spectrum.filePath:
    #         return partial(self._validateFrame.filePathFunc, spectrum, filePath)

    @queueStateChange(_verifyPopupApply)
    def _queueSetuserLayoutsPath(self):
        value = self.userLayoutsPathData.get()
        if value != self.preferences.general.userLayoutsPath:
            return partial(self._setUserLayoutsPath, value)

    def _setUserLayoutsPath(self, value):
        self.preferences.general.userLayoutsPath = value
        dialog = LayoutsFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getUserLayoutsPath(self):
        currentDataPath = aPath(self.userLayoutsPathData.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = LayoutsFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.userLayoutsPathData.setText(directory[0])

    @queueStateChange(_verifyPopupApply)
    def _queueSetMacroFilesPath(self):
        value = self.macroPathData.get()
        if value != self.preferences.general.userMacroPath:
            return partial(self._setMacroFilesPath, value)

    def _setMacroFilesPath(self, value):
        self.preferences.general.userMacroPath = value
        dialog = MacrosFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getMacroFilesPath(self):
        currentDataPath = aPath(self.macroPathData.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = MacrosFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.macroPathData.setText(directory[0])

    @queueStateChange(_verifyPopupApply)
    def _queueSetPluginFilesPath(self):
        value = self.pluginPathData.get()
        if value != self.preferences.general.userPluginPath:
            return partial(self._setPluginFilesPath, value)

    def _setPluginFilesPath(self, value):
        self.preferences.general.userPluginPath = value
        dialog = PluginsFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getPluginFilesPath(self):
        currentDataPath = aPath(self.pluginPathData.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = PluginsFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.pluginPathData.setText(directory[0])

    @queueStateChange(_verifyPopupApply)
    def _queueSetPipesFilesPath(self):
        value = self.userPipesPath.get()
        if value != self.preferences.general.userPipesPath:
            return partial(self._setPipesFilesPath, value)

    def _setPipesFilesPath(self, value):
        self.preferences.general.userPipesPath = value
        dialog = PipelineFileDialog(parent=self)
        dialog.initialPath = aPath(value).filepath

    def _getUserPipesPath(self):
        currentDataPath = aPath(self.userPipesPath.text() or '~')
        currentDataPath = currentDataPath if currentDataPath.exists() else aPath('~')
        dialog = PipelineFileDialog(parent=self, acceptMode='select', directory=currentDataPath, _useDirectoryOnly=True)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.userPipesPath.setText(directory[0])
            self._setPipesFilesPath(directory[0])

    @queueStateChange(_verifyPopupApply)
    def _queueChangeLanguage(self, value):
        value = languages[value]
        if value != self.preferences.general.language:
            return partial(self._changeLanguage, value)

    def _changeLanguage(self, value):
        self.preferences.general.language = value

    @queueStateChange(_verifyPopupApply)
    def _queueChangeColourScheme(self, value):
        value = COLOUR_SCHEMES[value]
        if value != self.preferences.general.colourScheme:
            return partial(self._changeColourScheme, value)

    def _changeColourScheme(self, value):
        self.preferences.general.colourScheme = value

    @queueStateChange(_verifyPopupApply)
    def _queueToggleGeneralOptions(self, option, checked):
        """Toggle a general checkbox option in the preferences
        Requires the parameter to be called 'option' so that the decorator gives it a unique name
        in the internal updates dict
        """
        if checked != self.preferences.general[option]:
            # change the enabled state of checkboxes as required
            _enabled = self.aliasEnabledData.get()
            self.aliasLabelsEnabledData.setEnabled(_enabled)
            self.aliasShadeData.setEnabled(_enabled)

            return partial(self._toggleGeneralOptions, option, checked)

    def _toggleGeneralOptions(self, option, checked):
        self.preferences.general[option] = checked

        if option == 'autoBackupEnabled':
            self.application.updateAutoBackup()

    @queueStateChange(_verifyPopupApply)
    def _queueToggleAppearanceOptions(self, option, checked):
        """Toggle a general checkbox option in the preferences
        Requires the parameter to be called 'option' so that the decorator gives it a unique name
        in the internal updates dict
        """
        if checked != self.preferences.appearance[option]:
            return partial(self._toggleAppearanceOptions, option, checked)

    def _toggleAppearanceOptions(self, option, checked):
        self.preferences.appearance[option] = checked

    @queueStateChange(_verifyPopupApply)
    def _queueSetExternalPath(self, external, dim):
        """Queue the change to the correct item in preferences
        """
        if external not in self.preferences.externalPrograms:
            raise RuntimeError(f'{external} not defined')
        if external not in self.externalPaths:
            raise RuntimeError(f'{external} not defined in preferences')

        widgetList = self.externalPaths[external]
        try:
            extPath, extButton, extTestButton = widgetList

            value = extPath.get()
            oldValue = self.preferences.externalPrograms[external]
            if value != oldValue:
                extTestButton.setText('test')

                return partial(self._setExternalPath, external, value)

        except Exception as es:
            raise RuntimeError(f'{external} does not contain the correct widgets {es}')

    def _setExternalPath(self, external, value):
        """Set the path in preferences
        """
        if 'externalPrograms' in self.preferences and external in self.preferences.externalPrograms:
            self.preferences.externalPrograms[external] = value

    def _getExternalPath(self, external):
        """Get the correct path from preferences
        """
        # NOTE:ED - native dialog on OSX does not show contents of an .app dir.

        if external not in self.preferences.externalPrograms:
            raise RuntimeError(f'{external} not defined')
        if external not in self.externalPaths:
            raise RuntimeError(f'{external} not defined in preferences')

        widgetList = self.externalPaths[external]
        try:
            extPath, _, _ = widgetList

            value = extPath.get()
            dialog = ExecutablesFileDialog(parent=self, acceptMode='select', directory=str(value))
            dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
            dialog._show()
            file = dialog.selectedFile()
            if file:
                extPath.setText(file)

        except Exception as es:
            raise RuntimeError(f'{external} does not contain the correct widgets')

    @queueStateChange(_verifyPopupApply)
    def _queueSetAutoBackupFrequency(self):
        textFromValue = self.autoBackupFrequencyData.textFromValue
        value = self.autoBackupFrequencyData.get()
        prefValue = textFromValue(self.preferences.general.autoBackupFrequency)
        if textFromValue(value) != prefValue:
            return partial(self._setAutoBackupFrequency, value)

    def _setAutoBackupFrequency(self, value):
        self.preferences.general.autoBackupFrequency = value
        self.application.updateAutoBackup()

    @queueStateChange(_verifyPopupApply)
    def _queueSetRegionPadding(self):
        textFromValue = self.regionPaddingData.textFromValue
        value = self.regionPaddingData.get()
        prefValue = textFromValue(100 * self.preferences.general.stripRegionPadding)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setRegionPadding, 0.01 * value)

    def _setRegionPadding(self, value):
        self.preferences.general.stripRegionPadding = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetDropFactor(self):
        textFromValue = self.dropFactorData.textFromValue
        value = self.dropFactorData.get()
        prefValue = textFromValue(100 * self.preferences.general.peakDropFactor)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setDropFactor, 0.01 * value)

    def _setDropFactor(self, value):
        self.preferences.general.peakDropFactor = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetDropFactor1D(self):
        value = self.peakFactor1D.get()
        return partial(self._set1DPeakFactor, value)

    def _set1DPeakFactor(self, value):
        self.preferences.general.peakFactor1D = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetSymbolSizePixel(self):
        value = self.symbolSizePixelData.get()
        if value != self.preferences.general.symbolSizePixel:
            return partial(self._setSymbolSizePixel, value)

    def _setSymbolSizePixel(self, value):
        """Set the size of the symbols (pixels)
        """
        self.preferences.general.symbolSizePixel = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetSymbolThickness(self):
        value = self.symbolThicknessData.get()
        if value != self.preferences.general.symbolThickness:
            return partial(self._setSymbolThickness, value)

    def _setSymbolThickness(self, value):
        """Set the Thickness of the peak symbols (ppm)
        """
        self.preferences.general.symbolThickness = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetContourThickness(self):
        value = self.contourThicknessData.get()
        if value != self.preferences.general.contourThickness:
            return partial(self._setContourThickness, value)

    def _setContourThickness(self, value):
        """Set the Thickness of the peak contours (ppm)
        """
        self.preferences.general.contourThickness = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAliasShade(self):
        value = int(self.aliasShadeData.get())
        if value != self.preferences.general.aliasShade:
            return partial(self._setAliasShade, value)

    def _setAliasShade(self, value):
        """Set the aliased peaks Shade 0.0->1.0; 0.0 is invisible
        """
        self.preferences.general.aliasShade = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetXUnits(self):
        value = self.xAxisUnitsData.getIndex()
        if value != self.preferences.general.xAxisUnits:
            return partial(self.setXAxisUnits, value)

    def setXAxisUnits(self, value):
        """Set the xAxisUnits
        """
        self.preferences.general.xAxisUnits = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetYUnits(self):
        value = self.yAxisUnitsData.getIndex()
        if value != self.preferences.general.yAxisUnits:
            return partial(self.setYAxisUnits, value)

    def setYAxisUnits(self, value):
        """Set the yAxisUnits
        """
        self.preferences.general.yAxisUnits = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetZPlaneNavigationMode(self):
        value = self.zPlaneNavigationModeData.getIndex()
        if value != self.preferences.general.zPlaneNavigationMode:
            return partial(self._setZPlaneNavigationMode, value)

    def _setZPlaneNavigationMode(self, value):
        """Set the zPlaneNavigationMode
        """
        self.preferences.general.zPlaneNavigationMode = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAspectRatioMode(self):
        value = self.aspectRatioModeData.getIndex()
        if value != self.preferences.general.aspectRatioMode:
            return partial(self._setAspectRatioMode, value)

    def _setAspectRatioMode(self, value):
        """Set the aspectRatioMode
        """
        self.preferences.general.aspectRatioMode = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAnnotations(self):
        value = self.annotationsData.getIndex()
        if value != self.preferences.general.annotationType:
            return partial(self._setAnnotations, value)

    def _setAnnotations(self, value):
        """Set the annotation type for the pid labels
        """
        self.preferences.general.annotationType = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetSymbol(self):
        value = self.symbol.getIndex()
        if value != self.preferences.general.symbolType:
            return partial(self._setSymbol, value)

    def _setSymbol(self, value):
        """Set the peak symbol type - current a cross or lineWidths
        """
        self.preferences.general.symbolType = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetStripArrangement(self):
        value = self.stripArrangementButtons.getIndex()
        if value != self.preferences.general.stripArrangement:
            return partial(self._setStripArrangement, value)

    def _setStripArrangement(self, value):
        """Set the stripArrangement
        """
        self.preferences.general.stripArrangement = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetZoomCentre(self):
        value = self.zoomCentre.getIndex()
        if value != self.preferences.general.zoomCentreType:
            return partial(self._setZoomCentre, value)

    def _setZoomCentre(self, value):
        """Set the zoom centring method to either mouse position or centre of the screen
        """
        self.preferences.general.zoomCentreType = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetZoomPercent(self):
        textFromValue = self.zoomPercentData.textFromValue
        value = self.zoomPercentData.get()
        prefValue = textFromValue(self.preferences.general.zoomPercent)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setZoomPercent, value)

    def _setZoomPercent(self, value):
        """Set the value for manual zoom
        """
        self.preferences.general.zoomPercent = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetStripWidthZoomPercent(self):
        textFromValue = self.stripWidthZoomPercentData.textFromValue
        value = self.stripWidthZoomPercentData.get()
        prefValue = textFromValue(self.preferences.general.stripWidthZoomPercent)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setStripWidthZoomPercent, value)

    def _setStripWidthZoomPercent(self, value):
        """Set the value for increasing/decreasing width of strips
        """
        self.preferences.general.stripWidthZoomPercent = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetNumSideBands(self):
        textFromValue = self.showSideBandsData.textFromValue
        value = self.showSideBandsData.get()
        prefValue = textFromValue(self.preferences.general.numSideBands)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setNumSideBands, value)

    def _setNumSideBands(self, value):
        """Set the value for number of sideband gridlines to display
        """
        self.preferences.general.numSideBands = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetMatchAxisCode(self):
        value = self.matchAxisCode.getIndex()
        if value != self.preferences.general.matchAxisCode:
            return partial(self._setMatchAxisCode, value)

    def _setMatchAxisCode(self, value):
        """Set the matching of the axis codes across different strips
        """
        self.preferences.general.matchAxisCode = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAxisOrderingOptions(self):
        value = self.axisOrderingOptions.getIndex()
        if value != self.preferences.general.axisOrderingOptions:
            return partial(self._setAxisOrderingOptions, value)

    def _setAxisOrderingOptions(self, value):
        """Set the option for the axis ordering of strips when opening a new display
        """
        self.preferences.general.axisOrderingOptions = value

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyPopupApply)
    def _queueChangePeakPicker1dIndex(self):
        value = self.peakPicker1dData.get() or None
        if value != self.preferences.general.peakPicker1d:
            return partial(self._setPeakPicker1d, value)

    def _setPeakPicker1d(self, value):
        """Set the default peak picker for 1d spectra
        """
        self.preferences.general.peakPicker1d = value

    @queueStateChange(_verifyPopupApply)
    def _queueChangePeakPickerNdIndex(self):
        value = self.peakPickerNdData.get() or None
        if value != self.preferences.general.peakPickerNd:
            return partial(self._setPeakPickerNd, value)

    def _setPeakPickerNd(self, value):
        """Set the default peak picker for Nd spectra
        """
        self.preferences.general.peakPickerNd = value

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyPopupApply)
    def _queueSetPeakFittingMethod(self):
        value = PEAKFITTINGDEFAULTS[self.peakFittingMethod.getIndex()]
        if value != self.preferences.general.peakFittingMethod:
            return partial(self._setPeakFittingMethod, value)

    def _setPeakFittingMethod(self, value):
        """Set the matching of the axis codes across different strips
        """
        self.preferences.general.peakFittingMethod = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetAspect(self, aspect, dim):
        """dim is required by the decorator to give a unique id for aspect dim
        """
        textFromValue = self.aspectData[aspect].textFromValue
        value = self.aspectData[aspect].get()
        prefValue = textFromValue(self.preferences.general.aspectRatios[aspect])
        if textFromValue(value) != prefValue:
            return partial(self._setAspect, aspect, value)

    def _setAspect(self, aspect, value):
        """Set the aspect ratio for the axes
        """
        self.preferences.general.aspectRatios[aspect] = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetUseSearchBoxMode(self):
        value = self.useSearchBoxModeBox.get()
        if value != self.preferences.general.searchBoxMode:
            return partial(self._setUseSearchBoxMode, value)

    def _setUseSearchBoxMode(self, value):
        self.preferences.general.searchBoxMode = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetUseSearchBoxDoFit(self):
        value = self.useSearchBoxDoFitBox.get()
        if value != self.preferences.general.searchBoxDoFit:
            return partial(self._setUseSearchBoxDoFit, value)

    def _setUseSearchBoxDoFit(self, value):
        self.preferences.general.searchBoxDoFit = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetSearchBox1d(self, searchBox1d, dim):
        """dim is required by the decorator to give a unique id for searchBox dim
        """
        textFromValue = self.searchBox1dData[searchBox1d].textFromValue
        value = self.searchBox1dData[searchBox1d].get()
        prefValue = textFromValue(self.preferences.general.searchBoxWidths1d[searchBox1d])
        if textFromValue(value) != prefValue:
            return partial(self._setSearchBox1d, searchBox1d, value)

    def _setSearchBox1d(self, searchBox1d, value):
        """Set the searchBox1d width for the axes
        """
        self.preferences.general.searchBoxWidths1d[searchBox1d] = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetSearchBoxNd(self, searchBoxNd, dim):
        """dim is required by the decorator to give a unique id for searchBox dim
        """
        textFromValue = self.searchBoxNdData[searchBoxNd].textFromValue
        value = self.searchBoxNdData[searchBoxNd].get()
        prefValue = textFromValue(self.preferences.general.searchBoxWidthsNd[searchBoxNd])
        if textFromValue(value) != prefValue:
            return partial(self._setSearchBoxNd, searchBoxNd, value)

    def _setSearchBoxNd(self, searchBoxNd, value):
        """Set the searchBoxNd width for the axes
        """
        self.preferences.general.searchBoxWidthsNd[searchBoxNd] = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetIntensityLimit(self):
        textFromValue = self.showIntensityLimitBox.textFromValue
        value = self.showIntensityLimitBox.get()
        prefValue = textFromValue(self.preferences.general.intensityLimit)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setIntensityLimit, value)

    def _setIntensityLimit(self, value):
        """Set the value for the minimum intensity limit
        """
        self.preferences.general.intensityLimit = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetMultipletAveraging(self):
        value = self.multipletAveraging.getIndex()
        if value != self.preferences.general.multipletAveraging:
            return partial(self._setMultipletAveraging, value)

    def _setMultipletAveraging(self, value):
        """Set the multiplet averaging type - normal or weighted
        """
        self.preferences.general.multipletAveraging = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetVolumeIntegralLimit(self):
        textFromValue = self.volumeIntegralLimitData.textFromValue
        value = self.volumeIntegralLimitData.get()
        prefValue = textFromValue(self.preferences.general.volumeIntegralLimit)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setVolumeIntegralLimit, value)

    def _setVolumeIntegralLimit(self, value):
        """Set the value for increasing/decreasing width of strips
        """
        self.preferences.general.volumeIntegralLimit = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetVerifySSL(self):
        value = self.verifySSLBox.get()
        if value != self.preferences.proxySettings.verifySSL:
            return partial(self._setVerifySSL, value)

    def _setVerifySSL(self, value):
        self.preferences.proxySettings.verifySSL = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetUseProxy(self):
        value = self.useProxyBox.get()
        # set the state of the other buttons
        self._setProxyButtons()
        if value != self.preferences.proxySettings.useProxy:
            return partial(self._setUseProxy, value)

    def _setUseProxy(self, value):
        self.preferences.proxySettings.useProxy = value

    @queueStateChange(_verifyPopupApply)
    def _queueUseSystemProxy(self):
        value = self.useSystemProxyBox.get()
        # set the state of the other buttons
        self._setProxyButtons()
        if value != self.preferences.proxySettings.useSystemProxy:
            return partial(self._setUseSystemProxy, value)

    def _setUseSystemProxy(self, value):
        self.preferences.proxySettings.useSystemProxy = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetProxyAddress(self):
        value = self.proxyAddressData.get()
        if value != self.preferences.proxySettings.proxyAddress:
            return partial(self._setProxyAddress, value)

    def _setProxyAddress(self, value):
        self.preferences.proxySettings.proxyAddress = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetProxyPort(self):
        value = self.proxyPortData.get()
        if value != self.preferences.proxySettings.proxyPort:
            return partial(self._setProxyPort, value)

    def _setProxyPort(self, value):
        self.preferences.proxySettings.proxyPort = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetUseProxyPassword(self):
        value = self.useProxyPasswordBox.get()
        # set the state of the other buttons
        self._setProxyButtons()
        if value != self.preferences.proxySettings.useProxyPassword:
            return partial(self._setUseProxyPassword, value)

    def _setUseProxyPassword(self, value):
        self.preferences.proxySettings.useProxyPassword = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetProxyUsername(self):
        value = self.proxyUsernameData.get()
        if value != self.preferences.proxySettings.proxyUsername:
            return partial(self._setProxyUsername, value)

    def _setProxyUsername(self, value):
        self.preferences.proxySettings.proxyUsername = value

    @queueStateChange(_verifyPopupApply)
    def _queueSetProxyPassword(self):
        value = self._userPreferences.encodeValue(str(self.proxyPasswordData.get()))
        if value != self.preferences.proxySettings.proxyPassword:
            return partial(self._setProxyPassword, value)

    def _setProxyPassword(self, value):
        self.preferences.proxySettings.proxyPassword = value

    def _setProxyButtons(self):
        """Enable/disable proxy widgets based on check boxes
        """
        usePW = self.useProxyPasswordBox.get()
        useP = self.useProxyBox.get()
        useSP = False
        usePEnabled = useP and not useSP

        self.proxyAddressData.setEnabled(usePEnabled)
        self.proxyPortData.setEnabled(usePEnabled)
        self.useProxyPasswordBox.setEnabled(usePEnabled)
        self.proxyUsernameData.setEnabled(usePEnabled and usePW)
        self.proxyPasswordData.setEnabled(usePEnabled and usePW)

    @queueStateChange(_verifyPopupApply)
    def _queueApplyToSpectrumDisplays(self, option, checked):
        """Toggle a general checkbox option in the preferences
        Requires the parameter to be called 'option' so that the decorator gives it a unique name
        in the internal updates dict
        - not sure whether needed now
        """
        if checked != self.preferences.general[option]:
            return partial(self._toggleGeneralOptions, option, checked)

    @queueStateChange(_verifyPopupApply)
    def _queueSetFont(self, dim):
        _fontAttr = getattr(self, FONTDATAFORMAT.format(dim))
        value = _fontAttr._fontString
        if value != self.preferences.appearance[FONTPREFS.format(dim)]:
            return partial(self._setFont, dim, value)

    def _setFont(self, dim, value):
        self.preferences.appearance[FONTPREFS.format(dim)] = value

    def _getFont(self, dim, fontName):
        # Simple font grabber from the system
        _fontAttr = getattr(self, FONTDATAFORMAT.format(dim))
        value = _fontAttr._fontString
        _font = QtGui.QFont()
        _font.fromString(value)
        newFont, ok = QtWidgets.QFontDialog.getFont(_font, caption='Select {} Font'.format(fontName))
        if ok:
            self.setFontText(_fontAttr, newFont.toString())
            # add the font change to the apply queue
            self._queueSetFont(dim)

    @queueStateChange(_verifyPopupApply)
    def _queueChangeGLFontSize(self, value):
        value = int(self.glFontSizeData.getText() or str(GLFONT_DEFAULTSIZE))
        if value != self.preferences.appearance.spectrumDisplayFontSize:
            return partial(self._changeGLFontSize, value)

    def _changeGLFontSize(self, value):
        self.preferences.appearance.spectrumDisplayFontSize = value
