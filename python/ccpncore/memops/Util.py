__author__ = 'rhf22'



try:
  from  xml.etree import ElementTree # in python >=2.5
except ImportError:
  # effbot's pure Python module. Python 2.1. In ObjectDomain only
  from elementtree import ElementTree

try:
  from  xml.etree import ElementInclude # in python >=2.5
except ImportError:
  # effbot's pure Python module. Python 2.1. In ObjectDomain only
  from elementtree import ElementInclude



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
    result = {}
    doneDict[key] = result

    for kk,val in dd.items():

      if type(val) == DictType:
        result[kk] = semideepcopy(val, doneDict)

      elif type(val) == ListType:
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
      nchars = nchars + i
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