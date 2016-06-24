"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

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

  def test_creation(self):
    project = self.project
    undo = self.project._undo
    undo.newWaypoint()
    task = project.tasks[0]
    task2 = project.newTask('TestTask')
    window2 = project.newWindow(title='W2')
    window2.task = task2
    module1 = task.newModule('TestMod')
    module2 = task.newModule('TestMod')
    module3 = task2.newModule('TestMod', window=window2, name='MyOwn', comment='really?')
    module4 = task.newModule('DifferentMod')
    undo.undo()
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
    undo.redo()
    self.assertEquals(module1.pid, 'GM:user.View.TestMod')
    self.assertEquals(module2.pid, 'GM:user.View.TestMod_1')
    self.assertEquals(module3.pid, 'GM:user.TestTask.MyOwn')
    self.assertEquals(module4.pid, 'GM:user.View.DifferentMod')
    self.assertEquals(module1.window.pid, 'GW:Main')
    self.assertEquals(module2.window.pid, 'GW:Main')
    self.assertEquals(module3.window.pid, 'GW:W2')
    self.assertEquals(module4.window.pid, 'GW:Main')
    self.assertEquals(module3.comment, 'really?')


class ParameterTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None


  def test_parameters(self):

    project = self.project
    task = project.newTask('TestTask')
    module1 = task.newModule('TestMod')

    testpars = collections.OrderedDict()
    for key,val in [
      ('bbb',1), ('ccc',[1,2,3]), ('ddd',True), ('aaa',()), ('xxx','xxx'), ('dict', {1:1}),
      ('odict', collections.OrderedDict(((2,100), (1,10))))
    ]:
      testpars[key] = val


    undo = self.project._undo
    undo.newWaypoint()
    self.assertEqual(module1.parameters, {})
    module1.setParameter('aaa', 1)
    self.assertEqual(module1.parameters, {'aaa':1})
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
      task = project.newTask('TestTask')
      module1 = task.newModule('TestMod')
      undo = self.project._undo
      undo.newWaypoint()
      module1.setParameter('ndarray', numpy.ndarray((5,3,1)))
      undo.undo()
      undo.redo()
      self.assertTrue(isinstance(module1.parameters['ndarray'], numpy.ndarray))

  def test_tensor_parameter(self):

      project = self.project
      task = project.newTask('TestTask')
      module1 = task.newModule('TestMod')
      undo = self.project._undo
      undo.newWaypoint()
      module1.setParameter('tensor', Tensor._fromDict({'orientationMatrix':numpy.identity(3),
                                     'xx':2.1, 'yy':-3, 'zz':0.9}))
      undo.undo()
      undo.redo()
      tensor = module1.parameters['tensor']
      self.assertTrue(isinstance(tensor, Tensor))
      self.assertEquals(tensor.xx, 2.1)
      self.assertEquals(tensor.yy, -3)
      self.assertEquals(tensor.zz, 0.9)

