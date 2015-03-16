"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
"""General path handling utilities. NB must be python 2.1 complieant!!!"""


#
# Convenient I/O functions
#

import os
import shutil
import sys
import glob

# NB necessary compatibility
# - this is imported to Python 2.1 (in ObjectDomain)
aliasTrue = not 0
aliasFalse = not aliasTrue

dirsep = '/'
# note, cannot just use os.sep below because can have window file names cropping up on unix machines
winsep = '\\'

def normalisePath(path, makeAbsolute=aliasFalse):
  """
  Normalises the path, e.g. removes redundant .. and slashes and
  makes sure path uses '/' rather than '\\' as can happen on Windows.
  """

  if os.sep == winsep:
    path = path.replace(dirsep, winsep)
    path = os.path.normpath(path)
    path = path.replace(winsep, dirsep)
  else:
    path = path.replace(winsep, dirsep)
    path = os.path.normpath(path)

  if makeAbsolute:
    if path and path[0] != dirsep:
      path = joinPath(os.getcwd(), path)

  return path

def unnormalisePath(path):
  """
  On Unix does nothing, on Windows replaces '/' with '\\'/
  """

  if os.sep != '/':
    path = path.replace('/', os.sep)

  return path

def joinPath(*args):
  """
  The same as os.path.join but normalises the result.
  """

  return normalisePath(os.path.join(*args))

def splitPath(path):
  """
  The same as os.path.split but with normalisation taken into account.
  """

  (head, tail) = os.path.split(unnormalisePath(path))
  head = normalisePath(head)

  return head, tail

def converseSplitPath(path):
  """
  Similar to splitPath but with head being the top directory and tail being the rest.
  """

  pair = splitPath(path)
  head = None
  tail = ''
  while pair[0] and pair[0] not in ('.', '/'):
    head = pair[0]
    tail = joinPath(pair[1], tail)
    pair = splitPath(head)

  if head is None:
    (head, tail) = pair

  return head, tail

def getTopDirectory():
  """
  Returns the 'top' directory of the contaiiining repository (ccpnv3).
  """

  return os.path.dirname(getPythonDirectory())

def setTopDirectory(newTopDirectory):

  """
  Set a new 'top' directory of the whole code and data structure.
  This is so that you can swap between different implementations.
  WARNING: This function should only be used by experts.
  """

  # There is no perfect way at getting at keys in sys.modules which
  # need to be deleted, because there are some funny keys for which
  # sys.modules[key] is None (otherwise you could use the __file__
  # attribute of the module).  So look at the directories in
  # the old python directory and see which of those have an __init__.py
  # inside and assume that those are the modules we are trying to remove
 
  newTopDirectory = normalisePath(newTopDirectory)
  oldTopDirectory = getTopDirectory()
  oldPythonDirectory = getPythonDirectory()
  # Below is a bit dangerous; could have used os.path.basename(oldPythonDirectory) instead
  # if could guarantee that python directory is only one directory below top directory
  n = len(oldTopDirectory)
  newPythonDirectory = newTopDirectory + oldPythonDirectory[n:]

  moduleNames = []
  files = os.listdir(oldPythonDirectory)
  for file in files:
    fullfile = joinPath(oldPythonDirectory, file)
    if os.path.isdir(fullfile):
      if '__init__.py' in os.listdir(fullfile):
        moduleNames.append(file)
 
  # Below does not necessarily find all paths we want because symbolic
  # links mean that sometimes the wrong names are stored in sys.paths

  paths = []
  for path in sys.path:
    path = normalisePath(path)
    if path == oldTopDirectory or path.startswith(oldTopDirectory + '/'):
      paths.append(path)

  sys_modules = sys.modules
  sys_path = sys.path

  keys = sys_modules.keys()
  for key in keys:
    for name in moduleNames:
      if key == name or key.startswith(name + '.'):
        del sys_modules[key]
        break

  for path in paths:
    sys_path.remove(path)

  # Now that have deleted what we can from sys.modules and sys.paths, put in
  # new information in sys.paths about newTopDirectory

  sys_path.insert(0, newPythonDirectory)

