
"""
======================COPYRIGHT/LICENSE START==========================

PyXmlMapWrite.py: Code generation for CCPN framework

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
from ccpncore.memops.scripts.xmlio.XmlMapWrite import XmlMapWrite
from ccpncore.memops.scripts.core.PyLanguage import PyLanguage
from ccpncore.memops.scripts.core.PyType import PyType

MemopsError = MetaModel.MemopsError


def writeXmlIo(modelPortal, rootFileName=None, rootDirName=None,
             releaseVersion=None, **kw):
  """write Python XML I/O mappings and code 
  
  Only function that should be called directly by 'make' scripts etc.
  """
  
  pyXmlWrite = PyXmlMapWrite(modelPortal=modelPortal, rootFileName=rootFileName, 
                        rootDirName=rootDirName, releaseVersion=releaseVersion,
                        scriptName='PyXmlMapWrite', **kw)
  pyXmlWrite.processModel()


class PyXmlMapWrite(PyLanguage, PyType, XmlMapWrite):

  def __init__(self, **kw):
  
    self.addModelFlavour('language', 'python')
    self.baseName = 'xml'
  
    for (tag, val) in kw.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)
    
    super(PyXmlMapWrite, self).__init__()

  ###########################################################################

  ###########################################################################
  
  # overrides XmlMapWrite
  def addXmlStringFunctions(self, dictName, typeCode):

    if typeCode == 'Boolean':
      self.setDictEntry(dictName, self.toLiteral('toStr'), 'bool2str')
      self.setDictEntry(dictName, self.toLiteral('cnvrt'), 'str2bool')
      
    elif typeCode == 'String':
      self.setDictEntry(dictName, self.toLiteral('toStr'), 
                        self.toLiteral('text'))
      self.setDictEntry(dictName, self.toLiteral('cnvrt'), 
                        self.toLiteral('text'))
    else:
      self.setDictEntry(dictName, self.toLiteral('toStr'),
                        'basicDataTypes.%s.toString' % typeCode)
      self.setDictEntry(dictName, self.toLiteral('cnvrt'),
                        'basicDataTypes.%s.fromString' % typeCode)

  ###########################################################################

  ###########################################################################
  
  # overrides XmlMapWrite
  def addXmlClassCreation(self, dictName, clazz, package=None):
    
    if package is not None:
      pp = clazz.container
      if pp in package.accessedPackages:
        self.write("import %s" 
         % self.getImportName(pp, subDirs=[metaConstants.apiCodeDir])
        )
    
    self.setDictEntry(dictName, self.toLiteral('class'), 
                      self.getImportName(clazz, 
                                         subDirs=[metaConstants.apiCodeDir]))

  ###########################################################################

  ###########################################################################
  
  # overrides XmlMapWrite
  def addDefaultValues(self, dictName, elemMap, elem):
    
    val = elemMap.get('default')
    if val is not None:
      self.setDictEntry(dictName, self.toLiteral('default'), repr(val))

  ###########################################################################

  ###########################################################################
  
  # overrides XmlMapWrite
  def initLeafPackage(self, package):
    """ write API header for package containing actual code
    """
    
    super(PyXmlMapWrite, self).initLeafPackage(package)
    
    self.write(
     "from ccpncore.memops.metamodel.Constants import baseDataTypeModule as basicDataTypes"
    )
    # import own API package
    self.writeComment("\n Current package api")
    self.write("import %s" 
               % self.getImportName(package, subDirs=[metaConstants.apiCodeDir]))

    if package is self.implPackage:
      
      self.writeNewline()
      self.writeComment('ApiError import')
      self.writeOne('from ccpncore.memops.ApiError import ApiError')
      self.writeNewline()

      # set up boolean converters
      self.write("""
def bool2str(value):
  return value and 'true' or 'false'

def str2bool(value):
  if value in ('True', 'true', '1'):
    return True
  elif value in ('False', 'false', '0'):
    return False
  else:
    raise ApiError("String '%s' is not legal for a Boolean" % value)
""")
      
      # define global functions
      self.write("""
_globalMapping = {}

