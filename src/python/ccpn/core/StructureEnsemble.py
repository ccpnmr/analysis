"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-10 12:56:45 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.util import Undo
from ccpn.util.StructureData import EnsembleData
from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble


class StructureEnsemble(AbstractWrapperObject):
  """Ensemble of coordinate structures."""
  
  #: Short class name, for PID.
  shortClassName = 'SE'
  # Attribute is necessary as subclasses must use superclass className
  className = 'StructureEnsemble'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'structureEnsembles'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiStructureEnsemble._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiStructureEnsemble(self) -> ApiStructureEnsemble:
    """ CCPN api StructureEnsemble matching StructureEnsemble"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - ID number converted to string"""
    return str(self._wrappedData.ensembleId)

  @property
  def serial(self) -> int:
    """ID number of StructureEnsemble, used in Pid and to identify the StructureEnsemble. """
    return self._wrappedData.ensembleId

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def label(self) -> str:
    """title of Model -  a line of free-form text."""
    return self._wrappedData.name

  @label.setter
  def label(self, value):
    self._wrappedData.name = value

  @property
  def data(self) -> EnsembleData:
    """EnsembleData (Pandas DataFrame) with structure data.

    Note that modifying the data via setValues, 'data[column] = ' or 'data.column = '
    will be echoed and put on the undo stack.
    Changing the data by direct pandas access will not."""
    apiObj = self._wrappedData.findFirstParameter(name='data')
    if apiObj is None:
      return None
    else:
      return apiObj.value

  @data.setter
  def data(self, value:EnsembleData):
    wrappedData = self._wrappedData
    if isinstance(value, EnsembleData):
      apiObj = wrappedData.findFirstParameter(name='data')
      if apiObj is None:
        wrappedData.newParameter(name='data', value=value)
      else:
        apiObj.value = value
    else:
      raise TypeError("Value is not of type EnsembleData")
    #
    value._containingObject = self

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  def resetModels(self):
    """Remove models without data, add models to reflect modelNumbers present"""
    data = self.data
    if data.shape[0]:
      # data present
      modelNumbers = set(x for x in data['modelNumber'] if x is not None)
      serial2Model = collections.OrderedDict((x.serial, x) for x in self.models)

      # remove models without data
      for serial, model in serial2Model.items():
        if serial not in modelNumbers:
          model.delete()

      # Add model for model-less data
      for modelNumber in modelNumbers:
        if modelNumber not in serial2Model:
          self.newModel(serial=modelNumber)


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.molSystem.sortedStructureEnsembles()

def _newStructureEnsemble(self:Project, serial:int=None, label:str=None, data:EnsembleData=None,
                          comment:str=None) -> StructureEnsemble:
  """Create new StructureEnsemble"""

  defaults = collections.OrderedDict((('serial', None), ('label', None), ('comment', None)))
  
  nmrProject = self._wrappedData
  self._startCommandEchoBlock('newStructureEnsemble', values=locals(), defaults=defaults,
                              parName='newStructureEnsemble')
  undo = self._undo
  undo.increaseBlocking()
  self.blankNotification()
  try:
    if serial is None:
      ll = nmrProject.root.structureEnsembles
      serial = max(x.ensembleId for x in ll) + 1 if ll else 1
    newApiStructureEnsemble = nmrProject.root.newStructureEnsemble(molSystem=nmrProject.molSystem,
                                                                   ensembleId=serial,
                                                                   details=comment)
    result = self._data2Obj[newApiStructureEnsemble]
    if data is None:
      result.data = EnsembleData()
    else:
      self._logger.warning(
        "EnsembleData successfully set on new StructureEnsemble were not echoed - too large")
      result.data = data
      data._containingObject = result
      for modelNumber in sorted(data['modelNumber'].unique()):
        result.newModel(serial=modelNumber, label='Model_%s' % modelNumber)
  finally:
    self._endCommandEchoBlock()
    self.unblankNotification()
    undo.decreaseBlocking()

  # Set up undo
  apiObjectsCreated = [newApiStructureEnsemble]
  apiObjectsCreated.extend(newApiStructureEnsemble.sortedModels())
  apiObjectsCreated.extend(newApiStructureEnsemble.parameters)
  undo.newItem(Undo._deleteAllApiObjects, nmrProject.root._unDelete,
               undoArgs=(apiObjectsCreated,),
               redoArgs=(apiObjectsCreated,  (nmrProject, nmrProject.root)))

  # Do creation notifications
  if serial is not None:
    result._finaliseAction('rename')
  result._finaliseAction('create')
  for model in result.models:
    model._finaliseAction('create')
  #
  return result
    
    
# Connections to parents:
Project.newStructureEnsemble = _newStructureEnsemble
del _newStructureEnsemble

# Notifiers:



