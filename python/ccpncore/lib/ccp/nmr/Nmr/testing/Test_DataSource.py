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
from ccpncore.util.Testing import Testing
from ccpncore.lib.ccp.nmr.Nmr import DataSource

class DataSourcePlaneDataTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)
    
  def Test_GetPlaneData(self, *args, **kw):
    spectrum = self.project.findFirstNmrProject().findFirstExperiment(name='HSQC').findFirstDataSource()
    planeData = DataSource.getPlaneData(spectrum)
    print('planeData.shape =', planeData.shape)
    print('planeData =', planeData[508:,2045:])

class DataSourceSliceDataTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)
    
  def Test_GetSliceData(self, *args, **kw):
    spectrum = self.project.findFirstNmrProject().findFirstExperiment(name='HSQC').findFirstDataSource()
    # just check an arbitrary slice
    sliceData = DataSource.getSliceData(spectrum, position=(1000, 230), sliceDim=1)
    print('sliceData.shape =', sliceData.shape)
    # check a small part of the returned data
    actualInd = 379
    actualData = [-75826.875, -135818.1563, -132515.0938, -76160.47656, 14403.3877, 119186.0625]
    sliceData = sliceData[actualInd:actualInd+len(actualData)]
    print('sliceData =', sliceData)
    diff = sum(abs(actualData-sliceData))
    assert diff < 0.001
