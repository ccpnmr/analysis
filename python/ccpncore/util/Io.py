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
"""Io-related utilities
"""

__author__ = 'rhf22'

import glob
import os
import shutil
import sys
import tempfile
# import time

from ccpncore.api.memops import Implementation
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.util import Path
from ccpncore.util import ApiPath
from ccpncore.util import Logging
from ccpncore.util import Common as commonUtil
from ccpncore.memops.ApiError import ApiError

# NBNB TBD this should be done by putting the function inside the class - later

from ccpncore.api.ccp.general.DataLocation import AbstractDataStore


printWarning = None

class DefaultIoHandler:
  """Class to handle interactions with user and logging
  Should be subclassed for actual functionality
  This default class simply does nothing"""

def _createLogger(project, applicationName=None, useFileLogger=None):
  
  if applicationName is None:
    applicationName = project._applicationName if hasattr(project, '_applicationName') else 'ccpn'
    
  if useFileLogger is None:
    useFileLogger = project._useFileLogger

  logger = Logging.createLogger(applicationName, project, stream=sys.stdout) if useFileLogger else Logging.getLogger()
  # # NBNB FIXME TBD temporary redirect to stdout for debug purposes
  # import sys
  # logger = Logging.createLogger(applicationName, project,
  #                               stream=sys.stdout) if useFileLogger else Logging.getLogger()
  project._applicationName = applicationName
  project._useFileLogger = useFileLogger
  project._logger = logger
  
  return logger
  
def newProject(projectName, path:str=None, overwriteExisting:bool=False,
               showYesNo:"function"=None, applicationName='ccpn',
               useFileLogger:bool=True) -> Implementation.MemopsRoot:
  """
  Create, and return, a new project using a specified path (directory).
  If path is not specified it takes the current working directory.
  The path can be either absolute or relative.
  The 'userData' repository is pointed to the path.
  The 'backup' repository is pointed to the path + '_backup'.
  If either of these paths already exist (either as files or as directories):

  If overwriteExisting:
    Delete the path
  Else if showYesNo:
    Ask the user if it is ok to delete the path
    If yes, delete.  If no return None.
  Else:
    Raise an IOError
  """

  # relies on knowing that repositories to move have these names, and these values for path suffix
  repositoryNameMap = {'userData': '', 'backup': '_backup'}

  if path:
    for name in repositoryNameMap.keys():
      fullPath = Path.joinPath(path, projectName) + repositoryNameMap[name]
      if not absentOrRemoved(Path.joinPath(fullPath, 'memops', 'Implementation'),
                             overwriteExisting, showYesNo):
        errMsg = 'Path ("%s") contains existing project.' % fullPath
        Logging.getLogger().warning(errMsg)
        raise Exception(errMsg)
    temporaryDirectory = None
  else:
    temporaryDirectory = tempfile.TemporaryDirectory(prefix='CcpnProject_')
    path = temporaryDirectory.name
    
  project = Implementation.MemopsRoot(name=projectName)
  
  if temporaryDirectory:
    project._temporaryDirectory = temporaryDirectory
  
  for name in repositoryNameMap.keys():
    fullPath = Path.normalisePath(Path.joinPath(path, projectName)
                             + repositoryNameMap[name], makeAbsolute=True)
    repository = project.findFirstRepository(name=name)
    repository.url = Implementation.Url(path=fullPath)

  # Reset DataLocations
  _initialiseStandardDataLocationStore(project)

  # NBNB PREFERENCES
  # Put here code to set remotedata location from preferences:
  #
  # remotePath = SOMETHING
  # obj = project.findFirstDataLocationStore(name='standard').findFirstDataUrl(name='remoteData')
  # obj.url = Implementation.Url(path=remotePath)

  # create logger
  logger = _createLogger(project, applicationName, useFileLogger)
  
  logger.info("Project is %s", project)

  return project

def absentOrRemoved(path:str, overwriteExisting:bool=False, showYesNo:"function"=None) -> bool:
  """Check if file is present, possibly removing it first.

  If path already exists:
    If overwriteExisting:
      Delete the path
      Return True
    Else if showYesNo:
      Ask the user if it is ok to delete the path
      If yes, delete and return True.  If no return False.
    Else:
      return False
  Else:
    Return True

  This function is not intended to be used outside this module but could be.
  """

  if os.path.exists(path):

    if overwriteExisting:
      Path.deletePath(path)
      return True

    elif showYesNo:
      if os.path.isdir(path):
        files = os.listdir(path)
        n = 5
        if len(files) > n:
          files = files[:n]
          files.append('...')
        ss = ', '.join(files)
        message = '%s already exists, remove it and all of its contents (%s) (if no, then no action taken)?' % (path, ss)
        if not showYesNo('Remove directory', message):
          return False
        else:
          Path.deletePath(path)
          return True
      else:
        message = '%s already exists (not as a directory), remove it?' % path
        if not showYesNo('Remove file', message):
          return False
        else:
          Path.deletePath(path)
          return True
    else:
      return False
  else:
    return True


