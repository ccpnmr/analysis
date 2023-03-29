"""Project-History related  routines

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-03-28 18:46:14 +0100 (Tue, March 28, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2021-11-10 10:28:41 +0000 (Wed, November 10, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import sys
import getpass
from collections import namedtuple

from ccpn.framework.PathsAndUrls import CCPN_STATE_DIRECTORY, ccpnVersionHistory
from ccpn.framework.Version import VersionString, applicationVersion
from ccpn.util.Time import now
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, TraitJsonHandlerBase
from ccpn.util.traits.CcpNmrTraits import List, Path


def getProjectSaveHistory(projectPath):
    """Return a ProjectSaveHistory instance from a project path, or default single-entry if it doesn't exist.
    File is not created.
    """
    sv = ProjectSaveHistory(projectPath)
    if not sv.exists():
        # pre 3.1.0 ccp project; create one with '3.0.4' as the last (and only) entry
        sv.addSaveRecord('3.0.4', comment='created retroactively')
    else:
        sv.restore()
    return sv


def fetchProjectSaveHistory(projectPath, readOnly=True):
    """Return a ProjectSaveHistory instance from a project path.
    Creates a default single-entry instance if it doesn't exist and creates file
    """
    sv = ProjectSaveHistory(projectPath, create=not readOnly)
    if not sv.exists():
        # pre 3.1.0 ccp project; create one with '3.0.4' as the last (and only) entry
        sv.addSaveRecord('3.0.4', comment='created retroactively')
        if not readOnly:
            sv.save()

    else:
        sv.restore()
    return sv


def newProjectSaveHistory(projectPath):
    """Create and return a new ProjectSaveHistory instance
    """
    sv = ProjectSaveHistory(projectPath, create=True)
    sv.addSaveRecord(applicationVersion, comment='created')
    sv.save()
    return sv


class ProjectSaveHistory(CcpNmrJson):
    """A simple class to maintain a project save history as
    a list, to be saved to and restored from a json file
    stores (version, datetime, user, platform, comment) tuples
    """

    classVersion = 1.0  # Json classVersion

    SaveRecord = namedtuple('SaveRecord', 'version datetime user platform comment')

    # The path of the file
    projectPath = Path()
    _path = Path()


    class RecordListHandler(TraitJsonHandlerBase):
        """Record-list handling by Json"""

        def decode(self, obj, trait, value):
            """uses value to generate and set the new (or modified) obj"""
            newValue = []
            for item in value:
                record = obj._newRecord(*item)
                newValue.append(record)
            setattr(obj, trait, newValue)


    # the list of entries
    records = List(default_value=[]).tag(saveToJson=True, jsonHandler=RecordListHandler)

    def __init__(self, projectPath, create=False):
        """
        :param projectPath: path of project
        """
        super().__init__()

        self.records = []  # to stop the singleton behaviour
        self.projectPath = _projectPath = aPath(projectPath)

        if not _projectPath.exists():
            getLogger().debug(f'Project path "{projectPath}" does not exist')

        self._path = aPath(CCPN_STATE_DIRECTORY) / ccpnVersionHistory

        if create:
            try:
                _projectPath.fetchDir(CCPN_STATE_DIRECTORY)

            except (PermissionError, FileNotFoundError):
                getLogger().warning(f'Child-folder {self._path} may be read-only')

    @property
    def lastSavedVersion(self) -> VersionString:
        """Return the program version of which the project was last saved as a
        VersionString instance
        """
        return VersionString(self.records[-1].version)

    @property
    def path(self):
        return self.projectPath / self._path

    def _newRecord(self, version, datetime=None, user=None, platform=None, comment=None):
        """Return a new record, set default for all None values
        """
        if not isinstance(version, (VersionString, str)):
            raise ValueError(f'Invalid version parameter "{version}"')
        version = VersionString(version)

        if datetime is None:
            datetime = str(now())
        if user is None:
            user = getpass.getuser()
        if platform is None:
            platform = sys.platform
        return self.SaveRecord(version, datetime, user, platform, comment)

    def addSaveRecord(self, version=None, comment=None):
        """Add a save record to the history;
        get version from application if None
        :return self
        """
        if version is None:
            version = applicationVersion
        record = self._newRecord(version=version, comment=comment)
        self.records.append(record)
        return self

    def exists(self) -> bool:
        """Return true if project save history file exists
        """
        # check no shenanigans with the sub-path
        # validRelative = aPath(self.path).is_relative_to(self.projectPath)
        rr = aPath(self.path).asString()
        ll = aPath(self.projectPath).asString()
        validRelative = bool(rr.startswith(ll) and len(rr[len(ll):]) > 1)
        return self._path.asString() != '.' and validRelative and self.path.exists()

    def save(self, *args, **kwds):
        """Save to (json) file
        """
        try:
            self.projectPath.fetchDir(CCPN_STATE_DIRECTORY)
            self._path = aPath(CCPN_STATE_DIRECTORY) / ccpnVersionHistory

            super().save(self.path)

        except (PermissionError, FileNotFoundError):
            getLogger().warning(f'Child-folder {self._path} may be read-only')

    def restore(self, **kwds):
        """Restore self from a json file.
        Check for prior 'ed'-formatted file
        :return self
        """
        if not self.exists():
            raise RuntimeError(
                    f'Path "{self.path}" does not exist; unable to restore project save history'
                    )

        try:
            if self._path.asString() == '.':
                getLogger().debug('Folder may be read-only')
            else:
                super().restore(self.path)

        except (RuntimeError, ValueError):

            # test for old 'ed' files
            with self.path.open('r') as fp:
                records = json.load(fp)

            self.records = []
            if isinstance(records, list) and len(records) > 0 and isinstance(records[0], str):
                for item in records:
                    self.addSaveRecord(item, 'reconstructed')
            else:
                self.addSaveRecord('3.0.4', 'created retroactively')
            self.save()

        return self

    def __getitem__(self, item):
        return self.records[item]

    def __len__(self):
        return len(self.records)

    def __str__(self):
        return '<%s: len=%s, lastSavedVersion=%r>' % \
            (self.__class__.__name__, len(self), self.lastSavedVersion)


# Register this class
ProjectSaveHistory.register()
