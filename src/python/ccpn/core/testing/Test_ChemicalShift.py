"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-10-20 17:42:33 +0100 (Mon, October 20, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from pandas.testing import assert_frame_equal
from traitlets import TraitError
from ccpn.core.testing.WrapperTesting import WrapperTesting, fixCheckAllValid


class ChemicalShiftTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'V3ProjectForTests.ccpn'

    def test_rename_list(self):
        # fix the bad structure for the test
        # new pdb loader does not load the into the data model so there are no atoms defined
        # the corresponding dataMatrices therefore have dimension set to zero which causes a crash :|
        fixCheckAllValid(self.project)

        self.project._wrappedData.root.checkAllValid(complete=True)

        shiftList = self.project.chemicalShiftLists[0]

        self.assertEqual(shiftList.pid, 'CL:default')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].pid, 'CS:default.20')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].nmrAtom.id, 'A.2.GLU.H')
        shiftList.rename('RenamedList')
        self.assertEqual(shiftList.pid, 'CL:RenamedList')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].pid, 'CS:RenamedList.20')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].nmrAtom.id, 'A.2.GLU.H')

        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(shiftList.pid, 'CL:default')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].pid, 'CS:default.20')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].nmrAtom.id, 'A.2.GLU.H')

        self.undo.redo()
        self.assertEqual(shiftList.pid, 'CL:RenamedList')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].pid, 'CS:RenamedList.20')
        self.assertEqual(sorted(shiftList.chemicalShifts)[20].nmrAtom.id, 'A.2.GLU.H')


class ChemicalShiftTestNew(WrapperTesting):

    def test_stuff(self):
        TESTNMRATOM = ('@-', '@1', None, '@_0')  # 'myNmrAtom')

        from ccpn.core.ChemicalShiftList import (CS_UNIQUEID, CS_ISDELETED, CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT,
                                                 CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME,
                                                 CS_SHIFTLISTPEAKS, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT,
                                                 CS_ALLPEAKSCOUNT,
                                                 CS_COMMENT, CS_OBJECT,
                                                 CS_COLUMNS, CS_TABLECOLUMNS, CS_CLASSNAME, CS_PLURALNAME)

        # from ccpn.core._implementation.DataFrameABC import DataFrameABC

        ch = self.project.chemicalShiftLists[0]
        # check that the dataframe is the correct type
        # self.assertTrue(isinstance(ch._wrappedData.data, (DataFrameABC, type(None))), 'must be of class DataFrameABC')

        if len(ch._shifts) == 0:
            for ii in range(5):
                ch.newChemicalShift()
            self.undo.undo()
            ch.newChemicalShift()

        if len(self.project.nmrAtoms) == 0:
            res = self.project.nmrChains[0].newNmrResidue()
            res.newNmrAtom()

        sh = ch._shifts[1]
        nmrAtom = self.project.nmrAtoms[0]

        sh.nmrAtom = None
        for atr in CS_COLUMNS:
            value = getattr(sh, atr)
            print(f'{atr}   {value}  {type(value)}')

        for atr in (CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT):
            with self.assertRaisesRegex(ValueError, '(-inf,inf)'):
                setattr(sh, atr, 'bad')

            # valid float, or None
            setattr(sh, atr, 0.75)
            setattr(sh, atr, None)

        # check figureOfMerit is valid
        with self.assertRaisesRegex(ValueError, 'must be in range'):
            setattr(sh, CS_FIGUREOFMERIT, -0.1)
        with self.assertRaisesRegex(ValueError, 'must be in range'):
            setattr(sh, CS_FIGUREOFMERIT, 1.1)

        sh.nmrAtom = None

        self.assertEqual(sh.nmrAtom, None)
        for atr in (CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME):
            self.assertEqual(getattr(sh, atr), None)

        sh.nmrAtom = nmrAtom
        self.assertEqual(sh.nmrAtom, nmrAtom)
        for atr, val in zip((CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME), TESTNMRATOM):
            self.assertEqual(getattr(sh, atr), val)

        self.undo.undo()
        self.assertEqual(sh.nmrAtom, None)
        for atr in (CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME):
            self.assertEqual(getattr(sh, atr), None)

        self.undo.redo()
        self.assertEqual(sh.nmrAtom, nmrAtom)
        for atr, val in zip((CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME), TESTNMRATOM):
            self.assertEqual(getattr(sh, atr), val)

        sh.nmrAtom = None
        sh.nmrAtom = nmrAtom.pid
        self.assertEqual(sh.nmrAtom, nmrAtom)
        self.undo.undo()
        self.assertEqual(sh.nmrAtom, None)
        self.undo.redo()
        self.assertEqual(sh.nmrAtom, nmrAtom)

        with self.assertRaises(ValueError) as e:
            sh.nmrAtom = 42

        # with self.assertRaisesRegex(ValueError, 'must be of type NmrAtom'):
        #     sh.nmrAtom = 42

        for atr in (CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME):
            with self.assertRaisesRegex(ValueError, 'instance expected a unicode string'):
                setattr(sh, atr, 42)
            if getattr(sh, atr, '_Undefined_') != None:
                # setters are skipped of the value hasn't changed; hence no raised error
                with self.assertRaisesRegex((RuntimeError, ValueError),
                                        'derived value, cannot modify when nmrAtom is set'):
                    setattr(sh, atr, None)

        # for atr in (CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME):
        #     setattr(sh, atr, None)

        # sh.nmrAtom = nmrAtom.pid

        # check again to make sure that the class has not changed
        # self.assertTrue(isinstance(ch._wrappedData.data, (DataFrameABC, type(None))), 'must be of class DataFrameABC')


