"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:20 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from operator import itemgetter
import numpy
from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting
# from ccpnmodel.ccpncore.lib.ccp.nmr.Nmr import DataSource
from ccpnc.peak import Peak


class PeakFitTest(CoreTesting):
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse1a'

    def Test_PeakFit(self, *args, **kwds):
        spectrum = self.nmrProject.findFirstExperiment(name='HSQC').findFirstDataSource()
        data = spectrum.getPlaneData()
        print('data.shape = %s' % (data.shape,))

        haveLow = 0
        haveHigh = 1
        low = 0  # arbitrary
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
