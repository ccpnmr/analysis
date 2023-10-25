"""
CcpNmr version of the Traitlets; all subclassed for added functionalities:
-  _traitOrder
- fixing of default_value issues (see also https://github.com/ipython/traitlets/issues/165)
- if default_value == None, automatically set allow_none=True
- json handlers
- recursion for all container objects (list, dict, tuple, set, ...)
- Typed-dict (TDict) and typed-list (TList) traits
- added functionalities


#=========================================================================================
# macro code used during development
#=========================================================================================

from ccpn.util.traits.CcpNmrTraits import List, Any, Int,  \
    V3Object, CList, TList, CEnum, Dict, Float, CFloat, Instance, \
    TDict, OWTraits

from ccpn.util.traits.CcpNmrJson import CcpNmrJson, Constants, register

import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core.Project import Project as _Project

@register(overwrite=True)
class MyObj2(CcpNmrJson):

    saveAllTraitsToJson = True
    classVersion = 1.0
    classInfo = 'just a second test object'

    floats = TList(Float(min=0.0), default_value=[0.0]*2, maxlen=8)

    def __str__(self):
        return f'<MyObj2 {hex(id(self))}: floats={self.floats}>'

    __repr__ = __str__

#=========================================================================================

@register(overwrite=True)
class MyObj(CcpNmrJson):

    classVersion = 1.0
    saveAllTraitsToJson = True

    ints = TList(Int(max=10), default_value=[1,2,3], maxlen=4)
    types = TList(CEnum(specLib.DATA_TYPES), default_value=[specLib.DATA_TYPE_REAL]*8, maxlen=8)
    enum = CEnum(specLib.DATA_TYPES, default_value=specLib.DATA_TYPE_REAL)
    project = V3Object(klass=_Project)
    spectra = TList(V3Object(klass='Spectrum'))
    mi = Int(default_value=None)
    mydict = TDict(CFloat(), default_value={'aap':1.0})
    myfloat = CFloat(default_value=None, min=0.0)
    obj2 = OWTraits(klass=MyObj2, default_value=MyObj2())

    def __str__(self):
        return f'<MyObj {hex(id(self))}>'

    __repr__ = __str__
#=========================================================================================

obj = MyObj()
obj.project = project
obj.spectra = project.spectra
obj.print()
obj.obj2.floats = (1.0, 2.0, 3.0)
obj.print()

print('\n=== to/from Json ===')
js = obj.toJson()
# print(js)
objCopy1 = MyObj().fromJson(js)
objCopy1.print()

print('\n=== duplicate ===')
objCopy2 = obj.duplicate()
objCopy2.print()


"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
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
__dateModified__ = "$dateModified: 2023-10-25 17:43:54 +0100 (Wed, October 25, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import pathlib
import inspect

from collections import OrderedDict
from traitlets import \
    Long, Complex, CComplex, Bytes, CBytes, \
    ObjectName, DottedObjectName, \
    Type, This, ForwardDeclaredInstance, ForwardDeclaredType, \
    CaselessStrEnum, TCPAddress, CRegExp, \
    TraitType, default, validate, observe, Undefined, TraitError, All, Bunch

from traitlets import Any as _Any
from traitlets import Instance as _Instance
from traitlets import Int as _Int
from traitlets import CInt as _CInt
from traitlets import Float as _Float
from traitlets import CFloat as _CFloat
from traitlets import Unicode as _Unicode
from traitlets import CUnicode as _CUnicode
from traitlets import Bool as _Bool
from traitlets import CBool as _CBool
from traitlets import Enum as _Enum

from traitlets import List as _List
from traitlets import Set as _Set
from traitlets import Dict as _Dict
from traitlets import Tuple as _Tuple

from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase, DictTraitJsonHandlerABC, \
    ListTraitJsonHandlerABC, CcpNmrJsonClassHandlerABC

from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.DataEnum import DataEnum
from ccpn.util.Path import aPath, Path
from ccpn.util.Logging import getLogger


# _VALIDATOR = 'Validator'

class _CcpNmrTrait(object):
    """A class that:
    - Maintains and sets trait-order
    - Add functionalities to a Trait
    """
    _globalTraitOrder = 0

    def __init__(self, itemTrait=None, valueTrait=None, keyTrait=None):
        self._traitOrder = _CcpNmrTrait._globalTraitOrder
        _CcpNmrTrait._globalTraitOrder += 1

        # Fix the allow_none issue
        if self.default_value is None:
            self.allow_none = True

        # initialisation; attributes used TList, TDict, etc subclasses
        self.itemTrait = itemTrait
        self.valueTrait = valueTrait
        self.keyTrait = keyTrait

    def _fullName(self, obj) -> str:
        """:return a obj-class-name.trait-name string; eg.for error reporting
        """
        return _fullName(obj, self)

    def __str__(self):
        return f'<Trait {self.__class__.__name__} {repr(self.name)}>'

    __repr__ = __str__

    def getJsonHandler(self, obj):
        """Get the json handler from:
        - the trait metadata
        - the trait class definition

        :parameter obj: the parent object in which the trait defines
                        an attribute,
                        or
                        the container obj (list, dict, set, ...) if
                        the trait defines an item/value

        :return a json handler instance
        :raises RuntimeError if handler is not defined
        """
        # local import to avoid cycles
        from ccpn.util.traits.CcpNmrJson import Constants

        handler = None
        # check for trait specific handler in metadata of trait
        if (handler := self.get_metadata(Constants.JSONHANDLER))is not None:
            # we found a handler in the metadata
            pass

        # next, check for trait-class specific handler
        elif hasattr(self, Constants.JSONHANDLER):
            handler = getattr(self, Constants.JSONHANDLER)

        if handler is None:
            # This can only happen if some code deliberately removed the below definition!
            raise RuntimeError(f'No json handler for trait {self.name}')

        return handler(obj=obj, trait=self)

    class jsonHandler(TraitJsonHandlerBase):
        """A default json handler that does nothing
        """
        pass


#=========================================================================================
# Actual trait definitions
#=========================================================================================

class Any(_Any, _CcpNmrTrait):
    def __init__(self, default_value=None, **kwargs):
        _Any.__init__(self, default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)


class Instance(_Instance, _CcpNmrTrait):
    def __init__(self, **kwargs):
        if not 'default_value' in kwargs:
            raise ValueError('%s Traitlet without explicit default_value' % self.__class__.__name__)
        _Instance.__init__(self, **kwargs)
        _CcpNmrTrait.__init__(self)


class Int(_Int, _CcpNmrTrait):
    def __init__(self, **kwargs):
        _Int.__init__(self, **kwargs)
        _CcpNmrTrait.__init__(self)

    def validate(self, obj, value):
        if value is None and self.allow_none:
            return None
        if isinstance(value, (int,)):
            if (self.max is not None and value > self.max) or \
               (self.min is not None and value < self.min):
                raise ValueError(f'{self._fullName(obj)}: value {value} out of bounds; expected {self.info}')
            return value
        else:
            raise TypeError(f'{self._fullName(obj)}: expected type int, got {_classType(value)}')

    def info(self):
        """:return info string
        """
        _min = 'minInt' if self.min is None else str(self.min)
        _max = 'maxInt' if self.max is None else str(self.max)
        return f'an int between ({_min},{_max})'


class CInt(Int):
    """A casting version of the int trait.
    """
    def validate(self, obj, value):
        if value is None and self.allow_none:
            return value

        if not isinstance(value, int):
            try:
                value = int(value)
            except:
                raise TypeError(f'{self._fullName(obj)}: unable to cast {value} to int')

        return Int.validate(self, obj, value)


class Float(_Float, _CcpNmrTrait):
    def __init__(self, default_value=Undefined, allow_none=False, **kwargs):
        _Float.__init__(self, default_value=default_value, allow_none=allow_none, **kwargs)
        _CcpNmrTrait.__init__(self)

    def validate(self, obj, value):
        if value is None and self.allow_none:
            return value
        else:
            return _Float.validate(self, obj, value)

    def info(self):
        """:return info string
        """
        _min = '-inf' if self.min is None else str(self.min)
        _max = '+inf' if self.max is None else str(self.max)
        return f'an float between ({_min},{_max})'


class CFloat(Float):
    """A casting version of the float trait;
    i.e. float(value) is used to validate and hence value could also
         be a string
    """
    def validate(self, obj, value):
        if value is None and self.allow_none:
            return value
        else:
            return _CFloat.validate(self, obj, value)

    def info(self):
        """:return info string
        """
        _min = '-inf' if self.min is None else str(self.min)
        _max = '+inf' if self.max is None else str(self.max)
        return f'an float between ({_min},{_max})'

class Unicode(_Unicode, _CcpNmrTrait):
    def __init__(self, *args, **kwargs):
        _Unicode.__init__(self, *args, **kwargs)
        _CcpNmrTrait.__init__(self)


class CUnicode(Unicode):
    """A casting version of the Unicode trait; i.e. any value is converted to str
    """
    def validate(self, obj, value):
        if value is None and self.allow_none:
            return value
        else:
            return _CUnicode.validate(self, obj, value)


class Bool(_Bool, _CcpNmrTrait):
    def __init__(self, *args, **kwargs):
        _Bool.__init__(self, *args, **kwargs)
        _CcpNmrTrait.__init__(self)


class CBool(Bool):
    """A casting version of the Bool trait.
    """
    def validate(self, obj, value):
        if value is None and self.allow_none:
            return value
        else:
            return _CBool.validate(self, obj, value)


class Enum(_Enum, _CcpNmrTrait):
    """Enum trait; ordered version
    """
    def __init__(self, values, default_value=Undefined, **kwargs):
        # local import, because isotopeRecords in Common cause circular imports £%%$$GRr
        from ccpn.util.Common import isIterable
        if not isIterable(values):
            raise ValueError(f'Enum.__init__: Invalid parameter values {values}')
        values = list(values)
        if len(values) == 0:
            raise ValueError(f'Enum.__init__: parameter values has zero length')

        if default_value == Undefined:
            default_value = values[0]
        _Enum.__init__(self, values=tuple(values), default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)

    def info(self):
        """:return info string
        """
        return f'an Enum; one of {list(self.values)}'


class CEnum(Enum):
    """A trait that allows casting from a mapping of (value, enum-value) pairs.
    # Json serialisation will store the value (and automatically revert to enum-value)
    # upon restore.
    """
    def __init__(self, mapping, *args, **kwargs):
        """
        :param mapping: A list, mapping-dict or DataEnum instance that defines the
                        mapping: i.e.
                        list, tuple: will yield a (index, item) dict
                        dict: should be (value, enum-value) dict
                        DataEnum: will yield a (value, name) dict
        :param args: optional arguments
        :param kwargs: optional keyword arguments
        """
        if isinstance(mapping, dict):
            self._mapping = mapping
        elif isinstance(mapping, (list, tuple)):
            self._mapping = dict(enumerate(mapping))
        elif isinstance(mapping, DataEnum):
            self._mapping = dict(zip(mapping.values(), mapping.names()))
        else:
            raise ValueError(f'CEnum.__init__(): invalid mapping {mapping}')

        Enum.__init__(self, list(self._mapping.values()), *args, **kwargs)

    def validate(self, obj, value):
        """Validate value, optionally do mapping
        """
        if value is None and self.allow_none:
            return value

        if value in self._mapping.values():
            # first check if value is already ok before attempting a mapping
            pass
        elif value in self._mapping.keys():
            # not in values, so check if it is a keys and do the mapping
            value = self._mapping[value]

        return super().validate(obj, value)

    def info(self):
        """:return info string
        """
        return f'an CEnum; one of {list(self._mapping.values())} or {list(self._mapping.keys())}'

    class jsonHandler(TraitJsonHandlerBase):
        def encode(self, value):
            """Encode the value for json
            :returns the encoded value as a json serialisable object
            :raises RuntimeError if obj is None or (trait and item) ar both None
            """
            _inverseMap = dict((val, key) for key, val in self.trait._mapping.items())

            if value is None:
                return None

            if value in _inverseMap.keys():
                return _inverseMap[value]

            else:
                raise RuntimeError(f'Invalid value {value}; should be {self.trait.info()}')

       # def decode(self, value):  # from base class


class List(_List, _CcpNmrTrait):
    """List-trait, ordered version, minlen/maxlen properties
    Fixing default_value problem
    """

    def __init__(self, default_value=[], minlen=0, maxlen=sys.maxsize, **kwargs):
        """
        Initialise the object
        :param default_value: the default value of the list
        :param minlen: minimum length of the list
        :param maxlen: maximum length of the list
        :param kwargs: optional keyword arguments
        """

        _List.__init__(self, default_value=default_value, minlen=minlen, maxlen=maxlen, **kwargs)
        _CcpNmrTrait.__init__(self)

        if default_value is not None:
            self.default_value = default_value

    @property
    def minlen(self):
        """:return the minimum length of the list
        """
        return self._minlen

    @property
    def maxlen(self):
        """:return the maximum length of the list
        """
        return self._maxlen

    class jsonHandler(ListTraitJsonHandlerABC):
        klass = list


class CList(List):
    """An List trait with casting from any iterable
    """

    def validate(self, obj, theList):
        """
        Validate theList
        :param obj: object containing trait
        :param theList: new value (list or iterable) for the trait to be validated
        :return: validated (and optionally converted) theList
        :raises: ValueError
        """
        # local import, because isotopeRecords in Common cause circular imports £%%$$GRr
        from ccpn.util.Common import isIterable

        if theList is None and self.allow_none:
            return None

        if isinstance(theList, list):
            return theList

        elif isIterable(theList):
            return [val for val in theList]

        else:
            raise ValueError(f'{self._fullName(obj)}: expected list or iterable, got {theList}')


class _TypedList(list):
    """A list with only specific type of items as defined by itemTrait;
    to be used by CcpNmr TList trait only
    Changing a list value, i.e. mylist[item] = value, extend() and append(), or del trigger traitlets
    change notifiers (if set on the TLict trait). The change-dict has an additional "itemsChanged"
    key with (item/key, value) pairs of those elements that have changed.
    """

    def __init__(self, obj, trait, values=[]):
        if not isinstance(trait, TraitType):
            raise TypeError(f'Invalid trait; expected TraitType instance')
        if not isinstance(values, (list, tuple)):
            raise TypeError(f'Invalid values; expected list or tuple instance')

        if trait.itemTrait is None:
            raise RuntimeError(f'trait.itemTrait is undefined')

        # we store these a private attributes, as the _TypedList instance becomes exposed
        # to the users. Hence, it need to look and feel as a regular list
        self._trait = trait
        self._itemTrait = trait.itemTrait
        self._obj = obj

        super().__init__()

        if len(values) < self._trait.minlen:
            raise ValueError(f'{self._fullName}.__init__(): too few initial items ({len(values)}); should be minimum of {self._trait.minlen}')
        if len(values) > self._trait.maxlen:
            raise ValueError(f'{self._fullName}.__init__(): too many initial items ({len(values)}); should be maximum of {self._trait.maxlen}')

        self.extend(values)

    def _validateItem(self, item, value):
        """
        Validate an item
        :param item: the index, i.e. item, in the list
        :param value: value for the item to be validated used self._itemTrait (if
                      self._itemTrait is not None and not Any)
        :return: validated (and optionally converted) value
        :raises: ValueError, TypeError
        """
        if self._itemTrait is None or isinstance(self._itemTrait, Any):
            return value

        try:
            value = self._itemTrait.validate(self._obj, value)
        except (TraitError, ValueError):
            raise ValueError(f'{self._fullName}[{item}]: invalid value {repr(value)}, expected {self._itemTrait.info()}')
        except TypeError:
            raise ValueError(f'{self._fullName}[{item}]: invalid type, expected {self._itemTrait.info()} got {_classType(value)}')

        return value

    def _newChangeBunch(self, subType) -> Bunch:
        """:return a new Bunch instance for change notification
        """
        change = Bunch()
        change.type = 'change'
        change.subType = subType
        change.name = self._trait.name
        change.owner = self._obj
        change.old = list(self)
        return change

    def _handleSliceItem(self, item, count):
        """Handle the slice item and translate into (start, stop, step) tuple
        """
        # examine slice parameters
        _start = item.start if item.start is not None else 0
        if _start < 0:
            # handle negative starts
            _start = _start % len(self)
        _step = item.step if item.step is not None else 1
        if item.stop is not None:
            _stop = item.stop
        elif count is not None:
            _stop = _start + count*_step
        else:
            _stop = len(self)
        return _start, _stop, _step

    def __setitem__(self, item, value):
        # local import because of cycles £$£$%^^&&
        from ccpn.util.Common import isIterable

        change = self._newChangeBunch(subType='__setitem__')

        if isinstance(item, int):
            if item >= len(self):
                raise IndexError(f'{self._fullName}[{item}] = {repr(value)}; list index should be < {len(self)}')
            newValue = self._validateItem(item, value)
            change.itemsChanged = [(item, newValue)]

        elif isinstance(item, slice):
            if not isIterable(value):
                raise ValueError(f'Expected iterable; got {value}')

            _start, _stop, _step = self._handleSliceItem(item, len(value))

            if _stop > self._trait.maxlen:
                raise IndexError(f'{self._fullName}[{_start}:{_stop}] = {repr(value)}; list maximum length is {self._trait.maxlen}')
            if  ((_stop - _start) // _step) < len(value):
                raise IndexError(f'{self._fullName}[{item.start}:{item.stop}] = {repr(value)}; too few items to assign')

            newValue = [self._validateItem(i, val) for i,val in zip(range(_start, _stop, _step), value)]
            # get all items that changed
            change.itemsChanged = [(i,val) for i,val in zip(range(_start, _stop, _step), newValue)]

        else:
            raise IndexError(f'{self._fullName}[]: expected int or slice; got {item}')

        super().__setitem__(item, newValue)

        change.new = self
        self._obj.notify_change(change)

    def __delitem__(self, item):

        change = self._newChangeBunch(subType='__delitem__')

        if isinstance(item, int):
            if item >= len(self):
                raise IndexError(f'{self._fullName}[{item}]; list index should be < {len(self)}')
            change.itemsChanged = [(item, self[item])]

        elif isinstance(item, slice):
            _start, _stop, _step = self._handleSliceItem(item, None)

            if _stop < self._trait.minlen:
                raise IndexError(f'{self._fullName}[{_start}:{_stop}]; list minimum length is {self._trait.minlen}')

            # get all items that got deleted
            change.itemsChanged = [(i, self[i]) for i in range(_start, _stop, _step)]

        else:
            raise IndexError(f'{self._fullName}[]: expected int or slice; got {item}')

        super().__delitem__(item)

        change.new = self
        self._obj.notify_change(change)

    def extend(self, values):
        """Extend self with values
        """
        _len = len(self)
        if _len+len(values) > self._trait.maxlen:
            raise ValueError(f'{self._fullName}.extend(): {len(values)} additional items would exceed maximum length ({self._trait.maxlen})')

        values = [self._validateItem(_len+i, val) for i, val in enumerate(values)]

        change = self._newChangeBunch(subType='extend')
        change.itemsChanged = [(_len+i, val) for i, val in enumerate(values)]

        super().extend(values)

        change.new = self
        self._obj.notify_change(change)

    def append(self, value):
        """Append self with value
        """
        _len = len(self)
        if _len+1 > self._trait._maxlen:
            raise ValueError(f'{self._fullName}.append(): an additional item would exceed maximum length ({self._trait._maxlen})')

        value = self._validateItem(_len+1, value)

        change = self._newChangeBunch(subType='append')
        change.itemsChanged = [(_len, value)]

        super().append(value)

        change.new = self
        self._obj.notify_change(change)

    def copy(self):
        return _TypedList(obj=self._obj, trait=self._trait, values=self[:])

    @property
    def _fullName(self):
        """:return: obj-classname.traitname
        """
        return _fullName(self._obj, self._trait)

    def __str__(self):
        # Need to define this, as I do define __repr__ and it will otherwise map to __str__ as well
        return super().__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'


class TList(List):
    """An Typed-List trait with:
    - casting from any iterable
    - Item validation; i.e. by the itemTrait defined in the init.
    """
    def __init__(self, itemTrait, default_value=[], minlen=0, maxlen=sys.maxsize, **kwargs):
        """
        Initialise the object
        :param itemTrait: An optional trait instance to validate the items
        :param default_value: the default value of the list
        :param minlen: minimum length of the list
        :param maxlen: maximum length of the list
        :param kwargs: optional keyword arguments
        """
        # fixing old signature
        if 'trait' in kwargs:
            itemTrait = kwargs['trait']
            del kwargs['trait']
            getLogger().warning(f'TList trait: depricated {repr("trait")} keyword, use {repr("itemTrait")} instead')

        if itemTrait is None or not isinstance(itemTrait, TraitType):
            raise ValueError(f'TList parameter itemTrait: invalid, got {itemTrait}')

        super().__init__(default_value=default_value, minlen=minlen, maxlen=maxlen, **kwargs)
        self.itemTrait = itemTrait

    def validate(self, obj, theList):
        """
        Validate theList
        :param obj: object containing trait
        :param theList: new value (list or iterable) for the trait to be validated
        :return: validated (and optionally converted) theList
        :raises: ValueError
        """
        # local import, because isotopeRecords in Common cause circular imports £%%$$GRr
        from ccpn.util.Common import isIterable

        if theList is None and self.allow_none:
            return None

        if isinstance(theList, _TypedList):
            return theList

        elif isIterable(theList):
            _tmp = [val for val in theList]
            return _TypedList(obj=obj, trait=self, values=_tmp)

        else:
            raise ValueError(f'{_fullName(obj, self)}: expected list or iterable, got {theList}')

    class jsonHandler(ListTraitJsonHandlerABC):
        klass = _TypedList


class RecursiveList(List):
    """A list trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    DEPRICATED: use List or CList
    """
    pass


class Set(_Set, _CcpNmrTrait):
    """Fixing default_value problem
    """

    def __init__(self, trait=None, default_value=None, minlen=0, maxlen=sys.maxsize, **kwargs):
        _Set.__init__(self, trait=trait, default_value=default_value, minlen=minlen, maxlen=maxlen, **kwargs)
        _CcpNmrTrait.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    class jsonHandler(ListTraitJsonHandlerABC):
        klass = set


class RecursiveSet(Set):
    """A Set trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    DEPRICATED: use Set
    """
    pass


class Tuple(_Tuple, _CcpNmrTrait):
    """Fixing default_value problem
    """
    def __init__(self, *traits, **kwargs):
        default_value = kwargs.setdefault('default_value', None)
        _Tuple.__init__(self, *traits, **kwargs)
        _CcpNmrTrait.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    class jsonHandler(ListTraitJsonHandlerABC):
        klass = tuple


class CTuple(Tuple):
    """Casting tuple, any iterable
    """
    def validate(self, obj, values):
        # local import, because isotopeRecords in Common cause circular imports £%%$$GRr
        from ccpn.util.Common import isIterable

        if values is None and self.allow_none:
            return values

        if isinstance(values, (tuple, list)):
            pass
        elif isIterable(values):
            values = [val for val in values]
        values = self.validate_elements(obj, values)
        return tuple(values)


class RecursiveTuple(Tuple):
    """A tuple trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    DEPRICATED: use Tuple or CTuple
    """
    pass


class Dict(_Dict, _CcpNmrTrait):
    """Fixing default_value problem
    Use TDict for a dict with type checking
    """

    def __init__(self, default_value={}, **kwargs):
        """
        :param default_value: the default for the trait
        :param kwargs: additional optional parameters of the Dict trailet, like allow_none, read_only ...
        """
        if default_value is None:
            kwargs['allow_none'] = True
        _Dict.__init__(self, default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    class jsonHandler(DictTraitJsonHandlerABC):
        klass = dict

class UDict(Dict):
    """A dict that updates the current value, rather than overwrites
    """
    class jsonHandler(DictTraitJsonHandlerABC):
        klass = dict

        def decode(self, theData):
            _decoded = super().decode(theData)
            _theDict = self.obj.getTraitValue(self.trait.name)
            _theDict.update(_decoded)
            return _theDict

class RecursiveDict(Dict):
    """A dict trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    DEPRICATED: use Dict, CDict, TDict
    """
    pass


class Adict(TraitType, _CcpNmrTrait):
    """A trait that defines a json serialisable AttributeDict; 
    dicts or (key,value) iterables are automatically cast into AttributeDict
    Recursion is not active by default, but can be set
    """
    default_value = AttributeDict()
    info_text = "'an AttributeDict'"

    def __init__(self, default_value={}, **kwargs):
        """
        :param default_value: the default for the trait
        :param kwargs: additional optional parameters of the Dict trailet, like allow_none, read_only ...
        """
        if default_value is not None:
            self.default_value = default_value
        TraitType.__init__(self, default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)

    def validate(self, obj, value):
        """Assure a AttributeDict instance
        """
        if isinstance(value, AttributeDict):
            return value
        elif isinstance(value, dict):
            return AttributeDict(**value)
        elif isinstance(value, list) or isinstance(value, tuple):
            return AttributeDict(value)
        else:
            raise TypeError(f'validate(value): invalid, got {value} but expected an AttributeDict, dict or iterable')

    # trait-specific json handler
    class jsonHandler(DictTraitJsonHandlerABC):
        klass = AttributeDict
# end class


class RecursiveAdict(Adict):
    """A trait that defines a json serialisable AttributeDict;
    dicts or (key,value) iterables are automatically cast into AttributeDict
    Recursion is active
    DEPRICATED: use Adict instead
    """
    # trait-specific json handler
    pass
# end class


class Odict(TraitType, _CcpNmrTrait):
    """A trait that defines a json serialisable OrderedDict;
    dicts are automatically cast into OrderedDict
    Recursion is not active
    """
    default_value = OrderedDict()
    info_text = "'an OrderedDict'"

    def __init__(self, default_value={}, **kwargs):
        """
        :param default_value: the default for the trait
        :param kwargs: additional optional parameters of the Dict trailet, like allow_none, read_only ...
        """
        TraitType.__init__(self, default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    def validate(self, obj, value):
        """Assure a OrderedDict instance
        """
        if isinstance(value, OrderedDict):
            return value
        elif isinstance(value, dict):
            return OrderedDict(list(value.items()))
        elif isinstance(value, (list, tuple)):
            return  OrderedDict(value)
        else:
            raise TypeError(f'validate(value): invalid, got {value} but expected an OrderedDict, dict or iterable')

    # trait-specific json handler
    class jsonHandler(DictTraitJsonHandlerABC):
        klass = OrderedDict
# end class


class RecursiveOdict(Odict):
    """A trait that defines a json serialisable OrderedDict;
    dicts are automatically cast into OrderedDict
    Recursion is active
    DEPRICATED: use Odict
    """
    pass
# end class


class _TypedDict(dict):
    """A dict with only specific type of values as defined by valueTrait;
    to be used by CcpNmr CDict trait only
    Changing a dict value, i.e. d[key] = value, update, or del d[key] trigger traitlets
    change notifiers (if set on the TDict trait). The change-dict has an additional "itemsChanged"
    key with (item/key, value) pairs of those elements that have changed.
    """

    def __init__(self, obj, trait, values={}):
        if not isinstance(trait, TraitType):
            raise TypeError(f'Invalid trait; expected TraitType instance')
        if not isinstance(values, dict):
            raise TypeError(f'Invalid values; expected dict instance; got {type(values)}')

        self._trait = trait
        self._valueTrait = trait.valueTrait
        self._obj = obj

        super().__init__()

        self.update(values)

    def _validateValue(self, key, value):
        """
        Validate an value
        :param key: the key of the value in the dict
        :param value: value to be validated used self._valueTrait (if
                      self._valueTrait is not None and not Any)
        :return: validated (and optionally converted) value
        :raises: ValueError
        """
        if self._valueTrait is None or isinstance(self._valueTrait, Any):
            return value

        # GWV: bit of a silly construct to catch the errors properly;
        # raising the error in the except clause gives poor output in console; not sure why
        _error = False
        try:
            value = self._valueTrait.validate(self._obj, value)
        except (TraitError, ValueError) as es:
            _error= True
        finally:
            if _error:
                raise ValueError(f'{self._fullName}[{key}]: invalid value {repr(value)}, expected {self._valueTrait.info()}')

        return value

    def _newChangeBunch(self, subType) -> Bunch:
        """:return a new Bunch instance for change notification
        """
        change = Bunch()
        change.type = 'change'
        change.subType = subType
        change.name = self._trait.name
        change.owner = self._obj
        change.old = dict(self.items())
        return change

    def __setitem__(self, key, value):
        value = self._validateValue(key, value)

        change = self._newChangeBunch(subType='__setitem__')
        super().__setitem__(key, value)
        change.itemsChanged = [(key, value)]
        change.new = self
        self._obj.notify_change(change)

    def __delitem__(self, key):
        if key not in self:
            raise KeyError(f'Key {key} not in {self._fullName}')
        value = self[key]

        change = self._newChangeBunch(subType='__setitem__')
        super().__delitem__(key)
        change.itemsChanged = [(key, value)]
        change.new = self
        self._obj.notify_change(change)

    def update(self,  E=None, **F): # known special case of dict.update
        """
        D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
        If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
        If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
        In either case, this is followed by: for k in F:  D[k] = F[k]

        Validates each value before updating
        """
        change = self._newChangeBunch(subType='update')
        change.itemsChanged = []

        # GWV: logic implemented form doc description above
        if E is not None and hasattr(E, 'keys'):
            for key in getattr(E, 'keys')():
                value = E[key]
                value = self._validateValue(key, value)
                super().__setitem__(key, value)
                change.itemsChanged.append((key, value))

        elif E is not None and not hasattr(E, 'keys'):
            for key, value in E.items():
                value = self._validateValue(key, value)
                super().__setitem__(key, value)
                change.itemsChanged.append((key, value))

        for key, value in F.items():
            value = self._validateValue(key, value)
            super().__setitem__(key, value)
            change.itemsChanged.append((key, value))

        change.new = self
        self._obj.notify_change(change)

    @property
    def _fullName(self):
        """:return: obj-classname.traitname
        """
        return f'{self._obj.__class__.__name__}.{self._trait.name}'

    def __str__(self):
        # Need to define this, as I do define __repr__ and it will otherwise map to __str__ as well
        return super().__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'


class TDict(Dict):
    """A typed-dict trait; i.e. the values of the dict will be checked to adhere to
    a trait-instance definition provided upon initialisation. Currently, all values
    need to be of the type defined by a single trait instance. This may be expanded
    in the future with a key-based definition.
    Changing a dict value, i.e. d[key] = value and update() trigger traitlets change notifiers
    (if set on the TDict trait)
    """
    def __init__(self, valueTrait, default_value={}, **kwargs):
        """
        Initialise the object
        :param valueTrait: A trait instance to validate the value of a (key,value) pair
        :param default_value: the default value of the dict
        :param kwargs: optional keyword arguments
        """
        # fixing old signature
        if 'trait' in kwargs:
            valueTrait = kwargs['trait']
            del kwargs['trait']
            getLogger().warning(f'TList trait: depricated {repr("trait")} keyword, use {repr("valueTrait")} instead')

        if valueTrait is None or not isinstance(valueTrait, TraitType):
            raise ValueError(f'parameter valueTrait: invalid, got {valueTrait}')

        super().__init__(default_value=default_value, **kwargs)

        self.valueTrait = valueTrait  # This is also store by traitlets, but do not like using private attributes

    def validate(self, obj, theDict) -> _TypedDict | None:
        """
        Validate theDict
        :param obj: object containing trait
        :param theDict: new value for the trait to be validated
        :return: validated (and optionally converted) theList
        :raises: ValueError
        """

        if theDict is None and self.allow_none:
            return None

        if isinstance(theDict, _TypedDict):
            return theDict

        elif isinstance(theDict, dict):
            return _TypedDict(obj=obj, trait=self, values=theDict)

        else:
            raise ValueError(f'{obj.__class__.__name__}.{self.name}: expected dict, got {theDict}')

    class jsonHandler(DictTraitJsonHandlerABC):
        klass = _TypedDict


class Immutable(Any, _CcpNmrTrait):
    info_text = 'an immutable object, intended to be used as constant'

    def __init__(self, value):
        TraitType.__init__(self, default_value=value, read_only=True)
        _CcpNmrTrait.__init__(self)


class CPath(TraitType, _CcpNmrTrait):
    """A trait that defines a casting Path object and is json serialisable
    """
    default_value = aPath('.')
    info_text = "'an Path object'"

    def __init__(self, default_value='', allow_none=False, read_only=False, **kwargs):
        TraitType.__init__(self, default_value=default_value, allow_none=allow_none, read_only=read_only, **kwargs)
        _CcpNmrTrait.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    def validate(self, obj, value):
        """Assure a Path instance
        """
        if value is None and self.allow_none:
            return value

        if isinstance(value, Path):
            pass

        elif isinstance(value, pathlib.Path) or isinstance(value, str):
            value = Path(value)

        else:
            self.error(obj, value)

        return value

    # trait-specific json handler
    class jsonHandler(TraitJsonHandlerBase):
        """Serialise Path to be json compatible.
        """
        def encode(self, value):
            # stores as a str for json if not None
            if value is not None:
                value = str(value)
            return value

        def decode(self, value):
            # needs conversion from str into Path if not None
            if value is not None:
                value = Path(value)
            return value
    # end class
# end class


class CString(TraitType, _CcpNmrTrait):
    """A trait that defines a string object, casts from bytes object and is json serialisable
    """
    default_value = ''
    info_text = "'an string'"

    NONE_VALUE = '__CSTRING_NONE_VALUE__'

    def __init__(self, default_value='', encoding='utf8', allow_none=False, read_only=None, **kwargs):
        TraitType.__init__(self, default_value=default_value, allow_none=allow_none, read_only=read_only, **kwargs)
        _CcpNmrTrait.__init__(self)
        self.encoding = encoding
        if default_value is not None:
            self.default_value = default_value

    def asBytes(self, value):
        """Return value encoded as a bytes object; encode None"""
        if value is None:
            value = self.NONE_VALUE
        return bytes(value, self.encoding)

    def fromBytes(self, value):
        """Return value decoded from bytes object; decode NONE_VALUE to None"""
        # 3.1.0.alpha2: encountered error that value was of type str
        if isinstance(value, bytes):
            value = value.decode(self.encoding)
        if value == self.NONE_VALUE:
            value = None
        return value

    def validate(self, obj, value):
        """Assure a str instance
        """
        if value is None and self.allow_none:
            return value

        if isinstance(value, str):
            pass

        elif isinstance(value, bytes):
            value = self.fromBytes(value)
            # Test again if None is allowed, as this was missed if it was encoded as NONE_VALUE
            if value is None and not self.allow_none:
                self.error(obj, value)

        else:
            self.error(obj, value)

        return value

# GWV: moved to CoreTraits
# class V3Object(TraitType, _CcpNmrTrait):
#     """A trait that defines a V3-object, json serialisable through its Pid
#     """
#     default_value = None
#     info_text = "A V3-Object"
#
#     def __init__(self, klass=None, default_value=None, **kwargs):
#         """
#         Initialise the trait
#         :param klass: only allow objects of type klass (V3object or className str);
#                       ignored when None
#         :param default_value: value set by default (None)
#         :param kwargs: optional
#         """
#         from ccpn.core._implementation.CoreModel import _isV3coreClass, _isV3coreClassInstance, _getV3coreClass
#
#         if klass is None:
#             self._klass = None
#
#         else:
#
#             if _isV3coreClass(klass):
#                 self._klass = klass
#
#             elif isinstance(klass, str) and \
#                (_klass := _getV3coreClass(klass)) is not None:
#                 self._klass = _klass
#
#             else:
#                 raise ValueError(f'parameter klass: expected a valid V3 class; got {klass}')
#
#         TraitType.__init__(self, default_value=default_value, **kwargs)
#         _CcpNmrTrait.__init__(self)
#
#         if default_value is not None:
#             self.default_value = default_value
#
#     def validate(self, obj, value):
#         """Assure a Core-class instance
#         :raises TypeError, ValueError
#         """
#         from ccpn.core._implementation.CoreModel import _isV3coreClass, _isV3coreClassInstance, _getV3coreClass
#
#         if value is None and not self.allow_none:
#             raise ValueError(f'Expected an instance of a V3 class; got None')
#
#         elif self._klass is not None and not isinstance(value, self._klass):
#             raise TypeError(f'Expected an instance of {_classType(self._klass)}; got {value} {_classType(value)}')
#
#         elif not _isV3coreClassInstance(value):
#             raise TypeError(f'Expected an instance of a V3 class; got {value} {_classType(value)}')
#
#         return value
#
#     # trait-specific json handler
#     class jsonHandler(TraitJsonHandlerBase):
#         """json compatible;
#         """
#         def encode(self, value):
#             "returns a json serialisable object"
#             if value is None:
#                 return None
#             else:
#                 return str(value.pid)
#
#         def decode(self, value):
#             "uses value to generate and set the new (or modified) obj"
#             if value is None:
#                 return None
#             else:
#                 _app = getApplication()
#                 if (result := _app.get(value)) is None:
#                     getLogger().warning('Error decoding %r; set to None' % value)
#                 return result
# # end class

