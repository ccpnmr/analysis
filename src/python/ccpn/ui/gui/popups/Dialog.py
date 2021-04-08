"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-04-08 15:34:41 +0100 (Thu, April 08, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore, QtGui
from contextlib import contextmanager
from ccpn.ui.gui.widgets.Base import Base
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.DialogButtonBox import DialogButtonBox
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.ui.gui.lib.ChangeStateHandler import ChangeDict
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Font import setWidgetFont


def _updateGl(self, spectrumList):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    # # spawn a redraw of the contours
    # for spec in spectrumList:
    #     for specViews in spec.spectrumViews:
    #         specViews.buildContours = True

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


HORIZONTAL = 'horizontal'
VERTICAL = 'vertical'
ORIENTATIONLIST = (HORIZONTAL, VERTICAL)
DEFAULTSPACING = 3
# DEFAULTMARGINS = (24, 8, 24, 18)
GETCHANGESTATE = '_getChangeState'


class CcpnDialogMainWidget(QtWidgets.QDialog, Base):
    """
    Class to handle popup dialogs
    """
    RESETBUTTON = QtWidgets.QDialogButtonBox.Reset
    CLOSEBUTTON = QtWidgets.QDialogButtonBox.Close
    CANCELBUTTON = QtWidgets.QDialogButtonBox.Cancel
    DISCARDBUTTON = QtWidgets.QDialogButtonBox.Discard
    APPLYBUTTON = QtWidgets.QDialogButtonBox.Apply
    OKBUTTON = QtWidgets.QDialogButtonBox.Ok
    HELPBUTTON = QtWidgets.QDialogButtonBox.Help
    DEFAULTBUTTON = CLOSEBUTTON

    REVERTBUTTONTEXT = 'Revert'
    CANCELBUTTONTEXT = 'Cancel'
    CLOSEBUTTONTEXT = 'Close'
    APPLYBUTTONTEXT = 'Apply'
    OKBUTTONTEXT = 'OK'

    # ok button is disabled on __init__ if the revert button has been enabled, requires call to __postInit__
    DISABLEOK = False

    USESCROLLWIDGET = False
    FIXEDWIDTH = True
    FIXEDHEIGHT = True
    ENABLEICONS = False

    EDITMODE = True
    DEFAULTMARGINS = (14, 14, 14, 14)

    # a dict to store any required widgets' states between popups
    _storedState = {}

    def __init__(self, parent=None, windowTitle='', setLayout=False,
                 orientation=HORIZONTAL, size=None, minimumSize=None, **kwds):

        super().__init__(parent)
        Base._init(self, setLayout=setLayout, **kwds)

        if orientation not in ORIENTATIONLIST:
            raise TypeError('orientation not in {}'.format(ORIENTATIONLIST))

        self.setWindowTitle(windowTitle)
        self.setContentsMargins(*self.DEFAULTMARGINS)
        self.getLayout().setSpacing(0)

        self._orientation = orientation
        # get the initial size as a QSize
        try:
            self._size = QtCore.QSize(*size) if size else None
        except Exception as es:
            raise TypeError('bad size {}'.format(size))

        # get the initial size as a QSize
        try:
            self._minimumSize = QtCore.QSize(*minimumSize) if minimumSize else None
        except Exception as es:
            raise TypeError('bad minimumSize {}'.format(size))

        # set up the mainWidget area
        self.mainWidget = Frame(self, setLayout=True, showBorder=False, grid=(0, 0))
        self.mainWidget.setAutoFillBackground(False)

        if self.USESCROLLWIDGET:
            # not resizing correctly on first show

            # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
            # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            # set up a scroll area
            self._scrollArea = ScrollArea(self, setLayout=True, grid=(0, 0))
            self._scrollArea.setWidgetResizable(True)
            self._scrollArea.setWidget(self.mainWidget)
            self._scrollArea.setStyleSheet("""ScrollArea { border: 0px; background: transparent; }""")

        # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self._scrollArea.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self._scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        # Spacer(self, 2, 2, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
        #        grid=(1, 1))

        # self._frameOptionsNested.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)
        # self.mainWidget.getLayout().setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        self.mainWidget.setContentsMargins(0, 0, 0, 0)
        self.mainWidget.getLayout().setSpacing(DEFAULTSPACING)

        self._buttonOptions = {}
        self.dialogButtons = None

        # keep a record of how many times the apply button has been pressed
        self._currentNumApplies = 0

        # clear the changes list
        self._changes = ChangeDict()

        self.setDefaultButton()

        # GST stops a file icon being shown
        self.setWindowFilePath('')
        self.setWindowIcon(QtGui.QIcon())

        _styleSheet = 'QToolTip { font-size: %dpt }' % self.font().pointSize()
        self.setStyleSheet(_styleSheet)

    def __postInit__(self):
        """post initialise functions
        """
        self._setButtons()
        self._setDialogSize()

        if self.getButton(self.OKBUTTON) and self.DISABLEOK:
            self.getButton(self.OKBUTTON).setEnabled(False or not self.EDITMODE)
        if self.getButton(self.APPLYBUTTON):
            self.getButton(self.APPLYBUTTON).setEnabled(False)
        if self.getButton(self.RESETBUTTON):
            self.getButton(self.RESETBUTTON).setEnabled(False)

        # restore the state of any required widgets
        self.restoreWidgetState()

    def _setDialogSize(self):
        """Set the fixed/free dialog size from size or sizeHint
        """
        # get the initial size as a QSize
        try:
            size = self._size if isinstance(self._size, QtCore.QSize) else QtCore.QSize(*self._size) if self._size else None
        except Exception as es:
            raise TypeError('bad size {}'.format(self._size))

        _size = QtCore.QSize(size.width() if size else self.sizeHint().width(),
                             size.height() if size else self.sizeHint().height())

        # get the initial minimumSize as a QSize
        try:
            minimumSize = self._minimumSize if isinstance(self._minimumSize, QtCore.QSize) else QtCore.QSize(*self._minimumSize) if self._minimumSize else None
        except Exception as es:
            raise TypeError('bad minimumSize {}'.format(self._minimumSize))

        _minimumSize = QtCore.QSize(minimumSize.width() if minimumSize else self.sizeHint().width(),
                             minimumSize.height() if minimumSize else self.sizeHint().height())

        # set the fixed sized policies as required
        if self.FIXEDWIDTH:
            self.setFixedWidth(_size.width())
        elif minimumSize:
            # set minimumSize from settings
            self.setMinimumWidth(_minimumSize.width())
        
        if self.FIXEDHEIGHT:
            self.setFixedHeight(_size.height())
        elif minimumSize:
            # set minimumSize from settings
            self.setMinimumHeight(_minimumSize.height())

        self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed if self.FIXEDWIDTH else QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Fixed if self.FIXEDHEIGHT else QtWidgets.QSizePolicy.Preferred, )
        self.resize(_size)

    def setOkButton(self, callback=None, text=None,
                    tipText='Apply changes and close',
                    icon='icons/dialog-apply.png',
                    enabled=True, visible=True):
        """Add an Ok button to the dialog box
        """
        return self._addButton(buttons=self.OKBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setCloseButton(self, callback=None, text=None,
                       tipText='Keep all applied changes and close',
                       icon='icons/window-close',
                       enabled=True, visible=True):
        """Add a Close button to the dialog box
        """
        return self._addButton(buttons=self.CLOSEBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setCancelButton(self, callback=None, text=None,
                        tipText='Roll-back all applied changes and close',
                        icon='icons/window-close',
                        enabled=True, visible=True):
        """Add a Cancel button to the dialog box
        """
        return self._addButton(buttons=self.CANCELBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setRevertButton(self, callback=None, text='Revert',
                        tipText='Roll-back all applied changes',
                        icon='icons/undo',
                        enabled=True, visible=True):
        """Add a Revert button to the dialog box
        """
        self.DISABLEOK = True
        return self._addButton(buttons=self.RESETBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setHelpButton(self, callback=None, text=None,
                      tipText='Help',
                      icon='icons/system-help',
                      enabled=True, visible=True):
        """Add a Help button to the dialog box
        """
        return self._addButton(buttons=self.HELPBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setDiscardButton(self, callback=None, text=None,
                         tipText='Discard changes',
                         icon='icons/orange-apply',
                         enabled=True, visible=True):
        """Add an Apply button to the dialog box
        """
        return self._addButton(buttons=self.DISCARDBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setApplyButton(self, callback=None, text=None,
                       tipText='Apply changes',
                       icon='icons/orange-apply',
                       enabled=True, visible=True):
        """Add an Apply button to the dialog box
        """
        return self._addButton(buttons=self.APPLYBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setUserButton(self, callback=None, text=None,
                      tipText='Apply changes to all spectra',
                      icon='icons/orange-apply',
                      enabled=True, visible=True):
        """Add an Apply button to the dialog box
        """
        return self._addButton(buttons=self.APPLYBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def _addButton(self, **kwds):
        """Add button settings to the buttonList
        """
        if self.dialogButtons:
            raise RuntimeError("Error: cannot add buttons after __init__")

        for k, v in kwds.items():
            if k not in self._buttonOptions:
                self._buttonOptions[k] = (v,)
            else:
                self._buttonOptions[k] += (v,)

    def _setButtons(self):
        """Set the buttons for the dialog
        """
        grid = (1, 0) if self._orientation.startswith('h') else (0, 1)

        self.dialogButtons = DialogButtonBox(self, grid=grid,
                                             orientation=self._orientation,
                                             defaultButton=self._defaultButton,
                                             enableIcons=self.ENABLEICONS,
                                             **self._buttonOptions)
        self.dialogButtons.setContentsMargins(0, 18, 0, 0)

    def setDefaultButton(self, button=CLOSEBUTTON):
        """Set the default dialog button
        """
        self._defaultButton = button

    def getButton(self, buttonName):
        """Get the button from the buttonNames defined in the class
        """
        return self.dialogButtons.button(buttonName)

    def fixedSize(self):
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.sizePolicy.setHorizontalStretch(0)
        self.sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(self.sizePolicy)
        self.setFixedSize(self.maximumWidth(), self.maximumHeight())
        self.setSizeGripEnabled(False)

    def _revertClicked(self):
        """Revert button signal comes here
        Revert (roll-back) the state of the project to before the popup was opened
        """
        if self.project and self.project._undo:
            for undos in range(self._currentNumApplies):
                self.project._undo.undo()

        self._populate()

        if not hasattr(self, GETCHANGESTATE):
            raise RuntimeError('widget {} must have changes defined'.format(self))
        _getChanges = getattr(self, GETCHANGESTATE)
        if not callable(_getChanges):
            raise RuntimeError('changes method for {} not correctly defined'.format(self))

        # get the information from the popup - which must handle its own nested _changes
        _changes = _getChanges()
        if not _changes:
            return
        popup, changeState, applyState, revertState, okButton, applyButton, revertButton, numApplies = _changes

        if popup:
            # disable the required buttons
            if okButton:
                okButton.setEnabled(False or not self.EDITMODE)
            if applyButton:
                applyButton.setEnabled(False)
            if revertButton:
                revertButton.setEnabled(False)

    def _cancelClicked(self):
        """Cancel button signal comes here
        """
        self._revertClicked()
        self.reject()

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

    def _helpClicked(self):
        """Help button signal comes here
        """
        pass

    def _applyAllChanges(self, changes):
        """Execute the Apply/OK functions
        """
        for v in changes.values():
            v()

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

        if self.EDITMODE:
            # get the list of widgets that have been changed - exit if all empty
            allChanges = True if self._changes else False
            if not allChanges:
                return True

        # handle clicking of the Apply/OK button
        with handleDialogApply(self) as error:

            # add item here to redraw items
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=self._refreshGLItems)

            # apply all functions to the object
            changes = self._changes
            if changes or not self.EDITMODE:
                self._applyAllChanges(changes)

            # add item here to redraw items
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=self._refreshGLItems)

            # redraw the items
            self._refreshGLItems()

        # everything has happened - disable the apply button
        if self.dialogButtons.button(self.APPLYBUTTON):
            self.dialogButtons.button(self.APPLYBUTTON).setEnabled(False)

        # check for any errors
        if error.errorValue:
            # repopulate popup on an error
            # self._populate()
            return False

        # remove all changes
        self._changes.clear()

        self._currentNumApplies += 1
        if self.dialogButtons.button(self.RESETBUTTON):
            self.dialogButtons.button(self.RESETBUTTON).setEnabled(True)

        return True

    def accept(self):
        super(CcpnDialogMainWidget, self).accept()

        # store the state of any required widgets
        self.storeWidgetState()

    def _refreshGLItems(self):
        """emit a signal to rebuild any required GL items
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def getActiveTabList(self):
        """Get a list of tabs for calulating the changes to settings
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def storeWidgetState(self):
        """Store the state of any required widgets between popups
        """
        # TO BE SUBCLASSED
        pass

    def restoreWidgetState(self):
        """Restore the state of any required widgets
        """
        # TO BE SUBCLASSED
        pass


class CcpnDialog(QtWidgets.QDialog, Base):
    """
    Class to handle popup dialogs
    """

    REVERTBUTTONTEXT = 'Revert'
    CANCELBUTTONTEXT = 'Cancel'
    CLOSEBUTTONTEXT = 'Close'
    APPLYBUTTONTEXT = 'Apply'
    OKBUTTONTEXT = 'OK'

    def __init__(self, parent=None, windowTitle='', setLayout=False, size=(300, 100), **kwds):

        super().__init__(parent)
        Base._init(self, setLayout=setLayout, **kwds)

        self.setWindowTitle(windowTitle)
        self.setContentsMargins(15, 15, 15, 15)
        self.resize(*size)

        # GST stops a file icon being shown
        self.setWindowFilePath('')
        self.setWindowIcon(QtGui.QIcon())

    def fixedSize(self):
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.sizePolicy.setHorizontalStretch(0)
        self.sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(self.sizePolicy)
        self.setFixedSize(self.maximumWidth(), self.maximumHeight())
        self.setSizeGripEnabled(False)

    def setDefaultButton(self, button):
        if isinstance(button, QtWidgets.QPushButton):
            button.setDefault(True)
            button.setAutoDefault(True)
        else:
            raise TypeError('%s is not a button' % str(button))


def dialogErrorReport(self, undo, es):
    """Show warning popup and check the undo stack for items that need to be culled
    """
    from ccpn.ui.gui.widgets.MessageDialog import showWarning

    showWarning(str(self.windowTitle()), str(es))

    # should only undo if something new has been added to the undo deque
    # may cause a problem as some things may be set with the same values
    # and still be added to the change list, so only undo if length has changed

    # get the name of the class propagating the error
    errorName = str(self.__class__.__name__)

    if undo.newItemsAdded:
        # undo any valid items and clear the stack above the current undo point
        undo.undo()
        undo.clearRedoItems()

        getLogger().debug('>>>Undo.%s._applychanges' % errorName)
    else:
        getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)


@contextmanager
def handleDialogApply(self):
    """Context manager to wrap the apply button for dialogs
    Error trapping is contained inside the undoBlockWithoutSideBar, any error raised is placed in
    the errorValue of the yielded object and a warning popup is raised

    e.g.

        with handleDialogApply(self) as error:
            ...  code block here ...

        if error.errorValue:
            # an error occurred in the code block
    """

    from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

    undo = self.project._undo


    # object to hold the error value
    class errorContent():
        def __init__(self):
            self.errorValue = None


    try:
        # add an undoBlockWithoutSideBar
        with undoBlockWithoutSideBar():

            # transfer control to the calling function
            error = errorContent()
            yield error

    except Exception as es:

        # if an error occurs, report as a warning popup and return error to the calling method
        dialogErrorReport(self, undo, es)
        error.errorValue = es

        # re-raise the error if in debug mode
        if self.application._isInDebugMode:
            raise es


def _verifyPopupApply(self, attributeName, value, *postArgs, **postKwds):
    """Change the state of the apply button based on the changes in the tabs
    """
    if not hasattr(self, GETCHANGESTATE):
        raise RuntimeError('widget {} must have changes defined'.format(self))
    _getChanges = getattr(self, GETCHANGESTATE)
    if not callable(_getChanges):
        raise RuntimeError('changes method for {} not correctly defined'.format(self))

    # _changes must  be a ChangeDict and be enabled to accept changes from the gui
    if not self._changes.enabled:
        return

    # if attributeName is defined use as key to dict to store change functions
    # append postFixes if need to differentiate partial functions
    if attributeName:

        # append the extra parameters to the end of attributeName to give a unique
        # identifier into _changes dict, to differentiate same-name partial functions
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

        getLogger().debug2('>>>attrib %s %s' % (attributeName, self._changes[attributeName] if attributeName in self._changes else 'None'))
        if getattr(self, 'LIVEDIALOG', None):
            self._changeSettings()

    # get the information from the popup - which must handle its own nested _changes
    _changes = _getChanges()
    if not _changes:
        return

    popup, changeState, applyState, revertState, okButton, applyButton, revertButton, numApplies = _changes

    if popup:
        # set button states depending on number of changes - ok button or apply button can be selected
        applyChanges = changeState and applyState
        revertChanges = changeState or revertState
        if okButton:
            okButton.setEnabled(applyChanges or not popup.EDITMODE)
        if applyButton:
            applyButton.setEnabled(applyChanges)
        if revertButton:
            revertButton.setEnabled(revertChanges or numApplies)
