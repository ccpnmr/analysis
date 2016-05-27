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
import collections

_name2DataClass = collections.OrderedDict()

# Contained classes in order in which they must be hooked up
_name2DataClass['Window'] = importlib.import_module('ccpn.ui._implementation.Window').Window
_name2DataClass['Task'] = importlib.import_module('ccpn.ui._implementation.Task').Task
_name2DataClass['Mark'] = importlib.import_module('ccpn.ui._implementation.Mark').Mark
_name2DataClass['SpectrumDisplay'] = (
  importlib.import_module('ccpn.ui._implementation.SpectrumDisplay').SpectrumDisplay
)
_name2DataClass['Strip'] = importlib.import_module('ccpn.ui._implementation.Strip').Strip
_name2DataClass['Axis'] = importlib.import_module('ccpn.ui._implementation.Axis').Axis
_name2DataClass['SpectrumView'] = (
  importlib.import_module('ccpn.ui._implementation._SpectrumView').SpectrumView
)
_name2DataClass['PeakListView'] = (
  importlib.import_module('ccpn.ui._implementation._PeakListView').PeakListView
)

_importOrder = list(_name2DataClass.keys())
