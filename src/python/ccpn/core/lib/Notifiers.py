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
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-03-21 16:21:09 +0000 (Thu, March 21, 2024) $"
__version__ = "$Revision: 3.2.2 $"
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

from ccpn.util.Logging import getLogger
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
    RENAME = 'rename'
    CHANGE = 'change'
    # For backwards compatibility
    CURRENT = 'current'

    ANY = '<Any>'

    # needs subclassing
    _triggerKeywords = ()

    # callback dict keywords
    NOTIFIER = 'notifier'       # The Notifier instance

    # the following can also be obtained from the Notifier instance
    THEOBJECT = 'theObject'     # The object for which a notifier was set
    TRIGGER = 'trigger'         # The trigger (see below)
    TARGETNAME = 'targetName'   # The traget name for trigger (see below)

    # The actual callback values/object
    OBJECT = 'object'           # the object created or deleted (trigger CREATE or DELETE)
    PID = 'pid'                 # the pid of the object (trigger RENAME)
    OLDPID = 'oldPid'           # the old or previous pid of the object (trigger RENAME)
    VALUE = 'value'             # the (new) value (trigger CHANGE)
    PREVIOUSVALUE = 'previousValue'  # the old or previous value (trigger CHANGE)

    SPECIFIERS = 'specifiers'

    def __init__(self, theObject, trigger, targetName, callback, setterObject=None, debug=False, **kwds):

        # Sanity checks
        if len(self._triggerKeywords) == 0:
            raise RuntimeError('Not trigger keywords defined; assure proper subclassing definitions')

        if theObject is None:
            raise RuntimeError('NotifierABC: theObject is None')
        self._theObject = theObject  # The object we are monitoring

        # backward compatibility for previous list of triggers
        if isinstance(trigger, (list, tuple)):
            # if len(trigger) != 1:
            #     raise RuntimeError(f'Invalid trigger "{trigger}"; should be one of {self._triggerKeywords}')
            # trigger = trigger[0]
            raise ValueError(f'Invalid tuple or list trigger "{trigger}"')

        if trigger not in self._triggerKeywords:
            raise ValueError('Invalid trigger "%s" for <%s>' % (trigger, self.__class__.__name__))
        self._trigger = trigger

        # initialisations
        self._id = NotifierABC._currentIndex
        NotifierABC._currentIndex += 1

        self._targetName = targetName
        self._callback = callback
        self._kwds = kwds

        self._setterObject = weakref.ref(setterObject) if setterObject is not None else None

        self._debug = debug or DEBUG or self._id in _debugIds
        self._isBlanked = False  # ability to blank notifier
        self._isRegistered = False  # flag indicating if any Notifier was registered

    @property
    def id(self):
        return self._id

    def setDebug(self, flag: bool):
        """Set debug output on/off"""
        self._debug = flag

    def setBlanking(self, flag: bool):
        """Set blanking on/off"""
        self._isBlanked = flag

    def triggersOn(self, trigger) -> bool:
        """Return True if notifier triggers on trigger"""
        return trigger in self._triggers

    def unRegister(self):
        """Reset the attributes"""
        if self._debug:
            sys.stderr.write('>>> unRegister %s\n' % self)

        self._theObject = None
        self._callback = None
        self._unregister = ()
        self._triggers = ()
        self._isRegistered = False
        self._setterObject = None

    @property
    def isRegistered(self) -> bool:
        """:return True if notifier is still registered; i.e. active"""
        return self._isRegistered

    def newCallbackDict(self, trigger, previousValue=None, value=None, obj=None,
                        oldpid=None, pid=None, specifiers=None):
        callbackDict = {
                self.NOTIFIER     : self,
                self.THEOBJECT    : self._theObject,
                self.TRIGGER      : trigger,
                self.TARGETNAME   : self._targetName,
                self.PREVIOUSVALUE: previousValue,
                self.VALUE        : value,
                self.OBJECT       : obj,
                self.OLDPID       : oldpid,
                self.PID          : pid,
                self.SPECIFIERS   : specifiers,
                }
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
        _registered = '' if self.isRegistered else ', not-registered'
        _pid = self._theObject.pid
        return f'<{self.__class__.__name__}: id={self.id}{_registered}, obj={_pid!r}: {self._trigger!r}->{self._targetName!r}>'

    __repr__ = __str__


