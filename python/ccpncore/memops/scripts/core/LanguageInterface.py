# interface for languages, with some implementation

from ccpncore.memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError
#
# ######################################################################
# # hack for Python 2.1 compatibility  NBNB                            #
# ######################################################################
# try:
#   junk = True
#   junk = False
# except:
#   dd = globals()
#   dd['True'] = not 0
#   dd['False'] = not True
#   del dd

mandatoryAttributes = ('noneValue',)

class LanguageInterface:

  ###########################################################################

  ###########################################################################

  # Functions which must be implemented in subclasses
  # Functions require real language-specific types

  def setVar(self, var, value, varType = None, castType = None):

    raise NotImplementedError("Should be overridden")

  def castVar(self, castType, var):

    raise NotImplementedError("Should be overridden")

  def defineVar(self, var, varType):

    raise NotImplementedError("Should be overridden")

  def returnStatement(self, value = None):

    raise NotImplementedError("Should be overridden")

  def noStatement(self):

    raise NotImplementedError("Should be overridden")

  def lenString(self, string):

    raise NotImplementedError("Should be overridden")

  def toLiteral(self, value):
    """ String representation of 'value' that will work as a literal
    in an expression. For languages that makes the distinction this will be
    an 'object' rather than a 'raw' literal.
    NB for objects that have no equivalent literal, behaviour is unpredictable
    """

    raise NotImplementedError("Should be overridden")
  
  
  # NBNB TBD can't we get rid of all this list-specific stuff? 
  # Use instead a fixed listPars = {'isUnique':False, 'isOrdered':True} and call the normal
  # collection functions with **listPars
  def listIsEmpty(self, collection, varType=None):

    return self.collectionIsEmpty(collection, isUnique=False, isOrdered=True, varType=varType)

  def listIsNotEmpty(self, collection, varType=None):

    return self.collectionIsNotEmpty(collection, isUnique=False, isOrdered=True, varType=varType)

  def listNotNoneAndNotEmpty(self, collection, varType=None):

    return self.collectionNotNoneAndNotEmpty(collection, isUnique=False, isOrdered=True, varType=varType)

  def valueNotNoneAndIfListNotEmpty(self, value, varType=None):

    return self.valueNotNoneAndIfCollectionNotEmpty(value, isUnique=False, isOrdered=True, varType=varType)

  def lenList(self, collection, varType=None):

    return self.lenCollection(collection, isUnique=False, isOrdered=True, varType=varType)

  def newList(self, collection, varType=None,
        initValues=None, isFrozen=False, needDeclType=False):
    
    return self.newCollection(collection, isUnique=False, isOrdered=True,
                              varType=varType, initValues=initValues,
                              isFrozen=isFrozen, needDeclType=needDeclType)

  def addList(self, var, collection, varType=None):

    return self.addCollection(var, collection, isUnique=False, isOrdered=True, varType=varType)

  def addAllList(self, var, collection, varType=None):

    return self.addAllCollection(var, collection, isUnique=False, isOrdered=True, varType=varType)

  def popList(self, var, collection, varType=None, castType=None):

    return self.popCollection(var, collection, isUnique=False, isOrdered=True, varType=varType, castType=castType)

  def getList(self, var, collection, varType=None):
    # NBNB keep varType for eventual use in other, typed languages

    return self.getCollection(var, collection, isUnique=False, isOrdered=True, varType=None)

  def removeList(self, var, collection, varType=None):

    return self.removeCollection(var, collection, isUnique=False, isOrdered=True, varType=varType)

  def isInList(self, var, collection, varType=None):

    return self.isInCollection(var, collection, isUnique=False, isOrdered=True, varType=varType)

  def countInList(self, var, collection, varType=None):

    return self.countInCollection(var, collection, isUnique=False, isOrdered=True, varType=varType)

  def replaceInList(self, oldvar, newvar, collection, varType=None):

    return self.replaceInCollection(oldvar, newvar, collection,
                          isUnique=False, isOrdered=True, varType=varType)

  
  def indexInList(self, var, collection, varType=None):

    return self.indexInCollection(var, collection,
                        isUnique=False, isOrdered=True, varType=varType)
  
  def setByIndexInList(self, indexvar, var, collection, varType=None):

    return self.setByIndexInCollection(indexvar, var, collection, 
                              isUnique=False, isOrdered=True, varType=varType)
    
  def getByIndexInList(self, index, collection, varType=None):

    return self.getByIndexInCollection(index, collection, 
                        isUnique=False, isOrdered=True, varType=varType)
  
  def concatenateList(self, newCollection, varType=None, *collections):

    return self.concatenateCollection(newCollection, False, True, varType, *collections)

  def collectionIsEmpty(self, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def collectionIsNotEmpty(self, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def collectionNotNoneAndNotEmpty(self, collection, isUnique, isOrdered, varType=None):
    """ NBNB TBD do we need this and the following? 
    """

    raise NotImplementedError("Should be overridden")

  def valueNotNoneAndIfCollectionNotEmpty(self, value, isUnique, isOrdered, varType=None):
    """ NBNB TBD do we need this and the preceding? 
    """

    raise NotImplementedError("Should be overridden")

  def lenCollection(self, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def newCollection(self, collection, isUnique, isOrdered, varType=None,
        initValues=None, isFrozen=False, needDeclType=False, useAdd=False):
    """ make new collection, possibly initailising it. 
    
    - collection is the variable name to set the new collection to.
    If collection is set, newCollection code will set the variable.
    If collection is None an expression will be returned.
    - if initValues if a string expression the new collection will be
    initialised from this string expression at runtime.
.   If initValues is a collection of literals the code will initialise
    the new collection to these values. NB this requires collection != None
    - if isFrozen the new collection will be frozen.
    - if initValuesObject is True then initValues represents an object rather than a collection
    - useAdd is a Java hack
    """
    
    raise NotImplementedError("Should be overridden")

  def addCollection(self, var, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def addAllCollection(self, var, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def popCollection(self, var, collection, isUnique, isOrdered, varType=None, castType=None):

    raise NotImplementedError("Should be overridden")

  # NOTE: only used in a couple of spots, assumes len(collection) > 0, should return (any) item
  def getCollection(self, var, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def getListSlice(self, collection, lo=0, hi=None, varType=None):

    raise NotImplementedError("Should be overridden")

  def reverseList(self, collection):

    raise NotImplementedError("Should be overridden")

  def removeCollection(self, var, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def isInCollection(self, var, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def countInCollection(self, var, collection, isUnique, isOrdered, varType=None):

    raise NotImplementedError("Should be overridden")

  def replaceInCollection(self, oldvar, newvar, collection, 
                          isUnique, isOrdered, varType=None):
    """ replace oldVar with newvar in collection.
    Will raise appropriate error if oldvar not present
    If the result breaks uniqueness or type constraints the collection
    is left unmodified and an error is raised.
    """

    raise NotImplementedError("Should be overridden")
  
  def indexInCollection(self, var, collection,
                        isUnique, isOrdered, varType=None):
    """ expression giving index of var in collection. Must work on ordered collections
    as well as any unordered collections that are implemented as sequences.
    """

    raise NotImplementedError("Should be overridden")
  
  def setByIndexInCollection(self, indexvar, var, collection, 
                              isUnique, isOrdered, varType=None):
    """ set value by index of var in collection. 
    Must work on ordered collections as well as any unordered
    collections that are implemented as sequences.
    """

    raise NotImplementedError("Should be overridden")
    
  def getByIndexInCollection(self, index, collection, 
                        isUnique, isOrdered, varType=None):
    """ get value by index. Works only on ordered collections.
    Returns an expression
    """
    raise NotImplementedError("Should be overridden")
  
  def concatenateCollection(self, newCollection, isUnique, isOrdered,
                            varType=None, *collections):

    raise NotImplementedError("Should be overridden")

  def newStack(self, stack, varType=None, initValues=None, needDeclType=False):

    raise NotImplementedError("Should be overridden")

  def stackIsEmpty(self, stack):

    raise NotImplementedError("Should be overridden")

  def stackIsNotEmpty(self, stack):

    raise NotImplementedError("Should be overridden")

  def pushStack(self, stack, var):

    raise NotImplementedError("Should be overridden")

  def popStack(self, stack, var=None, varType=None, castType=None, doWrite=True):

    raise NotImplementedError("Should be overridden")

  def peekStack(self, stack, var=None, varType=None, castType=None):

    raise NotImplementedError("Should be overridden")

  def stackSize(self, stack):

    raise NotImplementedError("Should be overridden")

  def inEnumeration(self, value, enumeration):

    raise NotImplementedError("Should be overridden")

  def constructorFuncname(self, clazz):

    raise NotImplementedError("Should be overridden")

  def startFunc(self, funcname, params=None, docString=None, returnType=None, throwsTypes=None):
    
    raise NotImplementedError("Should be overridden")

  def endFunc(self):

    raise NotImplementedError("Should be overridden")

  def callFunc(self, func, obj=None, params=None, doWrite=True):

    raise NotImplementedError("Should be overridden")
    
  def callKwFunc(self, func, obj=None, params = None, setVarTo=None, kwDict={}):
    """ call function with keyword-value parameters.
    kwDict keys are assumed to be strings, kwDict values are assumed to be
    printable as given (hint - use toLiteral for literals).
    the result is set to setVarTo, unless this is None
    
    NB for languages that do not accept keyword-value parameters, the information
    is passed in a dictionary variable that is put last on the variable list.
    callKwFunc will only work for functions that have this behaviour.
    """

    raise NotImplementedError("Should be overridden")

  def startBlock(self):

    raise NotImplementedError("Should be overridden")

  def endBlock(self):

    raise NotImplementedError("Should be overridden")

  def exceptionClass(self, exception = None):

    raise NotImplementedError("Should be overridden")

  def startTry(self):

    raise NotImplementedError("Should be overridden")

  def catchException(self, exception = None, exceptionVar = 'ex'):

    raise NotImplementedError("Should be overridden")

  def endTry(self):

    raise NotImplementedError("Should be overridden")

  def reraiseException(self, exceptionVar = 'exc', exceptionClass = None):

    raise NotImplementedError("Should be overridden")

  def startLoop(self, var, collection, isUnique, isOrdered, varType=None):
    raise NotImplementedError("Should be overridden")

  def endLoop(self):

    raise NotImplementedError("Should be overridden")

  def continueLoop(self):

    raise NotImplementedError("Should be overridden")

  def breakLoop(self):

    raise NotImplementedError("Should be overridden")

  def startIndexLoop(self, iVar, nVar, isReversed = False):

    raise NotImplementedError("Should be overridden")

  def endIndexLoop(self):

    raise NotImplementedError("Should be overridden")

  def startWhile(self, condition):

    raise NotImplementedError("Should be overridden")

  def endWhile(self):

    raise NotImplementedError("Should be overridden")

  def startIf(self, condition):

    raise NotImplementedError("Should be overridden")

  def elseIf(self, condition = None):

    raise NotImplementedError("Should be overridden")

  def endIf(self):

    raise NotImplementedError("Should be overridden")

  def negate(self, condition):

    raise NotImplementedError("Should be overridden")

  # this is for Java, to convert from Boolean to boolean
  def boolean(self, expression):

    raise NotImplementedError("Should be overridden")

  def comparison(self, expression1, func, expression2):

    raise NotImplementedError("Should be overridden")

  def equals(self, expression1, expression2):

    # expression1 or expression2 can be null
    raise NotImplementedError("Should be overridden")

  def logicalOp(self, expression1, op, expression2):

    raise NotImplementedError("Should be overridden")

  def newDict(self, dictVar=None, keyType=None, valueType=None, needDeclType=False):
    """ if dictVar is None returns expression, else write statement
    """

    raise NotImplementedError("Should be overridden")

  def getDictEntry(self, dictVar, key, castType = None,
                   defaultValue = None, keyIsMandatory = False):

    raise NotImplementedError("Should be overridden")

  def setDictEntry(self, dictVar, key, value):

    raise NotImplementedError("Should be overridden")

  def removeDictEntry(self, dictVar, key):

    raise NotImplementedError("Should be overridden")

  #def popDictEntry(self, dictVar, key):
  #  # NB probably unnecessary - identical to removeDictEntry. Removed
  #
  #  raise NotImplementedError("Should be overridden")

  def keyIsInDict(self, dictVar, key):

    raise NotImplementedError("Should be overridden")

  def getDictKeys(self, dictVar):
    """ set dict keys as collection or iterable
    NB must be valid as initValue to newCollection
    """

    raise NotImplementedError("Should be overridden")

  def getDictValues(self, dictVar):
    """ set dict values as collection or iterable
    NB must be valid as initValue to newCollection
    """

    raise NotImplementedError("Should be overridden")
  
  def startLoopOverDictKeys(self, dictVar, keyVar, varType=None):

    raise NotImplementedError("Should be overridden")
  
  def lenDict(self, dictVar):

    raise NotImplementedError("Should be overridden")

  def dictIsEmpty(self, dictVar):

    raise NotImplementedError("Should be overridden")

  def dictIsNotEmpty(self, dictVar):

    raise NotImplementedError("Should be overridden")

  def incrementInteger(self, var):

    raise NotImplementedError("Should be overridden")

  def subtractIntegers(self, var1, var2):

    raise NotImplementedError("Should be overridden")
    
  def arithmetic(self, expression1, op, expression2):

    raise NotImplementedError("Should be overridden")

  def stringReplace(self, val, stringToMatch, stringToReplace):

    raise NotImplementedError("Should be overridden")

  def stringIsNotEmpty(self, val):

    raise NotImplementedError("Should be overridden")

  def stringSlice(self, val, fromStart=0, fromEnd=None):

    raise NotImplementedError("Should be overridden")

  def currentTime(self):

    raise NotImplementedError("Should be overridden")

  def printMessage(self, message, *objs):

    raise NotImplementedError("Should be overridden")

  def isInstance(self, var, className):
    """ Boolean - is (string) var an instance of (string) clazz?
    """

    raise NotImplementedError("Should be overridden")

  def getClass(self, var):
    """ Get class of object passed in. Expression
    """

    raise NotImplementedError("Should be overridden")
    
  def getClassname(self, var):
    """ Get string class name of object passed in. Expression
    """

    raise NotImplementedError("Should be overridden")
    
  ###########################################################################
  
  # language-specific functions that interogate the model.
  
  # NB TBD should maybe be split off in the future

  def getFuncParams(self, op, defineFunc=True):
    """ get parameters as list of strings.
    If defineFunc get strings for function definition.
    Else get strings for function calls, assuming you use same variable names 
    as the definition. This second form is used e.g. to call constructors
    in factory functions.
    """

    raise NotImplementedError("Should be overridden")

  def getDocString(self, op, inClass=None):

    raise NotImplementedError("Should be overridden")

  def getOpValueType(self, op):

    raise NotImplementedError("Should be overridden")

  def getReturnType(self, op):

    raise NotImplementedError("Should be overridden")

  def getThrowsTypes(self, op):

    raise NotImplementedError("Should be overridden")

  def funcDeclaration(self, op):

    raise NotImplementedError("Should be overridden")


  ###########################################################################

  def raiseApiError(self, errorMsg, obj = None, obj2 = None, obj3 = None, inOp=None):

    raise NotImplementedError("Should be overridden")

  ###########################################################################

  ###########################################################################
