"""
This file contains the methods and data to initialise and maintain
the model-related aspects of the V3 core object
"""
from __future__ import annotations  # pycharm still highlights as errors


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
__dateModified__ = "$dateModified: 2024-11-08 08:31:30 +0000 (Fri, November 08, 2024) $"
__version__ = "$Revision: 3.2.10.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.core.lib.CcpNmrProperties import HasCcpNmrProperties


class CoreModel(HasCcpNmrProperties):
    """Model-related methods; Only to be used for core objects via
    AbstractWrapperObject or V3CoreModelABC
    """

    #: Short class name, for PID. Must be overridden for each subclass
    shortClassName = None

    # Class name - necessary since the actual objects may be of a subclass.
    className = None

    # Name of the parent class; used to make model linkages
    _parentClass = None

    # List of child classes. Will be filled by child-classes registering.
    _childClasses = []

    # the dict of (className, class) pairs
    _coreClassDict = {}

    # the dict of (shortClassName, class) pairs
    _coreClassShortNameDict = {}

    _isRegistered = False

    def __init__(self):
        # if not self._isRegistered:
        #     raise RuntimeError(f'{self.className}: not registered')
        pass

    @classmethod
    def _registerCoreClass(cls, factoryFunction=None):
        """Registers class; defines the model-linkages
        Registers Traities
        Optionally sets _factoryFunction attribute (if not None)
        """
        if cls._isRegistered:
            # 'raise' caused a crash in the NoUi mode when running test-cases
            getLogger().debug(f'Class "{cls.__name__}": class has been registered before')
            return

        if cls.className is None:
            raise RuntimeError(f'Class "{cls.__name__}": className class-attribute is undefined')

        if cls.shortClassName is None:
            raise RuntimeError(f'Class "{cls.__name__}": shortClassName class-attribute is undefined')

        if cls._parentClass is None and cls.className != 'Project':
            raise RuntimeError(f'Class "{cls.__name__}": _parentClass class-attribute is undefined')

        cls._coreClassDict[cls.className] = cls
        cls._coreClassShortNameDict[cls.shortClassName] = cls

        cls._linkCoreClass()

        if factoryFunction is not None:
            cls._factoryFunction = factoryFunction

        cls._registerCcpNmrProperties()

        cls._isRegistered = True

    @classmethod
    def _linkCoreClass(cls):
        """Defines the model-linkages for cls
        """
        if cls._parentClass is not None:
            parentKlass = cls._parentClass
            # Just to be save
            if cls not in parentKlass._childClasses:
                parentKlass._childClasses.append(cls)

    @classmethod
    def _getChildClasses(cls, recursion: bool = False) -> list:
        """
        :param recursion: use recursion to also add child-classes of cls
        :return: list of valid child classes of cls

        NB: Depth-first ordering

        CCPNINTERNAL: Notifier class
        """
        if not recursion:
            result = cls._childClasses

        else:
            result = []
            for klass in cls._childClasses:
                result.append(klass)
                if recursion:
                    result = result.extend(klass._getChildClasses(recursion=recursion))

        return result

    @classmethod
    def _getParentClasses(cls) -> list:
        """Return a list of parent classes, starting with the root (i.e. Project)
        """
        result = []
        klass = cls
        while klass._parentClass is not None:
            result.append(klass._parentClass)
            klass = klass._parentClass
        result.reverse()
        return result

    @classmethod
    def _getClassIndex(cls, className: str) -> int:
        """:return an ordering index for the className; used for "uniqueId" stuff
        """
        _classList = list(cls._coreClassDict.keys())
        return _classList.index(className)

    @classmethod
    def _getClass(cls, className: str) -> (CoreModel, None):
        """:return coreClass corresponding to className (either long or short versions)
        """
        return cls._coreClassDict.get(className) or cls._coreClassShortNameDict.get(className)

    @classmethod
    def _printClassTree(cls, node=None, tabs=0):
        """Simple Class-tree printing method
         """
        if node is None:
            node = cls
        s = '\t' * tabs + f'{node.className}'
        if node._isGuiClass:
            s += '  (GuiClass)'
        if hasattr(node, '_isRegistered') and node._isRegistered:
            s += '    --> (registered)'
        print(s)
        for child in node._childClasses:
            cls._printClassTree(child, tabs=tabs + 1)


def _isV3coreClassInstance(obj) -> bool:
    """
    Check if obj is a V3 core class instance
    :param obj: object to check
    :return: True if obj is a V3 core class instance

    CCPNINTERNAL: several places to make more readable code
    """
    return isinstance(obj, CoreModel)

def _isV3coreClass(klass) -> bool:
    """
    Check if klass is of type V3 core class
    :param klass: class to check
    :return: True if obj defines a core class

    CCPNINTERNAL: several places to make more readable code
    """
    return klass in CoreModel._coreClassDict.values()

def _getV3coreClass(className):
    """
    V3 core class name
    :param className: name of the class
    :return: class if className defines a core class else None

    CCPNINTERNAL: several places to make more readable code
    """
    return CoreModel._coreClassDict.get(className, None)
