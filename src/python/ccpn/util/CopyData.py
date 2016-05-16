"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
"""Code for copying CCPN data model objects"""

  
# miscellaneous useful functions

import os
import time

from ccpn.util import Logging


def copySubTree(sourceObj, newParent, maySkipCrosslinks:bool=False,
                topObjectParameters:dict=None, objectMap:dict=None):
  """ Copy an api object and all its descendants within or between projects

  :param sourceObj: CCPN api object to be copied
  :param newParent: parent for the copied object
  :param bool maySkipCrosslinks: Whether to skip crosslinks if copying them it not possible.
  :param dict topObjectParameters: parameters to be passed to copy of source object
  :param dict objectMap: oldObject:newObject mappings to use as targets for crosslinks
  :result: copy of source object

  
  (Parts of) crosslinks to objects within the subtree are copied to
  links to the new object copies;
  (Parts of) crosslinks to objects not within the subtree are copied to
  links to the old objects, provided this can be done without cutting 
  pre-existing links.
  If the above will not work *and* maySkipCrosslinks is True, the routine
  tries to set the crosslink using only the objects within the subtree.
  If none of the above works, an error is thrown.
  
  The key,val pairs in the topObjectParameters dictionary are passed to 
  the top object constructor, and the pre-existing values in the sourceObj 
  are ignored. This can be used to set new values for the keys of sourceObj.
  
  If the top object has 'serial' as the key and no valid serial is passed in
  topObjectParameters, the routine will set the serial to the next available
  value.
  
  Note that the function first builds all objects, then connects crosslinks,
  then connects parent-to-child links. Finally all notifiers are called but in
  random order. If there is an error the routine tries to delete all created
  objects before re-raising the original error. A failed function call may
  consume serial numbers if the key of the sourceObj is 'serial'. Also, there is
  a relatively high bug risk, as is always the case with functions that have to
  clean up after an error. 
  """

  from ccpnmodel.ccpncore.memops.metamodel.MetaModel import MemopsError
  if sourceObj.root is sourceObj:
    raise MemopsError("copySubTree cannot be used to copy entire projects")

  # Copy objectMap as it is modified lower down
  # NB topObjectParameters may be modified too if the top object has a serial key
  # but in that case we need to keep teh modification for redo
  oldToNew = None if objectMap is None else objectMap.copy()

  undo = sourceObj.root._undo
  if undo is not None:
    undo.increaseBlocking()

  try:
    result = _transferData(newParent, sourceObj, oldToNew=oldToNew,
                           targetObjParams=topObjectParameters,
                           ignoreMissing=maySkipCrosslinks, useOptLinks=True)
  finally:
    if undo is not None:
      undo.decreaseBlocking()

  if undo is not None and result is not None:
    undo.newItem(result.delete, copySubTree, redoArgs=(sourceObj, newParent),
                 redoKwargs = {'maySkipCrosslinks':maySkipCrosslinks,
                               'topObjectParameters':topObjectParameters,
                               'objectMap':objectMap})
  #
  return result
  
 
def newGuid(prefix = ''):
 
  if prefix:
    prefix = '%s_' % prefix

  # slightly modelled on memops.api.Implementation.MemopsRoot.newGuid()

  timeStamp = time.strftime("%Y_%m_%d_%H_%M_%S")
  user = os.environ.get('USER', 'unknown')

  guid = '%s%s_%s' % (prefix, user, timeStamp)

  return guid


