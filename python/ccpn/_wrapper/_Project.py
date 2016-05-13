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
import os
import typing
import operator
from collections import OrderedDict

from ccpn import AbstractWrapperObject
from ccpncore.api.ccp.nmr.Nmr import NmrProject as ApiNmrProject
from ccpncore.memops import Notifiers
from ccpncore.memops.ApiError import ApiError
from ccpncore.lib.molecule import MoleculeQuery
from ccpncore.lib.spectrum import NmrExpPrototype
from ccpncore.lib import Constants
from ccpn.util import Pid
from ccpn.util import Undo
from ccpn.util import Io as ioUtil

from ccpncore.lib.Io import Formats as ioFormats
from ccpncore.lib.Io import Fasta as fastaIo
from ccpncore.lib.Io import Pdb as pdbIo
from ccpncore.lib.spectrum.formats.Lookup import readXls,readCsv


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

  # All non-abstractWrapperClasses - filled in by
  _allLinkedWrapperClasses = []

  # List of CCPN api notifiers
  # Format is (wrapperFuncName, parameterDict, apiClassName, apiFuncName
  # The function self.wrapperFuncName(**parameterDict) will be registered
  # in the CCPN api notifier system
  # api notifiers are set automatically,
  # and are cleared by self._clearApiNotifiers and by self.delete()
  _apiNotifiers = []

  # Actions you can notify
  _notifierActions = ('create', 'delete', 'rename', 'change')
  
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
    
    # setup object handling dictionaries
    self._data2Obj = {wrappedData:self}
    self._pid2Obj = {}
    
    self._pid2Obj[self.className] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[_id] = self

    # Set up pid sorting dictionary to cache pid sort keys
    self._pidSortKeys = {}

    # Set up notification machinery

    # Old - to be removed eventually
    self._activeNotifiers = []

    # list or None. When set used to accumulate pending notifiers
    # Optional list. Elements are (func, onceOnly, wrapperObject, optional oldPid)
    self._pendingNotifications = []

    # Notification suspension level - to allow for nested notification suspension
    self._notificationSuspension = 0

    # Notification blanking level - to allow for nested notification disabling
    self._notificationBlanking = 0

    # {(className,action):OrderedDict(notifier:onceOnly)}
    self._context2Notifiers = {}


    #{(className,action):notifierId} dictionary
    # Actions are: ('rename', 'create', 'delete', 'change')
    # self._notifierContext2Id = OrderedDict()

    # {notifierId:(func, parameterDict, onceOnly)} dictionary
    # self._notifierId2funcdata = {}


    # Special attributes:
    self._implExperimentTypeMap = None

    # Set required objects in apiProject and ApiNmrProject
    #
    # NBNB TBD All this should probably be moved to either AppBase initiation or V2 upgrade
    # preferably the latter.

    # PeakLists and Spectrum contour colours
    for experiment in wrappedData.experiments:
      for dataSource in experiment.dataSources:

        if not dataSource.findFirstPeakList(dataType='Peak'):
          # Set a peakList for every spectrum
          dataSource.newPeakList()

        if not dataSource.positiveContourColour or not dataSource.negativeContourColour:
          # set contour colours for every spectrum
          (dataSource.positiveContourColour,
           dataSource.negativeContourColour) = dataSource.getDefaultColours()
        if not dataSource.sliceColour:
          dataSource.sliceColour = dataSource.positiveContourColour

    # MolSystem
    apiProject = wrappedData.root
    if wrappedData.molSystem is None:
      apiProject.newMolSystem(name=wrappedData.name, code=wrappedData.name,
                              nmrProjects = (wrappedData,))
    # SampleStore
    apiSampleStore = wrappedData.sampleStore
    if apiSampleStore is None:
      apiSampleStore = (apiProject.findFirstSampleStore(name='default') or
                        apiProject.newSampleStore(name='default'))
      wrappedData.sampleStore = apiSampleStore
    # RefSampleComponentStore
    apiComponentStore = apiSampleStore.refSampleComponentStore
    if apiComponentStore is None:
      apiComponentStore = (apiProject.findFirstRefSampleComponentStore(name='default') or
                           apiProject.newRefSampleComponentStore(name='default'))
      apiSampleStore.refSampleComponentStore = apiComponentStore
    # Make Substances that match finalised Molecules
    for apiMolecule in apiProject.sortedMolecules():
      if apiMolecule.isFinalised:
        # Create matchingMolComponent if none exists
        apiComponentStore.fetchMolComponent(apiMolecule)

    # Fix alpha or semi-broken projects. None of this should eb necessary, but hey!
    # NB written to modify nothing for valid projects

    # Get or (re)make default NmrChain
    defaultChain = wrappedData.findFirstNmrChain(code=Constants.defaultNmrChainCode)
    if defaultChain is None:
      # NO default chain - probably an alpha project or upgraded from V2
      defaultChain = wrappedData.findFirstNmrChain(code='@-')
      if defaultChain is None:
        defaultChain = wrappedData.newNmrChain(code=Constants.defaultNmrChainCode)
      else:
        defaultChain.code = '@-'
    # Make sure all non-offset ResonanceGroups have directNmrChain set.
    for rg in wrappedData.sortedResonanceGroups():
      if rg.mainGroupSerial == rg.serial:
        rg.mainGroupSerial = None
      if rg.mainGroupSerial is None and rg.directNmrChain is None:
        if hasattr(rg, 'chainSerial') and rg.chainSerial is not None:
          rg.directNmrChain = wrappedData.findFirstNmrChain(serial=rg.chainSerial)
        if rg.directNmrChain is None:
          rg.directNmrChain = defaultChain
    # End of API object fixing

    self._logger = wrappedData.root._logger

    self._registerApiNotifiers()

    for tt in self._coreNotifiers:
      self.registerNotifier(*tt)

    # set appBase attribute - for gui applications
    if hasattr(wrappedData.root, '_appBase'):
      appBase = wrappedData.root._appBase
      self._appBase = appBase
      appBase.project = self
    else:
      self._appBase = None

    self._initializeAll()

  def _close(self):
    """Clean up the wrapper project previous to deleting or replacing"""
    # Remove undo stack:
    self._logger.info("project._close()")

    self._resetUndo(maxWaypoints=0)

    ioUtil.cleanupProject(self)
    self._clearApiNotifiers()
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

  def save(self, newPath:str=None, newProjectName:str=None, changeBackup:bool=True,
                  createFallback:bool=False, overwriteExisting:bool=False,
                  checkValid:bool=False, changeDataLocations:bool=False):
    """Save project with all data, optionally to new location or with new name.
    Unlike lower-level functions, this function ensures that data in high level caches are also saved """
    self._flushCachedData()
    ioUtil.saveProject(self._wrappedData.root, newPath=newPath, newProjectName=newProjectName,
                       changeBackup=changeBackup, createFallback=createFallback,
                       overwriteExisting=overwriteExisting, checkValid=checkValid,
                       changeDataLocations=changeDataLocations)

  
  @property
  def name(self) -> str:
    """name of Project"""
    apiNmrProject = self._wrappedData
    if len(apiNmrProject.root.nmrProjects) == 1:
      return apiNmrProject.root.name
    else:
      return apiNmrProject.name

  @property
  def path(self) -> str:
    """path of/to Project"""
    return ioUtil.getRepositoryPath(self._wrappedData.memopsRoot, 'userData')

  @property
  def programName(self) -> str:
    """Name of running program - defaults to 'CcpNmr'"""
    appBase = self._appBase if hasattr(self, '_appBase') else None
    return 'CcpNmr' if appBase is None else appBase.applicationName

  def _flushCachedData(self, dummy=None):
    """Flush cached data to ensure up-to-date data are saved"""

    for structureEnsemble in self.structureEnsembles:
      structureEnsemble._flushCachedData()

  def rename(self, name:str) -> None:
    """Rename Project, and rename the underlying API project and the directory stored on disk.
    Name change is not undoable, but the undo stack is left untouched
    so that previous steps can still be undone"""

    apiNmrProject = self._apiNmrProject
    apiProject = apiNmrProject.root
    oldName = apiNmrProject.name

    if apiProject.findFirstNmrProject(name=name) not in (apiNmrProject, None):
      raise ValueError("Cannot rename to %s - name is in use for another NmrProject" % name)

    if name != oldName:
      # rename NmrProject

      # Load packages that (might) have hard links to the Nmr package,
      # to make sure the name change does not break them
      for apiNmrEntryStore in apiProject.nmrEntryStores:
        if not apiNmrEntryStore.isLoaded:
          apiNmrEntryStore.load()
      for apiNmrCalcStore in apiProject.nmrCalcStores:
        if not apiNmrCalcStore. isLoaded:
          apiNmrCalcStore.load()

      undo = apiProject._undo
      if undo is not None:
        undo.increaseBlocking()
      apiProject.override = True
      try:
        apiNmrProject.name = name
        parentDict = apiProject.__dict__['nmrProjects']
        del parentDict[oldName]
        parentDict[name] = apiNmrProject
        self._finaliseRename()

        # Do notifications - NB project has special behaviour, so it is done here
        if not self._notificationBlanking:
          className = self.className
          iterator = (self._context2Notifiers.setdefault((name, 'rename'), OrderedDict())
                     for name in (className, 'AbstractWrapperObject'))
          ll = self._pendingNotifications
          if self._notificationSuspension:
            for dd in iterator:
              for notifier, onceOnly in dd.items():
                ll.append((notifier, onceOnly, self, self.pid))
          else:
            for dd in iterator:
              for notifier in dd:
                notifier(self, self.pid)
      except:
        apiNmrProject.name = oldName
        parentDict[oldName] = apiNmrProject
        print("ERROR while renaming NmrProject. Project may be left in an invalid state")
        raise
      finally:
        apiProject.override = False
        if undo is not None:
          undo.decreaseBlocking()

    if name != apiProject.name:
      # rename and move CCPN project
      location = apiProject.findFirstRepository(name='userData').url.getDataLocation()
      dirName, oldName = os.path.split(location)
      self.save(newProjectName=name, newPath=os.path.join(dirName,name),
                overwriteExisting=True, checkValid=True, createFallback=True,
                changeDataLocations=True, changeBackup=True)


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
          dd2[refExperiment.synonym or name] = name

      self._implExperimentTypeMap = result
    #
    return result


  #
  #  Notifiers system
  #

  # Old, API-level functions:

  @staticmethod
  def _setupApiNotifier(func, apiClassOrName, apiFuncName, parameterDict=None):

    if parameterDict is None:
      parameterDict = {}

    apiClassName = (apiClassOrName if isinstance(apiClassOrName, str)
                    else apiClassOrName._metaclass.qualifiedName())

    dot = '_dot_'
    wrapperFuncName = '_%s%s%s' % (func.__module__.replace('.', dot), dot, func.__name__)

    setattr(Project, wrapperFuncName, func)
    Project._apiNotifiers.append((wrapperFuncName, parameterDict, apiClassName, apiFuncName))

  def _registerApiNotifiers(self):
    """Register notifiers"""

    for tt in self._apiNotifiers:
      wrapperFuncName, parameterDict, apiClassName, apiFuncName = tt
      notify = functools.partial(getattr(self,wrapperFuncName), **parameterDict)
      # self._registerNotify(notify, apiClassName, apiFuncName)
      self._activeNotifiers.append((notify, apiClassName, apiFuncName))
      Notifiers.registerNotify(notify, apiClassName, apiFuncName)

  def _clearApiNotifiers(self):
    """CLear all notifiers, previous to closing or deleting Project
    """
    while self._activeNotifiers:
      tt = self._activeNotifiers.pop()
      Notifiers.unregisterNotify(*tt)

  # def _registerNotify(self, notify, apiClassName, apiFuncName):
  #   """Register a single notifier"""
  #   self._activeNotifiers.append((notify, apiClassName, apiFuncName))
  #   Notifiers.registerNotify(notify, apiClassName, apiFuncName)

  # def _unregisterNotify(self, notify, apiClassName, apiFuncName):
  #   """Unregister a single notifier"""
  #   self._activeNotifiers.remove((notify, apiClassName, apiFuncName))
  #   Notifiers.unregisterNotify(notify, apiClassName, apiFuncName)

  # New notifier system



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

    param: Callable func: The function to call when the notifier is triggered.

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
      tt = tuple(sorted([className, target]))

    od = self._context2Notifiers.setdefault(tt, OrderedDict())
    if parameterDict:
      notifier = functools.partial(func, **parameterDict)
    else:
      notifier = func
    od[notifier] = onceOnly
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
    self._notificationSuspension += 1

  def resumeNotification(self):
    """Execute accumulated notifiers and resume immediate notifier execution"""
    self._notificationSuspension -= 1
    if self._notificationSuspension <= 0:
      scheduledNotifiers = set()
      executeNotifications = []
      ll = self._pendingNotifications
      while ll:
        notification = ll.pop()
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


  # Functions notified

  def _newApiObject(self, wrappedData, cls:AbstractWrapperObject):
    """Create new wrapper object of class cls, associated with wrappedData.
    and call creation notifiers"""

    if hasattr(cls, '_factoryFunction'):
      # Necessary for classes where you need to instantiate a subclass instead

      result = self._data2Obj.get(wrappedData)
      # There are cases where _newApiObject is registered twice,
      # when two wrapper classes share teh same API class
      # (Peak,Integral; PeakList, IntegralList)
      # In those cases only the notifiers are done the second time
      if result is None:
        result = cls._factoryFunction(self, wrappedData)
    else:
      result = cls(self, wrappedData)
    #
    result._finaliseAction('create')


  def _modifiedApiObject(self, wrappedData):
    """ call object-has-changed notifiers
    """
    obj = self._data2Obj[wrappedData]
    obj._finaliseAction('change')

  # def _preDelete(self, wrappedData):
  #   """ call pre-deletion notifiers
  #   """
  #   # get object
  #   obj = self._data2Obj.get(wrappedData)
  #   obj._executeNotifiers('preDelete')

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
    if self._notificationSuspension:
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

  #
  #
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