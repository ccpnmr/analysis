"""External functions for incorporatoin in NmrProject

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license
               "or ccpncore.memops.Credits.CcpnLicense for license text"
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpncore.util.Classes import NmrAtom



class LinkedNmrAtom(NmrAtom):
  """Add here functions to extract data related to NmrAtom"""

  _nmrProject = None

  # NBNB TBD add functions to extract information from NmrAtom data and _nmrProject link

def makeNmrAtom(nmrProject, *args, **kwargs):
  """get NmrAtom linked to NmrProject"""

  result = LinkedNmrAtom(*args, **kwargs)
  result._nmrProject = nmrProject
  #
  return result
