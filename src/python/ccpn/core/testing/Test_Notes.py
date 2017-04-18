"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:35 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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

