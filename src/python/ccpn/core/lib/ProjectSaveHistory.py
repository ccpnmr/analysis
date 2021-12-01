"""Project-History related  routines

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__dateModified__ = "$dateModified: 2021-12-01 10:03:42 +0000 (Wed, December 01, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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

from ccpn.util.Path import aPath
from ccpn.framework.PathsAndUrls import CCPN_STATE_DIRECTORY, ccpnVersionHistory
from ccpn.framework.Version import VersionString
from ccpn.framework.Application import getApplication
from ccpn.util.Time import now
from ccpn.util.Common import isIterable
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, TraitJsonHandlerBase
from ccpn.util.traits.CcpNmrTraits import List, Path


def getProjectSaveHistory(projectPath):
    """Return a ProjectSaveHistory instance from a project path
    """
    sv = ProjectSaveHistory(projectPath)
    if not sv.exists():
        # pre 3.1.0 ccp project; create one with '3.0.4' as the last (and only) entry
        sv.addSaveRecord('3.0.4', comment='created retroactively')
        sv.save()
    else:
        sv.restore()
    return sv


def newProjectSaveHistory(projectPath):
    """Create and return a new ProjectSaveHistory instance
    """
    sv = ProjectSaveHistory(projectPath)
    version = getApplication().applicationVersion
    sv.addSaveRecord(version, 'created')
    sv.save()
    return sv


class ProjectSaveHistory(CcpNmrJson):
    """A simple class to maintain a project save history as
    a list, to be saved to and restored from a json file
    stores (version, datetime, user, platform, comment) tuples
    """

    classVersion = 1.0  # Json classVersion

    SaveRecord = namedtuple('SaveRecord', 'version datetime user platform comment'.split())

    # The path of the file
    path = Path()

    class RecordListHandler(TraitJsonHandlerBase):
        "Record-list handling by Json"
        def decode(self, obj, trait, value):
            "uses value to generate and set the new (or modified) obj"
            newValue = []
            for item in value:
                record = obj._newRecord(*item)
                newValue.append(record)
            setattr(obj, trait, newValue)

    # the list of entries
    records = List(default_value=[]).tag(saveToJson=True, jsonHandler=RecordListHandler)

    def __init__(self, projectPath):
        """
        :param projectPath: path of project
        """
        super().__init__()

        _path = aPath(projectPath)
        if not _path.exists():
            raise ValueError('Project path "%s" does not exist' % projectPath)
        self.path = _path / CCPN_STATE_DIRECTORY / ccpnVersionHistory

    @property
    def lastSavedVersion(self) -> VersionString:
        """Return the program version of which the project was last saved as a
        VersionString instance
        """
        return VersionString(self.records[-1].version)

    def _newRecord(self, version, datetime=None, user=None, platform=None, comment=None):
        """Return a new record, set default for all None values
        """
        if not isinstance(version, (VersionString, str)):
            raise ValueError('Invalid version parameter "%s"' % version)
        version = VersionString(version)

        if datetime is None:
            datetime = str(now())
        if user is None:
            user = getpass.getuser()
        if platform is None:
            platform = sys.platform
        record = self.SaveRecord( version, datetime, user, platform, comment )
        return record

    def addSaveRecord(self, version=None, comment=None):
        """Add a save record to the history;
        get version from application if None
        :return self
        """
        if version is None:
            version = getApplication().applicationVersion
        record = self._newRecord(version=version, comment=comment)
        self.records.append(record)
        return self

    def exists(self) -> bool:
        """Return true if project save history file exists
        """
        return self.path.exists()

    def save(self):
        """Save to (json) file
        """
        # with self.path.open('w') as fp:
        #     json.dump(self.records, fp, indent=4)
        super().save(self.path)

    def restore(self):
        """Restore self from a json file.
        Convert the version strings of each record to VersionString objects
        """
        if not self.exists():
            raise RuntimeError('Path "%s" does not exist; unable to restore project save history' % self.path)

        # test for old 'ed' files
        with self.path.open('r') as fp:
            records = json.load(fp)

        if isinstance(records, list) and len(records) > 0 and isinstance(records[0], str):
            for item in records:
                self.addSaveRecord(item, 'reconstructed')
        else:
            super().restore(self.path)


    def __getitem__(self, item):
        return self.records[item]

    def __len__(self):
        return len(self.records)

    def __str__(self):
        return '<%s: len=%s, lastSavedVersion=%r>' % \
               (self.__class__.__name__, len(self), self.lastSavedVersion)

# Register this class
ProjectSaveHistory.register()
