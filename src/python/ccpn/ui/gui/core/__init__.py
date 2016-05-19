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
#=======
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================





import importlib

# Following import statement to ensure wrapper classes correctly loaded
from ccpn import core
from ccpn.core.Project import Project
from ccpn.core import _pluralPidTypeMap

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported

# # Keep childClasses snapshot for later comparison
# _previousChildClasses = list(ccpn.Project._childClasses)

# Order in which classes are imported:
_importOrder = [
  'Window', 'Task', 'Mark', 'SpectrumDisplay', 'Strip', 'Axis', 'SpectrumView', 'PeakListView',
]
_wrappedClasses = []
for className in _importOrder:
  _wrappedClasses.append(
    getattr(importlib.import_module('ccpn.ui.gui.core.%s' % className), className)
  )
#
# # Add class list for extended sphinx documentation to module
# _sphinxWrappedClasses = _wrappedClasses

# Make {shortClassName: className} map. NB may be added to by importing modules (ccpnmr wrapper)
for cls in _wrappedClasses:
  tag = cls.className if hasattr(cls, 'className') else cls.__class__.__name__
  _pluralPidTypeMap[cls.shortClassName] = _pluralPidTypeMap[className] = tag + 's'
del cls
del tag

# # Set up interclass links and related functions
Project._linkWrapperClasses()