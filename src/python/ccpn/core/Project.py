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

import functools
import os
import typing
import operator
from collections import OrderedDict

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.util import Undo
from ccpn.util import Logging

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrProject as ApiNmrProject
from ccpnmodel.ccpncore.memops import Notifiers
from ccpnmodel.ccpncore.memops.ApiError import ApiError
from ccpnmodel.ccpncore.lib.molecule import MoleculeQuery
from ccpnmodel.ccpncore.lib.spectrum import NmrExpPrototype
from ccpnmodel.ccpncore.lib import Constants
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.lib.Io import Fasta as fastaIo
from ccpnmodel.ccpncore.lib.Io import Pdb as pdbIo
from ccpnmodel.ccpncore.lib.spectrum.formats.Lookup import readXls,readCsv


class Project(AbstractWrapperObject):
  """ The Project is the object that contains all data objects and serves as the hub for
  navigating between them.

  There are eleven top-level data objects directly within a project, of which seven have child
  objects of their own, namely Spectrum, Sample, Chain, NmrChain, ChemicalShiftList, DataSet
  and StructureEnsemble. The child data objects are organised in a logical hierarchy; for example,
  a Spectrum has PeakLists, which in turn, are made up of Peaks, whereas a Chain is made up of
  -Residues, which are made up of Atoms. """
  
  #: Short class name, for PID.
  shortClassName = 'PR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Project'

  #: Name of plural link to instances of class
  _pluralLinkName = 'projects'
  
  #: List of child classes.
  _childClasses = []

  # All non-abstractWrapperClasses - filled in by
  _allLinkedWrapperClasses = []

  # Utility map - class shortName and longName to class.
  _className2Class = {}

  # List of CCPN pre-registered api notifiers
  # Format is (wrapperFuncName, parameterDict, apiClassName, apiFuncName
  # The function self.wrapperFuncName(**parameterDict) will be registered
  # in the CCPN api notifier system
  # api notifiers are set automatically,
  # and are cleared by self._clearAllApiNotifiers and by self.delete()
  # RESTRICTED. Direct access in core classes ONLY
  _apiNotifiers = []

  # Actions you can notify
  _notifierActions = ('create', 'delete', 'rename', 'change')

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiNmrProject._metaclass.qualifiedName()
  
  # Top level mapping dictionaries:
  # pid to object and ccpnData to object
  #__slots__ = ['_pid2Obj', '_data2Obj']

  # Implementation methods
  def __init__(self, wrappedData: ApiNmrProject):
    """ Special init for root (Project) object

    NB Project is NOT complete before the _initProject function is run.
    """

    if not isinstance(wrappedData, ApiNmrProject):
      raise ValueError("Project initialised with %s, should be ccp.nmr.Nmr.NmrProject."
                       % wrappedData)
    
    # set up attributes
    self._project = self
    self._wrappedData = wrappedData
    self._id = _id = ''
    
    # setup object handling dictionaries
    self._data2Obj = {wrappedData:self}
    self._pid2Obj = {}
    
    self._pid2Obj[self.className] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[_id] = self

    # Set up pid sorting dictionary to cache pid sort keys
    self._pidSortKeys = {}

    # Set up notification machinery

    # Active notifiers - saved for later cleanup. CORER APPLICAATION ONLY
    self._activeNotifiers = []

    # list or None. When set used to accumulate pending notifiers
    # Optional list. Elements are (func, onceOnly, wrapperObject, optional oldPid)
    self._pendingNotifications = []

    # Notification suspension level - to allow for nested notification suspension
    self._notificationSuspension = 0

    # Notification blanking level - to allow for nested notification disabling
    self._notificationBlanking = 0

    # Wrapper level notifier tracking.  APPLICATION ONLY
    # {(className,action):OrderedDict(notifier:onceOnly)}
    self._context2Notifiers = {}

    # Special attributes:
    self._implExperimentTypeMap = None

    # Set for Pre-May-2016 version. NBNB TODO remove when no longer needed
    self._appBase = None


  def _initialiseProject(self):
    """Complete initialisation of project,

    set up logger and notifiers, and wrap underlying data"""

    # The logger has already been set up when creating/loading the API project
    # so just get it
    self._logger = Logging.getLogger()

    # Set up notifiers
    self._registerPresetApiNotifiers()

    for tt in self._coreNotifiers:
      self.registerNotifier(*tt)

    # initialise, creating the wrapped objects
    self._initializeAll()

  def _close(self):
    """Clean up the wrapper project previous to deleting or replacing

    Cleanup includes wrapped data graphics objects (e.g. Window, Strip, ...)"""
    # Remove undo stack:
    self._logger.info("project._close()")

    self._resetUndo(maxWaypoints=0)

    apiIo.cleanupProject(self)
    self._clearAllApiNotifiers()
    for tag in ('_data2Obj','_pid2Obj'):
      getattr(self,tag).clear()
      # delattr(self,tag)
    # del self._wrappedData
    self.__dict__.clear()

  # This is all we want to happen
  delete = _close

  def __repr__(self):
    """String representation"""
    if self.isDeleted:
      return "<ccpn.Project:isDeleted=True>"
    else:
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

  def save(self, newPath:str=None, changeBackup:bool=True,
                  createFallback:bool=False, overwriteExisting:bool=False,
                  checkValid:bool=False, changeDataLocations:bool=False) -> bool:
    """Save project with all data, optionally to new location or with new name.
    Unlike lower-level functions, this function ensures that data in high level caches are saved.
    Return True if save succeeded otherwise return False (or throw error)"""
    self._flushCachedData()
    return apiIo.saveProject(self._wrappedData.root, newPath=newPath,
                             changeBackup=changeBackup, createFallback=createFallback,
                             overwriteExisting=overwriteExisting, checkValid=checkValid,
                             changeDataLocations=changeDataLocations)

  
  @property
  def name(self) -> str:
    """name of Project"""
    return self._wrappedData.root.name
    # apiNmrProject = self._wrappedData
    # if len(apiNmrProject.root.nmrProjects) == 1:
    #   return apiNmrProject.root.name
    # else:
    #   return apiNmrProject.name

  @property
  def path(self) -> str:
    """path to directory containing Project"""
    return apiIo.getRepositoryPath(self._wrappedData.root, 'userData')

  @property
  def programName(self) -> str:
    """Name of running program - defaults to 'CcpNmr'"""
    appBase = self._appBase if hasattr(self, '_appBase') else None
    return 'CcpNmr' if appBase is None else appBase.applicationName

  def _flushCachedData(self, dummy=None):
    """Flush cached data to ensure up-to-date data are saved"""

    for structureEnsemble in self.structureEnsembles:
      structureEnsemble._flushCachedData()

  # def rename(self, name:str) -> None:
  #   """Rename Project, and rename the underlying API project and the directory stored on disk.
  #   Name change is not undoable, but the undo stack is left untouched
  #   so that previous steps can still be undone"""
  #
  #   oldPath = self.path
  #
  #   apiNmrProject = self._apiNmrProject
  #   apiProject = apiNmrProject.root
  #   oldName = apiNmrProject.name
  #
  #   if apiProject.findFirstNmrProject(name=name) not in (apiNmrProject, None):
  #     raise ValueError("Cannot rename to %s - name is in use for another NmrProject" % name)
  #
  #   if name != oldName:
  #     # rename NmrProject
  #
  #     # Load packages that (might) have hard links to the Nmr package,
  #     # to make sure the name change does not break them
  #     for apiNmrEntryStore in apiProject.nmrEntryStores:
  #       if not apiNmrEntryStore.isLoaded:
  #         apiNmrEntryStore.load()
  #     for apiNmrCalcStore in apiProject.nmrCalcStores:
  #       if not apiNmrCalcStore. isLoaded:
  #         apiNmrCalcStore.load()
  #
  #     self._startFunctionCommandBlock('rename', name)
  #     undo = apiProject._undo
  #     if undo is not None:
  #       undo.increaseBlocking()
  #     apiProject.override = True
  #     try:
  #       apiNmrProject.name = name
  #       parentDict = apiProject.__dict__['nmrProjects']
  #       del parentDict[oldName]
  #       parentDict[name] = apiNmrProject
  #       self._finaliseRename()
  #
  #       # Do notifications - NB project has special behaviour, so it is done here
  #       if not self._notificationBlanking:
  #         className = self.className
  #         iterator = (self._context2Notifiers.setdefault((name, 'rename'), OrderedDict())
  #                    for name in (className, 'AbstractWrapperObject'))
  #         ll = self._pendingNotifications
  #         if self._notificationSuspension:
  #           for dd in iterator:
  #             for notifier, onceOnly in dd.items():
  #               ll.append((notifier, onceOnly, self, self.pid))
  #         else:
  #           for dd in iterator:
  #             for notifier in dd:
  #               notifier(self, self.pid)
  #     except:
  #       apiNmrProject.name = oldName
  #       parentDict[oldName] = apiNmrProject
  #       print("ERROR while renaming NmrProject. Project may be left in an invalid state")
  #       raise
  #     finally:
  #       apiProject.override = False
  #       if undo is not None:
  #         undo.decreaseBlocking()
  #       self._appBase._endCommandBlock()
  #
  #   if name != apiProject.name:
  #     # rename and move CCPN project
  #     dirName, oldName = os.path.split(oldPath)
  #     self.save(newProjectName=name, newPath=os.path.join(dirName,name),
  #               overwriteExisting=True, checkValid=True, createFallback=True,
  #               changeDataLocations=True, changeBackup=True)


  def deleteObjects(self, *objects:typing.Sequence[typing.Union[Pid.Pid, AbstractWrapperObject]]):
    """Delete one or more objects, given as either objects or Pids"""

    getByPid = self.getByPid

    objs = [getByPid(x) if isinstance(x, str) else x for x in objects]
    apiObjs = [x._wrappedData for x in objs]
    self._startDeleteCommandBlock(*apiObjs)
    try:
      for obj in objs:
        if obj and not obj.isDeleted:
          # If statement in case deleting one obj triggers the deletion of another
          obj.delete()
    finally:
      self._endDeleteCommandBlock(*apiObjs)

  def renameObject(self, objectOrPid:typing.Union[str,AbstractWrapperObject], newName:str):
    """Rename object indicated by objectOrPid to name newName
    NB at last one class (Substance) has a two-art name - these are passed as one,
    dot-separated string (e.g. 'Lysozyme.U13C'"""
    obj = self._data2Obj.get(objectOrPid) if isinstance(objectOrPid, str) else objectOrPid
    names = newName.split('.')
    obj.rename(*names)

  def execute(self, pid, funcName, *params, **kwparams):
    """Get the object identified by pid, execute object.funcName(*params, **kwparams)
    and return the result"""

    # NBNB TODO - probably not useful - remove?

    obj = self.getByPid(pid)
    if obj is None:
      raise ValueError("No objet found with pid %s" % pid)
    else:
      func = getattr(obj, funcName)
      if func is None:
        raise ValueError("Object *s has no method named %s" % funcName)
      else:
        return func(*params, **kwparams)

  @property
  def _apiNmrProject(self) -> ApiNmrProject:
    """API equivalent to object: NmrProject"""
    return self._wrappedData

  # Undo machinery
  @property
  def _undo(self):
    """undo stack for Project. Implementation attribute"""
    return self._wrappedData.root._undo

  def _resetUndo(self, maxWaypoints:int=20, maxOperations:int=10000,
                 debug:bool=False):
    """Reset undo stack, using passed-in parameters.
    NB setting either parameter to 0 removes the undo stack."""
    Undo.resetUndo(self._wrappedData.root, maxWaypoints=maxWaypoints,
                   maxOperations=maxOperations, debug=debug)

  def newUndoPoint(self):
    """Set a point in the undo stack, you can undo/redo to """
    undo = self._wrappedData.root._undo
    if undo is None:
      self._logger.warning("Trying to add undoPoint but undo is not initialised")
    else:
      undo.newWaypoint()
      self._logger.info("Added undoPoint")


  # Should be removed:
  @property
  def  _residueName2chemCompId(self) -> dict:
    """dict of {residueName:(molType,ccpCode)}"""
    return MoleculeQuery.fetchStdResNameMap(self._wrappedData.root)

  @property
  def _experimentTypeMap(self) -> OrderedDict:
    """{dimensionCount : {sortedNucleusCodeTuple :
                          OrderedDict(experimentTypeSynonym : experimentTypeName)}}
    dictionary

    NB The OrderedDicts are ordered ad-hoc, with the most common experiments (hopefully) first
    """

    # NB This is a hack, in order to rename experiments that we care particularly about
    # This should disappear under refactoring
    from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

    result = self._implExperimentTypeMap
    if result is None:
      result = OrderedDict()
      refExperimentMap = NmrExpPrototype.fetchIsotopeRefExperimentMap(self._apiNmrProject.root)

      for nucleusCodes, refExperiments in refExperimentMap.items():

        ndim = len(nucleusCodes)
        dd1 = result.get(ndim, {})
        result[ndim] = dd1

        dd2 = dd1.get(nucleusCodes, OrderedDict())
        dd1[nucleusCodes] = dd2
        for refExperiment in refExperiments:
          name = refExperiment.name
          key = refExperiment.synonym or name
          key = priorityNameRemapping.get(key, key)
          dd2[key] = name

      self._implExperimentTypeMap = result
    #
    return result


  #
  #  Notifiers system
  #

  # Old, API-level functions:

  @classmethod
  def _setupApiNotifier(cls, func, apiClassOrName, apiFuncName, parameterDict=None):
    """Setting up API notifiers for subsequent registration on each new project
       RESTRICTED. Use in core classes ONLY"""
    tt = cls._apiNotifierParameters(func, apiClassOrName, apiFuncName,
                                parameterDict=parameterDict)
    cls._apiNotifiers.append(tt)

  @classmethod
  def _apiNotifierParameters(cls, func, apiClassOrName, apiFuncName, parameterDict=None):
    """Define func as method of project and return API parameters for notifier setup
    APPLICATION ONLY"""
    if parameterDict is None:
      parameterDict = {}

    apiClassName = (apiClassOrName if isinstance(apiClassOrName, str)
                    else apiClassOrName._metaclass.qualifiedName())

    dot = '_dot_'
    wrapperFuncName = '_%s%s%s' % (func.__module__.replace('.', dot), dot, func.__name__)
    setattr(Project, wrapperFuncName, func)

    return (wrapperFuncName, parameterDict, apiClassName, apiFuncName)

  def _registerApiNotifier(self, func, apiClassOrName, apiFuncName, parameterDict=None):
    """Register notifier for immediate action on current project (only)
    ADVANCED, but free to use. Must be unregistered when any object referenced is deleted.
    Use return value as input parameter for _unregisterApiNotifier (if desired)"""
    tt = self.__class__._apiNotifierParameters(func, apiClassOrName, apiFuncName,
                                               parameterDict=parameterDict)
    return self._activateApiNotifier(*tt)

  def _unregisterApiNotifier(self, notifierTuple):
    """Remove acxtive notifier from project. ADVANVED but free to use.
    Use return value of _registerApiNotifier to identify the relevant notiifier"""
    self._activeNotifiers.remove(notifierTuple)
    Notifiers.unregisterNotify(*notifierTuple)


  def _registerPresetApiNotifiers(self):
    """Register preset API notifiers. APPLCATION ONLY"""

    for tt in self._apiNotifiers:
      self._activateApiNotifier(*tt)

  def _activateApiNotifier(self, wrapperFuncName, parameterDict, apiClassName, apiFuncName):
    """Activate API notifier. APPLICATION ONLY"""

    notify = functools.partial(getattr(self,wrapperFuncName), **parameterDict)
    notifierTuple = (notify, apiClassName, apiFuncName)
    self._activeNotifiers.append(notifierTuple)
    Notifiers.registerNotify(*notifierTuple)
    #
    return notifierTuple



  def _clearAllApiNotifiers(self):
    """CLear all notifiers, previous to closing or deleting Project
    APPLICATION ONLY
    """
    while self._activeNotifiers:
      tt = self._activeNotifiers.pop()
      Notifiers.unregisterNotify(*tt)


  # New notifier system (Free for use in application code):

  def registerNotifier(self, className:str, target:str, func:typing.Callable,
                       parameterDict:dict={}, onceOnly:bool=False) -> typing.Callable:
    """
    Register notifiers to be triggered when data change

    :param str className: className of wrapper class to monitor (AbstractWrapperObject for 'all')

    :param str target: can have the following values

      *'create'* is called after the creation (or undeletion) of the object and its wrapper.
      Notifier functions are called with the created wrapper object as the only parameter.

      *'delete'* is called after the object is deleted, but before the .id and .pid attributes
      are modified. Notifier functions are called with the deleted wrapper object as the only
      parameter.

      *'rename'* is called after the id and pid of an object has changed
      Notifier functions are called with the renamed wrapper object and the old pid as parameters.

      *'change'* when any object attribute changes value.
      Notifier functions are called with the created wrapper object as the only parameter.
      rename and crosslink notifiers (see below) may also trigger change notifiers.

      Any other value is interpreted as the name of a wrapper class, and the notifier
      is triggered when a cross link (NOT a parent-child link) between the className and
      the target class is modified

    :param Callable func: The function to call when the notifier is triggered.

      for actions 'create', 'delete' and 'change' the function is called with the object
      created (deleted, undeleted, changed) as the only parameter

      For action 'rename' the function is called with an additional parameter: oldPid,
      the value of the pid before renaming.

      If target is a second className, the function is called with the project as the only
      parameter.

    param: dict parameterDict: Parameters passed to the notifier function before execution.

      This allows you to use the same function with different parameters in different contexts

    param: bool onceOnly: If True, only one of multiple copies is executed

      when notifiers are resumed after a suspension.

    return: The registered notifier (which can be passed to removeNotifier or duplicateNotifier)

    """

    if target in self._notifierActions:
      tt = (className, target)
    else:
      # This is right, it just looks strange. But if target is not an action it is
      # another className, and if so the names must be sorted.
      tt = tuple(sorted([className, target]))

    od = self._context2Notifiers.setdefault(tt, OrderedDict())
    if parameterDict:
      notifier = functools.partial(func, **parameterDict)
    else:
      notifier = func
    if od.get(notifier) is None:
      od[notifier] = onceOnly
    else:
      raise TypeError("Coding error - notifier %s set twice for %s,%s "
                      % (notifier, className, target))
    #
    return notifier

  def duplicateNotifier(self,  className:str, target:str,
                        notifier:typing.Callable):
    """register copy of notifier for a new className and target.
    Intended for onceOnly=True notifiers. It is up to the user to make sure the calling
     interface matches the action"""
    if target in self._notifierActions:
      tt = (className, target)
    else:
      # This is right, it just looks strange. But if target is not an action it is
      # another className, and if so the names must be sorted.
      tt = tuple(sorted([className, target]))

    for od in self._context2Notifiers.values():
      onceOnly = od.get(notifier)
      if onceOnly is not None:
        self._context2Notifiers.setdefault(tt, OrderedDict())[notifier] = onceOnly
        break
    else:
      raise ValueError("Unknown notifier: %s" % notifier)


  def unRegisterNotifier(self,  className:str, target:str, notifier:typing.Callable):
    """Unregister the notifier from this className, and target"""
    if target in self._notifierActions:
      tt = (className, target)
    else:
      # This is right, it just looks strange. But if target is not an action it is
      # another className, and if so the names must be sorted.
      tt = tuple(sorted([className, target]))
    od = self._context2Notifiers.get((tt), {})
    try:
      del od[notifier]
    except KeyError:
      self._logger.warning("Attempt to unregister unknown notifier %s for %s" % (notifier, (className, action)))


  def removeNotifier(self, notifier:typing.Callable):
    """Unregister the the notifier from all places where it appears."""
    found = False
    for od in self._context2Notifiers.values():
      if notifier in od:
        del od[notifier]
        found = True
    if not found:
      self._logger.warning("Attempt to remove unknown notifier: %s" % notifier)

  def blankNotification(self):
    """Disable notifiers temporarily
    e.g. to disable 'object modified' notifiers during object creation

    Caller is responsible to make sure necessary notifiers are called, and to unblank after use"""
    self._notificationBlanking += 1

  def unblankNotification(self):
    """Resume notifier execution after blanking"""
    self._notificationBlanking -= 1

  def suspendNotification(self):
    """Suspend notifier execution and accumulate notifiers for later execution"""
    return
    # TODO suspension temporarily disabled
    self._notificationSuspension += 1

  def resumeNotification(self):
    """Execute accumulated notifiers and resume immediate notifier execution"""
    return
    # TODO suspension temporarily disabled
    self._notificationSuspension -= 1
    if self._notificationSuspension <= 0:
      scheduledNotifiers = set()
      executeNotifications = []
      pendingNotifications = self._pendingNotifications
      while pendingNotifications:
        notification = pendingNotifications.pop()
        notifier = notification[0]
        onceOnly = notification[1]
        if onceOnly:
          if notifier not in scheduledNotifiers:
            scheduledNotifiers.add(notifier)
            executeNotifications.append((notifier, notification[2:]))
        else:
          executeNotifications.append((notifier, notification[2:]))
      #
      for notifier, params in reversed(executeNotifications):
        notifier(*params)


  # Standard notified functions.
  # RESTRICTED. Use in core classes ONLY

  def _startDeleteCommandBlock(self, *allWrappedData):
    """Call startCommandBlock for wrapper object delete. Implementation only"""

    undo = self._undo
    if not self._appBase._echoBlocking and not undo.blocking:

      # set undo step
      undo.newWaypoint()
      getDataObj =  self._data2Obj.get
      ll = [getDataObj(x) for x in allWrappedData]
      ss = ', '.join(repr(x.pid) for x in ll if x is not None)
      if not ss:
        raise ValueError("No object for deletion recognised among API objects: %s"
                         % allWrappedData)
      command = "project.deleteObjects(%s)" % ss
      # echo command strings
      self._appBase.ui.echoCommands((command,))

    self._appBase._echoBlocking += 1


  def _endDeleteCommandBlock(self, *dummyWrappedData):
    """End block for delete command echoing

    MUST be paired with _startDeleteCommandBlock call - use try ... finally to ensure both are called"""
    if self._appBase._echoBlocking > 0:
      # If statement should always be True, but to avoid weird behaviour in error situations we check
      self._appBase._echoBlocking -= 1

  def _newApiObject(self, wrappedData, cls:AbstractWrapperObject):
    """Create new wrapper object of class cls, associated with wrappedData.
    and call creation notifiers"""

    factoryFunction = cls._factoryFunction
    if factoryFunction is None:
      result = cls(self, wrappedData)
    else:
      # Necessary for classes where you need to instantiate a subclass instead

      result = self._data2Obj.get(wrappedData)
      # There are cases where _newApiObject is registered twice,
      # when two wrapper classes share the same API class
      # (Peak,Integral; PeakList, IntegralList)
      # In those cases only the notifiers are done the second time
      if result is None:
        result = factoryFunction(self, wrappedData)
    #
    result._finaliseAction('create')


  def _modifiedApiObject(self, wrappedData):
    """ call object-has-changed notifiers
    """
    obj = self._data2Obj[wrappedData]
    obj._finaliseAction('change')

  def _finaliseApiDelete(self, wrappedData):
    """Clean up after object deletion - and call deletion notifiers
    Notifiers are called AFTER wrappedData are deleted, but BEFORE  wrapper objects are modified
    """
    if not wrappedData.isDeleted:
      raise ValueError("_finaliseApiDelete called before wrapped data are deleted: %s" % wrappedData)

    # get object
    obj = self._data2Obj.get(wrappedData)
    pid = obj.pid

    obj._finaliseAction('delete')

    # remove from wrapped2Obj
    del self._data2Obj[wrappedData]

    # remove from pid2Obj
    del self._pid2Obj[obj.shortClassName][obj._id]

    # Mark object as obviously deleted, and set up for undeletion
    obj._id += '-Deleted'
    wrappedData._oldWrapperObject = obj
    obj._wrappedData = None

  def _finaliseApiUnDelete(self, wrappedData):
    """restore undeleted wrapper object, and call creation notifiers,
    same as _newObject"""

    if wrappedData.isDeleted:
      raise ValueError("_finaliseApiUnDelete called before wrapped data are deleted: %s" % wrappedData)

    try:
      oldWrapperObject = wrappedData._oldWrapperObject
    except AttributeError:
      raise ApiError("Wrapper object to undelete wrongly set up - lacks _oldWrapperObject attribute")

    # put back in from wrapped2Obj
    self._data2Obj[wrappedData] = oldWrapperObject

    if oldWrapperObject._id.endswith('-Deleted'):
      oldWrapperObject._id = oldWrapperObject._id[:-8]

    # put back in pid2Obj
    self._pid2Obj[oldWrapperObject.shortClassName][oldWrapperObject._id] = oldWrapperObject

    # Restore object to pre-undeletion state
    del wrappedData._oldWrapperObject
    oldWrapperObject._wrappedData = wrappedData

    oldWrapperObject._finaliseAction('create')


  def _notifyRelatedApiObject(self, wrappedData, pathToObject:str, action:str):
    """ call 'action' type notifiers for getattribute(pathToObject)(wrappedData)
    pathToObject is a navigation path (may contain dots) and must yield an API object
    or an iterable of API objects"""

    getDataObj = self._data2Obj.get

    target = operator.attrgetter(pathToObject)(wrappedData)

    self._project._logger.debug('_notifyRelatedApiObject: %s: %s.%s = %s'
                                % (action, wrappedData, pathToObject, target))

    if not target:
      pass
    elif hasattr(target, '_metaclass'):
      # Hack. This is an API object
      getDataObj(target)._finaliseAction(action)
    else:
      # This must be an iterable
      for obj in target:
        getDataObj(obj)._finaliseAction(action)

  def _finaliseApiRename(self, wrappedData):
    """Reset Finalise rename - called from APi object (for API notifiers)
    """

    obj = self._data2Obj.get(wrappedData)
    obj._finaliseAction('rename')

  def _modifiedLink(self, dummy, classNames:typing.Tuple[str,str]):
    """ call link-has-changed notifiers
    The notifier function called must have the signature
    func(project, **parameterDict)

    NB
    1) calls to this function must be set up explicitly in the wrapper for each crosslink
    2) This function is only called when the link is changed explicitly, not when
    a linked object is created or deleted"""

    if self._notificationBlanking:
      return

    # get object
    className, target = tuple(sorted(classNames))
    # self._doNotification(classNames[0], classNames[1], self)
    iterator = (self._context2Notifiers.setdefault((name, target), OrderedDict())
               for name in (className, 'AbstractWrapperObject'))
    # TODO suspension temporarily disabled
    if False and self._notificationSuspension:
      ll = self._pendingNotifications
      for dd in iterator:
        for notifier, onceOnly in dd.items():
          ll.append((notifier, onceOnly, self))
    else:
      for dd in iterator:
        for notifier in dd:
          notifier(self)

  # Library functions

  def loadData(self, path:str) -> (list,None):
    """Load data from path, determining type first."""

    dataType, subType, usePath = ioFormats.analyseUrl(path)

    # urlInfo is list of triplets of (type, subType, modifiedUrl),

    # e.g. ('Spectrum', 'Bruker', newUrl)
    if dataType is None:
      print("Skipping: file data type not recognised for %s" % usePath)

    elif dataType == 'Dirs':
      # special case - usePath is a list of paths from a top dir with enumerate subDirs and paths.
      paths = usePath
      for path in paths:
        self.loadData(path)

    elif not os.path.exists(usePath):
      print("Skipping: no file found at %s" % usePath)
    elif dataType == 'Text':
      # Special case - you return the text instead of a list of Pids
      return open(usePath).read()
    else:

      funcname = '_load' + dataType
      if funcname == '_loadProject':
        return [self.loadProject(usePath, subType)]

      elif funcname == '_loadSpectrum':
        # NBNB TBD FIXME check if loadSpectrum should start with underscore
        # (NB referred to elsewhere
        return self.loadSpectrum(usePath, subType)

      elif hasattr(self, funcname):
        pids = getattr(self, funcname)(usePath, subType)
        return pids
      else:
        print("Skipping: project has no function %s" % funcname)

    return None

  # Data loaders and dispatchers
  def _loadSequence(self, path:str, subType:str) -> list:
    """Load sequence(s) from file into Wrapper project"""

    if subType == ioFormats.FASTA:
      sequences = fastaIo.parseFastaFile(path)
    else:
      raise ValueError("Sequence file type %s is not recognised" % subType)

    chains = []
    for sequence in sequences:
      chains.append(self.createSimpleChain(sequence=sequence[1], compoundName=sequence[0],
                                            molType='protein'))
    #
    return chains

  def _loadStructure(self, path:str, subType:str) -> list:
    """Load Structure ensemble(s) from file into Wrapper project"""

    if subType == ioFormats.PDB:
      apiEnsemble = pdbIo.loadStructureEnsemble(self._apiNmrProject.molSystem, path)
    else:
      raise ValueError("Structure file type %s is not recognised" % subType)
    #
    return [self._data2Obj[apiEnsemble]]

  def loadProject(self, path:str, subType:str) -> "Project":
    """Load project from file into application and return the new project"""

    if subType == ioFormats.CCPN:
      return self._appBase.loadProject(path)
    else:
      raise ValueError("Project file type %s is not recognised" % subType)

  def loadSpectrum(self, path:str, subType:str) -> list:
    """Load spectrum from file into application"""

    # NBNB TBD FIXME check for rename

    apiDataSource = self._wrappedData.loadDataSource(path, subType)
    if apiDataSource is None:
      return []
    else:
      spectrum = self._data2Obj[apiDataSource]
      spectrum.resetAssignmentTolerances()
      return [spectrum]

  def _loadLookupFile(self, path:str, subType:str, ):
    """Load data from a look-up file, csv or xls ."""

    if subType == ioFormats.CSV:
      readCsv(self, path=path)

    elif subType == ioFormats.XLS:
      readXls(self, path=path)


  def _uniqueSubstanceName(self, name:str=None, defaultName:str= 'Molecule') -> str:
    """add integer suffixed to name till it is unique"""

    apiComponentStore = self._wrappedData.sampleStore.refSampleComponentStore
    apiProject =apiComponentStore.root

    # ensure substance name is unique
    if name:
      i = 0
      result = name
      formstring = name + '_%d'
    else:
      formstring = defaultName + '_%d'
      i = 1
      result =  formstring % (name,i)
    while (apiProject.findFirstMolecule(name=result) or
           apiComponentStore.findFirstComponent(name=result)):
      i += 1
      result = '%s_%d' % (name,i)
    if result != name and name != defaultName:
      self._logger.warning(
      "CCPN molecule named %s already exists. New molecule has been named %s" %
      (name,result))
    #
    return result