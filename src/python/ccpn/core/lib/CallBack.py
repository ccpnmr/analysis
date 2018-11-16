"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from collections import OrderedDict
from typing import Callable, Any
from ccpn.framework.Current import Current
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

from ccpn.util.Logging import getLogger


logger = getLogger()


class CallBack(OrderedDict):
    # callback keywords
    CLICK = 'click'
    DOUBLECLICK = 'doubleclick'
    CURRENT = 'current'

    THEOBJECT = 'theObject'
    OBJECT = 'object'
    INDEX = 'index'
    TARGETNAME = 'targetName'
    TRIGGER = 'trigger'
    ROW = 'row'
    COL = 'col'
    ROWITEM = 'rowItem'

    _callbackwords = (CLICK, DOUBLECLICK, CURRENT)

    def __init__(self, theObject: Any = None,
                 object: Any = None,
                 index: int = None,
                 targetName: str = None,
                 trigger: list = None,
                 row: int = None,
                 col: int = None,
                 rowItem: dict = None,
                 # callback: Callable[..., str],
                 *args, **kwargs):
        """
        Create CallBack object
        an object for passing to the callback function
        """
        super(CallBack, self).__init__(*args, **kwargs)

        _dict = {}
        _dict[self.THEOBJECT] = theObject
        _dict[self.OBJECT] = object
        _dict[self.INDEX] = index
        _dict[self.TARGETNAME] = targetName
        _dict[self.TRIGGER] = trigger
        _dict[self.ROW] = row
        _dict[self.COL] = col
        _dict[self.ROWITEM] = rowItem
        self.update(_dict)
