"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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

from ccpn.framework import Framework
from ccpn.core.testing.WrapperTesting import WrapperTesting


class NoteTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_make_and_save_note(self):
    self.project.newNote(text='Balaclava')
    self.assertTrue(self.project.save())
    # loadedProject = core.loadProject(self.project.path)
    loadedProject = Framework.createFramework(projectPath=self.project.path).project
    loadedProject.delete()

  def test_rename_note(self):
    note = self.project.newNote(name='patty')
    undo = self.project._undo
    undo.newWaypoint()
    note.rename('cake')
    self.assertEqual(note.name, 'cake')
    undo.undo()
    self.assertEqual(note.name, 'patty')
    undo.redo()
    self.assertEqual(note.name, 'cake')

