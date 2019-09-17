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


import pathlib

from collections import OrderedDict
from traitlets import \
    Int, Long, Float, Complex, CInt, CFloat, CComplex, \
    Unicode, Bytes, CUnicode, CBytes, ObjectName, DottedObjectName, \
    Dict, List, Set, Tuple, \
    Instance, Type, This, ForwardDeclaredInstance, ForwardDeclaredType, ForwardDeclaredMixin, \
    Enum, Bool, CBool, CaselessStrEnum, TCPAddress, CRegExp, Any, \
    TraitType, default, validate, observe, Undefined, HasTraits

from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase, RecursiveDictHandlerABC, \
    RecursiveListHandlerABC
from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.Path import aPath, Path


class Immutable(Any):
    info_text = 'an immutable object, intended to be used as constant'

    def __init__(self, value):
        TraitType.__init__(self, default_value=value, read_only=True)

    # trait-specific json handler
    class jsonHandler(TraitJsonHandlerBase):
        """Serialise Immutable to be json compatible.
        """
        # def encode(self, obj, trait): # inherits from base class
        #     return getattr(obj, trait)

        def decode(self, obj, trait, value):
            # force set value
            obj.setTrait(trait, value, force=True)
    # end class
#end class


class RecursiveDict(Dict):
    """A dict trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    Recursion is active by default, unless tagged with .tag(recursion=False)
    """
    # trait-specific json handler
    class jsonHandler(RecursiveDictHandlerABC):
        klass = dict


class Adict(TraitType):
    """A trait that defines a json serialisable AttributeDict; 
    dicts or (key,value) iterables are automatically cast into AttributeDict
    Recursion is active by default, unless tagged with .tag(recursion=False)
    """
    default_value = AttributeDict()
    info_text = "'an AttributeDict'"

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
# end class


class Odict(TraitType):
    """A trait that defines a json serialisable OrderedDict;
    dicts are automatically cast into OrderedDict
    Recursion is active by default, unless tagged with .tag(recursion=False)
    """
    default_value = OrderedDict()
    info_text = "'an OrderedDict'"

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
# end class


class RecursiveList(List):
    """A list trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    Recursion is active by default, unless tagged with .tag(recursion=False)
    """
    # trait-specific json handler
    class jsonHandler(RecursiveListHandlerABC):
        klass = list


class RecursiveTuple(Tuple):
    """A tuple trait that implements recursion of any of the values that are a CcpNmrJson (sub)type
    Recursion is active by default, unless tagged with .tag(recursion=False)
    """
    # trait-specific json handler
    class jsonHandler(RecursiveListHandlerABC):
        klass = tuple


class CPath(TraitType):
    """A trait that defines a casting Path object and is json serialisable
    """
    default_value = aPath('.')
    info_text = "'an Path object'"

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

