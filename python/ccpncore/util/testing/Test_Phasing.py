"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
import numpy
import unittest

from ccpncore.util import Phasing

class PhasingTest(unittest.TestCase):
    
  def test_phasing_none(self):
    
    x = numpy.random.random(1000).astype('float32')
    y = Phasing.phaseRealData(x)
    
    delta = abs(y-x).max()
    
    assert delta < 1.0e-5, 'delta = %f' % delta

  def test_phasing_inverse_ph0(self):
    
    x = numpy.random.random(1000).astype('float32')
    y = Phasing.phaseRealData(x, ph0=130)
    z = Phasing.phaseRealData(y, ph0=-130)
    
    delta = abs(z-x).max()
    
    assert delta < 1.0e-5, 'delta = %f' % delta

  def test_phasing_inverse(self):
    
    x = numpy.random.random(1000).astype('float32') + 1j * numpy.random.random(1000).astype('float32')
    x = numpy.pad(x, pad_width=(0, len(x)), mode='constant') # zero pad once
    x = numpy.fft.fft(x)
    
    y = Phasing.phaseComplexData(x, ph0=140, ph1=300)
    z = Phasing.phaseComplexData(y, ph0=-140, ph1=-300)
    
    delta = abs(z-x).max()
    
    assert delta < 1.0e-5, 'delta = %f' % delta

