"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import collections
import operator
from typing import Tuple
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr

class ChemicalShift(AbstractWrapperObject):
  """Chemical Shift, containing a ChemicalShift value for the NmrAtom they belong to.

  Chemical shift values are continuously averaged over peaks assigned to the NmrAtom,
  unless this behaviour is turned off. If the NmrAtom is reassigned, the ChemcalShift
  is reassigned with it.

  ChemicalShift objects sort as the NmrAtom they belong to."""
  
  #: Short class name, for PID.
  shortClassName = 'CS'
  # Attribute it necessary as subclasses must use superclass className
  className = 'ChemicalShift'

  _parentClass = ChemicalShiftList

  #: Name of plural link to instances of class
  _pluralLinkName = 'chemicalShifts'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = Nmr.Shift._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiShift(self) -> Nmr.Shift:
    """ CCPN Chemical Shift matching ChemicalShift"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """identifier - assignment string"""
    # return ','.join(x or '' for x in self.nmrAtom.assignment)
    return self.nmrAtom._id

  @property
  def _localCcpnSortKey(self) -> Tuple:
    """Local sorting key, in context of parent."""

    return self.nmrAtom._ccpnSortKey[2:]
    
  @property
  def _parent(self) -> Project:
    """ChemicalShiftList containing ChemicalShift."""
    return self._project._data2Obj[self._wrappedData.parentList]
  
  chemicalShiftList = _parent
  
  @property
  def value(self) -> float:
    """shift value of ChemicalShift, in unit as defined in the ChemicalShiftList"""
    return self._wrappedData.value
    
  @value.setter
  def value(self, value:float):
    self._wrappedData.value = value

  @property
  def valueError(self) -> float:
    """shift valueError of ChemicalShift, in unit as defined in the ChemicalShiftList"""
    return self._wrappedData.error

  @valueError.setter
  def valueError(self, value:float):
    self._wrappedData.error = value

  @property
  def figureOfMerit(self) -> str:
    """Figure of Merit for ChemicalShift, between 0.0 and 1.0 inclusive."""
    return self._wrappedData.figOfMerit

  @figureOfMerit.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figOfMerit = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def nmrAtom(self) -> NmrAtom:
    """NmrAtom that the shift belongs to"""
    return self._project._data2Obj.get(self._wrappedData.resonance)
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: ChemicalShiftList)-> list:
    """get wrappedData (ApiShift) for all ChemicalShift children of parent ChemicalShiftList"""
    # NB this is NOT the right sorting order, but sorting on atomId is not possible at the API level
    return sorted(parent._wrappedData.measurements,
                  key=operator.attrgetter('resonance.serial'))

# Connections to parents:

def getter(self:NmrAtom) -> Tuple[ChemicalShift, ...]:
  getDataObj = self._project._data2Obj.get
  return tuple(sorted(getDataObj(x) for x in self._wrappedData.shifts))

NmrAtom.chemicalShifts = property(getter, None, None, "Chemical shifts belonging to NmrAtom")

del getter

def _newChemicalShift(self:ChemicalShiftList, value:float, nmrAtom:NmrAtom,
                     valueError:float=0.0, figureOfMerit:float=1.0,
                     comment:str=None) -> ChemicalShift:
  """Create new ChemicalShift within ChemicalShiftList."""

  nmrAtom = self.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
  defaults = collections.OrderedDict((('valueError', 0.0), ('figureOfMerit', 1.0),
                                      ('comment',None)))
  self._startFunctionCommandBlock('newChemicalShift', value, nmrAtom, values=locals(),
                                  defaults=defaults, parName='newChemicalShift')
  try:
    obj = self._wrappedData.newShift(value=value,
                                     resonance=nmrAtom._wrappedData, error=valueError,
                                     figOfMerit=figureOfMerit, details=comment)
  finally:
    self._project._appBase._endCommandBlock()
  return self._project._data2Obj.get(obj)

ChemicalShiftList.newChemicalShift = _newChemicalShift
del _newChemicalShift

# Notifiers:
# rename chemicalShifts when atom is renamed
NmrAtom._setupCoreNotifier('rename', AbstractWrapperObject._finaliseRelatedObjectFromRename,
                          {'pathToObject':'chemicalShifts', 'action':'rename'})
# NB The link to NmrAtom is immutable - does need a link notifier