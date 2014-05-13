from ccpncore.util import Path

from ccpncore.memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError

from ccpncore.memops.scripts.docgen.ApiDocGen import ApiDocGen


def writeApiDoc(modelPortal, rootFileName=None, rootDirName=None,
             releaseVersion=None, **kw):
  """write Python API documentation
  
  Only function that should be called directly by 'make' scripts etc.
  """
  
  pyApiDocGen = PyApiDocGen(modelPortal=modelPortal, rootFileName=rootFileName, 
                        rootDirName=rootDirName, releaseVersion=releaseVersion,
                        scriptName='PyApiDocGen', **kw)
  pyApiDocGen.processModel()


class PyApiDocGen(ApiDocGen):

  apiName = 'Python API'
  baseDirName = 'python/ccpn/doc'

  ###########################################################################

  ###########################################################################

  def __init__(self, **kw):
  
    for (tag, val) in kw.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)
    
    self.addModelFlavour('language', 'python')

    super(PyApiDocGen, self).__init__()

  ###########################################################################

  ###########################################################################

  # implements ApiDocGen
  def getClassPageMethods(self, complexDataType, methods):

    ll = [('Attribute', self.getClassAttrMethods(complexDataType, methods)),
          ('Class', self.getClassClassMethods(complexDataType, methods)),
          ('Other', self.getClassOtherMethods(complexDataType, methods))]
    if isinstance(complexDataType, MetaModel.MetaClass):
      ll[1:1] = [('Link Attribute', self.getClassLinkAttrMethods(complexDataType, methods))]
      ll[3:3] = [('Factory', self.getClassNewMethods(complexDataType, methods))]

    return ll

  ###########################################################################

  ###########################################################################

  # implements ApiDocGen
  def getParamString(self, parameter):

    paramString = self.getElemTypeString(parameter)
    cardString = self.getParamCardString(parameter)
    if cardString:
      paramString = '%s %s' % (paramString, cardString)

    return paramString

  ###########################################################################

  ###########################################################################

  # internal function
  def getParamCardString(self, parameter):

    if parameter.hicard != 1:
      if parameter.isOrdered:
        # note: below only works if parameter.container is MetaOperation, not MetaException
        method = parameter.container
        if method.opType == 'get':
          cardString = 'Tuple'
        else:
          cardString = 'List'
      else:
        cardString = 'Set'
    else:
      cardString = ''

    return cardString

  ###########################################################################

  ###########################################################################

  # implements ApiDocGen
  def getKeywordValueString(self, method):

    return 'keyword=value pairs'

  ###########################################################################

  ###########################################################################

  # implements ApiDocGen
  def getNewParamString(self, method):

    container = method.container
    target = method.target
    mandatoryElements, hasOptionals = self.getMandatoryElements(target)
    ll = []
    for elem in mandatoryElements:
      attr = target.getElement(elem)
      # attr.container is either target or superclass of target
      (name, ref) = self.getLinkInfo(container, attr.container)
      ss = '%s.%s' % (elem, self.fileSuffix)
      ref = Path.joinPath(ref, ss)
      ll.append('%s' % self.getLinkString(ref, elem))
    if hasOptionals:
      ll.append('...')
    if ll:
      paramsString = ', '.join(ll)
    else:
      paramsString = '-'

    return paramsString

  ###########################################################################

  ###########################################################################

  # implements ApiDocGen
  def writeConstructorRows(self, complexDataType, mandatoryElements):

    if mandatoryElements:
      paramString = '=value, '.join(mandatoryElements+['']) + ' ... '
    else:
      paramString = ' ... '

    if isinstance(complexDataType, MetaModel.MetaClass) and complexDataType.parentRole:
      paramString = " %s,%s" % (complexDataType.parentRole.name, paramString)

    self.writeStartRow(valign='top')
    self.writeCell('Constructor:')
    self.writeCell('newObj = %s(%s)' % (complexDataType.name, paramString))
    self.writeEndRow()

  ###########################################################################

  ###########################################################################

  # overrides ApiDocGen
  def getMethodReturn(self, method):

    returnString = super(PyApiDocGen, self).getMethodReturn(method)

    if returnString == '':
      returnString = '-'

    return returnString

