import os
from ccpncore.util import Path
from ccpncore.memops import Version
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import XmlModelIo
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.format.xml import XmlGen
from ccpncore.memops.metamodel.ModelPortal import ModelPortal
from ccpncore.memops.scripts.core import PyFileModelAdapt
from ccpnmodel.util import Conversion

compDataDir = 'ccpncore/memops/format/compatibility'
defaultInfoFile = 'MapInfo.py'

implTemplate = "%s.%s.%%s" % (metaConstants.modellingPackageName,
                              metaConstants.implementationPackageName)
stringTypeName = implTemplate % 'String'

ignoreTags = {'accessedPackages', 'codeStubs', 'constructorCodeStubs', 'destructorCodeStubs',
              'postDestructorCodeStubs', 'documentation', 'hicard', 'importedPackages',
              'isAutomatic', 'isOrdered', 'isUnique', 'partitionsChildren', 'subtypes'}

nameTags = {'name', 'baseName'}

class LocalXmlGen(XmlGen.XmlGen):

  def __init__(self, **kw):
  
    self.addModelFlavour('language', 'python')
    self.baseName = 'xml'
  
    for (tag, val) in kw.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)
    
    super(LocalXmlGen, self).__init__()


def makeUpgrade(fromVersionTag, toVersionTag, toTopPackage=None, modelPortal=None,
                includePackageNames=(), excludePackageNames=(), infoFileName=None):
  """ Make upgrade or downgrade map code from fromVersion to toVersion
  Will look for the models in ccpnmodel.versionDir
  and place the compatibility code in e.g.
  ccpncore/memops/format/compatibility/upgrade/v_2_0_3/MapInfo.py
  ccpncore/memops/format/compatibility/downgrade/v_2_2_1/MapInfo.py
  """

  if infoFileName is None:
    infoFileName = defaultInfoFile

  fromVersion = Version.Version(fromVersionTag)
  toVersion = Version.Version(toVersionTag)
  if fromVersion == toVersion:
    raise Exception("Trying to make compatibility between identical versions: %s %s"
                    % (fromVersion, toVersion))
  
  if toTopPackage is None:
    toTopPackage = XmlModelIo.readModel(versionTag=toVersionTag,
                                       includePackageNames=includePackageNames,
                                       excludePackageNames=excludePackageNames)

  fromTopPackage = XmlModelIo.readModel(versionTag=fromVersion,
                                      includePackageNames=includePackageNames,
                                      excludePackageNames=excludePackageNames)

  # full name for map info file
  mapInfoFile = os.path.join(Path.getPythonDirectory(), compDataDir, fromVersion.getDirName(),
                             infoFileName)

  conversionInfo = Conversion.getConversionInfo(fromVersion, toVersion)

  makeCompatibility(fromTopPackage, toTopPackage, modelPortal=modelPortal,
                    elementPairings=conversionInfo['elementPairings'],
                    fileName=mapInfoFile)

def dirNameFromVersionString(versionString):
  """ generate directory name from version string
  """
  return '_'.join(['v'] + versionString.split('.'))

def versionFromDir(topDir):
  """ Get current version string for directory tree rooted in topDir
  """
  from ccpncore.memops import Version
  versionFile = os.path.join(topDir, 'python/memops/general/Constants.py')
  if not os.path.isfile(versionFile):
    versionFile = os.path.join(topDir, 'python/ccpncore/memops/Version.py')
  for line in open(versionFile):
    if line.startswith('currentModelVersion = '):
      exec(line, locals(), globals())
      return Version.currentModelVersion
  else:
    return  None
    
  