def loadProject(path:str, projectName:str=None, askFile:"function"=None,
                askDir:"function"=None, suppressGeneralDataDir:bool=False,
                fixDataStores=True, applicationName='ccpn',
                useFileLogger:bool=True) -> Implementation.MemopsRoot:
  """
  Loads a project file and checks and deletes unwanted project repositories and
  changes the project repository path if the project has moved.  Returns the project.
  (The project repository path is effectively the userData repository.)
  askFile (if not None) has signature askFile(title, message, initial_value = '')
  askDir (if not None) has signature askDir(title, message, initial_value = '')
  Throws an IOError if there is an I/O error.
  Throws an ApiError if there is an API exception.
  """

  from ccpncore.memops.format.xml import XmlIO

  def isGeneralDataWriteable(generalDataRep):
    ppath = generalDataRep.url.path
    return commonUtil.isWindowsOS() or os.access(ppath, os.W_OK|os.X_OK)

  def isGeneralDataOk(proj):
    if suppressGeneralDataDir:
      return True
    generalDataRep = proj.findFirstRepository(name='generalData')
    if generalDataRep:
      return isGeneralDataWriteable(generalDataRep)
    return True

  path = Path.normalisePath(path, makeAbsolute=True)

  warningMessages = []

  # check if path exists and is directory
  if not os.path.exists(path):
    raise IOError('path "%s" does not exist' % path)
  if not os.path.isdir(path):
    raise IOError('path "%s" is not a directory' % path)

  projectFile = ApiPath.getProjectFile(path, projectName)

  if projectName:
    # projectName was specified so projectFile better exist
    if not os.path.exists(projectFile):
      raise IOError('project file "%s" does not exist' % projectFile)
  else:
    # projectName was not specified so default projectFile might not exist
    if not os.path.exists(projectFile):
      projectFiles = ApiPath.getPossibleProjectFiles(path)

      if len(projectFiles) == 0:
        raise IOError('"%s" contains no project file' % path)
      elif len(projectFiles) == 1:
        projectFile = projectFiles[0]
      elif askFile:
        projectFile = askFile('Select project file', 'Select project file', initial_value=projectFiles[0])
        if not projectFile: # cancelled
          raise IOError('Cancelled')
      else:
        raise IOError('"%s" contains %d project files, not sure which to use' % (path, len(projectFiles)))

    # TBD: should projectName be based on projectFile or on path???
    # the way it is set here do not need to change project.name
    # but if you used the path then you would need to change it
    projectName = ApiPath.getTopObjIdFromFileName(projectFile)

  # doing the loadProject twice has a bit of an overhead, but not much

  try:
    # below assumes TopObjects exist where stated, so might fail
    project = XmlIO.loadProject(path, projectName, partialLoad=False)

  except:
    warningMessages.append("\nFirst loading attempt failed - compatibility problem?.")
    project = None

  if project is not None and (not ApiPath.areAllTopObjectsPresent(project) or
      not isGeneralDataOk(project)):
    # if not all loaded (shell) TopObjects can be found, try again
    project = None
    warningMessages.append("\nSome files unfindable - project may have moved.")

  if project is None:
    warningMessages.append("Re-trying load, skipping cached TopObjects:")
    project = XmlIO.loadProject(path, projectName, partialLoad=True)

  # try and fix project repository path, if needed
  packageLocator = project.packageLocator
  repositories = packageLocator.repositories
  for repository in repositories:
    if repository.url.path == path:
      oldPath = path
      break
  else:
    # change first repository path to point to this one, and also change backup
    repository = repositories[0]
    oldPath = repository.url.path
    warningMessages.append('Project file has moved from\n"%s"\nto\n"%s"' % (oldPath, path))
    repository.url = Implementation.Url(path=path)
    # Necessary because activeRepositories are not set right
    # if file names do not match:
    project.__dict__['activeRepositories'].append(repository)

  projectRepository = repository

  # check backup path
  backupRepository = project.findFirstRepository(name="backup")
  if backupRepository:
    backupUrl = backupRepository.url
    oldBackupPath = backupUrl.path
    newBackupPath = path + '_backup'
    if oldBackupPath.startswith(oldPath): # hopefully true
      if path != oldPath:
        warningMessages.append('Backup is being changed from\n"%s"\nto\n"%s"' %
                               (oldBackupPath, newBackupPath))
        backupRepository.url = Implementation.Url(path=newBackupPath)
    elif not os.path.exists(oldBackupPath):
      warningMessages.append('Backup is being changed from\n"%s"\nto\n"%s"' %
                             (oldBackupPath, newBackupPath))
      backupRepository.url = Implementation.Url(path=newBackupPath)

  # check if project repository is called 'userData'
  if projectRepository.name != 'userData':
    warningMessages.append('Project has non-standard repository name "%s"' %
                           projectRepository.name)

  # repoint dataStores that are in same directory as project
  # (but only if old path does not exist and new one does)
  if path != oldPath:
    oldDirectory = os.path.dirname(oldPath)
    newDirectory = os.path.dirname(path)
    for dataLocationStore in project.dataLocationStores:
      for dataStore in dataLocationStore.dataStores:
        fullPath = dataStore.fullPath
        if not os.path.exists(fullPath):
          dataUrl = dataStore.dataUrl
          dataLocation = dataUrl.url.dataLocation
          if (dataLocation == oldDirectory or
              (dataLocation.startswith(oldDirectory) and dataLocation[len(oldDirectory)] ==
                Path.dirsep)):
            newDataUrlPath = newDirectory + dataLocation[len(oldDirectory):]
            newPath = Path.joinPath(newDataUrlPath, dataStore.path)
            if os.path.exists(newPath):
              warningMessages.append('DataStore %s:%s path has been changed from\n"%s"\nto\n"%s"' % (dataStore.dataLocationStore.name, dataStore.serial, oldDirectory, newDataUrlPath))
              dataUrl.url = dataUrl.url.clone(path=newDataUrlPath)

  # change refData to current one if need be
  refDataRepository = project.findFirstRepository(name='refData')
  if refDataRepository:
    oldPath = refDataRepository.url.path
    newPath = Path.normalisePath(Path.getDataDirectory())
    if newPath != oldPath:
      warningMessages.append('refData has been changed from\n"%s"\nto\n"%s"' % (oldPath, newPath))
      refDataRepository.url = Implementation.Url(path=newPath)
  else:
    warningMessages.append('Project has no repository with name "refData"')

  # change generalData to current one if need be
  generalDataRepository = project.findFirstRepository(name='generalData')
  if generalDataRepository and not suppressGeneralDataDir:
    oldPath = generalDataRepository.url.path
    if not os.path.exists(oldPath) or not isGeneralDataWriteable(generalDataRepository):
      newPath = Path.normalisePath(os.path.expanduser('~/.ccpn/data'))
      if not os.path.exists(newPath):
        os.makedirs(newPath)
      warningMessages.append('generalData has been changed from\n"%s"\nto\n"%s"' % (oldPath, newPath))
      generalDataRepository.url = Implementation.Url(path=newPath)

  # check other repository paths
  for repository in project.repositories:
    if repository not in (projectRepository, refDataRepository, backupRepository, generalDataRepository):
      oldPath = repository.url.path
      if not repository.stored:
        # title = 'Repository being deleted'
        # msg = 'Repository "%s" with path "%s" has no packageLocators, deleting' % (repository.name, oldPath)
        repository.delete()
      elif not os.path.exists(oldPath):

        msg = 'Repository "%s" path "%s" does not exist' % (repository.name, oldPath)
        warningMessages.append(msg)

        warningMessages.append('List of packageLocators for repository "%s":' % repository.name)
        for packageLocator in repository.stored:
          warningMessages.append('  %s' % packageLocator.targetName)

        if askDir:
          title = 'Repository path does not exist'
          newPath = askDir(title, msg + ': enter new path', initial_value=oldPath)
          while newPath and not os.path.exists(newPath):
            msg = 'Path "%s" does not exist' % newPath
            newPath = askDir(title, msg + ': enter new path', initial_value=newPath)
          if newPath:
            repository.url = Implementation.Url(path=Path.normalisePath(newPath))
            warningMessages.append("New path set: %s" % newPath)
          else:
            warningMessages.append(msg)

  # check and fix dataLocationStores
  if fixDataStores:
    dataStores = []
    for dataLocationStore in project.dataLocationStores:
      for dataStore in dataLocationStore.dataStores:
        if hasattr(dataStore, 'nmrDataSources') and not dataStore.nmrDataSources:
          warningMessages.append('deleting empty dataStore %s with path %s'
                                  % (dataStore, dataStore.fullPath))
          dataStore.delete()
        # We do nto use these, and if we ever did, who knows what else ehy might be used for
        # elif isinstance(dataStore, MimeTypeDataStore) and not dataStore.nmrDataSourceImages:
        #   warningMessages.append('deleting empty dataStore %s with path %s'
        #                          % (dataStore, dataStore.fullPath))
        #   dataStore.delete()
        else:
          dataStores.append(dataStore)

    badDataStores = [dataStore for dataStore in dataStores
                     if not os.path.exists(dataStore.fullPath)]

    if badDataStores:
      # find DataUrls involved
      dataUrls = set(dataStore.dataUrl for dataStore in badDataStores)
      # NBNB change here to possibly start a directory higher NBNB TBD
      # NB the following gets you the project directory (the one containing memops/)
      startDir = project.packageLocator.findFirstRepository().url.dataLocation

      for dataUrl in dataUrls:
        if not dataUrl.dataStores.difference(badDataStores):
          # all DataStores for this DataUrl are bad
          # we can make changes without affecting 'good' DataStores

          # Look for an obvious place the data may have moved to
          dataStores =  dataUrl.sortedDataStores()
          fullPaths = [dataStore.fullPath for dataStore in dataStores]
          baseDir, newPaths = Path.suggestFileLocations(fullPaths,
                                                        startDir=startDir)

          if baseDir is not None:
            # We have a file location that fits all missing files.
            # Change dataStores to use it
            warningMessages.append('WARNING, resetting data locations to: \n%s\n'
                                   % baseDir)

            AbstractDataStore.changeDataStoreUrl(dataStores[0], baseDir)
            for ii,dataStore in enumerate(dataStores):
              dataStore.path = newPaths[ii]

  if hasattr(project, '_movedPackageNames'):
    # Special hack for moving data of renamed packages on upgrade
    for newName, oldName in project._movedPackageNames.items():
      movePackageData(project, newName, oldName)
      
  logger = _createLogger(project, applicationName, useFileLogger)

  # initialise standard DataUrls and move dataStores to standard DataUrls where possible.
  _initialiseStandardDataLocationStore(project)
  _compressDataLocations(project)

  if warningMessages:
    # log warnings
    for msg in warningMessages:
      logger.warning(msg)

  # NBNB Hack: do data upgrade for V2-V3transition
  # TBD FIXME remove for future versions
  if hasattr(project,'_isUpgraded') and project._isUpgraded:
    from ccpnmodel.v_3_0_2.upgrade import correctFinalResult
    correctFinalResult(project)
  #
  return project

