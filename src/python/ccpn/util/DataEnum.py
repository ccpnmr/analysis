"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2025-10-15 18:13:30 +0100 (Wed, October 15, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-04-03 10:29:12 +0000 (Fri, April 03, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from enum import Enum, IntEnum
from types import DynamicClassAttribute
from typing import Any, TypeVar, Generic, Callable
from typing_extensions import Self  # noqa
import operator


_T = TypeVar("_T")  # Individual Type for property
# A uniform signature for our constructors: (cls, value) -> instance
_CT = Callable[[type, Any], object]
_reject_bool_for_int = True


class _TypeDynamicClassAttribute(DynamicClassAttribute, Generic[_T]):
    """A subclass of DynamicClassAttribute with type-annotations."""
    ...

    def __get__(self, __instance: Any, __owner: type | None = None) -> _T:
        """Get the value or dataValue from the class or instance, enforcing type constraints."""
        # Return the actual value from the class/instance
        return super().__get__(__instance, __owner)


class _DataEnumMixin(Enum):
    """Class to handle enumerated types with associated descriptions and dataValues.

    *example:*
    ::
        class MyTest(DataEnum):
            # name = value, optional description and optional dataValue
            FLOAT = 0, 'Float', <dataValue 1>
            INTEGER = 1, 'Integer', <dataValue 2>
            STRING = 2, 'String', <dataValue 3>
    """
    _description_: str | None
    _dataValue_: Any

    def __new__(cls, value: Any, description: str | None = None, dataValue: Any = None) -> Self:
        """
        Create a new instance of an enum member.

        :param value: The value of the enum member.
        :type value: Any
        :param description: An optional description for the enum member.
        :type description: str | None
        :param dataValue: An optional data-value for the enum member.
        :type dataValue: Any
        :return: A new instance of the enum member.
        :rtype: Self
        :raises TypeError: If the value type is inconsistent with existing members.
        """
        obj = cls._new_object(value)
        obj._value_ = value
        # Runtime check for consistent value types among enum members
        if (first_member := next(iter(cls.__members__.values()), None)) is not None and \
                not isinstance(value, (expected_type := type(first_member._value_))):  # type: ignore[attr-defined]
            raise TypeError(f"All values in {cls.__name__} must be of type {expected_type.__name__}")
        # add optional extra information
        obj._description_ = description
        obj._dataValue_ = dataValue
        return obj

    @classmethod
    def _new_object(cls, _value) -> Any:
        return object.__new__(cls)

    def __repr__(self) -> str:
        """
        Return the string representation of the enum member.

        If the dataValue is not None, include it in the representation.

        :return: The string representation of the enum member.
        :rtype: str
        """
        if self._dataValue_ is not None:
            # Include dataValue if it exists.
            return f"<{self.__class__.__name__}.{self._name_}: {self._value_!r}, {self._dataValue_!r}>"
        return f"<{self.__class__.__name__}.{self._name_}: {self._value_!r}>"

    # @DynamicClassAttribute
    # def value(self) -> Any:
    #     """Return the primary value of the enum member."""
    #     return super().value

    @DynamicClassAttribute
    def dataValue(self) -> Any:
        """Return the dataValue associated with the enum member."""
        return self._dataValue_

    @DynamicClassAttribute
    def description(self) -> str | None:
        """Return the description of the enum member."""
        return self._description_

    def prev(self) -> Self:
        """Return the previous member in the enumeration order."""
        members = list(type(self))
        index = (members.index(self) - 1) % len(members)
        return members[index]

    def next(self) -> Self:
        """Return the next member in the enumeration order."""
        members = list(type(self))
        index = (members.index(self) + 1) % len(members)
        return members[index]

    @classmethod
    def getByDataValue(cls, value: Any) -> Self | tuple[Self, ...] | None:
        """
        Search for member(s) by dataValue.

        Search the members for a matching dataValue. Return a single member if only one
        found, or a list for multiple members; otherwise, return None.
        :param str value: search parameter.
        :return: found member(s) or None.
        :rtype: Self | tuple[Self, ...] | None
        """
        members = tuple(mb for mb in cls if mb._dataValue_ == value)
        if not members:
            return None
        return members[0] if len(members) == 1 else members

    @classmethod
    def getByDescription(cls, value: str | None) -> Self | tuple[Self, ...] | None:
        """
        Search for a member(s) by description.

        Search the members for a matching description. Return a single member if only one
        found, or a list for multiple members; otherwise, return None.
        :param str value: search parameter.
        :return: found member(s) or None.
        :rtype: Self | tuple[Self, ...] | None
        """
        members = tuple(mb for mb in cls if mb._description_ == value)
        if not members:
            return None
        return members[0] if len(members) == 1 else members

    @classmethod
    def dataValues(cls) -> tuple[Any, ...] | None:
        """
        Return a tuple of all dataValues, or None if no dataValues are defined for any members.

        :return: Tuple of all dataValues or None if no dataValues are defined.
        :rtype: tuple[Any, ...] | None
        """
        result = tuple(mb._dataValue_ for mb in cls)
        return result if any(mb is not None for mb in result) else None

    @classmethod
    def descriptions(cls) -> tuple[str | None, ...] | None:
        """
        Return a tuple of all descriptions, or None if no descriptions are defined for any members.

        :return: Tuple of all descriptions or None if no descriptions are defined.
        :rtype: tuple[str | None, ...] | None
        """
        result = tuple(mb._description_ for mb in cls)
        return result if any(mb is not None for mb in result) else None

    @classmethod
    def names(cls) -> tuple[str, ...]:
        """
        Return a tuple of all names.

        :return: Tuple of all names.
        :rtype: tuple[str, ...]
        """
        return tuple(mb._name_ for mb in cls)

    @classmethod
    def values(cls) -> tuple[Any, ...]:
        """
        Return a tuple of all values.

        :return: Tuple of all values.
        :rtype: tuple[Any, ...]
        """
        return tuple(mb._value_ for mb in cls)

    @classmethod
    def get(cls, value: str, default: Any = Ellipsis) -> Self:
        """
        Return the enum member from its name.

        :param value: The name of the enum member to retrieve.
        :type value: str
        :param default: An optional default value to return if the name is not found.
        :type value: Any
        :return: The enum member corresponding to the given name.
        :rtype: Self
        :raises ValueError: If the name is not found and no default is provided.
        """
        try:
            return cls[value]
        except KeyError:
            if default is Ellipsis:
                raise ValueError(f'{value!r} is not a valid {cls.__name__}')
            return default


