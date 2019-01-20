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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning

from ccpn.util.Logging import getLogger


class SimpleAttributeEditorPopupABC(CcpnDialog):
    """Abstract base class to implement a popup for editing the name property
    """
    klass = None  # The class whose name property is edited
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;
                     # get/set-Function have getattr, setattr profile
                     # kwds: optional kwds passed to LineEdit

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True,
                            windowTitle='Edit ' + self.klass.className, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.obj = obj

        row = 0
        self.labels = {}
        self.edits = {}
        for attr, getFunction, setFunction, kwds in self.attributes:
            value = str(getFunction(self.obj, attr))
            self.labels[attr] = Label(self, attr, grid=(row, 0))
            self.edits[attr] = LineEdit(self, text=value, textAlignment='left',
                                              vAlign = 't', grid=(row, 1), **kwds)
            row += 1

        self.getLayout().addItem(QtWidgets.QSpacerItem(0, 5), row, 0)
        row += 1

        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(row, 0), gridSpan=(1,2))

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        """

        from ccpn.core.lib.ContextManagers import undoBlockManager

        with undoBlockManager():
            try:
                for attr, getFunction, setFunction, _tmp in self.attributes:
                    value = str(getFunction(self.obj, attr))
                    newValue = self.edits[attr].text()
                    if newValue != value:
                        setFunction(self.obj, attr, newValue)

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es
                return False

            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()

