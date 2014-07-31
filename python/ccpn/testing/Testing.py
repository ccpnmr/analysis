import os
import unittest

from ccpncore.util.Testing import TEST_PROJECTS_PATH

import ccpn

class Testing(unittest.TestCase):
  """Base class for all testing of wrapper code that requires projects."""

  def __init__(self, projectPath:str=None, *args, **kw):

    if projectPath is not None:
      if not os.path.isabs(projectPath):
        projectPath = os.path.join(TEST_PROJECTS_PATH, projectPath)

    self.projectPath = projectPath
    self.project = None

    unittest.TestCase.__init__(self, *args, **kw)

  def setUp(self):
      
    projectPath = self.projectPath

    if projectPath:
      self.project = ccpn.openProject(projectPath)

  def getSpectrum(self):

    if self.project is not None and hasattr(self, 'spectrumName'):
      return self.project.getById('Spectrum:'+self.spectrumName)
    
    return None