def cleanupProject(project):
  """Clean up project preparatory to closing (close log handlers etc.)"""

  # delete temporary project directory, if there is one
  deleteTemporaryDirectory(project)

  # clear loggers
  if hasattr(project, '_logger'):
    logger = project._logger
    for handler in logger.handlers[:]:
      logger.removeHandler(handler)


def deleteTemporaryDirectory(project):
  
  if hasattr(project, '_temporaryDirectory'):  
    project._temporaryDirectory.cleanup()
    del project._temporaryDirectory 
  
def saveProject(project, newPath=None, newProjectName=None, changeBackup=True,
                createFallback=False, overwriteExisting=False, showYesNo=None,
                checkValid=False, changeDataLocations=False):
  """
  Save the userData for a project to a location given by newPath (the url.path
  of the userData repository) if set, or the existing location if not.

  NB Changes to project in the function can NOT be undone, but previous contents of the undo
  queue are left active, so you can undo backwards.

  If userData does not exist then throws IOError.
  If newPath is not specified then it is set to oldPath.
  If newProjectName is not specified then it is set to oldProjectName if
  newPath==oldPath, otherwise it is set to basename(newPath).
  If changeBackup, then also changes backup URL path for project.
  If createFallback, then makes copy of existing modified topObjects
  files (in newPath, not oldPath) before doing save::

    If newPath != oldPath and newPath exists (either as file or as directory):
      If overwriteExisting:
        Delete the newPath.
      Else if showYesNo:
        Ask the user if it is ok to delete the newPath
        If yes, delete.  If no, return without saving.
      Else:
        Raise an IOError
    Elif newProjectName != oldProjectName and there exists corresponding path (file/directory):
      If overwriteExisting:
        Delete the path.
      Else if showYesNo:
        Ask the user if it is ok to delete the path.
        If yes, delete.  If no, return without saving.
      Else:
        Raise an IOError
    If checkValid then does checkAllValid on project
    If changeDataLocations then copy to project directory
    If there is no exception or early return then at end userData is pointing to newPath.
    Return True if save done, False if not (unless there is an exception)
  """
  
  undo = project._undo
  if undo is not None:
    undo.increaseBlocking()

  logger = project._logger

  # check project valid (so don't save an obviously invalid project)
  if checkValid:
    project.checkAllValid()

  # only want to change path for userData
  userData = project.findFirstRepository(name='userData')
  if not userData:
    raise IOError('Problem: userData not found')

  oldPath = userData.url.path
  oldProjectName = project.name

  if newPath:
    # normalise newPath
    newPath = Path.normalisePath(newPath, makeAbsolute=True)
  else:
    newPath = oldPath

  # if newProjectName isn't specified then use default
  if not newProjectName:
    if newPath == oldPath:
      newProjectName = oldProjectName
    else:
      newProjectName = os.path.basename(newPath)
      # below is because of data model limit
      newProjectName = newProjectName[:32]
  if newProjectName != project.name:
    renameProject(project, newProjectName)

  # if newPath same as oldPath, check if newProjectName already exists if it's not same as oldProjectName
  if newPath == oldPath:
    if newProjectName != oldProjectName:
      location = ApiPath.getTopObjectPath(project)
      if not absentOrRemoved(location, overwriteExisting, showYesNo):
        project.__dict__['name'] = oldProjectName  # TBD: for now name is frozen so change this way
        deleteTemporaryDirectory(project)
        if undo is not None:
          undo.decreaseBlocking()
        return False
  else: # check instead if newPath already exists
    if absentOrRemoved(newPath, overwriteExisting, showYesNo):
      # NBNB 2008/04/03 Rasmus Fogh. Added because it otherwise fell over when
      # target path did not exist
      upDir = os.path.dirname(newPath)
      if not os.path.exists(upDir):
        os.makedirs(upDir)
    else:
      if newProjectName != oldProjectName:
        project.__dict__['name'] = oldProjectName  # TBD: for now name is frozen so change this way
        deleteTemporaryDirectory(project)
        if undo is not None:
          undo.decreaseBlocking()
        logger = _createLogger(project)
        return False
      else:
        # TBD: should we be removing it?
        Path.deletePath(newPath)

    # check if any topObject activeRepository is not either of above
    refData = project.findFirstRepository(name='refData')
    genData = project.findFirstRepository(name='generalData')
    topObjects = []
    repositories = set()
    for topObject in project.topObjects:
      repository = topObject.findFirstActiveRepository()
      if repository and repository not in (userData, refData, genData):
        topObjects.append(topObject)
        repositories.add(repository)
    if topObjects:
      logger.warning('TopObjects %s, in repositories %s, being left in original locations'
                     % (topObjects, repositories))

  oldUrl = userData.url
  if changeBackup:
    # change project backup url to point to new path
    backupRepository = project.findFirstRepository(name="backup")
    if backupRepository:
      oldBackupUrl = backupRepository.url
    else:
      changeBackup = False

  try:
    # copy userData files over
    if newPath != oldPath:
      # if os.path.exists(oldPath):  # only copy if this is a directory
      if os.path.isdir(oldPath):
        # just copy everything from oldPath to newPath
        logger.warning(
          'Copying directory %s to %s (this might take some time if there are big files)'
          % (oldPath, newPath))
        shutil.copytree(oldPath, newPath)

        # but need to remove all implementation files
        implPath = Path.joinPath(newPath, metaConstants.modellingPackageName,
                            metaConstants.implementationPackageName)
        #implPath = pathImplDirectory(newPath)
        Path.deletePath(implPath)

        # and need to repoint dataUrl's that were copied over
        oldPathP = oldPath + '/'
        for dataLocationStore in project.dataLocationStores:
          for dataStore in dataLocationStore.dataStores:
            oldDataPath = dataStore.fullPath
            if oldDataPath.startswith(oldPathP):
              dataUrl = dataStore.dataUrl
              oldDataUrlPath = dataUrl.url.dataLocation
              if oldDataUrlPath.startswith(oldPathP): # normally true
                newDataUrlPath = newPath + oldDataUrlPath[len(oldPath):]
                dataUrl.url = Implementation.Url(path=newDataUrlPath)
              else: # path split awkwardly between absolute and relative
                newDataUrlPath = newPath
                dataUrl.url = Implementation.Url(path=newDataUrlPath)
                dataStore.path = oldDataPath[len(oldPath):]

      # change userData url to point to new path
      userData.url = Implementation.Url(path=newPath)
      # above will set project.isModified = True

      if changeBackup:
        # change project backup repository url to point to new path
        backupRepository.url = Implementation.Url(path=newPath+'_backup')

    # change project name
    if newProjectName != oldProjectName:
      if not project.isModified: # if it isModified it will be saved below
        if createFallback:
          createTopObjectFallback(project)
        project.save()

    # create fallbacks and keep track of modified topObjects
    modifiedTopObjects = []
    if createFallback:
      for topObject in (project,)+tuple(project.topObjects):
        if not topObject.isDeleted and topObject.isModified:
          createTopObjectFallback(topObject)
          modifiedTopObjects.append(topObject)

    if changeDataLocations:
      dataLocationStores = project.sortedDataLocationStores()

      userRepository = project.findFirstRepository(name='userData')
      userPath = userRepository.url.dataLocation
      # 2010 Aug 11: remove data directory from path
      #dataPath = joinPath(userPath, 'data')
      dataPath = userPath

      # 2010 Aug 11: change name
      #dataStorePrefix = 'dataStore'
      dataStorePrefix = 'spectra'
      if os.path.exists(dataPath):
        files = [xx for xx in os.listdir(dataPath) if xx.startswith(dataStorePrefix)]
        offset = len(files)
      else:
        offset = 0

      copyingList = []
      dataUrlDict = {}
      for dataLocationStore in dataLocationStores:
        for dataStore in dataLocationStore.sortedDataStores():

          # wb104: 24 Mar 2010: below check is a complete kludge
          # we should check whether dataStore is instance of
          # NumericMatrix, etc., but those are in ccp so should
          # not be imported here
          # in any case, there is no proper way to find out if
          # a dataStore is used without explicit knowledge of class
          knt = 0
          # hicard = 1
          for attr in ('nmrDataSourceImage',):
            if hasattr(dataStore, attr):
              if getattr(dataStore, attr):
                knt += 1
          # hicard > 1
          for attr in ('externalDatas', 'nmrDataSources'):
            if hasattr(dataStore, attr):
              knt += len(getattr(dataStore, attr))
          if knt == 0:
            continue

          oldFullPath = dataStore.fullPath
          if not oldFullPath.startswith(userPath+'/'):
            # first figure out new dataUrl path
            dataUrl = dataStore.dataUrl
            oldPath = dataUrl.url.dataLocation
            if dataUrl in dataUrlDict:
              newUrl = dataUrlDict[dataUrl]
            else:
              offset += 1
              newUrlPath = '%s%d' % (dataStorePrefix, offset)
              newUrlPath = Path.joinPath(dataPath, newUrlPath)
              newUrl = dataUrlDict[dataUrl] = Implementation.Url(path=newUrlPath)
            # then add to list to copy over if original data exists
            if os.path.exists(oldFullPath):
              newFullPath = Path.joinPath(newUrl.dataLocation, dataStore.path)
              copyingList.append((oldFullPath, newFullPath))

      # now copy data files over
      nfilesToCopy = len(copyingList)
      for n, (oldFullPath, newFullPath) in enumerate(copyingList):
        dirName = os.path.dirname(newFullPath)
        if not os.path.exists(dirName):
          os.makedirs(dirName)
        logger.warning('Copying file %s to %s (%d of %d)'
                       % (oldFullPath, newFullPath, n+1, nfilesToCopy))
        shutil.copy(oldFullPath, newFullPath)

      # finally change dataUrl paths
      for dataUrl in dataUrlDict:
        dataUrl.url = dataUrlDict[dataUrl]

    # save modifications
    # change way doing save in case exception is thrown
    if createFallback:
      for topObject in modifiedTopObjects:
        try:
          topObject.save()
        except:
          location = ApiPath.getTopObjectPath(topObject)
          logger.warning('Exception working on topObject %s, file %s' % (topObject, location))
          raise
      # be safe and do below in case new modifications after
      # modifiedTopObjects has been created
      project.saveModified()
    else:
      project.saveModified()

    if not commonUtil.isWindowsOS():
      os.system('touch "%s"' % newPath)  # so that user can see which are most recent

    badTopObjects = []
    for topObject in modifiedTopObjects:
      if not checkFileIntegrity(topObject):
        badTopObjects.append(topObject)

    if badTopObjects:
      logger.warning(
        'Incomplete save - one or more files did not save completely, you should check them:')
      for topObject in badTopObjects:
        logger.warning("Bad save: %s - %s" % (topObject, ApiPath.getTopObjectPath(topObject)))
      result = False
    else:
      result = True


  except:
    # saveModified failed so revert to old values
    if newProjectName != oldProjectName:
      project.__dict__['name'] = oldProjectName  # TBD: for now name is frozen so change this way
    if newPath != oldPath:
      userData.url = oldUrl
      if changeBackup:
        backupRepository.url = oldBackupUrl
      try:
        Path.deletePath(newPath)
      except:
        pass

    result = None
  
  logger = _createLogger(project)
  
  deleteTemporaryDirectory(project)

  if undo is not None:
    undo.decreaseBlocking()
  
  return result

