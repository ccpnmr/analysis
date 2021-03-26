"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-26 12:43:48 +0000 (Fri, March 26, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-04-03 10:29:12 +0000 (Fri, April 03, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from enum import Enum


class LabelledEnum(Enum):
    """
    Class to handle enumerated types with associated labels

    e.g.
        FLOAT = 0, 'Float'
        INTEGER = 1, 'Integer'
        STRING = 2, 'String'
    """

    def __new__(cls, value, description, label=None):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._description_ = description
        # add optional extra information
        obj._label_ = label
        return obj

    def __str__(self):
        return str(self.value)

    # this makes sure that the description is read-only
    @property
    def description(self):
        return self._description_

    # this makes sure that the label is read-only
    @property
    def label(self):
        return self._label_

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
        members = [val for val in list(cls) if val.label == value]
        if members and len(members) == 1:
            return members[0]


if __name__ == '__main__':
    class Test(LabelledEnum):
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
