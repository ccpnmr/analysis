"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
"""Scrips to (re)create project sphinx documentation"""

__author__ = 'rhf22'

from ccpncore.util import Path as corePath
import subprocess
import os
import shutil
from sphinx import apidoc

joinPath = corePath.joinPath


# Relative path to documentation directory
documentationPath = 'ccpn/doc'

def refreshSphinxDocumentation():
  """(Re)create sphinx documentation. Locations are hardwired"""

  pythonDirectory = corePath.getPythonDirectory()
  docDirectory = joinPath(pythonDirectory, documentationPath)

  # Remove sphinx-apidoc files
  for ss in ('ccpn', 'ccpncore'):
    inDirectory = joinPath(docDirectory, 'source', ss)
    if os.path.exists(inDirectory):
      shutil.rmtree(inDirectory)
    os.mkdir(inDirectory)

  # clean builds
  subprocess.call(['make', '-C', docDirectory, 'clean'])

  # Recreate apidoc
  # The parameters are command, option, output directory, module to document, dirs to skip
  # First ccpncore
  ll = ['ccpn/doc/source/ccpncore', 'ccpncore',
        'ccpncore/api', 'ccpncore/memops/', 'ccpncore/testing/', 'ccpncore/xml/']
  ll = ['sphinx-apidoc', '-o'] + [joinPath(pythonDirectory, xx) for xx in ll]
  print( '### running: ' + ' '.join(ll))
  apidoc.main(ll)

  # then ccpn
  ll = ['ccpn/doc/source/ccpn', 'ccpn']
  ll = ['sphinx-apidoc', '-o'] + [joinPath(pythonDirectory, xx) for xx in ll]
  print( '### running: ' + ' '.join(ll))
  apidoc.main(ll)
  #subprocess.call(ll)

  # rebuild docs
  subprocess.call(['make', '-C', docDirectory, 'html'])

if __name__ == '__main__':
  refreshSphinxDocumentation()