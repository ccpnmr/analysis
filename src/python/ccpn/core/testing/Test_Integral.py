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

import unittest
import numpy as np
from ccpn.core.testing.WrapperTesting import WrapperTesting, getProperties


def id_undo_redo(obj, undo_obj):
    """tests undo redo functionality by comparing change in object representations/PIDs"""
    undo_obj_id = repr(undo_obj)
    obj.undo.undo()
    # check repr change ('deleted' included on end)
    obj.assertNotEqual(undo_obj_id, repr(undo_obj))
    obj.undo.redo()
    # repr should revert to original (no 'deleted' on end)
    obj.assertEqual(undo_obj_id, repr(undo_obj))


def granular_dict_undo_redo(obj, instance, p_dict):
    """tests undo redo functionality for granular addition of attributes to an object"""
    for key, val in reversed(p_dict.items()):
        obj.undo.undo()
        obj.assertNotEqual(getattr(instance, key), val)
    for key, val in p_dict.items():
        obj.undo.redo()
        obj.assertEqual(getattr(instance, key), val)


class IntegralListTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):
        with self.initialSetup():
            self.params = dict(value=99.,
                               valueError=1.,
                               annotation='Why Bother?',
                               comment='really!',
                               figureOfMerit=0.92,
                               bias=7.0,
                               slopes=[0.3, 0.9],
                               limits=((1.0, 2.0), (21.0, 22.0)))
            # work around for WrapperTesting getProperties stringifying
            self.param_str = {key: str(val) for key, val in self.params.items()}

            self.spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H', '13C'), name='HSQC-tst')
            self.integralList = self.spectrum.newIntegralList(title='Int2d', comment='No!')

    def test_2dIntegralIterativeAddParam(self):
        # Undo and redo all operations
        undo_il_id = repr(self.integralList)
        self.undo.undo()
        self.assertNotEqual(undo_il_id, repr(self.integralList))
        self.undo.redo()
        self.assertEqual(undo_il_id, repr(self.integralList))

        integral = self.integralList.newIntegral()
        for key, val in self.params.items():
            setattr(integral, key, val)

        # check all properties are in integral instance
        i_vals = getProperties(integral)
        self.assertEqual(i_vals, i_vals | self.param_str)

        # Undo and redo all operations
        granular_dict_undo_redo(self, integral, self.params)
        self.assertEqual(i_vals, i_vals | self.param_str)

    @unittest.skip('fails with bias ')
    def test_2dIntegralKwargsAddParam(self):
        integral = self.integralList.newIntegral(**self.params)
        i_vals = getProperties(integral)
        print(i_vals['bias'], self.param_str['bias'])
        self.assertEqual(i_vals, i_vals | self.param_str)

        # Undo and redo all operations
        id_undo_redo(self, integral)
        self.assertEqual(i_vals, i_vals | self.param_str)

    def test_2dIntegralInitAddParam(self):
        init_params = {'value': '99.0', 'pointLimits': '((1, 2), (21, 22))'}
        integral = self.integralList.newIntegral(value=99., pointLimits=((1, 2), (21, 22)))
        i_vals = getProperties(integral)
        self.assertEqual(i_vals, i_vals | init_params)

        # Undo and redo all operations
        id_undo_redo(self, integral)

    def test_2dIntegralPropertyChangeParam(self):
        delta_params = {'value': None, 'valueError': None, 'annotation': None, 'comment': None}
        integral = self.integralList.newIntegral(**self.params)
        for key, val in delta_params.items():
            setattr(integral, key, val)

    def test_2dIntegralNaNOrInfinity(self):
        test_params = ({'value': float('NaN'), 'valueError': float('NaN'), 'bias': float('NaN')},
                       {'value': float('inf'), 'valueError': float('inf'), 'bias': float('inf')})

        integral = self.integralList.newIntegral(**self.params)
        for test in test_params:
            for key, val, in test.items():
                with self.assertRaises(TypeError) as cm:
                    setattr(integral, key, val)
                err = cm.exception
                self.assertEqual(str(err), f'{key} cannot be NaN or Infinity')

    def test_1dIntegral(self):
        spectrum = self.project.newEmptySpectrum(isotopeCodes=('1H',), name='H1D-tst')
        # set some dummy information on the 1D spectrum
        spectrum.positions = np.arange(0, 10, 1, dtype=np.float32)
        spectrum.intensities = np.linspace(0, .9, 10, dtype=np.float32)

        self.integralList = spectrum.newIntegralList()

        # Undo redo operations for integral creation on 1d

        integral1 = self.integralList.newIntegral()
        id_undo_redo(self, integral1)

        integral2 = self.integralList.newIntegral(value=99., valueError=1., bias=7, slopes=(0.9,),
                                                  figureOfMerit=0.92, annotation='Why Bother?',
                                                  comment='really!', limits=((1, 2),))
        id_undo_redo(self, integral2)

        integral3 = self.integralList.newIntegral(value=99., pointLimits=((21, 23),))
        id_undo_redo(self, integral3)
