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

from ccpn import AbstractWrapperObject
from ccpncore.api.ccp.nmr.Nmr import NmrProject as ApiNmrProject
from ccpncore.memops import Notifiers
from ccpncore.memops.ApiError import ApiError
from ccpncore.lib.molecule import MoleculeQuery
from ccpncore.lib.spectrum import NmrExpPrototype
from ccpncore.lib import Constants
from ccpncore.util import Pid
from ccpncore.util import Undo
from ccpncore.util import Io as ioUtil
from ccpncore.util.Types import Dict

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
  # and are cleared by self._clearApiNotifiers and by self.delete()
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
    self._old_id = None
    self._activeNotifiers = []
    
    # setup object handling dictionaries
    self._data2Obj = {wrappedData:self}
    self._pid2Obj = {}
    
    self._pid2Obj[self.className] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[_id] = self

    # Set up pid sorting dictionary to cache pid sort keys
    self._pidSortKeys = {}

    # Special attributes:
    self._implExperimentTypeMap = None

    # Set required objects in apiProject and ApiNmrProject
    #
    # NBNB TBD All this should probably be moved to either AppBase initiation or V2 upgrade
    # preferably the latter.

    # PeakLists and Spectrum contour colours
    for experiment in wrappedData.experiments:
      for dataSource in experiment.dataSources:

        if not dataSource.peakLists:
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

    # set appBase attribute - for gui applications
    if hasattr(wrappedData.root, '_appBase'):
      appBase = wrappedData.root._appBase
      self._appBase = appBase
      appBase.project = self
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
    wrapperFuncName = '_%s%s%s' % (func.__module__.replace('.', dot), dot, func.__name__)

    setattr(Project, wrapperFuncName, func)
    Project._apiNotifiers.append((wrapperFuncName, parameterDict, apiClassName, apiFuncName))

  def _registerApiNotifiers(self):
    """Register notifiers"""

    for tt in self._apiNotifiers:
      wrapperFuncName, parameterDict, apiClassName, apiFuncName = tt
      notify = functools.partial(getattr(self,wrapperFuncName), **parameterDict)
      self._registerNotify(notify, apiClassName, apiFuncName)

  def _clearApiNotifiers(self):
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

    result = cls(self, wrappedData)

    sideBar = self._getApplicationSidebar()
    if sideBar is not None:
      sideBar._createItem(result)
    #
    return result

  def _finaliseDelete(self, wrappedData):
    """Clean up after object deletion - to be called from notifiers
    wrapperObject to delete is identified from wrappedData"""

    if not wrappedData.isDeleted:
      raise ValueError("_finaliseDelete called before wrapped data are deleted: %s" % wrappedData)

    # get object
    obj = self._data2Obj.get(wrappedData)

    # Remove from GUI sidebar - if any
    sideBar = self._getApplicationSidebar()
    if sideBar is not None:
      sideBar._removeItem(obj.pid)

    # remove from wrapped2Obj
    del self._data2Obj[wrappedData]

    # remove from pid2Obj
    del self._pid2Obj[obj.shortClassName][obj._id]

    # Mark object as obviously deleted, and set up for undeletion
    obj._id += '-Deleted'
    wrappedData._oldWrapperObject = obj
    obj._wrappedData = None

  def _finaliseUnDelete(self, wrappedData):
    """restore undeleted wrapper object"""

    if wrappedData.isDeleted:
      raise ValueError("_finaliseUnDelete called before wrapped data are deleted: %s" % wrappedData)

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

    # Put back in GUI sidebar - if any
    sideBar = self._getApplicationSidebar()
    if sideBar is not None:
      sideBar._createItem(oldWrapperObject)

  def _resetPid(self, wrappedData):
    """Reset internal attributes after values determining PID have changed"""
    sideBar = self._getApplicationSidebar()

    getDataObj = self._data2Obj.get
    pid2Obj = self._pid2Obj

    objects = [getDataObj(wrappedData)]
    for obj in objects:
      # Add objects to list whose Pid needs to change in tandem
      objects.extend(obj._getPidDependentObjects())

      # reset _id
      oldId = obj._id
      oldPid = obj.pid

      parent = obj._parent
      if parent is None:
        _id = ''
      elif parent is self:
        _id = str(obj._key)
      else:
        _id = '%s%s%s'% (parent._id, Pid.IDSEP, obj._key)
      obj._id = _id
      obj._old_id = oldId

      # update pid:object mapping dictionary
      dd = pid2Obj[obj.className]
      del dd[oldId]
      dd[_id] = obj

      # Refresh sidebar items if any
      if sideBar is not None:
        sideBar._renameItem(oldPid, obj.pid)


  def _getApplicationSidebar(self):
    """Get Appliction sidebar, if any.

     Used as preliminary in sidebar reset functions"""
    mainWindow = self._appBase and self._appBase.mainWindow
    if mainWindow is not None:
      return mainWindow.sideBar

    return None

  def _resetSpectrumInSidebar(self, dataSource:'ApiDataSource'):
    """Reset application sidebar when spectrum<->SpectrumGroup link changes
    Called by notifiers.
    No-op if there is no application and thus no sidebar
    """

    sideBar = self._getApplicationSidebar()
    if sideBar is not None:
      spectrum = self._data2Obj[dataSource]
      sideBar._removeItem(spectrum.pid)
      sideBar._createItem(spectrum)

  def _resetSpectrumGroupInSidebar(self, apiSpectrumGroup:'ApiSpectrumGroup'):
    """Reset application sidebar when spectrum<->SpectrumGroup link changes
    Called by notifiers for addDataSource, __init__, and undelete, where all affected
    dataSources are attached after the operation.
    No-op if there is no application and thus no sidebar
    """

    sideBar = self._getApplicationSidebar()
    if sideBar is not None:
      for dataSource in apiSpectrumGroup.sortedDataSources():
        spectrum = self._data2Obj[dataSource]
        sideBar._removeItem(spectrum.pid)
        sideBar._createItem(spectrum)

  def _resetAllSpectraInSidebar(self, dummyObj:AbstractWrapperObject):
    """Reset application sidebar when spectrum<->SpectrumGroup link changes
    Called by notifiers for SpectrumGroup.delete, .setDataSources, and .removeDataSource
    where NOT all affected dataSources are attached after the operation.
    No-op if there is no application and thus no sidebar
    """

    sideBar = self._getApplicationSidebar()
    if sideBar is not None:
      for spectrum in self.spectra:
        sideBar._removeItem(spectrum.pid)
        sideBar._createItem(spectrum)

  # NBNB We do NOT want to delete the underlying nmrProject, in case the root
  # hangs around and is somehow saved
  # Anyway at this point deleting the API objects no longer delete the wrapper objects
  # as the notifiers have been disabled
  # def delete(self):
  #   """Delete underlying data and cleans up the wrapper project"""
  #   wrappedData = self._wrappedData
  #   self._close()
  #   wrappedData.delete()

  def _close(self):
    """Clean up the wrapper project previous to deleting or replacing"""
    # Remove undo stack:
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

  def _flushCachedData(self, dummy=None):
    """Flush cached data to ensure up-to-date data are saved"""
    for structureEnsemble in self.structureEnsembles:
      for tag in ('coordinateData', 'occupancyData', 'bFactorData'):
        _tag = '_' + tag
        if hasattr(structureEnsemble, _tag):
          # Save cached data back to underlying storage
          setattr(structureEnsemble, tag, getattr(structureEnsemble, _tag))
          delattr(structureEnsemble, _tag)

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
        self._resetPid(apiNmrProject)
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
      self._logger.warning("Trying to add undoPoint bu undo not initialised")
    else:
      undo.newWaypoint()
      self._logger.info("Added undoPoint")


  @property
  def  _residueName2chemCompId(self) -> dict:
    """dict of {residueName:(molType,ccpCode)}"""
    return MoleculeQuery.fetchStdResNameMap(self._wrappedData.root)

  @property
  def _experimentTypeMap(self) -> Dict:
    """{dimensionCount : {sortedNucleusCodeTuple : {experimentTypeSynonym : experimentTypeName}}}
    dictionary"""
    result = self._implExperimentTypeMap
    if result is None:
      result = {}
      refExperimentMap = NmrExpPrototype.fetchIsotopeRefExperimentMap(self._apiNmrProject.root)

      for nucleusCodes, refExperiments in refExperimentMap.items():

        ndim = len(nucleusCodes)
        dd1 = result.get(ndim, {})
        result[ndim] = dd1

        dd2 = dd1.get(nucleusCodes, {})
        dd1[nucleusCodes] = dd2
        for refExperiment in refExperiments:
          name = refExperiment.name
          dd2[refExperiment.synonym or name] = name

      self._implExperimentTypeMap = result
    #
    return result

  #
  # utility functions