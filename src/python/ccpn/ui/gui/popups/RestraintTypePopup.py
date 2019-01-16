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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger


restraintTypes = [
    'Distance',
    'Dihedral',
    'Rdc',
    'Csa',
    'ChemicalShift',
    'JCoupling'
    ]


class RestraintTypePopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, peakList=None, title='Restraints', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.restraintType = None

        self.restraintTypeLabel = Label(self, "Restraint Type ", grid=(0, 0))
        self.restraintTypeList = PulldownList(self, grid=(0, 1))
        self.restraintTypeList.setData(restraintTypes)
        buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

    def _setRestraintType(self):
        # try:
        self.restraintType = self.restraintTypeList.currentText()
        self.accept()

    # except Exception as e:
    #   showWarning('Restraints', str(e))

    def _repopulate(self):
        self.restraintTypeList.setText(self.restraintType)

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        # ejb - major refactoring

        applyAccept = False
        oldUndo = self.project._undo.numItems()

        from ccpn.core.lib.ContextManagers import undoBlockManager

        with undoBlockManager():
            try:
                self._setRestraintType()

                applyAccept = True

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)
            if oldUndo != self.project._undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

            # repopulate popup
            self._repopulate()
            return False
        else:
            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
