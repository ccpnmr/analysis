"""Peak-related functions and utiliities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
import collections

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-11-23 16:12:43 +0000 (Wed, 23 Nov 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-11-23 16:12:43 +0000 (Wed, 23 Nov 2016) $"
__version__ = "$Revision: 10012 $"

#=========================================================================================
# Start of code
#=========================================================================================

# import typing
from typing import Sequence
from ccpn.core.Peak import Peak

def refitPeaks(peaks:Sequence[Peak], method:str='gaussian'):

  from ccpnmodel.ccpncore.lib.spectrum import Peak as LibPeak
  LibPeak.fitExistingPeaks([peak._wrappedData for peak in peaks], method)
