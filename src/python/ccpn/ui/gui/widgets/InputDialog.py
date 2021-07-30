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
__dateModified__ = "$dateModified: 2021-07-30 20:44:26 +0100 (Fri, July 30, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2015-10-15 12:34:22 +0100 (Tue, October 15, 2015) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets


def askPassword(title, prompt, parent=None):
    dialog = QtWidgets.QInputDialog(parent)
    dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
    dialog.setTextEchoMode(QtWidgets.QLineEdit.Password)
    dialog.setLabelText(prompt)

    dialog.rejected.connect(lambda: dialog.setTextValue(''))
    dialog.exec_()

    return dialog.textValue() or None


def askString(title, prompt, initialValue='', parent=None):
    value, isOk = QtWidgets.QInputDialog.getText(parent, title, prompt,
                                                 text=initialValue)

    if isOk:
        return value


def askInteger(title, prompt, initialValue=0, minValue=-2147483647,
               maxValue=2147483647, parent=None):
    value, isOk = QtWidgets.QInputDialog.getInt(parent, title, prompt, initialValue,
                                                minValue, maxValue)
    if isOk:
        return value


def askFloat(title, prompt, initialValue=0.0, minValue=-2147483647,
             maxValue=2147483647, decimals=6, parent=None):
    value, isOk = QtWidgets.QInputDialog.getDouble(parent, title, prompt, initialValue,
                                                   minValue, maxValue, decimals)

    if isOk:
        return value


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import Application


    app = Application()

    print(askString('ask string title', 'ask string prompt', 'Hello'))
    print(askInteger('ask integer title', 'ask integer prompt', 7))
    print(askFloat('ask float title', 'ask float prompt', 3.141593))
    print(askPassword('ask password', 'ask password prompt'))
