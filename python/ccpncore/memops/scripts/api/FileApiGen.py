from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import Util as metaUtil

from ccpncore.memops.scripts.api.ApiGen import ApiGen
from ccpncore.memops.scripts.api.FileApiInterface import FileApiInterface
MemopsError = MetaModel.MemopsError

# implements PermissionInterface, PersistenceInterface, TransactionInterface
# implements implementation-specific parts of ApiInterface
# requires LanguageInterface and rest of ApiInterface functionality to be implemented in subclass
# requires FileApiInterface functionality to be implemented in subclass
class FileApiGen(ApiGen, FileApiInterface):

  nameVar = 'name'
  urlVar = 'url'

  def __init__(self):
  
    # model flavour (must be done first) 
    self.addModelFlavour('implementation','file')
    
    super(FileApiGen, self).__init__()
    
    # add topObjectsToCheck collection parameters:
    dd = self.getStdCollectionParams('checkDelete', 'topObjectsToCheck')
    self.stdCollectionParams['topObjectsToCheck'] = dd
    dd['collection'] = 'topObjectsToCheck'
    ## below no good because self.topObject not defined yet
    ##dd['varType'] = self.elementVarType[self.topObject]
    pp = self.modelPortal.topPackage
    impl = pp.metaObjFromQualName(self.implPackageName)
    dd['varType'] = self.elementVarType(impl.getElement(metaConstants.baseClassName))
    
    # special trick to avoid continous checking of topObject.isLoaded
    # is checked in possiblyLoadData
    self.topObjectPreloaded = False

  ###########################################################################

  ###########################################################################
  # implementation of PermissionInterface
  ###########################################################################

  ###########################################################################

  # implements PermissionInterface
  def checkPermission(self, op, inClass):

    # NOTE: this code goes hand in hand with endTransaction code

    opType = op.opType
    
    if opType in ('get', 'sorted', 'findFirst', 'findAll', 
                  'checkValid', 'checkAllValid', 'getByKey', 'getFullKey', 
                  'getLocalKey'):
      # no permission checking here

      return
      
    elif isinstance(inClass, MetaModel.MetaDataObjType):
      # no permission checking here either

      return


    elif opType in ('set', 'add', 'remove'):
      # NB this will do nothing for DataObjTypes, not should it
      
      element = op.target
        
      if (element.name == 'isModifiable'
          and element.container in (self.topObject, self.dataRoot)):
        # exception for isModifiable, or you could never unset it
        return
      
      # 'topObject' must have been set at this point

      if element.changeability != metaConstants.frozen:
      
        if (isinstance(element, MetaModel.MetaRole) and 
            self.couldHaveMultipleStoragesToCheck(element)):
          var = self.stdCollectionParams['topObjectsToCheck']['collection']
          varType = self.collectionType(self.baseClass, isUnique=True, isOrdered=False)
          self.defineVar(var, varType)
          self.setVar(var, self.toLiteral(None)) # needed to keep Java compiler happy

        self.startIf(self.varNames['notIsReading'])
      
        if (isinstance(element, MetaModel.MetaRole) and 
            self.couldHaveMultipleStoragesToCheck(element)):
          # need to do complicated runtime check on storages
          # first figure out which storages to check
          # create topObjectsToCheck, which should be a Set
          self.newCollection(**self.stdCollectionParams['topObjectsToCheck'])

          # add self.storage straight off if not in constructor
          self.startIf(self.varNames['notInConstructor'])
          self.addStorageToCheck(self.varNames['self'], inClass)
          self.endIf()

          # this is so complicated that set out each case in separate function
          if element.hicard == 1:
            self.checkPermission1X(op, inClass)
          else: # hicard != 1
            if element.otherRole and element.otherRole.hicard == 1:
              self.checkPermissionN1(op, inClass)
            else:
              self.checkPermissionNN(op, inClass)

          # now do actual checks on storages
          self.checkStoragesModifiable()

        else: # attrs or roles where only need to check self.storage
          self.startIf(self.varNames['notInConstructor'])
          self.checkStorageModifiable(self.varNames['topObject'], 
                                      inClass=inClass)
          self.endIf()

        self.endIf() # end of notIsReading
      
    elif opType == 'init':

      clazz = op.container
      if (self.topObject not in clazz.getAllSupertypes() 
          and clazz is not self.dataRoot):
        self.writeNewline()
        self.startIf(self.varNames['notIsReading'])
        self.checkStorageModifiable(self.varNames['topObject'], inClass=inClass)
        self.endIf()
    
    elif opType == 'fullDelete':

      self.startIf(self.varNames['notInConstructor'])
      self.checkStoragesModifiable()
      self.endIf()

    elif opType == 'fullUnDelete':

      self.checkStoragesModifiable()

    elif opType in self.operationData.keys():

      # TBD: is there any way of knowing what storages should be checked?
      pass

    else:

      raise MemopsError('unknown opType "%s"' % opType)

  ###########################################################################

  ###########################################################################

  # internal function
  def couldHaveMultipleStoragesToCheck(self, role):

    # is this correct: what if package is content storage?
    # Yes - as links between different extents of the same packages are illegal
    if (role.otherRole 
        and role.container.container is not role.valueType.container):
      return True
    else:
      return False

  ###########################################################################

  ###########################################################################

  # internal function
  def addStorageToCheck(self, var, varClass):

    topObj = self.varNames['topObject']
    self.getImplLink(var, 'topObject', topObj, varClass)
    self.addCollection(topObj, **self.stdCollectionParams['topObjectsToCheck'])

  ###########################################################################

  ###########################################################################

  # internal function
  def checkStoragesModifiable(self):

    # TBD: this will not work for Java, need to substitute real type ???
    self.startLoop('topObjectToCheck',
     **self.stdCollectionParams['topObjectsToCheck']
    )
    self.checkStorageModifiable('topObjectToCheck')
    self.endLoop()

  ###########################################################################

  ###########################################################################

  # internal function
  def checkStorageModifiable(self, storage, inClass=None):
    
    if inClass and inClass.container.topObjectClass is self.dataRoot:
      elem = self.dataRoot.getElement('isModifiable')
    else:
      elem = self.topObject.getElement('isModifiable')
    
    self.startIf(self.negate(
     self.boolean(self.getValue(storage, elem, lenient=True, inClass=inClass)))
    )
    self.raiseApiError('Storage not modifiable', storage)
    self.endIf()

  ###########################################################################

  ###########################################################################

  # PyApiGen note: crosslinks between objects from Coords or ChemComp (etc.) must be intrafile
  # TBD: this adds extra checks

  ###########################################################################

  ###########################################################################

  # internal function
  # role.hicard = 1, otherRole.hicard = whatever. NB otherRole may be None
  def checkPermission1X(self, op, inClass):

    role = op.target
    otherRole = role.otherRole
    
    if otherRole is not None:
      # there is nothing here for one-way links to check
    
      # add new value storage
      var = self.valueVar(role)
      self.startIf(self.valueIsNotNone(var))
      self.addStorageToCheck(var, role.valueType)
 
      if otherRole.hicard == 1:
        # add oldSelf storage
        self.getValue(var, otherRole, self.oldSelfVar, lenient=True,
                      inClass=inClass)
        self.startIf(self.valueIsNotNone(self.oldSelfVar))
        self.startIf(self.varNames['notIsReading'])
        self.addStorageToCheck(self.oldSelfVar, inClass)
        self.elseIf()
        self.raiseApiError("Read link incompatible with pre-existing link",
                           self.varNames['self'], inOp=op)
        self.endIf()
        self.endIf()
 
      self.endIf() # end of valueIsNotNone(var)
 
      # add old value storage
      currentVar = self.valueVar(role, prefix=self.currentPrefix)
      # currentVar already set at top of function
      self.startIf(self.valueIsNotNone(currentVar))
      self.addStorageToCheck(currentVar, role.valueType)
      self.endIf()

  ###########################################################################

  ###########################################################################

  # internal function
  # role.hicard != 1, otherRole.hicard = 1
  # NB otherRole must exist for us to get here
  def checkPermissionN1(self, op, inClass):
    
    opType = op.opType
    role = op.target
    otherRole = role.otherRole

    if opType == 'set':
      var = self.valueVar(role)
      currentVar = self.valueVar(role, prefix=self.currentPrefix)
      # currentVar already set at top of function
      iterVar = 'pv'
 
      # add old value storage if old value not in new values for all cases
      self.startLoop(iterVar, currentVar, **self.collectionParams(role))
      self.startIf(self.negate(self.isInCollection(iterVar, var, **self.collectionParams(role))))
      self.addStorageToCheck(iterVar, role.valueType)
      self.endIf()
      self.endLoop()

      # add new value storage if new value not in old value,
      # AND/OR add all oldself storages
      # NB we need the loop in either case

      self.startLoop(iterVar, var, **self.collectionParams(role))
 
      # add new value storage if new value not in old values
      self.startIf(self.negate(self.isInCollection(iterVar, currentVar, **self.collectionParams(role))))
 
      self.addStorageToCheck(iterVar, role.valueType)
 
      # add old self storage
      self.getValue(iterVar, otherRole, self.oldSelfVar, lenient=True,
                    inClass=inClass, needVarType=False)
      self.startIf(self.valueIsNotNone(self.oldSelfVar))
      self.startIf(self.varNames['notIsReading'])
      self.addStorageToCheck(self.oldSelfVar, inClass)
      self.elseIf()
      self.raiseApiError("Read link incompatible with pre-existing link",
                         self.varNames['self'], inOp=op)
      self.endIf()
      self.endIf()
 
      self.endIf()
 
      self.endLoop()
  
    elif opType == 'add':
      var = self.valueVar(role, doInstance=True)
      self.addStorageToCheck(var, role.valueType)
      # oldSelfVar already declared at top of function
      self.getValue(var, otherRole, self.oldSelfVar, inClass=inClass, needVarType=False)
      self.startIf(self.valueIsNotNone(self.oldSelfVar))
      self.addStorageToCheck(self.oldSelfVar, inClass)
      self.endIf()

    elif opType == 'remove':
      var = self.valueVar(role, doInstance=True)
      self.addStorageToCheck(var, role.valueType)

    else:
      raise MemopsError('disallowed opType "%s"' % opType)

  ###########################################################################

  ###########################################################################

  # internal function
  # role.hicard != 1, otherRole is None or otherRole.hicard != 1
  def checkPermissionNN(self, op, inClass):

    opType = op.opType
    role = op.target
    otherRole = role.otherRole
    
    if otherRole:
      # for one-way links there is nothing here to check
      
      if opType == 'set':
        var = self.valueVar(role)
        currentVar = self.valueVar(role, prefix=self.currentPrefix)
        # currentVar already set at top of function
        iterVar = 'pv'
  
        # add old value storage if old value not in new values
        self.startLoop(iterVar, currentVar, **self.collectionParams(role))
        self.startIf(self.negate(self.isInCollection(
         iterVar, var, **self.collectionParams(role)))
        )
        self.addStorageToCheck(iterVar, role.valueType)
        self.endIf()
        self.endLoop()

        # add new value storage if new value not in old values
        self.startLoop(iterVar, var, **self.collectionParams(role))
        self.startIf(self.negate(self.isInCollection(
         iterVar, currentVar, **self.collectionParams(role)))
        )
        self.addStorageToCheck(iterVar, role.valueType)
        self.endIf()
        self.endLoop()
  
      elif opType in ('add', 'remove'):
        var = self.valueVar(role, doInstance=True)
        self.addStorageToCheck(var, role.valueType)

      else:
        raise MemopsError('unknown opType "%s"' % opType)

  ###########################################################################

  ###########################################################################
  # implementation of PersistenceInterface
  ###########################################################################

  ###########################################################################

  # implements PersistenceInterface
  def getValue(self, owner, element, var=None, needVarType=True, 
              lenient=False, convertCollection=True, inClass=None,
              castType=None):
    """ get value of element.
    If var is None, return string expression, else set var to value and write.
    If not lenient will load packages as necessary to guarantee correct result.
    If convertCollection will convert collections that are stored differently
    (child links) to correct type. 
    
    """
    
    if var is None and not lenient:
      raise MemopsError("getValue cannot return expression if lenient=False")
    
    if inClass is None:
      inClass = element.container
    
    if element.isDerived:
      
      funcname = self.getFuncname(metaUtil.getOperation(element,'get'))
      valString = self.callFunc(funcname, owner, doWrite=False)
    
    elif element.isImplementation:
      if isinstance(element, MetaModel.MetaAttribute):
        valString = self.getImplAttr(owner, element.name, inClass)
      else:
        # implementation link
        if var is None or needVarType:
          funcname = self.getFuncname(metaUtil.getOperation(element,'get'))
          valString = self.callFunc(funcname, owner, doWrite=False)
        else:
          self.getImplLink(owner, element.name, var, element.container, castType=castType)
          return
    
    else:
      # non-derived link
      
      if not lenient:
        # load data if necessary
        self.possiblyLoadData(owner, element, inClass=inClass)
 
      valString = self.getMemoryValue(owner, element)
      
      
      if (element.hicard != 1 and isinstance(element,MetaModel.MetaRole)
          and element.hierarchy == metaConstants.child_hierarchy):
        # handle child links
        
        ###valString = self.getDictValues(valString, isUnique=element.isUnique, isOrdered=element.isOrdered)
        valString = self.getDictValues(valString)
        
        if convertCollection:
          # convert collection to correct type
          valString = self.newCollection(None, initValues=valString, 
                                         **self.collectionParams(element))
        
    # finalise and return 
    if var is None:
      return valString
 
    else:
      if element.hicard == 1:
        varType = self.elementVarType(element)
      else:
        varType = self.collectionType(element, useCollection=not convertCollection)
 
      self.setVar(var, valString, varType=varType)

  ###########################################################################

  ###########################################################################
  
  def possiblyLoadData(self, owner, element, inClass=None):
    """ Load data necessary for getting element from owner
    """
    
    rootVar = self.varNames['root']
        
    eName = element.name
    container = element.container
    if inClass is None:
      inClass = container
    
    if not isinstance(container, MetaModel.MetaClass):
      # DataObjType - nothing doing
      return
    
    if (element.isDerived or element.isImplementation 
        or element is container.parentRole):
      # never triggers load
      return
      
    isTopObject = (self.topObject in container.getAllSupertypes())
    
    if isTopObject:
      # TopObject - may need loading
      if isinstance(element, MetaModel.MetaAttribute):
        return
      elif eName in container.keyNames:
        return
      elif self.topObject in element.valueType.getAllSupertypes():
        pass
      elif not self.topObjectPreloaded:
        # element may require loading. Load if necessary
        if owner == self.varNames['self']:
          self.startIf(self.negate(self.logicalOp(
           self.boolean(self.getImplAttr(owner, 'isLoaded')), 'or',
           self.boolean(self.getImplAttr(owner, 'isReading'))))
          )
        else:
          self.startIf(self.negate(self.boolean(self.getImplAttr(owner, 
                                                                 'isLoaded'))))
        self.callFunc('load', owner)
        self.endIf()
            
    elif container is self.dataObject:
      # NB DataObject has to be included as functions defined here are 
      #    inherited down to TopObjects.
      #    This will result in some unnecessary checks, but since DataObject
      #    functions can not appear in Implementation they should
      #    not break anything 
      if element.isImplementation:
        pass
        
      else:
        # element may require loading. Load if necessary
        ss = self.getImplAttr(owner, 'topObject', inClass=inClass)
        if owner == self.varNames['self']:
          self.startIf(self.negate(self.logicalOp(
           self.boolean(self.getImplAttr(ss, 'isLoaded')), 'or',
           self.boolean(self.getImplAttr(ss, 'isReading'))))
          )
        else:
          self.startIf(self.negate(self.boolean(self.getImplAttr(ss, 
                                                                 'isLoaded'))))
        self.callFunc('load', ss)
        self.endIf()
        
 
    if isinstance(element, MetaModel.MetaRole):
      otherRole = element.otherRole
      valueType = element.valueType
      vtPackage = valueType.container.qualifiedName()
      if otherRole is None or element.canAccess(otherRole):
        # same or imported package
        if valueType is self.baseClass:
          # NBNB this should load all known TopObjects
          # this is the AccessObject-DataObject link
          self.defineVar(rootVar, self.elementVarType(self.dataRoot))
          self.getImplLink(self.varNames['self'], 'root', rootVar, inClass)
          for role in self.dataRoot.getAllRoles():
            if role.hierarchy == metaConstants.child_hierarchy:
              self.callFunc('refreshTopObjects', rootVar, 
                        params=self.toLiteral(role.valueType.packageName))
        else:
          pass
      
      elif container.container is self.implPackage:
        # link from root to TopObject or 'current' link or DataObject.access
        if element.hierarchy == metaConstants.child_hierarchy:
          # link from root to TopObject
          if owner != rootVar:
            self.defineVar(rootVar, self.elementVarType(self.dataRoot))
            self.getImplLink(self.varNames['self'], 'root', rootVar, inClass)
          self.callFunc('refreshTopObjects', rootVar, 
                        params=self.toLiteral(vtPackage))
      
      elif (isTopObject and 
            self.topObject in valueType.getAllSupertypes()):
            #and otherRole.name in valueType.keyNames):
        # link between two topObjects, 
        # now guaranteed to be loaded without explicit load
        if element.hicard == 1:
          self.startIf(self.valueIsNone(self.getMemoryValue(owner, element)))
        self.defineVar(rootVar, self.elementVarType(self.dataRoot))
        self.getImplLink(self.varNames['self'], 'root', rootVar, inClass)
        self.callFunc('refreshTopObjects', rootVar, 
                      params=self.toLiteral(vtPackage))
        if element.hicard == 1:
          self.endIf()
      
      else:
          
        self.startBlock()
 
        if element.hicard == 1:
          self.startIf(self.valueIsNone(self.getMemoryValue(owner, element)))
 
        elif element.hicard > 1:
          self.startIf(self.comparison(
           self.lenCollection(self.getMemoryValue(owner, element),
           **self.collectionParams(element)), '<', self.hicard)
          )
           
        # check if there is a partitioning link to help us
        uplinks, partitionRoles = self.getPartitioningLinkages(element)
        crossRole = partitionRoles[0]
        if crossRole:
          toTopObj = (valueType.container.topObjectClass 
                      in crossRole.valueType.getAllSupertypes())
        if crossRole and (toTopObj or crossRole.hicard >= 1):
          # partitioning role - use it
          
          if len(uplinks[0]) == 1:
            # special case - first link may be topObject:
            rr = uplinks[0][0]
            if rr is container.getElement(self.varNames['topObject']):
              # special case - first link is topObject:
              useType = self.elementVarType(container.container.topObjectClass)
            else:
              useType = self.elementVarType(rr)
            varName = 'xx1'
            self.defineVar(varName, useType)
            self.getValue(owner, rr, var=varName, needVarType=False,
                          inClass=inClass, castType=useType, lenient=True)
          
          else:
            # several links up - loop.
            varName = owner
            ii = 0
            for rr in uplinks[0]:
              ii += 1
              ss = 'xx%s' % ii
              # next two lines look silly,
              # but allow faster getting of Implementation links
              self.defineVar(ss, self.elementVarType(rr))
              self.getValue(varName, rr, var=ss, needVarType=False,
                            inClass=inClass, lenient=True)
              varName = ss
          
          if toTopObj:
            if crossRole.hicard == 1:
              self.getValue(varName, crossRole, var='tobj', needVarType=False, 
                            inClass=inClass)
              if crossRole.locard < 1:
                self.startIf(self.valueIsNotNone('tobj'))
              self.startIf(self.negate(self.boolean(
                           self.getImplAttr('tobj', 'isLoaded'))))
              self.callFunc('load', 'tobj')
              self.endIf()
              if crossRole.locard < 1:
                self.endIf()
            else:
              self.startLoop('tobj', 
                             self.getValue(varName, crossRole, lenient=True,
                                           inClass=inClass),
                             **self.collectionParams(crossRole))
              self.startIf(self.negate(self.boolean(
                           self.getImplAttr('tobj', 'isLoaded'))))

              self.callFunc('load', 'tobj')
              self.endIf()
              self.endLoop()
              
          else:
            # crosslink here. 
            self.possiblyLoadData(varName, crossRole, inClass=inClass)
        
        else:
          # No partitioning role - load all relevant files
          self.loadPackage(owner, element, inClass=inClass,
                           convertCollection=False)
          
        if element.hicard >= 1:
          self.endIf()
        
        self.endBlock()
       
  ###########################################################################

  ###########################################################################
  
  # internal function
  def loadPackage(self, owner, element, inClass=None, convertCollection=True):
    """ load all TopObjects in a given package
    """
  
    tobjList = 'tobjList'
    rootVar = self.varNames['root']
    if inClass is None:
      inClass = element.container
  
    # No partitioning role - load all relevant files
    topObjRole = element.valueType.container.topObjectClass.parentRole.otherRole
    
    self.defineVar(rootVar, self.elementVarType(self.dataRoot))
    self.getImplLink(self.varNames['self'], 'root', rootVar, inClass)
    self.getValue(rootVar, topObjRole, tobjList, inClass=inClass,
                  convertCollection=convertCollection)
    self.startLoop('tobj', tobjList,
                   **self.collectionParams(topObjRole))
    self.startIf(self.negate(self.boolean(
                             self.getImplAttr('tobj', 'isLoaded'))))

    self.callFunc('load', 'tobj')
    self.endIf()
    self.endLoop()
       
  ###########################################################################

  ###########################################################################

  # implements PersistenceInterface
  def setSerialValue(self, inClass, value):
    
    attrName = metaConstants.serial_attribute
    element = inClass.getElement(attrName)
    selfVar = self.varNames['self']
    parentVar = self.varNames['parent']
    intType = self.elementVarType(element)
    dictKey = self.toLiteral(inClass.parentRole.otherRole.name)
    
    self.startBlock()
    self.defineVar(parentVar, self.elementVarType(inClass.getParentClass()))
    self.getImplLink(selfVar, 'parent', parentVar, inClass)
    ss = self.getImplAttr(parentVar, metaConstants.serialdict_attribute)
    self.setVar('oldSerial', self.getDictEntry(ss, dictKey), intType, intType)
    self.initSerialDictIfNull(inClass.parentRole.otherRole.name)
    self.startIf(self.comparison(value, '<', self.toLiteral(0)))
    self.setVar(value, self.arithmetic('oldSerial', '+', self.toLiteral(1)))
    self.setDictEntry(ss, dictKey, value)
    self.elseIf(self.comparison(value, '>', 'oldSerial'))
    self.setDictEntry(ss, dictKey, value)
    self.endIf()
    self.setValue(selfVar, element, value)
    self.endBlock()
    
  ###########################################################################

  ###########################################################################

  # implements PersistenceInterface
  def setIdValue(self, inClass, value):

    attrName = metaConstants.id_attribute
    idVar = metaConstants.lastid_attribute
    element = inClass.getElement(attrName)
    selfVar = self.varNames['self']
    #parentVar = self.varNames['parent']
    intType = self.elementVarType(element)
    #dictKey = self.toLiteral(inClass.parentRole.otherRole.name)

    self.startBlock()
    #self.defineVar(parentVar, self.elementVarType(inClass.getParentClass()))
    #self.getImplLink(selfVar, 'parent', parentVar, inClass)
    ss = self.getImplAttr(self.varNames['topObject'], idVar)
    self.setVar(idVar, ss, intType, intType)
    #self.initSerialDictIfNull(inClass.parentRole.otherRole.name)
    self.startIf(self.comparison(value, '<', self.toLiteral(0)))
    self.setVar(value, self.arithmetic(idVar, '+', self.toLiteral(1)))
    self.setImplAttr(self.varNames['topObject'], idVar, value, inClass)
    #self.setDictEntry(ss, dictKey, value)
    self.elseIf(self.comparison(value, '>', idVar))
    #self.setDictEntry(ss, dictKey, value)
    self.setImplAttr(self.varNames['topObject'], idVar, value, inClass)
    self.endIf()
    self.setValue(selfVar, element, value)
    self.endBlock()

  ###########################################################################

  ###########################################################################
  # implementation of TransactionInterface
  ###########################################################################

  ###########################################################################

  # implements TransactionInterface
  def startTransaction(self, op, inClass):
    
    if op.opType == 'init' and isinstance(inClass, MetaModel.MetaClass):
      # force all necessary load of TopObjects
      parentVar = self.varNames['parent']
      selfVar = self.varNames['self']
      
      parentRole = inClass.parentRole
      if parentRole is not None:
        # non-MemopsRoot class.
        
        if self.topObject in inClass.getAllSupertypes():
          # topObject refreshTopObjects
          self.startIf(self.negate(self.boolean(
           self.getImplAttr(selfVar, 'isReading')))
          )
          self.callFunc('refreshTopObjects', parentVar, 
                        params=self.toLiteral(inClass.container.qualifiedName()))
          self.endIf()
        
        elif self.topObject in parentRole.valueType.getAllSupertypes():
          # child of TopObject. Force package load if necessary
          self.startIf(self.negate(self.logicalOp(
           self.boolean(self.getImplAttr(parentVar, 'isLoaded')), 'or',
           self.boolean(self.getImplAttr(parentVar, 'isReading'))))
          )
          self.callFunc('load', parentVar)
          self.endIf()
          
      # NB you just loaded, or the package is known to be loaded anyway
      self.topObjectPreloaded = True
    

  ###########################################################################

  ###########################################################################

  # implements TransactionInterface
  def endTransaction(self, op, inClass):

    opType = op.opType

    # NOTE: this code goes hand in hand with startTransaction and checkPermission code

        
    if opType in ('get', 'sorted', 'findFirst', 'findAll', 
                  'checkValid', 'checkAllValid', 'getByKey', 'getFullKey',
                  'getLocalKey'):
    
      return
    
    elif not isinstance(inClass, MetaModel.MetaClass):
      # nothing doing for DataObjTypes
      return

    elif opType in ('set', 'add', 'remove'):
      
      element = op.target

      if element.changeability != metaConstants.frozen:
        self.startIf(self.varNames['notIsReading'])
        if isinstance(element, MetaModel.MetaAttribute):
          self.startIf(self.varNames['notInConstructor'])
          self.setImplAttr(self.varNames['topObject'], 'isModified', True)
          self.endIf()
        elif isinstance(element, MetaModel.MetaRole):
          if self.couldHaveMultipleStoragesToCheck(element):
            if self.topObject in element.valueType.getAllSupertypes():
              self.setStoragesModified(loadFirst=True)
            else:
              self.setStoragesModified()
              
          else:
            self.startIf(self.varNames['notInConstructor'])
            self.setImplAttr(self.varNames['topObject'], 'isModified', True)
            self.endIf()
        self.endIf() # end of notIsReading

    elif opType == 'init':
    
      self.topObjectPreloaded = False
      
      clazz = op.container

      # TBD: anything else?
      if self.dataRoot not in clazz.getAllSupertypes():
        self.startIf(self.varNames['notIsReading'])
        self.setImplAttr(self.varNames['topObject'], 'isModified', True)
        self.endIf()

    elif opType == 'fullDelete':

      self.setStoragesModified(loadFirst=True)

    elif opType == 'fullUnDelete':

      self.setStoragesModified()

    elif opType in self.operationData.keys():

      # TBD: is there anything to do??
      pass

    else:

      raise MemopsError('unknown opType "%s"' % opType)

  ###########################################################################

  ###########################################################################

  # internal function
  def setStoragesModified(self, loadFirst=False):

    self.startLoop('topObjectModify',
                   **self.stdCollectionParams['topObjectsToCheck'])
    if loadFirst:
      self.startIf(self.negate(self.getImplAttr('topObjectModify', 'isLoaded')))
      self.callFunc('load', 'topObjectModify')
      self.endIf()
    self.setImplAttr('topObjectModify', 'isModified', True)
    self.endLoop()

  ###########################################################################

  ###########################################################################
  # implementation of ApiInterface
  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def shouldDoNotifies(self, op, inClass):

    opType = op.opType
    dd = self.varNames

    if opType == 'init':
      return dd['notOverride']
    # elif opType == 'fullDelete':
      # return self.logicalOp(self.negate(self.getImplAttr(self.varNames['self'],
      #  'inConstructor', inClass)),'and', dd['notOverride']
      # )
    else:
      return self.logicalOp(dd['notInConstructor'], 'and', dd['notOverride'])

  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def shouldDoUndos(self, op, inClass):

    opType = op.opType
    dd = self.varNames

    if opType == 'init':
      return dd['notIsReading']
    elif opType == 'fullDelete':
      return self.logicalOp(self.negate(self.getImplAttr(self.varNames['self'],
       'inConstructor', inClass)),'and', dd['notIsReading']
      )
    else:
      return self.logicalOp(dd['notInConstructor'], 'and', dd['notIsReading'])

  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def shouldDoInitChecks(self, op, inClass):

    return self.varNames['notOverride']

  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeInitConstructor(self, op, inClass):
    
    vn = self.varNames
    
    self.writeNewline()
    
    overrideElem = inClass.getElement('override')
    
    if isinstance(inClass, MetaModel.MetaClass):
    
      if inClass.container.topObjectClass is self.dataRoot:
        self.defineVar(vn['topObject'], self.elementVarType(self.dataRoot))
      else:
        self.defineVar(vn['topObject'], self.elementVarType(self.topObject))
 
      supertypes = inClass.getAllSupertypes()
 
      if inClass is self.dataRoot:
        # MemopsRoot

        self.setVar(vn['topObject'], vn['self'])
        self.setImplLink(vn['self'], 'topObject', vn['topObject'], inClass)
                         
        bbVar = 'bb'
        varType = self.elementVarType(self.booleanType)
        isReading = self.getDictEntry(vn['attrlinks'], self.toLiteral(vn['isReading']),
                                      defaultValue=self.toLiteral(False))
        self.setVar(bbVar, isReading, varType=varType, castType=varType)
        self.startIf(self.logicalOp(self.valueIsNotNone(bbVar), 'and', self.boolean(bbVar)))
                              
        self.removeDictEntry(vn['attrlinks'], self.toLiteral(vn['isReading']))
        self.setImplAttr(vn['self'], 'isLoaded', False)
        self.setImplAttr(vn['self'], 'isModified', False)
        self.setImplAttr(vn['self'], 'isReading', True)
        
        self.elseIf()
        self.setImplAttr(vn['self'], 'isLoaded', True)
        self.setImplAttr(vn['self'], 'isModified', True)
        self.setImplAttr(vn['self'], 'isReading', False)
        self.endIf()
        
        # set override
        ll = overrideElem.defaultValue
        if ll:
          defval = ll[0]
        else:
          defval = False
        self.setVar(vn['override'], 
         self.getDictEntry(vn['attrlinks'], self.toLiteral(vn['override'])),
         self.booleanType, self.booleanType
        )
        self.startIf(self.valueIsNone(vn['override']))
        self.setValue(vn['self'], overrideElem, self.toLiteral(defval))
        self.elseIf()
        self.setValue(vn['self'], overrideElem, vn['override'])
        self.endIf()
 
      elif self.topObject in supertypes:
        # TopObject, not Implementation class
 
        self.setVar(self.varNames['topObject'], self.varNames['self'])
        self.setImplLink(self.varNames['self'], 'topObject',
                         self.varNames['topObject'], inClass)
                         
        # set implementation attributes
        # NBNB TBD check 'if condition' for non-python
        self.startIf(self.getDictEntry(self.varNames['attrlinks'],
            self.toLiteral(self.varNames['isReading']),
            castType=self.booleanType,
            defaultValue=self.toLiteral(False)))
        self.removeDictEntry(self.varNames['attrlinks'],
                             self.toLiteral(self.varNames['isReading']))
        self.setImplAttr(self.varNames['self'], 'isLoaded', False)
        self.setImplAttr(self.varNames['self'], 'isModified', False)
        self.setImplAttr(self.varNames['self'], 'isReading', True)
        
        self.elseIf(self.getImplAttr(self.varNames['parent'],'isReading'))
        self.setImplAttr(self.varNames['self'], 'isLoaded', False)
        self.setImplAttr(self.varNames['self'], 'isModified', False)
        self.setImplAttr(self.varNames['self'], 'isReading', True)
        
        self.elseIf()
        self.setImplAttr(self.varNames['self'], 'isLoaded', True)
        self.setImplAttr(self.varNames['self'], 'isModified', True)
        self.setImplAttr(self.varNames['self'], 'isReading', False)
        self.endIf()
 
      else:
        # non-topObject

        # storage same as parent for non-top classes
        self.getImplLink(self.varNames['parent'], 'topObject',
                         self.varNames['topObject'],
                         inClass.parentRole.valueType)
        self.setImplLink(self.varNames['self'], 'topObject',
                         self.varNames['topObject'], inClass)
    
    else:
      # set override
      ll = inClass.getElement('override').defaultValue
      if ll:
        defval = ll[0]
      else:
        defval = False
      self.setVar(vn['override'], 
         self.getDictEntry(vn['attrlinks'], self.toLiteral(vn['override'])),
         self.booleanType, self.booleanType
      )
      self.startIf(self.valueIsNone(vn['override']))
      self.setVar(vn['override'], self.toLiteral(defval))
      self.elseIf()
      self.removeDictEntry(vn['attrlinks'], self.toLiteral(vn['override']))
      self.endIf()

      self.startIf(self.boolean(vn['override']))
      self.setValue(vn['self'], overrideElem, vn['override'])
      self.endIf()
    
  ###########################################################################

  ###########################################################################
  
  def writeAddChildToParent(self, childVar, parentVar, parentRole, 
                            inClass=None, inUndo=False):
    
    dictVar = 'childrenDict'
    objKeyVar = 'objKey'
    
    if inClass is None:
      inClass = parentRole.container
      
      
    otherRole = parentRole.otherRole
    if otherRole.hicard == 1:
      # only child
      self.checkVarIsNone(self.getValue(parentVar, otherRole, lenient=True,
                                        inClass=inClass))
      self.setValue(parentVar, otherRole, childVar)
 
    else:
      # normal case, multiple children
      self.startBlock()
      
      self.writeNewline()
      if not inUndo:
        self.startIf(self.varNames['notIsReading'])
      self.setVar(dictVar, 
                  self.getMemoryValue(parentVar, otherRole),
                  self.dictType)
 
      # check hicard - NB hardwired here to avoid getting child collection
      hicard = otherRole.hicard
      if hicard != metaConstants.infinity:
        self.startIf(self.comparison(self.lenDict(dictVar),
                                     '>', hicard))
        self.raiseApiError('%s can have maximum %d %s'
                           % (otherRole.container, hicard, otherRole.name), 
                           self.varNames['self'])
        self.endIf()
 
      # get local key
      self.setLocalKeyVar(metaClass=inClass, sourceName=childVar, 
                       resultVar=objKeyVar)
 
      # make checks and set reverse link
      self.startIf(self.valueIsNone(objKeyVar))
      self.raiseApiError("Key attribute or link not set (from %s)" 
                         % inClass.keyNames, self.varNames['self'])
      self.elseIf()
      self.startIf(self.valueIsNone(self.getDictEntry(dictVar,objKeyVar)))
      self.setDictEntry(dictVar, objKeyVar, childVar)
      self.elseIf()
      self.raiseApiError("Could not create, pre-existing object had same key", 
                         self.varNames['self'])
      self.endIf()
      self.endIf()
      if not inUndo:
        self.endIf()
      
      self.endBlock()
    
  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeInitPreDelete(self, callingOp, inClass):

    self.writeNewline()
    self.writeComment('topObjects to check if modifiable')
    self.newCollection(needDeclType=True, **self.stdCollectionParams['topObjectsToCheck'])

  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeImplDoDelete(self, op, inClass):
    """ This cuts links from TopObjects to its children
    As the TopObject is kept alive in the MemopsRoot.topObjects dict 
    you need to cut the links to the children to get them garbage collected.
    
    NBNB this may cause special problems for undeletion.
    """
    
    if isinstance(inClass, MetaModel.MetaClass):
      if self.topObject in inClass.getAllSupertypes():
        for role in inClass.getAllRoles():
          if role.hierarchy == metaConstants.child_hierarchy:
            self.writeInitRoleDefault(role)
                         
  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def checkChildKeysUnique(self, op, inClass, role):
    # not done in file implementation

    pass

  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeImplPreDelete(self, op, inClass, role = None):
    
    if role:
    
      thatVar = role.baseName
      thoseVar = role.name
      if thoseVar == thatVar:
        thoseVar += '_s'
      
      if inClass.container is not role.otherRole.container.container:
        # other has different storage from self
        # add storage to storages dict

        if role.hicard == 1:
          self.addStorageToCheck(thatVar, role.valueType)

        else:
          # each 'other' may have a different storage
          self.startLoop(thatVar, thoseVar, **self.collectionParams(role))
          self.addStorageToCheck(thatVar, role.valueType)
          self.endLoop()

    else:

      self.addStorageToCheck(self.varNames['self'], inClass)

  ###########################################################################

  ###########################################################################
  
  def getKeyComponent(self, sourceName, sourceType, listOffset, elem, var):
    """ returns expression that evaluates to one key component
    May write several statements before returning
    """
    
    #print 'getKeyComponent', sourceName, sourceType, listOffset, elem.qualifiedName(), var

    if sourceType == 'dict':
      self.setVar(var, self.getDictEntry(sourceName, self.toLiteral(elem.name)))

    elif sourceType == 'obj':
      self.getValue(sourceName, elem, var, needVarType=False)

    elif elem.hicard == 1:
      self.setVar(var, 
       self.getByIndexInCollection(listOffset, sourceName, **self.listPars)
      )
    
    else:
      # source is list, hicard > 1 
      self.newCollection(var, **self.listPars)
      for ii in range(listOffset, listOffset + elem.hicard):
        ss = self.getByIndexInCollection(ii, sourceName, **self.listPars)
        self.addCollection(ss, var, **self.listPars)

  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeInitSerial(self, op, inClass):
    
    attrName = metaConstants.serial_attribute
    ddName = metaConstants.serialdict_attribute
    selfVar = self.varNames['self']
    element = inClass.getElement(attrName)
    serialKids = [x for x in inClass.getAllRoles() 
                  if (x.hierarchy == metaConstants.child_hierarchy and
                  x.valueType.getElement(attrName))]
    
    # set new serial if necessary
    
    if serialKids or element is not None:
    
      self.writeNewline()
      
      self.startBlock()
      if element is not None:
        self.startIf(self.varNames['notOverride'])
        self.startIf(self.valueIsNone(
         self.getValue(selfVar, element, lenient=True, inClass=inClass))
        )
        setterOp = metaUtil.getOperation(element, 'set', inClass=inClass)
        funcName = self.getFuncname(setterOp, inClass)
        self.setImplAttr(self.varNames['self'], 'inConstructor', True, inClass)
        self.callFunc(funcName, obj=selfVar, params=self.toLiteral(-1))
        self.setImplAttr(self.varNames['self'], 'inConstructor', False, inClass)
        self.elseIf()
        self.raiseApiError("Cannot pass in explicit serial if not reading",
                           'parent', self.toLiteral(inClass.qualifiedName()))
        self.endIf()
        self.endIf()
 
      # set up serialDict 
      if serialKids:
        self.newDict(ddName, keyType=self.elementVarType(self.stringType),
                     valueType=self.elementVarType(self.intType))
        for role in serialKids:
          self.setDictEntry(ddName, self.toLiteral(role.name),
                            self.toLiteral(0))
      self.endBlock()

  ###########################################################################

  ###########################################################################

  # implements FileApiInterface
  def setLocalKeyVar(self, metaClass, sourceName, resultVar, 
                  sourceType='obj', listOffset=None, needDefine=True):
    """ get object key for metaClass, taking data from source called
    sourceName, and setting the result to resultVar. 
    If the key is None or the required data are not found in the source
    sets resultVar to None
    
    sourceType may be 
    'obj'  (source is a model object), 
    'dict' (source is a dictionary,
    'list' (source is a list, starting at listOffset)
    
    The function returns the next list offset to use for getting data 
    - if sourceType is not 'list', None is returned 
    
    NB - The resulting code looks a little odd for sourceType == 'list'
    (i.e. getByKey).
    It does work, though, and optimisation would require duplicating this
    function for little actual gain. 
    """
    
    listVar = 'll'
    
    # check input and set up
    if sourceType not in ('obj', 'dict', 'list'):
      raise MemopsError("Illegal sourceType %s passed to setLocalKeyVar" 
                        % sourceType)
    
    if sourceType == 'list' :
      if listOffset is None:
        raise MemopsError(
         "sourceType 'list' passed to setLocalKeyVar with no listOffset" 
        )
      else:
        offset = listOffset
    else:
      # dummy value
      offset = 0
    
    # make key
    keyNames = metaClass.keyNames
    if not keyNames:
      # no key
      raise MemopsError("setLocalKeyVar called for %s that has no key" % metaClass)
    
    if needDefine and resultVar != self.varNames['result']:
      varType = self.anyType
      self.defineVar(resultVar, varType)
    
    if len(keyNames) == 1:
      # a single key
      tag = keyNames[0]
      elem = metaClass.getElement(tag)
        
      if elem.hicard == 1:
        self.getKeyComponent(sourceName, sourceType, offset, elem, resultVar)
      else:
        tt = self.collectionType(self.anyObject, isUnique=False, isOrdered=True)
        if sourceType == 'list':
          tempVar = 'tempList'
          self.defineVar(tempVar, tt)
        else:
          tempVar = resultVar
        self.getKeyComponent(sourceName, sourceType, offset, elem, tempVar)
        # TBD: is the if needed? check with Rasmus (want tempVar --> resultVar)
        if sourceType != 'list':
          tt = self.collectionType(elem, isUnique=elem.isUnique, isOrdered=elem.isOrdered, useCollection=True)
          self.startIf(self.valueIsNotNone(tempVar))
          tempVar = self.castVar(tt, tempVar)
        self.newCollection(resultVar, isFrozen=True, initValues=tempVar,
                           **self.collectionParams(elem))
        if sourceType != 'list':
          self.endIf()
        
      offset = offset + elem.hicard
        
    else:
      # compound key
      self.defineVar(listVar, self.collectionType(self.listPars['varType'], isUnique=False, isOrdered=True))
      self.newCollection(listVar, **self.listPars)
      for ii in range(len(keyNames)):
        tag = keyNames[ii]
        elem = metaClass.getElement(tag)
        
        if ii == 0:
          self.getKeyComponent(sourceName, sourceType, offset, elem, resultVar)
        else: 
          self.startIf(self.valueIsNotNone(resultVar))
          self.getKeyComponent(sourceName, sourceType, offset, elem, resultVar)
        
        if elem.hicard == 1:
          self.addCollection(resultVar, listVar, **self.listPars)
        else:
          ss = self.newCollection(None, isFrozen=True, initValues=resultVar,
                                  **self.collectionParams(elem))
          self.addCollection(ss, listVar, **self.listPars)
        
        offset = offset + elem.hicard
      
      
      self.startIf(self.valueIsNotNone(resultVar))
      self.newCollection(resultVar, isFrozen=True, initValues=listVar,
                         **self.listPars)
      self.endIf()
      
      for ii in range(1,len(keyNames)):
        self.endIf()
    
    #
    if listOffset is None:
      return None
    else:
      return offset
    
  ###########################################################################

  ###########################################################################
  # other code
  ###########################################################################

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeInitDefaults(self, op, inClass):
    
    ApiGen.writeInitDefaults(self, op, inClass)
  
    supertypes = inClass.getAllSupertypes()
    
    if self.topObject in supertypes:
    
      self.setImplAttr(self.varNames['self'], 'activeRepositories', 
                       self.newCollection(None, isUnique=False, isOrdered=True))
    
    elif self.dataRoot in supertypes:
      valueType = self.elementVarType(self.topObject)
      self.setImplAttr(self.varNames['self'], 'topObjects',
                       self.newDict(keyType=self.stringType, valueType=valueType))
      varType = self.elementVarType(self.implPackage.getElement('Repository'))
      self.setImplAttr(self.varNames['self'], 'activeRepositories', 
                       self.newCollection(None, isUnique=False, isOrdered=True, varType=varType))

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeConstructorCode(self, op, inClass):
  
    supertypes = inClass.getAllSupertypes()
    
    isTopObject = self.topObject in supertypes
    
    if isTopObject:
      
      guidAttr = self.topObject.getElement('guid')
      
      self.startBlock()
      # get guid, and set it if necessary
      self.getValue(self.varNames['self'], guidAttr, 'guid', inClass=inClass)
      self.startIf(self.valueIsNone('guid'))
      self.setVar('guid', self.callFunc('newGuid', 'root', doWrite=False))
      self.setValue(self.varNames['self'], guidAttr, 'guid')
      self.endIf()
      # put TopObject in topObjects dict
      # NBNB TBD the getImmplAttr trick will need special work in Java
      elem = self.dataRoot.getElement('topObjects')
      self.setVar('dd',
       self.getImplAttr(self.varNames['root'], 'topObjects'),
       ###TBD: remove: varType=self.stringKeyDictType, 
       varType=self.interfaceType(elem),
      )
      self.startIf(self.valueIsNone(self.getDictEntry('dd','guid')))
      self.setDictEntry('dd', 'guid', self.varNames['self'])
      self.elseIf()
      self.raiseApiError("Creating TopObject with preexisting guid", 
                         self.varNames['self'], inOp=op)
      self.endIf()
      self.endBlock()
    
    if isTopObject or self.dataRoot in supertypes:
      createdByAttr = inClass.getElement('createdBy')
      userAttr = self.dataRoot.getElement('currentUserId')
      if isTopObject:
        varName = self.varNames['root']
      else:
        varName = self.varNames['self']
      self.setValue(self.varNames['self'], createdByAttr, 
       self.getValue(varName, userAttr, inClass=inClass, lenient=True)
      )
    
    if inClass.constructorCodeStubs:
      self.writeHandCode(inClass, 'constructorCodeStubs')

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeDelete(self, op, inClass):
    
    # set 'topObject'
    self.defineTopObject(inClass)
    self.getImplLink(self.varNames['self'], 'topObject', 
                     self.varNames['topObject'], inClass)
    
    ApiGen.writeDelete(self, op, inClass)
    
  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeUnDelete(self, op, inClass):

    # set 'topObject'
    self.defineTopObject(inClass)
    self.getImplLink(self.varNames['self'], 'topObject',
                     self.varNames['topObject'], inClass)

    ApiGen.writeUnDelete(self, op, inClass)

  ###########################################################################

  ###########################################################################

  def defineTopObject(self, inClass):

    allSupertypes = inClass.getAllSupertypes()
    if self.dataObject in allSupertypes:
      topObject = self.topObject
    elif self.implObject in allSupertypes:
      topObject = self.dataRoot
    else:
      raise MemopsError("defineTopObject called for incorrect class %s"
                         % inClass)
    
    self.defineVar(self.varNames['topObject'], self.elementVarType(topObject))

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writePreDelete(self, op, inClass):
    """  handle special case of TopObject in file implementation getValue
    """
    
    # TBD: looks like always need to be of type MemopsObject
    ###self.defineTopObject(inClass)
    self.defineVar(self.varNames['topObject'], self.elementVarType(self.baseClass))

    if self.topObject in inClass.getAllSupertypes():
      self.startIf(self.negate(self.logicalOp(
       self.boolean(self.getImplAttr(self.varNames['self'], 'isLoaded')), 'or',
       self.boolean(self.getImplAttr(self.varNames['self'], 'isReading'))))
      )
      self.callFunc('load', self.varNames['self'])
      self.endIf()
      
      self.topObjectPreloaded = True
      
      ApiGen.writePreDelete(self, op, inClass)
      
      self.topObjectPreloaded = False
      
    else:
      ApiGen.writePreDelete(self, op, inClass)

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def setupModifyFuncVars(self, op, inClass):
                         
    # set 'topObject' - must be done before super function call
    if isinstance(inClass, MetaModel.MetaClass):
    
      allSupertypes = inClass.getAllSupertypes()
      if self.dataObject in allSupertypes:
        topObject = self.topObject
      elif self.implObject in allSupertypes:
        topObject = self.dataRoot
      else:
        raise MemopsError("modify function %s defined for incorrect class %s"
                          % (op,inClass))
      self.defineVar(self.varNames['topObject'], self.elementVarType(topObject))
      self.getImplLink(self.varNames['self'], 'topObject',
                       self.varNames['topObject'], inClass)

    ApiGen.setupModifyFuncVars(self, op, inClass)
    
    elem = op.target
    if isinstance(elem,MetaModel.MetaRole):
      otherRole = elem.otherRole
      if (otherRole and 
          otherRole.container.container in inClass.container.importedPackages):
        # add package loading for 'self' package for interpackage links
        # in import direction. NB only these can be triggered during load
        if not (otherRole.hicard == metaConstants.infinity
                and otherRole.locard == 0):
          # if the reverse role is 0..* we never need to load
          
          if op.opType == 'set' or otherRole.hicard != 1:
            self.startIf(self.varNames['notIsReading'])
            self.loadPackage(self.varNames['self'], otherRole, inClass=inClass)
            self.endIf()

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeCheckValidComplete(self, op, inClass):
    """  handle special cases, e.g. TopObject in file implementation getValue
    """
    
    # reciprocity ehcck for parent roles
    if isinstance(inClass, MetaModel.MetaClass):
      parentRole = inClass.parentRole
      if parentRole is not None and parentRole.otherRole.hicard != 1:
        # check that parentlink is reciprocal
        var = self.valueVar(parentRole, doInstance=True)
        objKeyVar = 'objKey'
        dictVar = 'dd'
        self.setLocalKeyVar(metaClass=inClass, sourceName=self.varNames['self'],
                            resultVar=objKeyVar)
        self.startIf(self.valueIsNone(objKeyVar))
        self.raiseApiError("Key could not be calculated for object", 
                           self.varNames['self'], inOp=op)
        self.elseIf()
        self.getValue(self.varNames['self'], parentRole, var, inClass=inClass)
        ### TBD: remove
        ###varType = self.interfaceType(parentRole.otherRole)
        val = self.getMemoryValue(var, parentRole.otherRole)
        ###val = self.castVar(varType, val)
        varType = self.dictInterfaceType()
        self.setVar(dictVar, val, varType=varType)
        self.startIf(self.negate(self.comparison(self.varNames['self'], 'is',
                                 self.getDictEntry(dictVar, objKeyVar))))
        self.raiseApiError(
         "non-reciprocal parent link '%s' from object" % parentRole.name,
         self.varNames['self'], inOp=op
        )
        self.endIf()
        self.endIf()
    
    if self.topObject in inClass.getAllSupertypes():
      self.startIf(self.negate(self.logicalOp(
       self.boolean(self.getImplAttr(self.varNames['self'], 'isLoaded')), 'or',
       self.boolean(self.getImplAttr(self.varNames['self'], 'isReading'))))
      )
      self.callFunc('load', self.varNames['self'])
      self.endIf()
      
      self.topObjectPreloaded = True
      
      ApiGen.writeCheckValidComplete(self, op, inClass)
      
      self.topObjectPreloaded = False
      
    else:
      ApiGen.writeCheckValidComplete(self, op, inClass)

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeCheckAllValid(self, op, inClass):
    """  handle special case of TopObject in file implementation
    """
    
    if self.topObject in inClass.getAllSupertypes():
      self.startIf(self.negate(self.logicalOp(
       self.boolean(self.getImplAttr(self.varNames['self'], 'isLoaded')), 'or',
       self.boolean(self.getImplAttr(self.varNames['self'], 'isReading'))))
      )
      self.callFunc('load', self.varNames['self'])
      self.endIf()
      
      self.topObjectPreloaded = True
      
      ApiGen.writeCheckAllValid(self, op, inClass)
      
      self.topObjectPreloaded = False
      
    else:
      ApiGen.writeCheckAllValid(self, op, inClass)

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeCheckValid(self, op, inClass):
    """ Write checks for handcode and cardinality
    """
    
    doExtra = (self.topObject in inClass.getAllSupertypes())
    if doExtra:
      self.startIf(self.boolean(self.getImplAttr(self.varNames['self'],
                                                 'isLoaded')))
    
    ApiGen.writeCheckValid(self, op, inClass)
    
    if doExtra:
      # for an unloaded TopObject you only check key and guid
      self.elseIf()
      self.writeComment('check unloaded TopObject')
      
      for tag in  [metaConstants.guid_attribute] + inClass.keyNames:
        self.writeCheckElement(op, inClass, inClass.getElement(tag))
      
      self.endIf()
      
  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeCheckValidOtherRole(self, op, inClass, role):
    """ check that roles a.b and b.a are the same.
    """
    
    if (role.hierarchy == metaConstants.parent_hierarchy
        and role.otherRole.hicard != 1):
      return
    else:
      ApiGen.writeCheckValidOtherRole(self, op, inClass, role)

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def checkFindFirst(self, op, inClass):
    """ write findFirst body
    """
    # setup
    role = op.target
    currentVar = self.valueVar(role, prefix=self.currentPrefix)
    objKeyVar = 'objKey'
    
    self.defineVar(currentVar, self.collectionType(role, useCollection=True))

    metaClass = role.valueType
    # Extra check on metaClass.keyNames added because Java now has examples
    # (e.g. AbstractMeasurement) where that is empty
    if (isinstance(metaClass, MetaModel.MetaClass)
                  and role.hierarchy == metaConstants.child_hierarchy) and metaClass.keyNames:
    
      # get local key
      self.setLocalKeyVar(metaClass=metaClass,
                       sourceName=self.varNames['conditions'],
                       resultVar=objKeyVar, sourceType='dict')
         
      self.startIf(self.valueIsNotNone(objKeyVar))
      # key is in search, use it
      ss = self.getDictEntry(self.getMemoryValue(self.varNames['self'], role),
                             objKeyVar)
      if inClass is self.dataRoot:
        # save refreshTopObjkects if the TopObject is already there
        ###self.setVar(self.varNames['result'], ss, self.elementVarType(role))
        self.setVar(self.varNames['result'], ss, castType=self.elementVarType(role))
        self.startIf(self.valueIsNone(self.varNames['result']))
      self.possiblyLoadData(self.varNames['self'], role, inClass=inClass)
      ###self.setVar(self.varNames['result'], ss, self.elementVarType(role))
      self.setVar(self.varNames['result'], ss)
      if inClass is self.dataRoot:
        self.endIf()
      self.writeNewline()
      self.startIf(self.comparison(self.varNames['nConditions'], '<=', 
                                  self.toLiteral(len(role.valueType.keyNames))))
      self.returnStatement(self.varNames['result'])
      self.writeNewline()
      self.elseIf(self.valueIsNone(self.varNames['result']))
      self.returnStatement(self.varNames['result'])
      self.writeNewline()
      self.elseIf()
      self.newCollection(currentVar, **self.collectionParams(role))
      self.addCollection(self.varNames['result'], currentVar, 
                         **self.collectionParams(role))
      self.endIf()
      self.elseIf()
      # key not in search - do it the slow way

    # TBD NBNB need needVarType = False to avoid repeated definition of currentValues in
    # MemopsRoot.findFirstAccessControlStore
    self.getValue(self.varNames['self'], role, currentVar, 
                  convertCollection=False, inClass=inClass, needVarType=False)
    
    if (isinstance(metaClass, MetaModel.MetaClass)
                  and role.hierarchy == metaConstants.child_hierarchy) and metaClass.keyNames:
      self.endIf()
      
    self.checkFindBody(op, inClass, funcType='findFirst')

  ###########################################################################

  ###########################################################################
  
  # overrides ApiGen
  def writeGetLocalKey(self, op, inClass):
    """ write getLocalKey
    """
    if inClass.keyNames:
      # meaningful local key
      self.setLocalKeyVar(metaClass=inClass, sourceName=self.varNames['self'],
                        resultVar=self.varNames['result'])
    else:
      # local key si meaningless - we need the function for consistency, though.
      self.setVar(self.varNames['result'], self.noneValue)

  ###########################################################################

  ###########################################################################
  
  # implements ApiInterface
  def writeGetByKey(self, op, inClass):
    """ write getByKey
    """
    sourceName = 'fullKey'
    ###objKeyVar = 'objKey'
    startObj = 'startObj'
    resultVar = self.varNames['result']
    
    # do we need an isinstance check? 
    # Only for classes that inherit parentRole
    checkInstance = (inClass.parentRole.container is not inClass)
    
    # set up
    downlinks = []
    downlinkClasses = []
    clazz = op.container
    keyLength = 0
    pr = clazz.parentRole
    while pr is not None:
      # calculate keyLength for total and last step
      lastContrib = 0
      for tag in clazz.keyNames:
        lastContrib = lastContrib + clazz.getElement(tag).hicard
      keyLength = keyLength + lastContrib
      
      # get downlink and loop
      downlinks.append(pr.otherRole)
      downlinkClasses.append(pr.otherRole.container)
      clazz = pr.valueType
      pr = clazz.parentRole
    
    downlinks.reverse()
    downlinkClasses.reverse()
    memopsRoot = clazz
    downlink = downlinks[0]
    
    self.writeNewline()
    self.setVar(resultVar, self.noneValue)
    self.defineVar("obj1", self.elementVarType(downlink))
    
    if len(downlinks) == 1:
      # Direct children of MemopsRoot - no casting or isinstance necessary
      # set result directly
      
      vv = 'obj1'
      
      # check key length
      self.startIf(self.comparison(self.toLiteral(keyLength), '!=', 
                   self.lenCollection(sourceName, **self.listPars)))
      self.raiseApiError(
       "getByKey called with fullKey of wrong length. Parameters:", 
       startObj, sourceName, inOp=op
      )
      self.endIf()
      
      # TBD: remove
      #self.defineVar(objKeyVar, self.anyType)
      (listOffset, ss) = self.getObjByKey(downlink, sourceName, startObj)
      ###self.setLocalKeyVar(downlink.valueType, sourceName, objKeyVar, 
      ###                    sourceType='list', listOffset=0)
      ###ss = self.getDictEntry(self.getMemoryValue(startObj, downlink),
      ###                       objKeyVar)
      self.setVar(vv, ss, castType=self.elementVarType(downlink))
      
      # if this is a TopObject check for possible reload
      if inClass.container is not self.implPackage:
        self.startIf(self.valueIsNone(vv))
        self.callFunc('refreshTopObjects', startObj, 
                      params=self.toLiteral(inClass.container.qualifiedName()))
        self.setVar(vv, ss, castType=self.elementVarType(downlink))
        self.endIf()
        
    else:

      # first get TopObject, depending on startObj, and cast
      if inClass.container.qualifiedName() == self.implPackageName:
        # objects in Implementation - no topObject manipulation necessary
      
        # check key length
        self.startIf(self.comparison(self.toLiteral(keyLength), '!=', 
                     self.lenCollection(sourceName, **self.listPars)))
        self.raiseApiError(
         "getByKey called with fullKey of wrong length. Parameters:", 
         startObj, sourceName, inOp=op
        ) 
        self.endIf()
        
        (listOffset, ss) = self.getObjByKey(downlink, sourceName, startObj)
        ###listOffset = self.setLocalKeyVar(downlink.valueType, sourceName, 
        ###                                 objKeyVar, sourceType='list', 
        ###                                 listOffset=0)
        ###ss = self.getDictEntry(self.getMemoryValue(startObj, downlink),
        ###                       objKeyVar)
        self.setVar('obj1', ss)
    
      else:
    
        self.startIf(self.comparison(
         self.getImplAttr(startObj, 'className'), '==', 
         self.toLiteral(memopsRoot.name))
        )
        
        # check key length
        self.startIf(self.comparison(self.toLiteral(keyLength), '!=',
                     self.lenCollection(sourceName, **self.listPars)))
        self.raiseApiError(
         "getByKey called with fullKey of wrong length. Parameters:",
         startObj, sourceName, inOp=op
        )
        self.endIf()
        
        varType = castType = self.elementVarType(memopsRoot)
        self.setVar("obj0", startObj, varType=varType, castType=castType)
        (listOffset, ss) = self.getObjByKey(downlink, sourceName, 'obj0')
        ###listOffset = self.setLocalKeyVar(downlink.valueType, sourceName, 
        ###                                 objKeyVar, sourceType='list', 
        ###                                 listOffset=0)
        ###ss = self.getDictEntry(self.getMemoryValue('obj0', downlink), 
        ###                       objKeyVar)
        self.setVar('obj1', ss)
        
        self.startIf(self.valueIsNone('obj1'))
        self.callFunc('refreshTopObjects', 'obj0', 
                      params=self.toLiteral(inClass.container.qualifiedName()))
        self.setVar('obj1', ss, self.elementVarType(downlink))
        self.endIf()
        
        self.writeNewline()
        self.elseIf()
        
        # check key length
        # first adjust key length to exclude link to topObject
        keyLength = keyLength - lastContrib
        self.startIf(self.comparison(self.toLiteral(keyLength), 
                     '!=', self.lenCollection(sourceName, **self.listPars)))
        self.raiseApiError(
         "getByKey called with fullKey of wrong length. Parameters:",
         startObj, sourceName, inOp=op
        )
        self.endIf()
        
        varType = castType = self.elementVarType(downlink)
        self.setVar("obj1", startObj, varType=varType, castType=castType)
        self.endIf()
      
      # now continue downwards
      #    adjust listOffset to count from end, 
      #    given that key can have different lengths
      listOffset = -keyLength
      vv = 'obj1'
      for ii in range(1, len(downlinks)):
        downlink = downlinks[ii]
        self.writeNewline()
        self.startIf(self.valueIsNotNone(vv))
        if ii == 1:
          self.possiblyLoadData(vv, downlink, inClass=inClass)
        
        vv = self.castVar(self.elementVarType(downlinkClasses[ii]), vv)
        if downlink.hicard == 1:
          ss = self.getValue(vv, downlink, lenient=True, inClass=inClass)
        
        else:
          (listOffset, ss) = self.getObjByKey(downlink, sourceName, vv, listOffset)
          ###listOffset = self.setLocalKeyVar(downlink.valueType, sourceName,
          ###                              objKeyVar, sourceType='list',
          ###                              listOffset=listOffset, needDefine=(ii==1))
          ###ss = self.getDictEntry(self.getMemoryValue(vv, downlink),
          ###                                           objKeyVar)
                                                     
        vv = 'obj%s' % (ii + 1)
        ss = self.castVar(self.elementVarType(downlink), ss)
        self.setVar(vv, ss, self.elementVarType(downlink))
      
    # check if is instance of correct class
    if checkInstance:
      self.startIf(self.isInstance(
       vv, self.getImportName(inClass, inClass.container)
      ))
    self.setVar(resultVar, vv, castType=self.elementVarType(inClass))
    if checkInstance:
      self.endIf()
    
    # end if statements
    for ii in range(1, len(downlinks)):
      self.endIf()
      
  ###########################################################################

  ###########################################################################

  # default implementation, can be overriden
  def getObjByKey(self, downlink, sourceName, startObj, listOffset=0):

    objKeyVar = 'objKey'

    listOffset = self.setLocalKeyVar(downlink.valueType, sourceName, objKeyVar, 
                                     sourceType='list', listOffset=listOffset)
    ss = self.getDictEntry(self.getMemoryValue(startObj, downlink),
                           objKeyVar)

    return listOffset, ss

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  # Working on internal collection. For optimisation spare obj.elem=value step.
  def addValue(self, owner, element, var, collection):

    self.addCollection(var, collection, **self.collectionParams(element))

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  # Working on internal collection. For optimisation spare obj.elem=value step.
  def removeValue(self, owner, element, var, collection):

    self.removeCollection(var, collection, **self.collectionParams(element))
    
  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeCheckAllValidKeysUnique(self, op, inClass, role):
    # not done in file implementation

    pass

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeDoDeleteRole(self, op, inClass, role):
    """handle special case of links to parent
    """

    otherRole = role.otherRole
    thatVar = role.baseName
    dictVar = 'dd'
    objKeyVar = 'objKey'
    
    if role.hierarchy == metaConstants.parent_hierarchy:
      
      if otherRole.locard != otherRole.hicard:
        # maybe delete
        
        self.startBlock() 
        # necessary to shield internal parameters from name clashes
        
        self.getValue(self.varNames['self'], role, thatVar, lenient=True,
                      inClass=inClass)
        self.startIf(self.negate(self.isInCollection(
         thatVar, **self.stdCollectionParams['objsToBeDeleted']))
        )

        # NB - the comparisons are necessary as you might get a delete called
        # inside an incomplete create, e.g. because the keys overlap
        
        if otherRole.hicard == 1:
          self.startIf(
           self.comparison(self.varNames['self'], 'is', 
                           self.getValue(thatVar, otherRole, lenient=True,
                                         inClass=inClass))
          )
          self.setValue(thatVar, otherRole, self.noneValue)
          self.endIf()
    
        else: # otherRole.hicard != 1 
          self.setLocalKeyVar(metaClass=inClass, 
                              sourceName=self.varNames['self'],
                              resultVar=objKeyVar)
          self.startIf(self.valueIsNone(objKeyVar))
          self.raiseApiError(
           "Key could not be calculated for object to be deleted", inOp=op
          ) 
          self.elseIf()
          val = self.getMemoryValue(thatVar, otherRole)
          ### TBD: remove
          ###varType = self.interfaceType(otherRole)
          ###val = self.castVar(varType, val)
          varType = self.dictInterfaceType()
          self.setVar(dictVar, val, varType=varType)
          self.startIf(
           self.comparison(self.varNames['self'], 'is', 
                           self.getDictEntry(dictVar, objKeyVar))
          )
          self.removeDictEntry(dictVar, objKeyVar)
          self.endIf()
          self.endIf()
        self.endIf()
          
        self.endBlock() 
          
    else:
      ApiGen.writeDoDeleteRole(self, op, inClass, role)

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeDoUnDeleteRole(self, op, inClass, role):
    """handle special case of links to parent
    """

    otherRole = role.otherRole
    thatVar = role.baseName
    dictVar = 'dd'
    objKeyVar = 'objKey'

    if role.hierarchy == metaConstants.parent_hierarchy:

      if otherRole.locard != otherRole.hicard:
        # maybe delete

        self.startBlock()
        # necessary to shield internal parameters from name clashes

        self.getValue(self.varNames['self'], role, thatVar, lenient=True,
                      inClass=inClass)
        if (self.topObject not in otherRole.container.getAllSupertypes() and
            self.topObject not in inClass.getAllSupertypes()):
          self.startIf(self.negate(self.isInCollection(thatVar,
                                                 **self.stdCollectionParams['objsToBeUnDeleted'])))

        # NB - the comparisons are necessary as you might get a delete called
        # inside an incomplete create, e.g. because the keys overlap

        if otherRole.hicard == 1:
          self.startIf(self.valueIsNone(self.getValue(thatVar, otherRole,
                                                         lenient=True, inClass=inClass)))
          self.setValue(thatVar, otherRole, self.varNames['self'])
          self.elseIf()
          self.raiseApiError("Error undoing delete of %s object %s link - backLink %s.%s is not None"
                             % (inClass.name, role.name, otherRole.container.name, otherRole.name))

          self.endIf()

        else: # otherRole.hicard != 1
          self.writeAddChildToParent(self.varNames['self'], thatVar, role, inClass=inClass,
                                     inUndo=True)

        if (self.topObject not in otherRole.container.getAllSupertypes() and
            self.topObject not in inClass.getAllSupertypes()):
          self.endIf()

        self.endBlock()

    else:
      ApiGen.writeDoUnDeleteRole(self, op, inClass, role)

  ###########################################################################

  ###########################################################################
  # For hibernate sql API. Need to check if null and initialise
  # serial dict for this role. Override in JavaFileDbApiGen only

  def initSerialDictIfNull(self, name):
    pass
  

