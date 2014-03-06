"""NB Must conform to PYthon 2.1. Imporetd in ObjectDomain.
"""

__author__ = 'rhf22'

import os
import sys
import json

from ccpncore.util import Path
from ccpncore.memops.metamodel import Constants as metaConstants

# valid characters for file names
# NB string.ascii_letters and string.digits are not compatible
# with Python 2.1 (used in ObjectDomain)
defaultFileNameChar = '_'
separatorFileNameChar = '+'
validFileNamePartChars = ('abcdefghijklmnopqrstuvwxyz'
                          'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                          + defaultFileNameChar)
validCcpnFileNameChars  = validFileNamePartChars + '-.' + separatorFileNameChar



def convertStringToFileName(fileNameString, validChars=validCcpnFileNameChars,
                            defaultChar=defaultFileNameChar):

  ll = [x for x in fileNameString]
  for ii,char in enumerate(ll):
    if char not in validChars:
      ll[ii] = defaultChar
  #
  return ''.join(ll)

def getCcpFileString(fileNameString):
  """
  Changes an input string to the one used for a component of file names.
  """

  return convertStringToFileName(fileNameString, validFileNamePartChars,
                                   defaultFileNameChar)

def recursiveImport(dirname, modname=None, ignoreModules = None, force=False):
  """ recursively import all .py files
  (not starting with '__' and not containing internal '.' in their name)
  from directory dirname and all its subdirectories, provided they
  contain '__init__.py'
  Serves to check that files compile without error

  modname is the module name (dot-separated) corresponding to the directory
  dirName.
  If modname is None, dirname must be on the pythonPath

  Note that there are potential problems if the files we want are not
  the ones encountered first on the pythonPath
  """

  listdir = os.listdir(dirname)
  try:
    listdir.remove('__init__.py')
  except ValueError:
    if not force:
      return

  files = []

  if ignoreModules is None:
    ignoreModules = []

  if modname is None:
    prefix = ''
  else:
    prefix = modname + '.'

  listdir2 = []
  for name in listdir:
    head,ext = os.path.splitext(name)
    if (prefix + head) in ignoreModules:
      pass
    elif ext == '.py' and head.find('.') == -1:
      files.append(head)
    else:
      listdir2.append(name)

  # import directory and underlying directories
  if modname:
    # Note that files is never empty, so module is lowest level not toplevel
    for ff in files:
      try:
        __import__(modname, {}, {}, [ff])
      except:
        print("WARNING, Import failed for %s.%s" % (modname,ff))

  for name in listdir2:
    newdirname = Path.joinPath(dirname,name)
    if os.path.isdir(newdirname) and name.find('.') == -1:
      recursiveImport(newdirname, prefix + name,ignoreModules)


def getConfigParameter(name):
  """get configuration parameter, from reading configuration file
  """

  file = Path.joinPath(Path.getTopDirectory(),metaConstants.configFilePath)
  print ('###', file)
  dd = json.load(open(file))
  print ('###', list(dd.keys()))
  return dd[
    'configuration'].get(name)


def isWindowsOS():

  return sys.platform[:3].lower() == 'win'