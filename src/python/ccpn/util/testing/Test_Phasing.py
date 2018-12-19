"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:02 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy
import unittest

from ccpn.util import Phasing


class PhasingTest(unittest.TestCase):

    def test_phasing_none(self):
        x = numpy.random.random(1000).astype('float32')
        y = Phasing.phaseRealData(x)

        delta = abs(y - x).max()

        assert delta < 1.0e-5, 'delta = %f' % delta

    #def test_phasing_inverse_ph0(self):
    #  does not work, real data does not have inverse like this

    #  x = numpy.random.random(1000).astype('float32')
    #  y = Phasing.phaseRealData(x, ph0=130)
    #  z = Phasing.phaseRealData(y, ph0=-130)

    #  delta = abs(z-x).max()

    #  assert delta < 1.0e-5, 'delta = %f' % delta

    def test_phasing_inverse(self):
        x = numpy.random.random(1000).astype('float32') + 1j * numpy.random.random(1000).astype('float32')
        x = numpy.pad(x, pad_width=(0, len(x)), mode='constant')  # zero pad once
        x = numpy.fft.fft(x)

        y = Phasing.phaseComplexData(x, ph0=140, ph1=300)
        z = Phasing.phaseComplexData(y, ph0=-140, ph1=-300)

        delta = abs(z - x).max()

        assert delta < 1.0e-5, 'delta = %f' % delta
