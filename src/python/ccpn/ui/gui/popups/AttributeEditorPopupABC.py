"""
Abstract base class to easily implement a popup to edit attributes of V3 layer objects
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
__dateModified__ = "$dateModified: 2020-01-27 19:23:39 +0000 (Mon, January 27, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from string import whitespace
from functools import partial
from collections import OrderedDict
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange
from ccpn.util.Common import makeIterableList


ATTRGETTER = 0
ATTRSETTER = 1
ATTRSIGNAL = 2
ATTRPRESET = 3


class AttributeEditorPopupABC(CcpnDialogMainWidget):
    """Abstract base class to implement a popup for editing properties
    """
    klass = None  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    # the width of the first column for compound widgets
    hWidth = 100

    EDITMODE = True
    WINDOWPREFIX = 'Edit '

    # get/set-Function have getattr, setattr profile
    # if setFunction is None: display attribute value without option to change value
    # kwds: optional kwds passed to LineEdit constructor

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        """
        Initialise the widget
        """
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        super().__init__(parent, setLayout=True,
                         windowTitle=self.WINDOWPREFIX + self.klass.className, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.obj = obj

        row = 0
        self.edits = {}  # An (attributeName, widgetType) dict

        for attr, attrType, getFunction, setFunction, presetFunction, callback, kwds in self.attributes:
            editable = setFunction is not None
            newWidget = attrType(self.mainWidget, mainWindow=mainWindow, labelText=attr, editable=editable,
                                 grid=(row, 0), fixedWidths=(self.hWidth, None), compoundKwds=kwds)  #, **kwds)

            # remove whitespaces to give the attribute name in the class
            attr = attr.translate({ord(c): None for c in whitespace})

            # connect the signal
            if attrType and attrType.__name__ in CommonWidgetsEdits:
                attrSignalTypes = CommonWidgetsEdits[attrType.__name__][ATTRSIGNAL]

                for attrST in makeIterableList(attrSignalTypes):
                    this = newWidget

                    # iterate through the attributeName to get the signals to connect to (for compound widgets)
                    if attrST:
                        for th in attrST.split('.'):
                            this = getattr(this, th, None)
                            if this is None:
                                break
                        else:
                            if this is not None:
                                this.connect(partial(self._queueSetValue, attr, attrType, getFunction, setFunction, presetFunction, callback, row))

                if callback:
                    newWidget.setCallback(callback=partial(callback, self))

            self.edits[attr] = newWidget

            setattr(self, attr, newWidget)
            row += 1

        # set up the required buttons for the dialog
        self.setOkButton(callback=self._okClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        if self.EDITMODE:
            self.setRevertButton(callback=self._revertClicked, enabled=False)

        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        # clear the changes list
        self._changes = OrderedDict()

        # make the buttons appear
        self._setButtons()

        # populate the widgets
        self._populate()
        self.setFixedSize(self._size if self._size else self.sizeHint())

    def _populate(self):
        """Populate the widgets in the popup
        """
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        for attr, attrType, getFunction, _, _presetFunction, _, _ in self.attributes:
            # remove whitespaces to give the attribute name in the class
            attr = attr.translate({ord(c): None for c in whitespace})

            # populate the widget
            if attr in self.edits and attrType and attrType.__name__ in CommonWidgetsEdits:
                thisEdit = CommonWidgetsEdits[attrType.__name__]
                attrSetter = thisEdit[ATTRSETTER]

                if _presetFunction:
                    # call the preset function for the widget (e.g. populate pulldowns with modified list)
                    _presetFunction(self, self.obj)

                if getFunction and self.EDITMODE:
                    # set the current value
                    value = getFunction(self.obj, attr, None)
                    attrSetter(self.edits[attr], value)

    @queueStateChange(_verifyPopupApply)
    def _queueSetValue(self, attr, attrType, getFunction, setFunction, presetFunction, callback, dim):
        """Queue the function for setting the attribute in the calling object (dim needs to stay for the decorator)
        """
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        if attrType and attrType.__name__ in CommonWidgetsEdits:
            attrGetter = CommonWidgetsEdits[attrType.__name__][ATTRGETTER]
            value = attrGetter(self.edits[attr])

            if getFunction and self.EDITMODE:
                oldValue = getFunction(self.obj, attr, None)
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
