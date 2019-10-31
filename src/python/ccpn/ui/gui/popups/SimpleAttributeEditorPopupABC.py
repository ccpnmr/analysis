"""
Abstract base class to easily implement a popup to edit attributes of V3 layer objects
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
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange


class SimpleAttributeEditorPopupABC(CcpnDialogMainWidget):
    """Abstract base class to implement a popup for editing simple properties
    """
    klass = None  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    # get/set-Function have getattr, setattr profile
    # if setFunction is None: display attribute value without option to change value
    # kwds: optional kwds passed to LineEdit constructor

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        """
        Initialise the widget
        """
        super().__init__(parent, setLayout=True,
                         windowTitle='Edit ' + self.klass.className, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.obj = obj

        row = 0
        self.labels = {}    # An (attributeName, Label-widget) dict
        self.edits = {}     # An (attributeName, LineEdit-widget) dict

        for attr, getFunction, setFunction, kwds in self.attributes:
            value = getFunction(self.obj, attr)
            readOnly = setFunction is None
            self.labels[attr] = Label(self.mainWidget, attr, grid=(row, 0))
            self.edits[attr] = LineEdit(self.mainWidget, textAlignment='left', readOnly=readOnly,
                                        vAlign='t', grid=(row, 1), **kwds)

            self.edits[attr].textChanged.connect(partial(self._queueSetValue, attr, getFunction, setFunction, row))

            row += 1

        # set up the required buttons for the dialog
        self.setOkButton(callback=self._okClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        # clear the changes list
        self._changes = {}

        # make the buttons appear
        self._setButtons()

        # populate the widgets
        self._populate()
        self.setFixedSize(self._size if self._size else self.sizeHint())

    def _populate(self):
        for attr, getFunction, _, _ in self.attributes:
            if attr in self.edits:
                value = getFunction(self.obj, attr)
                self.edits[attr].setText(str(value))

    @queueStateChange(_verifyPopupApply)
    def _queueSetValue(self, attr, getFunction, setFunction, dim):
        """Queue the function for setting the attribute in the calling object
        """
        value = self.edits[attr].text()
        oldValue = str(getFunction(self.obj, attr))
        if value != oldValue:
            return partial(self._setValue, attr, setFunction, value)

    def _setValue(self, attr, setFunction, value):
        """Function for setting the attribute, called by _applyAllChanges
        """
        setFunction(self.obj, attr, value)

    def _refreshGLItems(self):
        """emit a signal to rebuild any required GL items
        Not required here
        """
        pass
