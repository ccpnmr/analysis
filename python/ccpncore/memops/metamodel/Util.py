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
""" Utilities to manipulate models (metamodel instances)

To handle inheritance etc. and to extract information not
stored in simply accessible for.

======================COPYRIGHT/LICENSE START==========================

Io.py: MetaModel implementation for CCPN data model and code generation framework

Copyright (C) 2005 Rasmus Fogh (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../license/LGPL.license
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.
 
You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================

"""

#
#  ALl utilities required in OBjectcomean, so working under Python2.1
#

import types
import time
strftime = time.strftime


######################################################################
# hack for Python 2.1 compatibility                                                        #
######################################################################
try:
  junk = True
  junk = False
except NameError:
  globals()['True'] = 1
  globals()['False'] = 0


try:
  # Python 2.1 only
  ListType = types.ListType
  DictType = types.DictType
except AttributeError:
  # PYthon >= 2.5
  ListType = list
  DictType = dict

# Python 2.1 compatibility
try:
  StringType = basestring
except NameError:
  StringType = str


try:
  from lxml import etree as ElementTree
except ImportError:
  try:
    from xml.etree import ElementTree # in python >=2.5
  except ImportError:
    # effbot's pure Python module. Python 2.1. In ObjectDomain only
    from elementtree import ElementTree

try:
  from lxml import ElementInclude
except ImportError:
  try:
    from xml.etree import ElementInclude # in python >=2.5
  except ImportError:
    # effbot's pure Python module. Python 2.1. In ObjectDomain only
    from elementtree import ElementInclude


from ccpncore.memops.metamodel import Constants as metaConstants
MemopsError = metaConstants.MemopsError

def sortByAttribute(objList, tag):
  """ sorts list of objects on value of obj.tag. Returns new list
  """
  # replaces sortByName and sortByQualName
  
  ll = [(getattr(x,tag), x) for x in objList]
  ll.sort()
  return [x[1] for x in ll]

def sortByMethodCall(objList, tag):
  """ sorts list of objects on value of obj.tag(). Returns new list
  """
  # replaces sortByName and sortByQualName
  
  ll = [(getattr(x,tag)(), x) for x in objList]
  ll.sort()
  return [x[1] for x in ll]


def sortByInheritance(objList):
  """ partially sort objList so that supertype comes before subtype
  
  NB signature has changed. No 'container' parameter any longer -
  the routine always sorts the entire list presented to it.
  """
  
  return topologicalSortSubgraph(objList, 'subtypes')


def sortByDataObjTypeDependency(objList):
  """ partially sort objList so that dependent MetaDataObjTypes come after
  the ones they depend on.
  """
  
  return topologicalSortSubgraph(objList, 'subtypes', 
                                 func=dataObjTypeDependencies)
        
        
def checkLinkCircularity(myself, tag):
  """ check for circular relationships in -to-one links
  """
  target = myself
  while target is not None:
    prev = target
    target = getattr(prev,tag)
    if target is myself:
      raise MemopsError("%s is (indirectly) its own %s" 
                                  % (myself,tag))
        
        
def topologicalSortSubgraph(objList, tag, func=getattr):
  """ Assumes that func(obj,tag) is a list of objects, of which
  some (but not all) may be in objList. This corresponds to a subset of
  the nodes of a graph in edge-list representation.
  The function returns a copy of objList sorted so that 
  if 'objA in func(objB,tag)' then objB is before objA in the list.
  If the graph contains cycles an error is raised.
  The algorithm is linear in the number of objects and the number of edges.
  
  See http://www.bitformation.com/art/python_toposort.html or 
  http://www.brpreiss.com/books/opus7/html/page555.html for the sources for this
  algorithm
  """
  
  # set up inLinkCount dictionary
  inLinkCount = {}
  for obj in objList:
    inLinkCount[obj] = 0
  
  # populate inLinkCount dictionary, ignoring out-of-subgraph links
  for obj in objList:
    for obj2 in func(obj,tag):
      if inLinkCount.get(obj2) is not None:
        inLinkCount[obj2] += 1
  
  # prime result list
  result = []
  for obj in objList:
    if not inLinkCount[obj]:
      result.append(obj)
  
  # process nodes in order, expanding result list
  for obj in result:
    del inLinkCount[obj]
    for obj2 in func(obj,tag):
      if inLinkCount.get(obj2) is not None:
        inLinkCount[obj2] -= 1
        if not inLinkCount[obj2]:
          result.append(obj2)
        
  # check for cycles
  if inLinkCount:
    raise MemopsError("Cycles in '%s' graph. Objects involved were %s"
                                % (tag, inLinkCount.keys()))
  #
  return result

def dataObjTypeDependencies(obj, tag):
  """ return dataObjypes that depend on this one. 
  For use in topologicalSortSubgraph
  """
  
  from ccpncore.memops.metamodel.MetaModel import MetaDataObjType
  
  if not isinstance(obj, MetaDataObjType):
    raise MemopsError(
     "dataObjTypeDependencies called with non-MetaDataObjType object %s" % obj)
  
  result = list(getattr(obj, tag))
  for attr in obj.getAllAttributes():
    valueType = attr.valueType
    if isinstance(valueType, MetaDataObjType):
      result.append(valueType)
  #
  return result
  
