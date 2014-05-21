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

  def Test_Get2DSliceData(self, *args, **kw):
    spectrum = self.project.findFirstNmrProject().findFirstExperiment(name='HSQC').findFirstDataSource()
    sliceData = DataSource.getSliceData(spectrum)
    print('sliceData.shape =', sliceData.shape)
    print('sliceData =', sliceData)
