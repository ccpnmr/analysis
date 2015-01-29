"""CCPN gui data. High level interface for normal data access


.. currentmodule:: ccpnmr

.. autosummary::

   _GuiWindow.GuiWindow
   _GuiTask.GuiTask

ccpnmr.GuiWindow class
------------------

.. autoclass:: ccpn._wrapper._GuiWindow.GuiWindow

ccpnmr.GuiTask class
------------------

.. autoclass:: ccpn._wrapper._GuiTask.GuiTask
"""

# import sys
# print ('sys.path=', sys.path)
# for key in sorted(sys.modules):
#   print(' - ', key)

# Following import statement to ensure wrapper classes correctly loaded
import ccpn

# from ccpncore.util import Io as ioUtil

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported

# from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
previousChildClasses = list(Project._childClasses)

from ccpnmr._wrapper._GuiWindow import GuiWindow
from ccpnmr._wrapper._GuiTask import GuiTask

# Set up interclass links and related functions
# HACK to link up newly imported wrapper classes only
childClasses = Project._childClasses
Project._childClasses = [x for x in childClasses if x not in previousChildClasses]
Project._linkWrapperClasses()
Project._childClasses = childClasses