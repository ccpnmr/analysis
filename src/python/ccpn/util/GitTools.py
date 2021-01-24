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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-01-24 17:58:26 +0000 (Sun, January 24, 2021) $"
__version__ = "$Revision: 3.0.3 $"
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
    """
    Return a dictionary of the current commit hashes for all the CCPN repositories
    """
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