def checkFileAtPath(path):
  """Check that file on disk ends correctly
  """
  if not os.path.exists(path):
    return False

  size = os.path.getsize(path)
  fp = open(path, 'rU')

  ss = '<!--End of Memops Data-->'
  n = len(ss)
  fp.seek(size-n-2, 0)  # -2 just to be safe in case has \r\n as line ending
  data = fp.read().strip()[-n:]
  fp.close()

  return data == ss

def checkFileIntegrity(topObject):
  """Check that topObject file on disk ends correctly
  """
  path = ApiPath.getTopObjectPath(topObject)

  return checkFileAtPath(path)

def createTopObjectFallback(topObject):
  """
  Create backup of topObject in same directory as original file but with '.bak' appended.
  This function is not intended to be used outside this module but could be.
  """

  logger = Logging.getLogger()

  location = ApiPath.getTopObjectPath(topObject)
  if not os.path.exists(location):
    return

  backupLocation = location + '.bak'
  if not checkFileAtPath(location) and checkFileAtPath(backupLocation):
    # current file no good and current backup good so do not do backup
    logger.warning('File at location "%s" not complete so not backing up' % location)
    return

  # copy rather than move because will need that much disk space in any case
  # and sometimes move fails at OS level if file with that name already exists
  directory = os.path.dirname(backupLocation)
  if not os.path.exists(directory):
    os.makedirs(directory)
  shutil.copy(location, backupLocation)