def getGlobalMap(oldVersionStr=None):

  from ccpncore.memops.Version import currentModelVersion
  newVersionStr = str(currentModelVersion)
  
  if oldVersionStr is None:
    oldVersionStr = newVersionStr

  versionMapping = _globalMapping.get(oldVersionStr)
  if versionMapping is None:
    versionMapping = {}
    _globalMapping[oldVersionStr] = versionMapping
    
    makeMapping(versionMapping)
""")
      
      # load maps for all other known packages
      for pp in self.modelPortal.leafPackagesByImport()[1:]:
        ss = self.getImportName(pp, package)
        self.write("""
    import %s
    %s.makeMapping(versionMapping)
""" % (ss, ss))

      self.write("""  
    # adjust Io map for compatibility considerations
    if oldVersionStr != newVersionStr:
      from ccpncore.memops.format.compatibility.Converters1 import modifyIoMap
      # versions are different - compatibility needed
      modifyIoMap(oldVersionStr, versionMapping)
  #
  return versionMapping
""")
    
    # start makeMapping function
    ss = self.localVarNames['globalMap']
    self.startFunc('makeMapping', params=[ss],
     docString="generates XML I/O mapping for package %s, adding it to %s" % 
     (self.prefix, ss)
    )
    
    if package is not self.implPackage:
    
      self.write("""
