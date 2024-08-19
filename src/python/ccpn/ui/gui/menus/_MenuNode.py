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
__dateModified__ = "$dateModified: 2024-08-19 15:06:23 +0100 (Mon, August 19, 2024) $"
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

from ccpn.framework.Application import getApplication, getProject, getCurrent
from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath
from ccpn.util.decorators import singleton
from ccpn.util.Tree import Tree
from ccpn.util.DataEnum import DataEnum

from ccpn.ui.gui.widgets.Menu import Menu as MenuWidget
from ccpn.ui.gui.widgets.Action import Action as ActionWidget

from ccpn.ui.gui.menus._MenuItems import Menu, Action, Section, Separator, DynamicMenu


class NodeType(DataEnum):
    UNDEFINED = 0, 'Undefined'
    SEPARATOR = 1, 'Separator'
    SECTION = 2, 'Section'
    MENU = 3, 'Menu'
    DYNAMIC_MENU = 4, 'DynamicMenu'
    ACTION = 5, 'Action'


class MenuNode(Tree):
    """Just a class to define the MenuNode tree structure to store the MenuWidget and
    ActionWidget objects
    Has dict like behavior to facilitate lookup,
    e.g. assume a myMenus (nested) object from a MenuDefs instance:

       myMenus['File']['New'] would yield the corresponding MenuNode for that Menu

    """

    def __init__(self, parent, name: str, nodeType: NodeType,
                 callback: CallableOrNone = None, options: dict = {}):
        """
        Initialise the node
        :param parent: parent node; None denotes root
        :param name: name of the node
        :param nodeType: type of the node
        :param callback: callback function (for an Action or DynamicMenu-node)
        :param options: (keyword,value) dict of options to the Action
        """

        # Make node initially as stand-alone,
        # to be added after all init's are completed
        Tree.__init__(self, parent=None)

        self.name: str = name
        self.nodeType = nodeType

        # Actions have a callback function
        self.callback: CallableOrNone = callback

        # Actions (can) have options
        self.options: dict = options

        # Action's can be checked by a callback for needing enabling
        self.checkEnable: bool = False
        self.checkEnableCallback: CallableOrNone = None

        # Menu nodes can be dynamically filled and have a callback function
        self.dynamicCallback: CallableOrNone = None

        # The widget associated with this node
        self.widget = None

        # Add to tree, if parent is not None, i.e. this node is not the root
        if parent is not None:
            parent._addChild(self)

    #-----------------------------------------------------------------------------------------

    @property
    def parent(self):
        return self._parent

    @property
    def level(self) -> int:
        """
        :return the level of the MenuNode in the nested structure (root has level 0)
        """
        return len(self.anchestors())

    @property
    def isSeparator(self) -> bool:
        """:return True if node is a separator
        """
        return self.nodeType == NodeType.SEPARATOR

    @property
    def isSection(self) -> bool:
        """:return True if node is a section
        """
        return self.nodeType == NodeType.SECTION

    @property
    def isMenu(self) -> bool:
        """:return True if node is a menu
        """
        return self.nodeType == NodeType.MENU

    @property
    def isDynamicMenu(self) -> bool:
        """:return True if node is a dynamic menu
        """
        return self.nodeType == NodeType.DYNAMIC_MENU

    @property
    def isAction(self) -> bool:
        """:return True if node is a action
        """
        return self.nodeType == NodeType.ACTION

    #-----------------------------------------------------------------------------------------

    def clearNode(self):
        """For a dynamic Menu node only:
        clear self; clear and remove all descendant nodes
        """
        if not (self.isDynamicMenu):
            raise RuntimeError(f'clearNode: Cannot clear {self}')

        if self.widget:
            self.widget.clear()
        # remove the descendant nodes;
        self._removeAllChildren()

    def setCheckedNode(self, callback):
        """Make node a checked one, defining callback for checking by parent
        param callback: a function with signature callback(node:MenuNode) -> bool
        """
        self.checkEnable = True
        self.checkEnableCallback = callback

    def setEnabled(self, flag):
        """Set the enabled status of widget to flag
        """
        if self.widget:
            self.widget.setEnabled(flag)

    #-----------------------------------------------------------------------------------------

    def addNode(self, name, **kwds):
        """Syntactically sugar to add a node to self.
        Node is defined by name and **kwds (see __init__)
        :return The newly created MenuNode instance
        """
        _node = MenuNode(parent=self, name=name, **kwds)
        return _node

    @classmethod
    def newFromList(cls, theList, parent=None, name='menuRoot'):
        """classmethod: Create new MenuNode instance, (Recursively) traverse
        theList with Menu definitions, adding items in theList as child-nodes.

        :param thelist: a list of Menu definitions
        :param parent: the parent Node; None indicates the result to be root
        :param name: name of the resulting node

        :return a the newly created MenuNode instance
        """
        if not isinstance(theList, list):
            raise TypeError(f'newFromList: expected list; got {type(theList)}')

        if len(theList) == 0:
            raise ValueError(f'newFromList: empty list')

        node = cls(parent=parent, name=name, nodeType=NodeType.MENU)
        node.addNodesFromList(theList)
        return node

    def addNodesFromList(self, theList) -> list:
        """(Recursively) Traverse theList with Menu definitions, adding items in theList as child-nodes.
        The method effectively parses the menu-definitions list, as defined by the
        MenuDefs class above

        :param theList: a list with Menu-item definitions (see also MenuDefs class)

        :return A list of nodes added
        """

        def _str120(val):
            """truncate str(val) to 120 chars
            """
            _tmp = str(val)
            if len(_tmp) > 120:
                _tmp = f'{_tmp[0:54]}    ....    {_tmp[-54:]}'
            return _tmp

        if not isinstance(theList, list):
            raise TypeError(f'addNodesFromList to {self}: expected list; got {type(theList)}')

        result = []
        separatorIndex = 0  # This gives each separator a unique name
        for item in theList:

            if isinstance(item, DynamicMenu):
                node = self.addNode(name=item.name, nodeType=NodeType.DYNAMIC_MENU)
                node.dynamicCallback = item.callback
                if item.checkEnabled is not None:
                    node.setCheckedNode(item.checkEnabled)
                result.append(node)

            elif isinstance(item, Menu):
                node = self.newFromList(theList=item, parent=self, name=item.name)
                if item.checkEnabled is not None:
                    node.setCheckedNode(item.checkEnabled)
                result.extend(node.allObjects())

            elif isinstance(item, Action):
                node = self.addNode(name=item.name, nodeType=NodeType.ACTION, callback=item.callback, options=item.options)
                if item.checkEnabled is not None:
                    node.setCheckedNode(item.checkEnabled)
                result.append(node)

            elif isinstance(item, Section):
                node = self.addNode(name=item.name, nodeType=NodeType.SECTION)
                result.append(node)

            elif isinstance(item, Separator):
                # A separator
                _name = f'Separator_{separatorIndex}'
                node = self.addNode(name=_name, nodeType=NodeType.SEPARATOR)
                result.append(node)
                separatorIndex += 1

            else:
                # this should not happen
                raise RuntimeError(
                    f'addNodesFromList to {self}: We should not be here! Invalid menu definition: \n>>> {_str120(item)}')

        return result

    #-----------------------------------------------------------------------------------------

    def _updateNodeCallback(self):
        """Callback to update the node:
        - optionally adding dynamic nodes
        - checking self for checkEnable
        - checking child-nodes for checkEnable and enabling/disabling corresponding widgets.
        """
        if self.isDynamicMenu and self.dynamicCallback:
            _menuDefs = self.dynamicCallback(self)
            self._updateDynamicNode(defs=_menuDefs)

        if self.checkEnable:
            self.checkEnableCallback(self)

        for child in [_c for _c in self._children if _c.checkEnable]:
            enabled = child.checkEnableCallback(child)
            child.setEnabled(enabled)

    def _updateDynamicNode(self, defs: list):
        """Update dynamic node using defs to generate child-nodes and corresponding
        Menu widgets.
        """
        if not self.isDynamicMenu:
            raise RuntimeError(f'_updateDynamicNode: not allowed for {self}')

        # clear this node and its decendants
        self.clearNode()
        # construct the new descendant nodes from the defs
        self.addNodesFromList(defs)
        # make the menu's
        for _child in self._children:
            _child.makeMenu()

    def makeMenu(self):
        """Use node to make its menu's; i.e. adding Menu/Action Widgets
        Recursively decent into its children

        """
        if self.isRoot:
            # MenuNode root's widget is the MenuBar instance; cannot modify that as it is maintanined by MenuBarManager
            raise RuntimeError(f'{self} is root; cannot make a menu')

        # We are not root, so should have a parent with a widget
        if (_parent := self.parent) is None:
            raise RuntimeError(f'makeMenu: {self} has no parent')

        if _parent.widget is None:
            raise ValueError(f'makeMenu: {_parent} has no widget')

        if self.isAction:
            self.widget = ActionWidget(parent=_parent.widget, text=self.name,
                                       callback=self.callback, **self.options
                                      )
            _parent.widget.addAction(self.widget)

        elif self.isMenu or self.isDynamicMenu:
            if self.level == 0:
                raise RuntimeError(f'makeMenu: invalid {self} for level=0 ')

            elif self.level == 1:
                # Adding to menuBar
                self.widget = MenuWidget(parent=_parent.widget, title=self.name)
                _parent.widget.addMenu(self.widget)

            # GWV: not quite sure why is needs this way, (i.e. different from addMenu
            # for menuBar, but it works)
            elif self.level > 1:
                self.widget = _parent.widget.addMenu(self.name)

            # Always set callback for Menu nodes;
            # this fills dynamic selfs and also enable/disables children depending on checkEnabled
            self.widget.aboutToShow.connect(self._updateNodeCallback)

        elif self.isSeparator:
            self.widget = _parent.widget.addSeparator()

        elif self.isSection:
            # We do not use _parent.widget.addSection as it does not show with native settings!!
            # Instead, we emulate it as a disabled Item with horizontal line left and right
            self.widget = _parent.widget.addItem(text=f'⎯⎯⎯⎯⎯ {self.name} ⎯⎯⎯⎯⎯', enabled=False)

        else:
            raise RuntimeError(f'Invalid: {self} is ill-defined')

        # recurse into children
        for _child in self._children:
            _child.makeMenu()

    #-----------------------------------------------------------------------------------------
    # implement some dict-like behaviour
    #-----------------------------------------------------------------------------------------

    @property
    def _childrenAsDict(self):
        """:return self._children as a dict of (name, child) key, value pairs
        """
        return dict([(child.name, child) for child in self._children])

    def keys(self) -> list:
        return list(self._childrenAsDict.keys())

    def items(self) -> list:
        return list(self._childrenAsDict.items())

    def values(self) -> list:
        return list(self._childrenAsDict.values())

    def __getitem__(self, key):
        _vals = self._childrenAsDict
        if key not in _vals:
            raise KeyError(f'key {key!r} not in {self}')
        return _vals[key]

    #-----------------------------------------------------------------------------------------

    def print(self):
        """
        print Tree of self with indentation
        """
        for node in self.allObjects():

            level = node.level
            tabs = '\t' * (level - 1) if level > 1 else ''
            if level == 1:
                tabs = '\n' + tabs
            _name = node.name if not (node.isSeparator or node.isSection) else f'--- {node.name} ---'
            _options = str(node.options) if node.isAction else ''

            print(f'{tabs}{_name!r:25}  (level={node.level}, type={node.nodeType.description}) {_options}')

            if node.isDynamicMenu and len(node._children) == 0:
                print(f'{tabs}\t--> dynamically filled ({node.dynamicCallback})')

    def __str__(self):
        return f'<MenuNode: {self.name!r} (level={self.level}, type={self.nodeType.description}, checkEnable={self.checkEnable})>'

    __repr__ = __str__

# end class #-----------------------------------------------------------------------------
