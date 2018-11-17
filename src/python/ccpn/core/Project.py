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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import functools
import os
import typing
from typing import Sequence, Tuple
import operator
from collections import OrderedDict
from ccpn.util.Common import _traverse, _getChildren
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.util import Undo
from ccpn.util import Logging
from ccpn.util.ExcelReader import ExcelReader
from ccpn.util.nef.GenericStarParser import DataBlock
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
from ccpn.ui.gui.lib.guiDecorators import suspendSideBarNotifications
from time import time
from ccpn.util.Logging import getLogger
from contextlib import contextmanager


# TODO These should be merged with the sams constants in CcpnNefIo
# (and likely those in ExportNefPopup) and moved elsewhere
CHAINS = 'chains'
CHEMICALSHIFTLISTS = 'chemicalShiftLists'
RESTRAINTLISTS = 'restraintLists'
PEAKLISTS = 'peakLists'
INTEGRALLISTS = 'integralLists'
MULTIPLETLISTS = 'multipletLists'
SAMPLES = 'samples'
SUBSTANCES = 'substances'
NMRCHAINS = 'nmrChains'
DATASETS = 'dataSets'
COMPLEXES = 'complexes'
SPECTRUMGROUPS = 'spectrumGroups'
NOTES = 'notes'
PEAKCLUSTERS = 'peakClusters'


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

    # Needs to know this for restoring the GuiSpectrum Module. Could be removed after decoupling Gui and Data!
    _isNew = None

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
        # self._id = _id = ''

        # setup object handling dictionaries
        self._data2Obj = {wrappedData: self}
        self._pid2Obj = {}

        # self._pid2Obj[self.className] =  dd = {}
        # self._pid2Obj[self.shortClassName] = dd
        # dd[_id] = self

        self._id = wrappedData.name
        self._resetIds()

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

    # GWV: 20181102: insert to retain consistency with future changes
    @property
    def application(self):
        return self._appBase

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
        self.close()

    def close(self):
        """Clean up the wrapper project previous to deleting or replacing

        Cleanup includes wrapped data graphics objects (e.g. Window, Strip, ...)"""
        # Remove undo stack:
        self._logger.info("Closing %s" % self.path)

        self._resetUndo(maxWaypoints=0)

        apiIo.cleanupProject(self)
        self._clearAllApiNotifiers()
        for tag in ('_data2Obj', '_pid2Obj'):
            getattr(self, tag).clear()
            # delattr(self,tag)
        # del self._wrappedData
        self.__dict__.clear()

    def __repr__(self):
        """String representation"""
        if self.isDeleted:
            return "<ccpn.core.Project:%s, isDeleted=True>" % self.name
        else:
            return "<ccpn.core.Project:%s>" % self.name

    def __str__(self):
        """String representation"""
        if self.isDeleted:
            return "<PR:%s, isDeleted=True>" % self.name
        else:
            return "<PR:%s>" % self.name

    # CCPN properties
    @property
    def _key(self) -> str:
        """Project id: Globally unique identifier (guid)"""
        return self._wrappedData.guid.translate(Pid.remapSeparators)

    @property
    def _parent(self) -> AbstractWrapperObject:
        """Parent (containing) object."""
        return None

    def save(self, newPath: str = None, changeBackup: bool = True,
             createFallback: bool = False, overwriteExisting: bool = False,
             checkValid: bool = False, changeDataLocations: bool = False) -> bool:
        """Save project with all data, optionally to new location or with new name.
        Unlike lower-level functions, this function ensures that data in high level caches are saved.
        Return True if save succeeded otherwise return False (or throw error)"""
        # self._flushCachedData()
        savedOk = apiIo.saveProject(self._wrappedData.root, newPath=newPath,
                                    changeBackup=changeBackup, createFallback=createFallback,
                                    overwriteExisting=overwriteExisting, checkValid=checkValid,
                                    changeDataLocations=changeDataLocations)
        if savedOk:
            self._resetIds()
            application = self._appBase
            if application is not None:
                application._refreshAfterSave()

        return savedOk

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
    def backupPath(self):
        """path to directory containing  backup Project"""
        backupRepository = self._wrappedData.parent.findFirstRepository(name="backup")

        if not backupRepository:
            self._logger.warning('Warning: no backup path set, so no backup done')
            return

        backupUrl = backupRepository.url
        backupPath = backupUrl.path
        return backupPath

    @property
    def programName(self) -> str:
        """Name of running program - defaults to 'CcpNmr'"""
        appBase = self._appBase if hasattr(self, '_appBase') else None
        return 'CcpNmr' if appBase is None else appBase.applicationName

    def deleteObjects(self, *objects: typing.Sequence[typing.Union[Pid.Pid, AbstractWrapperObject]]):
        """Delete one or more objects, given as either objects or Pids"""

        getByPid = self.getByPid

        objs = [getByPid(x) if isinstance(x, str) else x for x in objects]
        apiObjs = [x._wrappedData for x in objs]
        self._startDeleteCommandBlock(*apiObjs)
        try:
            for obj in objs:
                if obj and not obj.isDeleted:
                    # If statement in case deleting one obj triggers the deletion of another

                    # if the object is a Spectrum then delete peak/integralLists
                    if obj.pid.startswith('SP'):
                        for peakList in obj.peakLists:
                            peakList.delete()
                        for integralList in obj.integralLists:
                            integralList.delete()
                        for multipletList in obj.multipletLists:
                            multipletList.delete()
                    obj.delete()

        finally:
            self._endDeleteCommandBlock(*apiObjs)

    # def renameObject(self, objectOrPid:typing.Union[str,AbstractWrapperObject], newName:str):
    #   """Rename object indicated by objectOrPid to name newName
    #   NB at last one class (Substance) has a two-part name - these are passed as one,
    #   dot-separated string (e.g. 'Lysozyme.U13C'"""
    #   obj = self._data2Obj.get(objectOrPid) if isinstance(objectOrPid, str) else objectOrPid
    #   names = newName.split('.')
    #   obj.rename(*names)

    def execute(self, pid, funcName, *params, **kwparams):
        """Get the object identified by pid, execute object.funcName(\*params, \*\*kwparams)
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

    def _resetUndo(self, maxWaypoints: int = 20, maxOperations: int = 10000,
                   debug: bool = False, application=None):
        """Reset undo stack, using passed-in parameters.
        NB setting either parameter to 0 removes the undo stack."""
        Undo.resetUndo(self._wrappedData.root, maxWaypoints=maxWaypoints,
                       maxOperations=maxOperations, debug=debug, application=application)

    def newUndoPoint(self):
        """Set a point in the undo stack, you can undo/redo to """
        undo = self._wrappedData.root._undo
        if undo is None:
            self._logger.warning("Trying to add undoPoint but undo is not initialised")
        else:
            undo.newWaypoint()  # DO NOT CHANGE THIS ONE newWaypoint
            self._logger.debug("Added undoPoint")

    def blockWaypoints(self):
        """Block the setting of undo waypoints,
        so that command echoing (_startCommandBLock) does not set waypoints

        NB The programmer must GUARANTEE (try: ... finally) that waypoints are unblocked again"""
        undo = self._wrappedData.root._undo
        if undo is None:
            self._logger.warning("Trying to block waypoints but undo is not initialised")
        else:
            undo.increaseWaypointBlocking()
            self._logger.debug("Waypoint setting blocked")

    def unblockWaypoints(self):
        """Block the setting of undo waypoints,
        so that command echoing (_startCommandBLock) does not set waypoints

        NB The programmer must GUARANTEE (try: ... finally) that waypoints are unblocked again"""
        undo = self._wrappedData.root._undo
        if undo is None:
            self._logger.warning("Trying to unblock waypoints but undo is not initialised")
        else:
            undo.decreaseWaypointBlocking()
            self._logger.debug("Waypoint setting unblocked")

    # Should be removed:
    @property
    def _residueName2chemCompId(self) -> dict:
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

        # NBNB TODO FIXME fetchIsotopeRefExperimentMap should be merged with
        # getExpClassificationDict output - we should NOT have two parallel dictionaries

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

        func must be a function taking two parameters: the ccpn.core.Project and an Api object
        matching apiClassOrName.

        'apiFuncName' is either the name of an API modifier function (a setter, adder, remover),
        in which case the notifier is triggered by this function
        Or it is one of the following tags:
        ('', '__init__', 'postInit', 'preDelete', 'delete', 'startDeleteBlock', 'endDeleteBlock').
        '' registers the notifier to any modifier function call ( setter, adder, remover),
        __init__ and postInit triggers the notifier at the end of object creation, before resp.
        after execution of postConstructorCode, the four delete-related tags
        trigger notifiers at four different points in the deletion process
        (see memops.Implementation.DataObject.delete() code for details).


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

        notify = functools.partial(getattr(self, wrapperFuncName), **parameterDict)
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

    def registerNotifier(self, className: str, target: str, func: typing.Callable[..., None],
                         parameterDict: dict = {}, onceOnly: bool = False) -> typing.Callable[..., None]:
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

    def duplicateNotifier(self, className: str, target: str,
                          notifier: typing.Callable[..., None]):
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

    def unRegisterNotifier(self, className: str, target: str, notifier: typing.Callable[..., None]):
        """Unregister the notifier from this className, and target"""
        if target in self._notifierActions:
            tt = (className, target)
        else:
            # This is right, it just looks strange. But if target is not an action it is
            # another className, and if so the names must be sorted.
            tt = tuple(sorted([className, target]))
        try:
            if hasattr(self, '_context2Notifiers'):
                od = self._context2Notifiers.get((tt), {})
                del od[notifier]
        except KeyError:
            self._logger.warning("Attempt to unregister unknown notifier %s for %s" % (notifier, (className, target)))

    def removeNotifier(self, notifier: typing.Callable[..., None]):
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
        if self._notificationBlanking < 0:
            raise TypeError("Code Error: _notificationBlanking below zero!")

    def suspendNotification(self):
        """Suspend notifier execution and accumulate notifiers for later execution"""
        # return
        # TODO suspension temporarily disabled
        self._notificationSuspension += 1

    def resumeNotification(self):
        """Execute accumulated notifiers and resume immediate notifier execution"""
        # return
        # TODO suspension temporarily disabled
        # This was broken at one point, and we never found time to fix it
        # It is a time-saving measure, allowing you to e.g. execute a
        # peak-created notifier only once when creating hundreds of peaks in one operation

        if self._notificationSuspension > 1:
            self._notificationSuspension -= 1
        else:
            # Should not be necessary, but in this way we never get below 0 no matter what errors happen
            self._notificationSuspension = 0
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
                if not getattr(self, '_apiBlanking', 0):
                    # notifier(*params)
                    self._notifierAction(notifier, *params)

    # Standard notified functions.
    # RESTRICTED. Use in core classes ONLY

    def _startDeleteCommandBlock(self, *allWrappedData):
        """Call startCommandBlock for wrapper object delete. Implementation only"""

        undo = self._undo
        if undo is not None:
            # set undo step
            undo.newWaypoint()  # DO NOT CHANGE THIS
            undo.increaseWaypointBlocking()

            # TODO:ED check this!
            # self.suspendNotification()

        if not self._appBase._echoBlocking:

            getDataObj = self._data2Obj.get
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
        undo = self._undo
        if undo is not None:
            # TODO:ED check this!
            # self.resumeNotification()
            undo.decreaseWaypointBlocking()

        if self._appBase._echoBlocking > 0:
            # If statement should always be True, but to avoid weird behaviour in error situations we check
            self._appBase._echoBlocking -= 1

    def _newApiObject(self, wrappedData, cls: AbstractWrapperObject):
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
        print('>>>_modifiedApiObject', obj)
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

    def _notifyRelatedApiObject(self, wrappedData, pathToObject: str, action: str):
        """ call 'action' type notifiers for getattribute(pathToObject)(wrappedData)
        pathToObject is a navigation path (may contain dots) and must yield an API object
        or an iterable of API objects"""

        getDataObj = self._data2Obj.get

        target = operator.attrgetter(pathToObject)(wrappedData)

        # GWV: a bit too much for now; should be the highest debug level only
        #self._project._logger.debug('%s: %s.%s = %s'
        #                            % (action, wrappedData, pathToObject, target))

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

    def _modifiedLink(self, dummy, classNames: typing.Tuple[str, str]):
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
        # NB 'AbstractWrapperObject' not currently in use (Sep 2016), but kept for future needs
        iterator = (self._context2Notifiers.setdefault((name, target), OrderedDict())
                    for name in (className, 'AbstractWrapperObject'))
        # Notification suspension postpones notifications (and removes duplicates)
        # It is broken and has been disabled for a long time.
        # There may be some accumulated bugs when (if)it is turned back on.
        if False and self._notificationSuspension:
            ll = self._pendingNotifications
            for dd in iterator:
                for notifier, onceOnly in dd.items():
                    ll.append((notifier, onceOnly, self))
        else:
            for dd in iterator:
                for notifier in dd:
                    # notifier(self)
                    self._notifierAction(notifier, self)

    # Library functions

    def exportNef(self, path: str = None,
                  overwriteExisting: bool = False,
                  skipPrefixes: typing.Sequence = (),
                  expandSelection: bool = True,
                  pidList: list = None):
        """
        Export selected contents of the project to a Nef file.

          skipPrefixes: ( 'ccpn', ..., <str> )
          expandSelection: <bool> }

          Include 'ccpn' in the skipPrefixes list will exclude ccpn specific items from the file
          expandSelection = True  will include all data from the project, this may not be data that
                                  is not defined in the Nef standard.

        PidList is a list of <str>, e.g. 'NC:@-', obtained from the objects to be included.
        The Nef file may also contain further dependent items associated with the pidList.

        :param path: output path and filename
        :param skipPrefixes: items to skip
        :param expandSelection: expand the selection
        :param pidList: a list of pids
        """
        from ccpn.core.lib import CcpnNefIo
        from collections import OrderedDict

        defaults = OrderedDict((('path', None),
                                ('overwriteExisting', None),
                                ('skipPrefixes', None),
                                ('expandSelection', None),
                                ('pidList', None)))

        self._startCommandEchoBlock('exportNef', values=locals(), defaults=defaults)
        undo = self._undo
        if undo is not None:
            undo.increaseBlocking()
        self.blankNotification()

        try:
            t0 = time()
            CcpnNefIo.exportNef(self, path,
                                overwriteExisting=overwriteExisting,
                                skipPrefixes=skipPrefixes,
                                expandSelection=expandSelection,
                                pidList=pidList)
            t2 = time()
            getLogger().info('Exported NEF file, time = %.2fs' % (t2 - t0))

        finally:
            self._endCommandEchoBlock()
            self.unblankNotification()
            if undo is not None:
                undo.decreaseBlocking()

    def _convertToDataBlock(self, skipPrefixes: typing.Sequence = (),
                            expandSelection: bool = True,
                            pidList: list = None):
        """
        Export selected contents of the project to a Nef file.

          skipPrefixes: ( 'ccpn', ..., <str> )
          expandSelection: <bool> }

          Include 'ccpn' in the skipPrefixes list will exclude ccpn specific items from the file
          expandSelection = True  will include all data from the project, this may not be data that
                                  is not defined in the Nef standard.

        PidList is a list of <str>, e.g. 'NC:@-', obtained from the objects to be included.
        The Nef file may also contain further dependent items associated with the pidList.

        :param skipPrefixes: items to skip
        :param expandSelection: expand the selection
        :param pidList: a list of pids
        """
        from ccpn.core.lib import CcpnNefIo

        defaults = OrderedDict((('skipPrefixes', None),
                                ('expandSelection', None),
                                ('pidList', None)))

        self._startCommandEchoBlock('exportNef', values=locals(), defaults=defaults)
        undo = self._undo
        if undo is not None:
            undo.increaseBlocking()
        self.blankNotification()

        dataBlock = None
        newPath = None
        try:
            t0 = time()
            dataBlock = CcpnNefIo.convertToDataBlock(self, skipPrefixes=skipPrefixes,
                                                     expandSelection=expandSelection,
                                                     pidList=pidList)
            t2 = time()
            getLogger().info('File to dataBlock, time = %.2fs' % (t2 - t0))

        finally:
            self._endCommandEchoBlock()
            self.unblankNotification()
            if undo is not None:
                undo.decreaseBlocking()

        return dataBlock

    def _writeDataBlockToFile(self, dataBlock: DataBlock = None, path: str = None,
                              overwriteExisting: bool = False):
        # Export the modified dataBlock to file
        from ccpn.core.lib import CcpnNefIo

        defaults = OrderedDict((('dataBlock', None),
                                ('path', None),
                                ('overwriteExisting', None)))

        self._startCommandEchoBlock('writeDataBlockToFile', values=locals(), defaults=defaults)
        undo = self._undo
        if undo is not None:
            undo.increaseBlocking()
        self.blankNotification()

        try:
            t0 = time()
            CcpnNefIo.writeDataBlock(dataBlock, path=path, overwriteExisting=overwriteExisting)
            t2 = time()
            getLogger().info('Exporting dataBlock to file, time = %.2fs' % (t2 - t0))

        finally:
            self._endCommandEchoBlock()
            self.unblankNotification()
            if undo is not None:
                undo.decreaseBlocking()

    def recurseAnalyseUrl(self, filePath, includeUndefined=False):
        """Recurse through the given path to find valid data that can be loaded
        This list will contain loadable files and loadable folders which may load the same data
        if includeUndefined is True, will include ('Text', None, ...) results
        which may not be useful
        """
        from ccpn.util.OrderedSet import OrderedSet

        validList = OrderedSet()

        if os.path.isdir(filePath):
            # list the folders
            dirs = [os.path.join(filePath, dirpath) for dirpath, dirs, files in os.walk(filePath, topdown=False)]

            # list the files
            dirs += [os.path.join(filePath, dirpath, file)
                     for dirpath, dirs, files in os.walk(filePath, topdown=False)
                     for file in files]

            # search the folders and files the valid data
            for dI in dirs:
                dataType, subType, usePath = ioFormats.analyseUrl(dI)

                # only add the valid types to the set
                if usePath:

                    # include if both defined or either is None IF includeUndefined is True
                    if (dataType and subType) or (includeUndefined and ((dataType and not subType) or (subType and not dataType))):

                        # only add if not a subset of an existing path
                        for inList in validList:
                            if inList[2].startswith(usePath):
                                break
                        else:

                            # flag whether the usePath is a folder
                            validList.add((dataType, subType, usePath, os.path.isdir(usePath)))

        return validList

    def loadData(self, path: str) -> typing.Optional[typing.List]:
        """
        Load data from path, determining type first.
        Return None for Un-recognised or un-parsable files; return empty list for ???
        """

        # TODO: RASMUS:
        # RASMUS EXPLANATION (to my successor)
        # loadData does too many things: it is used for handling dropped files,
        # which includes a system for deciding what actions are taken where for what file types,
        # and it is called directly for loading e.g. a spectrum.
        #
        # Part of the idea was that a file of type 'Xyz' being dropped would trigger
        # a call to '_loadXyz' if, and only if, _loadXyz was defined for the object
        # in question. That allowed you to control which drops were allowed where, and what
        # specific actions should be triggered.
        #
        # The entire system has been (partially??) refactored by GV, so it is necessary to rethink this.
        # My proposal (hopefully consistent with GV's (?)) would be to use this function
        # ONLY to handle drops and other files of unknown type (and likely rename it _loadData')
        # and to call specific functions (like loadSpectrum) when you know that you are loading e.g. a
        # spectrum or a project (currently loadData is (too) widely used.
        # Some of these functions may or may not need to be written first.
        # That still leaves the question of how to handle a case where e.g. a text
        # file should trigger a specific action when loaded e.g. on a Note editor popup and oNLY there,
        # but that must be thought out and decided.
        # Anyway, this function should have a proper and consistent return type (as GV says)
        # Maybe we should consider returning a dictionary rather than a list of tuples??

        # urlInfo is list of triplets of (type, subType, modifiedUrl),
        # e.g. ('Spectrum', 'Bruker', newUrl)

        # scan the folder for valid data
        # validList = self.recurseAnalyseUrl(path)

        dataType, subType, usePath = ioFormats.analyseUrl(path)

        #TODO:RASMUS: Replace prints by logger calls
        #TODO:RASMUS: Fix all return types; define properly first
        if dataType is None:
            print("Skipping: file data type not recognised for %s" % usePath)
            return None

        elif dataType == 'Dirs':
            # special case - usePath is a list of paths from a top dir with enumerate subDirs and paths.
            paths = usePath
            #TODO:RASMUS: Undefined return type
            for path in paths:
                self.loadData(path)

        elif not os.path.exists(usePath):
            print("Skipping: no file found at %s" % usePath)
            return []

        elif dataType == 'Text':
            # Special case - you return the text instead of a list of Pids
            # GWV: Can't do this!! -> have to return a list of tuples: [(dataType, pid or data)]
            # need to define these dataTypes as CONSTANTS in the ioFormats.analyseUrl routine!
            #TODO:RASMUS: return type is not a list

            return open(usePath).read()

        elif dataType == 'Macro' and subType == ioFormats.PYTHON:
            # GWV: Can't do this: have to call the routine with a flag: autoExecute=True
            # with suspendSideBarNotifications(self, 'runMacro', usePath, quiet=False):
            self._appBase.runMacro(usePath)

        elif dataType == 'Project' and subType == ioFormats.CCPNTARFILE:
            # with suspendSideBarNotifications(self, 'loadData', usePath, quiet=False):
            projectPath, temporaryDirectory = self._appBase._unpackCcpnTarfile(usePath)
            project = self.loadProject(projectPath, ioFormats.CCPN)
            #TODO:RASMUS: use python tmpdir or V3 class
            # NBNB _unpackCcpnTarfile *does* use the Python tempfile module
            project._wrappedData.root._temporaryDirectory = temporaryDirectory
            return [project]

        else:
            # No idea what is going on here
            #TODO: use a dictionary to define
            funcname = '_load' + dataType
            if funcname == '_loadProject':
                # with suspendSideBarNotifications(self, 'loadData', usePath, quiet=False):
                thisProj = [self.loadProject(usePath, subType)]
                return thisProj

            elif funcname == '_loadSpectrum':
                # NBNB TBD #TODO:RASMUS:FIXME check if loadSpectrum should start with underscore
                # (NB referred to elsewhere
                with suspendSideBarNotifications(self, 'loadData', usePath, quiet=False):
                    thisSpec = self.loadSpectrum(usePath, subType)
                return thisSpec

            elif hasattr(self, funcname):
                pids = getattr(self, funcname)(usePath, subType)
                return pids
            else:
                print("Skipping: project has no function %s" % funcname)

        return []

    # Data loaders and dispatchers
    def _loadSequence(self, path: str, subType: str) -> list:
        """Load sequence(s) from file into Wrapper project"""

        if subType == ioFormats.FASTA:
            sequences = fastaIo.parseFastaFile(path)
        else:
            raise ValueError("Sequence file type %s is not recognised" % subType)

        chains = []
        for sequence in sequences:
            chains.append(self.createChain(sequence=sequence[1], compoundName=sequence[0],
                                           molType='protein'))
        #
        return chains

    def _loadStructure(self, path: str, subType: str):
        '''
        Load Structure ensemble(s) from file into Wrapper project
        '''

        from ccpn.util.StructureData import averageStructure

        if subType == 'PDB':
            name, ensemble = self._loadPdbStructure(path)
        else:
            raise NotImplementedError('{} type structures cannot be loaded'.format(subType))
        se = self.newStructureEnsemble()
        se.data = ensemble
        se.rename(name)

        ds = self.newDataSet(title=name)
        d = ds.newData(name='Derived')
        d.setParameter('average', averageStructure(ensemble))

        return [se]

    def _loadPdbStructure(self, path):
        import os
        from ccpn.util.StructureData import EnsembleData

        label = os.path.split(path)[1]
        label = label.split('.')[:-1]
        label = '_'.join(label)

        ensemble = EnsembleData.from_pdb(path)
        return label, ensemble

    def _loadNefFile(self, path: str, subType: str):
        """
        Load a Nef file into an existing project
        """
        # ejb - 24/6/17
        from ccpn.core.lib import CcpnNefIo

        if subType in (ioFormats.NEF):

            return self._appBase.loadProject(path)

            # # load Nef File here
            # nefReader = CcpnNefIo.CcpnNefReader(self)
            #
            # dataBlock = nefReader.getNefData(path)
            # # project = self.newProject(dataBlock.name)
            # # self._echoBlocking += 1
            # self._undo.increaseBlocking()
            # self._wrappedData.shiftAveraging = False
            #
            # nefReader.importNewProject(self, dataBlock)
            #
            # self._wrappedData.shiftAveraging = True
            # # self._echoBlocking -= 1
            # self._undo.decreaseBlocking()
            #
            # return True
        else:
            raise ValueError("Project file type %s is not recognised" % subType)

    def loadProject(self, path: str, subType: str) -> "Project":
        """Load project from file into application and return the new project"""

        # if subType == ioFormats.CCPN:
        if subType in (ioFormats.CCPN, ioFormats.NEF, ioFormats.NMRSTAR, ioFormats.SPARKY):
            return self._appBase.loadProject(path)
        else:
            raise ValueError("Project file type %s is not recognised" % subType)

    def loadSpectrum(self, path: str, subType: str) -> list:
        """Load spectrum from file into application"""

        # #TODO:RASMUS FIXME check for rename

        apiDataSource = self._wrappedData.loadDataSource(path, subType)
        if apiDataSource is None:
            return []
        else:
            spectrum = self._data2Obj[apiDataSource]
            spectrum.assignmentTolerances = spectrum.defaultAssignmentTolerances

            # make sure the colour brightness is not too close to the colourScheme background
            # TODO:ED another nasty _appBase

            # if there is a gui then check the colours
            if self._appBase.ui:
                if self._appBase.preferences and self._appBase.preferences.general.autoCorrectColours:
                    from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND
                    from ccpn.core.lib.SpectrumLib import getDefaultSpectrumColours

                    (spectrum.positiveContourColour, spectrum.negativeContourColour) = getDefaultSpectrumColours(spectrum)
                    spectrum.sliceColour = spectrum.positiveContourColour

                    # spectrum.positiveContourColour = autoCorrectHexColour(spectrum.positiveContourColour,
                    #                                                       getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                    # spectrum.negativeContourColour = autoCorrectHexColour(spectrum.negativeContourColour,
                    #                                                       getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                    # spectrum.sliceColour = autoCorrectHexColour(spectrum.sliceColour,
                    #                                                       getColours()[CCPNGLWIDGET_HEXBACKGROUND])

            return [spectrum]

    def _loadLookupFile(self, path: str, subType: str, ):
        """Load data from a look-up file, csv or xls ."""

        if subType == ioFormats.CSV:
            self._logger.warning("This function has not been implemented yet")
            # readCsv(self, path=path)

        elif subType == ioFormats.EXCEL:
            ExcelReader(project=self, excelPath=path)

    def _uniqueSubstanceName(self, name: str = None, defaultName: str = 'Molecule') -> str:
        """add integer suffixed to name till it is unique"""

        apiComponentStore = self._wrappedData.sampleStore.refSampleComponentStore
        apiProject = apiComponentStore.root

        # ensure substance name is unique
        if name:
            i = 0
            result = name
            formstring = name + '_%d'
        else:
            formstring = defaultName + '_%d'
            i = 1
            result = formstring % i
        while (apiProject.findFirstMolecule(name=result) or
               apiComponentStore.findFirstComponent(name=result)):
            i += 1
            result = formstring % i
        if name and result != name and name != defaultName:
            self._logger.warning(
                    "CCPN molecule named %s already exists. New molecule has been named %s" %
                    (name, result))
        #
        return result

    def getObjectsByPartialId(self, className: str,
                              idStartsWith: str) -> typing.List[AbstractWrapperObject]:
        """get objects from class name / shortName and the start of the ID.

        The function does NOT interrogate the API level, which makes it faster in a
        number fo cases, e.g. for NmrResidues"""

        dd = self._pid2Obj.get(className)
        if dd:
            # NB the _pid2Obj entry is set in the object init.
            # The relevant dictionary may therefore be missing if no object has yet been created
            result = [tt[1] for tt in dd.items() if tt[0].startswith(idStartsWith)]
        else:
            result = None
        #
        return result

    #===========================================================================================
    # Hot fixed methods (baahhhhhh)
    # Copied from their respective locations
    #===========================================================================================
    def newMark(self, colour: str, positions: Sequence[float], axisCodes: Sequence,
                style: str = 'simple', units: Sequence[str] = (), labels: Sequence[str] = ()):
        """Create new Mark

        :param str colour: Mark colour
        :param tuple/list positions: Position in unit (default ppm) of all lines in the mark
        :param tuple/list axisCodes: Axis codes for all lines in the mark
        :param str style: Mark drawing style (dashed line etc.) default: full line ('simple')
        :param tuple/list units: Axis units for all lines in the mark, Default: all ppm
        :param tuple/list labels: Ruler labels for all lines in the mark. Default: None

        return Mark instance

        Inserted later ccpn.ui._implementation.Mark
        """
        pass

    def _newSimpleMark(self, colour: str, position: float, axisCode: str, style: str = 'simple',
                       unit: str = 'ppm', label: str = None):
        """Create new child Mark with a single line

        :param str colour: Mark colour
        :param tuple/list position: Position in unit (default ppm)
        :param tuple/list axisCode: Axis code
        :param str style: Mark drawing style (dashed line etc.) default: full line ('simple')
        :param tuple/list unit: Axis unit. Default: all ppm
        :param tuple/list label: Line label. Default: None

        return Mark instance

        Inserted later ccpn.ui._implementation.Mark
        """
        pass

    def newSpectrum(self, name: str):
        """Creation of new Spectrum NOT IMPLEMENTED.
        Use Project.loadData or Project.createDummySpectrum instead

        Inserted later ccpn.Core.Spectrum
        """
        pass
        pass

    def _createDummySpectrum(self, axisCodes: Sequence[str], name=None,
                             chemicalShiftList=None):
        """Make dummy spectrum from isotopeCodes list - without data and with
        default parameters

        return Spectrum instance

        Inserted later ccpn.Core.Spectrum
        """
        pass