#
# class V3ObjectList(TList):
#     """A trait that defines a list of V3-objects, json serialisable through their Pid's
#     DEPRICATED: use TList(V3Object(), ....) instead
#     """
#     default_value = []
#     info_text = "A V3-ObjectList"
#
#     def __init__(self, default_value = [], **kwargs):
#         TList.__init__(self, itemTrait=V3Object(allow_none=True), default_value=default_value, **kwargs)
#
# # end class
#

class OWTraits(TraitType, _CcpNmrTrait):
    """A trait for CcpNmrJson object with traits instance
    """

    klass = None  # can subclass to overwrite this

    def __init__(self, klass=None, default_value=None, **kwds):
        """Initialise the CcpNmrJson trait.

        :parameter klass: Optional parameters to define a CcpNmrJson subclass, either as
                          a class object or its string registered representation
        :parameter default_value: if not None, a duplicate will be made of the default using
                                  the duplicate function of the CcpNmrJson class.
        """
        # local import to prevent cycles
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        # set the klass for this trait; default to class attribute klass or CcpNmrJson, or the value
        # given as the klass parameter to the call.
        if klass is None:
            self.klass = OWTraits.klass if OWTraits.klass is not None else CcpNmrJson

        else:
            if klass in CcpNmrJson._registeredClasses.values():
                self.klass = klass

            elif isinstance(klass, str):
                if (_cls := CcpNmrJson._registeredClasses.get(klass)) is not None:
                    self.klass = _cls
                else:
                    raise ValueError(f'parameter klass: invalid, class {repr(klass)} is not registered')
            else:
                raise ValueError(f'parameter klass: invalid; got {klass}')

        if default_value is not None:
            if not isinstance(default_value, self.klass):
                raise TypeError(f'parameter default_value: expected {_classType(self.klass)} instance, got {_classType(default_value)}')

        TraitType.__init__(self, default_value=default_value, **kwds)
        _CcpNmrTrait.__init__(self)

    def default(self, obj=None):
        """Initialise the default for this trait
        :return The default value
        """
        if self.default_value is None:
            return None
        else:
            return self.default_value.duplicate()

    def validate(self, obj, value):
        if value is None and self.allow_none:
            return value

        if not isinstance(value, self.klass):
            raise TypeError(f'validate value: expected {_classType(self.klass)} instance; got {_classType(value)}')

        return value

    class jsonHandler(CcpNmrJsonClassHandlerABC):

        def encode(self, value):
            _klass = self.trait.klass
            if not isinstance(value, _klass):
                raise TypeError(f'encode value: expected  {_classType(_klass)} instance; got {_classType(value)}')
            return super().encode(value)

        def decode(self, value):
            # decode value; a dict defining a self.trait.klass instance
            _klass = self.trait.klass
            if not _klass._isEncodedObject(value):
                raise RuntimeError(f'decode value: error decoding and initialising {_classType(_klass)} instance')
            return super().decode(value)