def makeCompatibility(fromModel, toModel, modelPortal=None,
                      elementPairings=None, fileName='CompatibilityMapInfo.py'):
  """ Make compatibility info for converting fromModel to toModel.
  elementPairings is a list of (oldGuid, newGuid) pairs that
  map elements from the two models. Note that several old guids
  can map to a single new guid and vice versa.
  """
  
  comparison = MetaModel.compareModels(fromModel, toModel,
                                       elementPairings=elementPairings)
  if modelPortal is None:
    modelPortal = ModelPortal(toModel)
    PyFileModelAdapt.processModel(modelPortal)
  xmlGen = LocalXmlGen(modelPortal=modelPortal)
  xmlGen.processModel()
  globalMapping = xmlGen.globalMap

  dirName = os.path.dirname(fileName)
  if not os.path.exists(dirName):
    os.makedirs(dirName)
  fp = open(fileName, 'w')
  
  dict1 = comparison['dict1']
  dict2 = comparison['dict2']
  # write elements to skip or delay
  skips = []
  delays = []
  elems = comparison['unique1']
  for ee in elems:
    # elements unique in old model
    if ee.container not in elems:
      if isinstance(ee, MetaModel.AbstractDataType):
        skips.append((ee.container.shortName, ee.name, '', ee.guid,
                      ee.__class__.__name__))
        
      elif isinstance(ee, MetaModel.MetaPackage):
        skips.append((ee.shortName or '', '', '', ee.guid, ee.__class__.__name__))
        
      elif (isinstance(ee, MetaModel.MetaOperation) or 
            isinstance(ee, MetaModel.MetaConstraint)):
        # nothing to do here
        continue
      
      #NBNB elif ee.isDerived and ee.changeability == ImpConstants.frozen:
      elif ee.isDerived:
        # derived class element. Ignore
        continue
      
      elif isinstance(ee, MetaModel.MetaRole):
        # ee is a missing role of a still existing ComplexDataType
        
        vt = ee.valueType
        cc = ee.container
        if vt.container in cc.container.accessedPackages:
          # interpackage link in wrong direction. Not in maps. Must be skipped
          # Should not matter, but skip rather than ignore in case of model changes.
          skips.append((cc.container.shortName, cc.name, ee.name, ee.guid, 
                        ee.__class__.__name__))
 
        elif ee.hierarchy != metaConstants.no_hierarchy:
          # parent or child link. Delay is not defined - must be skipped
          skips.append((cc.container.shortName, cc.name, ee.name, ee.guid, 
                        ee.__class__.__name__))
 
        elif vt.guid in comparison['dict2']:
          # The valueType also still exists
                         
          dd = XmlGen.getRoleMap(ee, cc, globalMapping)
          elemMap = {}
          if dd is None:
            print ('WARNING, no map found for %s' % ee)
            
          else:
            for tag in ('type', 'proc', 'name', 'eType', 'tag'):
              xx = dd.get(tag)
              if xx is not None:
                elemMap[tag] = xx
 
            if elemMap:
              # put as delay
              delays.append((cc.container.shortName, cc.name, ee.name, ee.guid,
                             elemMap, None))
            else:
              # cannot create map, skip
              print ('WARNING, incomplete map found for %s' % ee)
              skips.append((cc.container.shortName, cc.name, ee.name, ee.guid, 
                            ee.__class__.__name__))
 
        else:
          # ee valueType does not exist. Skip.
          skips.append(
           (cc.container.shortName, cc.name, ee.name, ee.guid, ee.__class__.__name__)
          )
 
      elif isinstance(ee, MetaModel.MetaAttribute):
        
        cc = ee.container
 
        vt = ee.valueType
        superVts = [x for x in vt.getAllSupertypes() if x.guid in dict2]
        valueTypeGuid = superVts[0].guid
        
        if (vt.guid in comparison['dict2'] 
            or vt.__class__.__name__ == 'MetaDataType' and superVts):
 
          dd = XmlGen.getAttrMap(ee, cc, globalMapping, 
                                 valueTypeGuid=valueTypeGuid)
          elemMap = {}
          if dd is not None:
            for tag in ('type', 'proc', 'name', 'eType', 'tag'):
              xx = dd.get(tag)
              if xx is not None:
                elemMap[tag] = xx
        
          if elemMap:
            delays.append((cc.container.shortName, cc.name, ee.name, ee.guid,
                           elemMap, valueTypeGuid))
          else:
            print ('WARNING, no map found for %s' % ee)
            skips.append((cc.container.shortName, cc.name, ee.name, ee.guid, ee.__class__.__name__))
  
        else:
          # ee valueType does not exist and can not be substituted. Skip.
          skips.append((cc.container.shortName, cc.name, ee.name, ee.guid, ee.__class__.__name__))

  skips.sort()
  fp.write('''
# Packages, classElements and AbstractDataTypes skipped in new model
# (prefix, typeName, elemName, newGuid, elemType)
skipElements = [
''')
  for tt in skips: 
    fp.write(" %s, \n" % (tuple(x or None for x in tt),))
  fp.write(']\n')
      
  delays.sort()
  fp.write('''
# classElements skipped in new model, but available for simple data transfer
# (prefix, typeName, elemName, newGuid, elemMap, valueTypeGuid)
delayElements = [
''')
  for tt in delays: 
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
  
  # write new elements
  mandatory = []
  optional = []
  constraints = []
  elems = comparison['unique2']
  for ee in elems:
  
    #if ee.container not in elems:
    if isinstance(ee, MetaModel.MetaConstraint):
      constraints.append((ee.qualifiedName(), ee.guid))
      
    elif isinstance(ee, MetaModel.ClassElement):
    
      #NBNB if not (ee.isDerived and ee.changeability == ImpConstants.frozen):
      if not ee.isDerived:
        cc = ee.container
        tt = (cc.container.shortName, cc.name, ee.name, ee.guid)
        if (ee.locard != 0 and not
            (isinstance(ee, MetaModel.MetaAttribute) and ee.defaultValue)
            and not ee.isImplementation and not ee.isDerived):
          mandatory.append(tt)
        else:
          optional.append(tt)
    
    elif isinstance(ee, MetaModel.AbstractDataType):
      optional.append((ee.container.shortName, ee.name, '', ee.guid))
      
    elif isinstance(ee, MetaModel.MetaPackage):
      optional.append((ee.shortName or '', '', '', ee.guid))

  mandatory.sort()
  optional.sort()
  constraints.sort()
        
  fp.write('''
# MetaConstraints added in new model
# (qualifiedName, guid)
newConstraints = [
''')
  for tt in constraints: 
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
        
  fp.write('''
# Mandatory classElements added in new model
# New ClassElements with locard !=0, no default, not derived or Implementation
# (prefix, typeName, elemName, newGuid)
newMandatories = [
''')
  for tt in mandatory: 
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
        
  fp.write('''
# Packages, classElements and AbstractDataTypes added in new model
# Optional, i.e. excluding mandatory classElements given above
# (prefix, typeName, elemName, newGuid)
newElements = [
''')
  for tt in optional:
    fp.write(" %s, \n" % (tuple(x or None for x in tt),))
  fp.write(']\n')
        
  # 
  typeChanges = [] 
  allDiffs = []
  
  neutraliseElements = []
  
  renames = {}
  
  for oldGuid, newGuid, diffs in comparison['differ']:
    
    usediffs = diffs.difference(ignoreTags)
        
    oldobj = dict1[oldGuid]
    newobj = dict2[newGuid]
    
    if isinstance(newobj, MetaModel.MetaPackage):
      if 'shortName' in usediffs:
        raise MetaModel.MemopsError ("%s: Change in shortName not implemented"
                           % newobj)
    elif (isinstance(newobj, MetaModel.ClassElement) or
        isinstance(newobj, MetaModel.AbstractDataType)):
    
      if isinstance(newobj, MetaModel.ClassElement):
        if (newobj.isDerived and
            (oldobj.isDerived or newobj.changeability == metaConstants.frozen)):
          # derived non-settable element, or both sides derived. Ignore
          continue 
        
        elif (isinstance(oldobj, MetaModel.MetaRole) and 
          oldobj.valueType.container in oldobj.container.container.accessedPackages):
          # interpackage link in wrong direction. Not in maps. Must be skipped
          continue
        
        elif oldobj.isDerived:
          # newObj cannot be derived at this point.
          # We cannot use old derived elements, as the derivation function may
          # no longer work by the time it is called
          cc = newobj.container
          neutraliseElements.append((cc.container.shortName,  cc.name, 
                                     newobj.name, newobj.guid))
          continue
          
      if 'name' in usediffs:
        usediffs.difference_update(nameTags)
        
        if not (isinstance(newobj, MetaModel.MetaRole) and
                newobj.hierarchy == metaConstants.parent_hierarchy):
          # ignore parent role renamings, handle everything else   
             
          if isinstance(newobj, MetaModel.ClassElement):
            # rename if not a parent role
            cc = oldobj.container
            tt = (cc.container.shortName, cc.name, oldobj.name)
            renames[tt] = (newobj.name,newGuid)
          
          else:
            # isinstance(newobj, MetaModel.AbstractDataType)
            shortName = oldobj.container.shortName
            oldobjName =  oldobj.name
            tt = (shortName, oldobjName, '')
            renames[tt] = (newobj.name, newGuid)
            
            # add renames for oldobj classElements - their XML tags will change
            if isinstance(oldobj,MetaModel.ComplexDataType):
              accessedPackages = oldobj.container.accessedPackages
              ll = oldobj.attributes
              if isinstance(oldobj,MetaModel.MetaClass):
                ll.extend(x for x in oldobj.roles
                          if x.valueType.container not in accessedPackages)
              for elem in ll:
                if elem.isDerived:
                  continue
                if elem.isImplementation:
                  continue
                newElem = newobj.getElement(elem.name)
                if newElem is not None and elem.guid == newElem.guid:
                  tt = (shortName, oldobjName, elem.name)
                  if tt not in renames:
                    renames[tt] = (newobj.name, elem.guid)
            
                            
      if (isinstance(newobj, MetaModel.ClassElement) 
          and 'valueType' in usediffs):
        # change of valueType
        
        newvt = newobj.valueType
        oldvt = oldobj.valueType
        
        if ([x for x in oldvt.getAllSupertypes() if x.guid == newvt.guid]):
            # and oldvt.guid in globalMapping['mapsByGuid']):
          # relaxation: change from subtype to supertype - always OK
          # NB standard treatment only works if the old type is still present in the new map
          action = 'ignore'
          if oldvt.guid in globalMapping['mapsByGuid']:
            # old valueType is still around and can be used
            valueTypeGuid = None
          else:
            # oldvt no longer around - switch to new vt
            valueTypeGuid = newvt.guid
          
        elif [x for x in newvt.getAllSupertypes() if x.guid == oldvt.guid]:
          # restriction - change from supertype to subtype - delay
          action = 'delay'
          if isinstance(newobj, MetaModel.MetaAttribute):
            valueTypeGuid = oldvt.guid
          else:
            valueTypeGuid = None
          
        elif isinstance(oldvt, MetaModel.MetaDataType):
          # 
          
          action = 'delay'
          oldTypecode = oldvt.typeCodes['python']
          try:
            useBaseType = newobj.metaObjFromQualName(implTemplate % oldTypecode)
          except MetaModel.MemopsError:
            useBaseType = newobj.metaObjFromQualName(stringTypeName)
          valueTypeGuid = useBaseType.guid
                  
        elif (isinstance(oldobj, MetaModel.MetaRole) and 
              oldobj.container.container is oldvt.container):
          # incompatible intrapackage crosslink - delay
          action = 'delay'
          valueTypeGuid = None
        
        else:
          # incompatible ComplexDataType or exolink - nothing doing
          #action = 'skip'
          action = 'delay'
          valueTypeGuid = None
        
        cc = oldobj.container
        
        if isinstance(newobj, MetaModel.MetaRole):
          dd = XmlGen.getRoleMap(oldobj, cc, globalMapping)
          elemMap = {}
          if dd:
            for tag in ('type', 'proc', 'name', 'eType', 'tag'):
              xx = dd.get(tag)
              if xx is not None:
                elemMap[tag] = xx
 
        else:
          # isinstance(newobj, MetaModel.MetaAttribute)
          dd = XmlGen.getAttrMap(oldobj, cc, globalMapping, 
                                 valueTypeGuid=valueTypeGuid)
          elemMap = {}
          if dd:
            for tag in ('type', 'proc', 'name', 'eType', 'tag'):
              xx = dd.get(tag)
              if xx is not None:
                elemMap[tag] = xx
 
        tt = (cc.container.shortName, cc.name, oldobj.name, action, 
              newobj.guid, elemMap, valueTypeGuid)
        
        typeChanges.append(tt)
        
        if len(usediffs) == 1:
          usediffs.remove('valueType')
        
      if usediffs:
        allDiffs.append((oldobj.qualifiedName(), newobj.name, oldGuid, newGuid,
                         diffs))
  
  neutraliseElements.sort()
  allDiffs.sort()
  typeChanges.sort()
  namematch = list(comparison['namematch'].items())
  namematch.sort()
  
        
  fp.write('''
# Class elements that exist in both models but that require handcode for
# transfer. E.g. elements that go from derived to non-derived.
# Note that old derivation functions can not be relied on to work during
# data transfer
# (prefix, typeName, elemName, newGuid, elemType)
neutraliseElements = [
''')
  for tt in neutraliseElements: 
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
  
  fp.write('''
# Differences between equivalent classElements and AbstractDataTypes :

# name changes
# (prefix, typeName, elemName, newName, newGuid
renames = [
''')

  # NBNB kludge around the impossibility of sorting strings with None
  for tt1, tt2 in sorted(renames.items()):
    fp.write(" %s, \n" % (tuple(x or None for x in tt1+tt2),))
  fp.write(']\n')
  
  fp.write('''
# ValueType changes
# change types are : 'ignore': do nothing, 'delay': available for calculation
# (prefix, typeName, elemName, action, newGuid, elemMap, valueTypeGuid)
typeChanges = [
''')
  for tt in typeChanges:
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
  
  fp.write('''
# Different elements with matching qualifiedNames
# (element.qName, differentTags, oldGuid, newGuid
nameMatches = [
''')
  for tt in namematch:
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
  
  fp.write('''
# Differences for matching elements, 
# excluding those where only names and/or valueTypes differ
# (oldElem.qName, newElem.name, oldGuid, newGuid, differentTags
allDiffs = [
''')
  for tt in allDiffs:
    fp.write(" %s, \n" % (tt,))
  fp.write(']\n')
  
  fp.close()
           
  
