"""
WeakRefList; simple implementation for Notifiers (for now)
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
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
__dateModified__ = "$dateModified: 2024-06-18 21:07:38 +0100 (Tue, June 18, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2023-10-16 16:42:30 +0100 (Mon, October 16, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================
#
import sys
from typing import Callable, Any, Optional, List

from weakref import WeakValueDictionary


class _WeakRefList(object):
    """A class to act as a weakref list for Notifier instances
    """

    def __init__(self, items: list | tuple = ()):
        """Initlialise self, optionally with items
        """
        self.nextKey: int = 0
        self.weakRefDict = WeakValueDictionary()
        for item in items:
            self.append(item)

    @property
    def items(self) -> list:
        """:return a list of the items of self
        """
        return list(self.weakRefDict.values())

    def append(self, item):
        """Add a item instance to the list
        """
        self.weakRefDict[self.nextKey] = item
        self.nextKey += 1

    def pop(self):
        """pop and return the first item or None when list is empty
        """
        if len(self.weakRefDict) == 0:
            return None

        key = list(self.weakRefDict.keys())[0]
        _item = self.weakRefDict.pop(key)
        return _item

    def __len__(self):
        return len(self.weakRefDict)

    def __str__(self):
        return f'<WeakRefList: {len(self)}>'

    __repr__ = __str__
