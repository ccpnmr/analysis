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
"""
======================COPYRIGHT/LICENSE START==========================

Converters1.py: Data compatibility handling

Copyright (C) 2007 Rasmus Fogh (CCPN project)
 
=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../../license/LGPL.license.
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.
 
You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

======================COPYRIGHT/LICENSE END============================

To obtain more information about this code:

- CCPN website (http://www.ccpn.ac.uk)

- contact Rasmus Fogh (ccpn@bioc.cam.ac.uk)

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following reference:

===========================REFERENCE START=============================
Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and 
automated software development. Bioinformatics 21, 1678-1684.
===========================REFERENCE END===============================
 
"""
# imports
import importlib
from ccpnmodel.util import Conversion
from ccpncore.memops.ApiError import ApiError
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops import Version
currentVersion = Version.currentModelVersion

mapInfoLocation = 'ccpncore.memops.format.compatibility'


def modifyIoMap(fromVersionStr, globalMapping):
  """ Adapt globalMapping to read oldVersion data
  """

  fromVersion = Version.Version(fromVersionStr)

  infodd = Conversion.getConversionInfo(fromVersion, currentVersion)
  
  # Model information by guid
  anApiClass = globalMapping['IMPL']['abstractTypes']['MemopsObject']['class']
  newElementsByGuid = getElementsByGuid(anApiClass._metaclass.topPackage())
  
  # new elements retrofitted by hand and therefore treated as old 
  # used for e.g. changes of parent tree.
  elemsTreatedAsOld = set(infodd['elemsTreatedAsOld'])

  diffMap =  importlib.import_module('%s.%s.MapInfo' % (mapInfoLocation,fromVersion.getDirName()))

  # correct maps for newly introduced elements
  for tag in ('newElements', 'newMandatories', 'neutraliseElements'):
    ll = getattr(diffMap, tag)
    for (prefix, typeName, elemName, newGuid) in ll:
      if prefix in globalMapping and newGuid not in elemsTreatedAsOld:
        removeElementName(newGuid, globalMapping, newElementsByGuid)

  # correct maps for skipped elements
  for (prefix, typeName, elemName, newGuid, elemType) in diffMap.skipElements:
    if prefix in globalMapping and newGuid not in elemsTreatedAsOld:
      fixElementMap(newGuid, 'skip', prefix, globalMapping, newElementsByGuid,
                    typeName, elemName)
      if elemType == 'MetaClass':
        fixExoLinkMap(newGuid, 'skip', prefix, globalMapping, typeName)

  # correct maps for changed valueTypes
  for tt in diffMap.typeChanges:
    (prefix, typeName, elemName, action, newGuid, elemMap, valueTypeGuid) = tt
    if prefix in globalMapping and newGuid not in elemsTreatedAsOld:
      fixElementMap(newGuid, action, prefix, globalMapping, newElementsByGuid,
                         typeName, elemName, valueTypeGuid=valueTypeGuid,
                         elemMap=elemMap, overrideGuidMap=True)

  # correct maps for renamed elements
  # NB must be done after valueTypes corrections, 
  # as elements may be both renamed and 'delay'ed or 'skip'ped
  # by changed valueType 
  for (prefix, typeName, elemName, newName, newGuid) in diffMap.renames:
    if prefix in globalMapping and newGuid not in elemsTreatedAsOld:
      fixElementMap(newGuid, 'rename', prefix, globalMapping, newElementsByGuid,
                    typeName, elemName)
      if elemName is None:
        fixExoLinkMap(newGuid, 'rename', prefix, globalMapping, typeName)
  dd = globalMapping['mapsByGuid']['www.ccpn.ac.uk_Fogh_2006-08-16-18:20:12_00012']
      

  # correct maps for delayed elements
  # NB, must be done after renaming, as we use type names to find 
  # appropriate maps
  for tt in diffMap.delayElements:
    (prefix, typeName, elemName, newGuid, elemMap, valueTypeGuid) = tt
    if prefix in globalMapping and newGuid not in elemsTreatedAsOld:
      fixElementMap(newGuid, 'delay', prefix, globalMapping, newElementsByGuid,
                    typeName, elemName, valueTypeGuid=valueTypeGuid,
                    elemMap=elemMap)

  # make extra changes
  infodd['extraMapChanges'](globalMapping)
  
