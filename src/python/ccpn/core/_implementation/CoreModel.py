"""
This file contains the methods and data to initialise and maintain
the model-related aspects of the V3 core object
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-01-26 14:54:56 +0000 (Thu, January 26, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

class CoreModel(object):
    """Model-related methods; Only to be used for core objects via AbstractWrapperObject
    """

    #: Short class name, for PID. Must be overridden for each subclass
    shortClassName = None

    # Class name - necessary since the actual objects may be of a subclass.
    className = None

    # Name of the parent class; used to make model linkages
    _parentClassName = None

    # List of child classes. Will be filled by child-classes registering.
    _childClasses = []

    # the dict of (className, class) and (shortClassName, class) pairs
    _coreClassDict = {}


    @classmethod
    def _registerCoreClass(cls, factoryFunction=None):
        """Registers class; defines the model-linkages
        optionally sets _factoryFunction attribute
        """
        if cls.className is None:
            raise RuntimeError(f'{cls.__name__}: className class-attribute is undefined')

        if cls.shortClassName is None:
            raise RuntimeError(f'{cls.__name__}: className class-attribute is undefined')

        if cls._parentClassName is not None:
            if (parentKlass := cls._coreClassDict.get(cls._parentClassName)) is None:
                raise RuntimeError(f'{cls.__name__}: cannot get class for "{cls._parentClassName}"')
            # Just for the transition period
            if cls not in parentKlass._childClasses:
                parentKlass._childClasses.append(cls)

        cls._coreClassDict[cls.className] = cls
        cls._coreClassDict[cls.shortClassName] = cls

        cls._factoryFunction = factoryFunction

    @classmethod
    def _getChildClasses(cls, recursion: bool = False) -> list:
        """
        :param recursion: use recursion to also add child objects
        :return: list of valid child classes of cls

        NB: Depth-first ordering

        CCPNINTERNAL: Notifier class
        """
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
