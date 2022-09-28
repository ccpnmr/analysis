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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-09-28 18:45:17 +0100 (Wed, September 28, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-01-12 15:18:54 +0100 (Wed, January 12, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from sys import _getframe
from typing import Optional
from collections import OrderedDict
from functools import partial

from ccpn.core import _importOrder
from ccpn.core.lib.ContextManagers import renameObject, ccpNmrV3CoreSetter, deleteV3Object, undoStackBlocking
from ccpn.core.lib.Pid import Pid, altCharacter
from ccpn.core.lib.Notifiers import NotifierBase
from ccpn.util.decorators import logCommand
from ccpn.framework.Version import VersionString
from ccpn.util.Logging import getLogger


_UNIQUEID = 'uniqueId'
_ISDELETED = 'isDeleted'
_NAME = 'name'
_COMMENT = 'comment'


class V3CoreObjectABC(NotifierBase):
    """V3 core object object, contained in _wrapperList.
    Does not have an api equivalent
    """

    #: Short class name, for PID.
    shortClassName = 'VC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'V3CoreObjectABC'

    # MUST be defined in subclass
    _parentClass = None

    #: Name of plural link to instances of class
    _pluralLinkName = 'v3CoreObjectABCs'

    #: List of child classes.
    _childClasses = []
    _isGuiClass = False

    # the attribute name used by current
    _currentAttributeName = 'v3CoreObjectABCs'

    def __init__(self, project, wrapperList, _uniqueId):
        """Create a new instance of v3 core object

        _unique Id links the core object to the dataFrame storage and MUST be specified
        before the V3CoreObjectABC can be used
        """
        if self._parentClass is None:
            raise RuntimeError(f'{self.className}._parentClass must be defined')

        self._wrapperList = wrapperList
        self._project = project
        if not isinstance(_uniqueId, (int, type(None))):
            raise ValueError(f'{self.className}.__init__: uniqueId {_uniqueId} must be int or None')
        self._uniqueId = None
        self._ccpnSortKey = None
        self._deletedId = None
        self._isDeleted = False
        self._resetUniqueId(_uniqueId)

        # keep last value for undo/redo
        self._oldPid = None

        # tuple to hold children that explicitly need finalising after atomic operations
        self._finaliseChildren = []
        self._childActions = []

        # All other properties are derived from the wrapperList pandas dataframe

    def __str__(self):
        """Readable string representation; potentially subclassed
        """
        return ("<%s-Deleted>" % self.pid) if self._isDeleted else ("<%s>" % self.pid)

    def __repr__(self):
        """Object string representation; compatible with application.get()
        """
        return self.__str__()

    def __bool__(self):
        """Truth value: true - core object classes are never empty
        """
        return True

    def __lt__(self, other):
        """Ordering implementation function, necessary for making lists sortable.
        """
        if hasattr(other, '_ccpnSortKey'):
            return self._ccpnSortKey < other._ccpnSortKey
        else:
            return id(self) < id(other)

    def __eq__(self, other):
        """Python 2 behaviour - objects equal only to themselves.
        """
        return self is other

    def __ne__(self, other):
        """Python 2 behaviour - objects equal only to themselves.
        """
        return self is not other

    def __hash__(self):
        return id(self)

    #=========================================================================================
    # CCPN Properties
    #=========================================================================================

    @property
    def project(self) -> 'Project':
        """The Project (root) containing the object.
        """
        return self._project

    @property
    def id(self) -> str:
        """Identifier for the object, used to generate the pid and longPid.
        Generated by combining the id of the containing object, i.e. the checmialShift instance,
        with the value of one or more key attributes that uniquely identify the object in context
        E.g. 'default.1'
        """
        return self._deletedId if self._isDeleted else self.name

    @property
    def pid(self) -> Pid:
        """Identifier for the object, unique within the project.
        Set automatically from the short class name, the parent wrapperList and object.uniqueId
        E.g. 'SH:default.1'
        """
        return Pid.new(self.shortClassName, self.id)

    @property
    def longPid(self) -> Pid:
        """Identifier for the object, unique within the project.
        Set automatically from the full class name, the parent wrapperList and object.uniqueId
        E.g. 'Collection:default.1'
        """
        return Pid.new(self.className, self.id)

    @property
    def _parent(self):
        """parent containing wrapperList
        """
        return self._wrapperList

    #=========================================================================================
    # Class Properties and methods
    #=========================================================================================

    @property
    def uniqueId(self) -> int:
        """unique identifier of wrapped object.
        """
        return self._uniqueId

    @property
    def isDeleted(self) -> bool:
        """True if this object is deleted.
        """
        return self._isDeleted

    @property
    def _deleted(self) -> bool:
        """True if this object is deleted.
        CCPN Internal - allows internal deletion of the Wrapped object
        sets/clears the value in the wrapperList's dataframe
        """
        return self._wrapperList._getAttribute(self._uniqueId, _ISDELETED, bool)

    @_deleted.setter
    def _deleted(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError(f'{self.className}.isDeleted must be True/False')
        self._wrapperList._setAttribute(self._uniqueId, _ISDELETED, value)

    #~~~~~~~~~~~~~~~~

    @property
    def name(self) -> str:
        """Name of wrapped object, part of identifier"""
        return self._wrapperList._getAttribute(self._uniqueId, _NAME, str)

    @name.setter
    @logCommand(get='self', isProperty=True)
    def name(self, value: str):
        """set Name of wrapped object, part of identifier"""
        self.rename(value)

    @property
    def comment(self) -> Optional[str]:
        """Optional user comment for wrapped object.
        """
        return self._wrapperList._getAttribute(self._uniqueId, _COMMENT, str)

    @comment.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def comment(self, value: Optional[str]):
        """Set optional comment
        Must be of type string or None

        :param value:
        """
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.comment must be of type str or None')
        self._wrapperList._setAttribute(self._uniqueId, _COMMENT, value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Wrapped object, changing its name and Pid.
        """
        return self._rename(value)

    def _rename(self, value):
        """Rename the wrapped object
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: function {repr(_getframe().f_code.co_name)} not implemented')

    @classmethod
    def _validateStringValue(cls, attribName: str, value: str,
                             allowWhitespace: bool = False,
                             allowEmpty: bool = False,
                             allowNone: bool = False):
        """Validate the value of any string

        :param attribName: used for reporting
        :param value: value to be validated

        CCPNINTERNAL: used in many rename() and newXYZ method of core classes
        """
        from ccpn.util import Common as commonUtil

        if value is None and not allowNone:
            raise ValueError('%s: None not allowed for %r' %
                             (cls.__name__, attribName))

        if value is not None:
            if not isinstance(value, str):
                raise ValueError('%s: %r must be a string' %
                                 (cls.__name__, attribName))

            if len(value) == 0 and not allowEmpty:
                raise ValueError('%s: %r must be set' %
                                 (cls.__name__, attribName))

            if altCharacter in value:
                raise ValueError('%s: Character %r not allowed in %r; got %r' %
                                 (cls.__name__, altCharacter, attribName, value))

            if not allowWhitespace and commonUtil.contains_whitespace(value):
                raise ValueError('%s: Whitespace not allowed in %r; got %r' %
                                 (cls.__name__, attribName, value))

    @classmethod
    def _defaultName(cls) -> str:
        """default name to use for objects with a name/title
        """
        return 'my%s' % cls.className

    @classmethod
    def _uniqueName(cls, project, name=None) -> str:
        """Return a unique name based on name (set to defaultName if None)
        """
        from ccpn.util import Common as commonUtil

        if name is None:
            name = cls._defaultName()
        cls._validateStringValue('name', name)
        name = name.strip()
        names = [sib.name for sib in getattr(project, cls._pluralLinkName)]
        while name in names:
            name = commonUtil.incrementName(name)
        return name

    #=========================================================================================
    # Implementation functions - necessary as there is no abstractWrapperObject
    #=========================================================================================

    def _resetUniqueId(self, value):
        """Reset the uniqueId
        CCPN Internal - although not sure whether actually required here
        """
        # if self._chemicalShiftList._searchChemicalShifts(uniqueId=value):
        #     raise ValueError(f'{self.className}._resetUniqueId: uniqueId {value} already exists')
        self._uniqueId = int(value)
        self._ccpnSortKey = (id(self.project), _importOrder.index(self.className), self._uniqueId)

    def _resetIds(self, oldId):
        """Reset the pids in the project lists
        """
        project = self._project
        className = self.className

        # update pid:object mapping dictionary
        dd = project._pid2Obj.get(className)
        if dd is None:
            dd = {}
            project._pid2Obj[className] = dd
            project._pid2Obj[self.shortClassName] = dd
        # assert oldId is not None
        if oldId in dd:
            del dd[oldId]
        dd[self.id] = self

    def _finaliseAction(self, action: str, **actionKwds):
        """Do v3 core object level finalisation, and execute all notifiers
        action is one of: 'create', 'delete', 'change', 'rename'
        """
        project = self.project
        if action == 'create':
            # housekeeping -
            #   handle the modifying of __str__/__repr__ here so that it does not require
            #   extra calls to _isDeleted which may crash on loose objects in the undo-deque (or elsewhere)
            #   update the pid2Obj list
            self._deleted = False
            self._isDeleted = False
            project._finalisePid2Obj(self, 'create')
        elif action == 'delete':
            self._deletedId = str(self.id)
            self._deleted = True
            self._isDeleted = True
            project._finalisePid2Obj(self, 'delete')

        if project._notificationBlanking:
            # do not call external notifiers
            # structures should be in a valid state at this point
            return

        # notify any external objects - these should NOT modify any objects/structures
        className = self.className
        # NB 'AbstractWrapperObject' not currently in use (Sep 2016), but kept for future needs
        iterator = (project._context2Notifiers.setdefault((name, action), OrderedDict())
                    for name in (className, 'AbstractWrapperObject'))

        if action == 'rename':
            try:
                # get the stored value BEFORE renaming - valid for undo/redo
                oldPid = self._oldPid
            except:
                oldPid = self.pid
            if oldPid != self.pid:
                self._resetIds(oldPid.id)
                self._project._collectionList._resetItemPids(oldPid, self.pid)

            for dd in iterator:
                for notifier in tuple(dd):
                    notifier(self, oldPid, **actionKwds)

            # for reference - as per AbstractWrapperObject
            # for obj in self._getDirectChildren():  # no children defined for anything yet - consider later
            #     obj._finaliseAction('rename')

        else:
            # Normal case - just call notifiers - as per AbstractWrapperObject
            for dd in iterator:
                for notifier in tuple(dd):
                    notifier(self, **actionKwds)

        # propagate the action to explicitly associated (generally child) instances
        for obj, action in self._finaliseChildren:
            obj._finaliseAction(action)
        self._finaliseChildren = []

        return True

    def delete(self):
        """Delete the shift
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: function {repr(_getframe().f_code.co_name)} not implemented')

    def getByPid(self, pid: str):
        """Get an arbitrary data object from either its pid (e.g. 'SP:HSQC2') or its longPid
        (e.g. 'Spectrum:HSQC2')

        Returns None for invalid or unrecognised input strings.
        """
        if pid is None or len(pid) is None:
            return None

        obj = None

        # return if the pid does not conform to a pid definition
        if not Pid.isValid(pid):
            return None

        pid = Pid(pid)
        dd = self._project._pid2Obj.get(pid.type)
        if dd is not None:
            obj = dd.get(pid.id)
        if obj is not None and obj._isDeleted:
            raise RuntimeError(f'{self.className}.getByPid "%s" defined a deleted object' % pid)
        return obj

    @classmethod
    def _linkWrapperClasses(cls, ancestors: list = None, Project: 'Project' = None, _allGetters=None):
        """Recursively set up links and functions involving children for wrapper classes
        V3CoreObjectABC should NOT link to any wrapped classes
        """
        # Fill in Project._className2Class map - add V3CoreObject name to dicts
        dd = Project._className2Class
        dd[cls.className] = dd[cls.shortClassName] = cls
        Project._className2ClassList.extend([cls.className, cls.shortClassName, cls])

        dd = Project._classNameLower2Class
        dd[cls.className.lower()] = dd[cls.shortClassName.lower()] = cls
        Project._classNameLower2ClassList.extend([cls.className.lower(), cls.shortClassName.lower(), cls])

    @classmethod
    def _getChildClasses(cls, recursion: bool = False) -> list:
        """list of valid child classes of cls
        """
        return []

    @classmethod
    def _getAllWrappedData(cls, parent) -> list:
        """get wrappedData - V3CoreObjectABC do not link to _wrappedData
        """
        return []

    @property
    def _objectVersion(self) -> Optional[VersionString]:
        """Contains the current _objectVersion for V3CoreObjects
        Not implemented here as _objectVersion is handled by the wrapperList
        """
        getLogger().debug2(f'{self.__class__.__name__}._objectVersion not implemented')
        return None

    @_objectVersion.setter
    def _objectVersion(self, version):
        getLogger().debug2(f'{self.__class__.__name__}._objectVersion not implemented')

    @property
    def _ccpnInternalData(self) -> Optional[dict]:
        """get _ccpnInternalData - V3CoreObjectABC do not link to _wrappedData
        Not implemented
        """
        getLogger().debug2(f'{self.__class__.__name__}._ccpnInternalData not implemented')
        return None

    @_ccpnInternalData.setter
    def _ccpnInternalData(self, value):
        getLogger().debug2(f'{self.__class__.__name__}._ccpnInternalData not implemented')

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    @property
    def collections(self) -> tuple:
        """Return the list of collections containing this core object
        """
        # dynamic lookup from the project collectionList
        return self.project._collectionList.searchCollections(self)

    @logCommand(get='self')
    def addToCollection(self, collection):
        """Add core object to the named collection
        """
        from ccpn.core.Collection import Collection

        if not isinstance(collection, Collection):
            raise ValueError(f'{self.__class__.__name__}.addToCollection: {collection} is not a collection')

        collection.addItems([self])

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    def _tryToRecover(self):
        """Routine to try to recover an object that has not loaded correctly to repair integrity
        """
        pass

    @deleteV3Object()
    def _deleteWrapper(self, wrapperList, newDeletedObjects, newObjects, oldDeletedObjects, oldObjects):
        """Delete a pure V3 wrapped object
        Method is wrapped with create/delete notifier
        CCPN Internal - Not standalone - requires functionality from wrapperList
        """
        # add an undo/redo item to recover wrapped objects
        with undoStackBlocking() as addUndoItem:
            # replace the contents of the internal list with the original/recovered items
            addUndoItem(undo=partial(wrapperList._undoRedoObjects, oldObjects),
                        redo=partial(wrapperList._undoRedoObjects, newObjects))

        # NOTE:ED - do stuff here

        with undoStackBlocking() as addUndoItem:
            addUndoItem(undo=partial(wrapperList._undoRedoDeletedObjects, oldDeletedObjects),
                        redo=partial(wrapperList._undoRedoDeletedObjects, newDeletedObjects))


def _newWrappedObject(project: 'Project', wrapperList, klass, _uniqueId: Optional[int] = None):
    """Create a new object attached to the wrappedData.

    :param project: core project
    :param wrapperList: parent list object containing v3 core objects
    :param klass: class type of object
    :param _uniqueId: _unique int identifier
    :return: a new Wrapped object instance.
    """

    result = klass(project, wrapperList, _uniqueId=_uniqueId)
    if result is None:
        raise RuntimeError(f'{wrapperList.__class__.__name__}._new{klass.__name__}: unable to generate new item')

    return result
