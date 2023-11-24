"""Module Documentation here

"""
# =========================================================================================
# Licence, Reference and Credits
# =========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
# =========================================================================================
# Last code modification
# =========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-04-14 19:56:58 +0100 (Wed, April 14, 2021) $"
__version__ = "$Revision: 3.0.3 $"
# =========================================================================================
# Created
# =========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"

import unittest

# =========================================================================================
# Start of code
# =========================================================================================

import numpy as np
from ccpn.core.testing.WrapperTesting import WrapperTesting


# Only testing 1D Integral lists for the time being. Still need to decide on the fate of ND ones
class MultipletListTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N'))
            self.multipletList = self.spectrum.newMultipletList()

    def test_newMultipletList(self):
        self.assertEqual(len(self.spectrum.multipletLists), 0)

        new_multipletList = self.spectrum.newMultipletList()

        self.assertEqual(len(self.spectrum.multipletLists), 1)
        self.assertEqual(new_multipletList.className, 'MultipletList')
        self.assertIs(self.spectrum.multipletLists[0], new_multipletList)

    def test_multipletAveraging_set(self):
        self.multipletList.multipletAveraging='Weighted Average'
        self.assertEqual(self.multipletList.multipletAveraging, 'Weighted Average')
        self.multipletList.multipletAveraging='Average'
        self.assertEqual(self.multipletList.multipletAveraging, 'Average')

        # undo redo all operations
        self.undo.undo()
        self.assertEqual(self.multipletList.multipletAveraging, 'Weighted Average')
        self.undo.redo()
        self.assertEqual(self.multipletList.multipletAveraging, 'Average')

    def test_multipletAveraging_set_errors(self):
        with self.assertRaises(ValueError) as cm:
            self.multipletList.multipletAveraging = 'Wrong Code'
        err = cm.exception
        self.assertEqual(str(err), f'multipletAveraging Wrong Code not defined correctly,'
                                   f' must be in [\'Average\', \'Weighted Average\']')
        with self.assertRaises(ValueError) as cm:
            self.multipletList.multipletAveraging = 42
        err = cm.exception
        self.assertEqual(str(err), 'multipletAveraging must be a string')

    def test_newMultipletList_UndoRedo(self):
        self.assertEqual(len(self.spectrum.multipletLists), 1)

        self.undo.undo()
        self.assertEqual(len(self.spectrum.multipletLists), 0)
        self.assertIn('Deleted', repr(self.multipletList))

        self.undo.redo()
        self.assertEqual(len(self.spectrum.multipletLists), 1)
        self.assertNotIn('Deleted', repr(self.multipletList))
        self.assertIs(self.spectrum.multipletLists[0], self.multipletList)
