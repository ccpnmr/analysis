#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:58 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-03-10 10:27:30 +0000 (Fri, March 10, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from subprocess import Popen, PIPE
from typing import Optional
from os import getcwd

from ccpn.framework.PathsAndUrls import ccpnCodePath
from ccpn.framework.PathsAndUrls import analysisAssignPath
from ccpn.framework.PathsAndUrls import analysisScreenPath
from ccpn.framework.PathsAndUrls import analysisStructurePath
from ccpn.framework.PathsAndUrls import analysisMetabolomicsPath
from ccpn.framework.PathsAndUrls import ccpnmodelPythonPath


def runGitCommand(command: str, workingDir: Optional[str] = None) -> str:
    if workingDir is None:
        workingDir = getcwd()

    gitCommand = ['git', ] + command.split()
    gitQuery = Popen(gitCommand, cwd=workingDir, stdout=PIPE, stderr=PIPE)
    gitStatus, error = gitQuery.communicate()
    if gitQuery.poll() == 0:
        return gitStatus.decode("utf-8").strip()


def getCurrentGitCommit(workingDir: Optional[str] = None) -> str:
    '''
    Get the current git commit hash.
    This function returns the git commit hash for the repository where it's called.
    '''
    return runGitCommand('rev-parse HEAD', workingDir=workingDir)


def getCurrentGitAuthor(workingDir: Optional[str] = None) -> str:
    '''
    Get the current git commit hash.
    This function returns the git commit hash for the repository where it's called.
    '''
    return runGitCommand('config user.name', workingDir=workingDir)


def getAllRepositoriesGitCommit() -> dict:
    '''
    Return a dictionary of the current commit hashes for all the CCPN repositories
    '''
    repos = {'analysis'            : ccpnCodePath,
             'ccpnmodel'           : ccpnmodelPythonPath,
             'AnalysisAssign'      : analysisAssignPath,
             'AnalysisScreen'      : analysisScreenPath,
             'AnalysisMetabolomics': analysisMetabolomicsPath,
             'AnalysisStructure'   : analysisStructurePath,
             }

    commits = {}
    for k, v in repos.items():
        try:
            commits[k] = getCurrentGitCommit(v)
        except FileNotFoundError:
            pass

    return commits
