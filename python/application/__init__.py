"""CCPN gui data. High level interface for normal data access

All classes in this module are subclasses of the :ref:`ccpn-AbstractWrapperObject-ref`

.. currentmodule:: ccpnmr


Class Hierarchy
^^^^^^^^^^^^^^^

Classes are organised in a hierarchy, with all data objects ultimately contained within the Project:

  Project

  ...

  |       Window
  |       Task
  |       |       Mark
  |       |       SpectrumDisplay
  |       |       |       Strip
  |       |       |       |       Axis
  |       |       |       |       SpectrumView
  |       |       |       |       |       PeakListView

"""

import importlib

# Following import statement to ensure wrapper classes correctly loaded
import ccpn

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported

# # Keep childClasses snapshot for later comparison
# _previousChildClasses = list(ccpn.Project._childClasses)

# _wrappedClassNames gives import order
_wrappedClasses = []
Window = cls = importlib.import_module('application._wrapper._Window').Window
_wrappedClasses.append(cls)
Task = cls = importlib.import_module('application._wrapper._Task').Task
_wrappedClasses.append(cls)
Mark = cls = importlib.import_module('application._wrapper._Mark').Mark
_wrappedClasses.append(cls)
SpectrumDisplay = cls = importlib.import_module(
  'application._wrapper._SpectrumDisplay').SpectrumDisplay
_wrappedClasses.append(cls)
Strip = cls = importlib.import_module('application._wrapper._Strip').Strip
_wrappedClasses.append(cls)
Axis = cls = importlib.import_module('application._wrapper._Axis').Axis
_wrappedClasses.append(cls)
SpectrumView = cls = importlib.import_module('application._wrapper._SpectrumView').SpectrumView
_wrappedClasses.append(cls)
PeakListView = cls = importlib.import_module('application._wrapper._PeakListView').PeakListView
_wrappedClasses.append(cls)
# PeakView = cls = importlib.import_module('ccpnmr._wrapper._PeakView').PeakView
# _wrappedClasses.append(cls)

# Add class list for extended sphinx documentation to module
_sphinxWrappedClasses = _wrappedClasses

# Make {shortClassName: className} map. NB may be added to by importing modules (ccpnmr wrapper)
for cls in _wrappedClasses:
  tag = cls.className if hasattr(cls, 'className') else cls.__class__.__name__
  ccpn._pluralPidTypeMap[cls.shortClassName] = tag + 's'

# Additional data
RulerData = importlib.import_module('application._wrapper._Mark').RulerData

# # Set up interclass links and related functions
ccpn.Project._linkWrapperClasses()
