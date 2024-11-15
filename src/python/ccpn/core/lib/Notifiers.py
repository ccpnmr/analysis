"""
Notifier extensions, wrapping it into a class that also acts as the called function,
dispatching the 'user' callback if required.

The Notifier can be defined relative to any valid V3 core object, as well as the current
object as it first checks if the triggered signature is valid.

The triggers CREATE, DELETE, RENAME and CHANGE can be combined in the call signature,
preventing unnecessary code duplication. They are translated into multiple notifiers
of the 'Project V3-machinery' (i.e., the Rasmus callbacks)

The callback function is passed a callback dictionary with relevant info (see
docstring of Notifier class). This idea was copied from the Traitlets package.

April 2017: First design by Geerten Vuister

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
__dateModified__ = "$dateModified: 2024-11-15 09:07:12 +0000 (Fri, November 15, 2024) $"
__version__ = "$Revision: 3.2.10.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys

from functools import partial
from collections import OrderedDict
from typing import Callable, Any, Optional
from itertools import permutations
import weakref
from contextlib import contextmanager

from ccpn.core.lib.WeakRefList import _WeakRefList

from ccpn.util.Logging import getLogger
from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.Common import Sentinel

from ccpn.framework.Application import getCurrent, getProject

DEBUG = False
_debugIds = ()

_STRICT = True  # Flag to enforce type checking; relaxed for testing ccpnv4 code

# _debugIds = (75, 84, 92, 94,95,96)  # for these _id's, debug will be True. This allows for selective debugging


def skip(*args, **kwargs):
    """Do nothing"""
    pass


class NotifierABC(object):
    """
    Abstract base class for Notifier, GuiNotifier and TraitNotifier classes
    """
    _currentIndex = 0

    CREATE = 'create'
    DELETE = 'delete'
    POST_DELETE = 'postDelete'
    UNDELETE = 'undelete'
    RENAME = 'rename'
    CHANGE = 'change'
    OBSERVE = 'observe'
    # For backwards compatibility
    CURRENT = 'current'

    ANY = '<Any>'

    # needs subclassing
    _triggerKeywords = ()

    # callback dict keywords
    NOTIFIER = 'notifier'               # The Notifier instance

    # the following can also be obtained from the Notifier instance
    THEOBJECT = 'theObject'             # The object for which a notifier was set
    TRIGGER = 'trigger'                 # The trigger (see below)
    TARGETNAME = 'targetName'           # The traget name for trigger (see below)

    # The actual callback values/object
    OBJECT = 'object'                   # the object created, deleted, changed or observed
    PID = 'pid'                         # the pid of the object (trigger RENAME)
    OLDPID = 'oldPid'                   # the old or previous pid of the object (trigger RENAME)
    VALUE = 'value'                     # the (new) value (trigger CHANGE, OBSERVE)
    PREVIOUSVALUE = 'previousValue'     # the old or previous value (trigger CHANGE, OBSERVE)
    ATTRIBUTE_NAME = 'attributeName'    # the name of the attribute that has changed (trigger CHANGE, OBSERVE)
    ITEMS_CHANGED = 'itemsChanged'      # The items in list/dict that have changed (trigger OBSERVE)
    SUBTYPE = 'subType'                 # The operation, e.g. __setitem__, that changed the list/dict
    SPECIFIERS = 'specifiers'

    def __init__(self, theObject: Any,
                       trigger: str,
                       targetName: str,
                       callback: Callable = None,
                       setterObject = None,
                       debug: bool = False, **kwds):

        # Sanity checks
        if len(self._triggerKeywords) == 0:
            raise RuntimeError('Not trigger keywords defined; assure proper subclassing definitions')

        if theObject is None:
            raise RuntimeError(f'NotifierABC.__init__(): theObject is None')
        self._theObject = theObject  # The object we are monitoring

        # check for previous list of triggers
        if isinstance(trigger, (list, tuple)):
            raise ValueError(f'NotifierABC.__init__(): invalid tuple or list trigger "{trigger}"')

        if trigger not in self._triggerKeywords:
            raise ValueError(f'NotifierABC.__init__(): invalid trigger "{trigger}" for {type(self)}')
        self._trigger: str = trigger

        if targetName is None:
            raise ValueError(f'NotifierABC.__init__(): invalid targetName None')
        self._targetName: str = targetName

        # if targetName == NotifierABC.CHANGE:
        #     print('>>> NotifierABC.__init__(): change')  # for debugging

        if callback is None:
            raise ValueError(f'Invalid callback None for {type(self)}')
        self._callback: Callable = callback

        # initialisations
        self._id: int = NotifierABC._currentIndex
        NotifierABC._currentIndex += 1

        self._kwds: dict = kwds
        self._unregister = None

        self._setterObject = weakref.ref(setterObject) if setterObject is not None else None

        self._attributeName: str | None = None  # set by sub-classed __init__'s

        self._debug: bool = debug or DEBUG or self._id in _debugIds
        self._isBlanked: bool = False  # ability to blank notifier
        self._isRegistered: bool = False  # flag indicating if the notifier is registered
        self._isExecuting: bool = False  # Flag to indicate notifier callback is executing
        self._objectList: list = []  # A list of object that notifier will be firing on;
                                     # assembled as part of the _doFireNotifiers context manager
        self._appliesToTheObject: bool = False  # A flag to indicate that the notifier is set to fire only
                                                # on theObject; i.e. always True for OBSERVE, False for CREATE and
                                                # variable for (POST_)DELETE and RENAME.

    @property
    def id(self):
        """:return the id of self
        """
        return self._id

    @property
    def theObject(self):
        """:return the theObject of self
        """
        return self._theObject

    @property
    def trigger(self):
        """:return the trigger of self
        """
        return self._trigger

    @property
    def targetName(self):
        """:return the targetName of self
        """
        return self._targetName

    @property
    def attributeName(self):
        """:return the attributeName of self
        """
        return self._attributeName

    @property
    def setterObject(self):
        """:return the setterObject  of self
        """
        return self._setterObject()  # ._setterObject is a weakRef

    @property
    def isRegistered(self) -> bool:
        """:return True if notifier is still registered; i.e. active"""
        return self._isRegistered

    @property
    def isExecuting(self) -> bool:
        """:return True if notifier callback is executing
        """
        return self._isExecuting

    def setDebug(self, flag: bool):
        """Set debug output on/off"""
        self._debug = flag

    def setBlanking(self, flag: bool):
        """Set blanking on/off"""
        self._isBlanked = flag

    @property
    def isBlanked(self) -> bool:
        """:return True if notifier is blanked
        """
        return self._isBlanked

    def triggersOn(self, trigger) -> bool:
        """Return True if notifier triggers on trigger"""
        return trigger == self._trigger

    def registerNotifier(self):
        """Register self with theObject
        """
        NotifierBase._registerNotifier(notifier=self, theObject=self._theObject)
        self._isRegistered = True

        if self._debug:
            sys.stderr.write('>>> registered %s\n' % self)

    def unRegisterNotifier(self):
        """Reset the attributes; unregisters from theObject and deletes self
        """
        if self._debug:
            sys.stderr.write('>>> unRegister %s\n' % self)

        if not self.isRegistered:
            raise RuntimeError(f'unregisterNotifier(): {self} is not registered')

        NotifierBase._unRegisterNotifier(notifier=self, theObject=self._theObject)
        self._isRegistered = False

        self._theObject = None
        self._callback = None
        self._unregister = None
        self._setterObject = None
        self._isExecuting = False

        del(self)

    def newCallbackDict(self,
                        previousValue=Sentinel, value=Sentinel, attributeName=Sentinel,
                        obj=Sentinel, object=Sentinel,
                        oldpid=Sentinel, pid=Sentinel,
                        specifiers=None,
                        itemsChanged=Sentinel
                        ) -> dict:
        """Create and return a dict with all the callback keys.
        Both the obj en object arguments are mapped to the OBJECT key
        """
        callbackDict = CallbackDict(
                previousValue=previousValue,
                value=value,
                attributeName=attributeName,
                obj=obj,
                object=object,
                oldpid=oldpid,
                pid=pid,
                specifiers=specifiers,
                itemsChanged=itemsChanged
        )
        callbackDict.updateFromNotifier(self)
        return callbackDict

    @staticmethod
    def _isEqual(value1, value2):
        """Return true if values are equal, accounting for tuple/list conversion"""
        if isinstance(value1, tuple):
            value1 = list(value1)
        if isinstance(value2, tuple):
            value1 = list(value2)
        return value1 == value2

    def __str__(self) -> str:
        if self.isRegistered:
            if self._isBlanked:
                _exec = 'blanked'
            elif self.isExecuting :
                _exec = 'executing'
            else:
                _exec = 'silent'

            _pid = self._theObject.pid if hasattr(self._theObject, 'pid') else self._theObject.__class__.__name__

            # return f'<{self.__class__.__name__} {self.id} ({_exec}): theObject={_pid!r}: {self._trigger!r}->{self._targetName!r}>'

        else:
            _exec = 'unregistered'
            _pid = self._theObject.pid if (self._theObject and hasattr(self._theObject, 'pid'))\
                                           else 'None'

            # return f'<{self.__class__.__name__} {self.id} (unregistered): theObject=None: {self._trigger!r}->{self._targetName!r}>'

        _setter = self.setterObject.pid if hasattr(self.setterObject, 'pid') else self.setterObject.__class__.__name__
        _name = self.__class__.__name__

        return f'<{_name} {self.id} ({_exec}): {_pid}:({self._trigger!r}->{self._targetName!r},{self._appliesToTheObject}); setter:{_setter}>'

    __repr__ = __str__


class CallbackDict(AttributeDict):
    """A class to implement the callbackDict, assuring all keys
    """

    def __init__(self, previousValue=Sentinel, value=Sentinel, attributeName=Sentinel,
                 obj=Sentinel, object=Sentinel,
                 oldpid=Sentinel, pid=Sentinel,
                 specifiers=None,
                 itemsChanged=Sentinel
                 ) -> dict:
        """Create and return a dict with all the callback keys.
        Both the obj en object arguments are mapped to the OBJECT key
        """
        _temp = {
            NotifierABC.NOTIFIER      : Sentinel,
            NotifierABC.THEOBJECT     : Sentinel,
            NotifierABC.TRIGGER       : Sentinel,
            NotifierABC.TARGETNAME    : Sentinel,
            NotifierABC.ATTRIBUTE_NAME: attributeName,
            NotifierABC.PREVIOUSVALUE : previousValue,
            NotifierABC.VALUE         : value,
            NotifierABC.ITEMS_CHANGED : itemsChanged,
            NotifierABC.OBJECT        : obj or object,
            NotifierABC.OLDPID        : oldpid,
            NotifierABC.PID           : pid,
            NotifierABC.SPECIFIERS    : specifiers,
        }
        self.update(_temp)

    def updateFromNotifier(self, notifier):
        """Update self with values from the notifier
        """
        self[NotifierABC.NOTIFIER] = notifier
        self[NotifierABC.THEOBJECT] = notifier.theObject
        self[NotifierABC.TRIGGER] = notifier.trigger
        self[NotifierABC.TARGETNAME] = notifier.targetName

    def checkForSentinels(self, keys: list | tuple):
        """Check callbackDict keys that have sentinel value
        :param keys: the list or tuple with keys to check
        :raises ValueError when detected
        """
        for _key in keys:
            if value := self.get(_key, Sentinel) == Sentinel:
                _notifier = self.get(NotifierABC.NOTIFIER)
                raise ValueError(f'Checking {_notifier}: expected value for key {_key!r}')

    def check(self):
        """check self for presence of required values for notifier depending on trigger
        :raises ValueError when errors are detected
        """
        if (notifier := self.get(NotifierABC.NOTIFIER)) == Sentinel:
            raise ValueError(f'Checking CallbackDict: notifier undefined')
        # Some sanity checks on the callbackDict:
        if notifier.trigger == NotifierABC.OBSERVE:
            self.checkForSentinels(
                    [NotifierABC.ATTRIBUTE_NAME, NotifierABC.VALUE, NotifierABC.PREVIOUSVALUE]
            )
        elif notifier.trigger == NotifierABC.RENAME:
            self.checkForSentinels(
                    [NotifierABC.OBJECT, NotifierABC.PID, NotifierABC.OLDPID]
            )
        elif notifier.trigger in (NotifierABC.DELETE, NotifierABC.CREATE):
            self.checkForSentinels(
                    [NotifierABC.OBJECT]
            )


class Notifier(NotifierABC):
    """
    Notifier Base class:

    triggers callback function with signature:  callback(callbackDict [, **kwargs])

    ____________________________________________________________________________________________________________________

    trigger             targetName           callbackDict keys          Notes
    ____________________________________________________________________________________________________________________

     Notifier.CREATE    className             theObject, object,        targetName: valid child className of theObject
                                              targetName,               (any for project instances)
                                              pid,
                                              trigger, notifier

     Notifier.DELETE    className             theObject, object,        targetName: valid child className of theObject
                                              targetName,               (any for project instances)
                                              pid,
                                              trigger, notifier

     Notifier.RENAME    className             theObject, object         targetName: valid child className of theObject
                                              targetName,               (any for project instances)
                                              pid, oldPid,
                                              trigger, notifier

     Notifier.CHANGE    className             theObject, object         targetName: valid child className of theObject
                                              targetName,               (any for project instances)
                                              pid,
                                              trigger, notifier

     Notifier.OBSERVE   attributeName         theObject,                 attributeName: valid attribute name of theObject
                                              value, previousValue,
                                              attributeName,
                                              trigger, notifier

    Implementation:

      Uses current notifier system from Project filters for child objects of type targetName in theObject.
      TargetName does need to denote a valid child-class, except for Project instances
      which can be triggered by all classes.

      The callback provides a dict with several (key, value) pairs (idea following the Traitlets concept).
      Note that this dict also contains a reference to the Notifier object itself.

    """

    # Trigger keywords (from NotifierABC)
    # CREATE = 'create'
    # DELETE = 'delete'
    # RENAME = 'rename'
    # CHANGE = 'change'
    # OBSERVE = 'observe'
    #
    # ANY = '<Any>'

    _triggerKeywords = (NotifierABC.CREATE, NotifierABC.DELETE, NotifierABC.RENAME,
                        NotifierABC.CHANGE, NotifierABC.OBSERVE)

    def __init__(self,
                 theObject: Any,
                 trigger: str,
                 targetName: str,
                 callback: Callable,
                 setterObject=None,
                 onceOnly=False,
                 debug=False,
                 **kwds
                 ):
        """
        Create Notifier object;

        :param theObject: valid V3 core object to watch
        :param trigger: a valid trigger keyword
        :param targetName: valid className, attributeName or ANY
        :param callback: callback function with signature: callback(callbackDict, **kwargs])
        :param setterObject: Object that was setting the Notifier
        :param onceOnly: If True, only one of multiple copies is executed (from underpinning V3-notifiers mechanism)
        :param debug: set debug
        :param **kwds: optional keywords arguments passed to callback
        """

        from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject  # local import to avoid cycles
        from ccpn.core._implementation.V3CoreObjectABC import V3CoreObjectABC  # local import to avoid cycles
        from ccpn.framework.Current import Current  # local import to avoid cycles

        if theObject is None:
            raise ValueError('Notifier: object is None')

        # GWV 20/3/24: No longer able to set notifier on Current; use CurrentNotifier class
        if isinstance(theObject, Current) or \
            (isinstance(trigger, (list, tuple)) and self.CURRENT in trigger):
            raise ValueError(f'Implementation has changed: use CurrentNotifier for current object')

        if _STRICT and not isinstance(theObject, (AbstractWrapperObject, V3CoreObjectABC)):
            raise ValueError(f'Notifier: invalid object; expected AbstractWrapper or V3CoreObject, got {type(theObject)}')

        if targetName is None:
            raise ValueError(f'Invalid targetName {targetName}')

        super().__init__(theObject=theObject,
                         trigger=trigger,
                         targetName=targetName,
                         callback=callback,
                         setterObject=setterObject,
                         debug=debug,
                         **kwds
                         )

        if (_project := getProject()) is None:
            raise RuntimeError(f'Undefined project: cannot register notifier for {theObject}')
        self._project = weakref.ref(_project)  # toplevel Project instance for theObject
        self._isProject = (theObject == _project)  # theObject is the toplevel Project instance

        self._previousValue = None  # used to store the value of attribute to observe for change

        # Limitation check:
        # Various triggers are set to fire for an object of class targetName.
        # (i.e. they are effectively class notifiers)
        if trigger in (NotifierABC.CHANGE, NotifierABC.CREATE, NotifierABC.DELETE, NotifierABC.RENAME):
            # for these triggers;
            # notifier can only be set on an object whose child classes are of type targetName
            # or
            # can be set on project.
            _allowedClasses = [] if self._isProject \
                                 else [klass.className for klass in theObject._childClasses]
            if not (self._isProject or targetName in _allowedClasses):
                raise ValueError(
                    f'Notifier ({trigger!r},{targetName!r}) can not be set on {theObject}')

        # Registering in current implementation
        if trigger == Notifier.OBSERVE:
            # OBSERVE special case, as the current underpinning implementation does not allow this directly
            # Hence, we track all changes to the object class, filtering those that apply

            if targetName == self.ANY or not hasattr(theObject, targetName):
                raise ValueError(
                    f'Notifier.__init__(): invalid targetName {targetName!r} for {theObject}')

            self._attributeName = targetName
            # self._previousValue = getattr(theObject, self._attributeName)
            self._appliesToTheObject = True

            # Now change the signature when registering in the V3 machinery
            # func = _project._registerV3Notifier(className=theObject.className,
            #                                     target=Notifier.CHANGE,
            #                                     func=self,
            #                                     onceOnly=onceOnly)
            # The info needed for unregistering
            # self._unregister = (theObject.className, Notifier.CHANGE, func)

        else:
            func = _project._registerV3Notifier(className=targetName,
                                                target=self._trigger,
                                                func=self,
                                                onceOnly=onceOnly)
            # The info needed for unregistering
            self._unregister= (targetName, self._trigger, func)

        self.registerNotifier()

    @property
    def project(self):
        """Return the project
        """
        # implemented as a weak reference
        return self._project()

    def unRegisterNotifier(self):
        """
        unregister the notifiers
        """
        # >>>>>>
        if self._debug:
            sys.stderr.write('>>> un-registering %s\n' % self)

        if not self.isRegistered:
            return

        # Unregister from the V3 notifier machinery
        # (if it was registered; not for OBSERVE!)
        if self._unregister:
            targetName, trigger, func = self._unregister
            self.project._unRegisterV3Notifier(targetName, trigger, func)

        # at the end as it clears all attributes
        super().unRegisterNotifier()

    def __call__(self, obj, parameter2=None, **kwds):
        """
        wrapper, accommodating the callback from V3-project notifier implementation
        """
        if not self.isRegistered:
            getLogger().warning(f'Notifier.__call__(): Triggering unregistered notifier {self}')
            return

        if self._isBlanked:
            return

        if obj is None:
            raise RuntimeError('Notifier.__call__(): obj is None')

        if self._debug:
            sys.stderr.write(f'>>> {self}.__call__():\n')
            sys.stderr.write(f'    {obj = }\n' )
            sys.stderr.write(f'    {parameter2 = }\n' )

        # check if the trigger applies:
        notifierFired = False

        # OBSERVE, targetName special case
        if self.trigger == Notifier.OBSERVE and self.targetName != self.ANY \
            and obj.pid == self._theObject.pid:

            # The check below catches all changes to obj that do not involve targetName,
            # as only when it has changed its value will we trigger the callback
            value = getattr(self._theObject, self.attributeName)
            if  not self._isEqual(value, self._previousValue):

                callbackDict = self.newCallbackDict(obj=obj,
                                                    value=value,
                                                    previousValue=self._previousValue,
                                                    attributeName=self.attributeName
                                                    )

                self._isExecuting = True
                self._callback(callbackDict, **self._kwds)
                self._isExecuting = False
                self._previousValue = value
                notifierFired = True

        elif self._isProject or obj._parent.pid == self.theObject.pid:
            if len(kwds) > 0:
                pass  #  for debug breakpoint
            callbackDict = self.newCallbackDict(obj=obj,
                                                oldpid=parameter2,
                                                pid=obj.pid,
                                                specifiers=kwds
                                                )
            kwds.update(self._kwds)

            self._isExecuting = True
            self._callback(callbackDict)
            self._isExecuting = False
            notifierFired = True

        if self._debug:
            _tmp = 'FIRED' if notifierFired else 'not-FIRED'
            sys.stderr.write('%-9s func:%s\n' % (_tmp, self._callback))

        return


class CurrentNotifier(NotifierABC):
    """
    Current-Notifier class:

    triggers callback function with signature:  callback(callbackDict [, **kwargs])

    ____________________________________________________________________________________________________________________

    targetName           callbackDict keys          Notes
    ____________________________________________________________________________________________________________________

    attributeName         theObject,targetName      theObject will be current object
                          value, previousValue,     targetName: valid attribute name of current
                          trigger, notifier

    Implemention:

      Uses current notifier system from Current;

      The callback provides a dict with several key, value pairs (idea following the Traitlets concept).
      Note that this dict also contains a reference to the Notifier object itself; this way it can be used
      to pass-on additional implementation specific information to the callback function.

    """

    _triggerKeywords = (NotifierABC.CURRENT,)

    def __init__(self,
                 targetName: str,
                 callback: Callable,
                 setterObject=None,
                 debug=False,
                 ):
        """
        Create CurrentNotifier object;
        :param targetName: valid Current attributeName or ANY
        :param callback: callback function with signature: callback(callbackDict)
        :param setterObject: Object that was setting the Notifier
        :param debug: set debug for this notifier
        """

        # some sanity checks
        if (_current := getCurrent()) is None:
            raise RuntimeError(f'CurrentNotifier(): unable to get Current instance')

        if targetName is None or not hasattr(_current, targetName):
            raise ValueError(f'Invalid targetName "{targetName}"')

        super().__init__(theObject=_current,
                         trigger=self.CURRENT,
                         targetName=targetName,
                         setterObject=setterObject,
                         debug=debug,
                         callback=callback,
                         )

        self._unregister = None  # The info needed for unregistering

        # Store the value of attribute to observe for change
        self._previousValue = getattr(_current, targetName)

        # current has its own notifier system
        # to register strip, the keywords is strips!
        tName = targetName + 's' if targetName == 'strip' else targetName
        func = _current.registerNotify(self, tName)
        self._unregister = (tName, func)
        self.registerNotifier()

    def unRegisterNotifier(self):
        """unregister self from theObject
        """
        if self._debug:
            sys.stderr.write(f'>>> un-registering {self}\n')

        if not self.isRegistered:
            return

        # Unregister from the Current notifier machinery
        targetName, func = self._unregister
        self._theObject.unRegisterNotify(func, targetName)

        # at the end, as it clears all attributes and unregisters itself from TheObject
        super().unRegisterNotifier()

    def __call__(self, _val):
        """
        wrapper, accommodating the different triggers before firing the callback
        """

        if not self.isRegistered:
            getLogger().warning(f'Triggering unregistered notifier {self}')
            return

        if self._isBlanked:
            return

        notifierFired = False
        value = getattr(self._theObject, self._targetName)

        if self._debug:
            sys.stderr.write(f'>>> {self}.__call__(): {value = }\n' )

        # Fire the notifier is there has been a change
        if not self._isEqual(value, self._previousValue):
            callbackDict = self.newCallbackDict(
                    obj=self._theObject,
                    value=value,
                    previousValue=self._previousValue,
            )

            self._callback(callbackDict)
            notifierFired = True
            self._previousValue = value

        if self._debug:
            _tmp = 'FIRED' if notifierFired else 'not-FIRED'
            sys.stderr.write('%-9s func:%s\n' % (_tmp, self._callback))

        return
# end class


class _NotifierList(list):
    """A class for backward compatibility with the old Notifier implementation.
    The latter allowed for multiple triggers for a single Notifier.
    The setNotifier() method now returns a NotifierList class, which has a unRegister()
    method, to mimic the behavior of the earlier implementation, which returned NotifierABC
    subclassed instances.
    """

    def unRegisterNotifier(self):
        """Un-register all notifiers of self
        For backward compatibility
        """
        for notifier in self:
            if not isinstance(notifier, NotifierABC):
                raise RuntimeError(f'unRegister(): Invalid notifier {notifier}')
            notifier.unRegisterNotifier()
# end class


class _NotifiersDict(dict):
    """A class to retain all notifiers of an object
    Dict comprised of {trigger : {id:notifier}} (i.e. a dict of dicts)
    {id:notifier} dict optionally a WeakReferenceDict
    """

    def __init__(self, useWeakRef=False):
        """Init the dict
        :param useWeakRef: flag to use WeakValueDictory for the {id:notifier} dict
        """
        super().__init__()
        self.useWeakRef = useWeakRef

    def addNotifier(self, notifier: NotifierABC):
        """Add notifier to self, in a trigger dependent way
        """
        if not isinstance(notifier, NotifierABC):
            raise TypeError(f'addNotifier(): expected NotifierABC subclass instance, got {type(notifier)}')

        if self.useWeakRef:
            _dict = self.setdefault((notifier._trigger, notifier._targetName), weakref.WeakValueDictionary())
        else:
            _dict = self.setdefault((notifier._trigger, notifier._targetName), {})

        _id = notifier.id
        # this should never happen; hence just a check
        if _id in _dict:
            raise RuntimeError(f'A notifier with id "{_id}" already exists; cannot add {notifier}')
        _dict[_id] = notifier

    def deleteNotifier(self, notifier: NotifierABC):
        """Delete notifier from self
        :raise ValueError if notifier is not part of self
        """
        if not isinstance(notifier, NotifierABC):
            raise TypeError(f'deleteNotifier(): expected NotifierABC subclass instance, got {type(notifier)}')

        if (_dict := self.get((notifier._trigger, notifier._targetName), None)) is None:
            raise ValueError(f'deleteNotifier(): {notifier} is not contained in self')
        if notifier.id not in _dict:
            raise ValueError(f'deleteNotifier(): {notifier} is not contained in self')
        del( _dict[notifier.id] )

    @property
    def allNotifiers(self) -> dict:
        """:return A list of all notifiers
        """
        _ll = [_item for _dict in self.values() for _item in _dict.values()]
        return _ll

    def allNotifiersAsDict(self) -> dict:
        """:return A dict of (id, notifier) pairs of all notifiers
        """
        _ll = [_item for _dict in self.values() for _item in _dict.items()]
        return dict(_ll)

    def __str__(self):
        # Convert to dict of dicts for printing
        dd = dict([(key,dict(val)) for key, val in self.items()])
        return str(dd)

    __repr__ = __str__


class NotifierBase(object):
    """
    A class confering notifier management routines
    """
    #-----------------------------------------------------------------------------------------
    # name to keep in-sinc with NotifiersABC.registerNotifier() function (unfortunately)
    REGISTERED_NOTIFIERS_DICT = '_registeredNotifiersDict'
    #-----------------------------------------------------------------------------------------

    # A dict that contains all NotifierSignal instances as (name, instance) pairs.
    _notifierSignalsDict: dict = Sentinel

    # A dict that contains all NotifierProperty instances as (name, instance) pairs.
    _notifierPropertiesDict: dict = Sentinel

    def __init__(self):

        # A dict that maintains the Notifiers initiated by the object; i.e. by setNotifier, setGuiNotifier,
        # setCurrentNotifier, etc
        self._objectNotifiersDict = _NotifiersDict(useWeakRef=True)

        # A dict that maintains the Notifiers registered for the object; i.e. those that will be called in
        # response to changes to the object
        self._registeredNotifiersDict = _NotifiersDict()

        # Called with every init, but effectively only executed once per class;
        # Alternatively, it would need to go in some form of register() method for the class,
        # but as many Classes inherit from NotifierBase, and not all have this mechanism,
        # this implementation is "easier".
        self._findNotifierSignals()

    @classmethod
    def _findNotifierSignals(cls):
        """Fill the _notifierSignalsDict with any instances of a NotifierSignal;
        Called with every init, but only effectively executed once per class
        """
        if cls._notifierSignalsDict == Sentinel:
            cls._notifierSignalsDict = {}
            for name, val in vars(cls).items():
                if isinstance(val, NotifierSignal):
                    val.klass = cls
                    val.name = name
                    cls._notifierSignalsDict[name] = val
        # pass

    # @classmethod
    # def _findNotifierProperties(cls):
    #     """Fill the _notifierPropertiesDict with any instances of a NotifierProperty;
    #     Called with every init, but only effectively executed once per class
    #     """
    #     if cls._notifierPropertiesDict == Sentinel:
    #         cls._notifierPropertiesDict = {}
    #         for name, val in vars(cls).items():
    #             if isinstance(val, NotifierProperty):
    #                 val.klass = cls
    #                 val.name = name
    #                 cls._notifierPropertiesDict[name] = val
    #     # pass
    #-----------------------------------------------------------------------------------------
    # creating, registering and unregistering notifier set for self
    #-----------------------------------------------------------------------------------------

    @staticmethod
    def _registerNotifier(notifier: NotifierABC, theObject):
        """Register notifier with theObject;
        check for presence of REGISTERED_NOTIFIERS_DICT on theObject.

        staticmethod as not all objects that get notifiers registered (e.g. Widgets) inherit
        from NotifierBase
        """
        if not isinstance(notifier, NotifierABC):
            raise TypeError(f'{notifier} is not a valid notifier instance')

        if not hasattr(theObject, NotifierBase.REGISTERED_NOTIFIERS_DICT):
            # This is the case with widgets, that do get GuiNotifiers set
            # Hotfix; unelegant but....
            # This code is also in widgets.Base._init and used in DropBase to check
            getLogger().debug2(f'_registerNotifier: {theObject} appears not to be a subclass of NotifierBase'\
                               f'; hotfixing {NotifierBase.REGISTERED_NOTIFIERS_DICT}')
            setattr(theObject, NotifierBase.REGISTERED_NOTIFIERS_DICT, _NotifiersDict())

        theObject._registeredNotifiersDict.addNotifier(notifier)
        notifier._isRegistered = True

    @staticmethod
    def _unRegisterNotifier(notifier: NotifierABC, theObject):
        """Un-register notifier from the theObject
        :param notifier: a Notifier|CurrentNotifier|GuiNotifier instance

        staticmethod as not all objects that get notifiers registered (e.g. Widgets) inherit
        from NotifierBase
        """
        if not isinstance(notifier, NotifierABC):
            raise TypeError(f'{notifier} is not a valid notifier instance')

        if not hasattr(theObject, NotifierBase.REGISTERED_NOTIFIERS_DICT):
           raise RuntimeError(f'_unRegisterNotifier(): {theObject} has no {NotifierBase.REGISTERED_NOTIFIERS_DICT}')

        theObject._registeredNotifiersDict.deleteNotifier(notifier)
        notifier._isRegistered = False

    def _newNotifier(self, trigger: str, targetName: str, callback: Callable, setterObject, **kwds) -> Notifier:
        """
        Create a new NotifierABC subtype instance to be registered with self.
        The created notifier registers itself with _registeredNotifiersDict

        To be subclassed for different implementations; e.g. GuiNotifierBase, TraitNotifierBase, ...

        :param triggers: list of triggers to trigger callback
        :param targetName: valid className, attributeName (See Notifier doc string for details)
        :param callback: callback function with signature: callback(callbackDict, **kwds])
        :param setterObject: the object setting the notifier
        :param **kwds: optional keyword,value arguments to callback

        :return: a Notifier instance
        """
        _notifier = Notifier(theObject=self, trigger=trigger, targetName=targetName,
                             callback=callback, setterObject=setterObject, **kwds
                             )
        return _notifier

    #-----------------------------------------------------------------------------------------
    # Functionalities for managing Notifiers set by self
    #-----------------------------------------------------------------------------------------
    def _addNotifier(self, notifier: NotifierABC):
        """Add notifier to _objectNotifiersDict of self;
        :param notifier: a Notifier|CurrentNotifier|GuiNotifier instance
        """
        if not isinstance(notifier, NotifierABC):
            raise ValueError('"%s" is not a valid notifier instance' % notifier)

        self._objectNotifiersDict.addNotifier(notifier)

    def setNotifier(self, theObject, triggers: list|tuple, targetName: str|list|tuple|None, callback: Callable, **kwds) -> _NotifierList:
        """Set Notifier for (V3/V4) theObject;
        Store for management; i.e. removal with deleteNotifier() or deleteAllNotifiers()
        methods.

        :param theObject: (V3/V4) object to register a notifier with
        :param triggers: list of triggers to trigger callback
        :param targetName: valid className, attributeName, list|tuple of attributeNames or None (See Notifier doc string for details)
        :param callback: callback function with signature: callback(callbackDict, **kwds])
        :param **kwds: optional keyword,value arguments passed to callback

        :return: a _NotifierList instance
        """
        from ccpn.framework.Current import Current

        if theObject is None:
            raise ValueError(f'setNotifier(): undefined object')

        if not isinstance(triggers, (list,tuple)):
            raise TypeError(f'setNotifier(): invalid triggers; expected list or tuple, got {type(triggers)}')

        if len(triggers) == 0:
            raise ValueError(f'setNotifier(): no triggers (len=0)')

        if isinstance(theObject, Current) or triggers[0] == CurrentNotifier.CURRENT:
            raise ValueError(f'setNotifier(): Object or trigger refer to Current; use setCurrentNotifier() method instead')

        _targetNames = []
        if targetName is None or isinstance(targetName, str):
            _targetNames = [targetName]
        elif isinstance(targetName, (list,tuple)):
            _targetNames = targetName
        else:
            raise TypeError(f'setNotifier(): invalid targetName; expected str, list, tuple or None, got {type(targetName)}')

        result = _NotifierList()
        for _trigger in triggers:
            for _targetName in _targetNames:
                _notifier = theObject._newNotifier(
                                    trigger=_trigger,
                                    targetName=_targetName,
                                    callback=callback,
                                    setterObject=self,
                                    **kwds
                )
                result.append(_notifier)
                self._addNotifier(_notifier)

        return result

    def setGuiNotifier(self, theObject: 'AbstractWrapperObject',
                             triggers: list, targetNames: list,
                             callback: Callable) -> _NotifierList:
        """Set GuiNotifier on (V3/V4) theObject.
        Store for management; i.e. removal with deleteNotifier() or deleteAllNotifiers()
        methods.

        :param theObject: The (V3) object to register a notifier with
        :param triggers: list of triggers to trigger callback
        :param targetNames: a list of dropTargets (URLS, TEXT, PIDS, IDS)
        :param callback: callback function with signature: callback(callbackDict)

        :return: a _NotifierList instance
        """
        from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier  # To avoid circular imports

        result = _NotifierList()
        for _trigger in triggers:
            for _target in targetNames:
                _notifier = GuiNotifier(theObject=theObject,
                                        trigger=_trigger,
                                        targetName=_target,
                                        callback=callback,
                                        setterObject=self,
                                        )
                result.append(_notifier)
                self._addNotifier(_notifier)
        return result

    def setCurrentNotifier(self, targetName: str, callback: Callable) -> _NotifierList:
        """Set CurrentNotifier
        Store for management; i.e. removal with deleteNotifier() or deleteAllNotifiers()
        methods.

        :param targetName: a valid attribute of Current
        :param callback: callback function with signature: callback(callbackDict)

        :return: a _NotifierList instance
        """

        result = _NotifierList()
        notifier = CurrentNotifier(targetName=targetName,
                                   callback=callback,
                                   setterObject=self,
                                   )
        result.append(notifier)
        self._addNotifier(notifier)
        return result

    def _hasNotifier(self, notifier) -> bool:
        """Return True if self has notifier

        :param notifier: a NotifierABC subclass instance
        :return: True or False
        """
        if not isinstance(notifier, NotifierABC):
            raise ValueError('"%s" is not a valid notifier instance' % notifier)

        objNotifiers = self._objectNotifiersDict

        if len(objNotifiers) == 0:
            return False

        if (_dict := objNotifiers.get((notifier._trigger, notifier._targetName), None)) is None:
            return False

        return notifier.id in _dict

    def searchNotifiers(self, objects=(), triggers=(), targetName=None) -> list:
        """Search whether a notifier with the given parameters is already defined
        for objects.
        The triggers CREATE, DELETE, RENAME and CHANGE can be combined in the call signature

        :param objects: valid V3 core or current or widget or object which has notifiers
        :param triggers: list of trigger keywords
        :param targetName: valid className, attributeName or ANY

        :return: list of existing notifiers (can be empty)
        """
        allNotifiers = self._objectNotifiersDict.allNotifiers
        foundNotifiers = []
        for notifier in allNotifiers:
            if notifier._theObject in objects and \
               targetName == notifier._targetName and \
               notifier._trigger in triggers:
                    foundNotifiers.append(notifier)

        return foundNotifiers

    def deleteNotifier(self, notifier: NotifierABC | int):
        """Remove notifier associated self, unregister it and delete it

        :param notifier: a Notifier instance previously set by
                         setNotifier, setGuiNotifier or setCurrentNotifier
                         or
                         the notifier-id (an int)
        """
        if isinstance(notifier, int):
            _id = notifier
        elif isinstance(notifier, NotifierABC):
            _id = notifier.id
        else:
            raise TypeError(f'deleteNotifier(): {notifier} is not a valid type')

        _idDict = dict((ntf.id, ntf) for ntf in self._objectNotifiersDict.allNotifiers)
        if (_notifier := _idDict.get(_id, None)) is None:
            raise ValueError(f'deleteNotifier(): {notifier} is not a (valid) notifier of {self}')

        self._objectNotifiersDict.deleteNotifier(_notifier)
        _notifier.unRegisterNotifier()
        del(_notifier)

    def deleteAllNotifiers(self):
        """Unregister and delete all the notifiers associated with self
        """
        objNotifiers = self._objectNotifiersDict
        # allNotifiers returns a list, as contents are being changed this is crucial
        for notifier in objNotifiers.allNotifiers:
            notifier.unRegisterNotifier()
            del(notifier)

    def _getRegisteredNotifiersBySetter(self, setterObject) -> list[NotifierABC]:
        """:return a list of the registered notifier with ntf.setterObject == setterObject
        """
        return [_ntf for _ntf in self._registeredNotifiersDict.allNotifiers if _ntf.setterObject == setterObject]

    def _testCallback(self, callbackDict:dict, **kwds):
        """A method to test callbacks; print kwds, callbackDict
        """
        _ntf = callbackDict[NotifierABC.NOTIFIER]
        print(f'\n>>> _testCallback() >>>\n')

        key='kwds'
        print(f'{key:20} : {kwds}')

        for key, val in callbackDict.items():
            print(f'{key:20} : {val!r}')

    #-----------------------------------------------------------------------------------------
    # Notification firing
    #-----------------------------------------------------------------------------------------

    def _fireSingleNotifier(self, notifier, callbackDict: dict):
        """Fire notifier passing callbackDict to callback function
        :param callbackDict: parameters passed to callback function as callbackDict
        """
        if not isinstance(notifier, NotifierABC):
            raise TypeError(f'_fireSingleNotifier(): expected Notifier (sub-)type; got {type(notifier)}')

        if notifier.isExecuting:
            raise RuntimeError(f'_fireSingleNotifier(): {notifier} is executing')

        if not notifier.isRegistered:
            getLogger().warning(f'_fireSingleNotifier(): Triggering unregistered notifier {notifier}')
            return

        if notifier.isBlanked:
            return

        # get proper callbackDict and update with any values passed in
        _callbackDict = notifier.newCallbackDict()
        _callbackDict.update(callbackDict)
        # to avoid the callbackdict inserting the incorrect value for this notifier;
        # update it with the notifier settings
        _callbackDict.updateFromNotifier(notifier)
        # Some sanity checks on the callbackDict:
        _callbackDict.check()

        if notifier._debug:
            sys.stderr.write(f'>>> _fireSingleNotifier(): {notifier}\n' )
            sys.stderr.write(f'    callback = {notifier._callback}\n' )
            sys.stderr.write(f'    callbackDict = {_callbackDict}\n' )

        # execute the callback
        try:
            # V4NotifierBase._notifierStack.append((V4NotifierBase._notifierContextLevel, notifier))
            notifier._isExecuting = True
            notifier._callback(_callbackDict, **notifier._kwds)

        except Exception as es:
            getLogger().error(f'While firing {notifier}: {es}')
            raise RuntimeError(f'While firing {notifier}: {es}') from es

        finally:
            notifier._isExecuting = False
            # V4NotifierBase._notifierStack.pop()

    def _fireRegisteredNotifiers(self, trigger: str, targetName: str | None, callbackDict: dict ):
        """Fire notifiers registered with self of type trigger, targetName passing kwds to the callbackDict.
        :parameter trigger: fire Notifiers of type trigger
        :parameter targetName: targetName of the Notifiers to fire; if None, all notifiers with
                               trigger are fired
        :param callbackDict: values passed to callback function as callbackDict
        """
        objNotifiers = self._registeredNotifiersDict

        if targetName is None:
            _notifiers = [_ntf for _ntf in objNotifiers.allNotifiers
                               if _ntf.trigger == trigger]
        else:
            _tmp = objNotifiers.get((trigger,targetName), {})
            _notifiers = list(_tmp.values())

        # Just a quick check to bailout is there is nothing to do
        if len(_notifiers) == 0:
            return

        # Create a weak-reference to notifiers, so if they do get deleted during a callback
        # the routine still works. It will just loop over fewer notifiers.
        # NB: deleting the an active notifier is not allowed.
        _weakNotifiers = _WeakRefList(_notifiers)
        while (_notifier := _weakNotifiers.pop()) is not None:
            self._fireSingleNotifier(notifier=_notifier, callbackDict=callbackDict)

    #-----------------------------------------------------------------------------------------
    # Notification blanking
    #-----------------------------------------------------------------------------------------

    # blanking level - to allow for nested notification disabling
    _notificationBlanking = 0

    @classmethod
    def _increaseNotificationBlanking(cls):
        """Increase notification blanking for all notifiers;
        This will disable notifiers until _decreaseNotifcationBlanking() has reset the situation.
        Caller is responsible to make sure necessary notifiers are called, and to decrease after use
        NB. classmethod allows for calling without an instance
        """
        NotifierBase._notificationBlanking += 1

    @classmethod
    def _decreaseNotificationBlanking(cls):
        """Decrease notification blanking for all notifiers;
        Notifier execution is resumed if resulting value == 0
        NB. classmethod allows for calling without an instance
        """
        if NotifierBase._notificationBlanking == 0:
            raise RuntimeError("_decreaseNotificationBlanking(): cannot set _notificationBlanking < 0")
        NotifierBase._notificationBlanking -= 1

    def setBlankingAllNotifiers(self, flag):
        """Set blanking of all the notifiers of self to flag
        """
        objNotifiers = self._objectNotifiersDict
        for notifier in objNotifiers.allNotifiers:
            notifier.setBlanking(flag)

    @contextmanager
    def blankNotifications(self):
        """Convenience method to blank notifications
        """
        NotifierBase._increaseNotificationBlanking()
        try:
            # transfer control to the calling function
            yield

        except Exception as es:
            raise es

        finally:
            # clean up after blocking notifications
            NotifierBase._decreaseNotificationBlanking()


    #-----------------------------------------------------------------------------------------
    # api 'change' notification blanking level -
    # To be used with the apiNotificationBlanking context manager; e.g.
    # with apiNotificationBlanking():
    #   do something
    #
    _apiNotificationBlanking = 0

    @classmethod
    def _increaseApiNotificationBlanking(cls):
        """Increase api-notification blanking;
        This routine will disable api-notifiers until _decreaseApiNotifcationBlanking() has reset the situation.
        NB. classmethod allows for calling without an instance
        """
        NotifierBase._apiNotificationBlanking += 1

    @classmethod
    def _decreaseApiNotificationBlanking(cls):
        """Decrease api-notification blanking;
        Api-notifier execution is resumed if resulting value == 0
        NB. classmethod allows for calling without an instance
        """
        if NotifierBase._apiNotificationBlanking == 0:
            raise RuntimeError("_decreaseApiNotificationBlanking(): cannot set _apiNotificationBlanking < 0")
        NotifierBase._apiNotificationBlanking -= 1

