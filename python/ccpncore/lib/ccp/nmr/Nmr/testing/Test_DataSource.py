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
from ccpncore.testing.CoreTesting import CoreTesting

class DataSourcePlaneDataTest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse1a'
    
  def Test_GetPlaneData(self, *args, **kw):
    spectrum = self.nmrProject.findFirstExperiment(name='HSQC').findFirstDataSource()
    planeData = spectrum.getPlaneData()
    print('planeData.shape =', planeData.shape)
    print('planeData =', planeData[508:,2045:])

class DataSourceSliceDataTest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse1a'
    
  def Test_GetSliceData(self, *args, **kw):
    spectrum = self.nmrProject.findFirstExperiment(name='HSQC').findFirstDataSource()
    # just check an arbitrary slice
    sliceData = spectrum.getSliceData(position=(1000, 230), sliceDim=1)
    print('sliceData.shape =', sliceData.shape)
    # check a small part of the returned data
    actualInd = 379
    actualData = [-75826.875, -135818.1563, -132515.0938, -76160.47656, 14403.3877, 119186.0625]
    sliceData = sliceData[actualInd:actualInd+len(actualData)]
    print('sliceData =', sliceData)
    diff = sum(abs(actualData-sliceData))
    assert diff < 0.001
