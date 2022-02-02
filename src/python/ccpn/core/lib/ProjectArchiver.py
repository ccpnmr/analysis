"""
Code for Project archiving
Replaced former Api.packageProject and _unpackCcpnTarfile
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-02-02 12:59:27 +0000 (Wed, February 02, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from tarfile import TarFile

from ccpn.util.Path import Path, aPath
from ccpn.util.Logging import getLogger

from ccpn.framework.PathsAndUrls import \
    CCPN_DIRECTORY_SUFFIX, \
    CCPN_API_DIRECTORY, \
    CCPN_STATE_DIRECTORY, \
    CCPN_ARCHIVES_DIRECTORY, \
    CCPN_SUMMARIES_DIRECTORY, \
    CCPN_LOGS_DIRECTORY, \
    CCPN_PLUGINS_DIRECTORY, \
    CCPN_SCRIPTS_DIRECTORY


_directoriesToArchive = (
    CCPN_API_DIRECTORY,
    CCPN_STATE_DIRECTORY,
    CCPN_SUMMARIES_DIRECTORY,
    CCPN_LOGS_DIRECTORY,
    CCPN_PLUGINS_DIRECTORY,
    CCPN_SCRIPTS_DIRECTORY
    )

ARCHIVE_SUFFIX = '.tgz'


class ProjectArchiver(object):
    """A class to manage the archives of a project
    """

    def __init__(self, projectPath):
        """Initialise the class with the specified projectPath
        """
        # check that the specified projectPath is valid type and exists
        if projectPath is None or not isinstance(projectPath, (str, Path)):
            raise ValueError(f'Invalid projectPath: expected str or Path instance but got {projectPath}')

        self._projectPath = aPath(projectPath)
        if not self._projectPath.exists():
            raise ValueError(f'Invalid projectPath: {projectPath} does not exist')

    @property
    def archiveDirectory(self) -> Path:
        """:return: absolute path to directory with archives as a Path instance
        """
        return self._projectPath.fetchDir(CCPN_ARCHIVES_DIRECTORY)

    @property
    def archives(self) -> list:
        """:return: a list of archive (.tgz) tar files"""
        return self.archiveDirectory.listdir(suffix=ARCHIVE_SUFFIX)

    def makeArchive(self) -> Path:
        """Make a new time-stamped archive from project.
        :return: absolute path to the new archives as a Path instance
                 or None on IOerror
        """
        archivePath = self.archiveDirectory / self._projectPath.basename
        archivePath = archivePath.addTimeStamp().withSuffix(
                CCPN_DIRECTORY_SUFFIX + ARCHIVE_SUFFIX)
        cwd = os.getcwd()

        try:
            os.chdir(self._projectPath)

            with TarFile.open(archivePath, mode='w:gz') as tarfile:
                for _dir in _directoriesToArchive:
                    # check that the directory exists and create as required
                    self._projectPath.fetchDir(_dir)
                    # add the folder as relative path
                    tarfile.add(_dir)

        except IOError as es:
            getLogger().error(f'ProjectArchiver.makeArchive: unable to complete archive {archivePath}')
            getLogger().debug(f'ProjectArchiver.makeArchive: {es}')
            archivePath = None

        finally:
            os.chdir(cwd)

        return archivePath

    def restoreArchive(self, archivePath) -> Path:
        """Restore project from archivePath.
        :return: the path to the restored project or None on IOerror
        """
        if archivePath is None or not isinstance(archivePath, (str, Path)):
            raise ValueError(f'Invalid archivePath: expected str or Path instance but got {archivePath}')

        archivePath = aPath(archivePath)
        if not archivePath.exists():
            raise ValueError(f'Invalid archivePath: {archivePath} does not exist')

        cwd = os.getcwd()

        # we unpack in the parent directory of the current project
        # the restored project will derive its name from the archive tar-file, without the .tgz suffix
        _restoredPath = (self._projectPath.parent / archivePath.name).withoutSuffix()
        if not _restoredPath.exists():
            _restoredPath.mkdir()
        os.chdir(_restoredPath)

        try:
            with TarFile.open(archivePath, mode='r') as tarfile:
                tarfile.extractall()

        except IOError:
            getLogger().error(f'ProjectArchiver.restoreArchive: unable to extract archive {archivePath}')
            _restoredPath = None

        finally:
            os.chdir(cwd)

        return _restoredPath

    def __str__(self):
        return f'<ProjectArchiver: {self._projectPath}>'