def renameProject(project, newProjectName):
  """ Rename project.
  """
  oldProjectName = project.name

  undo = project._undo
  if undo is not None:
    undo.increaseBlocking()

  logger = Logging.getLogger()

  logger.warning('Renaming project %s to %s' % (project.name, newProjectName))

  # change project name
  if newProjectName == oldProjectName:
    return

  else:
    project.override = True # TBD: for now name is frozen so change this way
    try:
      # below constraint is not checked in setName() if override is True so repeat here
      isValid = newProjectName.isalnum()  # superfluous but faster in most cases
      if not isValid:
        for cc in newProjectName:
          if cc != '_' and not cc.isalnum():
            isValid = False
            break
        else:
          isValid = True
      if not isValid:
        raise ApiError('project name must only have characters that are alphanumeric or underscore')

      # below checks for length of name as well
      project.name = newProjectName
    finally:
      project.override = False
      if undo is not None:
        undo.decreaseBlocking()
        undo.newItem(renameProject, renameProject, undoArgs=(project,oldProjectName),
                     redoArgs=(project, newProjectName))


def _downlinkTagsByImport(root):
  """ gives you the role names of links from MemopsRoot to TopObjects
  in import order, so that imported packages come before importing packages
  """

  from ccpncore.memops.metamodel import Util as metaUtil

  leafPackages = []
  packages = [root.metaclass.container.topPackage()]
  for pp in packages:
    childPackages = pp.containedPackages
    if childPackages:
      packages.extend(childPackages)
    else:
      leafPackages.append(pp)

  # sort leafPackages by import (imported before importing)
  leafPackages = metaUtil.topologicalSortSubgraph(leafPackages,
                                                  'accessedPackages')
  tags = []
  for pp in leafPackages:
    cc = pp.topObjectClass
    if cc is not None:
      pr = cc.parentRole
      if pr is not None:
        tags.append(pr.otherRole.name)
  #
  return tags


