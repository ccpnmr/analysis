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

import functools

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpncore.api.ccp.nmr.Nmr import NmrProject as Ccpn_NmrProject
from ccpncore.memops import Notifiers
from ccpncore.lib import DataConvertLib


class Project(AbstractWrapperClass):
  """Project (root) object. Corresponds to CCPN: NmrProject"""
  
  #: Short class name, for PID.
  shortClassName = 'PR'

  #: Name of plural link to instances of class
  _pluralLinkName = 'projects'
  
  #: List of child classes.
  _childClasses = []

  # List of CCPN api notifiers
  # Format is (wrapperFuncName, parameterDict, apiClassName, apiFuncName
  # The function self.wrapperFuncName(**parameterDict) will be registered
  # in the CCPN api notifier system
  # api notifiers are set automatically,
  # and are cleared by self._clearNotifiers and by self.delete()
  _apiNotifiers = []
  
  # Top level mapping dictionaries:
  # pid to object and ccpnData to object
  #__slots__ = ['_pid2Obj', '_data2Obj']
  
  
  # Implementation methods
  def __init__(self, wrappedData: Ccpn_NmrProject):
    """ Special init for root (Project) object
    """
    
    # set up attributes
    self._project = self
    self._wrappedData = wrappedData
    self._pid = pid = ''
    self._activeNotifiers = []
    
    # setup object handling dictionaries
    self._data2Obj = {wrappedData:self}
    self._pid2Obj = {}
    
    self._pid2Obj[self.__class__.__name__] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[pid] = self
    
    # general residue name to ChemCompIDs tuple Map.
    self._residueName2chemCompIds = DataConvertLib.getStdResNameMap(
      wrappedData.root.sortedChemComps()
    )

    self._logger = wrappedData.root._logger

    self._registerApiNotifiers()
    
    self._initializeAll()
  
  def _registerApiNotifiers(self):
    """Register or remove notifiers"""

    for tt in self._apiNotifiers:
      wrapperFuncName, parameterDict, apiClassName, apiFuncName = tt
      notify = functools.partial(getattr(self,wrapperFuncName), **parameterDict)
      self._registerNotify(notify, apiClassName, apiFuncName)

  def _clearNotifiers(self):
    """CLear all notifiers, previous to closing or deleting POroject
    """
    while self._activeNotifiers:
      tt = self._activeNotifiers.pop()
      Notifiers.unregisterNotify(*tt)

  def _registerNotify(self, notify, apiClassName, apiFuncName):
    """Register a single notifier"""
    self._activeNotifiers.append((notify, apiClassName, apiFuncName))
    Notifiers.registerNotify(notify, apiClassName, apiFuncName)

  def _unregisterNotify(self, notify, apiClassName, apiFuncName):
    """Unregister a single notifier"""
    self._activeNotifiers.remove((notify, apiClassName, apiFuncName))
    Notifiers.unregisterNotify(notify, apiClassName, apiFuncName)


  def _newObject(self, wrappedData, cls):
    """Create new wrapper object of class cls, associated with wrappedData.
    For use in creation notifiers"""
    return cls(self, wrappedData)

  def _finaliseDelete(self, wrappedData) -> None:
    """Clean up after object deletion - to be called from notifiers
    wrapperObject to delete is identified from wrappedData"""

    if not wrappedData.isDeleted:
      raise ValueError("_finaliseDelete called before wrapped data are deleted: %s" % wrappedData)

    # remove from wrapped2Obj
    obj = self._data2Obj.pop(wrappedData)

    # remove from pid2Obj
    del self._pid2Obj[obj.shortClassName][obj._pid]

  def delete(self):
    """Cleans up the wrapper project, without deleting the CCPN project (impossible)"""
    self.clearNotifiers()
    for tag in ('_wrappedData','_data2Obj','_pid2Obj'):
      delattr(self,tag)


  # CCPN properties  
  @property
  def id(self) -> str:
    """Project id: Globally unique identifier (guid)"""
    return self._wrappedData.guid
    
  @property
  def _parent(self) -> AbstractWrapperClass:
    """Parent (containing) object."""
    return None
  
  @property
  def name(self) -> str:
    """name of Project"""
    return self._wrappedData.name
  
  @property
  def nmrProject(self) -> Ccpn_NmrProject:
    """CCPN equivalent to object: Nmrproject"""
    return self._wrappedData

  #
  # utility functions
  #

# NBNB set function parameter annotations for AbstractBaseClass functions
# MUST be done here to avoid circular import problems
AbstractWrapperClass.__init__.__annotations__['project'] = Project
AbstractWrapperClass.project.fget.__annotations__['return'] = Project
#AbstractWrapperClass.project.getter.__annotations__['return'] = Project



def _getAtomResonance(atom:object) -> object:
  """get or create resonance corresponding to Atom
  NBNB TBD Must add Resonance if not currently there. NOT YET DONE
  NBNB duplicate. consolidate and move to right place"""
  return atom.ccpnResonance
