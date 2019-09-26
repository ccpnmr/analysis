"""
CcpNmr version of the Trailets; all subclassed for added functionalities:
-  _traitOrder
- fixing of default_value issues
- json handlers

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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

from collections import OrderedDict
from traitlets import \
    Long, Complex, CComplex, \
    Unicode, Bytes, CUnicode, CBytes, ObjectName, DottedObjectName, \
    Instance, Type, This, ForwardDeclaredInstance, ForwardDeclaredType, ForwardDeclaredMixin, \
    Enum, CaselessStrEnum, TCPAddress, CRegExp, Any, \
    TraitType, default, validate, observe, Undefined, HasTraits

from traitlets import Int as _Int
from traitlets import CInt as _CInt
from traitlets import Float as _Float
from traitlets import CFloat as _CFloat
from traitlets import Unicode as _Unicode
from traitlets import CUnicode as _CUnicode
from traitlets import Bool as _Bool
from traitlets import CBool as _CBool

from traitlets import List as _List
from traitlets import Set as _Set
from traitlets import Dict as _Dict
from traitlets import Tuple as _Tuple

from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase, RecursiveDictHandlerABC, \
    RecursiveListHandlerABC
from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.Path import aPath, Path

class _Ordered(object):
    "A class that maintains and sets trait-order"

    _globalTraitOrder = 0

    def __init__(self):
        self._traitOrder = _Ordered._globalTraitOrder
        _Ordered._globalTraitOrder += 1


class Int(_Int, _Ordered):
    def __init__(self, *args, **kwargs):
        _Int.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class CInt(_CInt, _Ordered):
    def __init__(self, *args, **kwargs):
        _CInt.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class Float(_Float, _Ordered):
    def __init__(self, *args, **kwargs):
        _Float.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class CFloat(_CFloat, _Ordered):
    def __init__(self, *args, **kwargs):
        _CFloat.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class Unicode(_Unicode, _Ordered):
    def __init__(self, *args, **kwargs):
        _Unicode.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class CUnicode(_CUnicode, _Ordered):
    def __init__(self, *args, **kwargs):
        _CUnicode.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class Bool(_Bool, _Ordered):
    def __init__(self, *args, **kwargs):
        _Bool.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class CBool(_CBool, _Ordered):
    def __init__(self, *args, **kwargs):
        _CBool.__init__(self, *args, **kwargs)
        _Ordered.__init__(self)


class List(_List, _Ordered):
    "Fixing default_value problem"
    def __init__(self, trait=None, default_value=[], minlen=0, maxlen=sys.maxsize, **kwargs):
        _List.__init__(self, trait=trait, default_value=default_value, minlen=minlen, maxlen=maxlen, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value


class RecursiveList(List):
    """A list trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    """
    # trait-specific json handler
    class jsonHandler(RecursiveListHandlerABC):
        klass = list
        recursion = True


class Set(_Set, _Ordered):
    "Fixing default_value problem"
    def __init__(self, trait=None, default_value=None, minlen=0, maxlen=sys.maxsize, **kwargs):
        _Set.__init__(self, trait=trait, default_value=default_value, minlen=minlen, maxlen=maxlen, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value


class RecursiveSet(Set):
    """A Set trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    """
    # trait-specific json handler
    class jsonHandler(RecursiveListHandlerABC):
        klass = set
        recursion = True


class Tuple(_Tuple, _Ordered):
    "Fixing default_value problem"
    def __init__(self, *traits, **kwargs):
        default_value = kwargs.setdefault('default_value', None)
        _Tuple.__init__(self, *traits, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value


class RecursiveTuple(Tuple):
    """A tuple trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    """
    # trait-specific json handler
    class jsonHandler(RecursiveListHandlerABC):
        klass = tuple
        recursion = True


class Dict(_Dict, _Ordered):
    "Fixing default_value problem"
    def __init__(self, trait=None, traits=None, default_value={}, **kwargs):
        _Dict.__init__(self, trait=trait, traits=traits, default_value=default_value, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value


class RecursiveDict(Dict):
    """A dict trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    Recursion is active by default, unless tagged with .tag(recursion=False)
    """
    # trait-specific json handler
    class jsonHandler(RecursiveDictHandlerABC):
        klass = dict


class Adict(TraitType, _Ordered):
    """A trait that defines a json serialisable AttributeDict; 
    dicts or (key,value) iterables are automatically cast into AttributeDict
    Recursion is not active
    """
    default_value = AttributeDict()
    info_text = "'an AttributeDict'"

    def __init__(self, default_value={}, allow_none=False, read_only=None, **kwargs):
        TraitType.__init__(self, default_value=default_value, allow_none=allow_none, read_only=read_only, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value

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
            self.error(obj, value)

    # trait-specific json handler
    class jsonHandler(RecursiveDictHandlerABC):
        klass = AttributeDict
        recursion = False
# end class


class RecursiveAdict(Adict):
    """A trait that defines a json serialisable AttributeDict;
    dicts or (key,value) iterables are automatically cast into AttributeDict
    Recursion is active
    """

    # trait-specific json handler
    class jsonHandler(RecursiveDictHandlerABC):
        klass = AttributeDict
        recursion = True
# end class


class Odict(TraitType, _Ordered):
    """A trait that defines a json serialisable OrderedDict;
    dicts are automatically cast into OrderedDict
    Recursion is not active
    """
    default_value = OrderedDict()
    info_text = "'an OrderedDict'"

    def __init__(self, default_value={}, allow_none=False, read_only=None, **kwargs):
        TraitType.__init__(self, default_value=default_value, allow_none=allow_none, read_only=read_only, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    def validate(self, obj, value):
        """Assure a OrderedDict instance
        """
        if isinstance(value, OrderedDict):
            return value
        elif isinstance(value, dict):
            return OrderedDict(list(value.items()))
        else:
            self.error(obj, value)

    # trait-specific json handler
    class jsonHandler(RecursiveDictHandlerABC):
        klass = OrderedDict
        recursion = False
# end class


class RecursiveOdict(Odict):
    """A trait that defines a json serialisable OrderedDict;
    dicts are automatically cast into OrderedDict
    Recursion is active
    """
    # trait-specific json handler
    class jsonHandler(RecursiveDictHandlerABC):
        klass = OrderedDict
        recursion = True
# end class


class Immutable(Any, _Ordered):
    info_text = 'an immutable object, intended to be used as constant'

    def __init__(self, value):
        TraitType.__init__(self, default_value=value, read_only=True)
        _Ordered.__init__(self)

    # trait-specific json handler
    class jsonHandler(TraitJsonHandlerBase):
        """Serialise Immutable to be json compatible.
        """
        # def encode(self, obj, trait): # inherits from base class
        #     return getattr(obj, trait)

        def decode(self, obj, trait, value):
            # force set value
            obj.setTraitValue(trait, value, force=True)
    # end class
#end class


class CPath(TraitType, _Ordered):
    """A trait that defines a casting Path object and is json serialisable
    """
    default_value = aPath('.')
    info_text = "'an Path object'"

    def __init__(self, default_value={}, allow_none=False, read_only=None, **kwargs):
        TraitType.__init__(self, default_value=default_value, allow_none=allow_none, read_only=read_only, **kwargs)
        _Ordered.__init__(self)
        if default_value is not None:
            self.default_value = default_value

    def validate(self, obj, value):
        """Assure a AttributeDict instance
        """
        if isinstance(value, Path):
            pass

        elif isinstance(value, pathlib.Path) or isinstance(value, str):
            value =  Path(value)

        else:
            self.error(obj, value)

        return value

    # trait-specific json handler
    class jsonHandler(TraitJsonHandlerBase):
        """Serialise Path to be json compatible.
        """
        def encode(self, obj, trait):
            # stores as a str for json
            return str(getattr(obj, trait))

        def decode(self, obj, trait, value):
            # needs conversion from str into Path
            setattr(obj, trait, Path(value))
    # end class
# end class

