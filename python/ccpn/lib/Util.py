"""CCPN-level utility code independent of model content

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
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

from ccpncore.util import Pid
from ccpn import _pluralPidTypeMap as pluralPidTypeMap

def pid2PluralName(pid:str) -> str:
  """Get plural class name, (e.g. 'Peaks', 'Spectra' from short-form or long-form, Pid string
  Unrecognised strings are returned unchanged"""
  tag = pid.split(Pid.PREFIXSEP, 1)[0]
  return pluralPidTypeMap.get(tag, tag)
