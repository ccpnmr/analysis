"""Scrips to (re)create project sphinx documentation"""

__author__ = 'rhf22'

from ccpncore.util import Path as corePath
import subprocess
import os
import shutil
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
  subprocess.call(ll)

  # then ccpn
  ll = ['ccpn/doc/source/ccpn', 'ccpn']
  ll = ['sphinx-apidoc', '-o'] + [joinPath(pythonDirectory, xx) for xx in ll]
  print( '### running: ' + ' '.join(ll))
  subprocess.call(ll)

  # rebuild docs
  subprocess.call(['make', '-C', docDirectory, 'html'])

if __name__ == '__main__':
  refreshSphinxDocumentation()