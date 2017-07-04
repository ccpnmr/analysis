__author__ = 'Rasmus Fogh'

import os
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.core.lib import CcpnNefIo


class TestCommentedExample(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = 'Commented_Example.nef'

  def test_commentedExample(self):
    outPath = os.path.dirname(self.project.path)[:-5] + '.out.nef'
    CcpnNefIo.saveNefProject(self.project, outPath, overwriteExisting=True)
    # TODO do diff to compare output with input

class TestCourse3e(WrapperTesting):
  # Path of project to load (None for new project
  projectPath = 'CcpnCourse3e'

  def test_Course3e(self):
    outPath = os.path.dirname(self.project.path)[:-5] + '.out.nef'
    CcpnNefIo.saveNefProject(self.project, outPath, overwriteExisting=True)
    application = self.project._appBase
    application.loadProject(outPath)
    nefOutput = CcpnNefIo.convert2NefString(application.project)
    # TODO do diff to compare nefOutput with input file

class TestCourse2c(WrapperTesting):
  # Path of project to load (None for new project
  projectPath = 'CcpnCourse2c'

  def test_Course2c(self):
    outPath = os.path.dirname(self.project.path)[:-5] + '.out.nef'
    self.assertRaises(NotImplementedError,
                      CcpnNefIo.saveNefProject(self.project, outPath, overwriteExisting=True))
    # application = self.project._appBase
    # application.loadProject(outPath)
    # nefOutput = CcpnNefIo.convert2NefString(application.project)
    # # TODO do diff to compare nefOutput with input file