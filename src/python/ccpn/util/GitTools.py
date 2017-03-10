# =========================================================================================
# Licence, Reference and Credits
# =========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 02:12:40 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, TJ Ragan, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

# =========================================================================================
# Last code modification:
# =========================================================================================
__author__ = "$Author: rhf22 $"
__date__ = "$Date: 2016-05-16 02:12:40 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 200 $"

# =========================================================================================
# Start of code
# =========================================================================================

from subprocess import Popen, PIPE
from typing import Optional
from os import getcwd

from ccpn.framework.PathsAndUrls import ccpnCodePath
from ccpn.framework.PathsAndUrls import analysisAssignPath
from ccpn.framework.PathsAndUrls import analysisScreenPath
from ccpn.framework.PathsAndUrls import analysisStructurePath
from ccpn.framework.PathsAndUrls import analysisMetabolomicsPath
from ccpn.framework.PathsAndUrls import ccpnmodelPythonPath


def runGitCommand(command:str, workingDir:Optional[str]=None) -> str:
  if workingDir is None:
    workingDir = getcwd()

  gitCommand = ['git', ] + command.split()
  gitQuery = Popen(gitCommand, cwd=workingDir, stdout=PIPE, stderr=PIPE)
  gitStatus, error = gitQuery.communicate()
  if gitQuery.poll() == 0:
    return gitStatus.decode("utf-8").strip()


def getCurrentGitCommit(workingDir:Optional[str]=None) -> str:
  '''
  Get the current git commit hash.
  This function returns the git commit hash for the repository where it's called.
  '''
  return runGitCommand('rev-parse HEAD', workingDir=workingDir)


def getCurrentGitAuthor(workingDir:Optional[str]=None) -> str:
  '''
  Get the current git commit hash.
  This function returns the git commit hash for the repository where it's called.
  '''
  return runGitCommand('config user.name', workingDir=workingDir)


def getAllRepositoriesGitCommit() -> dict:
  '''
  Return a dictionary of the current commit hashes for all the CCPN repositories
  '''
  repos = {'analysis': ccpnCodePath,
           'ccpnmodel': ccpnmodelPythonPath,
           'AnalysisAssign': analysisAssignPath,
           'AnalysisScreen': analysisScreenPath,
           'AnalysisMetabolomics': analysisMetabolomicsPath,
           'AnalysisStructure': analysisStructurePath,
          }

  commits = {}
  for k,v in repos.items():
    try:
      commits[k] = getCurrentGitCommit(v)
    except FileNotFoundError:
      pass

  return commits
