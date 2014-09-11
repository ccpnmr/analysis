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
""" Python-specific version of ModelAdapt
"""

from ccpncore.memops.scripts.core.ModelAdapt import ModelAdapt
from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel import Constants as metaConstants

import copy


class PyModelAdapt(ModelAdapt):
  """ Python-specific version of ModelAdapt
  """
  def __init__(self):
    """Class constructor.
    Automatically processes model.
    """
    
    # model flavour (must be done first) 
    self.addModelFlavour('language','python')
    
    # superclass init call
    super(PyModelAdapt, self).__init__()
    
    # adapt variableName data. 
    # NB this variable is used in handcode
    self.varNames['other'] = 'value'
  
    # MetaModelElement corresponding to class
    self.varNames['metaclass'] = '_metaclass'
 
    self.varNames['packageName'] = '_packageName'
 
    self.varNames['fieldNames'] = '_fieldNames'
 
    self.varNames['packageShortName'] = '_packageShortName'

    # new variable - used for dataDict optimisation
    # NB this variable is used in handcode
    self.varNames['dataDict'] = 'dataDict'
    
    # adapt opData
    operationData = self.operationData
    
    # new, init
    operationData['init']['name'] = '__init__'
            
  ###########################################################################

  ###########################################################################
  ###
  ### functions overriding ModelAdapt
  ###
  ###########################################################################

  ###########################################################################
    
  def initComplexDataType(self, complexDataType):
    """ processing actions for class
    """
    
    # super function call
    ModelAdapt.initComplexDataType(self, complexDataType)
    
    # add metaclass attribute
    if complexDataType.qualifiedName() == self.rootClassName:
      self.addMetaClassAttr(complexDataType)    
  
  initClass = initComplexDataType     
  
  initDataObjType = initComplexDataType    
    
  ###########################################################################

  ###########################################################################
  
  def addMetaClassAttr(self, clazz):
    
    # add metaclass implementation attribute
    dd = {
     'name':'metaclass',
     'baseName':'metaclass',
     'documentation':'metaclass: MetaModel object containing class description',
     'isImplementation':True,
     'changeability':metaConstants.frozen,
     'locard':1,
     'hicard':1,
     'container':clazz,
     'valueType':clazz.metaObjFromQualName('memops.Implementation.Any'),
    }
    self.newElement(MetaModel.MetaAttribute, **dd)
    
  ###########################################################################

  ###########################################################################

  def addDataObjTypeOperations(self, inClass):
    """ Add operations not linked to an element (e.g. init, delete, checkValid)
    """
    
    ModelAdapt.addDataObjTypeOperations(self, inClass)
    
    if inClass.isAbstract and not inClass.supertypes:
      # constructor (will be abstact and will raise an exception)
      self.makeOperations(inClass, 'init', inClass)
      
    
  ###########################################################################

  ###########################################################################

  def addClassOperations(self, inClass):
    """ Add operations not linked to an element (e.g. init, delete, checkValid)
    """
    
    ModelAdapt.addClassOperations(self, inClass)
    
    if inClass.isAbstract and not inClass.supertypes:
      # constructor (will be abstact and will raise an exception)
      self.makeOperations(inClass, 'init', inClass)
    
    if inClass.qualifiedName() == self.baseClassName:
      # special case
      
      # getByNavigation
      params = {
      'opType':'otherQuery',
      'isQuery':True,
      'name':'getByNavigation',
      'isImplicit':True,
      'documentation':"""Return object or element given a navigation sequence, or None if none found
    
Intended to provide fast, one-function-call access to
long range navigation, mainly for UML-embedded code.
NB there is no error checking on the input. 
The function may fail without proper warning for incorrect input.
Also the function bypasses the API on get commands, so that load is
not triggered on MemopsRoot->TopObject links or partially filled
interpackage crosslinks
Programmer beware!

Navigation starts at self and follows the navigation sequence,
which consists of either string tags, or (tag,key) tuples.
- For a string tag the function gets the corresponding element.
Except at the end of the navigation sequence, this assumes that 
the element has hicard==1, and is a link or complex data type attribute.
If the result evaluates false, a getattr is done instead.
This may trigger loading and follow derived links.
- For a (tag,key) tuple this assumes that the tag is the name of a 
child link, and gets the child with the given key.
If no children are found and the object has an attribute isLoaded==False, 
object.load() is tried.
- If at any stage in the lookup no object is found, None is returned
    """,
      'codeStubs':{'python':"""
isa = isinstance

result = self

for xx in navigation:
  dd = result.__dict__
  if isa(xx,str):
    # xx is a role name - get the link
    result = dd.get(xx) or getattr(result,xx)
  
  else:
    # xx must be a (childlink,key) tuple. 
    tag,key = xx
    dd2 = dd[tag]
    if not dd2 and dd.get('isLoaded') == False:
      # we might need to load this
      try:
        result.load()
      except AttributeError:
        pass
    # Now get the child
    result = dd2.get(key)
  
  if result is None:
    break
else:

  # freeze internal representations
  if isa(result, list):
    result = tuple(result)
  elif isa(result, set):
    result = frozenset(result)
  elif isa(result, dict):
    result = frozenset(result.values())"""}
      } 
      op = self.newElement(MetaModel.MetaOperation, container=inClass, **params)
      
      op.target = op
      
      anyType = inClass.metaObjFromQualName('memops.Implementation.Any')
      params = {'name':'result', 'direction':metaConstants.return_direction,
                'isImplicit':True, 'valueType':anyType}
      self.newElement(MetaModel.MetaParameter, container=op, **params)
      
      params = {'name':'navigation', 'direction':metaConstants.in_direction,
                'isImplicit':True, 'valueType':anyType,
                'locard':0, 'hicard':metaConstants.infinity,
                'taggedValues':{'isSubdivided':'True'},}
      self.newElement(MetaModel.MetaParameter, container=op, **params)
    
  ###########################################################################

  # ###########################################################################
  #
  # def getOpData(self, target, opType, inClass=None):
  #   """ Get opData for opType, taking special cases into account
  #
  #   NB should probably be removed. Try it.
  #   """
  #
  #   return ModelAdapt.getOpData(self, target, opType, inClass)
  #
  #   if (opType == 'init' and isinstance(target, MetaModel.MetaClass)
  #       and not target.isAbstract and target.parentRole is None):
  #     # Project init - must have optional parent to avoid
  #     # validity problems if the number of parameters change
  #     result = copy.deepcopy(self.operationData[opType])
  #     result['opType'] = opType
  #     result['target'] = target
  #     for subData in result['subOps'].values():
  #       subData['parameters'][0]['defaultValue'] = None
  #
  #   else:
  #     result = ModelAdapt.getOpData(self, target, opType, inClass)
  #
  #   #
  #   return result
  #
  ###########################################################################

  ###########################################################################
    
  def getOpDocumentation(self, opData, inClass, opSubType=None, 
                         copyElemDoc=False):
    """ get documentation for generated operation
    copyElemDoc defaults to False in Python
    we have the element documentation on the properties
    """
    return ModelAdapt.getOpDocumentation(self, opData, inClass, opSubType, 
                                         copyElemDoc)
    
  ###########################################################################

  ###########################################################################
  ###
  ### internal code
  ###
  ###########################################################################
