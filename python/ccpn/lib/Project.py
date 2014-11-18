"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import collections

from ccpncore.lib.memops.Implementation import MemopsRoot

def loadSpectrum(project:object, filePath:str, reReadSpectrum:object=None):

  if reReadSpectrum is not None:
    # NBNB TBD Rasmus - this is clearly not working yet
    raise NotImplementedError("reReadSpectrum parameter not implemented yet")

  if reReadSpectrum:
    spectrum = reReadSpectrum
    # NBNB TBD BROKEN - spectrum is overwritten lower down
  else:
    dataSource = MemopsRoot.loadDataSource(project.nmrProject, filePath)
    if not dataSource:
      return None
  
  # NBNB TBD BROKEN - dataSource is not always set.
  spectrum = project._data2Obj[dataSource]

  return spectrum
  
