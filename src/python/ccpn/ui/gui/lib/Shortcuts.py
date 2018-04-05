"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
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
  shortcutItem = {SHORTCUT_KEYS: keys,
                  SHORTCUT_KEYSTRING: keyString,
                  SHORTCUT_OBJECT: obj,
                  SHORTCUT_FUNC: func,
                  SHORTCUT_CONTEXT: context,
                  SHORTCUT_SHORTCUT: shortcut}
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