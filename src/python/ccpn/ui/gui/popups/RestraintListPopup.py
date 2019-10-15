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

from PyQt5 import QtGui, QtWidgets

from ccpn.core.RestraintList import RestraintList

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning

from ccpn.util.Logging import getLogger


class RestraintListPopup(CcpnDialog):

    def __init__(self, parent=None, mainWindow=None, restraintList=None, dataSet=None, editMode=False, **kwds):

        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Edit RestraintList',
                                  margins=(5,5,5,5), spacing=(5, 5), **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.restraintList = restraintList
        self.editMode = editMode
        self.dataSet = dataSet
        if self.dataSet is None and self.restraintList is not None:
            self.dataSet = self.restraintList.dataSet

        name = restraintList.name if restraintList is not None else ''
        self.nameLabel = Label(self, "Name ", grid=(0, 0))
        self.nameText = LineEdit(self, name, backgroundText='<default>', grid=(0, 1), textAlignment='left')

        if not editMode:
            # Only for new restraintLists, as setting the type affects the contained restraints
            self.restraintTypeLabel = Label(self, "Restraint Type ", grid=(1, 0))
            self.restraintTypeList = PulldownList(self, grid=(1, 1))
            self.restraintTypeList.setData(RestraintList.restraintTypes)
            # self.restraintTypeList.select(RestraintList.restraintTypes[0])

        buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(2, 1))

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        """
        from ccpn.core.lib.ContextManagers import undoBlock

        with undoBlock():
            try:
                name = self.nameText.text()
                if self.editMode:
                    if str(name) != self.restraintList.name:
                        self.restraintList.rename(name)
                else:
                    restraintType = self.restraintTypeList.currentText()
                    self.dataSet.newRestraintList(name=name, restraintType=restraintType)

                self.accept()

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es
                return False

        return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
