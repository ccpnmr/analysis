"""Module Documentation here

Read-Only Project
^^^^^^^^^^^^^^^^^

Test should contain the following folders, as of 3.1.1

::

    _temporary
    \----temp1.ccpn
        \----archives
        \----backup
            \----backup folder 1.ccpnV3backup
        \----ccpnv3
            \----ccp
                \----lims
                    \----RefSampleComponent
                    \----Sample
                \----molecule
                    \----MolStructure
                    \----MolSystem
                \----nmr
                    \----Nmr
            \----memops
                \----implementation
        \----data
            \----plugins
            \----spectra
        \----logs
        \----resources
        \----scripts
        \----state
        \----summaries
        
    \----temp2.ccpn
        \----archives
        \----ccpnv3
            \----ccp
                \----lims
                    \----RefSampleComponent
                    \----Sample
                \----molecule
                    \----MolStructure
                    \----MolSystem
                \----nmr
                    \----Nmr
            \----memops
                \----implementation
        \----logs
        \----state
        \----summaries

    \----temp3.ccpn
        \----archives
        \----backup
            \----backup folder 1.ccpnV3backup
        \----ccpnv3
            \----ccp
                \----lims
                    \----RefSampleComponent
                    \----Sample
                \----molecule
                    \----MolStructure
                    \----MolSystem
                \----nmr
                    \----Nmr
            \----memops
                \----implementation
        \----data
            \----plugins
            \----spectra
        \----logs
        \----resources
        \----scripts
        \----state
        \----summaries


Projects on loading only require the ccpnv3 folder.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-03-21 16:00:10 +0000 (Fri, March 21, 2025) $"
__version__ = "$Revision: 3.3.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import time
import shutil
import contextlib

from PyQt5 import QtCore, QtWidgets
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.ui.gui.guiSettings import consoleStyle
from ccpn.util.Path import aPath
from ccpn.util.OrderedSet import OrderedSet
from ccpn.framework.PathsAndUrls import userCcpnPath
from ccpn.framework.Application import getApplication


TEMPFOLDER = '_temporary'
TEMPPROJECT1 = 'temp1.ccpn'
TEMPPROJECT2 = 'temp2.ccpn'
TEMPPROJECT3 = 'temp3.ccpn'
V3FOLDER = 'ccpnv3'

tempFolder = userCcpnPath / TEMPFOLDER
tempProjectDir1 = tempFolder / TEMPPROJECT1
tempProjectDir2 = tempFolder / TEMPPROJECT2
tempProjectDir3 = tempFolder / TEMPPROJECT3

_printAll = True
os.system('')  # activates console text colours


def write(*text):
    """Debug - write output"""
    for tt in text:
        sys.stdout.write(str(tt) + ' ')
    sys.stdout.write('\n')


def writeTitle(msg):
    # slightly clearer heading between tests
    write(f'{consoleStyle.fg.yellow}\n   {msg}\n   {"~" * len(msg)}{consoleStyle.reset}')


class ProjectReadOnly(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None
    eventCount = 0
    dirEvents = set()
    fileEvents = set()

    noLogging = False
    noDebugLogging = False
    noEchoLogging = False  # block all logging to the terminal - debug<n>|warning|info
    debug=False
    _lock = QtCore.QMutex()

    def _fileEvent(self, fp):
        with QtCore.QMutexLocker(self._lock):  # is this required? :|
            if fp.endswith('.DS_Store'):
                # skip OS files
                return
            if fp in self.fileEvents:
                write(f'{consoleStyle.fg.darkmagenta}    file ***       {fp}')
                return
            self.fileEvents.add(fp)
            if _printAll:
                write(f'{consoleStyle.fg.magenta}    file     {len(self.fileEvents):2}    {fp}{consoleStyle.reset}')

    def _dirEvent(self, fp):
        # STILL sometimes getting a duplicate dirEvent, OR a missing event in the middle of a directory structure
        with QtCore.QMutexLocker(self._lock):  # is this required? :|
            if fp in self.dirEvents:
                write(f'{consoleStyle.fg.darkgreen}    dir  ***       {fp}')
                return
            self.dirEvents.add(fp)
            if _printAll:
                write(f'{consoleStyle.fg.green}    dir      {len(self.dirEvents):2}    {fp}{consoleStyle.reset}')

    @staticmethod
    def watchWalk(watcher, path):
        pths = set()
        fls = set()
        for root, dirs, files in os.walk(str(path)):
            for dd in dirs:
                r = aPath(root) / dd
                pths.add(str(r))
            for ff in files:
                r = aPath(root) / ff
                fls.add(str(r))
        if pths: watcher.addPaths(pths)
        if fls: watcher.addPaths(fls)
        # for pp in pths:
        #     print(f'{consoleStyle.fg.darkgrey}...adding path watcher {pp}{consoleStyle.reset}')
        # for ff in fls:
        #     print(f'{consoleStyle.fg.darkgrey}...adding file watcher {ff}{consoleStyle.reset}')

    @contextlib.contextmanager
    def checkEvents(self, app):
        self.dirEvents = set()
        self.fileEvents = set()
        # used to check IO-events, whether project-folder or contents has changed
        watcher = QtCore.QFileSystemWatcher()
        watcher.addPath(str(tempFolder))
        watcher.directoryChanged.connect(self._dirEvent)
        watcher.fileChanged.connect(self._fileEvent)
        self.watchWalk(watcher, tempProjectDir1)
        self.watchWalk(watcher, tempProjectDir2)
        self.watchWalk(watcher, tempProjectDir3)

        app.processEvents()
        write(f'{consoleStyle.fg.darkgrey}...checkevents{consoleStyle.reset}')
        try:
            yield  # pass control to the calling function
        finally:
            # wait for arbitrary time for IO to complete
            write(f'{consoleStyle.fg.darkgrey}...waiting{consoleStyle.reset}')
            app.processEvents()
            time.sleep(5)
            app.processEvents()
            write(f'{consoleStyle.fg.lightgrey}dirEvents {len(self.dirEvents)}{consoleStyle.reset}')
            write(f'{consoleStyle.fg.lightgrey}fileEvents {len(self.fileEvents)}{consoleStyle.reset}')

    def test_readOnly(self):
        app = QtWidgets.QApplication(sys.argv)

        application = getApplication()
        project = application.project  # the initial temporary project attached to application

        # current working-folder
        # curDir = os.getcwd()
        # thisFile = aPath(curDir) / __file__

        # make a test-folder in the user's ~/.ccpn path
        userCcpnPath.fetchDir(TEMPFOLDER)
        # clean-up
        for fp in (TEMPPROJECT1, TEMPPROJECT2, TEMPPROJECT3):
            if (tempFolder / fp).exists():
                (tempFolder / fp).removeDir()

        self._watched_dir = tempFolder
        self._previous_dirs = OrderedSet(os.path.join(root, dir_name)
                                         for root, dirs, _ in os.walk(self._watched_dir, topdown=True)
                                         for dir_name in dirs)

        # Write the empty project to the temp-folder
        writeTitle('Writing project - waiting...')

        with self.checkEvents(app):
            # start from an empty project
            project.setReadOnly(False)
            application.saveProjectAs(tempProjectDir1, overwrite=True)

        # /_temporary folder has changed, contains new project
        """
        * dir-event
        ** file-event
        >> has contents
        x not watched

        App opens with a new project.
        watch _temporary folder
        Save project to _temporary should spawn dir-event for temp1.ccpn          
        (using set(), watcher may spawn 1 or 2 events on this folder, could be OS timing between touching files)
        
        _temporary
            *\----temp1.ccpn
                x\----archives
                x\----backup
                x\----ccpnv3
                    >>
                x\----data
                    >>
                x\----logs
                x\----resources
                x\----scripts
                x\----state
                x\----summaries
        """
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 0)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        with self.checkEvents(app):
            # copy just the v2-folder
            shutil.copytree(tempProjectDir1 / V3FOLDER, tempProjectDir2 / V3FOLDER)
            shutil.copytree(tempProjectDir1 / V3FOLDER, tempProjectDir3 / V3FOLDER)

        # /_temporary folder has changed, contains 2 new projects
        """
        * dir-event
        ** file-event
        >> has contents

        All files/dir below _temporary are watched
        Copy the ccpnv3 folder to 2 new dirs to give 2 new minimal, empty projects: temp2/temp3.ccpn
        
        _temporary folder has changed, contains two new projects, notifies new dirs
        
        _temporary
            \----temp1.ccpn
                >>
            *\----temp2.ccpn
                *>>
            *\----temp3.ccpn
                *>>
        """
        # events registered as a set, so top-folder only once - new folders events
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 0)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Creating objects - waiting...')

        write(project, id(project), project._wrappedData, id(project._wrappedData))
        write(project._getChildren())

        with self.checkEvents(app):
            # temp1.ccpn
            #   change read-only state will output a single log-event
            project.setReadOnly(True)
        """
        * dir-event
        ** file-event
        >> has contents

        read-only should be no notifications

        _temporary
            \----temp1.ccpn         <<  current project NOT read-only - is write enabled
                *\----logs
                    **<log>.txt
                >>
            \----temp2.ccpn
                >>
            \----temp3.ccpn
                >>
        """
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 1)
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in dd for dd in self.dirEvents))
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in ff for ff in self.fileEvents))

        with self.checkEvents(app):
            # temp1.ccpn
            #   setting read-only to False should flush anything to the log-file
            #   (including its owned log-command)
            project.setReadOnly(False)
            project.setReadOnly(True)
        """
        * dir-event
        ** file-event
        >> has contents

        read-only should be no notifications

        _temporary
            \----temp1.ccpn         <<  current project NOT read-only again - is write enabled
                *\----logs
                    **<log>.txt
                >>
            \----temp2.ccpn
                >>
            \----temp3.ccpn
                >>
        """
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 1)
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in dd for dd in self.dirEvents))
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in ff for ff in self.fileEvents))

        with self.checkEvents(app):
            # temp1.ccpn
            # create new objects that will use different .xml files
            project.newChemicalShiftList()
            nmrChain = project.newNmrChain()
            nmrChain.newNmrResidue()
            project.newSample()
            project.newSubstance()
            project.newStructureEnsemble()
            project.newComplex()
            project.newDataTable()
            project.newCollection()
            project.newNote()
            spectrum = project.newEmptySpectrum(isotopeCodes=('1H', '15N'))
            pkList = spectrum.newPeakList()
            pkList.newPeak(ppmPositions=[5.5, 5.5])
            # should do nothing as read-only, and no files/logging should occur
            application.saveProject()

        """
        * dir-event
        ** file-event
        >> has contents

        read-only should be no notifications
        
        _temporary
            \----temp1.ccpn         <<  current project read-only
                >>
            \----temp2.ccpn
                >>
            \----temp3.ccpn
                >>
        """
        # no changes, project is read-only
        self.assertEqual(len(self.dirEvents), 0)
        self.assertEqual(len(self.fileEvents), 0)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Enable writing - waiting...')

        with self.checkEvents(app):
            # allow saving again, dumps the contents of the log to the log-file
            # temp1.ccpn
            project.setReadOnly(False)

        """
        * dir-event
        ** file-event
        >> has contents

        read-only has been disabled, writes to the log-file on the next logHandler emit/close

        _temporary
            \----temp1.ccpn         <<  current project NOT read-only - is write enabled
                *\----logs
                    **<log>.txt
                >>
            \----temp2.ccpn
                >>
            \----temp3.ccpn
                >>
        """
        # not read-only, writes log-file
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 1)
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in dd for dd in self.dirEvents))
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in ff for ff in self.fileEvents))

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Writing project again - waiting...')
        write(project, id(project))
        write(project._getChildren())

        with self.checkEvents(app):
            # should now write the files
            application.saveProject()

        """
        * dir-event
        ** file-event
        >> has contents
        x not watched
        
        explicit save-event, writes project files
        writes to the same log-file as same instance of app running
        backup is created in backup folder
                
        _temporary
            \----temp1.ccpn                     << current project NOT read-only - is write enabled
                *\----archives                  <-- new from project.save
                    **<save-file>.ccpn.tgz
                *\----backup
                    >>
                *\----ccpnv3
                    *\----ccp
                        *\----lims
                            *\----RefSampleComponent
                                **<file>.xml
                            *\----Sample
                                **<file>.xml
                        *\----molecule
                            x\----MolStructure  << not in previous file-structure
                                >>
                            *\----MolSystem
                                **<file>.xml
                        *\----nmr
                            *\----Nmr
                                **<file>.xml
                    *\----memops
                        *\----implementation
                            **<file>.xml
                \----data
                    \----plugins
                    \----spectra
                *\----logs
                    **<log>.txt
                \----resources
                \----scripts
                *\----state
                    *\----spectra
                        >>
                    **<state-file>.json
                    **Current
                \----summaries
            \----temp2.ccpn
                >>
            \----temp3.ccpn
                >>
        """
        # all folders written to
        self.assertEqual(len(self.dirEvents), 16)
        self.assertTrue(all(f'{TEMPPROJECT1}/' in dd for dd in self.dirEvents))
        self.assertEqual(len(self.fileEvents), 9)
        self.assertTrue(all(f'{TEMPPROJECT1}/' in ff for ff in self.fileEvents))
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.xml')]), 5)
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.json')]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.txt')]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.tgz')]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('/Current')]), 1)
        # Current does not have the .json extension :| will sort later

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Open new project2 - waiting...')

        del project
        with self.checkEvents(app):
            # temp1.ccpn previous project - not read-only
            # loading NEW project2 temp2.ccpn
            project2 = application.loadProject(tempProjectDir2)

        """
        * dir-event
        ** file-event
        >> has contents

        loading new project2 - temp2.ccpn
        old project temp1.ccpn is closed, as this is not read-only, log is updated, project is NOT isModified
        Should be single dir and single log event in temp1.ccpn
        
        _temporary
            \----temp1.ccpn             << previous project - NOT read-only
                \----archives
                \----backup
                    >>
                \----ccpnv3
                    >>
                \----data
                    >>
                *\----logs
                    **<log>.txt
                \----resources
                \----scripts
                \----state
                    >>
                \----summaries
            \----temp2.ccpn             << loading project2
                >>
            \----temp3.ccpn
                >>
        """
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 1)
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in dd for dd in self.dirEvents))
        self.assertTrue(all(f'{TEMPPROJECT1}/logs' in ff for ff in self.fileEvents))

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        write(project2, id(project2), project2._wrappedData, id(project2._wrappedData))
        write(project2._getChildren())

        with self.checkEvents(app):
            # temp2.ccpn
            project2.setReadOnly(True)
        """
        * dir-event
        ** file-event
        >> has contents

        read-only should be no notifications

        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn         <<  current project NOT read-only - is write enabled
                *\----logs
                    **<log>.txt
                >>
            \----temp3.ccpn
                >>
        """
        self.assertEqual(len(self.dirEvents), 1)
        self.assertEqual(len(self.fileEvents), 1)
        self.assertTrue(all(f'{TEMPPROJECT2}/logs' in dd for dd in self.dirEvents))
        self.assertTrue(all(f'{TEMPPROJECT2}/logs' in ff for ff in self.fileEvents))

        with self.checkEvents(app):
            # temp2.ccpn
            # create new objects that will use different .xml files
            project2.newChemicalShiftList()
            nmrChain = project2.newNmrChain()
            nmrChain.newNmrResidue()
            project2.newSample()
            project2.newSubstance()
            project2.newStructureEnsemble()
            project2.newComplex()
            project2.newDataTable()
            project2.newCollection()
            project2.newNote()
            spectrum = project2.newEmptySpectrum(isotopeCodes=('1H', '15N'))
            pkList = spectrum.newPeakList()
            pkList.newPeak(ppmPositions=[5.5, 5.5])
            # should do nothing as read-only, and no files/logging should okay
            application.saveProject()

        """
        * dir-event
        ** file-event
        >> has contents

        temp2.ccpn is read-only, should not write anything until explicit save, or crash-event

        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn             << current project2 is read-only
                >>
            \----temp3.ccpn
                >>
        """
        # nothing written, temp2.ccpn read-only
        self.assertEqual(len(self.dirEvents), 0)
        self.assertEqual(len(self.fileEvents), 0)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Open new project3 - waiting...')

        del project2
        with self.checkEvents(app):
            # project2 is read-only - temp2.ccpn
            # loading NEW project3 temp3.ccpn
            project3 = application.loadProject(tempProjectDir3)

        """
        * dir-event
        ** file-event
        >> has contents

        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn             << previous project2 is read-only - no log-file update
                >>
            \----temp3.ccpn             << loading project3
                >>
        """
        # nothing written, temp.ccpn read-only
        self.assertEqual(len(self.dirEvents), 0)
        self.assertEqual(len(self.fileEvents), 0)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        write(project3, id(project3), project3._wrappedData, id(project3._wrappedData))
        write(project3._getChildren())

        with self.checkEvents(app):
            # create new objects that will use different .xml files
            project3.newChemicalShiftList()
            nmrChain = project3.newNmrChain()
            nmrChain.newNmrResidue()
            project3.newSample()
            project3.newSubstance()
            project3.newStructureEnsemble()
            project3.newComplex()
            project3.newDataTable()
            project3.newCollection()
            project3.newNote()
            spectrum = project3.newEmptySpectrum(isotopeCodes=('1H', '15N'))
            pkList = spectrum.newPeakList()
            pkList.newPeak(ppmPositions=[5.5, 5.5])

            # just set near the end somewhere
            project3.setReadOnly(False)

            # not read-only, update files
            application.saveProject()

        """
        _temporary folder has changed
        * dir-event
        ** file-event
        >> has contents
        x not watched
                
        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn
                >>
            \----temp3.ccpn                 << current project3 not read-only - is write enabled
                x\----archives
                x\----backup
                    >>
                *\----ccpnv3
                    *\----ccp
                        *\----lims
                            *\----RefSampleComponent
                                **<file>.xml
                            *\----Sample
                                **<file>.xml
                        *\----molecule
                            x\----MolStructure      << not in previous file-structure
                                >>
                            *\----MolSystem
                                **<file>.xml
                        *\----nmr
                            *\----Nmr
                                **<file>.xml
                    *\----memops
                        *\----implementation
                            **<file>.xml
                x\----data
                    \----plugins
                    \----spectra
                x\----logs
                    >>
                x\----resources
                x\----scripts
                x\----state
                    x\----spectra
                x\----summaries
        """
        # all folders written to
        # not watching backups/state/logs
        self.assertEqual(len(self.dirEvents), 14)
        self.assertTrue(all(f'{TEMPPROJECT3}/' in dd for dd in self.dirEvents))
        self.assertEqual(len(self.fileEvents), 6)
        self.assertTrue(all(f'{TEMPPROJECT3}/' in ff for ff in self.fileEvents))
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.xml')]), 5)
        # no json/txt - folders not watching

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Open new project2 - waiting...')

        with self.checkEvents(app):
            # add new item to current project
            # SHOULD really be an error here for a modified project, or dialog-box
            project3.newNote()
            project2 = application.loadProject(tempProjectDir2)
        del project3

        """
        _temporary folder has changed
        * dir-event
        ** file-event
        >> has contents

        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn                 << loading project2
                *\----archives              <-- from _loadV3Project
                    **<save-file>.ccpn.tgz
                \----ccpnv3
                    >>
                *\----logs
                    **<log>.txt
                \----state
                \----summaries
            \----temp3.ccpn                 << previous project3 not read-only - is write enabled
                *\----logs
                    **<log>.txt
                >>
        """
        # log written to, folder and file, update log, same log file
        self.assertEqual(len(self.dirEvents), 3)
        self.assertEqual(len(self.fileEvents), 3)
        self.assertEqual(len([dd for dd in self.dirEvents if f'{TEMPPROJECT2}/logs' in dd]), 1)
        self.assertEqual(len([dd for dd in self.dirEvents if f'{TEMPPROJECT3}/logs' in dd]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if f'{TEMPPROJECT2}/logs' in ff]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if f'{TEMPPROJECT3}/logs' in ff]), 1)

        write(project2, id(project2), project2._wrappedData, id(project2._wrappedData))
        write(project2._getChildren())

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Open new project3 again - waiting...')

        with self.checkEvents(app):
            project3 = application.loadProject(tempProjectDir3)
        del project2

        """
        * dir-event
        ** file-event
        >> has contents

        read-only has been disabled but should not write anything until explicit save, or crash-event

        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn                 << previous project2 not read-only - is write enabled
                *\----logs
                    **<log>.txt
                >>
            \----temp3.ccpn                 << loading project3
                *\----archives              <-- from _loadV3Project
                    **<save-file>.ccpn.tgz
                *\----logs
                    **<log>.txt
                >>
        """
        # nothing written, project2 should be clean
        self.assertEqual(len(self.dirEvents), 3)
        self.assertEqual(len(self.fileEvents), 3)
        self.assertEqual(len([dd for dd in self.dirEvents if f'{TEMPPROJECT2}/logs' in dd]), 1)
        self.assertEqual(len([dd for dd in self.dirEvents if f'{TEMPPROJECT3}/logs' in dd]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if f'{TEMPPROJECT2}/logs' in ff]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if f'{TEMPPROJECT3}/logs' in ff]), 1)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        writeTitle('Writing project3 again - waiting...')
        write(project3, id(project3))
        write(project3._getChildren())

        with self.checkEvents(app):
            # should now write the files
            application.saveProject()

        """
        * dir-event
        ** file-event
        >> has contents

        explicit save-event, writes project3 files
        writes to the same log-file as same instance of app running
        backup is created in backup folder

        _temporary
            \----temp1.ccpn
                >>
            \----temp2.ccpn
                >>
            \----temp3.ccpn                     << current project3
                *\----archives                  <-- from project.save
                    **<save-file>.ccpn.tgz
                *\----backup
                    >>
                *\----ccpnv3
                    *\----ccp
                        *\----lims
                            *\----RefSampleComponent
                                **<file>.xml
                            *\----Sample
                                **<file>.xml
                        *\----molecule              <== SOMETIMES this is skipped :|
                            *\----MolStructure
                                **<file>.xml
                            *\----MolSystem
                                **<file>.xml
                        *\----nmr
                            *\----Nmr
                                **<file>.xml
                    *\----memops
                        *\----implementation
                            **<file>.xml
                \----data
                    \----plugins
                    \----spectra
                *\----logs
                    **<log>.txt
                \----resources
                \----scripts
                *\----state
                    *\----spectra
                        **<empty-spectrum>.json
                    **<state-file>.json
                    **Current
                \----summaries
        """
        # NOTE:ED - this is a hack for OS that I cannot find :|
        if not (moleculeDir := any(map(lambda fp: fp.endswith('temp3.ccpn/ccpnv3/ccp/molecule'), self.dirEvents))):
            write(f'*** temp3.ccpn/ccpnv3/ccp/molecule event not received')
        dirCount = 17 if moleculeDir else 16
        # NOTE:ED - all folders written to
        self.assertEqual(len(self.dirEvents), dirCount)
        self.assertTrue(all(f'{TEMPPROJECT3}/' in dd for dd in self.dirEvents))
        self.assertEqual(len(self.fileEvents), 11)
        self.assertTrue(all(f'{TEMPPROJECT3}/' in ff for ff in self.fileEvents))
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.xml')]), 6)

        # spectrum now in watched list
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.json')]), 2)
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('.txt')]), 1)
        self.assertEqual(len([ff for ff in self.fileEvents if ff.endswith('/Current')]), 1)
        # Current does not have the .json extension :| will sort later
