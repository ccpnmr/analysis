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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-05-16 10:48:21 +0100 (Mon, May 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-04-03 10:29:12 +0000 (Fri, April 03, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from enum import Enum
from types import DynamicClassAttribute


class DataEnum(Enum):
    """
    Class to handle enumerated types with associated descriptions and dataValues

    e.g.
        # name, value, description and optional dataValue
        FLOAT = 0, 'Float', 'dataValue 1'
        INTEGER = 1, 'Integer', 'dataValue 1'
        STRING = 2, 'String', 'dataValue 1'
    """

    def __new__(cls, value, description=None, dataValue=None):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._description_ = description
        # add optional extra information
        obj._dataValue_ = dataValue
        return obj

    def __str__(self):
        return str(self.value)

    # ensure the dataValue is read-only
    @DynamicClassAttribute
    def dataValue(self):
        return self._dataValue_

    # ensure the description is read-only
    @DynamicClassAttribute
    def description(self):
        return self._description_

    def prev(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) - 1
        return members[index % len(members)]

    def next(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        return members[index % len(members)]

    def search(self, value):
        cls = self.__class__
        members = [val for val in list(cls) if val._dataValue_ == value]
        if members and len(members) == 1:
            return members[0]

    @classmethod
    def dataValues(cls):
        """Return a tuple of all dataValues
        """
        return tuple(v._dataValue_ for v in cls)

    @classmethod
    def descriptions(cls):
        """Return a tuple of all descriptions
        """
        return tuple(v._description_ for v in cls)

    @classmethod
    def names(cls):
        """Return a tuple of all names
        """
        return tuple(v._name_ for v in cls)

    @classmethod
    def values(cls):
        """Return a tuple of all values
        """
        return tuple(v._value_ for v in cls)

    @classmethod
    def get(cls, value):
        """Return the enumerated type from the name
        """
        try:
            return cls.__getitem__(value)
        except KeyError:
            raise ValueError(f'value must be one of {repr(cls.names())}')


def main():
    """A few small tests for the labelled Enum
    """


    class Test(DataEnum):
        FLOAT = 0, 'Float'
        INTEGER = 1, 'Integer'
        STRING = 2, 'String'


    test = Test(1)

    print(test)
    print(test.name)
    print(test.value)
    print(test.description)
    print(test.prev())
    print(test.next())
    print(1 in [v.value for v in Test])
    print('Integer' in [v.description for v in Test])
    print(Test(1))


if __name__ == '__main__':
    # call the testing method
    main()