class Notifier(NotifierABC):
    """
    Notifier class:

    triggers callback function with signature:  callback(callbackDict [, *args] [, **kwargs])

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

     # Notifier.CHANGE_OBJECT
     #                  attributeName         theObject,targetName      targetName: valid attribute name of theObject
     #                  or ANY                value, previousValue,     NB: should only be used in isolation; i.e. not
     #                                        trigger, notifier         combined with other triggers

    Implementation:

      Uses current notifier system from Project filters for child objects of type targetName in theObject.
      TargetName does need to denote a valid child-class, except for Project instances
      which can be triggered by all classes.

      The callback provides a dict with several key, value pairs (idea following the Traitlets concept).
      Note that this dict also contains a reference to the Notifier object itself; this way it can be used
      to pass-on additional implementation specific information to the callback function.

    """

    # Trigger keywords (from NotifierABC)
    # CREATE = 'create'
    # DELETE = 'delete'
    # RENAME = 'rename'
    # CHANGE = 'change'
    # OBSERVE = 'observe'
    #
    # ANY = '<Any>'

    _triggerKeywords = (NotifierABC.CREATE, NotifierABC.DELETE, NotifierABC.RENAME, NotifierABC.CHANGE)

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

        :param theObject: valid V3 core object or current object to watch
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

            # CHANGE special case, as the current underpinning implementation does not allow this directly
            # Hence, we track all changes to the object class, filtering those that apply
            # if trigger == Notifier.CHANGE:
            #     if targetName != self.ANY and not hasattr(theObject, targetName):
            #         raise RuntimeWarning(
            #                 'Notifier.__init__: invalid targetName "%s" for class "%s"' % (targetName, theObject.className))
            #
            #     if targetName != self.ANY:
            #         self._previousValue = getattr(theObject, targetName)
            #
            #     notifier = (trigger, targetName)
            #     func = self.project.registerNotifier(className=theObject.className,
            #                                          target=Notifier.CHANGE,
            #                                          func=partial(self, notifier=notifier),
            #                                          onceOnly=onceOnly)
            #     self._unregister.append((theObject.className, Notifier.CHANGE, func))
            #     self._isRegistered = True


        func = _project._registerV3Notifier(className=targetName,
                                            target=self._trigger,
                                            func=self,
                                            onceOnly=onceOnly)
        # The info needed for unregistering
        self._unregister= (targetName, self._trigger, func)
        self._isRegistered = True

        if self._debug:
            sys.stderr.write('>>> registered %s\n' % self)

    @property
    def project(self):
        """Return the project
        """
        # implemented as a weak reference
        return self._project()

    def unRegister(self):
        """
        unregister the notifiers
        """
        # >>>>>>
        if self._debug:
            sys.stderr.write('>>> un-registering %s\n' % self)

        if not self.isRegistered:
            return

        targetName, trigger, func = self._unregister
        self.project._unRegisterV3Notifier(targetName, trigger, func)

        super().unRegister()  # the end as it clears all attributes

    def __call__(self, obj, parameter2=None):
        """
        wrapper, accommodating the callback from V3-project notifier implementation
        """

        if not self.isRegistered:
            getLogger().warning(f'Triggering unregistered notifier {self}')
            return

        if self._isBlanked:
            return

        if obj is None:
            raise RuntimeError('Notifier.__call__: obj is None')

        if self._debug:
            sys.stderr.write(f'>>> {self}.__call__(): {obj = }  {parameter2 = }\n' )

        notifierFired = False

        # # OBSERVE ANY special case
        # elif trigger == Notifier.OBSERVE and targetName == self.ANY:
        #     if obj.pid == self._theObject.pid:
        #         callbackDict[self.OBJECT] = self._theObject
        #         self._callback(callbackDict, **self._kwargs)
        #         notifierFired = True
        #
        # # OBSERVE targetName special case
        # elif trigger == Notifier.OBSERVE and targetName != self.ANY:
        #     # The check below catches all changes to obj that do not involve targetName, as only
        #     # when it has changed its value will we trigger the callback
        #     value = getattr(self._theObject, targetName)
        #     if obj.pid == self._theObject.pid and not self._isEqual(value, self._previousValue):
        #         callbackDict[self.OBJECT] = self._theObject
        #         callbackDict[self.PREVIOUSVALUE] = self._previousValue
        #         callbackDict[self.VALUE] = value
        #         self._callback(callbackDict, **self._kwargs)
        #         notifierFired = True
        #         self._previousValue = value

        # check if the trigger applies:
        if self._isProject or obj._parent.pid == self._theObject.pid:
            callbackDict = self.newCallbackDict(trigger=self._trigger,
                                                obj=obj,
                                                oldpid=parameter2,
                                                pid=obj.pid,
                                                )

            self._callback(callbackDict, **self._kwds)
            notifierFired = True

        if self._debug:
            _tmp = 'FIRED' if notifierFired else 'not-FIRED'
            sys.stderr.write('%-9s func:%s\n' % (_tmp, self._callback))

        return