#end class -----------------------------------------------------------------------------------------


class NotifierSignal(property):
    """A class for cross-object signalling.
    NotifierSignal defines a property that functions as a signal for other objects,
    as the latter can set OBSERVE notifiers for its value changing.

    e.g. in type MyClass:

        mySignal = NotifierSignal()

        def func1(self):
            .....
            self.mySignal = True

    elsewhere:
        myObject = MyClass()
        otherObject.setNotifier(myObject, [OBSERVE], 'mySignal', callback=someFunc)

    calling myObject.func1(), will trigger the callback someFunc()
    """

    def __init__(self):
        super().__init__(self._getter, self._setter)

        self.name: str | None = None   # initialised from first invocation of _setter()
        self.klass = None       # initialised from first invocation of _setter()
        self.counter: int = 0

    def _getter(self, instance):
        return self.counter

    def _setter(self, instance, value):
        """Any bool(value) == True will increment the counter and fire the notifiers
        """
        if self.name is None:
            raise RuntimeError(f'NotifierSignal: undefined attribute; cannot signal from {instance}')

        if self.klass is None:
            raise RuntimeError(f'NotifierSignal: undefined klass; cannot signal from {instance}')

        if bool(value):
            self.counter += 1
            _callbackDict = {NotifierABC.OBJECT:instance,
                             NotifierABC.ATTRIBUTE_NAME:self.name,
                             NotifierABC.PREVIOUSVALUE:self.counter-1,
                             NotifierABC.VALUE:self.counter
                             }
            instance._fireRegisteredNotifiers(trigger=Notifier.OBSERVE,
                                              targetName=self.name,
                                              callbackDict=_callbackDict
                                              )

    # def _findAttributeName(self, instance):
    #     """Find the attribute name for self from the class of instance
    #     sets self.klass and self.name
    #     """
    #     # find attributeName
    #     self.klass = instance.__class__
    #     found = None
    #     for _attr in dir(self.klass):
    #         try:
    #             _obj = getattr(self.klass, _attr)
    #         except AttributeError:
    #             obj = None
    #         finally:
    #             if _obj == self:
    #                 found = _attr
    #
    #     self.name = found

    def __str__(self):
        return(f'<NotifierSignal {self.name!r} of {self.klass}>')

    __repr__ = __str__

    # def __get__(self, *args, **kwds):
    #     return super().__get__(*args, **kwds)
    #
    # def __set__(self, *args, **kwds):
    #     super().__set__(*args, **kwds)

