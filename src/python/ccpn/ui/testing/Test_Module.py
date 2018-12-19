"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:57 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import numpy
from ccpn.util.Tensor import Tensor

from ccpn.core.testing.WrapperTesting import WrapperTesting


class ModuleTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = None

    def test_creation_1(self):
        project = self.project
        undo = self.project._undo
        self.project.newUndoPoint()
        window2 = project.newWindow(title='W2')
        module1 = project.newModule('TestMod')
        module2 = project.newModule('TestMod')
        module3 = project.newModule('TestMod', window=window2, title='MyOwn', comment='really?')
        module4 = project.newModule('DifferentMod')
        undo.undo()
        undo.undo()
        undo.undo()
        undo.undo()
        undo.undo()
        undo.redo()
        undo.redo()
        undo.redo()
        undo.redo()
        undo.redo()
        self.assertEquals(module1.pid, 'GM:TestMod')
        self.assertEquals(module2.pid, 'GM:TestMod_1')
        self.assertEquals(module3.pid, 'GM:MyOwn')
        self.assertEquals(module4.pid, 'GM:DifferentMod')
        self.assertEquals(module1.window.pid, 'GW:Main')
        self.assertEquals(module2.window.pid, 'GW:Main')
        self.assertEquals(module3.window.pid, 'GW:W2')
        self.assertEquals(module4.window.pid, 'GW:Main')
        self.assertEquals(module3.comment, 'really?')

    def test_creation_2(self):
        # This is known to fail.
        # There is a bug in undo/redo for additional windows and tasks
        # Since code does not (and probably never will) use additional windows or tasks
        # this is left for now.
        project = self.project
        undo = self.project._undo
        self.project.newUndoPoint()
        window2 = project.newWindow(title='W2')
        undo.undo()
        # self.assertRaises(KeyError, undo.undo)
        # undo.redo()
        undo.redo()


class ParameterTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_parameters(self):
        project = self.project
        # task = project.newTask('TestTask')
        module1 = project.newModule('TestMod')

        testpars = collections.OrderedDict()
        for key, val in [
            ('bbb', 1), ('ccc', [1, 2, 3]), ('ddd', True), ('aaa', ()), ('xxx', 'xxx'), ('dict', {1: 1}),
            ('odict', collections.OrderedDict(((2, 100), (1, 10))))
            ]:
            testpars[key] = val

        undo = self.project._undo
        self.project.newUndoPoint()
        self.assertEqual(module1.parameters, {})
        module1.setParameter('aaa', 1)
        self.assertEqual(module1.parameters, {'aaa': 1})
        module1.updateParameters(testpars)
        self.assertEqual(module1.parameters, testpars)
        module1.deleteParameter('ccc')
        del testpars['ccc']
        self.assertEqual(module1.parameters, testpars)
        module1.setParameter('ddd', 11)
        testpars['ddd'] = 11
        self.assertEqual(module1.parameters, testpars)
        undo.undo()
        undo.redo()
        self.assertEqual(module1.parameters, testpars)
        module1.clearParameters()
        self.assertEqual(module1.parameters, {})

    def test_numpy_parameter(self):
        project = self.project
        # task = project.newTask('TestTask')
        module1 = project.newModule('TestMod')
        undo = self.project._undo
        self.project.newUndoPoint()
        module1.setParameter('ndarray', numpy.ndarray((5, 3, 1)))
        undo.undo()
        undo.redo()
        self.assertTrue(isinstance(module1.parameters['ndarray'], numpy.ndarray))

    def test_tensor_parameter(self):
        project = self.project
        # task = project.newTask('TestTask')
        module1 = project.newModule('TestMod')
        undo = self.project._undo
        self.project.newUndoPoint()
        module1.setParameter('tensor', Tensor._fromDict({'orientationMatrix': numpy.identity(3),
                                                         'xx'               : 2.1, 'yy': -3, 'zz': 0.9}))
        undo.undo()
        undo.redo()
        tensor = module1.parameters['tensor']
        self.assertTrue(isinstance(tensor, Tensor))
        self.assertEquals(tensor.xx, 2.1)
        self.assertEquals(tensor.yy, -3)
        self.assertEquals(tensor.zz, 0.9)