def getPythonDirectory():

  """
  Returns the 'top' python directory, the one on the python path.
  """
  
  func = os.path.dirname
  
  return func(func(func(os.path.abspath(__file__))))

def getCcpnModelDirectory():

  """
  Returns the directory containing the ccpnmodel, python and testdata directory
  for the ccpnmodel code tree
  """
  import ccpnmodel
  func = os.path.dirname

  return func(func(func(os.path.abspath(ccpnmodel.__file__))))


def getDirectoryFromTop(*args):
  """Get directory with path given by successive path sections args, starting at top"""

  return joinPath(getTopDirectory(), *args)


def getDataDirectory(*args):

  return getDirectoryFromTop('data')

def removePath(path):
  """Removes path whether file or directory, taking into account whether symbolic link.
  """

  if not os.path.exists(path):
    return

  if os.path.isfile(path) or os.path.islink(path):
    os.remove(path)
  else:
    shutil.rmtree(path)


def commonSuperDirectory(*fileNames):
  """ Find lowest directory that contains all files in list
  NB does not normalise file names.

  Input: a list of file names
  Output: lowest directory that contains all files. Does *not* end with a file
  """
  return os.path.dirname(os.path.commonprefix(fileNames))

def suggestFileLocations(fileNames, startDir=None):
  """ From a list of files, return a common superdirectory and a list of
  relative file names. If any of the files do not exist, search for an
  alternative superdirectory that does contain the set of relative file names.
  Searches in either a auperdirectory of the starting/current directory,
  or in a direct subdirectory.

  Input: list of file names
  Output: Superdirectory, list of relative file names.
          If no suitable location is found, superdirectory is returned as None
  """

  if not fileNames:
    return None, []

  # set up startDir
  if startDir is None:
    startDir = os.getcwd()
  startDir = normalisePath(startDir, makeAbsolute=aliasTrue)

  # find common baseDir and paths
  files = [normalisePath(fp, makeAbsolute=aliasTrue) for fp in fileNames]
  baseDir = commonSuperDirectory(*files)
  prefix = os.path.join(baseDir, '')
  lenPrefix = len(prefix)
  paths = [fp[lenPrefix:] for fp in files]

  if [fp for fp in files if not os.path.exists(fp)]:
    # some file not found.

    # look in superdirectories
    tail = 'junk'
    baseDir = startDir
    while tail:
      for path in paths:
        fp = os.path.join(baseDir, path)
        if not os.path.exists(fp):
          # a file is not found. try new baseDir
          break
      else:
        # this one is OK - stop searching
        break
      #
      baseDir, tail = os.path.split(baseDir)

    else:
      # No success - try in a subdirectory (one level) of startDir
      matches = glob.glob(os.path.join(startDir, '*', paths[0]))
      for aMatch in matches:
        baseDir = normalisePath(aMatch[:-len(paths[0])])
        for path in paths:
          fp = os.path.join(baseDir, path)
          if not os.path.exists(fp):
            # a file is not found. try new baseDir
            break
        else:
          # this one is OK - stop searching
          break
      else:
        # we give up
        baseDir = None
  #
  return baseDir, paths

def checkFilePath(filePath, allowDir=aliasTrue):

  msg = ''
  isOk = aliasTrue

  if not filePath:
    isOk = aliasFalse

  elif not os.path.exists(filePath):
    msg = 'Location "%s" does not exist' % filePath
    isOk = aliasFalse

  elif not os.access(filePath, os.R_OK):
    msg = 'Location "%s" is not readable' % filePath
    isOk = aliasFalse

  elif os.path.isdir(filePath):
    if allowDir:
      return isOk, msg
    else:
      msg = 'Location "%s" is a directory' % filePath
      isOk = aliasFalse

  elif not os.path.isfile(filePath):
    msg = 'Location "%s" is not a regular file' % filePath
    isOk = aliasFalse

  elif os.stat(filePath).st_size == 0:
    msg = 'File "%s" is of zero size '% filePath
    isOk = aliasFalse

  return isOk, msg
