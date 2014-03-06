
"""
======================COPYRIGHT/LICENSE START==========================

XmlMapWrite.py: Code generation for CCPN framework

Copyright (C) 2005 Rasmus Fogh (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../license/GPL.license
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.
 
You should have received a copy of the GNU General Public
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
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.scripts.core.LanguageInterface import LanguageInterface
from ccpncore.memops.scripts.core.TypeInterface import TypeInterface
from ccpncore.memops.metamodel.TextWriter import TextWriter
from ccpncore.memops.format.xml.XmlGen import XmlGen

MemopsError = MetaModel.MemopsError
headerTextTypeNames = ['Token','Word']

mandatoryAttributes = ()

repositoryTag = '$Name:  $'
repositoryId  = '$Id: XmlMapWrite.py,v 1.42.2.7 2010/06/14 11:21:33 jmci Exp $'


class XmlMapWrite(LanguageInterface, TypeInterface, TextWriter, XmlGen):

  codeDirName = metaConstants.xmlCodeDir
  
  localVarNames = {
   'globalMap':'globalMap',
   'mapsByGuid':'mapsByGuid',
   'loadMaps':'loadMaps',
   'abstractTypes':'abstractTypes',
   'exolinks':'exolinks',
   'currentMap':'currentMap',
   'contentMap':'contentMap',
   'aList':'aList',
   'aDict':'aDict',
  }

  ###########################################################################

  ###########################################################################

  def __init__(self, **kw):
    
    # init handling
    super(XmlMapWrite, self).__init__()
    
    for tag in mandatoryAttributes:
      if not hasattr(self, tag):
        raise MemopsError(" XmlGen lacks mandatory %s attribute" % tag)

    self.stringVarType = self.elementVarType(self.stringType)
    self.booleanVarType = self.elementVarType(self.booleanType)
    self.intVarType = self.elementVarType(self.intType)
    self.dictVarType = self.elementVarType(self.dictType)
    self.anyVarType = self.elementVarType(self.anyType)

  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def processBranchPackage(self, package):
    """ processing actions for branch package
    """
    
    packageDirName = self.getObjDirName(package)
    
    if package in self.modelPortal.twigPackages():
      self.clearOutDir(packageDirName)
    
    # must be called after
    self.createDir(packageDirName)
    
    super(XmlMapWrite, self).processBranchPackage(package)
    
  ###########################################################################

  ###########################################################################
  # overrides XmlGen
  def processLeafPackage(self, package):
  
    self.setupLeafPackage(package)
    super(XmlMapWrite, self).processLeafPackage(package)

  ###########################################################################

  ###########################################################################

  # added for benefit of Java (originally was just in processLeafPackage)
  def setupLeafPackage(self, package):
  
    globalMapVar = self.localVarNames['globalMap']
    currentMapVar = self.localVarNames['currentMap']
    
    if package is self.implPackage:
      # set up top level dicts
      
      self.writeNewline()
      self.writeComment("Set up global dictionaries")
      for ddName in  ('loadMaps', 'mapsByGuid'):
        ss = self.localVarNames[ddName]
        self.newDict(ss, keyType=self.stringVarType, needDeclType=True)
        self.setDictEntry(globalMapVar, self.toLiteral(ddName), ss)
      
      for pp in self.modelPortal.leafPackagesByImport():
    
        pref = pp.shortName
        mapping = self.globalMap[pref]
 
        self.writeNewline()
        self.startBlock()
        self.writeComment("%s - %s: Set up top level dictionaries"
                          % (pref, pp))
 
        # set up mapping and contained dicts
        self.newDict(currentMapVar, keyType=self.stringVarType, 
                     needDeclType=True)
        self.setDictEntry(globalMapVar, self.toLiteral(pref), currentMapVar)
        for ddName in  ('abstractTypes', 'exolinks'):
          ss = self.localVarNames[ddName]
          self.newDict(ss, keyType=self.stringVarType, needDeclType=True)
          self.setDictEntry(currentMapVar, self.toLiteral(ss), ss)
          self.setDictEntry(ss, self.toLiteral('.prefix'),
                            self.toLiteral(pref))
          self.setDictEntry(ss, self.toLiteral('.qName'), 
                            self.toLiteral(mapping['.qName']))
          self.setDictEntry(ss, self.toLiteral('.name'),
                            self.toLiteral(ddName))
 
        # set top mapping parameters
        for ss in ('guid', '.prefix', '.qName'):
          self.setDictEntry(currentMapVar, self.toLiteral(ss),
                            self.toLiteral(mapping[ss]))
        self.setDictEntry(currentMapVar, self.toLiteral('.name'),
                          self.toLiteral('mapping'))
        ss = 'globalRelease'
        self.setDictEntry(currentMapVar, self.toLiteral(ss),
                          self.toLiteral(str(mapping[ss])))
        self.writeNewline()
        self.writeComment("Set up top level dictionaries")
        self.endBlock()

    else:
    
      self.writeNewline()
      self.writeComment("Set up top level dictionaries")
      for ddName in  ('loadMaps', 'mapsByGuid'):
        ss = self.getDictEntry(globalMapVar, self.toLiteral(ddName))
        self.setVar(self.localVarNames[ddName], 
                    ss, self.dictVarType, self.dictVarType)
      self.writeNewline()
    
    for ddName in  ('abstractTypes', 'exolinks'):
      ss = self.getDictEntry(globalMapVar, self.toLiteral(self.prefix))
      ss = self.getDictEntry(ss, self.toLiteral(ddName))
      self.setVar(self.localVarNames[ddName], 
                  ss, self.dictVarType, self.dictVarType)

  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def initLeafPackage(self, package):
    """ write API header for package containing actual code
    """
    
    super(XmlMapWrite, self).initLeafPackage(package)

    self.openObjFile(package)

    self.writeFileHeader(package)
    
  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def endLeafPackage(self, package):
  
    super(XmlMapWrite, self).endLeafPackage(package)

    self.closeFile()

  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def processDataType(self, clazz):
    
    self.writeNewline()
    self.writeComment("DataType %s" % clazz.name)
    
    XmlGen.processDataType(self, clazz)
    
    self.processAbstractDataType(clazz)
    
    # add converters to and from string
    self.addXmlStringFunctions(self.localVarNames['currentMap'], 
                               clazz.typeCodes[self.modelFlavours['language']])

  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def processDataObjType(self, clazz):
    
    self.writeNewline()
    self.writeComment("DataObjType %s" % clazz.name)
    
    XmlGen.processDataObjType(self, clazz)
    
    self.processAbstractDataType(clazz)
    
    self.addXmlClassCreation(self.localVarNames['currentMap'], clazz)

  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def processClass(self, clazz):
    
    self.writeNewline()
    self.writeComment("Class %s" % clazz.name)
    
    XmlGen.processClass(self, clazz)
    
    self.processAbstractDataType(clazz)
    
    self.addXmlClassCreation(self.localVarNames['currentMap'], clazz)

  ###########################################################################

  ###########################################################################
  
  def processAbstractDataType(self, clazz):
    
    lv = self.localVarNames
    currentMapVar = lv['currentMap']
    classMap = self.globalMap[self.prefix]['abstractTypes'][clazz.name]
  
    self.newDict(currentMapVar, keyType=self.stringVarType, needDeclType=True)
    
    # add to top level dicts
    self.setDictEntry(lv['abstractTypes'], 
                      self.toLiteral(clazz.name), currentMapVar)
    self.setDictEntry(lv['mapsByGuid'], 
                      self.toLiteral(classMap['guid']), currentMapVar)
    
    if clazz.isAbstract:
      tt = ('type', 'guid')
    else:
      tt = ('tag', 'type', 'guid')
      self.setDictEntry(lv['loadMaps'], 
                        self.toLiteral(classMap['tag']), currentMapVar)
    for ss in tt:
      self.setDictEntry(currentMapVar, self.toLiteral(ss), 
                        self.toLiteral(classMap[ss]))
    
    for ss in ('eType', 'fromParent', 'isTop', 'objkey', 'singleKid'):
      xx = classMap.get(ss)
      if xx is not None:
        self.setDictEntry(currentMapVar, self.toLiteral(ss),
                          self.toLiteral(xx))

  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def endComplexDataType(self, clazz):
    
    lv = self.localVarNames
    aList = lv['aList']
    contentMapVar = lv['contentMap']
    abstractTypes = lv['abstractTypes']
    classMap = self.globalMap[self.prefix]['abstractTypes'][clazz.name]
  
    self.newDict(contentMapVar, keyType=self.stringVarType, needDeclType=True)
    self.setDictEntry(lv['currentMap'], self.toLiteral('content'), 
                      contentMapVar)
    
    XmlGen.endComplexDataType(self, clazz)
    
    self.writeComment("End of %s" % clazz.name)
    self.writeNewline()
    
    self.startBlock()
    cMap = self.getDictEntry(abstractTypes, self.toLiteral(clazz.name))
    self.setVar(lv['currentMap'], cMap, self.dictVarType, self.dictVarType)
    for ss in ('headerAttrs', 'simpleAttrs', 'optLinks', 'cplxAttrs', 
               'children'):
      initValues = classMap.get(ss)
      if initValues:
        if ss == 'cplxAttrs':
          # then they appear in correct order in file
          initValues.reverse()
        
        self.newList(aList, needDeclType=True,
                           varType=self.stringVarType, initValues=initValues)
        self.setDictEntry(lv['currentMap'], self.toLiteral(ss), aList)

    self.endBlock()
    self.writeNewline()
    
  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def processAttribute(self, elem, inClass):
    
    lv = self.localVarNames
    currentMapVar = self.localVarNames['currentMap']
    
    result = XmlGen.processAttribute(self, elem, inClass)
    
    if result is not None:
    
      self.writeNewline()
      self.writeComment("Attribute %s.%s" % (inClass.name, elem.name))
      
      if elem.container is inClass:
        # write map
        self.processElement(result)
 
        # set default value
        self.addDefaultValues(currentMapVar, result, elem)
 
        # add contents dict
        if result['type'] == 'attr':
          # simple type
          self.setDictEntry(currentMapVar, self.toLiteral('data'),
           self.getDictEntry(lv['mapsByGuid'],
           self.toLiteral(result['data']['guid']))
          )
 
        else:
          # result['type'] == 'dobj'
          # complex type
          dd = result['content']
          ss = self.getDictEntry(lv['globalMap'], self.toLiteral(dd['.prefix']))
          ss = self.getDictEntry(ss, self.toLiteral(dd['.name']))
          self.setDictEntry(currentMapVar, self.toLiteral('content'), ss)
      
      else:
        # write reference to map
        ss = self.getDictEntry(lv['mapsByGuid'], self.toLiteral(result['guid']))
        self.setDictEntry(lv['contentMap'], self.toLiteral(result['name']), ss)

    #
    return result
    
  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def processRole(self, elem, inClass):
    
    lv = self.localVarNames
    currentMapVar = self.localVarNames['currentMap']
    
    result = XmlGen.processRole(self, elem, inClass)
    
    if result is not None:
    
      self.writeNewline()
      self.writeComment("Role %s.%s" % (inClass.name, elem.name))
      
      if elem.container is inClass:
        # write map
    
        self.processElement(result)
        
        if 'copyOverride' in result:
          # add copyOveride tag - used for subtree copying
          self.setDictEntry(currentMapVar, self.toLiteral('copyOverride'), 
                            self.toLiteral(result['copyOverride']))
 
        # add contents dict
        typ = result['type']
        if typ != 'link':
          # typ in ('exotop', 'exolink', 'child')
          dd = result['content']
          ss = self.getDictEntry(lv['globalMap'], self.toLiteral(dd['.prefix']))
          ss = self.getDictEntry(ss, self.toLiteral(dd['.name']))
          self.setDictEntry(currentMapVar, self.toLiteral('content'),ss)
          
      else:
        # write reference to map
        ss = self.getDictEntry(lv['mapsByGuid'], self.toLiteral(result['guid']))
        self.setDictEntry(lv['contentMap'], self.toLiteral(result['name']), ss)
    #
    return result

  ###########################################################################

  ###########################################################################
  
  def processElement(self, elemMap):
    
    lv = self.localVarNames
    currentMapVar = self.localVarNames['currentMap']
      
    # new dict
    #self.newDict(currentMapVar, keyType=self.stringVarType, needDeclType=True)
    self.newDict(currentMapVar, keyType=self.stringVarType)
    
    # add to top level dicts
    self.setDictEntry(lv['contentMap'],
                      self.toLiteral(elemMap['name']), currentMapVar)
    self.setDictEntry(lv['mapsByGuid'], 
                      self.toLiteral(elemMap['guid']), currentMapVar)
    self.setDictEntry(lv['loadMaps'], 
                      self.toLiteral(elemMap['tag']), currentMapVar)
    
    # add parameters
    for ss in ('tag', 'type', 'guid', 'name', 'hicard', 'locard'):
      self.setDictEntry(currentMapVar, self.toLiteral(ss), 
                        self.toLiteral(elemMap[ss]))

    for ss in ('eType', 'proc', 'implSkip'):
      xx = elemMap.get(ss)
      if xx is not None:
        self.setDictEntry(currentMapVar, self.toLiteral(ss), 
                          self.toLiteral(xx))
    
  ###########################################################################

  ###########################################################################
  
  # overrides XmlGen
  def processExoLink(self, clazz):
    
    lv = self.localVarNames
    currentMapVar = self.localVarNames['currentMap']
    
    elemMap = XmlGen.processExoLink(self, clazz)
    
    self.writeNewline()
    self.writeComment("Out-of-package link to %s" % clazz.name)
    self.startBlock()
      
    # new dict
    self.newDict(currentMapVar, keyType=self.stringVarType, needDeclType=True)
    
    # connect to toplevel dicts
    self.setDictEntry(lv['exolinks'], 
                      self.toLiteral(clazz.name), currentMapVar)
    self.setDictEntry(lv['loadMaps'], 
                      self.toLiteral(elemMap['tag']), currentMapVar)
    
    # add parameters
    for ss in ('tag', 'type', 'guid', 'name', 'eType'):
      self.setDictEntry(currentMapVar, self.toLiteral(ss), 
                        self.toLiteral(elemMap[ss]))
    
    self.addXmlClassCreation(currentMapVar, clazz)
    
    # add keyMaps list                    
    self.newList(lv['aList'], needDeclType=True)
    self.setDictEntry(currentMapVar, self.toLiteral('keyMaps'), lv['aList'])
    
    for km in elemMap['keyMaps']:
    
      if 'tag' in km:
        # simple attribute - elemmap
        ss = self.getDictEntry(lv['mapsByGuid'], self.toLiteral(km['guid']))
      else:
        # complex attribute or exolink - abstractTypes or exolinks dict
        ss = self.getDictEntry(lv['globalMap'], self.toLiteral(km['.prefix']))
        ss = self.getDictEntry(ss, self.toLiteral(km['.name']))
      
      # add to list
      self.addList(ss, lv['aList'])

    self.endBlock()
                      
  ###########################################################################

  ###########################################################################
  
  def addXmlStringFunctions(self, dictName, typeCode):
    """ Write info for conversion to and from string
    Must be overridden in subclasses
    """
    
    raise MemopsError("XmlMapWrite.addXmlStringFunctions must be overridden")

  ###########################################################################

  ###########################################################################
  
  def addDefaultValues(self, dictName, elemMap, elem):
    """ write default values.
    NB individual languages may choose to skip some of the more difficult ones.
    The value is compared with the stored value in XmlIo, look there for 
    exact format.
    """
    
    raise MemopsError("XmlMapWrite.addDefaultValues must be overridden")

  ###########################################################################

  ###########################################################################
  
  def addXmlClassCreation(self, dictName,  clazz, package=None):
    """ Write info for creation of new class
    """
    
    raise MemopsError("XmlMapWrite.addXmlClassCreation must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def getSaveToStreamDocString(self):

    return """
