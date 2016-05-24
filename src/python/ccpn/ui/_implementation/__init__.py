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




#
# import importlib
#
# # Following import statement to ensure wrapper classes correctly loaded
# from ccpn import core
# from ccpn.core.Project import Project

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported

# # Keep childClasses snapshot for later comparison
# _previousChildClasses = list(ccpn.Project._childClasses)

# Order in which classes are imported:
_importOrder = [
  'Window', 'Task', 'Mark', 'SpectrumDisplay', 'Strip', 'Axis', 'SpectrumView', 'PeakListView',
]

# File name map - to allow finding a file hiddej by prefixing underscore.
_class2file = {'SpectrumView':'_SpectrumView',
              'PeakListView':'_PeakListView',}

# def _activateClasses(importOrder=_importOrder, class2file=_class2file):
#   """Import classes in importOrder and connect them to other wrapper classes"""
#
#   wrappedClasses = []
#   for className in importOrder:
#     module = importlib.import_module('ccpn.ui.gui.core.%s'
#                                       % class2file.get(className, className))
#     module._connectWrapperClass()
#     wrappedClasses.append(getattr(module, className))
#
#   # # Add class list for extended sphinx documentation to module
#   # _sphinxWrappedClasses = _wrappedClasses
#
#   # Make {shortClassName: className} map. NB may be added to by importing modules (ccpnmr wrapper)
#   for cls in wrappedClasses:
#     tag = cls.className if hasattr(cls, 'className') else cls.__class__.__name__
#     _pluralPidTypeMap[cls.shortClassName] = _pluralPidTypeMap[className] = tag + 's'
#
#   # # Set up interclass links and related functions.
#   # NB classes already linked before are not linked again.
#   Project._linkWrapperClasses()
#
#   return wrappedClasses