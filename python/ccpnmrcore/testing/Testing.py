"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
import os
import unittest


from PyQt4 import QtGui

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
      self.window.raise_()
      self.start()
    
  def getSpectrum(self):

    if self.project is not None and hasattr(self, 'spectrumName'):
      return self.project.getById('Spectrum:'+self.spectrumName)
    
    return None
