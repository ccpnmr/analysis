"""
    The menus are specified by a (recursive) Menu's (i.e. lists) composed of menu items;
    i.e:

    - Action: triggered when the menu item is selected;
      signature:
        Action(name, callback, checkEnabled=None, **options)

      options is a dict of (option, value) pairs.
      Valid options (from Action widget):
            :param shortcut: optional two letter shortcut
            :param checked: optional checked flag (if checkable, default: True)
            :param checkable: optional checkable flag (default: False)
            :param icon: optional icon
            :param enabled: optional enable flag (default: True)
            :param toolTip: optional tooltip

        Signature checkEnabled, returning True if should be enabled:
            checkEnabled(node:MenuNode) -> bool

    - Menu: A menu (list) with items;
      Signature:
        Menu(name, *items, checkEnabled=None)

    - DynamicMenu: a dynamically filled menu
      Signature:
        DynamicMenu(name, callback, checkEnabled=None)

        Signature checkEnabled: see above
        Signature callback:
            callback(node:MenuNode) -> list

    - A section defining operation with signature:
        Section(name)

    - A separator defining operation with signature.
        Separator()
---------------------------------------------------------------------------------------
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-08-19 15:06:22 +0100 (Mon, August 19, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"

#=========================================================================================
# Start of code
#=========================================================================================

import os
import platform

from functools import partial
from typing import Optional, Callable, Any, TypeAlias

CallableOrNone = Optional[Callable]


#-----------------------------------------------------------------------------------------
# Menu items definitions
#-----------------------------------------------------------------------------------------

class _MenuItemABC():
    """A class that maintains the properties of various Menu items; e.g.
    Separator, Section, Action, Menu and DynamicMenu
    """
    def __init__(self, name: str):
        if name is None or len(name) == 0:
            raise ValueError(f'Undefined name for <{self.__class__.__name__}>')
        self.name: str = name

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.name}>'

    __repr__ = __str__


class Separator(_MenuItemABC):
    """A class for defining a Separator
    """
    def __init__(self):
        super().__init__(name = 'Separator')


class Section(_MenuItemABC):
    """A class for defining a Section
    """
    def __init__(self, name: str):
        super().__init__(name=name)


class Action(_MenuItemABC):
    """A class for defining a menu action
    """
    _validOptions = 'shortcut enabled checkable checked icon toolTip'.split()

    def __init__(self, name: str, callback: Callable, checkEnabled: CallableOrNone = None, **options):
        super().__init__(name=name)
        self.callback = callback
        self.checkEnabled = checkEnabled
        self.options = self._optionsDict(**options)

    def _optionsDict(self, **options) -> dict:
        """Create and return an options dict
        """
        options.setdefault('enabled', True)
        options.setdefault('checkable', False)
        options.setdefault('checked', True)

        errors = [option for option in options.keys() if option not in self._validOptions]
        if len(errors) > 0:
            raise ValueError(f'Invalid options: {errors!r}')
        return options


class Menu(list, _MenuItemABC):
    """A class representing a list of menu items
    """
    def __init__(self, name, *items, checkEnabled: CallableOrNone = None):
        list.__init__(self, items)
        _MenuItemABC.__init__(self, name=name)
        self.checkEnabled: CallableOrNone = checkEnabled
        self.callback: CallableOrNone = None


class DynamicMenu(_MenuItemABC):
    """A class representing a dynamic menu definition
    """
    def __init__(self, name, callback: Callable, checkEnabled: CallableOrNone = None):
        if callback is None:
            raise ValueError(f'DynamicMenu: undefined callback')
        super().__init__(name=name)
        self.checkEnabled=checkEnabled
        self.callback = callback

#-----------------------------------------------------------------------------------------
