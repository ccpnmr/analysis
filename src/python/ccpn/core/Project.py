"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-09-01 18:15:12 +0100 (Thu, September 01, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import functools
# import os
import typing
import operator
from typing import Sequence, Union, Optional, List
from collections import OrderedDict
# from time import time
from datetime import datetime
from collections.abc import Iterable
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core._implementation.Updater import UPDATE_POST_PROJECT_INITIALISATION
from ccpn.core._implementation.V3CoreObjectABC import V3CoreObjectABC

from ccpn.core.lib import Pid
from ccpn.core.lib import Undo
from ccpn.core.lib.ProjectSaveHistory import getProjectSaveHistory, fetchProjectSaveHistory, newProjectSaveHistory
from ccpn.core.lib.ContextManagers import notificationBlanking, undoBlock, undoBlockWithoutSideBar, \
    inactivity, logCommandManager

from ccpn.util import Logging
from ccpn.util.ExcelReader import ExcelReader
from ccpn.util.Path import aPath, Path
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import logCommand

from ccpn.framework.lib.pipeline.PipelineBase import Pipeline
from ccpn.framework.PathsAndUrls import CCPN_EXTENSION
from ccpn.framework.PathsAndUrls import \
    CCPN_ARCHIVES_DIRECTORY, \
    CCPN_STATE_DIRECTORY, \
    CCPN_DATA_DIRECTORY, \
    CCPN_SPECTRA_DIRECTORY, \
    CCPN_PLUGINS_DIRECTORY, \
    CCPN_SCRIPTS_DIRECTORY, \
    CCPN_SUB_DIRECTORIES

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrProject as ApiNmrProject
from ccpnmodel.ccpncore.memops import Notifiers
from ccpnmodel.ccpncore.memops.ApiError import ApiError
from ccpnmodel.ccpncore.lib.molecule import MoleculeQuery
from ccpnmodel.ccpncore.lib.spectrum import NmrExpPrototype
from ccpnmodel.ccpncore.api.ccp.nmr.NmrExpPrototype import RefExperiment
# from ccpnmodel.ccpncore.lib import Constants
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
# from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.lib import ApiPath
from ccpnmodel.ccpncore.lib.Io import Fasta as fastaIo
from ccpnmodel.ccpncore.api.memops import Implementation


# TODO These should be merged with the same constants in CcpnNefIo
# (and likely those in ExportNefPopup) and moved elsewhere
CHAINS = 'chains'
CHEMICALSHIFTLISTS = 'chemicalShiftLists'
RESTRAINTTABLES = 'restraintTables'
PEAKLISTS = 'peakLists'
INTEGRALLISTS = 'integralLists'
MULTIPLETLISTS = 'multipletLists'
SAMPLES = 'samples'
SUBSTANCES = 'substances'
NMRCHAINS = 'nmrChains'
# DATASETS = 'dataSets'
STRUCTUREDATA = 'structureData'
COMPLEXES = 'complexes'
SPECTRUMGROUPS = 'spectrumGroups'
NOTES = 'notes'
# _PEAKCLUSTERS = '_peakClusters'
COLLECTIONS = 'collections'


