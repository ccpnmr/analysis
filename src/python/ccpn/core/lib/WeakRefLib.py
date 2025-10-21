"""
This module provides a robust descriptor that manages object references
as weak-references, preventing memory leaks in complex object graphs.

It also includes a built-in observer system that is also managed with
weak-references for safe event handling.

:Authors: Ed Brooksbank
:Dates: 2024-12-05
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-10-09 13:16:45 +0100 (Thu, October 09, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2024-12-05 14:31:02 +0100 (Thu, December 05, 2024) $"
#=========================================================================================
# Start of code
#=========================================================================================

__all__ = [
    "OrderedWeakKeyDictionary",
    "PartialLike",
    "WeakRefConnector",
    "WeakRefDescriptor",
    "WeakRefPartial",
    "WeakRefProxyPartial",
    "WeakValueMappingView"
    ]

import sys
import collections
from functools import partial
import weakref
from collections.abc import Mapping, Iterator
from contextlib import suppress
from dataclasses import Field
from reprlib import recursive_repr
from typing import Any, Callable, Protocol, Generic, TypeVar, overload
from typing_extensions import runtime_checkable, Self


_DEBUG = False


class _consoleStyle():
    """
    Console styling with ANSI escape codes.

    This class provides ANSI escape codes for console output.
    All colors and styles can be reset with the `reset` attribute.
    Foreground colors are available in the nested `fg` class.

    :ivar reset: Resets all text formatting to default.
    :vartype reset: str
    :ivar fg: A nested class containing foreground color codes.
    :vartype fg: class
    """
    # Smaller version of that defined in Common to remove any non-built-in imports
    reset = '\033[0m'


    class fg:
        darkred = '\033[31m'
        darkyellow = '\033[33m'
        lightgrey = '\033[37m'
        red = '\033[91m'
        green = '\033[92m'
        yellow = '\033[93m'
        blue = '\033[94m'
        magenta = '\033[95m'
        white = '\033[97m'


def _write(*text):
    """Debug - write output"""
    sys.stderr.write(f'{_consoleStyle.fg.lightgrey}{__name__.split(".")[-1]}:  '
                     f'{" ".join(map(lambda val: str(val), text))}'
                     f'{_consoleStyle.reset}\n')


#=========================================================================================
# WeakRefDescriptor
#=========================================================================================

_T = TypeVar('_T')
_Owner = TypeVar('_Owner')
_K = TypeVar("_K")
_V = TypeVar("_V")


class WeakRefDescriptor(Generic[_T]):
    """
    A descriptor that stores values as weak-references tied to specific instances.

    This allows attributes to reference objects without preventing their garbage collection.
    When the referenced object is collected, the corresponding entry is automatically removed.

    This descriptor provides a robust `__set__` method that automatically attaches a
    finalizer callback to the referenced object. This callback is triggered upon
    garbage collection and can be used to notify any registered observers.
    """
    __slots__ = "_storage", "_attrib_name", "_connected", "_observers", "__weakref__"
    _storage: weakref.WeakValueDictionary[int, _T]
    _attrib_name: str
    _connected: bool
    _observers: dict[int, list[WeakRefPartial]]

    def __init__(self) -> None:
        """
        Initialise a new WeakRefDescriptor instance.

        This sets up a `WeakValueDictionary` for storing weak-references to the
        values and a standard dictionary for managing observers.
        """
        super().__init__()
        # A WeakValueDictionary to store weak-references keyed by instance IDs.
        self._storage = weakref.WeakValueDictionary()
        self._connected = False
        self._observers = {}

    def __set_name__(self, owner: type[_Owner], name: str):
        """
        Store the name of the attribute this descriptor is assigned to.

        This method is automatically called by the Python interpreter when the
        descriptor is assigned to an attribute of a class. It is used to
        store the name of the attribute (`e.g. 'application'`).

        :param owner: The class that owns this descriptor.
        :type owner: type[_Owner]
        :param name: The name of the attribute on the owner class.
        :type name: str
        """
        if _DEBUG:
            _write(f'{_consoleStyle.fg.magenta}--> {self.__class__.__name__}.__set_name__ {hex(id(owner))} {name}'
                   f'{_consoleStyle.reset}')
        self._attrib_name = name

    def __change_name__(self, name: str):
        """
        Change the name of the attribute this descriptor is assigned to.

        **INTERNAL**
        This is an internal method that should only be called by a metaclass
        during class construction or modification, not directly by a user.

        :param name: The new name of the attribute.
        :type name: str
        """
        if _DEBUG:
            _write(f'{_consoleStyle.fg.magenta}--> {self.__class__.__name__}.__change_name__ {name}'
                   f'{_consoleStyle.reset}')
        self._attrib_name = name

    # Overload 1: For class access (e.g. MyClass.descriptor)
    # The instance is None, and the method returns the descriptor itself.
    @overload
    def __get__(self, instance: None, owner: type[_Owner]) -> Self:
        ...

    # Overload 2: For instance access (e.g. my_instance.descriptor)
    # The instance is of type _Owner, and the method returns the stored value or None.
    @overload
    def __get__(self, instance: _Owner, owner: type[_Owner]) -> _T | None:
        ...

    def __get__(self, instance: _Owner | None, owner: type[_Owner]) -> Self | _T | None:
        """
        Retrieve the value associated with the instance from the weak-reference storage.

        **NOTE**

        Sometimes the type-checker gives a warning on the getter, especially if using mypy.
        It is advisable to add `type: ignore[return-type]`

        *example:*
        ::
            class Values:
                _value = WeakRefDescriptor[int]()

                @property
                def value(self) -> int:
                    return self._value  # type: ignore[return-value]

        The `[int]` is not strictly necessary, the type-checker will infer the type from the first usage.

        :param instance: The instance for which the attribute is being accessed.
        :type instance: _Owner
        :param owner: The owner class of the descriptor.
        :type owner: type[_Owner]
        :return: The value stored for the instance, or `None` if no value exists.
                 If accessed on the class (e.g., `MyClass.descriptor`), the descriptor
                 instance itself is returned.
        :rtype: Self | _T | None
        """
        if instance is None:
            # If accessed on the class rather than an instance, return the descriptor itself.
            return self
        result = self._storage.get(id(instance), None)
        if _DEBUG:
            _write(f'{_consoleStyle.fg.lightgrey}--> {self.__class__.__name__}.__get__  <==  {hex(id(instance))}'
                   f' {result}    from {owner.__name__}.{self._attrib_name}{_consoleStyle.reset}')
        return result

    def __set__(self, instance: _Owner, value: _T | None) -> None:
        """
        Set a value for the instance in the weak-reference storage.

        When a new value is set, a finalizer is attached to it. This finalizer
        will trigger the `_onWeakrefCollected` callback when the value is garbage
        collected.

        :param instance: The instance for which the value is being set.
        :type instance: _Owner
        :param value: The value to store. Must not be another `WeakRefDescriptor`.
        :type value: _T | None
        """
        if isinstance(value, WeakRefDescriptor):
            # Prevent setting the descriptor itself as a value.
            return
        if _DEBUG:
            _write(f'{_consoleStyle.fg.lightgrey}--> {self.__class__.__name__}.__set__  -->  {hex(id(instance))} '
                   f'{value}{_consoleStyle.reset}')
        if value is not None:
            # Store the value as a weak-reference associated with the instance ID.
            self._storage[id(instance)] = value
            # Register a callback to notify when the object is garbage-collected.
            # The callback receives a weak-reference to `self` to prevent a strong
            # reference cycle.
            weakref.finalize(value, WeakRefDescriptor._onWeakrefCollected,
                             weakref.ref(self), id(instance), id(value))
        else:
            # Remove the entry if the value is None.
            self._storage.pop(id(instance), None)
            self._observers.pop(id(instance), None)

    def __delete__(self, instance: _Owner) -> None:
        """
        Remove the value associated with the instance from the weak-reference storage.

        :param instance: The instance for which the value is being deleted.
        :type instance: _Owner
        """
        if _DEBUG:
            _write(f'{_consoleStyle.fg.lightgrey}--> {self.__class__.__name__}.__delete__  -->  {hex(id(instance))} '
                   f'{_consoleStyle.reset}')
        self._storage.pop(id(instance), None)
        self._observers.pop(id(instance), None)

    @staticmethod
    def _onWeakrefCollected(selfref: weakref.ReferenceType, _instanceId: int, owner: int) -> None:
        """
        Static callback function that is called when a weak-referenced object is collected.

        This method is triggered by `weakref.finalize` and notifies any observers
        connected to the instance.

        :param selfref: A weak-reference to the `WeakRefDescriptor` instance.
        :type selfref: weakref.ReferenceType
        :param _instanceId: The ID of the instance whose weak-reference was collected.
        :type _instanceId: int
        :param owner: The ID of the object that was collected.
        :type owner: int
        """
        if not (self := selfref()):
            # The descriptor itself has been garbage collected.
            return
        if _DEBUG:
            _write(f'{_consoleStyle.fg.yellow}--> Weak-reference collected for instance ID '
                   f'{hex(_instanceId)} {self} {hex(owner)}{_consoleStyle.reset}')
        # emit instance-based signals
        for observe in self._observers.get(_instanceId, []):
            observe()
        # emit class-based signals with instance-id of weakRefDescriptor container
        for observe in self._observers.get(-1, []):
            observe(_instanceId)

    #-----------------------------------------------------------------------------------------
    # public API for observer management

    def connect(self, observer: Callable[..., Any], instance: object | None = None) -> None:
        """
        Connect an observer to the signal for a specific instance or the descriptor itself.

        This adds the provided observer function to the list of observers
        that will be notified when the weak-referenced object for that instance is
        garbage collected. Note that an observer can only be connected to an
        instance that already has a value set for this descriptor.

        :param observer: The observer function that will be called.
        :type observer: Callable[..., Any]
        :param instance: The instance for which the observer is being connected.
                         If `None`, the observer is connected to the class-level signal.
        :type instance: object | None
        :raises TypeError: If the observer is not callable or if the instance is not defined.
        """
        if not callable(observer):
            raise TypeError(f'{self.__class__.__name__}.connect: observer must be Callable')
        if instance:
            if id(instance) not in self._storage.keys():
                raise TypeError(f'{self.__class__.__name__}.connect: instance {instance} is not defined')
            # instance-based signal
            _id = id(instance)
        else:
            # class-based signal
            _id = -1
        dd = self._observers.setdefault(_id, [])
        if any(func._func_ref() is observer for func in dd):
            raise TypeError(f'{self.__class__.__name__}.connect: observer already exists')
        dd.append(WeakRefPartial(observer))

    def disconnect(self, observer: Callable[..., Any], instance: object | None = None) -> None:
        """
        Disconnect an observer from the signal for a specific instance.

        :param observer: The observer function to be removed.
        :type observer: Callable[..., Any]
        :param instance: The instance for which the observer is being disconnected.
                         If `None`, the observer is disconnected from the class-level signal.
        :type instance: object | None
        :raises TypeError: If the observer is not callable or is not connected.
        """
        if not callable(observer):
            raise TypeError(f'{self.__class__.__name__}.disconnect: observer must be Callable')
        if instance:
            if id(instance) not in self._observers:
                raise TypeError(f'{self.__class__.__name__}.disconnect: {instance} has no connected observers')
            # instance-based signal
            _id = id(instance)
        else:
            # class-based signal
            _id = -1
        observers_list = self._observers.get(_id, [])
        if not any(func._func_ref() is observer for func in observers_list):
            raise TypeError(f'{self.__class__.__name__}.disconnect: observer {observer} not found')
        # Remove the observer if it exists, keep the same list-pointer
        observers_list[:] = list(filter(lambda func: func._func_ref() is not observer, observers_list))

    def isConnected(self, observer: Callable[..., Any], instance: object | None = None) -> bool:
        """
        Check if the requested observer is connected to the signal.

        :param observer: The observer function to check.
        :type observer: Callable[..., Any]
        :param instance: The instance for which the value is being checked.
        :type instance: object | None
        :return: `True` if the observer is connected, otherwise, `False`.
        :rtype: bool
        """
        if instance:
            if id(instance) not in self._storage.keys():
                return False
            # instance-based signal
            _id = id(instance)
        else:
            # class-based signal
            _id = -1
        dd = self._observers.setdefault(_id, [])
        return any(func._func_ref() is observer for func in dd)

    def getObservers(self, instance: object | None = None) -> list[Callable[..., Any]]:
        """
        Retrieve a list of observers connected to the signal.

        :param instance: The instance for which the observers are being retrieved.
                         If `None`, class-level observers are returned.
        :type instance: object | None
        :return: A list of observer functions.
        :rtype: list[Callable[..., Any]]
        """
        if instance:
            if id(instance) not in self._storage.keys():
                return []
            # instance-based observers
            _id = id(instance)
        else:
            # class-based observers
            _id = -1
        dd = self._observers.get(_id, [])
        return [func._func_ref() for func in dd if func._func_ref() is not None]

    def hasObservers(self, instance: object | None = None) -> bool:
        """
        Check if any observers are connected to the signal.

        :param instance: The instance for which the value is being checked.
        :type instance: object | None
        :return: `True` if there are any observers; otherwise, `False`.
        :rtype: bool
        """
        return bool(self.getObservers(instance))


#=========================================================================================
# _WeakRefDataClassMeta
#=========================================================================================

class _WeakRefDataClassMeta(type):
    """
    A metaclass to handle the initialisation of `WeakRefDescriptor` instances in dataclasses.

    This metaclass inspects the class attributes during class creation, identifies fields
    using `WeakRefDescriptor` as a `default_factory`, and replaces them with actual instances
    of `WeakRefDescriptor`. It ensures that weak-reference descriptors are properly initialized
    in dataclass-like structures.
    """

    def __new__(cls, name, bases, dct):
        """
        Create a new class, initializing `WeakRefDescriptor` instances as needed.

        :param cls: The metaclass itself.
        :param name: The name of the new class being created.
        :param bases: A tuple of base classes for the new class.
        :param dct: The dictionary of attributes for the new class.

        :return: A newly created class with `WeakRefDescriptor` fields properly initialized.
        """
        # Identify attributes defined as fields with a WeakRefDescriptor default_factory.
        _weakrefs = {key for key, value in dct.items()
                     if isinstance(value, Field) and value.default_factory is WeakRefDescriptor}
        # Remove identified weak-reference fields from the initial attribute dictionary.
        dct = {k: v for k, v in dct.items() if k not in _weakrefs}
        # Create the new class using the modified attribute dictionary.
        cls_new = super().__new__(cls, name, bases, dct)
        # Assign WeakRefDescriptor instances to the new class for the identified weak-reference fields.
        for k in _weakrefs:
            # Add the type annotation for 'weakref' here
            weakref: WeakRefDescriptor = WeakRefDescriptor()
            setattr(cls_new, k, weakref)
            # set the name for the weakref-garbage-collection signal
            weakref.__change_name__(name=k)
        return cls_new


#=========================================================================================
# WeakRefPartial
#=========================================================================================

@runtime_checkable
class PartialLike(Protocol):
    func: Callable[..., Any]
    args: tuple
    keywords: dict

    # Cheeky way to add args and keywords to pycharm type-hinting
    def __call__(self, *args, **kwargs):
        ...


class _IdHandle:
    """
    Small class that holds a weak-reference pointer.
    This can then be used by weakref.ref.

    :ivar __id: The id of the referenced object.
    """
    __slots__ = "__id", "__weakref__"
    __id: int

    def __init__(self, ref: object):
        """Initialize the _IdHandle instance.

        :param ref: The object to be referenced.
        """
        # Store the id of the caller, though it's not strictly necessary.
        # It's only the existence of Self that's important.
        self.__id = id(ref)

    def __del__(self):
        """Destructor that prints a message when the instance is garbage-collected,
        if debugging is enabled.
        """
        if _DEBUG:
            _write(f'{_consoleStyle.fg.darkred}--> {self.__class__.__name__}.__del__ {hex(id(self))}'
                   f'{_consoleStyle.reset}')


class WeakRefPartial:
    """
    A new function with partial application of the given arguments and keywords.

    This class allows creating a callable object where some arguments and/or keyword
    arguments are pre-filled for the specified function. The function is stored as a
    weak-reference, so it will not prevent the function from being garbage collected.
    If the function is deleted, calling the partial object raises a ``ReferenceError``.

    :ivar _func_ref: A weak-reference to the callable function.
    :vartype _func_ref: weakref.ReferenceType
    :ivar args: Positional arguments pre-filled for the function.
    :vartype args: tuple
    :ivar keywords: Keyword arguments pre-filled for the function.
    :vartype keywords: dict.
    """

    __slots__ = "_func_ref", "args", "keywords", "__id", "__dict__", "__weakref__"
    _func_ref: Callable[..., Any] | PartialLike
    args: tuple
    keywords: dict
    __id: _IdHandle | None

    def __new__(cls, func: Callable[..., Any] | PartialLike, /,
                *args: Any, **keywords: Any) -> WeakRefPartial:
        """
        Initialize a new partial object.

        :param func: The callable function to partially apply.
        :type func: Callable
        :param args: Positional arguments to pre-fill.
        :type args: Any
        :param keywords: Keyword arguments to pre-fill.
        :type keywords: Any
        :raises TypeError: If the first argument is not callable.
        """
        if not callable(func):
            raise TypeError("The first argument must be callable")
        if isinstance(func, PartialLike):
            # Wrap any nested partials
            args = func.args + args
            keywords = {**func.keywords, **keywords}
            func = func.func
        self = super().__new__(cls)

        # Pre-create a weakref to self for the weakref delete-callback
        selfref = weakref.ref(self)
        # Store a weak-reference to func
        self._func_ref = weakref.ref(func, lambda wref: WeakRefPartial.__remove(wref, selfref))
        self.args = args
        self.keywords = keywords
        self.__id = _IdHandle(self)
        return self

    #-----------------------------------------------------------------------------------------
    # Internal

    def __call__(self, /, *args: Any, **keywords: Any) -> Any | None:
        """
        Call the function with pre-filled and additional arguments.

        :param args: Additional positional arguments to pass to the function.
        :type args: Any
        :param keywords: Additional keyword arguments to pass to the function.
        :type keywords: Any
        :return: The result of the function call.
        :raises ReferenceError: If the referenced function has been deleted.
        """
        if not (func := self._func_ref()):
            return None
        keywords = {**self.keywords, **keywords}
        return func(*self.args, *args, **keywords)

    @recursive_repr()
    def __repr__(self) -> str:
        """
        Return a string representation of the partial object.

        :return: A string representation of the partial object.
        :rtype: str
        """
        if (func := self._func_ref()) is None:
            func_repr = "<deleted function>"
        else:
            func_repr = repr(func)
        qualname = type(self).__qualname__
        args = [func_repr]
        args.extend(repr(x) for x in self.args)
        args.extend(f"{k}={v!r}" for (k, v) in self.keywords.items())
        if type(self).__module__ == "functools":
            return f"functools.{qualname}({', '.join(args)})"
        return f"{qualname}({', '.join(args)})"

    def __reduce__(self) -> tuple:
        """
        Prepare the partial object for pickling.

        :return: A tuple containing the class, arguments, and state.
        :rtype: tuple
        :raises ReferenceError: If the referenced function has been deleted.
        """
        func = self._func_ref()
        return type(self), (func,), (func, self.args, self.keywords or None, self.__dict__ or None)

    def __setstate__(self, state: tuple) -> None:
        """
        Restore the state of the partial object during unpickling.

        :param state: A tuple containing the function, arguments, keywords, and dictionary.
        :type state: tuple
        :raises TypeError: If the state is invalid.
        """
        if not isinstance(state, tuple):
            raise TypeError("Argument to __setstate__ must be a tuple")
        if len(state) != 4:
            raise TypeError(f"Expected 4 items in state, got {len(state)}")
        func, args, kwds, namespace = state
        # Validate state components
        if (not callable(func) or not isinstance(args, tuple) or
                (kwds is not None and not isinstance(kwds, dict)) or
                (namespace is not None and not isinstance(namespace, dict))):
            raise TypeError("Invalid partial state")
        # Ensure arguments are a tuple (even if it's a subclass)
        args = tuple(args)
        if kwds is None:
            kwds = {}
        elif type(kwds) is not dict:  # XXX does it need to be *exactly* dict?
            kwds = dict(kwds)
        # Initialise namespace dictionary
        if namespace is None:
            namespace = {}
        self.__dict__ = namespace

        selfref = weakref.ref(self)
        # Restore the weak-reference
        self._func_ref = weakref.ref(func, lambda wref: WeakRefPartial.__remove(wref, selfref))
        self.args = args
        self.keywords = kwds
        # Initialise a unique ID handle (if required), not sure resetting the handle is strictly necessary
        self.__id = _IdHandle(self)

    def __bool__(self) -> bool:
        """
        Check whether the referenced function still exists.

        :return: True if the weakly-referenced function is still valid, False otherwise.
        :rtype: bool
        """
        return self._func_ref() is not None

    #-----------------------------------------------------------------------------------------
    # Properties

    @property
    def id(self) -> _IdHandle | None:
        """
        Return the internal identifier-handle.

        :return: The internal identifier-handle.
        """
        return self.__id

    #-----------------------------------------------------------------------------------------
    # Private

    @staticmethod
    def __remove(wref: weakref.ReferenceType, selfref: weakref.ReferenceType):
        """
        Callback function that is called when the weakly-referenced object is deleted.

        This function contains a weak-reference to the instance (`selfref`) to ensure that
        if the wrapper has already been collected, no action is required.

        :param wref: The weak-reference to the object that is being monitored.
        :type wref: weakref.ReferenceType
        :param selfref: A weak-reference to the instance of the class.
        :type selfref: weakref.ReferenceType
        """
        # Use a staticmethod instead of a monkey-patch
        if (sref := selfref()) is not None:
            if _DEBUG:
                _write(f'{_consoleStyle.fg.red}--> {sref.__class__.__name__}._remove '
                       f'{sref} - {wref}{_consoleStyle.reset}')
            # Remove the handle, it could be used as a reference elsewhere
            sref.__id = None


#=========================================================================================
# WeakRefProxyPartial
#=========================================================================================

class WeakRefProxyPartial:
    """
    A new function with partial application of the given arguments and keywords.

    This class allows creating a callable object where some arguments and/or keyword
    arguments are pre-filled for the specified function. The function is stored as a
    weak-reference, so it will not prevent the function from being garbage collected.
    If the function is deleted, calling the partial object raises a ``ReferenceError``.

    :ivar _func_ref: A weak-reference to the callable function.
    :vartype _func_ref: weakref.proxy
    :ivar args: Positional arguments pre-filled for the function.
    :vartype args: tuple
    :ivar keywords: Keyword arguments pre-filled for the function.
    :vartype keywords: dict.
    """

    __slots__ = "_func_ref", "args", "keywords", "__id", "__dict__", "__weakref__"
    _func_ref: Callable[..., Any] | PartialLike
    args: tuple
    keywords: dict
    __id: _IdHandle | None

    def __new__(cls, func: Callable[..., Any] | PartialLike, /,
                *args: Any, **keywords: Any) -> WeakRefProxyPartial:
        """
        Initialize a new partial object.

        :param func: The callable function to partially apply.
        :type func: Callable
        :param args: Positional arguments to pre-fill.
        :type args: Any
        :param keywords: Keyword arguments to pre-fill.
        :type keywords: Any
        :raises TypeError: If the first argument is not callable.
        """
        if not callable(func):
            raise TypeError("The first argument must be callable")
        if isinstance(func, PartialLike):
            # Wrap any nested partials
            args = func.args + args
            keywords = {**func.keywords, **keywords}
            func = func.func
        self = super().__new__(cls)

        # Pre-create a weakref to self for the weakref delete-callback
        selfref = weakref.ref(self)
        # Store a weak-reference to func
        self._func_ref = weakref.proxy(func, lambda _: WeakRefProxyPartial.__remove(selfref))
        self.args = args
        self.keywords = keywords
        self.__id = _IdHandle(self)
        return self

    #-----------------------------------------------------------------------------------------
    # Internal

    def __call__(self, /, *args: Any, **keywords: Any) -> Any | None:
        """
        Call the function with pre-filled and additional arguments.

        :param args: Additional positional arguments to pass to the function.
        :type args: Any
        :param keywords: Additional keyword arguments to pass to the function.
        :type keywords: Any
        :return: The result of the function call.
        :raises ReferenceError: If the referenced function has been deleted.
        """
        try:
            weakref.getweakrefcount(self._func_ref)
            keywords = {**self.keywords, **keywords}
            return self._func_ref(*self.args, *args, **keywords)
        except ReferenceError:
            return None

    @recursive_repr()
    def __repr__(self) -> str:
        """
        Return a string representation of the partial object.

        :return: A string representation of the partial object.
        :rtype: str
        """
        try:
            weakref.getweakrefcount(self._func_ref)
            func_repr = repr(self._func_ref)
        except ReferenceError:
            func_repr = "<deleted function>"
        qualname = type(self).__qualname__
        args = [func_repr]
        args.extend(repr(x) for x in self.args)
        args.extend(f"{k}={v!r}" for (k, v) in self.keywords.items())
        if type(self).__module__ == "functools":
            return f"functools.{qualname}({', '.join(args)})"
        return f"{qualname}({', '.join(args)})"

    def __bool__(self) -> bool:
        """
        Check whether the referenced function still exists.

        :return: True if the weakly-referenced function is still valid, False otherwise.
        :rtype: bool
        """
        try:
            weakref.getweakrefcount(self._func_ref)
            return True
        except ReferenceError:
            return False

    #-----------------------------------------------------------------------------------------
    # Properties

    @property
    def id(self) -> _IdHandle | None:
        """
        Return the internal identifier-handle.

        :return: The internal identifier-handle.
        """
        return self.__id

    #-----------------------------------------------------------------------------------------
    # Private

    @staticmethod
    def __remove(selfref: weakref.ReferenceType):
        """
        Callback function that is called when the weakly-referenced object is deleted.

        This function contains a weak-reference to the instance (`selfref`) to ensure that
        if the wrapper has already been collected, no action is required.

        :param selfref: A weak-reference to the instance of the class.
        :type selfref: weakref.ReferenceType
        """
        # Use a staticmethod instead of a monkey-patch
        if (sref := selfref()) is not None:
            if _DEBUG:
                _write(f'{_consoleStyle.fg.red}--> {sref.__class__.__name__}._remove '
                       f'{sref}{_consoleStyle.reset}')
            # Remove the handle, it could be used as a reference elsewhere
            sref.__id = None


#=========================================================================================
# OrderedWeakKeyDictionary
#=========================================================================================

class _IterationGuard:
    # This context manager registers itself in the current iterators of the
    # weak container, such as to delay all removals until the context manager
    # exits.
    # This technique should be relatively thread-safe (since sets are).

    def __init__(self, weakcontainer):
        # Don't create cycles
        self.weakcontainer = weakref.ref(weakcontainer)

    def __enter__(self):
        if (wc := self.weakcontainer()) is not None:
            wc._iterating.add(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if (wc := self.weakcontainer()) is not None:
            st = wc._iterating
            st.remove(self)
            if not st:
                # Handle _commit_removals when _iterating set is empty
                wc._commit_removals()


class OrderedWeakKeyDictionary(collections.OrderedDict):
    """
    A dictionary that preserves the order of keys and holds weak-references to the keys.

    Keys are weakly-referenced, allowing them to be garbage-collected when no strong
    references exist. This ensures memory-efficient storage while maintaining order.
    """

    def __init__(self, orderedDict=None):
        # A list of dead weak-refs (keys to be removed)
        self._pending_removals = []
        self._iterating = set()
        self._dirty_len = False
        super().__init__(orderedDict or {})

    #-----------------------------------------------------------------------------------------
    # Internal

    def __getitem__(self, key):
        """Retrieve the value for the specified key.
        """
        if ref := next((ref for ref in super().keys() if ref() == key), None):
            return super().__getitem__(ref)
        raise KeyError(key)

    def __setitem__(self, key, value):
        """Add or update an item in the dictionary. Keys are stored as weak-references.
        """
        if not isinstance(key, weakref.ReferenceType):
            _selfref = weakref.ref(self)
            weak_key = weakref.ref(key, lambda wref: OrderedWeakKeyDictionary.__remove(wref, _selfref))
        else:
            weak_key = key
        if _DEBUG:
            _write(f'{_consoleStyle.fg.green}--> {self.__class__.__name__}.__setitem__ '
                   f'{hex(id(self))} {weak_key}{_consoleStyle.reset}')
        super().__setitem__(weak_key, value)

    def __delitem__(self, key):
        """Remove an item from the dictionary by its key.
        """
        if ref := next((ref for ref in super().keys() if ref() == key), None):
            self._dirty_len = True
            return super().__delitem__(ref)
        raise KeyError(key)

    def __contains__(self, key):
        """Check if a key exists in the dictionary.
        """
        return any(ref == key for ref in self.keys())

    def __iter__(self):
        """Iterate over valid (non-collected) weak-references in the dictionary.
        """
        # Iterate over the parent OrderedDict
        with _IterationGuard(self):
            # Yield only valid references
            yield from (obj for ref in super().__iter__() if (obj := ref()) is not None)

    def __reversed__(self):
        """Iterate over valid (non-collected) weak-references in the dictionary in reverse order.
        """
        # Iterate over the parent OrderedDict in reverse
        with _IterationGuard(self):
            # Yield only valid references
            yield from (obj for ref in super().__reversed__() if (obj := ref()) is not None)

    def __deepcopy__(self, memo):
        from copy import deepcopy

        new = self.__class__()
        with _IterationGuard(self):
            for key, value in self.items():
                new[key] = deepcopy(value, memo)
        return new

    def __len__(self):
        if self._dirty_len and self._pending_removals:
            # self._pending_removals may still contain keys which were
            # explicitly removed, we have to scrub them (see issue #21173).
            self._scrub_removals()
        return super().__len__() - len(self._pending_removals)

    #-----------------------------------------------------------------------------------------
    # Private

    def _commit_removals(self):
        # NOTE: We don't need to call this method before mutating the dict,
        # because a dead weakref never compares equal to a live weakref,
        # even if they happened to refer to equal objects.
        # However, it means keys may already have been removed.
        while self._pending_removals:
            if (key := self._pending_removals.pop()):
                with suppress(KeyError):
                    if _DEBUG:
                        _write(f'{_consoleStyle.fg.darkyellow}--> {self.__class__.__name__}.__delitem__ pending {key}'
                               f'{_consoleStyle.reset}')
                    super(OrderedWeakKeyDictionary, self).__delitem__(key)

    def _scrub_removals(self):
        self._pending_removals = [k for k in self._pending_removals if k in self]
        self._dirty_len = False

    @staticmethod
    def __remove(key: Any, selfref: weakref.ReferenceType):
        """
        Removes the specified key from the `OrderedWeakKeyDictionary`, handling the removal
        either immediately or deferring it depending on the state of the object.

        If the object is currently iterating over its items, the removal is postponed and
        queued for later execution. Otherwise, the key is immediately removed from the
        dictionary. The method suppresses `KeyError` exceptions during the removal process.

        :param key: Dictionary key to be removed.
        :type key: Any
        :param selfref: A weak-reference to the object containing the dictionary. Used to access
                        the object and its state without creating strong references.
        :type selfref: weakref.ReferenceType
        """
        if (sref := selfref()) is not None:
            if sref._iterating:
                sref._pending_removals.append(key)
            else:
                with suppress(KeyError):
                    if _DEBUG:
                        _write(f'{_consoleStyle.fg.red}--> {sref.__class__.__name__}.__delitem__ {key}'
                               f'{_consoleStyle.reset}')
                    super(OrderedWeakKeyDictionary, sref).__delitem__(key)

    #-----------------------------------------------------------------------------------------
    # Methods

    def keys(self):
        """Iterate over non-collected keys in the dictionary.
        """
        with _IterationGuard(self):
            yield from (obj for ref in super().keys() if (obj := ref()) is not None)

    def items(self):
        """Iterate over key-value pairs with non-collected keys.
        """
        with _IterationGuard(self):
            yield from ((obj, value) for ref, value in super().items() if (obj := ref()) is not None)

    def values(self):
        """Iterate over values in the dictionary.
        """
        with _IterationGuard(self):
            yield from (self[ref] for ref in self.keys())

    def keyrefs(self):
        """Return a list of weak-references to the keys.

        The references are not guaranteed to be 'live' at the time
        they are used, so the result of calling the references needs
        to be checked before being used.  This can be used to avoid
        creating references that will cause the garbage collector to
        keep the keys around longer than needed.
        """
        return list(super().keys())

    def copy(self):
        new = OrderedWeakKeyDictionary()
        with _IterationGuard(self):
            for key, value in self.items():
                new[key] = value
        return new

    def popitem(self, last: bool = True):
        """Remove and return a (key, value) pair from the dictionary.
        Pairs are returned in LIFO order if last is True or FIFO order if False.
        """
        # Get the first or last item before calling popitem
        try:
            if last:
                # Should just do one iteration backwards
                ref_value_pair = next((itm for itm in reversed(super().items())))
            else:
                ref_value_pair = next((itm for itm in super().items()))
        except StopIteration:
            raise KeyError(f'{self.__class__.__name__}.popitem(): dictionary is empty')
        ref, value = ref_value_pair
        key = ref()
        self._dirty_len = True
        super().__delitem__(ref)
        return key, value

    def pop(self, key, *args):
        self._dirty_len = True
        return super().pop(key, *args)

    def move_to_end(self, key, last=True):
        value = self.pop(key)
        if last:
            self[key] = value
        else:
            # This is very expensive - superclass does not allow messing about :|
            currentOrder = list(super().items())
            self.clear()
            self[key] = value
            super().update(currentOrder)


#=========================================================================================
# WeakValueMappingView
#=========================================================================================

class WeakValueMappingView(Generic[_K, _V], Mapping[_K, _V]):
    """
    Live, read-only view over a :class:`weakref.WeakValueDictionary` that holds only a
    weak-reference to the underlying mapping.

    The view does **not** keep the underlying mapping alive. If the mapping has been
    garbage-collected, this view raises :class:`ReferenceError` on access via its public
    methods (see :method:`_live`).

    Iteration, ``len()``, and item access reflect the current live contents of the
    underlying weak mapping - values may disappear at any time due to garbage collection,
    as per :class:`weakref.WeakValueDictionary`
    semantics.

    * No mutation APIs are exposed (this class implements :class:`collections.abc.Mapping`).
    * Operations are **live** (not snapshot-based) and inherently subject to race-conditions
    with GC.

    **Example**
    ::
        from weakref import WeakValueDictionary
        from collections.abc import Mapping
        from typing import Generic, TypeVar

        _K = TypeVar("_K")
        _V = TypeVar("_V")

        class Owner(Generic[_K, _V]):
            def __init__(self) -> None:
                self._wvd: WeakValueDictionary[_K, _V] = WeakValueDictionary()
                self._view: WeakValueMappingView[_K, _V] = WeakValueMappingView(self._wvd)

            @property
            def view(self) -> Mapping[_K, _V]:
                \"\"\"Public, read-only access to the items.\"\"\"
                return self._view

    :ivar _wvd_ref: Weak-reference to the underlying
                    :class:`weakref.WeakValueDictionary`. If dereferenced and found
                    ``None``, the underlying mapping has been collected.
    :vartype _wvd_ref: weakref.ReferenceType[weakref.WeakValueDictionary[_K, _V]]
                       (or ``typing.ReferenceType``)
    """
    __slots__ = ("_wvd_ref",)

    def __init__(self, wvd: weakref.WeakValueDictionary[_K, _V]) -> None:
        """
        Initialize a live, read-only view over a weak-value-dictionary.

        :param wvd: The underlying weak value dictionary to be viewed. The view keeps
                    only a weak-reference to this object and will **not** prevent it
                    from being garbage-collected.
        :type wvd: weakref.WeakValueDictionary[_K, _V]
        """
        self._wvd_ref: weakref.ReferenceType[weakref.WeakValueDictionary[_K, _V]] = weakref.ref(wvd)

    def _live(self) -> weakref.WeakValueDictionary[_K, _V]:
        """
        Return the live underlying mapping or raise if it has been collected.

        This is a private helper that centralizes the dereferencing and validation
        of the weak-reference.

        :return: The underlying live :class:`weakref.WeakValueDictionary`.
        :rtype: weakref.WeakValueDictionary[_K, _V]
        :raises ReferenceError: If the underlying mapping has been garbage-collected.
        """
        wvd = self._wvd_ref()
        if wvd is None:
            raise ReferenceError("Underlying WeakValueDictionary has been garbage-collected")
        return wvd

    def __getitem__(self, key: _K) -> _V:
        """
        Retrieve the value for *key* from the underlying mapping.

        :param key: The key to look up.
        :type key: _K
        :return: The value associated with *key*.
        :rtype: _V
        :raises ReferenceError: If the underlying mapping has been garbage-collected.
        :raises KeyError: If *key* is not present in the (live) mapping.
        """
        return self._live()[key]

    def __iter__(self) -> Iterator[_K]:
        """
        Iterate over the keys of the underlying mapping.

        The iteration reflects the current state of the weak mapping. Keys may
        cease to be present if their associated values are garbage-collected
        during iteration.

        :return: An iterator over keys.
        :rtype: collections.abc.Iterator[_K]
        :raises ReferenceError: If the underlying mapping has been garbage-collected.
        """
        return iter(self._live())

    def __len__(self) -> int:
        """
        Return the current number of items in the underlying mapping.

        :return: The number of items visible at the moment of the call.
        :rtype: int
        :raises ReferenceError: If the underlying mapping has been garbage-collected.
        """
        return len(self._live())

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation of the view.

        If the underlying mapping is still live, this returns a representation
        including a **snapshot** of the current contents (converted to a strong
        :class:`dict` for display). If the mapping has been collected, returns
        ``\"<ClassName>(<dead>)\"``.

        :return: The representation string.
        :rtype: str
        """
        try:
            wvd = self._live()
        except ReferenceError:
            return f"{self.__class__.__name__}(<dead>)"
        return f"{self.__class__.__name__}({dict(wvd)!r})"