Write topObject and its descendants to open stream 'stream'.

'mapping' contains all XMLtag-Model and Model-XMLtag mapping info.
'comment' is added at the top of the file as an XML comment,
If 'simplified' one-to-many links are written out at one end only,
(otherwise at both ends), and attributes equal to the default are skipped.
If 'compact' most hicard==1 attributes are written as XML attributes of
the container, otherwise all attributes are written as elements.
If 'expanded' all attributes are written with inside an explicit type
definition element (e.g. <aSerial><Int>5</Int></aSerial> instead of
 <aSerial>5</aSerial>. Expanded form may be easier to do backwards
 compatibility in some rare cases.
"""

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def writeSaveToStream(self, originator, indentBySpaces = 2):

    apiDirs = [metaConstants.apiCodeDir]
    self.rootClassVarType = self.getImportName(self.rootClass, subDirs=apiDirs)
    self.baseClassVarType = self.getImportName(self.baseClass, subDirs=apiDirs)
    self.baseDataVarType = self.getImportName(self.baseDataType, subDirs=apiDirs)
    self.dataRootVarType = self.getImportName(self.dataRoot, subDirs=apiDirs)
    self.topObjectVarType = self.getImportName(self.topObject, subDirs=apiDirs)

    tt = self.dictInterfaceType(self.stringVarType, self.anyVarType)
    params= (('stream', self.fileInterfaceType('w'), 'output stream'),
             ('topObject', self.baseClassVarType, 'top object that is being saved'),
             ('mapping', tt, 'mapping which determines how to save (can be null)', self.toLiteral(None)),
             ('comment', self.stringVarType, 'comment to insert at top of file', self.toLiteral(None)),
             ('simplified', self.booleanVarType, 'whether output should be simplified', self.toLiteral(True)),
             ('compact', self.booleanVarType, 'whether output should be made compact', self.toLiteral(True)),
             ('expanded', self.booleanVarType, 'whether output should be expanded', self.toLiteral(False)))
    docString = """Write topObject and its descendants to open stream 'stream'.

'mapping' contains all XMLtag-Model and Model-XMLtag mapping info.
'comment' is added at the top of the file as an XML comment,
If 'simplified' one-to-many links are written out at one end only,
(otherwise at both ends), and attributes equal to the default are skipped.
If 'compact' most hicard==1 attributes are written as XML attributes of
the container, otherwise all attributes are written as elements.
If 'expanded' all attributes are written with inside an explicit type
definition element (e.g. <aSerial><Int>5</Int></aSerial> instead of
 <aSerial>5</aSerial>. Expanded form may be easier to do backwards
 compatibility in some rare cases.
"""

    self.streamStartFunc(funcname='saveToStream', params=params,
                         docString=docString)
    self.writeSaveToStreamBody(originator, indentBySpaces=indentBySpaces)
    self.endFunc()

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def writeSaveToStreamBody(self, originator, indentBySpaces = 2):

    # set up
    self.writeComment('set up')
    self.setVar('doComplex', self.negate('simplified'), varType=self.booleanVarType)
    self.writeNewline()

    # check parameters
    self.startIf(self.logicalOp('compact', 'and', 'expanded'))
    self.raiseApiError("XML save: Parameters 'compact' and 'expanded' are incompatible")
    self.endIf()

    # check for topObject
    self.writeComment('check for topObject')
    self.defineVar('isImplementation', varType=self.booleanVarType)
    self.startIf(self.isInstance('topObject', self.dataRootVarType))
    self.setVar('isImplementation', self.toLiteral(True))
    self.elseIf(self.isInstance('topObject', self.topObjectVarType))
    self.setVar('isImplementation', self.toLiteral(False))
    self.elseIf()
    self.raiseApiError('XML save: top obj is neither MemopsRoot nor TopObject', 
                       'topObject')
    self.endIf()

    # make sentinel objects
    self.writeComment('make sentinel objects')
    self.newList('startObj', varType=self.anyVarType, needDeclType=True)
    self.newList('endObj', varType=self.anyVarType, needDeclType=True)
    self.writeNewline()

    self.newList('reuseList', varType=self.anyVarType, initValues=[None],
                       needDeclType=True)
    self.newList('emptyList', varType=self.stringVarType, needDeclType=True)
    self.writeNewline()

    # set object ID dictionary
    # self.writeComment('set object ID dictionary')
    # self.setVar('nextID', 1, varType=self.intVarType)
    # self.newDict('classIDs', keyType=self.anyVarType, valueType=self.intVarType,
    #              needDeclType=True)
    # self.writeNewline()

    # set start indent
    self.writeNewline()
    self.writeComment('set start indent')
    self.setVar('indentBySpaces', self.toLiteral(indentBySpaces), 
                varType=self.intVarType)
    self.setVar('nIndent', self.toLiteral(0), varType=self.intVarType)
    self.setVar('indent', self.toLiteral(''), varType=self.stringVarType)

    # xml header
    self.writeNewline()
    self.streamWrite(self.toLiteral('<?xml version="1.0" encoding="UTF-8"?>\n'))

    # file comment
    self.writeNewline()
    self.startIf(self.stringIsNotEmpty('comment'))
    self.streamWriteComment('comment')
    self.endIf()

    # start StorageUnit
    self.setVar('guid', self.getDictEntry('mapping', self.toLiteral('guid')),
                varType=self.stringVarType, castType=self.stringVarType)
    self.setVar('release', 
                self.getDictEntry('mapping', self.toLiteral('globalRelease')),
                varType=self.stringVarType, castType=self.stringVarType)
    self.setVar('date', self.currentTime(),
                varType=self.stringVarType, castType=self.stringVarType)
    self.setVar('originator', self.toLiteral(originator), 
                varType=self.stringVarType)

    self.streamWriteStartElement(self.toLiteral('_StorageUnit'), time='date', 
                                 release='release', packageGuid='guid', 
                                 originator='originator')
    self.streamWrite(self.toLiteral('\n'))

    # Write objects
    self.writeNewline()
    self.writeComment('Write objects')
    self.printMessage(self.toLiteral('start generating output : '), 
     self.callFunc('getQualifiedName', 'topObject', doWrite=False)
    )

    # new stacks: stack and mapStack
    self.newStack('stack', initValues=('topObject',), needDeclType=True)
    initValue = self.getDictEntry('mapping', self.toLiteral('abstractTypes'),
                        castType=self.dictInterfaceType(), keyIsMandatory=True)
    initValue = self.getDictEntry(initValue,
          self.getClassname('topObject'), keyIsMandatory=True)
          ####castType=self.dictInterfaceType())
    self.newStack('mapStack', initValues=(initValue,), needDeclType=True)

    # while stack is not empty
    self.startWhile(self.stackIsNotEmpty('stack'))
    self.writeNewline()
    self.popStack('stack', 'val', varType=self.anyVarType)
    self.popStack('mapStack', 'curMap0', varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 1
    self.writeComment('IF BLOCK 1')
    # if val is startObj
    self.startIf(self.comparison('val', 'is', 'startObj'))
    self.writeComment('start new attribute-less element')
    self.writeComment('NB we have been cheating, putting a string on the mapStack')
    self.streamWriteStartElement('curMap0')
    self.streamIndent(increasing=True)
    self.writeNewline()

    # IF BLOCK 1
    # else if val is endObj
    self.elseIf(self.comparison('val', 'is', 'endObj'))
    self.writeComment('end element')
    self.writeComment('NB we have been cheating, putting a string on the mapStack')
    self.streamIndent(increasing=False)
    self.streamWriteEndElement('curMap0', doIndent=True)
    self.writeNewline()

    # IF BLOCK 1
    # else (val is a real object)
    self.elseIf()
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('curMap', 'curMap0', varType=tt, castType=tt)
    self.setVar('typ', self.getDictEntry('curMap', self.toLiteral('type')), 
                varType=self.stringVarType, castType=self.stringVarType)
    self.writeNewline()

    # IF BLOCK 2
    self.writeComment('IF BLOCK 2')
    # if typ == 'simple'
    self.startIf(self.comparison('typ', '==', self.toLiteral('simple')))
    ss = self.getDictEntry('curMap', self.toLiteral('tag'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('tag', ss, varType=tt, castType=tt)
    ss = self.getDictEntry('curMap', self.toLiteral('toStr'))
    self.setVar('toStr', ss, varType=self.anyVarType)
    self.writeNewline()

    self.startIf(self.comparison(self.toLiteral('text'), '==', 'toStr'))
    self.streamTextToString('val')
    self.elseIf()
    self.streamNonTextToString('val')
    self.endIf()
    self.streamWriteElement('tag', 'val')
    self.writeNewline()

    # IF BLOCK 2
    # else if typ == 'exo'
    self.elseIf(self.comparison('typ', '==', self.toLiteral('exo')))
    ss = self.getDictEntry('curMap', self.toLiteral('tag'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('tag', ss, varType=tt, castType=tt)
    self.pushStack('stack', 'endObj')
    self.pushStack('mapStack', 'tag')
    ss = self.getDictEntry('curMap', self.toLiteral('keyMaps'), keyIsMandatory=True)
    tt = self.listInterfaceType(self.dictInterfaceType(self.stringVarType))
    self.setVar('keyMaps', ss, varType=tt, castType=tt)
    self.writeNewline()

    # put keys on stack
    self.writeComment('put keys on stack')
    tt = self.listInterfaceType(self.anyVarType)
    ss = self.castVar(self.baseClassVarType, 'val')
    self.setVar('keys', self.callFunc('getFullKey', ss, self.toLiteral(True), doWrite=False), varType=tt)
    self.startIndexLoop('ii', self.lenList('keys'), isReversed=True)
    self.setVar('key', self.getByIndexInList('ii', 'keys'), varType=self.anyVarType)
    self.pushStack('stack', 'key')
    # TBD: look at again when (if) have common superclass
    self.startIf(self.logicalOp(
     self.isInstance('key', self.baseClassVarType),
     'or',
     self.isInstance('key', self.baseDataVarType),
    ))
    ss = self.getClassname('key')
    ss = self.getDictEntry(self.getByIndexInList('ii', 'keyMaps'), ss)
    self.pushStack('mapStack', ss)
    self.elseIf()
    ss = self.getByIndexInList('ii', 'keyMaps')
    self.pushStack('mapStack', ss)
    self.endIf()
    self.endIndexLoop()

    self.writeComment('Could be done directly')
    self.writeComment('But it will not make much difference, so for consistency')
    self.pushStack('stack', 'startObj')
    self.pushStack('mapStack', 'tag')
    self.writeNewline()
    
    # IF BLOCK 2
    # else typ is class or cplx
    self.elseIf()
    self.writeComment('type class or cplx')
    self.writeNewline()

    # setup
    self.writeComment('setup')
    self.setVar('stackVal', 'val', varType=self.anyVarType)

    ss = self.getDictEntry('curMap', self.toLiteral('content'), keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('contDict', ss, varType=tt, castType=tt)
    for ss in ('headerAttrs', 'optLinks', 'simpleAttrs', 'cplxAttrs'):
      tt = self.getDictEntry('curMap', self.toLiteral(ss), defaultValue='emptyList')
      tt = self.castVar(self.listInterfaceType(self.stringVarType), tt)
      self.setVar(ss, tt, varType=self.listInterfaceType(self.stringVarType))
    self.writeNewline()

    ss = self.getDictEntry('curMap', self.toLiteral('tag'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('classtag', ss, varType=tt, castType=tt)
    self.writeNewline()

    # put end-of-object marker on stack
    self.writeComment('put end-of-object marker on stack')
    self.pushStack('stack', 'endObj')
    self.pushStack('mapStack', 'classtag')
    self.writeNewline()

    # IF BLOCK 3
    self.writeComment('IF BLOCK 3')
    # if typ == 'class'
    self.startIf(self.comparison('typ', '==', self.toLiteral('class')))

    # # get and write obj _ID
    # self.writeComment('get and write obj _ID')
    # self.setVar('_ID', self.getDictEntry('classIDs', 'val'), varType=self.intVarType, castType=self.intVarType)
    # self.startIf(self.valueIsNone('_ID'))
    # self.setVar('_ID', 'nextID')
    # self.setDictEntry('classIDs', 'val', '_ID')
    # self.setVar('nextID', self.arithmetic('nextID', '+', 1))
    # self.endIf()
    # self.writeNewline()


    self.streamWriteStartElement('classtag', closeElement=False)
    self.writeNewline()

    # IF BLOCK 3
    # else typ == 'cplx'
    self.elseIf()
    self.writeComment("typ == 'cplx'")
    self.streamWriteStartElement('classtag', closeElement=False)
    self.writeNewline()
    
    # IF BLOCK 3
    self.endIf()

    # IF BLOCK 4
    self.writeComment('IF BLOCK 4')
    # if compact
    self.startIf('compact')
    # set header attributes and links
    self.writeComment('set header attributes and links')
    self.defineVar('names', self.listInterfaceType(self.stringVarType))
    ss = self.collectionIsNotEmpty('optLinks', isUnique=False, isOrdered=True)
    self.startIf(self.logicalOp('doComplex', 'and', ss))
    self.concatenateList('names', None, 'headerAttrs', 'optLinks')
    self.elseIf()
    self.setVar('names', 'headerAttrs')
    self.endIf()
    self.writeNewline()

    # LOOP A
    self.writeComment('LOOP A')
    self.startLoop('name', 'names', isUnique=False, isOrdered=True, varType=self.stringVarType)

    ss = self.getDictEntry('contDict', 'name', keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('tmpMap', ss, varType=tt, castType=tt)

    ss = self.getDictEntry('tmpMap', self.toLiteral('implSkip'),
               castType=self.booleanVarType, defaultValue=self.toLiteral(False))
    self.startIf(self.logicalOp('isImplementation', 'and', ss))
    self.continueLoop()
    self.endIf()
    self.writeNewline()

    # NB hicard is always 1 here
    # NB here we use name instead of tag, as tag is 'Clazz.attr'
    self.writeComment('NB hicard is always 1 here')
    self.writeComment("NB here we use name instead of tag, as tag is 'Clazz.attr'")

    tt = self.castVar(self.rootClassVarType, 'stackVal')
    ss = self.streamGetValue(tt, 'name', keyIsMandatory=True)
    self.setVar('value', ss, varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 5
    self.writeComment('IF BLOCK 5')
    self.startIf(self.valueIsNotNone('value'))

    ss = self.getDictEntry('tmpMap', self.toLiteral('type'), keyIsMandatory=True)
    self.setVar('typ', ss, castType=self.stringVarType)
    self.writeNewline()

    # IF BLOCK 6
    self.writeComment('IF BLOCK 6')
    # if typ == 'link'
    self.startIf(self.comparison('typ', '==', self.toLiteral('link')))


    ss = self.streamGetValue('value', '_ID', keyIsMandatory=True)
    self.setVar('_ID', ss, varType=self.intVarType)

    #
    # self.setVar('_ID', self.getDictEntry('classIDs', 'value'),
    #             varType=self.intVarType, castType=self.intVarType)
    # self.startIf(self.valueIsNone('_ID'))
    # self.setVar('_ID', 'nextID')
    # self.setDictEntry('classIDs', 'value', '_ID')
    # self.setVar('nextID', self.arithmetic('nextID', '+', 1))
    # self.endIf()

    ss = self.getDictEntry('tmpMap', self.toLiteral('name'), castType=self.stringVarType)
    self.streamWriteAttr(ss, '_ID', haveUnderscore=True)
    self.writeNewline()

    # IF BLOCK 6
    # else typ == 'attr'
    self.elseIf()
    self.writeComment("typ == 'attr'")

    # IF BLOCK 7
    self.writeComment('IF BLOCK 7')
    ss = self.getDictEntry('tmpMap', self.toLiteral('default'))
    ss = self.comparison('value', '!=', ss)
    self.startIf(self.logicalOp('doComplex', 'or', ss))
    ss = self.dictInterfaceType(self.stringVarType)
    ss = self.getDictEntry('tmpMap', self.toLiteral('data'), castType=ss, keyIsMandatory=True)
    self.setVar('toStr', self.getDictEntry(ss, self.toLiteral('toStr')), varType=self.anyVarType)
    self.startIf(self.comparison(self.toLiteral('text'), '==', 'toStr'))
    self.streamTextToString('value')
    self.elseIf()
    self.streamNonTextToString('value')
    self.endIf()
    ss = self.getDictEntry('tmpMap', self.toLiteral('name'), keyIsMandatory=True)
    self.streamWriteAttr(ss, 'value')

    # IF BLOCK 7
    self.endIf()

    # IF BLOCK 6
    self.endIf()

    # IF BLOCK 5
    self.endIf()

    # LOOP A
    self.endLoop()

    # IF BLOCK 4
    self.endIf()
    self.writeNewline()

    # IF BLOCK 8
    self.writeComment('IF BLOCK 8')
    # class contains no XML elements. end immediately
    ss = self.logicalOp(self.collectionIsEmpty('simpleAttrs', isUnique=False, isOrdered=True),
          'and', self.collectionIsEmpty('cplxAttrs', isUnique=False, isOrdered=True))
    self.startIf(self.logicalOp('compact', 'and', ss))
    self.writeComment('class contains no XML elements. end immediately')
    self.popStack('stack')
    self.popStack('mapStack')
    self.streamWrite(self.toLiteral('/>\n'))
    self.writeNewline()

    # IF BLOCK 8
    self.elseIf()
    # class may have more elements - process them
    # end start element
    self.writeComment('class may have more elements - process them')
    self.writeComment('end start element')
    self.streamWrite(self.toLiteral('>\n'))
    self.writeNewline()

    # set indent
    self.writeComment('set indent')
    self.streamIndent(increasing=True)
    self.writeNewline()

    self.defineVar('names', self.listInterfaceType(self.stringVarType))
    self.startIf('compact')
    self.setVar('names', 'simpleAttrs')
    self.elseIf(self.logicalOp('doComplex', 'and',
                  self.collectionIsNotEmpty('optLinks', isUnique=False, isOrdered=True)))
    self.concatenateList('names', None, 'headerAttrs', 'optLinks', 'simpleAttrs')
    self.elseIf()
    self.concatenateList('names', None, 'headerAttrs', 'simpleAttrs')
    self.endIf()
    self.writeNewline()

    # LOOP B
    self.writeComment('LOOP B')
    # set simple attributes and links
    self.writeComment('set simple attributes and links')
    self.startLoop('name', 'names', isUnique=False, isOrdered=True, varType=self.stringVarType)
    ss = self.getDictEntry('contDict', 'name', keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('tmpMap', ss, varType=tt, castType=tt)
    ss = self.getDictEntry('tmpMap', self.toLiteral('implSkip'),
               castType=self.booleanVarType, defaultValue=self.toLiteral(False))
    self.startIf(self.logicalOp('isImplementation', 'and', ss))
    self.continueLoop()
    self.endIf()

    # IF BLOCK 9
    self.writeComment('IF BLOCK 9')
    tt = self.castVar(self.rootClassVarType, 'stackVal')
    self.setVar('val', self.streamGetValue(tt, 'name', keyIsMandatory=True))
    ss = self.getDictEntry('tmpMap', self.toLiteral('default'))
    ss = self.comparison('val', '!=', ss)
    self.startIf(self.logicalOp('doComplex', 'or', ss))

    ss = self.getDictEntry('tmpMap', self.toLiteral('hicard'), keyIsMandatory=True)
    ss = self.comparison(ss, '==', self.toLiteral(1))
    self.startIf(self.logicalOp(ss, 'and', self.valueIsNotNone('val')))
    # put here in case of (future) types
    self.writeComment('put here in case of (future) types')
    self.setByIndexInList(self.toLiteral(0), 'val', 'reuseList')
    self.setVar('val', 'reuseList')
    self.endIf()
    self.writeNewline()

    # IF BLOCK 10
    self.writeComment('IF BLOCK 10')
    self.startIf(self.collectionNotNoneAndNotEmpty('val', isUnique=False, isOrdered=True))
    # TBD: because have collectionInterfaceType here, startLoop function
    # calls below are passing bogus isUnique and isOrdered, could be set
    # (in Python and Java the isUnique and isOrdered arguments are ignored so ok for now)
    tt = self.collectionInterfaceType()
    self.setVar('vals', 'val', varType=tt, castType=tt)
    ss = self.getDictEntry('tmpMap', self.toLiteral('tag'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('tag', ss, varType=tt, castType=tt)

    ss = self.getDictEntry('tmpMap', self.toLiteral('type'), keyIsMandatory=True)
    self.setVar('typ', ss, castType=self.stringVarType)
    self.writeNewline()

    # IF BLOCK 11
    self.writeComment('IF BLOCK 11')
    # if typ == 'link'
    self.startIf(self.comparison('typ', '==', self.toLiteral('link')))
    self.streamWriteStartElement('tag', newLine=False)

    # LOOP C
    self.writeComment('LOOP C')
    self.startLoop('value', 'vals', isUnique=False, isOrdered=True)

    self.setVar('_ID', self.streamGetValue('value', '_ID', keyIsMandatory=True), varType=self
                .intVarType, castType=self.intVarType)

    # self.setVar('_ID', self.getDictEntry('classIDs', 'value'), varType=self.intVarType, castType=self.intVarType)
    # self.startIf(self.valueIsNone('_ID'))
    # self.setVar('_ID', 'nextID')
    # self.setDictEntry('classIDs', 'value', '_ID')
    # self.setVar('nextID', self.arithmetic('nextID', '+', 1))
    # self.endIf()

    self.streamWriteValue('_ID', haveUnderscore=True)

    # LOOP C
    self.endLoop()
    self.writeNewline()

    self.streamWriteEndElement('tag')
    self.writeNewline()

    # IF BLOCK 11
    ss = self.getDictEntry('tmpMap', self.toLiteral('eType'))
    ss = self.comparison(self.toLiteral('cplx'), '==', ss)
    self.elseIf(self.logicalOp(ss, 'or', 'expanded'))

    # typ == 'attr', complex XML element
    self.writeComment("typ == 'attr', complex XML element")
    self.streamWriteStartElement('tag')
    self.streamIndent(increasing=True)
    self.writeNewline()

    tt = self.dictInterfaceType(self.stringVarType)
    tt = self.getDictEntry('tmpMap', self.toLiteral('data'), castType=tt, keyIsMandatory=True)
    ss = self.getDictEntry(tt, self.toLiteral('tag'), keyIsMandatory=True)
    self.setVar('tTag', ss, varType=self.stringVarType, castType=self.stringVarType)
    ss = self.getDictEntry(tt, self.toLiteral('toStr'))
    self.setVar('toStr', ss, varType=self.anyVarType)
    self.startIf(self.comparison(self.toLiteral('text'), '==', 'toStr'))
    self.startLoop('value', 'vals', isUnique=False, isOrdered=True)
    self.streamTextToString('value')
    self.writeNewline()
    self.streamWriteElement('tTag', 'value')
    self.endLoop()
    self.elseIf()
    self.startLoop('value', 'vals', isUnique=False, isOrdered=True)
    self.streamNonTextToString('value')
    self.writeNewline()
    self.streamWriteElement('tTag', 'value')
    self.endLoop()
    self.endIf()

    self.streamIndent(increasing=False)
    self.streamWriteEndElement('tag', doIndent=True)
    self.writeNewline()

    # IF BLOCK 11
    self.elseIf()
    # typ == 'attr', simple XML element
    self.writeComment("typ == 'attr', simple XML element")
    tt = self.dictInterfaceType(self.stringVarType)
    tt = self.getDictEntry('tmpMap', self.toLiteral('data'), castType=tt, keyIsMandatory=True)
    ss = self.getDictEntry(tt, self.toLiteral('toStr'))
    self.setVar('toStr', ss, varType=self.anyVarType)
    self.streamWriteStartElement('tag', newLine=False)
    self.writeNewline()
    self.startIf(self.comparison(self.toLiteral('text'), '==', 'toStr'))
    self.startLoop('value', 'vals', isUnique=False, isOrdered=True)
    self.streamTextToString('value')
    self.streamWriteValue('value')
    self.endLoop()
    self.elseIf()
    self.startLoop('value', 'vals', isUnique=False, isOrdered=True)
    self.streamNonTextToString('value')
    self.streamWriteValue('value')
    self.endLoop()
    self.endIf()
    self.streamWriteEndElement('tag')


    # IF BLOCK 11
    self.endIf()

    # IF BLOCK 10
    self.endIf()

    # IF BLOCK 9
    self.endIf()

    # LOOP B
    self.endLoop()
    self.writeNewline()

    # put DataObjType attrs, exolinks, and child links on stack
    self.writeComment('put DataObjType attrs, exolinks, and child links on stack')
    self.writeNewline()

    # LOOP D
    self.writeComment('LOOP D')
    self.startLoop('name', 'cplxAttrs', isUnique=False, isOrdered=True, varType=self.stringVarType)
    tt = self.castVar(self.rootClassVarType, 'stackVal')
    self.setVar('val', self.streamGetValue(tt, 'name', keyIsMandatory=True))
    self.writeNewline()

    # IF BLOCK 12
    self.writeComment('IF BLOCK 12')
    self.startIf(self.valueNotNoneAndIfListNotEmpty('val'))
    ss = self.getDictEntry('contDict', 'name', keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('tmpMap', ss, varType=tt, castType=tt)
    self.writeNewline()

    # IF BLOCK 13
    self.writeComment('IF BLOCK 13')
    ss = self.getDictEntry('tmpMap', self.toLiteral('implSkip'),
               castType=self.booleanVarType, defaultValue=self.toLiteral(False))
    self.startIf(self.negate(self.logicalOp('isImplementation', 'and', ss)))
    self.writeNewline()

    ss = self.getDictEntry('tmpMap', self.toLiteral('tag'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('tag', ss, varType=tt, castType=tt)

    ss = self.getDictEntry('tmpMap', self.toLiteral('content'), keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('tmpCont', ss, varType=tt, castType=tt)
    self.writeNewline()

    self.pushStack('stack', 'endObj')
    self.pushStack('mapStack', 'tag')
    self.writeNewline()

    # IF BLOCK 14
    self.writeComment('IF BLOCK 14')
    tt = self.getDictEntry('tmpMap', self.toLiteral('hicard'), keyIsMandatory=True)
    self.startIf(self.comparison(tt, '==', self.toLiteral(1)))
    self.pushStack('stack', 'val')
    ss = self.getDictEntry('tmpCont', self.getClassname('val'), keyIsMandatory=True)
    self.pushStack('mapStack', ss)
    self.writeNewline()

    # IF BLOCK 14
    self.elseIf()
    self.streamOrderedCollection('val')

    # IF BLOCK 14
    self.endIf()

    self.pushStack('stack', 'startObj')
    self.pushStack('mapStack', 'tag')

    # IF BLOCK 13
    self.endIf()

    # IF BLOCK 12
    self.endIf()

    # LOOP D
    self.endLoop()

    # IF BLOCK 8
    self.endIf()

    # IF BLOCK 2
    self.endIf()

    # IF BLOCK 1
    self.endIf()

    self.endWhile()

    self.streamWrite(self.toLiteral('\n</_StorageUnit>\n<!--End of Memops Data-->\n'))

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWriteElement(self, element, value = '', **attrs):

    self.streamWriteStartElement(element, newLine = False, **attrs)
    self.streamWrite(self.castVar(self.stringVarType, value))
    self.streamWriteEndElement(element)

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamTextToString(self, value):

    self.writeComment('String type')
    vv = self.castVar(self.stringVarType, value)
    self.setVar(value, self.stringReplace(vv, self.toLiteral('&'), self.toLiteral('&amp;')))
    self.setVar(value, self.stringReplace(vv, self.toLiteral('"'), self.toLiteral('&quot;')))
    self.setVar(value, self.stringReplace(vv, self.toLiteral('<'), self.toLiteral('&lt;')))
    self.setVar(value, self.stringReplace(vv, self.toLiteral('>'), self.toLiteral('&gt;')))

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWrite(self, s):

    raise MemopsError("XmlMapWrite.streamWrite must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWriteStartElement(self, element, closeElement = True, newLine = True, **attrs):

    raise MemopsError("XmlMapWrite.streamWriteStartElement must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWriteEndElement(self, element, newLine = True, doIndent = False):

    raise MemopsError("XmlMapWrite.streamWriteEndElement must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWriteAttr(self, key, value, haveUnderscore=False):

    raise MemopsError("XmlMapWrite.streamWriteAttr must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWriteValue(self, value, haveUnderscore=False):

    raise MemopsError("XmlMapWrite.streamWriteValue must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamWriteComment(self, comment):

    raise MemopsError("XmlMapWrite.streamWriteComment must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamNonTextToString(self, value):

    raise MemopsError("XmlMapWrite.streamNonTextToString must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  def streamIndent(self, increasing):

    raise MemopsError("XmlMapWrite.streamIndent must be overridden")

  ###########################################################################

  ###########################################################################
 
  # SaveToStream function
  def streamOrderedCollection(self, var):

    raise MemopsError("XmlMapWrite.streamOrderedCollection must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStream(self, parser):

    apiDirs = [metaConstants.apiCodeDir]
    self.rootClassVarType = self.getImportName(self.rootClass, subDirs=apiDirs)
    self.baseClassVarType = self.getImportName(self.baseClass, subDirs=apiDirs)
    self.baseDataVarType = self.getImportName(self.baseDataType, subDirs=apiDirs)

    params= (('stream', self.fileInterfaceType('r'), 'input stream'),
             ('topObjId', self.stringVarType, 'top object id', self.toLiteral(None)),
             ('topObject', self.baseClassVarType, 'top object', self.toLiteral(None)),
             ('partialLoad', self.booleanVarType, 'partialLoad', self.toLiteral(False)))
    docString = """load Ccpn XML document using %s parser.

topObjId should be the guid (for objects with such an attribute),
otherwise the name (for objects with sucn an attribute), otherwise None.
It is meant to reflect the file name, for proper topObjects.
topObjId must match the guid/name.

topObject can be None, the memopsRoot, or a package TopObject.
If None the file must correspond to the Implementation package.
If memopsRoot the file must be from a non-Implementaiton package, and the
function will use the file to create a new TopObject under MemopsRoot.
If a package TopObject the function will read the data from the file
topObject into the passed-in TopObject, checking that the packages match,
and giving a warning if the topObject (pseudo)key changes.
  
if partialLoad is True only the TopObject (minus children) will be loaded
for normal packages. For the Implementation package Classes actually 
in Implementation will be loaded while shell topObjectas and links to]
them will be skipped.
  
Conceivably the rules could later be relaxed to allow a lower-level empty
object  to be passed in for the purpose of reading subtrees. This would
require some code modifications.
""" % parser

    self.streamStartFunc(funcname='loadFromStream', params=params,
                         docString=docString, returnString='the loaded topObject',
                         returnType=self.baseClassVarType)

    # check for topObject
    self.startIf(self.valueIsNotNone('topObject'))
    self.writeComment('check for topObject')
    ss = self.isInstance('topObject', self.dataRootVarType)
    tt = self.isInstance('topObject', self.topObjectVarType)
    self.startIf(self.negate(self.logicalOp(ss, 'or', tt)))
    self.raiseApiError('XML load: top obj is neither MemopsRoot nor TopObject', 
                       'topObject')
    self.endIf()
    self.endIf()

    self.writeLoadFromStreamStart()
    self.startTry()
    self.writeLoadFromStreamMain()
    self.catchException()
    self.writeLoadFromStreamHandleError()
    self.reraiseException(exceptionClass=self.exceptionClass('ApiError'))
    self.endTry()
    self.writeNewline()
    self.returnStatement('result')
    self.endFunc()
    self.writeLoadFromStreamEnd()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamBody(self):

    # Expected that each of below will be overridden by implementations
    # by adding code at beginning and/or end
    # Problem is that some implementations use callbacks and some iterators
    self.streamStartParse()
    self.streamStartElement()
    self.streamEndElement()
    self.streamEndParse()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamErrorBody(self):

    # clean up in case of error.
    # Currently not done, as too hard to do properly. NBNB TBD
    self.writeComment('clean up in case of error.')
    self.writeComment('Currently not done, as too hard to do properly. NBNB TBD')

    self.startIf(self.valueIsNotNone('result'))
    tt = self.callFunc('getTopObject', 'result', doWrite=False)
    self.streamSetValue(tt, self.toLiteral('isReading'), self.toLiteral(False))
    self.endIf()

    self.printMessage(self.toLiteral('Error loading file for: '), 'result')
    self.printMessage(self.toLiteral('Reading: '), 'stream')
    self.printMessage(self.toLiteral('Last xml tag read: '), 'tag')
    self.printMessage(self.toLiteral('Parser state was: '), 'parserState')

    self.startIf(self.stackIsNotEmpty('objStack'))
    tt = self.peekStack('objStack')
    self.printMessage(self.toLiteral('Current object was: '), tt)
    self.elseIf()
    self.printMessage(self.toLiteral('Object stack was empty'))
    self.endIf()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamExtraFunctions(self):

    self.writeGetLoadingMaps()
    self.writeLinkChildData()
    self.writeDelayedLoadLinks()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamStartParse(self):

    # do not want defines here because that should be done in implementation
    # if required (e.g. in Java these will be private variables so as to be
    # accessible across functions)

    # TBD: not sure these all have type anyVarType
    for ss in ('crossLinkData', 'exoTopLinkData'):
      self.newList(ss, varType=self.anyVarType)

    self.newStack('objStack', varType=self.anyVarType)

    ###self.defineVar('loadMaps', self.dictInterfaceType(self.stringVarType))
    self.setVar('loadMaps', self.toLiteral(None))
    self.setVar('mapping', self.toLiteral(None))
    self.setVar('topObjectMap', self.toLiteral(None))

    self.newDict('objectDict', keyType=self.anyVarType, valueType=self.rootClassVarType)

    ## no longer below since MemopsDataTypeObject now using id(obj)
    ## delayDataDict: ComplexDataType --> (dd: string --> list)
    ##self.writeComment('delayDataDict: ComplexDataType --> (dd: string --> list)')
    # delayDataDict: AnyVarType --> (dd: string --> list)
    self.writeComment('delayDataDict: AnyVarType --> (dd: string --> list)')
    tt = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    ##self.newDict('delayDataDict', keyType=self.rootClassVarType, valueType=tt)
    self.newDict('delayDataDict', keyType=self.anyVarType, valueType=tt)

    ###self.setVar('topObjectKey', self.toLiteral(None), varType=self.anyVarType)
    ###self.setVar('parserState', self.toLiteral('starting'), varType=self.stringVarType)
    ###self.setVar('skipElement', self.toLiteral(None), varType=self.anyVarType)
    self.setVar('topObjectKey', self.toLiteral(None))
    self.setVar('parserState', self.toLiteral('starting'))
    self.setVar('skipElement', self.toLiteral(None))

    self.setVar('topObjByGuid', self.toLiteral(None))
    self.setVar('foundClosingTag', self.toLiteral(False))
    self.setVar('doOutOfPackage', self.toLiteral(False))
    self.setVar('linkTopToParent', self.toLiteral(False))
    self.setVar('needCompatibility', self.toLiteral(False))
    self.setVar('earlyExit', self.toLiteral(False))
    self.setVar('implPrefix', self.toLiteral('IMPL'))
    self.writeNewline()

    ###self.setVar('result', self.toLiteral(None), varType=self.baseClassVarType)
    self.setVar('result', self.toLiteral(None))
    self.writeNewline()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamStartElement(self):

    # element start
    self.writeComment('element start')
    self.writeNewline()

    self.streamElementCheckSkip(doReset=False)

    tt = self.streamElementTag('start')
    self.setVar('tag', tt, varType=self.stringVarType)
    self.writeNewline()

    # IF BLOCK 102
    self.writeComment('IF BLOCK 102')
    self.startIf(self.valueIsNotNone('loadMaps'))
    self.writeComment('file already started')
    self.writeNewline()

    # get map and test
    self.writeComment('get map and test')
    tt = self.dictInterfaceType(self.stringVarType)
    self.defineVar('curMap', tt)
    self.startTry()
    self.setVar('curMap', self.getDictEntry('loadMaps', 'tag', castType=tt, keyIsMandatory=True))
    self.catchException(self.exceptionClass('KeyError'))
    self.raiseApiError('no map found for element', 'tag')
    self.catchException(self.exceptionClass())
    self.raiseApiError('Load maps not set up correctly - should not get here', 'tag')
    self.endTry()
    self.writeNewline()

    # check if we start skipping
    self.writeComment('check if we start skipping')

    tt = self.getDictEntry('curMap', self.toLiteral('proc'))
    self.startIf(self.comparison(self.toLiteral('skip'), '==', tt))
    self.streamElementSetSkip()
    self.streamNextElement()
    self.endIf()

    self.setVar('typ', self.getDictEntry('curMap', self.toLiteral('type')),
                varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 103
    self.writeComment('IF BLOCK 103')
    self.startIf(self.stackIsEmpty('objStack'))

    # inside _StorageUnit - preliminary check for TopObject element
    self.writeComment('inside _StorageUnit - preliminary check for TopObject element')
    ss = self.comparison(self.toLiteral('class'), '==', 'typ')
    tt = self.valueIsNone('topObjectKey')
    self.startIf(self.negate(self.logicalOp(ss, 'and', tt)))
    self.raiseApiError('_StorageUnit has more than one child element')
    self.endIf()

    # IF BLOCK 103
    self.endIf()

    # IF BLOCK 104
    self.writeComment('IF BLOCK 104')
    ss = self.toLiteral('cplx')
    tt = self.getDictEntry('curMap', self.toLiteral('eType'))
    self.startIf(self.comparison(ss, '==', tt))

    # start of class, complex attribute, collection or exolink
    self.writeComment('start of class, complex attribute, collection or exolink')
    self.writeNewline()

    # IF BLOCK 105
    self.writeComment('IF BLOCK 105')
    ss = self.comparison(self.toLiteral('cplx'), '==', 'typ')
    tt = self.comparison(self.toLiteral('class'), '==', 'typ')
    self.startIf(self.logicalOp(ss, 'or', tt))

    # class, or cplx
    self.writeComment('class, or cplx')
    self.writeNewline()

    tt = self.getDictEntry('curMap', self.toLiteral('class'), keyIsMandatory=True)
    self.setVar('clazz', tt, varType=self.anyVarType)
    tt = self.getDictEntry('curMap', self.toLiteral('constructor'), defaultValue='clazz')
    self.setVar('constructor', tt, varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 106
    self.writeComment('IF BLOCK 106')
    self.setVar('obj', self.toLiteral(None), varType=self.rootClassVarType)

    tt = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    self.defineVar('objDelayDict', tt)

    # IF BLOCK 106
    self.startIf(self.comparison(self.toLiteral('class'), '==', 'typ'))
    self.writeNewline()

    tt=self.dictInterfaceType()
    self.defineVar('objDelayDict', tt)

    # IF BLOCK 107
    self.writeComment('IF BLOCK 107')
    self.startIf(self.valueIsNone('topObjectKey'))

    # start of first topObject (passed in)
    self.writeComment('start of first topObject (passed in)')
    self.writeNewline()

    self.startIf(self.stackIsNotEmpty('objStack'))
    self.raiseApiError('Non-empty stack at TopObject - should not get here')
    self.endIf()

    self.defineVar('idTag', varType=self.stringVarType)
    self.defineVar('elemId', varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 108
    self.writeComment('IF BLOCK 108')
    self.startIf(self.valueIsNone('topObject'))

    # reading Implementation.xml
    self.writeComment('reading Implementation.xml')

    ss = self.getDictEntry('mapping', self.toLiteral('.prefix'), keyIsMandatory=True)
    self.startIf(self.comparison(ss, '==', 'implPrefix'))
    self.setVar('topObjectKey', self.toLiteral('ignore'))
    self.streamCallConstructor('obj', 'constructor',
            castType=self.baseClassVarType, isReading=self.toLiteral(True))
    self.elseIf()
    self.raiseApiError('non-Implementation package called without TopObject',
                       'implPrefix')
    self.endIf()
    
    # set to partialLod if this is a new version
    self.startIf('needCompatibility')
    self.setVar('partialLoad', self.toLiteral(True))
    self.endIf()

    # get stored topObjId
    self.writeComment('get stored topObjId')
    self.setVar('idTag', self.toLiteral('name'))
    self.setVar('elemId', self.streamElementAttr('idTag'))
    self.writeNewline()

    # IF BLOCK 108
    self.elseIf(self.isInstance('topObject', self.dataRootVarType))
    self.writeComment('IF BLOCK 108')
    # topObject is MemopsRoot
    # reading new TopObject first time
    self.writeComment('topObject is MemopsRoot')
    self.writeComment('reading new TopObject first time')
    self.writeNewline()

    self.setVar('linkTopToParent', self.toLiteral(True))
    self.writeNewline()

    ss = self.getDictEntry('mapping', self.toLiteral('.prefix'), keyIsMandatory=True)
    self.startIf(self.comparison(ss, '==', 'implPrefix'))
    self.raiseApiError('Attempt to load into pre-existing MemopsRoot')
    self.endIf()
    self.writeNewline()

    # non-impl package - create TopObject afresh
    self.writeComment('non-impl package - create TopObject afresh')
    self.setVar('topObjectKey', self.toLiteral('ignore'))
    self.streamCallConstructor('obj', 'constructor', parent='topObject',
            castType=self.baseClassVarType, isReading=self.toLiteral(True))
    self.setVar('topObjectMap', 'curMap')
    self.writeNewline()

    # get stored topObjId
    self.writeComment('get stored topObjId')
    self.setVar('idTag', self.toLiteral('guid'))
    self.setVar('elemId', self.streamElementAttr('idTag'))
    self.writeNewline()

    # IF BLOCK 108
    self.elseIf()
    self.writeComment('IF BLOCK 108')
    # reading with pre-existing topObject - should fit mapping
    self.writeComment('reading with pre-existing topObject - should fit mapping')
    self.writeNewline()

    tt = self.getClass('topObject')
    self.startIf(self.comparison('clazz', 'is not', tt))
    self.raiseApiError('TopObject class does not fit first element class', tt, 'clazz')
    self.endIf()
    self.writeNewline()

    # check topObject status
    self.writeComment('check topObject status')
    tt = self.streamGetValue('topObject', self.toLiteral('isLoaded'),
                             defaultValue=self.toLiteral(False))
    tt = self.castVar(self.booleanVarType, tt)
    self.startIf(tt)
    self.raiseApiError('trying to load already loaded TopObject', 'topObject')
    self.endIf()

    tt = self.streamGetValue('topObject', self.toLiteral('isModified'),
                             defaultValue=self.toLiteral(False))
    tt = self.castVar(self.booleanVarType, tt)
    self.startIf(tt)
    self.raiseApiError('trying to load already modified TopObject', 'topObject')
    self.endIf()
    self.writeNewline()

    # check guid against topObj identifier
    self.writeComment('check guid against topObj identifier')
    self.setVar('idTag', self.toLiteral('guid'))
    self.setVar('elemId', self.streamElementAttr('idTag'))
    self.writeNewline()

    self.setVar('objId', self.streamGetValue('topObject', 'idTag'), varType=self.anyVarType)
    self.startIf(self.comparison('objId', '!=', 'elemId'))
    self.raiseApiError('TopObject identifier does not fit stored identifier', 'objId', 'elemId')
    self.endIf()
    self.writeNewline()

    # set up for continuing
    self.writeComment('set up for continuing')
    self.setVar('obj', 'topObject')

    # NB only MemopsRoot has fullKey None.
    self.writeComment('NB only MemopsRoot has fullKey None.')
    tt = self.callFunc('getFullKey', 'topObject', doWrite=False)
    self.setVar('topObjectKey', tt)
    self.startIf(self.valueIsNone('topObjectKey'))
    self.setVar('topObjectKey', self.toLiteral('ignore'))
    self.endIf()

    # TBD: isReading is implementation attribute, perhaps should have separate function for these
    self.streamSetValue('obj', self.toLiteral('isReading'), self.toLiteral(True))

    # IF BLOCK 108
    self.endIf()
    self.writeNewline()

    # check that file contents match file name
    self.writeComment('check that file contents match file name')
    self.startIf(self.comparison('elemId', '!=', 'topObjId'))
    self.raiseApiError('TopObject identifier does not fit passed=in identifier',
                       'elemId', 'topObjId')
    self.endIf()
    self.writeNewline()

    # initialise with topObject
    self.writeComment('initialise with topObject')
    self.setVar('result', 'obj', castType=self.baseClassVarType)
    
    # TBD: topObjByGuid is implementation dependent, should perhaps have separate function to get hold of this
    self.startIf(self.isInstance('obj', self.dataRootVarType))
    self.setVar('memopsRoot', 'obj', castType=self.dataRootVarType)
    self.elseIf()
    tt = self.castVar(self.topObjectVarType, 'obj')
    tt = self.callFunc('getMemopsRoot', tt, doWrite=False)
    self.setVar('memopsRoot', tt)
    self.endIf()
    ss = self.streamGetValue('memopsRoot', self.toLiteral('topObjects'))
    tt = self.dictInterfaceType(self.stringVarType, self.baseClassVarType)
    self.setVar('topObjByGuid', ss, castType=tt)
    self.writeNewline()
    
    self.streamSetupCompatibility()

    # IF BLOCK 107
    self.elseIf()
    self.writeComment('IF BLOCK 107')
    # normal case - start of non-TopObject class
    self.writeComment('normal case - start of non-TopObject class')
    self.writeNewline()

    # make new class object
    self.writeComment('make new class object')
    tt = self.listInterfaceType()
    self.popStack('objStack', 'objStackList', varType=tt, castType=tt)
    tt = self.baseClassVarType
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.streamCallConstructor('obj', 'constructor',
            parent='stackObj', castType=self.baseClassVarType)
    self.addList('obj', 'objStackList')
    self.pushStack('objStack', 'objStackList')
    self.writeNewline()

    # IF BLOCK 107
    self.endIf()
    self.writeNewline()

    # set delayDataDict
    self.writeComment('set delayDataDict')
    tt = self.newDict(keyType=self.stringVarType, valueType=self.listInterfaceType())
    self.setVar('objDelayDict', tt)
    tt = self.streamObjDictKey('obj', True)
    self.setDictEntry('delayDataDict', tt, 'objDelayDict')
    self.writeNewline()

    # IF BLOCK 106
    self.elseIf(self.comparison(self.toLiteral('cplx'), '==', 'typ'))
    self.writeComment('IF BLOCK 106')

    # start of complex datatype object
    self.writeComment('start of complex datatype object')
    self.writeNewline()

    # make new dataObjType object
    self.writeComment('make new dataObjType object')
    self.streamCallConstructor('obj', 'constructor',
            castType=self.baseDataVarType, override=self.toLiteral(True))
    tt = self.listInterfaceType()
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.addList('obj', 'stackObj')
    
    tt = self.newDict(keyType=self.stringVarType, valueType=self.listInterfaceType())
    self.setVar('objDelayDict', tt)
    tt = self.streamObjDictKey('obj', False)
    self.setDictEntry('delayDataDict', tt, 'objDelayDict')
    self.writeNewline()

    # IF BLOCK 106
    self.elseIf()
    self.writeComment('IF BLOCK 106')
    self.raiseApiError('Unknown element type', 'typ')

    # IF BLOCK 106
    self.endIf()
    self.writeNewline()

    # put obj on stack
    self.writeComment('put obj on stack')
    self.pushStack('objStack', 'obj')
    self.writeNewline()

    # treat XML attributes
    self.writeComment('treat XML attributes')
    ss = self.getDictEntry('curMap', self.toLiteral('content'), keyIsMandatory=True)
    tt=self.dictInterfaceType(self.stringVarType)
    self.setVar('contMap', ss, varType=tt, castType=tt)

    # LOOP I
    self.writeComment('LOOP I')
    self.streamStartAttributeLoop('tag2', 'value')

    # IF BLOCK 110
    self.writeComment('IF BLOCK 110')
    self.startIf(self.comparison(self.toLiteral('_ID'), '==', 'tag2'))

    self.setDictEntry('objectDict', 'value', 'obj')
    self.setVar('value', self.stringSlice('value', self.toLiteral(1)))

    # IF BLOCK 110
    # self.elseIf()
    self.endIf()

    tt = self.dictInterfaceType(self.stringVarType)
    self.defineVar('tmpMap', tt)
    self.startTry()
    self.setVar('tmpMap', self.getDictEntry('contMap', 'tag2', castType=tt, keyIsMandatory=True))
    self.catchException(self.exceptionClass('KeyError'))
    self.raiseApiError('no map found for XML attribute', 'tag2')
    self.endTry()
    self.writeNewline()

    # IF BLOCK 111
    self.writeComment('IF BLOCK 111')
    tt = self.getDictEntry('tmpMap', self.toLiteral('skip'))
    # TBD: ask Rasmus if valueIsNone is correct
    self.startIf(self.valueIsNone(tt))

    tt = self.getDictEntry('tmpMap', self.toLiteral('type'), keyIsMandatory=True)
    self.setVar('typ', tt)
    self.writeNewline()

    # IF BLOCK 112
    self.writeComment('IF BLOCK 112')
    self.startIf(self.comparison(self.toLiteral('link'), '==', 'typ'))

    self.newList('ll', varType=self.anyVarType, needDeclType=True)
    self.addList('value', 'll')
    self.writeNewline()

    tt = self.getDictEntry('tmpMap', self.toLiteral('proc'))
    self.startIf(self.comparison(self.toLiteral('delay'), '==', tt))
    tt = self.getDictEntry('tmpMap', self.toLiteral('name'),
                           castType=self.stringVarType, keyIsMandatory=True)
    self.setDictEntry('objDelayDict', tt, 'll')

    self.elseIf()
    
    self.addList('obj', 'crossLinkData')
    self.addList('ll', 'crossLinkData')
    self.addList('tmpMap', 'crossLinkData')

    self.endIf()
    self.writeNewline()

    # IF BLOCK 112
    self.elseIf()

    # types attr and text
    self.writeComment('types attr and text')
    tt = self.dictInterfaceType(self.stringVarType)
    ss = self.getDictEntry('tmpMap', self.toLiteral('data'), keyIsMandatory=True)
    self.setVar('dataMap', ss, varType=tt, castType=tt)
    tt = self.getDictEntry('dataMap', self.toLiteral('cnvrt'))
    self.setVar('cnvrt', tt, varType=self.anyVarType)

    tt = self.comparison(self.toLiteral('text'), '!=', 'cnvrt')
    self.startIf(tt)
    self.setVar('value', self.streamConvertStringToValue('cnvrt', 'value'))
    self.endIf()
    self.writeNewline()

    ss = self.getDictEntry('tmpMap', self.toLiteral('name'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('name', ss, varType=tt, castType=tt)

    ss = self.getDictEntry('tmpMap', self.toLiteral('proc'))
    self.setVar('proc', ss, varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 113
    self.writeComment('IF BLOCK 113')
    self.startIf(self.comparison(self.toLiteral('delay'), '==', 'proc'))
    self.newList('ll', varType=self.anyVarType, needDeclType=True)
    self.addList('value', 'll')
    self.setDictEntry('objDelayDict', 'name', 'll')
    self.writeNewline()

    # IF BLOCK 113
    self.elseIf(self.comparison(self.toLiteral('direct'), '==', 'proc'))
    # set, bypassing API
    self.writeComment('set, bypassing API')
    self.streamSetValue('obj', 'name', 'value')
    self.writeNewline()

    # IF BLOCK 113
    ss = self.getDictEntry('tmpMap', self.toLiteral('hicard'))
    self.elseIf(self.comparison(ss, '==', self.toLiteral(1)))
    # always, except when cardinality has changed
    self.writeComment('always, except when cardinality has changed')
    self.streamSetValue('obj', 'name', 'value', useDirectSet=False)
    self.writeNewline()

    # IF BLOCK 113
    self.elseIf()
    # only when hicard has changed from 1 to something else
    self.writeComment('only when hicard has changed from 1 to something else')
    self.newList('ll', varType=self.anyVarType, needDeclType=True)
    self.addList('value', 'll')
    # TBD: below will not work in Java as is because do not know whether
    # Set or List or even what type should be of the collection
    self.streamSetValue('obj', 'name', 'll', useDirectSet=False)

    # IF BLOCK 113
    self.endIf()

    # IF BLOCK 112
    self.endIf()

    # IF BLOCK 111
    self.endIf()

    # IF BLOCK 110
    # self.endIf()

    # LOOP I
    self.endLoop()

    # IF BLOCK 105
    tt = self.comparison(self.toLiteral('child'), '==', 'typ')
    tt = self.logicalOp(tt, 'and', 
                        self.comparison('result', 'is not', 'memopsRoot'))
    self.elseIf(self.logicalOp('partialLoad', 'and', tt))
    self.writeComment('IF BLOCK 105')

    # partially loading TopObject - end now
    self.writeComment('partially loading TopObject - end now')
    self.writeNewline()

    self.popStack('objStack', 'xx', varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 109
    self.writeComment('IF BLOCK 109')
    self.startIf(self.valueIsNotNone('topObjectMap'))

    tt = self.getDictEntry('topObjectMap', self.toLiteral('isTop'))
    self.startIf(self.valueIsNotNone(tt))

    # set TopObjects into TopObjects dictionary.
    self.writeComment('set TopObjects into TopObjects dictionary.')
    tt = self.topObjectVarType
    self.setVar('yy', 'xx', varType=tt, castType=tt)
    tt = self.streamGetValue('yy', self.toLiteral('guid'), keyIsMandatory=True)
    ss = self.stringVarType
    self.setVar('guid', tt, varType=ss, castType=ss)
    tt = self.getDictEntry('topObjByGuid', 'guid')
    self.startIf(self.valueIsNone(tt))
    self.setDictEntry('topObjByGuid', 'guid', 'yy')
    self.endIf()
    
    self.setVar('earlyExit', self.toLiteral(True))
    self.streamHaveEarlyExit()

    self.endIf()

    # IF BLOCK 109
    self.endIf()

    # if we get here there was an error
    self.writeComment('if we get here there was an error')
    self.raiseApiError("partial load with in incorrect context for ", 'xx')
    self.writeNewline()

    # IF BLOCK 105
    self.elseIf()
    self.writeComment('IF BLOCK 105')

    # exolink, collection (of exo, cplx, or attr (e.g. text))
    self.writeComment('exolink, collection (of exo, cplx, or attr (e.g. text))')
    self.newList('ll', varType=self.anyVarType, needDeclType=True)
    self.pushStack('objStack', 'll')

    # IF BLOCK 105
    self.endIf()

    # IF BLOCK 104
    self.endIf()

    # no action for : 'simple'.
    # Nor for 'attr' or  'link' if eType != 'cplx'
    self.writeComment("no action for : 'simple'.")
    self.writeComment("Nor for 'attr' or  'link' if eType != 'cplx'")
    self.writeNewline()

    # IF BLOCK 102
    self.elseIf()
    self.writeComment('IF BLOCK 102')

    # no map - at start of file or error
    self.writeComment('no map - at start of file or error')

    # IF BLOCK 114
    self.writeComment('IF BLOCK 114')
    self.startIf(self.comparison(self.toLiteral('starting'), '==', 'parserState'))

    # IF BLOCK 115
    self.writeComment('IF BLOCK 115')
    self.startIf(self.comparison(self.toLiteral('_StorageUnit'), '==', 'tag'))

    # first element
    self.writeComment('first element')
    self.writeNewline()

    # get version,  package, and updated mapping
    self.writeComment('get version,  package, and updated mapping')

    tt = self.stringVarType
    ss = self.streamElementAttr(self.toLiteral('release'))
    self.setVar('fileVersion', ss, varType=tt, castType=tt)
    ss = self.streamElementAttr(self.toLiteral('packageGuid'))
    self.setVar('packageGuid', ss, varType=tt, castType=tt)

    ss = self.valueIsNone('fileVersion')
    tt = self.valueIsNone('packageGuid')
    self.startIf(self.logicalOp(ss, 'or', tt))
    self.raiseApiError("<_StorageUnit element lacks 'release' or 'packageGuid'")
    self.endIf()
    tt = self.callFunc('getLoadingMaps', doWrite=False,
                  params=('packageGuid', 'fileVersion'))
    self.setVar('lm', tt, varType=self.listInterfaceType())
    ss = self.getByIndexInList(self.toLiteral(0), 'lm')
    tt = self.dictInterfaceType()
    self.setVar('mapping', ss, castType=tt)
    ss = self.getByIndexInList(self.toLiteral(1), 'lm')
    self.setVar('loadMaps', ss, castType=tt)
    ss = self.getByIndexInList(self.toLiteral(2), 'lm')
    self.setVar('needCompatibility', ss, castType=self.booleanVarType)
    self.writeNewline()

    # state tracker - for tests an error messages
    self.writeComment('state tracker - for tests an error messages')
    self.setVar('parserState', self.toLiteral('reading'))
    self.writeNewline()

    # IF BLOCK 115
    self.elseIf()
    self.raiseApiError("no '_StorageUnit' element found, or setup failed")

    # IF BLOCK 115
    self.endIf()

    # IF BLOCK 114
    self.elseIf()
    self.raiseApiError('Read past end of _StorageUnit')

    # IF BLOCK 114
    self.endIf()

    # IF BLOCK 102
    self.endIf()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamEndElement(self):

    # event == 'end', element end
    self.writeComment("event == 'end', element end")
    self.writeNewline()

    self.streamElementCheckSkip()

    tt = self.stringVarType
    self.setVar('tag', self.streamElementTag('end'), varType=tt, castType=tt)

    self.startIf(self.comparison(self.toLiteral('_StorageUnit'), '==', 'tag'))
    self.setVar('foundClosingTag', self.toLiteral(True))
    self.streamFoundClosingTag()
    self.endIf()
    self.writeNewline()

    tt = self.dictInterfaceType(self.stringVarType)
    self.defineVar('curMap', tt)
    self.startTry()
    self.setVar('curMap', self.getDictEntry('loadMaps', 'tag', castType=tt, keyIsMandatory=True))
    self.catchException(self.exceptionClass('KeyError'))
    self.raiseApiError('no map found for element', 'tag')
    self.catchException(self.exceptionClass())
    self.raiseApiError('Load maps not set up correctly - should not get here', 'tag')
    self.endTry()
    self.writeNewline()

    # IF BLOCK 202
    self.writeComment('IF BLOCK 202')
    self.startIf(self.stackIsNotEmpty('objStack'))

    # we are not yet finished
    self.writeComment('we are not yet finished')
    self.writeNewline()

    self.setVar('typ', self.getDictEntry('curMap', self.toLiteral('type')),
                varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 203
    self.writeComment('IF BLOCK 203')
    self.startIf(self.comparison(self.toLiteral('simple'), '==', 'typ'))

    # DataType value
    self.writeComment('DataType value')
    self.setVar('value', self.streamElementText(), varType=self.anyVarType)

    tt = self.getDictEntry('curMap', self.toLiteral('cnvrt'))
    self.setVar('cnvrt', tt, varType=self.anyVarType)

    tt = self.comparison(self.toLiteral('text'), '!=', 'cnvrt')
    self.startIf(tt)
    self.setVar('value', self.streamConvertStringToValue('cnvrt', 'value'))
    self.endIf()

    tt = self.listInterfaceType()
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.addList('value', 'stackObj')
    self.writeNewline()

    # IF BLOCK 203
    self.elseIf(self.comparison(self.toLiteral('child'), '==', 'typ'))

    # child link
    self.writeComment('child link')

    ss = self.listInterfaceType()
    self.popStack('objStack', 'll', varType=ss, castType=ss)

    ss = self.rootClassVarType
    self.peekStack('objStack', 'oo', varType=ss, castType=ss)

    ss = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    tt = self.getDictEntry('delayDataDict', 'oo', keyIsMandatory=True)
    self.setVar('dd', tt, varType=ss, castType=ss)

    ss = self.stringVarType
    tt = self.getDictEntry('curMap', self.toLiteral('name'), keyIsMandatory=True)
    self.setVar('nm', tt, varType=ss, castType=ss)

    self.setDictEntry('dd', 'nm', 'll')
    self.writeNewline()

    tt = self.getDictEntry('curMap', self.toLiteral('proc'))
    self.startIf(self.comparison(self.toLiteral('loadDelayed'), '==', tt))

    # Special case:
    # premature link dereferencing.
    # necessary to handle Impl package properly
    self.writeComment('Special case:')
    self.writeComment('premature link dereferencing.')
    self.writeComment('necessary to handle Impl package properly')
    
    self.callFunc('delayedLoadLinksStd', params=('objectDict', 'crossLinkData'))
    
    #self.callFunc('delayedLoadLinks', params=('topObjByGuid', 'exoTopLinkData'))
    self.startIf(self.collectionIsNotEmpty('exoTopLinkData', isUnique=False, isOrdered=True))
    self.raiseApiError('ExoTopLinks should not exist at intermediate MemopsRoot link-up')
    self.endIf()
    self.callFunc('linkChildData', params=('delayDataDict', 'result', 'mapping', 'linkTopToParent', 'doOutOfPackage'))
    self.setVar('doOutOfPackage', self.toLiteral(True))
    
    self.writeComment('Reading MemopsRoot')
    self.writeComment('and skipping everything to do with other packages')
    self.startIf('partialLoad')
    self.setVar('earlyExit', self.toLiteral(True))
    self.streamHaveEarlyExit()
    self.endIf()

    self.endIf()
    self.writeNewline()

    # IF BLOCK 203
    self.elseIf(self.comparison(self.toLiteral('class'), '==', 'typ'))

    # class
    self.writeComment('class')

    tt = self.baseClassVarType
    self.popStack('objStack', 'xx', varType=tt, castType=tt)
    self.writeNewline()
    
    # IF BLOCK 204
    self.writeComment('IF BLOCK 204')
    tt = self.getDictEntry('curMap', self.toLiteral('isTop'),
                           defaultValue=self.toLiteral(False))
    tt = self.castVar(self.booleanVarType, tt)
    self.startIf(tt)

    # set TopObjects into TopObjects dictionary.
    self.writeComment('set TopObjects into TopObjects dictionary.')
    tt = self.castVar(self.topObjectVarType, 'xx')
    tt = self.streamGetValue(tt, self.toLiteral('guid'), keyIsMandatory=True)
    self.setVar('guid', tt, varType=self.stringVarType, castType=self.stringVarType)
    tt = self.getDictEntry('topObjByGuid', 'guid')
    self.setVar('yy', tt, varType=self.baseClassVarType)

    self.startIf(self.valueIsNone('yy'))
    self.setDictEntry('topObjByGuid', 'guid', 'xx')
    self.elseIf(self.comparison('yy', 'is not', 'xx'))
    self.raiseApiError('Read topObj with guid conflicts with existing topObj', 'guid')
    self.endIf()

    # IF BLOCK 204
    self.elseIf(self.negate('needCompatibility'))
    # Rasmus 29/1/09 - remove useless empty dicts NBNB
    # NB delayDataDict is also used for backwards compatibility.
    # It should be possible to get the improvement also when upgrading,
    # but that would require debugging the compatibility scripts.
    # NBNB TODO  At the next major version upgrade this should be changed to plain self.elseIf()
    tt = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    ss =  self.getDictEntry('delayDataDict', self.streamObjDictKey('xx', True),
                            keyIsMandatory=True)
    self.setVar('dd', ss, varType=tt, castType=tt)
    self.startIf(self.dictIsEmpty('dd'))
    self.removeDictEntry('delayDataDict', self.streamObjDictKey('xx', True))
    self.endIf()
    
    # IF BLOCK 204
    self.endIf()

    # IF BLOCK 203
    self.elseIf(self.comparison(self.toLiteral('exo'), '==', 'typ'))

    # exolink
    self.writeComment('exolink')

    tt = self.listInterfaceType()
    self.popStack('objStack', 'xx', varType=tt, castType=tt)
    self.writeNewline()

    tt = self.lenList('xx')
    self.setVar('lenxx', tt, varType=self.intVarType)

    # IF BLOCK 205
    self.writeComment('IF BLOCK 205')
    self.startIf(self.comparison('lenxx', '>', self.toLiteral(1)))

    # normal exoLink. Append curMap for later dereferencing
    self.writeComment('normal exoLink. Append curMap for later dereferencing')
    self.addList('curMap', 'xx')

    tt = self.listInterfaceType()
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.addList('xx', 'stackObj')
    self.writeNewline()

    # IF BLOCK 205
    self.elseIf(self.comparison('lenxx', '==', self.toLiteral(1)))

    # link to TopObject. Must be handled differently, because
    # of toTopObject links that may be present in Implementation
    self.writeComment('link to TopObject. Must be handled differently, because')
    self.writeComment('of toTopObject links that may be present in Implementation')

    tt = self.listInterfaceType()
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.defineVar('yy', self.anyVarType)
    self.getList('yy', 'xx')
    self.addList('yy', 'stackObj')
    self.writeNewline()

    # IF BLOCK 205
    self.elseIf()
    self.raiseApiError('XML element appears empty')

    # IF BLOCK 205
    self.endIf()

    # IF BLOCK 203
    self.elseIf(self.comparison(self.toLiteral('cplx'), '==', 'typ'))

    # complex datatype
    self.writeComment('complex datatype')

    tt = self.baseDataVarType
    self.popStack('objStack', 'xx', varType=tt, castType=tt)
    self.streamOverrideOff('xx')
    self.writeNewline()
    
    # Rasmus 29/1/09 - remove useless empty dicts NBNB
    tt = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    ss =  self.getDictEntry('delayDataDict', self.streamObjDictKey('xx', False),
                            keyIsMandatory=True)
    self.setVar('dd', ss, varType=tt, castType=tt)
    self.startIf(self.dictIsEmpty('dd'))
    self.removeDictEntry('delayDataDict', self.streamObjDictKey('xx', False))
    self.endIf()

    # IF BLOCK 203
    self.elseIf()

    # class elements - typ is 'link', 'attr', 'exolink', 'exotop', 'dobj'
    self.writeComment("class elements - typ is 'link', 'attr', 'exolink', 'exotop', 'dobj'")
    self.writeNewline()

    # get value
    self.writeComment('get value')
    self.defineVar('val', self.listInterfaceType())

    # IF BLOCK 206
    self.writeComment('IF BLOCK 206')
    tt = self.getDictEntry('curMap', self.toLiteral('eType'))
    self.startIf(self.comparison(self.toLiteral('cplx'), '==', tt))

    self.popStack('objStack', 'val', castType=self.listInterfaceType())
    # TBD is valueIsNone correct?
    self.startIf(self.collectionIsEmpty('val', False, True))
    # NBNB with elements being skipped
    # this might legitimately happen during backwards compatibility
    self.writeComment('NBNB with elements being skipped')
    self.writeComment('this might legitimately happen during backwards compatibility')
    self.streamNextElement()
    self.endIf()
    self.writeNewline()

    # IF BLOCK 206
    self.elseIf(self.comparison(self.toLiteral('attr'), '==', 'typ'))
    ss = self.getDictEntry('curMap', self.toLiteral('data'), keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType)
    self.setVar('dataMap', ss, varType=tt, castType=tt)
    ss = self.getDictEntry('dataMap', self.toLiteral('cnvrt'), keyIsMandatory=True)
    self.setVar('cnvrt', ss, varType=self.anyVarType)
    self.streamElementSplitText('val', 'cnvrt')

    # check if non-empty
    self.writeComment('check if non-empty')

    tt = self.collectionIsEmpty('val', isUnique=False, isOrdered=True)
    self.startIf(tt)
    self.raiseApiError('XML element appears empty')
    self.endIf()
    self.writeNewline()

    self.writeNewline()

    # IF BLOCK 206
    self.elseIf()
    self.streamElementSplitText('val')

    # check if non-empty
    self.writeComment('check if non-empty')

    tt = self.collectionIsEmpty('val', isUnique=False, isOrdered=True)
    self.startIf(tt)
    self.raiseApiError('XML element appears empty')
    self.endIf()
    self.writeNewline()

    # IF BLOCK 206
    self.endIf()
    self.writeNewline()

    # set up
    self.writeComment('set up')

    tt = self.getDictEntry('curMap', self.toLiteral('proc'))
    self.setVar('proc', tt, varType=self.anyVarType)
    self.writeNewline()

    # IF BLOCK 207
    self.writeComment('IF BLOCK 207')
    self.startIf(self.comparison(self.toLiteral('delay'), '==', 'proc'))

    # defunct element, preserved for backwards compatibility
    self.writeComment('defunct element, preserved for backwards compatibility')

    tt = self.baseClassVarType
    self.peekStack('objStack', 'containerObj', varType=tt, castType=tt)
    self.defineVar('dictid', self.anyVarType)
    self.startIf(self.isInstance('containerObj', self.baseClassVarType))
    tt = self.streamObjDictKey('containerObj', True)
    self.setVar('dictid', tt)
    self.elseIf()
    tt = self.streamObjDictKey('containerObj', False)
    self.setVar('dictid', tt)
    self.endIf()
    ss = self.getDictEntry('delayDataDict', 'dictid', keyIsMandatory=True)
    tt = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    self.setVar('dd', ss, varType=tt, castType=tt)
    tt = self.getDictEntry('curMap', self.toLiteral('name'),
                           castType=self.stringVarType, keyIsMandatory=True)
    self.setDictEntry('dd', tt, 'val')
    self.writeNewline()

    # IF BLOCK 207
    self.elseIf(self.comparison(self.toLiteral('link'), '==', 'typ'))

    # crosslink - delayed setting
    self.writeComment('crosslink - delayed setting')

    tt = self.anyVarType
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.addList('stackObj', 'crossLinkData')
    self.addList('val', 'crossLinkData')
    self.addList('curMap', 'crossLinkData')
    self.writeNewline()

    # IF BLOCK 207
    self.elseIf(self.comparison(self.toLiteral('exotop'), '==', 'typ'))

    # exolink to topObject. delayed setting
    self.writeComment('exolink to topObject. delayed setting')

    tt = self.anyVarType
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)
    self.addList('stackObj', 'exoTopLinkData')
    self.addList('val', 'exoTopLinkData')
    self.addList('curMap', 'exoTopLinkData')
    self.writeNewline()

    # IF BLOCK 207
    self.elseIf()

    # attribute for setting now
    self.writeComment('attribute for setting now')

    self.startIf(self.comparison(self.toLiteral('exolink'), '==', 'typ'))
    # exolink not to topObject - convert to objects now.
    # val is topObjGuid, followed by rest of key,
    # followed by the exo link I/O map.
    self.writeComment('exolink not to topObject - convert to objects now.')
    self.writeComment('val is topObjGuid, followed by rest of key,')
    self.writeComment('followed by the exo link I/O map.')
    self.streamConvertExolink()
    self.endIf()

    # set up
    self.writeComment('set up')

    ss = self.getDictEntry('curMap', self.toLiteral('name'), keyIsMandatory=True)
    tt = self.stringVarType
    self.setVar('name', ss, varType=tt, castType=tt)

    ss = self.getDictEntry('curMap', self.toLiteral('hicard'), keyIsMandatory=True)
    tt = self.intVarType
    self.setVar('hicard', ss, varType=tt, castType=tt)
    self.writeNewline()

    # set value
    self.writeComment('set value')

    tt = self.rootClassVarType
    self.peekStack('objStack', 'stackObj', varType=tt, castType=tt)

    # IF BLOCK 208
    self.writeComment('IF BLOCK 208')
    self.startIf(self.comparison('hicard', '==', self.toLiteral(1)))

    self.defineVar('vv', self.anyVarType)
    tt = self.castVar(self.listInterfaceType(), 'val')
    self.getList('vv', tt)

    self.startIf(self.comparison(self.toLiteral('direct'), '==', 'proc'))
    # set, bypassing API - hicard must be 1.
    self.writeComment('set, bypassing API - hicard must be 1.')
    self.streamSetValue('stackObj', 'name', 'vv')
    self.elseIf()
    # std set, hicard == 1
    self.writeComment('std set, hicard == 1')
    self.streamSetValue('stackObj', 'name', 'vv', useDirectSet=False)
    self.endIf()
    self.writeNewline()

    # IF BLOCK 208
    self.elseIf(self.comparison('hicard', '<', self.toLiteral(1)))

    # std set, hicard == infinity
    self.writeComment('std set, hicard == infinity')

    self.streamSetValue('stackObj', 'name', 'val', useDirectSet=False)
    self.writeNewline()

    # IF BLOCK 208
    self.elseIf()

    # std set, hicard > 1
    tt = self.castVar(self.listInterfaceType(), 'val')
    tt = self.getListSlice(tt, hi='hicard')
    self.streamSetValue('stackObj', 'name', tt, useDirectSet=False)

    # IF BLOCK 208
    self.endIf()

    # IF BLOCK 207
    self.endIf()

    # IF BLOCK 203
    self.endIf()
    self.writeNewline()

    # IF BLOCK 202
    # TBD: should this be _StorageUnit
    self.elseIf(self.comparison(self.toLiteral('_StorageUnit'), '!=', 'tag'))
    self.writeComment('IF BLOCK 202')
    self.raiseApiError('objStack empty but element is not _StorageUnit')

    # IF BLOCK 202
    self.endIf()
    self.writeNewline()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamEndParse(self):

    self.startIf(self.negate('earlyExit'))
    self.startIf(self.negate('foundClosingTag'))
    self.raiseApiError('Premature end of file - no </_StorageUnit> found')
    self.endIf()

    ss = self.stackIsNotEmpty('objStack')
    tt = self.valueIsNotNone('skipElement')
    self.startIf(self.logicalOp(ss, 'or', tt))
    ss = self.stackSize('objStack')
    self.raiseApiError('Illegal state after parsing: objStack length, skipElement', ss, 'skipElement')
    self.endIf()
    self.endIf()
    self.writeNewline()

    # delayed load
    self.writeComment('delayed load')
    self.setVar('parserState', self.toLiteral('postprocessing data'))
    self.startIf(self.logicalOp(self.comparison('result', 'is', 'memopsRoot'),
                                'or', self.negate('partialLoad')))
    self.callFunc('delayedLoadLinksStd', params=('objectDict', 'crossLinkData'))
    self.endIf()
    self.callFunc('delayedLoadLinksExo', params=('topObjByGuid', 'exoTopLinkData'))
    self.writeNewline()

    self.startIf('needCompatibility')
    # backwards compatibility
    self.writeComment('backwards compatibility')
    self.setVar('parserState', self.toLiteral('handling version compatibility'))
    self.streamDoCompatibility()
    self.endIf()
    self.writeNewline()

    # link children to parents
    self.writeComment('link children to parents')
    self.callFunc('linkChildData', params=('delayDataDict', 'result', 'mapping', 'linkTopToParent', 'doOutOfPackage'))
    self.writeNewline()

    # validity check
    self.writeComment('validity check')
    self.setVar('parserState', self.toLiteral('checking validity'))
    self.writeNewline()
 
    # unset isReading (NB - extra link is for future load of non-topObjects)
    self.writeComment('unset isReading (NB - extra link is for future load of non-topObjects)')
    tt = self.callFunc('getTopObject', obj='result', doWrite=False)
    self.setVar('resultTop', tt, varType=self.baseClassVarType)
    self.streamSetValue('resultTop', self.toLiteral('isReading'), self.toLiteral(False))
    self.startIf(self.logicalOp(self.negate('partialLoad'), 'or', 
                  self.comparison('result', 'is', 'memopsRoot')))
    self.streamSetValue('resultTop', self.toLiteral('isLoaded'), self.toLiteral(True))
    
    # NBNB new addition set to modified if upgraded and modifieable
    tt = self.streamGetValue('resultTop', self.toLiteral('isModifiable'),
                             defaultValue=self.toLiteral(False))
    tt = self.castVar(self.booleanVarType, tt)
    self.startIf(self.logicalOp('needCompatibility', 'and', tt))
    self.streamSetValue('resultTop', self.toLiteral('isModified'), self.toLiteral(True))
    self.endIf()
    
    self.endIf()
    self.writeNewline()

    ss = self.valueIsNotNone('topObjectKey')
    tt = self.comparison('topObjectKey', '!=', self.toLiteral('ignore'))
    self.startIf(self.logicalOp(ss, 'and', tt))
    tt = self.callFunc('getFullKey', 'result', doWrite=False)
    self.setVar('xx', tt, varType=self.anyVarType)
    self.startIf(self.comparison('topObjectKey', '!=', 'xx'))
    self.printMessage(self.toLiteral('WARNING TopObject key changed on reading'),
                      'topObjectKey', 'xx')
    self.endIf()
    self.endIf()
    self.writeNewline()

    tt = self.getDictValues('objectDict')
    self.startLoop('obj', tt, isUnique=False, isOrdered=False,
                   varType=self.rootClassVarType)
    self.callFunc('checkValid', 'obj')
    self.endLoop()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  # internal function
  def streamElementCheckSkip(self, doReset = True):

    self.startIf(self.valueIsNotNone('skipElement'))
    # we are skipping an element
    self.writeComment('we are skipping an element')
    if doReset:
      self.startIf(self.streamElementIsSkip())
      self.streamElementSetSkip(setToNone=True)
      self.endIf()
    self.streamNextElement()
    self.endIf()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeGetLoadingMaps(self):

    params= (('packageGuid', self.stringVarType, 'package guid'),
             ('fileVersion', self.stringVarType, 'file version'))
    docString = """returns (mapping, loadMaps, needCompatibility) tuple.
Allows for backwards compatibility
"""

    self.streamStartFunc(funcname='getLoadingMaps', params=params,
                         docString=docString, returnString='the loading maps',
                         returnType=self.listInterfaceType())
    self.writeGetLoadingMapsBody()
    self.writeNewline()
    self.returnStatement('ll')
    self.endFunc()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeGetLoadingMapsBody(self):

    self.streamInitLoadingMaps()

    # select mapping for package
    self.writeComment('select mapping for package')

    self.setVar('mapping', self.toLiteral(None), varType=self.dictInterfaceType())

    values = self.getDictValues('globalMapping')
    tt = self.dictInterfaceType()
    self.startLoop('dd', values, isUnique=False, isOrdered=False, varType=tt)

    tt = self.getDictEntry('dd', self.toLiteral('guid'))
    self.startIf(self.comparison('packageGuid', '==', tt))
    self.setVar('mapping', 'dd')
    self.breakLoop()
    self.endIf()

    self.endLoop()

    self.startIf(self.valueIsNone('mapping'))
    self.raiseApiError('No package mapping with guid found', 'packageGuid')
    self.endIf()

    self.newList('ll', varType=self.anyVarType, needDeclType=True)
    self.addList('mapping', 'll')

    tt = self.getDictEntry('globalMapping', self.toLiteral('loadMaps'), keyIsMandatory=True)
    self.addList(tt, 'll')

    self.addList('needCompatibility', 'll')

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLinkChildData(self):

    tt = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    ## no longer below since using id(obj) for MemopsDataTypeObject
    ##tt = self.dictInterfaceType(self.rootClassVarType, tt)
    tt = self.dictInterfaceType(self.anyVarType, tt)
    params= (('delayDataDict', tt, 'delay data dict'),
             ('topObj', self.baseClassVarType, 'top object'),
             ('mapping', self.dictVarType, 'package mapping'),
             ('linkTopToParent', self.booleanVarType, 'link top to parent', self.toLiteral(False)),
             ('doOutOfPackage', self.booleanVarType, 'do out of package', self.toLiteral(False)))
    docString = """set parent-child links.
delayDataDict is an obj/id:{childRoleName:listOfChildren}} dictionary
(it also contains other information used elsewhere for compatibility)
topObj is the TopObject
mapping is the package mapping
linkTopToParent determines if the root-to-topObject link must be set
doOutOfPackage determines if out-of-package children must be linked -
This is only relevant for the Implementation package, where first
intrapackge and later out-of-package children are set.
"""

    self.streamStartFunc(funcname='linkChildData', params=params,
                         docString=docString)
    self.writeLinkChildDataBody()
    self.endFunc()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLinkChildDataBody(self):

    # set up
    self.writeComment('set up')

    ss = self.dictVarType
    tt = self.getDictEntry('mapping', self.toLiteral('abstractTypes'), keyIsMandatory=True)
    self.setVar('dataTypeMap', tt, varType=ss, castType=ss)

    tt = self.getClassname('topObj')
    tt = self.getDictEntry('dataTypeMap', tt, keyIsMandatory=True)
    self.setVar('topObjMap', tt, varType=ss, castType=ss)
    self.writeNewline()

    # prime the stacks
    self.writeComment('prime the stacks')

    tt = self.stackInterfaceType(self.baseClassVarType)
    self.defineVar('parentStack', tt)
    tt = self.stackInterfaceType(self.listInterfaceType(self.baseClassVarType))
    self.defineVar('childStack', tt)

    # IF BLOCK 301
    self.writeComment('IF BLOCK 301')
    self.startIf('linkTopToParent')

    tt = self.callFunc('getParent', 'topObj', doWrite=False)
    initValues=[tt]
    self.newStack('parentStack', varType=self.baseClassVarType, 
                  initValues=initValues)

    self.newList('ll', varType=self.baseClassVarType, needDeclType=True)
    self.addList('topObj', 'll')
    initValues=['ll']
    self.newStack('childStack', 
                  varType=self.listInterfaceType(self.baseClassVarType), 
                  initValues=initValues)
    self.writeNewline()

    # IF BLOCK 301
    self.elseIf()

    initValues=['topObj']
    self.newStack('parentStack', varType=self.baseClassVarType, 
                  initValues=initValues)

    self.newList('ll', varType=self.baseClassVarType, needDeclType=True)
    initValues=['ll']
    tt = self.listInterfaceType(self.baseClassVarType)
    self.newStack('childStack', tt, initValues=initValues)

    ss = self.listInterfaceType(self.stringVarType)
    tt = self.getDictEntry('topObjMap', self.toLiteral('children'), 
                           keyIsMandatory=True)
    self.setVar('cl', tt, varType=ss, castType=ss)
    ss = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    tt = self.getDictEntry('delayDataDict', 'topObj', keyIsMandatory=True)
    self.setVar('dt', tt, varType=ss, castType=ss)
    self.startLoop('tag', 'cl', isUnique=True, isOrdered=False,
                   varType=self.stringVarType)
    tt = self.getDictEntry('dt', 'tag')
    ss = self.listInterfaceType()
    self.setVar('xx', tt, varType=ss)
    self.startIf(self.valueIsNotNone('xx'))
    self.streamAddAll('xx', 'll')
    self.endIf()

    self.endLoop()
    
    # IF BLOCK 301
    self.endIf()
    self.writeNewline()

    # IF BLOCK 302
    self.writeComment('IF BLOCK 302')
    self.startIf('doOutOfPackage')

    # special case for TopObjects in Implementation
    self.writeComment('special case for TopObjects in Implementation')
    self.writeNewline()

    # IF BLOCK 303
    self.writeComment('IF BLOCK 303')
    self.startIf(self.isInstance('topObj', self.dataRootVarType))
    self.writeNewline()
    
    tt = self.getDictEntry('delayDataDict', 'topObj', keyIsMandatory=True)
    ss = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    self.setVar('dd', tt, varType=ss, castType=ss)

    tt = self.getDictEntry('topObjMap', self.toLiteral('content'), keyIsMandatory=True)
    ss = self.dictVarType
    self.setVar('content', tt, varType=ss, castType=ss)

    ss = self.listInterfaceType(self.stringVarType)
    tt = self.getDictEntry('topObjMap', self.toLiteral('children'), keyIsMandatory=True)
    self.setVar('cl', tt, varType=ss, castType=ss)
    self.startLoop('tag', 'cl', isUnique=True, isOrdered=False, varType=self.stringVarType)

    tt = self.getDictEntry('dd', 'tag')
    ss = self.listInterfaceType()
    self.setVar('val', tt, varType=ss)

    # IF BLOCK 304
    self.writeComment('IF BLOCK 304')
    self.startIf(self.valueIsNotNone('val'))
    self.writeNewline()

    tt = self.getDictEntry('content', 'tag', keyIsMandatory=True)
    ss = self.dictVarType
    self.setVar('linkMap', tt, varType=ss, castType=ss)

    # IF BLOCK 305
    self.writeComment('IF BLOCK 305')
    ss = self.toLiteral('child')
    tt = self.getDictEntry('linkMap', self.toLiteral('type'), keyIsMandatory=True)
    self.startIf(self.comparison(ss, '==', tt))

    # child link
    self.writeComment('child link')
    self.writeNewline()

    tt = self.getDictEntry('linkMap', self.toLiteral('content'), keyIsMandatory=True)
    ss = self.dictVarType
    self.setVar('linkContent', tt, varType=ss, castType=ss)

    self.startLoop('obj', 'val', isUnique=False, isOrdered=True)

    tt = self.baseClassVarType
    self.setVar('obj2', 'obj', varType=tt, castType=tt)

    tt = self.getClassname('obj2')
    tt = self.getDictEntry('linkContent', tt, keyIsMandatory=True)
    ss = self.dictVarType
    self.setVar('curMap', tt, varType=ss, castType=ss)

    # IF BLOCK 306
    self.writeComment('IF BLOCK 306')
    tt = self.getDictEntry('curMap', self.toLiteral('isTop'))
    self.startIf(self.valueIsNotNone(tt))

    # TopObject. Do the link to parent
    self.writeComment('TopObject. Do the link to parent')
    self.writeNewline()

    # get key
    self.writeComment('get key')

    tt = self.getDictEntry('curMap', self.toLiteral('objkey'))
    ss = self.stringVarType
    self.setVar('tag2', tt, varType=ss, castType=ss)

    self.defineVar('key', varType=self.anyVarType)
    self.startIf(self.valueIsNone('tag2'))
    tt = self.callFunc('getLocalKey', 'obj2', doWrite=False)
    self.setVar('key', tt)
    self.elseIf()
    tt = self.streamGetValue('obj2', 'tag2', keyIsMandatory=True)
    self.setVar('key', tt)
    self.endIf()

    tt = self.getDictEntry('curMap', self.toLiteral('fromParent'),
                           castType=self.stringVarType, keyIsMandatory=True)
    tt = self.streamGetValue('topObj', tt, keyIsMandatory=True, getChildAsDict=True)
    ss = self.dictInterfaceType()
    self.setVar('parDict', tt, varType=ss, castType=ss)
    self.writeNewline()

    # add child link to parent dict
    self.writeComment('add child link to parent dict')
    self.startIf(self.keyIsInDict('parDict', 'key'))
    # TBD: took off qualifiedName because only have two slots
    ss = self.callFunc('getQualifiedName', 'obj2', doWrite=False)
    tt = self.callFunc('getParent', 'obj2', doWrite=False)
    self.raiseApiError('Cannot add child - key already in use', ss, tt, 'key')

    self.elseIf()
    self.setDictEntry('parDict', 'key', 'obj2')
    # NB these are shell TopObjects read in Implementation package
    self.writeComment('NB these are shell TopObjects read in Implementation package')
    self.streamSetValue('obj2', self.toLiteral('isReading'), self.toLiteral(False))
    self.endIf()

    # IF BLOCK 306
    self.endIf()

    self.endLoop()

    # IF BLOCK 305
    self.endIf()

    # IF BLOCK 304
    self.endIf()

    self.writeNewline()
    
    self.endLoop()
    self.writeNewline()

    # IF BLOCK 303
    self.elseIf()
    self.raiseApiError('linkChildData: called with doOutOfPackage for non-root', 'topObj')

    # IF BLOCK 303
    self.endIf()
    self.writeNewline()

    # IF BLOCK 302
    self.elseIf()

    # Normal case. Add children to parent dictionary
    self.writeComment('Normal case. Add children to parent dictionary')
    self.writeNewline()

    self.startWhile(self.stackIsNotEmpty('childStack'))
    self.writeNewline()

    tt = self.listInterfaceType(self.baseClassVarType)
    self.peekStack('childStack', 'kids', varType=tt)

    # IF BLOCK 307
    self.writeComment('IF BLOCK 307')
    self.startIf(self.listIsNotEmpty('kids'))

    self.popList('obj', 'kids', varType=self.baseClassVarType)
    tt = self.getClassname('obj')
    tt = self.getDictEntry('dataTypeMap', tt, keyIsMandatory=True)
    ss = self.dictVarType
    self.setVar('curMap', tt, varType=ss, castType=ss)

    self.peekStack('parentStack', 'parentObj', varType=self.baseClassVarType)
    tt = self.getDictEntry('curMap', self.toLiteral('fromParent'), keyIsMandatory=True)
    self.setVar('fromParent', tt, varType=self.stringVarType, castType=self.stringVarType)

    # IF BLOCK 308
    self.writeComment('IF BLOCK 308')
    tt = self.getDictEntry('curMap', self.toLiteral('singleKid'))
    self.startIf(self.valueIsNotNone(tt))

    # only child
    self.writeComment('only child')

    tt = self.streamGetValue('parentObj', 'fromParent')
    ss = self.dictInterfaceType()
    self.setVar('sibling', tt, varType=ss, castType=ss)
    self.writeNewline()

    self.startIf(self.valueIsNone('sibling'))
    self.streamSetValue('parentObj', 'fromParent', 'obj')
    self.elseIf()
    self.raiseApiError('Attempt to override single child', 'sibling')
    self.endIf()

    # IF BLOCK 308
    self.elseIf()

    tt = self.streamGetValue('parentObj', 'fromParent', keyIsMandatory=True, getChildAsDict=True)
    ss = self.dictInterfaceType()
    self.setVar('parDict', tt, varType=ss, castType=ss)
    self.writeNewline()

    # get key
    self.writeComment('get key')

    tt = self.getDictEntry('curMap', self.toLiteral('objkey'))
    ss = self.stringVarType
    self.setVar('tag', tt, varType=ss, castType=ss)

    self.defineVar('key', varType=self.anyVarType)
    self.startIf(self.valueIsNone('tag'))
    tt = self.callFunc('getLocalKey', 'obj', doWrite=False)
    self.setVar('key', tt)
    self.elseIf()
    tt = self.streamGetValue('obj', 'tag', keyIsMandatory=True)
    self.setVar('key', tt)
    self.endIf()

    # add child link to parent dict
    self.writeComment('add child link to parent dict')
    self.startIf(self.keyIsInDict('parDict', 'key'))
    # TBD: took off qualifiedName because only have two slots
    ss = self.callFunc('getQualifiedName', 'obj', doWrite=False)
    tt = self.callFunc('getParent', 'obj', doWrite=False)
    self.raiseApiError('Cannot add child - key already in use', ss, tt, 'key')

    self.elseIf()
    self.setDictEntry('parDict', 'key', 'obj')
    self.endIf()
    self.writeNewline()

    # IF BLOCK 308
    self.endIf()

    # put children on stack
    self.pushStack('parentStack', 'obj')
    self.newList('ll', varType=self.baseClassVarType, needDeclType=True)
    self.pushStack('childStack', 'll')

    ss = self.dictInterfaceType(self.stringVarType, self.listInterfaceType())
    tt = self.getDictEntry('delayDataDict', 'obj')
    self.setVar('dd', tt, varType=ss)

    # IF BLOCK 309
    self.writeComment('IF BLOCK 309')
    self.startIf(self.valueIsNotNone('dd'))

    ss = self.listInterfaceType(self.stringVarType)
    tt = self.getDictEntry('curMap', self.toLiteral('children'))
    self.setVar('mm', tt, varType=ss, castType=ss)

    # IF BLOCK 310
    self.writeComment('IF BLOCK 310')
    self.startIf(self.valueIsNotNone('mm'))
    self.startLoop('tag2', 'mm', isUnique=False, isOrdered=True, varType=self.stringVarType)

    ss = self.listInterfaceType()
    tt = self.getDictEntry('dd', 'tag2')
    self.setVar('xx', tt, varType=ss)
    self.startIf(self.valueIsNotNone('xx'))
    self.streamAddAll('xx', 'll')
    self.endIf()

    self.endLoop()
    # IF BLOCK 310
    self.endIf()

    # IF BLOCK 309
    self.endIf()
    self.writeNewline()

    # IF BLOCK 307
    self.elseIf()

    # no children left - go up a step
    self.writeComment('no children left - go up a step')

    self.popStack('childStack')
    self.popStack('parentStack')

    # IF BLOCK 307
    self.endIf()

    self.endWhile()

    # IF BLOCK 302
    self.endIf()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeDelayedLoadLinks(self):

    params= (('objectDict', self.dictInterfaceType(), 'object dict'),
             ('linkData', self.listInterfaceType(), 'link data'),)
    docString = """Load single or multiple, %slinks
