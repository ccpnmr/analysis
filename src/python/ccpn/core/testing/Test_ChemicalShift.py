"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-01 11:20:56 +0000 (Mon, November 01, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

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

        from ccpn.core.ChemicalShiftList import CS_UNIQUEID, CS_ISDELETED, CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT, \
            CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME, \
            CS_SHIFTLISTPEAKS, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT, \
            CS_COMMENT, CS_OBJECT, \
            CS_COLUMNS, CS_TABLECOLUMNS, CS_CLASSNAME, CS_PLURALNAME
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
            with self.assertRaisesRegex(ValueError, 'must be of type float, int or None'):
                setattr(sh, atr, 'bad')
            # ints now allowed
            # with self.assertRaisesRegex(ValueError, 'must be of type float, int or None'):
            #     setattr(sh, atr, 1)

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

        with self.assertRaisesRegex(ValueError, 'must be of type NmrAtom'):
            sh.nmrAtom = 42
        for atr in (CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME):
            with self.assertRaisesRegex(ValueError, 'must be of type str or None'):
                setattr(sh, atr, 42)
            with self.assertRaisesRegex(RuntimeError, 'cannot modify'):
                setattr(sh, atr, None)

        for atr in (CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME):
            setattr(sh, atr, None)

        sh.nmrAtom = nmrAtom.pid

        # check again to make sure that the class has not changed
        # self.assertTrue(isinstance(ch._wrappedData.data, (DataFrameABC, type(None))), 'must be of class DataFrameABC')