#=========================================================================================

class DataIntEnum(_DataEnumMixin, IntEnum):

    @classmethod
    def _new_object(cls, value) -> int:
        if _reject_bool_for_int and type(value) is bool:
            raise TypeError(f"{cls.__name__} values must be int (bool not allowed)")
        try:
            iValue = operator.index(value)  # accepts numpy.int*, etc.
        except Exception as exc:
            raise TypeError(f"{cls.__name__} values must be int-like") from exc
        return int.__new__(cls, iValue)


class DataEnum(_DataEnumMixin, Enum):  # fallback; value is Any
    pass


#=========================================================================================

def main():
    """
    A few small tests for the DataEnum class.
    """


    class Test_mixed(DataIntEnum):
        FLOAT = 0, None, 'Float'
        INTEGER = 1, None, 'Integer'
        STRING = 2, 'Some type of string', 'String'
        OTHER = 3, None, 'Integer'


    ll = Test_mixed.dataValues()
    print(ll)
    test = Test_mixed(2)
    print(test)
    print(test.name)
    print(test.value)
    print(test.description)
    print(test.description and test.description.startswith('Some'))
    print(test.prev())
    print(test.next())
    print(test.next().next())
    print(1 in [v.value for v in Test_mixed])
    print('Integer' in [v.description for v in Test_mixed])
    print(Test_mixed(1))
    print(Test_mixed.STRING)
    print(Test_mixed.dataValues() is None)
    print(Test_mixed.get('FLOAT'))
    print(Test_mixed.getByDescription(None))
    print(ll[Test_mixed.get('STRING').value])  # type: ignore[index]
    try:
        print(int(Test_mixed.get('OTHER').dataValue))  # type: ignore[index]
    except ValueError:
        ...
    try:
        print(ll[Test_mixed.get('STRING').dataValue])  # type: ignore[index]
    except TypeError:
        ...
    try:
        print(ll[Test_mixed.get('MISSING').dataValue])  # type: ignore[index]
    except ValueError:
        ...
    try:
        print(Test_mixed.value)
    except AttributeError:
        ...


    #-----------------------------------------------------------------------------------------

    class Test_OK(DataIntEnum):
        FLOAT = 0, 'Some type of float', 'Float'
        INTEGER = 1, 'Some type of integer', 'Integer'
        STRING = 2, 'Some type of string', 'String'
        OTHER = 3, 'Another integer type', 'Integer'


    print(f"All data values: {Test_OK.dataValues()}")

    #-----------------------------------------------------------------------------------------
    # Accessing an enum member and its attributes
    test_member = Test_OK.STRING
    print(f"\nTesting member: {test_member}")
    print(f"Name: {test_member.name}")
    print(f"Value: {test_member.value}")
    print(f"Description: {test_member.description}")
    print(f"Data value: {test_member.dataValue}")

    #-----------------------------------------------------------------------------------------
    # Navigation
    print(f"\nMember before {test_member.name}: {test_member.prev()}")
    print(f"Member after {test_member.name}: {test_member.next()}")
    print(f"Two members after: {test_member.next().next()}")

    #-----------------------------------------------------------------------------------------
    # Membership testing
    print(f"\nIs 1 a value in Test_OK? {1 in Test_OK.values()}")
    print(f"Is 'Some type of integer' a description? {'Some type of integer' in Test_OK.descriptions()}")  # type: ignore[operator]

    #-----------------------------------------------------------------------------------------
    # Lookups
    print(f"\nLookup by value 1: {Test_OK(1)}")
    print(f"Lookup by name 'FLOAT': {Test_OK.get('FLOAT')}")
    print(f"Search for dataValue 'Integer': {Test_OK.getByDataValue('Integer')}")
    print(f"Search for description 'Some type of float': {Test_OK.getByDescription('Some type of float')}")

    #-----------------------------------------------------------------------------------------
    # Error handling
    try:
        Test_OK.get('INVALID_NAME')
    except ValueError as e:
        print(f"\nSuccessfully caught error: {e}")

    try:
        class Test_float(DataIntEnum):  # noqa
            FLOAT = 0.0, 'Some type of float', 'Float'
            INTEGER = 1.0, 'Some type of integer', 'Integer'
    except TypeError as e:
        print(f"\nSuccessfully caught error: {e}")

    try:
        class Test_mismatch_float(DataEnum):  # noqa
            FLOAT = 0.0, 'Some type of float', 'Float'
            INTEGER = 1, 'Some type of integer', 'Integer'
    except TypeError as e:
        print(f"\nSuccessfully caught error: {e}")

    try:
        class Test_mismatch_int(DataEnum):  # noqa
            FLOAT = 0, 'Some type of float', 'Float'
            INTEGER = 'one', 'Some type of integer', 'Integer'
    except TypeError as e:
        print(f"\nSuccessfully caught error: {e}")

    try:
        class Test_mismatch_bool(DataIntEnum):  # noqa
            FLOAT = False, 'Some type of float', 'Float'
            INTEGER = True, 'Some type of integer', 'Integer'
    except TypeError as e:
        print(f"\nSuccessfully caught error: {e}")


if __name__ == '__main__':
    # call the testing method
    main()