#=========================================================================================
# Helper functions
#=========================================================================================

def _fullName(obj, trait):
    """Helper function to yield a string
    className.traitName
    """
    return f'{obj.__class__.__name__}.{trait.name}'

def _classType(obj):
    """Helper function to yield a more managable class description for an object (either class or instance)
    (in lieu of type())
    """
    if inspect.isclass(obj):
        return f'<class {repr(obj.__name__)}>'
    else:
        return f'<class {repr(obj.__class__.__name__)}>'



#=========================================================================================
# GWV unused code (for now); validator concept
#=========================================================================================
#
#
#     def useValidator(self, obj, value):
#         """General validate; use validator class if defined
#         Check for None
#         :return value or modified value
#         """
#         if value is None:
#             if self.allow_none:
#                 return None
#             raise ValueError(f'{_fullName(obj, self)}.validate(): None is not allowed')
#
#         if (validator := getattr(self, _VALIDATOR, None)) is not None:
#             return validator(obj, self).validate(value)
#
#         else:
#             raise ValueError(f'{_fullName(obj, self)}.validate(): No validator')
#
#
#
# class ValidatorABC(object):
#     """A class to hold validator information
#     """
#     validateItems = False  # flag to set
#
#     def __init__(self, obj, trait):
#
#         if not isinstance(trait, _CcpNmrTrait):
#             raise TypeError(f'Invalid trait; expected CcpNmr Trait instance, got {_classType(trait)}')
#
#         self.obj = obj
#         self.trait = trait
#         self.itemTrait = trait.itemTrait
#
#     def validate(self, value):
#         """Validate the value
#         :return value or modified value
#         :raises ValueError if value is not appropriate
#         To be subclassed
#         """
#         return value
#
# class xyz
#
#     validate = _CcpNmrTrait.useValidator
#
#     class Validator(ValidatorABC):
#         def validate(self, value):
#             """Validate value, optionally do mapping
#             """
#             if value in self.trait._mapping.values():
#                 # first check if value is already ok before attempting a mapping
#                 pass
#             elif value in self.trait._mapping.keys():
#                 # not in values, so check if it is a keys and do the mapping
#                 value = self.trait._mapping[value]
#             else:
#                 raise ValueError(f'{_fullName(self.obj, self.trait)}: {value} is invalid; expected {self.trait.info()}')
#
#             return value