#end class -----------------------------------------------------------------------------------------


def _removeDuplicatedNotifiers(notifierQueue):
    """Remove any duplicated notifiers from the queue

    Notifiers are filtered on (obj, trigger)
    Notifier priority from high-low is: DELETE, CREATE, CHANGE
    When one is encountered, the lower-priority are ignored

    Return the condensed list of notifiers
    """
    # based on previous suspendNotification
    executeQueue = []
    scheduledQueue = set()

    # iterate through the queue in reverse order
    for func, data in notifierQueue.items(reverse=True):
        # assume that data is a non-empty dict
        obj = data.get(Notifier.OBJECT) if data else None
        trigger = data.get(Notifier.TRIGGER) if data else None

        match = (obj, trigger)
        if match not in scheduledQueue:
            scheduledQueue.add(match)

            # if True:
            #     # NOTE:ED - still not sure about this, disabled for the minute
            #     #   doesn't work correctly with SequenceGraph
            #     if trigger == Notifier.DELETE:
            #         # # can skip these two notifiers if DELETE found
            #         # scheduledQueue |= {(obj, Notifier.CHANGE), (obj, Notifier.RENAME), (obj, Notifier.CREATE)}
            #         #
            #         # # discard ALL other notifiers, not needed with DELETE
            #         # executeQueue = list(filter(lambda val: val[1][Notifier.OBJECT] != obj, executeQueue))
            #
            #         # can skip this notifier if CREATE found
            #         scheduledQueue |= {(obj, Notifier.CHANGE), (obj, Notifier.RENAME)}
            #
            #         # discard CHANGE, RENAME notifiers
            #         executeQueue = list(filter(lambda val: val[1][Notifier.OBJECT] != obj or
            #                                                val[1][Notifier.TRIGGER] not in [Notifier.CHANGE, Notifier.RENAME],
            #                                    executeQueue))
            #
            #     if trigger == Notifier.CREATE:
            #         # can skip this notifier if CREATE found
            #         scheduledQueue |= {(obj, Notifier.CHANGE), (obj, Notifier.RENAME)}
            #
            #         # discard CHANGE, RENAME notifiers
            #         executeQueue = list(filter(lambda val: val[1][Notifier.OBJECT] != obj or
            #                                                val[1][Notifier.TRIGGER] not in [Notifier.CHANGE, Notifier.RENAME],
            #                                    executeQueue))
            #
            #     elif trigger == Notifier.CHANGE:
            #         # can skip this notifier if RENAME found
            #         scheduledQueue |= {(obj, Notifier.RENAME),}
            #
            #         # discard CHANGE notifiers
            #         executeQueue = list(filter(lambda val: val[1][Notifier.OBJECT] != obj or
            #                                                val[1][Notifier.TRIGGER] not in [Notifier.RENAME],
            #                                    executeQueue))

            # this is in reverse order
            executeQueue.append((func, data))

    return list(reversed(executeQueue))