def removeElementName(guid, globalMapping, newElementsByGuid):
  """ Remove element from name lists used for selecting input
  and remove element from loadMaps (in case another element with the
  same signature needs the slot).
  """
  
  # set up
  useObj = newElementsByGuid.get(guid)
  if useObj is None:
    # guid does not exist. Probably was not included in model generation. 
    # Anyway, nothing to do.
    return
  newName = useObj.name
  mapsByGuid = globalMapping['mapsByGuid']
  
  # remove from lists in container and its subtypes
  if useObj.__class__.__name__ in ('MetaAttribute', 'MetaRole'):
    
    if (useObj.isAbstract 
        or (useObj.isDerived and useObj.changeability == metaConstants.frozen)):
      # These elements have no maps, so nothing to do
      return
      
    subtypes = useObj.container.getAllSubtypes()
    for metaclass in subtypes:
      containerMap =  mapsByGuid.get(metaclass.guid)
      if containerMap is not None:
        # NB there might not be a map if this is (e.g.) an abstract superclass 
        # that does not inherit from DataObject 
        for tag in ('simpleAttrs', 'headerAttrs', 'optLinks', 'cplxAttrs',
                    'children'):
          ll = containerMap.get(tag)
          if ll and newName in ll:
            ll.remove(newName)
  
    # remove from loadMaps
    oldMap = mapsByGuid.get(guid)
    if oldMap is None:
      # check if there is need for concern
      if (useObj.__class__.__name__ == 'MetaRole' and 
          useObj.container.container in useObj.valueType.container.importedPackages):
        # interpackage link in backwards direction
        pass
      elif (useObj.__class__.__name__ == 'MetaRole' and 
            useObj.hierarchy == 'parent'):
        pass
      elif useObj.container.guid not in mapsByGuid:
        # The class is not mapped. 
        # Could be (is?) abstract multi-inheritance class
        pass
      else:
        print('WARNING, no previous map found for %s (%s)' % (useObj, guid))
    else:
      del globalMapping['loadMaps'][oldMap['tag']]
  
  
def fixElementMap(newGuid, action, prefix, globalMapping, newElementsByGuid, 
                  typeName=None, elemName=None, overrideGuidMap=False, 
                  valueTypeGuid=None, elemMap=None):
  """ insert/modify I/O map in mapping 
  - newGuid is the guid to use in the new map 
  (new guid if element exists, old guid otherwise) 
  - prefix is the package shortname
  - typeName is the name of the class/DataObjType (if any) 
  - elemName is the name of the ClassElement (if any) 
  - overrideGuidMap controls if an existing map should be overridden
  - valueTypeGuid is the guid for a new valueType (for attr)
  - elemMap is a passed-in ({typ, proc, name, eType}) I/O map for the element
  
  """
  
  from ccpncore.memops.format.xml import XmlGen
  
  if action == 'ignore':
    return
  
  elif action not in ('rename', 'skip', 'delay'):
    raise ApiError("action: %s not supported" % action)
  
  loadMaps = globalMapping['loadMaps']
  mapsByGuid = globalMapping['mapsByGuid']
  mapping = globalMapping[prefix]
  
  if typeName is None:
    return
  
  xmlTag = XmlGen.xmlTag(prefix, typeName, elemName)
  if elemName is None:
    typ = 'dataType'
  else:
    typ = 'elem'  
  
  if action == 'skip':
    # we are skipping the element
    if newGuid in mapsByGuid:
      raise ApiError("%s: guid already has map" % xmlTag)
    else:
      mapsByGuid[newGuid] = newMap = {'guid':newGuid, 'proc':'skip'}
    
    if typ == 'dataType':
      # put map in abstractTypes
      abstractTypes = mapping['abstractTypes']
      if typeName in abstractTypes:
        raise ApiError("%s: name %s already in use" % (xmlTag, typeName))
      else:
        abstractTypes[typeName] = newMap
  
  elif action == 'rename':
    # this is a renaming
    
    # get previous I/O map (must exist)
    newMap = mapsByGuid.get(newGuid)
    if newMap is None:
      # guid does not exist. Probably was not included in model generation. 
      # Anyway, nothing to do.
      return
    
    # clean up loadMaps
    del loadMaps[newMap['tag']]
    
    if typ == 'elem':
      # ClassElement
      newObj = newElementsByGuid[newGuid]
      newName = newObj.name
      
      if newName != elemName:
        # they may be equal if the container class only is being renamed
        
        # fix attribute lists and contents for container and its subtypes
        subtypes = newObj.container.getAllSubtypes()
        for metaclass in subtypes:
          fixMap = mapsByGuid[metaclass.guid]
 
          # fix content map
          contDict = fixMap['content']
          if elemName in contDict:
            raise ApiError("%s: name %s already in use" % (xmlTag, elemName))
          contDict[elemName] = contDict[newName]
          del contDict[newName]
 
          # fix attribute lists
          for tag in ('simpleAttrs', 'headerAttrs', 'optLinks', 'cplxAttrs',
                      'children'):
            ll = fixMap.get(tag)
            if ll and newName in ll:
              ll[ll.index(newName)] = elemName
    else:
      # classifier - stil needs renaming
      # as we use the type name to find the right map
      # put map in abstractTypes
      abstractTypes = mapping['abstractTypes']
      if typeName in abstractTypes:
        raise ApiError("%s: name %s already in use" % (xmlTag, typeName))
      else:
        abstractTypes[typeName] = newMap
    
  else:
    # action == 'delay'
    # we are delaying storage for use in compatibility
    if typ != 'elem':
      raise ApiError("%s: only ClassElements may be 'delay'ed" % xmlTag)
    
    if valueTypeGuid is not None:
      elemMap['data'] = mapsByGuid[valueTypeGuid]
    
    if overrideGuidMap:
      newMap = mapsByGuid[newGuid]
    
    elif newGuid in mapsByGuid:
      raise ApiError("%s: guid %s already in use" % (xmlTag, newGuid))
    
    elif xmlTag in loadMaps:
      raise ApiError("%s: xml tag already in use" % (xmlTag,))
    
    else:
      mapsByGuid[newGuid] = newMap = {}
      containerGuid = mapping['abstractTypes'][typeName]['guid']
      newContainer = newElementsByGuid[containerGuid]
      subtypes = newContainer.getAllSubtypes()
      for metaclass in subtypes:
        # put new map in content dictionary
        fixMap = mapsByGuid[metaclass.guid]
        contDict = fixMap['content']
        if elemName in contDict:
          # we are overriding the previous definition.The tag is already there
          pass
        else:
          # put tag on cplxAttrs (it does not matter which list it is on)
          contDict[elemName] = newMap
          ll = fixMap.setdefault('cplxAttrs', [])
          ll.append(elemName)
          
    # update map contents
    newMap.update(elemMap)
    newMap['proc'] = 'delay'
  
  # fix loadMaps
  loadMaps[xmlTag] = newMap
  
  
