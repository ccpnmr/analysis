"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-09-09 18:38:58 +0100 (Wed, September 09, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
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
    ROWOBJECT = 'rowObject'

    _callbackwords = (CLICK, DOUBLECLICK, CURRENT)

    def __init__(self, theObject: Any = None,
                 object: Any = None,
                 index: int = None,
                 targetName: str = None,
                 trigger: list = None,
                 row: int = None,
                 col: int = None,
                 rowItem: dict = None,
                 rowObject : Any = None,
                 # callback: Callable[..., Optional[str]],
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
        _dict[self.ROWOBJECT] = rowObject
        self.update(_dict)