def _makeNotifiers(theObject,
                   triggers: list|tuple,
                   targetName: str,
                   callback: Callable,
                   setterObject=None,
                   onceOnly=False) -> _NotifierList:
    """Backward compatibility to make a NotifierList from multiple triggers

    :param theObject: the object to set the Notifier for
    :param triggers: list of triggers to trigger callback
    :param targetName: valid className, attributeName or None (See Notifier doc string for details)
    :param callback: callback function with signature: callback(callBackDict)
    :param setterObject: reference to the object setting the notifier
    :param onceOnly: If True, only one of multiple copies is executed (from underpinning V3-notifiers mechanism)
    :return: a _NotifierList instance

    """
    if not isinstance(triggers, (list,tuple)) or len(triggers) == 0:
        raise ValueError(f'Invalid triggers {triggers}; expected list, tuple with at least one item')

    result = _NotifierList()
    for _trigger in triggers:
        _notifier = Notifier(theObject=theObject,
                             trigger=_trigger,
                             targetName=targetName,
                             callback=callback,
                             onceOnly=onceOnly,
                             setterObject=setterObject,
                             )
        result.append(_notifier)

        # bit of a hack to set add _notifier to setterObject if it is not there yet.
        # This adds some backward compatibility to Notifiers not initialised through the
        # setNotifier() method of NotifierBase.
        if setterObject is not None \
            and hasattr(setterObject, '_addNotifier') \
            and hasattr(setterObject, '_hasNotifier') \
            and not setterObject._hasNotifier(_notifier):
            setterObject._addNotifier(_notifier)

    return result


def _getRegisteredNotifiers(obj, trigger) -> list | None:
    """Get the notifiers registered with obj for trigger
    :return a list of the notifiers or None if none defined for obj,trigger
    #CCPNMR_INTERNAL: used a various places to check and get the notifiers
    """
    if not hasattr(obj, NotifierBase.REGISTERED_NOTIFIERS_DICT):
        return None

    if (_nDict := getattr(obj, NotifierBase.REGISTERED_NOTIFIERS_DICT)) is None:
        return None

    if not isinstance(_nDict, _NotifiersDict):
        raise RuntimeError(f'_getRegisteredNotifiers: retrieved an unexpected object {_nDict}')

    _notifiers = [_ntf for _ntf in _nDict.allNotifiers if _ntf.trigger == trigger]
    if len(_notifiers) == 0:
        return None

    return _notifiers
