"""Generation of Sphinx automatic documentation

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
"""Scrips to (re)create project sphinx documentation"""

__author__ = 'rhf22'

import typing

import subprocess
import os
import re
import shutil
from sphinx import apidoc
from ccpn.framework import Version
from ccpn.util import Path as corePath

joinPath = corePath.joinPath


# Relative path to documentation directory
documentationPath = 'doc'

ll = ('__pycache__', 'testing', 'api', 'xml', 'data', 'macros', 'chemBuild', 'Bmrb',
                      'v_\d+_\d+_.*')
skipSubDirectories = re.compile('|'.join(ll))

def refreshSphinxDocumentation():
  """(Re)create sphinx documentation. Locations are hardwired"""

  pythonDirectory = corePath.getPythonDirectory()
  topDirectory = corePath.getTopDirectory()
  docDirectory = joinPath(topDirectory, documentationPath)

  # Direwcteories that should not be documented
  excludeTopDirs = ('chemBuild', '__pycache__')

  inputDirectories = list(x for x in os.scandir(pythonDirectory)
                          if x.is_dir() and x.name not in excludeTopDirs)

  # Remove sphinx-apidoc files
  outputDirs = {}
  for dirEntry in inputDirectories:
    inDirectory = joinPath(docDirectory, 'source', dirEntry.name)
    outputDirs[dirEntry.name] = inDirectory
    if os.path.exists(inDirectory):
      print ("Removing %s" % inDirectory)
      shutil.rmtree(inDirectory)
      os.mkdir(inDirectory)

  # clean builds
  subprocess.call(['make', '-C', docDirectory, 'clean'])

  # Recreate apidoc
  precommand = ['sphinx-apidoc']
  # documentation target - filled in below
  precommand.extend(('-o', 'output TBD'))
  # Put module documentation before submodule documentation:
  precommand.append('--module-first')
  # Project name header:
  precommand.extend(('-A', Version.authors))
  # Project name header:
  precommand.extend(('-V', Version.applicationVersion))
  # Project name header:
  precommand.extend(('-R', Version.revision))

  # Generate documentation - ccpn:
  for dirEntry in inputDirectories:
    module = dirEntry.name
    target = dirEntry.path
    skipDirs = getNamedSubdirectories(target, skipSubDirectories)
    command = precommand + ['-H','CCPN', target] + skipDirs
    if module == 'ccpnmodel':
      # Skip an additional directory
      command.append(os.path.join(target, 'ccpncore', 'memops', 'scripts', 'model'))
    command[2] = outputDirs[module]
    apidoc.main(command)

  # rebuild docs
  subprocess.call(['make', '-C', docDirectory, 'html'])

def getNamedSubdirectories(path, matchExpression=None) -> typing.List[str]:
  """Get a list of all subdirectories of path whose basename starts with one of the prefixes

  Does not look inside the selected subdirectories"""

  result = []

  if matchExpression is not None:
    for root, dirs, files in os.walk(path):
      if matchExpression.fullmatch(os.path.basename(root)) is not None:
        result.append(root)
        del dirs[:]
  #
  return result

if __name__ == '__main__':
  refreshSphinxDocumentation()