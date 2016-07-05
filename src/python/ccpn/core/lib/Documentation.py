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

from ccpn.core.lib import Version
from ccpn.util import Path as corePath
import subprocess
import os
import shutil
from sphinx import apidoc

joinPath = corePath.joinPath


# Relative path to documentation directory
documentationPath = 'doc'

def refreshSphinxDocumentation():
  """(Re)create sphinx documentation. Locations are hardwired"""

  pythonDirectory = corePath.getPythonDirectory()
  topDirectory = corePath.getTopDirectory()
  docDirectory = joinPath(topDirectory, documentationPath)

  # Remove sphinx-apidoc files
  outputDirs = {}
  for ss in ('ccpn',):
  # for ss in ('ccpn', 'ccpnmodel'):
    inDirectory = joinPath(docDirectory, 'source', ss)
    outputDirs[ss] = inDirectory
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
  # PUt module documentation before submodule documentation:
  precommand.append('--module-first')
  # Project name header:
  precommand.extend(('-A', Version.authors))
  # Project name header:
  precommand.extend(('-V', Version.applicationVersion))
  # Project name header:
  precommand.extend(('-R', Version.revision))

  # Generate documentation - ccpn:
  module = 'ccpn'
  target = joinPath(pythonDirectory, module)
  skipDirs = getNamedSubdirectories(target, 'testing')
  command = precommand + ['-H','CCPN', target] + skipDirs
  # Additional directories to skip
  command.append(joinPath(pythonDirectory, 'ccpn/macros'))
  command[2] = outputDirs[module]
  # print ('\n\n@~@~', command)
  apidoc.main(command)


  # # Generate documentation - ccpn:
  # module = 'ccpnmodel'
  # target = joinPath(pythonDirectory, module)
  # skipDirs = getNamedSubdirectories(target, ('testing', 'v_'))
  # command = precommand + ['-H', 'CCPN storage implementation', target] + skipDirs
  # # Additional directories to skip
  # command.append(joinPath(pythonDirectory, 'ccpnmodel/ccpncore/memops'))
  # command.append(joinPath(pythonDirectory, 'ccpnmodel/ccpncore/xml'))
  # command[2] = outputDirs[module]
  # # print ('\n\n@~@~', command)
  # apidoc.main(command)


  # rebuild docs
  subprocess.call(['make', '-C', docDirectory, 'html'])

def getNamedSubdirectories(path, prefixes=()) -> typing.List[str]:
  """Get a list of all subdirectories of path whose basename starts with one of the prefixes

  Does not look inside the selected subdirectories"""

  if not prefixes:
    return

  result = []

  for root, dirs, files in os.walk(path):
    for ss in prefixes:
      if os.path.basename(root).startswith(ss):
        result.append(root)
        del dirs[:]
  #
  return result

if __name__ == '__main__':
  refreshSphinxDocumentation()