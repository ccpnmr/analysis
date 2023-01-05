"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-01-05 14:27:54 +0000 (Thu, January 05, 2023) $"
__version__ = "$Revision: 3.1.0 $"
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
import pandas as pd
from ccpn.util import StructureData
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.core._implementation.DataFrameABC import valueToOptionalInt, valueToOptionalType


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
    # testOccupancySorting
    #=========================================================================================

    def test_float_column_1(self):
        self.data['x'] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        self.data['y'] = 11
        self.data['z'] = None
        ll = [1, 2.0, '4', '5.0', None, 'NaN']
        ll2 = StructureData.fitToDataType(ll, float, force=True)

        # calls the __setattr__ method of ensembleData for _reserved columns, otherwise
        self.data['bFactor'] = ll2
        self.assertEqual(list(self.data.index), [1, 2, 3, 4, 5, 6])
        self.assertEqual(list(self.data['x']), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        self.assertEqual(list(self.data['y']), [11] * 6)
        self.assertTrue(all(math.isnan(x) for x in self.data['z']))
        self.assertEqual(list(self.data.bFactor)[:4], [1, 2, 4, 5])
        self.assertTrue(all(math.isnan(x) for x in self.data['bFactor'][-2:]))
        self.assertRaises(ValueError, self.data.__setitem__, 'bFactor', ll)

    def test_occupancy(self):
        self.data['occupancy'] = (0, 0, 0.1, 0.99, 1, 1)
        self.assertRaises(ValueError, setattr, self.data, 'occupancy', (0, 0, -0.1, 0.99, 1, 1))
        self.assertRaises(ValueError, setattr, self.data, 'occupancy', (0, 0, 0.1, 0.99, 1, 1.1))

    def test_sorting(self):
        self.UndoState = (self.undo.maxWaypoints,  # = maxWaypoints
                          self.undo.maxOperations,  # = maxOperations
                          self.undo.nextIndex,  # = 0   # points to next free slot (or first slot to redo)
                          self.undo.waypoints,  # = []  # array of last item in each waypoint
                          self.undo._blocked,  # = False # Block/unblock switch - internal use only
                          self.undo.undoItemBlocking,
                          len(self.undo),
                          self.undo[0])  # = 0 # Blocking level - modify with increaseBlocking/decreaseBlocking only
        print('preUNDO STATE:                          ', self.UndoState)

        self.data['x'] = [2, 2, 2, 2, 1, 1, 1, 1] * 2
        self.UndoState = (self.undo.maxWaypoints,  # = maxWaypoints
                          self.undo.maxOperations,  # = maxOperations
                          self.undo.nextIndex,  # = 0   # points to next free slot (or first slot to redo)
                          self.undo.waypoints,  # = []  # array of last item in each waypoint
                          self.undo._blocked,  # = False # Block/unblock switch - internal use only
                          self.undo.undoItemBlocking,  # = 0 # Blocking level - modify with increaseBlocking/decreaseBlocking only
                          len(self.undo),
                          self.undo[0])  # = 0 # Blocking level - modify with increaseBlocking/decreaseBlocking only
        print("preUNDO STATE, addition data['x']:      ", self.UndoState)

        self.assertEqual(list(self.data['x']), [2, 2, 2, 2, 1, 1, 1, 1] * 2)

        self.undo.undo()  # ejb - undo addition of 'x'

        with self.assertRaisesRegex(KeyError, 'x'):  # should raise KeyError as deleted
            self.assertEqual(list(self.data['x']), None)

        self.UndoState = (self.undo.maxWaypoints,  # = maxWaypoints
                          self.undo.maxOperations,  # = maxOperations
                          self.undo.nextIndex,  # = 0   # points to next free slot (or first slot to redo)
                          self.undo.waypoints,  # = []  # array of last item in each waypoint
                          self.undo._blocked,  # = False # Block/unblock switch - internal use only
                          self.undo.undoItemBlocking,  # = 0 # Blocking level - modify with increaseBlocking/decreaseBlocking only
                          len(self.undo),
                          self.undo[0])  # = 0 # Blocking level - modify with increaseBlocking/decreaseBlocking only
        print("postUNDO STATE, deletion data['x']:     ", self.UndoState)

        self.undo.redo()  # ejb redo addition of 'x'
        self.assertEqual(list(self.data['x']), [2, 2, 2, 2, 1, 1, 1, 1] * 2)

        self.data['y'] = [2, 1, 2, 1, 2, 1, 2, 1] * 2
        self.data['z'] = None

        self.undo.undo()
        self.undo.undo()
        self.assertEqual(len(self.data.columns), 1)
        self.assertEqual(list(self.data.columns), ['x'])
        self.undo.redo()
        self.undo.redo()

        self.data['modelNumber'] = [2, 2, 2, 2, 1, 1, 1, 1] * 2
        self.assertEqual(len(self.data.columns), 4)
        self.assertEqual(list(self.data.columns), ['x', 'y', 'z', 'modelNumber'])

        self.undo.undo()
        self.undo.undo()
        self.undo.undo()
        self.undo.undo()

        with self.assertRaisesRegex(KeyError, 'x'):  # should raise KeyError as deleted
            self.assertEqual(list(self.data['x']), None)
        # undo from here should be redundant
        self.undo.undo()
        self.undo.undo()
        self.undo.undo()  # test with plenty

        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        # undo from here should be redundant
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()  # check
        self.undo.redo()  # check
        self.assertEqual(len(self.data.columns), 4)
        self.assertEqual(list(self.data.columns), ['x', 'y', 'z', 'modelNumber'])

        self.data['chainCode'] = ['B', 'B', 'A', 'A', 'B', 'B', 'A', 'A'] * 2
        self.undo.undo()
        self.undo.redo()
        self.data['sequenceId'] = [2, 1, 2, 1, 2, 1, 2, 1] * 2
        self.data['atomName'] = ['HG12'] * 8 + ['HG2'] * 8
        self.data['nmrAtomName'] = self.data['atomName']
        self.data['nmrChainCode'] = ['@12', '@12', '@2', '@2', '#12', '#12', '#2', '#2'] * 2
        self.data['nmrSequenceCode'] = ['12', '2b'] * 8
        self.data.setValues(17)
        self.assertEqual(len(self.data), 17)

        self.undo.undo()  # undo new row 17
        self.assertEqual(len(self.data), 16)

        self.undo.redo()
        self.assertEqual(len(self.data), 17)

        _checkRow = [nan, nan, nan, nan, None, nan, None, None, None, None]
        _row = list(self.data.loc[17])
        for rowVal, checkVal in zip(_row, _checkRow):
            if checkVal is None:
                self.assertEqual(rowVal, checkVal)
            else:  # is nan
                self.assertTrue(math.isnan(rowVal))
        # self.assertEqual(list(self.data.loc[17])[3:], _checkRow)
        # self.assertTrue(all(math.isnan(x) for x in self.data.loc[17][:3]))
        self.data.addRow()
        self.assertEqual(len(self.data), 18)

        self.undo.undo()  # undo new row with 'addRow'
        self.assertEqual(len(self.data), 17)
        self.undo.redo()  # should be the same as above

        for rowVal, checkVal in zip(_row, _checkRow):
            if checkVal is None:
                self.assertEqual(rowVal, checkVal)
            else:
                self.assertTrue(math.isnan(rowVal))
        # self.assertEqual(list(self.data.loc[18])[3:], _checkRow)
        # self.assertTrue(all(math.isnan(x) for x in self.data.loc[18][:3]))

        # not really required as implicit to the sorting - new columns SHOULD be included in undo/redo
        self.data['origIndex'] = list(range(1, self.data.shape[0] + 1))
        _val = self.data.copy()
        self.undo.undo()
        self.undo.redo()
        _val2 = self.data.copy()
        self.assertEqual(_val.equals(_val2), True)

        self.assertRaises(ValueError, self.data.setValues, 110)
        self.assertRaises(ValueError, self.data.setValues, -1)
        self.assertRaises(ValueError, self.data.setValues, 0)

        ll = ['modelNumber', 'chainCode', 'sequenceId']
        self.data.ccpnSort(*ll)
        self.undo.undo()
        self.undo.redo()

        # ejb - [2:] because of the inserted rows being sorted to the head of the list

        self.assertEqual(list(self.data['modelNumber'])[2:], ([1] * 8 + [2] * 8))
        self.assertEqual(list(self.data['chainCode'])[2:], (['A'] * 4 + ['B'] * 4) * 2)
        self.assertEqual(list(self.data['sequenceId'])[2:], ([1, 1, 2, 2] * 4))
        self.assertEqual(list(self.data['atomName'])[2:], (['HG12', 'HG2'] * 8))
        self.assertEqual(list(self.data['origIndex']),
                         [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
        self.data.sort_values('origIndex', inplace=True)
        self.data.index = self.data['origIndex']

        ll = ['modelNumber', 'chainCode', 'sequenceId', 'atomName']
        self.data.ccpnSort(*ll)
        self.assertEqual(list(self.data['origIndex']),
                         [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
        self.data.sort_values('origIndex', inplace=True)
        self.data.index = self.data['origIndex']

        ll = ['x', 'y', 'z']
        self.data.ccpnSort(*ll)
        self.assertEqual(list(self.data['origIndex']),
                         [17, 18, 6, 8, 14, 16, 5, 7, 13, 15, 2, 4, 10, 12, 1, 3, 9, 11])
        self.data.sort_values('origIndex', inplace=True)
        self.data.index = self.data['origIndex']

        ll = ['nmrChainCode', 'nmrSequenceCode']
        self.data.ccpnSort(*ll)
        self.assertEqual(list(self.data['origIndex']),
                         [17, 18, 8, 16, 7, 15, 6, 14, 5, 13, 4, 12, 3, 11, 2, 10, 1, 9])
        self.data.sort_values('origIndex', inplace=True)
        self.data.index = self.data['origIndex']

        # ejb - CANNOT UNDO PAST THIS POINT AS NOT USING CCPNSORT
        #       ONLY CCPN OPERATIONS CAN BE PERFORMED ON PANDAS DATAFRAMES
        #       IF THE INTEGRITY OF THE UNDO LIST IS TO BE PRESERVED

        ll = ['nmrChainCode', 'nmrSequenceCode', 'nmrAtomName']
        self.data.ccpnSort(*ll)
        self.assertEqual(list(self.data['origIndex']),
                         [17, 18, 16, 8, 15, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1])

        _presort = self.data.copy()

        # self.data.sort_values('origIndex', inplace=True)
        # self.data.index = self.data['origIndex']
        self.data.ccpnSort('origIndex')  # same as the above 2 lines
        _val = self.data.copy()
        self.undo.undo()
        self.assertEqual(self.data.equals(_presort), True)
        self.undo.redo()
        self.assertEqual(self.data.equals(_val), True)

        self.data['tempSequence'] = [3, 2, 1, 2, 1, 2, 2, 1, 0] * 2
        _postCol = self.data.copy()
        self.undo.undo()
        self.assertEqual(self.data.equals(_val), True)
        self.undo.redo()
        self.assertEqual(self.data.equals(_postCol), True)
        self.undo.undo()
        self.assertEqual(self.data.equals(_val), True)

        namedTuple = self.data.as_namedtuples()[4]
        AtomRecord = namedTuple.__class__
        # cannot compare if contains nans
        self.assertEqual(str(namedTuple), str(AtomRecord(Index=5, x=1.0, y=2.0, z=nan, modelNumber=1.0, chainCode='B', sequenceId=2.0,
                                                         atomName='HG12', nmrAtomName='HG12', nmrChainCode='#12', nmrSequenceCode='12',
                                                         origIndex=5)))

        self.data.deleteRow(7)
        self.assertEqual(list(self.data['chainCode']),
                         ['B', 'B', 'A', 'A', 'B', 'B', 'A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', None, None])
        self.undo.undo()
        self.assertEqual(list(self.data['chainCode']),
                         ['B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', None, None])
        self.undo.redo()
        self.assertEqual(list(self.data['chainCode']),
                         ['B', 'B', 'A', 'A', 'B', 'B', 'A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'A', None, None])

        with self.assertRaisesRegex(TypeError, 'required positional argument'):  # should raise ValueError
            self.data.deleteRow()
        with self.assertRaisesRegex(ValueError, 'deleteRow: Row does not exist'):  # should raise ValueError
            self.data.deleteRow(42)
        with self.assertRaisesRegex(TypeError, 'deleteRow: Row is not an int'):  # should raise ValueError
            self.data.deleteRow('notInt')

        self.data.setValues(5, chainCode='B', sequenceId=-1, x=0.995)
        self.data.setValues(10, chainCode='B', sequenceId=-1, x=0.99)
        ll = ['modelNumber', 'chainCode', 'sequenceId', 'atomName']
        self.data.ccpnSort(*ll)
        self.undo.undo()
        self.undo.redo()

        self.assertEqual(list(self.data['origIndex']),
                         [17, 18, 8, 16, 15, 5, 6, 14, 13, 4, 12, 3, 11, 2, 10, 1, 9])
        self.data.setValues(1, x=1.0, y=1.0)
        self.data.setValues(2, x=1.0, y=1.0)

        self.undo.undo()  # Can undo 7 points to the self.data.sort_values
        self.undo.undo()  # but not any further as this is not supported by Ccpn
        self.undo.undo()
        self.undo.undo()

        self.undo.undo()
        self.undo.undo()
        self.undo.undo()

        self.undo.redo()
        self.undo.redo()
        self.undo.redo()

        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()

        _predelete = self.data.copy()
        self.data.deleteCol('chainCode')
        _postdelete = self.data.copy()
        self.undo.undo()
        self.assertEqual(self.data.equals(_predelete), True)
        self.undo.redo()
        self.assertEqual(self.data.equals(_postdelete), True)
        self.undo.undo()
        self.assertEqual(self.data.equals(_predelete), True)

        _predelete = self.data.copy()
        # self.data.drop('z', axis=1, inplace=True)      # ejb - does not work on 'drop'
        # new function deleteCol has been added to replace simple drop
        self.data.deleteCol('z')
        self.data.deleteSelectedRows(index='1, 2, 6-7, 9')
        _postdelete = self.data.copy()
        self.undo.undo()
        self.undo.undo()
        self.assertEqual(self.data.equals(_predelete), True)
        self.undo.redo()
        self.undo.redo()
        self.assertEqual(self.data.equals(_postdelete), True)

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[0:4], (
            AtomRecord(Index=1, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                       atomName='HG12', nmrAtomName='HG12', nmrChainCode='#2', nmrSequenceCode='2b',
                       origIndex=8.0),
            AtomRecord(Index=2, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                       atomName='HG2', nmrAtomName='HG2', nmrChainCode='#2', nmrSequenceCode='2b',
                       origIndex=16.0),
            AtomRecord(Index=3, x=1.0, y=2.0, modelNumber=1, chainCode='A', sequenceId=2,
                       atomName='HG2', nmrAtomName='HG2', nmrChainCode='#2', nmrSequenceCode='12',
                       origIndex=15.0),
            AtomRecord(Index=4, x=1.0, y=1.0, modelNumber=1, chainCode='B', sequenceId=1,
                       atomName='HG2', nmrAtomName='HG2', nmrChainCode='#12', nmrSequenceCode='2b',
                       origIndex=14.0)))

        self.undo.undo()  # recover deleted rows index='1, 2, 6-7, 9'
        self.undo.undo()  # recover column 'z'
        self.undo.redo()  # delete column 'z' again
        self.undo.redo()  # delete index='1, 2, 6-7, 9' again
        self.undo.undo()  # recover deleted rows index='1, 2, 6-7, 9' again

        with self.assertRaisesRegex(TypeError, 'deleteCol: required positional argument'):  # should raise ValueError
            self.data.deleteCol()
        with self.assertRaisesRegex(ValueError, 'deleteCol: Column does not exist'):  # should raise ValueError
            self.data.deleteCol('notFound')
        with self.assertRaisesRegex(TypeError, 'deleteCol: Column is not a string'):  # should raise ValueError
            self.data.deleteCol(42)

        with self.assertRaisesRegex(KeyError, 'z'):  # should raise KeyError as deleted
            self.assertEqual(list(self.data['z']), None)
        self.undo.undo()  # recover 'z' as nans

        self.assertEqual(str(list(self.data['z'])), str([nan] * 17))  # back again as list of nan
        self.undo.redo()  # delete 'z' again

        with self.assertRaisesRegex(KeyError, 'z'):  # should raise KeyError as re-deleted
            self.assertEqual(list(self.data['z']), None)

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        # cannot compare first 2 elements as contain nans
        self.assertEqual(namedTuples[2:], (
            # AtomRecord(Index=1, x=1.0, y=1.0, modelNumber=None, chainCode=None, sequenceId=None,
            #            atomName=None, nmrAtomName=None, nmrChainCode=None, nmrSequenceCode=None,
            #            origIndex=17),
            # AtomRecord(Index=2, x=1.0, y=1.0, modelNumber=None, chainCode=None, sequenceId=None,
            #            atomName=None, nmrAtomName=None, nmrChainCode=None, nmrSequenceCode=None,
            #            origIndex=18),
            AtomRecord(Index=3, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                       atomName='HG12', nmrAtomName='HG12', nmrChainCode='#2', nmrSequenceCode='2b',
                       origIndex=8),
            AtomRecord(Index=4, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                       atomName='HG2', nmrAtomName='HG2', nmrChainCode='#2', nmrSequenceCode='2b',
                       origIndex=16),
            AtomRecord(Index=5, x=1.0, y=2.0, modelNumber=1, chainCode='A', sequenceId=2,
                       atomName='HG2', nmrAtomName='HG2', nmrChainCode='#2', nmrSequenceCode='12',
                       origIndex=15),
            AtomRecord(Index=6, x=0.995, y=2.0, modelNumber=1, chainCode='B', sequenceId=-1,
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
            AtomRecord(Index=13, x=0.99, y=2.0, modelNumber=2, chainCode='B', sequenceId=-1,
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

        self.data.deleteCol('y')
        self.undo.undo()  # recover 'y'
        self.undo.undo()  # recover
        self.undo.undo()  # recover
        self.undo.undo()  # recover
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[2], AtomRecord(Index=3, x=1.0, modelNumber=1, chainCode='A', sequenceId=1,
                                                    atomName='HG12', nmrAtomName='HG12', nmrChainCode='#2', nmrSequenceCode='2b',
                                                    origIndex=8))
        # self.undo.undo()
        # namedTuples = self.data.as_namedtuples()
        # AtomRecord = namedTuples[0].__class__
        # self.assertEqual(namedTuples[2], AtomRecord(Index=3, x=1.0, y=1.0, modelNumber=1, chainCode='A', sequenceId=1,
        #                    atomName='HG12', nmrAtomName='HG12', nmrChainCode='#2', nmrSequenceCode='2b',
        #                    origIndex=8))

    #=========================================================================================
    # test_structureData_modelNumber
    #=========================================================================================

    def test_structureData_modelNumber(self):
        # with self.assertRaisesRegex(TypeError, 'does not correspond to an integer'):
        self.data['modelNumber'] = ['12']
        # with self.assertRaisesRegex(KeyError, 'modelNumber'):      # should raise KeyError
        #   self.assertEqual(list(self.data['modelNumber']), None)

        # with self.assertRaisesRegex(ValueError, 'Length of values does not match length of index'):
        #     self.data['modelNumber'] = [1, 2, 3, 4, 5]  # other attributes must be defined first
        # with self.assertRaisesRegex(KeyError, 'modelNumber'):      # should raise KeyError
        self.assertEqual(list(self.data['modelNumber']), [12])

        self.data['modelNumber'] = [5]
        with self.assertRaisesRegex(ValueError, 'Model numbers must be integers >= 1'):
            self.data['modelNumber'] = [-1]
        self.assertEqual(list(self.data['modelNumber']), [5])

    #=========================================================================================
    # test_structureData_nmrSequenceCode
    #=========================================================================================

    def test_structureData_nmrSequenceCode(self):
        self.data['nmrSequenceCode'] = ['12']
        self.assertEqual(list(self.data['nmrSequenceCode']), ['12'])

        self.data['nmrSequenceCode'] = [13]
        self.assertEqual(list(self.data['nmrSequenceCode']), ['13'])

        self.data['nmrSequenceCode'] = [14.0]
        self.assertEqual(list(self.data['nmrSequenceCode']), ['14'])

        self.data['nmrSequenceCode'] = [nan]
        self.assertEqual(list(self.data['nmrSequenceCode']), [None])

        with self.assertRaisesRegex(ValueError, 'nmrSequenceCode must have integer values if entered as numbers'):  # should raise KeyError as re-deleted
            self.data['nmrSequenceCode'] = [15.5]
        self.assertEqual(list(self.data['nmrSequenceCode']), [None])  # still None from above

        with self.assertRaisesRegex(ValueError, 'nmrSequenceCode must be set as strings or integer values'):  # should raise KeyError as re-deleted
            self.data['nmrSequenceCode'] = [(15, 16)]
        self.assertEqual(list(self.data['nmrSequenceCode']), [None])  # still None from above

    #=========================================================================================
    # test_structureData_ChainCode
    #=========================================================================================

    def test_structureData_ChainCode(self):
        self.data['chainCode'] = ['B', 'B', 'A', 'A', 'B', 'B', 'A', 'A']

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

    #=========================================================================================
    # test_structureData_residueNames
    #=========================================================================================

    def test_structureData_residueNames(self):
        self.data['residueName'] = ['ALA', 'LEU', 'MET', 'THR', 'VAL']

        try:
            self.data['residueName'] = ['MET-ALU']  # a final check, but Pandas is catching all errors
        except Exception as e:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e), e)


#=========================================================================================
# TestSelectors
#=========================================================================================

class TestSelectors_Iterator(WrapperTesting):
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
            self.testAtomName = ['CA', 'C', 'N', 'O', 'H',
                                 'CB', 'HB1', ' HB2', 'HB3',
                                 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23',
                                 'CE', 'HE1', 'HE2', 'HE3',
                                 'CG', 'HG1', 'HG2', 'HG3',
                                 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
            self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + ['VAL'] * 8
            self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
            self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
            self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
            self.testElement = ['H'] * 4 + ['O'] * 4 + ['C'] * 4 + ['N'] * 21
            self.testFuncName = ['H',
                                 'HB1', ' HB2', 'HB3',
                                 'HD11', 'HD12', 'HD13', 'HD21', 'HD22', 'HD23',
                                 'HE1', 'HE2', 'HE3',
                                 'HG1', 'HG2', 'HG3',
                                 'HG11', 'HG12', 'HG13', 'HG21', 'HG22', 'HG23']

            self.data['atomName'] = self.testAtomName
            self.data['residueName'] = self.testResidueName
            self.data['chainCode'] = self.testChainCode
            self.data['sequenceId'] = self.testSequenceId
            self.data['modelNumber'] = self.testModelNumber
            # self.testIds = [CH+'.'+str(SI)+'.'+RN+'.'+AT for AT, RN, CH, SI in zip(testAtomName,
            #                                                              testResidueName,
            #                                                              testChainCode,
            #                                                               testSequenceId)]
            # self.data['ids'] = testIds
            # Ids are set automatically, code is above just for visible check

    #=========================================================================================
    # test_structureData_testSelectors
    #=========================================================================================

    def test_structureData_testSelectors(self):
        self.assertEqual(list(self.data.backboneSelector), [True] * 5 + [False] * 28)
        self.assertEqual(list(self.data.amideProtonSelector), [False] * 4 + [True] + [False] * 28)
        self.assertEqual(list(self.data.amideNitrogenSelector), [False] * 2 + [True] + [False] * 30)
        self.assertEqual(list(self.data.methylSelector), [False] * 5 + [True] * 28)

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
        self.ed = self.data.extract()  # select everything
        self.assertEqual(list(self.ed['atomName']), self.testAtomName)
        self.assertEqual(list(self.ed['residueName']), self.testResidueName)

        self.ed = self.data.extract(inverse=True)  # select nothing
        self.assertEqual(list(self.ed['atomName']), [])
        self.assertEqual(list(self.ed['residueName']), [])

        self.ed = self.data.extract(self.data.amideProtonSelector)
        self.assertEqual(list(self.ed['atomName']), ['H'])
        self.assertEqual(list(self.ed['residueName']), ['ALA'])
        namedTuples = self.ed.as_namedtuples()
        self.assertEqual(len(namedTuples), 1)  # there should only be 1
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[0], (AtomRecord(Index=5,
                                                     atomName='H',
                                                     residueName='ALA',
                                                     chainCode='A',
                                                     sequenceId=1,
                                                     modelNumber=1)))  # check initial values

        with self.assertRaisesRegex(ValueError, 'must be a Pandas series or None'):
            self.ed = self.data.extract(42)

        with self.assertRaisesRegex(ValueError, 'number of records'):
            self.ed = self.data.extract(pd.Series((True,)))  # only 1 element

        self.ed = self.data.extract(index=range(1, 5))  # select nothing
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[:4])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[:4])

        self.ed = self.data.extract(index=1)  # select nothing
        self.assertEqual(list(self.ed['atomName']), [self.testAtomName[0]])  # remember, list of 1 element
        self.assertEqual(list(self.ed['residueName']), [self.testResidueName[0]])

        self.ed = self.data.extract(index='1, 2, 6-7, 9')  # select numbered elements
        self.assertEqual(list(self.ed['atomName']), ['CA', 'C', 'CB', 'HB1', 'HB3'])
        self.assertEqual(list(self.ed['residueName']), ['ALA'] * 5)

        self.ed = self.data.extract(chainCodes=['B'])
        self.assertEqual(list(self.ed['atomName']), ['CB', 'HB1', ' HB2', 'HB3'])
        self.assertEqual(list(self.ed['residueName']), ['ALA'] * 4)

        self.ed = self.data.extract(sequenceIds=[1, 2])
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[:9])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[:9])

        self.ed = self.data.extract(sequenceIds=2)
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[5:9])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[5:9])

        self.ed = self.data.extract(sequenceIds='2-3')
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[5:17])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[5:17])
        self.ed = self.data.extract(sequenceIds='4,5,6')
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[17:])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[17:])

        self.ed = self.data.extract(modelNumbers=[1, 2])
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[:9])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[:9])

        self.ed = self.data.extract(modelNumbers=2)
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[5:9])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[5:9])

        self.ed = self.data.extract(modelNumbers='2-3')
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[5:17])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[5:17])
        self.ed = self.data.extract(modelNumbers='4,5,6')
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[17:])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[17:])

        self.ed = self.data.extract(ids='A.1.ALA.C')
        self.assertEqual(list(self.ed['atomName']), [self.testAtomName[1]])
        self.assertEqual(list(self.ed['residueName']), [self.testResidueName[1]])

        self.ed = self.data.extract(ids=['A.1.ALA.CA', 'A.1.ALA.C'])
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[:2])
        self.assertEqual(list(self.ed['residueName']), self.testResidueName[:2])

        with self.assertRaisesRegex(KeyError, 'element'):
            self.ed = self.data.extract(elements=['N'])
        self.data['element'] = self.testElement
        self.ed = self.data.extract(elements=['O'])
        self.assertEqual(list(self.ed['atomName']), self.testAtomName[4:8])

        self.data['notFound'] = self.testAtomName  # this is non-reserved
        self.data.drop('notFound', axis=1, inplace=True)  # need to use drop for non-reserved columns

        self.ed = self.data.extract(atomNames='HG12')
        namedTuples = self.ed.as_namedtuples()
        self.assertEqual(len(namedTuples), 1)  # there should only be 1
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[0], (AtomRecord(Index=28,
                                                     atomName='HG12',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6,
                                                     element='N')))  # check initial values

        def funcSelect(*args, **kwargs) -> bool:
            """
            Test function to check that the funcSelector is working.
            Return True if the atomName contains 'H' otherwise False
            :param args:
            :param kwargs:
            :return:
            """
            thisAtomName = args[0]['atomName']
            return 'H' in thisAtomName

        self.ed = self.data.extract(func=funcSelect)
        self.assertEqual(list(self.ed['atomName']), self.testFuncName)

    #=========================================================================================
    # test_structureData_Iterator
    #=========================================================================================

    def test_structureData_Iterator(self):
        self.itRec = self.data.records()
        for rNum, rec in enumerate(self.itRec):
            self.assertEqual(list(rec['atomName']), [self.testAtomName[rNum]])
            self.assertEqual(list(rec['residueName']), [self.testResidueName[rNum]])
            self.assertEqual(list(rec['chainCode']), [self.testChainCode[rNum]])
            self.assertEqual(list(rec['sequenceId']), [self.testSequenceId[rNum]])
            self.assertEqual(list(rec['modelNumber']), [self.testModelNumber[rNum]])


