"""
Code for Project archiving
Replaced former Api.packageProject and _unpackCcpnTarfile
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-01-21 12:41:19 +0000 (Fri, January 21, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================
import os
import tempfile
import datetime

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

    def __init__(self, project):
        self.project = project

    @property
    def _projectPath(self) -> Path:
        """:return a project.path as a Path instance"""
        return aPath(self.project.path)

    @property
    def archiveDirectory(self) -> Path:
        """:return absolute path to directory with archives as a Path instance
        """
        return self._projectPath.fetchDir(CCPN_ARCHIVES_DIRECTORY)

    @property
    def archives(self) -> list:
        """:return a list of archive (.tgz) tar files"""
        return self.archiveDirectory.listdir(suffix = ARCHIVE_SUFFIX)

    def makeArchive(self) -> Path:
        """Make a new time-stamped archive from project.
        :return absolute path to the new archives as a Path instance
                or None on IOerror
        """
        now = datetime.datetime.now().strftime('-%Y-%m-%d-%H%M%S')
        archivePath = self.archiveDirectory / (self.project.name + \
                                               now + CCPN_DIRECTORY_SUFFIX + ARCHIVE_SUFFIX)

        cwd = os.getcwd()

        try:
            os.chdir(self._projectPath)

            with TarFile.open(archivePath, mode='w:gz') as tarfile:
                for _dir in _directoriesToArchive:
                    tarfile.add(_dir)

        except IOError:
            getLogger().error('ProjectArchiver.makeArchive: unable to complete archive %s' % archivePath)
            archivePath = None

        finally:
            os.chdir(cwd)

        return archivePath

    def restoreArchive(self, archivePath) -> Path:
        """Restore project from archivePath.
        :return the path to the restored project or None on IOerror
        """
        if archivePath is None or not isinstance(archivePath, (str, Path)):
            raise ValueError('Invalid archivePath: expected str or Path instance but got %s' % archivePath)

        archivePath = aPath(archivePath)
        if not archivePath.exists():
            raise ValueError('Invalid archivePath:  %s does not exist' % archivePath)

        cwd = os.getcwd()

        # we unpack in the parent directory of the current project
        # the restored project will derive it's name from the archive tar-file, without the .tgz suffix
        _restoredPath = (self._projectPath.parent / archivePath.name).withoutSuffix()
        if not _restoredPath.exists():
            _restoredPath.mkdir()
        os.chdir(_restoredPath)

        try:
            with TarFile.open(archivePath, mode='r') as tarfile:
                tarfile.extractall()

        except IOError:
            getLogger().error('ProjectArchiver.restoreArchive: unable to extract archive %s' % archivePath)
            _restoredPath = None

        finally:
            os.chdir(cwd)

        return _restoredPath

    def __str__(self):
        return '<ProjectArchiver: %s>' % self.project.pid
