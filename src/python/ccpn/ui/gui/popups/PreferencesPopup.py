"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore

import os
from functools import partial
from copy import deepcopy
from math import floor
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit, PasswordEdit
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER, setColourScheme
from ccpn.framework.Translation import languages
from ccpn.ui.gui.popups.Dialog import CcpnDialog, handleDialogApply
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.util.Logging import getLogger
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown, addNewColourString, \
    colourNameNoSpace, _setColourPulldown
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.DialogButtonBox import DialogButtonBox
from ccpn.core.PeakList import GAUSSIANMETHOD, PARABOLICMETHOD
from ccpn.core.MultipletList import MULTIPLETAVERAGINGTYPES
from ccpn.util.UserPreferences import UserPreferences
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraForPreferences
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.core.lib.ContextManagers import queueStateChange, undoStackBlocking


PEAKFITTINGDEFAULTS = [PARABOLICMETHOD, GAUSSIANMETHOD]

# FIXME separate pure GUI to project/preferences properites
# The code sets Gui Parameters assuming that  Preference is not None and has a bunch of attributes.


PulldownListsMinimumWidth = 200
LineEditsMinimumWidth = 195
NotImplementedTipText = 'This option has not been implemented yet'


def _updateSettings(self, newPrefs, updateColourScheme):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    self.application.preferences = newPrefs
    # application preferences updated so re-save
    self.application._savePreferences()

    self._updateDisplay(updateColourScheme)

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


def _verifyApply(self, attributeName, value, *postArgs, **postKwds):
    """Change the state of the apply button based on the changes in the tabs
    """

    # if attributeName is defined use as key to dict to store change functions
    # append postFixes if need to differentiate partial functions
    if attributeName:

        for pf in postArgs:
            if pf is not None:
                attributeName += str(pf)
        for k, pf in sorted(postKwds.items()):
            if pf is not None:
                attributeName += str(pf)
        attributeName += str(id(self))

        if value:
            # store in dict - overwrite as required
            self._changes[attributeName] = value
        else:
            if attributeName in self._changes:
                # delete from dict - empty dict implies no changes
                del self._changes[attributeName]

        print('>>>attrib', attributeName, self._changes[attributeName] if attributeName in self._changes else 'None')

    if self:
        # set button state depending on number of changes
        allChanges = True if self._changes else False
        _button = self.dialogButtons.button(QtWidgets.QDialogButtonBox.Apply)
        if _button:
            _button.setEnabled(allChanges)
        _button = self.dialogButtons.button(QtWidgets.QDialogButtonBox.Reset)
        if _button:
            _button.setEnabled(allChanges or self._currentNumApplies)


class PreferencesPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, preferences=None, title='Preferences', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, size=(300, 100), **kwds)

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

        # keep a record of how many times the apply button has been pressed
        self._currentNumApplies = 0
        self._changes = {}

        self.mainLayout = self.getLayout()
        self._setTabs()

        self.dialogButtons = DialogButtonBox(self, grid=(1, 2), orientation='horizontal',
                                             buttons=(QtWidgets.QDialogButtonBox.Reset,
                                                      QtWidgets.QDialogButtonBox.Close,
                                                      QtWidgets.QDialogButtonBox.Apply,
                                                      QtWidgets.QDialogButtonBox.Ok,
                                                      QtWidgets.QDialogButtonBox.Help),
                                             callbacks=(self._revertClicked, self._closeClicked,
                                                        self._applyClicked, self._okClicked),
                                             texts=['Revert', None, None, None, ''],
                                             tipTexts=['Revert - roll-back all applied changes',
                                                       'Close - keep all applied changes and close',
                                                       'Apply changes',
                                                       'Apply changes and close',
                                                       'Help'],
                                             icons=['icons/undo', 'icons/window-close',
                                                    'icons/orange-apply', 'icons/dialog-apply.png',
                                                    'icons/system-help'],
                                             enabledStates=[False, None, False, None, False],
                                             visibleStates=[None],
                                             defaultButton=QtWidgets.QDialogButtonBox.Close)

        self._applyButton = self.dialogButtons.button(QtWidgets.QDialogButtonBox.Apply)
        self._revertButton = self.dialogButtons.button(QtWidgets.QDialogButtonBox.Reset)

        self._populate()

        self.setFixedWidth(self.sizeHint().width() + 24)

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
        self._applyButton.setEnabled(False)
        self._revertButton.setEnabled(False)

    def _closeClicked(self):
        """Close button signal comes here
        """
        self.reject()

    def _applyClicked(self):
        """Apply button signal comes here
        """
        self._applyChanges()

    def _okClicked(self):
        """OK button signal comes here
        """
        if self._applyChanges() is True:
            self.accept()

    def _applyAllChanges(self, changes):
        """Execute the Apply/OK functions
        """
        for v in changes.values():
            v()

    def _updateDisplay(self, updateColourScheme):

        # for display in self.project.spectrumDisplays:
        #     for strip in display.strips:
        #         strip.peakLabelling = self.preferences.general.annotationType
        #         strip.symbolType = self.preferences.general.symbolType
        #         strip.symbolSize = self.preferences.general.symbolSizePixel
        #
        #         strip.symbolThickness = self.preferences.general.symbolThickness
        #         strip.gridVisible = self.preferences.general.showGrid
        #         strip._contourThickness = self.preferences.general.contourThickness
        #         strip.crosshairVisible = self.preferences.general.showCrosshair

        # checked = self.preferences.general['showToolbar']
        # for spectrumDisplay in self.project.spectrumDisplays:
        #     spectrumDisplay.spectrumUtilToolBar.setVisible(checked)

        if updateColourScheme:
            # change the colour theme
            setColourScheme(self.application.preferences.general.colourScheme)
            self.application.correctColours()

            # colour theme has changed - flag displays to update
            self._updateGui()

        # self.application._savePreferences()

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

            # add an undo item to update settings
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateSettings, self, lastPrefs, _changeColour))

            # remember the new state - between addUndoItems because it may append to the undo stack
            newPrefs = deepcopy(self.preferences)
            _updateSettings(self, newPrefs, _changeColour)

            # add a redo item to update settings
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_updateSettings, self, newPrefs, _changeColour))

            # everything has happened - disable the apply button
            self._applyButton.setEnabled(False)

        # check for any errors
        if error.errorValue:
            # re-populate popup from self.preferences on error
            self._populate()
            return False

        # remove all changes
        self._changes = {}

        self._currentNumApplies += 1
        self._revertButton.setEnabled(True)
        return True

    def _updateGui(self):

        # prompt the GLwidgets to update
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitEvent(triggers=[GLNotifier.GLALLCONTOURS,
                                      GLNotifier.GLALLPEAKS,
                                      GLNotifier.GLALLMULTIPLETS,
                                      GLNotifier.GLPREFERENCES])

    def _setTabs(self):

        """ Creates the tabs as Frame Widget. All the children widgets will go in the Frame.
         Each frame will be the widgets parent.
         Tabs are displayed by the order how appear here. """

        self.tabWidget = Tabs(self, grid=(0, 0), gridSpan=(1, 3))

        ## 1 Tab
        self.generalTabFrame = Frame(self, setLayout=True)
        # self.generalTabFrame.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self.generalTabFrame.setContentsMargins(1, 10, 1, 10)
        self._setGeneralTabWidgets(parent=self.generalTabFrame)
        self.tabWidget.addTab(self.generalTabFrame, 'General')
        # self.generalTabFrame.layout().setSpacing(2)

        ## 2 Tab
        self.spectrumTabFrame = Frame(self, setLayout=True)

        # make a new scroll area for the frame
        self._spectrumTabScrollArea = ScrollArea(self, setLayout=True)
        self._spectrumTabScrollArea.setWidgetResizable(True)
        self._spectrumTabScrollArea.setWidget(self.spectrumTabFrame)
        self.spectrumTabFrame.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self._spectrumTabScrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # these are required to make the background of the tabs the visible
        self._spectrumTabScrollArea.setStyleSheet('ScrollArea { border: 0px; background: transparent; }')
        self.spectrumTabFrame.setAutoFillBackground(False)

        self.spectrumTabFrame.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self.spectrumTabFrame.setContentsMargins(1, 10, 1, 10)  # l,t,r,b

        # populate the frame
        self._setspectrumTabWidgets(parent=self.spectrumTabFrame)
        # self.tabWidget.addTab(self.spectrumTabFrame, 'Spectrum')

        # add the scroll area to the tabs
        self.tabWidget.addTab(self._spectrumTabScrollArea, 'Spectrum')

        # 3 Tab Disabled. # Keep the code for future additions
        self.externalProgramsTabFrame = Frame(self, setLayout=True)
        self.externalProgramsTabFrame.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self.externalProgramsTabFrame.setContentsMargins(1, 10, 1, 10)  # l,t,r,b
        self._setExternalProgramsTabWidgets(parent=self.externalProgramsTabFrame)
        self.tabWidget.addTab(self.externalProgramsTabFrame, 'External Programs')
        # self.externalProgramsTabFrame.layout().setSpacing(2)

    def _setGeneralTabWidgets(self, parent):
        ''' Insert a widget in here to appear in the General Tab  '''

        row = 0

        self.languageLabel = Label(parent, text="Language", grid=(row, 0))
        self.languageBox = PulldownList(parent, grid=(row, 1), hAlign='l')
        self.languageBox.addItems(languages)
        self.languageBox.setMinimumWidth(PulldownListsMinimumWidth)
        # self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
        self.languageBox.currentIndexChanged.connect(self._queueChangeLanguage)

        row += 1
        self.colourSchemeLabel = Label(parent, text="Colour Scheme ", grid=(row, 0))
        self.colourSchemeBox = PulldownList(parent, grid=(row, 1), hAlign='l')
        self.colourSchemeBox.setToolTip('SpectrumDisplay Background only')
        self.colourSchemeBox.setMinimumWidth(PulldownListsMinimumWidth)
        self.colourSchemeBox.addItems(COLOUR_SCHEMES)
        # self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(self.preferences.general.colourScheme))
        self._oldColourScheme = None
        self.colourSchemeBox.currentIndexChanged.connect(self._queueChangeColourScheme)

        row += 1
        self.useNativeFileLabel = Label(parent, text="Use Native File Dialogs: ", grid=(row, 0))
        self.useNativeFileBox = CheckBox(parent, grid=(row, 1))         #, checked=self.preferences.general.useNative)
        self.useNativeFileBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'useNative'))

        row += 1
        self.useNativeWebLabel = Label(parent, text="Use Native Web Browser: ", grid=(row, 0))
        self.useNativeWebBox = CheckBox(parent, grid=(row, 1))         #, checked=self.preferences.general.useNativeWebbrowser)
        self.useNativeWebBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'useNativeWebbrowser'))

        # self._toggleGeneralOptions('useNativeWebbrowser', True)
        self.useNativeWebLabel.setEnabled(False)
        self.useNativeWebBox.setEnabled(False)

        row += 1
        self.autoSaveLayoutOnQuitLabel = Label(parent, text="Auto Save Layout On Quit: ", grid=(row, 0))
        self.autoSaveLayoutOnQuitBox = CheckBox(parent, grid=(row, 1))#,
                                                # checked=self.preferences.general.autoSaveLayoutOnQuit)
        self.autoSaveLayoutOnQuitBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoSaveLayoutOnQuit'))

        row += 1
        self.restoreLayoutOnOpeningLabel = Label(parent, text="Restore Layout On Opening: ", grid=(row, 0))
        self.restoreLayoutOnOpeningBox = CheckBox(parent, grid=(row, 1))#,
                                                  # checked=self.preferences.general.restoreLayoutOnOpening)
        self.restoreLayoutOnOpeningBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'restoreLayoutOnOpening'))

        row += 1
        self.autoBackupEnabledLabel = Label(parent, text="Auto Backup On: ", grid=(row, 0))
        self.autoBackupEnabledBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.autoBackupEnabled)
        self.autoBackupEnabledBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoBackupEnabled'))

        row += 1
        self.autoBackupFrequencyLabel = Label(parent, text="Auto Backup Freq (mins)", grid=(row, 0))
        self.autoBackupFrequencyData = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', min=10, decimals=0, step=10)
        self.autoBackupFrequencyData.setMinimumWidth(LineEditsMinimumWidth)
        # self.autoBackupFrequencyData.setValue(self.preferences.general.autoBackupFrequency)
        self.autoBackupFrequencyData.valueChanged.connect(self._queueSetAutoBackupFrequency)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.userWorkingPathLabel = Label(parent, "User Working Path ", grid=(row, 0), )
        self.userWorkingPathData = PathEdit(parent, grid=(row, 1), hAlign='l')
        self.userWorkingPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.userWorkingPathButton = Button(parent, grid=(row, 2), callback=self._getUserWorkingPath, 
                                            icon='icons/directory', hPolicy='fixed')
        # self.userLayoutsLe.setText(self.preferences.general.get('userLayoutsPath'))
        self.userWorkingPathData.textChanged.connect(self._queueSetUserWorkingPath)

        row += 1
        userLayouts = Label(parent, text="User Predefined Layouts ", grid=(row, 0))
        self.userLayoutsLe = PathEdit(parent, grid=(row, 1), hAlign='l')
        self.userLayoutsLe.setMinimumWidth(LineEditsMinimumWidth)
        self.userLayoutsLeButton = Button(parent, grid=(row, 2), callback=self._getUserLayoutsPath,
                                          icon='icons/directory', hPolicy='fixed')
        # self.userLayoutsLe.setText(self.preferences.general.get('userLayoutsPath'))
        self.userLayoutsLe.textChanged.connect(self._queueSetuserLayoutsPath)

        row += 1
        self.auxiliaryFilesLabel = Label(parent, text="Auxiliary Files Path ", grid=(row, 0))
        self.auxiliaryFilesData = PathEdit(parent, grid=(row, 1), hAlign='l')
        self.auxiliaryFilesData.setMinimumWidth(LineEditsMinimumWidth)
        self.auxiliaryFilesDataButton = Button(parent, grid=(row, 2), callback=self._getAuxiliaryFilesPath,
                                               icon='icons/directory', hPolicy='fixed')
        # self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
        self.auxiliaryFilesData.textChanged.connect(self._queueSetAuxiliaryFilesPath)

        row += 1
        self.macroPathLabel = Label(parent, text="Macro Path", grid=(row, 0))
        self.macroPathData = PathEdit(parent, grid=(row, 1), hAlign='l')
        self.macroPathData.setMinimumWidth(LineEditsMinimumWidth)
        # self.macroPathData.setText(self.preferences.general.userMacroPath)
        self.macroPathDataButton = Button(parent, grid=(row, 2), callback=self._getMacroFilesPath,
                                          icon='icons/directory', hPolicy='fixed')
        self.macroPathData.textChanged.connect(self._queueSetMacroFilesPath)

        row += 1
        self.pluginPathLabel = Label(parent, text="Plugin Path", grid=(row, 0))
        self.pluginPathData = PathEdit(parent, grid=(row, 1), hAlign='l', tipText=NotImplementedTipText)
        self.pluginPathData.setMinimumWidth(LineEditsMinimumWidth)
        # self.pluginPathData.setText(self.preferences.general.userPluginPath)
        self.pluginPathDataButton = Button(parent, grid=(row, 2), callback=self._getPluginFilesPath,
                                           icon='icons/directory', hPolicy='fixed')
        self.pluginPathData.textChanged.connect(self._queueSetPluginFilesPath)

        # TODO enable plugin PathData
        # self.pluginPathData.setDisabled(True)
        # self.pluginPathDataButton.setDisabled(True)

        row += 1
        self.pipesPathLabel = Label(parent, text="Pipes Path", grid=(row, 0), )
        self.pipesPathData = PathEdit(parent, grid=(row, 1), hAlign='l', tipText=NotImplementedTipText)
        self.pipesPathData.setMinimumWidth(LineEditsMinimumWidth)
        # self.pipesPathData.setText(self.preferences.general.userExtensionPath)
        self.pipesPathDataButton = Button(parent, grid=(row, 2), callback=self._getExtensionFilesPath,
                                          icon='icons/directory', hPolicy='fixed')
        self.pipesPathData.textChanged.connect(self._queueSetPipesFilesPath)
        # TODO enable pipes PathData
        self.pipesPathData.setDisabled(True)
        self.pipesPathDataButton.setDisabled(True)

        # row += 1
        # self.annotationsLabel = Label(parent, text="Annotations", grid=(row, 0))
        # try:
        #   annType = self.preferences.general.annotationType
        # except:
        #   annType = 0
        #   self.preferences.general.annotationType = annType
        # self.annotationsData = RadioButtons(parent, texts=['Short', 'Full', 'Pid'],
        #                                                    selectedInd=annType,
        #                                                    callback=self._setAnnotations,
        #                                                    direction='horizontal',
        #                                                    grid=(row, 1), hAlign='l',
        #                                                    tipTexts=None,
        #                                                    )

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.useProxyLabel = Label(parent, text="Use Proxy Settings: ", grid=(row, 0))
        self.useProxyBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.proxySettings.useProxy)
        self.useProxyBox.toggled.connect(self._queueSetUseProxy)

        # row += 1
        # self.useSystemProxyLabel = Label(parent, text="   Use System Proxy for Network: ", grid=(row, 0))
        # self.useSystemProxyBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.proxySettings.useSystemProxy)
        # self.useSystemProxyBox.toggled.connect(self._queueSetUseSystemProxy)

        row += 1
        self.proxyAddressLabel = Label(parent, text="   Web Proxy Server: ", grid=(row, 0), hAlign='l')
        self.proxyAddressData = LineEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyAddressData.setMinimumWidth(LineEditsMinimumWidth)
        # self.proxyAddressData.setText(str(self.preferences.proxySettings.proxyAddress))
        self.proxyAddressData.textEdited.connect(self._queueSetProxyAddress)

        row += 1
        self.proxyPortLabel = Label(parent, text="   Port: ", grid=(row, 0), hAlign='l')
        self.proxyPortData = LineEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyPortData.setMinimumWidth(LineEditsMinimumWidth)
        # self.proxyPortData.setText(str(self.preferences.proxySettings.proxyPort))
        self.proxyPortData.textEdited.connect(self._queueSetProxyPort)

        row += 1
        self.useProxyPasswordLabel = Label(parent, text="   Proxy Server Requires Password: ", grid=(row, 0))
        self.useProxyPasswordBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.proxySettings.useProxyPassword)
        self.useProxyPasswordBox.toggled.connect(self._queueSetUseProxyPassword)

        row += 1
        self.proxyUsernameLabel = Label(parent, text="        Username: ", grid=(row, 0), hAlign='l')
        self.proxyUsernameData = LineEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyUsernameData.setMinimumWidth(LineEditsMinimumWidth)
        # self.proxyUsernameData.setText(str(self.preferences.proxySettings.proxyUsername))
        self.proxyUsernameData.textEdited.connect(self._queueSetProxyUsername)

        row += 1
        self.proxyPasswordLabel = Label(parent, text="        Password: ", grid=(row, 0), hAlign='l')
        self.proxyPasswordData = PasswordEdit(parent, grid=(row, 1), hAlign='l')
        self.proxyPasswordData.setMinimumWidth(LineEditsMinimumWidth)
        # self.proxyPasswordData.setText(self._userPreferences.decodeValue(str(self.preferences.proxySettings.proxyPassword)))
        self.proxyPasswordData.textEdited.connect(self._queueSetProxyPassword)

        # set the enabled state of the proxy settings boxes
        # self._setProxyButtons()

        # row += 1
        Spacer(parent, row, 1,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(row, 0), gridSpan=(row, 1))

    def _populate(self):
        """Populate the widgets in the tabs
        """
        with self.blockWidgetSignals():
            # clear all changes
            self._changes = {}

            self._populateGeneralTab()
            self._populateSpectrumTab()
            self._populateExternalProgramsTab()
            
    def _populateGeneralTab(self):
        """Populate the widgets in the generalTab
        """
        self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
        self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(self.preferences.general.colourScheme))
        self.useNativeFileBox.setChecked(self.preferences.general.useNative)
        self.useNativeWebBox.setChecked(self.preferences.general.useNativeWebbrowser)

        # TODO:ED disabled for testing
        # self._toggleGeneralOptions('useNativeWebbrowser', True)
        self.useNativeWebLabel.setEnabled(False)
        self.useNativeWebBox.setEnabled(False)

        self.autoSaveLayoutOnQuitBox.setChecked(self.preferences.general.autoSaveLayoutOnQuit)
        self.restoreLayoutOnOpeningBox.setChecked(self.preferences.general.restoreLayoutOnOpening)
        self.autoBackupEnabledBox.setChecked(self.preferences.general.autoBackupEnabled)
        self.autoBackupFrequencyData.setValue(self.preferences.general.autoBackupFrequency)
        self.userLayoutsLe.setText(self.preferences.general.userLayoutsPath)
        self.userWorkingPathData.setText(self.preferences.general.userWorkingPath)
        self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
        self.macroPathData.setText(self.preferences.general.userMacroPath)
        self.pluginPathData.setText(self.preferences.general.userPluginPath)

        # TODO enable plugin PathData
        self.pluginPathData.setDisabled(True)
        self.pluginPathDataButton.setDisabled(True)

        self.pipesPathData.setText(self.preferences.general.userExtensionPath)

        # TODO enable pipes PathData
        self.pipesPathData.setDisabled(True)
        self.pipesPathDataButton.setDisabled(True)

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
        self._validateFrame._populate()

        self.regionPaddingData.setValue(float('%.1f' % (100 * self.preferences.general.stripRegionPadding)))
        self.dropFactorData.setValue(float('%.1f' % (100 * self.preferences.general.peakDropFactor)))

        volumeIntegralLimit = self.preferences.general.volumeIntegralLimit
        self.volumeIntegralLimitData.setValue(int(volumeIntegralLimit))
        self.peakFittingMethod.setIndex(PEAKFITTINGDEFAULTS.index(self.preferences.general.peakFittingMethod))
        self.showToolbarBox.setChecked(self.preferences.general.showToolbar)
        self.spectrumBorderBox.setChecked(self.preferences.general.showSpectrumBorder)
        self.showGridBox.setChecked(self.preferences.general.showGrid)
        self.showCrosshairBox.setChecked(self.preferences.general.showCrosshair)
        self.showDoubleCrosshairBox.setChecked(self.preferences.general.showDoubleCrosshair)
        self.showLastAxisOnlyBox.setChecked(self.preferences.general.lastAxisOnly)
        self.matchAxisCode.setIndex(self.preferences.general.matchAxisCode)
        self.axisOrderingOptions.setIndex(self.preferences.general.axisOrderingOptions)
        self.zoomCentre.setIndex(self.preferences.general.zoomCentreType)
        self.zoomPercentData.setValue(int(self.preferences.general.zoomPercent))
        self.stripWidthZoomPercentData.setValue(int(self.preferences.general.stripWidthZoomPercent))

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
            self.aspectData[aspect].valueChanged.connect(partial(self._queueSetAspect, aspect))

        self.showZoomXLimitApplyBox.setChecked(self.preferences.general.zoomXLimitApply)
        self.showZoomYLimitApplyBox.setChecked(self.preferences.general.zoomYLimitApply)
        self.showIntensityLimitBox.setValue(self.preferences.general.intensityLimit)
        self.annotationsData.setIndex(self.preferences.general.annotationType)
        self.symbol.setIndex(self.preferences.general.symbolType)
        self.symbolSizePixelData.setValue(float('%i' % self.preferences.general.symbolSizePixel))
        self.symbolThicknessData.setValue(int(self.preferences.general.symbolThickness))
        self.contourThicknessData.setValue(int(self.preferences.general.contourThickness))
        self.autoCorrectBox.setChecked(self.preferences.general.autoCorrectColours)
        _setColourPulldown(self.marksDefaultColourBox, self.preferences.general.defaultMarksColour)

        multipletAveraging = self.preferences.general.multipletAveraging
        self.multipletAveraging.setIndex(MULTIPLETAVERAGINGTYPES.index(multipletAveraging) if multipletAveraging in MULTIPLETAVERAGINGTYPES else 0)
        self.singleContoursBox.setChecked(self.preferences.general.generateSinglePlaneContours)

    def _populateExternalProgramsTab(self):
        """Populate the widgets in the externalProgramsTab
        """
        self.pymolPath.setText(self.preferences.externalPrograms.pymol)

    def _setspectrumTabWidgets(self, parent):
        """Insert a widget in here to appear in the Spectrum Tab. Parent = the Frame obj where the widget should live
        """

        row = 0
        self.autoSetDataPathLabel = Label(parent, text="Auto Set dataPath: ", grid=(row, 0))
        self.autoSetDataPathBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.autoSetDataPath)
        self.autoSetDataPathBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoSetDataPath'))

        row += 1
        self.userDataPathLabel = Label(parent, "User Data Path", grid=(row, 0), )
        self.userDataPathText = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.userDataPathText.setMinimumWidth(LineEditsMinimumWidth)
        self.userDataPathText.textChanged.connect(self._queueSetUserDataPath)
        # self.userDataPathText.setText(self.preferences.general.dataPath)
        self.userDataPathButton = Button(parent, grid=(row, 2), callback=self._getUserDataPath, icon='icons/directory',
                                     hPolicy='fixed')

        # add validate frame
        row += 1
        self._validateFrame = ValidateSpectraForPreferences(parent, mainWindow=self.mainWindow, spectra=self.project.spectra,
                                                            setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 3))

        self._validateFrame._filePathCallback = self._queueSetValidateFilePath
        self._validateFrame._dataUrlCallback = self._queueSetValidateDataUrl
        self._validateFrame._matchDataUrlWidths = parent
        self._validateFrame._matchFilePathWidths = parent

        # row += 1
        # self._dataUrlData = {}
        # self.userDataPathLabel = Label(parent, "$DATA (user datapath)", grid=(row, 0), )
        # self.userDataPathText = PathEdit(parent, grid=(row, 1), vAlign='t')
        # self.userDataPathText.setMinimumWidth(LineEditsMinimumWidth)
        # self.userDataPathText.textChanged.connect(self._queueSetUserDataPath)
        #
        # # if self.project:
        # #     urls = _findDataUrl(self, 'remoteData')
        # #     if urls and urls[0]:
        # #         self.userDataPathText.setValidator(DataUrlValidator(parent=self.userDataPathText, dataUrl=urls[0]))
        # #         _setUrlData(self, urls[0], self.userDataPathText)
        #
        # self.userDataPathText.setText(self.preferences.general.dataPath)
        # self.userDataPathButton = Button(parent, grid=(row, 2), callback=self._getUserDataPath, icon='icons/directory',
        #                                  hPolicy='fixed')

        row += 1
        self.regionPaddingLabel = Label(parent, text="Spectral Padding (%)", grid=(row, 0))
        self.regionPaddingData = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=0, max=100)
        self.regionPaddingData.setMinimumWidth(LineEditsMinimumWidth)
        # self.regionPaddingData.setValue(float('%.1f' % (100 * self.preferences.general.stripRegionPadding)))
        self.regionPaddingData.valueChanged.connect(self._queueSetRegionPadding)

        row += 1
        self.dropFactorLabel = Label(parent, text="Peak Picking Drop (%)", grid=(row, 0))
        self.dropFactorData = DoubleSpinbox(parent, grid=(row, 1), hAlign='l', decimals=1, step=0.1, min=0, max=100)
        self.dropFactorData.setMinimumWidth(LineEditsMinimumWidth)
        # self.dropFactorData.setValue(float('%.1f' % (100 * self.preferences.general.peakDropFactor)))
        self.dropFactorData.valueChanged.connect(self._queueSetDropFactor)

        row += 1
        volumeIntegralLimit = self.preferences.general.volumeIntegralLimit
        self.volumeIntegralLimitLabel = Label(parent, text="Volume Integral Limit", grid=(row, 0))
        self.volumeIntegralLimitData = DoubleSpinbox(parent, step=0.05, decimals=2,
                                                     min=1.0, max=5.0, grid=(row, 1), hAlign='l')
        # self.volumeIntegralLimitData.setValue(int(volumeIntegralLimit))
        self.volumeIntegralLimitData.setMinimumWidth(LineEditsMinimumWidth)
        self.volumeIntegralLimitData.valueChanged.connect(self._queueSetVolumeIntegralLimit)

        row += 1
        self.peakFittingMethodLabel = Label(parent, text="Peak Region Fitting Method", grid=(row, 0))
        peakFittingMethod = self.preferences.general.peakFittingMethod
        self.peakFittingMethod = RadioButtons(parent, texts=PEAKFITTINGDEFAULTS,
                                              # selectedInd=PEAKFITTINGDEFAULTS.index(peakFittingMethod),
                                              callback=self._queueSetPeakFittingMethod,
                                              direction='h',
                                              grid=(row, 1), hAlign='l',
                                              tipTexts=None,
                                              )

        ### Not fully Tested, Had some issues with $Path routines in setting the path of the copied spectra.
        ###  Needs more testing for different spectra formats etc. Disabled until completion.
        # row += 1
        # self.keepSPWithinProjectTipText = 'Keep a copy of spectra inside the project directory. Useful when changing the original spectra location path'
        # self.keepSPWithinProject = Label(parent, text="Keep a Copy Inside Project: ", grid=(row, 0))
        # self.keepSPWithinProjectBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.keepSpectraInsideProject,
        #                                        tipText=self.keepSPWithinProjectTipText)
        # self.keepSPWithinProjectBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'keepSpectraInsideProject'))

        row += 1
        self.showToolbarLabel = Label(parent, text="Show ToolBar(s): ", grid=(row, 0))
        self.showToolbarBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.showToolbar)
        self.showToolbarBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showToolbar'))

        row += 1
        self.spectrumBorderLabel = Label(parent, text="Show Spectrum Border: ", grid=(row, 0))
        self.spectrumBorderBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.showSpectrumBorder)
        self.spectrumBorderBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showSpectrumBorder'))

        row += 1
        self.showGridLabel = Label(parent, text="Show Grids: ", grid=(row, 0))
        self.showGridBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.showGrid)
        self.showGridBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showGrid'))

        row += 1
        self.showCrosshairLabel = Label(parent, text="Show Crosshairs: ", grid=(row, 0))
        self.showCrosshairBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.showCrosshair)
        self.showCrosshairBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showCrosshair'))

        row += 1
        self.showDoubleCrosshairLabel = Label(parent, text="    - and Double Crosshairs: ", grid=(row, 0))
        self.showDoubleCrosshairBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.showDoubleCrosshair)
        self.showDoubleCrosshairBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showDoubleCrosshair'))

        row += 1
        self.showLastAxisOnlyLabel = Label(parent, text="Share Y Axis: ", grid=(row, 0))
        self.showLastAxisOnlyBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.lastAxisOnly)
        self.showLastAxisOnlyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'lastAxisOnly'))

        row += 1
        self.matchAxisCodeLabel = Label(parent, text="Match Axis Codes", grid=(row, 0))
        # matchAxisCode = self.preferences.general.matchAxisCode
        self.matchAxisCode = RadioButtons(parent, texts=['Atom Type', 'Full Axis Code'],
                                          # selectedInd=matchAxisCode,
                                          callback=self._queueSetMatchAxisCode,
                                          direction='h',
                                          grid=(row, 1), hAlign='l',
                                          tipTexts=None,
                                          )

        row += 1
        self.axisOrderingOptionsLabel = Label(parent, text="Axis Ordering", grid=(row, 0))
        # axisOrderingOptions = self.preferences.general.axisOrderingOptions
        self.axisOrderingOptions = RadioButtons(parent, texts=['Use Spectrum Settings', 'Always Ask'],
                                                # selectedInd=axisOrderingOptions,
                                                callback=self._queueSetAxisOrderingOptions,
                                                direction='h',
                                                grid=(row, 1), hAlign='l',
                                                tipTexts=None,
                                                )

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        # row += 1
        #self.showDoubleCursorLabel = Label(parent, text="Show Double Cursor: ", grid=(row, 0))
        #self.showDoubleCursorBox = CheckBox(parent, grid=(row, 1), tipText=NotImplementedTipText)#, checked=self.preferences.general.showDoubleCursor)
        # TODO enable DoubleCursor
        #self.showDoubleCursorBox.setDisabled(True)
        ## self.showDoubleCursorBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showDoubleCursor'))

        row += 1
        self.zoomCentreLabel = Label(parent, text="Zoom Centre", grid=(row, 0))
        # zoomCentre = self.preferences.general.zoomCentreType
        self.zoomCentre = RadioButtons(parent, texts=['Mouse', 'Screen'],
                                       # selectedInd=zoomCentre,
                                       callback=self._queueSetZoomCentre,
                                       direction='h',
                                       grid=(row, 1), hAlign='l',
                                       tipTexts=None,
                                       )
        # self.zoomCentre.setEnabled(False)

        row += 1
        # zoomPercent = self.preferences.general.zoomPercent
        self.zoomPercentLabel = Label(parent, text="Manual Zoom (%)", grid=(row, 0))
        self.zoomPercentData = DoubleSpinbox(parent, step=1,
                                             min=1, max=100, grid=(row, 1), hAlign='l')
        # self.zoomPercentData.setValue(int(zoomPercent))
        self.zoomPercentData.setMinimumWidth(LineEditsMinimumWidth)
        self.zoomPercentData.valueChanged.connect(self._queueSetZoomPercent)

        row += 1
        # stripWidthZoomPercent = self.preferences.general.stripWidthZoomPercent
        self.stripWidthZoomPercentLabel = Label(parent, text="Strip Width Zoom (%)", grid=(row, 0))
        self.stripWidthZoomPercentData = DoubleSpinbox(parent, step=1,
                                                       min=1, max=100, grid=(row, 1), hAlign='l')
        # self.stripWidthZoomPercentData.setValue(int(stripWidthZoomPercent))
        self.stripWidthZoomPercentData.setMinimumWidth(LineEditsMinimumWidth)
        self.stripWidthZoomPercentData.valueChanged.connect(self._queueSetStripWidthZoomPercent)

        # row += 1
        # self.matchAxisCodeLabel = Label(parent, text="Match Axis Codes", grid=(row, 0))
        # matchAxisCode = self.preferences.general.matchAxisCode
        # self.matchAxisCode = RadioButtons(parent, texts=['Atom Type', 'Full Axis Code'],
        #                                 selectedInd=matchAxisCode,
        #                                 callback=self._setMatchAxisCode,
        #                                 direction='v',
        #                                 grid=(row, 1), hAlign='l',
        #                                 tipTexts=None,
        #                                 )

        # row += 1
        # self.showGridLabel = Label(parent, text="Show Grids: ", grid=(row, 0))
        # self.showGridBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.showGrid)
        # self.showGridBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'showGrid'))
        #
        # row += 1
        # self.showLastAxisOnlyLabel = Label(parent, text="Share Y Axis: ", grid=(row, 0))
        # self.showLastAxisOnlyBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.lastAxisOnly)
        # self.showLastAxisOnlyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'lastAxisOnly'))

        row += 1
        self.lockAspectRatioLabel = Label(parent, text="Aspect Ratios: ", grid=(row, 0))
        # self.lockAspectRatioBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.lockAspectRatio)
        # self.lockAspectRatioBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'lockAspectRatio'))

        row += 1
        self.aspectLabel = {}
        self.aspectData = {}
        self.aspectLabelFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 0))
        self.aspectDataFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 1))

        # for aspect in sorted(self.preferences.general.aspectRatios.keys()):
        #     # aspectValue = self.preferences.general.aspectRatios[aspect]
        #     self.aspectLabel[aspect] = Label(parent, text=aspect, grid=(row, 0), hAlign='r')
        #     self.aspectData[aspect] = ScientificDoubleSpinBox(parent,  #step=1,
        #                                                       min=1, grid=(row, 1), hAlign='l')
        #     # self.aspectData[aspect].setValue(aspectValue)
        #     self.aspectData[aspect].setMinimumWidth(LineEditsMinimumWidth)
        #     self.aspectData[aspect].valueChanged.connect(partial(self._queueSetAspect, aspect))
        #     row += 1

        row += 1
        self.showZoomXLimitApplyLabel = Label(parent, text="Apply Zoom limit to X axis: ", grid=(row, 0))
        self.showZoomXLimitApplyBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.zoomXLimitApply)
        self.showZoomXLimitApplyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'zoomXLimitApply'))

        # self._toggleGeneralOptions('zoomXLimitApply', True)
        # self.showZoomXLimitApplyBox.setChecked(True)
        # self.showZoomXLimitApplyBox.setEnabled(False)

        row += 1
        self.showZoomYLimitApplyLabel = Label(parent, text="Apply Zoom limit to Y axis: ", grid=(row, 0))
        self.showZoomYLimitApplyBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.zoomYLimitApply)
        self.showZoomYLimitApplyBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'zoomYLimitApply'))

        # self._toggleGeneralOptions('zoomYLimitApply', True)
        # self.showZoomYLimitApplyBox.setChecked(True)
        # self.showZoomYLimitApplyBox.setEnabled(False)

        row += 1
        # intensityLimit = self.preferences.general.intensityLimit
        self.showIntensityLimitLabel = Label(parent, text='Minimum Intensity Limit', grid=(row, 0), hAlign='r')
        self.showIntensityLimitBox = ScientificDoubleSpinBox(parent,  #step=1,
                                                             min=1e-6, grid=(row, 1), hAlign='l')
        # self.showIntensityLimitBox.setValue(intensityLimit)
        self.showIntensityLimitBox.setMinimumWidth(LineEditsMinimumWidth)
        self.showIntensityLimitBox.valueChanged.connect(self._queueSetIntensityLimit)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.annotationsLabel = Label(parent, text="Peak Annotations", grid=(row, 0))
        # try:
        #     annType = self.preferences.general.annotationType
        # except:
        #     annType = 0
        #     self.preferences.general.annotationType = annType
        self.annotationsData = RadioButtons(parent, texts=['Short', 'Full', 'Pid', 'Minimal', 'Peak Id'],
                                            # selectedInd=annType,
                                            callback=self._queueSetAnnotations,
                                            direction='horizontal',
                                            grid=(row, 1), hAlign='l',
                                            tipTexts=None,
                                            )
        row += 1
        self.symbolsLabel = Label(parent, text="Symbols", grid=(row, 0))
        # symbol = self.preferences.general.symbolType
        self.symbol = RadioButtons(parent, texts=['Cross', 'lineWidths', 'Filled lineWidths', 'Plus'],
                                   # selectedInd=symbol,
                                   callback=self._queueSetSymbol,
                                   direction='h',
                                   grid=(row, 1), hAlign='l',
                                   tipTexts=None,
                                   )

        row += 1
        self.symbolSizePixelLabel = Label(parent, text="Symbol Size (pixels)", grid=(row, 0))
        self.symbolSizePixelData = DoubleSpinbox(parent, decimals=0, step=1,
                                                 min=2, max=50, grid=(row, 1), hAlign='l')
        self.symbolSizePixelData.setMinimumWidth(LineEditsMinimumWidth)
        # symbolSizePixel = self.preferences.general.symbolSizePixel
        # self.symbolSizePixelData.setValue(float('%i' % symbolSizePixel))
        self.symbolSizePixelData.valueChanged.connect(self._queueSetSymbolSizePixel)

        row += 1
        self.symbolThicknessLabel = Label(parent, text="Symbol Thickness (points)", grid=(row, 0))
        self.symbolThicknessData = Spinbox(parent, step=1,
                                           min=1, max=20, grid=(row, 1), hAlign='l')
        self.symbolThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        # symbolThickness = self.preferences.general.symbolThickness
        # self.symbolThicknessData.setValue(int(symbolThickness))
        self.symbolThicknessData.valueChanged.connect(self._queueSetSymbolThickness)

        row += 1
        self.contourThicknessLabel = Label(parent, text="Contour Thickness (points)", grid=(row, 0))
        self.contourThicknessData = Spinbox(parent, step=1,
                                            min=1, max=20, grid=(row, 1), hAlign='l')
        self.contourThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        # contourThickness = self.preferences.general.contourThickness
        # self.contourThicknessData.setValue(int(contourThickness))
        self.contourThicknessData.valueChanged.connect(self._queueSetContourThickness)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.autoCorrectLabel = Label(parent, text="Autocorrect Colours: ", grid=(row, 0))
        self.autoCorrectBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.autoCorrectColours)
        self.autoCorrectBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'autoCorrectColours'))

        row += 1
        self.marksDefaultColourLabel = Label(parent, text="Default Marks Colour:", grid=(row, 0))
        self.marksDefaultColourBox = PulldownList(parent, grid=(row, 1), vAlign='t')

        # populate colour pulldown and set to the current colour
        fillColourPulldown(self.marksDefaultColourBox, allowAuto=False)
        self.marksDefaultColourBox.currentIndexChanged.connect(self._queueChangeMarksColourIndex)

        # add a colour dialog button
        self.marksDefaultColourButton = Button(parent, grid=(row, 2), vAlign='t', hAlign='l',
                                               icon='icons/colours', hPolicy='fixed')
        self.marksDefaultColourButton.clicked.connect(self._queueChangeMarksColourButton)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.multipletAveragingLabel = Label(parent, text="Multiplet Averaging:", grid=(row, 0))
        # multipletAveraging = self.preferences.general.multipletAveraging
        self.multipletAveraging = RadioButtons(parent, texts=MULTIPLETAVERAGINGTYPES,
                                               # selectedInd=MULTIPLETAVERAGINGTYPES.index(
                                               #         multipletAveraging) if multipletAveraging in MULTIPLETAVERAGINGTYPES else 0,
                                               callback=self._queueSetMultipletAveraging,
                                               direction='h',
                                               grid=(row, 1), hAlign='l',
                                               tipTexts=None,
                                               )

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.singleContoursLabel = Label(parent, text="Generate Single Contours\n   per Plane: ", grid=(row, 0))
        self.singleContoursBox = CheckBox(parent, grid=(row, 1))#, checked=self.preferences.general.generateSinglePlaneContours)
        self.singleContoursBox.toggled.connect(partial(self._queueToggleGeneralOptions, 'generateSinglePlaneContours'))

        # add spacer to stop columns changing width
        row += 1
        Spacer(parent, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 3), gridSpan=(1, 1))

    @queueStateChange(_verifyApply)
    def _queueChangeMarksColourIndex(self, value):
        if value >= 0 and list(spectrumColours.keys())[value] != self.preferences.general.defaultMarksColour:
            return partial(self._changeMarksColourIndex, value)

    def _changeMarksColourIndex(self, value):
        """Change the default maerks colour in the preferences
        """
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.marksDefaultColourBox.currentText()))]
        if newColour:
            self.preferences.general.defaultMarksColour = newColour

    def _queueChangeMarksColourButton(self):
        """set the default marks colour from the colour dialog
        """
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            fillColourPulldown(self.marksDefaultColourBox, allowAuto=False)
            self.marksDefaultColourBox.setCurrentText(spectrumColours[newColour.name()])

    def _setExternalProgramsTabWidgets(self, parent):
        """
        Insert a widget in here to appear in the externalPrograms Tab
        """

        row = 0
        self.pymolPathLabel = Label(parent, "Pymol Path", grid=(row, 0), )
        self.pymolPath = PathEdit(parent, grid=(row, 1), hAlign='l')
        self.pymolPath.setMinimumWidth(LineEditsMinimumWidth)
        self.pymolPath.textChanged.connect(self._queueSetPymolPath)
        # self.pymolPath.setText(self.preferences.externalPrograms.pymol)
        self.pymolPathButton = Button(parent, grid=(row, 2), callback=self._getPymolPath, icon='icons/directory',
                                      hPolicy='fixed')

        self.testPymolPathButton = Button(parent, grid=(row, 3), callback=self._testPymol,
                                          text='test', hPolicy='fixed')

    def _testPymol(self):
        program = self.pymolPath.get()
        if not self._testExternalProgram(program):
            self.sender().setText('Failed')
        else:
            self.sender().setText('Success')

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

    # def _getDataPath(self):
    #     if os.path.exists('/'.join(self.userDataPathText.text().split('/')[:-1])):
    #         currentDataPath = '/'.join(self.userDataPathText.text().split('/')[:-1])
    #     else:
    #         currentDataPath = os.path.expanduser('~')
    #     dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
    #                         preferences=self.preferences.general)
    #     directory = dialog.selectedFiles()
    #     if directory:
    #         self.userDataPathText.setText(directory[0])
    #         self.preferences.general.dataPath = directory[0]
    #
    # def _setDataPath(self):
    #     if self.userDataPathText.isModified():
    #         newPath = self.userDataPathText.text().strip()
    #
    #         self.preferences.general.dataPath = newPath     # do we need this?
    #
    #         dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
    #                 name='standard').findFirstDataUrl(name='remoteData')
    #         dataUrl.url = Implementation.Url(path=newPath)

    @queueStateChange(_verifyApply)
    def _queueSetUserDataPath(self):
        value = self.userDataPathText.get()
        if value != self.preferences.general.dataPath:
            return partial(self._setUserDataPath, value)

    def _setUserDataPath(self, value):
        # newPath = self.userDataPathText.text().strip()
        self.preferences.general.dataPath = value

    def _getUserDataPath(self):
        if os.path.exists(os.path.expanduser(self.userDataPathText.text())):
            currentDataPath = os.path.expanduser(self.userDataPathText.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select User Working File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if directory:
            self.userDataPathText.setText(directory[0])
            # self._setUserDataPath()
            # self.preferences.general.dataPath = directory[0]

    @queueStateChange(_verifyApply)
    def _queueSetUserWorkingPath(self):
        value = self.userWorkingPathData.get()
        if value != self.preferences.general.userWorkingPath:
            return partial(self._setUserWorkingPath, value)

    def _setUserWorkingPath(self, value):
        # newPath = self.userWorkingData.text()
        self.preferences.general.userWorkingPath = value

    def _getUserWorkingPath(self):
        if os.path.exists(os.path.expanduser(self.userWorkingPathData.text())):
            currentDataPath = os.path.expanduser(self.userWorkingPathData.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if directory:
            self.userWorkingData.setText(directory[0])
            # self._setUserWorkingPath()
            # self.preferences.general.userWorkingPath = directory[0]

    @queueStateChange(_verifyApply)
    def _queueSetAuxiliaryFilesPath(self):
        value = self.auxiliaryFilesData.get()
        if value != self.preferences.general.auxiliaryFilesPath:
            return partial(self._setAuxiliaryFilesPath, value)

    def _setAuxiliaryFilesPath(self, value):
        # newPath = self.auxiliaryFilesData.text()
        self.preferences.general.auxiliaryFilesPath = value

    def _getAuxiliaryFilesPath(self):
        if os.path.exists(os.path.expanduser(self.auxiliaryFilesData.text())):
            currentDataPath = os.path.expanduser(self.auxiliaryFilesData.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if directory:
            self.auxiliaryFilesData.setText(directory[0])
            # self._setAuxiliaryFilesPath()
            # self.preferences.general.auxiliaryFilesPath = directory[0]

    @queueStateChange(_verifyApply)
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
        if dim == 0:
            # must be the first dataUrl for the preferences
            # self.preferences.general.dataPath = newUrl
            pass

        # if urlValid:
        self._validateFrame.dataUrlFunc(dataUrl, newUrl)

    @queueStateChange(_verifyApply)
    def _queueSetValidateFilePath(self, spectrum, filePath, dim):
        """Set the new filePath for the spectrum
        dim is required by the decorator to give a unique id for filePath row
        """
        if filePath != spectrum.filePath:
            return partial(self._validateFrame.filePathFunc, spectrum, filePath)

    @queueStateChange(_verifyApply)
    def _queueSetuserLayoutsPath(self):
        value = self.userLayoutsLe.get()
        if value != self.preferences.general.userLayoutsPath:
            return partial(self._setUserLayoutsPath, value)

    def _setUserLayoutsPath(self, value):
        # newPath = self.userLayoutsLe.text()
        self.preferences.general.userLayoutsPath = value

    def _getUserLayoutsPath(self):
        if os.path.exists(os.path.expanduser(self.userLayoutsLe.text())):
            currentDataPath = os.path.expanduser(self.userLayoutsLe.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if len(directory) > 0:
            self.userLayoutsLe.setText(directory[0])
            # self._setuserLayoutsPath()
            # self.preferences.general.userLayoutsPath = directory[0]

    @queueStateChange(_verifyApply)
    def _queueSetMacroFilesPath(self):
        value = self.macroPathData.get()
        if value != self.preferences.general.userMacroPath:
            return partial(self._setMacroFilesPath, value)

    def _setMacroFilesPath(self, value):
        # newPath = self.macroPathData.text()
        self.preferences.general.userMacroPath = value

    def _getMacroFilesPath(self):
        if os.path.exists(os.path.expanduser(self.macroPathData.text())):
            currentDataPath = os.path.expanduser(self.macroPathData.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if len(directory) > 0:
            self.macroPathData.setText(directory[0])
            # self._setMacroFilesPath()
            # self.preferences.general.userMacroPath = directory[0]

    @queueStateChange(_verifyApply)
    def _queueSetPluginFilesPath(self):
        value = self.pluginPathData.get()
        if value != self.preferences.general.userPluginPath:
            return partial(self._setPluginFilesPath, value)

    def _setPluginFilesPath(self, value):
        # newPath = self.pluginPathData.text()
        self.preferences.general.userPluginPath = value

    def _getPluginFilesPath(self):
        if os.path.exists(os.path.expanduser(self.pluginPathData.text())):
            currentDataPath = os.path.expanduser(self.pluginPathData.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if len(directory) > 0:
            self.pluginPathData.setText(directory[0])
            # self._setPluginFilesPath()
            # self.preferences.general.pluginMacroPath = directory[0]

    @queueStateChange(_verifyApply)
    def _queueSetPipesFilesPath(self):
        value = self.pipesPathData.get()
        if value != self.preferences.general.userExtensionPath:
            return partial(self._setPipesFilesPath, value)

    def _setPipesFilesPath(self, value):
        # newPath = self.pipesPathData.text()
        self.preferences.general.userExtensionPath = value

    def _getExtensionFilesPath(self):
        if os.path.exists(os.path.expanduser(self.pipesPathData.text())):
            currentDataPath = os.path.expanduser(self.pipesPathData.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                            preferences=self.preferences.general)
        directory = dialog.selectedFiles()
        if len(directory) > 0:
            self.pipesPathData.setText(directory[0])
            # self._setPipesFilesPath()
            # self.preferences.general.userExtensionPath = directory[0]

    def _setPipesFilesPath(self, value):
        # newPath = self.pipesPathData.text()
        self.preferences.general.userExtensionPath = value

    @queueStateChange(_verifyApply)
    def _queueChangeLanguage(self, value):
        value = languages[value]
        if value != self.preferences.general.language:
            return partial(self._changeLanguage, value)

    def _changeLanguage(self, value):
        self.preferences.general.language = value       #(languages[value])

    @queueStateChange(_verifyApply)
    def _queueChangeColourScheme(self, value):
        value = COLOUR_SCHEMES[value]
        if value != self.preferences.general.colourScheme:
            return partial(self._changeColourScheme, value)

    def _changeColourScheme(self, value):
        # self._oldColourScheme = self.preferences.general.colourScheme
        self.preferences.general.colourScheme = value       #(COLOUR_SCHEMES[value])

    @queueStateChange(_verifyApply)
    def _queueToggleGeneralOptions(self, preference, checked):
        if checked != self.preferences.general[preference]:
            return partial(self._toggleGeneralOptions, preference, checked)

    def _toggleGeneralOptions(self, preference, checked):
        self.preferences.general[preference] = checked
        # if preference == 'showToolbar':
        #     for spectrumDisplay in self.project.spectrumDisplays:
        #         spectrumDisplay.spectrumUtilToolBar.setVisible(checked)
        # elif preference == 'showSpectrumBorder':
        #     for strip in self.project.strips:
        #         for spectrumView in strip.spectrumViews:
        #             spectrumView._setBorderItemHidden(checked)
        if preference == 'autoBackupEnabled':
            self.application.updateAutoBackup()

    @queueStateChange(_verifyApply)
    def _queueSetPymolPath(self):
        value = self.pymolPath.get()
        if 'externalPrograms' in self.preferences:
            if 'pymol' in self.preferences.externalPrograms:
                if value != self.preferences.externalPrograms.pymol:
                    self.testPymolPathButton.setText('test')
                    return partial(self._setPymolPath, value)

    def _setPymolPath(self, value):
        # pymolPath = self.pymolPath.get()
        if 'externalPrograms' in self.preferences:
            if 'pymol' in self.preferences.externalPrograms:
                self.preferences.externalPrograms.pymol = value
        # self.testPymolPathButton.setText('test')

    def _getPymolPath(self):
        dialog = FileDialog(self, text='Select File', preferences=self.preferences.general)
        file = dialog.selectedFile()
        if file:
            self.pymolPath.setText(file)
            # self._setPymolPath()

    @queueStateChange(_verifyApply)
    def _queueSetAutoBackupFrequency(self):
        textFromValue = self.autoBackupFrequencyData.textFromValue
        value = self.autoBackupFrequencyData.get()
        prefValue = textFromValue(self.preferences.general.autoBackupFrequency)
        if textFromValue(value) != prefValue:
            return partial(self._setAutoBackupFrequency, value)

    def _setAutoBackupFrequency(self, value):
        # try:
        #     frequency = int(self.autoBackupFrequencyData.text())
        # except:
        #     return
        self.preferences.general.autoBackupFrequency = value
        self.application.updateAutoBackup()

    @queueStateChange(_verifyApply)
    def _queueSetRegionPadding(self):
        textFromValue = self.regionPaddingData.textFromValue
        value = self.regionPaddingData.get()
        prefValue = textFromValue(100 * self.preferences.general.stripRegionPadding)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setRegionPadding, 0.01 * value)

    def _setRegionPadding(self, value):
        # try:
        #     padding = 0.01 * float(self.regionPaddingData.text())
        # except:
        #     return
        self.preferences.general.stripRegionPadding = value

    @queueStateChange(_verifyApply)
    def _queueSetDropFactor(self):
        textFromValue = self.dropFactorData.textFromValue
        value = self.dropFactorData.get()
        prefValue = textFromValue(100 * self.preferences.general.peakDropFactor)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setDropFactor, 0.01 * value)
        else:
            pass

    def _setDropFactor(self, value):
        # try:
        #     dropFactor = 0.01 * float(self.dropFactorData.text())
        # except:
        #     return
        self.preferences.general.peakDropFactor = value

    @queueStateChange(_verifyApply)
    def _queueSetSymbolSizePixel(self):
        value = self.symbolSizePixelData.get()
        if value != self.preferences.general.symbolSizePixel:
            return partial(self._setSymbolSizePixel, value)

    def _setSymbolSizePixel(self, value):
        """
        Set the size of the symbols (pixels)
        """
        # try:
        #     symbolSizePixel = int(self.symbolSizePixelData.text())
        # except:
        #     return
        self.preferences.general.symbolSizePixel = value

    @queueStateChange(_verifyApply)
    def _queueSetSymbolThickness(self):
        value = self.symbolThicknessData.get()
        if value != self.preferences.general.symbolThickness:
            return partial(self._setSymbolThickness, value)

    def _setSymbolThickness(self, value):
        """
        Set the Thickness of the peak symbols (ppm)
        """
        # try:
        #     symbolThickness = int(self.symbolThicknessData.text())
        # except:
        #     return
        self.preferences.general.symbolThickness = value

    @queueStateChange(_verifyApply)
    def _queueSetContourThickness(self):
        value = self.contourThicknessData.get()
        if value != self.preferences.general.contourThickness:
            return partial(self._setContourThickness, value)

    def _setContourThickness(self, value):
        """
        Set the Thickness of the peak contours (ppm)
        """
        # try:
        #     contourThickness = int(self.contourThicknessData.text())
        # except:
        #     return
        self.preferences.general.contourThickness = value

    # @queueStateChange(_verifyApply)
    # def _queueToggleSpectralOptions(self, preference, checked):
    #     if checked != self.preferences.spectra[preference]:
    #         return partial(self._toggleSpectralOptions, checked)
    #
    # def _toggleSpectralOptions(self, preference, checked):
    #     self.preferences.spectra[preference] = str(checked)

    @queueStateChange(_verifyApply)
    def _queueSetAnnotations(self):
        value = self.annotationsData.getIndex()
        if value != self.preferences.general.annotationType:
            return partial(self._setAnnotations, value)

    def _setAnnotations(self, value):
        """
        Set the annotation type for the pid labels
        """
        # try:
        #     annotationType = self.annotationsData.getIndex()
        # except:
        #     return
        self.preferences.general.annotationType = value

    @queueStateChange(_verifyApply)
    def _queueSetSymbol(self):
        value = self.symbol.getIndex()
        if value != self.preferences.general.symbolType:
            return partial(self._setSymbol, value)

    def _setSymbol(self, value):
        """
        Set the peak symbol type - current a cross or lineWidths
        """
        # try:
        #     symbol = self.symbol.getIndex()
        # except:
        #     return
        self.preferences.general.symbolType = value

    @queueStateChange(_verifyApply)
    def _queueSetZoomCentre(self):
        value = self.zoomCentre.getIndex()
        if value != self.preferences.general.zoomCentreType:
            return partial(self._setZoomCentre, value)

    def _setZoomCentre(self, value):
        """
        Set the zoom centring method to either mouse position or centre of the screen
        """
        # try:
        #     zoomCentre = self.zoomCentre.getIndex()
        # except:
        #     return
        self.preferences.general.zoomCentreType = value

    @queueStateChange(_verifyApply)
    def _queueSetZoomPercent(self):
        textFromValue = self.zoomPercentData.textFromValue
        value = self.zoomPercentData.get()
        prefValue = textFromValue(self.preferences.general.zoomPercent)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setZoomPercent, value)

    def _setZoomPercent(self, value):
        """
        Set the value for manual zoom
        """
        # try:
        #     zoomPercent = float(self.zoomPercentData.text())
        # except:
        #     return
        self.preferences.general.zoomPercent = value

    @queueStateChange(_verifyApply)
    def _queueSetStripWidthZoomPercent(self):
        textFromValue = self.stripWidthZoomPercentData.textFromValue
        value = self.stripWidthZoomPercentData.get()
        prefValue = textFromValue(self.preferences.general.stripWidthZoomPercent)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setStripWidthZoomPercent, value)

    def _setStripWidthZoomPercent(self, value):
        """
        Set the value for increasing/decreasing width of strips
        """
        # try:
        #     stripWidthZoomPercent = float(self.stripWidthZoomPercentData.text())
        # except:
        #     return
        self.preferences.general.stripWidthZoomPercent = value

    @queueStateChange(_verifyApply)
    def _queueSetMatchAxisCode(self):
        value = self.matchAxisCode.getIndex()
        if value != self.preferences.general.matchAxisCode:
            return partial(self._setMatchAxisCode, value)

    def _setMatchAxisCode(self, value):
        """
        Set the matching of the axis codes across different strips
        """
        # try:
        #     matchAxisCode = self.matchAxisCode.getIndex()
        # except:
        #     return
        self.preferences.general.matchAxisCode = value

    @queueStateChange(_verifyApply)
    def _queueSetAxisOrderingOptions(self):
        value = self.axisOrderingOptions.getIndex()
        if value != self.preferences.general.axisOrderingOptions:
            return partial(self._setAxisOrderingOptions, value)

    def _setAxisOrderingOptions(self, value):
        """
        Set the option for the axis ordering of strips when opening a new display
        """
        # try:
        #     axisOrderingOptions = self.axisOrderingOptions.getIndex()
        # except:
        #     return
        self.preferences.general.axisOrderingOptions = value

    @queueStateChange(_verifyApply)
    def _queueSetPeakFittingMethod(self):
        value = PEAKFITTINGDEFAULTS[self.peakFittingMethod.getIndex()]
        if value != self.preferences.general.peakFittingMethod:
            return partial(self._setPeakFittingMethod, value)

    def _setPeakFittingMethod(self, value):
        """
        Set the matching of the axis codes across different strips
        """
        # try:
        #     peakFittingMethod = PEAKFITTINGDEFAULTS[self.peakFittingMethod.getIndex()]
        # except:
        #     return
        self.preferences.general.peakFittingMethod = value

    @queueStateChange(_verifyApply)
    def _queueSetAspect(self, aspect):
        textFromValue = self.aspectData[aspect].textFromValue
        value = self.aspectData[aspect].get()
        prefValue = textFromValue(self.preferences.general.aspectRatios[aspect])
        if textFromValue(value) != prefValue:
            return partial(self._setAspect, aspect, value)

    def _setAspect(self, aspect, value):
        """
        Set the aspect ratio for the axes
        """
        # try:
        #     aspectValue = float(self.aspectData[aspect].text())
        # except Exception as es:
        #     return
        self.preferences.general.aspectRatios[aspect] = value

    @queueStateChange(_verifyApply)
    def _queueSetIntensityLimit(self):
        textFromValue = self.showIntensityLimitBox.textFromValue
        value = self.showIntensityLimitBox.get()
        prefValue = textFromValue(self.preferences.general.intensityLimit)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setIntensityLimit, value)

    def _setIntensityLimit(self, value):
        """
        Set the value for the minimum intensity limit
        """
        # try:
        #     limitValue = float(self.showIntensityLimitBox.text())
        # except Exception as es:
        #     return
        self.preferences.general.intensityLimit = value

    @queueStateChange(_verifyApply)
    def _queueSetMultipletAveraging(self):
        value = self.multipletAveraging.getIndex()
        if value != self.preferences.general.multipletAveraging:
            return partial(self._setMultipletAveraging, value)

    def _setMultipletAveraging(self, value):
        """
        Set the multiplet averaging type - normal or weighted
        """
        # try:
        #     symbol = self.multipletAveraging.getSelectedText()
        # except:
        #     return
        self.preferences.general.multipletAveraging = value

    @queueStateChange(_verifyApply)
    def _queueSetVolumeIntegralLimit(self):
        textFromValue = self.volumeIntegralLimitData.textFromValue
        value = self.volumeIntegralLimitData.get()
        prefValue = textFromValue(self.preferences.general.volumeIntegralLimit)
        if value >= 0 and textFromValue(value) != prefValue:
            return partial(self._setVolumeIntegralLimit, value)

    def _setVolumeIntegralLimit(self, value):
        """
        Set the value for increasing/decreasing width of strips
        """
        # try:
        #     volumeIntegralLimit = float(self.volumeIntegralLimitData.text())
        # except:
        #     return
        self.preferences.general.volumeIntegralLimit = value

    @queueStateChange(_verifyApply)
    def _queueSetUseProxy(self):
        value = self.useProxyBox.get()
        # set the state of the other buttons
        self._setProxyButtons()
        if value != self.preferences.proxySettings.useProxy:
            return partial(self._setUseProxy, value)

    def _setUseProxy(self, value):
        # try:
        #     value = self.useProxyBox.isChecked()
        # except:
        #     return
        self.preferences.proxySettings.useProxy = value
        # set the state of the other buttons
        # self._setProxyButtons()

    @queueStateChange(_verifyApply)
    def _queueUseSystemProxy(self):
        value = self.useSystemProxyBox.get()
        # set the state of the other buttons
        self._setProxyButtons()
        if value != self.preferences.proxySettings.useSystemProxy:
            return partial(self._setUseSystemProxy, value)

    def _setUseSystemProxy(self, value):
        # try:
        #     value = self.useSystemProxyBox.isChecked()
        # except:
        #     return
        self.preferences.proxySettings.useSystemProxy = value
        # set the state of the other buttons
        # self._setProxyButtons()

    @queueStateChange(_verifyApply)
    def _queueSetProxyAddress(self):
        value = self.proxyAddressData.get()
        if value != self.preferences.proxySettings.proxyAddress:
            return partial(self._setProxyAddress, value)

    def _setProxyAddress(self, value):
        # try:
        #     value = str(self.proxyAddressData.text())
        # except:
        #     return
        self.preferences.proxySettings.proxyAddress = value

    @queueStateChange(_verifyApply)
    def _queueSetProxyPort(self):
        value = self.proxyPortData.get()
        if value != self.preferences.proxySettings.proxyPort:
            return partial(self._setProxyPort, value)

    def _setProxyPort(self, value):
        # try:
        #     value = str(self.proxyPortData.text())
        # except:
        #     return
        self.preferences.proxySettings.proxyPort = value

    @queueStateChange(_verifyApply)
    def _queueSetUseProxyPassword(self):
        value = self.useProxyPasswordBox.get()
        # set the state of the other buttons
        self._setProxyButtons()
        if value != self.preferences.proxySettings.useProxyPassword:
            return partial(self._setUseProxyPassword, value)

    def _setUseProxyPassword(self, value):
        # try:
        #     value = self.useProxyPasswordBox.isChecked()
        # except:
        #     return
        self.preferences.proxySettings.useProxyPassword = value
        # set the state of the other buttons
        # self._setProxyButtons()

    @queueStateChange(_verifyApply)
    def _queueSetProxyUsername(self):
        value = self.proxyUsernameData.get()
        if value != self.preferences.proxySettings.proxyUsername:
            return partial(self._setProxyUsername, value)

    def _setProxyUsername(self, value):
        # try:
        #     value = str(self.proxyUsernameData.text())
        # except:
        #     return
        self.preferences.proxySettings.proxyUsername = value

    @queueStateChange(_verifyApply)
    def _queueSetProxyPassword(self):
        value = self._userPreferences.encodeValue(str(self.proxyPasswordData.get()))
        if value != self.preferences.proxySettings.proxyPassword:
            return partial(self._setProxyPassword, value)

    def _setProxyPassword(self, value):
        # try:
        #     value = self._userPreferences.encodeValue(str(self.proxyPasswordData.text()))
        # except:
        #     return
        self.preferences.proxySettings.proxyPassword = value

    def _setProxyButtons(self):
        """Enable/disable proxy widgets based on check boxes
        """
        usePW = self.useProxyPasswordBox.get()          #self.preferences.proxySettings.useProxyPassword
        useP = self.useProxyBox.get()                   #self.preferences.proxySettings.useProxy
        useSP = False
        usePEnabled = useP and not useSP

        # self.useSystemProxyBox.setEnabled(useP)
        self.proxyAddressData.setEnabled(usePEnabled)
        self.proxyPortData.setEnabled(usePEnabled)
        self.useProxyPasswordBox.setEnabled(usePEnabled)
        self.proxyUsernameData.setEnabled(usePEnabled and usePW)
        self.proxyPasswordData.setEnabled(usePEnabled and usePW)