from %s import bool2str, str2bool
""" % self.getImportName(self.implPackage, package))
      
    
  ###########################################################################

  ###########################################################################
  
  # overrides XmlMapWrite
  def writeFileHeader(self, package):
    
    self.writeMultilineComment(
     (self.getVersionString(metaobj=package) + 
     '\n' + 
     self.getCreditsString(metaobj=package, programType='XML-I/O-mapping')),
     compress=False
    )

  ###########################################################################

  ###########################################################################

  # overrides XmlMapWrite
  def endLeafPackage(self, package):
    
    self.endFunc()
  
    if package is self.implPackage:
      # saveToStream
      self.writeSaveToStream('CCPN Python XmlIO')

      # loadFromStream
      self.writeLoadFromStream('elementtree')

    super(PyXmlMapWrite, self).endLeafPackage(package)

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # overrides XmlMapWrite
  def writeSaveToStreamBody(self, originator, indentBySpaces = 2):

    self.write('''
import time
strapp = stream.write
indents = {0:''}

if mapping is None:
  mapping = getGlobalMap()[topObject.metaclass.container.shortName]

''')

    super(PyXmlMapWrite, self).writeSaveToStreamBody(originator, indentBySpaces=indentBySpaces)

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamWrite(self, s):

    self.write('strapp(%s)' % s)

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamWriteStartElement(self, element, closeElement = True, newLine = True, **attrs):

    keys = attrs.keys()
    strs = []
    strs2 = [element]
    
    for key in keys:
      # if key == '_ID':
      #   strs.append(' %s="_%%s"' % key)
      # else:
      strs.append(' %s="%%s"' % key)
      strs2.append(attrs[key])
        
    if closeElement:
      if newLine:
        strs.append('>\\n')
      else:
        strs.append('>')
    
    self.streamWrite("'%%s<%%s%s' %% (indent, %s)" 
                     % (''.join(strs), ', '.join(strs2)))

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamWriteEndElement(self, element, newLine = True, doIndent = False):

    if newLine:
      t = '\\n'
    else:
      t = ''
    
    if doIndent:
      s = "'%%s</%%s>%s' %% (indent, %s)" % (t, element)
    else:
      s = "'</%%s>%s' %% %s" % (t, element)

    self.streamWrite(s)

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamWriteAttr(self, key, value, haveUnderscore=False):

    if haveUnderscore:
      ss = '_'
    else:
      ss = ''

    self.streamWrite('\' %%s="%s%%s"\' %% (%s, %s)' % (ss, key, value))

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamWriteValue(self, value, haveUnderscore=False):

    if haveUnderscore:
      ss = '_'
    else:
      ss = ''

    self.streamWrite('\' %s%%s\' %% %s' % (ss, value))

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamWriteComment(self, comment):

    self.streamWrite("\"<!--%%s-->\\n\" %% %s.replace('--','\-\-')" % comment)

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamNonTextToString(self, value):

    self.writeComment('non-string simple type - toStr is conversion function')
    self.writeOne('%s = toStr(%s)' % (value, value))

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamIndent(self, increasing):

    if increasing:
      self.writeOne('nIndent += indentBySpaces')
      self.writeOne("indent = indents.setdefault(nIndent, nIndent*' ')")
    else:
      self.writeOne('nIndent -= indentBySpaces')
      self.writeOne('indent = indents[nIndent]')

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # implements XmlMapWrite
  def streamOrderedCollection(self, var):

    self.write('''
if tmpMap['type'] == 'child':
  items = list(%s.items())
  items.sort()
  ll = [x[1] for x in items]
else:
  ll = list(%s)
ll.reverse() # for reproducibility

stack.extend(ll)
mapStack.extend(tmpCont[x.__class__.__name__] for x in ll)
''' % (var, var))

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def writeLoadFromStreamStart(self):

    pass

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def writeLoadFromStreamMain(self):

    self.writeLoadFromStreamBody()

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def writeLoadFromStreamHandleError(self):

    self.write('''
if elem:
  tag = elem.tag
else:
  tag = 'None'

''')

    self.writeLoadFromStreamErrorBody()

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def writeLoadFromStreamEnd(self):

    self.writeLoadFromStreamExtraFunctions()

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # overrides XmlMapWrite
  def streamStartParse(self):

    super(PyXmlMapWrite, self).streamStartParse()

    # TBD: optimisations involving stack.append, stack.pop

    self.write('''
# needed for error handling
elem = None
''')

    # LOOP H
    self.write('''
# get elementtree NBNB TBD to be redone to allow for different sources
from xml.etree import ElementTree

# LOOP H
for event, elem in ElementTree.iterparse(stream, events=("start", "end")):

''')

    self.indent += self.INDENT

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # overrides XmlMapWrite
  def streamStartElement(self):

    # IF BLOCK 100
    self.writeComment('IF BLOCK 100')
    self.startIf(self.comparison('event', '==', self.toLiteral('start')))

    super(PyXmlMapWrite, self).streamStartElement()
    
  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # overrides XmlMapWrite
  def streamEndElement(self):

    # IF BLOCK 100
    self.elseIf()
    self.writeComment('IF BLOCK 100')

    super(PyXmlMapWrite, self).streamEndElement()

    # clean out to save memory#
    # self.writeComment('clean out to save memory')
    # self.startIf('clearElem')
    # self.writeOne('elem.clear()')
    # self.endIf()

    # IF BLOCK 100
    self.endIf()

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # overrides XmlMapWrite
  def streamEndParse(self):

    # LOOP H
    self.indent -= self.INDENT

    super(PyXmlMapWrite, self).streamEndParse()

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamDoCompatibility(self):

    self.writeOne('from ccpncore.memops.format.compatibility import Converters1')
    self.writeOne('Converters1.minorPostProcess(fileVersion, result, delayDataDict, objectDict, mapping)')

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  # def streamSetupCompatibility(self):
  #
  #   self.writeComment('Set up for compatibility - keeping XML parse tree')
  #   self.setVar('clearElem', self.getDictEntry('mapping', '"clearXmlElements"'))
  #   self.startIf('clearElem')
  #   self.setVar('topObjElem', 'elem')
  #   self.elseIf()
  #   self.setVar('topObjElem', None)
  #   self.endIf()


  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamElementTag(self, state='start'):

    return 'elem.tag'

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamElementText(self):

    return 'elem.text'

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamElementSplitText(self, var, cnvrt = None):

    if cnvrt:
      self.write('''
if cnvrt == 'text':
  %s = elem.text.split()
else:
  %s = [%s(x) for x in elem.text.split()]
''' % (var, var, cnvrt))

    else:
      self.writeOne('%s = elem.text.split()' % var)

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamElementAttr(self, key):

    return 'elem.get(%s)' % key

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamElementSetSkip(self, setToNone = False):

    if setToNone:
      elem = 'None'
    else:
      elem = 'elem'

    self.writeOne('skipElement = %s' % elem)
    # if setToNone:
    #   self.startIf('clearElem')
    #   self.writeOne('elem.clear()')
    #   self.endIf()

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamElementIsSkip(self, doReset=True):

    return self.comparison('elem', 'is', 'skipElement')

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamNextElement(self):

    self.writeOne('continue')

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamStartAttributeLoop(self, tag, value):

    self.startLoop('(%s, %s)' % (tag, value), 'elem.items()', isUnique=False, isOrdered=False)

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # LoadFromStream function
  # implements XmlMapWrite
  def streamGetValue(self, var, name, defaultValue = None,
                     keyIsMandatory = False, getChildAsDict = False):

    return self.getDictEntry('%s.__dict__' % var, name,
              defaultValue=defaultValue, keyIsMandatory=keyIsMandatory)

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamSetValue(self, var, name, value, useDirectSet=True):

    if useDirectSet:
      self.writeOne('%s.__dict__[%s] = %s' % (var, name, value))
    else:
      self.writeOne('setattr(%s, %s, %s)' % (var, name, value))

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamConvertStringToValue(self, cnvrt, value):

    return '%s(%s)' % (cnvrt, value)

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamOverrideOff(self, var):

    self.writeOne("del %s.__dict__['override']" % var)

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamFoundClosingTag(self):

    self.writeOne('break')

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamHaveEarlyExit(self):

    self.writeOne('break')

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamConvertExolink(self):

    self.write('''
for ii, vv in enumerate(val):
  oo = topObjByGuid.get(vv[0])
  clazz = vv[-1]['class']
  if (oo is None):
    # NB naughty - _packageName is a private attribute. 
    # But getPackageName is not static
    memopsRoot.refreshTopObjects(clazz._packageName)
    try:
      oo = topObjByGuid[vv[0]]
    except:
      raise ApiError("""TopObject with package:gui not found or loaded"""
       + ": %s:%s" % (curMap['content']['.qName'], vv[0])
      )
  value = clazz.getByKey(oo,vv[1:-1])
  if value is None:
    raise ApiError("No object found with package,class,key: %s" 
                   % ((curMap['content']['.qName'], clazz.__name__, vv[1:-1]),))
  else:
    val[ii] = value
''')



  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamCallConstructor(self, var, constructor, parent = None, castType = None, **attrlinks):

    ss = ['%s=%s' % (key, value) for (key, value) in attrlinks.items()]
    ss = ', '.join(ss)

    if parent:
      if ss:
        tt = ', '
      else:
        tt = ''
      self.writeOne('%s = %s(%s%s%s)' % (var, constructor, parent, tt, ss))
    else:
      self.writeOne('%s = %s(%s)' % (var, constructor, ss))

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  # implements XmlMapWrite
  def streamAddAll(self, collectionToBeAdded, collectionToBeAddedTo):

    self.writeOne('%s.extend(%s)' % (collectionToBeAddedTo, collectionToBeAdded))

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  def streamObjDictKey(self, obj, isMetaClass):

    if isMetaClass:
      return obj
    else:
      return 'id(%s)' % obj

  ###########################################################################

  ###########################################################################

  # LoadFromStream function
  def streamInitLoadingMaps(self):

    self.write('''
from ccpncore.memops.Version import currentModelVersion
newVersionStr = str(currentModelVersion)
from ccpncore.xml.memops.Implementation import getGlobalMap
 
globalMapping = getGlobalMap(fileVersion)

# handle compatibility considerations
if fileVersion == newVersionStr:
  needCompatibility = False
else:
  needCompatibility = True

''')

  ###########################################################################

  ###########################################################################

  # SaveToStream function
  # LoadFromStream function
  # implements XmlMapWrite
  def streamStartFunc(self, funcname, params=None, docString='',
                      returnString='', returnType=None, throwsApiError=True):

   if not params:
     params = ()

   pars = []
   for param in params:
     if len(param) == 4:
       ss = '=%s' % param[3]
     else:
       ss = ''
     par = '%s%s' % (param[0], ss)
     pars.append(par)
   self.startFunc(funcname, params=pars, docString=docString)

  ###########################################################################

  ###########################################################################

  # must be here because if in XmlMapWrite then not picked up
  # because of order of superclasses
  # overrides LanguageInterface
  def raiseApiError(self, errorMsg, obj = None, obj2 = None, obj3 = None):

    super(PyXmlMapWrite, self).raiseApiError(errorMsg, obj=obj, obj2=obj2, obj3=obj3, inOp=False)