def loadAllData(root):
  """ Load all data for a given root (version >= 2.0)
  """
  # load all new data before modifying IO map
  for tag in _downlinkTagsByImport(root):
    for topObj in getattr(root, tag):
      if not topObj.isLoaded:
        topObj.load()



def backupProject(project, dataLocationStores = None, skipRefData = True, clearOutDir = False):

  def modificationTime(path):
    return os.stat(path)[8]

  backupRepository = project.findFirstRepository(name="backup")

  if not backupRepository:
    project._logger.warning('Warning: no backup path set, so no backup done')
    return

  backupUrl = backupRepository.url
  backupPath = backupUrl.path

  if not dataLocationStores:
    dataLocationStores = set()

  if clearOutDir:
    Path.deletePath(backupPath)

  topObjects = tuple(project.topObjects) + (project,)

  for topObject in topObjects:
    if skipRefData:
      repository = topObject.findFirstActiveRepository(name='refData')
      if repository:
        continue

    if topObject.isModified:
      topObject.backup()
    else:
      repository = topObject.findFirstActiveRepository()
      if repository:
        origFile = ApiPath.findTopObjectPath(repository.url.path, topObject)
        if os.path.exists(origFile):
          # problem with appending repository.name is that topObject.backup()
          # above does not do it this way, so end up with inconsistent backup
          ###backupDir = joinPath(backupPath, repository.name)
          # so use same backup pah as topObject.backup()
          backupDir = backupPath
          backupFile = ApiPath.findTopObjectPath(backupDir, topObject)
          if not os.path.exists(backupFile) or \
              (modificationTime(backupFile) < modificationTime(origFile)):
            directory = os.path.dirname(backupFile)
            if not os.path.exists(directory):
              os.makedirs(directory)
            shutil.copy(origFile, backupFile)
        else:
          # one is stuffed
          project._logger.warning('Warning: could not backup" "'
                                  ' %s since could not find original file "%s"'
                                  % (topObject, origFile))
      else:
        # one is stuffed
        project._logger.warning('Warning: could not backup %s since could not find repository'
                                % topObject)

  dataBackupPath = Path.joinPath(backupPath, 'data')
  for dataLocationStore in dataLocationStores:
    dataBackupDir = Path.joinPath(dataBackupPath, dataLocationStore.name)
    for dataStore in dataLocationStore.dataStores:
      origFile = dataStore.dataUrl.url.path
      backupFile = Path.joinPath(dataBackupDir, dataStore.path)

      if os.path.exists(origFile):
        if not os.path.exists(backupFile) or \
            (modificationTime(backupFile) < modificationTime(origFile)):
          directory = os.path.dirname(backupFile)
          if not os.path.exists(directory):
            os.makedirs(directory)
          shutil.copy(origFile, backupFile)
      else:
        project._logger.warning('Warning: could not backup dataStore '
                                '"%s" because could not find original file "%s"'
                                % (dataStore.name, origFile))

