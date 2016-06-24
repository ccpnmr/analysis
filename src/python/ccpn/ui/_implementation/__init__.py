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

# CCPNINTERNAL used in ccpn.core.__init__

# Order to import ui implementation classes -
_importOrder = ['Window','Task','Mark','SpectrumDisplay','Module','Strip',
                'Axis','SpectrumView', 'PeakListView']

# Necessary to ensure classes are always imported in the right order
from ccpn import core