#=========================================================================================
# BoundConnector
#=========================================================================================

class WeakRefConnector(Generic[_T]):
    """
    A descriptor that provides a Pythonic, instance-bound connection syntax
    for an underlying WeakRefDescriptor (signal).

    When accessed via an instance (e.g. ``menu.connectToParent``), it returns a
    callable object bound to that instance. This eliminates the need for
    the user to manually pass the instance during connection.

    It is used to handle connecting methods to protected weak-ref-descriptors to be notified when
    they have been garbage-collected.

    *example*
    ::
        class MyClass:
            \"\"\"Class with a protected _parent attribute.
            \"\"\"
            _parent: WeakRefDescriptor[_T] = WeakRefDescriptor()
            connectToParent = WeakRefConnector(_parent)

        def respondToGC(*arg):
            ...

        my_instance = MyClass()
        my_instance.connectToParent(respondToGC)  # signal on an instance being GC'd
        MyClass.connectToParent(respondToGC)  # signal on ANY instance being GC'd

    :ivar _attrib: A weak-reference to the target WeakRefDescriptor instance (e.g. _parent).
    :vartype _attrib: weakref.ReferenceType[WeakRefDescriptor[_T]]
    """
    __slots__ = ("_attrib",)
    # Use Any for the weakref target type since the descriptor class is likely circular
    _attrib: weakref.ReferenceType[WeakRefDescriptor[_T]]

    def __init__(self, attrib: WeakRefDescriptor[_T]) -> None:
        """
        Initialise a new BoundConnector instance.

        The initializer is typically called once on the owning class
        (e.g. TableMenuABC) to store a weak-reference to the target descriptor.

        :param attrib: The underlying descriptor instance (e.g. TableMenuABC._parent).
        :type attrib: WeakRefDescriptor[_T]
        """
        super().__init__()
        # Store a weak-reference to the target WeakRefDescriptor object.
        self._attrib: weakref.ReferenceType[WeakRefDescriptor[_T]] = weakref.ref(attrib)

    # Overload 1: For class access (e.g. MyClass.descriptor)
    # The instance is None, and the method returns the descriptor itself.
    @overload
    def __get__(self, instance: None, owner: type[_Owner]) -> Self:
        ...

    # Overload 2: For instance access (e.g. my_instance.descriptor)
    # The instance is of type _Owner, and the method returns a partial containing the instance.
    @overload
    def __get__(self, instance: _Owner, owner: type[_Owner]) -> partial:
        ...

    def __get__(self, instance: _Owner | None, owner: type[_Owner]) -> Self | partial:
        """
        Retrieve the descriptor itself or a callable bound to the instance.

        This method implements the core descriptor protocol.

        :param instance: The instance for which the attribute is being accessed. If :code:`None`,
                         the descriptor was accessed via the class.
        :type instance: _Owner | None
        :param owner: The owner class of the descriptor (e.g. TableMenuABC).
        :type owner: Type[_Owner]
        :return: The BoundConnector instance (for class access) or a partially-applied
                 callable (for instance access).
        :rtype: WeakRefConnector | functools.partial
        """
        if instance is None:
            # If accessed via class (e.g. MyClass.connectToParent), return self
            return self
        # If accessed via instance (e.g. my_instance.connectToParent),
        # return a partial function that pre-fills the 'instance' argument for __call__.
        # This creates the desired bound method effect.
        return partial(self, _instance=instance)

    def __call__(self, func: Callable[..., Any], _instance: _Owner = None) -> None:
        """
        The method executed when the user calls the bound connector to register an observer.

        This receives the instance automatically from :py:func:`functools.partial`.
        It retrieves the target descriptor and calls its core :py:meth:`~WeakRefDescriptor.connect` method.
        Note, _instance is internal and not to be passed as a parameter by the user.

        :param func: The observer function or method to be connected.
        :type func: Callable[..., Any]
        :param _instance: The object instance to which the connection is bound (e.g. table.searchMenu).
        :type _instance: _Owner
        """
        # Retrieve the target WeakRefDescriptor. 'att' will be None if GC'd.
        if att := self._attrib():
            # Call the core connect method on the descriptor, passing the observer and the bound instance.
            att.connect(func, _instance)

#=========================================================================================
# Testing - see Test_WeakRefLib.py
#=========================================================================================