def modifyPackageLocators(project,repositoryName,repositoryPath,packageNames,resetPackageLocator = True,resetRepository = False):

  """
  Resets package locators for specified packages to specified repository.

  Use as, for example:

  modifyPackageLocators(project,'newChemComps','/mydir/data/chemComps/',('ccp.molecule.ChemComp','ccp.molecule.ChemCompCoord'))

  Additional args:

  - resetPackageLocator:  True   will reset the package locator completely, removing old info
                          False  will add the repository to the package locator.

  - resetRepository:      True   will reset url for the repository, even if it already exists
                          False  will not reset the url for the repository if it already exists

  Returns the relevant repository.

  """

  repository = project.findFirstRepository(name = repositoryName)
  ss = Path.normalisePath(repositoryPath)

  if not repository:
    repository = project.newRepository(name= repositoryName,
                                       url=Implementation.Url(path=ss))
  elif resetRepository and repository.url.path != repositoryPath:
    repository.url = Implementation.Url(path=ss)

  for packageName in packageNames:
    packageLocator = project.findFirstPackageLocator(targetName = packageName)

    if not packageLocator:
      raise ApiError("Cannot modify repository 'any' for package %s"
                     % packageName)

    if resetPackageLocator:
      packageLocator.repositories = (repository,)
    elif not repository in packageLocator.repositories:
      packageLocator.addRepository(repository)

  return repository

def packageProject(project, filePrefix=None, includeBackups=False, includeData=False):
  """
  Package up project userData into one gzipped tar file.
  If filePrefix is None then instead use the userData path.
  The tar file is filePrefix+".tgz".
  By default only \*.xml files are packaged up.
  If includeBackups then also \*.xml.bak files are included.
  If includeData then also dataStores located inside project directory are included.
  """

  # NBNB TBD FIXME check how many dataLocatoins to package (and make sure you reset first)

  import tarfile

  userPath = getRepositoryPath(project, 'userData')
  userDir = os.path.dirname(userPath)

  if includeData:
    userPathP = userPath + '/'
    n = len(userDir) + 1
    includedDataPaths = set()
    for dataLocationStore in project.dataLocationStores:
      for dataStore in dataLocationStore.dataStores:
        fullPath = dataStore.fullPath
        if fullPath.startswith(userPathP):
          includedDataPaths.add(fullPath[n:])

  userPath = os.path.basename(userPath)

  def visitDir(directory):
    tarFiles = []
    for relfile in os.listdir(directory):
      fullfile = os.path.join(directory, relfile)
      include = False
      if os.path.isdir(fullfile):
        tarFiles.extend(visitDir(fullfile))
      elif relfile.endswith('.xml'):
        include = True
      elif includeBackups and relfile.endswith('.xml.bak'):
        include = True
      elif includeData and fullfile in includedDataPaths:
        include = True

      if include:
        project._logger.info(fullfile)
        tarFiles.append(fullfile)

    if tarFiles:
      tarFiles.insert(0, directory)

    return tarFiles

  if not filePrefix:
    filePrefix = userPath

  tarFile = '%s.tgz' % filePrefix
  tarFp = tarfile.open(tarFile, 'w:gz')

  cwd = os.getcwd()
  os.chdir(userDir)
  try:
    project._logger.nfo('Files included in tar file:')
    files = visitDir(userPath)
    for tarFile in files:
      tarFp.add(tarFile, recursive=False)
  finally:
    os.chdir(cwd)
    tarFp.close()

# def logMemoryStats(project, path):
#   """
#   Logs stats for a project.
#   It appends information to the file given by path.
#   """
#   import gc
#
#   path = Path.normalisePath(path)
#   fp = open(path, 'a')
#   if fp:
#     t = time.ctime(time.time())
#     m = gc.collect()
#     n = len(gc.get_objects())
#     s = '%s: %d collected, %d objects' % (t, m, n)
#     fp.write('%s\n' % s)
#     project._logger.info('logging: %s' % s)
#     fp.close()

def findCcpXmlFile(project,packageName,fileSearchString):

  """
  Finds an XML file by a file search pattern from all available package repositories
  """

  ff = project.findFirstPackageLocator
  packageLocator = ff(targetName=packageName) or ff(targetName='any')

  xmlFileName = None
  # The repositories link is ordered!
  for repository in packageLocator.repositories:

    fileLocation = repository.getFileLocation(packageName)
    xmlFileNameMatches = glob.glob(os.path.join(fileLocation,fileSearchString))

    if xmlFileNameMatches:
      if xmlFileNameMatches[-1][-4:] == '.xml':
        xmlFileName = xmlFileNameMatches[-1]
        break

  return xmlFileName

