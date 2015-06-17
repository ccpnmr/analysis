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
from operator import itemgetter
import numpy

from ccpncore.testing.Testing import Testing
# from ccpncore.lib.ccp.nmr.Nmr import DataSource

from ccpnc.peak import Peak

class PeakFitTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)

  def Test_PeakFit(self, *args, **kw):
    spectrum = self.project.findFirstNmrProject().findFirstExperiment(name='HSQC').findFirstDataSource()
    data = spectrum.getPlaneData()
    print('data.shape = %s' % (data.shape,))

    haveLow = 0
    haveHigh = 1
    low = 0 # arbitrary
    high = 1.0e8
    buffer = [1, 1]
    nonadjacent = 0
    dropFactor = 0.0
    minLinewidth = [0.0, 0.0]

    peakPoints = Peak.findPeaks(data, haveLow, haveHigh, low, high, buffer, nonadjacent, dropFactor, minLinewidth)
    print('number of peaks found = %d' % len(peakPoints))

    peakPoints.sort(key=itemgetter(1), reverse=True)

    position, height = peakPoints[0]
    print('position of highest peak = %s, height = %s' % (position, height))

    numDim = len(position)
    peakArray = numpy.array(position, dtype='float32')
    firstArray = peakArray - 2
    lastArray = peakArray + 3
    peakArray = peakArray.reshape((1, numDim))
    firstArray = firstArray.astype('int32')
    lastArray = lastArray.astype('int32')
    regionArray = numpy.array((firstArray, lastArray))

    method = 0  # Gaussian
    result = Peak.fitPeaks(data, regionArray, peakArray, method)
    intensity, center, linewidth = result[0]
    print('Gaussian fit: intensity = %s, center = %s, linewidth = %s' % (intensity, center, linewidth))

    method = 1  # Lorentzian
    result = Peak.fitPeaks(data, regionArray, peakArray, method)
    intensity, center, linewidth = result[0]
    print('Lorentzian fit: intensity = %s, center = %s, linewidth = %s' % (intensity, center, linewidth))

