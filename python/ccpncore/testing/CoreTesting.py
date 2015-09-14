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
"""Test code"""


import os
import unittest

from ccpncore.util import Path
from ccpncore.util import Io

TEST_PROJECTS_PATH = os.path.join(Path.getTopDirectory(), 'data/testProjects')

class CoreTesting(unittest.TestCase):
  """Base class for all testing code that requires projects."""

  # Path for project to load - can be overridden in subclasses
  projectPath = None

  def setUp(self):

    if self.projectPath is None:
      project = self.project = Io.newProject('default', removeExisting=True)
      self.nmrProject = project.newNmrProject(name='default')
    else:
      project = self.project = Io.loadProject(os.path.join(TEST_PROJECTS_PATH, self.projectPath))
      nmrProject = project.currentNmrProject
      if not nmrProject:
        nmrProject = project.currentNmrProject = project.findFirstNmrProject()
      self.nmrProject = nmrProject


  def tearDown(self):

    self.project = None
    self.nmrProject = None