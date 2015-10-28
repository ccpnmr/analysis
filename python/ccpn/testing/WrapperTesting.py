"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import os
import unittest
import contextlib
import ccpn

from ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH

class WrapperTesting(unittest.TestCase):
  """Base class for all testing of wrapper code that requires projects."""

  # Path for project to load - can be overridden in subclasses
  projectPath = None

  @contextlib.contextmanager
  def initialSetup(self):
    if self.projectPath is None:
      print ("@~@~ making new project")
      self.project = ccpn.newProject('default')
    else:
      print ("@~@~ loadubg new project", self.projectPath)
      self.project = ccpn.loadProject(os.path.join(TEST_PROJECTS_PATH, self.projectPath))
    print ('@~@~ done making project')
    self.project._resetUndo(debug=True)
    self.undo = self.project._undo
    self.undo.debug = True
    try:
      yield
    except:
      self.tearDown()
      raise

  def setUp(self):
    with self.initialSetup():
      pass

  def tearDown(self):
    if self.project:
      self.project._close()

  def loadData(self, dataPath):
    """load data relative to TEST_PROJECTS_PATH (unless dataPath is absolute"""
    if not os.path.isabs(dataPath):
      dataPath = os.path.join(TEST_PROJECTS_PATH, dataPath)
    dataList = self.project.loadData(dataPath)
    #
    return dataList

if __name__ == '__main__':
  # test for raw porject opening, in case of setup malfunctioning
  print('@~@~ start making new project')
  pp = ccpn.newProject('default')
  print('@~@~ done making new project')
  print('@~@~ start reading old project')
  pp = ccpn.loadProject(os.path.join(TEST_PROJECTS_PATH, 'CcpnCourse2b'))
  print('@~@~ done reading old project')