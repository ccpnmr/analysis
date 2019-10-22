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
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from contextlib import contextmanager
from ccpn.ui.gui.widgets.Base import Base
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.DialogButtonBox import DialogButtonBox


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


class CcpnDialogMainWidget(QtWidgets.QDialog, Base):
    """
    Class to handle popup dialogs
    """
    RESETBUTTON = QtWidgets.QDialogButtonBox.Reset
    CLOSEBUTTON = QtWidgets.QDialogButtonBox.Close
    CANCELBUTTON = QtWidgets.QDialogButtonBox.Cancel
    APPLYBUTTON = QtWidgets.QDialogButtonBox.Apply
    OKBUTTON = QtWidgets.QDialogButtonBox.Ok
    HELPBUTTON = QtWidgets.QDialogButtonBox.Help
    DEFAULTBUTTON = CLOSEBUTTON

    def __init__(self, parent=None, windowTitle='', setLayout=False,
                 orientation=HORIZONTAL, size=None, **kwds):

        super().__init__(parent)
        Base._init(self, setLayout=setLayout, **kwds)

        if orientation not in ORIENTATIONLIST:
            raise TypeError('Error: orientation not in %s', ORIENTATIONLIST)

        self.setWindowTitle(windowTitle)
        self.setContentsMargins(15, 15, 15, 15)
        self._orientation = orientation
        self._size = size

        # set up the mainWidget area
        self.mainWidget = Frame(self, setLayout=True, showBorder=False, grid=(0, 0))
        self.mainWidget.setAutoFillBackground(False)
        # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # # set up a scroll area
        # self._scrollArea = ScrollArea(self, setLayout=True, grid=(0, 0))
        # self._scrollArea.setWidgetResizable(True)
        # self._scrollArea.setWidget(self.mainWidget)
        # self._scrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")

        # self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self._scrollArea.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self._scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        self._buttonOptions = {}
        self.dialogButtons = None
        self.setDefaultButton()

    def __postInit__(self):
        """post initialise functions
        """
        self._setButtons()
        self.setFixedSize(self._size if self._size else self.sizeHint())

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
        return self._addButton(buttons=self.RESETBUTTON, callbacks=callback,
                               texts=text, tipTexts=tipText, icons=icon,
                               enabledStates=enabled, visibleStates=visible)

    def setHelpButton(self, callback=None, text='',
                        tipText='Help',
                        icon='icons/system-help',
                        enabled=True, visible=True):
        """Add a Help button to the dialog box
        """
        return self._addButton(buttons=self.HELPBUTTON, callbacks=callback,
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
        grid=(1, 0) if self._orientation.startswith('h') else (0, 1)

        self.dialogButtons = DialogButtonBox(self, grid=grid,
                                             orientation=self._orientation,
                                             defaultButton=self._defaultButton,
                                             **self._buttonOptions)

    def setDefaultButton(self, button=CLOSEBUTTON):
        self._defaultButton = button

    def fixedSize(self):
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.sizePolicy.setHorizontalStretch(0)
        self.sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(self.sizePolicy)
        self.setFixedSize(self.maximumWidth(), self.maximumHeight())
        self.setSizeGripEnabled(False)

    # def setDefaultButton(self, button):
    #     if isinstance(button, QtWidgets.QPushButton):
    #         button.setDefault(True)
    #         button.setAutoDefault(True)
    #     else:
    #         raise TypeError('%s is not a button' % str(button))


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
    Error trapping is contained inside the undoBlock, any error raised is placed in
    the errorValue of the yielded object and a warning popup is raised

    e.g.

        with handleDialogApply(self) as error:
            ...  code block here ...

        if error.errorValue:
            # an error occurred in the code block
    """

    from ccpn.core.lib.ContextManagers import undoBlock

    undo = self.project._undo


    # object to hold the error value
    class errorContent():
        def __init__(self):
            self.errorValue = None


    try:
        # add an undoBlock
        with undoBlock():

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
