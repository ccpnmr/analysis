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
__dateModified__ = "$dateModified: 2021-11-09 14:06:37 +0000 (Tue, November 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-04-16 12:14:51 +0000 (Thu, April 16, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
import ccpn.util.Colour as Colour
from functools import partial
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, _verifyPopupApply
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.lib.ContextManagers import undoStackBlocking, queueStateChange, notificationEchoBlocking
from ccpn.core._implementation.PMIListABC import MERITENABLED, MERITTHRESHOLD, \
    SYMBOLCOLOUR, TEXTCOLOUR, LINECOLOUR, MERITCOLOUR
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown
from ccpn.ui.gui.lib.ChangeStateHandler import changeState
from ccpn.ui.gui.popups.AttributeEditorPopupABC import getAttributeTipText
from ccpn.util.Common import stringToCamelCase, camelCaseToString
from ccpn.ui.gui.popups.AttributeEditorPopupABC import _attribContainer


# define two groups of buttons for above/below the merit checkbox
BUTTONOPTIONS1 = (SYMBOLCOLOUR, TEXTCOLOUR, LINECOLOUR, None)
BUTTONOPTIONS2 = (None, None, None, MERITCOLOUR)
BUTTONOPTIONS = tuple(b1 or b2 for b1, b2 in zip(BUTTONOPTIONS1, BUTTONOPTIONS2))


