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
"""code for Generating in-memory CCPN MetaModel from inside ObjectDomain

Rules for ObjectDomain version of dataModel
  
 Rules for View names:
 - As the program uses the qualified names of objects to identify them,
 Views must have names that do not overlap with classes, dataTypes or packages
 contained in the same package. Currently all view names are automatically
 made to start with an underscore ('_'), but this could be replaced with a
 constraint on the names.
 
 Special rules for Associations:
 - A class may have an association with itself where only one role is desired,
  e.g. for Resonance.covalentlyBound.
  If the two roles are identical (except that one of them may have 
  'documentation' empty and the other not), this will interpreted it as a 
  symmetrical link requiring only one role, and will not throw an error. 
  This role will be its own otherRole.
 
 Default Values:
  Default values must be converted to the correct dataType before being passed
  to MetaModel classes.
  For single valued attributes the value is simply the appropriate string.
  For multivalued attributes the default value is given as a tuple of strings,
  such that e.g. a default value of two integers must be given as 
  ('0','1').
  Parameter defaults folow the same rules as attribute defaults, except that
  only parameters with hicard == 1 can have default values
  An attribute with a default value and hicard==1 will automatically get
  locard = 0.
 
 Multiplicities:
  Multiplicities are found for attributes, links, and parameters
 
  Hicard==1 elements are by definition unordered and unique.
 
  For attributes and links the cardinality defaults to 0..1.
  For parameters it defaults to 1..1
 
  Links with hicard !=1 default to  unordered, unique.
  Attributes and parameters with hicard != 1 default to ordered, nonunique.
 
  The type expression field of attributes that are not 0..1 is set by the
  program as e.g. [3], [*], [0..2].
  
  For parameters the multiplicity is set by the type expression field, if set.
  The recommended format is e.g. [0..1], [2]. [4]{+u}, [*], 1..3]{+u-o}
  See parseMultiplicity function for exact rules.
  If this field is not set, the default is 1..1, unordered, unique
 
 
 NBNB removed hasSpecialConstructor, hasSpecialDestructor
 
 Meaning of tagged values:
 - documentation (all): Documentation string for python, html documentation ...
 - keyNames (class): The attribute(s) that serve as key and identify an object 
  relative to its parent object. NBNB change 
 - baseName(role,attribute): Role or attribute name used to generate names
  that need a name in the singular. Mandatory for list attributes, 
  defaults to class names for -to-many links.
 - isDerived (attribute, association): Derived attributes and links are in 
  principle calculated on the fly at getting time (the implementation may
  precalculate them). Derived elements can not be set or removed (unless 
  specially coded to make  it possible),  Derived elements are not stored to 
  file. There is no entry in object.__dict__ for a derived attrribute.
 - isDerived (class): Used for classes that are not stored, but that are
  calculated on the fly when needed. These may be needed for backwards
  compatibility (molecule.MolStructure.Coord) or compatibility with other
  programs' way of working.
 - isImplementation (attribute, association): Implementation attributes and 
  links are are set or derived by the implementation. The code generation
  machinery will provide the necessary code. They must be frozen and have 
  hicard ==1  Implementation elements are not stored to file. 
 - isAutomatic (attribute, association): Automatic attributes and links can 
  not be set, and the setting of them must be hardcoded in the API. They are 
  stored normally and cannot be derived. Typically serials or timestamps
 - code:python (etc.) (operation). Python code that makes up the complete body of an 
  operation. The code is correct Python, written flush left with two-space
  indentation. Imported directly into the Python API, and serves as
  documentation for other languages.
  Similarly for other languages
 - throws (operation). A comma-separated list of qualified names of operations
  that are thrown by the operation. For operations that are otherwise
  autogenerated (i.e. all opTypes that do not start with 'other') the standard
  exceptions are added automatically, so you only need to specify non-standard
  ones.
 - ConstructorCode:python (etc.) (class). Code to add to the autogenerated
  class constructor (__init__). Intended to handle creation of mandatory child 
  objects. The code is incorporated after the object has been created, but 
  before any validity checks, and is not executed if reading==True. 
  Syntax as for code:python.
  Similarly for other languages
 - DestructorCode:python (etc.) (class). Code to add to the autogenerated
  class destructor (delete). Intended to check whether the object can be deleted.
  The code is incorporated at the very top of the function, before any actions
  have been carried out. 
  Syntax as for code:python.
 - isOpen (dataType): Boolean determining whether an enumeration is open.
 - enumeration (dataType): list of permitted values for an enumeration.
  The enumeration is given as a tuple of python strings (complete with quotation
  marks), whatever the actual type of the enumeration, in the same way as 
  default values are given.
 - length (dataType): maximum length of a string dataType.
 - isOrdered (Attribute) Is order of atributes significant?
   Only meaningful if hicard != 1.
   Only used where it differs from the default
 - isUnique (Attribute, Role) Are duplicates allowed?
   Only meaningful if hicard != 1.
   Only used where it differs from the default
 
 Constraints:
 Objectdomain does not allow tagged values in constraints. We need them, 
 however, for handling code for various languages. The constraint body is 
 therefore interpreted as follows:
 Lines consisting of a single underscore are separators
 The string is of tag, separator, value, separator, ...; 
 
 
 Constants:
 MetaConstants are represented in OD by a class with stereotype 'Constant'.
 There must be no links and a single attribute named 'value'.
 The value and type of the constant is detemined by the defaultValue and
 type of the 'value' attribute.
 
 Exceptions:
 MetaConstants are represented in OD by a class with stereotype 'Exception'.
 They can have no attributes, links or operations.
 
 
 DataTypes:
 DataTypes are represented in OD by a class with stereotype 'DataType'.
 They can have no attributes, links or operations.
 
 DataObjTypes:
 DataObjTypes are represented in OD by a class with stereotype 'DataType', like
 DataTypes. They must have atttibutes, may have operations and may not have 
 links. They are handled like Classes. Only exceptions: 
 They lack isSingleton, destructorCodeStubs, and keyNames

======================COPYRIGHT/LICENSE START==========================

ObjectDomain.py: Code generation for CCPN framework

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

# NBNB TBD renamed mainkey to keyNames TBD
# NBNB TBD consider reorganising codestubs etc.
#          to allow e.g. python:file:ME tags

# general imports
import string
import time
# Ccp imports
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import OpTypes
from ccpncore.memops.metamodel import TaggedValues
from ccpncore.memops.metamodel import Util as metaUtil

MemopsError = MetaModel.MemopsError

trueString = metaConstants.trueString
falseString = metaConstants.falseString
# NBNB ObjectDomain always works under Python 2.1
# Ccp imports
True = not 0
False = not True

def toBoolean(x):
  """ Convert x to true/false.
  Could be inlined, but function is more intelligible.
  """
  return x and True or False

# set up guid generation
from odUserSetup import odUser
guidGenerator = metaUtil.SimpleGuidGenerator(odUser.operator,
                                             odUser.organisation)
newGuid = guidGenerator.newGuid

OdContainingPackageName = 'Model.Logical'

# NBNB HACK used for renaming of old to new tagged values
renameTags = {
 'mainkey':'keyNames',
 'pythonConstructorCode':'constructorCode:python',
 'javaConstructorCode':'constructorCode:java',
 'pythonDestructorCode':'destructorCode:python',
 'javaDestructorCode':'destructorCode:java',
 'pythonCode':'code:python',
 'javaCode':'code:java',
 'typeCode':'typeCode:python',
 'javaTypeCode':'typeCode:java',
 'xmlTypeCode':'typeCode:xml',
 'xmlCode':'code:xml',
}

skipTags = [
 'hasSpecialConstructor', 'hasSpecialDestructor', 'altClassName',
 'jdbcTypeCode', 'javaSimpleTypeCode', 'BMRBstatus', 'getByKey',
 '',
]

# Global variables:

# qualifiedName of Od package containing the topmost Ccp package
OdDataRootClassName = '.'.join([OdContainingPackageName,
                                metaConstants.modellingPackageName,
                                metaConstants.implementationPackageName,
                                metaConstants.dataRootName])
OdDataTypeObjectClassName = '.'.join([OdContainingPackageName,
                                metaConstants.modellingPackageName,
                                metaConstants.implementationPackageName,
                                metaConstants.baseDataTypeObjName])
OdRootClassName = '.'.join([OdContainingPackageName,
                                metaConstants.modellingPackageName,
                                metaConstants.implementationPackageName,
                                metaConstants.rootClassName])

# allowedTags gives the tagged values allowed for each category, 
# and the enumerated values (if any)
# NB These are tagged values used in ObjectDomain but stored differently 
# in the MetaModel. 
# Tagged values stored as such in the MetaModel are handled in MetaModel.py
#
# allowedTags that end in a colon (':') must match only the start of the
# actual tag. I.e. an allowedTag 'code:' would match 'code:python'.

allowedTags = {
 'MetaClass':{
  'documentation':None,
  'keyNames':None,
  'guid':None,
  'constructorCode:':None,
  'destructorCode:':None,
  'postDestructorCode:':None,
  'partitionsChildren':(trueString,),
  'isDerived':(trueString,),
 },
 'MetaAttribute':{
  'documentation':None,
  'baseName':None,
  'isDerived':(trueString,),
  'isImplementation':(trueString,),
  'isAutomatic':(trueString,),
  'isUnique':(trueString, ),
  'isOrdered':(falseString,),
  'isAbstract':(trueString,),
  'guid':None,
 },
 'MetaPackage':{
  'shortName':None,
  'documentation':None,
  'guid':None,
 },
 'MetaAssociation':{
  'isDerived':(trueString,),
  'isImplementation':(trueString,),
  'isAutomatic':(trueString,),
  'partitionsChildren':(trueString,),
  'noDeleteIfSet':(trueString,),
  'isUnique':(falseString, ),
 },
 'MetaRole':{
  'documentation':None,
  'baseName':None,
  'isOrdered':(trueString,),
  'isUnique':(falseString,),
  'guid':None,
  'noDeleteIfSet':(trueString,),
 },
 'MetaOperation':{
  'documentation':None,
  'opType':tuple(OpTypes.operationData.keys()),
  'opSubType':None,
  'guid':None,
  'throws':None,
  'code:': None
 },
 'MetaParameter':{
  'documentation':None,
  'guid':None,
 },
 'MetaDataType':{
  'documentation':None,
  'typeCode:':None,
  'isOpen':(trueString,falseString),
  'enumeration':None,
  'length':None,
  'guid':None,
 },
 'MetaConstant':{
  'guid':None,
 },
 'MetaConstraint':{
  'guid':None,
 },
 'MetaException':{
  'guid':None,
  'scope':None,
 },
 'MetaDataObjType':{
  'documentation':None,
  'guid':None,
  'constructorCode:':None,
 }
}

# NBNB TBD check various TypeCodes

# Default multiplicities:
# The standard default is set in the MetaModel
                          
# Attributes with hicard != 1
defaultMultiAttrMultiplicity = {'isUnique':False, 'isOrdered':True}
                          
# Parameters with hicard != 1
defaultMultiParMultiplicity = {'isUnique':False, 'isOrdered':True}

# Roles with hicard != 1
defaultMultiRoleMultiplicity = {'isUnique':True, 'isOrdered':False}

# default value of hicard when not set explicitly
defaultHicard = 1

# OD imports:
import objectdomain.uml.mechanisms.UmlPackage as OdUmlPackage
import objectdomain.uml.core.UmlClass as OdUmlClass
import objectdomain.uml.core.UmlAssociation as OdUmlAssociation
import objectdomain.uml.core.IDependency as OdDependency
import objectdomain.uml.core.IGeneralization as OdGeneralization
import objectdomain.uml.core.IUmlDiagram as OdUmlDiagram
import objectdomain.uml.core.UmlComment as OdUmlComment
#import objectdomain.uml.core.UmlClassifier
#import objectdomain.uml.core.UmlInterface
#import objectdomain.uml.core.UmlOperation
#import objectdomain.uml.core.UmlAttribute
#import objectdomain.uml.core.UmlParameter
#import objectdomain.uml.core.UmlTaggedValue
#import objectdomain.uml.mechanisms.UmlBaseClass
#import objectdomain.uml.mechanisms.UmlComponent

import odUtil, odApp
od = odApp.OdApp()


def modelFromOd():
  """ Make in-memory CCPN metamodel.
  Must be run inside ObjectDomain
  Usage:
  1) run this function.
  Toplevel packages are those that are contained within the package named
  OdContainingPackageName (currently 'Model.Logical')
  modelFromOd will create an in-memory python model corresponding all toplevel
  packages and their contents
  """
  
  start = time.time()
  
  # create root package
  global rootPackage
  rootPackage = MetaModel.MetaPackage(name=metaConstants.rootPackageName,
   guid='www.ccpn.ac.uk_RasmusFogh_2006-06-21-19:13:29_00000',
   taggedValues={'packageGroup':TaggedValues.defaultPackageGroup}
  )
  
  # get map of DataObjTypes ahead of time
  dataTypeObjMap = {}
  dataTypeObjMap[od.get(OdRootClassName)] = None
  ll = [od.get(OdDataTypeObjectClassName)]
  for dto in ll:
    dataTypeObjMap[dto] = None
    ll.extend([x.getSubtype() 
               for x in odUtil.toList(dto.startSpecializations())])
    
  # process packages and make direct contents
  topContainer = odObjFromQualName(OdContainingPackageName)
  elementList = odUtil.toList(topContainer.startOwns())
  for ee in elementList:
    if isinstance(ee,OdUmlPackage):
      # recursively create and add contained package and its direct contents
      objectsFromOd(ee, rootPackage, dataTypeObjMap)
  
  # get list of leaf packages:
  packages = [rootPackage]
  leafPackages = []
  for pp in packages:
    ll = pp.containedPackages
    if ll:
      pp._MetaPackage__containedPackageNames.sort()
      packages.extend(ll)
    else:
      leafPackages.append(pp)
  
  # sort names of package contents
  for pp in leafPackages:
    for tag in ('_MetaPackage__classNames', '_MetaPackage__dataTypeNames', 
                '_MetaPackage__dataObjTypeNames', '_MetaPackage__constantNames',
                '_MetaPackage__exceptionNames',):
      getattr(pp,tag).sort()
  
  # create package connections
  for metaPackage in leafPackages:
    addPackageConnections(metaPackage)
  
  #sort import/access links
  for metaPackage in leafPackages:
    dd = metaPackage._MetaModelElement__dataDict
    dd['importedPackages'] = metaUtil.sortByMethodCall(dd['importedPackages'], 
                                                       'qualifiedName')
    dd['accessedPackages'] = metaUtil.sortByMethodCall(dd['accessedPackages'], 
                                                       'qualifiedName')
  
  # create supertype links
  # NB has to happen after package connections are ready
  for metaPackage in leafPackages:
    for ee in metaPackage.dataTypes:
      setSupertypes(ee)
    for ee in metaPackage.dataObjTypes:
      setSupertypes(ee)
    for ee in metaPackage.classes:
      setSupertypes(ee)
    for ee in metaPackage.exceptions:
      setSupertypes(ee)
  
  # get DataTypes in inheritance order
  dataTypes = []
  for metaPackage in leafPackages:
    dataTypes.extend(metaPackage.dataTypes)
  dataTypes = metaUtil.sortByInheritance(dataTypes)
  
  # copy down DataType attributes - must be done in inheritance order
  for ee in dataTypes:
    inheritToDataType(ee)
  
  # process DataType attributes (in practice: convert enumerations)
  for ee in dataTypes:
    finaliseDataType(ee)
      
    dd = ee._MetaModelElement__dataDict
    dd['subtypes'] = metaUtil.sortByAttribute(dd['subtypes'],'name')
  
  # create MetaConstants - better done after datatypes are finalised
  for metaPackage in leafPackages:
    
    for qname in metaPackage._tempData['constantNames']:
      createMetaConstant(metaPackage, qname)
    del metaPackage._tempData['constantNames']
  
  # finalise remaining objects
  for metaPackage in leafPackages:
      
    # DataObjTypes
    for ee in metaPackage.dataObjTypes:
      attributesFromOd(ee)
      operationsFromOd(ee)
      
      dd = ee._MetaModelElement__dataDict
      dd['subtypes'] = metaUtil.sortByAttribute(dd['subtypes'],'name')
    
    partitioners = []
    for ee in metaPackage.classes:
    
      rolesFromOd(ee)
      attributesFromOd(ee)
      operationsFromOd(ee)
      
      # sort subtypes alphabetically
      dd = ee._MetaModelElement__dataDict
      dd['subtypes'] = metaUtil.sortByAttribute(dd['subtypes'],'name')
      
      # sort supertypes. NBNB relies on the rule that only the first supertype
      # can have a supertype in turn, and that the order of the does not matter.
      ll = dd['supertypes']
      if len(ll) > 1:
        firstSupertype = None
        if not ll[0]._MetaModelElement__dataDict['supertypes']:
          for obj in ll[1:]:
            if obj._MetaModelElement__dataDict['supertypes']:
              firstSupertype = obj
              break
          if firstSupertype is not None:
            ll.remove(firstSupertype)
            ll.insert(0,firstSupertype)
      
      # handle partitionsChildren
      if ee.partitionsChildren:
        partitioners.append(ee)
    
    for ee in partitioners:
      for xx in ee.getAllSubtypes():
        xx.partitionsChildren=True
      
    # exceptions
    for ee in metaPackage.exceptions:
      dd = ee._MetaModelElement__dataDict
      dd['subtypes'] = metaUtil.sortByAttribute(dd['subtypes'],'name')
  
  
  # Needed for special code in loop
  ss = '%s.%s' % (metaConstants.modellingPackageName,
                  metaConstants.implementationPackageName)
  implPackage = rootPackage.metaObjFromQualName(ss)
  rootClass = implPackage.getElement(metaConstants.dataRootName)
  rootName = metaUtil.lowerFirst(metaConstants.dataRootName)
  
  # Second run for special purposes and some things that have to be delayed
  for metaPackage in leafPackages:
    if metaPackage is implPackage:
      continue
    for ee in metaPackage.classes:
      
      # special code: Add parent and current link to root for TopObjects
      # parent TopObject must have keyNames and lack superclasses in the package
      # NB special code requires that all links are properly done first
      
      if not ee.isAbstract:
      
        # look for parentRole or keyNames in superclasses
        cc = ee
        topClass = None
        while cc is not None and cc.container is metaPackage:
          pRole = cc.__dict__.get('parentRole')
          keyNames = cc._MetaModelElement__dataDict.get('keyNames')
          if pRole:
            topClass = cc
            break
          elif keyNames:
            topClass = cc
          cc = cc.supertype
        
        if pRole:
          # parentRole found - use it
          if pRole.valueType.container is metaPackage:
            # parentRole is not to MemopsRoot. Not a TopObject
            continue
          else:
            # This is a TopObject
            topRole = pRole
        
        elif topClass is not None:
          # No parentRole - topClass is the topObject
          # add parentRole to it
          params = {'container':topClass, 'valueType':rootClass, 
           'aggregation':metaConstants.composite_aggregation,
           'hierarchy':metaConstants.parent_hierarchy,
           'changeability':metaConstants.frozen,
           'locard':1, 'name':rootName, 'baseName':rootName,
           'guid':'ccpn_automatic_%s.%s' % (topClass.qualifiedName(),rootName),
           'documentation':'parent link',
          }
          topRole = MetaModel.MetaRole(**params)
          baseName = metaUtil.lowerFirst(topClass.name)
          params = {'container':rootClass, 'valueType':topClass, 
           'hierarchy':metaConstants.child_hierarchy,
           'locard':0, 'hicard':metaConstants.infinity,
           'name':baseName+'s', 'baseName':baseName,
           'guid':'ccpn_automatic_%s.%s' % (rootClass.qualifiedName(),baseName),
           'documentation':'child link',
           'otherRole':topRole,
          }
          MetaModel.MetaRole(**params)
          
        else:
          # neither parentRole nor keyNames
          raise MemopsError(
           "Non-abstract MetaClass %s inherits neither parentRole nor keyNames"
           % ee.qualifiedName()
          )
        
        # add current link if necessary
        baseName = topRole.otherRole.baseName
        BaseName =  metaUtil.upperFirst(baseName)
        curRoleName = 'current' + BaseName
        curRole = rootClass.getElement(curRoleName)
        if curRole is None:
          # add current link
          params = {'container':rootClass, 'valueType':topClass,
           'name':curRoleName, 'baseName':curRoleName,
           'guid':'ccpn_automatic_%s.current%s' % (rootClass.qualifiedName(),
                                            BaseName),
           'documentation':('current %s - may be reset by implementation.'
                            % baseName),
          }
          curRole = MetaModel.MetaRole(**params)
        
        # add getter function if necessary
        getOpName = 'getCurrent%s' % BaseName
        getOp = rootClass.getElement(getOpName)
        if getOp is None:
          params = {'isQuery':True, 'opType':'get', 'target':curRole,
           'container':rootClass, 'name':getOpName, 
           'guid':'ccpn_automatic_%s.%s' % (rootClass.qualifiedName(),
                                               getOpName),
           'documentation':"Get for %s.current%s" % (rootClass.qualifiedName(),
                                              BaseName),
          }
          getOp = MetaModel.MetaOperation(**params)
          
          pythonCode = """
