"""CCPN gui data. High level interface for normal data access

All classes in this module are subclasses of the :ref:`ccpn-AbstractWrapperObject-ref`

.. currentmodule:: ccpnmr

"""

import importlib

# Following import statement to ensure wrapper classes correctly loaded
import ccpn

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported

# Keep chilcClasses shapshot for later comparison
_previousChildClasses = list(ccpn.Project._childClasses)

# _wrappedClassNames gives import order
_wrappedClasses = []
Window = cls = importlib.import_module('ccpnmr._wrapper._Window').Window
_wrappedClasses.append(cls)
Task = cls = importlib.import_module('ccpnmr._wrapper._Task').Task
_wrappedClasses.append(cls)
SpectrumDisplay = cls = importlib.import_module('ccpnmr._wrapper._SpectrumDisplay').SpectrumDisplay
_wrappedClasses.append(cls)
Axis = cls = importlib.import_module('ccpnmr._wrapper._Axis').Axis
_wrappedClasses.append(cls)
Strip = cls = importlib.import_module('ccpnmr._wrapper._Strip').Strip
_wrappedClasses.append(cls)
SpectrumView = cls = importlib.import_module('ccpnmr._wrapper._SpectrumView').SpectrumView
_wrappedClasses.append(cls)
PeakListView = cls = importlib.import_module('ccpnmr._wrapper._PeakListView').PeakListView
_wrappedClasses.append(cls)
PeakView = cls = importlib.import_module('ccpnmr._wrapper._PeakView').PeakView
_wrappedClasses.append(cls)

# Add class list for extended sphinx documentation to module
_sphinxWrappedClasses = _wrappedClasses


# Set up interclass links and related functions
# HACK to link up newly imported wrapper classes only
_childClasses = ccpn.Project._childClasses
ccpn.Project._childClasses = [x for x in _childClasses if x not in _previousChildClasses]
ccpn.Project._linkWrapperClasses()
ccpn.Project._childClasses = _childClasses