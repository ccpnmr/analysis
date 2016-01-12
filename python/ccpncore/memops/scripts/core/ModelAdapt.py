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
""" Operations on the model in memory, adapting the basic model for a 
particular language and implementation. 
Does no output.
"""

import copy
import types
import time

from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.metamodel.ModelTraverse import ModelTraverse
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import Util as metaUtil
from ccpncore.memops.metamodel import OpTypes


MemopsError = MetaModel.MemopsError
try:
  StringType = types.StringType
except AttributeError:
  StringType = str


class ModelAdapt(ModelTraverse):
  """ This class processes and modifies an input model, specifically adding 
  operations that are absent in the basic model but needed for generation. 
  Assumes that basic model is valid. 
  All additions in this file are independent of language, implementation and
  task. May be overridden in subclasses to handle specific changes.
  """
  
  # operation handling info
  
  # Names of class contents, apart from the opTypes above
  # that are not inherited. - currently not in use. 
  #doNotInheritElements = ()
  
  # variable names and their default values (may be overridden)
  _varNames = {
  
  # common variable names
  
  # variable indiating the current object
  # NB used in UML handcode
  'self':'self',
  
  # synonym for'self' used in constraints handcode for link constraints (only)
  # NB used in UML handcode
  'me':'self',
  
  # collection element input or element collection.
  # NB used in UML handcode
  'values':'values',
  
  # non-collection element input or member of element collection.
  # NB used in UML handcode
  'value':'value',
  
  # synonym for'value' used in constraints handcode for link constraints (only). 
  # NB used in UML handcode
  'other':'other',
  
  # return value for any function that returns a value.
  # NB used in UML handcode
  'result':'result',
  
  # temporary variable where needed
  # NB used in UML handcode
  'tempVar':'tempVar',
  
  # Boolean saying if a constraint evaluates as valid.
  # NB used in UML handcode
  'isValid':'isValid',
  
  # parameters for specific functions and function types
  
  # filtering conditions input to findFirst and findAll
  'conditions':'conditions',
  
  # filtering conditions input to findFirst and findAll
  'nConditions':'nConditions',
  
  # keywprd,value input to init
  'attrlinks':'attrlinks',
  
  # keyword,value input to init
  'attrDict':'attrDict',
  
  # doCompleteCheck Boolean input to checkValid functions
  'complete':'complete',
  
  # Set of objects to be deleted (for checkDelete/singleDelete calls)
  'objsToBeDeleted':'objsToBeDeleted',

  # Set of objects to be undeleted (for _fullUnDelete/_singleUnDelete calls)
  'objsToBeUnDeleted':'objsToBeUnDeleted',
  
  # Set of objects to check for deletion (for checkDelete/singleDelete calls)
  'objsToBeChecked':'objsToBeChecked',

  # Set of objects newly created (for passing to undo machinery0
  'objectsCreated':'objectsCreated',
  
  # links-to-check dictionary (for checkDelete/singleDelete calls)
  'linkCounter':'linkCounter',
  
  # parameters for specific situations
  
  # variable name: are we currently not executing a constructor? 
  'notInConstructor':'notInConstructor',
  
  # variable name: are we currently in global override? 
  'notOverride':'notOverride',
  
  # variable name: are we currently in override? 
  'override':'override',
  
  
  # Implementation links
  
  # name of baseclass link to memopsRoot
  'root':'root',
  
  # name of storage attribute. Present and used also for non-file implemnetation,
  # e.g. in ModelTraverse.getPartitioningLinkages
  'topObject':'topObject',
  
  # parent object of current object
  'parent':'parent',

  # undo object
  '_undo':'_undo',
  
  
  # Implementation attributes
  
  #
  'className':'className',
  
  #
  'packageName':'packageName',
  
  #
  'packageShortName':'packageShortName',
  
  # fieldNames attribute (names of class elements)
  'fieldNames':'fieldNames',
  # is object deleted?
  'isDeleted':'isDeleted',
  
  # internal attribute: are we currently executing a constructor?
  'inConstructor':'inConstructor',
  }
  
  # Std. documentation templates
  opDocTemplate = "%s for %s"
  parDocTemplate = " the %s"
  
  
  def __init__(self):
    """Class constructor.
    """ 
    
    # copy setup info down, to allow modification
    self.varNames = copy.deepcopy(self._varNames)
    self.operationData = copy.deepcopy(OpTypes.operationData)
    
    # initialise ModelTraverse
    super(ModelAdapt, self).__init__()
    
    # link varNames to modelPortal, for transport.
    self.modelPortal.varNames = self.varNames
    self.modelPortal.operationData = self.operationData
    
    # set model flavour (and check if it is compatible)
    for (key, val) in self.modelFlavours.items():
      self.modelPortal.setModelFlavour(key, val)
    
  ###########################################################################
  
  ###########################################################################
  ###
  ### code overriding ModelTraverse
  ###
  ###########################################################################

  ###########################################################################
  
  def processModel(self):
    """ top function that does all actions. Only function that should
    be called from outside the module.
    """
    
    # pre-process model - handle multiple inheritance and 
    # select implementation-dependent classes
    self.preprocessModel()
    
    # process model
    ModelTraverse.processModel(self)
    
    # final check
    
    t0 = time.time()
    self.modelPortal.topPackage.checkValid()
    t1 = time.time()
    print("ModelAdapt - Model validity check took %s" % (t1-t0))
    
  ###########################################################################
  
  def preprocessModel(self):
    """pre-process model - handle multiple inheritance 
    and select implementation-dependent classes
    """
    
    rootPackage = self.modelPortal.topPackage
    rootClass = rootPackage.metaObjFromQualName(self.rootClassName)
    
    for package in self.modelPortal.leafPackagesByImport():
    
      for xx in self.modelPortal.dataObjTypesByInheritance(package):
        # inherit down
        ll = []
        if not xx.supertypes and xx is not rootClass:
          xx.inheritDown()
          xx.delete()
    
      for xx in self.modelPortal.classesByInheritance(package):
        
        # remove classes specific to other implementations
        forImpl = xx.taggedValues.get('specificImplementation')
        if (forImpl is not None 
            and forImpl != self.modelFlavours.get('implementation')):
          xx.delete()
      
        # inherit down
        elif not xx.supertypes and xx is not rootClass:
          xx.inheritDown()
          xx.delete()
    
    # remove deleted objects from modepPortal internals
    self.modelPortal.resetObjectDicts()
    
  ###########################################################################
    
  def initComplexDataType(self, complexDataType):
    """ processing actions for start of complexDataType
    """
    
    self._tempOpList = complexDataType.operations
  
  initClass = initComplexDataType
  
  initDataObjType = initComplexDataType
    
  ###########################################################################
  
  ###########################################################################
    
  def processDataObjType(self, dataObjType):
    """ processing actions for class
    """
    
    # class operations - not related to elements
    self.addDataObjTypeOperations(dataObjType)
    
    # super function call
    ModelTraverse.processDataObjType(self, dataObjType)        
    
  ###########################################################################

  ###########################################################################
    
  def endComplexDataType(self, complexDataType):
    """ processing actions for end of complexDataType
    """
    
    # sort contents
    self.sortAttributes(complexDataType)
    self.sortOperations(complexDataType)
    
    # check all specific operations have been consumed
    for op in self._tempOpList:
      if self.operationData[op.opType]['targetTag'] != 'masterOp':
        raise MemopsError(
         "operation %s with opType %s and target %s defined but not used"
         % (op.qualifiedName(), op.opType, op.target)
        )
    
    del self._tempOpList
  
  ###########################################################################

  ###########################################################################
    
  def endDataObjType(self, dataObjType):
  
    self.endComplexDataType(dataObjType)

  ###########################################################################

  ###########################################################################
    
  def processClass(self, clazz):
    """ processing actions for class
    """

    # class operations - not related to elements
    self.addClassOperations(clazz)
    
    self.addParentLink(clazz)
    
    # super function call
    ModelTraverse.processClass(self, clazz)        
    
  ###########################################################################

  ###########################################################################
    
  def endClass(self, clazz):
    """ processing actions for end of class
    """
    
    self.sortRoles(clazz)
    
    self.endComplexDataType(clazz)
    
  ###########################################################################
  
  ###########################################################################
    
  def processAttribute(self, elem, inClass):
    """ processing actions for attribute
    """
    if elem.container is inClass:
      #get 
      self.addGetters(elem, inClass)
    
      # set, add, remove
      self.addModifiers(elem, inClass)
      
      # findFirst, findAll
      if isinstance(elem.valueType, MetaModel.MetaDataObjType):
        self.addRoleOperations(elem, inClass)
    
  ###########################################################################

  ###########################################################################
    
  def processRole(self, elem, inClass):
    """ processing actions for role
    """
    # add default documentation
    if not elem.documentation:
      hier = elem.hierarchy
      if hier == metaConstants.parent_hierarchy:
        elem.documentation = 'parent link'
      elif hier == metaConstants.child_hierarchy:
        elem.documentation = 'child link to class %s' % elem.valueType.name

    if elem.container is inClass:
      #get 
      self.addGetters(elem, inClass)
    
      # set, add, remove
      self.addModifiers(elem, inClass)
    
      # role-specific operations
      self.addRoleOperations(elem, inClass)
    
  ###########################################################################

  ###########################################################################
    
  def processOperation(self, op, inClass):
    """ processing actions for operation
    """
    
    if not op.documentation:
      if op.opType == 'get':
        target = op.target
        if isinstance(target, MetaModel.MetaAttribute):
          ss = 'attribute'
        elif isinstance(target, MetaModel.MetaRole):
          ss = 'link'
        else:
          raise MemopsError("Code error, should never get here)")
        op.documentation = 'getter for derived %s %s' % (ss, target.name)

    ModelTraverse.processOperation(self, op, inClass)   
  
  ###########################################################################

  ###########################################################################
  ###
  ### Internal functions - may be overridden in subclasses
  ###
  ###########################################################################

  ###########################################################################
  
  def sortAttributes(self, clazz):
    """ sort attributes within clazz
    """
    pass
  
  ###########################################################################
 
  ###########################################################################
  
  def sortRoles(self, clazz):
    """ sort roles within clazz
    """
    clazz._MetaClass__roleNames.sort()
  
  ###########################################################################
 
  ###########################################################################
  
  def sortOperations(self, elem):
    """ sort operations within class by name
    """
    elem._ComplexDataType__operationNames.sort()
    
  
  ###########################################################################

  ###########################################################################
    
  def addClassOperations(self, inClass):
    """ Add operations not linked to an element (e.g. init, delete, checkValid)
    """
    
    isNotRootClass = True
    
    if inClass.container.qualifiedName() == self.implPackageName:
      
      if  inClass.name == metaConstants.dataObjClassName:
        # DataObject
      
        # full delete
        self.makeOperations(inClass, 'fullDelete', inClass)
 
        # TBD: to remove
        # checkers (will be abstract)
        ###self.makeOperations(inClass, 'checkValid', inClass)
        ###self.makeOperations(inClass, 'checkAllValid', inClass)
      
        # no longer needed, in ComplexDataType instead
      # elif  inClass.name == ImpConstants.baseClassName:
      #
      #   # checkers (will be abstract)
      #   self.makeOperations(inClass, 'checkValid', inClass)
      #   self.makeOperations(inClass, 'checkAllValid', inClass)

      elif inClass.name == metaConstants.dataRootName:
        # MemopsRoot
        
        isNotRootClass = False

        # full undelete
        self.makeOperations(inClass, 'fullUnDelete', inClass)
      
      elif not inClass.isAbstract:
        # Non-abstract non-root Implementation classes
      
        # full delete
        self.makeOperations(inClass, 'fullDelete', inClass)
        
    
    if not inClass.isAbstract:
    
      # delete
      if isNotRootClass:
        self.makeOperations(inClass, 'checkDelete', inClass)
        self.makeOperations(inClass, 'singleDelete', inClass)
        self.makeOperations(inClass, 'singleUnDelete', inClass)
 
      # checkers
      self.makeOperations(inClass, 'checkValid', inClass)
      self.makeOperations(inClass, 'checkAllValid', inClass)
      
      # constructor
      self.makeOperations(inClass, 'init', inClass)
    
      # getAttr, setAttr
      self.makeOperations(inClass, 'getAttr', inClass)
      self.makeOperations(inClass, 'setAttr', inClass)

    # fullKey operations - may also be for abstract classes
    parentRole = inClass.parentRole
    if parentRole:
      ot = parentRole.otherRole
      if inClass.keyNames or (ot is not None and ot.hicard == 1):
        # any class with a full key defined, also if inherited.
        self.makeOperations(inClass, 'getByKey', inClass)
 
        if parentRole.container is inClass:
          # topmost supertype with a full key defined.
          self.makeOperations(inClass, 'getFullKey', inClass)
          self.makeOperations(inClass, 'getLocalKey', inClass)
          
    
    elif parentRole is None and not inClass.isAbstract:
      # specific for MemopsRoot
      self.makeOperations(inClass, 'getFullKey', inClass)
      self.makeOperations(inClass, 'getLocalKey', inClass)
      
  ###########################################################################

  ###########################################################################
    
  def addDataObjTypeOperations(self, inClass):
    """ Add operations not linked to an element (e.g. init, checkValid)
    """
    
    # TBD: added
    if inClass.isAbstract:
      ###if inClass.name == ImpConstants.baseDataTypeObjName:
      if inClass.name == metaConstants.rootClassName:
        self.makeOperations(inClass, 'checkValid', inClass)
        self.makeOperations(inClass, 'checkAllValid', inClass)

    # TBD: to remove
    ###if not inClass.isAbstract:
    else:
 
      # checkers
      self.makeOperations(inClass, 'checkValid', inClass)
      self.makeOperations(inClass, 'checkAllValid', inClass)
      
      # constructor
      self.makeOperations(inClass, 'init', inClass)
      
      # constructor
      self.makeOperations(inClass, 'clone', inClass)
    
      # getAttr, setAttr
      self.makeOperations(inClass, 'getAttr', inClass)
      self.makeOperations(inClass, 'setAttr', inClass)

  ###########################################################################

  ###########################################################################
  
  def newElement(self, clazz, **params):
    """ make new element of class clazz using parameter dict params
    Sets isImplicit to True and the Guid to a dummy value, if not already set.
    """
    
    result = clazz(**params)
    
    if 'isImplicit' not in params:
      result.isImplicit=True
    
    if 'guid' not in params:
      result.guid = 'temporary_%s' % result.qualifiedName()
    
    #
    return result
  
  
  ###########################################################################

  ###########################################################################
  
  def addParentLink(self, clazz):
    """ Add element and getter for parent link (synonym for the real one)
    Must be treated as special case later.
    """
    
    # Add 'parent' link NB must be treated as special case later
    parentRole = clazz.parentRole
    if (parentRole is not None and parentRole.container is clazz
        and not parentRole.isAbstract ):
      baseRole = parentRole
      
    elif parentRole is None and clazz.qualifiedName() == self.dataRootName:
      # special case - dataRoot
      baseRole = clazz.getElement('root')
    
    else:
      return
    
    dd = {}
    for tag,pData in MetaModel.MetaRole.parameterData.items():
      if pData['type'] != 'content' and pData.get('setterFunc') != 'unsettable':
        dd[tag] = getattr(baseRole,tag)
    
    # remove some attributes
    del dd['otherRole']
    del dd['isImplicit']
    del dd['guid']
    
    # make new MetaRole
    dd.update({
     'name':self.varNames['parent'],
     'baseName':self.varNames['parent'],
     'documentation':'link to parent object'
                     ' - synonym for %s' % baseRole.name,
     'isImplementation':True,
     'aggregation':metaConstants.no_aggregation,
     'hierarchy':metaConstants.no_hierarchy,
    })
    
    if parentRole is None:
      # special case - dataRoot
      dd['container'] = dd['valueType']
      dd['documentation'] = "link to parent object - returns None"
      dd['locard'] = 0
 
    self.newElement(MetaModel.MetaRole, **dd)
  
  ###########################################################################

  ###########################################################################
    
  def addGetters(self, elem, inClass):
    """ select, and find or create 'get' functions
    """
    
    if elem.isDerived:
      self.checkOpForDerived(elem, inClass, 'get')
      
    else:
      self.makeOperations(elem, 'get', inClass)
    
  ###########################################################################

  ###########################################################################
    
  def addModifiers(self, elem, inClass):
    """ select, and find or create modifiers (set, add, remove)
    """
      
    # set
    makeModifiers = False
    
    if elem.isImplementation:
      pass
    
    elif elem.isDerived:         
      if elem.changeability != metaConstants.frozen:
        self.checkOpForDerived(elem, inClass, 'set')
        makeModifiers = True
    
    elif (isinstance(elem, MetaModel.MetaAttribute) or
          elem.hierarchy == metaConstants.no_hierarchy):
      self.makeOperations(elem, 'set', inClass)
      makeModifiers = True
    
    if makeModifiers and elem.hicard != 1:
      # add, remove
      # NB add and remove can be generated from set and get if needed.
      
      # set up
      elems = [elem]
      if isinstance(elem, MetaModel.MetaRole):
        otherRole = elem.otherRole
        if otherRole is not None:
          elems.append(otherRole)
      
      # check if functions should be generated
      for ee in elems:
        if ee.hicard == ee.locard or ee.changeability == metaConstants.frozen:
          break
      else:
        self.makeOperations(elem, 'add', inClass)
        self.makeOperations(elem, 'remove', inClass)
        
  ###########################################################################

  ###########################################################################
  
  def checkOpForDerived(self, elem, inClass, opType):
    """ verify existence of op for derived element and check the op.
    """
    
    self.currentOpData = opData = self.getOpData(elem, opType, inClass)
    op = metaUtil.getOperation(elem, opType)
    
    if op is None:
      raise MemopsError("no %s function found in %s for derived element %s"
                        % (opType, inClass.qualifiedName(), elem.name))
    
    elif op.container is not elem.container:
      raise MemopsError(
       "%s function %s for derived element %s in %s found in supertype %s"
       % (opType, op.name, elem.name, inClass.qualifiedName(), op.container)
      )
    
    else:
      try:
        self._tempOpList.remove(op)
      except:
        pass
      self.checkOperation(op, opData, inClass)
 
    del self.currentOpData
    
  ###########################################################################

  ###########################################################################
    
  def addRoleOperations(self, elem, inClass):
    """ select, and find or create operations specific for roles 
      or DataObjType attrs (findFirst, findAll, new)
    """
    
    if elem.hicard != 1:
      # findFirst, findAll
      self.makeOperations(elem, 'findFirst', inClass)
      self.makeOperations(elem, 'findAll', inClass)
    
    if isinstance(elem, MetaModel.MetaRole):
          
      if elem.hicard != 1 and not elem.isOrdered:
        # 'sorted' function
        self.makeOperations(elem, 'sorted', inClass)
      
      # factory functions 
      # NB assumes that all subClasses are known to the model at this stage
      if (elem.hierarchy == metaConstants.child_hierarchy
          and not elem.isAbstract):
        # factory functions
        for target in elem.valueType.getNonAbstractSubtypes():
          self.makeOperations(target, 'new', inClass, elem)
    
  ###########################################################################

  ###########################################################################
    
  def makeOperations(self, target, opType, inClass, elem=None):
    """ get existing operation and check it, or create a new one
    Some error checking and bookkeeping for existing operations
    
    NB elem passed in separately for the 'new' operations, where it is
    the childRole pointing to the class to create.
    Otherwise it is set equal to the target.
    """
        
    if elem is None:
      elem = target
    
    self.currentOpData = opData = self.getOpData(target, opType, inClass)
    opSubTypes = opData['subOps'].keys()
    for opSubType in opSubTypes:
      op = metaUtil.getOperation(target, opType, inClass, opSubType)
      if op is None:
        if (self.operationData[opType]['targetTag'] == 'container'
            or elem.container is inClass):
          self.newOperation(opData, inClass, opSubType)
        else:
          # There should have been an inherited operation here.
          raise MemopsError(
           "new '%s' function for %s made in %s. Should have been inherited" 
           % (opType, elem.qualifiedName(), inClass.qualifiedName())
          )
      else:
        try:
          self._tempOpList.remove(op)
        except:
          pass
        self.checkOperation(op, opData, inClass, opSubType)
    #
    del self.currentOpData
    
    
  ###########################################################################

  ###########################################################################
    
  def newOperation(self, opData, inClass, opSubType=None):
    """ create a new operation
    """
    
    params = self.stdOperationData(opData, opSubType)
    params['documentation'] = self.getOpDocumentation(opData, inClass, 
                                                      opSubType)
    
    op = self.newElement(MetaModel.MetaOperation, container=inClass, **params)
    
    #parameters
    for parData in opData['subOps'][opSubType]['parameters']:
      self.newOpParameter(op, inClass, self.opParameterData(parData, op))
    
    # NBNB TBD this needs reworking
    self.addOperationExceptions(op, inClass)

    return op
    
  ###########################################################################

  ###########################################################################
    
  def checkOperation(self, op, opData, inClass, opSubType=None):
    """check an existing operation conforms to the rules, and adds missing
    information (target, parameters) where it can be deduced from context.
    """ 
    
    # check MetaOp input parameters
    params = self.stdOperationData(opData, opSubType)
    for (key, val) in params.items():
      if getattr(op, key) != val:
        raise MemopsError(
         "%s.%s value %s does not conform to standard %s"
         % (op.qualifiedName(), key, getattr(op, key), val)
        )
     
    # MetaParameters
    existingParNames = op._HasParameters__parameterNames[:]
    for parData in opData['subOps'][opSubType]['parameters']:
      pInput = self.opParameterData(parData, op)
      if pInput['name'] in existingParNames:
        existingParNames.remove(pInput['name'])
        self.checkOpParameter(op.getElement(pInput['name']), inClass, pInput)
      else:
        self.newOpParameter(op, inClass, pInput)
    #
    if existingParNames:
      raise MemopsError(
       "non-std. parameters named %s found for %s"
       % (existingParNames, op.qualifiedName())
      )
      
    
  ###########################################################################
        
  ###########################################################################
  
  def stdOperationData(self, opData, opSubType=None):
    """ get data describing a normal operation for checking or creation
    """
    
    # NBNB TBD get rid of 'isQuery'?
    # No, it is used in ApiGen.writeExternalOp
    
    opType = opData['opType']
    target = opData['target']
  
    result = {
     'name':self.getOperationName(target, opType, opSubType=opSubType),
     'isQuery':(opData['group'] == 'query'),
     'opType':opType,
     'opSubType':opSubType,
     'target':target,
    }
    
    dd = opData.get('taggedValues')
    if dd:
      result['taggedValues'] = dd
    
    isAbstract = opData.get('isAbstract')
    if isAbstract is not None:
      result['isAbstract'] = isAbstract
    elif opType in ('getByKey', 'getFullKey', 'getLocalKey', 'fullDelete', 'fullUnDelete'):
      result['isAbstract'] = False
    elif (isinstance(target, MetaModel.ClassElement) or
          self.operationData[opType]['targetTag'] == 'container'):
      result['isAbstract'] = target.isAbstract
    else:
      result['isAbstract'] = False
    
    scope = opData.get('scope')
    if scope is not None:
      result['scope'] = scope

    visibility = opData.get('visibility')
    if visibility is not None:
      result['visibility'] = visibility

    return result

  ###########################################################################

  ###########################################################################
    
  def getOperationName(self, target, opType, opSubType=None):
    """ get name of operation - NB does not use actual operation object, 
    which may not exist yet
    
    Note that opSubType!=None is used as an operation name suffix.
    If subOp is found and contains a 'suffix' item, this will be used instead.
    """
    
    # get opData
    if hasattr(self, 'currentOpData'):
      opData = self.currentOpData
    else:
      opData =  self.getOpData(target, opType)
    
    # get main name
    targetType = opData['targetTag']
      
    if targetType == 'masterOp':
      opName = target.name
    
    else:
      opName = opData.get('name') or opType
      
      if targetType != 'container':
        if 'useCollection' in opData and not opData['useCollection']:
          targetName = target.baseName
        else:
          targetName = target.name
        opName = opName + metaUtil.upperFirst(targetName)
    
    # handle subTypes
    if opSubType is None:
      return opName
    else:
      subOp = opData['subOps'].get(opSubType)
      if subOp is None:
        suffix = opSubType
      else:
        suffix = subOp.get('suffix') or opSubType
      return '%s_%s' % (opName, suffix)
    
  ###########################################################################

  ###########################################################################

  def getOpData(self, target, opType, inClass=None):
    """ Get opData for opType, taking special cases into account
    """
    
    if inClass is None:
      if isinstance(target, MetaModel.ComplexDataType):
        inClass = target
      else:
        inClass = target.container
    
    # NB this must be a copy, as it is being modified
    result = copy.deepcopy(self.operationData[opType])
    
    result['opType'] = opType
    result['target'] = target
    ###result['visibility'] = target.visibility
    
    if opType == 'init':
      if (isinstance(inClass, MetaModel.MetaDataObjType)
          or (not inClass.isAbstract and inClass.parentRole is None)):
        # remove 'parent' parameter for MemopsRoot and DataObjTypes

        for subData in result['subOps'].values():
          if subData['parameters']: # can have zero-argument constructor
            del subData['parameters'][0] 
    
    elif opType == 'getByKey':
      pr1 = inClass.parentRole
      if pr1 is not None and (
       pr1.valueType.parentRole is None
       or inClass.container.qualifiedName() == self.implPackageName
      ):
        # TopObject or in Implementation - change startObj typing to MemopsRoot
        for subOp in result['subOps'].values():
          ll = [x for x in subOp['parameters'] if x['name'] == 'startObj']
          ll[0]['target'] = self.dataRootName
    #
    return result
    
  ###########################################################################

  ###########################################################################
    
  def getOpDocumentation(self, opData, inClass, opSubType=None, 
                         copyElemDoc=True):
    """ get documentation for generated operation
    """
  
    opType = opData['opType']
    subOpData = opData['subOps'][opSubType]
    target = opData['target']
    template = subOpData.get('opDocTemplate')
    if template:
      result = template % target.qualifiedName()
    else:
      result = (self.opDocTemplate %
                (metaUtil.upperFirst(opType), target.qualifiedName()))
    
    if (copyElemDoc and 
        opData['targetTag'] not in ('container', 'masterOp', 'ChildClass')):
      ss = target.documentation.strip()
      if ss:
        result = '%s\n\n%s' % (result, ss)
    #
    return result
    
    
  ###########################################################################

  ###########################################################################
    
  def newOpParameter(self, op, inClass, params):
    """ Delegate Operation parameter creation to appropriate function
    """
    self.newElement(MetaModel.MetaParameter, container=op, **params)
    
  ###########################################################################

  ###########################################################################
    
  def checkOpParameter(self, par, inClass, params):
    """check an existing operation parameter conforms to the rules.
    """ 
    # parameter attributes to ignore
    skip = ('documentation',)
    
    for (key, val) in params.items():
      if key not in skip:
        if getattr(par, key) != val:
          raise MemopsError(
           "%s.%s value %s does not conform to standard %s"
           % (par.qualifiedName(), key, getattr(par, key), val)
          )
    
  ###########################################################################

  ###########################################################################
    
  def opParameterData(self, parData, op):
    """ Delegate Operation parameter creation to appropriate function
    """
    
    # set up
    name = parData['name']
    
    if 'target' in parData:
    
      # use explicit target 
      target = parData['target']
      
      if isinstance(target, StringType):
        # target is string - convert to object
        target = self.modelPortal.metaObjFromQualName(target)
        
    else:
      # no explicit parameter target in parData
      
      if name == 'parent':
        # special case - parent role
        # the 'or' will happen if such a parameter is used on 
        # a class without parentRole, which must be abstract by definetion
        # - in practice an init for an abstract class
        # It happens in Python, maybe nowhere else, but meanwhile this
        # prevents crashes lower down
        target = (op.container.parentRole
                  or op.metaObjFromQualName(self.baseClassName))
            
      elif name == 'self':
        # special case - self
        target = op.container
      
      else:
        # use op.target
        target = op.target
        if isinstance(target, MetaModel.MetaOperation):
          # 'other' op can not have parameters default to target
          raise MemopsError("parameter %s lacks explicit target" % name)

    parData['target'] = target
    result = self.stdOpParameterData(parData)
    
    # postprocessing - name can be reset only afterwards
    if name == 'value':
      hicard = result.get('hicard', 1)
      if hicard != 1:
        result['name'] = 'values'
        
    # change name if it is a varName
    ss = result['name']
    result['name'] = self.varNames.get(ss) or ss
    #
    return result
    
  ###########################################################################

  ###########################################################################
    
  def stdOpParameterData(self, parData):
    """
    """
    
    result = {} 
    
    # get target. 
    target = parData.get('target')
    
    # valueType
    if isinstance(target, MetaModel.ClassElement):
      result['valueType'] = target.valueType
    
      if parData.get('useCollection') and target.hicard != 1:
        # collection parameter
        for tag in ('isUnique', 'isOrdered', 'hicard','locard'):
          result[tag] = getattr(target, tag)

    elif parData.get('useCollection'):
      # error
      try:
        ss = target.qualifiedName()
      except:
        ss = str(target)
      raise MemopsError(
       "parameter %(name)s with 'useCollection':%(useCollection)s has target "
       % parData + ss
      )
      
    else:
      result['valueType'] = target
    
    # get values from parData, overriding if necessary  
    # mandatory parameters     
    for tag in MetaModel.MetaParameter.parameterData.keys():
      if tag in parData:
        result[tag] = parData[tag]
        
    if 'defaultValue' in parData:
      # NB this would no longer work if you could have hicard!=1 here.
      result['locard'] = 0
    
    # tagged values
    tv = parData.get('taggedValues')
    if tv is not None:
      # necessary as the dictionary may be modified elsewhere
      result['taggedValues'] = tv.copy()
    
    # add documentation
    result['documentation'] = self.parDocumentation(parData)
    #
    return result
      
  ###########################################################################

  ###########################################################################
    
  def parDocumentation(self, parData):
    """ make documentation for generated parameter
    """
  
    result = parData.get('parDocumentation')
    name = parData['name']
    if result is None:
      result = self.parDocTemplate % (self.varNames.get(name) or name)
    else:
      result = result % self.varNames
    #
    return result
    
  ###########################################################################

  ###########################################################################

  # internal function (should be overridden for SQL, etc.)
  def addOperationExceptions(self, op, inClass):
    """NBNB TBD add exceptions raised"""
    pass

  ###########################################################################

  ###########################################################################
