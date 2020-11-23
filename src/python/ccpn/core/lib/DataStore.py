"""
This wraps the silly dataStore and dataUrl data structures

A project has stores (i.e. insideData, remoteData, alongSideData), that contain dataStores
with individual spectrum files

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
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:48 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os, sys

from ccpn.util.Path import aPath, Path
from ccpn.framework import constants
from ccpn.util.traits.CcpNmrJson import CcpNmrJson
from ccpn.util.traits.CcpNmrTraits import Unicode, Any, CPath, Bool

from ccpn.core.lib.ContextManagers import notificationBlanking
from ccpn.util.decorators import singleton

from ccpn.framework.Application import getApplication


# Data path URL's (not yet used everywhere; i.e. there are still hardcoded instances to track)
INSIDE_DATAURL_NAME = 'insideData'
INSIDE_INDENTIFIER = '$INSIDE'

ALONGSIDE_DATAURL_NAME = 'alongsideData'
ALONGSIDE_INDENTIFIER = '$ALONGSIDE'

DATA_DATAURL_NAME = 'remoteData'
DATA_INDENTIFIER = '$DATA'

# Covenience
dataUrlsDict = {
    INSIDE_DATAURL_NAME:INSIDE_INDENTIFIER,
    ALONGSIDE_DATAURL_NAME:ALONGSIDE_INDENTIFIER,
    DATA_DATAURL_NAME:DATA_INDENTIFIER,
}

@singleton
class PathRedirections(CcpNmrJson):
    """
    Class to maintain the path redirections $DATA, $ALONGSIDE, $INSIDE
    """

    _application = Any(default_value=None, allow_none=True)

    _dataPath = CPath(default_value=None, allow_none=True).tag(apiName=DATA_DATAURL_NAME, identifier=DATA_INDENTIFIER)
    _insidePath = CPath(default_value=None, allow_none=True).tag(apiName=INSIDE_DATAURL_NAME, identifier=INSIDE_INDENTIFIER)
    _alongsidePath = CPath(default_value=None, allow_none=True).tag(apiName=ALONGSIDE_DATAURL_NAME, identifier=ALONGSIDE_INDENTIFIER)


    def __init__(self):
        super().__init__()
        self._application = getApplication()

    @property
    def dataPath(self):
        if self._dataPath is None:
            self._dataPath = self._application.preferences.general.dataPath
        return self._dataPath

    @dataPath.setter
    def dataPath(self, path):
        self._dataPath = path
        self._application.preferences.general.dataPath = path

    @property
    def insidePath(self):
        self._insidePath = aPath(self._application.project.path)
        return self._insidePath

    @property
    def alongsidePath(self):
        self._alongsidePath = aPath(self._application.project.path).parent
        return self._alongsidePath



# def getDataStores(project):
#     """
#     Return a list of DataStore objects corresponding to the various spectrum files in project
#
#     """
#     # dataUrls = [url for store in project._wrappedData.root.sortedDataLocationStores()
#     #                     for url in store.sortedDataUrls()]
#     # dataStores = [DataStore(s) for url in dataUrls for s in url.sortedDataStores()]
#     dataStores = [DataStore.newFromSpectrum(s) for s in project.spectra]
#     return dataStores



