"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-03-08 16:20:26 +0000 (Tue, March 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-02-10 13:34:53 +0100 (Thu, February 10, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re

from PyQt5 import QtGui
from ccpn.ui.gui.modules.CcpnModule import INVALIDROWCOLOUR


class LineEditValidator(QtGui.QValidator):
    """Validator to restrict input to non-whitespace characters
    """

    def __init__(self, parent=None, allowSpace=True, allowEmpty=True):
        super().__init__(parent=parent)

        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)
        self._parent = parent
        self._allowSpace = allowSpace
        self._allowEmpty = allowEmpty

    def _isValidInput(self, value):
        notAllowedSequences = {'Illegal_Characters': '[^A-Za-z0-9_ ]+',
                               'Empty_Spaces'      : '\s',
                               }

        if not value and not self._allowEmpty:
            return False
        if self._allowSpace:
            notAllowedSequences.pop('Empty_Spaces')
        for key, seq in notAllowedSequences.items():
            if re.findall(seq, value):
                return False

        return True

    def validate(self, p_str, p_int):
        palette = self.parent().palette()

        if self._isValidInput(p_str):
            palette.setColor(QtGui.QPalette.Base, self.baseColour)
            state = QtGui.QValidator.Acceptable  # entry is valid
        else:
            palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
            state = QtGui.QValidator.Intermediate  # entry is NOT valid, but can continue editing
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)

    @property
    def checkState(self):
        state, _, _ = self.validate(self.parent().text(), 0)
        return state


class LineEditValidatorCoreObject(QtGui.QValidator):
    """Validator to restrict input to non-whitespace characters
    and restrict input to the names not already in the core object klass
    """

    def __init__(self, parent=None, target=None, klass=None, allowSpace=True, allowEmpty=True):
        super().__init__(parent=parent)

        # self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)
        self.baseColour = QtGui.QColor('#ffffff')  # why the wrong colour?
        self._parent = parent
        self._allowSpace = allowSpace
        self._allowEmpty = allowEmpty
        self._pluralLinkName = klass._pluralLinkName
        self._target = target

    def _isValidInput(self, value):
        notAllowedSequences = {'Illegal_Characters': '[^A-Za-z0-9_ \#\!\@\£\$\%\&\*\(\)\-\=\_\+\[\]\{\}\;]+',
                               'Empty_Spaces'      : '\s',
                               }

        if not value and not self._allowEmpty:
            return False
        if self._allowSpace:
            notAllowedSequences.pop('Empty_Spaces')
        for key, seq in notAllowedSequences.items():
            if re.findall(seq, value):
                return False

        # check klass
        if self._pluralLinkName and self._target:
            _found = [obj.name for obj in getattr(self._target, self._pluralLinkName, ())]
            if value in _found:
                return False

        return True

    def validate(self, p_str, p_int):
        palette = self.parent().palette()

        if self._isValidInput(p_str):
            palette.setColor(QtGui.QPalette.Base, self.baseColour)
            state = QtGui.QValidator.Acceptable  # entry is valid
        else:
            palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
            state = QtGui.QValidator.Intermediate  # entry is NOT valid, but can continue editing
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)

    @property
    def checkState(self):
        state, _, _ = self.validate(self.parent().text(), 0)
        return state

    @property
    def isValid(self):
        state, _, _ = self.validate(self.parent().text(), 0)
        return state == QtGui.QValidator.Acceptable