class CurrentNotifier(NotifierABC):
    """
    Current-Notifier class:

    triggers callback function with signature:  callback(callbackDict [, *args] [, **kwargs])

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
        self._isRegistered = True

        if self._debug:
            sys.stderr.write(f'>>> registered {self}\n')

    def unRegister(self):
        """
        unregister the notifier
        """
        if self._debug:
            sys.stderr.write(f'>>> un-registering {self}\n')

        if not self.isRegistered:
            return

        targetName, func = self._unregister
        self._theObject.unRegisterNotify(func, targetName)
        super().unRegister()  # at the end as it clears all attributes

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
                    trigger=self._trigger,
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

    def unRegister(self):
        """Un-register all notifiers of self
        """
        for notifier in self:
            if not isinstance(notifier, NotifierABC):
                raise RuntimeError(f'unRegister(): Invalid notifier {notifier}')
            notifier.unRegister()
# end class


class _NotifiersDict(dict):
    """A class to retain all notifiers of an object
    Comprised of (trigger, {}) key, value pairs (i.e. a dict of dicts
    """

    def addNotifier(self, notifier:NotifierABC):
        """Add notifier to self, in a trigger dependent way
        """
        _dict = self.setdefault(notifier._trigger, {})
        _id = notifier.id
        # this should never happen; hence just a check
        if _id in _dict:
            raise RuntimeError(f'A notifier with id "{_id}" already exists; cannot add {notifier}')
        _dict[_id] = notifier

    def deleteNotifier(self, notifier:NotifierABC):
        """Delete notifier from self
        :raise ValueError if notifier is not part of self
        """
        if (_dict := self.get(notifier._trigger, None)) is None:
            raise ValueError(f'deleteNotifier(): {notifier} is not contained in self')
        if notifier.id not in _dict:
            raise ValueError(f'deleteNotifier(): {notifier} is not contained in self')
        del( _dict[notifier.id] )

    @property
    def allNotifiers(self) -> dict:
        """:return A dict of (id, notifier) pairs of all notifiers
        """
        _ll = [_item for _dict in self.values() for _item in _dict.items()]
        return dict(_ll)


class NotifierBase(object):
    """
    A class confering notifier management routines
    """
    _NOTIFIERSDICT = '_objectNotifiersDict'  # attribute name for storing notifiers in Ccpn objects

    def _getObjectNotifiersDict(self):
        """Internal routine to get the object notifiers dict
        """
        if not hasattr(self, self._NOTIFIERSDICT):
            setattr(self, self._NOTIFIERSDICT, _NotifiersDict())

        objNotifiers = getattr(self, self._NOTIFIERSDICT)
        # check type
        if not isinstance(objNotifiers, _NotifiersDict):
            raise RuntimeError(f'Invalid NotifiersDict, got {type(objNotifiers)}, expected {type(_NotifiersDict)}')

        return objNotifiers

    def _addNotifier(self, notifier):
        """Add notifier to notifiersDict;
        Isolating for easier subclassing of setNotifier()
        :param notifier: a Notifier|CurrentNotifier|GuiNotifier instance
        """
        objNotifiers = self._getObjectNotifiersDict()
        # add the notifier
        objNotifiers.addNotifier(notifier)

    def setNotifier(self, theObject, triggers: list|tuple, targetName: str, callback: Callable, **kwds) -> _NotifierList:
        """
        Set Notifier for Ccpn V3 object theObject; store in own CcpNmrNotifiersDict for management.

        :param theObject: V3 object to register a notifier with
        :param triggers: list of triggers to trigger callback
        :param targetName: valid className, attributeName or None (See Notifier doc string for details)
        :param callback: callback function with signature: callback(callbackDict, **kwds])
        :param **kwds: optional keyword,value arguments to call back

        :return: a _NotifierList or CurrentNotifier instance
        """
        from ccpn.framework.Current import Current

        if not isinstance(triggers, (list,tuple)) or len(triggers) == 0:
            raise ValueError(f'setNotifier(): invalid triggers "{triggers}"; expected list or tuple with at least one of {Notifier._triggerKeywords}')

        if isinstance(theObject, Current) or triggers[0] == CurrentNotifier.CURRENT:
            raise ValueError(f'setNotifier(): Object or trigger refer to Current; use setCurrentNotifier() method instead')

        if theObject is None:
            raise ValueError(f'setNotifier(): undefined object')

        result = _NotifierList()
        for _trigger in triggers:
            _notifier = Notifier(
                    theObject=theObject,
                    trigger=_trigger,
                    targetName=targetName,
                    callback=callback,
                    setterObject=self,
                    **kwds
            )
            result.append(_notifier)
            self._addNotifier(_notifier)

        return result

    def setGuiNotifier(self, theObject, triggers: list, targetNames: str, callback: Callable) -> _NotifierList:
        """
        Set GuiNotifier for Ccpn V3 object theObject

        :param theObject: V3 object to register a notifier with
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
        """
        Set CurrentNotifier for Ccpn V3 object theObject

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

    def hasNotifier(self, notifier) -> bool:
        """
        return True if theObject has set notifier or
        has any notifier (when notifier==None)

        :param notifier: a Notifier|CurrentNotifier|GuiNotifier instance
        :return: True or False
        """
        if not hasattr(self, self._NOTIFIERSDICT):
            return False

        objNotifiers = self._getObjectNotifiersDict()
        if len(objNotifiers) == 0:
            return False

        if notifier is None and len(objNotifiers) > 0:
            return True

        if not isinstance(notifier, NotifierABC):
            raise ValueError('"%s" is not a valid notifier instance' % notifier)

        if (_dict := objNotifiers.get(notifier._trigger, None)) is None:
            return False

        return notifier.id in _dict

    def searchNotifiers(self, objects=[], triggers=[], targetName=None) -> list:
        """Search whether a notifier with the given parameters is already defined
        for objects.
        The triggers CREATE, DELETE, RENAME and CHANGE can be combined in the call signature

        :param objects: valid V3 core object or current object to watch
        :param triggers: list of trigger keywords
        :param targetName: valid className, attributeName or ANY
        :return: list of existing notifiers (can be empty)
        """
        if not hasattr(self, self._NOTIFIERSDICT):
            return []

        objNotifiers = self._getObjectNotifiersDict()
        if len(objNotifiers) == 0:
            return []

        foundNotifiers = []
        for notifier in objNotifiers.allNotifiers.values():
            if notifier._theObject in objects and \
               targetName == notifier._targetName and \
               notifier._trigger in triggers:
                    foundNotifiers.append(notifier)

        return foundNotifiers

    def deleteNotifier(self, notifier):
        """
        unregister notifier; remove it from the list and delete it
        :param notifier: a Notifier|CurrentNotifier|GuiNotifier instance
        """
        if not self.hasNotifier(notifier):
            raise ValueError(f'deleteNotifier(): {notifier} is not a (valid) notifier of {self}')

        objNotifiers = self._getObjectNotifiersDict()
        objNotifiers.deleteNotifier(notifier)
        notifier.unRegister()
        del(notifier)

    def deleteAllNotifiers(self):
        """Unregister all the notifiers
        """
        if not self.hasNotifier(None):
            # there are no notifiers
            return

        objNotifiers = self._getObjectNotifiersDict()
        # explicitly cast to list, as contents are being changed and .values() is an iterator
        for notifier in list(objNotifiers.allNotifiers.values()):
            objNotifiers.deleteNotifier(notifier)
            notifier.unRegister()
            del(notifier)

    def setBlankingAllNotifiers(self, flag):
        """Set blanking of all the notifiers of theObject to flag
        """
        if not self.hasNotifier(None):
            return
        objNotifiers = self._getObjectNotifiersDict()
        for notifier in list(objNotifiers.allNotifiers.values()):
            notifier.setBlanking(flag)


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

        # bit of a hack to set the linkage to setterObject
        if setterObject is not None and hasattr(setterObject, '_addNotifier'):
            setterObject._addNotifier(_notifier)

    return result
