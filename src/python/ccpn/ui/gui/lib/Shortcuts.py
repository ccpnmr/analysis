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
__dateModified__ = "$dateModified: 2018-12-20 15:53:13 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:34 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtGui, QtCore


SHORTCUT_KEYS = 'keys'
SHORTCUT_KEYSTRING = 'keyString'
SHORTCUT_OBJECT = 'obj'
SHORTCUT_FUNC = 'func'
SHORTCUT_CONTEXT = 'context'
SHORTCUT_SHORTCUT = 'shortcut'

_shortcutList = {}


def addShortCut(keys=None, obj=None, func=None, context=None):
    """
    Add a new shortcut to the widget/context and store in the shortcut list
    :param keys - string containing the keys; e.g., 'a, b' or the keySequence object:
                  e.g., QtGui.QKeySequence.SelectAll
    :param obj - widget to attach keySequence to:
    :param func - function to attach:
    :param context - context; e.g., WidgetShortcut|ApplicationShortcut:
    """
    if isinstance(keys, str):
        keys = QtGui.QKeySequence(keys)

    shortcut = QtWidgets.QShortcut(keys, obj, func, context=context)
    storeShortcut(keys, obj, func, context, shortcut)
    return shortcut


def storeShortcut(keys=None, obj=None, func=None, context=None, shortcut=None):
    """
    Store the new shortcut in the dict, may be an Action from the menu
    :param keys - string containing the keys; e.g., 'a, b' or the keySequence object:
                  e.g., QtGui.QKeySequence.SelectAll
    :param obj - widget to attach keySequence to:
    :param func - function to attach:
    :param context - context; e.g., WidgetShortcut|ApplicationShortcut:
    """
    if obj not in _shortcutList:
        _shortcutList[obj] = {}

    if isinstance(keys, str):
        keys = QtGui.QKeySequence(keys)

        keyString = keys.toString()
        shortcutItem = {SHORTCUT_KEYS     : keys,
                        SHORTCUT_KEYSTRING: keyString,
                        SHORTCUT_OBJECT   : obj,
                        SHORTCUT_FUNC     : func,
                        SHORTCUT_CONTEXT  : context,
                        SHORTCUT_SHORTCUT : shortcut}
        _shortcutList[obj][keyString] = shortcutItem


def clearShortcuts(widget=None):
    """
    Clear all shortcuts that exist in all objects from the current widget
    :param widget - target widget:
    """
    toast = _shortcutList
    context = QtCore.Qt.WidgetWithChildrenShortcut
    for obj in _shortcutList.values():
        for shortcutItem in obj.values():
            QtWidgets.QShortcut(shortcutItem[SHORTCUT_KEYS], widget, context=context)
