"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpncore.util.typing import Sequence
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpncore.api.ccp.nmr.NmrConstraint import NmrConstraintStore as ApiNmrConstraintStore
from ccpncore.api.ccp.nmr.NmrConstraint import FixedResonance as ApiFixedResonance
from ccpncore.lib.spectrum.Util import DEFAULT_ISOTOPE_DICT


class RestraintSet(AbstractWrapperObject):
  """Restraint set."""
  
  #: Short class name, for PID.
  shortClassName = 'RS'
  # Attribute it necessary as subclasses must use superclass className
  className = 'RestraintSet'

  #: Name of plural link to instances of class
  _pluralLinkName = 'restraintSets'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiRestraintSet(self) -> ApiNmrConstraintStore:
    """ CCPN NmrConstraintStore matching RestraintSet"""
    return self._wrappedData

    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for RestraintSet"""
    return self._wrappedData.serial

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.sortedNmrConstraintStores()

  def _fetchFixedResonance(self, assignment:Sequence) -> ApiFixedResonance:
    """Fetch FixedResonance matching assignment tuple, creating anew if needed."""

    apiNmrConstraintStor = self._wrappedData

    tt = assignment
    if len(tt) != 4:
      raise ValueError("assignment %s must have four fields" % tt)

    dd = {
      'chainCode':tt[0],
      'sequenceCode':tt[1],
      'residueType':tt[2],
      'name':tt[3]
    }
    result = apiNmrConstraintStor.findFirstFixedResonance(**dd)

    if result is None:
      dd['isotopeCode'] = DEFAULT_ISOTOPE_DICT.get(tt[3][0])
      result = apiNmrConstraintStor.newFixedResonance(**dd)
    #
    return result


def newRestraintSet(parent:Project, comment:str=None) -> RestraintSet:
  """Create new empty child NmrConstraintStores

  :param str comment: comment for new chain (optional)"""
  
  nmrProject = parent._wrappedData
  newApiNmrConstraintStore = nmrProject.root.newNmrConstraintStore(nmrProject=nmrProject,
                                                         details=comment)
  return parent._data2Obj.get(newApiNmrConstraintStore)

    
    
# Connections to parents:
Project._childClasses.append(RestraintSet)
Project.newRestraintSet = newRestraintSet

# Notifiers:
className = ApiNmrConstraintStore._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':RestraintSet}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
