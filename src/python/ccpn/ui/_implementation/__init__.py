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
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:03 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# CCPNINTERNAL used in ccpn.core.__init__

# Order to import ui implementation classes -
_uiImportOrder = ('Window','Task','Mark','SpectrumDisplay','Module','Strip',
                'Axis','SpectrumView', 'PeakListView')

# Necessary to ensure classes are always imported in the right order
from ccpn import core