def parseCardinality(cardString):
  """ parse cardinality string expression and get locard and hicard
  """
  
  result = []
  
  for tag in cardString.strip().split('..'):
    if tag == '*':
      result.append(metaConstants.infinity)
    else:
      try:
        result.append(int(tag))
      except:
        raise MemopsError("inValid content in cardinality string %s"
         % cardString
        )
  
  #
  if result == [metaConstants.infinity]:
    return 0, metaConstants.infinity
  
  elif len(result) == 1:
    return result[0], result[0]
    
  elif len(result) == 2:
    return tuple(result)
    
  else:
    raise MemopsError("inValid cardinality string %s"
     % cardString
    )


class SimpleGuidGenerator:
  """ Generator for simple, low-quality GUIDs 
  (operator_organisation_timeStamp_serial)
  Only appropriate for controlled environments."""
  
  def __init__(self, operator, organisation, initialSerial=1):
    
    self.initialSerial = int(initialSerial)
    self.operator = str(operator)
    self.organisation = str(organisation)
    self.lastTimeSerial = self.initialSerial
    self.lastTimeStamp = ''
    
    # check for characters not allowed in XML storage
    for char in metaConstants.xmlDisallowedChars:
      if char in self.operator:
        raise MemopsError(
         "operator %s contains disallowed character %s"
         % (self.operator,char)
        )
      if char in self.organisation:
        raise MemopsError(
         "organisation %s contains disallowed character %s"
         % (self.operator,char)
        )
  
  def newGuid(self):
    """ generate new GUID. Writeable in XML without character escapes
    """
    
    timeStamp = strftime("%Y-%m-%d-%H:%M:%S")
    
    if timeStamp == self.lastTimeStamp:
      serial = self.lastTimeSerial + 1
      self.lastTimeSerial = serial
    else:
      self.lastTimeStamp = timeStamp
      serial = self.lastTimeSerial = self.initialSerial
      
    return "%s_%s_%s_%05d" % (self.organisation, self.operator, 
                               timeStamp, serial)
  

def topObjLinksByImport(root):
  """get child link names of root in import order
  """
  
  leafPackages = []
  packages = [root.metaclass.container.topPackage()]
  
  # take all packages
  for pp in packages:
    childPackages = pp.containedPackages
    if childPackages:
      packages.extend(childPackages)
    else:
      leafPackages.append(pp)
  
  # sort leafPackages by import (imported before importing)
  ll = topologicalSortSubgraph(leafPackages, 'accessedPackages')
  
  # get desired names
  result = []
  for pp in ll:
    cc = pp.topObjectClass
    if cc is not None:
      pr = cc.parentRole
      if pr is not None:
        ot = pr.otherRole
        result.append(ot.name)
  #
  return result


###########################################################################

# Utilities working on

###########################################################################
  
def getOperation(target, opType, inClass=None, opSubType=None):
  """ get existing operation. If none found return None
  """

  if inClass is None:
    container = target.container
    if container.__class__.__name__ == 'MetaPackage':
      inClass = target
    else:
      inClass = target.container
  
  for op in inClass.getAllOperations():
    if (op.target is target and op.opType == opType
        and op.opSubType == opSubType):
      return op
  #
  return None

###########################################################################
    
def getFuncname(op, inClass=None):
  """ get function calling name for operation
  
  the name is the operation name of the corresponding operation with
  opSubType==None
  """
  if inClass is None:
    inClass = op.container
  
  if not op.__class__.__name__ == 'MetaOperation':
    raise MemopsError("Illegal parameter for getFuncname : %s" % op)
  
  if op.opSubType is not None:
    op = getOperation(op.target, op.opType, inClass)
  if op is None:
    raise MemopsError("No operation with opSubType None corresponds to %s"
     % op.qualifiedName()
    )
  else:
    return op.name
  
###########################################################################

###########################################################################

def getReturnPar(op):
  """ select and return MetaParameter with direction 'return', if any
  """

  for par in op.parameters:
    
    if par.direction == metaConstants.return_direction:
      return par

  return None

###########################################################################

###########################################################################

def getReferenceName(oo, pp=None, subDirs=None):
  """ get name to refer to an object oo from package pp
  If pp is not None the routine will return a short form of the name whenever
  oo is contained within pp.
  Otherwise the routine returns the full import name.
  NB the function is used also to generate names for documentation.
  Unless oo is an object contained within a package, the result will
  not be valid for the purpose of importing oo.
  """
  pathStart = ['ccpncore']

  if pp is not None and (oo.container is pp):
    # pp passed in and oo directly available from pp. Return short name
    name = oo.name
  else:
    # no shortcuts - return fully qualified import name
    qname = oo.qualifiedName()
    if qname == '':
      name = qname
    else:
      if subDirs is None:
        subDirs = []
      pathList = qname.split('.')
      name = '.'.join(pathStart + subDirs + pathList)

  return name

###########################################################################

#  General utilities used in Python 2.1 related code

###########################################################################

def coerceToList(params):
  
  # wrap non-iterables into list
  if params is None:
    params = []
  elif isinstance(params, StringType):
    params = [params]
  else:
    try:
      params = list(params)
    except TypeError:
      params = [params]
  #
  return params

###########################################################################

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


def lowerFirst(s):
  """lowercase first letter
  """
  return s[0].lower() + s[1:]


def upperFirst(s):
  """uppercase first letter
  """
  return s[0].upper() + s[1:]


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