class Project(AbstractWrapperObject):
    """ The Project is the object that contains all data objects and serves as the hub for
    navigating between them.

    There are 15 top-level data objects directly within a project, of which 8 have child
    objects of their own, e.g. Spectrum, Sample, Chain, NmrChain, ChemicalShiftList, DataSet
    and StructureEnsemble. The child data objects are organised in a logical hierarchy; for example,
    a Spectrum has PeakLists, which in turn, are made up of Peaks, whereas a Chain is made up of Residues,
    which are made up of Atoms.
    """

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

    # 20211113:ED - added extra for searching the Collection objects as these are immutable
    _classNameLower2Class = {}
    _className2ClassList = []
    _classNameLower2ClassList = []

    # List of CCPN pre-registered api notifiers
    # Format is (wrapperFuncName, parameterDict, apiClassName, apiFuncName)
    #
    # The function self.wrapperFuncName(**parameterDict) will be registered in the CCPN api notifier system
    # api notifiers are set automatically, and are cleared by self._clearAllApiNotifiers and by self.delete()
    #
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

    #-----------------------------------------------------------------------------------------
    # Attributes of the data structure (incomplete)
    #-----------------------------------------------------------------------------------------

    @property
    def spectra(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def peakLists(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def peaks(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def multipletLists(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def integralLists(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def spectrumViews(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def chemicalShiftLists(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def chains(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def restraintTables(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def violationTables(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def samples(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def substances(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def nmrChains(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def structureData(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def complexes(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def spectrumGroups(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def notes(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def _peakClusters(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def chemicalShifts(self):
        """Return the list of chemicalShifts in the project
        """
        _shifts = []
        for shiftList in self.chemicalShiftLists:
            _shifts.extend(shiftList.chemicalShifts)
        return _shifts

    @property
    def collections(self):
        """Return the list of collections in the project
        """
        return self._collectionList.collections

    @property
    def _collectionData(self):
        return self._wrappedData.collectionData

    @_collectionData.setter
    def _collectionData(self, value):
        self._wrappedData.collectionData = value

    #-----------------------------------------------------------------------------------------
    # (Sub-)directories of the project
    #-----------------------------------------------------------------------------------------
    @property
    def projectPath(self) -> Path:
        """
        Convenience, as project.path (currently) does not yield a Path instance
        :return: the absolute path to the project as a Path instance
        """
        return aPath(self.path)

    @property
    def statePath(self) -> Path:
        """
        :return: the absolute path to the state sub-directory of the current project
                 as a Path instance
        """
        return self.projectPath / CCPN_STATE_DIRECTORY

    @property
    def pipelinePath(self) -> Path:
        """
        :return: the absolute path to the state/pipeline sub-directory of
                 the current project as a Path instance
        """
        return self.statePath.fetchDir(Pipeline.className)

    @property
    def dataPath(self) -> Path:
        """
        :return: the absolute path to the data sub-directory of the current project
                 as a Path instance
        """
        return self.projectPath / CCPN_DATA_DIRECTORY

    @property
    def spectraPath(self):
        """
        :return: the absolute path to the data sub-directory of the current project
                 as a Path instance
        """
        return self.projectPath / CCPN_SPECTRA_DIRECTORY

    @property
    def pluginDataPath(self) -> Path:
        """
        :return: the absolute path to the data/plugins sub-directory of the
                 current project as a Path instance
        """
        return self.projectPath / CCPN_PLUGINS_DIRECTORY

    @property
    def scriptsPath(self) -> Path:
        """
        :return: the absolute path to the script sub-directory of the current project
                 as a Path instance
        """
        return self.projectPath / CCPN_SCRIPTS_DIRECTORY

    @property
    def archivesPath(self) -> Path:
        """
        :return: the absolute path to the archives sub-directory of the current project
                 as a Path instance
        """
        return aPath(self.project.path) / CCPN_ARCHIVES_DIRECTORY

    # TODO: define not using API
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

    #-----------------------------------------------------------------------------------------
    # Implementation methods
    #-----------------------------------------------------------------------------------------

    def __init__(self, wrappedData: ApiNmrProject):
        """ Special init for root (Project) object

        NB Project is NOT complete before the _initProject function is run.
        """

        if not isinstance(wrappedData, ApiNmrProject):
            raise ValueError("Project initialised with %s, should be ccp.nmr.Nmr.NmrProject."
                             % wrappedData)

        # Define linkage attributes
        self._project = self
        self._wrappedData = wrappedData

        # self._appBase = None (delt with below)
        # Reference to application; defined by Framework
        self._application = None

        # setup object handling dictionaries
        self._data2Obj = {wrappedData: self}
        self._pid2Obj = {}

        self._id = wrappedData.name
        self._resetIds()

        # Set up notification machinery
        # Active notifiers - saved for later cleanup. CORE APPLICATION ONLY
        self._activeNotifiers = []

        # list or None. When set used to accumulate pending notifiers
        # Optional list. Elements are (func, onceOnly, wrapperObject, optional oldPid)
        self._pendingNotifications = []

        # Notification suspension level - to allow for nested notification suspension
        self._notificationSuspension = 0
        self._progressSuspension = 0

        # Notification blanking level - to allow for nested notification disabling
        self._notificationBlanking = 0

        # api 'change' notification blanking level - to allow for api 'change' call to be
        # disabled in the _modifiedApiObject method.
        # To be used with the apiNotificationBlanking contact manager; e.g.
        # with apiNotificationBlanking():
        #   do something
        #
        self._apiNotificationBlanking = 0

        # Wrapper level notifier tracking.  APPLICATION ONLY
        # {(className,action):OrderedDict(notifier:onceOnly)}
        self._context2Notifiers = {}

        # Special attributes:
        self._implExperimentTypeMap = None

        # reference to a ProjectSaveHistory instance; defined _newProject() or _loadProject()
        self._saveHistory = None

        # reference to the logger; defined in call to _initialiseProject())
        self._logger = None

        # reference to special v3 core lists without abstractWrapperObject
        self._collectionList = None

        self._checkProjectSubDirectories()

    @property
    def application(self):
        return self._application

    # GWV: 20181102: insert _appBase to retain consistency with current data loading models
    _appBase = application

    @property
    def isNew(self):
        """Return true if the project is new
        """
        # NOTE:ED - based on original check in _initProject
        return self._wrappedData.root.isModified

    @property
    def isTemporary(self):
        """Return true if the project is temporary, i.e., not saved or updated.
        """
        apiProject = self._wrappedData.root
        return hasattr(apiProject, '_temporaryDirectory')

    @property
    def isModified(self):
        """Return true if any part of the project has been modified
        """
        return self._wrappedData.root.isProjectModified()

    @property
    def _isUpgradedFromV2(self):
        """Return True if project was upgraded from V2
        """
        return self._apiNmrProject.root._upgradedFromV2

    @staticmethod
    def _needsUpgrading(path) -> bool:
        """
        Check if project defined by path needs upgrading
        :param path: a ccpn project-path
        :return: True/False
        """
        from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader

        # Check for V2 project; always needs upgrading
        if (dataloader := CcpNmrV2ProjectDataLoader.checkForValidFormat(path)) is not None:
            return True

        if (dataloader := CcpNmrV3ProjectDataLoader.checkForValidFormat(path)) is None:
            raise ValueError('Path "%s" does not define a valid ccpn project' % path)

        if (projectHistory := getProjectSaveHistory(dataloader.path)):
            # check whether the history exists
            return projectHistory.lastSavedVersion <= '3.0.4'

        return True

    @property
    def _data(self):
        """Get the contents of the data property from the model
        CCPNInternal only
        """
        return self._wrappedData.data

    @_data.setter
    def _data(self, value):
        """Set the contents of the data property from the model
        CCPNInternal only
        """
        if not isinstance(value, dict):
            raise ValueError('value must be a dict')

        self._wrappedData.data = value

    def _checkProjectSubDirectories(self):
        """if need be, create all project subdirectories
        """
        for dir in CCPN_SUB_DIRECTORIES:
            self.projectPath.fetchDir(dir)

    def _initialiseProject(self):
        """Complete initialisation of project,
        set up logger and notifiers, and wrap underlying data
        This routine is called from Framework, as some other machinery first needs to set up
        (linkages, Current, notifiers and such)
        """

        # The logger has already been set up when creating/loading the API project
        # so just get it
        self._logger = Logging.getLogger()

        # Set up notifiers
        self._registerPresetApiNotifiers()

        # initialise, creating the children; pass in self as we are initialising
        with inactivity(project=self):
            self._restoreChildren()
            # perform any required restoration of project not covered by children
            self._restoreObject(self, self._wrappedData)

            # we always have the default chemicalShift list
            if len(self.chemicalShiftLists) == 0:
                self.newChemicalShiftList(name='default')

            # Call any updates
            self._update()

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Process data that must always be performed after updating all children
        """
        from ccpn.core._implementation.CollectionList import CollectionList

        # create new collection table
        project._collectionList = CollectionList(project=project)

        # create new collections from table
        project._collectionList._restoreObject(project, None)

        # check that strips have been recovered correctly
        try:
            for sd in project.application.mainWindow.spectrumDisplays:
                for strp in sd.strips:
                    if not strp.axes:
                        # set the border to red
                        sd.mainWidget.setStyleSheet('Frame { border: 3px solid #FF1234; }')
                        sd.mainWidget.setEnabled(False)
                        strp.setEnabled(False)

                        getLogger().error(f'Strip {strp} contains bad axes - please close SpectrumDisplay {sd} outlined in red.')

        except Exception as es:
            getLogger().warning(f'There was an issue checking the spectrumDisplays')

        # don't need to call super here
        return project

    def _close(self):
        self.close()

    def close(self):
        """Clean up the wrapper project previous to deleting or replacing
        Cleanup includes wrapped data graphics objects (e.g. Window, Strip, ...)
        """
        getLogger().info("Closing %s" % self.path)

        # close any spectra
        for sp in self.spectra:
            sp._close()

        # Remove undo stack:
        self._resetUndo(maxWaypoints=0)

        apiIo.cleanupProject(self)
        self._clearAllApiNotifiers()
        self.deleteAllNotifiers()
        for tag in ('_data2Obj', '_pid2Obj'):
            getattr(self, tag).clear()
            # delattr(self,tag)
        # del self._wrappedData
        self.__dict__.clear()

    def __repr__(self):
        """String representation"""
        if self.isDeleted:
            return "<Project:%s, isDeleted=True>" % self.name
        else:
            return "<Project:%s>" % self.name

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

    # _uniqueId: Some classes require a unique identifier per class
    # use _uniqueId property defined in AbstractWrapperObject; values are maintained for project instance
    def _queryNextUniqueIdValue(self, className) -> int:
        """query the next uniqueId for class className; does not increment its value
        CCPNINTERNAL: used in NmrAtom on _uniqueName
        """
        # _nextUniqueIdValues = {}    # a (className, nexIdValue) dictionary
        if not hasattr(self._wrappedData, '_nextUniqueIdValues'):
            setattr(self._wrappedData, '_nextUniqueIdValues', {})
        if self._wrappedData._nextUniqueIdValues is None:
            self._wrappedData._nextUniqueIdValues = {}

        nextUniqueId = self._wrappedData._nextUniqueIdValues.setdefault(className, 0)
        return nextUniqueId

    def _getNextUniqueIdValue(self, className) -> int:
        """Get the next uniqueId for class className; increments its value
        CCPNINTERNAL: used in AbstractWrapper on __init__
        """
        nextUniqueId = self._queryNextUniqueIdValue(className)
        self._wrappedData._nextUniqueIdValues[className] += 1
        return nextUniqueId

    def _setNextUniqueIdValue(self, className, value):
        """Set the next uniqueId for class className
        CCPNINTERNAL: should only be used in _restoreObject or Nef
        """
        self._queryNextUniqueIdValue(className)
        self._wrappedData._nextUniqueIdValues[className] = int(value)

    @property
    def _parent(self) -> AbstractWrapperObject:
        """Parent (containing) object."""
        return None

    def save(self, newPath: str = None, changeBackup: bool = True,
             createFallback: bool = False, overwriteExisting: bool = False,
             checkValid: bool = False, changeDataLocations: bool = False) -> bool:
        """Save project with all data, optionally to new location or with new name.
        Unlike lower-level functions, this function ensures that data in high level caches are saved.
        Return True if save succeeded otherwise return False (or throw error)
        """
        # self._flushCachedData()

        # Update the spectrum internal settings
        for spectrum in self.spectra:
            spectrum._saveObject()

        # path is empty for save under the same name
        if newPath:
            # check validity of the newPath
            newPath = aPath(newPath)
            newPath.assureSuffix(CCPN_EXTENSION)
            if newPath.exists() and not overwriteExisting:
                raise ValueError('Cannot overwrite existing file "%s"' % newPath)
            path = str(newPath)
            if len(path) > 1024:
                raise ValueError('There is a limit (1024) to the length of the path (%s)' % path)
            _saveAs = True
        else:
            path = str(self.path)
            _saveAs = False

        try:
            apiStatus = self._getAPIObjectsStatus()
            if apiStatus.invalidObjects:
                # if deleteInvalidObjects:
                # delete here ...
                # run save and apiStatus again. Ensure nothing else has been compromised on the deleting process
                # else:
                errorMsg = '\n '.join(apiStatus.invalidObjectsErrors)
                getLogger().critical('Found compromised items. Project might be left in an invalid state. %s' % errorMsg)
                # raise ValueError(error)
        except Exception as es:
            getLogger().warning('Error checking project status: %s' % str(es))

        # don't check valid inside this routine as it is not optimised and only results in a crash. Use apiStatus object.
        savedOk = apiIo.saveProject(self._wrappedData.root, newPath=path,
                                    changeBackup=changeBackup, createFallback=createFallback,
                                    overwriteExisting=overwriteExisting, checkValid=False,
                                    changeDataLocations=changeDataLocations)
        if savedOk:
            self._resetIds()
            # check for application and Gui; might not yet be there (e.g. on save of converted V2
            # project)
            if self.application and self.application.hasGui:
                self.application.mainWindow.sideBar.setProjectName(self)

            # store the version history in state sub-folder json file
            if _saveAs:
                self._checkProjectSubDirectories()
                # create a new save history
                self._saveHistory = newProjectSaveHistory(path)
            else:
                # find the old history or create a new one
                self._saveHistory = fetchProjectSaveHistory(path)

            # add a new record
            self._saveHistory.addSaveRecord().save()

        return savedOk

    @property
    def name(self) -> str:
        """name of Project"""
        return self._wrappedData.root.name

    @property
    def path(self) -> str:
        """return absolute path to directory containing Project
        """
        return apiIo.getRepositoryPath(self._wrappedData.root, 'userData')

    @logCommand('project.')
    def deleteObjects(self, *objs: typing.Sequence[typing.Union[str, Pid.Pid, AbstractWrapperObject]]):
        """Delete one or more objects, given as either objects or Pids
        """
        getByPid = self.getByPid
        objs = [getByPid(x) if isinstance(x, str) else x for x in objs]

        with undoBlockWithoutSideBar():
            for obj in objs:
                if obj and not obj.isDeleted:
                    obj.delete()

    @property
    def _apiNmrProject(self) -> ApiNmrProject:
        """API equivalent to object: NmrProject"""
        return self._wrappedData

    # Undo machinery
    @property
    def _undo(self):
        """undo stack for Project. Implementation attribute"""

        try:
            result = self._wrappedData.root._undo
        except:
            result = None

        return result

    def _resetUndo(self, maxWaypoints: int = Undo.MAXUNDOWAYPOINTS,
                   maxOperations: int = Undo.MAXUNDOOPERATIONS,
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

    def _getReferenceExperimentFromType(self, value) -> Optional[RefExperiment]:
        """Search for a reference experiment matching name
        """
        if value is None:
            return

        # nmrExpPrototype = self._wrappedData.root.findFirstNmrExpPrototype(name=value) # Why not findFirst instead of looping all sortedNmrExpPrototypes
        for nmrExpPrototype in self._wrappedData.root.sortedNmrExpPrototypes():
            for refExperiment in nmrExpPrototype.sortedRefExperiments():
                if refExperiment.name == value:
                    return refExperiment

    @property
    def shiftAveraging(self):
        """Return shiftAveraging
        """
        return self._wrappedData.shiftAveraging

    @shiftAveraging.setter
    def shiftAveraging(self, value):
        """Set shiftAveraging
        """
        if not isinstance(value, bool):
            raise TypeError('shiftAveraging must be True/False')

        self._wrappedData.shiftAveraging = value

    #===========================================================================================
    #  Notifiers system
    #
    # Old, API-level functions:
    #
    #===========================================================================================

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

    #===========================================================================================
    #  Notifiers system
    #
    # New notifier system (Free for use in application code):
    #
    #===========================================================================================

    def registerNotifier(self, className: str, target: str, func: typing.Callable[..., None],
                         parameterDict: dict = {}, onceOnly: bool = False) -> typing.Callable[..., None]:
        """
        Register notifiers to be triggered when data change

        :param str className: className of wrapper class to monitor (AbstractWrapperObject for 'all')

        :param str target: can have the following values

          *'create'* is called after the creation (or undeletion) of the object and its wrapper.
          Notifier functions are called with the created V3 core object as the only parameter.

          *'delete'* is called before the object is deleted
          Notifier functions are called with the deleted to be deleted V3 core object as the only
          parameter.

          *'rename'* is called after the id and pid of an object has changed
          Notifier functions are called with the renamed V3 core object and the old pid as parameters.

          *'change'* when any object attribute changes value.
          Notifier functions are called with the changed V3 core object as the only parameter.
          rename and crosslink notifiers (see below) may also trigger change notifiers.

          Any other value is interpreted as the name of a V3 core class, and the notifier
          is triggered when a cross link (NOT a parent-child link) between the className and
          the target class is modified

        :param Callable func: The function to call when the notifier is triggered.

          for actions 'create', 'delete' and 'change' the function is called with the object
          created (deleted, undeleted, changed) as the only parameter

          For action 'rename' the function is called with an additional parameter: oldPid,
          the value of the pid before renaming.

          If target is a second className, the function is called with the project as the only
          parameter.

        :param dict parameterDict: Parameters passed to the notifier function before execution.

          This allows you to use the same function with different parameters in different contexts

        :param bool onceOnly: If True, only one of multiple copies is executed

          when notifiers are resumed after a suspension.

        :return The registered notifier (which can be passed to removeNotifier or duplicateNotifier)

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
        if self.application.hasGui:
            self.application.ui.qtApp.progressAboutToChangeSignal.emit(self._progressSuspension)
        self._progressSuspension += 1

        return
        # TODO suspension temporarily disabled
        self._notificationSuspension += 1

    def resumeNotification(self):
        """Execute accumulated notifiers and resume immediate notifier execution"""
        self._progressSuspension -= 1
        if self._progressSuspension < 0:
            raise RuntimeError("Code Error: _progressSuspension below zero")
        if self.application.hasGui:
            self.application.ui.qtApp.progressChangedSignal.emit(self._progressSuspension)

        return

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

                    # check whether the match pair, (function, object) is in the found set
                    matchNotifier = (notifier, notification[2])
                    if matchNotifier not in scheduledNotifiers:
                        scheduledNotifiers.add(matchNotifier)

                        # append the function call (function, object, *params)
                        executeNotifications.append((notifier, notification[2:]))

                    # if notifier not in scheduledNotifiers:
                    #     scheduledNotifiers.add(notifier)
                    #     executeNotifications.append((notifier, notification[2:]))
                else:
                    executeNotifications.append((notifier, notification[2:]))
            #
            for notifier, params in reversed(executeNotifications):
                notifier(*params)

    # Standard notified functions.
    # RESTRICTED. Use in core classes ONLY

    def _startDeleteCommandBlock(self, *allWrappedData):
        """Call startCommandBlock for wrapper object delete. Implementation only

        If commented: _activateApiNotifier fails

        Used by the preset Api notifiers populated for self._apiNotifiers;
        have _newApiObject, _startDeleteCommandBlock, _finaliseApiDelete, _endDeleteCommandBlock, _finaliseApiUnDelete
        and _modifiedApiObject for each V3 class
        Initialised from _linkWrapperObjects in AbstractWrapperObject.py:954
        """

        undo = self._undo
        if undo is not None:
            # set undo step
            undo.newWaypoint()  # DO NOT CHANGE THIS
            undo.increaseWaypointBlocking()

            # self.suspendNotification()

    def _endDeleteCommandBlock(self, *dummyWrappedData):
        """End block for delete command echoing

        MUST be paired with _startDeleteCommandBlock call - use try ... finally to ensure both are called
        """
        undo = self._undo
        if undo is not None:
            # self.resumeNotification()
            undo.decreaseWaypointBlocking()

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
        if self._apiNotificationBlanking == 0:
            obj = self._data2Obj[wrappedData]
            obj._finaliseAction('change')

    def _finaliseApiDelete(self, wrappedData):
        """Clean up after object deletion
        """
        if not wrappedData.isDeleted:
            raise ValueError("_finaliseApiDelete called before wrapped data are deleted: %s" % wrappedData)

        # get object
        obj = self._data2Obj.get(wrappedData)
        if not obj:
            # NOTE:ED - it shouldn't get here but occasionally it does :|
            getLogger().warning(f'_finaliseApiDelete: no V3 object for {wrappedData}')

        else:
            # obj._finaliseAction('delete')  # GWV: 20181127: now as notify('delete') decorator on delete method

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

        # oldWrapperObject._finaliseAction('create')  # EJB: 20211119: now as notify('delete') decorator on delete method

    def _notifyRelatedApiObject(self, wrappedData, pathToObject: str, action: str):
        """ call 'action' type notifiers for getattribute(pathToObject)(wrappedData)
        pathToObject is a navigation path (may contain dots) and must yield an API object
        or an iterable of API objects"""

        if self._apiNotificationBlanking == 0:
            getDataObj = self._data2Obj.get

            target = operator.attrgetter(pathToObject)(wrappedData)

            # GWV: a bit too much for now; should be the highest debug level only
            #self._project._logger.debug('%s: %s.%s = %s'
            #                            % (action, wrappedData, pathToObject, target))

            if not target:
                pass
            elif hasattr(target, '_metaclass'):
                if not target.isDeleted:
                    # Hack. This is an API object - only if exists
                    getDataObj(target)._finaliseAction(action)
            else:
                # This must be an iterable
                for obj in target:
                    if not obj.isDeleted:
                        getDataObj(obj)._finaliseAction(action)

    # def _finaliseApiRename(self, wrappedData):
    #     """Reset Finalise rename - called from API object (for API notifiers)
    #     """
    #     # Should be handled by decorators
    #     if self._apiNotificationBlanking == 0:
    #         getLogger().debug2(f'***   SHOULD THIS BE CALLED? {self._data2Obj.get(wrappedData)}')
    #         # obj = self._data2Obj.get(wrappedData)
    #         # obj._finaliseAction('rename')

    def _finalisePid2Obj(self, obj, action):
        """New/Delete object to the general dict for v3 pids
        """
        # update pid:object mapping dictionary
        dd = self._pid2Obj.setdefault(obj.className, self._pid2Obj.setdefault(obj.shortClassName, {}))

        # set/delete on action
        if action == 'create':
            dd[obj.id] = obj
        elif action == 'delete':
            # should never fail
            del dd[obj.id]

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
        # if False and self._notificationSuspension:
        #     ll = self._pendingNotifications
        #     for dd in iterator:
        #         for notifier, onceOnly in dd.items():
        #             ll.append((notifier, onceOnly, self))
        # else:

        for dd in iterator:
            for notifier in dd:
                notifier(self)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Library functions
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _updateApiDataUrl(self, path):
        """Update the data url to path; for legacy purposes
        """
        # Reset remoteData DataStores to match path
        if path is None or len(path) == 0:
            getLogger().debug('_updateApiDataUrl: invalid path %r' % path)
            return
        path = aPath(path)
        if not path.exists():
            getLogger().debug('_updateApiDataUrl: path %r does not exist' % path)
            return

        memopsRoot = self._wrappedData.root
        dataUrl = memopsRoot.findFirstDataLocationStore(name='standard').findFirstDataUrl(
                name='remoteData'
                )
        dataUrl.url = Implementation.Url(path=str(path.as_posix()))

    def _getAPIObjectsStatus(self, completeScan=False, includeDefaultChildren=False):
        """
        Scan all API objects and check their validity.

        Parameters:
        completeScan: bool, True to perform a complete validity check of all found API objects
        includeDefaultChildren: bool, False to exclude default objects for inspection such as
                                ChemComps and associated, nmrExpPrototypes etc.See _APIStatus._excludedChildren
                                for the full list of exclusions.

        Return: the API Status object. See _APIStatus for full description

        """
        getLogger().info('Validating Project integrity...')
        from ccpn.core._implementation.APIStatus import APIStatus

        root = self._apiNmrProject.root
        apiStatus = APIStatus(apiObj=root, completeScan=completeScan, includeDefaultChildren=includeDefaultChildren)
        return apiStatus

    def _update(self):
        """Call the _updateObject method on all objects, including self
        """
        self._updateObject(UPDATE_POST_PROJECT_INITIALISATION)
        objs = self._getAllDecendants()
        for obj in objs:
            obj._updateObject(UPDATE_POST_PROJECT_INITIALISATION)

    @logCommand('project.')
    def exportNef(self, path: str = None,
                  overwriteExisting: bool = False,
                  skipPrefixes: typing.Sequence[str] = (),
                  expandSelection: bool = True,
                  includeOrphans: bool = False,
                  pidList: typing.Sequence[str] = None):
        """
        Export selected contents of the project to a Nef file.

        skipPrefixes: ( 'ccpn', ..., <str> )
        expandSelection: <bool>
        includeOrphans: <bool>

        Include 'ccpn' in the skipPrefixes list will exclude ccpn specific items from the file
        expandSelection = True      will include all data from the project, this may not be data that
                                    is not defined in the Nef standard.
        includeOrphans = True       will include chemicalShifts that have no peak assignments (orphans)

        PidList is a list of <str>, e.g. 'NC:@-', obtained from the objects to be included.
        The Nef file may also contain further dependent items associated with the pidList.

        :param path: output path and filename
        :param skipPrefixes: items to skip
        :param expandSelection: expand the selection
        :param includeOrphans: include chemicalShift orphans
        :param pidList: a list of pids
        """
        from ccpn.framework.lib.ccpnNef import CcpnNefIo

        with undoBlock():
            with notificationBlanking():
                CcpnNefIo.exportNef(self, path,
                                    overwriteExisting=overwriteExisting,
                                    skipPrefixes=skipPrefixes,
                                    expandSelection=expandSelection,
                                    includeOrphans=includeOrphans,
                                    pidList=pidList)

    @staticmethod
    def isCoreObject(obj) -> bool:
        """Return True if obj is a core ccpn object
        """
        return isinstance(obj, (AbstractWrapperObject, V3CoreObjectABC))

    @staticmethod
    def isCoreClass(klass) -> bool:
        """Return True if type(klass) is a core ccpn object type
        """
        return isinstance(klass, type) and issubclass(klass, (AbstractWrapperObject, V3CoreObjectABC))

    #===========================================================================================
    # Data loaders
    #===========================================================================================

    def loadData(self, path: (str, Path)) -> list:
        """Just a stub for backward compatibility
        """
        return self.application.loadData(path)

    def _loadFastaFile(self, path: (str, Path)) -> list:
        """Load Fasta sequence(s) from file into Wrapper project
        CCPNINTERNAL: called from FastDataLoader
        """
        with logCommandManager('application.', 'loadData', path):
            sequences = fastaIo.parseFastaFile(path)
            chains = []
            for sequence in sequences:
                newChain = self.createChain(sequence=sequence[1], compoundName=sequence[0],
                                            molType='protein')
                chains.append(newChain)

        return chains

    def _loadPdbFile(self, path: (str, Path)) -> list:
        """Load data from pdb file path into new StructureEnsemble object(s)
        CCPNINTERNAL: called from pdb dataLoader
        """
        from ccpn.util.StructureData import EnsembleData, averageStructure

        with logCommandManager('application.', 'loadData', path):
            path = aPath(path)
            name = path.basename

            ensemble = EnsembleData.from_pdb(str(path))
            se = self.newStructureEnsemble(name=name, data=ensemble)

            # create a new ensemble-average in a dataTable
            dTable = self.newDataTable(name=f'{name}-average', data=averageStructure(ensemble))
            dTable.setMetadata('structureEnsemble', se.pid)

        return [se]

    def _loadTextFile(self, path: (str, Path)) -> list:
        """Load text from file path into new Note object
        CCPNINTERNAL: called from text dataLoader
        """
        with logCommandManager('application.', 'loadData', path):
            path = aPath(path)
            name = path.basename

            with path.open('r') as fp:
                # cannot do read() as we want one string
                text = ''.join(line for line in fp.readlines())
            note = self.newNote(name=name, text=text)
        return [note]

    def _loadLayout(self, path: (str, Path), subType: str):
        # this is a GUI only function call. Please move to the appropriate location on 3.1
        self.application._restoreLayoutFromFile(path)

    def _loadExcelFile(self, path: (str, Path)) -> list:
        """Load data from a Excel file.
        :returns list of loaded objects (awaiting adjust ment of excelReader)
        CCPNINTERNAL: used in Excel data loader
        """

        with logCommandManager('application.', 'loadData', path):
            with undoBlock():
                reader = ExcelReader(project=self, excelPath=str(path))
                result = reader.load()
        return result

    #===========================================================================================
    # End data loaders
    #===========================================================================================

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

    def getObjectsById(self, className: str, id: str) -> typing.List[AbstractWrapperObject]:
        """get objects from class name / shortName and the start of the ID.

        The function does NOT interrogate the API level, which makes it faster in a
        number fo cases, e.g. for NmrResidues"""

        dd = self._pid2Obj.get(className)
        if dd:
            # NB the _pid2Obj entry is set in the object init.
            # The relevant dictionary may therefore be missing if no object has yet been created
            result = [tt[1] for tt in dd.items() if tt[0] == id]
        else:
            result = None
        #
        return result

    def getObjectsByPids(self, pids: Iterable, objectTypes: tuple = None):
        """Optimise method to get all found objects from a list of pids. Remove any None.
        Warning: do not use with zip
        Specify objectTypes to only return objects of the required type, otherwise all objects returned, defaults to None
        """

        if not isinstance(pids, Iterable):
            raise ValueError(f'{self.__class__.__name__}.getObjectsByPids: pids argument must be an iterable')
        if not isinstance(objectTypes, (type, type(None))) and \
                not (isinstance(objectTypes, tuple) and all(isinstance(obj, (type, type(None))) for obj in objectTypes)):
            raise ValueError(f'{self.__class__.__name__}.getObjectsByPids: objectTypes must be a type, tuple of types, or None')

        if objectTypes:
            return list(filter(lambda obj: isinstance(obj, objectTypes), map(lambda x: self.getByPid(x) if isinstance(x, str) else x, pids)))
        else:
            return list(filter(None, map(lambda x: self.getByPid(x) if isinstance(x, str) else x, pids)))

    def getByPids(self, pids: list):
        """Optimise method to get all found objects from a list of pids. Remove any None.
        """
        objs = [self.getByPid(pid) if isinstance(pid, str) else pid for pid in pids]
        return list(filter(lambda obj: self.isCoreObject(obj), objs))

    def getPidsByObjects(self, objs: list):
        """Optimise method to get all found pids from a list of objects. Remove any None.
         Warning: do not use with zip"""
        return list(filter(None, map(lambda x: x.pid if isinstance(x, AbstractWrapperObject) else None, objs)))

    def getCcpCodeData(self, ccpCode, molType=None, atomType=None):
        """Get the CcpCode for molType/AtomType
        """
        from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import getCcpCodeData

        return getCcpCodeData(self._apiNmrProject, ccpCode, molType='protein', atomType=atomType)

    # def packageProject(self, filePrefix, includeBackups=True, includeLogs=True):
    #     """Package the project
    #     """
    #     from ccpnmodel.ccpncore.lib.Io import Api as apiIo
    #
    #     return apiIo.packageProject(self._wrappedData.parent, filePrefix,
    #                                 includeBackups=includeBackups, includeLogs=includeLogs)

    @logCommand('project.')
    def saveToArchive(self) -> Path:
        """Make new time-stamped archive of project
        :return path to .tgz archive file as a Path object
        """
        from ccpn.core.lib.ProjectArchiver import ProjectArchiver

        archiver = ProjectArchiver(projectPath=self.path)
        archivePath = archiver.makeArchive()
        getLogger().info('==> Project archived to %s' % archivePath)
        return archivePath

    def _getArchivePaths(self) -> List[Path]:
        """:return list of archives from archive directory
        CCPNINTERAL: used in GuiMainWindow
        """
        from ccpn.core.lib.ProjectArchiver import ProjectArchiver

        archiver = ProjectArchiver(projectPath=self.project.path)
        return archiver.archives

    def getExperimentClassifications(self) -> dict:
        """Get a dictionary of dictionaries of dimensionCount:sortedNuclei:ExperimentClassification named tuples.
        """
        # NOTE:ED - better than being in spectrumLib but still needs moving
        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import getExpClassificationDict

        return getExpClassificationDict(self._wrappedData)

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    def newMark(self, colour: str, positions: Sequence[float], axisCodes: Sequence[str],
                style: str = 'simple', units: Sequence[str] = (), labels: Sequence[str] = ()):
        """
        To be depreciated in next version; use mainWindow.newMark() instead
        """

        return self.application.mainWindow.newMark(colour=colour, positions=positions,
                                                   axisCodes=axisCodes, style=style,
                                                   units=units, labels=labels)

    @logCommand('project.')
    def newSpectrum(self, path: str, name: str = None):
        """Creation of new Spectrum defined by path; optionally set name.
        """
        from ccpn.core.Spectrum import _newSpectrum

        return _newSpectrum(self, path=path, name=name)

    # @logCommand('project.')
    # def createDummySpectrum(self, axisCodes: Sequence[str], name=None, chemicalShiftList=None):
    #     """
    #     Make dummy spectrum from isotopeCodes list - without data and with default parameters.
    #
    #     :param axisCodes:
    #     :param name:
    #     :param chemicalShiftList:
    #     :return: a new Spectrum instance.
    #     """
    #     raise NotImplementedError('Use Project.newEmptySpectrum')

    @logCommand('project.')
    def newEmptySpectrum(self, isotopeCodes: Sequence[str], dimensionCount=None, name='emptySpectrum', path=None,
                         **parameters):
        """
        Make new Empty spectrum from isotopeCodes list - without data and with default parameters.
        default parameters are defined in: SpectrumDataSourceABC.isotopeDefaultDataDict

        :param isotopeCodes: a tuple/list of isotope codes that define the dimensions; e.g. ('1H', '13C')
        :dimensionCount: an optional dimensionCount parameter; default derived from len(isotopeCodes)
        :param name: the name of the resulting spectrum
        :param path: an optional path to be stored with the Spectrum instance
        :param **parameters: optional spectrum (parameter, value) pairs
        :return: a new Spectrum instance.
        """
        from ccpn.core.Spectrum import _newEmptySpectrum

        return _newEmptySpectrum(self, isotopeCodes=isotopeCodes, dimensionCount=dimensionCount,
                                 name=name, path=path, **parameters)

    @logCommand('project.')
    def newHdf5Spectrum(self, isotopeCodes: Sequence[str], name='hdf5Spectrum', path=None, **parameters):
        """
        Make new hdf5 spectrum from isotopeCodes list - without data and with default parameters.

        :param isotopeCodes:
        :param name: name of the spectrum
        :param path: optional path (autogenerated from name when None; resulting file will be in
                     data/spectra folder of the project)
        :param **parameters: optional spectrum (parameter, value) pairs
        :return: a new Spectrum instance.
        """
        from ccpn.core.Spectrum import _newHdf5Spectrum

        return _newHdf5Spectrum(self, isotopeCodes=isotopeCodes, name=name, path=path, **parameters)

    @logCommand('project.')
    def newNmrChain(self, shortName: str = None, isConnected: bool = False, label: str = '?',
                    comment: str = None):
        """Create new NmrChain. Setting isConnected=True produces a connected NmrChain.

        :param str shortName: shortName for new nmrChain (optional, defaults to '@ijk' or '#ijk',  ijk positive integer
        :param bool isConnected: (default to False) If true the NmrChain is a connected stretch. This can NOT be changed later
        :param str label: Modifiable NmrChain identifier that does not change with reassignment. Defaults to '@ijk'/'#ijk'
        :param str comment: comment for new nmrChain (optional)
        :return: a new NmrChain instance.
        """
        from ccpn.core.NmrChain import _newNmrChain

        return _newNmrChain(self, shortName=shortName, isConnected=isConnected,
                            label=label, comment=comment)

    @logCommand('project')
    def fetchNmrChain(self, shortName: str = None):
        """Fetch chain with given shortName; If none exists call newNmrChain to make one first

        If shortName is None returns a new NmrChain with name starting with '@'

        :param shortName: string name of required nmrAtom
        :return: an NmrChain instance.
        """
        from ccpn.core.NmrChain import _fetchNmrChain

        return _fetchNmrChain(self, shortName=shortName)

    @logCommand('project.')
    def produceNmrAtom(self, atomId: str = None, chainCode: str = None,
                       sequenceCode: Union[int, str] = None,
                       residueType: str = None, name: str = None):
        """Get chainCode, sequenceCode, residueType and atomName from dot-separated atomId or Pid
            or explicit parameters, and find or create an NmrAtom that matches
            Empty chainCode gets NmrChain:@- ; empty sequenceCode get a new NmrResidue

        :param atomId:
        :param chainCode:
        :param sequenceCode:
        :param residueType:
        :param name: new or existing nmrAtom, matching parameters
        :return:
        """
        from ccpn.core.NmrAtom import _produceNmrAtom

        return _produceNmrAtom(self, atomId=atomId, chainCode=chainCode,
                               sequenceCode=sequenceCode, residueType=residueType, name=name)

    @logCommand('project.')
    def newNote(self, name: str = None, text: str = None, comment: str = None, **kwds):
        """Create new Note.

        See the Note class for details.

        Optional keyword arguments can be passed in; see Note._newNote for details.

        :param name: name for the note.
        :param text: contents of the note.
        :return: a new Note instance.
        """
        from ccpn.core.Note import _newNote

        return _newNote(self, name=name, text=text, comment=comment, **kwds)

    @logCommand('project.')
    def newWindow(self, title: str = None, position: tuple = (), size: tuple = (), **kwds):
        """Create new child Window.

        See the Window class for details.

        Optional keyword arguments can be passed in; see Window._newWindow for details.

        :param str title: window  title (optional, defaults to 'W1', 'W2', 'W3', ...
        :param tuple position: x,y position for new window in integer pixels.
        :param tuple size: x,y size for new window in integer pixels.
        :return: a new Window instance.
        """
        from ccpn.ui._implementation.Window import _newWindow

        return _newWindow(self, title=title, position=position, size=size, **kwds)

    @logCommand('project.')
    def newStructureEnsemble(self, name: str = None, data=None, comment: str = None, **kwds):
        """Create new StructureEnsemble.

        See the StructureEnsemble class for details.

        Optional keyword arguments can be passed in; see StructureEnsemble._newStructureEnsemble for details.

        :param name: new name for the StructureEnsemble.
        :param data: Pandas dataframe.
        :param comment: optional comment string
        :return: a new StructureEnsemble instance.
        """
        from ccpn.core.StructureEnsemble import _newStructureEnsemble

        return _newStructureEnsemble(self, name=name, data=data, comment=comment, **kwds)


    def newDataTable(self, name: str = None, data=None, comment: str = None, **kwds):
        """Create new DataTable.

        See the DataTable class for details.

        Optional keyword arguments can be passed in; see DataTable._newDataTable for details.

        :param name: new name for the DataTable.
        :param data: Pandas dataframe.
        :param comment: optional comment string
        :return: a new DataTable instance.
        """
        from ccpn.core.DataTable import _newDataTable
        getLogger().info(f'project.newDataTable(name={name})') # don't log the full dataFrame. is not needed! Add exclusions on Decorator logCommand
        return _newDataTable(self, name=name, data=data, comment=comment, **kwds)

    @logCommand('project.')
    def fetchDataTable(self, name: str):
        """Get or create new DataTable.
        :param name: name for the DataTable.
        """
        from ccpn.core.DataTable import _fetchDataTable

        return _fetchDataTable(self, name=name)

    @logCommand('project.')
    def _newPeakCluster(self, peaks: Sequence[Union['Peak', str]] = None, **kwds) -> Optional['_PeakCluster']:
        """Create new PeakCluster.

        See the PeakCluster class for details.

        Optional keyword arguments can be passed in; see PeakCluster._newPeakCluster for details.

        CCPN Internal - this object is deprecated.

        :param peaks: optional list of peaks as objects or pids.
        :return: a new PeakCluster instance.
        """
        from ccpn.core._implementation._PeakCluster import _newPeakCluster

        return _newPeakCluster(self, peaks=peaks, **kwds)

    @logCommand('project.')
    def newCollection(self, items: Sequence[typing.Any] = None, **kwds) -> Optional['Collection']:
        """Create new Collection.

        See the Collection class for details.

        Optional keyword arguments can be passed in; see Collection._newCollection for details.

        :param items: optional list of core objects as objects or pids.
        :return: a new Collection instance.
        """
        return self._collectionList.newCollection(items=items, **kwds)

    @logCommand('project.')
    def newSample(self, name: str = None, pH: float = None, ionicStrength: float = None,
                  amount: float = None, amountUnit: str = None, isVirtual: bool = False, isHazardous: bool = None,
                  creationDate: datetime = None, batchIdentifier: str = None, plateIdentifier: str = None,
                  rowNumber: int = None, columnNumber: int = None, comment: str = None, **kwds):
        """Create new Sample.

        See the Sample class for details.

        Optional keyword arguments can be passed in; see Sample._newSample for details.

        :param name:
        :param pH:
        :param ionicStrength:
        :param amount:
        :param amountUnit:
        :param isVirtual:
        :param isHazardous:
        :param creationDate:
        :param batchIdentifier:
        :param plateIdentifier:
        :param rowNumber:
        :param columnNumber:
        :param comment:
        :param serial: optional serial number.
        :return: a new Sample instance.
        """
        from ccpn.core.Sample import _newSample

        return _newSample(self, name=name, pH=pH, ionicStrength=ionicStrength,
                          amount=amount, amountUnit=amountUnit, isVirtual=isVirtual, isHazardous=isHazardous,
                          creationDate=creationDate, batchIdentifier=batchIdentifier, plateIdentifier=plateIdentifier,
                          rowNumber=rowNumber, columnNumber=columnNumber, comment=comment, **kwds)

    @logCommand('project.')
    def fetchSample(self, name: str):
        """Get or create Sample with given name.
        See the Sample class for details.
        :param self: project
        :param name: sample name
        :return: new or existing Sample instance.
        """
        from ccpn.core.Sample import _fetchSample

        return _fetchSample(self, name)

    @logCommand('project.')
    def newStructureData(self, name: str = None, title: str = None, programName: str = None, programVersion: str = None,
                         dataPath: str = None, creationDate: datetime = None, uuid: str = None,
                         comment: str = None, moleculeFilePath: str = None, **kwds):
        """Create new StructureData

        See the StructureData class for details.

        Optional keyword arguments can be passed in; see StructureData._newStructureData for details.

        :param title: deprecated - original name for StructureData, please use .name
        :param name:
        :param programName:
        :param programVersion:
        :param dataPath:
        :param creationDate:
        :param uuid:
        :param comment:
        :return: a new StructureData instance.
        """
        from ccpn.core.StructureData import _newStructureData

        return _newStructureData(self, name=name, title=title, programName=programName, programVersion=programVersion,
                                 dataPath=dataPath, creationDate=creationDate, uuid=uuid, comment=comment,
                                 moleculeFilePath=moleculeFilePath, **kwds)

    @logCommand('project.')
    def newSpectrumGroup(self, name: str, spectra=(), **kwds):
        """Create new SpectrumGroup

        See the SpectrumGroup class for details.

        Optional keyword arguments can be passed in; see SpectrumGroup._newSpectrumGroup for details.

        :param name: name for the new SpectrumGroup
        :param spectra: optional list of spectra as objects or pids
        :return: a new SpectrumGroup instance.
        """
        from ccpn.core.SpectrumGroup import _newSpectrumGroup

        return _newSpectrumGroup(self, name=name, spectra=spectra, **kwds)

    @logCommand('project.')
    def createChain(self, sequence: Union[str, Sequence[str]], compoundName: str = None,
                    startNumber: int = 1, molType: str = None, isCyclic: bool = False,
                    shortName: str = None, role: str = None, comment: str = None,
                    expandFromAtomSets: bool = True,
                    addPseudoAtoms: bool = True, addNonstereoAtoms: bool = True,
                    **kwds):
        """Create new chain from sequence of residue codes, using default variants.

        Automatically creates the corresponding polymer Substance if the compoundName is not already taken

        See the Chain class for details.

        Optional keyword arguments can be passed in; see Chain._createChain for details.

        :param Sequence sequence: string of one-letter codes or sequence of residue types
        :param str compoundName: name of new Substance (e.g. 'Lysozyme') Defaults to 'Molecule_n
        :param str molType: molType ('protein','DNA', 'RNA'). Needed only if sequence is a string.
        :param int startNumber: number of first residue in sequence
        :param str shortName: shortName for new chain (optional)
        :param str role: role for new chain (optional)
        :param str comment: comment for new chain (optional)
        :param bool expandFromAtomSets: Create new Atoms corresponding to the ChemComp AtomSets definitions.
                Eg. H1, H2, H3 equivalent atoms will add a new H% atom. This will facilitate assignments workflows.
                See ccpn.core.lib.MoleculeLib.expandChainAtoms for details.
        :return: a new Chain instance.
        """
        from ccpn.core.Chain import _createChain

        return _createChain(self, sequence=sequence, compoundName=compoundName,
                            startNumber=startNumber, molType=molType, isCyclic=isCyclic,
                            shortName=shortName, role=role, comment=comment,
                            expandFromAtomSets=expandFromAtomSets, addPseudoAtoms=addPseudoAtoms,
                            addNonstereoAtoms=addNonstereoAtoms, **kwds)

    @logCommand('project.')
    def newSubstance(self, name: str = None, labelling: str = None, substanceType: str = 'Molecule',
                     userCode: str = None, smiles: str = None, inChi: str = None, casNumber: str = None,
                     empiricalFormula: str = None, molecularMass: float = None, comment: str = None,
                     synonyms: typing.Sequence[str] = (), atomCount: int = 0, bondCount: int = 0,
                     ringCount: int = 0, hBondDonorCount: int = 0, hBondAcceptorCount: int = 0,
                     polarSurfaceArea: float = None, logPartitionCoefficient: float = None, **kwds):
        """Create new substance WITHOUT storing the sequence internally
        (and hence not suitable for making chains). SubstanceType defaults to 'Molecule'.

        ADVANCED alternatives are 'Cell' and 'Material'

        See the Substance class for details.

        Optional keyword arguments can be passed in; see Substance._newSubstance for details.

        :param name:
        :param labelling:
        :param substanceType:
        :param userCode:
        :param smiles:
        :param inChi:
        :param casNumber:
        :param empiricalFormula:
        :param molecularMass:
        :param comment:
        :param synonyms:
        :param atomCount:
        :param bondCount:
        :param ringCount:
        :param hBondDonorCount:
        :param hBondAcceptorCount:
        :param polarSurfaceArea:
        :param logPartitionCoefficient:
        :return: a new Substance instance.
        """
        from ccpn.core.Substance import _newSubstance

        return _newSubstance(self, name=name, labelling=labelling, substanceType=substanceType,
                             userCode=userCode, smiles=smiles, inChi=inChi, casNumber=casNumber,
                             empiricalFormula=empiricalFormula, molecularMass=molecularMass, comment=comment,
                             synonyms=synonyms, atomCount=atomCount, bondCount=bondCount,
                             ringCount=ringCount, hBondDonorCount=hBondDonorCount, hBondAcceptorCount=hBondAcceptorCount,
                             polarSurfaceArea=polarSurfaceArea, logPartitionCoefficient=logPartitionCoefficient, **kwds)

    @logCommand('project.')
    def fetchNefSubstance(self, sequence: typing.Sequence[dict], name: str = None, **kwds):
        """Fetch Substance that matches sequence of NEF rows and/or name

        See the Substance class for details.

        Optional keyword arguments can be passed in; see Substance._fetchNefSubstance for details.

        :param self:
        :param sequence:
        :param name:
        :return: a new Nef Substance instance.
        """
        from ccpn.core.Substance import _fetchNefSubstance

        return _fetchNefSubstance(self, sequence=sequence, name=name, **kwds)

    @logCommand('project.')
    def getNefSubstance(self, sequence: typing.Sequence[dict], name: str = None, **kwds):
        """Get existing Substance that matches sequence of NEF rows and/or name

        See the Substance class for details.

        Optional keyword arguments can be passed in; see Substance._fetchNefSubstance for details.

        :param self:
        :param sequence:
        :param name:
        :return: a new Nef Substance instance.
        """
        from ccpn.core.Substance import _getNefSubstance

        return _getNefSubstance(self, sequence=sequence, name=name, **kwds)

    @logCommand('project.')
    def createPolymerSubstance(self, sequence: typing.Sequence[str], name: str,
                               labelling: str = None, userCode: str = None, smiles: str = None,
                               synonyms: typing.Sequence[str] = (), comment: str = None,
                               startNumber: int = 1, molType: str = None, isCyclic: bool = False,
                               **kwds):
        """Make new Substance from sequence of residue codes, using default linking and variants

        NB: For more complex substances, you must use advanced, API-level commands.

        See the Substance class for details.

        Optional keyword arguments can be passed in; see Substance._fetchNefSubstance for details.

        :param Sequence sequence: string of one-letter codes or sequence of residueNames
        :param str name: name of new substance
        :param str labelling: labelling for new substance. Optional - None means 'natural abundance'
        :param str userCode: user code for new substance (optional)
        :param str smiles: smiles string for new substance (optional)
        :param Sequence[str] synonyms: synonyms for Substance name
        :param str comment: comment for new substance (optional)
        :param int startNumber: number of first residue in sequence
        :param str molType: molType ('protein','DNA', 'RNA'). Required only if sequence is a string.
        :param bool isCyclic: Should substance created be cyclic?
        :return: a new Substance instance.
        """
        from ccpn.core.Substance import _createPolymerSubstance

        return _createPolymerSubstance(self, sequence=sequence, name=name,
                                       labelling=labelling, userCode=userCode, smiles=smiles,
                                       synonyms=synonyms, comment=comment,
                                       startNumber=startNumber, molType=molType, isCyclic=isCyclic,
                                       **kwds)

    @logCommand('project.')
    def fetchSubstance(self, name: str, labelling: str = None):
        """Get or create Substance with given name and labelling.
        See the Substance class for details.

        :param self:
        :param name:
        :param labelling:
        :return: new or existing Substance instance.
        """
        from ccpn.core.Substance import _fetchSubstance

        return _fetchSubstance(self, name=name, labelling=labelling)

    @logCommand('project.')
    def newComplex(self, name: str, chains=(), **kwds):
        """Create new Complex.
        See the Complex class for details.
        Optional keyword arguments can be passed in; see Complex._newComplex for details.

        :param name:
        :param chains:
        :return: a new Complex instance.
        """
        from ccpn.core.Complex import _newComplex

        return _newComplex(self, name=name, chains=chains, **kwds)

    @logCommand('project.')
    def newChemicalShiftList(self, name: str = None, spectra=(), **kwds):
        """Create new ChemicalShiftList.
        See the ChemicalShiftList class for details.

        :param name:
        :param spectra:
        :return: a new ChemicalShiftList instance.
        """
        from ccpn.core.ChemicalShiftList import _newChemicalShiftList
        from ccpn.core.Spectrum import Spectrum

        if (result := _newChemicalShiftList(self, name=name, **kwds)):
            # needs to be here so that all chemicalShiftTables are notified correctly
            if spectra:
                getByPid = self._project.getByPid
                if (spectra := list(filter(lambda sp: isinstance(sp, Spectrum),
                                           map(lambda sp: getByPid(sp) if isinstance(sp, str) else sp, spectra)))):
                    # add/transfer the spectra
                    result.spectra = spectra

            return result

    @logCommand('project.')
    def getChemicalShiftList(self, name: str = None, **kwds):
        """Get existing ChemicalShiftList.
        See the ChemicalShiftList class for details.

        :param name:
        :return: a new ChemicalShiftList instance.
        """
        from ccpn.core.ChemicalShiftList import _getChemicalShiftList

        return _getChemicalShiftList(self, name=name, **kwds)

    def getCollection(self, name: str) -> Optional['Collection']:
        """Return the collection from the supplied name
        """
        from ccpn.core.Collection import _getCollection

        return _getCollection(self, name=name)

    @logCommand('project.')
    def fetchCollection(self, name: str = None) -> 'Collection':
        """Get or create Collection.
        See the Collection class for details.

        :param name:
        :return: a new Collection instance.
        """
        from ccpn.core.Collection import _fetchCollection

        return _fetchCollection(self, name=name)


#=========================================================================================
# Code adapted from prior _implementation/Io.py
#=========================================================================================

def _loadProject(application, path: str) -> Project:
    """Load the project defined by path
    :return Project instance
    """
    from ccpn.core._implementation.updates.update_v2 import updateProject_fromV2

    _path = aPath(path)
    if not _path.exists():
        raise ValueError(f'Path {_path} does not exist')

    if (apiProject := apiIo.loadProject(str(path), useFileLogger=True)) is None:
        raise RuntimeError("No valid project loaded from %s" % path)

    apiNmrProject = apiProject.fetchNmrProject()
    apiNmrProject.initialiseData()
    apiNmrProject.initialiseGraphicsData()
    project = Project(apiNmrProject)
    project._isNew = False
    # NB: linkages are set in Framework._initialiseProject()

    # If path pointed to a V2 project, save the result
    if project._isUpgradedFromV2:
        try:
            # call the update
            getLogger().info('==> Upgrading %s to version-3' % project)
            updateProject_fromV2(project)
            # Using api calls as V3-Project has not yet been fully instantiated
            apiProject.touch()
            apiProject.save()
            getLogger().info('==> Writing model data')
        except Exception as es:
            getLogger().warning('Failed upgrading %s (%s)' % (project, str(es)))

    else:
        # check if it has been moved
        projectPath = project.path
        oldName = project.name
        newName = aPath(projectPath).basename
        if oldName != newName:
            # Directory name has changed. Change project name and move Project xml file.
            oldProjectFilePath = aPath(ApiPath.getProjectFile(projectPath, oldName))
            if oldProjectFilePath.exists():
                oldProjectFilePath.removeFile()
            apiProject.__dict__['name'] = newName
            # Using api calls as V3-Project has not yet been fully instantiated
            apiProject.touch()
            apiProject.save()

    project._resetUndo(debug=application._debugLevel <= Logging.DEBUG2, application=application)

    # Do some admin
    # need project.path, as it may have changed; e.g. for a V2 project
    project._saveHistory = getProjectSaveHistory(project.path)

    # the initialisation is completed by Framework when it has done its things
    # project._initialiseProject()

    return project


def _newProject(application, name: str = 'default', path: str = None, overwrite=False) -> Project:
    """Make new project, putting underlying data storage (API project) at path
    :return Project instance
    """
    # apiIo.newProject will create a temp path if path is None
    if (apiProject := apiIo.newProject(name, path, overwriteExisting=overwrite, useFileLogger=True)) is None:
        raise RuntimeError("New project could not be created (overlaps exiting project?) name:%s, path:%s, overwrite:"
                           % (name, path, overwrite))

    apiNmrProject = apiProject.fetchNmrProject()
    apiNmrProject.initialiseData()
    apiNmrProject.initialiseGraphicsData()
    project = Project(apiNmrProject)
    project._isNew = True
    # NB: linkages are set in Framework._initialiseProject()

    project._objectVersion = application.applicationVersion

    project._resetUndo(debug=application._debugLevel <= Logging.DEBUG2, application=application)
    project._saveHistory = newProjectSaveHistory(project.path)

    # the initialisation is completed by Framework when it has done its things
    # project._initialiseProject()

    return project
