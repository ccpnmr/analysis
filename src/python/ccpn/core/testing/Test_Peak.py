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
__modifiedBy__ = "$modifiedBy: Daniel Thompson $"
__dateModified__ = "$dateModified: 2023-11-30 17:14:18 +0000 (Thu, November 30, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

import unittest

import pandas as pd
from collections.abc import Iterable
from ccpn.core.lib.AxisCodeLib import axisCodeMatch
from ccpn.core.testing.WrapperTesting import WrapperTesting, fixCheckAllValid, getProperties


class PeakTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'V3ProjectForTests.ccpn'

    singleValueTags = ['height', 'volume', 'heightError', 'volumeError', 'figureOfMerit',
                       'annotation', 'comment']
    dimensionValueTags = ['ppmPositions', 'positionError', 'boxWidths', 'lineWidths', 'assignedNmrAtoms']

    # NBNB TODO We still need a case where axisCodes are not in the same order (e.g. HNC<->HCN)

    def test_Peak_copy_exo_1(self):
        peakList1 = self.project.getPeakList('15NNoesy_182.1')
        peak1 = peakList1.getPeak(2)
        peak2 = peak1.copyTo(peakList1)

        # fix the bad structure for the test
        # new pdb loader does not load the into the data model so there are no atoms defined
        # the corresponding dataMatrices therefore have dimension set to zero which causes a crash :|
        fixCheckAllValid(self.project)

        self.project._wrappedData.root.checkAllValid(complete=True)

        self.assertIs(peak1._parent, peakList1)
        self.assertIs(peak2._parent, peakList1)

        tags = self.singleValueTags + self.dimensionValueTags

        for tag in tags:
            self.assertEqual((tag, getattr(peak1, tag)), (tag, getattr(peak2, tag)))
        self.assertEqual(('serial', peak2.serial), ('serial', 11))

    @unittest.skip("ISSUE: doesn't copy the serial number during peak copy to other list")
    def test_Peak_copy_exo_2(self):
        peakList1 = self.project.getPeakList('15NNoesy_182.1')
        peakList2 = self.project.getPeakList('15NTocsy_181.1')
        peak1 = peakList1.getPeak(2)
        peak3 = peak1.copyTo(peakList2)

        tags = self.singleValueTags + self.dimensionValueTags

        self.assertIs(peak1._parent, peakList1)
        self.assertIs(peak3._parent, peakList2)

        for tag in tags:
            self.assertEqual((tag, getattr(peak1, tag)), (tag, getattr(peak3, tag)))
        # self.assertEqual(('serial', peak1.serial), ('serial', peak3.serial))

    def test_assignPeak(self):
        self.spectrum = self.project.getSpectrum('hsqc_115')
        self.shiftList = self.project.newChemicalShiftList()
        self.spectrum.chemicalShiftList = self.shiftList
        self.nmrResidue = self.project.nmrChains[0].fetchNmrResidue()
        self.nmrAtom = self.nmrResidue.fetchNmrAtom(name='N')
        self.peak = self.spectrum.peakLists[0].peaks[0]
        self.peak.assignDimension(axisCode=axisCodeMatch('N', self.spectrum.axisCodes),
                                  value=self.nmrAtom)

        shift = self.shiftList.getChemicalShift(self.nmrAtom)

        self.assertTrue(shift is not None)
        self.assertTrue(shift.value is not None)

        # Undo and redo all operations
        self.assertNotIn('Deleted', repr(shift))
        self.undo.undo()
        self.assertIn('Deleted', repr(shift))
        self.undo.redo()
        self.assertNotIn('Deleted', repr(shift))

    def test_getAsDataFrame(self):
        """Tests the values put into a data frame using the getAsDataFrame() method
        Comparisons are made between the objects properties and the values inside
        the data frame - a faster version simply compares a dataframe to an expected
        string this is a more generalized solution.
        """

        # Changing this allows you to easily see on the commandline
        # what will is being tested
        verbose = False


        peakList1 = self.project.getPeakList('15NNoesy_182.1')
        peak1 = peakList1.getPeak(2)
        params = peak1.getAsDict()

        # filter out the parameters that are not converted into the data frame
        param_filter = ['positionError', 'volumeError', 'spectrum', 'project', 'peakList',
                        'integral', 'heightError', 'clusterId', 'collections',
                        'chemicalShiftList', 'boxWidths', 'assignedNmrAtoms',
                        'dimensionNmrAtoms', 'assignmentsByDimensions', 'annotation']

        params_dict = {key: value for key, value in params.items() if key not in param_filter}

        df = peak1.getAsDataFrame()
        self.assertIsInstance(df, pd.DataFrame)

        for key, value in params_dict.items():
            if value is not None and isinstance(value, Iterable) and not isinstance(value, str):
                for i, list_val in enumerate(value):
                    # separate out assignments
                    if key is 'assignments':
                        for a_i, a_val in enumerate(list_val):
                            if a_val is None:
                                if verbose: print(f'Assign_F{a_i + 1}', '')
                                self.assertEqual('', df.loc[2, f'Assign_F{a_i + 1}'])
                            else:
                                if verbose: print(f'Assign_F{a_i + 1}', a_val)
                                self.assertEqual(str(a_val)[1:-1], df.loc[2, f'Assign_F{a_i + 1}'])
                    else:
                        if key.endswith('s'):
                            if verbose: print(f"{key[:-1]}_F{i + 1}", value[i])
                            self.assertEqual(value[i], df.loc[2, f"{key[:-1]}_F{i + 1}"])
                        else:
                            if verbose: print(f"{key}_F{i + 1}", value[i])
                            self.assertEqual(value[i], df.loc[2, f"{key}_F{i + 1}"])
            else:
                if verbose: print(key, value)
                self.assertEqual(value, df.loc[2, key])

    @unittest.skip("A faster (but worse) version of the getDataFrame() test")
    def test_getDataFrame_fast(self):

        # NOTE: this isn't a great way of testing as it was created implying the function
        # worked when the test was made (and that the format of the data frame will
        # remain unchanged), however a more comprehensive option would require a lot
        # more work for now some semi-random value tests thrown in at end.

        peakList1 = self.project.getPeakList('15NNoesy_182.1')
        peak1 = peakList1.getPeak(2)
        params = peak1.getAsDict()

        df_string = ('                                        2\n'
                     'Assign_F1                    NA:A.4.THR.H\n'
                     'Assign_F2                                \n'
                     'Assign_F3                    NA:A.4.THR.N\n'
                     'aliasing_F1                           0.0\n'
                     'aliasing_F2                           0.0\n'
                     'aliasing_F3                           0.0\n'
                     'axisCode_F1                             H\n'
                     'axisCode_F2                            H1\n'
                     'axisCode_F3                             N\n'
                     'className                            Peak\n'
                     'comment                                  \n'
                     'figureOfMerit                         1.0\n'
                     'height                          5705718.0\n'
                     'id                       15NNoesy_182.1.2\n'
                     'isDeleted                           False\n'
                     'lineWidth_F1                     27.23871\n'
                     'lineWidth_F2                    63.495101\n'
                     'lineWidth_F3                    39.412925\n'
                     'longPid             Peak:15NNoesy_182.1.2\n'
                     'pid                   PK:15NNoesy_182.1.2\n'
                     'pointLineWidth_F1                5.578488\n'
                     'pointLineWidth_F2                2.958364\n'
                     'pointLineWidth_F3                2.074141\n'
                     'pointPosition_F1                55.324882\n'
                     'pointPosition_F2               144.023302\n'
                     'pointPosition_F3                26.943757\n'
                     'position_F1                      9.368322\n'
                     'position_F2                       4.25528\n'
                     'position_F3                    118.271366\n'
                     'ppmLineWidth_F1                  27.23871\n'
                     'ppmLineWidth_F2                 63.495101\n'
                     'ppmLineWidth_F3                 39.412925\n'
                     'ppmPosition_F1                   9.368322\n'
                     'ppmPosition_F2                    4.25528\n'
                     'ppmPosition_F3                 118.271366\n'
                     'serial                                2.0\n'
                     'shortClassName                         PK\n'
                     'signalToNoiseRatio              70.512341\n'
                     'volume                 443456823755.64563')

        df = peak1.getAsDataFrame()
        self.assertIsInstance(df, pd.DataFrame)

        self.assertEqual(df.T.to_string(), df_string)  # transposed dataframe for earlier string formatting.

        # selected tests (1 nmrAtom and 1 property)
        self.assertTrue(df.loc[2, 'Assign_F1'] in str(peak1.assignmentsByDimensions[0]))
        self.assertEqual(df.loc[2, 'volume'], params['volume'])

    def test_fit(self):
        peak_list = self.project.getPeakList('15NNoesy_182.1')
        peak = peak_list.getPeak(2)

        start_pos, prev_height = peak.position, peak.height

        peak.fit(keepPosition=True, iterations=10)
        self.assertNotEqual(prev_height, peak.height)
        self.assertEqual(start_pos, peak.position)

        peak.fit(keepPosition=False, iterations=3)
        self.assertNotEqual(start_pos, peak.position)
        prev_pos, prev_lw = peak.position, peak.lineWidths

        peak.fit(fitMethod='lorentzian', keepPosition=True, iterations=5)
        self.assertNotEqual(prev_lw, peak.lineWidths)
        self.assertEqual(prev_pos, peak.position)

        # undo redo all operations
        self.undo.undo()
        self.assertEqual(prev_lw, peak.lineWidths)
        self.undo.undo()
        self.assertEqual(start_pos, peak.position)
        self.undo.redo()
        self.assertEqual(prev_lw, peak.lineWidths)
        self.undo.redo()
        self.assertNotEqual(prev_lw, peak.lineWidths)

    def test_delete(self):
        peak_list = self.project.getPeakList('15NNoesy_182.1')
        peak1 = peak_list.getPeak(1)
        peak2 = peak_list.getPeak(2)
        peak3 = peak_list.getPeak(3)

        peak1.delete()
        self.assertIn('Deleted', repr(peak1))
        peak2.delete()
        self.assertIn('Deleted', repr(peak2))
        peak3.delete()
        self.assertIn('Deleted', repr(peak3))

        # undo redo all operations
        self.undo.undo()
        self.assertNotIn('Deleted', repr(peak3))
        # self.assertIn('Deleted', repr(peak2))
        # self.assertIn('Deleted', repr(peak1))

        self.undo.undo()
        self.assertNotIn('Deleted', repr(peak2))
        # self.assertNotIn('Deleted', repr(peak3))
        # self.assertIn('Deleted', repr(peak1))

        self.undo.undo()
        self.assertNotIn('Deleted', repr(peak1))
        # self.assertNotIn('Deleted', repr(peak3))
        # self.assertNotIn('Deleted', repr(peak2))

        self.undo.redo()
        self.assertIn('Deleted', repr(peak1))
        # self.assertNotIn('Deleted', repr(peak3))
        # self.assertNotIn('Deleted', repr(peak2))

        self.undo.redo()
        self.assertIn('Deleted', repr(peak2))
        # self.assertIn('Deleted', repr(peak1))
        # self.assertNotIn('Deleted', repr(peak3))

        self.undo.redo()
        self.assertIn('Deleted', repr(peak3))
        self.assertIn('Deleted', repr(peak2))
        self.assertIn('Deleted', repr(peak1))
