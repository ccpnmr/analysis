"""
======================COPYRIGHT/LICENSE START==========================

ApiGen.py: Code generation for CCPN framework

Copyright (C) 2005 Wayne Boucher (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../license/GPL.license
 
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
# major API generating script
# implements most high-level logic

# NBNB TBD allow for changeability == 'add_only'


from ccpncore.memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.metamodel import Util as metaUtil

from ccpncore.memops import Constants as memopsConstants
infinity = memopsConstants.infinity

from ccpncore.memops.scripts.core.LanguageInterface import LanguageInterface
from ccpncore.memops.scripts.core.TypeInterface import TypeInterface
from ccpncore.memops.TextWriter import TextWriter
from ccpncore.memops import Util as memopsUtil
from ccpncore.memops.metamodel.ModelTraverse import ModelTraverse

from ccpncore.memops.scripts.api.ApiInterface import ApiInterface
from ccpncore.memops.scripts.api.PermissionInterface import PermissionInterface
from ccpncore.memops.scripts.api.PersistenceInterface import PersistenceInterface
from ccpncore.memops.scripts.api.TransactionInterface import TransactionInterface
  
mandatoryAttributes = ('varNames',)

# Requires other writers also to be implemented in subclass
class ApiGen(ApiInterface, PermissionInterface, PersistenceInterface, 
             TransactionInterface, TypeInterface, LanguageInterface, 
             TextWriter, ModelTraverse):
  
  codeDirName = memopsConstants.apiCodeDir

  oldSelfVar = 'oldSelf'
  oldSelfVars = 'oldSelves'
  newSelfVars = 'newSelves'
  currentPrefix = 'current'
  siblingPrefix = 'sibling'

  ###########################################################################

  ###########################################################################

  def __init__(self):
    
    # init handling
    super(ApiGen, self).__init__()
    
    for tag in mandatoryAttributes:
      if not hasattr(self, tag):
        raise MemopsError(" ApiGen lacks mandatory %s attribute" % tag)
    
    # set standard collection parameters from Operation parametere data
    self.stdCollectionParams = dd1 = {}
    
    for (opType, parName) in (
     ('checkDelete', 'objsToBeChecked'),
     ('checkDelete', 'objsToBeDeleted'),
    ):
      dd1[parName] = dd2 = self.getStdCollectionParams(opType, parName)
      dd2['collection'] = parName

    # types
    pp = self.modelPortal.topPackage
    impl = pp.metaObjFromQualName(self.implPackageName)
    self.booleanType = self.elementVarType(impl.getElement('Boolean'))
    self.intType = self.elementVarType(impl.getElement('Int'))
    self.anyType = self.elementVarType(impl.getElement('Any'))
    self.stringType = self.elementVarType(impl.getElement('String'))
    self.stringKeyDictType = self.elementVarType(impl.getElement(
                                                'StringKeyDict'))
    self.dictType = self.elementVarType(impl.getElement('Dict'))
    self.listPars = {'varType':self.anyType, 'isUnique':False, 'isOrdered':True}

  ###########################################################################

  ###########################################################################
  ###
  ### code overriding ModelTraverse
  ###
  ###########################################################################

  ###########################################################################

  def processBranchPackage(self, package):
    """ processing actions for branch package
    """
    
    packageDirName = self.getObjDirName(package)
    
    if package in self.modelPortal.twigPackages():
      self.clearOutDir(packageDirName)
    
    # must be called after
    self.createDir(packageDirName)
    
    super(ApiGen, self).processBranchPackage(package)
      
    
  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def initOperation(self, op, inClass):

    if op.container is not inClass:
      return
    
    else:
      self.writeStartFunc(op, inClass)

  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def processOperation(self, op, inClass):

    opType = op.opType
    
    # special trick for writing getParent functions:
    oldParent = op.target
    if (opType == 'get' and oldParent.name == self.varNames['parent']
        and oldParent.container is not oldParent.valueType):
      # now the getParent code will be generated
      # the same as for the real parentRole.
      # the last if excludes the MemopsRoot parent
      op.target = op.container.parentRole
    else:
      oldParent = None
    
    if op.container is not inClass:
      self.writeInheritedOperation(op, inClass)
    elif op.isAbstract:
      self.writeAbstractOperation(op, inClass)
    elif opType == 'init':
      self.writeInitClass(op, inClass)
    elif opType == 'new':
      self.writeFactoryFunction(op, inClass)
    elif opType in ('get', 'sorted', 'findFirst', 'findAll', 
                    'getByKey', 'getFullKey', 'getLocalKey'):
      self.writeGetElement(op, inClass)
    elif opType == 'getAttr':
      self.writeGetAttr(op, inClass)
    elif opType in ('set', 'add', 'remove'):
      self.writeModifyElement(op, inClass)
    elif opType == 'setAttr':
      self.writeSetAttr(op, inClass)
    elif opType == 'fullDelete':
      self.writeDelete(op, inClass)
    elif opType == 'checkDelete':
      self.writePreDelete(op, inClass)
    elif opType == 'singleDelete':
      self.writeDoDelete(op, inClass)
    elif opType in ('checkValid', 'checkAllValid'):
      self.writeCheckClass(op, inClass)
    elif opType == 'clone':
      self.writeCloneObj(op, inClass)
    elif opType in self.operationData:
      self.writeExternalOp(op, inClass)
    else:
      raise MemopsError('unknown or invalid opType "%s" for %s'
                                  % (opType,op.qualifiedName()))
                                  
    # restore after getParent trick:
    if oldParent is not None:
      op.target = oldParent

  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def endOperation(self, op, inClass):
    
    if op.container is not inClass:
      return
    
    else:
      self.writeEndFunc(op, inClass)

  ###########################################################################

  ###########################################################################
  ###
  ### internal code
  ###
  ###########################################################################

  ###########################################################################

  # 
  def writeInheritedOperation(self, op, inClass):

    # does nothing by default, can be overridden in subclass
    pass

  ###########################################################################

  ###########################################################################
  
  def writeAbstractOperation(self, op, inClass):
    """ write abstract operation i.e. a 'must be overridden' error
    """
    
    self.raiseApiError(
     "%s should never be called - must be overridden in subclass" 
     % self.getFuncname(op), self.varNames['self'], inOp=op
    )
    
  ###########################################################################

  ###########################################################################
    
  def writeCloneObj(self, op, inClass):
    """ write 'clone object' function for DataObjTypes
    """

    if not op.isImplicit:
      # TBD: are there any examples of below? 
      # NO. Discouraged. Consider changes if a case arises.
      self.writeExternalOp(op, inClass)
      return
    
    if not isinstance(inClass, MetaModel.MetaDataObjType):
      raise MemopsError("writeCloneObj called for non-DAtaObjType %s" % inClass)
    
    dictVar = self.varNames['attrlinks']
    self.newDict(dictVar=dictVar, keyType=self.stringType, needDeclType=True)
    
    for attr in inClass.getAllAttributes():
      if not attr.isDerived and not attr.isImplementation:
        ss = self.getValue(self.varNames['self'], attr, needVarType=False, 
                           lenient=True, inClass=inClass)
        self.setDictEntry(dictVar, self.toLiteral(attr.name), ss)
    
    self.implCloneObj(op, inClass)
    
    
    # get constructor op
    # NB this works because dictVar 'attrlinks' is the name of the normal
    # keyword:value input dict for the constructor
    ll = [x for x in inClass.operations 
          if x.opType == 'init' and x.opSubType is None]
    constructorOp = ll[0]
    params = self.getFuncParams(constructorOp, defineFunc=False)

    self.returnStatement(self.callConstructor(constructorOp, inClass, params))
    
    
    
  ###########################################################################

  ###########################################################################
    
  def implCloneObj(self, op, inClass):
    """ write implementation-specific part of 'clone object' function 
    for DataObjTypes
    """
    dictVar = self.varNames['attrlinks']
    attrDictVar = self.varNames['attrDict']
    keyVar = 'kk'
    self.startLoopOverDictKeys(attrDictVar, keyVar, varType=self.stringType)
    ss = self.getDictEntry(attrDictVar, keyVar)
    self.setDictEntry(dictVar, keyVar, ss)
    self.endLoop()
    
  ###########################################################################

  ###########################################################################
    
  def writeInitClass(self, op, inClass):

    if not op.isImplicit:
      # TBD: are there any examples of below? 
      # NO. Discouraged. Consider changes if a case arises.
      # Note that have extra hand code allowed via constructorCodeStubs
      self.writeExternalOp(op, inClass)
      return
    
    if isinstance(inClass, MetaModel.MetaClass):
      parentRole = inClass.parentRole
    else:
      # NBNB TBD, first try - unlikely to last
      parentRole = None

    if parentRole is not None: 
      self.setValue(self.varNames['self'], parentRole, 
                    value=self.varNames['parent'])
      self.checkComparableInstance(inClass, self.varNames['parent'], parentRole)
      self.checkIsNotDeleted(op, inClass, self.varNames['parent'])

    # implementation specific initialization
    self.writeInitConstructor(op, inClass)
    
    self.getOverride(op, inClass)

    self.checkPermission(op, inClass)

    self.startTransaction(op, inClass)

    self.writeInitDefaults(op, inClass)
      
    self.writeSetAttrLinks(op, inClass)
    
    if isinstance(inClass, MetaModel.MetaClass):
      self.writeInitSerial(op, inClass)
    
    if parentRole is not None:
      self.writeAddChildToParent(self.varNames['self'], 
                                 self.varNames['parent'], parentRole, inClass)
    
    # add extra class constructor code, if any
    self.writeConstructorCode(op, inClass)
    
    # check validity, if required, and reset 'current' link
    self.startIf(self.shouldDoInitChecks(op, inClass))
    self.stdCallFunc(self.varNames['self'], 'checkValid')
    self.endIf()
    
    # set currentTopObj link to this one
    if self.topObject in inClass.getAllSupertypes():
      parRole = inClass.parentRole
      clz = parRole.container
      memopsRoot = parRole.valueType
      
      # get currentLink
      roles = memopsRoot.getAllRoles()
      for curLink in roles:
        if curLink.valueType is clz and curLink.name.startswith('current'):
          break
      else:
        raise MemopsError("no 'currentTopObj' link found for %s" % inClass)
      
      self.startIf(self.logicalOp(
       self.varNames['notIsReading'], 'or', 
       self.valueIsNone(self.getValue(self.varNames['root'], curLink, 
                                         lenient=True))
      ))
      self.setValue(self.varNames['root'], curLink, self.varNames['self'])
      self.endIf()
    

    self.endTransaction(op, inClass)

    # TBD: should this be before endTransaction?
    self.doNotifies(op, inClass)

  ###########################################################################

  ###########################################################################

  def writeInitDefaults(self, op, inClass):
    
    self.writeNewline()

    for attr in inClass.getAllAttributes():
      if not attr.isDerived and not attr.isImplementation:
        self.writeInitAttrDefault(attr)
    
    
    if isinstance(inClass, MetaModel.MetaClass):
      for role in inClass.getAllRoles():
        if (not role.isDerived  and not role.isImplementation 
            and role.hierarchy != metaConstants.parent_hierarchy):
          self.writeInitRoleDefault(role)

  ###########################################################################

  ###########################################################################

  def writeInitAttrDefault(self, attr):
    
    default = attr.defaultValue
    
    if attr.hicard == 1:
      if default:
        value = self.toLiteral(default[0])
      else:
        value = self.noneValue
      self.setValue(self.varNames['self'], attr, value=value)
      
    else:
      self.writeInitCollection(attr, initValues=attr.defaultValue)

  ###########################################################################

  ###########################################################################

  def writeInitRoleDefault(self, role):

    if role.hicard == 1:
      self.setValue(self.varNames['self'], role, value=None)
      
    elif role.hierarchy == metaConstants.child_hierarchy:
      self.setValue(self.varNames['self'], role,
                    value=self.newDict(valueType=self.elementVarType(role)))
        
    else:
      self.writeInitCollection(role)

  ###########################################################################

  ###########################################################################

  def writeInitCollection(self, element, initValues = None):

    if initValues:
      self.startBlock()
      self.defineVar('defaultValues', varType=self.implementationType(element))
      self.newCollection('defaultValues', initValues=initValues,
                         **self.collectionParams(element))
      self.setValue(self.varNames['self'], element, value='defaultValues')
      self.endBlock()
    else:
      self.setValue(self.varNames['self'], element,
                    value=self.newCollection(None, **self.collectionParams(element)))

  ###########################################################################

  ###########################################################################

  def writeConstructorCode(self, op, inClass):
  
    if inClass.constructorCodeStubs:
      self.writeHandCode(inClass, 'constructorCodeStubs')

  ###########################################################################

  ###########################################################################

  def writeDelete(self, op, inClass):
  
    self.setVar(self.varNames['notInConstructor'], 
     self.negate(self.getImplAttr(self.varNames['self'], 'inConstructor', inClass)), 
     self.booleanType
    )
                
    self.getOverride(op, inClass)

    self.callPreDeletes(op, inClass)

    self.checkPermission(op, inClass)

    self.checkIsNotDeleted(op, inClass)

    self.startTransaction(op, inClass)

    self.callDoDeletes(op, inClass)

    self.endTransaction(op, inClass)

    # TBD: should this be before endTransaction?
    self.startIf(self.varNames['notOverride'])
    self.startIf(self.varNames['notInConstructor'])
    self.doNotifies(op, inClass)
    self.endIf()
    self.endIf()

  ###########################################################################

  ###########################################################################

  def writePreDelete(self, op, inClass):

    self.addCollection(self.varNames['self'], **self.stdCollectionParams['objsToBeDeleted'])

    # add extra class destructor code, if any
    # TBD: assumes this is only checking code, not doing code
    self.writeHandCode(inClass, 'destructorCodeStubs')

    # check all links

    for role in inClass.getAllRoles():
      self.writePreDeleteRole(op, inClass, role)

    self.writeImplPreDelete(op, inClass)

  ###########################################################################

  ###########################################################################

  def writePreDeleteRole(self, op, inClass, role):
    
    thatVar = role.baseName
    thoseVar = role.name
    if thoseVar == thatVar:
      thoseVar += '_s'
    
    if role.isDerived:
      return

    otherRole = role.otherRole
    if otherRole is None:
      return
    
    package = inClass.container
    otherPackage =  otherRole.container.container
    if package is otherPackage and otherRole.locard == 0:
      return
    
    self.startBlock() 
    # necessary to shield internal parameters from name clashes
    
    if role.hicard == 1:
      self.getValue(self.varNames['self'], role, thatVar, inClass=inClass)
      self.startIf(self.valueIsNotNone(thatVar))
      
      # check that we are allowed to do this
      if role.noDeleteIfSet:
        self.raiseApiError(
         "Object can not be deleted while %s is set" % role.name,
         self.varNames['self'], inOp=op
        )
        
      else:
        # look for cascading deletes
        # NB either branch of the 'or' catches child links
        if (otherRole.hicard == otherRole.locard or
         (role.hierarchy != metaConstants.parent_hierarchy
         and otherRole.changeability == metaConstants.frozen)
        ):
          self.checkObjToBeDeleted(thatVar)

        elif otherRole.locard > 0:
          # locard > 0 and locard < hicard, and hicard != 1
          self.checkLinkToBeDeleted(op, inClass, otherRole, thatVar)
 
        self.writeImplPreDelete(op, inClass, role)

      self.endIf() # self.valueIsNotNone(self.thatVar)

    else:
      # role.hicard != 1
      self.getValue(self.varNames['self'], role, thoseVar, 
                    convertCollection=False, inClass=inClass)
      
      
      if role.noDeleteIfSet:
        # check that we are allowed to do this
        self.startIf(self.collectionIsNotEmpty(thoseVar, 
                                               **self.collectionParams(role)))
        self.raiseApiError(
         "Object can not be deleted while %s is set" % role.name,
         self.varNames['self'], inOp=op
        )
        self.endIf()
        
      else:
        # look for cascading deletes
        if (otherRole.hicard == otherRole.locard or
            otherRole.changeability == metaConstants.frozen):

          self.startLoop(thatVar, thoseVar, **self.collectionParams(role))
          self.checkObjToBeDeleted(thatVar)
          self.endLoop()
 
        elif otherRole.locard > 0:

          # locard > 0 and locard < hicard, and hicard != 1
          self.startLoop(thatVar, thoseVar, **self.collectionParams(role))
          self.checkLinkToBeDeleted(op, inClass, otherRole, thatVar)
          self.endLoop()

        else:

          # TBD: can we guarantee we don't need below?
          self.noStatement()

        self.writeImplPreDelete(op, inClass, role)

    self.endBlock()
    
  ###########################################################################

  ###########################################################################

  def checkObjToBeDeleted(self, thatVar):
    
    self.startIf(self.negate(
     self.isInCollection(thatVar,**self.stdCollectionParams['objsToBeDeleted']))
    )
    self.addCollection(thatVar, **self.stdCollectionParams['objsToBeDeleted'])
    self.addCollection(thatVar, **self.stdCollectionParams['objsToBeChecked'])
    self.endIf()
      
  ###########################################################################

  ###########################################################################

  def checkLinkToBeDeleted(self, op, inClass, otherRole, thatVar):

    # TBD: there are several one-off language functions used here
    #      an alternative would be to put this in PyApiGen, etc

    self.startIf(self.negate(
     self.isInCollection(thatVar, **self.stdCollectionParams['objsToBeDeleted']))
    )
    self.getValue(thatVar, otherRole, 'backlink', inClass=inClass)
    self.setCheckLinkKey('key', thatVar, otherRole)
    self.setVar('nFound', self.getDictEntry(self.varNames['linkCounter'], 'key'),
                varType=self.intType, castType=self.intType)
    self.startIf(self.valueIsNone('nFound'))
    self.setVar('nFound', 1)
    self.elseIf()
    self.incrementInteger('nFound')
    self.removeDictEntry(self.varNames['linkCounter'], 'key')
    self.endIf()

    ll = self.lenCollection('backlink', **self.collectionParams(otherRole))
    ll = self.subtractIntegers(ll, 'nFound')
    self.startIf(self.comparison(ll, '<', otherRole.locard))
    self.addCollection(thatVar, **self.stdCollectionParams['objsToBeDeleted'])
    self.addCollection(thatVar, **self.stdCollectionParams['objsToBeChecked'])
    self.elseIf()
    self.setDictEntry(self.varNames['linkCounter'], 'key', 'nFound')
    self.endIf()

    self.endIf()

  ###########################################################################

  ###########################################################################

  def writeDoDelete(self, op, inClass):

    self.setImplAttr(self.varNames['self'], 'isDeleted', True)
    
    # add extra class destructor code, if any
    # TBD: this is for code that actuall changes data
    self.writeHandCode(inClass, 'postDestructorCodeStubs')
    
    parentRole = inClass.parentRole
    
    if self.topObject in inClass.getAllSupertypes():
      BaseName = memopsUtil.upperFirst(parentRole.otherRole.baseName)
      curRole = parentRole.valueType.getElement('current' + BaseName)
      self.getValue(self.varNames['self'], parentRole, var=parentRole.baseName, 
                    lenient=True, inClass=inClass)
      ss = self.getValue(parentRole.baseName, curRole, lenient=True,
                         inClass=inClass)
      self.startIf(self.comparison(self.varNames['self'], 'is', ss))
      self.setValue(parentRole.baseName, curRole, self.toLiteral(None))
      self.endIf()
    
    for role in inClass.getAllRoles():
      if role is not parentRole:
        self.writeDoDeleteRole(op, inClass, role)
    
    # do parentRole last. It is the most vulnerable to raising errors
    # so better clean up the easy stuff first
    self.writeDoDeleteRole(op, inClass, parentRole)
    
    
    self.writeImplDoDelete(op, inClass)

  ###########################################################################

  ###########################################################################

  def writeDoDeleteRole(self, op, inClass, role):

    otherRole = role.otherRole
    
    if role.hierarchy == metaConstants.child_hierarchy:
      # always deleted
      return
      
    elif otherRole is None:
      # no action needed
      return
    
    elif role.isDerived:
      # no action needed
      return
    
    elif otherRole.changeability == metaConstants.frozen:
      # always deleted
      return
    
    self.startBlock() 
    # necessary to shield internal parameters from name clashes
    
    thatVar = role.baseName
    var = otherRole.name
    if var == thatVar:
      var += '_2'

    if otherRole.hicard == 1:
      
      if otherRole.locard != 1:
        # maybe deleted
        if role.hicard == 1:
          # ONE-TO-ONE

          #self.write('HERE1')
          self.getValue(self.varNames['self'], role, thatVar, lenient=True,
                        inClass=inClass)
          self.startIf(self.logicalOp(self.valueIsNotNone(thatVar), 'and', 
           self.negate(self.isInCollection(thatVar, 
           **self.stdCollectionParams['objsToBeDeleted'])))
          )
          self.setValue(thatVar, otherRole, value=None)
          self.endIf() 

        else:
          # ONE-TO-MANY
 
          #self.write('HERE2')
          self.startLoop(thatVar, self.getValue(self.varNames['self'], 
           role, lenient=True, inClass=inClass), **self.collectionParams(role)
          )
          self.startIf(self.negate(self.isInCollection(thatVar, 
                       **self.stdCollectionParams['objsToBeDeleted'])))
          self.setValue(thatVar, otherRole, value=None)
          self.endIf() 
          self.endLoop()

    else: # otherRole.hicard != 1
    
      if otherRole.locard != otherRole.hicard:
        # maybe deleted
      
        if role.hicard == 1:
          # MANY-TO-ONE

          #self.write('HERE3')
          self.getValue(self.varNames['self'], role, thatVar, lenient=True,
                        inClass=inClass)
          self.startIf(self.logicalOp(self.valueIsNotNone(thatVar), 'and', 
           self.negate(self.isInCollection(thatVar, 
           **self.stdCollectionParams['objsToBeDeleted'])))
          )
          self.getValue(thatVar, otherRole, var, lenient=True, inClass=inClass)
          self.removeValue(thatVar, otherRole, self.varNames['self'], var)
          self.endIf() 

        else:
          # MANY-TO-MANY
 
          #self.write('HERE4')
          self.startLoop(thatVar, self.getValue(self.varNames['self'], role,
           lenient=True, inClass=inClass), **self.collectionParams(role)
          )
          self.startIf(self.negate(self.isInCollection(
           thatVar, **self.stdCollectionParams['objsToBeDeleted']))
          )
          self.getValue(thatVar, otherRole, var, lenient=True, inClass=inClass)
          self.removeValue(thatVar, otherRole, self.varNames['self'], var)
          self.endIf() 
          self.endLoop()
          
    self.endBlock() 

  ###########################################################################

  ###########################################################################

  def callPreDeletes(self, op, inClass):

    # set up
    self.writeNewline()
    self.writeComment('objects to be deleted')
    self.newCollection(needDeclType=True, **self.stdCollectionParams['objsToBeDeleted'])

    self.writeComment('objects still to be checked for cascading delete'
                      ' (each object to be deleted gets checked)')
    self.newCollection(needDeclType=True, **self.stdCollectionParams['objsToBeChecked'])

    self.writeComment('counter keyed on (obj, roleName) for how many objects'
                      ' at other end of link are to be deleted')
    self.newDict(self.varNames['linkCounter'], needDeclType=True)

    self.writeInitPreDelete(op, inClass)

    self.writeNewline()
    self.addCollection(self.varNames['self'], 
                       **self.stdCollectionParams['objsToBeChecked'])

    # find objects to delete
    self.startWhile(self.comparison(
     self.lenCollection(**self.stdCollectionParams['objsToBeChecked']), '>', 0)
    )
    self.defineVar('obj', self.elementVarType(self.baseClass))
    self.popCollection('obj', **self.stdCollectionParams['objsToBeChecked'])
    self.stdCallFunc('obj', 'checkDelete')
    self.endWhile()  

  ###########################################################################

  ###########################################################################

  def callDoDeletes(self, op, inClass):

    self.startLoop('obj', **self.stdCollectionParams['objsToBeDeleted'])
    self.stdCallFunc('obj', 'singleDelete')
    self.endLoop()

  ###########################################################################

  ###########################################################################

  def writeHandCode(self, inClass, codeDictName):
    
    codeDict = getattr(inClass,codeDictName)
    if codeDict:
      handCodeKey = self.modelFlavours['language']
      code = codeDict.get(handCodeKey)
      if code is None:
        raise MemopsError("Missing special tag %s for Class %s %s" % 
                          (handCodeKey, inClass.qualifiedName(), codeDictName))
      else:
        ll = ['',''] + code.splitlines() + ['']
        self.write('\n'.join(ll))

  ###########################################################################

  ###########################################################################

  def writeStartFunc(self, op, inClass):
    """ write start of (most) functions
    """

    self.errorMsg = '.%s' % (self.getFuncname(op))
    self.defineFunc(op)

  ###########################################################################

  ###########################################################################

  def writeEndFunc(self, op, inClass):
    """ write end of (most) functions
    """

    self.errorMsg = ''
    self.endFunc()

  ###########################################################################

  ###########################################################################

  def writeGetElement(self, op, inClass):
    """ Write element queries (get, findFirst, findAll)
    """
  
    opType = op.opType
    target = op.target

    self.checkPermission(op, inClass)

    resultVar = self.varNames['result']
    
    if opType == 'getFullKey':
      elem = self.anyObject
      resultVarType = self.collectionType(elem, isUnique=False, isOrdered=True)
    
    elif opType == 'getLocalKey':
      resultVarType = self.elementVarType(op.getElement('result').valueType)
    
    elif opType == 'sorted':
      ###resultVarType = self.collectionType(target, isUnique=True, isOrdered=True)
      valueType = self.getOpValueType(op)
      resultVarType = self.collectionType(valueType, isUnique=True, isOrdered=True)
                                          
    elif opType == 'getByKey':
      resultVarType = self.elementVarType(inClass)
                                          
    elif opType == 'findFirst' or target.hicard == 1:
      resultVarType = self.elementVarType(target)
      
    elif isinstance(target, MetaModel.MetaRole):
      valueType = self.getOpValueType(op)
      resultVarType = self.collectionType(valueType, isUnique=target.isUnique, isOrdered=target.isOrdered)

    else:
      resultVarType = self.collectionType(target)
      
    ### TBD: does not belong in some cases (e.g. DataSource.getDataDims, etc.)
    ### TBD: but it is in other cases
    ###self.writeComment('TBD: writeGetElement self.defineVar')
    self.defineVar(resultVar, varType=resultVarType)


    self.startTransaction(op, inClass)

    if not op.isImplicit:
      self.writeExternalCode(op, inClass)
    elif opType == 'get':
      self.writeGetValue(op, inClass)
    elif opType == 'getByKey':
      self.writeGetByKey(op, inClass)
    elif opType == 'getFullKey':
      self.writeGetFullKey(op, inClass)
    elif opType == 'getLocalKey':
      self.writeGetLocalKey(op, inClass)
    elif opType == 'sorted':
      self.writeSortedValue(op, inClass)
    elif opType == 'findFirst':
      self.writeFindFirst(op, inClass)
    elif opType == 'findAll':
      self.writeFindAll(op, inClass)

    self.endTransaction(op, inClass)

    self.returnStatement(resultVar)

  ###########################################################################

  ###########################################################################

  def writeGetValue(self, op, inClass):
    """ write element getter
    """
    
    element = op.target
    resultVar = self.varNames['result']
    tempVar = self.varNames['tempVar']
    selfVar = self.varNames['self']
    
    var = resultVar
    if element.isImplementation:
      if isinstance(element, MetaModel.MetaAttribute):
        self.setVar(resultVar, self.getImplAttr(selfVar, element.name, inClass))
      else:
        self.getImplLink(selfVar, element.name, resultVar, inClass)
        
    else:
      # NB convertCollection=False is correct for child links
      # and is ignored in all other cases
      if element.hicard != 1:
        var = tempVar
        needVarType = True
      else:
        needVarType = False
      ## TBD NBNB removed needVarType because seem to need it
      
      self.getValue(selfVar, element, var,
                    convertCollection=False, inClass=inClass, 
                    needVarType=needVarType)

    if element.hicard != 1:
      dd = self.collectionParams(element)
      dd['varType'] = self.elementVarType(self.getOpValueType(op))
      supertype = op.target.container.supertype
      if supertype and supertype.getOperation(op.name):
        useAdd = True
      else:
        useAdd = False
      self.newCollection(resultVar, isFrozen=True, initValues=var, useAdd=useAdd, **dd)
      ###                   **self.collectionParams(element))
    
    
  ###########################################################################

  ###########################################################################

  def writeFindFirst(self, op, inClass):
    """ write findFirst
    """
    
    # setup
    role = op.target
    resultVar = self.varNames['result']
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
    collectionParams = self.collectionParams(role)
    
    self.setVar(self.varNames['nConditions'], 
                self.lenDict(self.varNames['conditions']), 
                varType=self.intType)
    self.startIf(self.comparison(self.varNames['nConditions'], '==',
                 self.toLiteral(0)))
                 
    self.getValue(self.varNames['self'], role, currentVar, 
                  convertCollection=False, inClass=inClass)
    self.startIf(self.collectionIsNotEmpty(currentVar, **collectionParams))
    self.getCollection(resultVar, currentVar, **collectionParams)
    self.elseIf()
    self.setVar(resultVar, self.noneValue)
    self.endIf()
    
    self.writeNewline()
    self.elseIf()
    self.checkFindFirst(op, inClass)
    self.endIf()


  ###########################################################################

  ###########################################################################

  def writeFindAll(self, op, inClass):
    """ write findAll
    """
    
    # setup
    role = op.target
    resultVar = self.varNames['result']
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
    
    
    self.setVar(self.varNames['nConditions'], 
                self.lenDict(self.varNames['conditions']), 
                varType=self.intType)
    self.startIf(self.comparison(self.varNames['nConditions'], '==',
                 self.toLiteral(0)))
                 
    self.getValue(self.varNames['self'], role, currentVar, 
                  convertCollection=False, inClass=inClass)
    dd = dict(varType=self.elementVarType(self.getOpValueType(op)), isUnique=role.isUnique, isOrdered=role.isOrdered)
    if role.container.supertype.getOperation(op.name):
      useAdd = True
    else:
      useAdd = False
    self.newCollection(resultVar, initValues=currentVar, useAdd=useAdd, **dd)
    ###                   **self.collectionParams(role))
    
    self.writeNewline()
    self.elseIf()
    self.checkFindAll(op, inClass)
    self.endIf()

  ###########################################################################

  ###########################################################################
  
  def writeGetByKey(self, op, inClass):
    """ write getByKey
    """
    raise MemopsError(" writeGetByKey must be overridden in subclass")

  ###########################################################################

  ###########################################################################
  
  def writeGetLocalKey(self, op, inClass):
    """ write getLocalKey
    """
    raise MemopsError(" writeGetLocalKey must be overridden in subclass")

  ###########################################################################

  ###########################################################################
  
  def writeGetFullKey(self, op, inClass):
    """ write getFullKey
    """
    
    # set up. First parent list
    parents = [op.container]
    for pp in parents:
      pr = pp.parentRole
      if pr is None:
        break
      else:
        parents.append(pr.valueType)
    
    # remove MemopsRoot
    parents.pop()
    
    nParents = len(parents)
    
    # create results collection
    self.newCollection(self.varNames['result'], **self.listPars)
    
    if not nParents:
      # op.container has no parents, must be a MemopsRoot
      return
      
    else:
      # make varNames list
      varNames = ([self.varNames['self']] +
                  ['obj%s' % (nParents - ii) for ii in range(1,nParents)])
 
      # create parents, going upwards from self
      self.writeNewline()
      self.startBlock()
      for jj in range(1,nParents):
        ii = jj - 1
        self.defineVar(varNames[jj], self.elementVarType(parents[jj]))
        self.getImplLink(varNames[ii], 'parent', varNames[jj], parents[ii])
 
      # create key, now going downwards from top
      self.writeNewline()
      parents.reverse()
      varNames.reverse()
      self.addKeyToResult(owner=varNames[0], ownerClass=parents[0], 
                          checkGuid=True, inClass=inClass)
      for ii in range(1,nParents):
        self.addKeyToResult(owner=varNames[ii], ownerClass=parents[ii],
                            inClass=inClass)
 
      self.endBlock()
      self.writeNewline()
    
  ###########################################################################

  ###########################################################################
  
  def addKeyToResult(self, owner, ownerClass, checkGuid=False, inClass=None):
    """ Internal function
    """
    
    if checkGuid:
      tag = 'guid'
      elem = ownerClass.getElement(tag)
      if elem is None:
        # no guid
        checkGuid = False
      else:
        self.startIf(self.boolean('useGuid'))
        ss = self.getValue(owner, elem, needVarType=False, lenient=True, 
                           inClass=inClass)
        self.addCollection(ss, self.varNames['result'], **self.listPars)
        self.elseIf()
    
    keyNames = ownerClass.keyNames
    
    for tag in keyNames:
      elem = ownerClass.getElement(tag)
      ss = self.getValue(owner, elem, needVarType=False, lenient=True, 
                         inClass=inClass)
      if elem.hicard == 1:
        self.addCollection(ss, self.varNames['result'], **self.listPars)
      else:
        self.startLoop('xx', ss, **self.collectionParams(elem))
        self.addCollection('xx', self.varNames['result'], **self.listPars)
        self.endLoop()
    
    if checkGuid:
      self.endIf()
    
  ###########################################################################

  ###########################################################################

  def writeModifyElement(self, op, inClass):
    """ Write all modifier functions (set, add, remove)
    """

    opType = op.opType
    element = op.target
    
    doInstance = (opType in ('add','remove'))
    
    var = self.valueVar(element, doInstance=doInstance)
    currentVar = self.valueVar(element, prefix=self.currentPrefix)

    self.checkCompatibleVar(inClass, element, doInstance=doInstance)

    # sets up currentVar
    self.setupModifyFuncVars(op, inClass)

    self.checkPermission(op, inClass)

    self.checkIsNotDeleted(op, inClass)

    if opType == 'set':
      self.checkIfValueUnchanged(element)
    elif opType == 'add':
      self.checkValueIsNotInList(element)
    elif opType == 'remove':
      self.checkValueIsInList(element)
    else:
      raise MemopsError('unknown opType "%s for %s"'
                                  % (opType,op.qualifiedName()))
    
    if not element.isDerived:
      self.checkModifyConstraints(op, inClass)

    self.startTransaction(op, inClass)

    if not op.isImplicit:
      self.writeExternalCode(op, inClass)
    else:
      # TBD: this is not complete for roles
      if opType == 'set':
        if isinstance(element, MetaModel.MetaRole):
          otherRole = element.otherRole
          if otherRole:
            # in this case have more to do, separate out by cardinality
            if element.hicard == 1:
              if otherRole.hicard == 1:
                self.writeSetRole11(op, inClass)
              else:
                self.writeSetRole1N(op, inClass)
            else:
              if otherRole.hicard == 1:
                self.writeSetRoleN1(op, inClass)
              else:
                self.writeSetRoleNN(op, inClass)
                
        if element.name == metaConstants.serial_attribute:
          self.setSerialValue(inClass, value=var)
        else:
          self.setValue(self.varNames['self'], element, value=var)

      elif opType == 'add':
    
        if element.isDerived:
          # 15/3/2011 Rasmus Fogh. Added set command, 
          # so the modified local list is actually set back into the data
          # 21/2/12 Rasmus Fogh, 
          # modified to convert currentVar to modifiable collection
          newColVar = self.valueVar(element, prefix='new')
          self.newCollection(newColVar, initValues=currentVar, 
                             **self.collectionParams(element))
          self.addValue(self.varNames['self'], element, var, newColVar)
          funcname = self.getFuncname(metaUtil.getOperation(element, 'set'))
          self.callFunc(funcname, self.varNames['self'], newColVar)
        
        else:
          if isinstance(element, MetaModel.MetaRole):
            # Not needed for derived, 
            # where the 'set' func call above does all modification
            otherRole = element.otherRole
            if otherRole:
              if otherRole.hicard == 1:
                self.writeAddRoleN1(op, inClass)
              else:
                self.writeAddRoleNN(op, inClass)
                
          self.addValue(self.varNames['self'], element, var, currentVar)

      elif opType == 'remove':
    
        if element.isDerived:
          # 15/3/2011 Rasmus Fogh. Added set command, 
          # so the modified local list is actually set back into the data
          # 21/2/12 Rasmus Fogh, 
          # modified to convert currentVar to modifiable collection
          newColVar = self.valueVar(element, prefix='new')
          self.newCollection(newColVar, initValues=currentVar, 
                             **self.collectionParams(element))
          self.removeValue(self.varNames['self'], element, var, newColVar)
          funcname = self.getFuncname(metaUtil.getOperation(element, 'set'))
          self.callFunc(funcname, self.varNames['self'], newColVar)
        
        else:
          if isinstance(element, MetaModel.MetaRole):
            # Not needed for derived, 
            # where the 'set' func call above does all modification
            otherRole = element.otherRole
            if otherRole:
              if otherRole.hicard == 1:
                self.writeRemoveRoleN1(op, inClass)
              else:
                self.writeRemoveRoleNN(op, inClass)
                
          self.removeValue(self.varNames['self'], element, var, currentVar)
        
      else:
        raise MemopsError('unknown opType "%s for %s"'
                                    % (opType,op.qualifiedName()))

    # Note: below in File case sets storage.isModified = True
    self.endTransaction(op, inClass)

    # TBD: should this be before endTransaction?
    if not element.isDerived:
      self.doNotifies(op, inClass)

  ###########################################################################

  ###########################################################################

  def addValue(self, owner, element, var, collection):

    self.addCollection(var, collection, **self.collectionParams(element))
    self.setValue(owner, element, value=collection)

  ###########################################################################

  ###########################################################################

  def removeValue(self, owner, element, var, collection):

    self.removeCollection(var, collection, **self.collectionParams(element))
    self.setValue(owner, element, value=collection)

  ###########################################################################

  ###########################################################################

  def writeSetRole11(self, op, inClass):

    role = op.target
    otherRole = role.otherRole

    var = self.valueVar(role)
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
 
    # TBD: if otherRole.locard = 1 and have done cardinality check
    # then know that currentVar = None at this point so lines below never done
    # so could do better...
    self.startIf(self.valueIsNotNone(currentVar))
    self.setValue(currentVar, otherRole, value=None)
    self.endIf()

    self.startIf(self.valueIsNotNone(var))
    # TBD: under what conditions has self.oldSelfVar already been set?
    # (in which case the getValue would not be needed)
    self.getValue(var, otherRole, self.oldSelfVar, lenient=True, 
                  inClass=inClass, needVarType=False)
    self.startIf(self.valueIsNotNone(self.oldSelfVar))
    self.setValue(self.oldSelfVar, role, value=None)
    self.endIf()
    self.setValue(var, otherRole, value=self.varNames['self'])
    self.endIf()

  ###########################################################################

  ###########################################################################

  def writeSetRole1N(self, op, inClass):

    role = op.target
    otherRole = role.otherRole

    var = self.valueVar(role)
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
 
    self.startIf(self.valueIsNotNone(currentVar))
    self.startIf(self.varNames['notIsReading'])
    self.getValue(currentVar, otherRole, self.oldSelfVars, lenient=True,
                  inClass=inClass)
    self.removeValue(currentVar, otherRole, self.varNames['self'], 
                     self.oldSelfVars)
    self.elseIf()
    self.raiseApiError(
     "Read link '%s' incompatible with pre-existing link" % op.target.name,
     self.varNames['self'], inOp=op
    )
    self.endIf()
    self.endIf()

    self.startIf(self.valueIsNotNone(var))
    self.getValue(var, otherRole, self.newSelfVars, lenient=True, inClass=inClass)
    self.addValue(var, otherRole, self.varNames['self'], self.newSelfVars)
    self.endIf()

  ###########################################################################

  ###########################################################################

  def writeSetRoleN1(self, op, inClass):

    role = op.target
    otherRole = role.otherRole

    var = self.valueVar(role)
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
    iterVar = 'cv'

    # TBD: is this correct?  NMBNB TBD this function still to check RHF
    if otherRole.changeability != metaConstants.frozen:
      # TBD: otherRole.locard == 1 implies already know that everything in currentVar is in var
      # but that is assuming that locard check has been done
      self.startLoop(iterVar, currentVar, **self.collectionParams(role))
      self.startIf(self.negate(self.isInCollection(iterVar, var, **self.collectionParams(role))))
      self.setValue(iterVar, otherRole, value=None)
      self.endIf()
      self.endLoop()

    self.startLoop(iterVar, var, **self.collectionParams(role))
    # TBD: is this correct?
    if otherRole.changeability != metaConstants.frozen:
      self.startIf(self.negate(self.isInCollection(iterVar, currentVar, **self.collectionParams(role))))
      self.getValue(iterVar, otherRole, self.oldSelfVar, lenient=True,
                    inClass=inClass, needVarType=False)
      self.startIf(self.valueIsNotNone(self.oldSelfVar))
      self.getValue(self.oldSelfVar, role, 'vv', lenient=True, inClass=inClass)
      self.removeValue(self.oldSelfVar, role, iterVar, 'vv')
      self.endIf()
      self.endIf()
    self.setValue(iterVar, otherRole, value=self.varNames['self'])
    self.endLoop()

  ###########################################################################

  ###########################################################################

  def writeSetRoleNN(self, op, inClass):

    role = op.target
    otherRole = role.otherRole

    var = self.valueVar(role)
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
    iterVar = 'cv'

    # TBD: not sure this is correct implementation for sets, ...

    self.startLoop(iterVar, currentVar, **self.collectionParams(role))
    self.startIf(self.negate(self.isInCollection(iterVar, var, **self.collectionParams(role))))
    self.getValue(iterVar, otherRole, self.oldSelfVars, lenient=True, inClass=inClass)
    self.removeValue(iterVar, otherRole, self.varNames['self'], self.oldSelfVars)
    self.endIf()
    self.endLoop()

    self.startLoop(iterVar, var, **self.collectionParams(role))
    self.startIf(self.negate(self.isInCollection(iterVar, currentVar, **self.collectionParams(role))))
    self.getValue(iterVar, otherRole, self.oldSelfVars, lenient=True, inClass=inClass)
    self.addValue(iterVar, otherRole, self.varNames['self'], self.oldSelfVars)
    self.endIf()
    self.endLoop()

  ###########################################################################

  ###########################################################################

  def writeAddRoleN1(self, op, inClass):

    role = op.target
    if role.changeability != metaConstants.frozen: # TBD: is this correct?
      
      # set up variables etc.
      var = self.valueVar(role, doInstance=True)
      otherRole = role.otherRole
      siblingVar = self.valueVar(role, doInstance=False, prefix='sibling')
    
      # remove previous link - 
      # NB package loading already done in checkPermissionN1
      self.getValue(var, otherRole, self.oldSelfVar, lenient=True,
                    inClass=inClass, needVarType=False)
      self.startIf(self.valueIsNotNone(self.oldSelfVar))
      self.getValue(self.oldSelfVar, role, siblingVar, inClass=inClass)
      self.removeValue(self.oldSelfVar, role, var, siblingVar)
      self.endIf()
      
      # set new link
      self.setValue(var, otherRole, value=self.varNames['self'])


  ###########################################################################

  ###########################################################################

  def writeAddRoleNN(self, op, inClass):

    role = op.target
    if role.changeability != metaConstants.frozen: # TBD: is this correct?
      var = self.valueVar(role, doInstance=True)
      otherRole = role.otherRole
      self.getValue(var, otherRole, self.oldSelfVars, lenient=True, inClass=inClass)
      self.addValue(var, otherRole, self.varNames['self'], self.oldSelfVars)

  ###########################################################################

  ###########################################################################

  def writeRemoveRoleN1(self, op, inClass):

    role = op.target
    if role.changeability != metaConstants.frozen: # TBD: is this correct?
      var = self.valueVar(role, doInstance=True)
      otherRole = role.otherRole
      self.setValue(var, otherRole, value=None)

  ###########################################################################

  ###########################################################################

  def writeRemoveRoleNN(self, op, inClass):

    role = op.target
    if role.changeability != metaConstants.frozen: # TBD: is this correct?
      var = self.valueVar(role, doInstance=True)
      otherRole = role.otherRole
      self.getValue(var, otherRole, self.oldSelfVars, lenient=True, inClass=inClass)
      self.removeValue(var, otherRole, self.varNames['self'], self.oldSelfVars)

  ###########################################################################

  ###########################################################################

  def writeFactoryFunction(self, op, inClass):
    
    if not op.isImplicit:
      self.writeExternalOp(op, inClass)
      return
     #raise MemopsError('handcoded operation for "new" op %s'
     #                             % (op.qualifiedName()))
    
    params = ([self.varNames['self']]
              + self.getFuncParams(op, defineFunc=False))

    self.returnStatement(self.callConstructor(op, inClass, params))
         
  ###########################################################################

  ###########################################################################

  def writeCheckClass(self, op, inClass):
    """ Write 'is not complete' part of checkValid functions
  
    checkValid does an almost full validity check (see below).
    This includes Class, Attribute and Role Constraints, 
    Role constraints are checked only for the forward role, 
    not for the reverse role.
    
    Checking of uniqueness of keys is done in checkAllValid of the parent object.
    """

    opType = op.opType
    
    if not op.isImplicit:
      raise MemopsError('handcoded operation for "%s" op %s'
                                  % (opType, op.qualifiedName()))

    self.checkPermission(op, inClass)

    if op.opType == 'checkValid':
      self.checkIsNotDeleted(op, inClass)

    self.startTransaction(op, inClass)

    if op.opType == 'checkValid':
      # NB for technical reasons (data loading) complete must come before normal
      self.startIf(self.varNames['complete'])
      self.writeCheckValidComplete(op, inClass)
      self.endIf()
      self.writeCheckValid(op, inClass)
    else:
      self.writeCheckAllValid(op, inClass)

    self.endTransaction(op, inClass)

  ###########################################################################

  ###########################################################################

  def writeCheckValidComplete(self, op, inClass):
    """ Write 'is complete' part of checkValid functions 
    
    1) checking that derived attributes and links can be derived without error
    2) checking links that require data loading. 
       For complete==False the objects currently present are checked, but no load
       is triggered, and lower cardinality is not checked.
    3)  checking that if a is linked to b, b is also linked to a
    4) DataType constraints
  
    Checking of uniqueness of keys is done in checkAllValid of the parent object.
    """
    doFor = [ ('attribute', inClass.getAllAttributes()),]
    if isinstance(inClass, MetaModel.MetaClass):
      doFor.append(('role', inClass.getAllRoles()))
    
    for tag, elements in doFor:
    
      self.writeComment('check %ss' % tag)
      for elem in elements:
        # check you can get the element, and check type
        
        if not elem.isImplementation:
          self.writeCheckElementComplete(op, inClass, elem, tag)

  ###########################################################################

  ###########################################################################

  def writeCheckValid(self, op, inClass):
    """ Write checks for handcode and cardinality
    """
    
    doFor = [ ('attribute', inClass.getAllAttributes()),]
    if isinstance(inClass, MetaModel.MetaClass):
      doFor.append(('role', inClass.getAllRoles()))
    
    else:
      self.startIf(self.boolean(self.getImplAttr(self.varNames['self'],
                                                 'override', inClass)))
      self.raiseApiError('override is on', self.varNames['self'], inOp=op)
      self.endIf()
    
    self.writeComment('check explicit class constraints')
    self.checkHandConstraints(op.container, op.opType)
    
    
    for tag, elements in doFor:
                           
      self.writeComment('check %ss' % tag)
      for elem in elements:
        # check you can get the attribute, check type, and checkAll DataObjType
        if (not elem.isDerived and not elem.isAutomatic 
            and not elem.isImplementation):
          if isinstance(elem.valueType, MetaModel.MetaDataObjType):
            self.startBlock()
            doBlock = False
          else:
            doBlock = True
          self.writeCheckElement(op, inClass, elem, doBlock=doBlock)
          if isinstance(elem.valueType, MetaModel.MetaDataObjType):
            self.writeCheckAllValidRecursiveLink(op, inClass, elem)
            self.endBlock()

  ###########################################################################

  ###########################################################################
  
  def writeCheckElementComplete(self, op, inClass, elem, tag):
    """Write checkValid (complete) for a single element 
    """ 
    
    self.oldErrorMsg = self.errorMsg
    self.errorMsg = '%s: %s' % (self.oldErrorMsg, elem.name)
    
    self.startBlock()
    self.getValue(self.varNames['self'], elem, self.valueVar(elem),
                  convertCollection=False, inClass=inClass)
    
    singleVar = self.valueVar(elem, doInstance=True)
    
    if elem.isDerived or elem.isAutomatic:
      if elem.locard != 0 or elem.hicard > 1:
        self.checkValidCardinality(op, inClass, elem)
        
    self.startCheckElement(elem)
 
    if elem.hicard == 1:
      self.checkCompatibleInstance(inClass, singleVar, elem)
    else:
      self.checkCompatibleInstance(inClass, singleVar, elem,
                                   inCollection=self.valueVar(elem))
    
    if elem.isDerived or elem.isAutomatic:
      # check other constraints, if any
      if self.hasHandConstraints(elem):
        self.checkInstanceConstraints(elem)
 
    if tag == 'role':
      if elem.otherRole and not elem.isAutomatic:
        self.writeCheckValidOtherRole(op, inClass, elem)
   
      # check object partitioning - do two-way links only once
      if elem.hierarchy == metaConstants.no_hierarchy:
         otherRole = elem.otherRole
         if (otherRole is None or otherRole.hicard > elem.hicard
             or (otherRole.hicard == elem.hicard and otherRole.name >= elem.name)):
           self.checkObjectPartitioning(elem, doInstance=True, inClass=inClass)
 
    self.endCheckElement(elem)
    self.endBlock()

    self.errorMsg = self.oldErrorMsg
    
  ###########################################################################

  ###########################################################################
  
  def writeCheckElement(self, op, inClass, elem, doBlock = True):
    """Write checkValid (not complete) for a single element
    
    NB there is no need to worry about the 'lenient'=True
    if complete==True everything will already be loaded
    If not we will check what is loaded, but by the model rules
    we can have no hicard>0 links or frozen links towards non-imported
    packages, so we will not get into trouble
    """ 
    self.oldErrorMsg = self.errorMsg
    self.errorMsg = '%s: %s' % (self.oldErrorMsg, elem.name)
    
    if doBlock:
      self.startBlock()
    
    self.getValue(self.varNames['self'], elem, self.valueVar(elem),
                  convertCollection=False, lenient=True, inClass=inClass)
   
    if elem.locard != 0 or elem.hicard > 1:
      self.checkValidCardinality(op, inClass, elem)
      
    if self.hasHandConstraints(elem):
      self.startCheckElement(elem)
      self.checkInstanceConstraints(elem)
      self.endCheckElement(elem)
    
    if doBlock:
      self.endBlock()

    self.errorMsg = self.oldErrorMsg
    
  ###########################################################################

  ###########################################################################
  
  def startCheckElement(self, element):

    self.startBlock()

    var = self.valueVar(element)

    if element.hicard == 1:
      if element.locard == 0:
        self.startIf(self.valueIsNotNone(var))
      
    else: # element.hicard != 1 (-to-many)
      iterVar = self.valueVar(element, doInstance=True)
      self.startLoop(iterVar, var, **self.collectionParams(element))

  ###########################################################################

  ###########################################################################
  
  def endCheckElement(self, element):

    if element.hicard == 1:
      if element.locard == 0:
        self.endIf()
      
    else: # role.hicard != 1 (-to-many)
      self.endLoop()

    self.endBlock()

  ###########################################################################

  ###########################################################################

  def writeCheckValidOtherRole(self, op, inClass, role):
    """ check that roles a.b and b.a are the same.
    """

    var = self.valueVar(role, doInstance=True)
    otherRole = role.otherRole
    
    # NB using oldSelfVar(s) here is a bit nonstandard, but it works
    otherVar = self.oldSelfVar
    otherVars = self.oldSelfVars

    if otherRole.hicard == 1:
      self.getValue(var, otherRole, otherVar, lenient=True, inClass=inClass)
      self.startIf(self.negate(self.comparison(otherVar, 'is', 
                                               self.varNames['self'])))
    else:
      self.getValue(var, otherRole, otherVars, lenient=True, inClass=inClass)
      self.startIf(self.negate(self.isInCollection(self.varNames['self'],
       otherVars, **self.collectionParams(otherRole)))
      )
    # NBNB Rasmus 25/1/2011 Changed as info was wrong
    #self.raiseApiError('non-reciprocal link %s from object' % op.target.name, 
    self.raiseApiError('non-reciprocal link %s from object' % role.name, 
                       self.varNames['self'], inOp=op)
    self.endIf()

  ###########################################################################

  ###########################################################################

  def writeCheckAllValid(self, op, inClass):
    """ writes function to recursively check object and all its children.
    the 'complete' keyword determines whether extra checking is done for
    each object. 
    This slows down the process and triggers loading of all connected data packages
    """

    self.stdCallFunc(self.varNames['self'], 'checkValid', doOptionalPars=True)
    
    
    # actual classs
    if isinstance(inClass, MetaModel.MetaClass):
      for role in inClass.getAllRoles():
        if role.hierarchy == metaConstants.child_hierarchy:
          self.writeCheckAllValidElement(op, inClass, role, isChildLink=True)
    
  ###########################################################################

  ###########################################################################

  def writeCheckAllValidElement(self, op, inClass, elem, isChildLink=False):

    errorMsg = self.errorMsg
    self.errorMsg = '%s: %s' % (errorMsg, elem.name)

    self.startBlock()

    var = self.valueVar(elem)
    self.getValue(self.varNames['self'], elem, var, convertCollection=False,
                  inClass=inClass)

    self.writeCheckAllValidRecursiveLink(op, inClass, elem)
    if isChildLink and elem.hicard != 1:
      self.writeCheckAllValidKeysUnique(op, inClass, elem)

    self.endBlock()

    self.errorMsg = errorMsg

  ###########################################################################

  ###########################################################################

  def writeCheckAllValidRecursiveLink(self, op, inClass, role):
    
    var = self.valueVar(role)

    if role.hicard == 1:
      if role.locard == 0:
        self.startIf(self.valueIsNotNone(var))
        self.stdCallFunc(var, 'checkAllValid', doOptionalPars=True)
        self.endIf()
      else:
        self.stdCallFunc(var, 'checkAllValid', doOptionalPars=True)

    else:
      iterVar = self.valueVar(role, doInstance=True)
      self.startLoop(iterVar, var, **self.collectionParams(role))
      self.stdCallFunc(iterVar, 'checkAllValid', doOptionalPars=True)
      self.endLoop()

  ###########################################################################

  ###########################################################################

  def writeCheckAllValidKeysUnique(self, op, inClass, role):

    # write check command for keys. 

    keyNames = role.valueType.keyNames
    serialKeyList = ['serial']
    if keyNames == serialKeyList:
      self.startIf(self.varNames['complete'])

    self.checkChildKeysUnique(op, inClass, role)

    if keyNames == serialKeyList:
      self.endIf()

  ###########################################################################

  ###########################################################################

  def writeExternalOp(self, op, inClass):

    returnPars = [x for x in op.parameters 
                  if x.direction == metaConstants.return_direction]

    if returnPars and len(returnPars) != 1:
        raise MemopsError("%s: multiple return parameters not allowed"
                          % op.qualifiedName())

    if returnPars:
      returnPar = returnPars[0]
    else:
      returnPar = None

    # TBD: should this be called for each arg??
    #self.checkCompatibleVar(op, inClass, ***, ***)

    self.checkPermission(op, inClass)

    # Note, have decided that should allow queries on deleted objects
    if not op.isQuery:
      self.checkIsNotDeleted(op, inClass)

    # define result, if any
    if returnPar:
      ##resultVar = returnPars[0].name  ## TBD: should this ever be used or should it always be ignored
      resultVar = self.varNames['result']
      ee = returnPar.valueType
      if returnPar.hicard == 1:
        varType = self.elementVarType(ee)
      else:
        varType = self.collectionType(ee, isUnique=returnPar.isUnique, isOrdered=returnPar.isOrdered)
      self.defineVar(resultVar, varType=varType)

    self.startTransaction(op, inClass)

    self.writeExternalCode(op, inClass)

    self.endTransaction(op, inClass)
    
    # handle return statement, if any
    if returnPar:
      self.returnStatement(resultVar)

    # TBD: should this be before endTransaction?
    # TBD: should this be done (not in current API)?
    #self.doNotifies(op, inClass)

  ###########################################################################

  ###########################################################################

  def setupModifyFuncVars(self, op, inClass):
    """ Set-up header for modifier functions
    """

    element = op.target
    
    selfVar = self.varNames['self']

    # currentVar
    # this is actually gotten here, not just defined
    currentVar = self.valueVar(element, prefix=self.currentPrefix)
    
    # For certain TopObject elements we need explicit load
    container = element.container
    if self.topObject in container.getAllSupertypes():
      lenient=True
          
      self.startIf(self.negate(self.logicalOp(
       self.boolean(self.getImplAttr(selfVar, 'isLoaded')), 'or',
       self.boolean(self.getImplAttr(selfVar, 'isReading'))))
      )
      self.callFunc('load', selfVar)
      self.endIf()
    else:
      lenient=False
    
    self.getValue(selfVar, element, currentVar, inClass=inClass,
                  lenient=lenient)
    
    # set override checking vars
    self.setVar(self.varNames['notInConstructor'], 
     self.negate(self.getImplAttr(self.varNames['self'], 'inConstructor', inClass)), 
     self.booleanType
    )
    self.getOverride(op, inClass)
    
    
    if isinstance(element, MetaModel.MetaRole):
      
      # oldSelfVar, defined here because useful to do so
      otherRole = element.otherRole
      if otherRole and otherRole.hicard == 1:
        # (slight loss of efficiency but old self not even defined unless var is not None)
        if element.hicard == 1 or op.opType != 'remove':
          self.defineVar(self.oldSelfVar, varType=self.elementVarType(element.container))

  ###########################################################################

  ###########################################################################

  # Note: this function does not do class constaints
  def checkModifyConstraints(self, op, inClass):
    """ Constraint checking for modifiers
    - checks if current state can be changed
    """

    opType = op.opType
    element = op.target
    
    self.startIf(self.varNames['notOverride'])
    self.checkModifyCardinality(op, inClass, element)
    if opType == 'remove':
      self.noStatement()
    else:
      if isinstance(element, MetaModel.MetaRole):
        doInstance = (opType == 'add')
        if doInstance or (element.hicard == 1 and element.locard == 0):
          var = self.valueVar(element, doInstance=True)
          self.startIf(self.valueIsNotNone(var))
        self.checkObjectPartitioning(element, doInstance=doInstance, 
                                     inClass=inClass)
        if doInstance or (element.hicard == 1 and element.locard == 0):
          self.endIf()
      if self.hasHandConstraints(element):
        self.startIf(self.varNames['notInConstructor'])
        self.checkHandConstraints(element, opType)
        self.endIf()
      elif not isinstance(element, MetaModel.MetaRole):
        self.noStatement()
    self.endIf()

  ###########################################################################

  ###########################################################################

  def checkValidCardinality(self, op, inClass, element):
    """ Cardinality checking for checkValid - checks if current state is valid
    """
    
    hicard = element.hicard
    locard = element.locard
    var = self.valueVar(element)

    if hicard == 1:
      if locard == 1:
        self.checkVarIsNotNone(var)

    else: # hicard != 1
      self.checkVarCardinality(var, element)

  ###########################################################################

  ###########################################################################

  def checkModifyCardinality(self, op, inClass, element):
    """ Cardinality checking for modifiers - checks if state may be modified
    """

    opType = op.opType
    hicard = element.hicard
    locard = element.locard
    var = self.valueVar(element)
    currentVar = self.valueVar(element, prefix=self.currentPrefix)
    
    # checks for frozen elements
    if element.changeability == metaConstants.frozen:
      self.startIf(self.varNames['notInConstructor'])
      self.raiseApiError('cannot set %s, frozen' % op.target.name, 
                         self.varNames['self'], inOp=op)
      self.endIf()
    
    
    # first do checks that the same for attibutes and roles
    # DIAGRAM **: this card check called "self"

    if hicard == 1:
      if locard == 1:
        self.checkVarIsNotNone(var)

    else: # hicard != 1

      if opType == 'set':
        self.checkVarCardinality(var, element)

      elif opType == 'add':
        self.checkVarCanBeAdded(currentVar, element)

      elif opType == 'remove':
        self.checkVarCanBeRemoved(currentVar, element)

    # now do role only checks
    if isinstance(element, MetaModel.MetaRole) and element.otherRole:

      # these so complicated that separate out by cardinality

      otherRole = element.otherRole
      otherHicard = otherRole.hicard

      if hicard == 1:
        if otherHicard == 1:
          self.checkModifyCardinality11(op, inClass)
        else: # otherHicard != 1
          self.checkModifyCardinality1N(op, inClass)

      else: # hicard != 1
        if otherHicard == 1:
          self.checkModifyCardinalityN1(op, inClass)
        else: # otherHicard != 1
          self.checkModifyCardinalityNN(op, inClass)

  ###########################################################################

  ###########################################################################
  
  def checkObjectPartitioning(self, role, doInstance=False, inClass=None):
    
    uplinks,partitionRoles = self.getPartitioningLinkages(role)
    
    valueVar = self.valueVar(role, doInstance=True)
    
    # special set-up to get type of topObject, when used.
    # needed for java typing
    topObjClasses = [None, None]
    
    # handle partitioning role
    useMultiRoleAt = None
    crossRole = partitionRoles[0]
    if crossRole is None:
      crossRole = partitionRoles[1]
      if crossRole is not None:
        # set special topObjectClass for typing. Only needed if we are here
        topObjRole = role.valueType.getElement(self.varNames['topObject'])
        if len(uplinks[1]) == 1 and uplinks[1][0] is topObjRole:
          topObjClasses[1] = role.valueType.container.topObjectClass
        
        if crossRole.hicard == 1:
          uplinks[1].append(crossRole)
        else:
          useMultiRoleAt = 1
    
    elif crossRole.hicard == 1:
      # set special topObjectClass for typing. Only needed if we are here
      topObjRole = role.container.getElement(self.varNames['topObject'])
      if len(uplinks[0]) == 1 and uplinks[0][0] is topObjRole:
        topObjClasses[0] = role.container.container.topObjectClass
      uplinks[0].append(crossRole)
    
    elif partitionRoles[1] is not None and partitionRoles[1].hicard == 1:
      # set special topObjectClass for typing. Only needed if we are here
      crossRole = partitionRoles[1]
      topObjRole = role.valueType.getElement(self.varNames['topObject'])
      if len(uplinks[1]) == 1 and uplinks[1][0] is topObjRole:
        topObjClasses[1] = role.valueType.container.topObjectClass
      uplinks[1].append(crossRole)
      
    else:
      useMultiRoleAt = 0
      # set special topObjectClass for typing. Only needed if we are here
      topObjRole = role.container.getElement(self.varNames['topObject'])
      if len(uplinks[0]) == 1 and uplinks[0][0] is topObjRole:
        topObjClasses[0] = role.container.container.topObjectClass
    
    self.startBlock()
    
    # get top parent from self
    xvarName = self.varNames['self']
    ii = 0
    for rr in uplinks[0]:
      ii += 1
      ss = 'xx%s' % ii
      
      # get variable typing element
      typeElem = topObjClasses[0]
      if typeElem is None:
        useType = self.elementVarType(rr)
      else:
        topObjClasses[0] = None
        useType = self.elementVarType(typeElem)
        
      # next two lines look silly, 
      # but allow faster getting of Implementation links
      self.defineVar(ss, useType)
      self.getValue(xvarName, rr, var=ss, needVarType=False, inClass=inClass, 
                    lenient=True, castType=useType)
      xvarName = ss
      
    if useMultiRoleAt == 0:
      self.getValue(xvarName, partitionRoles[0], var='xcoll', lenient=True,
                    inClass=inClass)
    
    # loop if we are checking multiple values
    if role.hicard != 1 and not doInstance:
      self.startLoop(valueVar, self.valueVar(role, doInstance=False), 
                     **self.collectionParams(role))
    
    # get top parent from value
    yvarName = valueVar
    ii = 0
    for rr in uplinks[1]:
      ii += 1
      ss = 'yy%s' % ii
      
      # get variable typing element
      typeElem = topObjClasses[1]
      if typeElem is None:
        useType = self.elementVarType(rr)
      else:
        topObjClasses[1] = None
        useType = self.elementVarType(typeElem)
        
      # next two lines look silly, 
      # but allow faster getting of Implementation links
      self.defineVar(ss, useType)
      self.getValue(yvarName, rr, var=ss, needVarType=False, inClass=inClass, 
                    castType=useType, lenient=True)
      yvarName = ss
    
    # do comparison:
    if crossRole is None:
      self.startIf(self.negate(self.comparison(xvarName, 'is', yvarName)))
      self.raiseApiError("""Link %s between objects from separate partitions
 - %s does not match""" 
                     % (role.name, uplinks[1][-1].valueType.qualifiedName()),
                        self.varNames['self'], valueVar)
      self.endIf()
    
    else:
    
      if useMultiRoleAt == 0:
        self.startIf(self.negate(self.isInCollection(
         yvarName, 'xcoll', **self.collectionParams(partitionRoles[0]))))
      elif useMultiRoleAt == 1:
        self.startIf(self.negate(self.isInCollection(xvarName, self.getValue(
         yvarName, partitionRoles[1], lenient=True, inClass=inClass),
         **self.collectionParams(partitionRoles[1])))
        )
      else:
        self.startIf(self.negate(self.comparison(xvarName, 'is', yvarName)))
    
    
      self.raiseApiError("""Link %s between objects from separate partitions
 - %s not set correctly"""
                     % (role.name, crossRole.qualifiedName()), 
                        self.varNames['self'], valueVar)
      self.endIf()
    
    
    if role.hicard != 1 and not doInstance:
      self.endLoop()
    
    self.endBlock()
    
  ###########################################################################

  ###########################################################################

  def checkVarIsNone(self, var):

    self.startIf(self.valueIsNotNone(var))
    self.raiseApiError('%s must be None' % var, self.varNames['self'])
    self.endIf()

  ###########################################################################

  ###########################################################################

  def checkVarIsNotNone(self, var):

    self.startIf(self.valueIsNone(var))
    self.raiseApiError('%s cannot be None' % var, self.varNames['self'])
    self.endIf()

  ###########################################################################

  ###########################################################################

  def checkVarCardinality(self, var, element):

    locard = element.locard
    hicard = element.hicard

    if locard == hicard:
      self.startIf(self.negate(self.comparison(
       self.lenCollection(var, **self.collectionParams(element)), '==', locard))
      )
      self.raiseApiError('locard, hicard: %s must be of length == %d' % (var, locard), 
                         self.varNames['self'])
      self.endIf()

    else:
      if locard > 0:
        self.startIf(self.comparison(
         self.lenCollection(var, **self.collectionParams(element)), '<', locard)
        )
        self.raiseApiError('locard: %s must be of length >= %d' % (var, locard), 
                           self.varNames['self'])
        self.endIf()

      if hicard != infinity:
        self.startIf(self.comparison(
         self.lenCollection(var, **self.collectionParams(element)), '>', hicard)
        )
        self.raiseApiError('hicard: %s must be of length <= %d' % (var, hicard), 
                           self.varNames['self'])
        self.endIf()

  ###########################################################################

  ###########################################################################

  def checkVarCanBeAdded(self, var, element):
    """cardinality check for use in add function
    """

    hicard = element.hicard
    if hicard != infinity:
      self.startIf(self.comparison(
       self.lenCollection(var, **self.collectionParams(element)), '>=', hicard)
      )
      self.raiseApiError('hicard: %s: cannot add value' % var,
                         self.varNames['self'])
      self.endIf()

  ###########################################################################

  ###########################################################################

  def checkVarCanBeRemoved(self, var, element, nRemoved="1"):
    """cardinality check for use in remove function
    """

    locard = element.locard
    if locard > 0:
      self.startIf(self.comparison(
                   self.lenCollection(var, **self.collectionParams(element)),
                   '<', self.arithmetic(locard,'+',nRemoved)))
      # NBNB use of string nRremoved instead of suggested int is OK.
      self.raiseApiError('locard: %s: cannot remove value' % var,
                         self.varNames['self'])
      self.endIf()

  ###########################################################################

  ###########################################################################

  # role.hicard = 1, otherRole.hicard = 1
  def checkModifyCardinality11(self, op, inClass):

    role = op.target
    locard = role.locard
    otherRole = role.otherRole
    otherLocard = otherRole.locard
    var = self.valueVar(role)
    currentVar = self.valueVar(role, prefix=self.currentPrefix)

    if locard == 1:
      # DIAGRAM 11: this card check called "old_self"
      # oldSelfVar already declared at top of function
      self.getValue(var, otherRole, self.oldSelfVar, inClass=inClass, needVarType=False)
      # already know here that valueIsNotNone(var) so do not have to check for that
      self.checkVarIsNone(self.oldSelfVar)

    if otherLocard == 1:
      # DIAGRAM 11: this card check called "current_value"
      self.checkVarIsNone(currentVar)

  ###########################################################################

  ###########################################################################

  # role.hicard = 1, otherRole.hicard != 1
  def checkModifyCardinality1N(self, op, inClass):

    role = op.target
    otherRole = role.otherRole
    otherHicard = otherRole.hicard
    otherLocard = otherRole.locard
    var = self.valueVar(role)
    currentVar = self.valueVar(role, prefix=self.currentPrefix)

    if otherLocard > 0:
      # DIAGRAM 1N: this card check called "current_value"
      self.startIf(self.valueIsNotNone(currentVar))
      self.getValue(currentVar, otherRole, self.oldSelfVars, inClass=inClass)
      self.checkVarCanBeRemoved(self.oldSelfVars, otherRole)
      self.endIf()

    if otherHicard != infinity:
      # DIAGRAM 1N: this card check called "value"
      self.startIf(self.valueIsNotNone(var))
      self.getValue(var, otherRole, self.newSelfVars, inClass=inClass)
      self.checkVarCanBeAdded(self.newSelfVars, otherRole)
      self.endIf()

  ###########################################################################

  ###########################################################################

  # role.hicard != 1, otherRole.hicard = 1
  def checkModifyCardinalityN1(self, op, inClass):

    iterVar = 'cv'
    countVar = 'knt'
    
    opType = op.opType
    role = op.target
    locard = role.locard
    otherRole = role.otherRole
    otherLocard = otherRole.locard
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
    siblingVar = self.valueVar(role, prefix=self.siblingPrefix)

    if opType == 'set':
      var = self.valueVar(role)
      if locard > 0:
        # DIAGRAM N1 set: this card check called "old_self[]"
        self.newDict(self.oldSelfVars, keyType=self.elementVarType(otherRole),
                     valueType=self.intType, needDeclType=True)
        self.startLoop(iterVar, var, **self.collectionParams(role))
        self.startIf(self.negate(self.isInCollection(
         iterVar, currentVar, **self.collectionParams(role)))
        )
        self.getValue(iterVar, otherRole, self.oldSelfVar, inClass=inClass)
        self.startIf(self.valueIsNotNone(self.oldSelfVar))
        self.setVar(countVar, 
                    self.getDictEntry(self.oldSelfVars,self.oldSelfVar),
                    varType=self.intType)
        self.startIf(self.valueIsNone(countVar))
        self.setVar(countVar, 1)
        self.elseIf()
        self.incrementInteger(countVar)
        self.endIf()
        self.setDictEntry(self.oldSelfVars, self.oldSelfVar, countVar)
        self.endIf()
        self.endIf()
        self.endLoop()
        
        loopVar = 'osv'
        self.startLoopOverDictKeys(self.oldSelfVars, loopVar, 
                                   varType=self.elementVarType(otherRole))
        self.getValue(loopVar, role, siblingVar, inClass=inClass)
        self.setVar(countVar, 
                    self.getDictEntry(self.oldSelfVars, loopVar),
                    varType=self.intType)
        self.checkVarCanBeRemoved(siblingVar, role, nRemoved=countVar)
        self.endLoop()

      if otherLocard == 1:
        # DIAGRAM N1 set: this card check called "current_values-values"
        self.startLoop(iterVar, currentVar, **self.collectionParams(role))
        self.startIf(self.negate(
         self.isInCollection(iterVar, var, **self.collectionParams(role)))
        )
        self.raiseApiError(
         'locard %s: cannot set because some of current values not in values' 
         % otherRole.name, self.varNames['self'], inOp=op)
        self.endIf()
        self.endLoop()

    elif opType == 'add':
      var = self.valueVar(role, doInstance=True)
      if locard > 0:
        # DIAGRAM N1 add: this card check called "old_self"
        # oldSelfVar already declared at top of function
        self.getValue(var, otherRole, self.oldSelfVar, inClass=inClass)
        # already know here that valueIsNotNone(var) so do not have to check 
        # for that
        # if condition can only happen if isUnique = False, in that case can 
        # have oldSelf = self
        if not role.isUnique:
          self.startIf(self.negate(self.comparison(self.varNames['self'], 'is',
                                                   self.oldSelfVar)))
        self.startIf(self.valueIsNotNone(self.oldSelfVar))
        self.getValue(self.oldSelfVar, role, siblingVar, inClass=inClass)
        self.checkVarCanBeRemoved(siblingVar, role)
        self.endIf()
        if not role.isUnique:
          self.endIf()

    elif opType == 'remove':
      if otherLocard == 1:
        raise MemopsError(
         "Error for %s.This should never happen with the current model rules."
         % op.qualifiedName()
        )
      # DIAGRAM N1 remove: this card check called "value"
      # if condition can only happen if isUnique = False, in that case can
      # have value in values more than once
      # var = self.valueVar(role, doInstance=True)
      # if not role.isUnique:
      #   self.startIf(self.comparison(
      #    self.countInCollection(var, currentVar, **self.collectionParams(role)),
      #    '==', 1)
      #   )
      # self.raiseApiError('locard %s: cannot remove value' % otherRole.name,
      #                    self.varNames['self'], inOp=op)
      # if not role.isUnique:
      #   self.endIf()

  ###########################################################################

  ###########################################################################

  # role.hicard != 1, otherRole.hicard != 1
  def checkModifyCardinalityNN(self, op, inClass):

    opType = op.opType
    role = op.target
    otherRole = role.otherRole
    otherHicard = otherRole.hicard
    otherLocard = otherRole.locard

    # TBD: below is not good enough in all (isUnique, isOrdered) cases, 
    # see N1 remove example above
    if opType == 'set':
      var = self.valueVar(role)
      currentVar = self.valueVar(role, prefix=self.currentPrefix)
      if otherLocard > 0:
        # DIAGRAM NN set: this card check called "current_values-values"
        iterVar = 'cv'
        self.startLoop(iterVar, currentVar, **self.collectionParams(role))
        self.startIf(self.negate(
         self.isInCollection(iterVar, var, **self.collectionParams(role)))
        )
        self.getValue(iterVar, otherRole, self.oldSelfVars, inClass=inClass)
        self.checkVarCanBeRemoved(self.oldSelfVars, otherRole)
        self.endIf()
        self.endLoop()

      if otherHicard != infinity:
        # DIAGRAM NN set: this card check called "values-current_values"
        iterVar = 'cv'
        self.startLoop(iterVar, var, **self.collectionParams(role))
        self.startIf(self.negate(self.isInCollection(
         iterVar, currentVar, **self.collectionParams(role)))
        )
        self.getValue(iterVar, otherRole, self.oldSelfVars, inClass=inClass)
        self.checkVarCanBeAdded(self.oldSelfVars, otherRole)
        self.endIf()
        self.endLoop()

    elif opType == 'add':
      var = self.valueVar(role, doInstance=True)
      if otherHicard != infinity:
        # DIAGRAM NN add: this card check called "value"
        # oldSelfVar already declared at top of function
        self.getValue(var, otherRole, self.oldSelfVars, inClass=inClass)
        self.checkVarCanBeAdded(self.oldSelfVars, otherRole)

    elif opType == 'remove':
      var = self.valueVar(role, doInstance=True)
      if otherLocard > 0:
        # DIAGRAM NN remove: this card check called "value"
        # oldSelfVar not declared at top of function
        self.getValue(var, otherRole, self.oldSelfVars, inClass=inClass)
        self.checkVarCanBeRemoved(self.oldSelfVars, otherRole)

  ###########################################################################

  ###########################################################################
  
  def hasHandConstraints(self, target):
    """ Has target got handconstraints to check
    """

    if target.getAllConstraints():
      return True
    
    elif isinstance(target, MetaModel.MetaRole):
      otherRole = target.otherRole
      if otherRole and otherRole.getAllConstraints():
        return True
      if target is otherRole:
        return True
    #
    return False
    
  ###########################################################################

  ###########################################################################

  def checkHandConstraints(self, target, opType = None):
    """check handcode constraints for atribute, role, class, or dataType
    """
    
    if self.hasHandConstraints(target):

      if isinstance(target, MetaModel.ClassElement):
        if target.hicard == 1 or opType == 'add':
          var = self.valueVar(target, doInstance=True)
          self.startIf(self.valueIsNotNone(var))
          self.checkInstanceConstraints(target)
          self.endIf()
        elif opType != 'remove':
          loopVar = self.valueVar(target, doInstance=True)
          var = self.valueVar(target)
          self.startLoop(loopVar, var, **self.collectionParams(target))
          self.checkInstanceConstraints(target)
          self.endLoop()
      else:
        self.checkInstanceConstraints(target)

  ###########################################################################

  ###########################################################################

  def checkInstanceConstraints(self, inElement):
    
    # set-up
    handCodeKey = self.modelFlavours['language']
    
    # handle roles where constraints may be on either side
    element = inElement
    constraints = element.getAllConstraints()
    
    roleIsOtherRole = False
    if isinstance(element, MetaModel.MetaRole):
      
      # role is own otherRole
      otherRole = element.otherRole
      if element is otherRole:
        roleIsOtherRole = True
        
      # change if constraints are on otherRole
      if not constraints:
        if otherRole is not None and otherRole.getAllConstraints():
          element = otherRole
          constraints = otherRole.getAllConstraints()
    
    # do checks
    if constraints or roleIsOtherRole:
      
      # initialise
      self.initCheckInstanceConstraints(element, inElement)

      sortedConstraints = [(x.name,x) for x in constraints]
      sortedConstraints.sort()
      for name,constraint in sortedConstraints:
 
        self.startBlock()

        body = constraint.codeStubs.get(handCodeKey)
        # TBD: TEMP
        body = body.replace('? extends ', '')
 
        if body is None:
          raise MemopsError("%s constraint %s lacks '%s' codeStub"
           % (element.qualifiedName(), name, handCodeKey)
          )
          ###print "%s constraint %s lacks '%s' codeStub" % (element.qualifiedName(), name, handCodeKey)
          ###body = 'true'
 
        index = body.find(self.varNames['isValid'])
        ll = body.splitlines()
        if index == -1:
          # body does not contain 'isValid'
 
          if len(ll) == 1:
            #single line constraint
            self.startIf(self.negate(body))
 
          else:
            raise MemopsError("""%s: Multiline constraint:\n%s
  with body:\n%s
  does not contain string '%s'
            """ % (element.qualifiedName(), name, body, self.varNames['isValid']))
 
        else:
          # body contains 'isValid'
 
          self.defineVar(self.varNames['isValid'], varType=self.booleanType)
          self.write(body)
          self.startIf(self.negate(self.varNames['isValid']))
 
        if isinstance(element, MetaModel.ComplexDataType):
          self.raiseApiError('constraint %s violated' % name,
                             self.varNames['self'])
        else:
          self.raiseApiError('%s constraint %s violated by value'
                             % (element.name, name), 'value')
 
        self.endIf()

        self.endBlock()
  
      # special case - roles that are their own inverse
      if roleIsOtherRole:
        self.startIf(self.comparison(self.varNames['me'], 'is', 
                                     self.varNames['other']))
        self.raiseApiError('symmetrical link connects object to itself')
        self.endIf()
    
      # finalise
      self.endCheckInstanceConstraints(element, inElement) 

  ###########################################################################

  ###########################################################################

  def initCheckInstanceConstraints(self, element, inElement):
    
    self.startBlock()
    
    if isinstance(element, MetaModel.MetaRole):
      if element is inElement:
        self.setVar(self.varNames['me'], self.varNames['self'], 
                    varType = self.elementVarType(element.container))
        self.setVar(self.varNames['other'], self.varNames['value'], 
                    varType = self.elementVarType(element.valueType))
      else:
        self.setVar(self.varNames('other'), self.varNames['self'], 
                    varType = self.elementVarType(element.container))
        self.setVar(self.varNames['me'], self.varNames['value'], 
                    varType = self.elementVarType(element.valueType))

  ###########################################################################

  ###########################################################################

  def endCheckInstanceConstraints(self, element, inElement):
    
    self.endBlock()
        
  
  ###########################################################################

  ###########################################################################

  # includes check that not None if element.hicard != 1
  # TBD: should include conversion correctly for hicard != 1 for set
  def checkCompatibleVar(self, inClass, element, doInstance=None):
    """Type compatibility check - handles instance/collection handling
    """
    
    singleVar = self.valueVar(element, doInstance=True)
    
    if element.hicard == 1:
      if element.locard == 1:
        self.checkCompatibleInstance(inClass, singleVar, element)
      else:
        self.startIf(self.valueIsNotNone(singleVar))
        self.checkCompatibleInstance(inClass, singleVar, element)
        self.endIf()
      
    elif doInstance:
      self.checkCompatibleInstance(inClass, singleVar, element)
 
    else:
      pluralVar = self.valueVar(element)
      self.makeCompatibleCollection(inClass, pluralVar, element)
      self.startLoop(singleVar, pluralVar, **self.collectionParams(element))
      self.checkCompatibleInstance(inClass, singleVar, element,
                                   inCollection=pluralVar)
      self.endLoop()
      

  ###########################################################################

  ###########################################################################

  def makeCompatibleCollection(self, inClass, var, element):
    
    if element.isUnique:
      dummyCollVar = 'xx'
      self.startBlock()
      if element.isOrdered:
        collParams = {'isUnique':True, 'isOrdered':False,
                      'varType':self.elementVarType(element)}
        self.defineVar(dummyCollVar, varType=self.collectionType(element, isUnique=True, isOrdered=False))
        self.newCollection(dummyCollVar, initValues=var, **collParams)
      else:
        collParams = self.collectionParams(element)
        self.setVar(dummyCollVar, var, varType=self.collectionType(element))
      
    self.newCollection(var, initValues=var, **self.collectionParams(element))
      
    if element.isUnique:
      self.startIf(self.comparison(
       self.lenCollection(var,**self.collectionParams(element)),
       '!=', self.lenCollection(dummyCollVar,**collParams))
      )
      self.raiseApiError("%s may not contain duplicates" % var, 
                         self.varNames['self'])
      self.endIf()
      self.endBlock()

  ###########################################################################

  ###########################################################################

  def checkCompatibleInstance(self, inClass, var, element, inCollection=None):
    """Type compatibility check - handles special case of closed
    enumeration data types, and delegates to checkComparableInstance
    for other cases.
    
    NB where dataType HandConstraints are involved, var *must* be 'value'
    """

    if isinstance(element.valueType, MetaModel.MetaDataType):
      # attributes of primitive type

      dataType = element.valueType
      dataTypeName = dataType.qualifiedName()

      if dataType.enumeration and not dataType.isOpen:
        self.startIf(self.negate(self.inEnumeration(var, dataType.enumeration)))
        self.raiseApiError('%s input is not in enumeration %s'
         % (dataTypeName, dataType.enumeration), var
        )
        self.endIf()

      elif dataType is self.anyObject:
        # a pass necessary ass this is within a loop
        self.noStatement()
        
      else:
        self.checkComparableInstance(inClass, var, element, 
                                     inCollection=inCollection)

        if dataType.length not in (None, infinity):
          self.startBlock()
          self.setVar('_lenValue', self.lenString(var), self.intType)
          # NB - only string types can have dataType.length
          self.startIf(self.comparison('_lenValue', '>', dataType.length))
          self.raiseApiError('%s maximum length is %d violated by %s' % 
           (dataTypeName, dataType.length, var), var
          )
          self.endIf()
          
          # string types may not be empty
          self.startIf(self.comparison('_lenValue', '<', self.toLiteral(1)))
          self.raiseApiError('%s: Empty string not allowed' 
                             % dataTypeName, var)
          self.endIf()
          self.endBlock()
        
      if var != self.varNames['value']:
        raise MemopsError(
         "variable must be valled 'value' to fit dataType hand constraints"
        )
      self.checkHandConstraints(dataType)

    elif isinstance(element, MetaModel.ClassElement):
      # roles and attributes of complex type

      self.checkComparableInstance(inClass, var, element)
      # TBD: anything else?

  ###########################################################################

  ###########################################################################

  def checkIsNotDeleted(self, op, inClass, owner = None):
    """ Check if object is deleted. If the operation handles
    a role, also checks that value(s) are not deleted.
    """
      
    if not isinstance(inClass, MetaModel.MetaClass):
      # checkIsNotDeleted is not allowed for DataObjTypes
      # NBNB WARNING this could still be called on a DataObjType owner
      # from somewhere else. That wuold crash at runtime, but there is
      # no really good way to catch it here. Coder beware!
      return
    
    if not owner:
      owner = self.varNames['self']
      
    if owner == self.varNames['self']:
      msg = 'called on deleted object'
      
    else:
      msg = 'called with deleted %s' % owner

    self.startIf(self.getImplAttr(owner, 'isDeleted'))
    self.raiseApiError(msg, inOp=op)
    self.endIf()

    element = op.target
    if isinstance(element, MetaModel.MetaRole):
      
      
      if op.opType in ('add', 'remove'):
        # we already know var is not None
        var = self.valueVar(element, doInstance=True)
        self.startIf(self.getImplAttr(var, 'isDeleted'))
        self.raiseApiError('called with deleted %s' % var, inOp=op)
        self.endIf()
        
      else:
        var = self.valueVar(element)
        
        if element.hicard == 1:
          self.startIf(self.valueIsNotNone(var))
          self.startIf(self.getImplAttr(var, 'isDeleted'))
          self.raiseApiError('called with deleted %s' % var, inOp=op)
          self.endIf()
          self.endIf()
 
        else:
          objVar = 'obj'
          self.startLoop(objVar, var, **self.collectionParams(element))
          self.startIf(self.getImplAttr(objVar, 'isDeleted'))
          self.raiseApiError('an object in %s is deleted' % var, inOp=op)
          self.endIf()
          self.endLoop()

  ###########################################################################

  ###########################################################################

  def checkIfValueUnchanged(self, element):

    newvar = self.valueVar(element)
    oldvar = self.valueVar(element, prefix=self.currentPrefix)

    # TBD: is this good enough if element.hicard != 1, with isUnique and isOrdered...
    self.startIf(self.equals(newvar, oldvar))
    self.returnStatement()
    self.endIf()

  ###########################################################################

  ###########################################################################

  def checkValueIsNotInList(self, element):

    if element.isUnique:

      var = self.valueVar(element, doInstance=True)
      oldvar = self.valueVar(element, prefix=self.currentPrefix)

      self.startIf(self.isInCollection(var, oldvar, **self.collectionParams(element)))
      self.raiseApiError('%s is in list already' % var, self.varNames['self'])
      self.endIf()

  ###########################################################################

  ###########################################################################

  def checkValueIsInList(self, element):

    var = self.valueVar(element, doInstance=True)
    oldvar = self.valueVar(element, prefix=self.currentPrefix)

    self.startIf(self.negate(self.isInCollection(var, oldvar, **self.collectionParams(element))))
    self.raiseApiError('%s not in list' % var, self.varNames['self'])
    self.endIf()

  ###########################################################################

  ###########################################################################

  def doNotifies(self, op, inClass):
    
    self.writeNewline()
    self.writeComment("doNotifies")

    if not isinstance(inClass, MetaModel.MetaClass):
      return
    
    opType = op.opType
    element = op.target
   
    if opType in ('init', 'fullDelete') or ((
     isinstance(element,MetaModel.ClassElement) ) and 
     element.changeability != metaConstants.frozen
    ):
      if opType == 'fullDelete':
        s = '' # check already done in singleDelete
      else:
        s = self.shouldDoNotifies(op, inClass)
      if s:
        self.writeNewline()
        self.startIf(s)
      self.writeNotifyCode(op, inClass)
      if s:
        self.endIf()

  ###########################################################################

  ###########################################################################

  def writeExternalCode(self, op, inClass):

    key = self.modelFlavours['language']
    code = op.codeStubs.get(key)
  
    if code is None:
      raise MemopsError("Operation %s lacks %s code"
       % (op.qualifiedName(), key)
      )

    # TBD: TEMP
    code = code.replace('? extends ', '')

    self.write(code)

  ###########################################################################

  ###########################################################################

  def shouldDoInstance(self, opType, element):
    """ Check if checks etc. should be done on an object (hicard == 1 or
    add, remove functions), or on a collection (hicard!=1 and set or checkValid).
    """

    return element.hicard == 1 or opType in ('add', 'remove')
    
  ###########################################################################

  ###########################################################################
  
  def getStdCollectionParams(self, opType, parName):
    """ get collection parameters from operationData parData
    """
    
    parName = self.varNames[parName]
    for parData in self.operationData[opType]['subOps'][None]['parameters']:
      if parData['name'] == parName:
        break
    else:
      raise MemopsError("%s parameter %s not found" % (opType, parName))
    
    target = parData.get('target')
    if target is None:
      target = self.anyObject
    elif isinstance(target, str):
      target = self.modelPortal.topPackage.metaObjFromQualName(target)
    #
    return {'varType':self.elementVarType(target),
            'isUnique':parData['isUnique'], 'isOrdered':parData['isOrdered']}
    
  ###########################################################################

  ###########################################################################

  def collectionParams(self, element):

    return {'varType':self.elementVarType(element), 
            'isUnique':element.isUnique, 'isOrdered':element.isOrdered}
    
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stdCallFunc(self, objVar, opType, target=None, doWrite=True, 
                  doOptionalPars=False):
    """ Call function using parameter name for all input parameters
    
    If target is None parameters are taken from self.operationData;
    this only works for operations with container targets
    """
    
    returndir = metaConstants.return_direction
    
    if target is None:
      # No target - get information from standard operationData
      opData = self.operationData[opType]
      func = opData.get('name') or opType
      parData = opData['subOps'][None]['parameters']
      
      if opData['targetTag'] != 'container':
        raise MemopsError(
         "stdCallFunc called with target None for non-'container' opType %s" 
         % opType
        )
      
      if doOptionalPars:
        pNames = [x['name'] for x in parData if x['direction'] != returndir]
      else:
        pNames = [x['name'] for x in parData
         if x['direction'] != returndir and 'defaultValue' not in x
        ]
      
    else:
      # known target - get information from operation
      op = metaUtil.getOperation(target, opType)
      func = self.getFuncname(op)
      pars =  op.parameters
      
      if doOptionalPars:
        pNames = [y.name for y in pars if y.direction != returndir]
      else:
        pNames = [y.name for y in pars
                  if y.direction != returndir 
                  and not (y.locard == 0 and y.hicard ==1)]
    
    self.callFunc(func, objVar, params=pNames, doWrite=doWrite)

  ###########################################################################

  ###########################################################################

  def classHasSingletonKey(self, clazz):

    keyNames = clazz.keyNames
    if len(keyNames) == 1:
      ee = clazz.getElement(keyNames[0])
      if ee.hicard == 1:
        return True

    return False

