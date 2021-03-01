"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-01 11:22:50 +0000 (Mon, March 01, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from unittest import expectedFailure, skip
from ccpn.framework import Framework
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError


#=========================================================================================
# NoteTest_SetUp
#=========================================================================================

class NoteTest_setUp(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    #=========================================================================================
    # setUp       initialise a new project
    #=========================================================================================

    def setUp(self):
        """
        Create a valid Note of name 'Validname'
        """
        with self.initialSetup():
            self.note = self.project.newNote(name='ValidNote')

    #=========================================================================================
    # test_rename_Note          functions to test bad renames
    #=========================================================================================

    def test_rename_Note_ES(self):
        """
        Test that renaming to '' raises an error and does not alter the original Note.
        ^ is a bad character and not to be included in strings.
        """
        with self.assertRaisesRegexp(ValueError, 'must be set'):
            self.note.rename('')
        self.assertEqual(self.note.name, 'ValidNote')

    def test_rename_Note_Badname(self):
        """
        Test that renaming to '^Badname' raises an error and does not alter the original Note.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.note.rename('^Badname')
        self.assertEqual(self.note.name, 'ValidNote')

    def test_rename_Note_None(self):
        """
        Test that renaming to None raises an error and does not alter the original Note.
        """
        with self.assertRaisesRegexp(ValueError, 'None not allowed'):
            self.note.rename(None)
        self.assertEqual(self.note.name, 'ValidNote')

    def test_rename_Note_Int(self):
        """
        Test that renaming to 42 (non-string) raises an error and does not alter the original Note.
        """
        # with self.assertRaisesRegexp(TypeError, 'argument of type'):
        #   self.note.rename(42)
        #
        with self.assertRaisesRegexp(TypeError, 'must be a string'):
            self.note.rename(42)
        self.assertEqual(self.note.name, 'ValidNote')

    #=========================================================================================
    # test_undo_Note
    #=========================================================================================

    def test_undo_Note(self):
        """
        Create an Undo point and check that the original/changed names are correct.
        """
        undo = self.project._undo
        newUndoPoint = self.project.newUndoPoint
        newUndoPoint()  # set a recovery point

        self.note.rename('Changed')
        self.assertEqual(self.note.name, 'Changed')

        undo.undo()
        self.assertEqual(self.note.name, 'ValidNote')  # revert to the original name

        undo.redo()
        self.assertEqual(self.note.name, 'Changed')  # redo

    #=========================================================================================
    # test_properties_Note      Properties
    #=========================================================================================

    def test_properties_Note_Serial(self):
        """
        Test that Note attribute .serial is populated.
        """
        self.assertEqual(self.note.serial, 1)

    def test_properties_Note_Name(self):
        """
        Test that Note attribute .name is populated.
        """
        self.assertEqual(self.note.name, 'ValidNote')

    def test_properties_Note_Text(self):
        """
        Test that Note attribute .text is populated.
        """
        self.assertEqual(self.note.text, None)

    def test_properties_Note_Header(self):
        """
        Test that Note attribute .header is populated.
        """
        self.assertEqual(self.note.header, None)

    #=========================================================================================
    # test_properties_Note
    #=========================================================================================

    def test_properties_Note_None(self):
        """
        Test that text setter is setting the .header correctly.
        Read the attribute, if it not populated then an error is raised.
        If no error, then test the setter by setting and then getting to check consistent.
        """
        text = self.note.text
        self.note.text = None
        self.assertEqual(self.note.header, None)

    def test_properties_Note_ES(self):
        """
        Test that text setter is setting the .header correctly.
        """
        self.note.text = ''
        self.assertEqual(self.note.header, None)

    def test_properties_Note_S(self):
        """
        Test that text setter is setting the .header correctly.
        """
        self.note.text = 'Changed Header'
        self.assertEqual(self.note.header, 'Changed Header')

    def test_properties_Note_Int(self):
        """
        Test that text setter does not accept a non-string.
        """
        # with self.assertRaisesRegexp(ApiError, 'String input is not of a valid type'):
        #   self.note.text = 42
        #
        with self.assertRaisesRegexp(TypeError, 'Note text must be a string'):
            self.note.text = 42
        self.assertEqual(self.note.header, None)

    #=========================================================================================
    # test_properties_Note      expectedFailure
    #=========================================================================================

    # @expectedFailure                          remove this as we want to see the failure
    def test_properties_Note_created(self):
        """
        Test that Note attribute .created returns an strftime of Note creation time.

        This is an expectedFailure as .created has not been populated.
        """
        created = self.note.created

    # @expectedFailure                          remove this as we want to see the failure
    def test_properties_Note_lastModified(self):
        """
        Test that Note attribute .lastModified returns an strftime of Note modification time.

        This is an expectedFailure as .lastModified has not been populated.
        """
        lastModified = self.note.lastModified

    #=========================================================================================
    # test_make_and_save_Note
    #=========================================================================================

    # def test_make_and_save_Note(self):
    #     """
    #     Test that the project can be saved and loaded.
    #     """
    #     self.project.newNote(text='test_make_and_save_Note')
    #     self.assertTrue(self.project.save())
    #     #
    #     # loadedProject = core.loadProject(self.project.path)
    #     loadedProject = Framework.createFramework(projectPath=self.project.path, _skipUpdates=True).project
    #     # loadedProject.delete()


#=========================================================================================
# NoteTest_No_setUp
#=========================================================================================

class NoteTest_No_setUp(WrapperTesting):

    #=========================================================================================
    # test_newNote            functions to create new Notes
    #=========================================================================================

    def test_newNote(self):
        """
        Test that creating a new Note with no parameter creates a valid Note.
        """
        self.note = self.project.newNote()
        self.assertEqual(self.note.name, 'myNote_1')  # check that default name has been set 'Note'

    def test_newNote_ES(self):
        """
        Test that creating a new Note with '' raises an error.
        """
        # with self.assertRaisesRegexp(ApiError, 'Empty string not allowed'):
        #   self.project.newNote('')
        #
        self.project.newNote('')

    def test_newNote_Badname(self):
        """
        Test that creating a new Note with '^Badname' raises an error.
        ^ is a bad character and not to be included in strings.
        """
        with self.assertRaisesRegexp(ValueError, 'Character'):
            self.project.newNote('^Badname')

    def test_newNote_None(self):
        """
        Test that creating a new Note with None raises an error.
        """
        # with self.assertRaisesRegexp(ApiError, 'Line input is not of a valid type'):
        #   self.project.newNote(None)
        #
        self.project.newNote(None)

    def test_newNote_Int(self):
        """
        Test that creating a new Note with 42 (non-string) raises an error.
        """
        # with self.assertRaisesRegexp(TypeError, 'argument of type'):
        #   self.project.newNote(42)
        #
        with self.assertRaisesRegexp(TypeError, 'must be a string'):
            self.project.newNote(42)
