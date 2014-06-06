import os
import unittest

from PySide import QtGui

from ccpncore.gui.Button import Button
from ccpncore.gui.Frame import Frame

from ccpncore.gui.Application import Application
from ccpncore.util.Testing import TEST_PROJECTS_PATH

import ccpn

class Testing(unittest.TestCase, Application):
  """Base class for all testing of modules that requires projects."""

  def __init__(self, projectPath:str=None, *args, **kw):

    if projectPath is not None:
      if not os.path.isabs(projectPath):
        projectPath = os.path.join(TEST_PROJECTS_PATH, projectPath)

    self.projectPath = projectPath
    self.project = None
    self.window = None
    self.frame = None

    unittest.TestCase.__init__(self, *args, **kw)
    Application.__init__(self, 'TestApplication', '1.0')

  def setUp(self):
      
    projectPath = self.projectPath

    if projectPath:
      self.project = ccpn.openProject(projectPath)
      
      self.window = QtGui.QWidget()
      # add widgets to self.frame, then at end do self.window.show() and self.start()
      self.frame = Frame(self.window, grid=(0, 0))
      button = Button(self.window, text='Quit', callback=self.quit,
                      tipText='Click to quit', grid=(1, 0))

  def tearDown(self):
    
    if self.window:
      self.window.show()
      self.start()
    
  def getSpectrum(self):

    if self.project is not None and hasattr(self, 'spectrumName'):
      return self.project.getById('Spectrum:'+self.spectrumName)
    
    return None
