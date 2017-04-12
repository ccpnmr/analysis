"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan",
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-12 16:40:29 +0100 (Wed, April 12, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
import sys
import os
from ccpn.util import StructureData
from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr
from ccpnmodel.ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH
import pandas as pd

nan = math.nan

#=========================================================================================
# TestPandasData
#=========================================================================================

class TestPandasData(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  #=========================================================================================
  # setUp       initialise a newStructureEnsemble with ensemble.data
  #=========================================================================================

  def setUp(self):
    """
    Create a valid empty structureEnsemble
    """
    with self.initialSetup():
      self.ensemble = self.project.newStructureEnsemble()
      self.data = self.ensemble.data

  #=========================================================================================
  # setUp       initialise a newStructureEnsemble
  #=========================================================================================

  def test_float_column_1(self):
    self.data['x'] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    self.data['y'] = 11
    self.data['z'] = None
    ll = [1,2.0,'4', '5.0', None, 'NaN']
    ll2 = StructureData.fitToDataType(ll, float, force=True)
    self.data.bFactor = ll2
    self.assertEquals(list(self.data.index), [1,2,3,4,5,6])
    self.assertEquals(list(self.data['x']),  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    self.assertEquals(list(self.data['y']),  [11]*6)
    self.assertTrue(all(math.isnan(x) for x in self.data['z']))
    self.assertEquals(list(self.data.bFactor)[:4],  [1, 2,4,5])
    self.assertTrue(all(math.isnan(x) for x in self.data['bFactor'][-2:]))
    self.assertRaises(ValueError, self.data.__setitem__, 'bFactor', ll)

  def test_occupancy(self):
    self.data['occupancy'] = (0,0,0.1,0.99,1,1)
    self.assertRaises(ValueError, setattr, self.data, 'occupancy',  (0,0,-0.1,0.99,1,1))
    self.assertRaises(ValueError, setattr, self.data, 'occupancy',  (0,0,0.1,0.99,1,1.1))

  def test_sorting(self):
    self.data['x'] = [2,2,2,2,1,1,1,1] * 2
    self.data['y'] = [2,1,2,1,2,1,2,1] * 2
    self.data['z'] = None
    self.data['modelNumber'] = [2,2,2,2,1,1,1,1] * 2
    self.data['chainCode'] = ['B','B','A','A','B','B','A','A'] * 2
    self.data['sequenceId'] = [2,1,2,1,2,1,2,1] * 2
    self.data['atomName'] = ['HG12'] * 8 + ['HG2'] * 8
    self.data['nmrAtomName'] = self.data['atomName']
    self.data['nmrChainCode'] = ['@12', '@12', '@2', '@2', '#12', '#12', '#2', '#2'] * 2
    self.data['nmrSequenceCode'] = ['12', '2b'] * 8
    self.data.setValues(17)
    self.assertEquals(list(self.data.loc[17])[3:],  [None] * 7)
    self.assertTrue(all(math.isnan(x) for x in self.data.loc[17][:3]))
    self.data.addRow()
    self.assertEquals(list(self.data.loc[18])[3:],  [None] * 7)
    self.assertTrue(all(math.isnan(x) for x in self.data.loc[18][:3]))

    self.data['origIndex'] = range(1, self.data.shape[0] + 1)

    self.assertRaises(ValueError, self.data.setValues, 110)
    self.assertRaises(ValueError, self.data.setValues, -1)
    self.assertRaises(ValueError, self.data.setValues, 0)

    ll = ['modelNumber', 'chainCode', 'sequenceId']
    self.data.ccpnSort(*ll)
    self.assertEquals(list(self.data['modelNumber'])[2:], ([1] * 8 + [2] * 8))
    self.assertEquals(list(self.data['chainCode'])[2:], (['A'] * 4 + ['B'] * 4) * 2)
    self.assertEquals(list(self.data['sequenceId'])[2:], ([1,1,2,2] *4))
    self.assertEquals(list(self.data['atomName'])[2:], (['HG12', 'HG2'] *8))
    self.assertEquals(list(self.data['origIndex']),
                      [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    self.data.sort_values('origIndex', inplace=True)
    self.data.index = self.data['origIndex']

    ll = ['modelNumber', 'chainCode', 'sequenceId', 'atomName']
    self.data.ccpnSort(*ll)
    self.assertEquals(list(self.data['origIndex']),
                      [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    self.data.sort_values('origIndex', inplace=True)
    self.data.index = self.data['origIndex']

    ll = ['x', 'y', 'z']
    self.data.ccpnSort(*ll)
    self.assertEquals(list(self.data['origIndex']),
                      [17, 18, 6, 8, 14, 16, 5, 7, 13, 15, 2, 4, 10, 12, 1, 3, 9, 11])
    self.data.sort_values('origIndex', inplace=True)
    self.data.index = self.data['origIndex']

    ll = ['nmrChainCode', 'nmrSequenceCode']
    self.data.ccpnSort(*ll)
    self.assertEquals(list(self.data['origIndex']),
                      [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    self.data.sort_values('origIndex', inplace=True)
    self.data.index = self.data['origIndex']

    ll = ['nmrChainCode', 'nmrSequenceCode', 'nmrAtomName']
    self.data.ccpnSort(*ll)
    self.assertEquals(list(self.data['origIndex']),
                      [17, 18, 16, 8, 15, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1])
    self.data.sort_values('origIndex', inplace=True)
    self.data.index = self.data['origIndex']

    self.data.drop(7, inplace=True)
    self.data.setValues(5,chainCode='B', sequenceId=-1, x=0.999)
    self.data.setValues(10,chainCode='B', sequenceId=-1, x=0.999)
    ll = ['modelNumber', 'chainCode', 'sequenceId', 'atomName']
    self.data.ccpnSort(*ll)
    self.assertEquals(list(self.data['origIndex']),
                      [17, 18, 8, 16, 15, 5, 6, 14, 13, 4, 12, 3, 11, 2, 10, 1, 9])
    self.data.setValues(1, x=1.0, y=1.0)
    self.data.setValues(2, x=1.0, y=1.0)
    self.data.drop('z', axis=1, inplace=True)
    namedTuples = self.data.as_namedtuples()
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

  def test_structureData_ChainCode(self):
    self.data['chainCode'] = ['B','B','A','A','B','B','A','A']

    try:
      self.data['chainCode'] = ['A,B', 'C,D']
    except Exception as e:
      print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)

    try:
      self.data['chainCode'] = ['A, B, C']
    except Exception as e:
      print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)

    try:
      self.data['chainCode'] = ['A,B', 'C']
    except Exception as e:
      print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)

    try:
      self.data['chainCode'] = ['A-B']
    except Exception as e:
      print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)

  def test_structureData_residueNames(self):
    self.data['residueName'] = ['ALA', 'LEU', 'MET', 'THR', 'VAL']

    try:
      self.data['residueName'] = ['MET-ALU']   # a final check, but Pandas is catching all errors
    except Exception as e:
      print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)

  def test_structureData_testSelectors(self):
    self.data['atomName'] = ['CA', 'C', 'N', 'O', 'H'
                             ,'CB', 'HB1', ' HB2', 'HB3'
                             ,'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'
                             ,'CE', 'HE1', 'HE2', 'HE3'
                             ,'CG', 'HG1', 'HG2', 'HG3'
                             ,'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    self.data['residueName'] = ['ALA']*5 + ['ALA']*4 + ['LEU']*8 + ['MET']*4 + ['THR']*4 + ['VAL']*8

    self.assertEquals(list(self.data.backboneSelector), [True]*5+[False]*28)
    self.assertEquals(list(self.data.amideProtonSelector), [False]*4+[True]+[False]*28)
    self.assertEquals(list(self.data.amideNitrogenSelector), [False]*2+[True]+[False]*30)
    self.assertEquals(list(self.data.methylSelector), [False]*5+[True]*28)

  # def _test_structureData_loadPDB(self):
  #   """
  #   Test the from_pdf loading of a file.
  #   from_pdb and pdb2df will be removed soon.
  #   :return:
  #   """
  #   dataPath = '../structures/2CPP.pdb'
  #   if not os.path.isabs(dataPath):
  #     dataPath = os.path.join(TEST_PROJECTS_PATH, dataPath)
  #
  #   self.pd = self.data.from_pdb(dataPath)

  def test_structureData_extract(self):
    testAtomName = ['CA', 'C', 'N', 'O', 'H'
                   ,'CB', 'HB1', ' HB2', 'HB3'
                   ,'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'
                   ,'CE', 'HE1', 'HE2', 'HE3'
                   ,'CG', 'HG1', 'HG2', 'HG3'
                   ,'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    testResidueName = ['ALA']*5 + ['ALA']*4 + ['LEU']*8 + ['MET']*4 + ['THR']*4 + ['VAL']*8
    testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    testSequenceId = [1]*5 + [2]*4 + [3]*8 + [4]*4 + [5]*4 + [6]*8
    testModelNumbers = [1]*5 + [2]*4 + [3]*8 + [4]*4 + [5]*4 + [6]*8
    # testIds = [CH+'.'+str(SI)+'.'+RN+'.'+AT for AT, RN, CH, SI in zip(testAtomName
    #                                                              , testResidueName
    #                                                              , testChainCode
    #                                                              , testSequenceId)]

    self.data['atomName'] = testAtomName
    self.data['residueName'] = testResidueName
    self.data['chainCode'] = testChainCode
    self.data['sequenceId'] = testSequenceId
    self.data['modelNumber'] = testModelNumbers
    # self.data['ids'] = testIds

    self.ed = self.data.extract()                               # select everything
    self.assertEquals(list(self.ed['atomName']), testAtomName)
    self.assertEquals(list(self.ed['residueName']), testResidueName)

    self.ed = self.data.extract(inverse=True)                   # select nothing
    self.assertEquals(list(self.ed['atomName']), [])
    self.assertEquals(list(self.ed['residueName']), [])

    self.ed = self.data.extract(self.data.amideProtonSelector)
    self.assertEquals(list(self.ed['atomName']), ['H'])
    self.assertEquals(list(self.ed['residueName']), ['ALA'])

    with self.assertRaisesRegexp(ValueError, 'must be a Pandas series or None'):
      self.ed = self.data.extract(42)

    with self.assertRaisesRegexp(ValueError, 'number of atom records'):
      self.ed = self.data.extract(pd.Series((True,)))                     # only 1 element

    self.ed = self.data.extract(index=range(1, 5))                        # select nothing
    self.assertEquals(list(self.ed['atomName']), testAtomName[:4])
    self.assertEquals(list(self.ed['residueName']), testResidueName[:4])

    self.ed = self.data.extract(index=1)                                  # select nothing
    self.assertEquals(list(self.ed['atomName']), [testAtomName[0]])       # remember, list of 1 element
    self.assertEquals(list(self.ed['residueName']), [testResidueName[0]])

    self.ed = self.data.extract(index='1, 2, 6-7, 9')                     # select numbered elements
    self.assertEquals(list(self.ed['atomName']), ['CA', 'C', 'CB', 'HB1', 'HB3'])
    self.assertEquals(list(self.ed['residueName']), ['ALA']*5)

    self.ed = self.data.extract(chainCodes = ['B'])
    self.assertEquals(list(self.ed['atomName']), ['CB', 'HB1', ' HB2', 'HB3'])
    self.assertEquals(list(self.ed['residueName']), ['ALA']*4)

    self.ed = self.data.extract(sequenceIds=[1, 2])
    self.assertEquals(list(self.ed['atomName']), testAtomName[:9])
    self.assertEquals(list(self.ed['residueName']), testResidueName[:9])

    self.ed = self.data.extract(sequenceIds=2)
    self.assertEquals(list(self.ed['atomName']), testAtomName[5:9])
    self.assertEquals(list(self.ed['residueName']), testResidueName[5:9])

    self.ed = self.data.extract(sequenceIds='2-3')
    self.assertEquals(list(self.ed['atomName']), testAtomName[5:17])
    self.assertEquals(list(self.ed['residueName']), testResidueName[5:17])
    self.ed = self.data.extract(sequenceIds='4,5,6')
    self.assertEquals(list(self.ed['atomName']), testAtomName[17:])
    self.assertEquals(list(self.ed['residueName']), testResidueName[17:])

    self.ed = self.data.extract(modelNumbers=[1, 2])
    self.assertEquals(list(self.ed['atomName']), testAtomName[:9])
    self.assertEquals(list(self.ed['residueName']), testResidueName[:9])

    self.ed = self.data.extract(modelNumbers=2)
    self.assertEquals(list(self.ed['atomName']), testAtomName[5:9])
    self.assertEquals(list(self.ed['residueName']), testResidueName[5:9])

    self.ed = self.data.extract(modelNumbers='2-3')
    self.assertEquals(list(self.ed['atomName']), testAtomName[5:17])
    self.assertEquals(list(self.ed['residueName']), testResidueName[5:17])
    self.ed = self.data.extract(modelNumbers='4,5,6')
    self.assertEquals(list(self.ed['atomName']), testAtomName[17:])
    self.assertEquals(list(self.ed['residueName']), testResidueName[17:])

    self.ed = self.data.extract(ids='A.1.ALA.C')
    self.assertEquals(list(self.ed['atomName']), [testAtomName[1]])
    self.assertEquals(list(self.ed['residueName']), [testResidueName[1]])

    self.ed = self.data.extract(ids=['A.1.ALA.CA', 'A.1.ALA.C'])
    self.assertEquals(list(self.ed['atomName']), testAtomName[:2])
    self.assertEquals(list(self.ed['residueName']), testResidueName[:2])

#=========================================================================================
# test_StructureData_properties
#=========================================================================================

class TestStructureData_properties(WrapperTesting):

  #=========================================================================================
  # setUp       initialise a newStructureEnsemble
  #=========================================================================================

  def setUp(self):
    """
    Create a valid empty structureEnsemble
    """
    with self.initialSetup():
      self.ensemble = self.project.newStructureEnsemble()

  #=========================================================================================
  # test_valuetoOptionalInt      force is False
  #=========================================================================================

  def test_valuetoOptionalInt_Int(self):
    """
    Test that passing 42 (int) to valuetoOptionalInt returns an int.
    """
    self.assertEquals(StructureData.valueToOptionalInt(42), 42)

  def test_valuetoOptionalInt_None(self):
    """
    Test that passing None to valuetoOptionalInt returns None.
    """
    self.assertEquals(StructureData.valueToOptionalInt(None), None)

  def test_valuetoOptionalInt_NaN(self):
    """
    Test that passing NaN to valuetoOptionalInt returns None.
    """
    self.assertEquals(StructureData.valueToOptionalInt(float('NaN')), None)

  def test_valuetoOptionalInt_IntFloat(self):
    """
    Test that passing int value float to valuetoOptionalInt returns int.
    """
    vtoint = StructureData.valueToOptionalInt(float(42.0))
    self.assertIsInstance(vtoint, int)

  def test_valuetoOptionalInt_Float(self):
    """
    Test that passing float to valuetoOptionalInt raises error.
    """
    with self.assertRaisesRegexp(TypeError, 'does not correspond to an integer'):
      StructureData.valueToOptionalInt(42.42)

  def test_valuetoOptionalInt_String(self):
    """
    Test that passing string to valuetoOptionalInt raises error.
    Can assume that all other non-number will raise error
    """
    with self.assertRaisesRegexp(TypeError, 'does not correspond to an integer'):
      StructureData.valueToOptionalInt('Invalid')

  #=========================================================================================
  # test_valuetoOptionalType      force is True - overrides the error and returns None
  #=========================================================================================

  def test_valuetoOptionalInt_forceInt(self):
    """
    Test that passing 42 (int) to valuetoOptionalInt returns an int.
    """
    self.assertEquals(StructureData.valueToOptionalInt(42, True), 42)

  def test_valuetoOptionalInt_forceFloat(self):
    """
    Test that passing float to valuetoOptionalInt returns None.
    """
    self.assertEquals(StructureData.valueToOptionalInt(42.42, True), None)

  def test_valuetoOptionalInt_forceFloatInt(self):
    """
    Test that passing int value float to valuetoOptionalInt returns int.
    """
    self.assertEquals(StructureData.valueToOptionalInt(float(42.0), True), 42)

  def test_valuetoOptionalInt_forceString(self):
    """
    Test that passing string to valuetoOptionalInt returns None.
    """
    self.assertEquals(StructureData.valueToOptionalInt('Invalid', True), None)

  #=========================================================================================
  # test_valuetoOptionalType      force is False
  #=========================================================================================

  def test_valuetoOptionalType_None(self):
    """
    Test that passing None to valuetoOptionalType returns None.
    """
    self.assertEquals(StructureData.valueToOptionalType(None, int), None)

  def test_valuetoOptionalType_Nan(self):
    """
    Test that passing NaN to valuetoOptionalType returns None.
    """
    self.assertEquals(StructureData.valueToOptionalType(float('NaN'), str), None)


  def test_valuetoOptionalType_Int(self):
    """
    Test that passing 42 (int=int) to valuetoOptionalType returns 42.
    """
    self.assertEquals(StructureData.valueToOptionalType(42, int), 42)

  def test_valuetoOptionalType_String(self):
    """
    Test that passing 42 (string=string) to valuetoOptionalType returns 42.
    """
    self.assertEquals(StructureData.valueToOptionalType('42', str), '42')

  def test_valuetoOptionalType_ES(self):
    """
    Test that passing 42 (int<>float) to valuetoOptionalType returns None.
    """
    with self.assertRaisesRegexp(TypeError, 'does not correspond to type'):
      StructureData.valueToOptionalType(42, float)

  #=========================================================================================
  # test_valuetoOptionalType      force is True
  #=========================================================================================

  def test_valuetoOptionalType_IntFloat(self):
    """
    Test that passing 42 (int<>float) to valuetoOptionalType returns float.
    """
    self.assertEquals(StructureData.valueToOptionalType(42, float, True), 42.0)

  def test_valuetoOptionalType_IntString(self):
    """
    Test that passing 42 (int<>string) to valuetoOptionalType returns string.
    """
    self.assertEquals(StructureData.valueToOptionalType(42, str, True), '42')

  def test_valuetoOptionalType_IntTuple(self):
    """
    Test that passing 42 (int<>tuple) to valuetoOptionalType raises error.

    This is an expectedFailure needs to be expected type
    """
    with self.assertRaisesRegexp(TypeError, 'does not correspond to type'):
      StructureData.valueToOptionalType(42, tuple, True)
