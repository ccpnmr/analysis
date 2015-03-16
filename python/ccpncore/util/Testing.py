"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
"""Test code"""


import os
import unittest

from ccpncore.util import Path
from ccpncore.util import Io

TEST_PROJECTS_PATH = os.path.join(Path.getTopDirectory(), 'data/testProjects')

class Testing(unittest.TestCase):
  """Base class for all testing code that requires projects."""

  def __init__(self, projectPath:str=None, *args, **kw):

    if projectPath is not None:
      if not os.path.isabs(projectPath):
        projectPath = os.path.join(TEST_PROJECTS_PATH, projectPath)

    self.projectPath = projectPath
    self.project = self.nmrProject = None

    unittest.TestCase.__init__(self, *args, **kw)

  def setUp(self):

    projectPath = self.projectPath

    if projectPath:
      project = self.project = Io.loadProject(projectPath)
      nmrProject = project.currentNmrProject
      if not nmrProject:
        nmrProject = project.currentNmrProject = project.findFirstNmrProject()
      self.nmrProject = nmrProject
