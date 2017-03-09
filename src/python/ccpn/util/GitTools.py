from subprocess import Popen, PIPE
from typing import Optional
from os import getcwd

from ccpn.framework.PathsAndUrls import ccpnCodePath
from ccpn.framework.PathsAndUrls import analysisAssignPath
from ccpn.framework.PathsAndUrls import analysisScreenPath
from ccpn.framework.PathsAndUrls import analysisStructurePath
from ccpn.framework.PathsAndUrls import analysisMetabolomicsPath
from ccpn.framework.PathsAndUrls import ccpnmodelPythonPath


def getCurrentGitCommit(cwd:Optional[str]=None) -> str:
  '''
  Get the current git commit hash.

  This function returns the git commit hash for the repository where it's called.
  '''

  git_command = ['git', 'rev-parse', 'HEAD']

  if cwd is None:
    cwd = getcwd()

  git_query = Popen(git_command, cwd=cwd, stdout=PIPE, stderr=PIPE)
  (git_status, error) = git_query.communicate()

  if git_query.poll() == 0:
    return(git_status.strip())


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
      commits[k] = str(getCurrentGitCommit(v))[2:-1]
    except FileNotFoundError:
      pass

  return commits