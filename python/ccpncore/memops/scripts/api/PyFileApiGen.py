from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import Util as metaUtil

from ccpncore.memops.scripts.api.PyApiGen import PyApiGen
from ccpncore.memops.scripts.api.FileApiGen import FileApiGen
MemopsError = MetaModel.MemopsError


def writeApi(modelPortal, rootFileName=None, rootDirName=None,
             releaseVersion=None, **kw):
  """write Python File API
  
  Only function that should be called directly by 'make' scripts etc.
  """
  
  pyFileApiGen = PyFileApiGen(modelPortal=modelPortal, rootFileName=rootFileName, 
                        rootDirName=rootDirName, releaseVersion=releaseVersion,
                        scriptName='PyFileApiGen',
                        **kw)
  pyFileApiGen.processModel()


class PyFileApiGen(FileApiGen, PyApiGen):

  ###########################################################################

  ###########################################################################

  def __init__(self, **kw):
  
    for (tag, val) in kw.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)
    
    super(PyFileApiGen, self).__init__()

  ###########################################################################

  ###########################################################################
  ###
  ### code implementing ApiInterface
  ###
  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeSetAttrLinks(self, op, inClass):

    keyVar = 'key'
    valueVar = 'value'
    
    self.writeNewline()
    self.setImplAttr(self.varNames['self'], 'inConstructor', True)
    
    supertypes = inClass.getAllSupertypes()
    
    if self.dataRoot in supertypes:
      self.writeComment('Hack for handling the root implementation attribute')
      self.setDictEntry(self.getDataDict(self.varNames['self']), 
                        self.toLiteral('memopsRoot'), 'self')

      # Initialise _undo to None
      self.setDictEntry(self.getDataDict(self.varNames['self']),
                        self.toLiteral('_undo'), 'None')

    # Add _lastId attribute to topObject
    if inClass is inClass.container.topObjectClass:
      self.setDictEntry(self.getDataDict(self.varNames['self']),
                        self.toLiteral(metaConstants.lastid_attribute),
                        self.toLiteral(0))

    self.write("try:")
    self.indent += self.INDENT
    self.write('''
for %s, %s in %s.items():
  try:
    func = getattr(%s.__class__, %s).fset
  except:
    raise ApiError("%%s: error setting %%s - not a modeled attribute"
                   %% (self, key))
  if func is None:
    raise ApiError("%%s: error setting %%s - not a settable attribute"
                   %% (self, key))
  else:
    func(%s, %s)
''' % (keyVar, valueVar, self.varNames['attrlinks'], self.varNames['self'], 
       keyVar, self.varNames['self'], valueVar))

    if isinstance(inClass, MetaModel.MetaClass):
      # Set _ID attribute. NBNB new March 2014 Rasmus Fogh

      idVar = metaConstants.id_attribute
      for cls in supertypes:
        element = cls.getElement(idVar)
        if element is not None:
          break
      else:
        raise MemopsError("No element %s found for class %s" % (idVar, inClass))

      self.startIf(self.valueIsNone(
       self.getValue(self.varNames['self'], element, lenient=True, inClass=inClass))
      )
      setterOp = metaUtil.getOperation(element, 'set', inClass=inClass)
      funcName = self.getFuncname(setterOp, inClass)
      self.callFunc(funcName, obj=self.varNames['self'], params=self.toLiteral(-1))
      self.elseIf()
      self.raiseApiError("Class %s - set explicit _ID %s when not reading",
                         self.toLiteral(inClass.qualifiedName()), 'value')
      self.endIf()

    self.setImplAttr(self.varNames['self'], 'inConstructor', False)
    self.indent -= self.INDENT
    
    self.writeOne("except:")
    self.indent += self.INDENT
    if self.dataRoot in supertypes:
      self.writeOne('print("ERROR in %s.__init__")' % inClass.qualifiedName())
    else:
      self.writeOne('self.root._logger.error("in %s.__init__")' % inClass.qualifiedName())
    self.setImplAttr(self.varNames['self'], 'inConstructor', False)
    self.writeOne('raise')
    self.indent -= self.INDENT

  ###########################################################################

  ###########################################################################

  # Auxiliary function Optimisation
  def checkFindSingleCondition(self, op, currentVar, resultCode):
    """ Do check for case where there is only one conditions
    Separated out to allow an optimisation in PyFileApiGen
    """
    
    # get names of fast-treatment attributes
    targetClass = op.target.valueType
    ll = targetClass.getAllAttributes()
    if isinstance(targetClass, MetaModel.MetaClass):
      ll = ll + targetClass.getAllRoles()
    useTags = [x.name for x in ll if x.hicard == 1 and not x.isDerived 
               and not x.isImplementation]
    
    if useTags:
      # write optimisation
      self.newCollection('directAttrs', isUnique=True, isOrdered=False, 
                         isFrozen=True, varType=self.stringType, 
                         needDeclType=True, initValues=useTags) 
      self.startIf(self.isInCollection('key', 'directAttrs',isUnique=True, 
                   isOrdered=False, varType=self.stringType))
      
      self.startLoop('v', currentVar, **self.collectionParams(op.target))
      self.startIf(self.equals('condition', 
       self.getDictEntry(self.getDataDict('v'), 'key'))
      )
      self.write(resultCode)
      self.endIf()
      self.endLoop()
      self.elseIf()
    
    PyApiGen.checkFindSingleCondition(self, op, currentVar, resultCode)
    
    if useTags:
      self.endIf()

  ###########################################################################

  ###########################################################################
  ###
  ### code implementing PersistenceInterface
  ###
  ###########################################################################

  ###########################################################################

  # implements PersistenceInterface
  def setValue(self, owner, element, value):

    self.setDictEntry(self.getDataDict(owner), self.toLiteral(element.name),
                      value)

  ###########################################################################

  ###########################################################################
  ###
  ### code implementing ApiInterface
  ###
  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def getOverride(self, op, inClass):
    
    self.writeNewline()
    
    dd = self.varNames
    
    if isinstance(inClass, MetaModel.MetaClass):
    
      # It is assumed that topObject is already set
      
      # get root
      topcc = inClass.container.topObjectClass
      if topcc is None or topcc is inClass or topcc is self.dataRoot:
        self.getImplLink(dd['self'], 'root', dd['root'], inClass)
      
      else:
        self.getImplLink(dd['topObject'], 'parent', dd['root'], topcc)
      
      # get override from root
      overrideElem = self.dataRoot.getElement('override')
      self.setVar(dd['notOverride'], self.negate(self.boolean(
         self.getValue(dd['root'], overrideElem, lenient=True, inClass=inClass))),
         self.booleanType
        )
    
      # get isReading
      self.setVar(dd['notIsReading'],
       self.negate(self.boolean(self.getImplAttr(dd['topObject'], 'isReading'))),
       self.booleanType
      )
 
      # set override to fit isReading
      self.setVar(dd['notOverride'],
                  self.logicalOp(dd['notOverride'], 'and', dd['notIsReading']))
    
    else:
    
      overrideElem = inClass.getElement('override')
      
      self.setVar(dd['notOverride'], self.negate(self.boolean(
       self.getValue(dd['self'], overrideElem, lenient=True, inClass=inClass))),
       self.booleanType
      )
      
    
  ###########################################################################

  ###########################################################################

  # implements ApiInterface
  def writeSortedValue(self, op, inClass):
    """ write sorted element getter
    """
    ddname = 'sortdd'
    
    elem = op.target
    
    if (isinstance(elem, MetaModel.MetaRole) 
        and elem.hierarchy == metaConstants.child_hierarchy):
    
      self.possiblyLoadData(self.varNames['self'], elem, inClass=inClass)
      self.setVar(ddname, self.getMemoryValue(self.varNames['self'], elem))
      self.write("""
ll = list(%s.keys())
ll.sort()
%s = [%s[x] for x in ll]""" % (ddname, self.varNames['result'], ddname,))
    else:
      PyApiGen.writeSortedValue(self, op, inClass)
    
  ###########################################################################

  ###########################################################################

  # overrides FileApiGen ApiInterface
  def writeInitSerial(self, op, inClass):
    
    FileApiGen. writeInitSerial(self, op, inClass)
    
    # NBNB Slightly naughty this
    # we are adding a statement after rather than before an endBlock, 
    # but in Python it does not matter
    
    attrName = metaConstants.serial_attribute
    ddName = metaConstants.serialdict_attribute
    serialKids = [x for x in inClass.getAllRoles() 
                  if (x.hierarchy == metaConstants.child_hierarchy and
                  x.valueType.getElement(attrName))]
    
    if serialKids:
      self.setImplAttr(self.varNames['self'], ddName, ddName)

  ###########################################################################

  ###########################################################################
  ###
  ### code implementing FileApiInterface
  ###
  ###########################################################################

  ###########################################################################

  # implements FileApiInterface
  def getImplLink(self, owner, linkName, var, ownerClass, castType=None):
    """ do 'var = owner.linkName'. ownerClass is the class of Owner.
    """
    
    varName = self.varNames[linkName]
    
    if linkName == 'root':
      
      if self.dataRoot in ownerClass.getAllSupertypes():
        # owner is MemopsRoot
        if owner == var:
          # nothing needs doing
          return
        else:
          # set value 
          ss = owner
      
      elif (ownerClass.parentRole and 
       self.dataRoot in ownerClass.parentRole.valueType.getAllSupertypes()
      ):
        # root is parent of owner
        self.getValue(owner, ownerClass.parentRole, var,
                      needVarType=False, lenient=True, inClass=ownerClass)
        return
      
      elif (ownerClass.container.qualifiedName() == self.implPackageName
            and not ownerClass.isAbstract):
        ss = self.getImplAttr(owner, 'topObject')
          
      else:
        # because MemopsRoot.memopsRoot is MemospRoot (hack) this always works,
        # but the preceding alternatives are quicker
        ss = self.getImplAttr(owner, 'topObject')
        ss = self.getDictEntry(self.getDataDict(ss), 
                               self.toLiteral('memopsRoot'))
      self.setVar(var, ss)
      
    elif linkName == 'parent':
      if self.dataRoot in ownerClass.getAllSupertypes():
        # this is MemopsRoot
        self.setVar(var, self.noneValue)
      
      else:
        self.getValue(owner, ownerClass.parentRole, var,
                      needVarType=False, lenient=True, inClass=ownerClass)
      
    elif linkName == 'topObjects':
      if self.dataRoot in ownerClass.getAllSupertypes():
        # this is MemopsRoot
        self.setVar(var, "set(x for x in %s if not x.isDeleted)" 
                    % self.getDictValues(self.getImplAttr(owner,linkName)))
      
      else:
        raise MemopsError("topObjects is only defined for root, called on %s"
                          % ownerClass)
      
    elif linkName == 'activeRepositories':
      supertypes = ownerClass.getAllSupertypes()
      if self.dataRoot in supertypes or self.topObject in supertypes:
        self.setVar(var, self.getImplAttr(owner,linkName))
        if self.dataRoot not in supertypes:
          self.startIf(self.collectionIsEmpty(var, isUnique=True, isOrdered=True))
          ss = self.getImplAttr(owner, 'topObject')
          ss = self.getDictEntry(self.getDataDict(ss), 
                               self.toLiteral('memopsRoot'))
          self.callFunc('refreshTopObjects', ss,
                        params=self.getImplAttr(owner,'packageName'))
          self.setVar(var, self.getImplAttr(owner,linkName))
          self.endIf()
      
      else:
        raise MemopsError("activeRepositories is only defined for root, called on %s"
                          % ownerClass)
    
    else:
      self.setVar(var, self.getImplAttr(owner, varName))

  ###########################################################################

  ###########################################################################

  # implements FileApiInterface
  def setImplLink(self, owner, linkName, value, ownerClass):
    """ do 'owner.linkName = var'. ownerClass is teh class of OwnerYes, that is the idea.
   """
    
    if linkName in ('root', 'parent'):
      raise MemopsError("setImplLink(%s,%s,%s,%s): %s not a valid input" %
                        (owner, linkName, value, ownerClass, linkName))
   
    else:
      self.setImplAttr(owner, linkName, value)

  ###########################################################################

  ###########################################################################

  # implements FileApiInterface
  def getImplAttr(self, owner, attrName, inClass=None):
    """ Direct attribute get. NB may be used 'creatively' to get at 
    mutable private attributes.
    
    As of 1/3/08 used for :
    ('activeRepositories', 'className', 'inConstructor', 'isDeleted', 
     'isLoaded', 'isModified', 'isReading', 'metaclass', 'override',
     'packageName', 'packageShortName', 'serialDict', 'topObject',  
     'topObjects', 'fieldNames') 
    """
    
    varName = self.varNames[attrName]
    
    if attrName == 'className':
      return "%s.__class__.__name__" % owner
      
    elif attrName in ('packageName', 'packageShortName', 'metaclass', 
                      'fieldNames'):
      return "%s.__class__.%s" % (owner, varName)
    
    else:  
      return self.getDictEntry(self.getDataDict(owner), self.toLiteral(varName))
    
  ###########################################################################

  ###########################################################################

  # implements FileApiInterface
  def setImplAttr(self, owner, attrName, value, inClass = None):
    
    varName = self.varNames[attrName]
    
    if attrName in ('isDeleted', 'inConstructor', 'override'):
      if value:
        self.setDictEntry(self.getDataDict(owner), self.toLiteral(varName), 
                          True)
      else:
        self.removeDictEntry(self.getDataDict(owner), self.toLiteral(varName))
    
    elif attrName in ('className', 'packageName', 'packageShortName', 
                      'fieldNames'):
      raise MemopsError("setImplAttr(%s,%s,%s): %s not a valid input" %
                        (owner, attrName, value, attrName))
    
    else:
      self.setDictEntry(self.getDataDict(owner), self.toLiteral(varName), value)

  ###########################################################################

  ###########################################################################

  # implements FileApiInterface
  def getMemoryValue(self, owner, element):
    
    if isinstance(element, MetaModel.ClassElement):
      return self.getDictEntry(self.getDataDict(owner), 
                               self.toLiteral(element.name))
    
    else:
      raise MemopsError(
       "getMemoryValue called with %s, must be attribute or role" % element
      )

  ###########################################################################

  ###########################################################################
  ###
  ### code overriding FileApiGen
  ###
  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeConstructorCode(self, op, inClass):
    
    self.writeNewline()
  
    supertypes = inClass.getAllSupertypes()
    
    if self.dataRoot in supertypes:
      # MemopsRoot
      self.writeNewline()
      FileApiGen.writeConstructorCode(self, op, inClass)
      
      self.writeNewline()
      self.startIf(self.varNames['notOverride'])
      
      self.write("""
from ccpncore.util import Path
from ccpncore.util.Common import getConfigParameter
import os, os.path
rootDir = Path.normalisePath(os.getcwd())

# repositories from configuration
for (name, urlPath) in getConfigParameter('repositories'):
  self.newRepository(name=name, url=Url(path=urlPath))

# default repositories
inData = (
 ('userData', Path.joinPath(rootDir, self.name)),
 ('backup', Path.joinPath(rootDir, self.name + '_backup')),
 ('refData', Path.joinPath(Path.getTopDirectory(), 'data')),
 ('generalData', Path.normalisePath(os.path.expanduser('~/.ccpn/data'))),
)
for (name, urlPath) in inData:
  if not self.findFirstRepository(name=name):
    self.newRepository(name=name, url=Url(path=urlPath))

# packageLocators from configuration
for (targetName,repository) in getConfigParameter('packageLocators'):
  loc = self.findFirstPackageLocator(targetName=targetName)
  if loc is None:
    loc = self.newPackageLocator(targetName=targetName,
     repositories=self.findAllRepositories(name=repository)
    )
  else:
    loc.addRepository(self.findFirstRepository(name=repository))

# default packageLocators
inData = (
 ('any', 'userData'),
)
for (targetName,repository) in inData:
  if not self.findFirstPackageLocator(targetName=targetName):
    self.newPackageLocator(targetName=targetName,
     repositories=self.findAllRepositories(name=repository)
    )

# Add logger attribute
try:
  from ccpncore.util.Logging import getLogger
  self._logger = getLogger()
except ImportError:
  self._logger = None
""")
      self.endIf()
    
    elif self.topObject in supertypes:
      # TopObject, no Implementation class
      
      self.startIf(self.varNames['notIsReading'])
      
      FileApiGen.writeConstructorCode(self, op, inClass)
        
      self.endIf()
      
    elif inClass.constructorCodeStubs:
        self.startIf(self.varNames['notIsReading'])
        FileApiGen.writeConstructorCode(self, op, inClass)
        self.endIf()

  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeGetValue(self, op, inClass):
    """ write element getter
    special case for Boolean implementation attributes
    """
    element = op.target
    valueType = element.valueType
    
    if (element.isImplementation and
        isinstance(valueType, MetaModel.MetaDataType) and 
        valueType.typeCodes.get('python') == 'Boolean'):
        
        ss = 'bool(%s)' % self.getImplAttr(self.varNames['self'], element.name)
        self.setVar(self.varNames['result'], ss)
    
    else:
      super(PyFileApiGen, self).writeGetValue(op, inClass)
      
  ###########################################################################

  ###########################################################################

  # overrides ApiGen
  def writeStartFunc(self, op, inClass):

    PyApiGen.writeStartFunc(self, op, inClass)

    if (op.scope == metaConstants.instance_level and not
        (op.opType == 'new' and op.isImplicit)):
      self.setDataDict()

  ###########################################################################

  ###########################################################################

  # overrides FileApiGen
  def startTransaction(self, op, inClass):

    if op.opType == 'init':
    
      self.writeNewline()
      if isinstance(inClass, MetaModel.MetaClass):
        self.writeOne('try:')
        self.indent += self.INDENT

    FileApiGen.startTransaction(self, op, inClass)

  ###########################################################################

  ###########################################################################

  # overrides FileApiGen
  def endTransaction(self, op, inClass):

    FileApiGen.endTransaction(self, op, inClass)

    if op.opType == 'init':
      
      supertypes = inClass.getAllSupertypes()
      
      if isinstance(inClass, MetaModel.MetaClass):
      
        self.indent -= self.INDENT
      
        if self.dataRoot in supertypes:
          # MemopsRoot
          self.write("""
except:

  raise
""")

        else:
          # NB - sys.exc_info() allows you to re-raise previous exceptions
          # but keeping references around creates cyclic garbage.
          # deleting exc_info and using raise is better, but can not be done
          # where a new error has intervened. Hence the two different ways
          # of re-raising the original error
          self.write("""
except:
  import sys
  exc_info = sys.exc_info()
  try:
    %s['%s'] = True
    self.delete()
    del %s['%s']
  except:
    print('''WARNING Error in clean-up of incorrectly created object. 
    Data may be left in an illegal state''')
    del %s['%s']
  raise exc_info[0](exc_info[1])
""" % (self.varNames['dataDict'], self.varNames['inConstructor'], 
       self.varNames['dataDict'], self.varNames['inConstructor'], 
       self.varNames['dataDict'], self.varNames['inConstructor']))

  ###########################################################################

  # overrides PyApiGen
    
  # internal function 
  def getDataObjIdTuple(self, tag):
    """get DataObjType ID tuple.
    """
    
    ss = self.getValue(tag, self.baseDataType.getElement('qualifiedName'), 
                       lenient=True)
    dd = self.getDataDict(tag)
    #
    return "(%s,tuple((x, %s[x]) for x in sorted(%s)))" % (ss, dd ,dd)
    

  ###########################################################################

  ###########################################################################
  ###
  ### internal functions
  ###
  ###########################################################################

  ###########################################################################

  # internal function 
  def setDataDict(self):

    self.writeOne('%s = self.__dict__' % self.varNames['dataDict'])

  ###########################################################################

  ###########################################################################

  # internal function 
  def getDataDict(self, owner):

    if owner == self.varNames['self']:
      return self.varNames['dataDict']
    else:
      return '%s.__dict__' % owner

  ###########################################################################

  ###########################################################################

  def addComparisonsForClass(self, clazz):

    # __eq__ function
    self.startFunc('__eq__',
     params=(self.varNames['self'], self.varNames['other']),
     docString=""" equality function. With functools.totalordering allows object comparison."""
    )
    self.returnStatement(self.comparison(self.varNames['self'], 'is', self.varNames['other']))
    self.endFunc()

    # __hash__ function
    self.startFunc('__hash__',
     params=(self.varNames['self'],),
     docString=""" hash function. Necessary now we have __eq__."""
    )
    ss = self.callFunc('id', params=[self.varNames['self']], doWrite=False,)
    self.returnStatement(self.callFunc('hash',params=[ss], doWrite=False))
    self.endFunc()

    # __lt__ function
    self.startFunc('__lt__',
     params=(self.varNames['self'], self.varNames['other']),
     docString=""" comparison function. With functools.totalordering allows object comparison."""
    )

    self.write("""
selfClass = self.qualifiedName
otherClass = value.qualifiedName
if selfClass == otherClass:
  return self.getFullKey() < value.getFullKey()
else:
  return selfClass < otherClass""")

    self.endFunc()

  ###########################################################################

  ###########################################################################

  # internal function
  def addToStringForClass(self, clazz):
      
    # __repr__ function
    self.startFunc('__repr__', params=(self.varNames['self'],), 
                     docString=""" string representation of object.
    identifies object uniquely, but can not be executed to regenerate it.
    """)
    
    self.setDataDict()
    # get className
    self.startTry()
    self.getValue(self.varNames['self'], clazz.getElement('qualifiedName'), 
                  var='className', lenient=True)
    self.catchException()
    self.getValue(self.varNames['self'], clazz.getElement('className'), 
                  var='className', lenient=True)
    self.endTry()
    
    # get fullKey
    self.startTry()
    self.setVar('key', self.callFunc('getFullKey', self.varNames['self'], 
                                     doWrite=False))
    self.catchException()
    self.setVar('key', self.noneValue)
    self.endTry()
    
    # compensate for deletions
    self.startIf(self.getValue(self.varNames['self'], clazz.getElement('isDeleted'), 
                               lenient=True))
    self.setVar('ss', self.toLiteral(' (deleted)'))
    self.elseIf()
    self.setVar('ss', self.toLiteral(' '))
    self.endIf()
    
    # compensate for missing fullKey - NBNB Python specific
    self.startIf(self.negate(self.boolean('key')))
    self.setVar('key', self.callFunc('id', params=[self.varNames['self']], doWrite=False))
    self.write("ss = ss + 'id:'")
    self.endIf()
    
    # return result NBNB Python specific
    self.returnStatement("'<%s%s%s>' % (className, ss, key)")
    
    self.endFunc()
  
  ###########################################################################

  ###########################################################################

  # internal function 
  def addToStringForDataObj(self):

    # __repr__ function
    self.startFunc('__repr__',
     params=(self.varNames['self'], ), 
     docString=""" string representation of object.
    identifies object uniquely, but can not be executed to regenerate it."""
    )
    self.setDataDict()
    self.setVar('tt', self.getDataObjIdTuple(self.varNames['self']))
    self.setVar('ss', 
                "', '.join('%s=%s' % (x[0], repr(x[1])) for x in tt[1])")
    
    self.returnStatement("'<%s {%s}>' % (tt[0], ss)")
    
    self.endFunc()
  
  ###########################################################################

  ###########################################################################

    # __lt__, __eq__, and __hash__  functions
  def addComparisonsForDataObj(self):
    self.startFunc('__lt__',
     params=(self.varNames['self'], self.varNames['other']),
     docString=""" less-than function. With functools.totalordering allows object comparison."""
    )
    self.setDataDict()
    self.returnStatement(self.comparison(self.getDataObjIdTuple(self.varNames['self']), '<',
                                         self.getDataObjIdTuple(self.varNames['other'])))

    self.endFunc()

    # __eq__ function
    self.startFunc('__eq__',
     params=(self.varNames['self'], self.varNames['other']),
     docString=""" equality function. With functools.totalordering allows object comparison."""
    )
    self.setDataDict()
    self.startTry()
    self.returnStatement(self.equals(self.getDataObjIdTuple(self.varNames['self']),
                                         self.getDataObjIdTuple(self.varNames['other'])))
    self.catchException()
    self.returnStatement(self.comparison(self.varNames['self'], 'is', self.varNames['other']))
    self.endTry()
    self.endFunc()
      
    # __hash__ function
    self.startFunc('__hash__', params=(self.varNames['self'],), 
     docString=" basic hash function. NB inConstructor is automatically excluded"
    )
    
    self.setDataDict()
    self.setVar('tt', self.getDataObjIdTuple(self.varNames['self']))
    self.returnStatement(self.callFunc('hash', params=['tt'], doWrite=False))
    
    self.endFunc()
  
  ###########################################################################