class DataStore(CcpNmrJson):
    """
    This class wraps the inplementation of $DATA, $ALONGSIDE, $INSIDE redirections
    For old S[ectrum instances, its parses the api insideData, remoteData, alongSideData etc. api dataStores

    It stores the path and other relevenant info as json-encoded string in the spectrum instance internal
    parameter storage
    """

    version = 1.0

    _path = CPath(allow_none=True, default_value=None).tag(saveToJson=True)
    spectrum = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    expandData = Bool(default_value=True).tag(saveToJson=False)
    autoRedirect = Bool(default_value=False).tag(saveToJson=False)

    # api dataStore
    apiDataStore = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    apiDataStoreName = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStoreDir = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStorePath = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)

    # Redirection paths
    insidePath = CPath(allow_none=True, default_value=None).tag(saveToJson=True,
                                                                identifier=INSIDE_INDENTIFIER,
                                                                apiName=INSIDE_DATAURL_NAME)
    alongsidePath = CPath(allow_none=True, default_value=None).tag(saveToJson=True,
                                                                   identifier=ALONGSIDE_INDENTIFIER,
                                                                   apiName=ALONGSIDE_DATAURL_NAME)
    dataPath = CPath(allow_none=True, default_value=None).tag(saveToJson=True,
                                                              identifier=DATA_INDENTIFIER,
                                                              apiName=DATA_DATAURL_NAME)


    def __init__(self, spectrum=None, expandData=True, autoRedirect=False):
        """expandData: optionally expand $DATA to home directory if not defined
        autoRedirect: optionally try to redefine path into $DATA, $ALONGSIDE, $INSIDE redirections
        """
        super().__init__()
        self.spectrum = spectrum
        self.expandData = expandData
        self.autoRedirect = autoRedirect
        
        if spectrum is not None:
            self._importFromSpectrum(spectrum)

    @classmethod
    def newFromPath(cls, path, expandData=True, autoRedirect=False):
        """Create and return a new instance from path
        """
        instance = cls(expandData=expandData, autoRedirect=autoRedirect)
        instance.path = path
        return instance

    def _importFromSpectrum(self, spectrum):
        """Restore state from spectrum, either from internal parameter store or from api-dataStores
        Returns self
        """
        if spectrum is None:
            raise ValueError('Invalid spectrum "%s"' % spectrum)

        if spectrum._hasInternalParameter(self.__class__.__name__):
            self.spectrum = spectrum
            self._restoreInternal()
        else:
            self._restoreFromApiSpectrum(spectrum._wrappedData)
            self.spectrum = spectrum
            self._saveInternal()

        return self

    def _saveInternal(self):
        """Save into spectrum internal parameter store
        CCPNINTERNAL: e.g. _newSpectrum
        """
        if self.spectrum is None:
            raise RuntimeError('%s._saveInternal: spectrum not defined' % self.__class__.__name__)
        jsonData = self.toJson()
        self.spectrum._setInternalParameter(self.__class__.__name__, jsonData)

    def _restoreInternal(self):
        """Restore from spectrum internal parameter store
        CCPNINTERNAL: e.g. _newSpectrum
        """
        if self.spectrum is None:
            raise RuntimeError('%s._restoreInternal: spectrum not defined' % self.__class__.__name__)
        jsonData = self.spectrum._getInternalParameter(self.__class__.__name__)
        self.fromJson(jsonData)

    def _restoreFromApiSpectrum(self, apiSpectrum):
        """This routine implements the extraction from the old storage mechanism (using api DataStores).
        Returns self
        """
        if apiSpectrum is None:
            raise ValueError('Invalid spectrum "%s"' % apiSpectrum)

        self.apiDataStore = apiSpectrum.dataStore

        if self.apiDataStore is not None:
            self.apiDataStoreName = self.apiDataStore.dataUrl.name
            self.apiDataStoreDir = self.apiDataStore.dataUrl.url.path
            self.apiDataStorePath = self.apiDataStore.path

            # Encode the different dataStores
            if self.apiDataStoreName in dataUrlsDict:
                self._path = os.path.join(dataUrlsDict[self.apiDataStoreName], self.apiDataStorePath)
            else:
                self._path = os.path.join(self.apiDataStoreDir, self.apiDataStorePath)

        return self

    def _setPaths(self):
        """Set redirection paths and return a list of (identifier, path) tuples
        optionally (depending on expandData flag) expand $DATA to home directory if not defined
        """
        self.dataPath = getDataPath() #PathRedirections().dataPath #
        self.insidePath = PathRedirections().insidePath
        self.alongsidePath = PathRedirections().alongsidePath

        result = [ (INSIDE_INDENTIFIER, self.insidePath),
                   (ALONGSIDE_INDENTIFIER, self.alongsidePath),
                   (DATA_INDENTIFIER, self.dataPath)
                 ]
        return result

    @property
    def aPath(self):
        """Return aPath instance of self, decoded for $DATA, $ALONGSIDE, $INSIDE redirections
        optionally expand $DATA to home directory if not defined, depending on the self.expandData flag
        """
        if self._path is None:
            return aPath(constants.UNDEFINED_STRING)

        # decode the $DATA, $INSIDE $ALONGSIDE
        _path = Path(self._path)
        for d, p in self._setPaths():
            if str(self._path).startswith(d):
                _path = p / Path._from_parts(_path.parts[1:])
                break

        return aPath(_path)

    def redirectPath(self, path):
        """Redefine path into $DATA, $ALONGSIDE, $INSIDE redirections
        return Path instance
        """
        _path = Path(path)
        for d, p in self._setPaths():
            if str(path).startswith(str(p)):
                _path = Path(d) / _path.relative_to(p)
                break
        return _path

    @property
    def path(self):
        """Return a Path representation of self, optionally encoded with $DATA, $ALONGSIDE, $INSIDE redirections
        """
        if self._path is None:
            return Path(constants.UNDEFINED_STRING)

        return Path(self._path)

    @path.setter
    def path(self, value):
        """Set path to value; None makes it undefined
        """
        if value is not None and self.autoRedirect:
            value = self.redirectPath(value)
        self._path = value
        if self.spectrum is not None:
            self._saveInternal()

    def exists(self):
        """Return True if self.path exists
        """
        if self._path is None:
            return False
        else:
            return self.aPath.exists()

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.path)

    __repr__ = __str__


def _getPathFromApiStore(storeName):
    """Return path associated with storeName
    """
    if storeName not in dataUrlsDict.keys():
        raise RuntimeError('_getPathFromApiStore: invalid storeName "%s"' %storeName)

    project = getApplication().project
    if project is None:
        raise RuntimeError('_getPathFromApiStore: undefined project')

    dataUrl = project._apiNmrProject.root.findFirstDataLocationStore(
                name='standard').findFirstDataUrl(name=DATA_DATAURL_NAME)
    path = dataUrl.url.dataLocation
    return path



def getDataPath(expandDataPath=False):
    """Return the path corresponding to $DATA
    Optionally expand to user home directory if it None or has len==0
    returns aPath instance
    """
    path = _getPathFromApiStore(DATA_DATAURL_NAME)
    if (path is None or len(path) == 0) and expandDataPath:
        path = Path.home()
    return aPath(path)


# def getInsidePath():
#     """Return the path corresponding to $INSIDE
#     returns aPath instance
#     """
#     # path = _getPathFromApiStore(INSIDE_DATAURL_NAME) Incorrect GWV??
#     path = getApplication().project.path
#     return aPath(path)
#
#
# def getAlongsidePath():
#     """Return the path corresponding to $ALONGSIDE
#     returns aPath instance
#     """
#     return getInsidePath().parent
