__author__ = 'TJ Ragan'

import unittest
import os

from ccpn.util.Path import getTopDirectory

from ccpn.util.SubclassLoader import loadSubclasses



class TestSubclassLoader(unittest.TestCase):

  def test(self):
    from ccpn.util.testing.SubclassLoaderTestSuperclass import Superclass

    path = os.path.join(getTopDirectory(), 'src', 'python', 'ccpn', 'util', 'testing')
    subclasses = loadSubclasses(path, baseclass=Superclass)

    self.assertEqual(len(subclasses), 2)
