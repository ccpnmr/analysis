"""
Module documentation
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-03-18 18:36:50 +0000 (Mon, March 18, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2023-10-16 16:42:30 +0100 (Mon, October 16, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================
#


class Tree(object):
    """
    Core tree behavior; maintain _parent, _children and _root attributes
    """
    # _root and _parent linkages are restored from _children by _restoreLinkages;


    def __init__(self, parent=None):
        """Init to object
        parent = None indicates the object to be the root, otherwise add to the tree
        """
        # initially object is root object without parent or children;
        # this is the root (for now)
        self._parent = None
        self._root = self
        self._children = []

        if parent is not None:
            # parent is not None, so add self as a child;
            # needs to be done here for recursion-init reasons
            parent._addChild(self)

    @property
    def isRoot(self) -> bool:
        """:return True if self is root
        """
        return (self._root == self and self._parent is None)

    def _setRoot(self, root):
        """set root of self and children to root
        """
        self._root = root
        for obj in self.allDecendants():
            obj._root = root

    def _addChild(self, child):
        """Add child to the tree, child (and its children) inherit root from self
        :parameter child: a Tree instance that is a child of self
        CCPNMRINTERNAL: Used in super classes; hidden for user perspective reasons
        """
        if child == self:
            raise RuntimeError(f'addChild(): Cannot be both child and parent ({child})')
        if child in self._children:
            raise RuntimeError (f'addChild(): {child} is already a child of {self}')
        child._parent = self
        # child and its children inherit _root from self
        child._setRoot(self._root)
        self._children.append(child)

    def _removeChild(self, child):
        """Remove child from self, child becomes root;
        :parameter child: a Tree instance that is a child of self
        :return child as root object

        CCPNMRINTERNAL: Used in super classes; hidden for user perspective reasons
        """
        if child not in self._children:
            raise RuntimeError (f'removeChild(): {child} is not a child of {self}')
        self._children.remove(child)
        # child becomes root of its tree
        child._parent = None
        child._setRoot(child)
        return child

    def _removeAllChildren(self):
        """Remove all children from self
        Dedicated routine as looping over self._children while removing from the same list yields
        not the desired result.
        """
        # remove the children; first make a "copy" into a list, otherwise
        for child in list(self._children):
            self._removeChild(child)

    def _getChildrenByClass(self, klass) -> list:
        """Conveniance function to get all children, optionally filtered for klass
        CCPNMRINTERNAL: used throughout in various Tree's
        """
        if klass is None:
            _children = self._children
        else:
            _children = [child for child in self._children if isinstance(child, klass)]
        return _children

    def _getIndex(self, klass=None) -> int:
        """Get an index for self;
        * non-root: position in list of children (optionally filtered for klass)
        * -1 for root,
        :parameter klass: filter for instances of klass; None implies self.__class__
        CCPNMRINTERNAL: used throughout in various Tree's
        """
        if self.isRoot:
            return -1
        if klass is None:
            klass = self.__class__
        _children = self._parent._getChildrenByClass(klass=klass)
        return _children.index(self)

    def _nextIndex(self, klass=None) -> int:
        """Get the next index derived from the children of self
        (optionally filtered for klass)
        :parameter klass: filter for instances of klass;
        CCPNMRINTERNAL: used throughout in various Tree's
        """
        _children = self._getChildrenByClass(klass=klass)
        return len(_children)

    def isSibling(self, other, klass=None) -> bool:
        """
        :parameter other: a Tree instance to check
        :parameter klass: filter for instances of klass; None implies self.__class__
        :return True is other is sibling of self
        """
        if self.isRoot or other.isRoot:
            return False

        if other._parent != self._parent:
            return False

        if klass is None:
            klass = self.__class__

        return other in self._parent._getChildrenByClass(klass=klass)

    def getRelativeSibling(self, relativeIndex:int, klass=None):
        """Get sibling relative to self, or None if not exist.
        :parameter relativeIndex: index relative to self [-n ... +n] (mod function will be applied)
        :parameter klass: filter for instances of klass; None implies self.__class__
        :return sibling or None
        """
        if self.isRoot:
            return None

        if klass is None:
            klass = self.__class__
        _children = self._parent._getChildrenByClass(klass=klass)

        if len(_children) == 0:
            return None
        if len(_children) == 1 and relativeIndex != 0:
            return None

        idx = _children.index (self)
        idx = (idx + relativeIndex) % len(_children)
        return _children[idx]

    def allDecendants(self) -> list:
        """:return: a list of all decendants of self
        """
        return self.traverse(lambda obj: obj)[1:]

    def allObjects(self) -> list:
        """:return: a list of self and all decendants of self
        """
        return self.traverse(lambda obj: obj)

    def anchestors(self) -> list:
        """:return: a list of all anchestors of self (_parent upto root)
        """
        result = []
        obj = self
        while obj._parent is not None:
            obj = obj._parent
            result.append(obj)
        return result

    def traverse(self, func, *args, **kwargs) -> list:
        """Method for recursively traversing the tree,
        executing func(self, *args, **kwargs) on each node, including self first.
        :returns a list of result of func() on each node

        Very powerful to access all objects;
        e.g. to have all objects from this node in a list:
            self.traverse(lambda obj: obj)
        NB: This is already implemented as the allObjects() method
        """
        result = [func(self, *args, **kwargs)]
        for child in self._children:
            result.extend(child.traverse(func, *args, **kwargs))
        return result

#end class