def getRepositoryPath(project, repositoryName):

  repository = project.findFirstRepository(name=repositoryName)
  if repository:
    path = repository.url.path
  else:
    path = None

  return path

def setRepositoryPath(project, repositoryName, path):

  from ccpncore.api.memops.Implementation import Url

  repository = project.findFirstRepository(name=repositoryName)
  if repository:
    if path != repository.url.path:
      # TBD: should we copy anything over from old url?
      url = Url(path=Path.normalisePath(path))
      repository.url = url

  # TBD: should we throw an exception if repository is not found?


def movePackageData(root, newPackageName, oldPackageName):
  """Move all data from package oldPackageNAme to newPackageName"""
  ff = root.findFirstPackageLocator
  repositories = (ff(targetName=newPackageName) or ff(targetName='any')).repositories
  newLocations = [x.getFileLocation(newPackageName) for x in repositories]

  # If there were data in correct location assume that project is fixed already
  if not any(x for x in newLocations if os.path.isdir(x)):
    repositories = (ff(targetName=oldPackageName) or ff(targetName='any')).repositories
    oldLocations = [x.getFileLocation(oldPackageName) for x in repositories]
    oldLocations = [x for x in oldLocations if os.path.isdir(x)]

    if oldLocations:
      # there were old data in the wrong location. Move to new one.
      newDir = newLocations[-1]
      os.makedirs(newDir)
      for oldDir in oldLocations:
        for filename in os.listdir(oldDir):

          if filename.startswith('.'):
            # skip hidden files (on *nix/Mac)
            continue

          elif filename.endswith('.xml'):
            shutil.move(os.path.join(oldDir, filename), os.path.join(newDir, filename))



# def getBackupPath(project):
#
#   return getRepositoryPath(project, 'backup')
#
# def setBackupPath(project, path):
#
#   return setRepositoryPath(project, 'backup', path)


# def findCcpnProjectDirs(inDir):
#   """ Find list of (potential) CCPN project dirs within inDir
#   """
#   result = []
#   for dirpath, dirnames, filenames in os.walk(inDir):
#     if dirpath.endswith('memops') and 'Implementation' in dirnames:
#       result.append(os.path.dirname(dirpath))
#   #
#   return result
#   # NBNB fixme
#   ff = project.findFirstPackageLocator
#   packageLocator = ff(targetName=packageName) or ff(targetName='any')
#
#   xmlFileName = None
#   # The repositories link is ordered!
#   for repository in packageLocator.repositories:
#
#     fileLocation = repository.getFileLocation(packageName)
#     xmlFileNameMatches = glob.glob(os.path.join(fileLocation,fileSearchString))
#
#     if xmlFileNameMatches:
#       if xmlFileNameMatches[-1][-4:] == '.xml':
#         xmlFileName = xmlFileNameMatches[-1]
#         break
#
#   return xmlFileName

def _initialiseStandardDataLocationStore(memopsRoot:Implementation.MemopsRoot):
  """Get or create standard DataLocationStore, and reset standard data location urls
  to current location.
   Called from MemopsRoot.__init__"""

  result = memopsRoot.findFirstDataLocationStore(name='standard')
  if result is None:
    # Normal case make the DataLocationStore and contents
    result = memopsRoot.newDataLocationStore(name='standard')

  # insideData = data inside the project
  dataUrlObject = result.findFirstDataUrl(name='insideData')
  projectUrl = memopsRoot.findFirstRepository(name='userData').url
  if dataUrlObject is None:
    # make new dataUrl
    result.newDataUrl(name='insideData', url=projectUrl)

  # alongsideData - points to directory containing project directory
  dataUrlObject = result.findFirstDataUrl(name='alongsideData')
  path, junk = Path.splitPath(projectUrl.path)
  if dataUrlObject is None:
    # make new dataUrl
    result.newDataUrl(name='alongsideData', url=Implementation.Url(path=path))

  # remoteData - initialised to home directory and not reset
  dataUrlObject = result.findFirstDataUrl(name='remoteData')
  path = os.path.expanduser('~')
  if dataUrlObject is None:
    # make new dataUrl
    result.newDataUrl(name='remoteData', url=Implementation.Url(path=path))
  #
  return result

def _compressDataLocations(memopsRoot:Implementation.MemopsRoot):
  """Reorganise DataLocations to use standard DataUrls"""
  standardStore = memopsRoot.findFirstDataLocationStore(name='standard')
  locationData = []
  standardTags = ('insideData', 'alongsideData', 'remoteData')
  for tag in standardTags:
    dataUrl = standardStore.findFirstDataUrl(name=tag)
    locationData.append((os.path.join(dataUrl.url.path, ''), dataUrl))
  standardUrls = [tt[1] for tt in locationData]

  for dataLocationStore in memopsRoot.dataLocationStores:
    for dataUrl in dataLocationStore.dataUrls:
      if dataUrl not in standardUrls:
        for dataStore in dataUrl.dataStores:
          fullPath = dataStore.fullPath
          for directory, targetUrl in locationData:
            if fullPath.startswith(directory):
              dataStore.repointToDataUrl(targetUrl)
              dataStore.path = fullPath[len(directory):]
              break