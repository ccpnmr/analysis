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


class CallBack(object):
  """
  CallBack class:

  CallBack returns a callback dictionary with keywords based on the action type
  """
  _currentIndex = 0

  # callback keywords
  CLICK = 'click'
  DOUBLECLICK = 'doubleclick'
  CURRENT = 'current'

  CALLBACK = 'callback'
  THEOBJECT = 'theObject'
  TRIGGER = 'trigger'
  OBJECT = 'object'
  GETPID = 'pid'

  _callbackwords = (CLICK, DOUBLECLICK, CURRENT)

  def __init__(self, theObject: Any
               , triggers: list
               , targetName: str
               , callback: Callable[..., str]
               , onceOnly=False
               , *args, **kwargs):
    """
    Create CallBack object;
    """
    pass


