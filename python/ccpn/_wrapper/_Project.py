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

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpncore.api.ccp.nmr.Nmr import NmrProject as ApiNmrProject
from ccpncore.memops import Notifiers
from ccpncore.lib.molecule import DataConvertLib
from ccpncore.util import Common as commonUtil
from ccpncore.util import pid as Pid
from ccpncore.util import Io as utilIo


class Project(AbstractWrapperObject):
  """Project (root) object. Corresponds to API: NmrProject"""
  
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
  def __init__(self, wrappedData: ApiNmrProject):
    """ Special init for root (Project) object
    """

    if not isinstance(wrappedData, ApiNmrProject):
      raise ValueError("Project initialised with %s, should be ccp.nmr.Nmr.NmrProject."
                       % wrappedData)
    
    # set up attributes
    self._project = self
    self._wrappedData = wrappedData
    self._id = _id = ''
    self._activeNotifiers = []
    
    # setup object handling dictionaries
    self._data2Obj = {wrappedData:self}
    self._pid2Obj = {}
    
    self._pid2Obj[self.__class__.__name__] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[_id] = self

    # Set up pid sorting dictionary to cache pid sort keys
    self._pidSortKeys = {}
    
    # general residue name to ChemCompIDs tuple Map.
    self._residueName2chemCompIds = DataConvertLib.getStdResNameMap(
      wrappedData.root.sortedChemComps()
    )

    # Set necessary values in apiProject
    if wrappedData.molSystem is None:
      wrappedData.root.newMolSystem(name=wrappedData.name, code=wrappedData.name,
                                    nmrProjects = (wrappedData,))

    self._logger = wrappedData.root._logger

    self._registerApiNotifiers()

    # set appBase attribute - for gui applications
    if hasattr(wrappedData, '_appBase'):
      self._appBase = wrappedData._appBase
    else:
      self._appBase = None
    
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
    """Cleans up the wrapper project, without deleting the API project (impossible)"""
    self.clearNotifiers()
    for tag in ('_wrappedData','_data2Obj','_pid2Obj'):
      delattr(self,tag)


  # CCPN properties  
  @property
  def _key(self) -> str:
    """Project id: Globally unique identifier (guid)"""
    return self._wrappedData.guid.translate(Pid.remapSeparators)
    
  @property
  def _parent(self) -> AbstractWrapperObject:
    """Parent (containing) object."""
    return None
  
  @property
  def name(self) -> str:
    """name of Project"""
    return self._wrappedData.name

  @property
  def path(self) -> str:
    """path of/to Project"""
    return utilIo.getRepositoryPath(self._wrappedData.memopsRoot, 'userData')
  
  @property
  def nmrProject(self) -> ApiNmrProject:
    """API equivalent to object: Nmrproject"""
    return self._wrappedData

  #
  # utility functions
  #

  def _pidSortKey(self, key) -> tuple:
    """ sort key that splits pids, and sorts numerical fields numerically (e.g. '11a' before '2b').
     A string without PREFIXSEP is treated as a pid with empty header, so that simple strings
     sort numerically as well

     If 'key' is a non-string sequence,
     directly contained strings are converted to their _pidSortKeys"""
    PREFIXSEP = Pid.PREFIXSEP
    IDSEP = Pid.IDSEP

    result = self._pidSortKeys.get(key)

    if result is None:

      if isinstance(key, str):
        ll = key.split(PREFIXSEP,1)
        if len(ll) == 1:
          ll = ['', key]
        result = ll[:1] + commonUtil.integerStringSortKey(key.split(IDSEP))

      else:
        # Treat as list of pids
        result = list(key)
        for ii,pid in enumerate(result):
          if isinstance(pid, str):
            ll = pid.split(PREFIXSEP,1)
            if len(ll) == 1:
              ll = ['', pid]
            result[ii] = ll[:1] + commonUtil.integerStringSortKey(pid.split(IDSEP))
    #
    self._pidSortKeys[key] = result
    return result

# NBNB set function parameter annotations for AbstractBaseClass functions
# MUST be done here to avoid circular import problems
AbstractWrapperObject.__init__.__annotations__['project'] = Project
AbstractWrapperObject.project.fget.__annotations__['return'] = Project
#AbstractWrapperObject.project.getter.__annotations__['return'] = Project