def _transferData(newParent, sourceObj, oldToNew=None,
                 oldVersionStr=None, targetObjParams=None,
                 ignoreMissing=True, useOptLinks=False):
  """ Copy sourceObj and recursively all its children,
  to a new tree where the new targetObj is a child of newParent

  - If oldVersionStr is set, do as  backwards compatibility, 
  including minor post-processing, otherwise do as subtree copying

  - targetObjParams: parameters to be passed to the copy of sourceObj.
    Only meaningful for subtree copy, and ignored for
    backwards compatibility.

  - oldToNew is an old-to-new-object dictionary, serves for either

  - useOptLinks controls if optional links (basically the -to-one
    direction of one-to-many links) should be followed. For compatibility
    this is a waste of time (but harmless), but for copySubTree it is
    necessary
  """

  logger = newParent.root._logger

  from ccpnmodel.ccpncore.memops.metamodel import Constants as metaConstants
  
  from ccpnmodel.ccpncore.xml.memops import Implementation as xmlImplementation
  
  serialTag = metaConstants.serial_attribute
  # NB serialDictTag hardwired to avoid using the varNames dictionary
  serialDictTag = '_' + metaConstants.serialdict_attribute
    
  globalMapping = xmlImplementation.getGlobalMap(oldVersionStr)
  
  # mapsByGuid = globalMapping['mapsByGuid']
  
  if targetObjParams is None:
    targetObjParams = {}
  
  if oldToNew is None:
    oldToNew = {}
  
  # decide which links to follow
  if useOptLinks:
    followTags = ('headerAttrs', 'simpleAttrs', 'cplxAttrs', 'optLinks')
  else:
    followTags = ('headerAttrs', 'simpleAttrs', 'cplxAttrs')
  
  localOldToNew = {}
  emptyList = []
  oneElemList = [None]
  # emptySet = set()
  crossLinkData = []
  appCrossLinkData = crossLinkData.append
  delayDataDict = {}
  # stack of child objects to map - these are old objects
  oldChildStack = [[sourceObj]]
  # stack of parent objects to attach to - these are new objects
  newParentStack = [newParent]
  # objects to notify on - for correct ordering of notifiers when copying subtree
  # should not put newParent in notifyObjects because already exists
  #notifyObjects = [newParent]
  notifyObjects = []
  
  targetObj = None
  try:
 
    nextDd = {}
    while oldChildStack:
      ll = oldChildStack[-1]
      if ll:
        oldObj = ll.pop()
 
        # current object map
        ss = oldObj.packageShortName
        curMap = globalMapping[ss]['abstractTypes'][oldObj.__class__.__name__]

        if curMap.get('proc') == 'skip':
          # skip this one
          continue
 
        # create or get new object
        parent = newParentStack[-1]
 
        if parent is newParent:
          # this is the target object - special case
             
          # fix serial key for sourceObj if copying subtree
          if oldVersionStr is None:
            # we are copying a subtree
            if serialTag in sourceObj.metaclass.keyNames:
              # serial key for top
              if serialTag not in targetObjParams:
                # not being passed in explicitly - we must fix it (special case)
                # NB _serialDict is hardwired to avoid using the varNames di
                serialDict = newParent.__dict__.setdefault(serialDictTag,{})
                oldSerial = serialDict.get(curMap['fromParent'],0)
                targetObjParams[serialTag] = oldSerial + 1
          
          # new object not already there - make it and transfer from old
          if parent.root is newParent:
            # targetObj is a TopObject
            obj = targetObj = curMap['class'](parent, isReading=True,
                                              **targetObjParams)
          else:
            # targetObj is not a TopObject (and we are doing subtree copying)
            parent.topObject.__dict__['isReading'] = True
            obj = targetObj = curMap['class'](parent, **targetObjParams)
          
          notifyObjects.append(obj)
 
          objId = obj
          delayDataDict[objId] = nextDd
          if curMap.get('_transf') == 1:
            oldToNew[oldObj] = obj
          else:
            localOldToNew[oldObj] = obj
          for tag in curMap.get('children', emptyList):
            nextDd[tag] = []
 
          content = curMap['content']
          for tag in curMap.get('cplxAttrs', emptyList):
            if content[tag]['type'] == 'dobj':
              nextDd[tag] = []
 
        else:
          # normal object
 
          if curMap['type'] == 'cplx':
            # complex data type
            obj = curMap['class'](override=True)
 
            objId = id(obj)
            delayDataDict[objId] = nextDd
            localOldToNew[id(oldObj)] = obj
 
          else:
            # type class
            obj = curMap['class'](parent)
 
            objId = obj
            delayDataDict[objId] = nextDd
            if curMap.get('_transf') == 1:
              oldToNew[oldObj] = obj
            else:
              localOldToNew[oldObj] = obj
            delayDataDict[parent][curMap['fromParent']].append(obj)
 
            for tag in curMap.get('children', emptyList):
              nextDd[tag] = []
            
            notifyObjects.append(obj)
 
          # add list for complex data type attrs
          content = curMap['content']
          for tag in curMap.get('cplxAttrs', emptyList):
            if content[tag]['type'] == 'dobj':
              nextDd[tag] = []
 
        # put objects on stack
        childList = []
        oldChildStack.append(childList)
        newParentStack.append(obj)
        contDict = curMap['content']
 
        # transfer object contents
        for ss in followTags:
          tags = curMap.get(ss, emptyList)
          for tag in tags:
            if obj is targetObj and tag in targetObjParams:
              # special case: parameters passed in directly to targetObj
              # needed for tree copying only
              continue
 
            tmpMap = contDict[tag]
            name = tmpMap['name']
            val = getattr(oldObj, tag)
 
            if val is None:
              # no value - skip empties
              continue
 
            elif isinstance(val, (tuple, frozenset)):
              # convert to list for future processing
              if val:
                valIsList = True
              else:
                # no values - skip empties
                continue
 
            else:
              valIsList = False
 
            typ = tmpMap['type']
            
            if typ == 'attr':
              # simple type attribute
 
              proc = tmpMap.get('proc')
 
              if proc == 'delay':
                # pass to compatibility processing - making sure it is a list
                if valIsList:
                  delayDataDict[objId][name] = val
                else:
                  delayDataDict[objId][name] = [val]
 
              else:
                # fix list/nonlist and set
                if tmpMap['hicard'] == 1:
                  if valIsList:
                    for vv in val:
                      break
                    val = vv
                  if proc == 'direct':
                    # direct setting if simple non-constrained attribute
                    obj.__dict__[name] = val
                  else:
                    setattr(obj, name, val)
                
                else:
                  if not valIsList:
                    # optimisation - avoid creating temporary lists
                    oneElemList[0] = val
                    val = oneElemList
                  setattr(obj, name, val)
 
            elif typ == 'child':
              # normal child
              if valIsList:
                childList.extend(val)
              else:
                childList.append(val)
 
            elif typ == 'dobj':
              # normal DataTypeObject
 
              if not valIsList:
                val = [val]
 
              # put on stack for further processing
              childList.extend(val)
 
              if tmpMap.get('proc') == 'delay':
                # delayed - put in delayDataDict
                delayDataDict[objId][name] = val
 
              else:
                # convert to ID and put in crossLinkData to resolve links later
                appCrossLinkData(obj)
                appCrossLinkData([id(xx) for xx in val])
                appCrossLinkData(tmpMap)
 
            else:
              # typ in ('link', 'exolink', 'exotop')
 
              if not valIsList:
                val = [val]
 
              if tmpMap.get('proc') == 'delay':
                delayDataDict[objId][name] = val
 
              else:
                # put in crossLinkData to resolve links later
                appCrossLinkData(obj)
                appCrossLinkData(val)
                appCrossLinkData(tmpMap)
 
        if oldVersionStr is None:
          # this is tree copying
          nextDd = {}
          
        else:
          # this is backwards compatibility
          # clear old object to keep memory use down
          nextDd = oldObj.__dict__
          nextDd.clear()
 
 
      else:
        # no children left - go up a step
        oldChildStack.pop()
        lastParent = newParentStack.pop()
        if lastParent.metaclass.__class__.__name__ == 'MetaDataObjType':
          # parent is complex data type
          lastParent.endOverride()
 
        if not newParentStack:
          # back at root - put root back in
          newParentStack.append(lastParent)
      
    # update local oldToNew map
    localOldToNew.update(oldToNew)

    # postprocess objects - set links now all objects are done
    if oldVersionStr is None:
      # copy subtree
      _delayedLoadLinksCopy(localOldToNew, crossLinkData,
                       ignoreMissing=ignoreMissing)
 
    else:
      # backwards compatibility.

      # first dereference links
      _delayedLoadLinksComp(localOldToNew, crossLinkData)

      # minor post-processing
      from ccpnmodel.ccpncore.memops.format.compatibility.Converters1 import minorPostProcess
      minorPostProcess(oldVersionStr, targetObj, delayDataDict, localOldToNew)
 
      # set TopObjects into TopObjects dictionary.
      newTopObjByGuid = newParent.__dict__['topObjects']
      guid = targetObj.__dict__['guid']
      if guid not in newTopObjByGuid:
        newTopObjByGuid[guid] = targetObj
      else:
        raise Exception("CCPN API error: %s: guid %s already in use"
                       % (targetObj, targetObj.__dict__['guid']))
 
    newTopObj = targetObj.topObject
    
    # set parent-to-child links
    mapping = globalMapping[newTopObj.metaclass.container.shortName]
    if not targetObj.isDeleted:
      # filter out deleted targetObj - could happen in minor postprocessing
      xmlImplementation.linkChildData(delayDataDict, targetObj, mapping,
                                      linkTopToParent=True)
  
  
  except:
    # try cleaning up
    import sys
    exc_info = sys.exc_info()
    # NB '[]' only put in for Python 2.1
    objsToBeDeleted = set([x for x in delayDataDict if not isinstance(x, int,)])
    deleteFailed = False
    for obj in objsToBeDeleted:
      try:
        obj._singleDelete(objsToBeDeleted)
      except:
        deleteFailed = True
        logger.error("WARNING Error in deleting object of class %s, id %s"
               % (obj.__class__, id(obj)))
  
    if targetObj is not None:
      try:
        topObj = targetObj.topObject
        topObj.__dict__['isReading'] = False
      except:
        deleteFailed = True
    
    if deleteFailed:
      logger.error('''Error in clean-up of incorrectly copied data tree.
      Data may be left in an illegal state''')
    else:
      logger.info("NOTE created objects deleted without error")
    
    # re-raise original exception
    raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])

  
  # unset isReading and set to modified
  newTopObj.__dict__['isReading'] = False
  newTopObj.__dict__['isModified'] = True
    
 
  if oldVersionStr is None:
    # we are copying a subtree
    
    if targetObj is newTopObj:
      # root is a TopObject - we need to set isLoaded
      root = newTopObj.root
      newTopObj.__dict__['isLoaded'] = True
      guid = root.newGuid()
      newTopObj.__dict__['guid'] = guid
      root.__dict__['topObjects'][guid] = newTopObj
      
    #check validity
    targetObj.checkAllValid()
 
    # notify - list gicves you parent-before-child order
    for xx in notifyObjects:
      for notify in xx.__class__._notifies.get('__init__', ()):
        notify(xx)
    del notifyObjects
    
    
  else:
    # we are doing backwards compatibility.
    # Set to loaded and leave teh rest to others
    newTopObj.__dict__['isLoaded'] = True
 
  # clean up
  delayDataDict.clear()
  
  #
  return targetObj

