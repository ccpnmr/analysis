"""CCPN gui data. High level interface for normal data access


.. currentmodule:: ccpnmr

.. autosummary::

   _Window.Window
   _Task.Task
   _SpectrumDisplay.SpectrumDisplay
   _Strip.Strip
   _Axis.Axis
   _SpectrumView.SpectrumView

ccpnmr.Window class
------------------

.. autoclass:: ccpn._wrapper._Window.Window

ccpnmr.Task class
------------------

.. autoclass:: ccpn._wrapper._Task.Task

ccpnmr.SpectrumDisplay class
------------------

.. autoclass:: ccpn._wrapper._SpectrumDisplay.SpectrumDisplay

ccpnmr.Strip class
------------------

.. autoclass:: ccpn._wrapper._Strip.Strip

ccpnmr.Axis class
------------------

.. autoclass:: ccpn._wrapper._Axis.Axis

ccpnmr.SpectrumView class
------------------

.. autoclass:: ccpn._wrapper._SpectrumView.SpectrumView

"""

# import sys
# print ('sys.path=', sys.path)
# for key in sorted(sys.modules):
#   print(' - ', key)

# Following import statement to ensure wrapper classes correctly loaded
import ccpn

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported

# from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
previousChildClasses = list(Project._childClasses)

from ccpnmr._wrapper._Window import Window
from ccpnmr._wrapper._Task import Task
from ccpnmr._wrapper._SpectrumDisplay import SpectrumDisplay
from ccpnmr._wrapper._Axis import Axis
from ccpnmr._wrapper._SpectrumView import SpectrumView
from ccpnmr._wrapper._Strip import Strip

# Set up interclass links and related functions
# HACK to link up newly imported wrapper classes only
childClasses = Project._childClasses
Project._childClasses = [x for x in childClasses if x not in previousChildClasses]
Project._linkWrapperClasses()
Project._childClasses = childClasses