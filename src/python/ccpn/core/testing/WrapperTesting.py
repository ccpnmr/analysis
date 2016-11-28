"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
import os
import unittest
import contextlib
# from ccpn import core
from ccpn.framework import Framework

from ccpnmodel.ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH

class WrapperTesting(unittest.TestCase):
  """Base class for all testing of wrapper code that requires projects."""

  # Path for project to load - can be overridden in subclasses
  projectPath = None

  @contextlib.contextmanager
  def initialSetup(self):
    # if self.projectPath is None:
    #   self.project = core.newProject('default')
    # else:
    #   self.project = core.loadProject(os.path.join(TEST_PROJECTS_PATH, self.projectPath))

    projectPath = self.projectPath
    if projectPath is not None:
      projectPath = os.path.join(TEST_PROJECTS_PATH, projectPath)
    self.framework = Framework.createFramework(projectPath=projectPath)
    self.project = self.framework.project

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
    if self.framework:
      self.framework._closeProject()
    self.framework = self.project = self.undo = None

  def loadData(self, dataPath):
    """load data relative to TEST_PROJECTS_PATH (unless dataPath is absolute"""
    if not os.path.isabs(dataPath):
      dataPath = os.path.join(TEST_PROJECTS_PATH, dataPath)
    dataList = self.project.loadData(dataPath)
    #
    return dataList

  def raiseDelayedError(self, *args, **kwargs):
    """Debugging tool. To raise an error the """
    if hasattr(self, 'delayedError') and self.delayedError:
      self.delayedError -= 1
    else:
      raise Exception('Deliberate delayed error!!')