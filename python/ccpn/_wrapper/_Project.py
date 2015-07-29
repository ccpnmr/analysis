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

import functools

from ccpn import AbstractWrapperObject
from ccpncore.api.ccp.nmr.Nmr import NmrProject as ApiNmrProject
from ccpncore.memops import Notifiers
from ccpncore.lib.molecule import MoleculeQuery
from ccpncore.util import Common as commonUtil
from ccpncore.util import Pid
from ccpncore.util.Undo import Undo
from ccpncore.util import Io as ioUtil

class Project(AbstractWrapperObject):
  """Project (root) object. Corresponds to API: NmrProject"""
  
  #: Short class name, for PID.
  shortClassName = 'PR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Project'

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
    
    self._pid2Obj[self.className] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[_id] = self

    # Set up pid sorting dictionary to cache pid sort keys
    self._pidSortKeys = {}

    # Set necessary values in apiProject
    if wrappedData.molSystem is None:
      wrappedData.root.newMolSystem(name=wrappedData.name, code=wrappedData.name,
                                    nmrProjects = (wrappedData,))

    self._logger = wrappedData.root._logger

    self._registerApiNotifiers()

    # set appBase attribute - for gui applications
    if hasattr(wrappedData.root, '_appBase'):
      self._appBase = wrappedData.root._appBase
    else:
      self._appBase = None

    self._initializeAll()

  @staticmethod
  def _setupNotifier(func, apiClassOrName, apiFuncName, parameterDict=None):

    if parameterDict is None:
      parameterDict = {}

    apiClassName = (apiClassOrName if isinstance(apiClassOrName, str)
                    else apiClassOrName._metaclass.qualifiedName())

    dot = '_dot_'
    wrapperFuncName = '%s%s%s' % (func.__module__.replace('.', dot), dot, func.__name__)

    setattr(Project, wrapperFuncName, func)
    Project._apiNotifiers.append((wrapperFuncName, parameterDict, apiClassName, apiFuncName))

  def _registerApiNotifiers(self):
    """Register or remove notifiers"""

    for tt in self._apiNotifiers:
      wrapperFuncName, parameterDict, apiClassName, apiFuncName = tt
      notify = functools.partial(getattr(self,wrapperFuncName), **parameterDict)
      self._registerNotify(notify, apiClassName, apiFuncName)

  def _clearNotifiers(self):
    """CLear all notifiers, previous to closing or deleting Project
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
    del self._pid2Obj[obj.shortClassName][obj._id]

  def _resetPid(self, wrappedData):
    """Reset internal attributes after values determining PID have changed"""

    getDataObj = self._data2Obj.get
    pid2Obj = self._pid2Obj

    objects = [getDataObj(wrappedData)]
    for obj in objects:
      # Add child objects to list
      objects.extend(getDataObj(y) for x in obj._childClasses for y in x._getAllWrappedData(obj))

      # print ('@~@~ to reset: ', obj,
      #        obj._wrappedData.serial if hasattr(obj._wrappedData, 'serial') else None)

      # reset _id
      oldId = obj._id

      parent = obj._parent
      if parent is self:
        _id = str(obj._key)
      else:
        _id = '%s%s%s'% (parent._id, Pid.IDSEP, obj._key)
      obj._id = _id

      # if oldId == 'A.2.Lys':
      #   print ('@~@~', oldId, _id, parent, obj.__class__.__name__)

      # update pid:object mapping dictionary
      dd = pid2Obj[obj.className]
      # print('@~@~', obj, sorted(x for x in dd))
      del dd[oldId]
      dd[_id] = obj

  def delete(self):
    """Delete underlying data and cleans up the wrapper project"""
    wrappedData = self._wrappedData
    self._close()
    wrappedData.delete()

  def _close(self):
    """Clean up the wrapper project previous to deleting or replacing"""
    # Remove undo stack:
    self._resetUndo(maxWaypoints=0)

    ioUtil.cleanupProject(self)
    self._clearNotifiers()
    for tag in ('_data2Obj','_pid2Obj'):
      delattr(self,tag)
    del self._wrappedData

  def __repr__(self):
    """String representation"""
    return "<ccpn.Project:name=%s>" % self.name


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
    return ioUtil.getRepositoryPath(self._wrappedData.memopsRoot, 'userData')
  
  @property
  def nmrProject(self) -> ApiNmrProject:
    """API equivalent to object: Nmrproject"""
    return self._wrappedData

  # Undo machinery
  @property
  def _undo(self):
    """undo stack for Project. Implementation attribute"""
    return self._wrappedData.root._undo

  def _resetUndo(self, maxWaypoints=20, maxOperations=10000):
    """Reset undo stack, using passed-in parameters.
    NB setting either parameter to 0 removes the undo stack."""

    undo = self._wrappedData.root._undo
    if undo is not None:
      undo.clear()

    if maxWaypoints and maxOperations:
      self._wrappedData.root._undo = Undo(maxWaypoints=maxWaypoints, maxOperations=maxOperations)
    else:
      self._wrappedData.root._undo = None

  def newUndoPoint(self):
    """Set a point in the undo stack, you can undo/redo to """
    undo = self._wrappedData.root._undo
    if undo is None:
      self._logger.warning("Trying to add undoPoint bu undo not initialised")
    else:
      undo.newWaypoint()
      self._logger.info("Added undoPoint")


  @property
  def  _residueName2chemCompId(self) -> dict:
    """dict of {residueName:(molType,ccpCode)}"""
    return MoleculeQuery.fetchStdResNameMap(self._wrappedData.root)

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
        result = ll[:1] + commonUtil.integerStringSortKey(ll[1].split(IDSEP))

      else:
        # Treat as list of pids
        result = list(key)
        for ii,pid in enumerate(result):
          if isinstance(pid, str):
            ll = pid.split(PREFIXSEP,1)
            if len(ll) == 1:
              ll = ['', pid]
            result[ii] = ll[:1] + commonUtil.integerStringSortKey(ll[1].split(IDSEP))
    #
    self._pidSortKeys[key] = result
    return result
      