def fixExoLinkMap(newGuid, action, prefix, globalMapping, typeName):
  """ Fix exoLink maps
  if action == 'rename' enter newGuid map under (prefix, typeName) name
  if action == 'skip', enter skip record for guid under (prefix, typeName) name
  """
  
  from ccpncore.memops.format.xml import XmlGen
  
  exoTag = XmlGen.xmlTag(prefix, typeName, var='exo')
  
  # set up
  exolinks = globalMapping[prefix]['exolinks']
  loadMaps = globalMapping['loadMaps']
  
  # check if slots are occupied
  if typeName in exolinks:
    raise ApiError("%s exolink: name %s already in use" % (exoTag, typeName))
  if exoTag in loadMaps:
    raise ApiError("%s exolink: name already in use" % exoTag)
  
  if action == 'skip':
    # we are not replacing anything, but skippping
    newMap = {
     'type':'exo',
     'guid':newGuid,
     'eType':'cplx', 
     'proc':'skip'
    }
  
  else:
    # replacing an existing map
    newClassMap = globalMapping['mapsByGuid'].get(newGuid)
    newExoTag =  XmlGen.xmlTag(prefix, newClassMap['class'].__name__, var='exo')
    #newMap = globalMapping['mapsByGuid'].get(newGuid)
    newMap = loadMaps[newExoTag]
    del exolinks[newMap['class'].__name__]
    #del loadMaps[newMap['tag']]
  
  # set new map
  exolinks[typeName] = newMap
  loadMaps[exoTag] = newMap
  
  
def getElementsByGuid(rootPackage):
  """ get guid:obj dictionary for MetaModelElements
  in MetaModel corresponding to rootPackage
  
  Used in mapping of reference data.
  NBNB may need version-specific expansion later to handle 
  difficult reference data modifications.
  """
  from ccpncore.memops.metamodel.MetaModel import makeObjDict
  #
  return makeObjDict(rootPackage, ignoreImplicit=True, crucialOnly=True)

def minorPostProcess(fromVersion, topObj, delayDataDict, toNewObjDict, mapping=None):
  """ postProcess - update newRoot object tree
  May be used to postprocess a file load (minor upgrade)
  
  topObj is a TopObject in the new tree
  delayDataDict is a {newobj:{tag:value}} dictionary of delayed set elements
  and children
  toNewObjDict is _ID:newObj for minor upgrades
  mapping is the IO mapping
  """

  infodd = Conversion.getConversionInfo(fromVersion, currentVersion)
  infodd['correctData'](topObj, delayDataDict, toNewObjDict, mapping)