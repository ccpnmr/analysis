"""Module Documentation here

"""
# =========================================================================================
# Licence, Reference and Credits
# =========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
# =========================================================================================
# Last code modification
# =========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-08-20 22:18:49 +0100 (Fri, August 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
# =========================================================================================
# Created
# =========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"

# =========================================================================================
# Start of code
# =========================================================================================

import pytest
import numpy as np
from ccpn.core.testing.WrapperTesting import WrapperTesting


class IntegralListTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            self.params1 = dict(value=99.,
                                valueError=1.,
                                annotation='Why Bother?',
                                comment='really!')
            self.params2 = dict(figureOfMerit=0.92,
                                bias=7,
                                slopes=[0.3, 0.9],
                                limits=((1, 2), (21, 22)))
            self.params = self.params1.copy()
            self.params.update(self.params2)

            self.spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H', '13C'), name='HSQC-tst')

    def test_2dIntegral(self):

        integralList = self.spectrum.newIntegralList(title='Int2d', comment='No!')
        undo_il_id = repr(integralList)
        self.undo.undo()
        self.assertNotEqual(undo_il_id, repr(integralList))
        self.undo.redo()
        self.assertEqual(undo_il_id, repr(integralList))

        integral1 = integralList.newIntegral()
        # print("\n")
        for key, val in self.params.items():
            setattr(integral1, key, val)
            # print(key, val)
        # print("\n")

        # test attributes are added
        # would rather have done the bellow but doesnt access all variables(?)
        # self.assertEqual(vars(integral1), vars(integral1) | params)
        for key, val in self.params.items():
            self.assertEqual(val, getattr(integral1, key))

        self.undo.undo()

        # # self.undo.undo()
        # # self.undo.undo()
        # # self.undo.undo()
        # # print(integral1)
        # # for key, val in params.items():
        # #     print(key, getattr(integral1, key))
        #
        # self.undo.redo()

        # # ======================== UNDO REDO TEMP ============================= #
        #
        # # undo redo test for block undo redo
        # self.undo.undo()
        # for key, val in params.items():
        #     self.assertNotEqual(getattr(integral1, key), val)
        # self.undo.redo()
        #
        # # ============================== OR =================================== #
        # # undo redo test for granular undo redo
        #
        # for key, val in reversed(params.items()):
        #     self.undo.undo()
        #     self.assertNotEqual(getattr(integral1, key), val)
        #
        # for key, val in params.items():
        #     self.undo.redo()
        #     self.assertEqual(getattr(integral1, key), val)
        # # ==================================================================== #

        integral2 = integralList.newIntegral(**self.params)
        integral3 = integralList.newIntegral(value=99., pointLimits=((1, 2), (21, 22)))
        for key in self.params1:
            setattr(integral2, key, None)
        integral2.limits = ((None, None), (None, None))
        integral2.bias = 0
        integral2.figureOfMerit = 0
        integral2.slopes = (0.0, 0.0)
        # Undo and redo all operations

        self.undo.undo()
        self.undo.redo()

    def test_1dIntegral(self):
        spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H',), name='H1D-tst')
        # set some dummy information on the 1D spectrum
        spectrum.positions = np.arange(0, 10, 1, dtype=np.float32)
        spectrum.intensities = np.linspace(0, .9, 10, dtype=np.float32)

        integralList = spectrum.newIntegralList()
        integral1 = integralList.newIntegral()
        integral2 = integralList.newIntegral(value=99., valueError=1., bias=7, slopes=(0.9,),
                                             figureOfMerit=0.92, annotation='Why Bother?',
                                             comment='really!', limits=((1, 2),))
        integral3 = integralList.newIntegral(value=99., pointLimits=((21, 23),))
        # Undo and redo all operations

        self.undo.undo()
        self.undo.redo()