# ---- column constants ----
CS_UNIQUEID = 'uniqueId'
CS_NMRATOM = 'nmrAtom'
CS_ISDELETED = 'isDeleted'
CS_STATIC = 'static'
CS_COLUMNS = [CS_UNIQUEID, CS_NMRATOM, CS_ISDELETED, 'value']  # example schema

class ChemicalShiftDuplicates(WrapperTesting):

    def test_pandas_duplicates(self):
        import pandas as pd
        import numpy as np


        # ---- sample DataFrame with duplicates + nulls + a deleted row ----
        data = pd.DataFrame([
            # uniqueId, nmrAtom, isDeleted, value
            [1, "Atom6", False, 'a'],  # dup group "101" (first)
            [2, "Atom6", False, 'b'],  # dup group "101" (second) -> should be dropped if keep='first'
            [3, "Atom6", False, 'c'],  # dup group "101" (second) -> should be dropped if keep='first'
            [4, "Atom23", False, 'd'],  # unique, keep
            [5, None, False, 'e'],  # null, keep
            [6, None, False, 'f'],  # null, keep
            [7, "Atom19", np.nan, 'g'],  # bad, should be removed before de-dup
            [8, "Atom12", False, 'h'],  # unique, keep
            [9, None, False, 'i'],  # unique, keep
            [10, "Atom2", True, 'j'],  # deleted, should be removed before de-dup
            ], columns=CS_COLUMNS)

        print("Input:")
        print(data)

        # ---- simulate your pipeline ----
        # remove deleted shifts
        _data = data.copy()

        _data = (_data
                 .loc[~_data[CS_ISDELETED].fillna(True)]
                 .reset_index(drop=True))  #.copy()
        oldLen = len(_data)
        oldLen2 = 0
        oldIndex = None

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # de-duplicate by CS_NMRATOM (keep first) + keep all nulls
        non_nas = (_data
                   .dropna(subset=[CS_NMRATOM])
                   .drop_duplicates(subset=[CS_NMRATOM], keep='first')
                   )
        nas = _data[_data[CS_NMRATOM].isna()]
        new_df = pd.concat([non_nas, nas], axis=0, copy=False)
        new_df.sort_values(CS_UNIQUEID, inplace=True)

        print("\nAfter de-dup (keep='first') + keep all nulls:")
        print(new_df)

        dropped_idx = _data.index.difference(new_df.index)
        dropped_uids = list(_data.loc[dropped_idx, CS_UNIQUEID])
        new_df.set_index(CS_UNIQUEID, drop=False, inplace=True)

        print("\nDupes")
        print(dropped_uids)
        self.checkDf(new_df, data)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        def _df_len(df):
            nonlocal oldLen2
            oldLen2 = len(df)
            oldIndex = df.index.copy()
            return df

        new_df_pipe = (
            _data
            .loc[~_data[CS_ISDELETED].fillna(True)]
            .pipe(lambda d: _df_len(d))
            .pipe(lambda d: pd.concat([(d
                                        .dropna(subset=[CS_NMRATOM])
                                        .drop_duplicates(subset=[CS_NMRATOM], keep='first')
                                        ),
                                       d[d[CS_NMRATOM].isna()]
                                       ], axis=0, copy=False))
            .sort_values(CS_UNIQUEID)
            # .set_index(CS_UNIQUEID, drop=False)  # dropped_idx must be captured before this
        )

        print("\nAfter de-dup (keep='first') + keep all nulls:")
        print(new_df_pipe)

        dropped_idx = _data.index.difference(new_df_pipe.index)
        dropped_uids = list(_data.loc[dropped_idx, CS_UNIQUEID])
        new_df_pipe.set_index(CS_UNIQUEID, drop=False, inplace=True)

        print("\nDupes")
        print(dropped_uids)
        self.checkDf(new_df_pipe, data)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        _data_orig = data.copy()
        _data_orig = _data_orig[_data_orig[CS_ISDELETED] == False]
        _data_orig.reset_index(drop=True, inplace=True)

        new_df_orig = (_data_orig
                         .drop_duplicates(CS_NMRATOM)
                         .merge(_data_orig[_data_orig[CS_NMRATOM].isna()],
                                how='outer')
                         )
        new_df_orig.sort_values(CS_UNIQUEID, inplace=True)
        new_df_orig.set_index(CS_UNIQUEID, drop=False, inplace=True)

        print("\nOriginal")
        print(new_df_orig)
        print(oldLen, oldLen2)
        self.checkDf(new_df_orig, data)

        assert_frame_equal(new_df, new_df_pipe)
        assert_frame_equal(new_df, new_df_orig)

    @staticmethod
    def checkDf(df_in: pd.DataFrame, source: pd.DataFrame):
        expected_uids = [1, 4, 5, 6, 8, 9]
        assert df_in[CS_UNIQUEID].tolist() == expected_uids
        print(df_in[CS_NMRATOM].isna().sum())
        print(source[CS_NMRATOM].duplicated().sum())
        assert df_in[CS_NMRATOM].isna().sum() == 3  # both null rows kept
        assert source[CS_NMRATOM].duplicated().sum() == 4  # original had one duplicate among non-nulls
