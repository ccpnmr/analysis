"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-04-14 19:56:58 +0100 (Wed, April 14, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.core.testing.WrapperTesting import WrapperTesting

#Only testing 1D Integral lists for the time being. Still need to decide on the fate of ND ones
class MultipletListTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H', '15N'))
    def test_newMultipletList(self):
        self.assertEqual(len(self.spectrum.multipletLists), 0)

        multipletList = self.spectrum.newMultipletList()

        self.assertEqual(len(self.spectrum.multipletLists), 1)
        self.assertEqual(multipletList.className, 'MultipletList')
        self.assertIs(self.spectrum.multipletLists[0], multipletList)

    def test_newMultipletList_UndoRedo(self):
        multipletList = self.spectrum.newMultipletList()

        self.assertEqual(len(self.spectrum.multipletLists), 1)
        self.undo.undo()
        self.assertEqual(len(self.spectrum.multipletLists), 0)

        self.undo.redo()
        self.assertEqual(len(self.spectrum.multipletLists), 1)
        self.assertIs(self.spectrum.multipletLists[0], multipletList)
