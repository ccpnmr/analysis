"""
Various Project related routines
"""
from __future__ import annotations

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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-01-24 13:15:55 +0000 (Tue, January 24, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2023-01-19 11:47:50 +0000 (Thu, January 19, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
import sys

from ccpn.util import Logging
from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath, Path

from ccpn.framework.Application import getApplication

from ccpn.framework.PathsAndUrls import \
    CCPN_API_DIRECTORY, \
    CCPN_DIRECTORY_SUFFIX, \
    CCPN_BACKUP_SUFFIX, \
    ccpnmodelDataPythonPath, \
    userCcpnDataPath, \
    CCPN_BACKUPS_DIRECTORY, \
    CCPN_LOGS_DIRECTORY


from ccpnmodel.ccpncore.memops.metamodel import Constants as metaConstants
MEMOPS                  = metaConstants.modellingPackageName
IMPLEMENTATION          = metaConstants.implementationPackageName


def checkProjectName(name, correctName=True) -> (str, None):
    """Checks name

    :param name: name to be checked
    :param correctName: flag to correct
    :return: name (optionally corrected) or None
    """
    from ccpn.core.Project import Project

    newName = re.sub('[^0-9a-zA-Z]+', '_', name)
    if name != newName and not correctName:
        return None

    if len(newName) > Project._MAX_PROJECT_NAME_LENGTH:
        if not correctName:
            return None
        newName = newName[0:32]

    return newName


def isV3project(path) -> bool:
    """Convenience method:
    :return True is path is (appears to be?) a V3 project"""
    path = aPath(path)
    if not path.is_dir(): return False
    if path.suffix != CCPN_DIRECTORY_SUFFIX: return False
    if path.name == CCPN_API_DIRECTORY: return False
    if not (path / CCPN_API_DIRECTORY / MEMOPS / IMPLEMENTATION).exists(): return False
    # it is a directory with .ccpn suffix, not named ccpnv3, that has ccpnv3/memops/implementation subdirectory,
    # so we assume it to be a V3 project directory.
    return True


def isV2project(path) -> bool:
    """Convenience method:
    :return True is path is (appears to be?) a V2 project"""
    path = aPath(path)
    if not path.is_dir(): return False
    if isV3project(path): return False
    if not (path / MEMOPS / IMPLEMENTATION).exists(): return False
    # it is a directory which is not a V3project directory , that has memops/implementation subdirectory,
    # so we assume it to be a V2 project directory.
    return True


def createLogger(project):
    """Create a logger for project
    Adapted from Api.py
    """

    # Cannot use the back linkage to application, as this routine is called during Project initialisation
    _app = getApplication()

    logger = Logging.createLogger(_app.applicationName,
                                  project.projectPath / CCPN_LOGS_DIRECTORY,
                                  stream=sys.stderr,
                                  level = _app._debugLevel
                                  )

    return logger