result = dataDict.get('current%s')
if result is None:
  self.findFirst%s()
  result = dataDict.get('current%s')
""" % (BaseName, BaseName, BaseName)
          getOp.addCodeStub('python', pythonCode)
            
          javaCode = """
result = _current%s;
if (result == null) {
  findFirst%s();
  result = _current%s;
}
""" % (BaseName, BaseName, BaseName)
          getOp.addCodeStub('java', javaCode)
      
      # end special code 
      ee._MetaClass__roleNames.sort()
            
  
  # add operation targets
  for metaPackage in leafPackages:
      
    # DataObjTypes and classes
    for ee in metaPackage.dataObjTypes + metaPackage.classes:
      for op in ee.operations:
        op.target = OpTypes.getTarget(op)
  
  print ("Generated without errors: %s" 
         % rootPackage._MetaPackage__containedPackageNames)
  
  mid = time.time()
  
  # complete is better, but too slow for constant use. 
  # To be tried every now and then
  #rootPackage.checkValid(complete=True)
  rootPackage.checkValid()
  
  # check operator and organisation for illegal characters
  for ss in  (odUser.operator, odUser.organisation):
    if ss:
      for char in metaConstants.xmlDisallowedChars:
        if char in ss:
          raise MemopsError(
           "user or operator string %s contains illegal character %s"
           % (ss,repr(char))
          )
          
  end = time.time()
  print ("Checks valid: %s - generation %.3fs, validity check %.3fs" 
   % (rootPackage._MetaPackage__containedPackageNames, (mid-start), (end-mid))
  )
  #
  return rootPackage

def getTopPackageName(odObj):
  """ get name of top-level package containing odObj
  By definition this is also the qualified name of the top-level package.
  """
  nn = len(OdContainingPackageName) + 1
  qname = odObj.qualifiedName[nn:]
  return qname.split('.')[0]
  

def objectsFromOd(odPackage, container, dataTypeObjMap):
  """  create metaPackage instance, recursively create contained packages,
  and create all objects directly contained in packages.
  """
  
  #######################################################################
  # make package
  
  name = odPackage.name
  guid = getGuid(odPackage)
    
  tagVals, extraTaggedValues = taggedValuesFromOd(odPackage, 'MetaPackage')
  
  # set packageGroup to default, if necessary
  if not extraTaggedValues.has_key('packageGroup'):
    extraTaggedValues['packageGroup'] = TaggedValues.defaultPackageGroup
  
  # get parameters
  params = {
   'name'         : name,
   'guid'         : guid,
   'container'    : container,
   'documentation': odPackage.getDocumentation(),
   'taggedValues' : extraTaggedValues,
   'isRoot'       : toBoolean(odPackage.isInheritanceRoot()),
   'isLeaf'       : toBoolean(odPackage.isLeaf()),
   'isAbstract'   : toBoolean(odPackage.isAbstract()),
   'visibility'   : str(odPackage.getVisibility()) + '_vis',
   'shortName'    : tagVals.get('shortName'),
  }
  
  # create package
  metaPackage = MetaModel.MetaPackage(**params)  
  
  ########################################################################
  # make package contents. 
  
  elementList = odUtil.toList(odPackage.startOwns())
  
  tempnames = {}
  diagnames = []
  
  # add temporary list to metaPackage
  metaPackage._tempData['constantNames'] = []
  
  for ee in elementList:
    
    # check for name overlap
    if tempnames.has_key(ee.name):
      raise MemopsError("Package namespace overlap for %s" % ee.qualifiedName)
    elif ee.name:
      tempnames[ee.name] = None
        
    if isinstance(ee,OdUmlPackage):
      # recursively create and add contained package
      
      # NBNB TBD check here if package is not loaded, and skip if it is.
      
      objectsFromOd(ee, metaPackage, dataTypeObjMap)
  
    elif isinstance(ee,OdUmlClass):
      # create class or datatype
      stereotype = ee.getStereotype().name
      
      if stereotype == 'DataType':
        if dataTypeObjMap.has_key(ee):
          # DataObjType - NB it *is* 'classFromOd', it is not a typo
          classFromOd(metaPackage,ee)
        else:
          # DataType
          dataTypeFromOd(metaPackage,ee)
      
      elif stereotype == 'Constant':
        # constant
        metaPackage._tempData['constantNames'].append(ee.qualifiedName)
      
      elif stereotype == 'Exception':
        # exception
        exceptionFromOd(metaPackage,ee)
      
      elif stereotype == 'unspecified':
        # class
        classFromOd(metaPackage,ee)
      
      else:
        raise MemopsError(' Class %s has unimplemented stereotype %s' %
         (ee.qualifiedName,stereotype)
        )
      
    elif isinstance(ee,OdDependency):
      # handle on next pass
      pass
    
    elif isinstance(ee,OdUmlDiagram):
      # add to diagram name list
      diagnames.append(ee.name)
        
    elif isinstance(ee,OdUmlComment):
      # ignore
      pass
    
    else:
      # NB we are not supporting other elements. 
      # This includes generalizations (package inheritance)
      print 'Error on element of class :', ee.__class__
      print 'Error on element of class named:', ee.__class__.__name__
      raise MemopsError(" package contains object %s  of unexpected type"
       % ee.qualifiedName
      )
  
  # sort out docDiagramNames tagged value
  if diagnames:
    diagnames.sort()
    metaPackage.addTaggedValue('docDiagramNames',' '.join(diagnames))
  
  # clean up branch packages
  if metaPackage.containedPackages:
    del metaPackage._tempData['constantNames']

  #
  return metaPackage

def classFromOd(metaPackage, odClass):
  """ create MetaClass or MetaDataObjType within metaPackage
  """
  name = odClass.name
  guid = getGuid(odClass)
  
  tagVals, extraTaggedValues = taggedValuesFromOd(odClass, 'MetaClass')
  
  # get parameters
  params = {
   'name'         : name,
   'guid'         : guid,
   'container'    : metaPackage,
   'documentation': odClass.getDocumentation(),
   'taggedValues' : extraTaggedValues,
   'isRoot'       : toBoolean(odClass.isInheritanceRoot()),
   'isLeaf'       : toBoolean(odClass.isLeaf()),
   'isAbstract'   : toBoolean(odClass.isAbstract()),
   'visibility'   : str(odClass.getVisibility()) + '_vis',
  }
  
  # set constructor code stubs
  dd = tagVals.get('constructorCode')
  if dd:
    params['constructorCodeStubs'] = dd
  
  if odClass.getStereotype().name == 'DataType':
    # create DataObjType
    
    if [x for x in odUtil.toList(odClass.startOwns()) 
        if isinstance(x,OdUmlAssociation)]:
      raise MemopsError("DataObjType %s.%s has roles" % (metaPackage, name))
    
    clazz = MetaModel.MetaDataObjType(**params)
    
  else:
    
    # set Boolean parameters
    for tag in ('partitionsChildren', 'isDerived'):
      if tagVals.get(tag) == trueString:
        params[tag] = True
    
    # set destructor code stubs
    dd = tagVals.get('destructorCode')
    if dd:
      params['destructorCodeStubs'] = dd
    dd = tagVals.get('postDestructorCode')
    if dd:
      params['postDestructorCodeStubs'] = dd
    
    # create class
    clazz = MetaModel.MetaClass(**params)
 
    # NB isSingleton is not defined in OD. Would require a tagged value.
    # use default in MetaModel
 
    # set keyNames
    keyNames = tagVals.get('keyNames','')
    if keyNames:
      for kk in map(string.strip,string.split(keyNames,',')):
        clazz.addKeyName(kk)
  
  # Constraints:
  addConstraints(clazz, odClass)

def dataTypeFromOd(metaPackage, odDataTypeClass):
  """ create metaDataType within metaPackage
  """
  name = odDataTypeClass.name
  guid = getGuid(odDataTypeClass)
  
  if odUtil.toList(odDataTypeClass.operationElements()):
    raise MemopsError("DataType %s.%s has operations" % (metaPackage, name))
    
  if odUtil.toList(odDataTypeClass.attributeElements()):
    raise MemopsError("DataType %s.%s has attributes" % (metaPackage, name))
  
  if [x for x in odUtil.toList(odDataTypeClass.startOwns()) 
      if isinstance(x,OdUmlAssociation)]:
    raise MemopsError("DataType %s.%s has roles" % (metaPackage, name))
  
  tagVals, extraTaggedValues = taggedValuesFromOd(odDataTypeClass,
                                                  'MetaDataType')
  
  # get parameters
  params = {
   'name'         : name,
   'guid'         : guid,
   'container'    : metaPackage,
   'documentation': odDataTypeClass.getDocumentation(),
   'taggedValues' : extraTaggedValues,
   'isRoot'       : toBoolean(odDataTypeClass.isInheritanceRoot()),
   'isLeaf'       : toBoolean(odDataTypeClass.isLeaf()),
   'isAbstract'   : toBoolean(odDataTypeClass.isAbstract()),
   'visibility'   : str(odDataTypeClass.getVisibility()) + '_vis'
  }

  # set type code stubs
  dd = tagVals.get('typeCode')
  if dd:
    params['typeCodes'] = dd
  
  isOpen = tagVals.get('isOpen')
  if isOpen == trueString:
    params['isOpen'] = True
  elif isOpen == falseString:
    params['isOpen'] = False
  
  length = tagVals.get('length')
  if length is not None:
    params['length'] = int(length)
  
  # NB The enumeration evals to a tuple of strings.
  # Is converted to the right dataType during the next pass
  enums = tagVals.get('enumeration')
  if enums is not None:
    params['enumeration'] = eval(enums,{})
  
  dataType = MetaModel.MetaDataType(**params)
  
  # Constraints:
  addConstraints(dataType,odDataTypeClass)


def exceptionFromOd(metaPackage,odClass):
  """ create MetaException within metaPackage
  """
  
  name = odClass.name
  guid = getGuid(odClass)
  
  tagVals, extraTaggedValues = taggedValuesFromOd(odClass, 'MetaException')
  
  # get parameters
  params = {
   'name'         : name,
   'guid'         : guid,
   'container'    : metaPackage,
   'documentation': odClass.getDocumentation(),
   'taggedValues' : extraTaggedValues,
   'visibility'   : str(odClass.getVisibility()) + '_vis',
  }
  
  # get scope
  scope = tagVals.get('scope')
  if scope:
    params['scope'] = scope
  
  MetaModel.MetaException(**params)


def addPackageConnections(metaPackage):
  
  # get metaPackage from Od side
  odPackage = odObjFromQualName(metaPackage.qualifiedName())
  
  for ee in [x for x in odUtil.toList(odPackage.startOwns())
                     if isinstance(x,OdDependency)]:
    
    suppliers = odUtil.toList(ee.startSuppliers())
    clients = odUtil.toList(ee.startClients())
 
    if len(suppliers) != 1:
      for xx in suppliers:
        print ("Supplier %s" % xx.qualifiedName)
      raise MemopsError("Dependency %s must have a single supplier, has %s"
       % (ee.qualifiedName, len(suppliers))
      )
 
    elif  len(clients) != 1:
      for xx in clients:
        print ("Client %s" % xx.qualifiedName)
      raise MemopsError("Dependency %s must have a single client, has %s"
       % (ee.qualifiedName, len(clients))
      )
 
    if isinstance(clients[0],OdUmlComment):
      pass
 
    elif ee.getStereotype().name == 'import':
      # process package import
 
      ll = odUtil.toList(ee.startSuppliers())
      metaPackage.addImportedPackage(metaObjFromQualName(ll[0].qualifiedName))
 
    else:
      raise MemopsError(" Dependency %s is of unsupported type"
       % ee.qualifiedName
      )
  
  # Add Implementation package import
  implPackage = metaObjFromQualName('%s.%s' % 
   (metaConstants.modellingPackageName, metaConstants.implementationPackageName)
  )
  if metaPackage is not implPackage:
  
    if implPackage not in metaPackage.importedPackages:
      metaPackage.addImportedPackage(implPackage)


def setSupertypes(metaObj):
  """ set superType link (if any)
  """ 
  
  odObj = odObjFromQualName(metaObj.qualifiedName())

  generalisations = [ee for ee in odUtil.toList(odObj.startOwns())
                      if isinstance(ee, OdGeneralization)]
             
  if generalisations:    
    supertypes = [metaObjFromQualName(gg.getSupertype().qualifiedName)
                  for gg in generalisations]     
    
    metaObj.supertypes = supertypes  


def inheritToDataType(subType):
  """ copy attributes down from supertype to subtype
  NB in ObjectDomain these attributes are not set if they are the same
  as those in the superType
  NB the function assumes that inheritance is done in the supertype
  before it is done in the subtype.
  """
  
  superType = subType.supertype
  
  if superType is not None:
    
    subTypeCodes = subType.typeCodes
    for tag,val in superType.typeCodes.items():
      if not subTypeCodes.has_key(tag):
        subType.addTypeCode(tag,val)
  
    if subType.length is None:
      subType.length = superType.length
  
    if not subType.enumeration:
      subType.enumeration = superType.enumeration
  
    if subType.isOpen:
      subType.isOpen = superType.isOpen
 
 
def finaliseDataType(dataType):
  """ Convert enumerations from strings to correct type
  """
  
  # convert enumerations from String (now the dataType is complete)
  enum = dataType.enumeration
  if enum:
    typeCode = dataType.typeCodes.get('python')
    if typeCode:
      func = getattr(metaConstants.baseDataTypeModule,typeCode).fromString
      try:
        dataType.enumeration = tuple(map(func,enum))
      except:
        print ("%s error in converting enumeration to correct data type" 
               % dataType)
        raise
    else:
      raise MemopsError("%s has no python typeCode - may be missing superType"
       % dataType
      )


def createMetaConstant(metaPackage,qname):
  """ create MetaConstant within metaPackage
  """
  
  odClass = odObjFromQualName(qname)
  
  name = odClass.name
  guid = getGuid(odClass)
  
  tagVals, extraTaggedValues = taggedValuesFromOd(odClass, 'MetaConstant')
  
  # get parameters
  params = {
   'name'         : name,
   'guid'         : guid,
   'container'    : metaPackage,
   'documentation': odClass.getDocumentation(),
   'taggedValues' : extraTaggedValues,
  }
  
  # get value attribute
  for odAttr in odUtil.toList(odClass.attributeElements()):
    
    # get attribute 'value'
    valueAttr = None
    if odAttr.name == 'value':
      if valueAttr is None:
        valueAttr = odAttr
      else:
        raise MemopsError(
         "%s: MetaConstant has more than one attribute named 'value'" % (qname,)
        )
    else:
      raise MemopsError(
       "%s: MetaConstant attribute named %s instead of 'value'" 
       % (qname,odAttr.name)
      )
  
  # set valueType
  valueType = metaObjFromQualName(valueAttr.getTypeRef().qualifiedName)
  params['valueType'] = valueType
  
  # get value
  defVal = valueAttr.getInitialValue()
  if defVal:
    typeCode = valueType.typeCodes.get('python')
    if typeCode:
      func = getattr(metaConstants.baseDataTypeModule,typeCode).fromString
      try:
        value = func(defVal)
      except:
        print ("%s error in converting value to correct data type"
               % qname)
        raise
      params['value'] = value
    else:
      raise MemopsError("%s has no python typeCode - may be missing superType"
       % valueType
      )
  else:
    raise MemopsError("%s.value hs no default value" % qname)
  
  MetaModel.MetaConstraint(**params)
    

def attributesFromOd(metaObj): 
  """ get all attributes from odClass and put them in appropriate metaClass
  NB requires that dataTypes are already read and postprocessed.
  metaObj may be either a MetaClass or a MetaDataObjType
  """
  odClass = odObjFromQualName(metaObj.qualifiedName())
  
  for odAttr in odUtil.toList(odClass.attributeElements()):
  
    name = odAttr.name
    guid = getGuid(odAttr)
    
    if not name:
      raise MemopsError("nameless attribute in %s" % metaObj)

    try:
      valueType = metaObjFromQualName(odAttr.getTypeRef().qualifiedName)
    except:
      print ("Error setting type of %s.%s to %s" %
       (odClass.qualifiedName, name, repr(odAttr.getTypeRef()))
      )
      raise
    
    tagVals, extraTaggedValues = taggedValuesFromOd(odAttr, 'MetaAttribute')
    
    documentation = odAttr.getDocumentation()
    params = {
     'container'    : metaObj,
     'name'         : name,
     'guid'         : guid,
     'documentation': documentation,
     'taggedValues' : extraTaggedValues,
     'valueType'    : valueType
    }
    
    # Set default documentation for special attributes
    if not documentation:
      if name == metaConstants.serial_attribute:
        params['documentation'] = (
         "Serial number of object. Serves as object main key."
         " Serial numbers of deleted objects are not re-used."
         " Serial numbers can only be set by the implementation."
         " Values are in practice always positive, since negative"
         " values are interpreted as a signal to set the next free serial"
        )
      if name == metaConstants.details_attribute:
        params['documentation'] = (
         "Free text, for notes, explanatory comments, etc."
        )
    
    # get scope
    scope = str(odAttr.getTargetScope())
    if scope == 'instance':
      params['scope'] = metaConstants.instance_level
    elif scope == 'type':
      params['scope'] = metaConstants.classifier_level
    else:
      raise MemopsError('%s.%s : scope %s not supported' 
       % (odClass.qualifiedName, name, scope)
      )
    
    # get visibility
    params['visibility'] = str(odAttr.getVisibility()) + '_vis'
    
    # get changeability
    changeability = str(odAttr.getChangeability())
    if changeability == 'none':
      params['changeability'] = metaConstants.changeable
    elif changeability == 'frozen':
      params['changeability'] = metaConstants.frozen
    elif changeability == 'Add Only':
      params['changeability'] = metaConstants.add_only
    else:
      raise MemopsError('%s.%s : changeability %s not supported' % 
       (odClass.qualifiedName, name, changeability)
      )
    
    # get isDerived
    for tag in ('isDerived', 'isAutomatic', 'isAbstract', 'isImplementation'):
      if tagVals.get(tag) == trueString:
        params[tag] = True
      else:
        params[tag] = False
    
    # get multiplicity
    mul = odAttr.getMultiplicity()
    nn = mul.getCount()
    #
    if nn == 0:
      pass
    #
    elif nn == 1:
      # one multiplicity range - process it
      rr = mul.getRange(0)
      params['locard'] = max(rr.low,0)
      hicard = rr.high
      if hicard < 1:
        hicard = metaConstants.infinity
      params['hicard'] = hicard
      if hicard != 1:
        params.update(defaultMultiAttrMultiplicity)
    #
    else:
      # multiple ranges - throw error
      raise MemopsError('%s.%s has illegal multipicity indicator : %s' % 
       (odClass.qualifiedName, name, mul.asText())
      )
    #
    # fix missing parameters
      
    # get isOrdered
    if tagVals.get('isOrdered') == trueString:
      params['isOrdered'] = True
    elif tagVals.get('isOrdered') == falseString:
      params['isOrdered'] = False
 
    # get isUnique
    if tagVals.get('isUnique') == trueString:
      params['isUnique'] = True
    elif tagVals.get('isUnique') == falseString:
      params['isUnique'] = False
      
    # NB hicard defaults to 1
    hicard = params.get('hicard', defaultHicard)
    if hicard == 1:
      params['baseName'] = name

    else:
      ss = tagVals.get('baseName')
      if not ss:
        raise MemopsError("%s : baseName tagged value missing" 
         % odAttr.qualifiedName
        )
      params['baseName'] = ss

    # get defaultValue
    defaultValue = odAttr.getInitialValue()
    if defaultValue:
      typeCode = valueType.typeCodes.get('python')
      ff = getattr(metaConstants.baseDataTypeModule, typeCode).fromString
      if hicard == 1:
        try:
          params['defaultValue'] = (ff(defaultValue),)
        except:
          print ("%s error in converting default value %s"
                 % (odAttr.qualifiedName, defaultValue))
          raise
      else:
        try:
          params['defaultValue'] = tuple(map(ff,eval(defaultValue)))
        except:
          print ("%s error in converting default value %s"
                 % (odAttr.qualifiedName, defaultValue))
          raise
    
    # create attribute
    attribute = MetaModel.MetaAttribute(**params)
  
    # handle constraints
    addConstraints(attribute,odAttr)


def rolesFromOd(metaClass):
  """ get both roles from association assoc 
  and put them in appropriate metaClass
  """
  
  odClass = odObjFromQualName(metaClass.qualifiedName())
  
  for odAssoc in [x for x in odUtil.toList(odClass.startOwns()) 
                      if isinstance(x,OdUmlAssociation)]:
    
    # set up
    roleData = [{},{}]
    aes = odUtil.toList(odAssoc.startConnections())
    try:
      assert len(aes) == 2, 'Error, association must have 2 ends: %s' % aes
    except:
      print ('ERROR - link with wrong number of ends:', metaClass)
      raise
    # get classes and types
    classNames = (aes[0].getType().qualifiedName,aes[1].getType().qualifiedName)

    skipAssociation = False
    for ii in range(2):
 
      try:
        clazz = metaObjFromQualName(classNames[ii])
        roleData[ii]['valueType'] = clazz
 
      except MemopsError:
 
        if OdDataRootClassName in classNames:
          # NBNB TBD
          # Link involving DataRootClass. 
          # It is OK the class on the other end is missing. Ignore
          print("WARNING, link between %s and %s accesses unknown package"
           % classNames
          )
          skipAssociation = True
 
        elif toBoolean(aes[ii].isNavigable()):
          # class on the other end reachable, but not defined
          print ("ERROR for link between %s and %s" % classNames)
          raise
 
        else:
          # The class on the other end is not defined but also not reachable
          # This is a one-way link into a class *into* the model
          # Ignore
          skipAssociation = True
    
    if skipAssociation:
      continue
    
    metaClasses = [roleData[1]['valueType'], roleData[0]['valueType']]
 
    # get tagged values from Association
    assoTagVals, assoExtraTaggedValues = taggedValuesFromOd(odAssoc, 'MetaAssociation')
    
    #  get isDerived, isAutomatic isImplementation partitionsChildren
    for tag in ('isDerived', 'isAutomatic', 'partitionsChildren', 
                'isImplementation'):
      if assoTagVals.get(tag) == trueString:
        x = True
      else:
        x = False
      roleData[0][tag] = roleData[1][tag] = x
  
    # get isAbstract
    x = toBoolean(odAssoc.isAbstract())
    roleData[0]['isAbstract'] = roleData[1]['isAbstract'] = x
    
    # get rest of parameters, from association ends
    for ii in range(2):
      otherii = 1 - ii
      ae = aes[ii]
      dd = roleData[ii]
 
      # get metaClass -needed for error messages only
      metaClass = roleData[otherii]['valueType']
 
      # get name(s) (first pass)
      tempRoleName = ae.name
      if not tempRoleName:
        tempRoleName = metaUtil.lowerFirst(dd['valueType'].name)
      
      # get tagged values
      tv, etv = taggedValuesFromOd(ae,'MetaRole')
 
      tagVals = assoTagVals.copy()
      tagVals.update(tv)
      extraTaggedValues = assoExtraTaggedValues.copy()
      extraTaggedValues.update(etv)
      
      # NBNB TBD
      if extraTaggedValues.get('isImplementation'):
        print ('ERROR implementation role %s.%s' % (metaClass,tempRoleName))
 
      # get documentation and tagged values
      dd['documentation'] = ae.getDocumentation()
      dd['taggedValues'] = extraTaggedValues
 
      # get scope
      scope = str(ae.getTargetScope())
      if scope == 'instance':
        dd['scope'] = metaConstants.instance_level
      elif scope == 'type':
        dd['scope'] = metaConstants.classifier_level
      else:
        raise MemopsError('%s.%s : scope %s not supported' %
         (metaClass.qualifiedName(),tempRoleName,scope)
        )
 
      # get visibility
      dd['visibility'] = str(ae.getVisibility()) + '_vis'
 
      # get changeability
      changeability = str(ae.getChangeability())
      if changeability == 'none':
        dd['changeability'] = metaConstants.changeable
      elif changeability == 'frozen':
        dd['changeability'] = metaConstants.frozen
      elif changeability == 'Add Only':
        dd['changeability'] = metaConstants.add_only
      else:
        raise MemopsError('%s.%s : changeability %s not supported' %
         (metaClass.qualifiedName(),tempRoleName,changeability)
        )
 
      # get aggregation
      aggregation = ae.getAggregation()
      if aggregation == aggregation.COMPOSITE:
        dd['aggregation'] = metaConstants.composite_aggregation
        dd['hierarchy'] = metaConstants.parent_hierarchy
        roleData[otherii]['hierarchy'] = metaConstants.child_hierarchy
      elif aggregation == aggregation.AGGREGATE:
        # aggregate is not supported, but for completeness
        try:
          dd['aggregation'] = metaConstants.aggregate_aggregation
        except:
          raise MemopsError("%s.%s aggregation 'aggregate' not supported" %
           (metaClass.qualifiedName(), tempRoleName,)
          )
      else:
        dd['aggregation'] = metaConstants.no_aggregation
 
      # get multiplicity
      mul = ae.getMultiplicity()
      nn = mul.getCount()
      #
      if nn == 0:
        pass
      #
      elif nn == 1:
        # one multiplicity range - process it
        rr = mul.getRange(0)
        dd['locard'] = max(rr.low,0)
        hicard = rr.high
        if hicard < 1:
          hicard = metaConstants.infinity
        dd['hicard'] = hicard
        if hicard != 1:
          dd.update(defaultMultiRoleMultiplicity)
      #
      else:
        # multiple ranges - throw error
        raise MemopsError('%s.%s has illegal multipicity indicator : %s' %
         (metaClass.qualifiedName(), tempRoleName, mul.asText())
        )
      #
      # fix missing parameters
      # NB hicard efaults to 1
      if dd.get('hicard', defaultHicard) == 1:
        dd['baseName'] = tempRoleName
 
      else:
        baseName = tagVals.get('baseName')
        if baseName is None:
          if ae.name:
            # explicit names require explicit basenames (to reduce errors)
            raise MemopsError(
             "%s.%s has explicit name, but no baseName tagged value"
             % (metaClass.qualifiedName(), tempRoleName)
            )
          else:
            baseName = metaUtil.lowerFirst(dd['valueType'].name)
 
        dd['baseName'] = baseName
 
      # get noDeleteIfSet
      if tagVals.get('noDeleteIfSet') == trueString:
        dd['noDeleteIfSet'] = True
 
      # get isUnique
      if tagVals.get('isUnique') == trueString:
        dd['isUnique'] = True
      elif tagVals.get('isUnique') == falseString:
        dd['isUnique'] = False

      # get isOrdered
      if ae.isOrdered():
        dd['isOrdered'] = True
      else:
        dd['isOrdered'] = False
 
    # create both roles:
    doRoles = []
    for ii in range(2):
      if toBoolean(aes[ii].isNavigable()):
        baseName = roleData[ii]['baseName']
        # NB hicard defaults to 1
        if roleData[ii].get('hicard', defaultHicard) == 1:
          name = baseName
        else:
          name = aes[ii].name
          if not name:
            name = baseName + 's'
        roleData[ii]['name'] = name
        doRoles.append(ii)
      
    if len(doRoles) == 1:
      
      # only navigable one direction. Create
      ii = doRoles[0]
      
      # get guid
      guid = getGuid(aes[ii])
 
      role = MetaModel.MetaRole(container=metaClasses[ii], guid=guid,
                                **roleData[ii])
      addConstraints(role,aes[ii])
 
    elif len(doRoles) == 2:
      # navigable both directions.
 
      if (metaClasses[0] is metaClasses[1] and 
          roleData[0]['name'] == roleData[1]['name']):
        # Special case - symmetrical to-own-class link. Create one, shared role.
        # Equalise documentation and check roles are identical
 
        if not roleData[0].get('documentation'):
          roleData[0]['documentation'] = roleData[1].get('documentation')
 
        elif not roleData[1].get('documentation'):
          roleData[1]['documentation'] = roleData[0].get('documentation')
 
        if roleData[0] ==  roleData[1]:
          # OK for special case, implement:
          
          # first arrange guid
          guids = [x.getTaggedValueVal('guid') for x in aes]
          if guids[0] == guids[1]:
            guid = guids[0]
            if not guid:
              guid = newGuid()
              aes[0].setTaggedValueVal('guid', guid)
              aes[1].setTaggedValueVal('guid', guid)
              
          else:
            raise MemopsError("two OD roles named %s have different guid" 
                              % aes[0].qualifiedName)
          # now make role
          role = MetaModel.MetaRole(container=metaClasses[0], guid=guid,
                                    **roleData[0])
          role.setOtherRole(role)
 
          addConstraints(role,aes[0])
 
        else:
          raise MemopsError("%s.%s Invalid symmetrical -to-self association." %
           (metaClasses[0].name, roleData[0].get('name'))
          )
 
      else:
        # normal two-way link. Implement
        
        guid = getGuid(aes[0])
        role  = MetaModel.MetaRole(container=metaClasses[0], guid=guid, 
                                   **roleData[0])
        guid = getGuid(aes[1])
        role1 = MetaModel.MetaRole(container=metaClasses[1], guid=guid, 
                                   **roleData[1])
        role.setOtherRole(role1)
 
        # add constraints
        addConstraints(role,aes[0])
        addConstraints(role1,aes[1])
 
    else:
      raise MemopsError(
       "Link between classes %s One or two roles must be navigable." %
       (tuple(classNames),)
      )


def operationsFromOd(metaClass):
  """ get all operations from odClass and put them in appropriate metaClass
  """
  
  odClass = odObjFromQualName(metaClass.qualifiedName())
  
  for odOp in odUtil.toList(odClass.operationElements()):
  
    name = odOp.name
    guid = getGuid(odOp)
    
    tagVals, extraTaggedValues = taggedValuesFromOd(odOp,'MetaOperation')
    
    #
    params = {
     'container'    : metaClass,
     'name'         : name,
     'guid'         : guid,
     'documentation': odOp.getDocumentation(),
     'taggedValues' : extraTaggedValues
    }
  
    # set  code stubs
    dd = tagVals.get('code')
    if dd:
      params['codeStubs'] = dd
    
    # get scope. NBNB we use owner scope as here is no target scope WOT IS ???!!
    scope = str(odOp.getOwnerScope())
    if scope == 'instance':
      params['scope'] = metaConstants.instance_level
    elif scope == 'type':
      params['scope'] = metaConstants.classifier_level
    else:
      raise MemopsError('%s : scope %s not supported' %
      (odOp.qualifiedName,scope)
     )
    
    # get visibility
    params['visibility'] = str(odOp.getVisibility()) + '_vis'
    
    # get isQuery
    params['isQuery'] = toBoolean(odOp.isQuery())
    
    # get isAbstract
    params['isAbstract'] = toBoolean(odOp.isAbstract())
    
    # get opType
    params['opType'] = tagVals.get('opType')
    params['opSubType'] = tagVals.get('opSubType')
    if params['opType'] is None:
      raise MemopsError('%s : operation lacks opTyped' % odOp.qualifiedName)
    
    # make operation
    metaOperation = MetaModel.MetaOperation(**params)
    
    # add parameters
    parametersFromOd(metaOperation)
    

def parametersFromOd(metaOp):
  """ get all parameters for odOperation and add as appropriate
  NB requires that dataTypes are already read and postprocessed.
  """
  
  opType = metaOp.opType
  opTargetTag = OpTypes.operationData[opType]['targetTag']
  
  odOp = odObjFromQualName(metaOp.qualifiedName())
  
  if opTargetTag == 'masterOp':
    # add parameters
 
    for odPar in odUtil.toList(odOp.startParameters()):
 
      # get parameter name
      name = odPar.name
      guid = getGuid(odPar)
 
      # get parameter type
      try:
        valueType = metaObjFromQualName(odPar.getTypeRef().qualifiedName)
      except:
        print ("Error setting type of %s to %s" %
         (odPar.qualifiedName, repr(odPar.getTypeRef()))
        )
        raise
 
      # get tagged values
      tagVals, extraTaggedValues = taggedValuesFromOd(odPar, 'MetaParameter')
 
      # get documentation
      params = {
       'container'    : metaOp,
       'name'         : name,
       'guid'         : guid,
       'documentation': odPar.getDocumentation(),
       'taggedValues' : extraTaggedValues,
       'valueType'    : valueType
      }
 
      # get parameter direction
      params ['direction'] = str(odPar.getKind()) + '_dir'
 
      # get cardinality etc. from typeExpression
      ss = odPar.getTypeExpression().getBody()
      params.update(parseMultiplicity(ss))
      hicard = params.get('hicard',defaultHicard)
      if hicard != 1:
        params.update(defaultMultiParMultiplicity)
 
      # get defaultValue
      defaultValue = odPar.getDefaultValue()
      if defaultValue:
        typeCode = valueType.typeCodes.get('python')
        ff = getattr(metaConstants.baseDataTypeModule, typeCode).fromString
        if hicard == 1:
          params['locard'] = 0
          try:
            #params['defaultValue'] = (ff(defaultValue),)
            # 27/11/2014 Rasmus Fogh. This should be the value, no the tuple
            params['defaultValue'] = ff(defaultValue)
          except:
            print ("%s error in converting default value %s"
                   % (odPar.qualifiedName, defaultValue))
            raise
        else:
          # NB MetaParameters with hicard != 1 can *not* have defaults currently
          # This will raise an error on validation, so we might as well leave it
          # as is.
          try:
            params['defaultValue'] = tuple(map(ff,eval(defaultValue)))
          except:
            print ("%s error in converting default value %s"
                   % (odPar.qualifiedName, defaultValue))
            raise
 
      # create parameter
      MetaModel.MetaParameter(**params)
    
  else:
    # there should be no parameters - write warning and delete.
    for odPar in odUtil.toList(odOp.startParameters()):

      # get parameter name
      name = odPar.name
      print ("WARNING %s, opType %s has explicit parameter %s - deleting"
       % (metaOp, opType, name)
      )
      odOp.removeParameter(odPar)

def taggedValuesFromOd(odElement, elementType):
  """ get tag:value dictionary for an od Element,
  checking against localAllowedVals dictionary
  """
  
  # set up
  dd = {}
  taggedValues = {}
  extraTaggedValues = {}
  
  localAllowedVals = allowedTags[elementType]
  
  specialAllowedTags = ('constructorCode:', 'destructorCode:', 
                        'postDestructorCode:', 'typeCode:', 'code:')
  
  # compatibility for old to new MetaModel NBNB HACK
  compatibilityTaggedValues(odElement, elementType)
  
  # start processing
  odTagvals = odUtil.toList(odElement.startTaggedValues())
  for tt in odTagvals:
    dd[tt.name] = tt.getValue()
  
  for kk,vv in dd.items():
  
    if localAllowedVals.has_key(kk):
      allowedVals = localAllowedVals[kk]
      
      if allowedVals is None or vv in allowedVals:
        taggedValues[kk] = vv
      
      else:
        print 'localAllowedVals', localAllowedVals
        raise MemopsError("Illegal tagged value %s:%s for %s %s" 
                          % (kk, repr(vv), elementType, odElement.qualifiedName))
        
    else:
      # check for special tags
      for specialTag in specialAllowedTags:
        if kk.startswith(specialTag):
          allowedVals = localAllowedVals[specialTag]
      
          if allowedVals is None or vv in allowedVals:
            ss = specialTag[:-1]
            dd = taggedValues.get(ss)
            if dd is None:
              dd = taggedValues[ss] = {}
            dd[kk[len(specialTag):]] = vv
            
          else:
            raise MemopsError("Illegal tagged value %s:%s for %s %s" 
                              % (kk, repr(vv), elementType, odElement.qualifiedName))
          break
          
      else:
        # pass on as tagged value
        extraTaggedValues[kk] = vv
  
  #
  return taggedValues, extraTaggedValues


def compatibilityTaggedValues(odElement, elementType):
  """ Modify tagged values to update to new machinery (June 2006)
  
  NBNB HACK
  """
  
  # set up taggedValues dictionary
  taggedValues = {}
  for tt in odUtil.toList(odElement.startTaggedValues()):
    taggedValues[tt.name] = tt
  
  # rename tagged values
  for oldtag,newtag in renameTags.items():
    tv = taggedValues.get(oldtag)
    if tv is not None:
      odElement.setTaggedValueVal(newtag,tv.getValue())
      odElement.removeTaggedValue(tv)
  
  # skip tagged values
  for oldtag in skipTags:
    tv = taggedValues.get(oldtag)
    if tv is not None:
      odElement.removeTaggedValue(tv)


def addConstraints(metaObj, odObj):
  """ add constraints to metaObject given odObject
  returns True if constraints were found, otherwise False.
  """
  
  odCons = odUtil.toList(odObj.startConstraints())
  
  if odCons:
  
    for odCon in odCons:
      
      try:
        codeStubs = parseConstraint(odCon)
      
      except:
        print ("Error processing %s constraint :\n %s" % 
         (odObj.qualifiedName, odCon.name)
        )
        raise
      
      # get or set guid
      guid = getGuid(odCon)
          
      params = {'name':odCon.name, 'guid':guid, 'codeStubs':codeStubs}
    
      MetaModel.MetaConstraint(container=metaObj, **params)
      
    #
    return True
  
  else:
    return False


def parseConstraint(odCon):
  """Unpack constraint code tagged values.
  """
      
  body = odCon.getBody()
  # make sure lineseparator is '\n'
  ss = '\n'.join(body.splitlines())
  
  # parse body and make tagged values
  ll = ss.split('\n_\n')
  result = {}
  
  length = len(ll)
  if length <= 1:
    raise MemopsError("invalid code tagged value: \n%s\n" % ss)
  if length % 2:
    raise MemopsError(
     "code tagged value has wrong number of separators: \n%s\n" % ss
    )
    
  
  try:
    ii=0
    while ii < len(ll):
      tag = ll[ii].strip()
      value = ll[ii+1] 
      # next line to ensure multiline code tags end in newline
      if '\n' in value and '\n' != value[-1]:
        value += '\n'
       
      result[tag] = value
      ii += 2
  except:
    print(
     "Illegal value for code taggedvalue: \n%s" % ss
    )
    raise
  
  # compatibility for old to new MetaModel
  # NBNB HACK
  rewrite = False
  for tag,val in result.items():
    newTag = renameTags.get(tag)
    if newTag is not None:
      rewrite = True
      del result[tag]
      result[newTag] = val
  
  if rewrite:
    # Compatibility contd. NBNB HACK - change stored version of body
    ll = []
    for tag,val in result.items():
      # set up for writing
      ll.append(tag)
      ll.append(val)
    odCon.setBody('\n_\n'.join(ll))
  
  # convert tag names, removing 'code:'
  for tag,val in result.items():
    if tag[:5] == 'code:':
      del result[tag]
      result[tag[5:]] = val
  
  #
  return result

def odObjFromQualName(qname):
  """ find odObject given qualified name
  """
  
  result = od.get(qname)
  
  if result is None:
   raise MemopsError("No OdObject corresponding to %s" % qname)
   
  else:
    return result

def metaObjFromQualName(qname):
  """ find MetaObject given qualified name.
  If no success, remove default objectdomain prefix ('Model.Logical')
  and try again
  """
  
  try:
    # get using qualified name
    return rootPackage.metaObjFromQualName(qname)
    
  except MemopsError:
    pass
  
  except:
    print ("""An unexpected error occurred. Causes could be:
    1) Some modules but not others have been reloaded. 
       Try reloading all modules or restarting
    2) A coding error (bug).""")
    raise
    
  try:
    # get after first removing OdContainingPackageName
    nn = len(OdContainingPackageName) + 1
    if qname[:nn] == OdContainingPackageName + '.':
      return rootPackage.metaObjFromQualName(qname[nn:])
  
  except MemopsError:
    # no result. Raise error(using full qname)
    print("ERROR: No MetaObject corresponding to %s can be found" 
     % qname
    )
    raise
  
  # no result - raise error
  raise MemopsError("No MetaObject corresponding to %s can be found" % qname)


def getGuid(odElement):
  """ return guid tagged value
  
  If none is set, get a new globally unique ID and set it as a tagged value
  """
  guid = odElement.getTaggedValueVal('guid')
  
  if not guid:
    guid = newGuid()
    odElement.setTaggedValueVal('guid', guid)
  
  return guid


def parseMultiplicity(value):
  """ parse multiplicity string and return dictionary with values
  for hicard, locard, isOrdered, and isUnique (if set)
  
  Input string can contain:
  a single multiplicity string of the form 'n..m', 'n', '*', or 'n..*',
  where n and m are integers.
  The following strings as uniqueness and ordering indicators:
  '+u', '-u', '+o', '-o', 'unordered', 'ordered', 'nonunique', 'unique'.
  
  The mulitplicity string must precede the uniqueness and ordering indicators.
  NB Note that the strings '-unique' and '-ordered' are interpreted as
  'nonunique' and 'unordered' respectively.
  
  If string is empty an empty dictionary is returned
  """
  
  indicators = (
   ('+u','isUnique',True),
   ('unique','isUnique',True),
   ('-u','isUnique',False), 
   ('nonunique','isUnique',False), 
   ('+o','isOrdered',True),
   ('ordered','isOrdered',True),
   ('-o','isOrdered',False),
   ('unordered','isOrdered',False),
  )
  mTags = '0123456789*'
  
  result = {}
  
  if value:
  
    # find uniqueness and order info. NB it is deliberate that e.g.
    # 'unordered' overrides 'ordered'
    end = len(value)
    for ss,tag,val in indicators:
      ii = value.find(ss)
      if ii != -1:
        end = min(end,ii)
        result[tag] = val
 
    # restrict string to potential multiplicity indicator
    start = 0
    while start < end:
      if value[start] in mTags:
        break
      else:
        start += 1
 
    while end > start:
      jj = end - 1
      if value[jj] in mTags:
        break
      else:
        end = jj
 
    # find multiplicity
    locard,hicard = metaUtil.parseCardinality(value[start:end])
    result['locard'] = locard
    result['hicard'] = hicard
    
  #
  return result