#=========================================================================================
# test_StructureData_properties
#=========================================================================================

class TestStructureData_properties(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

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
    # test_valueToOptionalInt      force is False
    #=========================================================================================

    def test_valueToOptionalInt_Int(self):
        """
        Test that passing 42 (int) to valueToOptionalInt returns an int.
        """
        self.assertEqual(valueToOptionalInt(42), 42)

    def test_valueToOptionalInt_None(self):
        """
        Test that passing None to valueToOptionalInt returns None.
        """
        self.assertEqual(valueToOptionalInt(None), None)

    def test_valueToOptionalInt_NaN(self):
        """
        Test that passing NaN to valueToOptionalInt returns None.
        """
        self.assertEqual(valueToOptionalInt(float('NaN')), None)

    def test_valueToOptionalInt_IntFloat(self):
        """
        Test that passing int value float to valueToOptionalInt returns int.
        """
        vtoint = valueToOptionalInt(float(42.0))
        self.assertIsInstance(vtoint, int)

    def test_valueToOptionalInt_Float(self):
        """
        Test that passing float to valueToOptionalInt raises error.
        """
        with self.assertRaisesRegex(TypeError, 'does not correspond to an integer'):
            valueToOptionalInt(42.42)

    def test_valueToOptionalInt_String(self):
        """
        Test that passing string to valueToOptionalInt raises error.
        Can assume that all other non-number will raise error
        """
        with self.assertRaisesRegex(TypeError, 'does not correspond to an integer'):
            valueToOptionalInt('Invalid')

    #=========================================================================================
    # test_valueToOptionalType      force is True - overrides the error and returns None
    #=========================================================================================

    def test_valueToOptionalInt_forceInt(self):
        """
        Test that passing 42 (int) to valueToOptionalInt returns an int.
        """
        self.assertEqual(valueToOptionalInt(42, True), 42)

    def test_valueToOptionalInt_forceFloat(self):
        """
        Test that passing float to valueToOptionalInt returns None.
        """
        self.assertEqual(valueToOptionalInt(42.42, True), None)

    def test_valueToOptionalInt_forceFloatInt(self):
        """
        Test that passing int value float to valueToOptionalInt returns int.
        """
        self.assertEqual(valueToOptionalInt(float(42.0), True), 42)

    def test_valueToOptionalInt_forceString(self):
        """
        Test that passing string to valueToOptionalInt returns None.
        """
        self.assertEqual(valueToOptionalInt('Invalid', True), None)

    #=========================================================================================
    # test_valueToOptionalType      force is False
    #=========================================================================================

    def test_valueToOptionalType_None(self):
        """
        Test that passing None to valueToOptionalType returns None.
        """
        self.assertEqual(valueToOptionalType(None, int), None)

    def test_valueToOptionalType_Nan(self):
        """
        Test that passing NaN to valueToOptionalType returns None.
        """
        self.assertEqual(valueToOptionalType(float('NaN'), str), None)

    def test_valueToOptionalType_Int(self):
        """
        Test that passing 42 (int=int) to valueToOptionalType returns 42.
        """
        self.assertEqual(valueToOptionalType(42, int), 42)

    def test_valueToOptionalType_String(self):
        """
        Test that passing 42 (string=string) to valueToOptionalType returns 42.
        """
        self.assertEqual(valueToOptionalType('42', str), '42')

    def test_valueToOptionalType_ES(self):
        """
        Test that passing 42 (int<>float) to valueToOptionalType returns None.
        """
        with self.assertRaisesRegex(TypeError, 'does not correspond to type'):
            valueToOptionalType(42, float)

    #=========================================================================================
    # test_valueToOptionalType      force is True
    #=========================================================================================

    def test_valueToOptionalType_IntFloat(self):
        """
        Test that passing 42 (int<>float) to valueToOptionalType returns float.
        """
        self.assertEqual(valueToOptionalType(42, float, True), 42.0)

    def test_valueToOptionalType_IntString(self):
        """
        Test that passing 42 (int<>string) to valueToOptionalType returns string.
        """
        self.assertEqual(valueToOptionalType(42, str, True), '42')

    def test_valueToOptionalType_IntTuple(self):
        """
        Test that passing 42 (int<>tuple) to valueToOptionalType raises error.

        This is an expectedFailure needs to be expected type
        """
        with self.assertRaisesRegex(TypeError, 'does not correspond to type'):
            valueToOptionalType(42, tuple, True)


#=========================================================================================
# TestContainer
#=========================================================================================

class TestContainer(WrapperTesting):
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
            # self.newEnsemble = self.project.newStructureEnsemble()
            # self.newData = self.newEnsemble.data

            self.testAtomName = ['CA', 'C', 'N', 'O', 'H',
                                 'CB', 'HB1', ' HB2', 'HB3',
                                 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23',
                                 'CE', 'HE1', 'HE2', 'HE3',
                                 'CG', 'HG1', 'HG2', 'HG3',
                                 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
            self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + ['VAL'] * 8
            self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
            self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
            self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8

            self.data['atomName'] = self.testAtomName
            self.data['residueName'] = self.testResidueName
            self.data['chainCode'] = self.testChainCode
            self.data['sequenceId'] = self.testSequenceId
            self.data['modelNumber'] = self.testModelNumber

    #=========================================================================================
    # TestContainerTypes
    #=========================================================================================

    def testContainerTypes_tooManyEnsemble(self):
        """
        Test that an error raised of too many ensambleDatas are passed as argument
        :return:
        """
        self.newData = self.data.extract(index=range(4, 5))  # get the 4th-5th elements in list
        with self.assertRaisesRegex(ValueError, 'Only single row EnsembleDatas'):
            self.data.setValues(self.data)

    def testContainerTypes_SingleEnsemble_Proton(self):
        """
        Test that selecting a single item form the list with 'extract' can be
        used to set new values
        :return:
        """
        self.newData = self.data.extract(self.data.amideProtonSelector)  # get fifth element in list
        newDataTuples = self.newData.as_namedtuples()
        self.assertEqual(len(newDataTuples), 1)  # there should only be 1
        AtomRecord = newDataTuples[0].__class__
        self.assertEqual(newDataTuples[0], (AtomRecord(Index=5,
                                                       atomName='H',
                                                       residueName='ALA',
                                                       chainCode='A',
                                                       sequenceId=1,
                                                       modelNumber=1)))  # check found element is correct

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[4], (AtomRecord(Index=5,
                                                     atomName='H',
                                                     residueName='ALA',
                                                     chainCode='A',
                                                     sequenceId=1,
                                                     modelNumber=1)))  # check initial values
        self.data.setValues(self.newData,
                            atomName='HG23',
                            residueName='VAL',
                            chainCode='F',
                            sequenceId=6,
                            modelNumber=6)  # change the element
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[4], (AtomRecord(Index=5,
                                                     atomName='HG23',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6)))  # check set correctly

    def testContainerTypes_SingleEnsemble_Index(self):
        """
        Test that selecting a single item form the list with 'extract' can be
        used to set new values
        :return:
        """
        self.newData = self.data.extract(index=10)  # get fifth element in list
        newDataTuples = self.newData.as_namedtuples()
        self.assertEqual(len(newDataTuples), 1)  # there should only be 1
        AtomRecord = newDataTuples[0].__class__
        self.assertEqual(newDataTuples[0], (AtomRecord(Index=10,
                                                       atomName='CD1',
                                                       residueName='LEU',
                                                       chainCode='C',
                                                       sequenceId=3,
                                                       modelNumber=3)))  # check found element is correct

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[9], (AtomRecord(Index=10,
                                                     atomName='CD1',
                                                     residueName='LEU',
                                                     chainCode='C',
                                                     sequenceId=3,
                                                     modelNumber=3)))  # check initial values
        self.data.setValues(self.newData,
                            atomName='HG23',
                            residueName='VAL',
                            chainCode='F',
                            sequenceId=6,
                            modelNumber=6)  # change the element
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[9], (AtomRecord(Index=10,
                                                     atomName='HG23',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6)))  # check set correctly
        self.undo.undo()
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[9], (AtomRecord(Index=10,
                                                     atomName='CD1',
                                                     residueName='LEU',
                                                     chainCode='C',
                                                     sequenceId=3,
                                                     modelNumber=3)))  # check initial values
        self.undo.redo()
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[9], (AtomRecord(Index=10,
                                                     atomName='HG23',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6)))  # check set correctly

    def testContainerTypes_pdSeries(self):
        """
        Test that setValues with a pd.Series as an argument:
          raises error for nothing selected: AssertionError
          returns correctly with 1 item in the list selected
          raises an error for too may selected: AssertionError
          raises an error for out of range: AssertionError
          returns correctly for item in list even if selection is too long
        :return:
        """
        with self.assertRaisesRegex(ValueError, 'Boolean selector must select a single row'):
            self.data.setValues(pd.Series((False,) * 33, index=range(1, 34)))

        self.data.setValues(pd.Series((True,) + (False,) * 32, index=range(1, 34)))
        with self.assertRaisesRegex(ValueError, 'Attempt to set columns not present in DataFrame'):
            self.data.setValues(pd.Series(self.data.amideProtonSelector), badName=['badName'])

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[4], (AtomRecord(Index=5,
                                                     atomName='H',
                                                     residueName='ALA',
                                                     chainCode='A',
                                                     sequenceId=1,
                                                     modelNumber=1)))  # check initial values
        self.data.setValues(pd.Series(self.data.amideProtonSelector),
                            atomName='HG23',
                            residueName='VAL',
                            chainCode='F',
                            sequenceId=6,
                            modelNumber=6)  # change the element
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[4], (AtomRecord(Index=5,
                                                     atomName='HG23',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6)))  # check set correctly

        with self.assertRaisesRegex(ValueError, 'Boolean selector must select a single row'):
            self.data.setValues(self.data.methylSelector)

        with self.assertRaisesRegex(ValueError, 'Boolean selector must select an existing row'):
            self.data.setValues(pd.Series((False,) * 45 + (True,), index=range(1, 47)))

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[1], (AtomRecord(Index=2,
                                                     atomName='C',
                                                     residueName='ALA',
                                                     chainCode='A',
                                                     sequenceId=1,
                                                     modelNumber=1)))  # check initial values
        self.data.setValues(pd.Series((False,) + (True,) + (False,) * 44, index=range(1, 47)),
                            atomName='HG23',
                            residueName='VAL',
                            chainCode='F',
                            sequenceId=6,
                            modelNumber=6)  # change the element
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[1], (AtomRecord(Index=2,
                                                     atomName='HG23',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6)))  # check set correctly
        self.undo.undo()
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[1], (AtomRecord(Index=2,
                                                     atomName='C',
                                                     residueName='ALA',
                                                     chainCode='A',
                                                     sequenceId=1,
                                                     modelNumber=1)))  # check initial values
        self.undo.redo()
        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEqual(namedTuples[1], (AtomRecord(Index=2,
                                                     atomName='HG23',
                                                     residueName='VAL',
                                                     chainCode='F',
                                                     sequenceId=6,
                                                     modelNumber=6)))  # check set correctly

    def testContainerTypes_badType(self):
        """
        Test that setValues with a string raises TypeError
        :return:
        """
        with self.assertRaisesRegex(TypeError, 'accessor must be index, ensemble row, or selector'):
            self.data.setValues('badSetValue')

    #=========================================================================================
    # test_structureData_LastErrors
    #=========================================================================================

    def test_structureData_LastErrors(self):
        with self.assertRaisesRegex(ValueError, 'EnsembleData._containingObject'):
            self.data._containingObject = 'badObject'
