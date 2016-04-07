"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
__version__ = "$Revision: 8180 $"

#=========================================================================================
# Start of code
#=========================================================================================
import numpy
from scipy import signal

from typing import Sequence

def phaseRealData(data:Sequence, ph0:float=0.0, ph1:float=0.0, pivot:float=1.0) -> Sequence:
  # data is the (1D) spectrum data (real)
  # ph0 and ph1 are in degrees
  
  data = numpy.array(data)
  data = signal.hilbert(data) # convert real to complex data in best way possible
  data = phaseComplexData(data, ph0, ph1, pivot)
  data = data.real
  
  return data
  
def phaseComplexData(data:Sequence, ph0:float=0.0, ph1:float=0.0, pivot:float=1.0) -> Sequence:
  # data is the (1D) spectrum data (complex)
  # ph0 and ph1 are in degrees
  
  data = numpy.array(data)
  
  ph0 *= numpy.pi / 180.0
  ph1 *= numpy.pi / 180.0
  pivot -= 1 # points start at 1 but code below assumes starts at 0
 
  npts = len(data)
  angles = ph0 + (numpy.arange(npts) - pivot) * ph1 / npts
  multipliers = numpy.exp(-1j * angles)
  
  data *= multipliers
  
  return data
  
  
