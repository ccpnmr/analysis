"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-03-20 19:06:25 +0000 (Wed, March 20, 2024) $"
__version__ = "$Revision: 3.2.2.1 $"
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
class IntegralListTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            self.spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H',), name='H1D-tst')
            self.integralList = self.spectrum.newIntegralList()

    def test_new1dIntegralList(self):
        self.assertEqual(len(self.spectrum.integralLists), 1)
        new_integralList = self.spectrum.newIntegralList(comment='test comment')

        self.assertIs(self.spectrum.integralLists[1], new_integralList)
        self.assertEqual(len(self.spectrum.integralLists), 2)

        self.assertEqual('test comment', new_integralList.comment)
        self.assertIn('IL', new_integralList.pid)
        self.assertEqual(new_integralList.className, 'IntegralList')


    def test_new1dIntegralList_UndoRedo(self):
        self.assertEqual(len(self.spectrum.integralLists), 1)
        self.undo.undo()
        self.assertEqual(len(self.spectrum.integralLists), 0)

        self.undo.redo()
        self.assertEqual(len(self.spectrum.integralLists), 1)
        self.assertIs(self.spectrum.integralLists[0], self.integralList)
