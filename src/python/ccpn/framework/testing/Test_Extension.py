__author__ = 'TJ Ragan'

import unittest

from ccpn.core.testing.WrapperTesting import WrapperTesting

from ccpn.framework.lib.Extension import ExtensionABC


class TestExtensionClass(unittest.TestCase):

  def test(self):
    assert True

  # def setUp(self):
  #   with self.initialSetup():
  #     pass


  def test_ABC(self):

    class Extension(ExtensionABC):
      METHODNAME = 'test extension'
      def runMethod(self, dataset):
        return

    e = Extension(None)
    e.runMethod(None)


import sys
from PyQt4.QtGui import QApplication
from ccpn.framework.lib.Extension import GuiModule
class TestExtensionGuiBox(unittest.TestCase):

  def setUp(self):
    self.app = QApplication(sys.argv)


  def test(self):
    gm = GuiModule(None, 'test')


  def test_autoTextParam(self):
    gm = GuiModule(None, 'test', params={'test string':'test1'})


  def test_autoDropDownBoxParam_list(self):
    gm = GuiModule(None, 'test', params={'test list of strings':['test1', 'test2']})


  def test_autoDropDownBoxParam_tuple(self):
    gm = GuiModule(None, 'test', params={'test tuple of strings':('test1', 'test2')})


  def test_autoMappedDropDownBoxParam(self):
    gm = GuiModule(None, 'test', params={'test dict of strings':{'test1k':'test1v'}})


  def test_autoIntRangedSpinBox(self):
    gm = GuiModule(None, 'test', params={'test tuple of ints':(7, (1, 9, 2))})


  def test_autoFloatSpinBox(self):
    gm = GuiModule(None, 'test', params={'test tuple of floats':(0.5, (1., 2., 0.1))})



class TestExtensionClassAnalysisIntegration(WrapperTesting):

  def _test1(self):
    print(self.project)
    ds = self.project.newDataSet()
    print(ds)
