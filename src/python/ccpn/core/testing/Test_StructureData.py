"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

import math
from ccpn.util import StructureData
from ccpn.core.testing.WrapperTesting import WrapperTesting

nan = math.nan

class TestPandasData(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_float_column_1(self):
    ensemble = self.project.newStructureEnsemble()
    data = ensemble.data
    data['x'] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    data['y'] = 11
    data['z'] = None
    ll = [1,2.0,'4', '5.0', None, 'NaN']
    ll2 = StructureData.fitToDataType(ll, float, force=True)
    data.bFactor = ll2
    self.assertEquals(list(data.index), [1,2,3,4,5,6])
    self.assertEquals(list(data['x']),  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    self.assertEquals(list(data['y']),  [11]*6)
    self.assertTrue(all(math.isnan(x) for x in data['z']))
    self.assertEquals(list(data.bFactor)[:4],  [1, 2,4,5])
    self.assertTrue(all(math.isnan(x) for x in data['bFactor'][-2:]))
    self.assertRaises(ValueError, data.__setitem__, 'bFactor', ll)


  def test_occupancy(self):
    ensemble = self.project.newStructureEnsemble()
    data = ensemble.data
    data['occupancy'] = (0,0,0.1,0.99,1,1)
    self.assertRaises(ValueError, setattr, data, 'occupancy',  (0,0,-0.1,0.99,1,1))
    self.assertRaises(ValueError, setattr, data, 'occupancy',  (0,0,0.1,0.99,1,1.1))

  def test_sorting(self):
    print('\n\n START sorttest\n')
    ensemble = self.project.newStructureEnsemble()
    data = ensemble.data
    data['x'] = [2,2,2,2,1,1,1,1] * 2
    data['y'] = [2,1,2,1,2,1,2,1] * 2
    data['z'] = None
    data['modelNumber'] = [2,2,2,2,1,1,1,1] * 2
    data['chainCode'] = ['B','B','A','A','B','B','A','A'] * 2
    data['sequenceId'] = [2,1,2,1,2,1,2,1] * 2
    data['atomName'] = ['HG12'] * 8 + ['HG2'] * 8
    data['nmrAtomName'] = data['atomName']
    data['nmrChainCode'] = ['@12', '@12', '@2', '@2', '#12', '#12', '#2', '#2'] * 2
    data['nmrSequenceCode'] = ['12', '2b'] * 8
    data.setValues(17)
    self.assertEquals(list(data.loc[17])[3:],  [None] * 7)
    self.assertTrue(all(math.isnan(x) for x in data.loc[17][:3]))
    data.addRow()
    self.assertEquals(list(data.loc[18])[3:],  [None] * 7)
    self.assertTrue(all(math.isnan(x) for x in data.loc[18][:3]))

    data['origIndex'] = range(1, data.shape[0] + 1)

    self.assertRaises(ValueError, data.setValues, 110)
    self.assertRaises(ValueError, data.setValues, -1)
    self.assertRaises(ValueError, data.setValues, 0)

    ll = ['modelNumber', 'chainCode', 'sequenceId']
    data.ccpnSort(*ll)
    self.assertEquals(list(data['modelNumber'])[2:], ([1] * 8 + [2] * 8))
    self.assertEquals(list(data['chainCode'])[2:], (['A'] * 4 + ['B'] * 4) * 2)
    self.assertEquals(list(data['sequenceId'])[2:], ([1,1,2,2] *4))
    self.assertEquals(list(data['atomName'])[2:], (['HG12', 'HG2'] *8))
    self.assertEquals(list(data['origIndex']),
                      [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    data.sort_values('origIndex', inplace=True)
    data.index = data['origIndex']

    ll = ['modelNumber', 'chainCode', 'sequenceId', 'atomName']
    data.ccpnSort(*ll)
    self.assertEquals(list(data['origIndex']),
                      [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    data.sort_values('origIndex', inplace=True)
    data.index = data['origIndex']

    ll = ['x', 'y', 'z']
    data.ccpnSort(*ll)
    self.assertEquals(list(data['origIndex']),
                      [17, 18, 6, 8, 14, 16, 5, 7, 13, 15, 2, 4, 10, 12, 1, 3, 9, 11])
    data.sort_values('origIndex', inplace=True)
    data.index = data['origIndex']

    ll = ['nmrChainCode', 'nmrSequenceCode']
    data.ccpnSort(*ll)
    self.assertEquals(list(data['origIndex']),
                      [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    data.sort_values('origIndex', inplace=True)
    data.index = data['origIndex']

    ll = ['nmrChainCode', 'nmrSequenceCode', 'nmrAtomName']
    data.ccpnSort(*ll)
    self.assertEquals(list(data['origIndex']),
                      [17, 18, 16, 8, 15, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1])
    data.sort_values('origIndex', inplace=True)
    data.index = data['origIndex']

    data.drop(7, inplace=True)
    data.setValues(5,chainCode='B', sequenceId=-1, x=0.999)
    data.setValues(10,chainCode='B', sequenceId=-1, x=0.999)
    ll = ['modelNumber', 'chainCode', 'sequenceId', 'atomName']
    data.ccpnSort(*ll)
    self.assertEquals(list(data['origIndex']),
                      [17, 18, 8, 16, 15, 5, 6, 14, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    data.setValues(1, x=1.0, y=1.0)
    data.setValues(2, x=1.0, y=1.0)
    data.drop('z', axis=1, inplace=True)
    namedTuples = data.as_namedtuples()
    AtomRecord = namedTuples[0].__class__
    self.assertEquals(namedTuples, (
      AtomRecord(Index=1, x=1.0, y=1.0, modelNumber=None, chainCode=None, sequenceId=None,
                 atomName=None, nmrAtomName=None, nmrChainCode=None, nmrSequenceCode=None,
                 origIndex=17),
      AtomRecord(Index=2, x=1.0, y=1.0, modelNumber=None, chainCode=None, sequenceId=None,
                 atomName=None, nmrAtomName=None, nmrChainCode=None, nmrSequenceCode=None,
                 origIndex=18),
      AtomRecord(Index=3, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='#2', nmrSequenceCode='2b',
                 origIndex=8),
      AtomRecord(Index=4, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='#2', nmrSequenceCode='2b',
                 origIndex=16),
      AtomRecord(Index=5, x=1.0, y=2.0, modelNumber=1, chainCode='A', sequenceId=2,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='#2', nmrSequenceCode='12',
                 origIndex=15),
      AtomRecord(Index=6, x=0.999, y=2.0, modelNumber=1, chainCode='B', sequenceId=-1,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='#12', nmrSequenceCode='12',
                 origIndex=5),
      AtomRecord(Index=7, x=1.0, y=1.0, modelNumber=1, chainCode='B', sequenceId=1,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='#12', nmrSequenceCode='2b',
                 origIndex=6),
      AtomRecord(Index=8, x=1.0, y=1.0, modelNumber=1, chainCode='B', sequenceId=1,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='#12', nmrSequenceCode='2b',
                 origIndex=14),
      AtomRecord(Index=9, x=1.0, y=2.0, modelNumber=1, chainCode='B', sequenceId=2,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='#12', nmrSequenceCode='12',
                 origIndex=13),
      AtomRecord(Index=10, x=2.0, y=1.0, modelNumber=2, chainCode='A', sequenceId=1,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='@2', nmrSequenceCode='2b',
                 origIndex=4),
      AtomRecord(Index=11, x=2.0, y=1.0, modelNumber=2, chainCode='A', sequenceId=1,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='@2', nmrSequenceCode='2b',
                 origIndex=12),
      AtomRecord(Index=12, x=2.0, y=2.0, modelNumber=2, chainCode='A', sequenceId=2,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='@2', nmrSequenceCode='12',
                 origIndex=3),
      AtomRecord(Index=13, x=0.999, y=2.0, modelNumber=2, chainCode='B', sequenceId=-1,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='@2', nmrSequenceCode='12',
                 origIndex=11),
      AtomRecord(Index=14, x=2.0, y=1.0, modelNumber=2, chainCode='B', sequenceId=1,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='@12', nmrSequenceCode='2b',
                 origIndex=2),
      AtomRecord(Index=15, x=2.0, y=1.0, modelNumber=2, chainCode='B', sequenceId=1,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='@12', nmrSequenceCode='2b',
                 origIndex=10),
      AtomRecord(Index=16, x=2.0, y=2.0, modelNumber=2, chainCode='B', sequenceId=2,
                 atomName='HG12', nmrAtomName='HG12', nmrChainCode='@12', nmrSequenceCode='12',
                 origIndex=1),
      AtomRecord(Index=17, x=2.0, y=2.0, modelNumber=2, chainCode='B', sequenceId=2,
                 atomName='HG2', nmrAtomName='HG2', nmrChainCode='@12', nmrSequenceCode='12',
                 origIndex=9)
    ))