class PMIListPropertiesPopupABC(CcpnDialogMainWidget):
    """Abstract Base Class for popups for Peak/Multiplet/Integral
    """

    klass = None    # The class whose properties are edited/displayed
    attributes = [] # A list of (attributeName, getFunction, setFunction, kwds) tuples;
    # options for displaying colours
    _symbolColourOption = False
    _textColourOption = False
    _lineColourOption = False
    _meritColourOption = False
    _meritOptions = False
    LIVEDIALOG = True           # changes are reflected instantly
    EDITMODE = True

    def __init__(self, parent=None, mainWindow=None, ccpnList=None, spectrum=None, title=None, editMode=None, **kwds):
        """
        Initialise the widget
        """
        if editMode is not None:
            self.EDITMODE = editMode
            self.LIVEDIALOG = editMode
            self.WINDOWPREFIX = 'Edit ' if editMode else 'New '

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if self.mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self.spectrum = spectrum
        if self.EDITMODE:
            self.ccpnList = ccpnList
        else:
            self.ccpnList = self._newContainer()
            self._populateInitialValues()

        if not (self.ccpnList or spectrum):
            showWarning(title, 'No %s Found' % self.klass.className)
            self.close()

        self._colourPulldowns = []

        # add the first row with the name of the listView
        row = 0
        # Label(self.mainWidget, "Name: ", grid=(row, 0))
        # self.ccpnListLabel = Label(self.mainWidget, '<None>', grid=(row, 1))
        # row += 1

        # add initial dialog options as specified by attributes list
        self.labels = {}    # An (attributeName, Label-widget) dict
        self.edits = {}     # An (attributeName, LineEdit-widget) dict

        for _label, getFunction, setFunction, kwds in self.attributes:
            attr = stringToCamelCase(_label)
            tipText = getAttributeTipText(self.klass, attr)

            editable = setFunction is not None
            self.labels[attr] = Label(self.mainWidget, _label, grid=(row, 0))
            self.edits[attr] = LineEdit(self.mainWidget, textAlignment='left', editable=editable,
                                    vAlign='t', grid=(row, 1), **kwds)
            self.edits[attr].textChanged.connect(partial(self._queueSetValue, attr, getFunction, setFunction, row))

            if tipText:
                self.labels[attr].setToolTip(tipText)
            row += 1

        # add first set of default colours as required
        for colButton, enabled in zip(BUTTONOPTIONS1, (self._symbolColourOption, self._textColourOption, self._lineColourOption, self._meritColourOption)):
            if colButton and enabled:
                row += 1
                self._addButtonOption(self._colourPulldowns, colButton, row)

        # add the meritOption buttons
        if self._meritOptions:
            row += 1
            self.meritEnabledLabel = Label(self.mainWidget, text="Use Merit Threshold: ", grid=(row, 0))
            tipText = getAttributeTipText(self.klass, MERITENABLED)
            if tipText:
                self.meritEnabledLabel.setToolTip(tipText)
            self.meritEnabledBox = CheckBox(self.mainWidget, grid=(row, 1), )
            self.meritEnabledBox.toggled.connect(self._queueSetMeritEnabled)

            row += 1
            self.meritThresholdLabel = Label(self.mainWidget, text=camelCaseToString(MERITTHRESHOLD), grid=(row, 0))
            tipText = getAttributeTipText(self.klass, MERITTHRESHOLD)
            if tipText:
                self.meritThresholdLabel.setToolTip(tipText)
            self.meritThresholdData = DoubleSpinbox(self.mainWidget, grid=(row, 1), hAlign='l', decimals=2, step=0.01, min=0.0, max=1.0)
            self.meritThresholdData.valueChanged.connect(self._queueSetMeritThreshold)

            # add second set of default colours as required
            for colButton, enabled in zip(BUTTONOPTIONS2, (self._symbolColourOption, self._textColourOption, self._lineColourOption, self._meritColourOption)):
                if colButton and enabled:
                    row += 1
                    self._addButtonOption(self._colourPulldowns, colButton, row)

        # set the next available row for inserting new items from subclass
        self._rowForNewItems = row + 1

        self.GLSignals = GLNotifier(parent=self)

        self.setOkButton(callback=self._okClicked, enabled=False)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        self.ccpnListViews = self._getListViews(ccpnList)
        self._getSettings()

    def __postInit__(self):
        """post initialise functions - required as may need to insert more objects into dialog
        """
        # add spacer to stop columns changing width
        self._rowForNewItems += 1
        Spacer(self.mainWidget, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(self._rowForNewItems, 3), gridSpan=(1, 1))

        super().__postInit__()

        self._okButton = self.dialogButtons.button(self.OKBUTTON)
        self._cancelButton = self.dialogButtons.button(self.CANCELBUTTON)
        self._helpButton = self.dialogButtons.button(self.HELPBUTTON)
        self._revertButton = self.dialogButtons.button(self.RESETBUTTON)

        self.COMPARELIST = AttrDict(self.listViewSettings)

        self._populate()

    def _populate(self):
        """Populate the widgets from listViewSettings
        """
        # with self.blockWidgetSignals():
        with notificationEchoBlocking():
            with self._changes.blockChanges():
                # populate widgets from settings
                self._setWidgetSettings()

    def _getChangeState(self):
        """Get the change state from the _changes dict
        """
        if not self._changes.enabled:
            return None

        applyState = True
        revertState = False
        allChanges = True if self._changes else False

        return changeState(self, allChanges, applyState, revertState, self._okButton, None, self._revertButton, self._currentNumApplies)

    def _addButtonOption(self, pulldowns, attrib, row):
        """Add a labelled pulldown list for the selected attribute
        """
        _label = camelCaseToString(attrib)
        _colourLabel = Label(self.mainWidget, _label, grid=(row, 0))

        _tipText = getAttributeTipText(self.klass, attrib)
        if _tipText:
            _colourLabel.setToolTip(_tipText)

        _colourPulldownList = PulldownList(self.mainWidget, grid=(row, 1))
        Colour.fillColourPulldown(_colourPulldownList, allowAuto=True, includeGradients=False)
        pulldowns.append((_colourLabel, _colourPulldownList, attrib))
        _colourButton = Button(self.mainWidget, hAlign='l', grid=(row, 2), hPolicy='fixed', #vAlign='t',
                              callback=partial(self._queueSetColourButton, _colourPulldownList), icon='icons/colours')

        _colourPulldownList.currentIndexChanged.connect(partial(self._queueSetColour, _colourPulldownList, attrib, row))

    def _getSettings(self):
        """Fill the settings dict from the listView object
        """
        self.listViewSettings = {}
        for item in self._colourPulldowns:
            _, _, attrib = item

            c = getattr(self.ccpnList, attrib, None)
            self.listViewSettings[attrib] = c

        self.listViewSettings[MERITENABLED] = getattr(self.ccpnList, MERITENABLED, False)
        self.listViewSettings[MERITTHRESHOLD] = getattr(self.ccpnList, MERITTHRESHOLD, 0.0)

    def _setWidgetSettings(self):
        """Populate the widgets from the settings dict
        """
        # self.ccpnListLabel.setText(self.ccpnList.id)
        for _label, getFunction, _, _ in self.attributes:
            attr = stringToCamelCase(_label)

            if getFunction and attr in self.edits:
                value = getFunction(self.ccpnList, attr)
                self.edits[attr].setText(str(value) if value is not None else '')

        # add any new colours that may not be in the colour list
        for item in self._colourPulldowns:
            _, pl, attrib = item

            c = self.listViewSettings[attrib]
            if not Colour.isSpectrumColour(c):
                Colour.addNewColourString(c)

        # set the colours in the pulldowns
        for item in self._colourPulldowns:
            _, pl, attrib = item
            Colour.fillColourPulldown(pl, allowAuto=True, includeGradients=False)

            c = self.listViewSettings[attrib]
            Colour.selectPullDownColour(pl, c, allowAuto=True)

        self.meritEnabledBox.setChecked(self.listViewSettings[MERITENABLED] or False)
        self.meritThresholdData.setValue(self.listViewSettings[MERITTHRESHOLD] or 0.0)

    def _setListViewFromWidgets(self):
        """Set listView object from the widgets
        """
        with notificationEchoBlocking():
            with undoStackBlocking():
                # # apply all functions to the object
                # changes = self._changes
                # if changes: # or not self.EDITMODE:
                #     self._applyAllChanges(changes)

                for item in self._colourPulldowns:
                    _, pl, attrib = item

                    value = pl.currentText()
                    colour = Colour.getSpectrumColour(value, defaultReturn='#')
                    if colour is not None:
                        setattr(self.ccpnList, attrib, colour)

                meritEnabled = self.meritEnabledBox.isChecked()
                setattr(self.ccpnList, MERITENABLED, meritEnabled)
                meritThreshold = self.meritThresholdData.get()
                setattr(self.ccpnList, MERITTHRESHOLD, meritThreshold)

    def _setListViewFromSettings(self):
        """Set listView object from the original settings dict
        """
        with notificationEchoBlocking():
            with undoStackBlocking():
                for item in self._colourPulldowns:
                    _, pl, attrib = item

                    colour = self.listViewSettings[attrib]
                    if colour is not None:
                        setattr(self.ccpnList, attrib, colour)

                if self.listViewSettings[MERITENABLED] is not None:
                    setattr(self.ccpnList, MERITENABLED, self.listViewSettings[MERITENABLED])
                if self.listViewSettings[MERITTHRESHOLD] is not None:
                    setattr(self.ccpnList, MERITTHRESHOLD, self.listViewSettings[MERITTHRESHOLD])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _changeSettings(self):
        """Widgets have been changed in the dialog
        """
        self._setListViewFromWidgets()

        # redraw the items
        self._refreshGLItems()

    def _getListViews(self, ccpnList):
        """Return the listViews containing this list
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _okClicked(self):
        """Accept the dialog and disconnect all signals
        """
        if self._changes or not self.EDITMODE:
            # with undoStackBlocking():
            # reset so the apply works correctly for undo/redo
            self._setListViewFromSettings()
            self._applyChanges()

        self.accept()

    def _revertClicked(self):
        """Handle the revert clicked button
        """
        if self._changes:
            # with notificationEchoBlocking():
            #     with undoStackBlocking():
            self._setListViewFromSettings()
            self._populate()

        # redraw the items
        self._refreshGLItems()
        self._changes.clear()

        # disable the buttons
        self._okButton.setEnabled(False or not self.EDITMODE)
        self._revertButton.setEnabled(False)

    def _helpClicked(self):
        pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fillPullDowns(self):
        for item in self._colourPulldowns:
            _, pl, attrib = item

            fillColourPulldown(pl, allowAuto=False, includeGradients=False)

    @queueStateChange(_verifyPopupApply)
    def _queueSetValue(self, attr, getFunction, setFunction, dim, _value):
        """Queue the function for setting the attribute in the calling object
        """
        value = self.edits[attr].text()
        oldValue = str(getFunction(self.ccpnList, attr))
        if value != oldValue:
            return partial(self._setValue, attr, setFunction, value)

    def _setValue(self, attr, setFunction, value):
        """Function for setting the attribute, called by _applyAllChanges
        """
        setFunction(self.ccpnList, attr, value)

    def _queueSetColourButton(self, pulldown):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            self._fillPullDowns()
            pulldown.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyPopupApply)
    def _queueSetColour(self, pl, attrib, dim, _value):
        """Queue the function for setting a colour attribute
        """
        value = pl.currentText()
        colour = Colour.getSpectrumColour(value, defaultReturn='#')
        if colour != getattr(self.COMPARELIST, attrib, None):
            return partial(self._setColour, attrib, colour)

    def _setColour(self, attrib, value):
        """Function for setting the colour attribute, called by _applyAllChanges
        """
        setattr(self.ccpnList, attrib, value)

    @queueStateChange(_verifyPopupApply)
    def _queueSetMeritEnabled(self, _value):
        """Queue the function for setting merit
        """
        value = self.meritEnabledBox.get()
        if value != getattr(self.COMPARELIST, MERITENABLED, False):
            return partial(self._setMeritEnabled, value)

    def _setMeritEnabled(self, value):
        """Function for setting merit, called by _applyAllChanges
        """
        setattr(self.ccpnList, MERITENABLED, value)

    @queueStateChange(_verifyPopupApply)
    def _queueSetMeritThreshold(self, _value):
        """Queue the function for setting merit threshold
        """
        value = self.meritThresholdData.get()
        # set the state of the other buttons
        textFromValue = self.meritThresholdData.textFromValue
        if textFromValue(value) != textFromValue(getattr(self.COMPARELIST, MERITTHRESHOLD, 0.0) or 0.0):
            return partial(self._setMeritThreshold, value)

    def _setMeritThreshold(self, value):
        """Function for setting merit threshold, called by _applyAllChanges
        """
        setattr(self.ccpnList, MERITTHRESHOLD, value)

    def _newContainer(self):
        """Make a new container to hold attributes for objects not created yet
        """
        return _attribContainer(self)

    def _populateInitialValues(self):
        """Populate the initial values for an empty object
        """
        # add second set of default colours as required
        for colButton, enabled in zip(BUTTONOPTIONS, (self._symbolColourOption, self._textColourOption, self._lineColourOption, self._meritColourOption)):
            if colButton and enabled:
                setattr(self.ccpnList, colButton, '#')
