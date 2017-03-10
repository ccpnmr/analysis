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