def _delayedLoadLinksComp(objectDict, linkData):
  """ Set links (of whatever kind) derefencing as you go using objectDict.
  Skips objects not found in the map.
  For backwards compatibility rather than compatibility 
  """

  logger = Logging.getLogger()
  
  popLinkData = linkData.pop
  getObj = objectDict.get

  try:
    while linkData:
      # setup
      curMap = popLinkData()
      val = popLinkData()
      obj = popLinkData()

      # map values
      valueList = list()
      for vv in val:
        oo = getObj(vv)
        if oo is not None:
          valueList.append(oo)

      if valueList:
        name = curMap.get('name')
        hicard = curMap.get('hicard')
        # set element
        if hicard == 1:
          ov = valueList[0]
        elif hicard > 1:
          ov = valueList[:hicard]
        else:
          ov = valueList

        setattr(obj, name, ov)

  except:
    logger.error('''Error during link dereferencing. Object was: %s
    values were: %s
    tag name was: %s''' % (obj, val, name))
    raise


def _delayedLoadLinksCopy(objectDict, linkData, ignoreMissing=False):
  """ Set links (of whatever kind) derefencing as you go using objectDict.
  For copySubTree rather than compatibility 
  """
  
  popLinkData = linkData.pop
  getObj = objectDict.get
   
  while linkData:
    
    # set up 
    curMap = popLinkData()
    val = popLinkData()
    obj = popLinkData()
    name = curMap['name']
    hicard = curMap['hicard']
    
    # locard = curMap['locard']
    copyOverride = curMap.get('copyOverride')
    
    # NB copyOverride determines whether you are allowed to set links
    # that modifies object outside the subtree
    
    if hicard == 1:
    
      # get new value
      vv = val[0]
      newVal = getObj(vv)
      
      if newVal:
        # linked-to object replaced by new object
        setattr(obj, name, newVal)
      
      elif copyOverride:
        # try setting link to old object
        try:
          setattr(obj, name, vv)
          
        except:
          if ignoreMissing:
            # we can skip the link
            pass
          else:
            # link could not be handled
            raise Exception(
             "%s: Out-of-subtree -to-one link %s cannot be copied"
             % (obj, name)
            )
    
    else:
      # -to-many link
      
      # get new values
      others = []
      newies = []
      foundAll = True
      for vv in val:
        other = getObj(vv)
        if other:
          newies.append(other)
          others.append(other)
        else:
          foundAll = False
          others.append(vv)
      
      done = False
          
      if foundAll or copyOverride:
        # try making link to full set of objects
        try:
          setattr(obj, name, others)
          done = True
        except:
          pass
      
      if not done and not foundAll and ignoreMissing:
        # try making link to the subset of objects found in subtree
        try:
          setattr(obj, name, newies)
          done = True
        except:
          pass
          
      if not done:
        # link could not be handled
        raise Exception(
         "%s: Out-of-subtree link %s cannot be copied"
         % (obj, name)
        )
