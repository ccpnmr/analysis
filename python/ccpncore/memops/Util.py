"""NB Must conform to PYthon 2.1. Imporetd in ObjectDomain.
"""
__author__ = 'rhf22'

import types
import os
from ccpncore.util import Path

######################################################################
# hack for Python 2.1 compatibility                                                        #
######################################################################
try:
  junk = True
  junk = False
except NameError:
  dd = globals()
  dd['True'] = 1
  dd['False'] = 0
  del dd


try:
  # Python 2.1 only
  ListType = types.ListType
  DictType = types.DictType
except AttributeError:
  # PYthon >= 2.5
  ListType = list
  DictType = dict


try:
  from xml.etree import ElementTree # in python >=2.5
except ImportError:
  # effbot's pure Python module. Python 2.1. In ObjectDomain only
  from elementtree import ElementTree

try:
  from xml.etree import ElementInclude # in python >=2.5
except ImportError:
  # effbot's pure Python module. Python 2.1. In ObjectDomain only
  from elementtree import ElementInclude



def upperFirst(s):
  """uppercase first letter
  """
  return s[0].upper() + s[1:]

def lowerFirst(s):
  """lowercase first letter
  """
  return s[0].lower() + s[1:]


def semideepcopy(dd, doneDict=None):
  """ does a semi-deep copy of a nested dictionary, for copying mappings.
  Dictionaries are copied recursively, .
  Lists are copied, but not recursively.
  In either case a single copy is made from a single object
  no matter how many times it appears.
  Keys and other values are passed unchanged
  """

  if doneDict is None:
    doneDict = {}

  key = id(dd)
  result = doneDict.get(key)
  if result is None:
    doneDict[key] = result = {}

    for kk,val in dd.items():

      if isinstance(val, DictType):
        result[kk] = semideepcopy(val, doneDict)

      elif isinstance(val, ListType):
        key2 = id(val)
        newval = doneDict.get(key2)
        if newval is None:
          newval = val[:]
          doneDict[key2] = newval

        result[kk] = newval

      else:
        result[kk] = val
  #
  return result


def compactStringList(stringList, separator='', maxChars=80):
  """ compact stringList into shorter list of longer strings,
  each either made from a single start string, or no longer than maxChars

  From previous breakString function.
  Modified to speed up and add parameter defaults, Rasmus Fogh 28 Aug 2003
  Modified to split into two functions
  and to add separator to end of each line, Rasmus Fogh 12 Sep 03
  Modified to separate string breaking from list modification
  Rasmus Fogh 29/6/06
  Modified to return single-element lists unchanged
  Rasmus Fogh 29/6/06
  """

  result = []

  if not stringList:
    return result
  elif len(stringList) ==1:
    return stringList[:]

  seplength = len(separator)

  nchars = len(stringList[0])
  start=0
  for n in range(1,len(stringList)):
    i = len(stringList[n])
    if nchars + i + (n-start)*seplength > maxChars:
      result.append(separator.join(stringList[start:n] + ['']))
      start = n
      nchars = i
    else:
      nchars += i
  result.append(separator.join(stringList[start:len(stringList)]))

  return result



def breakString(text, separator=' ', joiner='\n', maxChars=72):

  """ Splits text on separator and then joins pieces back together using joiner
      so that each piece either single element or no longer than maxChars

      Modified to speed up and add parameter defaults, Rasmus Fogh 28 Aug 2003
      Modified to split into two functions
      and to add separator to end of each line
      Modified to separate string breaking from list modification
      Rasmus Fogh 29/6/06
      Added special case for text empty or None
      Rasmus Fogh 07/07/06
  """

  if not text:
    return ''

  t = compactStringList(text.split(separator), separator=separator,
                        maxChars=maxChars)

  return joiner.join(t)



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

