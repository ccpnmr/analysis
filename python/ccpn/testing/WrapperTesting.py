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
import ccpn

from ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH

class WrapperTesting(unittest.TestCase):
  """Base class for all testing of wrapper code that requires projects."""

  # Path for project to load - can be overridden in subclasses
  projectPath = None

  def setUp(self):

    if self.projectPath is None:
      self.project = ccpn.newProject('default')
    else:
      self.project = ccpn.openProject(os.path.join(TEST_PROJECTS_PATH,
                                                   self.projectPath))

  def tearDown(self):
    if self.project:
      self.project.delete()

  def loadData(self, dataPath):
    """load data relative to TEST_PROJECTS_PATH (unless dataPath is absolute"""
    if not os.path.isabs(dataPath):
      dataPath = os.path.join(TEST_PROJECTS_PATH, dataPath)
    dataList = self.project.loadData(dataPath)
    #
    return dataList

