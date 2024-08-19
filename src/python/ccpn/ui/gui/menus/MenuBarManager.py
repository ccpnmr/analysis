"""
MenuBarManager; used by MainWindow to manage the programme's menu-bar
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
from functools import partial
from typing import Optional, Callable, Any, TypeAlias

CallableOrNone = Optional[Callable]

# from ccpn.util.Common import isWindowsOS
# from ccpn.util.Logging import getLogger
# from ccpn.util.Path import aPath
# from ccpn.util.decorators import singleton
# from ccpn.util.Tree import Tree
# from ccpn.util.DataEnum import DataEnum

from ccpn.ui.gui.menus._MenuItems import Menu, Action, Section, Separator, DynamicMenu
from ccpn.ui.gui.menus._MenuNode import MenuNode


class MenuBarManager(object):
    """A class to manage the menu's of the menuBar of the programme;
    used by MainWindow.
    Works of a MenuNode Tree structure
    """

    def __init__(self, mainWindow, menuDefs: Menu):

        self.mainWindow = mainWindow
        self.menuBar = mainWindow._getMenuBarWidget()
        self.useNativeMenus = False

        # define self.application; project, current and ui are derived via properties
        self.application = mainWindow.application

        # define the MenuNode's tree
        self.menuNodes = MenuNode.newFromList(menuDefs)

    @property
    def project(self):
        """:return The Project instance
        """
        return self.application.project

    @property
    def current(self):
        """:return The Current instance
        """
        return self.application.current

    @property
    def ui(self):
        """:return The Ui instance
        """
        return self.application.ui

    #-----------------------------------------------------------------------------------------

    def makeMenus(self, useNativeMenus=False):
        """Use node to make its menu's; i.e. adding Menu/Action to node
        Recursively decent into its children
        :param useNativeMenus: flag to use native menu's
        """
        node = self.menuNodes
        if not node.isRoot:
            raise RuntimeError(f'Ill-defined menuNodes root')

        # MenuNode root's widget is the MenuBar instance
        self.menuBar.clear()
        self.menuBar.setNativeMenuBar(useNativeMenus)
        self.useNativeMenus = useNativeMenus
        node.widget = self.menuBar

        # recurse into children
        for _child in node._children:
            _child.makeMenu()

    #-----------------------------------------------------------------------------------------

    def __str__(self):
        return f'<MenuBarManager>'

# end class #-----------------------------------------------------------------------------
