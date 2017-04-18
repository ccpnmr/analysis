"""Peak-related functions and utiliities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
import collections

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:34 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"

__date__ = "$Date: 2016-11-23 16:12:43 +0000 (Wed, 23 Nov 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import typing
from typing import Sequence
from ccpn.core.Peak import Peak

def refitPeaks(peaks:Sequence[Peak], method:str='gaussian'):

  from ccpnmodel.ccpncore.lib.spectrum import Peak as LibPeak
  LibPeak.fitExistingPeaks([peak._wrappedData for peak in peaks], method)
