"""Wrapper level I/O utility functions

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-07-27 12:17:06 +0100 (Tue, July 27, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-24 14:31:06 +0000 (Fri, March 24, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import logging
import os

# NB this import can cause circular imports, but ccpn.__init__ makes sure it does not happen
from ccpn.core.Project import Project
from ccpn.util import Logging
from ccpn.util.Path import aPath
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.lib import ApiPath


def loadProject(path: str, useFileLogger: bool = True, level=logging.INFO) -> Project:
    """Open Project stored at path."""
    project = _loadNmrProject(path, useFileLogger=useFileLogger)
    logger = Logging.getLogger()
    Logging.setLevel(logger, level)
    apiProject = project._wrappedData.root

    if apiProject._upgradedFromV2:
        # Regrettably this V2 upgrade operation must be done at the wrapper level.
        # No good place except here
        for structureEnsemble in project.structureEnsembles:
            data = structureEnsemble.data
            if data is None:
                project._logger.warning("%s has no data. This should never happen")
            else:
                data._containingObject = structureEnsemble

    projectPath = project.path
    oldName = project.name
    newName = aPath(projectPath).basename
    if oldName != newName:
        # Directory name has changed. Change project name and move Project xml file.
        oldProjectFilePath = aPath(ApiPath.getProjectFile(projectPath, oldName))
        if oldProjectFilePath.exists():
            oldProjectFilePath.removeFile()
        apiProject.__dict__['name'] = newName
        apiProject.touch()
        apiProject.save()
    #
    return project


def _loadNmrProject(path: str, nmrProjectName: str = None, useFileLogger: bool = True, level=logging.INFO) -> Project:
    """Open project matching the API Project stored at path. ADVANCED - requires post-processing

    If the API project contains several NmrProjects (rare, and only for legacy projects),
    nmrProjectName lets you select which one to open"""
    path = aPath(path)
    apiProject = apiIo.loadProject(path.asString(), useFileLogger=useFileLogger)

    # # Ad hoc fixes for temporary internal versions (etc.).
    # _fixLoadedProject(apiProject)

    if apiProject is None:
        raise ValueError("No valid project loaded from %s" % path)
    else:
        apiNmrProject = apiProject.fetchNmrProject(name=nmrProjectName)
        apiNmrProject.initialiseData()
        apiNmrProject.initialiseGraphicsData()
        return Project(apiNmrProject)


def newProject(name: str = 'default', path: str = None, useFileLogger: bool = True, level=logging.INFO) -> Project:
    """Make RAW new project, putting underlying data storage (API project) at path"""
    apiProject = apiIo.newProject(name, path, overwriteExisting=True,
                                  useFileLogger=useFileLogger)
    if apiProject is None:
        raise ValueError("New project could not be created (overlaps exiting project?) name:%s, path:%s"
                         % (name, path))
    else:
        apiNmrProject = apiProject.fetchNmrProject()
        apiNmrProject.initialiseData()
        apiNmrProject.initialiseGraphicsData()
        project = Project(apiNmrProject)
        logger = Logging.getLogger()
        Logging.setLevel(logger, level)
        return project
