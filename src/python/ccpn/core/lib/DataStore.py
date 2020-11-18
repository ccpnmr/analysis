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
from ccpn.util.traits.CcpNmrTraits import Unicode, Any, CPath

from ccpn.framework.Application import getApplication


# Data path URL's (not yet used everywhere; i.e. there are still hardcoded instances to track
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


def getDataStores(project):
    """
    Return a list of DataStore objects corresponding to the various spectrum files in project

    """
    # dataUrls = [url for store in project._wrappedData.root.sortedDataLocationStores()
    #                     for url in store.sortedDataUrls()]
    # dataStores = [DataStore(s) for url in dataUrls for s in url.sortedDataStores()]
    dataStores = [DataStore.newFromSpectrum(s) for s in project.spectra]
    return dataStores


class DataStore(CcpNmrJson):
    """
    This class wraps the inplementation of $DATA, $ALONGSIDE, $INSIDE redirections
    For old S[ectrum instances, its parses the api insideData, remoteData, alongSideData etc. api dataStores

    It stores the path and other relevenant info as json-encoded string in the spectrum instance internal
    parameter storage
    """

    version = 1.0

    spectrum = Any(allow_none=True, default_value=None).tag(saveToJson=False)

    # api dataStore
    apiDataStore = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    apiDataStoreName = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStoreDir = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStorePath = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)

    insidePath = CPath(allow_none=True, default_value=None).tag(saveToJson=True,
                                                                identifier=INSIDE_INDENTIFIER,
                                                                apiName=INSIDE_DATAURL_NAME)
    alongsidePath = CPath(allow_none=True, default_value=None).tag(saveToJson=True,
                                                                   identifier=ALONGSIDE_INDENTIFIER,
                                                                   apiName=ALONGSIDE_DATAURL_NAME)
    dataPath = CPath(allow_none=True, default_value=None).tag(saveToJson=True,
                                                              identifier=DATA_INDENTIFIER,
                                                              apiName=DATA_DATAURL_NAME)

    _path = CPath(allow_none=True, default_value=None).tag(saveToJson=True)

    def __init__(self, path=None, expandData=True, autoRedirect=False):
        """expandData: optionally expand $DATA to home directory if not defined
        autoRedirect: optionally try to redefine path into $DATA, $ALONGSIDE, $INSIDE redirections
        """

        super().__init__()
        self.expandData = expandData
        self.autoRedirect = autoRedirect
        self.path = path  # Needs to be last as we need self.autoRedirect to be defined

    @classmethod
    def newFromSpectrum(cls, spectrum):
        if spectrum is None:
            raise ValueError('Invalid spectrum "%s"' % spectrum)

        if not spectrum._hasInternalParameter(cls.__name__):
            instance = cls.newFromApiSpectrum(spectrum._wrappedData)
            jsonData = instance.toJson()
            spectrum._setInternalParameter(cls.__name__, jsonData)
        else:
            instance = cls()
            jsonData = spectrum._getInternalParameter(cls.__name__)
            instance.fromJson(jsonData)

        instance.spectrum = spectrum

        return instance

    @classmethod
    def newFromApiSpectrum(cls, apiSpectrum):
        """This routine implements the extraction from the old storage mechanism (using api DataStores).
        Return an DataStore instance
        """
        if apiSpectrum is None:
            raise ValueError('Invalid spectrum "%s"' % apiSpectrum)

        instance = cls()
        instance.apiDataStore = apiSpectrum.dataStore

        if instance.apiDataStore is not None:
            instance.apiDataStoreName = instance.apiDataStore.dataUrl.name
            instance.apiDataStoreDir = instance.apiDataStore.dataUrl.url.path
            instance.apiDataStorePath = instance.apiDataStore.path

            # Encode the different dataStores
            if instance.apiDataStoreName in dataUrlsDict:
                instance._path = os.path.join(dataUrlsDict[instance.apiDataStoreName], instance.apiDataStorePath)
            else:
                instance._path = os.path.join(instance.apiDataStoreDir, instance.apiDataStorePath)

        return instance

    def _setPaths(self):
        """Set paths and return a list of (identifier, path) tuples
        optionally expand $DATA to home directory if not defined
        """
        application = getApplication()

        dataPath = application.preferences.general.get('dataPath')
        if (dataPath is None or len(dataPath) == 0) and self.expandData:
            self.dataPath = Path.home()
        else:
            self.dataPath = Path(dataPath)
        self.insidePath = Path(application.project.path)
        self.alongsidePath = self.insidePath.parent

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

    def reDirectPath(self, path):
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
            value = self.reDirectPath(value)
        self._path = value

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



# class DataStore2(object):
#     """
#     This class wraps an api DataStore and allows for inplementation of the insideData, remoteData,
#     alongSideData etc.
#     """
#
#     def __init__(self, spectrum):
#         if spectrum is None or not isinstance(spectrum, Spectrum):
#             raise ValueError('Invalid spectrum "%s"' % spectrum)
#         self.spectrum = spectrum
#
#     @property
#     def apiDataStore(self):
#         "Return apiDataStore or None if does not exist"
#         return self.spectrum._wrappedData.dataStore
#
#     @apiDataStore.setter
#     def apiDataStore(self, value):
#         self.spectrum._wrappedData.dataStore = value
#
#     @property
#     def aPath(self):
#         """Return aPath instance of self, decoded for insideData, remoteData, alongSideData
#         redirections
#         """
#         if self.apiDataStore is None:
#             return aPath(constants.UNDEFINED_STRING)
#
#         _storeName, _storePath, _path = self.getValues()
#         return aPath(_storePath) / _path
#
#     @property
#     def path(self):
#         """Return a string representation of self, encoded for insideData, remoteData, alongSideData
#         """
#         if self.apiDataStore is None:
#             return aPath(constants.UNDEFINED_STRING)
#
#         _storeName, _storePath, _path = self.getValues()
#         if _storeName in constants.dataUrlsDict:
#             return os.path.join(constants.dataUrlsDict[_storeName], _path)
#         else:
#             return os.path.join(_storePath, _path)
#
#     # @path.setter
#     # def path(self, value):
#     #     """Set path to value; None makes it undefined
#     #     """
#     #     _storeName, _storePath, _path = self.getValues()
#     #     self.apiDataStore.delete()
#     #
#     #     if value is None:
#     #         self.apiDataStore = None
#     #         return
#     #
#     #     apiUrl = self.spectrum._wrappedData.root.fetchDataUrl(value)
#
#
#     def getValues(self):
#         """Return triple (storeName, storePath, itemPath) or (None, None, <Undefined>) in case there is
#         no valid datastore
#         """
#         if self.apiDataStore is None:
#             return (None, None, constants.UNDEFINED_STRING)
#
#         return (self.apiDataStore.dataUrl.name,
#                 self.apiDataStore.dataUrl.url.path,
#                 self.apiDataStore.path)
#
#     def exists(self):
#         """Return True if dataStore path exists
#         """
#         if self.apiDataStore is None:
#             return False
#         else:
#             return self.aPath.exists()
#
#     def __str__(self):
#         return '<%s: %s>' % (self.__class__.__name__, self.path)
#
#     __repr__ = __str__