derefencing as you go using objectDict.
"""
    extraDoc = {'Std':'cross', 'Exo':'exo-to-TopObject'}
    
    for tag in ('Std', 'Exo'):
    
      self.streamStartFunc(funcname='delayedLoadLinks%s' % tag, params=params,
                           docString=docString % extraDoc[tag])
      self.writeDelayedLoadLinksBody(tag)
      self.endFunc()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeDelayedLoadLinksBody(self, tag):

    ss = self.toLiteral(None)
    tt = self.baseClassVarType
    self.setVar('obj', ss, varType=tt)
    tt = self.listInterfaceType()
    self.setVar('val', ss, varType=tt)
    tt = self.stringVarType
    self.setVar('name', ss, varType=tt)
    self.writeNewline()

    self.startTry()

    self.startWhile(self.collectionIsNotEmpty('linkData',
                                            isUnique=False, isOrdered=True))

    # set up
    self.writeComment('setup')

    tt = self.dictInterfaceType()
    self.popList('curMap', 'linkData', varType=tt, castType=tt)
    tt = self.listInterfaceType()
    self.popList('val', 'linkData', castType=tt)
    tt = self.baseClassVarType
    self.popList('obj', 'linkData', castType=tt)
    self.writeNewline()

    ss = self.getDictEntry('curMap', self.toLiteral('name'))
    tt = self.stringVarType
    self.setVar('name', ss, castType=tt)

    ss = self.getDictEntry('curMap', self.toLiteral('hicard'))
    tt = self.intVarType
    self.setVar('hicard', ss, varType=tt, castType=tt)
    self.newList('valueList', varType=self.anyVarType, needDeclType=True)
    self.writeNewline()

    # map values
    self.writeComment('map values')
    
    if tag == 'Exo':
      # ExoTop version
      self.startLoop('vv', 'val', isUnique=False, isOrdered=True)
      ss = self.getDictEntry('objectDict', 'vv')
      self.setVar('oo', ss, varType=self.anyVarType)

      # IF 2
      self.startIf(self.valueIsNone('oo'))
      tt = self.callFunc('getRoot', 'obj', doWrite=False)
      self.setVar('root', tt, varType=self.dataRootVarType)
      tt = self.dictInterfaceType(keyType=self.stringVarType)
      tt = self.getDictEntry('curMap', self.toLiteral('content'),
                              castType=tt, keyIsMandatory=True)
      tt = self.getDictEntry(tt, self.toLiteral('.qName'), keyIsMandatory=True)
      self.setVar('packageName', tt, varType=self.stringVarType, castType=self.stringVarType)
      self.callFunc('refreshTopObjects', 'root', params=('packageName',))

      self.startTry()
      ss = self.getDictEntry('objectDict', 'vv', keyIsMandatory=True)
      self.setVar('oo', ss)
      self.catchException()
      self.raiseApiError('Linked-to object with ID not found', 'obj', 'name', 'vv')
      self.endTry()
      self.writeNewline()

      # IF 2
      self.endIf()

      self.addList('oo', 'valueList')
      self.endLoop()
    
    else:
      # std crosslink version
      self.startLoop('vv', 'val', isUnique=False, isOrdered=True)

      self.startTry()
      ss = self.getDictEntry('objectDict', 'vv', keyIsMandatory=True)
      self.setVar('oo', ss, varType=self.anyVarType)
      self.addList('oo', 'valueList')
      self.catchException()
      self.raiseApiError('Linked-to object with ID not found', 'obj', 'name', 
                         'vv')
      self.endTry()
      self.writeNewline()

      self.endLoop()

    # set element
    self.writeComment('set element')

    self.defineVar('ov', varType=self.anyVarType)

    # IF 3
    self.startIf(self.comparison('hicard', '==', self.toLiteral(1)))
    self.getList('ov', 'valueList')

    # IF 3
    self.elseIf(self.comparison('hicard', '>', self.toLiteral(1)))
    self.setVar('ov', self.getListSlice('valueList', hi='hicard'))

    # IF 3
    self.elseIf()
    self.setVar('ov', 'valueList')

    # IF 3
    self.endIf()

    self.streamSetValue('obj', 'name', 'ov', useDirectSet=False)

    self.endWhile()

    self.catchException()
    self.printMessage(
     self.toLiteral('Error during %s link dereferencing. Object was: ' % tag), 
     'obj'
    )
    self.printMessage(self.toLiteral('values were: '), 'val')
    self.printMessage(self.toLiteral('tag name was: '), 'name')
    self.reraiseException(exceptionClass=self.exceptionClass('ApiError'))
    self.endTry()

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamStart(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamMain(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamHandleError(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def writeLoadFromStreamEnd(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamElementTag(self, state = 'start'):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamElementText(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamElementSplitText(self, var, cnvrt = None):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamElementAttr(self, key):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamElementSetSkip(self, setToNone = False):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamElementIsSkip(self, doReset = True):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamNextElement(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamStartAttributeLoop(self, tag, value):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  # LoadFromStream function
  def streamGetValue(self, var, name, defaultValue = None,
                     keyIsMandatory = False, getChildAsDict = False):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamSetValue(self, var, name, value, useDirectSet=True):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamConvertStringToValue(self, cnvrt, value):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamOverrideOff(self, var):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamFoundClosingTag(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamHaveEarlyExit(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamConvertExolink(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamCallConstructor(self, var, constructor, parent = None, castType = None, **attrlinks):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamAddAll(self, collectionToBeAdded, collectionToBeAddedTo):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamObjDictKey(self, obj, isMetaClass):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamInitLoadingMaps(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamDoCompatibility(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # LoadFromStream function
  def streamSetupCompatibility(self):

    raise MemopsError("must be overridden")

  ###########################################################################

  ###########################################################################
  
  # SaveToStream function
  # LoadFromStream function
  def streamStartFunc(self, funcname, params=None, docString='',
                      returnString='', returnType=None, throwsApiError=True):

    raise MemopsError("must be overridden")

