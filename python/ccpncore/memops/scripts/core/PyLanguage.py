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
""" Python language writing. 
"""

import os

from ccpncore.memops.metamodel.MetaModel import MemopsError
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.metamodel import TextWriter
from ccpncore.memops.metamodel import Util as metaUtil
from ccpncore.memops.scripts.core import LanguageInterface


try:
  StringType = basestring
except NameError:
  StringType = str



class PyLanguage(LanguageInterface.LanguageInterface, TextWriter.TextWriter, object):

  def __init__(self):

    settings = TextWriter.settings['python']
    for (tag, val) in settings.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)
        
    for tag in LanguageInterface.mandatoryAttributes:
      if not hasattr(self, tag):
        raise MemopsError(" PyLanguage lack mandatory %s attribute" % tag)

    # 
    super(PyLanguage, self).__init__()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def createDir(self, dirName):

    TextWriter.TextWriter.createDir(self, dirName)
    fullfile = os.path.join(dirName, '__init__.py')
    if not os.path.exists(fullfile):
      fp = open(fullfile, 'w')
      fp.close()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def setVar(self, var, value, varType=None, castType=None):

    self.writeOne('%s = %s' % (var, value))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def castVar(self, castType, var):

    return var

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def defineVar(self, var, varType):

    pass

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def returnStatement(self, value = None):

    if value is None:
      s = 'return'
    else:
      s = 'return %s' % value

    self.writeOne(s)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def noStatement(self):

    self.writeOne('pass')

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def lenString(self, string):

    return 'len(%s)' % string

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def toLiteral(self, value):

    result = repr(value)
    if eval(result, {}) == value:
      return result
    else:
      raise MemopsError("value cannot be converted to literal: %s" % value)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def collectionIsEmpty(self, collection, isUnique, isOrdered, varType=None):

    return 'not %s' % collection

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def collectionIsNotEmpty(self, collection, isUnique, isOrdered, varType=None):

    return '%s' % collection

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def collectionNotNoneAndNotEmpty(self, collection, isUnique, isOrdered, varType=None):

    return '%s' % collection

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def valueNotNoneAndIfCollectionNotEmpty(self, value, isUnique, isOrdered, varType=None):

    return '%s' % value

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def lenCollection(self, collection, isUnique, isOrdered, varType=None):

    return 'len(%s)' % collection

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def newCollection(self, collection, isUnique, isOrdered, varType=None, initValues=None,
                    isFrozen=False, needDeclType=False, useAdd=False):
    """ initValues must be a string variable name (referring to an iterable)
    an iterable of literals, or None"""
    
    # convert input if list of literals
    haveListInitValues = False
    if not initValues:
      initValues = ''
      
    elif not isinstance(initValues, StringType):
      haveListInitValues = True
      initValues = '(%s,)' % ', '.join([self.toLiteral(x) for x in initValues])
    
    # make newCollection string
    if isUnique and not isOrdered:
      if isFrozen:
        c = 'frozenset(%s)' % initValues
      else:
        c = 'set(%s)' % initValues
        
    elif haveListInitValues:
      if isFrozen:
        c = initValues
      else:
        c = '[%s]' % initValues[1:-2]
        
    else:
      if isFrozen:
        c = 'tuple(%s)' % initValues
      else:
        c = 'list(%s)' % initValues
        
    if collection is None:
      return c
    else:
      self.writeOne('%s = %s' % (collection, c))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def addCollection(self, var, collection, isUnique, isOrdered, varType=None):

    if isUnique and not isOrdered:
      f = 'add'
    else:
      f = 'append'

    self.writeOne('%s.%s(%s)' % (collection, f, var))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def addAllCollection(self, var, collection, isUnique, isOrdered, varType=None):

    if isUnique and not isOrdered:
      f = 'update'
    else:
      f = 'extend'

    self.writeOne('%s.%s(%s)' % (collection, f, var))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def popCollection(self, var, collection, isUnique, isOrdered,
                    varType=None, castType=None):

    self.writeOne('%s = %s.pop()' % (var, collection))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def getCollection(self, var, collection, isUnique, isOrdered, varType=None):
    """ Get first element from ordered collection, 
    and random element from others. Works whether modifiable or not.
    """
    
    self.defineVar(var, varType)
    
    if isUnique and not isOrdered:
      ss = "next(iter(%s))" % collection
    else:
      ss = "%s[0]" % collection
    
    if var is None:
      return ss
    else:
      self.writeOne("%s = %s" % (var, ss))
      
    
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def getListSlice(self, collection, lo=0, hi=None, varType=None):
    """ get slice out of list
    """
    
    if hi is None:
      return '%s[%s:]' % (collection, lo)
    elif lo == 0:
      return '%s[:%s]' % (collection, hi)
    else:
      return '%s[%s:%s]' % (collection, lo, hi)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def reverseList(self, collection):

    self.writeOne('%s.reverse()' % collection)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def removeCollection(self, var, collection, isUnique, isOrdered, varType=None):

    self.writeOne('%s.remove(%s)' % (collection, var))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def isInCollection(self, var, collection, isUnique, isOrdered, varType=None):
    
    return '%s in %s' % (var, collection)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def countInCollection(self, var, collection, 
                        isUnique, isOrdered, varType=None):

    if isUnique:
      return '%s in %s and 1 or 0' % (var, collection)
    else:
      return '%s.count(%s)' % (collection, var)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def replaceInCollection(self, oldvar, newvar, collection, 
                          isUnique, isOrdered, varType=None):
    """ resulting code may raise KeyError (for unique, nonordered)
     or ValueError (for all others)
    """
    if isUnique and not isOrdered:
      # implemented as set
      self.removeCollection(oldvar, collection, isUnique, isOrdered, varType)
      self.startIf(self.isInCollection(newvar, collection, isUnique, isOrdered, varType))
      self.addCollection(oldvar, collection, isUnique, isOrdered, varType)
      self.raiseApiError("replacement value already in unique collection ",
                         newvar)
      self.elseIf()
      self.addCollection(newvar, collection, isUnique, isOrdered, varType)
      self.endIf()
    else:
      # all others implemented as lists
      self.setVar('replaceIndex', 
       self.indexInCollection(oldvar, collection, isUnique, isOrdered, varType),
       varType
      )
      if isUnique:
        self.setByIndexInCollection(
         'replaceIndex', 'None', collection, isUnique, isOrdered, varType
        )
        self.startIf(self.isInCollection(newvar, collection, isUnique, isOrdered, varType))
        self.setByIndexInCollection(
         'replaceIndex', oldvar, collection, isUnique, isOrdered, varType
        )
        self.raiseApiError("replacement value already in unique collection ",
                           newvar)
        self.elseIf()
        self.setByIndexInCollection(
         'replaceIndex', newvar, collection, isUnique, isOrdered, varType
        )
        self.endIf()
      else:
        self.setByIndexInCollection(
         'replaceIndex', newvar, collection, isUnique, isOrdered, varType
        )
           
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def indexInCollection(self, var, collection, 
                        isUnique, isOrdered, varType=None):
  
    if isUnique and not isOrdered:
      raise MemopsError(
       "indexInCollection not defined for isUnique=%s, isOrdered=%s"
       % (isUnique, isOrdered)
      )
    else:
      return '%s.index(%s)' % (collection, var)
      
  ###########################################################################

  ###########################################################################
  
  # implements LanguageInterface
  def getByIndexInCollection(self, index, collection, 
                        isUnique, isOrdered, varType=None):
                        
    if isUnique and not isOrdered:
      raise MemopsError(
       "getByIndexInCollection not defined for isOrdered=%s"
       % isOrdered
      )
    else:
      return '%s[%s]' % (collection, index)
    
      
  ###########################################################################

  ###########################################################################
  
  def setByIndexInCollection(self, indexvar, var, collection, 
                             isUnique, isOrdered, varType=None):
    if not isOrdered:
      raise MemopsError(
       "setByIndexInCollection not defined for isOrdered=%s"
       % isOrdered
      )
    else:
      self.writeOne('%s[%s] = %s' % (collection, indexvar, var))
    
  ###########################################################################

  ###########################################################################
  
  def concatenateCollection(self, newCollection, isUnique, isOrdered,
                            varType=None, *collections):

    self.writeOne('%s = %s' % (newCollection, ' + '.join(collections)))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def newStack(self, stack, varType=None, initValues=None, needDeclType=False):

    if not initValues:
      initValues = []

    initValues = ', '.join(initValues)
    self.writeOne('%s = [%s]' % (stack, initValues))
      
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stackIsEmpty(self, stack):

    return 'not %s' % stack

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stackIsNotEmpty(self, stack):

    return stack

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def pushStack(self, stack, var):

    self.writeOne('%s.append(%s)' % (stack, var))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def popStack(self, stack, var=None, varType=None, castType=None, doWrite = True):

    if not doWrite:
      assert not var

    if var:
      ss = '%s = ' % var
    else:
      ss = ''

    if doWrite:
      self.writeOne('%s%s.pop()' % (ss, stack))
    else:
      return '%s.pop()' % stack

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def peekStack(self, stack, var=None, varType=None, castType=None):

    if var:
      self.writeOne('%s = %s[-1]' % (var, stack))
    else:
      return '%s[-1]' % stack

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stackSize(self, stack):

    return 'len(%s)' % stack

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def inEnumeration(self, value, enumeration):

    return '%s in %s' % (value, enumeration)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def constructorFuncname(self, clazz):

    return '__init__'

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startFunc(self, funcname, params=None, docString=None, returnType=None, throwsTypes=None):
    
    params = params or []
    paramString = ', '.join(params)

    self.write('''
def %s(%s):''' % (funcname, paramString))

    self.indent += self.INDENT
    
    if docString:
      self.writeMultilineComment(docString)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endFunc(self):

    self.indent -= self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def callFunc(self, func, obj=None, params=None, doWrite=True):
    """ call function with normal parameters
    """

    pars = []
    params = metaUtil.coerceToList(params)

    for par in params:
      if par == 'false':
        print("WARNING, conversion of 'false' will disappear")
        par = 'False'
      elif par == 'true':
        print("WARNING, conversion of 'true' will disappear")
        par = 'True'
      pars.append(par)
    if obj is None:
      s = '%s(%s)' % (func, ', '.join(pars))
    else:
      s = '%s.%s(%s)' % (obj, func, ', '.join(pars))

    if doWrite:
      self.writeOne(s)
    else:
      return s

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def callKwFunc(self, func, obj=None, params=None, setVarTo=None, kwDict={}):
    
    # NBNB TBD in use? remove?
    
    params = metaUtil.coerceToList(params)
    
    for key,val in kwDict.items():
      params.append('%s=%s' % (key,val))
    #
    
    if setVarTo is None:
      self.callFunc(func, obj, params)
    else:
      self.writeOne('%s = %s' % 
                    (setVarTo, self.callFunc(func, obj, params, doWrite=False)))
    
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startBlock(self):

    pass

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endBlock(self):

    pass

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def exceptionClass(self, exception = None):

    if exception is None:
      ee = 'Exception'
    elif exception in ('KeyError', 'ApiError'):
      ee = exception
    else:
      raise MemopsError("Unexpected exceptionClass" % exception)

    return ee

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startTry(self):

    self.writeOne('try:')
    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def catchException(self, exception = None, exceptionVar = 'ex'):

    self.indent -= self.INDENT
    if exception is None:
      self.writeOne('except:')
    else:
      self.writeOne('except %s as %s:' % (exception, exceptionVar))
    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endTry(self):

    self.indent -= self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def reraiseException(self, exceptionVar = 'exc', exceptionClass = None):

    self.writeOne('raise')

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startLoop(self, var, collection, isUnique, isOrdered, varType=None):
      
    self.writeOne('for %s in %s:' % (var, collection))
    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endLoop(self):

    self.indent -= self.INDENT
    self.writeNewline()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def continueLoop(self):
      
    self.writeOne('continue')

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def breakLoop(self):
      
    self.writeOne('break')

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startIndexLoop(self, iVar, nVar, isReversed = False):
      
    ss = 'range(%s)' % nVar
    if isReversed:
      ss = 'reversed(%s)' % ss

    self.writeOne('for %s in %s:' % (iVar, ss))
    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endIndexLoop(self):

    self.indent -= self.INDENT
    self.writeNewline()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startWhile(self, condition):

    self.writeOne('while %s:' % condition)
    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endWhile(self):

    self.indent -= self.INDENT
    self.writeNewline()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def startIf(self, condition):

    self.writeOne('if (%s):' % condition)

    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def elseIf(self, condition = None):

    self.indent -= self.INDENT

    if condition is None:
      s = 'else:'
    else:
      s = 'elif (%s):' % condition

    self.writeOne(s)
    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def endIf(self):

    self.indent -= self.INDENT
    self.writeNewline()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def negate(self, condition):

    return 'not (%s)' % condition

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def boolean(self, expression):

    return expression

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def comparison(self, expression1, func, expression2):

    return '%s %s %s' % (expression1, func, expression2)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def equals(self, expression1, expression2):

    return '%s == %s' % (expression1, expression2)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def logicalOp(self, expression1, op, expression2):

    return '(%s %s %s)' % (expression1, op, expression2)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def newDict(self, dictVar=None, keyType=None, valueType=None, needDeclType=False):
    
    if dictVar is None:
      return '{}'
    else:
      self.writeOne('%s = {}' % dictVar)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  # below assumes key is variable not literal
  def getDictEntry(self, dictVar, key, castType = None,
                   defaultValue = None, keyIsMandatory = False):

    assert defaultValue is None or not keyIsMandatory

    if keyIsMandatory:
      return "%s[%s]" % (dictVar, key)
    elif defaultValue is None:
      return "%s.get(%s)" % (dictVar, key)
    else:
      return "%s.get(%s, %s)" % (dictVar, key, defaultValue)
    
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  # below assumes key is variable not literal
  def setDictEntry(self, dictVar, key, value):

    self.writeOne("%s[%s] = %s" % (dictVar, key, value))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  # below assumes key is variable not literal
  def removeDictEntry(self, dictVar, key):

    self.writeOne("del %s[%s]" % (dictVar, key))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  # below assumes key is variable not literal
  # NB probably unnecessary - same as removeDictEntry. Removed
  #def popDictEntry(self, dictVar, key):
  #
  #  self.writeOne("%s.pop(%s)" % (dictVar, key))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def keyIsInDict(self, dictVar, key):

    return '%s in %s' % (key, dictVar)

  ###########################################################################

  ###########################################################################

  def getDictKeys(self, dictVar):

    return '%s.keys()' % dictVar

  ###########################################################################

  ###########################################################################

  def getDictValues(self, dictVar):

    return '%s.values()' % dictVar

  ###########################################################################

  ###########################################################################
  
  # implements LanguageInterface
  def startLoopOverDictKeys(self, dictVar, keyVar, varType=None):
    
    self.writeOne('for %s in %s.keys():' % (keyVar, dictVar))
    self.indent += self.INDENT
  
  ###########################################################################

  ###########################################################################
  
  # implements LanguageInterface
  def lenDict(self, dictVar):

    return 'len(%s)' % dictVar
  
  ###########################################################################

  ###########################################################################
  
  # implements LanguageInterface
  def dictIsEmpty(self, dictVar):

    return 'not %s' % dictVar
  
  ###########################################################################

  ###########################################################################
  
  # implements LanguageInterface
  def dictIsNotEmpty(self, dictVar):

    return '%s' % dictVar
  
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def incrementInteger(self, var):

    self.writeOne('%s = %s + 1' % (var, var))

  ###########################################################################

  ###########################################################################

  # below assumes var are variables not literals
  # implements LanguageInterface
  def subtractIntegers(self, var1, var2):

    return '%s - %s' % (var1, var2)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def arithmetic(self, expression1, op, expression2):
  
    if op not in ('+','-','*','/'):
      raise MemopsError("arithmetic operation %s not supported" % op )

    return '(%s %s %s)' % (expression1, op, expression2)

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stringReplace(self, val, stringToMatch, stringToReplace):

    return '%s.replace(%s, %s)' % (val, stringToMatch, stringToReplace)
  
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stringIsNotEmpty(self, val):

    return val

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def stringSlice(self, val, fromStart=0, fromEnd=None):
    """Slice string. Uses Python convention with positive and negative indices"""

    if fromEnd:
      return '%s[%s:%s]' % (val, fromStart, fromEnd)
    else:
      return '%s[%s:]' % (val, fromStart)


  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def currentTime(self):

    return 'time.ctime()'

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def printMessage(self, *objs):

    self.write("print(%s)" % ', '.join(objs))

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def isInstance(self, var, className):
    
    return "isinstance(%s, %s)" % (var, className)

  ###########################################################################

  ###########################################################################

  def getClass(self, var):
    """ Get class of object passed in. Expression
    """

    return "%s.__class__" % var
    
  ###########################################################################

  ###########################################################################

  def getClassname(self, var):
    """ Get string class name of object passed in. Expression
    """

    return "%s.__class__.__name__" % var
    
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def raiseApiError(self, errorMsg, obj = None, obj2 = None, obj3 = None, inOp=None):
    """NB obj and obj2 and obj3 must evaluate to a single Python object
    More specifically you can pass in a tuple, like '(a,b,c)'
    but not a comma-separated list, like 'a,b,c'
    """
    
    if inOp and inOp.scope == metaConstants.classifier_level:
      ss = self.toLiteral(inOp.container.qualifiedName())
      self.write('''raise ApiError("""%s%s:
 %s""" ''' % (ss, self.errorMsg, errorMsg))
    
    elif inOp == False:          # NBNB Deliberate. False and None are treated differently
      # special case - we are not in a CCPN object
      if self.errorMsg:
        self.write('''raise ApiError("""%s:
 %s""" ''' % (self.errorMsg, errorMsg))
      else:
        self.write('''raise ApiError("""%s""" ''' % errorMsg)

    else:
      self.write('''raise ApiError("""%%s%s:
 %s""" %% self.qualifiedName''' % (self.errorMsg, errorMsg))
    
    if obj and obj2 and obj3:
      self.writeOne(' + ": %%s:%%s:%%s" %% (%s, %s, %s)' % (obj, obj2, obj3))
    elif obj and obj2:
      self.writeOne(' + ": %%s:%%s" %% (%s, %s)' % (obj, obj2))
    elif obj:
      self.writeOne(' + ": %%s" %% (%s,)' % obj)
      
    self.writeOne(')')

  ###########################################################################

  ###########################################################################
  
  # language-specific functions that interrogate the model.
  
  # NB TBD should maybe be split off in the future

  ###########################################################################

  # implements LanguageInterface
  def getFuncParams(self, op, defineFunc=True):
    
    if defineFunc and op.scope == metaConstants.instance_level:
      result = ['self']
    else:
      result = []
    
    for par in op.parameters:
      
      if par.direction != metaConstants.return_direction:
      
        pName = par.name
 
        if par.taggedValues.get('isSubdivided'):
          if par.hicard == 1:
            # keywordValue parameters (dict)
            result.append('**' + pName)
          else:
            # normal parameters (list)
            result.append('*' + pName)
 
        elif defineFunc and ((par.locard == 0 and par.hicard == 1)
              or par.defaultValue is not None):
          # optional parameter. NB the or statement is currently superflous
          # but we might allow defaults for hicard!= 1 later
          result.append("%s=%s" % (pName, self.toLiteral(par.defaultValue)))
 
        else:
          # mandatory parameter
          result.append(pName)
    #
    return result
  
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def getDocString(self, op, inClass=None):
    
    return metaUtil.breakString(op.documentation)
  
  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def getOpValueType(self, op):
    
    # Python has no type
    
    return ''

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def getReturnType(self, op):
    
    # Python has no returntype
    
    return ''

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def getThrowsTypes(self, op):
    
    # Python has no exception reporting at start of function
    
    return ()

  ###########################################################################

  ###########################################################################

  # implements LanguageInterface
  def funcDeclaration(self, op):
    # NBNB TBD move to IntGen

    pass # this used only in interface, which does not exist in Python

  ###########################################################################

  ###########################################################################
