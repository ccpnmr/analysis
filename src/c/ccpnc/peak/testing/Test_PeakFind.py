"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from operator import itemgetter

from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting

from ccpnc.peak import Peak

class PeakFindTest(CoreTesting):

  # Path of project to load (None for new project
  projectPath = 'CcpnCourse1a'

  def Test_PeakFind(self, *args, **kw):
    spectrum = self.nmrProject.findFirstExperiment(name='HSQC').findFirstDataSource()
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
    print('number of peaks = %d' % len(peakPoints))
    assert len(peakPoints) == 4

    peakPoints.sort(key=itemgetter(1), reverse=True)
    
    for (position, height) in peakPoints:
      print(position, height)

    height = peakPoints[0][1]
    assert abs(height-149625408) < 0.1
