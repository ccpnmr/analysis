"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import ccpn.util.Colour as Colour
from functools import partial
from ccpn.ui.gui.widgets.MessageDialog import MessageDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.popups.Dialog import handleDialogApply, CcpnDialogMainWidget
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.lib.ContextManagers import undoStackBlocking, queueStateChange
from ccpn.core.PMIListABC import MERITENABLED, MERITTHRESHOLD, \
    SYMBOLCOLOUR, TEXTCOLOUR, LINECOLOUR, MERITCOLOUR
from ccpn.ui.gui.popups.PreferencesPopup import _verifyApply
from ccpn.util.AttrDict import AttrDict


BUTTONOPTIONS1 = (SYMBOLCOLOUR, TEXTCOLOUR, LINECOLOUR, None)
BUTTONOPTIONS2 = (None, None, None, MERITCOLOUR)
BUTTONOPTIONS = tuple(b1 or b2 for b1, b2 in zip(BUTTONOPTIONS1, BUTTONOPTIONS2))


class PMIListPropertiesPopupABC(CcpnDialogMainWidget):
    """Abstract Base Class for popups for Peak/Multiplet/Integral
    """

    # class of list type
    _baseClass = None
    _symbolColourOption = False
    _textColourOption = False
    _lineColourOption = False
    _meritColourOption = False
    _meritOptions = False
    LIVEDIALOG = True

    def __init__(self, parent=None, mainWindow=None, ccpnList=None, title=None, **kwds):
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

        self.ccpnList = ccpnList

        if not self.ccpnList:
            MessageDialog.showWarning(title, 'No %s Found' % self._baseClass.className)
            self.close()

        self.ccpnListViews = self._getListViews(ccpnList)

        self._colourPulldowns = []

        # NOTE: below is not sorted in any way, but if we change that, we also have to change loop in _fillColourPulldown
        self.spectrumColourKeys = list(Colour.spectrumColours.keys())

        row = 0
        self.ccpnListLabel = Label(self.mainWidget, "name ", grid=(row, 0))
        self.ccpnListLabel = Label(self.mainWidget, ccpnList.id, grid=(row, 1))

        # set default colours if not defined
        for colButton, enabled in zip(BUTTONOPTIONS1,
                                      (self._symbolColourOption, self._textColourOption, self._lineColourOption, self._meritColourOption)):
            if colButton and enabled:
                if not getattr(self.ccpnList, colButton, None):
                    setattr(self.ccpnList, colButton, self.spectrumColourKeys[0])

                row += 1
                self._addButtonOption(self._colourPulldowns, colButton, row)

        if self._meritOptions:
            row += 1
            self.meritEnabledLabel = Label(self.mainWidget, text="Use Merit Threshold: ", grid=(row, 0))
            self.meritEnabledBox = CheckBox(self.mainWidget, grid=(row, 1),
                                            checked=getattr(self.ccpnList, MERITENABLED, False))
            self.meritEnabledBox.toggled.connect(self._queueSetMeritEnabled)
            # self.meritEnabledBox.toggled.connect(self._changeSettings)

            row += 1
            self.meritThresholdLabel = Label(self.mainWidget, text=MERITTHRESHOLD, grid=(row, 0))
            self.meritThresholdData = DoubleSpinbox(self.mainWidget, grid=(row, 1), hAlign='l', decimals=2, step=0.01, min=0.0, max=1.0)
            self.meritThresholdData.setValue(getattr(self.ccpnList, MERITTHRESHOLD, 0.0))
            self.meritThresholdData.valueChanged.connect(self._queueSetMeritThreshold)
            # self.meritThresholdData.valueChanged.connect(self._changeSettings)

            # set default colours if not defined
            for colButton, enabled in zip(BUTTONOPTIONS2,
                                          (self._symbolColourOption, self._textColourOption, self._lineColourOption, self._meritColourOption)):
                if colButton and enabled:
                    if not getattr(self.ccpnList, colButton, None):
                        setattr(self.ccpnList, colButton, self.spectrumColourKeys[0])

                    row += 1
                    self._addButtonOption(self._colourPulldowns, colButton, row)

        # set the next available row for inserting new items from subclass
        self._rowForNewItems = row + 1

        # row += 10
        # self.closeButton = Button(self.mainWidget, text='Close', grid=(row, 1), callback=self._accept)

        self.GLSignals = GLNotifier(parent=self)

        self.setOkButton(callback=self._okClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        self._getSettings()

        self._changes = {}
        self._currentNumApplies = 0

        self.COMPARELIST = AttrDict(self.listViewSettings)

    def __postInit__(self):
        """post initialise functions - required as may need to insert more objects into dialog
        """
        self._setButtons()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)
        self._cancelButton = self.dialogButtons.button(self.CANCELBUTTON)
        self._helpButton = self.dialogButtons.button(self.HELPBUTTON)
        self._revertButton = self.dialogButtons.button(self.RESETBUTTON)

        self.setFixedSize(self._size if self._size else self.sizeHint())

    def _addButtonOption(self, pulldowns, attrib, row):
        """Add a labelled pulldown list for the selected attribute
        """
        _colourLabel = Label(self.mainWidget, '%s' % attrib, grid=(row, 0))
        _colourPulldownList = PulldownList(self.mainWidget, grid=(row, 1))
        Colour.fillColourPulldown(_colourPulldownList, allowAuto=True)

        pulldowns.append((_colourLabel, _colourPulldownList, attrib))
        c = getattr(self.ccpnList, attrib, None)
        if c in self.spectrumColourKeys:
            _colourPulldownList.setCurrentText(Colour.spectrumColours[c])
        else:
            Colour.addNewColourString(c)
            for item in pulldowns:
                _, pl, _ = item
                Colour.fillColourPulldown(pl, allowAuto=True)
            Colour.selectPullDownColour(_colourPulldownList, c, allowAuto=True)

        _colourPulldownList.activated.connect(partial(self._queueSetColour, _colourPulldownList, attrib, row))
        # _colourPulldownList.activated.connect(self._changeSettings)

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
        print('>>>_setWidgetSettings')
        for item in self._colourPulldowns:
            _, pl, attrib = item

            c = self.listViewSettings[attrib]
            if c in self.spectrumColourKeys:
                pl.setCurrentText(Colour.spectrumColours[c])
            else:
                Colour.addNewColourString(c)
                for item in self._colourPulldowns:
                    _, pl, _ = item
                    Colour.fillColourPulldown(pl, allowAuto=True)
                Colour.selectPullDownColour(pl, c, allowAuto=True)

        self.meritEnabledBox.setChecked(self.listViewSettings[MERITENABLED] or False)
        self.meritThresholdData.setValue(self.listViewSettings[MERITTHRESHOLD] or 0.0)

    def _setListViewFromWidgets(self):
        """Set listView object from the widgets
        """
        print('>>>_setListViewFromWidgets')
        for item in self._colourPulldowns:
            _, pl, attrib = item

            value = pl.currentText()
            colour = Colour.getSpectrumColour(value, defaultReturn='#')
            setattr(self.ccpnList, attrib, colour)

        meritEnabled = self.meritEnabledBox.isChecked()
        setattr(self.ccpnList, MERITENABLED, meritEnabled)
        meritThreshold = self.meritThresholdData.get()
        setattr(self.ccpnList, MERITTHRESHOLD, meritThreshold)

    def _setListViewFromSettings(self):
        """Set listView object from the original settings dict
        """
        print('>>>_setListViewFromSettings')
        for item in self._colourPulldowns:
            _, pl, attrib = item

            colour = self.listViewSettings[attrib]
            setattr(self.ccpnList, attrib, colour)

        setattr(self.ccpnList, MERITENABLED, self.listViewSettings[MERITENABLED])
        setattr(self.ccpnList, MERITTHRESHOLD, self.listViewSettings[MERITTHRESHOLD])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _changeSettings(self):
        """Widgets have been changed in the dialog
        """
        print('>>>_changeSettings')
        with undoStackBlocking():
            self._setListViewFromWidgets()

        # redraw the items
        self._refreshGLItems()

    def _applyAllChanges(self, changes):
        """Execute the Apply/OK functions
        """
        for v in changes.values():
            v()

    def _applyChanges(self):
        """The Apply/OK button has been clicked.
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        # allChanges = True if self._changes else False
        # if not allChanges:
        #     return True

        print('>>>_applyChanges')
        with handleDialogApply(self) as error:
            # add item here to redraw items
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=self._refreshGLItems)

            self._setListViewFromWidgets()

            # add item here to redraw items
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=self._refreshGLItems)

            # redraw the items
            self._refreshGLItems()

        return error.errorValue is None

    def _refreshGLItems(self):
        """emit a signal to rebuild all list items
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _getListViews(self, ccpnList):
        """Return the listViews containing this list
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _okClicked(self):
        """Accept the dialog and disconnect all signals
        """
        # for (_, pl, _) in self._colourPulldowns:
        #     pl.activated.disconnect(self._changeSettings)

        with undoStackBlocking():
            # reset so the apply works correctly for undo/redo
            self._setListViewFromSettings()

        # # reset object to pre values - for ok to work
        # with self.blockWidgetSignals():
        #     # populate widgets from settings
        #     self._setWidgetSettings()
        #     self._setListViewFromWidgets()

        self._applyChanges()
        self.accept()

    def _cancelClicked(self):
        self._revertClicked()
        self.reject()

    def _revertClicked(self):
        print('>>>_revertClicked')
        with undoStackBlocking():
            self._setListViewFromSettings()

        with self.blockWidgetSignals():
            # populate widgets from settings
            self._setWidgetSettings()

        # redraw the items
        self._refreshGLItems()
        self._changes = {}

        self._revertButton.setEnabled(False)

    def _helpClicked(self):
        pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyApply)
    def _queueSetColour(self, pl, attrib, dim):
        value = pl.currentText()
        colour = Colour.getSpectrumColour(value, defaultReturn='#')
        if colour != getattr(self.COMPARELIST, attrib, None):
            return partial(self._setColour, attrib, colour)

    def _setColour(self, attrib, value):
        setattr(self.ccpnList, attrib, value)

    @queueStateChange(_verifyApply)
    def _queueSetMeritEnabled(self):
        value = self.meritEnabledBox.get()
        if value != getattr(self.COMPARELIST, MERITENABLED, False):
            return partial(self._setMeritEnabled, value)

    def _setMeritEnabled(self, value):
        setattr(self.ccpnList, MERITENABLED, value)

    @queueStateChange(_verifyApply)
    def _queueSetMeritThreshold(self):
        value = self.meritThresholdData.get()
        # set the state of the other buttons
        textFromValue = self.meritThresholdData.textFromValue
        if textFromValue(value) != textFromValue(getattr(self.COMPARELIST, MERITTHRESHOLD, 0.0)):
            return partial(self._setMeritThreshold, value)

    def _setMeritThreshold(self, value):
        setattr(self.ccpnList, MERITTHRESHOLD, value)

